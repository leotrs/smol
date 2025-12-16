#!/usr/bin/env python3
"""Pre-compute cospectral pairs for all matrix types.

This script populates the cospectral_pairs table with all pairs of graphs
that share the same spectrum (spectral hash) for each matrix type.

For a cospectral family of k graphs, we store C(k,2) = k*(k-1)/2 pairs.
This redundancy is intentional: it enables O(1) lookup of all cospectral
mates for any graph by querying:
    SELECT * FROM cospectral_pairs WHERE graph1_id = ? OR graph2_id = ?

Example: A family {A, B, C} with the same adjacency spectrum stores:
    (A, B, 'adj'), (A, C, 'adj'), (B, C, 'adj')

Usage:
    python scripts/compute_cospectral_pairs.py [--matrix adj|lap|nb|nbl]
"""

import argparse
import sys
from itertools import combinations

sys.path.insert(0, str(__file__).rsplit("/", 2)[0])

from db.database import connect


def compute_pairs_for_matrix(conn, matrix: str):
    """Compute cospectral pairs for a single matrix type."""
    cur = conn.cursor()
    hash_col = f"{matrix}_spectral_hash"

    # Check if already computed
    cur.execute(
        "SELECT COUNT(*) FROM cospectral_pairs WHERE matrix_type = %s", (matrix,)
    )
    existing = cur.fetchone()[0]
    if existing > 0:
        print(f"{matrix}: {existing:,} pairs already exist, skipping")
        return existing

    print(f"{matrix}: Streaming graphs ordered by hash...")

    # Stream through graphs ordered by (n, hash) to group cospectral graphs
    cur.execute(f"""
        SELECT id, n, {hash_col}
        FROM graphs
        ORDER BY n, {hash_col}, id
    """)

    pairs_buffer = []
    total_pairs = 0
    current_key = None
    current_ids = []

    def flush_group():
        """Generate pairs for current group and add to buffer."""
        nonlocal total_pairs
        if len(current_ids) > 1:
            for id1, id2 in combinations(current_ids, 2):
                pairs_buffer.append((id1, id2, matrix))
            total_pairs += len(current_ids) * (len(current_ids) - 1) // 2

    def flush_buffer():
        """Insert buffered pairs into database."""
        if not pairs_buffer:
            return
        insert_cur = conn.cursor()
        from psycopg2.extras import execute_values
        execute_values(
            insert_cur,
            "INSERT INTO cospectral_pairs (graph1_id, graph2_id, matrix_type) VALUES %s",
            pairs_buffer,
        )
        conn.commit()
        pairs_buffer.clear()

    rows_processed = 0
    for row in cur:
        graph_id, n, hash_val = row
        key = (n, hash_val)

        if key != current_key:
            flush_group()
            current_key = key
            current_ids = []

        current_ids.append(graph_id)
        rows_processed += 1

        # Flush buffer periodically
        if len(pairs_buffer) >= 100000:
            flush_buffer()
            print(f"  {matrix}: {total_pairs:,} pairs so far...")

    # Final flush
    flush_group()
    flush_buffer()

    print(f"  {matrix}: {total_pairs:,} pairs total")
    return total_pairs


def main():
    parser = argparse.ArgumentParser(description="Compute cospectral pairs")
    parser.add_argument(
        "--matrix",
        choices=["adj", "lap", "nb", "nbl"],
        help="Compute only this matrix type (default: all)",
    )
    args = parser.parse_args()

    conn = connect()

    if args.matrix:
        compute_pairs_for_matrix(conn, args.matrix)
    else:
        for matrix in ["adj", "lap", "nb", "nbl"]:
            compute_pairs_for_matrix(conn, matrix)

    conn.close()
    print("Done.")


if __name__ == "__main__":
    main()
