#!/usr/bin/env python3
"""One-off importer: load a production SQLite smol.db into local PostgreSQL.

The production database lives only as a SQLite file (the dev PostgreSQL is the
authoritative source normally, but it can be empty after a machine handover).
This rebuilds the local PostgreSQL `smol` database from that file.

It is generic: for each table it intersects the PostgreSQL columns with the
SQLite columns and converts each value based on the PostgreSQL column type
(JSON-text -> array, 0/1 -> boolean, JSON-text -> jsonb). Sparse `id` values
are preserved so switching_mechanisms graph references remain valid.

Usage:
    uv run python scripts/import_sqlite_to_pg.py --sqlite smol_prod.db
"""

import argparse
import json
import sqlite3
import sys

import psycopg2
from psycopg2.extras import execute_values, Json

# Import order respects foreign keys (graphs must exist before its referents).
TABLES = ["graphs", "cospectral_families", "switching_mechanisms", "stats_cache"]
BATCH = 5000


def pg_columns(pg, table):
    """Return [(name, data_type)] in ordinal order for a PostgreSQL table."""
    with pg.cursor() as cur:
        cur.execute(
            """
            SELECT column_name, data_type
            FROM information_schema.columns
            WHERE table_name = %s
            ORDER BY ordinal_position
            """,
            (table,),
        )
        return cur.fetchall()


def sqlite_columns(sl, table):
    return [r[1] for r in sl.execute(f"PRAGMA table_info({table})")]


def make_converter(data_type):
    """Build a value converter for a PostgreSQL column based on its type."""
    if data_type == "ARRAY":
        return lambda v: None if v is None else json.loads(v)
    if data_type == "boolean":
        return lambda v: None if v is None else bool(v)
    if data_type in ("jsonb", "json"):
        return lambda v: None if v is None else Json(json.loads(v))
    return lambda v: v


def import_table(sl, pg, table):
    pgcols = pg_columns(pg, table)
    if not pgcols:
        print(f"  {table}: no such PostgreSQL table, skipping")
        return
    slcols = set(sqlite_columns(sl, table))
    cols = [(name, dt) for name, dt in pgcols if name in slcols]
    names = [c[0] for c in cols]
    convs = [make_converter(dt) for _, dt in cols]
    skipped = sorted(slcols - set(names))
    if skipped:
        print(f"  {table}: skipping SQLite-only columns {skipped}")

    total = sl.execute(f"SELECT COUNT(*) FROM {table}").fetchone()[0]
    select = f"SELECT {', '.join(names)} FROM {table}"
    insert = f"INSERT INTO {table} ({', '.join(names)}) VALUES %s"

    cur_sl = sl.execute(select)
    done = 0
    with pg.cursor() as cur:
        while True:
            rows = cur_sl.fetchmany(BATCH)
            if not rows:
                break
            converted = [
                tuple(conv(val) for conv, val in zip(convs, row)) for row in rows
            ]
            execute_values(cur, insert, converted, page_size=BATCH)
            done += len(rows)
            print(f"  {table}: {done}/{total}", end="\r", flush=True)
    pg.commit()
    print(f"  {table}: {done}/{total} done")

    # Keep any owned sequence ahead of the imported (preserved) ids.
    if "id" not in names:
        return
    with pg.cursor() as cur:
        cur.execute(
            "SELECT pg_get_serial_sequence(%s, 'id')", (table,)
        )
        seq = cur.fetchone()[0]
        if seq:
            cur.execute(
                f"SELECT setval(%s, COALESCE((SELECT MAX(id) FROM {table}), 1))",
                (seq,),
            )
    pg.commit()


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--sqlite", default="smol_prod.db")
    ap.add_argument("--pg", default="dbname=smol")
    args = ap.parse_args()

    sl = sqlite3.connect(args.sqlite)
    pg = psycopg2.connect(args.pg)

    print(f"Importing {args.sqlite} -> PostgreSQL ({args.pg})")
    # Truncate in reverse FK order so the import is idempotent.
    with pg.cursor() as cur:
        for table in reversed(TABLES):
            cur.execute(f"TRUNCATE {table} RESTART IDENTITY CASCADE")
    pg.commit()

    for table in TABLES:
        import_table(sl, pg, table)

    sl.close()
    pg.close()
    print("Import complete.")


if __name__ == "__main__":
    sys.exit(main())
