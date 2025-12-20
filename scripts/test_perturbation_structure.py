#!/usr/bin/env python3
"""Analyze the perturbation structure ΔT that preserves eigenvalues."""

import sys
from itertools import permutations

import networkx as nx
import numpy as np
import psycopg2


def get_pairs(conn):
    cur = conn.cursor()
    cur.execute("""
        SELECT g1.graph6, g2.graph6
        FROM cospectral_mates cm
        JOIN graphs g1 ON cm.graph1_id = g1.id
        JOIN graphs g2 ON cm.graph2_id = g2.id
        WHERE cm.matrix_type = 'nbl'
        ORDER BY g1.m, g1.n
    """)
    return cur.fetchall()


def find_switch_vertices(G1, G2):
    E1 = set(G1.edges())
    E2 = set(G2.edges())
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
        if (G1.has_edge(v1, w1) and G1.has_edge(v2, w2) and
            not G1.has_edge(v1, w2) and not G1.has_edge(v2, w1) and
            G1.degree(v1) == G1.degree(v2) and G1.degree(w1) == G1.degree(w2)):
            return (v1, v2, w1, w2)
    return None


def is_switchable_pattern(G, v1, v2, w1, w2):
    if len({v1, v2, w1, w2}) != 4:
        return False
    if not G.has_edge(v1, w1) or not G.has_edge(v2, w2):
        return False
    if G.has_edge(v1, w2) or G.has_edge(v2, w1):
        return False
    if G.degree(v1) != G.degree(v2) or G.degree(w1) != G.degree(w2):
        return False
    return True


def perform_switch(G, v1, v2, w1, w2):
    G2 = G.copy()
    G2.remove_edge(v1, w1)
    G2.remove_edge(v2, w2)
    G2.add_edge(v1, w2)
    G2.add_edge(v2, w1)
    return G2


def build_T(G):
    directed_edges = []
    for u, v in G.edges():
        directed_edges.append((u, v))
        directed_edges.append((v, u))
    edge_to_idx = {e: i for i, e in enumerate(directed_edges)}
    m = len(directed_edges)
    T = np.zeros((m, m))
    for i, (u, v) in enumerate(directed_edges):
        d = G.degree(v) - 1
        if d > 0:
            for w in G.neighbors(v):
                if w != u:
                    T[i, edge_to_idx[(v, w)]] = 1.0 / d
    return T, directed_edges, edge_to_idx


def spectral_distance(G1, G2):
    T1, _, _ = build_T(G1)
    T2, _, _ = build_T(G2)
    L1 = np.eye(T1.shape[0]) - T1
    L2 = np.eye(T2.shape[0]) - T2
    eig1 = np.sort(np.linalg.eigvals(L1))
    eig2 = np.sort(np.linalg.eigvals(L2))
    return np.linalg.norm(eig1 - eig2)


def find_all_potential_switches(G):
    potential = []
    edges = list(G.edges())
    for i, (a, b) in enumerate(edges):
        for j, (c, d) in enumerate(edges):
            if i >= j:
                continue
            for v1, w1 in [(a, b), (b, a)]:
                for v2, w2 in [(c, d), (d, c)]:
                    if is_switchable_pattern(G, v1, v2, w1, w2):
                        potential.append((v1, v2, w1, w2))
    return potential


def analyze_perturbation(G1, v1, v2, w1, w2):
    """Analyze the perturbation structure."""
    G2 = perform_switch(G1, v1, v2, w1, w2)

    T1, edges1, idx1 = build_T(G1)
    T2, edges2, idx2 = build_T(G2)

    # The perturbation is not straightforward because the edge sets differ
    # We need to align them

    # Common edges
    set(edges1) & set(edges2)
    only_G1 = set(edges1) - set(edges2)
    set(edges2) - set(edges1)

    S = {v1, v2, w1, w2}
    ext_v1 = set(n for n in G1.neighbors(v1) if n not in S)
    ext_v2 = set(n for n in G1.neighbors(v2) if n not in S)
    ext_w1 = set(n for n in G1.neighbors(w1) if n not in S)
    ext_w2 = set(n for n in G1.neighbors(w2) if n not in S)

    # Analyze which rows/columns of T are affected
    affected_rows_G1 = set()
    affected_cols_G1 = set()

    for e in edges1:
        u, v = e
        # Row e is affected if:
        # - e is a switch edge (it disappears)
        # - e ends at a switch vertex (its successors change)
        if e in only_G1:
            affected_rows_G1.add(e)
        if v in S:
            affected_rows_G1.add(e)

        # Column e is affected if:
        # - e is a switch edge (it disappears)
        # - e is a successor of a switch edge (its in-edges change)
        if e in only_G1:
            affected_cols_G1.add(e)
        if u in S and e not in only_G1:
            # Check if e is a successor of a switch edge
            for sw in [(v1, w1), (v2, w2)]:
                if sw[1] == u:
                    affected_cols_G1.add(e)

    # Look at the submatrix structure
    d_v = G1.degree(v1)  # = G1.degree(v2)
    d_w = G1.degree(w1)  # = G1.degree(w2)

    result = {
        'ext_v1': ext_v1,
        'ext_v2': ext_v2,
        'ext_w1': ext_w1,
        'ext_w2': ext_w2,
        'common_v': len(ext_v1 & ext_v2),
        'common_w': len(ext_w1 & ext_w2),
        'sym_diff_v': len(ext_v1 ^ ext_v2),
        'sym_diff_w': len(ext_w1 ^ ext_w2),
        'd_v': d_v,
        'd_w': d_w,
        'condition_B': ext_v1 == ext_v2 or ext_w1 == ext_w2,
        # Degree of the induced subgraph
        'internal_v1_v2': G1.has_edge(v1, v2),
        'internal_w1_w2': G1.has_edge(w1, w2),
    }

    # New: check if the "external to S" neighborhoods form a specific pattern
    # The key might be how the external neighborhoods overlap with each other

    # Cross overlaps: does an external neighbor of v also neighbor w?
    cross_v1_to_w = len([x for x in ext_v1 if any(G1.has_edge(x, w) for w in [w1, w2])])
    cross_v2_to_w = len([x for x in ext_v2 if any(G1.has_edge(x, w) for w in [w1, w2])])
    cross_w1_to_v = len([x for x in ext_w1 if any(G1.has_edge(x, v) for v in [v1, v2])])
    cross_w2_to_v = len([x for x in ext_w2 if any(G1.has_edge(x, v) for v in [v1, v2])])

    result['cross_v1_to_w'] = cross_v1_to_w
    result['cross_v2_to_w'] = cross_v2_to_w
    result['cross_w1_to_v'] = cross_w1_to_v
    result['cross_w2_to_v'] = cross_w2_to_v
    result['cross_v_equal'] = cross_v1_to_w == cross_v2_to_w
    result['cross_w_equal'] = cross_w1_to_v == cross_w2_to_v
    result['cross_both_equal'] = result['cross_v_equal'] and result['cross_w_equal']

    # Total external connections from S to outside
    result['total_ext_v'] = len(ext_v1) + len(ext_v2)
    result['total_ext_w'] = len(ext_w1) + len(ext_w2)

    return result


def main():
    print("Connecting to database...")
    conn = psycopg2.connect("dbname=smol")

    print("Fetching NBL-cospectral pairs...")
    pairs = get_pairs(conn)

    switch_pairs = []
    for g6_1, g6_2 in pairs:
        G1 = nx.from_graph6_bytes(g6_1.encode())
        G2 = nx.from_graph6_bytes(g6_2.encode())
        assignment = find_switch_vertices(G1, G2)
        if assignment:
            switch_pairs.append((g6_1, G1, assignment))

    print(f"Found {len(switch_pairs)} switch pairs")

    working = []
    nonworking = []
    processed = set()

    for idx, (g6, G, assignment) in enumerate(switch_pairs):
        if g6 in processed:
            continue
        processed.add(g6)

        v1, v2, w1, w2 = assignment
        result = analyze_perturbation(G, v1, v2, w1, w2)
        result['working'] = True
        working.append(result)

        for pv1, pv2, pw1, pw2 in find_all_potential_switches(G):
            if {pv1, pv2, pw1, pw2} == {v1, v2, w1, w2}:
                continue

            G_sw = perform_switch(G, pv1, pv2, pw1, pw2)
            dist = spectral_distance(G, G_sw)

            result = analyze_perturbation(G, pv1, pv2, pw1, pw2)
            result['dist'] = dist
            result['working'] = dist < 1e-10

            if result['working']:
                working.append(result)
            else:
                nonworking.append(result)

        if (idx + 1) % 25 == 0:
            print(f"  [{idx+1}/{len(switch_pairs)}]", file=sys.stderr)

    print(f"\nWorking: {len(working)}, Non-working: {len(nonworking)}")

    # Focus on non-Condition-B cases
    non_B_working = [r for r in working if not r['condition_B']]
    non_B_nonworking = [r for r in nonworking if not r['condition_B']]

    print(f"Non-B working: {len(non_B_working)}")
    print(f"Non-B non-working: {len(non_B_nonworking)}")

    # Test cross-connection conditions
    print("\n" + "=" * 70)
    print("CROSS-CONNECTION CONDITIONS (Non-Condition-B cases)")
    print("=" * 70)

    conditions = [
        ('cross_v_equal', 'Cross v connections equal'),
        ('cross_w_equal', 'Cross w connections equal'),
        ('cross_both_equal', 'BOTH cross connections equal'),
    ]

    for key, label in conditions:
        w = sum(1 for r in non_B_working if r.get(key))
        nw = sum(1 for r in non_B_nonworking if r.get(key))
        total = w + nw
        prec = w / total * 100 if total else 0
        perf = " *** PERFECT" if nw == 0 and w > 0 else ""
        print(f"{label:<40} W:{w:>4} NW:{nw:>4} Prec:{prec:>5.1f}%{perf}")

    # Combinations
    print("\nCombination conditions:")

    def test_combo(name, pred):
        w = sum(1 for r in non_B_working if pred(r))
        nw = sum(1 for r in non_B_nonworking if pred(r))
        total = w + nw
        prec = w / total * 100 if total else 0
        cov = w / len(non_B_working) * 100 if non_B_working else 0
        perf = " *** PERFECT" if nw == 0 and w > 0 else ""
        print(f"{name:<55} W:{w:>3} NW:{nw:>4} Prec:{prec:>5.1f}% Cov:{cov:>5.1f}%{perf}")

    test_combo("cross_both_equal AND sym_diff_v == sym_diff_w",
               lambda r: r['cross_both_equal'] and r['sym_diff_v'] == r['sym_diff_w'])

    test_combo("cross_both_equal AND common_v == common_w",
               lambda r: r['cross_both_equal'] and r['common_v'] == r['common_w'])

    test_combo("internal_v1_v2 AND internal_w1_w2",
               lambda r: r['internal_v1_v2'] and r['internal_w1_w2'])

    test_combo("d_v == d_w (equal switch vertex degrees)",
               lambda r: r['d_v'] == r['d_w'])

    test_combo("total_ext_v == total_ext_w",
               lambda r: r['total_ext_v'] == r['total_ext_w'])

    # Look at specific patterns
    print("\n" + "=" * 70)
    print("SPECIFIC PATTERN ANALYSIS")
    print("=" * 70)

    # What about when sym_diff both equal 2?
    w_sym2 = [r for r in non_B_working if r['sym_diff_v'] == 2 and r['sym_diff_w'] == 2]
    nw_sym2 = [r for r in non_B_nonworking if r['sym_diff_v'] == 2 and r['sym_diff_w'] == 2]
    print(f"\nsym_diff_v == sym_diff_w == 2: W={len(w_sym2)}, NW={len(nw_sym2)}")

    if w_sym2 and nw_sym2:
        # What distinguishes working from non-working when both have sym_diff=2?
        print("\nWithin sym_diff==2 cases, testing additional conditions:")

        def test_sub(name, pred):
            w = sum(1 for r in w_sym2 if pred(r))
            nw = sum(1 for r in nw_sym2 if pred(r))
            total = w + nw
            prec = w / total * 100 if total else 0
            perf = " *** PERFECT" if nw == 0 and w > 0 else ""
            print(f"  {name:<50} W:{w:>3} NW:{nw:>3} Prec:{prec:>5.1f}%{perf}")

        test_sub("common_v > 0 OR common_w > 0",
                 lambda r: r['common_v'] > 0 or r['common_w'] > 0)
        test_sub("common_v > 0 AND common_w > 0",
                 lambda r: r['common_v'] > 0 and r['common_w'] > 0)
        test_sub("cross_both_equal",
                 lambda r: r['cross_both_equal'])
        test_sub("internal_v1_v2 OR internal_w1_w2",
                 lambda r: r['internal_v1_v2'] or r['internal_w1_w2'])
        test_sub("d_v == d_w",
                 lambda r: r['d_v'] == r['d_w'])

    conn.close()


if __name__ == "__main__":
    main()
