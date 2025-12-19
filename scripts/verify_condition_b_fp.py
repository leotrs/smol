#!/usr/bin/env python3
"""Verify if Condition B false positives are real or bugs."""

import networkx as nx
import numpy as np
import psycopg2


def is_switchable(G, v1, v2, w1, w2):
    if len({v1, v2, w1, w2}) != 4:
        return False
    if not G.has_edge(v1, w1) or not G.has_edge(v2, w2):
        return False
    if G.has_edge(v1, w2) or G.has_edge(v2, w1):
        return False
    return G.degree(v1) == G.degree(v2) and G.degree(w1) == G.degree(w2)


def perform_switch(G, v1, v2, w1, w2):
    G2 = G.copy()
    G2.remove_edge(v1, w1)
    G2.remove_edge(v2, w2)
    G2.add_edge(v1, w2)
    G2.add_edge(v2, w1)
    return G2


def build_hashimoto(G):
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
                H.add_edge(e1, (v, w))
    return H, directed_edges


def build_NBL(G):
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
    return np.eye(m) - T


def spectral_distance(G1, G2):
    L1 = build_NBL(G1)
    L2 = build_NBL(G2)
    eig1 = np.sort(np.linalg.eigvals(L1))
    eig2 = np.sort(np.linalg.eigvals(L2))
    return np.linalg.norm(eig1 - eig2)


def find_all_potential_switches(G):
    potential = []
    edges = list(G.edges())
    for i, (a, b) in enumerate(edges):
        for j, (c, d) in enumerate(edges):
            if i >= j:
                continue
            for v1, w1 in [(a, b), (b, a)]:
                for v2, w2 in [(c, d), (d, c)]:
                    if is_switchable(G, v1, v2, w1, w2):
                        potential.append((v1, v2, w1, w2))
    return potential


# Create a simple test case
# Let's construct a graph where we can verify Condition B

# Build a small graph manually
G = nx.Graph()
G.add_edges_from([
    (0, 1), (0, 2), (0, 3),  # vertex 0 has neighbors 1, 2, 3
    (1, 4), (1, 5),          # vertex 1 has neighbors 0, 4, 5
    (2, 4), (2, 5),          # vertex 2 has neighbors 0, 4, 5 (SAME as 1 outside {0,1,2})
    (3, 6), (3, 7),
    (4, 6), (5, 7),
])

print("Test graph edges:", list(G.edges()))
print("Degrees:", dict(G.degree()))

# Check all potential switches
for v1, v2, w1, w2 in find_all_potential_switches(G):
    S = {v1, v2, w1, w2}
    ext_v1 = set(n for n in G.neighbors(v1) if n not in S)
    ext_v2 = set(n for n in G.neighbors(v2) if n not in S)
    ext_w1 = set(n for n in G.neighbors(w1) if n not in S)
    ext_w2 = set(n for n in G.neighbors(w2) if n not in S)

    condition_B = (ext_v1 == ext_v2) or (ext_w1 == ext_w2)

    if condition_B:
        G2 = perform_switch(G, v1, v2, w1, w2)
        dist = spectral_distance(G, G2)

        # Check Hashimoto isomorphism
        H1, _ = build_hashimoto(G)
        H2, _ = build_hashimoto(G2)
        is_iso = nx.is_isomorphic(H1, H2)

        print(f"\nSwitch: v1={v1}, v2={v2}, w1={w1}, w2={w2}")
        print(f"  N_ext(v1)={ext_v1}, N_ext(v2)={ext_v2}")
        print(f"  N_ext(w1)={ext_w1}, N_ext(w2)={ext_w2}")
        print(f"  Condition B (v or w equal): {condition_B}")
        print(f"  Hashimoto isomorphic: {is_iso}")
        print(f"  Spectral distance: {dist:.2e}")
        print(f"  Cospectral: {dist < 1e-10}")

# Now let's find a graph from the database that supposedly has Condition B FP
print("\n" + "=" * 70)
print("CHECKING DATABASE FOR CONDITION B FALSE POSITIVES")
print("=" * 70)

conn = psycopg2.connect("dbname=smol")
cur = conn.cursor()
cur.execute("""
    SELECT g1.graph6, g2.graph6
    FROM cospectral_mates cm
    JOIN graphs g1 ON cm.graph1_id = g1.id
    JOIN graphs g2 ON cm.graph2_id = g2.id
    WHERE cm.matrix_type = 'nbl'
    LIMIT 50
""")
pairs = cur.fetchall()

fps_found = []

for g6_1, _ in pairs:
    G = nx.from_graph6_bytes(g6_1.encode())

    for v1, v2, w1, w2 in find_all_potential_switches(G):
        S = {v1, v2, w1, w2}
        ext_v1 = set(n for n in G.neighbors(v1) if n not in S)
        ext_v2 = set(n for n in G.neighbors(v2) if n not in S)
        ext_w1 = set(n for n in G.neighbors(w1) if n not in S)
        ext_w2 = set(n for n in G.neighbors(w2) if n not in S)

        condition_B = (ext_v1 == ext_v2) or (ext_w1 == ext_w2)

        if condition_B:
            G2 = perform_switch(G, v1, v2, w1, w2)
            dist = spectral_distance(G, G2)

            if dist > 1e-10:  # Not cospectral - FALSE POSITIVE
                fps_found.append({
                    'g6': g6_1,
                    'switch': (v1, v2, w1, w2),
                    'ext_v1': ext_v1, 'ext_v2': ext_v2,
                    'ext_w1': ext_w1, 'ext_w2': ext_w2,
                    'dist': dist,
                })

print(f"\nFound {len(fps_found)} Condition B false positives in first 50 pairs")

if fps_found:
    print("\nFirst few false positives:")
    for fp in fps_found[:3]:
        print(f"\n  Graph: {fp['g6']}")
        print(f"  Switch: {fp['switch']}")
        print(f"  N_ext(v1)={fp['ext_v1']}, N_ext(v2)={fp['ext_v2']}")
        print(f"  N_ext(w1)={fp['ext_w1']}, N_ext(w2)={fp['ext_w2']}")
        print(f"  Spectral distance: {fp['dist']:.2e}")

        # Verify Hashimoto isomorphism
        G = nx.from_graph6_bytes(fp['g6'].encode())
        v1, v2, w1, w2 = fp['switch']
        G2 = perform_switch(G, v1, v2, w1, w2)
        H1, _ = build_hashimoto(G)
        H2, _ = build_hashimoto(G2)
        print(f"  Hashimoto isomorphic: {nx.is_isomorphic(H1, H2)}")

conn.close()
