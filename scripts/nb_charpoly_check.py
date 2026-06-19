#!/usr/bin/env python3
"""Compare exact (integer charpoly) NB cospectrality counts against the float-hash
counts, to investigate the NB discrepancy with the published reference tables.

The stored nb_spectral_hash is built from rounded floating-point eigenvalues, which
can both merge distinct spectra (false cospectral pairs) and split equal spectra.
This recomputes NB cospectrality from the exact integer non-backtracking
characteristic polynomial (Ihara-Bass + Bareiss, db.spectrum.nb_charpoly) and reports
"graphs not determined by their NB spectrum" per n for both methods.

Usage:
    uv run python scripts/nb_charpoly_check.py --min-n 4 --max-n 9 --workers 6
"""

import argparse
import sys
from collections import Counter
from pathlib import Path

import networkx as nx
import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from db.database import connect
from db.spectrum import nb_charpoly, charpoly_hash


def _charpoly_hash_for_g6(g6: str) -> str:
    G = nx.from_graph6_bytes(g6.encode())
    A = nx.to_numpy_array(G, nodelist=sorted(G.nodes()), dtype=int)
    return charpoly_hash(nb_charpoly(A))


def counts_for_n(conn, n: int, workers: int) -> tuple[int, int, int]:
    """Return (total_graphs, graphs_in_families, num_families) by exact charpoly."""
    cur = conn.cursor()
    cur.execute("SELECT graph6 FROM graphs WHERE n = %s", (n,))
    g6s = [r[0] for r in cur.fetchall()]

    if workers > 1 and len(g6s) > 1000:
        from multiprocessing import Pool
        with Pool(workers) as pool:
            hashes = pool.map(_charpoly_hash_for_g6, g6s, chunksize=2000)
    else:
        hashes = [_charpoly_hash_for_g6(g) for g in g6s]

    counts = Counter(hashes)
    in_families = sum(c for c in counts.values() if c > 1)
    families = sum(1 for c in counts.values() if c > 1)
    return len(g6s), in_families, families


def float_count_for_n(conn, n: int) -> int:
    cur = conn.cursor()
    cur.execute(
        "SELECT COALESCE(SUM(family_size), 0) FROM cospectral_families "
        "WHERE matrix_type = 'nb' AND n = %s",
        (n,),
    )
    return cur.fetchone()[0]


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--min-n", type=int, default=4)
    ap.add_argument("--max-n", type=int, default=9)
    ap.add_argument("--workers", type=int, default=6)
    args = ap.parse_args()

    conn = connect()
    print(f"{'n':>3} {'graphs':>10} {'exact_cosp':>12} {'exact_fam':>10} "
          f"{'float_cosp':>12} {'exact-float':>12}")
    print("-" * 64)
    for n in range(args.min_n, args.max_n + 1):
        total, exact_cosp, exact_fam = counts_for_n(conn, n, args.workers)
        float_cosp = float_count_for_n(conn, n)
        print(f"{n:>3} {total:>10,} {exact_cosp:>12,} {exact_fam:>10,} "
              f"{float_cosp:>12,} {exact_cosp - float_cosp:>+12,}")
    conn.close()


if __name__ == "__main__":
    main()
