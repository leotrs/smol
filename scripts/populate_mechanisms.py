#!/usr/bin/env python3
"""Populate switching_mechanisms table with detected mechanisms.

This script reads mechanism detection output files and populates the database.

Usage:
    python scripts/populate_mechanisms.py --mechanism gm --file docs/adj_n9_gm_correct.txt
    python scripts/populate_mechanisms.py --redetect gm --n 9
"""

import argparse
import json
import sys
from pathlib import Path

import networkx as nx

sys.path.insert(0, str(Path(__file__).parent.parent))

from db.database import connect
from gm_switching_proper import is_gm_switching_pair


def load_pairs_from_file(filepath):
    """Load graph pairs from file (g1,g2 format)."""
    pairs = []
    with open(filepath) as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            g1, g2 = line.split(',')
            pairs.append((g1.strip(), g2.strip()))
    return pairs


def get_graph_ids(conn, g6_list):
    """Map graph6 strings to database IDs."""
    cur = conn.cursor()
    placeholders = ','.join(['%s'] * len(g6_list))
    cur.execute(f"SELECT graph6, id FROM graphs WHERE graph6 IN ({placeholders})", g6_list)
    return dict(cur.fetchall())


def populate_gm_from_file(conn, filepath, matrix_type='adj', force=False):
    """Populate GM mechanisms from a file of detected pairs."""
    pairs = load_pairs_from_file(filepath)
    print(f"Loaded {len(pairs)} pairs from {filepath}")

    # Get all unique graph6 strings
    all_g6 = set()
    for g1, g2 in pairs:
        all_g6.add(g1)
        all_g6.add(g2)

    # Map to IDs
    g6_to_id = get_graph_ids(conn, list(all_g6))
    print(f"Mapped {len(g6_to_id)} graphs to database IDs")

    # Re-detect mechanisms to get configs
    print("Re-detecting mechanisms to extract configurations...")
    cur = conn.cursor()
    inserted = 0
    skipped = 0

    for i, (g6_1, g6_2) in enumerate(pairs, 1):
        if (i % 100) == 0:
            print(f"  Progress: {i}/{len(pairs)}")

        if g6_1 not in g6_to_id or g6_2 not in g6_to_id:
            print(f"  WARNING: Could not find IDs for {g6_1},{g6_2}")
            continue

        id1 = g6_to_id[g6_1]
        id2 = g6_to_id[g6_2]

        # Ensure id1 < id2
        if id1 > id2:
            id1, id2 = id2, id1
            g6_1, g6_2 = g6_2, g6_1

        # Check if already exists
        if not force:
            cur.execute("""
                SELECT 1 FROM switching_mechanisms
                WHERE graph1_id = %s AND graph2_id = %s
                  AND matrix_type = %s AND mechanism_type = 'gm'
            """, (id1, id2, matrix_type))
            if cur.fetchone():
                skipped += 1
                continue

        # Re-detect to get config
        G = nx.from_graph6_bytes(g6_1.encode())
        H = nx.from_graph6_bytes(g6_2.encode())

        result, switching_set, partition = is_gm_switching_pair(G, H)

        if not result:
            print(f"  WARNING: Could not re-detect GM for {g6_1},{g6_2}")
            continue

        # Build config JSON
        config = {
            "switching_set": sorted(list(switching_set)),
            "partition": [sorted(list(cell)) for cell in partition],
            "num_classes": len(partition)
        }

        # Insert
        cur.execute("""
            INSERT INTO switching_mechanisms
                (graph1_id, graph2_id, matrix_type, mechanism_type, config)
            VALUES (%s, %s, %s, 'gm', %s)
            ON CONFLICT (graph1_id, graph2_id, matrix_type, mechanism_type)
            DO UPDATE SET config = EXCLUDED.config
        """, (id1, id2, matrix_type, json.dumps(config)))

        inserted += 1

    conn.commit()
    print(f"\nInserted: {inserted}, Skipped: {skipped}")


def redetect_and_populate(conn, mechanism, n, matrix_type='adj'):
    """Re-detect mechanisms for all pairs at given n and populate."""
    print(f"Re-detecting {mechanism} mechanisms for n={n}, matrix_type={matrix_type}")

    cur = conn.cursor()

    # Get all cospectral pairs
    cur.execute("""
        SELECT cm.graph1_id, cm.graph2_id, g1.graph6, g2.graph6
        FROM cospectral_mates cm
        JOIN graphs g1 ON cm.graph1_id = g1.id
        JOIN graphs g2 ON cm.graph2_id = g2.id
        WHERE cm.matrix_type = %s AND g1.n = %s
    """, (matrix_type, n))

    pairs = cur.fetchall()
    print(f"Found {len(pairs)} pairs to check")

    inserted = 0

    for i, (id1, id2, g6_1, g6_2) in enumerate(pairs, 1):
        if (i % 100) == 0:
            print(f"  Progress: {i}/{len(pairs)} ({inserted} GM found)")

        G = nx.from_graph6_bytes(g6_1.encode())
        H = nx.from_graph6_bytes(g6_2.encode())

        if mechanism == 'gm':
            result, switching_set, partition = is_gm_switching_pair(G, H)

            if result:
                config = {
                    "switching_set": sorted(list(switching_set)),
                    "partition": [sorted(list(cell)) for cell in partition],
                    "num_classes": len(partition)
                }

                cur.execute("""
                    INSERT INTO switching_mechanisms
                        (graph1_id, graph2_id, matrix_type, mechanism_type, config)
                    VALUES (%s, %s, %s, 'gm', %s)
                    ON CONFLICT DO NOTHING
                """, (id1, id2, matrix_type, json.dumps(config)))

                inserted += 1

    conn.commit()
    print(f"Inserted {inserted} mechanisms")


def main():
    parser = argparse.ArgumentParser(description="Populate switching_mechanisms table")
    parser.add_argument("--mechanism", required=True, choices=['gm', 'nbl_2edge'])
    parser.add_argument("--file", help="File with pairs (g1,g2 format)")
    parser.add_argument("--redetect", action="store_true", help="Re-detect from scratch")
    parser.add_argument("--n", type=int, help="For --redetect, which n to process")
    parser.add_argument("--matrix", default="adj", help="Matrix type")
    parser.add_argument("--force", action="store_true", help="Overwrite existing")

    args = parser.parse_args()

    conn = connect()

    try:
        if args.redetect:
            if not args.n:
                print("ERROR: --n required with --redetect")
                return 1
            redetect_and_populate(conn, args.mechanism, args.n, args.matrix)
        elif args.file:
            populate_gm_from_file(conn, args.file, args.matrix, args.force)
        else:
            print("ERROR: Must specify --file or --redetect")
            return 1

    finally:
        conn.close()

    print("Done!")
    return 0


if __name__ == "__main__":
    sys.exit(main())
