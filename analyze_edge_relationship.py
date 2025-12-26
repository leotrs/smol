"""
Analyze the relationship between the two switched edges.
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

def analyze_edge_relationship(G, v1, w1, v2, w2):
    """Analyze the relationship between edges (v1,w1) and (v2,w2)."""
    S = {v1, v2, w1, w2}
    
    # Distances between the 4 vertices
    dist = {}
    for a in S:
        for b in S:
            if a < b:
                try:
                    d = nx.shortest_path_length(G, a, b)
                except nx.NetworkXNoPath:
                    d = float('inf')
                dist[(a,b)] = d
    
    # Internal structure of S (which pairs are connected)
    internal = []
    if G.has_edge(v1, v2): internal.append('v1-v2')
    if G.has_edge(w1, w2): internal.append('w1-w2')
    if G.has_edge(v1, w2): internal.append('v1-w2')  # Should not exist
    if G.has_edge(v2, w1): internal.append('v2-w1')  # Should not exist
    
    # External neighborhoods
    ext = {x: set(G.neighbors(x)) - S for x in S}
    
    # Pairwise intersections
    intersections = {
        'v1∩w1': ext[v1] & ext[w1],
        'v2∩w2': ext[v2] & ext[w2],
        'v1∩w2': ext[v1] & ext[w2],
        'v2∩w1': ext[v2] & ext[w1],
        'v1∩v2': ext[v1] & ext[v2],
        'w1∩w2': ext[w1] & ext[w2],
    }
    
    # Check if removed edges have "equivalent" external connections
    # i.e., do v1,w1 see the same external structure as v2,w2?
    
    # Connection pattern to external vertices
    # For each external vertex, which of S does it connect to?
    all_ext = ext[v1] | ext[w1] | ext[v2] | ext[w2]
    ext_patterns = {}
    for x in all_ext:
        pattern = tuple(sorted([v for v in S if G.has_edge(x, v)]))
        if pattern not in ext_patterns:
            ext_patterns[pattern] = []
        ext_patterns[pattern].append(x)
    
    return {
        'internal': internal,
        'intersections': {k: len(v) for k, v in intersections.items()},
        'ext_patterns': ext_patterns,
        'ext_pattern_summary': {p: len(vs) for p, vs in ext_patterns.items()},
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
print("Edge relationship analysis")
print("="*70)

for g1, g2 in pairs:
    G1, G2 = to_graph(g1), to_graph(g2)
    switch = find_switch(G1, G2)
    if not switch:
        continue
    
    v1, w1, v2, w2 = switch
    rel = analyze_edge_relationship(G1, v1, w1, v2, w2)
    
    print(f"\n{g1}")
    print(f"  Switch: ({v1},{w1}) <-> ({v2},{w2})")
    print(f"  Internal edges in S: {rel['internal']}")
    print(f"  Intersections: {rel['intersections']}")
    print("  External connection patterns:")
    for pattern, count in sorted(rel['ext_pattern_summary'].items()):
        # Translate pattern to readable form
        names = []
        for v in pattern:
            if v == v1: names.append('v1')
            elif v == w1: names.append('w1')
            elif v == v2: names.append('v2')
            elif v == w2: names.append('w2')
        print(f"    {{{','.join(names)}}}: {count} vertices")
