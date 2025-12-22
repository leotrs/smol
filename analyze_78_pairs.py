"""
Analyze the 78 NBL-cospectral pairs with min_degree >= 2.
Check which satisfy (C1)+(C2) and which satisfy (C2').
"""

import networkx as nx
import numpy as np

def to_graph(g6):
    return nx.from_graph6_bytes(g6.encode())

def weighted_sum(G, vertices):
    return sum(1/(G.degree(x)-1) for x in vertices if G.degree(x) > 1)

def find_switch(G1, G2):
    """Find if G1 and G2 differ by a 2-edge switch. Return switch params or None."""
    e1 = set(G1.edges())
    e2 = set(G2.edges())
    
    only_in_1 = e1 - e2
    only_in_2 = e2 - e1
    
    if len(only_in_1) != 2 or len(only_in_2) != 2:
        return None
    
    # Check if it's a valid 2-edge switch
    removed = list(only_in_1)
    added = list(only_in_2)
    
    # Try to identify v1, w1, v2, w2
    # Removed: (v1, w1), (v2, w2)
    # Added: (v1, w2), (v2, w1)
    for (a, b), (c, d) in [(removed[0], removed[1]), (removed[1], removed[0])]:
        for v1, w1 in [(a, b), (b, a)]:
            for v2, w2 in [(c, d), (d, c)]:
                expected_added = {(v1, w2), (w2, v1), (v2, w1), (w1, v2)}
                actual_added = {(x, y) for x, y in added} | {(y, x) for x, y in added}
                if expected_added & actual_added == expected_added:
                    return (v1, w1, v2, w2)
    return None

def check_c1(G, v1, w1, v2, w2):
    return G.degree(v1) == G.degree(v2) and G.degree(w1) == G.degree(w2)

def check_c2(G, v1, w1, v2, w2):
    S = {v1, v2, w1, w2}
    ext = {x: set(G.neighbors(x)) - S for x in S}
    return (len(ext[v1] & ext[w1]) == len(ext[v2] & ext[w1]) and
            len(ext[v1] & ext[w2]) == len(ext[v2] & ext[w2]))

def check_c2_prime(G, v1, w1, v2, w2, tol=1e-9):
    S = {v1, v2, w1, w2}
    ext = {x: set(G.neighbors(x)) - S for x in S}
    ws1_w1 = weighted_sum(G, ext[v1] & ext[w1])
    ws2_w1 = weighted_sum(G, ext[v2] & ext[w1])
    ws1_w2 = weighted_sum(G, ext[v1] & ext[w2])
    ws2_w2 = weighted_sum(G, ext[v2] & ext[w2])
    return (np.isclose(ws1_w1, ws2_w1, atol=tol) and 
            np.isclose(ws1_w2, ws2_w2, atol=tol))

# Load pairs
pairs = []
with open('docs/78_pairs.txt') as f:
    for line in f:
        line = line.strip()
        if ',' in line:
            g1, g2 = line.split(',')
            pairs.append((g1, g2))

print(f"Loaded {len(pairs)} pairs\n")

direct_switch = 0
satisfies_c1c2 = 0
satisfies_c2_prime = 0
not_direct_switch = []

for g1, g2 in pairs:
    G1 = to_graph(g1)
    G2 = to_graph(g2)
    
    switch = find_switch(G1, G2)
    
    if switch is None:
        not_direct_switch.append((g1, g2))
        continue
    
    direct_switch += 1
    v1, w1, v2, w2 = switch
    
    c1 = check_c1(G1, v1, w1, v2, w2)
    c2 = check_c2(G1, v1, w1, v2, w2)
    c2p = check_c2_prime(G1, v1, w1, v2, w2)
    
    if c1 and c2:
        satisfies_c1c2 += 1
    if c1 and c2p:
        satisfies_c2_prime += 1
    
    if c1 and c2 and not c2p:
        print(f"C2 but not C2': {g1}")
        S = {v1, v2, w1, w2}
        ext = {x: set(G1.neighbors(x)) - S for x in S}
        print(f"  switch: ({v1},{w1},{v2},{w2})")
        print(f"  ext(v1)∩ext(w1)={ext[v1]&ext[w1]}, ext(v2)∩ext(w1)={ext[v2]&ext[w1]}")
        for x in ext[v1] & ext[w1]:
            print(f"    deg({x})={G1.degree(x)}")
        for x in ext[v2] & ext[w1]:
            print(f"    deg({x})={G1.degree(x)}")

print("\n=== SUMMARY ===")
print(f"Total pairs: {len(pairs)}")
print(f"Direct 2-edge switches: {direct_switch}")
print(f"  Satisfy (C1)+(C2): {satisfies_c1c2}")
print(f"  Satisfy (C1)+(C2'): {satisfies_c2_prime}")
print(f"Not direct switches: {len(not_direct_switch)}")
