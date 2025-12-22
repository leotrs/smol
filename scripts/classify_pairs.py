"""Classify NBL-cospectral pairs by which theorem explains them."""

import networkx as nx
from itertools import combinations
from pathlib import Path


def load_pairs():
    path = Path(__file__).parent.parent / "docs" / "78_pairs.txt"
    pairs = []
    for line in path.read_text().strip().split("\n"):
        g1, g2 = line.strip().split(",")
        pairs.append((g1, g2))
    return pairs


def is_c1c2_switch(G, H):
    """Check 2-edge (C1)+(C2) switch."""
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


def is_bipartite_swap(G, H, k=2):
    """Check k-edge bipartite swap (C1')+(C2')+(C3')."""
    nodes = list(G.nodes())
    # Try all pairs of hubs
    for h1, h2 in combinations(nodes, 2):
        # Find potential leaves: vertices adjacent to exactly one hub
        L1_candidates = [v for v in nodes if v not in {h1, h2} and G.has_edge(v, h1) and not G.has_edge(v, h2)]
        L2_candidates = [v for v in nodes if v not in {h1, h2} and G.has_edge(v, h2) and not G.has_edge(v, h1)]
        
        if len(L1_candidates) < k or len(L2_candidates) < k:
            continue
        
        # Try all k-subsets
        for L1 in combinations(L1_candidates, k):
            for L2 in combinations(L2_candidates, k):
                L1, L2 = set(L1), set(L2)
                S = {h1, h2} | L1 | L2
                
                # C1': hub degrees equal, all leaves equal degree
                if G.degree(h1) != G.degree(h2):
                    continue
                leaf_degs = [G.degree(leaf) for leaf in L1 | L2]
                if len(set(leaf_degs)) != 1:
                    continue

                # C2': aggregate cross-intersection balanced
                ext = {v: set(G.neighbors(v)) - S for v in S}
                gamma_1j = [sum(len(ext[leaf] & ext[hj]) for leaf in L1) for hj in [h1, h2]]
                gamma_2j = [sum(len(ext[leaf] & ext[hj]) for leaf in L2) for hj in [h1, h2]]
                if gamma_1j[0] != gamma_2j[0] or gamma_1j[1] != gamma_2j[1]:
                    continue

                # C3': |L1| = |L2| (already ensured by k)

                # Apply swap and check isomorphism
                Gp = G.copy()
                for leaf in L1:
                    Gp.remove_edge(leaf, h1)
                    Gp.add_edge(leaf, h2)
                for leaf in L2:
                    Gp.remove_edge(leaf, h2)
                    Gp.add_edge(leaf, h1)
                if nx.is_isomorphic(Gp, H):
                    return True
    return False


def check_c1c2(g6_1, g6_2):
    G = nx.from_graph6_bytes(g6_1.encode())
    H = nx.from_graph6_bytes(g6_2.encode())
    return is_c1c2_switch(G, H) or is_c1c2_switch(H, G)


def check_bipartite_swap(g6_1, g6_2, k=2):
    G = nx.from_graph6_bytes(g6_1.encode())
    H = nx.from_graph6_bytes(g6_2.encode())
    return is_bipartite_swap(G, H, k) or is_bipartite_swap(H, G, k)


def main():
    pairs = load_pairs()
    c1c2_pairs = []
    bipartite_pairs = []
    unexplained = []
    
    for g1, g2 in pairs:
        if check_c1c2(g1, g2):
            c1c2_pairs.append((g1, g2))
        elif check_bipartite_swap(g1, g2, k=2):
            bipartite_pairs.append((g1, g2))
        else:
            unexplained.append((g1, g2))
    
    print(f"C1+C2 (2-edge): {len(c1c2_pairs)}")
    print(f"C1'+C2'+C3' k=2 (4-edge): {len(bipartite_pairs)}")
    print(f"Unexplained: {len(unexplained)}")
    
    # Write files
    docs = Path(__file__).parent.parent / "docs"
    
    with open(docs / "pairs_c1c2.txt", "w") as f:
        for g1, g2 in c1c2_pairs:
            f.write(f"{g1},{g2}\n")
    
    with open(docs / "pairs_bipartite_swap.txt", "w") as f:
        for g1, g2 in bipartite_pairs:
            f.write(f"{g1},{g2}\n")
    
    with open(docs / "pairs_unexplained.txt", "w") as f:
        for g1, g2 in unexplained:
            f.write(f"{g1},{g2}\n")
    
    print("\nWrote: docs/pairs_c1c2.txt, docs/pairs_bipartite_swap.txt, docs/pairs_unexplained.txt")


if __name__ == "__main__":
    main()
