#!/usr/bin/env python3
"""Backfill a matrix type's spectrum columns for existing graphs.

Registry-driven: works for any matrix type in db.matrix_types. Only updates
rows where the spectral-hash column is NULL, so it is safe to re-run and never
touches columns that are already populated.

Usage:
    uv run python scripts/backfill_matrix.py --matrix seidel
    uv run python scripts/backfill_matrix.py --matrix seidel --max-n 8
"""

import argparse
import os
import sys
from pathlib import Path

import psycopg2

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

import networkx as nx

from db.matrix_types import MATRIX_TYPES, MATRIX_KEYS
from db.spectrum import (
    compute_real_eigenvalues,
    compute_complex_eigenvalues,
    spectral_hash_real,
    spectral_hash_complex,
)


def compute_columns(mt, g6):
    """Return (eigenvalue_column_values, hash) for one graph and matrix type."""
    import numpy as np

    G = nx.from_graph6_bytes(g6.encode("ascii"))
    M = mt.builder(G)
    null = [None] * len(mt.eigenvalue_columns), None
    if M is None:  # connected-only matrix on a disconnected graph
        return null
    if mt.is_complex:
        eigs = compute_complex_eigenvalues(M)
        if mt.null_if_trivial and (eigs.size == 0 or np.allclose(eigs, 0.0)):
            return null
        return [eigs.real.tolist(), eigs.imag.tolist()], spectral_hash_complex(eigs)
    eigs = compute_real_eigenvalues(M)
    if mt.null_if_trivial and (eigs.size == 0 or np.allclose(eigs, 0.0)):
        return null
    return [eigs.tolist()], spectral_hash_real(eigs)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--matrix", required=True, choices=list(MATRIX_KEYS))
    ap.add_argument("--max-n", type=int, default=None)
    ap.add_argument("--batch-size", type=int, default=2000)
    args = ap.parse_args()

    mt = MATRIX_TYPES[args.matrix]
    set_cols = list(mt.eigenvalue_columns) + [mt.hash_column]
    set_clause = ", ".join(f"{c} = %s" for c in set_cols)

    conn = psycopg2.connect(os.environ.get("DATABASE_URL", "dbname=smol"))
    where_n = "" if args.max_n is None else f" AND n <= {int(args.max_n)}"

    with conn.cursor() as cur:
        cur.execute(
            f"SELECT COUNT(*) FROM graphs WHERE {mt.hash_column} IS NULL{where_n}"
        )
        total = cur.fetchone()[0]
    print(f"{args.matrix}: {total:,} graphs to backfill")
    if total == 0:
        return

    with conn.cursor() as read:
        read.execute(
            f"SELECT id, graph6 FROM graphs WHERE {mt.hash_column} IS NULL{where_n}"
        )
        rows = read.fetchall()

    done = 0
    batch = []
    write = conn.cursor()
    for graph_id, g6 in rows:
        values, h = compute_columns(mt, g6)
        batch.append((*values, h, graph_id))
        if len(batch) >= args.batch_size:
            write.executemany(
                f"UPDATE graphs SET {set_clause} WHERE id = %s", batch
            )
            conn.commit()
            done += len(batch)
            print(f"  {done:,}/{total:,}", end="\r", flush=True)
            batch = []
    if batch:
        write.executemany(f"UPDATE graphs SET {set_clause} WHERE id = %s", batch)
        conn.commit()
        done += len(batch)
    print(f"  {done:,}/{total:,} done")
    conn.close()


if __name__ == "__main__":
    sys.exit(main())
