#!/usr/bin/env python3
"""Analyze the one hard case in detail."""

import networkx as nx
import numpy as np
from itertools import permutations


def build_hashimoto(G):
    """Build the Hashimoto (line) graph on directed edges."""
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


def build_T(G):
    """Build the transition matrix T = D^{-1}B."""
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


def perform_switch(G, v1, v2, w1, w2):
    G2 = G.copy()
    G2.remove_edge(v1, w1)
    G2.remove_edge(v2, w2)
    G2.add_edge(v1, w2)
    G2.add_edge(v2, w1)
    return G2


def find_switch_vertices(G1, G2):
    E1 = set(G1.edges())
    E2 = set(G2.edges())
    only_in_G1 = E1 - E2
    only_in_G2 = E2 - E1
    if len(only_in_G1) != 2 or len(only_in_G2) != 2:
        return None
    verts = set()
    for e in only_in_G1 | only_in_G2:
        verts.update(e)
    if len(verts) != 4:
        return None
    for perm in permutations(verts):
        v1, v2, w1, w2 = perm
        if (G1.has_edge(v1, w1) and G1.has_edge(v2, w2) and
            not G1.has_edge(v1, w2) and not G1.has_edge(v2, w1) and
            G1.degree(v1) == G1.degree(v2) and G1.degree(w1) == G1.degree(w2)):
            return (v1, v2, w1, w2)
    return None


def analyze_graph(g6):
    print(f"Analyzing: {g6}")
    G1 = nx.from_graph6_bytes(g6.encode())

    print("\nGraph G1:")
    print(f"  Nodes: {G1.nodes()}")
    print(f"  Edges: {list(G1.edges())}")
    print(f"  Degrees: {dict(G1.degree())}")

    # Find all valid switch patterns
    edges = list(G1.edges())
    valid_switches = []
    for i, (a, b) in enumerate(edges):
        for j, (c, d) in enumerate(edges):
            if i >= j:
                continue
            for v1, w1 in [(a, b), (b, a)]:
                for v2, w2 in [(c, d), (d, c)]:
                    if len({v1, v2, w1, w2}) != 4:
                        continue
                    if not G1.has_edge(v1, w1) or not G1.has_edge(v2, w2):
                        continue
                    if G1.has_edge(v1, w2) or G1.has_edge(v2, w1):
                        continue
                    if G1.degree(v1) != G1.degree(v2):
                        continue
                    if G1.degree(w1) != G1.degree(w2):
                        continue
                    valid_switches.append((v1, v2, w1, w2))

    print(f"\nValid switch patterns: {len(valid_switches)}")

    for v1, v2, w1, w2 in valid_switches:
        print(f"\n{'='*60}")
        print(f"Switch: v1={v1}, v2={v2}, w1={w1}, w2={w2}")
        print(f"{'='*60}")

        S = {v1, v2, w1, w2}

        # External neighborhoods
        ext_v1 = set(n for n in G1.neighbors(v1) if n not in S)
        ext_v2 = set(n for n in G1.neighbors(v2) if n not in S)
        ext_w1 = set(n for n in G1.neighbors(w1) if n not in S)
        ext_w2 = set(n for n in G1.neighbors(w2) if n not in S)

        print("\nExternal neighborhoods:")
        print(f"  N_ext(v1={v1}) = {ext_v1}")
        print(f"  N_ext(v2={v2}) = {ext_v2}")
        print(f"  N_ext(w1={w1}) = {ext_w1}")
        print(f"  N_ext(w2={w2}) = {ext_w2}")

        # Cross connections
        print("\nCross connections:")
        print(f"  N_ext(v1) ∩ N_ext(w2) = {ext_v1 & ext_w2} (size {len(ext_v1 & ext_w2)})")
        print(f"  N_ext(v2) ∩ N_ext(w1) = {ext_v2 & ext_w1} (size {len(ext_v2 & ext_w1)})")
        print(f"  N_ext(v1) ∩ N_ext(w1) = {ext_v1 & ext_w1} (size {len(ext_v1 & ext_w1)})")
        print(f"  N_ext(v2) ∩ N_ext(w2) = {ext_v2 & ext_w2} (size {len(ext_v2 & ext_w2)})")

        # Common
        print("\nCommon external neighbors:")
        print(f"  N_ext(v1) ∩ N_ext(v2) = {ext_v1 & ext_v2}")
        print(f"  N_ext(w1) ∩ N_ext(w2) = {ext_w1 & ext_w2}")

        # Symmetric difference
        print("\nSymmetric differences:")
        print(f"  N_ext(v1) △ N_ext(v2) = {ext_v1 ^ ext_v2} (size {len(ext_v1 ^ ext_v2)})")
        print(f"  N_ext(w1) △ N_ext(w2) = {ext_w1 ^ ext_w2} (size {len(ext_w1 ^ ext_w2)})")

        # Perform switch
        G2 = perform_switch(G1, v1, v2, w1, w2)

        # Check spectral distance
        T1, edges1, _ = build_T(G1)
        T2, edges2, _ = build_T(G2)

        eig1 = np.sort(np.linalg.eigvals(T1))
        eig2 = np.sort(np.linalg.eigvals(T2))
        dist = np.linalg.norm(eig1 - eig2)

        print(f"\nSpectral distance: {dist:.2e}")
        print(f"Cospectral: {dist < 1e-10}")

        if dist < 1e-10:
            # Check Hashimoto isomorphism
            H1, _ = build_hashimoto(G1)
            H2, _ = build_hashimoto(G2)

            try:
                is_iso = nx.is_isomorphic(H1, H2)
            except Exception:
                is_iso = "Error"

            print(f"\nHashimoto graphs isomorphic: {is_iso}")

            # Look at the specific rows/columns that changed
            print("\nT matrix analysis:")

            # Find the directed edges involved in switch
            switch_edges_G1 = [(v1, w1), (w1, v1), (v2, w2), (w2, v2)]
            switch_edges_G2 = [(v1, w2), (w2, v1), (v2, w1), (w1, v2)]

            print(f"  Switch edges G1: {switch_edges_G1}")
            print(f"  Switch edges G2: {switch_edges_G2}")

            # Build detailed edge info
            def edge_info(G, e):
                u, v = e
                return f"[{u},{v}]: d(v)={G.degree(v)}, out_to={[w for w in G.neighbors(v) if w != u]}"

            print("\nEdge details G1:")
            for e in switch_edges_G1:
                print(f"  {edge_info(G1, e)}")

            print("\nEdge details G2:")
            for e in switch_edges_G2:
                print(f"  {edge_info(G2, e)}")


# The hard case
g6 = "I?`D@bCW_"
analyze_graph(g6)

# Also look at a few other working cases for comparison
print("\n\n" + "=" * 70)
print("COMPARISON WITH OTHER WORKING CASES")
print("=" * 70)

# A case that satisfies cross-connection condition
g6_easy = "I?q`Djcb?"  # We'll find one from the database
