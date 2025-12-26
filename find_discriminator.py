"""
Systematically extract ALL local properties of the 11 cospectral switches
and compare to counterexamples to find discriminating conditions.
"""

import networkx as nx
import numpy as np
from itertools import combinations
import subprocess

def to_graph(g6):
    return nx.from_graph6_bytes(g6.encode())

def ws(G, vertices):
    return sum(1/(G.degree(x)-1) for x in vertices if G.degree(x) > 1)

def tri(G, u, v):
    return len(set(G.neighbors(u)) & set(G.neighbors(v)))

def get_all_properties(G, v1, w1, v2, w2):
    """Extract every conceivable local property."""
    S = {v1, v2, w1, w2}
    ext = {x: set(G.neighbors(x)) - S for x in S}
    
    props = {}
    
    # Degrees
    props['dv1'] = G.degree(v1)
    props['dw1'] = G.degree(w1)
    props['dv2'] = G.degree(v2)
    props['dw2'] = G.degree(w2)
    
    # External neighborhood sizes
    props['ext_v1'] = len(ext[v1])
    props['ext_w1'] = len(ext[w1])
    props['ext_v2'] = len(ext[v2])
    props['ext_w2'] = len(ext[w2])
    
    # Pairwise intersection sizes
    props['v1w1'] = len(ext[v1] & ext[w1])
    props['v2w2'] = len(ext[v2] & ext[w2])
    props['v1w2'] = len(ext[v1] & ext[w2])
    props['v2w1'] = len(ext[v2] & ext[w1])
    props['v1v2'] = len(ext[v1] & ext[v2])
    props['w1w2'] = len(ext[w1] & ext[w2])
    
    # Weighted sums
    props['ws_v1w1'] = ws(G, ext[v1] & ext[w1])
    props['ws_v2w2'] = ws(G, ext[v2] & ext[w2])
    props['ws_v1w2'] = ws(G, ext[v1] & ext[w2])
    props['ws_v2w1'] = ws(G, ext[v2] & ext[w1])
    props['ws_v1v2'] = ws(G, ext[v1] & ext[v2])
    props['ws_w1w2'] = ws(G, ext[w1] & ext[w2])
    
    # Triangles through edges
    props['tri_v1w1'] = tri(G, v1, w1)
    props['tri_v2w2'] = tri(G, v2, w2)
    props['tri_v1w2'] = tri(G, v1, w2)  # Will be created
    props['tri_v2w1'] = tri(G, v2, w1)  # Will be created
    
    # Internal edges within S
    props['e_v1v2'] = G.has_edge(v1, v2)
    props['e_w1w2'] = G.has_edge(w1, w2)
    props['e_v1w1'] = G.has_edge(v1, w1)  # Always True (being switched)
    props['e_v2w2'] = G.has_edge(v2, w2)  # Always True
    props['e_v1w2'] = G.has_edge(v1, w2)  # Always False (being added)
    props['e_v2w1'] = G.has_edge(v2, w1)  # Always False
    
    # Degree sequences of external neighbors
    props['ext_degs_v1'] = tuple(sorted([G.degree(x) for x in ext[v1]]))
    props['ext_degs_w1'] = tuple(sorted([G.degree(x) for x in ext[w1]]))
    props['ext_degs_v2'] = tuple(sorted([G.degree(x) for x in ext[v2]]))
    props['ext_degs_w2'] = tuple(sorted([G.degree(x) for x in ext[w2]]))
    
    # Degree sequences of intersection neighbors
    props['int_degs_v1w1'] = tuple(sorted([G.degree(x) for x in ext[v1] & ext[w1]]))
    props['int_degs_v2w2'] = tuple(sorted([G.degree(x) for x in ext[v2] & ext[w2]]))
    props['int_degs_v1w2'] = tuple(sorted([G.degree(x) for x in ext[v1] & ext[w2]]))
    props['int_degs_v2w1'] = tuple(sorted([G.degree(x) for x in ext[v2] & ext[w1]]))
    
    # Twin-like conditions
    props['ext_v1_eq_v2'] = ext[v1] == ext[v2]
    props['ext_w1_eq_w2'] = ext[w1] == ext[w2]
    
    # Symmetric difference sizes
    props['symdiff_v1v2'] = len(ext[v1].symmetric_difference(ext[v2]))
    props['symdiff_w1w2'] = len(ext[w1].symmetric_difference(ext[w2]))
    
    return props

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

# Load cospectral switches
pairs = []
with open('docs/78_pairs.txt') as f:
    for line in f:
        line = line.strip()
        if ',' in line:
            g1, g2 = line.split(',')
            pairs.append((g1, g2))

cospec_props = []
for g1, g2 in pairs:
    G1, G2 = to_graph(g1), to_graph(g2)
    switch = find_switch(G1, G2)
    if switch:
        props = get_all_properties(G1, *switch)
        cospec_props.append((g1, switch, props))

print(f"=== {len(cospec_props)} COSPECTRAL SWITCHES ===\n")

# Find counterexamples at n=8
def nbl_matrix(G):
    edges = [(u,v) for u,v in G.edges()] + [(v,u) for u,v in G.edges()]
    idx = {e:i for i,e in enumerate(edges)}
    n = len(edges)
    T = np.zeros((n, n))
    for (u,v), i in idx.items():
        d = G.degree(v)
        if d <= 1: continue
        for w in G.neighbors(v):
            if w != u:
                T[i, idx[(v,w)]] = 1.0 / (d - 1)
    return T

def spectra_equal(T1, T2, max_k=30):
    P1, P2 = T1.copy(), T2.copy()
    for k in range(1, max_k + 1):
        if not np.isclose(np.trace(P1), np.trace(P2), atol=1e-9):
            return False
        P1, P2 = P1 @ T1, P2 @ T2
    return True

result = subprocess.run(['geng', '-c', '-d2', '8'], capture_output=True, text=True)
graphs = [line.strip() for line in result.stdout.strip().split('\n') if line.strip()]

counter_props = []
for g6 in graphs:
    if len(counter_props) >= 50:
        break
    G = to_graph(g6)
    
    for e1, e2 in combinations(G.edges(), 2):
        if len(counter_props) >= 50:
            break
        for v1, w1 in [e1, e1[::-1]]:
            for v2, w2 in [e2, e2[::-1]]:
                if G.has_edge(v1, w2) or G.has_edge(v2, w1):
                    continue
                S = {v1, v2, w1, w2}
                if len(S) != 4:
                    continue
                if G.degree(v1) != G.degree(v2):
                    continue
                if G.degree(w1) != G.degree(w2):
                    continue
                
                ext = {x: set(G.neighbors(x)) - S for x in S}
                if len(ext[v1] & ext[w1]) != len(ext[v2] & ext[w1]):
                    continue
                if len(ext[v1] & ext[w2]) != len(ext[v2] & ext[w2]):
                    continue
                
                Gp = G.copy()
                Gp.remove_edge(v1, w1)
                Gp.remove_edge(v2, w2)
                Gp.add_edge(v1, w2)
                Gp.add_edge(v2, w1)
                
                if not spectra_equal(nbl_matrix(G), nbl_matrix(Gp)):
                    props = get_all_properties(G, v1, w1, v2, w2)
                    counter_props.append((g6, (v1, w1, v2, w2), props))
                    break

print(f"=== {len(counter_props)} COUNTEREXAMPLES (C1+C2 satisfied) ===\n")

# Find discriminating properties
print("PROPERTY COMPARISON:")
print("="*70)

# Check each derived condition
def check_condition(props, name, func):
    return func(props)

conditions = [
    ('tri_eq', lambda p: p['tri_v1w1'] == p['tri_v2w2']),
    ('tri_new_eq', lambda p: p['tri_v1w2'] == p['tri_v2w1']),
    ('ws_diag1', lambda p: np.isclose(p['ws_v1w1'], p['ws_v2w2'], atol=1e-9)),
    ('ws_diag2', lambda p: np.isclose(p['ws_v1w2'], p['ws_v2w1'], atol=1e-9)),
    ('ws_row1', lambda p: np.isclose(p['ws_v1w1'], p['ws_v1w2'], atol=1e-9)),
    ('ws_row2', lambda p: np.isclose(p['ws_v2w1'], p['ws_v2w2'], atol=1e-9)),
    ('ws_col1', lambda p: np.isclose(p['ws_v1w1'], p['ws_v2w1'], atol=1e-9)),
    ('ws_col2', lambda p: np.isclose(p['ws_v1w2'], p['ws_v2w2'], atol=1e-9)),
    ('ws_all_eq', lambda p: np.isclose(p['ws_v1w1'], p['ws_v2w2'], atol=1e-9) and 
                           np.isclose(p['ws_v1w1'], p['ws_v1w2'], atol=1e-9) and
                           np.isclose(p['ws_v1w1'], p['ws_v2w1'], atol=1e-9)),
    ('int_degs_diag1', lambda p: p['int_degs_v1w1'] == p['int_degs_v2w2']),
    ('int_degs_diag2', lambda p: p['int_degs_v1w2'] == p['int_degs_v2w1']),
    ('ext_degs_v', lambda p: p['ext_degs_v1'] == p['ext_degs_v2']),
    ('ext_degs_w', lambda p: p['ext_degs_w1'] == p['ext_degs_w2']),
    ('v1v2_overlap', lambda p: p['v1v2'] > 0),
    ('w1w2_overlap', lambda p: p['w1w2'] > 0),
    ('both_overlap', lambda p: p['v1v2'] > 0 and p['w1w2'] > 0),
    ('has_internal_vv', lambda p: p['e_v1v2']),
    ('has_internal_ww', lambda p: p['e_w1w2']),
    ('both_internal', lambda p: p['e_v1v2'] and p['e_w1w2']),
    ('nonempty_v1w1', lambda p: p['v1w1'] > 0),
    ('nonempty_v2w2', lambda p: p['v2w2'] > 0),
]

for cond_name, cond_func in conditions:
    cosp_pass = sum(1 for _, _, p in cospec_props if cond_func(p))
    ctr_pass = sum(1 for _, _, p in counter_props if cond_func(p))
    
    # Discriminating power: high cosp_pass, low ctr_pass
    if cosp_pass == len(cospec_props) and ctr_pass < len(counter_props):
        marker = " <-- CANDIDATE"
    elif cosp_pass == len(cospec_props):
        marker = " (all cospec pass)"
    else:
        marker = ""
    
    print(f"{cond_name:20s}: cospec={cosp_pass}/{len(cospec_props)}, counter={ctr_pass}/{len(counter_props)}{marker}")
