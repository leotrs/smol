#!/usr/bin/env python3
"""Populate exact charpoly spectral hashes into graphs_cp (the blue-green rebuild).

Computes db.charpoly.exact_spectral_hash for every "easy" matrix and writes them
into graphs_cp via a staging table + UPDATE FROM. Live `graphs` is untouched.

Usage:
    uv run python scripts/build_charpoly_hashes.py --max-n 9 --workers 8
"""

import argparse
import sys
from pathlib import Path

import networkx as nx

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from db.charpoly import CHARPOLY_MATRICES, exact_spectral_hash
from db.database import connect

COLS = list(CHARPOLY_MATRICES)
HASH_COLS = [f"{k}_spectral_hash" for k in COLS]


def _hashes_for(args):
    gid, g6 = args
    G = nx.from_graph6_bytes(g6.encode())
    return (gid, [exact_spectral_hash(k, G) for k in COLS])


def build_for_n(conn, n: int, workers: int):
    cur = conn.cursor()
    cur.execute("SELECT id, graph6 FROM graphs_cp WHERE n = %s ORDER BY id", (n,))
    rows = cur.fetchall()
    if not rows:
        return 0

    if workers > 1 and len(rows) > 1000:
        from multiprocessing import Pool
        with Pool(workers) as pool:
            results = pool.map(_hashes_for, rows, chunksize=1000)
    else:
        results = [_hashes_for(r) for r in rows]

    from psycopg2.extras import execute_values
    cur.execute("DROP TABLE IF EXISTS _cp_stage")
    cols_ddl = ", ".join(f"{c} char(16)" for c in HASH_COLS)
    cur.execute(f"CREATE TEMP TABLE _cp_stage (id bigint PRIMARY KEY, {cols_ddl})")
    execute_values(
        cur,
        f"INSERT INTO _cp_stage (id, {', '.join(HASH_COLS)}) VALUES %s",
        [(gid, *hashes) for gid, hashes in results],
        page_size=5000,
    )
    set_clause = ", ".join(f"{c} = s.{c}" for c in HASH_COLS)
    cur.execute(
        f"UPDATE graphs_cp g SET {set_clause} FROM _cp_stage s WHERE g.id = s.id"
    )
    cur.execute("DROP TABLE _cp_stage")
    conn.commit()
    return len(rows)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--min-n", type=int, default=1)
    ap.add_argument("--max-n", type=int, default=9)
    ap.add_argument("--workers", type=int, default=8)
    args = ap.parse_args()

    conn = connect()
    for n in range(args.min_n, args.max_n + 1):
        count = build_for_n(conn, n, args.workers)
        print(f"n={n}: {count:,} graphs hashed ({len(COLS)} matrices)", flush=True)
    conn.close()
    print("Done.")


if __name__ == "__main__":
    main()
