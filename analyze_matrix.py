"""
Analyze the full 2x2 weighted sum matrix structure.
Matrix: [[ws(v1,w1), ws(v1,w2)], [ws(v2,w1), ws(v2,w2)]]

Look for patterns that distinguish cospectral from counterexamples.
"""

import networkx as nx
import numpy as np
from itertools import combinations
import subprocess
from collections import Counter

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

def classify_matrix(a, b, c, d, tol=1e-9):
    """Classify the 2x2 matrix [[a,b],[c,d]] by symmetry type."""
    # Check various equalities
    all_equal = all(abs(x - a) < tol for x in [b, c, d])
    diag = abs(a - d) < tol and abs(b - c) < tol
    row1 = abs(a - b) < tol
    row2 = abs(c - d) < tol
    col1 = abs(a - c) < tol
    col2 = abs(b - d) < tol
    
    if all_equal:
        return 'all_equal'
    elif diag and row1 and row2:
        return 'doubly_stochastic'  # all rows and cols sum same, diag equal
    elif diag:
        return 'diag_only'
    elif row1 and row2:
        return 'row_sym'
    elif col1 and col2:
        return 'col_sym'
    else:
        return 'none'

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

cospec_types = Counter()
counter_types = Counter()

cospec_with_tri = Counter()
counter_with_tri = Counter()

for g6 in graphs:
    G = to_graph(g6)
    if min(dict(G.degree()).values()) < 2:
        continue
    
    for v1, w1, v2, w2, Gp in find_c1c2_switches(G):
        T_G, T_Gp = nbl_matrix(G), nbl_matrix(Gp)
        is_cospec = spectra_equal(T_G, T_Gp)
        
        S = {v1, v2, w1, w2}
        ext = {x: set(G.neighbors(x)) - S for x in S}
        
        a = ws(G, ext[v1] & ext[w1])
        b = ws(G, ext[v1] & ext[w2])
        c = ws(G, ext[v2] & ext[w1])
        d = ws(G, ext[v2] & ext[w2])
        
        mat_type = classify_matrix(a, b, c, d)
        
        tri_match = tri(G, v1, w1) == tri(G, v2, w2)
        combined = (mat_type, tri_match)
        
        if is_cospec:
            cospec_types[mat_type] += 1
            cospec_with_tri[combined] += 1
        else:
            counter_types[mat_type] += 1
            counter_with_tri[combined] += 1

print("=== Matrix type distribution ===")
print()
print(f"{'Type':<20} {'Cospec':>8} {'Counter':>8} {'Precision':>10}")
print("-" * 50)

all_types = set(cospec_types.keys()) | set(counter_types.keys())
for t in sorted(all_types):
    c = cospec_types[t]
    x = counter_types[t]
    total = c + x
    prec = c / total if total > 0 else 0
    print(f"{t:<20} {c:>8} {x:>8} {prec:>10.1%}")

print()
print("=== Matrix type + triangle match ===")
print()
print(f"{'Type':<30} {'Cospec':>8} {'Counter':>8} {'Precision':>10}")
print("-" * 60)

all_combined = set(cospec_with_tri.keys()) | set(counter_with_tri.keys())
for t in sorted(all_combined, key=lambda x: (x[0], not x[1])):
    c = cospec_with_tri[t]
    x = counter_with_tri[t]
    total = c + x
    prec = c / total if total > 0 else 0
    label = f"{t[0]} + tri={'Y' if t[1] else 'N'}"
    print(f"{label:<30} {c:>8} {x:>8} {prec:>10.1%}")

# Find best combination
print()
print("=== Best candidates for sufficient condition ===")
for t in sorted(all_combined, key=lambda x: (x[0], not x[1])):
    c = cospec_with_tri[t]
    x = counter_with_tri[t]
    if x == 0 and c > 0:
        print(f"SUFFICIENT: {t} → {c} cospectral, 0 counterexamples")
