#!/usr/bin/env python3
"""Compute distance matrix eigenvalues for connected graphs.

Sequential computation of distance matrix spectra.
Only computes for connected graphs (sets NULL for disconnected).

Usage:
    python scripts/compute_distance.py
"""

import os
import sys
import time

import networkx as nx
import psycopg2

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from db.matrices import distance_matrix
from db.spectrum import compute_real_eigenvalues, spectral_hash_real

DATABASE_URL = os.environ.get("DATABASE_URL", "dbname=smol")


def main():
    conn = psycopg2.connect(DATABASE_URL)
    cur = conn.cursor()

    # Only process connected graphs (diameter IS NOT NULL)
    cur.execute("""
        SELECT COUNT(*)
        FROM graphs
        WHERE dist_eigenvalues IS NULL
        AND diameter IS NOT NULL
    """)
    total = cur.fetchone()[0]

    if total == 0:
        print("No connected graphs need distance matrix computation!")
        cur.close()
        conn.close()
        return

    print(f"Processing {total:,} connected graphs\n")

    # Fetch and process connected graphs one at a time
    cur.execute("""
        SELECT id, graph6
        FROM graphs
        WHERE dist_eigenvalues IS NULL
        AND diameter IS NOT NULL
        ORDER BY n, id
    """)

    processed = 0
    start_time = time.time()

    for row in cur:
        graph_id, graph6 = row

        try:
            G = nx.from_graph6_bytes(graph6.encode())
            D = distance_matrix(G)

            if D is None:
                # Disconnected graph
                eigs = None
                hash_val = None
            else:
                # Connected graph
                d_eigs = compute_real_eigenvalues(D)
                eigs = d_eigs.tolist()
                hash_val = spectral_hash_real(d_eigs)

            # Update immediately
            update_cur = conn.cursor()
            update_cur.execute(
                """
                UPDATE graphs
                SET dist_eigenvalues = %s,
                    dist_spectral_hash = %s
                WHERE id = %s
                """,
                (eigs, hash_val, graph_id)
            )
            update_cur.close()
            conn.commit()

            processed += 1
            if processed % 1000 == 0:
                elapsed = time.time() - start_time
                rate = processed / elapsed if elapsed > 0 else 0
                print(f"Progress: {processed:,}/{total:,} ({100*processed/total:.1f}%) | {rate:.0f} graphs/s", flush=True)

        except Exception as e:
            print(f"Error processing {graph_id}: {e}", flush=True)
            conn.rollback()

    elapsed = time.time() - start_time
    print(f"\nCompleted {processed:,} graphs in {elapsed:.0f}s ({processed/elapsed:.0f} graphs/s)", flush=True)

    cur.close()
    conn.close()


if __name__ == "__main__":
    main()
