#!/usr/bin/env python3
"""Quantify float-hash vs exact-charpoly cospectrality, per integer matrix, at n<=9.

For each integer-valued matrix, recompute cospectrality from the exact integer
characteristic polynomial det(xI - M) (Bareiss, exact arithmetic) and compare the
"graphs not determined by their spectrum" count to the stored float-eigenvalue-hash
count. The comparison universe is exactly the graphs whose float hash is non-null
for that matrix, so any difference is purely float-vs-exact grouping.

Covers the integer matrices: adj, kirchhoff, signless, dist, distlap, distsign, ecc
(symmetric, via det(xI - M)), and nb (via the Ihara-Bass charpoly). The normalized
matrices (lap, nbl, distnorm) and yoon types are not integer matrices and need a
generalized formulation, so they are out of scope here.

Usage:
    uv run python scripts/charpoly_sweep.py --min-n 4 --max-n 9 --workers 8
"""

import argparse
import sys
from collections import Counter
from pathlib import Path

import networkx as nx
import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from db.charpoly import EASY_MATRICES, exact_spectral_hash
from db.database import connect

INTEGER_MATRICES = list(EASY_MATRICES)


def _hash_for(args):
    key, g6 = args
    G = nx.from_graph6_bytes(g6.encode())
    return exact_spectral_hash(key, G)


def exact_in_families(conn, key: str, n: int, workers: int) -> int:
    """Graphs in exact-charpoly families of size >1, over the float-non-null universe."""
    cur = conn.cursor()
    cur.execute(
        f"SELECT graph6 FROM graphs WHERE n = %s AND {key}_spectral_hash IS NOT NULL",
        (n,),
    )
    g6s = [r[0] for r in cur.fetchall()]
    if not g6s:
        return 0
    items = [(key, g) for g in g6s]
    if workers > 1 and len(items) > 1000:
        from multiprocessing import Pool
        with Pool(workers) as pool:
            hashes = pool.map(_hash_for, items, chunksize=2000)
    else:
        hashes = [_hash_for(it) for it in items]
    counts = Counter(h for h in hashes if h is not None)
    return sum(c for c in counts.values() if c > 1)


def float_in_families(conn, key: str, n: int) -> int:
    cur = conn.cursor()
    cur.execute(
        "SELECT COALESCE(SUM(family_size), 0) FROM cospectral_families "
        "WHERE matrix_type = %s AND n = %s",
        (key, n),
    )
    return cur.fetchone()[0]


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--min-n", type=int, default=4)
    ap.add_argument("--max-n", type=int, default=9)
    ap.add_argument("--workers", type=int, default=8)
    ap.add_argument("--matrices", nargs="*", default=INTEGER_MATRICES)
    args = ap.parse_args()

    conn = connect()
    print(f"{'matrix':>10} {'n':>3} {'exact':>10} {'float':>10} {'diff':>8}")
    print("-" * 46)
    for key in args.matrices:
        total_diff = 0
        for n in range(args.min_n, args.max_n + 1):
            ex = exact_in_families(conn, key, n, args.workers)
            fl = float_in_families(conn, key, n)
            total_diff += ex - fl
            flag = "" if ex == fl else "  <-- differs"
            print(f"{key:>10} {n:>3} {ex:>10,} {fl:>10,} {ex - fl:>+8,}{flag}")
        print(f"{key:>10} {'tot':>3} {'':>10} {'':>10} {total_diff:>+8,}")
        print("-" * 46)
    conn.close()


if __name__ == "__main__":
    main()
