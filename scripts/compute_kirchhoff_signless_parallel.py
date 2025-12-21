#!/usr/bin/env python3
"""Parallel computation of Kirchhoff and Signless eigenvalues using Pool."""

import os
import sys
import time
import multiprocessing as mp
import psycopg2
from psycopg2.extras import execute_values
import networkx as nx
import numpy as np

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from db.spectrum import compute_real_eigenvalues, spectral_hash_real

DATABASE_URL = os.environ.get("DATABASE_URL", "dbname=smol")


def compute_both(args):
    """Compute both Kirchhoff and Signless for one graph."""
    graph_id, graph6 = args
    try:
        # Fast path: graph6 directly to adjacency matrix (skip NetworkX)
        A = nx.to_numpy_array(nx.from_graph6_bytes(graph6.encode()), dtype=np.float64)
        degrees = A.sum(axis=1)
        D = np.diag(degrees)

        # Kirchhoff: L = D - A
        L_k = D - A
        k_eigs = compute_real_eigenvalues(L_k)
        k_hash = spectral_hash_real(k_eigs)

        # Signless: Q = D + A
        Q_s = D + A
        s_eigs = compute_real_eigenvalues(Q_s)
        s_hash = spectral_hash_real(s_eigs)

        return (k_eigs.tolist(), k_hash, s_eigs.tolist(), s_hash, graph_id)
    except Exception as e:
        print(f"Error on {graph_id}: {e}", flush=True)
        return None


def fetch_batch(cursor, size=5000):
    """Fetch a batch of graphs."""
    return cursor.fetchmany(size)


if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument("--workers", type=int, default=mp.cpu_count())
    parser.add_argument("--batch", type=int, default=5000)
    args = parser.parse_args()

    print(f"Starting with {args.workers} workers...", flush=True)

    # Separate connections
    read_conn = psycopg2.connect(DATABASE_URL)
    write_conn = psycopg2.connect(DATABASE_URL)

    cur = read_conn.cursor('fetch_missing')
    cur.execute("""
        SELECT id, graph6
        FROM graphs
        WHERE kirchhoff_eigenvalues IS NULL OR signless_eigenvalues IS NULL
        ORDER BY n, id
    """)

    print("Processing...", flush=True)
    count = 0
    start = None  # Will set after first batch

    with mp.Pool(processes=args.workers) as pool:
        while True:
            # Fetch batch
            batch = fetch_batch(cur, args.batch)
            if not batch:
                break

            # Process in parallel
            results = pool.map(compute_both, batch, chunksize=100)

            # Filter out errors
            results = [r for r in results if r is not None]

            if results:
                # Batch update
                cur2 = write_conn.cursor()
                execute_values(
                    cur2,
                    """
                    UPDATE graphs AS g SET
                        kirchhoff_eigenvalues = v.k_eigs,
                        kirchhoff_spectral_hash = v.k_hash,
                        signless_eigenvalues = v.s_eigs,
                        signless_spectral_hash = v.s_hash
                    FROM (VALUES %s) AS v(k_eigs, k_hash, s_eigs, s_hash, id)
                    WHERE g.id = v.id
                    """,
                    results
                )
                cur2.close()
                write_conn.commit()

                count += len(results)

                # Start timer after first batch (excludes startup overhead)
                if start is None:
                    start = time.time()
                    print(f"  {count:,} - starting timer...", flush=True)
                else:
                    elapsed = time.time() - start
                    rate = count / elapsed
                    print(f"  {count:,} - {rate:.0f}/sec", flush=True)

    read_conn.close()
    write_conn.close()

    elapsed = time.time() - start
    print(f"Done! {count:,} graphs in {elapsed/60:.1f}m ({count/elapsed:.0f}/sec)", flush=True)
