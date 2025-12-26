"""
Check if the switch preserves the local neighborhood structure.
Also look for weaker symmetries.
"""

import networkx as nx
from networkx.algorithms.isomorphism import GraphMatcher

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

def apply_switch(G, v1, w1, v2, w2):
    """Apply the switch to G."""
    Gp = G.copy()
    Gp.remove_edge(v1, w1)
    Gp.remove_edge(v2, w2)
    Gp.add_edge(v1, w2)
    Gp.add_edge(v2, w1)
    return Gp

def check_external_symmetry(G, v1, w1, v2, w2):
    """
    Check if there's an automorphism of the external structure
    (everything except v1,w1,v2,w2) that relates the two edges.
    """
    S = {v1, v2, w1, w2}
    ext = {x: set(G.neighbors(x)) - S for x in S}
    
    # External vertices
    ext_vertices = ext[v1] | ext[w1] | ext[v2] | ext[w2]
    
    # Subgraph on external vertices
    ext_G = G.subgraph(ext_vertices).copy()
    
    # Check for automorphisms
    auto_count = sum(1 for _ in GraphMatcher(ext_G, ext_G).isomorphisms_iter())
    
    return {
        'ext_vertices': ext_vertices,
        'ext_size': (ext_G.number_of_nodes(), ext_G.number_of_edges()),
        'ext_auto_count': auto_count,
    }

def check_isomorphism_type_preservation(G, v1, w1, v2, w2):
    """Check if local neighborhoods before/after switch are isomorphic."""
    Gp = apply_switch(G, v1, w1, v2, w2)
    
    local_G = get_local_neighborhood(G, v1, w1, v2, w2)
    local_Gp = get_local_neighborhood(Gp, v1, w1, v2, w2)  # Same vertices
    
    # They should have the same vertex set
    assert set(local_G.nodes()) == set(local_Gp.nodes())
    
    # Are they isomorphic as unlabeled graphs?
    is_iso = nx.is_isomorphic(local_G, local_Gp)
    
    # More specific: is there an isomorphism that fixes all vertices except S?
    S = {v1, v2, w1, w2}
    ext_vertices = set(local_G.nodes()) - S
    
    # Check if there's an isomorphism G -> G' that fixes external vertices
    def node_match(n1_attrs, n2_attrs):
        return True
    
    fixed_iso = False
    for iso in GraphMatcher(local_G, local_Gp).isomorphisms_iter():
        # Check if iso fixes all external vertices
        if all(iso[v] == v for v in ext_vertices):
            fixed_iso = True
            # What does it do to S?
            s_mapping = {v: iso[v] for v in S}
            break
    
    return {
        'is_isomorphic': is_iso,
        'has_fixed_ext_iso': fixed_iso,
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
print("Local structure preservation after switch")
print("="*70)

for g1, g2 in pairs:
    G1, G2 = to_graph(g1), to_graph(g2)
    switch = find_switch(G1, G2)
    if not switch:
        continue
    
    v1, w1, v2, w2 = switch
    
    iso_check = check_isomorphism_type_preservation(G1, v1, w1, v2, w2)
    ext_sym = check_external_symmetry(G1, v1, w1, v2, w2)
    
    print(f"\n{g1}")
    print(f"  Switch: ({v1},{w1}) <-> ({v2},{w2})")
    print(f"  Local nbhd isomorphic after switch: {iso_check['is_isomorphic']}")
    print(f"  Has iso fixing external vertices: {iso_check['has_fixed_ext_iso']}")
    print(f"  External structure: {ext_sym['ext_size']}")
    print(f"  External automorphisms: {ext_sym['ext_auto_count']}")
