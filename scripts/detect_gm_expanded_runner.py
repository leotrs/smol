#!/usr/bin/env python3
"""Run expanded GM detector on all pairs.

Usage:
    python scripts/detect_gm_expanded_runner.py --n 8
    python scripts/detect_gm_expanded_runner.py --n 9 --sample 1000
"""

import argparse
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from db.database import connect
from gm_switching_expanded import is_gm_switching_pair
import networkx as nx


def main():
    parser = argparse.ArgumentParser(description="Detect GM switching (expanded algorithm)")
    parser.add_argument("--n", type=int, required=True)
    parser.add_argument("--sample", type=int, help="Sample size (default: all)")
    args = parser.parse_args()

    conn = connect()
    cur = conn.cursor()

    query = """
        SELECT cm.graph1_id, cm.graph2_id, g1.graph6, g2.graph6
        FROM cospectral_mates cm
        JOIN graphs g1 ON cm.graph1_id = g1.id
        JOIN graphs g2 ON cm.graph2_id = g2.id
        WHERE cm.matrix_type = 'adj' AND g1.n = %s
    """

    if args.sample:
        query += f" ORDER BY RANDOM() LIMIT {args.sample}"

    cur.execute(query, (args.n,))
    pairs = cur.fetchall()

    print(f"\nAnalyzing {len(pairs)} adjacency cospectral pairs at n={args.n} (EXPANDED)")
    print("=" * 70)

    gm_pairs = []

    for i, (id1, id2, g6_1, g6_2) in enumerate(pairs):
        if (i + 1) % 100 == 0:
            print(f"  Progress: {i+1}/{len(pairs)} pairs checked... ({len(gm_pairs)} GM found)")

        G = nx.from_graph6_bytes(g6_1.encode())
        H = nx.from_graph6_bytes(g6_2.encode())

        result, switching_set, partition = is_gm_switching_pair(G, H)

        if result:
            gm_pairs.append((g6_1, g6_2))
            print(f"  GM FOUND: {g6_1},{g6_2}")

    print("\nResults (EXPANDED):")
    print("-" * 70)
    print(f"GM switching:        {len(gm_pairs):6d} ({100*len(gm_pairs)/len(pairs):5.1f}%)")
    print(f"Non-GM:              {len(pairs)-len(gm_pairs):6d} ({100*(len(pairs)-len(gm_pairs))/len(pairs):5.1f}%)")
    print("=" * 70)

    # Write results
    docs_dir = Path(__file__).parent.parent / "docs"
    docs_dir.mkdir(exist_ok=True)

    if gm_pairs:
        filename = f"adj_n{args.n}_gm_expanded.txt"
        with open(docs_dir / filename, "w") as f:
            for g1, g2 in gm_pairs:
                f.write(f"{g1},{g2}\n")
        print(f"\nWrote GM pairs: docs/{filename}")

    conn.close()


if __name__ == "__main__":
    main()
