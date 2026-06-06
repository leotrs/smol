#!/usr/bin/env python3
"""Remap switching mechanisms from a prod SQLite snapshot onto local graph ids.

Mechanism detection depends on a research script (gm_switching_proper) that is
no longer in the tree, so mechanisms cannot be re-detected here. They are
deterministic results, however, so we carry them over from the prod snapshot,
keyed by graph6 (graph ids differ after a local regenerate).

GM switching is an involution: the switching set/partition that maps G1 to G2
also maps G2 to G1, so the config is orientation-independent and we can store
the pair as (min_id, max_id) regardless of the snapshot's ordering.

Must run AFTER scripts/compute_cospectral_tables.py, because switching_mechanisms
has a foreign key into cospectral_mates.

Usage:
    uv run python scripts/remap_mechanisms.py --sqlite smol_prod.db
"""

import argparse
import json
import sqlite3
import sys

import psycopg2
from psycopg2.extras import execute_values, Json


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--sqlite", default="smol_prod.db")
    ap.add_argument("--pg", default="dbname=smol")
    args = ap.parse_args()

    sl = sqlite3.connect(args.sqlite)
    pg = psycopg2.connect(args.pg)

    with pg.cursor() as cur:
        cur.execute("SELECT graph6, id FROM graphs")
        g6_to_id = dict(cur.fetchall())

    rows = sl.execute(
        """
        SELECT g1.graph6, g2.graph6, sm.matrix_type, sm.mechanism_type, sm.config
        FROM switching_mechanisms sm
        JOIN graphs g1 ON g1.id = sm.graph1_id
        JOIN graphs g2 ON g2.id = sm.graph2_id
        """
    ).fetchall()

    out = []
    missing = 0
    for g6a, g6b, matrix_type, mechanism_type, config in rows:
        ia, ib = g6_to_id.get(g6a), g6_to_id.get(g6b)
        if ia is None or ib is None:
            missing += 1
            continue
        g1, g2 = (ia, ib) if ia < ib else (ib, ia)
        out.append((g1, g2, matrix_type, mechanism_type, Json(json.loads(config))))

    with pg.cursor() as cur:
        cur.execute("TRUNCATE switching_mechanisms")
        execute_values(
            cur,
            """
            INSERT INTO switching_mechanisms
                (graph1_id, graph2_id, matrix_type, mechanism_type, config)
            VALUES %s ON CONFLICT DO NOTHING
            """,
            out,
            page_size=5000,
        )
        inserted = cur.rowcount
    pg.commit()

    with pg.cursor() as cur:
        cur.execute("REFRESH MATERIALIZED VIEW graph_mechanism_stats")
    pg.commit()

    print(f"remapped {inserted} mechanisms ({missing} skipped: graph6 not found locally)")
    sl.close()
    pg.close()


if __name__ == "__main__":
    sys.exit(main())
