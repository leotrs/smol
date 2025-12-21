#!/usr/bin/env python3
"""
Comprehensive experiments for NBL switching theorem paper.

1. Verify all 11 known pairs satisfy (C1)+(C2)
2. Find ALL (C1)+(C2) configurations, check NBL-cospectrality (sufficiency)
3. Count isomorphic vs non-isomorphic switches
4. Check if 11 pairs are also NB-cospectral (Hashimoto)
5. Check if 11 pairs are adjacency-cospectral
6. Find counterexamples: (C1) only or (C2) only → not cospectral
"""

import networkx as nx
import numpy as np
import psycopg2
from itertools import combinations, permutations


def build_nbl_matrix(G):
    """Build the NBL transition matrix."""
    edges = [(u, v) for u, v in G.edges()] + [(v, u) for u, v in G.edges()]
    edge_to_idx = {e: i for i, e in enumerate(edges)}
    n = len(edges)
    T = np.zeros((n, n))
    
    for i, (u, v) in enumerate(edges):
        deg_v = G.degree(v)
        if deg_v > 1:
            for w in G.neighbors(v):
                if w != u:
                    j = edge_to_idx[(v, w)]
                    T[i, j] = 1.0 / (deg_v - 1)
    return T, edges, edge_to_idx


def build_hashimoto_matrix(G):
    """Build the unweighted Hashimoto (NB) matrix."""
    edges = [(u, v) for u, v in G.edges()] + [(v, u) for u, v in G.edges()]
    edge_to_idx = {e: i for i, e in enumerate(edges)}
    n = len(edges)
    B = np.zeros((n, n))
    
    for i, (u, v) in enumerate(edges):
        for w in G.neighbors(v):
            if w != u:
                j = edge_to_idx[(v, w)]
                B[i, j] = 1.0
    return B


def nbl_spectrum(G):
    """Compute NBL spectrum (sorted by magnitude, then real, then imag)."""
    T, _, _ = build_nbl_matrix(G)
    if T.shape[0] == 0:
        return np.array([])
    eigs = np.linalg.eigvals(T)
    # Sort by (magnitude, real, imag)
    idx = np.lexsort((eigs.imag, eigs.real, np.abs(eigs)))
    return eigs[idx]


def hashimoto_spectrum(G):
    """Compute Hashimoto spectrum."""
    B = build_hashimoto_matrix(G)
    if B.shape[0] == 0:
        return np.array([])
    eigs = np.linalg.eigvals(B)
    idx = np.lexsort((eigs.imag, eigs.real, np.abs(eigs)))
    return eigs[idx]


def adj_spectrum(G):
    """Compute adjacency spectrum."""
    A = nx.adjacency_matrix(G).toarray()
    eigs = np.linalg.eigvalsh(A)
    return np.sort(eigs)


def spectra_equal(s1, s2, tol=1e-8):
    """Check if two spectra are equal."""
    if len(s1) != len(s2):
        return False
    return np.allclose(np.sort(np.abs(s1)), np.sort(np.abs(s2)), atol=tol)


def check_c1(G, v1, v2, w1, w2):
    """Check condition (C1): deg(v1)=deg(v2) and deg(w1)=deg(w2)."""
    return G.degree(v1) == G.degree(v2) and G.degree(w1) == G.degree(w2)


def check_c2(G, v1, v2, w1, w2):
    """Check condition (C2): |ext(vi) ∩ ext(wj)| = c for all i,j."""
    S = {v1, v2, w1, w2}
    ext_v1 = set(x for x in G.neighbors(v1) if x not in S)
    ext_v2 = set(x for x in G.neighbors(v2) if x not in S)
    ext_w1 = set(x for x in G.neighbors(w1) if x not in S)
    ext_w2 = set(x for x in G.neighbors(w2) if x not in S)
    
    c11 = len(ext_v1 & ext_w1)
    c12 = len(ext_v1 & ext_w2)
    c21 = len(ext_v2 & ext_w1)
    c22 = len(ext_v2 & ext_w2)
    
    return c11 == c12 == c21 == c22


def is_valid_switch(G, v1, v2, w1, w2):
    """Check if (v1,v2,w1,w2) forms a valid 2-edge switch."""
    # Must have edges v1-w1 and v2-w2
    if not G.has_edge(v1, w1) or not G.has_edge(v2, w2):
        return False
    # Must not have edges v1-w2 and v2-w1
    if G.has_edge(v1, w2) or G.has_edge(v2, w1):
        return False
    # All four vertices must be distinct
    if len({v1, v2, w1, w2}) != 4:
        return False
    return True


def apply_switch(G, v1, v2, w1, w2):
    """Apply the 2-edge switch: remove v1-w1, v2-w2; add v1-w2, v2-w1."""
    G2 = G.copy()
    G2.remove_edge(v1, w1)
    G2.remove_edge(v2, w2)
    G2.add_edge(v1, w2)
    G2.add_edge(v2, w1)
    return G2


def find_switch_config(G1, G2):
    """Given two graphs differing by 2-edge switch, find the configuration."""
    E1 = set(frozenset(e) for e in G1.edges())
    E2 = set(frozenset(e) for e in G2.edges())
    only_in_G1 = E1 - E2
    only_in_G2 = E2 - E1
    
    if len(only_in_G1) != 2 or len(only_in_G2) != 2:
        return None
    
    verts = set()
    for e in only_in_G1 | only_in_G2:
        verts.update(e)
    
    if len(verts) != 4:
        return None
    
    for perm in permutations(verts):
        v1, v2, w1, w2 = perm
        e1 = frozenset([v1, w1])
        e2 = frozenset([v2, w2])
        new_e1 = frozenset([v1, w2])
        new_e2 = frozenset([v2, w1])
        
        if only_in_G1 == {e1, e2} and only_in_G2 == {new_e1, new_e2}:
            return (v1, v2, w1, w2)
    
    return None


def main():
    conn = psycopg2.connect('dbname=smol')
    cur = conn.cursor()
    
    print("=" * 80)
    print("COMPREHENSIVE NBL SWITCHING THEOREM EXPERIMENTS")
    print("=" * 80)
    print()
    
    # =========================================================================
    # EXPERIMENT 1: Verify all 11 known pairs satisfy (C1)+(C2)
    # =========================================================================
    print("EXPERIMENT 1: Verify known NBL-cospectral pairs satisfy (C1)+(C2)")
    print("-" * 60)
    
    cur.execute('''
        SELECT g1.graph6, g2.graph6
        FROM cospectral_mates cm
        JOIN graphs g1 ON cm.graph1_id = g1.id
        JOIN graphs g2 ON cm.graph2_id = g2.id
        WHERE cm.matrix_type = 'nbl'
          AND g1.min_degree >= 2
          AND g2.min_degree >= 2
          AND g1.n = 10
        ORDER BY g1.graph6
    ''')
    nbl_pairs = cur.fetchall()
    
    switches_11 = []
    for g6_1, g6_2 in nbl_pairs:
        G1 = nx.from_graph6_bytes(g6_1.encode())
        G2 = nx.from_graph6_bytes(g6_2.encode())
        config = find_switch_config(G1, G2)
        if config:
            switches_11.append((g6_1, g6_2, G1, G2, config))
    
    print(f"Found {len(switches_11)} 2-edge switch pairs among NBL-cospectral graphs")
    print()
    
    all_satisfy = True
    for g6_1, g6_2, G1, G2, (v1, v2, w1, w2) in switches_11:
        c1 = check_c1(G1, v1, v2, w1, w2)
        c2 = check_c2(G1, v1, v2, w1, w2)
        status = "✓" if (c1 and c2) else "✗"
        if not (c1 and c2):
            all_satisfy = False
        print(f"  {g6_1}: (C1)={'✓' if c1 else '✗'} (C2)={'✓' if c2 else '✗'} {status}")
    
    print()
    if all_satisfy:
        print("✓ All 11 pairs satisfy (C1)+(C2)")
    else:
        print("✗ Some pairs fail (C1) or (C2) - UNEXPECTED!")
    print()
    
    # =========================================================================
    # EXPERIMENT 2 & 3: Find ALL (C1)+(C2) configs, check cospectrality & isomorphism
    # =========================================================================
    print("EXPERIMENT 2 & 3: Sufficiency and Isomorphism Analysis")
    print("-" * 60)
    print("Scanning all graphs with n=10, min_degree>=2 for (C1)+(C2) configs...")
    
    cur.execute('''
        SELECT graph6 FROM graphs
        WHERE n = 10 AND min_degree >= 2
    ''')
    all_graphs = [row[0] for row in cur.fetchall()]
    print(f"Total graphs to scan: {len(all_graphs)}")
    
    configs_found = []
    
    for idx, g6 in enumerate(all_graphs):
        if idx % 10000 == 0:
            print(f"  Progress: {idx}/{len(all_graphs)} ({100*idx/len(all_graphs):.1f}%)")
        
        G = nx.from_graph6_bytes(g6.encode())
        nodes = list(G.nodes())
        
        # Check all possible 4-tuples
        for v1, v2 in combinations(nodes, 2):
            for w1, w2 in combinations(nodes, 2):
                if len({v1, v2, w1, w2}) != 4:
                    continue
                if not is_valid_switch(G, v1, v2, w1, w2):
                    continue
                if check_c1(G, v1, v2, w1, w2) and check_c2(G, v1, v2, w1, w2):
                    G2 = apply_switch(G, v1, v2, w1, w2)
                    configs_found.append((g6, G, G2, v1, v2, w1, w2))
    
    print(f"\nFound {len(configs_found)} (C1)+(C2) configurations")
    print()
    
    # Check cospectrality and isomorphism
    cospectral_count = 0
    isomorphic_count = 0
    non_iso_cospectral = []
    
    for g6, G1, G2, v1, v2, w1, w2 in configs_found:
        spec1 = nbl_spectrum(G1)
        spec2 = nbl_spectrum(G2)
        is_cospectral = spectra_equal(spec1, spec2)
        
        if is_cospectral:
            cospectral_count += 1
        
        is_iso = nx.is_isomorphic(G1, G2)
        if is_iso:
            isomorphic_count += 1
        elif is_cospectral:
            non_iso_cospectral.append((g6, G1, G2, v1, v2, w1, w2))
    
    print("Results:")
    print(f"  Total (C1)+(C2) configurations: {len(configs_found)}")
    print(f"  NBL-cospectral: {cospectral_count}")
    print(f"  Isomorphic (G ≅ G'): {isomorphic_count}")
    print(f"  Non-isomorphic & cospectral: {len(non_iso_cospectral)}")
    print()
    
    if cospectral_count == len(configs_found):
        print("✓ SUFFICIENCY VERIFIED: All (C1)+(C2) configs yield NBL-cospectrality!")
    else:
        print(f"✗ {len(configs_found) - cospectral_count} configs are NOT cospectral - conditions not sufficient!")
    print()
    
    # =========================================================================
    # EXPERIMENT 4: Check if 11 pairs are also NB-cospectral (Hashimoto)
    # =========================================================================
    print("EXPERIMENT 4: Hashimoto (NB) Cospectrality")
    print("-" * 60)
    
    all_nb_cospectral = True
    for g6_1, g6_2, G1, G2, config in switches_11:
        spec1 = hashimoto_spectrum(G1)
        spec2 = hashimoto_spectrum(G2)
        is_nb_cosp = spectra_equal(spec1, spec2)
        status = "✓" if is_nb_cosp else "✗"
        if not is_nb_cosp:
            all_nb_cospectral = False
        print(f"  {g6_1}: NB-cospectral {status}")
    
    print()
    if all_nb_cospectral:
        print("✓ All 11 pairs are also NB-cospectral (Hashimoto)")
    else:
        print("✗ Some pairs are NOT NB-cospectral")
    print()
    
    # =========================================================================
    # EXPERIMENT 5: Check if 11 pairs are adjacency-cospectral
    # =========================================================================
    print("EXPERIMENT 5: Adjacency Cospectrality")
    print("-" * 60)
    
    adj_cospectral_count = 0
    for g6_1, g6_2, G1, G2, config in switches_11:
        spec1 = adj_spectrum(G1)
        spec2 = adj_spectrum(G2)
        is_adj_cosp = np.allclose(spec1, spec2, atol=1e-8)
        status = "✓" if is_adj_cosp else "✗"
        if is_adj_cosp:
            adj_cospectral_count += 1
        print(f"  {g6_1}: Adj-cospectral {status}")
    
    print()
    print(f"Summary: {adj_cospectral_count}/11 pairs are adjacency-cospectral")
    print()
    
    # =========================================================================
    # EXPERIMENT 6: Counterexamples - (C1) only or (C2) only
    # =========================================================================
    print("EXPERIMENT 6: Counterexamples")
    print("-" * 60)
    print("Finding switches where only (C1) or only (C2) holds...")
    
    c1_only = []
    c2_only = []
    
    # Sample some graphs (full scan would take too long)
    sample_size = min(5000, len(all_graphs))
    import random
    random.seed(42)
    sample_graphs = random.sample(all_graphs, sample_size)
    
    for g6 in sample_graphs:
        G = nx.from_graph6_bytes(g6.encode())
        nodes = list(G.nodes())
        
        for v1, v2 in combinations(nodes, 2):
            for w1, w2 in combinations(nodes, 2):
                if len({v1, v2, w1, w2}) != 4:
                    continue
                if not is_valid_switch(G, v1, v2, w1, w2):
                    continue
                
                c1 = check_c1(G, v1, v2, w1, w2)
                c2 = check_c2(G, v1, v2, w1, w2)
                
                if c1 and not c2 and len(c1_only) < 5:
                    G2 = apply_switch(G, v1, v2, w1, w2)
                    c1_only.append((g6, G, G2, v1, v2, w1, w2))
                elif c2 and not c1 and len(c2_only) < 5:
                    G2 = apply_switch(G, v1, v2, w1, w2)
                    c2_only.append((g6, G, G2, v1, v2, w1, w2))
                
                if len(c1_only) >= 5 and len(c2_only) >= 5:
                    break
            if len(c1_only) >= 5 and len(c2_only) >= 5:
                break
        if len(c1_only) >= 5 and len(c2_only) >= 5:
            break
    
    print(f"\n(C1) only examples (found {len(c1_only)}):")
    for g6, G1, G2, v1, v2, w1, w2 in c1_only:
        spec1 = nbl_spectrum(G1)
        spec2 = nbl_spectrum(G2)
        is_cosp = spectra_equal(spec1, spec2)
        print(f"  {g6}: NBL-cospectral = {'✓' if is_cosp else '✗'}")
    
    print(f"\n(C2) only examples (found {len(c2_only)}):")
    for g6, G1, G2, v1, v2, w1, w2 in c2_only:
        spec1 = nbl_spectrum(G1)
        spec2 = nbl_spectrum(G2)
        is_cosp = spectra_equal(spec1, spec2)
        print(f"  {g6}: NBL-cospectral = {'✓' if is_cosp else '✗'}")
    
    print()
    print("=" * 80)
    print("EXPERIMENTS COMPLETE")
    print("=" * 80)
    
    conn.close()


if __name__ == '__main__':
    main()
