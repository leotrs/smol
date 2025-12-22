"""
Check Option 3 (local isomorphism) on all 78 pairs.

C3-iso: There exists an isomorphism φ: G[N[v₁] ∪ N[w₁]] → G[N[v₂] ∪ N[w₂]] 
such that φ(v₁) = v₂, φ(w₁) = w₂
"""

import networkx as nx
from itertools import permutations

def to_graph(g6):
    return nx.from_graph6_bytes(g6.encode())

def find_switch(G1, G2):
    """Find if G1 and G2 differ by a 2-edge switch."""
    e1 = set(frozenset(e) for e in G1.edges())
    e2 = set(frozenset(e) for e in G2.edges())
    
    only_in_1 = e1 - e2
    only_in_2 = e2 - e1
    
    if len(only_in_1) != 2 or len(only_in_2) != 2:
        return None
    
    removed = [tuple(e) for e in only_in_1]
    added = [tuple(e) for e in only_in_2]
    
    # Try to find v1, w1, v2, w2
    for (a, b), (c, d) in [(removed[0], removed[1]), (removed[1], removed[0])]:
        for v1, w1 in [(a, b), (b, a)]:
            for v2, w2 in [(c, d), (d, c)]:
                expected = {frozenset({v1, w2}), frozenset({v2, w1})}
                actual = set(frozenset(e) for e in added)
                if expected == actual:
                    return (v1, w1, v2, w2)
    return None

def closed_neighborhood(G, v):
    """N[v] = {v} ∪ N(v)"""
    return {v} | set(G.neighbors(v))

def check_local_isomorphism(G, v1, w1, v2, w2):
    """
    Check if G[N[v1] ∪ N[w1]] ≅ G[N[v2] ∪ N[w2]] with φ(v1)=v2, φ(w1)=w2.
    """
    # Get the two induced subgraphs
    region1 = closed_neighborhood(G, v1) | closed_neighborhood(G, w1)
    region2 = closed_neighborhood(G, v2) | closed_neighborhood(G, w2)
    
    H1 = G.subgraph(region1).copy()
    H2 = G.subgraph(region2).copy()
    
    # Must have same size
    if H1.number_of_nodes() != H2.number_of_nodes():
        return False, "different node count"
    if H1.number_of_edges() != H2.number_of_edges():
        return False, "different edge count"
    
    # Check degree sequences match
    if sorted(dict(H1.degree()).values()) != sorted(dict(H2.degree()).values()):
        return False, "different degree sequences"
    
    # v1, w1 must map to v2, w2 - check their degrees match
    if H1.degree(v1) != H2.degree(v2):
        return False, f"deg(v1)={H1.degree(v1)} != deg(v2)={H2.degree(v2)} in induced"
    if H1.degree(w1) != H2.degree(w2):
        return False, f"deg(w1)={H1.degree(w1)} != deg(w2)={H2.degree(w2)} in induced"
    
    # Try to find an isomorphism with v1->v2, w1->w2
    # Brute force: try all mappings of remaining vertices
    fixed = {v1: v2, w1: w2}
    remaining1 = [v for v in region1 if v not in fixed]
    remaining2 = [v for v in region2 if v not in fixed]
    
    if len(remaining1) != len(remaining2):
        return False, "remaining vertex count mismatch"
    
    for perm in permutations(remaining2):
        mapping = dict(fixed)
        mapping.update(zip(remaining1, perm))
        
        # Check if this is an isomorphism
        is_iso = True
        for u, v in H1.edges():
            if not H2.has_edge(mapping[u], mapping[v]):
                is_iso = False
                break
        
        if is_iso:
            # Also verify edge count matches (in case H2 has extra edges)
            if H1.number_of_edges() == H2.number_of_edges():
                return True, mapping
    
    return False, "no valid isomorphism found"

# Load pairs
pairs = []
with open('docs/78_pairs.txt') as f:
    for line in f:
        line = line.strip()
        if ',' in line:
            g1, g2 = line.split(',')
            pairs.append((g1, g2))

print(f"Checking {len(pairs)} pairs\n")

direct_switches = []
non_switches = []

for g1, g2 in pairs:
    G1 = to_graph(g1)
    G2 = to_graph(g2)
    
    switch = find_switch(G1, G2)
    if switch:
        direct_switches.append((g1, g2, switch, G1))
    else:
        non_switches.append((g1, g2))

print(f"Direct 2-edge switches: {len(direct_switches)}")
print(f"Not direct switches: {len(non_switches)}\n")

print("=" * 60)
print("Checking local isomorphism (C3-iso) for direct switches:")
print("=" * 60)

passes = 0
fails = []

for g1, g2, switch, G in direct_switches:
    v1, w1, v2, w2 = switch
    result, info = check_local_isomorphism(G, v1, w1, v2, w2)
    
    if result:
        passes += 1
        print(f"✓ {g1[:12]}... switch ({v1},{w1},{v2},{w2})")
    else:
        fails.append((g1, switch, info))
        print(f"✗ {g1[:12]}... switch ({v1},{w1},{v2},{w2}): {info}")

print()
print(f"RESULT: {passes}/{len(direct_switches)} satisfy C3-iso")

if fails:
    print("\nFailed cases:")
    for g1, switch, info in fails:
        print(f"  {g1}, {switch}: {info}")
