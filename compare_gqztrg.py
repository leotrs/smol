"""
Deep comparison: all properties of GQzTrg counterexample vs 11 cospectral.
"""

import networkx as nx

def to_graph(g6):
    return nx.from_graph6_bytes(g6.encode())

def ws(G, vertices):
    return sum(1/(G.degree(x)-1) for x in vertices if G.degree(x) > 1)

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

def full_analysis(G, v1, w1, v2, w2):
    S = {v1, v2, w1, w2}
    ext = {x: set(G.neighbors(x)) - S for x in S}
    
    # All pairwise intersections
    pairs = [(v1,w1,'v1w1'), (v2,w2,'v2w2'), (v1,w2,'v1w2'), (v2,w1,'v2w1'),
             (v1,v2,'v1v2'), (w1,w2,'w1w2')]
    
    result = {}
    for a, b, name in pairs:
        inter = ext[a] & ext[b]
        result[f'{name}_size'] = len(inter)
        result[f'{name}_ws'] = round(ws(G, inter), 4)
        result[f'{name}_degs'] = tuple(sorted([G.degree(x) for x in inter]))
    
    # Degrees
    result['deg_v'] = G.degree(v1)
    result['deg_w'] = G.degree(w1)
    
    # Internal edges
    result['e_v1v2'] = G.has_edge(v1, v2)
    result['e_w1w2'] = G.has_edge(w1, w2)
    
    # Triangles
    result['tri_v1w1'] = len(set(G.neighbors(v1)) & set(G.neighbors(w1)))
    result['tri_v2w2'] = len(set(G.neighbors(v2)) & set(G.neighbors(w2)))
    
    # Union sizes
    result['union_v1w1'] = len(ext[v1] | ext[w1])
    result['union_v2w2'] = len(ext[v2] | ext[w2])
    
    # External sizes
    result['ext_v1'] = len(ext[v1])
    result['ext_w1'] = len(ext[w1])
    
    return result

# Counterexample
G = to_graph('GQzTrg')
counter = full_analysis(G, 0, 2, 1, 3)
print("COUNTEREXAMPLE GQzTrg (0,2,1,3):")
for k, v in sorted(counter.items()):
    print(f"  {k}: {v}")

# Cospectral
pairs = []
with open('docs/78_pairs.txt') as f:
    for line in f:
        line = line.strip()
        if ',' in line:
            g1, g2 = line.split(',')
            pairs.append((g1, g2))

print("\n" + "="*60)
print("COSPECTRAL CASES:")
print("="*60)

for g1, g2 in pairs:
    G1, G2 = to_graph(g1), to_graph(g2)
    switch = find_switch(G1, G2)
    if switch:
        cosp = full_analysis(G1, *switch)
        print(f"\n{g1[:12]} sw={switch}:")
        # Show key differences from counterexample
        diffs = []
        for k in counter:
            if counter[k] != cosp.get(k):
                diffs.append(f"{k}: {cosp.get(k)} (vs {counter[k]})")
        if diffs:
            for d in diffs[:5]:
                print(f"  {d}")
        else:
            print("  IDENTICAL to counterexample!")
