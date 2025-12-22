"""
Counterexample search: Find (C1)+(C2) switches that are NOT NBL-cospectral.
"""

import subprocess

import networkx as nx
import numpy as np
from itertools import combinations

def to_graph(g6):
    return nx.from_graph6_bytes(g6.encode())

def nbl_matrix(G):
    """Compute the NBL transition matrix."""
    # Directed edges (u,v) where uv is an edge
    edges = []
    for u, v in G.edges():
        edges.append((u, v))
        edges.append((v, u))
    
    edge_to_idx = {e: i for i, e in enumerate(edges)}
    n = len(edges)
    T = np.zeros((n, n))
    
    for (u, v), i in edge_to_idx.items():
        deg_v = G.degree(v)
        if deg_v <= 1:
            continue
        for w in G.neighbors(v):
            if w != u:  # non-backtracking
                j = edge_to_idx[(v, w)]
                T[i, j] = 1.0 / (deg_v - 1)
    
    return T

def nbl_spectrum(G):
    """Compute NBL eigenvalues, sorted by (real, imag)."""
    T = nbl_matrix(G)
    eigs = np.linalg.eigvals(T)
    # Sort by real part, then imaginary part
    eigs = sorted(eigs, key=lambda x: (x.real, x.imag))
    return np.array(eigs)

def spectra_equal(eigs1, eigs2, tol=1e-8):
    """Check if two spectra are equal up to tolerance."""
    if len(eigs1) != len(eigs2):
        return False
    return np.allclose(sorted(eigs1, key=lambda x: (x.real, x.imag)),
                       sorted(eigs2, key=lambda x: (x.real, x.imag)),
                       atol=tol)

def find_c1c2_switches(G):
    """Find all (C1)+(C2) switches in G. Returns list of (v1,w1,v2,w2,G')."""
    results = []
    
    for e1, e2 in combinations(G.edges(), 2):
        for v1, w1 in [e1, e1[::-1]]:
            for v2, w2 in [e2, e2[::-1]]:
                # Check switch is valid
                if G.has_edge(v1, w2) or G.has_edge(v2, w1):
                    continue
                
                S = {v1, v2, w1, w2}
                if len(S) != 4:
                    continue
                
                # (C1): degree equality
                if G.degree(v1) != G.degree(v2):
                    continue
                if G.degree(w1) != G.degree(w2):
                    continue
                
                # (C2): pairwise intersection equality
                ext = {x: set(G.neighbors(x)) - S for x in S}
                if len(ext[v1] & ext[w1]) != len(ext[v2] & ext[w1]):
                    continue
                if len(ext[v1] & ext[w2]) != len(ext[v2] & ext[w2]):
                    continue
                
                # Create switched graph
                Gp = G.copy()
                Gp.remove_edge(v1, w1)
                Gp.remove_edge(v2, w2)
                Gp.add_edge(v1, w2)
                Gp.add_edge(v2, w1)
                
                results.append((v1, w1, v2, w2, Gp))
    
    return results

# Search through SMOL graphs
print("Loading graphs from SMOL...")

# We'll generate small graphs and check exhaustively

def generate_graphs(n):
    """Generate all connected graphs on n vertices using geng."""
    result = subprocess.run(['geng', '-c', str(n)], capture_output=True, text=True)
    return [line.strip() for line in result.stdout.strip().split('\n') if line.strip()]

counterexamples = []
total_switches = 0

for n in range(4, 9):  # Start small
    print(f"\n=== n = {n} ===")
    graphs = generate_graphs(n)
    print(f"Generated {len(graphs)} connected graphs")
    
    n_switches_this_n = 0
    
    for i, g6 in enumerate(graphs):
        G = to_graph(g6)
        
        # Skip if min degree < 2 (NBL degenerates)
        if min(dict(G.degree()).values()) < 2:
            continue
        
        switches = find_c1c2_switches(G)
        
        for v1, w1, v2, w2, Gp in switches:
            n_switches_this_n += 1
            total_switches += 1
            
            # Check NBL cospectrality
            spec_G = nbl_spectrum(G)
            spec_Gp = nbl_spectrum(Gp)
            
            if not spectra_equal(spec_G, spec_Gp):
                counterexamples.append({
                    'g6': g6,
                    'switch': (v1, w1, v2, w2),
                    'spec_G': spec_G,
                    'spec_Gp': spec_Gp
                })
                print(f"  COUNTEREXAMPLE: {g6}, switch ({v1},{w1},{v2},{w2})")
                print(f"    spec_G:  {spec_G[:5]}...")
                print(f"    spec_Gp: {spec_Gp[:5]}...")
    
    print(f"  Checked {n_switches_this_n} (C1)+(C2) switches, {len(counterexamples)} counterexamples so far")

print("\n=== SUMMARY ===")
print(f"Total (C1)+(C2) switches checked: {total_switches}")
print(f"Counterexamples found: {len(counterexamples)}")

if counterexamples:
    print("\nCounterexamples:")
    for ce in counterexamples[:10]:
        print(f"  {ce['g6']}, switch {ce['switch']}")
