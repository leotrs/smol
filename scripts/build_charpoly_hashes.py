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


def _flush(conn, results):
    """Stage a batch of (id, hashes) and UPDATE graphs_cp from it."""
    from psycopg2.extras import execute_values
    cur = conn.cursor()
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
    cur.execute(f"UPDATE graphs_cp g SET {set_clause} FROM _cp_stage s WHERE g.id = s.id")
    cur.execute("DROP TABLE _cp_stage")
    conn.commit()


def build_for_n(conn, n: int, workers: int, batch_size: int, shard: int, num_shards: int):
    """Compute charpoly hashes for graphs_cp at vertex count n, in id-ordered batches
    (bounded memory). Optionally restrict to a residue class of id for parallel runs."""
    cur = conn.cursor()
    where = "n = %s AND {col} IS NULL".format(col=HASH_COLS[0])
    if num_shards > 1:
        where += f" AND (id %% {int(num_shards)}) = {int(shard)}"
    cur.execute(f"SELECT id, graph6 FROM graphs_cp WHERE {where} ORDER BY id", (n,))
    rows = cur.fetchall()
    if not rows:
        return 0

    from multiprocessing import Pool
    total = 0
    pool = Pool(workers) if workers > 1 else None
    try:
        for start in range(0, len(rows), batch_size):
            chunk = rows[start:start + batch_size]
            if pool:
                results = pool.map(_hashes_for, chunk, chunksize=1000)
            else:
                results = [_hashes_for(r) for r in chunk]
            _flush(conn, results)
            total += len(chunk)
            from datetime import datetime
            ts = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            print(f"[{ts}] n={n} shard={shard}: {total:,}/{len(rows):,}", flush=True)
    finally:
        if pool:
            pool.close()
            pool.join()
    return total


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--min-n", type=int, default=1)
    ap.add_argument("--max-n", type=int, default=9)
    ap.add_argument("--workers", type=int, default=8)
    ap.add_argument("--batch-size", type=int, default=200000)
    ap.add_argument("--shard", type=int, default=0)
    ap.add_argument("--num-shards", type=int, default=1)
    args = ap.parse_args()

    conn = connect()
    for n in range(args.min_n, args.max_n + 1):
        count = build_for_n(conn, n, args.workers, args.batch_size, args.shard, args.num_shards)
        print(f"n={n}: {count:,} graphs hashed ({len(COLS)} matrices)", flush=True)
    conn.close()
    print("Done.")


if __name__ == "__main__":
    main()
