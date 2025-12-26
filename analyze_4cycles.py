"""
Deep analysis: what local property predicts whether a switch preserves 4-cycles?

The switch removes (v1,w1), (v2,w2) and adds (v1,w2), (v2,w1).
A 4-cycle through both removed edges: v1-w1-x-w2-v2-... wait, that's not right.

Actually, let's think about 4-cycles that get created or destroyed.

4-cycle created by switch: uses at least one new edge (v1,w2) or (v2,w1)
4-cycle destroyed by switch: used at least one removed edge (v1,w1) or (v2,w2)
"""

import networkx as nx
import numpy as np
from itertools import combinations
import subprocess

def to_graph(g6):
    return nx.from_graph6_bytes(g6.encode())

def count_4cycles_through_edge(G, u, v):
    """Count 4-cycles containing edge (u,v)."""
    # 4-cycle: u-v-x-y-u where x ≠ u, y ≠ v, and (u,y), (v,x), (x,y) are edges
    count = 0
    for x in G.neighbors(v):
        if x == u:
            continue
        for y in G.neighbors(u):
            if y == v or y == x:
                continue
            if G.has_edge(x, y):
                count += 1
    return count // 2  # Each cycle counted twice

def count_4cycles_through_nonedge(G, u, v):
    """Count 4-cycles that would exist if (u,v) were an edge."""
    # Would create 4-cycle u-v-x-y-u if (v,x), (x,y), (y,u) exist
    count = 0
    for x in G.neighbors(v):
        if x == u:
            continue
        for y in G.neighbors(u):
            if y == v or y == x:
                continue
            if G.has_edge(x, y):
                count += 1
    return count // 2

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

def analyze_switch(G, v1, w1, v2, w2):
    """Analyze 4-cycle changes from switch."""
    # 4-cycles destroyed (through removed edges)
    c4_v1w1 = count_4cycles_through_edge(G, v1, w1)
    c4_v2w2 = count_4cycles_through_edge(G, v2, w2)
    
    # 4-cycles created (through new edges)
    c4_v1w2 = count_4cycles_through_nonedge(G, v1, w2)
    c4_v2w1 = count_4cycles_through_nonedge(G, v2, w1)
    
    return {
        'destroyed_v1w1': c4_v1w1,
        'destroyed_v2w2': c4_v2w2,
        'created_v1w2': c4_v1w2,
        'created_v2w1': c4_v2w1,
        'net': (c4_v1w2 + c4_v2w1) - (c4_v1w1 + c4_v2w2),
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

# Collect statistics
cospec_stats = []
counter_stats = []

count = 0
for g6 in graphs:
    G = to_graph(g6)
    if min(dict(G.degree()).values()) < 2:
        continue
    
    for v1, w1, v2, w2, Gp in find_c1c2_switches(G):
        count += 1
        T_G, T_Gp = nbl_matrix(G), nbl_matrix(Gp)
        is_cospec = spectra_equal(T_G, T_Gp)
        
        stats = analyze_switch(G, v1, w1, v2, w2)
        stats['tri_v1w1'] = tri(G, v1, w1)
        stats['tri_v2w2'] = tri(G, v2, w2)
        
        S = {v1, v2, w1, w2}
        ext = {x: set(G.neighbors(x)) - S for x in S}
        stats['ws_v1w1'] = ws(G, ext[v1] & ext[w1])
        stats['ws_v2w2'] = ws(G, ext[v2] & ext[w2])
        stats['ws_v1w2'] = ws(G, ext[v1] & ext[w2])
        stats['ws_v2w1'] = ws(G, ext[v2] & ext[w1])
        
        if is_cospec:
            cospec_stats.append(stats)
        else:
            counter_stats.append(stats)

print(f"Total (C1+C2) switches at n=8: {count}")
print(f"Cospectral: {len(cospec_stats)}, Counterexamples: {len(counter_stats)}")
print()

# Analyze patterns
print("=== 4-CYCLE ANALYSIS ===")
print()

# Check if net 4-cycle change predicts cospectrality
cospec_net = [s['net'] for s in cospec_stats]
counter_net = [s['net'] for s in counter_stats]

print("Net 4-cycle change (created - destroyed):")
print(f"  Cospectral: min={min(cospec_net)}, max={max(cospec_net)}, mean={np.mean(cospec_net):.2f}")
print(f"  Counter:    min={min(counter_net)}, max={max(counter_net)}, mean={np.mean(counter_net):.2f}")
print()

# How many have net=0?
cospec_zero = sum(1 for n in cospec_net if n == 0)
counter_zero = sum(1 for n in counter_net if n == 0)
print("Net = 0:")
print(f"  Cospectral: {cospec_zero}/{len(cospec_stats)} ({100*cospec_zero/len(cospec_stats):.1f}%)")
print(f"  Counter:    {counter_zero}/{len(counter_stats)} ({100*counter_zero/len(counter_stats):.1f}%)")
print()

# Check diagonal equality
def diag_equal(s, tol=1e-9):
    return (abs(s['ws_v1w1'] - s['ws_v2w2']) < tol and 
            abs(s['ws_v1w2'] - s['ws_v2w1']) < tol and
            s['tri_v1w1'] == s['tri_v2w2'])

cospec_diag = sum(1 for s in cospec_stats if diag_equal(s))
counter_diag = sum(1 for s in counter_stats if diag_equal(s))
print("Diagonal equality (ws and triangles):")
print(f"  Cospectral: {cospec_diag}/{len(cospec_stats)} ({100*cospec_diag/len(cospec_stats):.1f}%)")
print(f"  Counter:    {counter_diag}/{len(counter_stats)} ({100*counter_diag/len(counter_stats):.1f}%)")
print()

# Check if destroyed = created for each pair
def balanced(s):
    return (s['destroyed_v1w1'] == s['created_v1w2'] and 
            s['destroyed_v2w2'] == s['created_v2w1'])

cospec_bal = sum(1 for s in cospec_stats if balanced(s))
counter_bal = sum(1 for s in counter_stats if balanced(s))
print("Balanced (destroyed_v1w1=created_v1w2 AND destroyed_v2w2=created_v2w1):")
print(f"  Cospectral: {cospec_bal}/{len(cospec_stats)} ({100*cospec_bal/len(cospec_stats):.1f}%)")
print(f"  Counter:    {counter_bal}/{len(counter_stats)} ({100*counter_bal/len(counter_stats):.1f}%)")
