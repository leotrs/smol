#!/usr/bin/env python3
"""Export PostgreSQL database to SQLite.

Exports all tables from PostgreSQL to SQLite, filtering graphs by max_n.

Usage:
    python scripts/export_to_sqlite.py --output smol.db --max-n 10
"""

import argparse
import json
import os
import sqlite3
import sys
import time

import psycopg2

PG_DATABASE_URL = os.environ.get("DATABASE_URL", "dbname=smol")

# Tables to export and their n-filtering (None = export all rows)
TABLES = {
    "graphs": "n <= {max_n}",
    "cospectral_mates": "graph1_id IN (SELECT id FROM graphs WHERE n <= {max_n})",
    "stats_cache": None,
}


def get_pg_connection():
    return psycopg2.connect(PG_DATABASE_URL)


def create_sqlite_db(output_path: str):
    """Create SQLite database with schema."""
    if os.path.exists(output_path):
        os.remove(output_path)

    conn = sqlite3.connect(output_path)
    schema_path = os.path.join(os.path.dirname(__file__), "..", "sql", "schema_sqlite.sql")
    with open(schema_path) as f:
        conn.executescript(f.read())
    conn.commit()
    return conn


def pg_to_sqlite_value(val, col_type: str):
    """Convert PostgreSQL value to SQLite-compatible value."""
    if val is None:
        return None
    if isinstance(val, list):
        return json.dumps(val)
    if isinstance(val, dict):
        return json.dumps(val)
    if isinstance(val, bool):
        return 1 if val else 0
    return val


def export_table(
    sqlite_conn,
    pg_conn,
    table: str,
    where_clause: str | None,
    max_n: int,
    batch_size: int = 5000,
):
    """Export a single table from PostgreSQL to SQLite."""
    pg_cur = pg_conn.cursor()
    sqlite_cur = sqlite_conn.cursor()

    # Get column info
    pg_cur.execute(
        """
        SELECT column_name, data_type
        FROM information_schema.columns
        WHERE table_name = %s
        ORDER BY ordinal_position
        """,
        (table,),
    )
    columns = [(row[0], row[1]) for row in pg_cur.fetchall()]
    col_names = [c[0] for c in columns]

    # Skip 'id' column if it's auto-generated (let SQLite handle it)
    # Actually, we need to preserve IDs for foreign key relationships
    # So we include all columns

    # Build query
    select_cols = ", ".join(col_names)
    query = f"SELECT {select_cols} FROM {table}"
    if where_clause:
        query += f" WHERE {where_clause.format(max_n=max_n)}"

    # Count rows
    count_query = f"SELECT COUNT(*) FROM {table}"
    if where_clause:
        count_query += f" WHERE {where_clause.format(max_n=max_n)}"
    pg_cur.execute(count_query)
    total = pg_cur.fetchone()[0]

    if total == 0:
        print(f"  {table}: 0 rows (skipping)")
        return 0

    print(f"  {table}: exporting {total:,} rows...", end="", flush=True)
    start = time.time()

    # Stream and insert
    pg_cur.execute(query)

    placeholders = ", ".join(["?"] * len(col_names))
    insert_sql = f"INSERT INTO {table} ({select_cols}) VALUES ({placeholders})"

    count = 0
    batch = []

    for row in pg_cur:
        converted = tuple(pg_to_sqlite_value(v, columns[i][1]) for i, v in enumerate(row))
        batch.append(converted)

        if len(batch) >= batch_size:
            sqlite_cur.executemany(insert_sql, batch)
            count += len(batch)
            pct = 100 * count / total
            elapsed = time.time() - start
            rate = count / elapsed if elapsed > 0 else 0
            print(f"\r  {table}: {count:,}/{total:,} ({pct:.0f}%) - {rate:.0f}/s", end="", flush=True)
            batch = []

    if batch:
        sqlite_cur.executemany(insert_sql, batch)
        count += len(batch)

    sqlite_conn.commit()
    elapsed = time.time() - start
    print(f"\r  {table}: {count:,} rows in {elapsed:.1f}s")
    return count


def verify_counts(sqlite_conn, pg_conn, max_n: int):
    """Verify row counts match."""
    pg_cur = pg_conn.cursor()
    sqlite_cur = sqlite_conn.cursor()

    print("\nVerifying counts...")
    all_match = True

    for table, where_clause in TABLES.items():
        # PostgreSQL count
        query = f"SELECT COUNT(*) FROM {table}"
        if where_clause:
            query += f" WHERE {where_clause.format(max_n=max_n)}"
        pg_cur.execute(query)
        pg_count = pg_cur.fetchone()[0]

        # SQLite count
        sqlite_cur.execute(f"SELECT COUNT(*) FROM {table}")
        sqlite_count = sqlite_cur.fetchone()[0]

        match = "✓" if pg_count == sqlite_count else "✗"
        if pg_count != sqlite_count:
            all_match = False
        print(f"  {table}: PG={pg_count:,} SQLite={sqlite_count:,} {match}")

    return all_match


def main():
    parser = argparse.ArgumentParser(description="Export PostgreSQL to SQLite")
    parser.add_argument("--output", "-o", default="smol.db", help="Output SQLite file")
    parser.add_argument("--max-n", type=int, default=10, help="Maximum n to export")
    parser.add_argument("--batch-size", type=int, default=5000, help="Batch size for inserts")
    args = parser.parse_args()

    print(f"Creating SQLite database: {args.output}")
    sqlite_conn = create_sqlite_db(args.output)

    print("Connecting to PostgreSQL...")
    pg_conn = get_pg_connection()

    print(f"\nExporting tables (max_n={args.max_n})...")
    total_rows = 0
    start = time.time()

    for table, where_clause in TABLES.items():
        total_rows += export_table(
            sqlite_conn, pg_conn, table, where_clause, args.max_n, args.batch_size
        )

    elapsed = time.time() - start
    print(f"\nExported {total_rows:,} total rows in {elapsed:.1f}s")

    if verify_counts(sqlite_conn, pg_conn, args.max_n):
        print("\n✓ Export verified successfully!")
    else:
        print("\n✗ Export verification failed!")
        sqlite_conn.close()
        pg_conn.close()
        return 1

    # Show file size
    size_mb = os.path.getsize(args.output) / (1024 * 1024)
    print(f"\nSQLite file size: {size_mb:.1f} MB")

    sqlite_conn.close()
    pg_conn.close()
    return 0


if __name__ == "__main__":
    sys.exit(main())
