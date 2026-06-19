#!/usr/bin/env python3
"""Generate cospectrality tables from cospectral_families.

Produces two tables:
1. All graphs not determined by their spectrum, by n
2. Graphs with min_degree >= 2 not determined by their spectrum, by n

Usage:
    python scripts/cospectral_tables.py [--max-n 10]
"""

import argparse
import os
import sys
from pathlib import Path

import psycopg2

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from db.matrix_types import MATRIX_KEYS

PG_DATABASE_URL = os.environ.get("DATABASE_URL", "dbname=smol")


def get_conn():
    return psycopg2.connect(PG_DATABASE_URL)


def table1(conn, max_n: int) -> dict:
    """Table 1: All graphs not determined by their spectrum."""
    cur = conn.cursor()

    # Total graph counts by n
    cur.execute(
        "SELECT n, COUNT(*) FROM graphs WHERE n <= %s GROUP BY n ORDER BY n",
        (max_n,),
    )
    totals = {r[0]: r[1] for r in cur.fetchall()}

    # Cospectral counts by matrix type: sum of family sizes per n.
    results = {}
    for matrix in MATRIX_KEYS:
        cur.execute(
            """
            SELECT n, COALESCE(SUM(family_size), 0)
            FROM cospectral_families
            WHERE matrix_type = %s AND n <= %s
            GROUP BY n
            ORDER BY n
            """,
            (matrix, max_n),
        )
        results[matrix] = {r[0]: r[1] for r in cur.fetchall()}

    return {"totals": totals, "cospectral": results}


def table2(conn, max_n: int) -> dict:
    """Table 2: Graphs with min_degree >= 2 not determined by their spectrum."""
    cur = conn.cursor()

    # Total graph counts by n (min_degree >= 2)
    cur.execute(
        """SELECT n, COUNT(*) FROM graphs
           WHERE n <= %s AND min_degree >= 2
           GROUP BY n ORDER BY n""",
        (max_n,),
    )
    totals = {r[0]: r[1] for r in cur.fetchall()}

    # Cospectral counts by matrix type, restricted to md2 graphs cospectral with
    # ANOTHER md2 graph: within each family, count members with min_degree >= 2 and
    # keep only families where at least two such members remain.
    results = {}
    for matrix in MATRIX_KEYS:
        hash_col = f"{matrix}_spectral_hash"
        cur.execute(
            f"""
            WITH md2_fam AS (
                SELECT g.n AS n, COUNT(*) AS c
                FROM graphs g
                JOIN cospectral_families cf
                  ON cf.matrix_type = %s AND cf.n = g.n
                 AND cf.spectral_hash = g.{hash_col}
                WHERE g.min_degree >= 2 AND g.n <= %s
                GROUP BY g.n, g.{hash_col}
                HAVING COUNT(*) > 1
            )
            SELECT n, SUM(c) FROM md2_fam GROUP BY n ORDER BY n
            """,
            (matrix, max_n),
        )
        results[matrix] = {r[0]: r[1] for r in cur.fetchall()}

    return {"totals": totals, "cospectral": results}


def print_table(title: str, data: dict, max_n: int):
    """Print a formatted table."""
    print()
    print("=" * 98)
    print(title)
    print("=" * 98)
    print(f"{'N':>3} {'#graphs':>12} {'A':>8} {'K':>8} {'Q':>8} {'L':>8} {'Ã':>8} {'L̃':>8} {'D':>8}")
    print("-" * 98)

    totals = data["totals"]
    cospectral = data["cospectral"]

    grand_total = 0
    grand_cospec = {"adj": 0, "kirchhoff": 0, "signless": 0, "lap": 0, "nb": 0, "nbl": 0, "dist": 0}

    for n in range(1, max_n + 1):
        if n not in totals:
            continue

        total = totals[n]
        adj = cospectral["adj"].get(n, 0)
        kirchhoff = cospectral["kirchhoff"].get(n, 0)
        signless = cospectral["signless"].get(n, 0)
        lap = cospectral["lap"].get(n, 0)
        nb = cospectral["nb"].get(n, 0)
        nbl = cospectral["nbl"].get(n, 0)
        dist = cospectral["dist"].get(n, 0)

        print(f"{n:>3} {total:>12,} {adj:>8,} {kirchhoff:>8,} {signless:>8,} {lap:>8,} {nb:>8,} {nbl:>8,} {dist:>8,}")

        grand_total += total
        grand_cospec["adj"] += adj
        grand_cospec["kirchhoff"] += kirchhoff
        grand_cospec["signless"] += signless
        grand_cospec["lap"] += lap
        grand_cospec["nb"] += nb
        grand_cospec["nbl"] += nbl
        grand_cospec["dist"] += dist

    print("-" * 98)
    print(
        f"{'tot':>3} {grand_total:>12,} {grand_cospec['adj']:>8,} "
        f"{grand_cospec['kirchhoff']:>8,} {grand_cospec['signless']:>8,} "
        f"{grand_cospec['lap']:>8,} {grand_cospec['nb']:>8,} {grand_cospec['nbl']:>8,} "
        f"{grand_cospec['dist']:>8,}"
    )


def main():
    parser = argparse.ArgumentParser(description="Generate cospectrality tables")
    parser.add_argument("--max-n", type=int, default=10, help="Maximum n to include")
    args = parser.parse_args()

    conn = get_conn()

    data1 = table1(conn, args.max_n)
    print_table("TABLE 1: All graphs not determined by their spectrum", data1, args.max_n)

    data2 = table2(conn, args.max_n)
    print_table(
        "TABLE 2: Graphs with min_degree >= 2 not determined by their spectrum",
        data2,
        args.max_n,
    )

    conn.close()


if __name__ == "__main__":
    main()
