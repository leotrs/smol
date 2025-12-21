#!/usr/bin/env python3
"""
Final attempt at a clean proof.

The key insight: The matrices T1 and T2 are NOT similar because they're 
defined on different edge sets. But their TRACES are equal.

Strategy: Decompose tr(T^k) into:
1. Contributions from non-switch edges (equal since external structure is identical)
2. Contributions from switch edges (equal by the pairing invariant)

Let's verify this decomposition and understand WHY the switch contributions match.
"""

import networkx as nx
import psycopg2
from itertools import permutations
from collections import defaultdict

def get_one_switch():
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
        
        for perm in permutations(list(verts)):
            v1, v2, w1, w2 = perm
            e1 = frozenset([v1, w1])
            e2 = frozenset([v2, w2])
            new_e1 = frozenset([v1, w2])
            new_e2 = frozenset([v2, w1])
            
            if only_in_G1 == {e1, e2} and only_in_G2 == {new_e1, new_e2}:
                if G1.degree(v1) == G1.degree(v2) and G1.degree(w1) == G1.degree(w2):
                    return G1, G2, v1, v2, w1, w2
    
    return None

def closed_walk_weight(G, start_edge, k):
    """Compute total weight of closed k-walks starting at start_edge."""
    edges = [(u, v) for u, v in G.edges()] + [(v, u) for u, v in G.edges()]
    edge_to_idx = {e: i for i, e in enumerate(edges)}
    
    if start_edge not in edge_to_idx:
        return 0.0
    
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
    
    current = defaultdict(float)
    current[start_edge] = 1.0
    
    for step in range(k):
        next_state = defaultdict(float)
        for e, w in current.items():
            for e_next, trans_w in get_transitions(e):
                next_state[e_next] += w * trans_w
        current = next_state
    
    return current.get(start_edge, 0.0)

G1, G2, v1, v2, w1, w2 = get_one_switch()
S = {v1, v2, w1, w2}

print(f"Switch: v1={v1}, v2={v2}, w1={w1}, w2={w2}")
print()

# Categorize edges
edges1 = [(u, v) for u, v in G1.edges()] + [(v, u) for u, v in G1.edges()]
edges2 = [(u, v) for u, v in G2.edges()] + [(v, u) for u, v in G2.edges()]

switch1 = {(v1, w1), (w1, v1), (v2, w2), (w2, v2)}
switch2 = {(v1, w2), (w2, v1), (v2, w1), (w1, v2)}

common_edges = set(edges1) & set(edges2)  # Non-switch edges (same in both)

print(f"Total edges in G1: {len(edges1)}")
print(f"Total edges in G2: {len(edges2)}")
print(f"Common (non-switch) edges: {len(common_edges)}")
print(f"Switch edges in G1: {len(switch1)}")
print(f"Switch edges in G2: {len(switch2)}")
print()

# Verify decomposition for k = 5
k = 5
print(f"Trace decomposition for k={k}:")
print("-" * 50)

# Non-switch contribution (should be equal)
non_switch_G1 = sum(closed_walk_weight(G1, e, k) for e in common_edges)
non_switch_G2 = sum(closed_walk_weight(G2, e, k) for e in common_edges)

print("Non-switch edges contribution:")
print(f"  G1: {non_switch_G1:.6f}")
print(f"  G2: {non_switch_G2:.6f}")
print(f"  Diff: {abs(non_switch_G1 - non_switch_G2):.2e}")
print()

# Switch contribution
switch_G1 = sum(closed_walk_weight(G1, e, k) for e in switch1)
switch_G2 = sum(closed_walk_weight(G2, e, k) for e in switch2)

print("Switch edges contribution:")
print(f"  G1: {switch_G1:.6f}")
print(f"  G2: {switch_G2:.6f}")
print(f"  Diff: {abs(switch_G1 - switch_G2):.2e}")
print()

# Verify the PAIRING
print("Individual switch edge contributions:")
print()
print("G1 switch edges:")
for e in [(v1, w1), (w1, v1), (v2, w2), (w2, v2)]:
    w = closed_walk_weight(G1, e, k)
    print(f"  {e}: {w:.6f}")

print()
print("G2 switch edges:")
for e in [(v1, w2), (w2, v1), (v2, w1), (w1, v2)]:
    w = closed_walk_weight(G2, e, k)
    print(f"  {e}: {w:.6f}")

print()
print("Pairing verification:")
# Pair 1: (v1, w1) + (v2, w2) in G1 vs (v1, w2) + (v2, w1) in G2
pair1_G1 = closed_walk_weight(G1, (v1, w1), k) + closed_walk_weight(G1, (v2, w2), k)
pair1_G2 = closed_walk_weight(G2, (v1, w2), k) + closed_walk_weight(G2, (v2, w1), k)
print(f"  W(v1,w1) + W(v2,w2) in G1: {pair1_G1:.6f}")
print(f"  W(v1,w2) + W(v2,w1) in G2: {pair1_G2:.6f}")
print(f"  Equal: {abs(pair1_G1 - pair1_G2) < 1e-10}")
print()

# Pair 2: (w1, v1) + (w2, v2) in G1 vs (w2, v1) + (w1, v2) in G2
pair2_G1 = closed_walk_weight(G1, (w1, v1), k) + closed_walk_weight(G1, (w2, v2), k)
pair2_G2 = closed_walk_weight(G2, (w2, v1), k) + closed_walk_weight(G2, (w1, v2), k)
print(f"  W(w1,v1) + W(w2,v2) in G1: {pair2_G1:.6f}")
print(f"  W(w2,v1) + W(w1,v2) in G2: {pair2_G2:.6f}")
print(f"  Equal: {abs(pair2_G1 - pair2_G2) < 1e-10}")
print()

print("=" * 60)
print("WHY THE PAIRING WORKS")
print("=" * 60)
print("""
The pairing invariant holds because:

1. FIRST EXIT STRUCTURE:
   - From (v1, w1) in G1: first step exits to neighbors of w1
   - From (v2, w1) in G2: first step exits to neighbors of w1 (SAME!)
   
   So (v1, w1) in G1 and (v2, w1) in G2 have the same "exit distribution"
   to external vertices.

2. EXTERNAL PATH IDENTITY:
   - The external graph (edges not in S) is identical in G1 and G2
   - So external excursions have the same weights

3. RETURN STRUCTURE (condition C2):
   - |ext(v1) ∩ unique_1| = |ext(v1) ∩ unique_2|
   - This ensures equal "return multiplicities" for walks returning via
     unique_1 vs unique_2

4. DEGREE EQUALITY (condition C1):
   - deg(w1) = deg(w2) ensures equal exit weights
   - deg(v1) = deg(v2) ensures equal internal transition weights

5. INTERNAL PATH BIJECTION (Φ-conjugacy):
   - σ maps internal paths in G1 to internal paths in G2
   - Weights are preserved because of (C1)

The pairing is:
  (v1, w1) in G1  ←→  (v2, w1) in G2  [both exit via w1]
  (v2, w2) in G1  ←→  (v1, w2) in G2  [both exit via w2]
  
Within each pair, walks have the same first exit distribution (via w1 or w2),
same external paths, and symmetric return structure (by C2).

The aggregate weights match because of this correspondence, even though
individual walks don't pair up one-to-one.
""")
