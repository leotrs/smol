#!/usr/bin/env python3
"""
Direct analysis of trace contributions.

Since similarity doesn't work, let's understand WHY the traces match
by decomposing contributions by which switched edges are used.
"""

import networkx as nx
import numpy as np
import psycopg2
from itertools import permutations
from collections import defaultdict

def get_switches():
    conn = psycopg2.connect('dbname=smol')
    cur = conn.cursor()
    cur.execute('''
        SELECT g1.graph6, g2.graph6
        FROM cospectral_mates cm
        JOIN graphs g1 ON cm.graph1_id = g1.id
        JOIN graphs g2 ON cm.graph2_id = g2.id
        WHERE cm.matrix_type = 'nbl'
          AND g1.min_degree >= 2
          AND g2.min_degree >= 2
    ''')
    pairs = cur.fetchall()
    conn.close()
    
    switches = []
    for g6_1, g6_2 in pairs:
        G1 = nx.from_graph6_bytes(g6_1.encode())
        G2 = nx.from_graph6_bytes(g6_2.encode())
        E1 = set(frozenset(e) for e in G1.edges())
        E2 = set(frozenset(e) for e in G2.edges())
        only_in_G1 = E1 - E2
        only_in_G2 = E2 - E1
        
        if len(only_in_G1) != 2:
            continue
        
        verts = set()
        for e in only_in_G1 | only_in_G2:
            verts.update(e)
        
        if len(verts) != 4:
            continue
        
        for perm in permutations(verts):
            v1, v2, w1, w2 = perm
            e1 = frozenset([v1, w1])
            e2 = frozenset([v2, w2])
            new_e1 = frozenset([v1, w2])
            new_e2 = frozenset([v2, w1])
            
            if only_in_G1 == {e1, e2} and only_in_G2 == {new_e1, new_e2}:
                if G1.degree(v1) == G1.degree(v2) and G1.degree(w1) == G1.degree(w2):
                    switches.append((g6_1, g6_2, G1, G2, v1, v2, w1, w2))
                    break
    
    return switches

def enumerate_closed_walks(G, k, edge_to_idx):
    """
    Enumerate all closed non-backtracking walks of length k.
    Returns dict: start_edge -> total weight of closed walks starting there.
    """
    edges = list(edge_to_idx.keys())
    n = len(edges)
    
    # Build NBL transition
    def get_transitions(e):
        u, v = e
        deg_v = G.degree(v)
        if deg_v <= 1:
            return []
        weight = 1.0 / (deg_v - 1)
        trans = []
        for w in G.neighbors(v):
            if w != u:
                trans.append(((v, w), weight))
        return trans
    
    # For each starting edge, enumerate walks
    result = {}
    for start_edge in edges:
        # BFS/DFS to enumerate walks
        # State: (current_edge, weight_so_far)
        # After k steps, check if we're back at start_edge
        
        total_weight = 0.0
        
        # Use dynamic programming
        # current[e] = total weight to reach e after t steps
        current = defaultdict(float)
        current[start_edge] = 1.0
        
        for step in range(k):
            next_state = defaultdict(float)
            for e, w in current.items():
                for e_next, trans_w in get_transitions(e):
                    next_state[e_next] += w * trans_w
            current = next_state
        
        total_weight = current.get(start_edge, 0.0)
        result[start_edge] = total_weight
    
    return result

def analyze_trace_contributions(G, k, v1, v2, w1, w2):
    """
    Decompose tr(T^k) by which switched edges are used.
    """
    edges = [(u, v) for u, v in G.edges()] + [(v, u) for u, v in G.edges()]
    edge_to_idx = {e: i for i, e in enumerate(edges)}
    
    S = {v1, v2, w1, w2}
    switched_edges_G1 = {(v1, w1), (w1, v1), (v2, w2), (w2, v2)}
    
    walk_weights = enumerate_closed_walks(G, k, edge_to_idx)
    
    total = sum(walk_weights.values())
    
    # Decompose by starting edge type
    external_start = 0.0
    boundary_start = 0.0
    internal_start = 0.0
    switched_start = 0.0
    
    for e, w in walk_weights.items():
        u, v = e
        if u in S and v in S:
            if e in switched_edges_G1:
                switched_start += w
            else:
                internal_start += w
        elif u in S or v in S:
            boundary_start += w
        else:
            external_start += w
    
    return {
        'total': total,
        'external': external_start,
        'boundary': boundary_start,
        'internal': internal_start,
        'switched': switched_start,
    }

# Main
switches = get_switches()

print("=" * 80)
print("TRACE DECOMPOSITION BY EDGE TYPE")
print("=" * 80)
print()

# Pick one switch and analyze in detail
idx = 0
g6_1, g6_2, G1, G2, v1, v2, w1, w2 = switches[idx]

print(f"Analyzing Switch {idx}: {g6_1}")
print(f"  v1={v1}, v2={v2}, w1={w1}, w2={w2}")
print()

for k in [3, 4, 5, 6]:
    contrib_G1 = analyze_trace_contributions(G1, k, v1, v2, w1, w2)
    contrib_G2 = analyze_trace_contributions(G2, k, v1, v2, w1, w2)
    
    print(f"k={k}:")
    print(f"  G1: total={contrib_G1['total']:.6f}")
    print(f"      external={contrib_G1['external']:.6f}, boundary={contrib_G1['boundary']:.6f}")
    print(f"      internal={contrib_G1['internal']:.6f}, switched={contrib_G1['switched']:.6f}")
    print(f"  G2: total={contrib_G2['total']:.6f}")
    print(f"      external={contrib_G2['external']:.6f}, boundary={contrib_G2['boundary']:.6f}")
    print(f"      internal={contrib_G2['internal']:.6f}, switched={contrib_G2['switched']:.6f}")
    print(f"  Difference: {contrib_G1['total'] - contrib_G2['total']:.2e}")
    print()

# Now let's look at the difference more carefully
print("=" * 80)
print("ANALYZING THE CANCELLATION MECHANISM")
print("=" * 80)
print()

# The key: walks starting at switched edges in G1 vs G2 must have matching total weight
# Let's verify this for each pair of switched edges

print("Closed walk weights starting at switched edges (k=5):")
print()

edges1 = [(u, v) for u, v in G1.edges()] + [(v, u) for u, v in G1.edges()]
edges2 = [(u, v) for u, v in G2.edges()] + [(v, u) for u, v in G2.edges()]
e2i1 = {e: i for i, e in enumerate(edges1)}
e2i2 = {e: i for i, e in enumerate(edges2)}

walks_G1 = enumerate_closed_walks(G1, 5, e2i1)
walks_G2 = enumerate_closed_walks(G2, 5, e2i2)

# G1 switched edges: v1-w1, v2-w2
# G2 switched edges: v1-w2, v2-w1

print("G1 switched edges:")
for e in [(v1, w1), (w1, v1), (v2, w2), (w2, v2)]:
    print(f"  {e}: {walks_G1[e]:.6f}")

print()
print("G2 switched edges:")
for e in [(v1, w2), (w2, v1), (v2, w1), (w1, v2)]:
    print(f"  {e}: {walks_G2[e]:.6f}")

print()
print("Sum of weights at G1 switched edges:", sum(walks_G1[e] for e in [(v1, w1), (w1, v1), (v2, w2), (w2, v2)]))
print("Sum of weights at G2 switched edges:", sum(walks_G2[e] for e in [(v1, w2), (w2, v1), (v2, w1), (w1, v2)]))

print()
print("Key pairing:")
print(f"  G1: (v1,w1) + (v2,w2) = {walks_G1[(v1,w1)] + walks_G1[(v2,w2)]:.6f}")
print(f"  G2: (v1,w2) + (v2,w1) = {walks_G2[(v1,w2)] + walks_G2[(v2,w1)]:.6f}")
print(f"  G1: (w1,v1) + (w2,v2) = {walks_G1[(w1,v1)] + walks_G1[(w2,v2)]:.6f}")
print(f"  G2: (w2,v1) + (w1,v2) = {walks_G2[(w2,v1)] + walks_G2[(w1,v2)]:.6f}")
