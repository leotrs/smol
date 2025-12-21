#!/usr/bin/env python3
"""Compute Kirchhoff and Signless eigenvalues for graphs missing them.

Parallel, resumable computation of missing Kirchhoff and Signless Laplacian spectra.

Usage:
    python scripts/compute_kirchhoff_signless.py --workers 8
    python scripts/compute_kirchhoff_signless.py --batch-size 500
"""

import argparse
import multiprocessing as mp
import os
import sys
import time
from typing import Iterator

import networkx as nx
import psycopg2
from psycopg2.extras import execute_values

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from db.matrices import kirchhoff_laplacian, signless_laplacian
from db.spectrum import compute_real_eigenvalues, spectral_hash_real

DATABASE_URL = os.environ.get("DATABASE_URL", "dbname=smol")


def get_missing_graphs() -> Iterator[tuple[int, str]]:
    """Yield (id, graph6) for all graphs missing Kirchhoff/Signless."""
    print("Fetching graphs from database...", flush=True)
    conn = psycopg2.connect(DATABASE_URL)
    cur = conn.cursor(name='fetch_missing')
    cur.itersize = 10000

    cur.execute("""
        SELECT id, graph6
        FROM graphs
        WHERE kirchhoff_eigenvalues IS NULL OR signless_eigenvalues IS NULL
        ORDER BY n, id
    """)

    print("Starting to yield graphs...", flush=True)
    count = 0
    for row in cur:
        count += 1
        if count % 10000 == 0:
            print(f"  Fetched {count:,} tasks...", flush=True)
        yield row

    print(f"Finished fetching {count:,} graphs", flush=True)
    cur.close()
    conn.close()


def process_graph(graph_id: int, graph6: str) -> tuple:
    """Compute Kirchhoff and Signless for a single graph."""
    try:
        G = nx.from_graph6_bytes(graph6.encode())

        # Kirchhoff Laplacian
        L_k = kirchhoff_laplacian(G)
        k_eigs = compute_real_eigenvalues(L_k)
        k_hash = spectral_hash_real(k_eigs)

        # Signless Laplacian
        Q_s = signless_laplacian(G)
        s_eigs = compute_real_eigenvalues(Q_s)
        s_hash = spectral_hash_real(s_eigs)

        return (k_eigs.tolist(), k_hash, s_eigs.tolist(), s_hash, graph_id)
    except Exception as e:
        print(f"Error processing {graph_id}: {e}")
        return None


def worker_process(task_queue: mp.Queue, result_queue: mp.Queue):
    """Worker process that consumes tasks and produces results."""
    while True:
        item = task_queue.get()
        if item is None:
            break

        graph_id, graph6 = item
        result = process_graph(graph_id, graph6)
        if result:
            result_queue.put(result)


def producer_process(task_queue: mp.Queue, num_workers: int):
    """Producer process that feeds tasks to workers."""
    for graph_id, graph6 in get_missing_graphs():
        task_queue.put((graph_id, graph6))
    # Send stop signals
    for _ in range(num_workers):
        task_queue.put(None)


def update_batch(conn, updates: list):
    """Batch update graphs with Kirchhoff and Signless eigenvalues."""
    cur = conn.cursor()
    execute_values(
        cur,
        """
        UPDATE graphs AS g SET
            kirchhoff_eigenvalues = v.kirchhoff_eigenvalues,
            kirchhoff_spectral_hash = v.kirchhoff_spectral_hash,
            signless_eigenvalues = v.signless_eigenvalues,
            signless_spectral_hash = v.signless_spectral_hash
        FROM (VALUES %s) AS v(
            kirchhoff_eigenvalues, kirchhoff_spectral_hash,
            signless_eigenvalues, signless_spectral_hash, id
        )
        WHERE g.id = v.id
        """,
        updates
    )
    conn.commit()


def main():
    parser = argparse.ArgumentParser(description="Compute Kirchhoff and Signless eigenvalues")
    parser.add_argument("--workers", type=int, default=mp.cpu_count(), help="Number of parallel workers")
    parser.add_argument("--batch-size", type=int, default=1000, help="Batch size for database updates")
    args = parser.parse_args()

    print(f"Starting computation with {args.workers} workers...", flush=True)

    # Don't count - just start processing
    conn = psycopg2.connect(DATABASE_URL)

    # Setup queues
    task_queue = mp.Queue(maxsize=args.workers * 2)
    result_queue = mp.Queue()

    # Start workers
    workers = []
    for _ in range(args.workers):
        p = mp.Process(target=worker_process, args=(task_queue, result_queue))
        p.start()
        workers.append(p)

    # Producer process - feed tasks
    producer_thread = mp.Process(target=producer_process, args=(task_queue, args.workers))
    producer_thread.start()

    # Consumer - collect results and batch update
    updates = []
    processed = 0
    start_time = time.time()
    last_report = start_time

    print("Processing graphs...", flush=True)

    while True:
        try:
            result = result_queue.get(timeout=1)
            updates.append(result)
            processed += 1

            # Batch update
            if len(updates) >= args.batch_size:
                update_batch(conn, updates)
                updates = []

            # Progress report every 5 seconds
            now = time.time()
            if now - last_report >= 5:
                elapsed = now - start_time
                rate = processed / elapsed if elapsed > 0 else 0
                print(f"  {processed:,} graphs - {rate:.0f} graphs/sec", flush=True)
                last_report = now

        except Exception:
            # Check if workers are done
            if all(not w.is_alive() for w in workers):
                break

    # Final batch
    if updates:
        update_batch(conn, updates)

    # Cleanup
    producer_thread.join()
    for w in workers:
        w.join()

    conn.close()

    elapsed = time.time() - start_time
    rate = processed / elapsed if elapsed > 0 else 0
    print(f"\nDone! Processed {processed:,} graphs in {elapsed/60:.1f}m ({rate:.0f} graphs/sec)", flush=True)


if __name__ == "__main__":
    main()
