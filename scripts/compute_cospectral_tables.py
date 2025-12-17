#!/usr/bin/env python3
"""Pre-compute cospectral tables for all matrix types.

This script populates two tables:

1. cospectral_mates: All pairs of graphs sharing the same spectrum.
   For a cospectral family of k graphs, stores C(k,2) = k*(k-1)/2 pairs.
   Enables O(1) lookup of cospectral mates for any graph.

2. cospectral_index: One row per graph that has at least one cospectral mate.
   Denormalizes n, m, min_degree for instant aggregate queries like:
   - Count of graphs with cospectral mates by n
   - Count of graphs with cospectral mates by m
   - Same counts filtered by min_degree >= 2

Usage:
    python scripts/compute_cospectral_tables.py [--matrix adj|lap|nb|nbl] [--n N]

Examples:
    python scripts/compute_cospectral_tables.py           # All matrix types, all n
    python scripts/compute_cospectral_tables.py --n 9     # All matrix types, only n=9
    python scripts/compute_cospectral_tables.py --matrix adj --n 10  # adj only, n=10
"""

import argparse
import sys
from itertools import combinations

sys.path.insert(0, str(__file__).rsplit("/", 2)[0])

from db.database import connect


def compute_for_matrix(conn, matrix: str, n_filter: int | None = None):
    """Compute cospectral_mates and cospectral_index for a single matrix type."""
    cur = conn.cursor()
    hash_col = f"{matrix}_spectral_hash"
    label = f"{matrix}" if n_filter is None else f"{matrix} (n={n_filter})"

    # Check if already computed for this n
    if n_filter is not None:
        cur.execute(
            "SELECT COUNT(*) FROM cospectral_index WHERE matrix_type = %s AND n = %s",
            (matrix, n_filter),
        )
    else:
        cur.execute(
            "SELECT COUNT(*) FROM cospectral_mates WHERE matrix_type = %s", (matrix,)
        )
    existing = cur.fetchone()[0]
    if existing > 0:
        print(f"{label}: {existing:,} entries already exist, skipping")
        return

    print(f"{label}: Streaming graphs ordered by hash...")

    # Stream through graphs ordered by (n, hash) to group cospectral graphs
    if n_filter is not None:
        cur.execute(f"""
            SELECT id, n, m, min_degree, {hash_col}
            FROM graphs
            WHERE n = %s
            ORDER BY {hash_col}, id
        """, (n_filter,))
    else:
        cur.execute(f"""
            SELECT id, n, m, min_degree, {hash_col}
            FROM graphs
            ORDER BY n, {hash_col}, id
        """)

    mates_buffer = []
    index_buffer = []
    total_pairs = 0
    total_graphs = 0
    current_key = None
    current_group = []  # list of (id, n, m, min_degree)

    def flush_group():
        """Generate pairs and index entries for current group."""
        nonlocal total_pairs, total_graphs
        if len(current_group) > 1:
            # Add to cospectral_index (one row per graph)
            for gid, n, m, min_deg in current_group:
                index_buffer.append((gid, n, m, min_deg, matrix))
            total_graphs += len(current_group)

            # Add to cospectral_mates (all pairs)
            for (id1, _, _, _), (id2, _, _, _) in combinations(current_group, 2):
                mates_buffer.append((id1, id2, matrix))
            total_pairs += len(current_group) * (len(current_group) - 1) // 2

    def flush_buffers():
        """Insert buffered data into database."""
        if mates_buffer:
            from psycopg2.extras import execute_values
            insert_cur = conn.cursor()
            execute_values(
                insert_cur,
                "INSERT INTO cospectral_mates (graph1_id, graph2_id, matrix_type) VALUES %s",
                mates_buffer,
            )
            mates_buffer.clear()

        if index_buffer:
            from psycopg2.extras import execute_values
            insert_cur = conn.cursor()
            execute_values(
                insert_cur,
                "INSERT INTO cospectral_index (graph_id, n, m, min_degree, matrix_type) VALUES %s",
                index_buffer,
            )
            index_buffer.clear()

        conn.commit()

    for row in cur:
        graph_id, n, m, min_degree, hash_val = row
        key = (n, hash_val)

        if key != current_key:
            flush_group()
            current_key = key
            current_group = []

        current_group.append((graph_id, n, m, min_degree))

        # Flush buffers periodically
        if len(mates_buffer) >= 100000:
            flush_buffers()
            print(f"  {label}: {total_pairs:,} pairs, {total_graphs:,} graphs so far...")

    # Final flush
    flush_group()
    flush_buffers()

    print(f"  {label}: {total_pairs:,} pairs, {total_graphs:,} graphs total")


def main():
    parser = argparse.ArgumentParser(description="Compute cospectral tables")
    parser.add_argument(
        "--matrix",
        choices=["adj", "lap", "nb", "nbl"],
        help="Compute only this matrix type (default: all)",
    )
    parser.add_argument(
        "--n",
        type=int,
        help="Compute only for this vertex count (default: all)",
    )
    args = parser.parse_args()

    conn = connect()

    if args.matrix:
        compute_for_matrix(conn, args.matrix, args.n)
    else:
        for matrix in ["adj", "lap", "nb", "nbl"]:
            compute_for_matrix(conn, matrix, args.n)

    conn.close()
    print("Done.")


if __name__ == "__main__":
    main()
