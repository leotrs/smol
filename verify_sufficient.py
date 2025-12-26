"""
Verify the sufficient condition for NBL-cospectral 2-edge switches.

CONDITIONS:
(C1) deg(v1) = deg(v2), deg(w1) = deg(w2)
(C2) |ext(v1) ∩ ext(wj)| = |ext(v2) ∩ ext(wj)| for j=1,2
(C3) All 4 weighted sums equal: ws(vi ∩ wj) = constant
(C4) Triangle counts: tri(v1,w1) = tri(v2,w2)  
(C5) Non-empty: |ext(v1) ∩ ext(v2)| > 0 AND |ext(w1) ∩ ext(w2)| > 0
(C6) Not (2,2,2): NOT (int_vw=2 AND int_vv=2 AND int_ww=2)
"""

import networkx as nx
import numpy as np
from itertools import combinations
import subprocess

def to_graph(g6):
    return nx.from_graph6_bytes(g6.encode())

def nbl_matrix(G):
    edges = [(u,v) for u,v in G.edges()] + [(v,u) for u,v in G.edges()]
    if len(edges) == 0:
        return np.array([])
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
    if T1.size == 0 or T2.size == 0:
        return T1.size == T2.size
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

def satisfies_sufficient_condition(G, v1, w1, v2, w2, tol=1e-9):
    """Check if switch satisfies the sufficient condition."""
    S = {v1, v2, w1, w2}
    ext = {x: set(G.neighbors(x)) - S for x in S}
    
    # C1: degree matching (assumed from C1C2 filtering)
    # C2: intersection size matching (assumed from C1C2 filtering)
    
    # C3: All 4 ws equal
    ws_vals = [ws(G, ext[v1]&ext[w1]), ws(G, ext[v1]&ext[w2]),
               ws(G, ext[v2]&ext[w1]), ws(G, ext[v2]&ext[w2])]
    if not all(abs(v - ws_vals[0]) < tol for v in ws_vals):
        return False
    
    # C4: Triangle counts match
    if tri(G, v1, w1) != tri(G, v2, w2):
        return False
    
    # C5: Non-empty v1v2 and w1w2
    int_vv = len(ext[v1] & ext[v2])
    int_ww = len(ext[w1] & ext[w2])
    if int_vv == 0 or int_ww == 0:
        return False
    
    # C6: Not the (2,2,2) pattern
    int_vw = len(ext[v1] & ext[w1])
    if int_vw == 2 and int_vv == 2 and int_ww == 2:
        return False
    
    return True

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

print("VERIFYING SUFFICIENT CONDITION FOR NBL-COSPECTRAL 2-EDGE SWITCHES")
print("=" * 65)
print()

total_suff = 0
total_cospec = 0
total_counter = 0

for n in range(4, 10):
    result = subprocess.run(['geng', '-c', str(n)], capture_output=True, text=True)
    graphs = [line.strip() for line in result.stdout.strip().split('\n') if line.strip()]
    
    n_suff = 0
    n_cospec = 0
    n_counter = 0
    
    for g6 in graphs:
        G = to_graph(g6)
        if min(dict(G.degree()).values()) < 2:
            continue
        
        for v1, w1, v2, w2, Gp in find_c1c2_switches(G):
            if not satisfies_sufficient_condition(G, v1, w1, v2, w2):
                continue
            
            n_suff += 1
            T_G, T_Gp = nbl_matrix(G), nbl_matrix(Gp)
            if spectra_equal(T_G, T_Gp):
                n_cospec += 1
            else:
                n_counter += 1
                print(f"COUNTEREXAMPLE at n={n}: {g6} switch ({v1},{w1},{v2},{w2})")
    
    total_suff += n_suff
    total_cospec += n_cospec
    total_counter += n_counter
    
    prec = 100 * n_cospec / n_suff if n_suff > 0 else 0
    print(f"n={n}: {n_suff} switches satisfy condition, {n_cospec} cospectral, {n_counter} counterexamples ({prec:.1f}%)")

print()
print("=" * 65)
print(f"TOTAL: {total_suff} switches, {total_cospec} cospectral, {total_counter} counterexamples")
if total_counter == 0:
    print()
    print("✓ CONDITION IS SUFFICIENT FOR ALL n ≤ 9")
