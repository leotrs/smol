#!/usr/bin/env python3
"""Backfill exact nb/nbl spectral hashes into the live `graphs` table.

Replaces the float-eigenvalue nb/nbl hashes with exact characteristic-polynomial
hashes (the Hashimoto matrix is integer and <=90x90; NBL is rational of the same
size, so both are exactly computable, no Ihara-Bass). Resumable per n via a NULL
watermark: with --null-first the target columns are set NULL for the n range, and
work proceeds on rows whose nb hash is still NULL.

Usage:
    uv run python scripts/backfill_nb_exact.py --min-n 1 --max-n 9
    uv run python scripts/backfill_nb_exact.py --min-n 10 --max-n 10 --workers 6 --null-first
"""

import argparse
import sys
from datetime import datetime
from pathlib import Path

import networkx as nx

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from db.charpoly import exact_spectral_hash
from db.database import connect

COLS = ["nb", "nbl"]
HASH_COLS = [f"{k}_spectral_hash" for k in COLS]


def _hashes_for(args):
    gid, g6 = args
    G = nx.from_graph6_bytes(g6.encode())
    return (gid, [exact_spectral_hash(k, G) for k in COLS])


def _flush(conn, results):
    from psycopg2.extras import execute_values
    cur = conn.cursor()
    cur.execute("DROP TABLE IF EXISTS _nb_stage")
    cols_ddl = ", ".join(f"{c} char(16)" for c in HASH_COLS)
    cur.execute(f"CREATE TEMP TABLE _nb_stage (id bigint PRIMARY KEY, {cols_ddl})")
    execute_values(
        cur,
        f"INSERT INTO _nb_stage (id, {', '.join(HASH_COLS)}) VALUES %s",
        [(gid, *hashes) for gid, hashes in results],
        page_size=5000,
    )
    set_clause = ", ".join(f"{c} = s.{c}" for c in HASH_COLS)
    cur.execute(f"UPDATE graphs g SET {set_clause} FROM _nb_stage s WHERE g.id = s.id")
    cur.execute("DROP TABLE _nb_stage")
    conn.commit()


def build_for_n(conn, n, workers, batch_size, null_first):
    cur = conn.cursor()
    if null_first:
        cur.execute(f"UPDATE graphs SET {', '.join(c + ' = NULL' for c in HASH_COLS)} WHERE n = %s", (n,))
        conn.commit()
    # Resume marker: nb hash NULL means "not yet (re)computed". Edgeless graphs
    # have a genuine NULL nb spectrum; there is exactly one per n, so re-touching
    # it each run is harmless.
    cur.execute(f"SELECT id, graph6 FROM graphs WHERE n = %s AND {HASH_COLS[0]} IS NULL ORDER BY id", (n,))
    rows = cur.fetchall()
    if not rows:
        return 0

    from multiprocessing import Pool
    total = 0
    pool = Pool(workers) if workers > 1 else None
    try:
        for start in range(0, len(rows), batch_size):
            chunk = rows[start:start + batch_size]
            results = pool.map(_hashes_for, chunk, chunksize=500) if pool else [_hashes_for(r) for r in chunk]
            # edgeless graph -> nb hash None -> stays NULL (cannot use NULL watermark
            # on it, but it never forms a family, so exclude from the staged update)
            results = [r for r in results if r[1][0] is not None]
            if results:
                _flush(conn, results)
            total += len(chunk)
            ts = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            print(f"[{ts}] n={n}: {total:,}/{len(rows):,}", flush=True)
    finally:
        if pool:
            pool.close()
            pool.join()
    return total


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--min-n", type=int, default=1)
    ap.add_argument("--max-n", type=int, default=9)
    ap.add_argument("--workers", type=int, default=6)
    ap.add_argument("--batch-size", type=int, default=100000)
    ap.add_argument("--null-first", action="store_true",
                    help="NULL the nb/nbl columns for each n before filling (enables resume)")
    args = ap.parse_args()

    conn = connect()
    for n in range(args.min_n, args.max_n + 1):
        count = build_for_n(conn, n, args.workers, args.batch_size, args.null_first)
        print(f"n={n}: {count:,} graphs re-hashed (nb, nbl)", flush=True)
    conn.close()
    print("Done.")


if __name__ == "__main__":
    main()
