"""
Check if external connection patterns have swap symmetry:
swapping v1<->v2 and w1<->w2 gives the same multiset.
"""

import networkx as nx
from collections import Counter

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

def get_ext_patterns(G, v1, w1, v2, w2):
    """Get external connection patterns."""
    S = {v1, v2, w1, w2}
    ext = {x: set(G.neighbors(x)) - S for x in S}
    all_ext = ext[v1] | ext[w1] | ext[v2] | ext[w2]
    
    patterns = []
    for x in all_ext:
        # Which of S does x connect to?
        connected = frozenset(v for v in S if G.has_edge(x, v))
        patterns.append(connected)
    
    return patterns, S

def swap_pattern(pattern, v1, w1, v2, w2):
    """Apply swap v1<->v2, w1<->w2 to a pattern."""
    swap_map = {v1: v2, v2: v1, w1: w2, w2: w1}
    return frozenset(swap_map[v] for v in pattern)

def check_swap_symmetry(G, v1, w1, v2, w2):
    """Check if patterns are invariant under v1<->v2, w1<->w2 swap."""
    patterns, S = get_ext_patterns(G, v1, w1, v2, w2)
    
    original = Counter(patterns)
    swapped = Counter(swap_pattern(p, v1, w1, v2, w2) for p in patterns)
    
    return original == swapped, original, swapped

# Load pairs
pairs = []
with open('docs/78_pairs.txt') as f:
    for line in f:
        line = line.strip()
        if ',' in line:
            g1, g2 = line.split(',')
            pairs.append((g1, g2))

print("="*70)
print("Swap symmetry check: v1<->v2, w1<->w2")
print("="*70)

for g1, g2 in pairs:
    G1, G2 = to_graph(g1), to_graph(g2)
    switch = find_switch(G1, G2)
    if not switch:
        continue
    
    v1, w1, v2, w2 = switch
    is_symmetric, orig, swapped = check_swap_symmetry(G1, v1, w1, v2, w2)
    
    print(f"\n{g1}")
    print(f"  Switch: ({v1},{w1}) <-> ({v2},{w2})")
    print(f"  Swap symmetric: {is_symmetric}")
    if not is_symmetric:
        print(f"  Original: {dict(orig)}")
        print(f"  Swapped:  {dict(swapped)}")
