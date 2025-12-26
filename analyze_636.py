"""
Analyze the 636 counterexamples that have all_equal ws + matching triangles.
What else differs?
"""

import networkx as nx
import numpy as np
from itertools import combinations
import subprocess

def to_graph(g6):
    return nx.from_graph6_bytes(g6.encode())

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

def spectra_equal(T1, T2, max_k=50):
    P1, P2 = T1.copy(), T2.copy()
    for k in range(1, max_k + 1):
        if not np.isclose(np.trace(P1), np.trace(P2), atol=1e-9):
            return False
        P1, P2 = P1 @ T1, P2 @ T2
    return True

def ws(G, vertices):
    return sum(1/(G.degree(x)-1) for x in vertices if G.degree(x) > 1)

def tri(G, u, v):
    return len(set(G.neighbors(u)) & set(G.neighbors(v)))

def all_equal_ws(G, v1, w1, v2, w2, tol=1e-9):
    S = {v1, v2, w1, w2}
    ext = {x: set(G.neighbors(x)) - S for x in S}
    vals = [
        ws(G, ext[v1] & ext[w1]),
        ws(G, ext[v1] & ext[w2]),
        ws(G, ext[v2] & ext[w1]),
        ws(G, ext[v2] & ext[w2]),
    ]
    return all(abs(v - vals[0]) < tol for v in vals)

def get_ext_structure(G, v1, w1, v2, w2):
    """Get detailed external structure."""
    S = {v1, v2, w1, w2}
    ext = {x: set(G.neighbors(x)) - S for x in S}
    
    # External neighborhood sizes
    sizes = {x: len(ext[x]) for x in S}
    
    # Intersection sizes (all 6 pairs)
    int_sizes = {
        'v1w1': len(ext[v1] & ext[w1]),
        'v1w2': len(ext[v1] & ext[w2]),
        'v2w1': len(ext[v2] & ext[w1]),
        'v2w2': len(ext[v2] & ext[w2]),
        'v1v2': len(ext[v1] & ext[v2]),
        'w1w2': len(ext[w1] & ext[w2]),
    }
    
    # Degree multisets of external neighbors
    deg_multisets = {x: tuple(sorted(G.degree(y) for y in ext[x])) for x in S}
    
    # Check if ext degree multisets match
    v_deg_match = deg_multisets[v1] == deg_multisets[v2]
    w_deg_match = deg_multisets[w1] == deg_multisets[w2]
    
    return {
        'sizes': sizes,
        'int_sizes': int_sizes,
        'deg_multisets': deg_multisets,
        'v_deg_match': v_deg_match,
        'w_deg_match': w_deg_match,
    }

def find_c1c2_switches(G):
    results = []
    for e1, e2 in combinations(G.edges(), 2):
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
                results.append((v1, w1, v2, w2, Gp))
    return results

result = subprocess.run(['geng', '-c', '8'], capture_output=True, text=True)
graphs = [line.strip() for line in result.stdout.strip().split('\n') if line.strip()]

# Collect all_equal + tri=Y cases
cospec_cases = []
counter_cases = []

for g6 in graphs:
    G = to_graph(g6)
    if min(dict(G.degree()).values()) < 2:
        continue
    
    for v1, w1, v2, w2, Gp in find_c1c2_switches(G):
        if not all_equal_ws(G, v1, w1, v2, w2):
            continue
        if tri(G, v1, w1) != tri(G, v2, w2):
            continue
        
        T_G, T_Gp = nbl_matrix(G), nbl_matrix(Gp)
        is_cospec = spectra_equal(T_G, T_Gp)
        
        struct = get_ext_structure(G, v1, w1, v2, w2)
        
        if is_cospec:
            cospec_cases.append((g6, (v1, w1, v2, w2), struct))
        else:
            counter_cases.append((g6, (v1, w1, v2, w2), struct))

print(f"all_equal + tri=Y: {len(cospec_cases)} cospectral, {len(counter_cases)} counterexamples")
print()

# Compare external degree multiset matching
cospec_both_match = sum(1 for _, _, s in cospec_cases if s['v_deg_match'] and s['w_deg_match'])
counter_both_match = sum(1 for _, _, s in counter_cases if s['v_deg_match'] and s['w_deg_match'])

print("External degree multiset matching (ext(v1) degs = ext(v2) degs AND ext(w1) degs = ext(w2) degs):")
print(f"  Cospectral: {cospec_both_match}/{len(cospec_cases)} ({100*cospec_both_match/len(cospec_cases):.1f}%)")
print(f"  Counter:    {counter_both_match}/{len(counter_cases)} ({100*counter_both_match/len(counter_cases):.1f}%)")
print()

# Compare v1v2 and w1w2 intersection sizes
cospec_v1v2 = [s['int_sizes']['v1v2'] for _, _, s in cospec_cases]
counter_v1v2 = [s['int_sizes']['v1v2'] for _, _, s in counter_cases]
cospec_w1w2 = [s['int_sizes']['w1w2'] for _, _, s in cospec_cases]
counter_w1w2 = [s['int_sizes']['w1w2'] for _, _, s in counter_cases]

print("v1∩v2 intersection size:")
print(f"  Cospectral: mean={np.mean(cospec_v1v2):.2f}, zeros={sum(1 for x in cospec_v1v2 if x==0)}")
print(f"  Counter:    mean={np.mean(counter_v1v2):.2f}, zeros={sum(1 for x in counter_v1v2 if x==0)}")
print()

print("w1∩w2 intersection size:")
print(f"  Cospectral: mean={np.mean(cospec_w1w2):.2f}, zeros={sum(1 for x in cospec_w1w2 if x==0)}")
print(f"  Counter:    mean={np.mean(counter_w1w2):.2f}, zeros={sum(1 for x in counter_w1w2 if x==0)}")
print()

# Show some counterexamples
print("First 5 counterexamples (all_equal + tri=Y):")
for g6, sw, s in counter_cases[:5]:
    print(f"  {g6} sw={sw}")
    print(f"    int_sizes: {s['int_sizes']}")
    print(f"    v_deg_match: {s['v_deg_match']}, w_deg_match: {s['w_deg_match']}")
    print()
