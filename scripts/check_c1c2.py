"""Check which NBL-cospectral pairs satisfy (C1)+(C2) switch conditions."""

import networkx as nx
from itertools import combinations
from pathlib import Path


def load_pairs():
    """Load pairs from docs/78_pairs.txt."""
    path = Path(__file__).parent.parent / "docs" / "78_pairs.txt"
    pairs = []
    for line in path.read_text().strip().split("\n"):
        g1, g2 = line.strip().split(",")
        pairs.append((g1, g2))
    return pairs


def is_c1c2_switch(G, H):
    """Check if G and H are related by a (C1)+(C2) switch.

    Returns True if there exists vertices v1,w1,v2,w2 such that:
    - G has edges v1-w1, v2-w2 (but not v1-w2, v2-w1)
    - H is isomorphic to G with v1-w1,v2-w2 swapped to v1-w2,v2-w1
    - (C1) deg(v1)=deg(v2) and deg(w1)=deg(w2)
    - (C2) |ext(v1) ∩ ext(wj)| = |ext(v2) ∩ ext(wj)| for j=1,2
    """
    for e1, e2 in combinations(G.edges(), 2):
        for v1, w1 in [e1, e1[::-1]]:
            for v2, w2 in [e2, e2[::-1]]:
                if G.has_edge(v1, w2) or G.has_edge(v2, w1):
                    continue
                if G.degree(v1) != G.degree(v2) or G.degree(w1) != G.degree(w2):
                    continue
                S = {v1, v2, w1, w2}
                if len(S) != 4:
                    continue
                ext = {v: set(G.neighbors(v)) - S for v in S}
                # C2: pairwise equality, not all four equal
                if len(ext[v1] & ext[w1]) != len(ext[v2] & ext[w1]):
                    continue
                if len(ext[v1] & ext[w2]) != len(ext[v2] & ext[w2]):
                    continue
                Gp = G.copy()
                Gp.remove_edge(v1, w1)
                Gp.remove_edge(v2, w2)
                Gp.add_edge(v1, w2)
                Gp.add_edge(v2, w1)
                if nx.is_isomorphic(Gp, H):
                    return True
    return False


def check_pair(g6_1, g6_2):
    """Check if a pair satisfies (C1)+(C2) in either direction."""
    G = nx.from_graph6_bytes(g6_1.encode())
    H = nx.from_graph6_bytes(g6_2.encode())
    return is_c1c2_switch(G, H) or is_c1c2_switch(H, G)


def main():
    pairs = load_pairs()
    explained, unexplained = [], []
    for g1, g2 in pairs:
        if check_pair(g1, g2):
            explained.append((g1, g2))
        else:
            unexplained.append((g1, g2))

    print(f"Explained by (C1)+(C2): {len(explained)}")
    print(f"Unexplained: {len(unexplained)}")
    print()
    print("UNEXPLAINED:")
    for g1, g2 in unexplained:
        print(f"  {g1},{g2}")


if __name__ == "__main__":
    main()
