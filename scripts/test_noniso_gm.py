#!/usr/bin/env python3
"""Test GM switching on pairs known to be non-isomorphic.

Strategy: Use pairs from our database (which are definitely non-isomorphic
since they come from nauty's canonical form), and see if any are GM-related.
"""

import sys
from pathlib import Path
import networkx as nx
from gm_switching_proper import is_gm_switching_pair


sys.path.insert(0, str(Path(__file__).parent.parent))
from db.database import connect


def analyze_pair(g6_1, g6_2):
    """Analyze a cospectral pair in detail."""
    G = nx.from_graph6_bytes(g6_1.encode())
    H = nx.from_graph6_bytes(g6_2.encode())

    print(f"Analyzing: {g6_1} vs {g6_2}")
    print(f"  G: {G.number_of_nodes()}v, {G.number_of_edges()}e, deg seq: {sorted([d for n,d in G.degree()], reverse=True)}")
    print(f"  H: {H.number_of_nodes()}v, {H.number_of_edges()}e, deg seq: {sorted([d for n,d in H.degree()], reverse=True)}")

    # Check isomorphism
    iso = nx.is_isomorphic(G, H)
    print(f"  Isomorphic: {iso}")

    if iso:
        print("  ERROR: These graphs are isomorphic! Shouldn't be in database as separate.")
        return False

    # Check GM switching
    print("  Checking GM switching...")
    result, switching_set, partition = is_gm_switching_pair(G, H)
    print(f"  GM switching: {result}")

    if result:
        print(f"    Switching set: {switching_set}")
        print(f"    Partition: {partition}")
        return True

    # Try reverse direction explicitly
    result_rev, switching_set_rev, partition_rev = is_gm_switching_pair(H, G)
    if result_rev:
        print(f"    GM switching (reverse): {result_rev}")
        print(f"    Switching set: {switching_set_rev}")
        print(f"    Partition: {partition_rev}")
        return True

    return False


def main():
    conn = connect()
    cur = conn.cursor()

    # Get some pairs at different sizes
    for n in [6, 7, 8]:
        print("=" * 70)
        print(f"Testing n={n} pairs")
        print("=" * 70)

        cur.execute("""
            SELECT g1.graph6, g2.graph6
            FROM cospectral_mates cm
            JOIN graphs g1 ON cm.graph1_id = g1.id
            JOIN graphs g2 ON cm.graph2_id = g2.id
            WHERE cm.matrix_type = 'adj' AND g1.n = %s
            LIMIT 50
        """, (n,))

        pairs = cur.fetchall()
        gm_count = 0

        for g6_1, g6_2 in pairs:
            if analyze_pair(g6_1, g6_2):
                gm_count += 1
                print()  # Extra line break for GM pairs

        print(f"\nGM switching pairs found: {gm_count}/{len(pairs)}")
        print()

    conn.close()


if __name__ == "__main__":
    main()
