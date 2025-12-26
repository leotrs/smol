#!/usr/bin/env python3
"""Test GM switching on real cospectral pairs from the database."""

import sys
from pathlib import Path
import networkx as nx
import numpy as np

sys.path.insert(0, str(Path(__file__).parent.parent))
from db.database import connect
from gm_switching_proper import is_gm_switching_pair


def test_database_pairs(n, sample_size=10):
    """Test GM switching on actual cospectral pairs from database."""
    conn = connect()
    cur = conn.cursor()

    cur.execute("""
        SELECT g1.graph6, g2.graph6
        FROM cospectral_mates cm
        JOIN graphs g1 ON cm.graph1_id = g1.id
        JOIN graphs g2 ON cm.graph2_id = g2.id
        WHERE cm.matrix_type = 'adj' AND g1.n = %s
        LIMIT %s
    """, (n, sample_size))

    pairs = cur.fetchall()
    conn.close()

    print(f"Testing {len(pairs)} adjacency cospectral pairs at n={n}")
    print("=" * 70)

    gm_found = 0
    for i, (g6_1, g6_2) in enumerate(pairs, 1):
        G = nx.from_graph6_bytes(g6_1.encode())
        H = nx.from_graph6_bytes(g6_2.encode())

        # Verify they're actually cospectral
        A_G = nx.adjacency_matrix(G).todense()
        A_H = nx.adjacency_matrix(H).todense()
        evals_G = sorted(np.linalg.eigvalsh(A_G))
        evals_H = sorted(np.linalg.eigvalsh(A_H))

        if not np.allclose(evals_G, evals_H, atol=1e-6):
            print(f"Pair {i}: NOT COSPECTRAL! ({g6_1}, {g6_2})")
            continue

        result, switching_set, partition = is_gm_switching_pair(G, H)

        if result:
            gm_found += 1
            print(f"Pair {i}: GM SWITCHING FOUND!")
            print(f"  G: {g6_1} ({G.number_of_edges()} edges)")
            print(f"  H: {g6_2} ({H.number_of_edges()} edges)")
            print(f"  Switching set: {switching_set}")
            print(f"  Partition: {partition}")
            print()

    print("=" * 70)
    print(f"GM switching found: {gm_found}/{len(pairs)}")


if __name__ == "__main__":
    test_database_pairs(6, 5)
    test_database_pairs(7, 10)
    test_database_pairs(8, 20)
