#!/usr/bin/env python3
"""Populate the cospectral_families table for all matrix types.

For each matrix type, groups graphs by (n, spectral_hash) and records one row per
family of size >= 2. This is O(#families), unlike the old per-pair table which was
O(sum C(k,2)) and exploded for weak discriminators (ecc reaches families of 8000+).

Family membership is recovered at query time via the idx_n_<matrix>_hash indexes on
graphs, so the family hash column used here MUST match the one the API derives mates
from (<matrix>_spectral_hash). The exact-charpoly NB improvement is tracked separately
and would change that column for nb consistently across the API and this script.

Usage:
    python scripts/compute_cospectral_tables.py           # All matrix types, all n
    python scripts/compute_cospectral_tables.py --n 9     # All matrix types, only n=9
    python scripts/compute_cospectral_tables.py --matrix adj --n 10  # adj only, n=10
"""

import argparse
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from db.database import connect
from db.matrix_types import MATRIX_KEYS


def compute_for_matrix(conn, matrix: str, n_filter: int | None = None):
    """Populate cospectral_families for a single matrix type."""
    cur = conn.cursor()
    hash_col = f"{matrix}_spectral_hash"
    label = f"{matrix}" if n_filter is None else f"{matrix} (n={n_filter})"

    # Skip if already populated for this scope
    if n_filter is not None:
        cur.execute(
            "SELECT COUNT(*) FROM cospectral_families WHERE matrix_type = %s AND n = %s",
            (matrix, n_filter),
        )
    else:
        cur.execute(
            "SELECT COUNT(*) FROM cospectral_families WHERE matrix_type = %s", (matrix,)
        )
    existing = cur.fetchone()[0]
    if existing > 0:
        print(f"{label}: {existing:,} families already exist, skipping")
        return

    print(f"{label}: aggregating families...")

    # A single grouped INSERT does all the work: families of size >= 2 keyed by
    # (n, hash). NULL hashes (disconnected/undefined graphs) are excluded.
    where_n = "" if n_filter is None else " AND n = %s"
    params = (matrix,) if n_filter is None else (matrix, n_filter)
    cur.execute(
        f"""
        INSERT INTO cospectral_families (matrix_type, n, spectral_hash, family_size)
        SELECT %s, n, {hash_col}, COUNT(*)
        FROM graphs
        WHERE {hash_col} IS NOT NULL{where_n}
        GROUP BY n, {hash_col}
        HAVING COUNT(*) > 1
        ON CONFLICT (matrix_type, n, spectral_hash) DO NOTHING
        """,
        params,
    )
    inserted = cur.rowcount
    conn.commit()

    cur.execute(
        "SELECT COALESCE(SUM(family_size), 0) FROM cospectral_families WHERE matrix_type = %s"
        + ("" if n_filter is None else " AND n = %s"),
        params,
    )
    graphs_in_families = cur.fetchone()[0]
    print(f"  {label}: {inserted:,} families, {graphs_in_families:,} graphs total")


def main():
    parser = argparse.ArgumentParser(description="Populate cospectral_families")
    parser.add_argument(
        "--matrix",
        choices=list(MATRIX_KEYS),
        help="Compute only this matrix type (default: all)",
    )
    parser.add_argument(
        "--n",
        type=int,
        help="Compute only for this vertex count (default: all)",
    )
    args = parser.parse_args()

    conn = connect()

    if args.matrix:
        compute_for_matrix(conn, args.matrix, args.n)
    else:
        for matrix in MATRIX_KEYS:
            compute_for_matrix(conn, matrix, args.n)

    conn.close()
    print("Done.")


if __name__ == "__main__":
    main()
