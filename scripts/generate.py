#!/usr/bin/env python3
"""
Generate spectral graph database entries using geng.

Usage:
    python generate.py --n 8              # Generate all connected graphs on 8 vertices
    python generate.py --n 8 --dry-run    # Count without inserting
    python generate.py --n 1 --n 8        # Generate for n=1 through n=8
"""

import argparse
import subprocess
import sys
import time
from typing import Iterator


# Add parent directory to path for imports
sys.path.insert(0, str(__file__).rsplit("/", 2)[0])

from db.graph_data import process_graph, graph_from_graph6
from db.database import get_connection, init_schema, insert_batch


def generate_graphs(
    n: int, min_edges: int | None = None, max_edges: int | None = None
) -> Iterator[str]:
    """
    Generate all connected graphs on n vertices using geng.

    Args:
        n: Number of vertices
        min_edges: Minimum number of edges (optional, for parallelization)
        max_edges: Maximum number of edges (optional, for parallelization)

    Yields:
        graph6 strings
    """
    cmd = ["geng", "-c", str(n)]

    if min_edges is not None and max_edges is not None:
        cmd.append(f"{min_edges}:{max_edges}")
    elif min_edges is not None:
        cmd.append(f"{min_edges}:")
    elif max_edges is not None:
        cmd.append(f":{max_edges}")

    proc = subprocess.Popen(
        cmd,
        stdout=subprocess.PIPE,
        stderr=subprocess.DEVNULL,
    )

    for line in proc.stdout:
        yield line.decode("ascii").strip()

    proc.wait()


def process_and_insert(
    n: int,
    batch_size: int = 1000,
    dry_run: bool = False,
    verbose: bool = True,
) -> int:
    """
    Generate and insert all graphs for a given n.

    Args:
        n: Number of vertices
        batch_size: Number of graphs to process before inserting
        dry_run: If True, process but don't insert
        verbose: Print progress

    Returns:
        Total number of graphs processed
    """
    if not dry_run:
        conn = get_connection().__enter__()
        init_schema(conn)
    else:
        conn = None

    batch = []
    total = 0
    start_time = time.time()

    for graph6_str in generate_graphs(n):
        try:
            G = graph_from_graph6(graph6_str)
            record = process_graph(G, graph6_str)
            batch.append(record)
            total += 1

            if len(batch) >= batch_size:
                if not dry_run:
                    insert_batch(conn, batch)
                batch = []

                if verbose:
                    elapsed = time.time() - start_time
                    rate = total / elapsed
                    print(
                        f"\rn={n}: {total:,} graphs ({rate:.1f}/s)", end="", flush=True
                    )

        except Exception as e:
            print(f"\nError processing {graph6_str}: {e}", file=sys.stderr)
            continue

    # Insert remaining batch
    if batch and not dry_run:
        insert_batch(conn, batch)

    if verbose:
        elapsed = time.time() - start_time
        rate = total / elapsed if elapsed > 0 else 0
        print(f"\rn={n}: {total:,} graphs completed in {elapsed:.1f}s ({rate:.1f}/s)")

    if conn:
        conn.close()

    return total


def main():
    parser = argparse.ArgumentParser(description="Generate spectral graph database")
    parser.add_argument(
        "--n",
        type=int,
        action="append",
        required=True,
        help="Number of vertices (can specify multiple times for range)",
    )
    parser.add_argument(
        "--batch-size",
        type=int,
        default=1000,
        help="Batch size for database inserts",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Process graphs without inserting into database",
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
            batch_size=args.batch_size,
            dry_run=args.dry_run,
            verbose=not args.quiet,
        )
        total_all += count

    if not args.quiet:
        print(f"\nTotal: {total_all:,} graphs")


if __name__ == "__main__":
    main()
