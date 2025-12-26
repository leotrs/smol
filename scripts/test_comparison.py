#!/usr/bin/env python3
"""Compare original vs expanded GM detector."""

import sys
from pathlib import Path
import networkx as nx

sys.path.insert(0, str(Path(__file__).parent.parent))
from db.database import connect
from gm_switching_proper import is_gm_switching_pair as gm_original
from gm_switching_expanded import is_gm_switching_pair as gm_expanded


def main():
    conn = connect()
    cur = conn.cursor()

    # Test on 20 n=8 pairs
    cur.execute("""
        SELECT g1.graph6, g2.graph6
        FROM cospectral_mates cm
        JOIN graphs g1 ON cm.graph1_id = g1.id
        JOIN graphs g2 ON cm.graph2_id = g2.id
        WHERE cm.matrix_type = 'adj' AND g1.n = 8
        LIMIT 20
    """)

    pairs = cur.fetchall()

    original_found = 0
    expanded_found = 0
    both_found = 0

    for i, (g6_1, g6_2) in enumerate(pairs, 1):
        G = nx.from_graph6_bytes(g6_1.encode())
        H = nx.from_graph6_bytes(g6_2.encode())

        orig_result, _, _ = gm_original(G, H)
        exp_result, _, _ = gm_expanded(G, H)

        if orig_result:
            original_found += 1
        if exp_result:
            expanded_found += 1
        if orig_result and exp_result:
            both_found += 1

        if orig_result != exp_result:
            print(f"Pair {i} ({g6_1},{g6_2}): orig={orig_result}, expanded={exp_result}")

    print(f"\nResults on 20 pairs:")
    print(f"  Original found: {original_found}")
    print(f"  Expanded found: {expanded_found}")
    print(f"  Both found: {both_found}")

    conn.close()


if __name__ == "__main__":
    main()
