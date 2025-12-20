#!/usr/bin/env python3
"""Test advanced conditions that might distinguish switch edges.

For degree-matched edge pairs [a,b] vs [c,d], check:
1. Common neighbors: |N(a) ∩ N(c)| and |N(b) ∩ N(d)|
2. Non-adjacency pattern: a≁d AND c≁b (switchable config)
4. Off-diagonal T^k entries equality
5. Cross-entries: (T^k)[e1,e2] = (T^k)[e2,e1]
6. Walk counts between endpoints
7. Same eigenvector components
9. Symmetry under swap
"""

import sys
from itertools import permutations

import networkx as nx
import numpy as np
import psycopg2
from sympy import Matrix, Rational

sys.path.insert(0, str(__file__).rsplit("/", 2)[0])


def get_pairs(conn, limit=None):
    cur = conn.cursor()
    query = """
        SELECT g1.graph6, g2.graph6, g1.n, g1.m
        FROM cospectral_mates cm
        JOIN graphs g1 ON cm.graph1_id = g1.id
        JOIN graphs g2 ON cm.graph2_id = g2.id
        WHERE cm.matrix_type = 'nbl'
        ORDER BY g1.m, g1.n
    """
    if limit:
        query += f" LIMIT {limit}"
    cur.execute(query)
    return cur.fetchall()


def build_T_sympy(G):
    directed_edges = []
    for u, v in G.edges():
        directed_edges.append((u, v))
        directed_edges.append((v, u))
    edge_to_idx = {e: i for i, e in enumerate(directed_edges)}
    m = len(directed_edges)
    T = Matrix.zeros(m, m)
    for i, (u, v) in enumerate(directed_edges):
        d = G.degree(v) - 1
        for w in G.neighbors(v):
            if w != u:
                T[i, edge_to_idx[(v, w)]] = Rational(1, d)
    return T, directed_edges, edge_to_idx


def build_T_numpy(G):
    directed_edges = []
    for u, v in G.edges():
        directed_edges.append((u, v))
        directed_edges.append((v, u))
    edge_to_idx = {e: i for i, e in enumerate(directed_edges)}
    m = len(directed_edges)
    T = np.zeros((m, m))
    for i, (u, v) in enumerate(directed_edges):
        d = G.degree(v) - 1
        for w in G.neighbors(v):
            if w != u:
                T[i, edge_to_idx[(v, w)]] = 1.0 / d
    return T, directed_edges, edge_to_idx


def find_switch_vertices(G1, G2):
    E1 = set(G1.edges())
    E2 = set(G2.edges())
    only_in_G1 = E1 - E2
    only_in_G2 = E2 - E1
    if len(only_in_G1) != 2 or len(only_in_G2) != 2:
        return None
    verts = set()
    for e in only_in_G1:
        verts.update(e)
    for e in only_in_G2:
        verts.update(e)
    if len(verts) != 4:
        return None
    valid = []
    for perm in permutations(verts):
        v1, v2, w1, w2 = perm
        if not (G1.has_edge(v1, w1) and G1.has_edge(v2, w2) and
                not G1.has_edge(v1, w2) and not G1.has_edge(v2, w1)):
            continue
        if not (G2.has_edge(v1, w2) and G2.has_edge(v2, w1)):
            continue
        if G1.degree(v1) != G1.degree(v2):
            continue
        if G1.degree(w1) != G1.degree(w2):
            continue
        valid.append((v1, v2, w1, w2))
    return valid if valid else None


def check_conditions(G, T_np, directed_edges, edge_to_idx, i, j, max_k=3):
    """Check all conditions for edge pair (i, j)."""
    e_i = directed_edges[i]  # (a, b)
    e_j = directed_edges[j]  # (c, d)
    a, b = e_i
    c, d = e_j

    results = {}

    # Condition 1: Common neighbors
    N_a = set(G.neighbors(a))
    N_c = set(G.neighbors(c))
    N_b = set(G.neighbors(b))
    N_d = set(G.neighbors(d))
    results['common_N_source'] = len(N_a & N_c)
    results['common_N_target'] = len(N_b & N_d)

    # Condition 2: Non-adjacency pattern (switchable)
    # For edges [a,b] and [c,d] to be switchable: a≁d AND c≁b
    results['switchable'] = (not G.has_edge(a, d)) and (not G.has_edge(c, b))

    # Also check: are all 4 vertices distinct?
    results['four_distinct'] = len({a, b, c, d}) == 4

    # Full switch pattern: a~b, c~d (given), a≁d, c≁b, a≁c(?), b≁d(?)
    results['a_adj_c'] = G.has_edge(a, c)
    results['b_adj_d'] = G.has_edge(b, d)

    # Compute T^k
    T1 = T_np
    T2 = T_np @ T_np
    T3 = T2 @ T_np

    # Condition 4: Off-diagonal entries
    # Check if the entire row structure is similar in terms of which entries are nonzero
    results['same_nonzero_pattern_k1'] = np.allclose(T1[i] > 0, T1[j] > 0)

    # Condition 5: Cross-entries equal (T^k)[i,j] = (T^k)[j,i]
    results['cross_equal_k1'] = np.isclose(T1[i, j], T1[j, i])
    results['cross_equal_k2'] = np.isclose(T2[i, j], T2[j, i])
    results['cross_equal_k3'] = np.isclose(T3[i, j], T3[j, i])

    # Also check: T[i,j] = T[j,i] = 0? (no direct transition)
    results['cross_zero_k1'] = np.isclose(T1[i, j], 0) and np.isclose(T1[j, i], 0)

    # Condition 6: Walk counts - T^k[i,i] vs T^k[j,j] (return probs - already checked)
    # Let's check walks to/from the reverse edges
    # Get reverse edge indices
    rev_i = edge_to_idx.get((b, a))
    rev_j = edge_to_idx.get((d, c))
    if rev_i is not None and rev_j is not None:
        # Walks from edge to its reverse
        results['to_reverse_k2_i'] = T2[i, rev_i]
        results['to_reverse_k2_j'] = T2[j, rev_j]
        results['to_reverse_equal_k2'] = np.isclose(T2[i, rev_i], T2[j, rev_j])

    # Condition 7: Eigenvector components
    # Compute eigenvectors of T
    try:
        eigenvalues, eigenvectors = np.linalg.eig(T_np)
        # Sort by eigenvalue magnitude (descending)
        idx = np.argsort(-np.abs(eigenvalues))
        eigenvalues = eigenvalues[idx]
        eigenvectors = eigenvectors[:, idx]

        # Check if components at i and j are equal in top eigenvectors
        results['evec1_equal'] = np.isclose(np.abs(eigenvectors[i, 0]), np.abs(eigenvectors[j, 0]))
        results['evec2_equal'] = np.isclose(np.abs(eigenvectors[i, 1]), np.abs(eigenvectors[j, 1]))
        results['evec2_components'] = (eigenvectors[i, 1], eigenvectors[j, 1])
    except Exception:
        results['evec1_equal'] = None
        results['evec2_equal'] = None

    # Condition 9: Symmetry under swap
    # Check if swapping rows/cols i,j leaves certain structure invariant
    # One version: T[i,:] and T[j,:] when restricted to columns not i,j
    mask = np.ones(T_np.shape[0], dtype=bool)
    mask[i] = False
    mask[j] = False
    row_i_rest = T1[i, mask]
    row_j_rest = T1[j, mask]
    results['rows_equal_outside_ij'] = np.allclose(sorted(row_i_rest), sorted(row_j_rest))

    return results


def main():
    print("Connecting to database...")
    conn = psycopg2.connect("dbname=smol")

    print("Fetching NBL-cospectral pairs...")
    pairs = get_pairs(conn)

    # Collect valid switches
    valid_switches = []
    for g6_1, g6_2, n, m in pairs:
        G1 = nx.from_graph6_bytes(g6_1.encode())
        G2 = nx.from_graph6_bytes(g6_2.encode())
        assignments = find_switch_vertices(G1, G2)
        if assignments:
            valid_switches.append((g6_1, g6_2, n, m, G1, assignments[0]))

    print(f"Found {len(valid_switches)} valid switches")
    print("=" * 70)

    # Collect stats
    switch_stats = []
    nonswitch_stats = []

    for idx, (g6_1, g6_2, n, m, G1, assignment) in enumerate(valid_switches):
        v1, v2, w1, w2 = assignment

        T_np, directed_edges, edge_to_idx = build_T_numpy(G1)
        num_edges = len(directed_edges)

        # Switch edge indices (the parallel pairs from theorem)
        switch_pairs = [
            (edge_to_idx[(v1, w1)], edge_to_idx[(v2, w2)]),
            (edge_to_idx[(w1, v1)], edge_to_idx[(w2, v2)]),
        ]

        # Check switch pairs
        for i, j in switch_pairs:
            results = check_conditions(G1, T_np, directed_edges, edge_to_idx, i, j)
            results['is_switch'] = True
            switch_stats.append(results)

        # Check non-switch pairs with degree match (sample some)
        checked_nonswitch = 0
        for i in range(num_edges):
            if checked_nonswitch >= 10:  # Limit per graph
                break
            for j in range(i + 1, num_edges):
                if checked_nonswitch >= 10:
                    break
                e_i = directed_edges[i]
                e_j = directed_edges[j]

                # Degree conditions
                if G1.degree(e_i[0]) != G1.degree(e_j[0]):
                    continue
                if G1.degree(e_i[1]) != G1.degree(e_j[1]):
                    continue

                # Skip if it's a switch pair
                if (i, j) in switch_pairs or (j, i) in switch_pairs:
                    continue

                results = check_conditions(G1, T_np, directed_edges, edge_to_idx, i, j)
                results['is_switch'] = False
                nonswitch_stats.append(results)
                checked_nonswitch += 1

        if (idx + 1) % 20 == 0:
            print(f"[{idx+1}/{len(valid_switches)}] processed", file=sys.stderr)

    print()
    print("=" * 70)
    print("RESULTS")
    print("=" * 70)
    print()
    print(f"Switch pairs analyzed: {len(switch_stats)}")
    print(f"Non-switch pairs analyzed: {len(nonswitch_stats)}")
    print()

    # Aggregate and compare
    conditions = [
        ('switchable', 'Cond 2: Non-adjacency pattern (a≁d, c≁b)'),
        ('four_distinct', '         Four distinct vertices'),
        ('cross_zero_k1', 'Cond 5: Cross entries zero at k=1'),
        ('cross_equal_k1', 'Cond 5: Cross entries equal at k=1'),
        ('cross_equal_k2', 'Cond 5: Cross entries equal at k=2'),
        ('to_reverse_equal_k2', 'Cond 6: Equal walks to reverse edge k=2'),
        ('evec1_equal', 'Cond 7: Same |component| in eigenvec 1'),
        ('evec2_equal', 'Cond 7: Same |component| in eigenvec 2'),
        ('rows_equal_outside_ij', 'Cond 9: Rows equal outside {i,j}'),
    ]

    print(f"{'Condition':<50} {'Switch':>10} {'Non-Switch':>12}")
    print("-" * 75)

    for key, label in conditions:
        switch_true = sum(1 for s in switch_stats if s.get(key))
        switch_total = sum(1 for s in switch_stats if s.get(key) is not None)
        nonswitch_true = sum(1 for s in nonswitch_stats if s.get(key))
        nonswitch_total = sum(1 for s in nonswitch_stats if s.get(key) is not None)

        sw_pct = f"{100*switch_true/switch_total:.0f}%" if switch_total > 0 else "N/A"
        nsw_pct = f"{100*nonswitch_true/nonswitch_total:.0f}%" if nonswitch_total > 0 else "N/A"

        print(f"{label:<50} {sw_pct:>10} {nsw_pct:>12}")

    print()
    print("=" * 70)
    print()

    # Condition 1: Common neighbors distribution
    print("Condition 1: Common neighbors")
    print("-" * 40)
    sw_common_src = [s['common_N_source'] for s in switch_stats]
    sw_common_tgt = [s['common_N_target'] for s in switch_stats]
    nsw_common_src = [s['common_N_source'] for s in nonswitch_stats]
    nsw_common_tgt = [s['common_N_target'] for s in nonswitch_stats]

    print("  Common neighbors (source vertices):")
    print(f"    Switch:     mean={np.mean(sw_common_src):.2f}, range=[{min(sw_common_src)}, {max(sw_common_src)}]")
    print(f"    Non-switch: mean={np.mean(nsw_common_src):.2f}, range=[{min(nsw_common_src)}, {max(nsw_common_src)}]")
    print("  Common neighbors (target vertices):")
    print(f"    Switch:     mean={np.mean(sw_common_tgt):.2f}, range=[{min(sw_common_tgt)}, {max(sw_common_tgt)}]")
    print(f"    Non-switch: mean={np.mean(nsw_common_tgt):.2f}, range=[{min(nsw_common_tgt)}, {max(nsw_common_tgt)}]")

    print()
    print("=" * 70)

    conn.close()


if __name__ == "__main__":
    main()
