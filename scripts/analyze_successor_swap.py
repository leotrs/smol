#!/usr/bin/env python3
"""Analyze successor set swapping in non-isomorphic cospectral switches."""

import networkx as nx
import numpy as np


def build_hashimoto(G):
    """Build Hashimoto graph on directed edges."""
    directed_edges = []
    for u, v in G.edges():
        directed_edges.append((u, v))
        directed_edges.append((v, u))

    H = nx.DiGraph()
    for e in directed_edges:
        H.add_node(e)

    for e1 in directed_edges:
        u, v = e1
        for w in G.neighbors(v):
            if w != u:
                e2 = (v, w)
                H.add_edge(e1, e2)

    return H, directed_edges


def get_successors(G, e):
    """Get successor edges in Hashimoto graph."""
    u, v = e
    return frozenset((v, w) for w in G.neighbors(v) if w != u)


def analyze_switch(G1, v1, v2, w1, w2):
    """Analyze a switch in detail."""
    G2 = G1.copy()
    G2.remove_edge(v1, w1)
    G2.remove_edge(v2, w2)
    G2.add_edge(v1, w2)
    G2.add_edge(v2, w1)

    print(f"\nSwitch: v1={v1}, v2={v2}, w1={w1}, w2={w2}")
    print("=" * 60)

    # Switch edges
    switch_G1 = [(v1, w1), (w1, v1), (v2, w2), (w2, v2)]
    switch_G2 = [(v1, w2), (w2, v1), (v2, w1), (w1, v2)]

    print("\nSuccessor analysis (targets of outgoing Hashimoto edges):")
    print("-" * 60)

    # For each G1 switch edge, find its successors
    # Then see which G2 switch edge has the same successors (if any)
    print("\nG1 switch edges and their successors:")
    for e in switch_G1:
        succ = get_successors(G1, e)
        targets = {s[1] for s in succ}  # Just the target vertices
        print(f"  {e} -> targets {targets}")

    print("\nG2 switch edges and their successors:")
    for e in switch_G2:
        succ = get_successors(G2, e)
        targets = {s[1] for s in succ}
        print(f"  {e} -> targets {targets}")

    # Check if there's a perfect matching of successor sets
    print("\nSuccessor set matching:")
    g1_succs = {e: get_successors(G1, e) for e in switch_G1}
    g2_succs = {e: get_successors(G2, e) for e in switch_G2}

    # For each G1 edge, which G2 edge has matching successors?
    for e1 in switch_G1:
        s1 = g1_succs[e1]
        # Convert to target vertices for comparison (since edge labels differ)
        t1 = frozenset(s[1] for s in s1)
        matches = []
        for e2 in switch_G2:
            s2 = g2_succs[e2]
            t2 = frozenset(s[1] for s in s2)
            if t1 == t2:
                matches.append(e2)
        print(f"  G1 {e1} (targets={set(t1)}) matches G2 {matches}")

    # Build and compare Hashimoto adjacency matrices
    H1, edges1 = build_hashimoto(G1)
    H2, edges2 = build_hashimoto(G2)

    # Check characteristic polynomials
    A1 = nx.to_numpy_array(H1, nodelist=edges1)
    A2 = nx.to_numpy_array(H2, nodelist=edges2)

    eig1 = np.sort(np.linalg.eigvals(A1))
    eig2 = np.sort(np.linalg.eigvals(A2))

    print(f"\nHashimoto adjacency eigenvalue distance: {np.linalg.norm(eig1 - eig2):.2e}")

    # Now check NBL (I - T where T = D^{-1}B)
    def build_T(G):
        directed_edges = []
        for u, v in G.edges():
            directed_edges.append((u, v))
            directed_edges.append((v, u))
        edge_to_idx = {e: i for i, e in enumerate(directed_edges)}
        m = len(directed_edges)
        T = np.zeros((m, m))
        for i, (u, v) in enumerate(directed_edges):
            d = G.degree(v) - 1
            if d > 0:
                for w in G.neighbors(v):
                    if w != u:
                        T[i, edge_to_idx[(v, w)]] = 1.0 / d
        return T, directed_edges, edge_to_idx

    T1, edges1, idx1 = build_T(G1)
    T2, edges2, idx2 = build_T(G2)

    L1 = np.eye(len(edges1)) - T1
    L2 = np.eye(len(edges2)) - T2

    nbl_eig1 = np.sort(np.linalg.eigvals(L1))
    nbl_eig2 = np.sort(np.linalg.eigvals(L2))

    print(f"NBL eigenvalue distance: {np.linalg.norm(nbl_eig1 - nbl_eig2):.2e}")

    # Analyze the structure more deeply
    S = {v1, v2, w1, w2}
    ext_v1 = set(n for n in G1.neighbors(v1) if n not in S)
    ext_v2 = set(n for n in G1.neighbors(v2) if n not in S)
    ext_w1 = set(n for n in G1.neighbors(w1) if n not in S)
    ext_w2 = set(n for n in G1.neighbors(w2) if n not in S)

    print("\nExternal neighborhoods:")
    print(f"  N_ext(v1={v1}) = {ext_v1}")
    print(f"  N_ext(v2={v2}) = {ext_v2}")
    print(f"  N_ext(w1={w1}) = {ext_w1}")
    print(f"  N_ext(w2={w2}) = {ext_w2}")

    # Key observation: after the switch, the NEW edges have successors that
    # relate to the OLD edges' successors
    print("\nDetailed successor comparison:")

    # In G1: edge (v1,w1) goes to all (w1,x) where x ∈ N(w1)\{v1}
    # In G2: edge (v2,w1) goes to all (w1,x) where x ∈ N_G2(w1)\{v2}
    # Since the switch doesn't change w1's neighbors except v1↔v2, these might be related

    print(f"\n  G1 edge (v1={v1},w1={w1}):")
    print(f"    Successors: edges to {set(G1.neighbors(w1)) - {v1}}")

    print(f"  G2 edge (v2={v2},w1={w1}):")
    print(f"    Successors: edges to {set(G2.neighbors(w1)) - {v2}}")

    # Check if N_G1(w1)\{v1} == N_G2(w1)\{v2}
    # N_G2(w1) = N_G1(w1) - {v1} + {v2}
    # So N_G2(w1)\{v2} = (N_G1(w1) - {v1} + {v2}) - {v2} = N_G1(w1) - {v1}
    # This equals N_G1(w1)\{v1} !

    succ_match_1 = (set(G1.neighbors(w1)) - {v1}) == (set(G2.neighbors(w1)) - {v2})
    print(f"  Successor sets match: {succ_match_1}")

    # Similarly for (v2,w2) in G1 vs (v1,w2) in G2
    succ_match_2 = (set(G1.neighbors(w2)) - {v2}) == (set(G2.neighbors(w2)) - {v1})
    print(f"\n  G1 edge (v2={v2},w2={w2}) vs G2 edge (v1={v1},w2={w2}):")
    print(f"  Successor sets match: {succ_match_2}")

    return np.linalg.norm(nbl_eig1 - nbl_eig2) < 1e-10


# Test on the hard case
g6 = "I?`D@bCW_"
G = nx.from_graph6_bytes(g6.encode())

print("Graph:", g6)
print("Edges:", list(G.edges()))
print("Degrees:", dict(G.degree()))

# The non-isomorphic cospectral switch
analyze_switch(G, 0, 2, 8, 9)

# Compare with a non-working switch from the same graph
print("\n" + "=" * 70)
print("COMPARISON: A NON-WORKING SWITCH")
print("=" * 70)
analyze_switch(G, 0, 6, 8, 2)
