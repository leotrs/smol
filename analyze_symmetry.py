"""
Steps 1 and 2: Extract local structure and look for symmetries in the 11 cospectral switches.
"""

import networkx as nx

def to_graph(g6):
    return nx.from_graph6_bytes(g6.encode())

def find_switch(G1, G2):
    e1 = set(frozenset(e) for e in G1.edges())
    e2 = set(frozenset(e) for e in G2.edges())
    only_in_1 = e1 - e2
    only_in_2 = e2 - e1
    if len(only_in_1) != 2 or len(only_in_2) != 2:
        return None
    removed = [tuple(e) for e in only_in_1]
    added = [tuple(e) for e in only_in_2]
    for (a, b), (c, d) in [(removed[0], removed[1]), (removed[1], removed[0])]:
        for v1, w1 in [(a, b), (b, a)]:
            for v2, w2 in [(c, d), (d, c)]:
                expected = {frozenset({v1, w2}), frozenset({v2, w1})}
                actual = set(frozenset(e) for e in added)
                if expected == actual:
                    return (v1, w1, v2, w2)
    return None

def get_local_neighborhood(G, v1, w1, v2, w2):
    """Get 1-hop neighborhood of all 4 vertices."""
    vertices = set()
    for x in [v1, w1, v2, w2]:
        vertices.add(x)
        vertices.update(G.neighbors(x))
    return G.subgraph(vertices).copy()

def find_automorphisms_swapping_edges(G, v1, w1, v2, w2):
    """
    Find automorphisms of G that map edge (v1,w1) to (v2,w2).
    Returns list of such automorphisms as dicts.
    """
    from networkx.algorithms.isomorphism import GraphMatcher
    
    swapping_autos = []
    
    # Check for automorphisms that map v1->v2, w1->w2
    gm = GraphMatcher(G, G)
    for iso in gm.isomorphisms_iter():
        # iso maps G to G, so iso[v] gives where v maps to
        if iso[v1] == v2 and iso[w1] == w2:
            swapping_autos.append(('v1->v2, w1->w2', iso))
        elif iso[v1] == w2 and iso[w1] == v2:
            swapping_autos.append(('v1->w2, w1->v2', iso))
    
    return swapping_autos

def check_local_symmetry(G, v1, w1, v2, w2):
    """Check various symmetry conditions."""
    S = {v1, v2, w1, w2}
    
    # Get local neighborhood
    local_G = get_local_neighborhood(G, v1, w1, v2, w2)
    
    # Find automorphisms of local neighborhood that swap edges
    swapping = find_automorphisms_swapping_edges(local_G, v1, w1, v2, w2)
    
    # Also check full graph automorphisms
    full_swapping = find_automorphisms_swapping_edges(G, v1, w1, v2, w2)
    
    return {
        'local_vertices': set(local_G.nodes()),
        'local_edges': list(local_G.edges()),
        'local_size': (local_G.number_of_nodes(), local_G.number_of_edges()),
        'local_swapping_autos': len(swapping),
        'full_swapping_autos': len(full_swapping),
        'swapping_types': [s[0] for s in swapping[:3]],  # First 3
    }

# Load pairs
pairs = []
with open('docs/78_pairs.txt') as f:
    for line in f:
        line = line.strip()
        if ',' in line:
            g1, g2 = line.split(',')
            pairs.append((g1, g2))

print("="*70)
print("STEP 1 & 2: Local structure and symmetries of 11 cospectral switches")
print("="*70)

for g1, g2 in pairs:
    G1, G2 = to_graph(g1), to_graph(g2)
    switch = find_switch(G1, G2)
    if not switch:
        continue
    
    v1, w1, v2, w2 = switch
    sym = check_local_symmetry(G1, v1, w1, v2, w2)
    
    print(f"\n{g1}")
    print(f"  Switch: ({v1},{w1}) <-> ({v2},{w2})")
    print(f"  Local neighborhood: {sym['local_size'][0]} vertices, {sym['local_size'][1]} edges")
    print(f"  Local swapping automorphisms: {sym['local_swapping_autos']}")
    print(f"  Full graph swapping automorphisms: {sym['full_swapping_autos']}")
    if sym['swapping_types']:
        print(f"  Swapping types: {sym['swapping_types']}")
