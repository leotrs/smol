#!/usr/bin/env python3
"""
Generate spectral graph database entries using geng.

Usage:
    python generate.py --n 8              # Generate all graphs on 8 vertices
    python generate.py --n 8 --dry-run    # Count without inserting
    python generate.py --n 1 --n 8        # Generate for n=1 through n=8
    python generate.py --n 10 --workers 8 # Use 8 parallel workers
    python generate.py --n 10 --m 18      # Generate only graphs with exactly 18 edges

Features:
    - Parallel processing by default (uses all CPU cores)
    - Resumable: skips graphs already in the database
    - Progress reporting with ETA
    - Optional edge count filter (--m)
"""

import argparse
import multiprocessing as mp
import subprocess
import sys
import time
from typing import Iterator

sys.path.insert(0, str(__file__).rsplit("/", 2)[0])

from db.graph_data import process_graph, graph_from_graph6
from db.database import connect, init_schema


def generate_graphs(n: int, m: int | None = None, connected: bool = False) -> Iterator[str]:
    """
    Generate all non-isomorphic simple graphs on n vertices using geng.

    Args:
        n: Number of vertices
        m: Exact number of edges (optional)
        connected: If True, generate only connected graphs (default: False, all graphs)

    Yields:
        graph6 strings
    """
    cmd = ["geng", "-q", str(n)]
    if connected:
        cmd.insert(2, "-c")
    if m is not None:
        cmd.append(f"{m}:{m}")

    proc = subprocess.Popen(
        cmd,
        stdout=subprocess.PIPE,
        stderr=subprocess.DEVNULL,
    )

    for line in proc.stdout:
        yield line.decode("ascii").strip()

    proc.wait()


def get_existing_graphs(conn, n: int) -> set[str]:
    """Get set of graph6 strings already in database for given n."""
    with conn.cursor() as cur:
        cur.execute("SELECT graph6 FROM graphs WHERE n = %s", (n,))
        return {row[0] for row in cur.fetchall()}


def process_single_graph(graph6_str: str) -> dict | None:
    """Process a single graph and return its record as a dict."""
    try:
        G = graph_from_graph6(graph6_str)
        record = process_graph(G, graph6_str)
        return record.to_db_tuple()
    except Exception as e:
        print(f"\nError processing {graph6_str}: {e}", file=sys.stderr)
        return None


def process_and_insert(
    n: int,
    m: int | None = None,
    batch_size: int = 1000,
    dry_run: bool = False,
    verbose: bool = True,
    workers: int | None = None,
    resume: bool = True,
) -> int:
    """
    Generate and insert all graphs for a given n (and optionally m edges).

    Args:
        n: Number of vertices
        m: Exact number of edges (optional)
        batch_size: Number of graphs to process before inserting
        dry_run: If True, process but don't insert
        verbose: Print progress
        workers: Number of parallel workers (default: CPU count)
        resume: If True, skip graphs already in database

    Returns:
        Total number of graphs processed
    """
    if workers is None:
        workers = min(6, mp.cpu_count())

    if not dry_run:
        conn = connect()
        init_schema(conn)
    else:
        conn = None

    # Label for output
    label = f"n={n}" if m is None else f"n={n},m={m}"

    # Get existing graphs for resumability
    existing = set()
    if resume and not dry_run and conn:
        if verbose:
            print(f"{label}: Checking for existing graphs...", end=" ", flush=True)
        existing = get_existing_graphs(conn, n)
        if verbose:
            if existing:
                print(f"found {len(existing):,} (will skip)")
            else:
                print("none found")

    # Collect graphs to process (filtering out existing)
    if verbose:
        print(f"{label}: Generating graph list from geng...", end=" ", flush=True)

    graphs_to_process = []
    total_generated = 0
    for graph6_str in generate_graphs(n, m=m):
        total_generated += 1
        if graph6_str not in existing:
            graphs_to_process.append(graph6_str)

    if verbose:
        print(f"{total_generated:,} total, {len(graphs_to_process):,} to process")

    if not graphs_to_process:
        if verbose:
            print(f"{label}: All graphs already in database, nothing to do")
        if conn:
            conn.close()
        return 0

    # Process in parallel
    batch = []
    total = 0
    start_time = time.time()

    if verbose:
        print(f"{label}: Processing with {workers} workers...")

    with mp.Pool(workers) as pool:
        for result in pool.imap(process_single_graph, graphs_to_process, chunksize=100):
            if result is None:
                continue

            batch.append(result)
            total += 1

            if len(batch) >= batch_size:
                if not dry_run:
                    insert_batch_tuples(conn, batch)
                batch = []

                if verbose:
                    elapsed = time.time() - start_time
                    rate = total / elapsed
                    remaining = len(graphs_to_process) - total
                    eta = remaining / rate if rate > 0 else 0
                    eta_str = format_time(eta)
                    print(
                        f"\r{label}: {total:,}/{len(graphs_to_process):,} "
                        f"({100*total/len(graphs_to_process):.1f}%) "
                        f"[{rate:.1f}/s, ETA {eta_str}]",
                        end="",
                        flush=True,
                    )

    # Insert remaining batch
    if batch and not dry_run:
        insert_batch_tuples(conn, batch)

    if verbose:
        elapsed = time.time() - start_time
        rate = total / elapsed if elapsed > 0 else 0
        print(
            f"\r{label}: {total:,} graphs completed in {format_time(elapsed)} ({rate:.1f}/s)"
            + " " * 20
        )

    if conn:
        conn.close()

    return total


def insert_batch_tuples(conn, tuples: list[tuple]) -> int:
    """Insert a batch of tuples directly into the database."""
    if not tuples:
        return 0

    from psycopg2.extras import execute_values

    sql = """
    INSERT INTO graphs (
        n, m, graph6,
        adj_eigenvalues, adj_spectral_hash,
        lap_eigenvalues, lap_spectral_hash,
        nb_eigenvalues_re, nb_eigenvalues_im, nb_spectral_hash,
        nbl_eigenvalues_re, nbl_eigenvalues_im, nbl_spectral_hash,
        is_bipartite, is_planar, is_regular,
        diameter, girth, radius,
        min_degree, max_degree, triangle_count
    ) VALUES %s
    ON CONFLICT (graph6) DO NOTHING
    """

    with conn.cursor() as cur:
        execute_values(cur, sql, tuples)
        inserted = cur.rowcount

    conn.commit()
    return inserted


def format_time(seconds: float) -> str:
    """Format seconds as human-readable string."""
    if seconds < 60:
        return f"{seconds:.0f}s"
    elif seconds < 3600:
        return f"{seconds/60:.1f}m"
    else:
        hours = int(seconds // 3600)
        mins = int((seconds % 3600) // 60)
        return f"{hours}h{mins}m"


def main():
    parser = argparse.ArgumentParser(
        description="Generate spectral graph database",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
    python generate.py --n 8              # Generate n=8
    python generate.py --n 1 --n 9        # Generate n=1 through n=9
    python generate.py --n 10 --workers 4 # Use 4 workers for n=10
    python generate.py --n 10 --no-resume # Regenerate all (ignore existing)
        """,
    )
    parser.add_argument(
        "--n",
        type=int,
        action="append",
        required=True,
        help="Number of vertices (can specify multiple times for range)",
    )
    parser.add_argument(
        "--m",
        type=int,
        default=None,
        help="Exact number of edges (optional, filters geng output)",
    )
    parser.add_argument(
        "--batch-size",
        type=int,
        default=1000,
        help="Batch size for database inserts (default: 1000)",
    )
    parser.add_argument(
        "--workers",
        type=int,
        default=None,
        help=f"Number of parallel workers (default: {min(6, mp.cpu_count())})",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Process graphs without inserting into database",
    )
    parser.add_argument(
        "--no-resume",
        action="store_true",
        help="Don't skip existing graphs (regenerate all)",
    )
    parser.add_argument(
        "--quiet",
        action="store_true",
        help="Suppress progress output",
    )

    args = parser.parse_args()

    n_values = sorted(set(args.n))
    if len(n_values) == 2:
        n_values = list(range(n_values[0], n_values[1] + 1))

    total_all = 0
    for n in n_values:
        count = process_and_insert(
            n,
            m=args.m,
            batch_size=args.batch_size,
            dry_run=args.dry_run,
            verbose=not args.quiet,
            workers=args.workers,
            resume=not args.no_resume,
        )
        total_all += count

    if not args.quiet and len(n_values) > 1:
        print(f"\nTotal: {total_all:,} graphs")


if __name__ == "__main__":
    main()
