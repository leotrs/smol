#!/usr/bin/env python3
"""
Derive minimal sufficient conditions for NBL-cospectrality in 2-edge switches.

Key discovery: uniform cross-intersection IMPLIES the u->v symmetry condition.

Let's verify this and find the TRUE minimal conditions.
"""

import networkx as nx
import psycopg2
from itertools import permutations

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

print("DERIVING MINIMAL CONDITIONS")
print("=" * 80)
print()

print("Claim: Uniform cross-intersection implies |u1 ∩ ext(vi)| = |u2 ∩ ext(vi)| for i=1,2")
print()
print("Proof:")
print("  ext(vi) ∩ ext(wj) = (ext(vi) ∩ shared) ∪ (ext(vi) ∩ unique_j)")
print("  Since shared ⊆ ext(w1) ∩ ext(w2) and unique_j ⊆ ext(wj) \\ ext(w_{3-j}):")
print("    ext(vi) ∩ shared and ext(vi) ∩ unique_j are disjoint")
print("  So: |ext(vi) ∩ ext(wj)| = |ext(vi) ∩ shared| + |ext(vi) ∩ unique_j|")
print()
print("  Uniform cross says: |ext(v1) ∩ ext(w1)| = |ext(v1) ∩ ext(w2)|")
print("  => |ext(v1) ∩ shared| + |ext(v1) ∩ unique_1| = |ext(v1) ∩ shared| + |ext(v1) ∩ unique_2|")
print("  => |ext(v1) ∩ unique_1| = |ext(v1) ∩ unique_2|  ✓")
print()
print("  Similarly for v2.  QED")
print()

# Verify this claim on all 11 switches
print("Verification on all 11 switches:")
for idx, (g6_1, g6_2, G1, G2, v1, v2, w1, w2) in enumerate(switches):
    S = {v1, v2, w1, w2}
    G = G1
    
    ext_v1 = set(x for x in G.neighbors(v1) if x not in S)
    ext_v2 = set(x for x in G.neighbors(v2) if x not in S)
    ext_w1 = set(x for x in G.neighbors(w1) if x not in S)
    ext_w2 = set(x for x in G.neighbors(w2) if x not in S)
    
    shared = ext_w1 & ext_w2
    unique_1 = ext_w1 - ext_w2
    unique_2 = ext_w2 - ext_w1
    
    # Cross intersections
    c11 = len(ext_v1 & ext_w1)
    c12 = len(ext_v1 & ext_w2)
    c21 = len(ext_v2 & ext_w1)
    c22 = len(ext_v2 & ext_w2)
    
    # Decomposition
    v1_shared = len(ext_v1 & shared)
    v1_u1 = len(ext_v1 & unique_1)
    v1_u2 = len(ext_v1 & unique_2)
    
    v2_shared = len(ext_v2 & shared)
    v2_u1 = len(ext_v2 & unique_1)
    v2_u2 = len(ext_v2 & unique_2)
    
    # Verify decomposition
    assert c11 == v1_shared + v1_u1
    assert c12 == v1_shared + v1_u2
    assert c21 == v2_shared + v2_u1
    assert c22 == v2_shared + v2_u2
    
    # Verify implication
    uniform = (c11 == c12 == c21 == c22)
    v1_sym = (v1_u1 == v1_u2)
    v2_sym = (v2_u1 == v2_u2)
    
    if uniform:
        assert v1_sym and v2_sym, "Uniform cross should imply symmetry!"
    
    status = "✓" if uniform else "✗"
    print(f"  Switch {idx}: cross=({c11},{c12},{c21},{c22}), v1:(sh={v1_shared},u1={v1_u1},u2={v1_u2}), v2:(sh={v2_shared},u1={v2_u1},u2={v2_u2}) {status}")

print()
print("All verifications passed!")
print()

# Now let's understand what OTHER conditions are needed beyond uniform cross
print("=" * 80)
print("ADDITIONAL CONDITIONS NEEDED")
print("=" * 80)
print()

# The trace proof requires that closed walks have matching weights.
# Let's think about what structure is needed.

print("Analysis of what uniform cross-intersection provides:")
print()
print("1. |ext(vi) ∩ unique_j| is the same for j=1,2 (proved above)")
print("2. This means: for any vi, the number of unique_1 neighbors = number of unique_2 neighbors")
print("3. Key observation: deg(w1) = deg(w2) + |shared| + |unique_1| - |shared| - |unique_2|")
print("   = deg(w2) when |unique_1| = |unique_2|")
print()

# Check what structural properties hold
print("Checking structural properties:")
for idx, (g6_1, g6_2, G1, G2, v1, v2, w1, w2) in enumerate(switches):
    S = {v1, v2, w1, w2}
    G = G1
    
    ext_w1 = set(x for x in G.neighbors(w1) if x not in S)
    ext_w2 = set(x for x in G.neighbors(w2) if x not in S)
    
    shared = ext_w1 & ext_w2
    unique_1 = ext_w1 - ext_w2
    unique_2 = ext_w2 - ext_w1
    
    # The S-internal graph structure
    has_v1v2 = G.has_edge(v1, v2)
    has_w1w2 = G.has_edge(w1, w2)
    has_v1w2 = G.has_edge(v1, w2)
    has_v2w1 = G.has_edge(v2, w1)
    
    # After switch: we add v1-w2 and v2-w1, remove v1-w1 and v2-w2
    # So in G2:
    # has_v1v2_G2 = has_v1v2
    # has_w1w2_G2 = has_w1w2
    # has_v1w2_G2 = True (added)
    # has_v2w1_G2 = True (added)
    
    # But wait, in G1 we might already have v1-w2 or v2-w1!
    # These are NOT the switched edges. Let me check.
    
    print(f"Switch {idx}: S-internal edges: v1v2={has_v1v2}, w1w2={has_w1w2}, v1w2={has_v1w2}, v2w1={has_v2w1}")
    
    # In fact, v1-w2 and v2-w1 are the edges that GET ADDED in the switch.
    # So in G1, they should NOT exist!
    
    # Check this
    assert not has_v1w2, f"Switch {idx}: v1-w2 should not exist in G1"
    assert not has_v2w1, f"Switch {idx}: v2-w1 should not exist in G1"

print()
print("Confirmed: In all G1, the edges v1-w2 and v2-w1 do not exist.")
print("These are exactly the edges added by the switch.")
print()

# Now let's think about what makes the traces equal
print("=" * 80)
print("THE TRACE EQUALITY MECHANISM")
print("=" * 80)
print()

print("For trace equality, we need: sum of weights of all k-closed walks equal in G1 and G2")
print()
print("Key insight: The graphs G1 and G2 are identical except for the edges within S.")
print("- G1 has edges: v1-w1, v2-w2 (and possibly v1-v2, w1-w2)")
print("- G2 has edges: v1-w2, v2-w1 (and same v1-v2, w1-w2)")
print()
print("So the difference in closed walks comes from walks that USE the switched edges.")

conn.close()
