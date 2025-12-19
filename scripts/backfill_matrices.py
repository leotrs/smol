#!/usr/bin/env python3
"""Backfill Kirchhoff and Signless Laplacian matrices for existing graphs.

This script computes and updates the new matrix eigenvalues for graphs that don't have them yet.
"""

import psycopg2
import psycopg2.extras

from db.graph_data import graph_from_graph6
from db.matrices import kirchhoff_laplacian, signless_laplacian
from db.spectrum import compute_real_eigenvalues, spectral_hash_real

DATABASE_URL = "dbname=smol"


def backfill(max_n: int = 8):
    """Backfill Kirchhoff and Signless Laplacian eigenvalues for graphs up to n=max_n."""
    conn = psycopg2.connect(DATABASE_URL)
    cur = conn.cursor(cursor_factory=psycopg2.extras.DictCursor)

    try:
        # Count graphs needing backfill
        cur.execute("""
            SELECT COUNT(*)
            FROM graphs
            WHERE n <= %s AND kirchhoff_eigenvalues IS NULL
        """, (max_n,))
        total = cur.fetchone()[0]

        print(f"Graphs with n ≤ {max_n} needing backfill: {total:,}")

        if total == 0:
            print("No graphs need backfilling.")
            return

        # Fetch graphs needing backfill
        cur.execute("""
            SELECT id, graph6
            FROM graphs
            WHERE n <= %s AND kirchhoff_eigenvalues IS NULL
            ORDER BY n, id
        """, (max_n,))

        rows = cur.fetchall()
        print(f"Processing {len(rows):,} graphs...")

        # Process in batches
        batch_size = 1000
        update_cur = conn.cursor()

        for i in range(0, len(rows), batch_size):
            batch = rows[i:i + batch_size]
            batch_num = i // batch_size + 1
            total_batches = (len(rows) + batch_size - 1) // batch_size
            print(f"Processing batch {batch_num}/{total_batches}...", flush=True)

            for row in batch:
                graph_id = row['id']
                graph6 = row['graph6']

                # Reconstruct graph
                G = graph_from_graph6(graph6)

                # Compute matrices and eigenvalues
                L_kirchhoff = kirchhoff_laplacian(G)
                Q_signless = signless_laplacian(G)

                kirchhoff_eigs = compute_real_eigenvalues(L_kirchhoff)
                signless_eigs = compute_real_eigenvalues(Q_signless)

                kirchhoff_hash = spectral_hash_real(kirchhoff_eigs)
                signless_hash = spectral_hash_real(signless_eigs)

                # Update database
                update_cur.execute("""
                    UPDATE graphs
                    SET kirchhoff_eigenvalues = %s,
                        kirchhoff_spectral_hash = %s,
                        signless_eigenvalues = %s,
                        signless_spectral_hash = %s
                    WHERE id = %s
                """, (
                    kirchhoff_eigs.tolist(),
                    kirchhoff_hash,
                    signless_eigs.tolist(),
                    signless_hash,
                    graph_id,
                ))

            conn.commit()

        update_cur.close()

        # Verify completion
        cur.execute("""
            SELECT
                COUNT(*) as total,
                COUNT(kirchhoff_eigenvalues) as kirchhoff_filled,
                COUNT(signless_eigenvalues) as signless_filled
            FROM graphs
            WHERE n <= %s
        """, (max_n,))
        result = cur.fetchone()

        print(f"\nBackfill complete for n ≤ {max_n}:")
        print(f"  Total graphs: {result['total']:,}")
        print(f"  Kirchhoff filled: {result['kirchhoff_filled']:,}")
        print(f"  Signless filled: {result['signless_filled']:,}")

        if result['total'] == result['kirchhoff_filled'] == result['signless_filled']:
            print("  ✓ All graphs backfilled successfully")
        else:
            missing = result['total'] - result['kirchhoff_filled']
            print(f"  ⚠ {missing:,} graphs still need backfilling")

    finally:
        cur.close()
        conn.close()


if __name__ == "__main__":
    import sys
    max_n = int(sys.argv[1]) if len(sys.argv) > 1 else 8
    backfill(max_n)
