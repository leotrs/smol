#!/usr/bin/env python3
"""Export graphs from PostgreSQL to SQLite.

Usage:
    python scripts/export_to_sqlite.py --output smol.db --max-n 9
"""

import argparse
import json
import os
import sqlite3

import psycopg2

# PostgreSQL connection
PG_DATABASE_URL = os.environ.get("DATABASE_URL", "dbname=smol")


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


def array_to_json(arr):
    """Convert PostgreSQL array to JSON string."""
    if arr is None:
        return None
    return json.dumps(list(arr))


def export_graphs(sqlite_conn, pg_conn, max_n: int, batch_size: int = 1000):
    """Export graphs from PostgreSQL to SQLite."""
    pg_cur = pg_conn.cursor()

    # Get total count
    pg_cur.execute("SELECT COUNT(*) FROM graphs WHERE n <= %s", (max_n,))
    total = pg_cur.fetchone()[0]
    print(f"Exporting {total:,} graphs (n <= {max_n})...")

    # Fetch and insert in batches
    pg_cur.execute(
        """
        SELECT
            n, m, graph6,
            adj_eigenvalues, adj_spectral_hash,
            lap_eigenvalues, lap_spectral_hash,
            nb_eigenvalues_re, nb_eigenvalues_im, nb_spectral_hash,
            nbl_eigenvalues_re, nbl_eigenvalues_im, nbl_spectral_hash,
            is_bipartite, is_planar, is_regular,
            diameter, radius, girth,
            min_degree, max_degree, triangle_count,
            clique_number, chromatic_number,
            algebraic_connectivity, global_clustering, avg_local_clustering,
            avg_path_length, assortativity,
            degree_sequence, betweenness_centrality, closeness_centrality, eigenvector_centrality
        FROM graphs
        WHERE n <= %s
        ORDER BY n, id
        """,
        (max_n,),
    )

    sqlite_cur = sqlite_conn.cursor()
    count = 0
    batch = []

    for row in pg_cur:
        (
            n, m, graph6,
            adj_eig, adj_hash,
            lap_eig, lap_hash,
            nb_re, nb_im, nb_hash,
            nbl_re, nbl_im, nbl_hash,
            is_bipartite, is_planar, is_regular,
            diameter, radius, girth,
            min_degree, max_degree, triangle_count,
            clique_number, chromatic_number,
            alg_conn, global_clust, avg_local_clust,
            avg_path, assort,
            deg_seq, between, close, eigen,
        ) = row

        batch.append((
            n, m, graph6,
            array_to_json(adj_eig), adj_hash,
            array_to_json(lap_eig), lap_hash,
            array_to_json(nb_re), array_to_json(nb_im), nb_hash,
            array_to_json(nbl_re), array_to_json(nbl_im), nbl_hash,
            1 if is_bipartite else 0,
            1 if is_planar else 0,
            1 if is_regular else 0,
            diameter, radius, girth,
            min_degree, max_degree, triangle_count,
            clique_number, chromatic_number,
            alg_conn, global_clust, avg_local_clust,
            avg_path, assort,
            array_to_json(deg_seq), array_to_json(between),
            array_to_json(close), array_to_json(eigen),
        ))

        if len(batch) >= batch_size:
            insert_batch(sqlite_cur, batch)
            sqlite_conn.commit()
            count += len(batch)
            print(f"  {count:,}/{total:,} ({100*count/total:.1f}%)")
            batch = []

    if batch:
        insert_batch(sqlite_cur, batch)
        sqlite_conn.commit()
        count += len(batch)

    print(f"Exported {count:,} graphs")
    return count


def insert_batch(cursor, batch):
    """Insert batch of rows into SQLite."""
    cursor.executemany(
        """
        INSERT INTO graphs (
            n, m, graph6,
            adj_eigenvalues, adj_spectral_hash,
            lap_eigenvalues, lap_spectral_hash,
            nb_eigenvalues_re, nb_eigenvalues_im, nb_spectral_hash,
            nbl_eigenvalues_re, nbl_eigenvalues_im, nbl_spectral_hash,
            is_bipartite, is_planar, is_regular,
            diameter, radius, girth,
            min_degree, max_degree, triangle_count,
            clique_number, chromatic_number,
            algebraic_connectivity, global_clustering, avg_local_clustering,
            avg_path_length, assortativity,
            degree_sequence, betweenness_centrality, closeness_centrality, eigenvector_centrality
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """,
        batch,
    )


def export_stats(sqlite_conn, pg_conn):
    """Export stats_cache table."""
    pg_cur = pg_conn.cursor()
    pg_cur.execute("SELECT key, value FROM stats_cache")
    rows = pg_cur.fetchall()

    if rows:
        sqlite_cur = sqlite_conn.cursor()
        # Convert dict values to JSON strings for SQLite
        converted_rows = []
        for key, value in rows:
            if isinstance(value, dict):
                value = json.dumps(value)
            converted_rows.append((key, value))
        sqlite_cur.executemany(
            "INSERT OR REPLACE INTO stats_cache (key, value) VALUES (?, ?)",
            converted_rows,
        )
        sqlite_conn.commit()
        print(f"Exported {len(rows)} stats cache entries")


def verify_export(sqlite_conn, pg_conn, max_n: int):
    """Verify export by comparing counts."""
    pg_cur = pg_conn.cursor()
    sqlite_cur = sqlite_conn.cursor()

    print("\nVerifying export...")

    # Compare counts by n
    pg_cur.execute(
        "SELECT n, COUNT(*) FROM graphs WHERE n <= %s GROUP BY n ORDER BY n",
        (max_n,),
    )
    pg_counts = dict(pg_cur.fetchall())

    sqlite_cur.execute(
        "SELECT n, COUNT(*) FROM graphs GROUP BY n ORDER BY n"
    )
    sqlite_counts = dict(sqlite_cur.fetchall())

    all_match = True
    for n in sorted(set(pg_counts.keys()) | set(sqlite_counts.keys())):
        pg_count = pg_counts.get(n, 0)
        sqlite_count = sqlite_counts.get(n, 0)
        match = "✓" if pg_count == sqlite_count else "✗"
        if pg_count != sqlite_count:
            all_match = False
        print(f"  n={n}: PG={pg_count:,} SQLite={sqlite_count:,} {match}")

    # Compare a few specific graphs
    print("\nSpot-checking specific graphs...")
    sqlite_cur.execute("SELECT graph6, adj_spectral_hash, lap_spectral_hash FROM graphs LIMIT 5")
    for graph6, adj_hash, lap_hash in sqlite_cur.fetchall():
        pg_cur.execute(
            "SELECT adj_spectral_hash, lap_spectral_hash FROM graphs WHERE graph6 = %s",
            (graph6,),
        )
        pg_row = pg_cur.fetchone()
        if pg_row and pg_row[0] == adj_hash and pg_row[1] == lap_hash:
            print(f"  {graph6}: ✓")
        else:
            print(f"  {graph6}: ✗ MISMATCH")
            all_match = False

    return all_match


def main():
    parser = argparse.ArgumentParser(description="Export PostgreSQL to SQLite")
    parser.add_argument("--output", "-o", default="smol.db", help="Output SQLite file")
    parser.add_argument("--max-n", type=int, default=9, help="Maximum n to export")
    parser.add_argument("--batch-size", type=int, default=1000, help="Batch size for inserts")
    args = parser.parse_args()

    print(f"Creating SQLite database: {args.output}")
    sqlite_conn = create_sqlite_db(args.output)

    print("Connecting to PostgreSQL...")
    pg_conn = get_pg_connection()

    export_graphs(sqlite_conn, pg_conn, args.max_n, args.batch_size)
    export_stats(sqlite_conn, pg_conn)

    if verify_export(sqlite_conn, pg_conn, args.max_n):
        print("\n✓ Export verified successfully!")
    else:
        print("\n✗ Export verification failed!")
        return 1

    # Show file size
    import os
    size_mb = os.path.getsize(args.output) / (1024 * 1024)
    print(f"\nSQLite file size: {size_mb:.1f} MB")

    sqlite_conn.close()
    pg_conn.close()
    return 0


if __name__ == "__main__":
    exit(main())
