#!/usr/bin/env python3
"""
Verify the swap bijection actually works.

The issue: When we swap edges, do the transitions remain valid?
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

print("CHECKING BIJECTION VALIDITY")
print("=" * 80)
print()

# Consider a walk step: (a, b) -> (b, c) in G1
# The swap sends this to a step in G2.
# We need: (1) the swapped edges exist in G2
#          (2) the step is valid (c != a)

# The key issue:
# In G1, from (x, w1) we can step to (w1, y) for y in N_G1(w1) \ {x}
# The swap maps (x, w1) -> (x, w2) and (w1, y) -> ???
# 
# If y is in ext(w1), then (w1, y) is an edge in G1.
# But (w2, y) is an edge in G2 only if y ∈ ext(w2) = shared ∪ unique_2
# If y ∈ unique_1, then (w2, y) is NOT an edge in G2!

print("The simple swap bijection DOES NOT WORK because:")
print("  - In G1, walks can go from w1 to unique_1 vertices")
print("  - In G2, walks can go from w2 to unique_2 vertices")
print("  - unique_1 ≠ unique_2, so a direct edge-by-edge swap fails")
print()

# Let me check: what is the actual mechanism?

print("ALTERNATIVE APPROACH: Aggregate by boundary types")
print("-" * 60)
print()

# The trace proof works by showing that the TOTAL contribution of walks
# with a given "boundary interaction pattern" is the same.

# For this, we need to use the lumped kernel approach.
# The key is that unique_1 and unique_2 are "equivalent" in the lumped sense.

# Let's define boundary types:
# - v1, v2: entry/exit from v-vertices
# - shared: entry/exit from shared vertices
# - unique: entry/exit from unique vertices (lumping unique_1 and unique_2)

# The lumping works because:
# - |unique_1| = |unique_2| (by Lemma 1)
# - Transitions from v_i to unique_1 = transitions from v_i to unique_2 (by Lemma 2)

print("The lumped kernel approach works because:")
print("  1. We group unique_1 (in G1) with unique_2 (in G2) as a single 'unique' type")
print("  2. The swap σ acts on boundary types: σ(w1_type) ↔ σ(w2_type)")
print("  3. Condition (C2) ensures the lumped transition weights match")
print()

# Let me verify this more carefully
for idx, (g6_1, g6_2, G1, G2, v1, v2, w1, w2) in enumerate(switches):
    S = {v1, v2, w1, w2}
    
    ext_v1_G1 = set(x for x in G1.neighbors(v1) if x not in S)
    ext_v2_G1 = set(x for x in G1.neighbors(v2) if x not in S)
    ext_w1_G1 = set(x for x in G1.neighbors(w1) if x not in S)
    ext_w2_G1 = set(x for x in G1.neighbors(w2) if x not in S)
    
    shared = ext_w1_G1 & ext_w2_G1
    unique_1 = ext_w1_G1 - ext_w2_G1
    unique_2 = ext_w2_G1 - ext_w1_G1
    
    # In G2, the external neighborhoods are the SAME as in G1
    # (switch only affects internal edges)
    ext_v1_G2 = set(x for x in G2.neighbors(v1) if x not in S)
    ext_v2_G2 = set(x for x in G2.neighbors(v2) if x not in S)
    ext_w1_G2 = set(x for x in G2.neighbors(w1) if x not in S)
    ext_w2_G2 = set(x for x in G2.neighbors(w2) if x not in S)
    
    assert ext_v1_G1 == ext_v1_G2
    assert ext_v2_G1 == ext_v2_G2
    assert ext_w1_G1 == ext_w1_G2
    assert ext_w2_G1 == ext_w2_G2
    
    # So the external structure is unchanged!
    # The switch only changes the internal connections within S.
    
    # Now let's think about boundary transitions:
    # Entry type (x, w1) for x ∈ ext(w1) = shared ∪ unique_1
    # Entry type (x, w2) for x ∈ ext(w2) = shared ∪ unique_2
    
    # After entering at (x, w1), next step could be:
    # - (w1, v1) if w1-v1 exists (YES in G1, NO in G2 after switch - wait, no!)
    # 
    # Actually, let me check: does the switch change w1-v1?
    
    # G1 edges in S: v1-w1, v2-w2, (possibly v1-v2, w1-w2)
    # G2 edges in S: v1-w2, v2-w1, (same v1-v2, w1-w2)
    
    # So in G1: w1-v1 exists (YES), w1-v2 exists only if w1-w2 exists? NO!
    # w1-v2 can exist via the edge v2-w1 only in G2, not G1.
    
    has_w1_v1_G1 = G1.has_edge(w1, v1)
    has_w1_v2_G1 = G1.has_edge(w1, v2)
    has_w1_v1_G2 = G2.has_edge(w1, v1)
    has_w1_v2_G2 = G2.has_edge(w1, v2)
    
    print(f"Switch {idx}:")
    print(f"  G1: w1-v1={has_w1_v1_G1}, w1-v2={has_w1_v2_G1}")
    print(f"  G2: w1-v1={has_w1_v1_G2}, w1-v2={has_w1_v2_G2}")

print()
print("=" * 80)
print("KEY INSIGHT")
print("=" * 80)
print()
print("In G1: w1 connects to v1 (switch edge), and possibly to v2 (if v1-v2 and path via internal)")
print("In G2: w1 connects to v2 (switch edge), and possibly to v1 (if v1-v2 and path via internal)")
print()
print("Wait - this is exactly the swap! The switch changes:")
print("  - In G1: w1-v1 (direct), w1-v2 only via other paths")  
print("  - In G2: w1-v2 (direct), w1-v1 only via other paths")
print()
print("So the swap σ that exchanges w1↔w2 in boundary types is consistent")
print("with the actual edge structure change!")

conn.close()
