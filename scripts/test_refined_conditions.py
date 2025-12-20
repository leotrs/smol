#!/usr/bin/env python3
"""Refined condition testing - focus on high-precision combinations."""

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


def is_switchable(G, v1, v2, w1, w2):
    if len({v1, v2, w1, w2}) != 4:
        return False
    if not G.has_edge(v1, w1) or not G.has_edge(v2, w2):
        return False
    if G.has_edge(v1, w2) or G.has_edge(v2, w1):
        return False
    return G.degree(v1) == G.degree(v2) and G.degree(w1) == G.degree(w2)


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
    return np.eye(m) - T


def spectral_distance(G1, G2):
    L1 = build_T(G1)
    L2 = build_T(G2)
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
                    if is_switchable(G, v1, v2, w1, w2):
                        potential.append((v1, v2, w1, w2))
    return potential


def compute_features(G, v1, v2, w1, w2):
    S = {v1, v2, w1, w2}

    ext_v1 = set(n for n in G.neighbors(v1) if n not in S)
    ext_v2 = set(n for n in G.neighbors(v2) if n not in S)
    ext_w1 = set(n for n in G.neighbors(w1) if n not in S)
    ext_w2 = set(n for n in G.neighbors(w2) if n not in S)

    # Cross connections: does external neighbor of v also neighbor w?
    cross_v1_w1 = len(ext_v1 & ext_w1)
    cross_v1_w2 = len(ext_v1 & ext_w2)
    cross_v2_w1 = len(ext_v2 & ext_w1)
    cross_v2_w2 = len(ext_v2 & ext_w2)

    return {
        'condition_B': ext_v1 == ext_v2 or ext_w1 == ext_w2,
        'ext_v1': ext_v1, 'ext_v2': ext_v2,
        'ext_w1': ext_w1, 'ext_w2': ext_w2,
        'common_v': len(ext_v1 & ext_v2),
        'common_w': len(ext_w1 & ext_w2),
        'sym_diff_v': len(ext_v1 ^ ext_v2),
        'sym_diff_w': len(ext_w1 ^ ext_w2),
        'cross_v1_w1': cross_v1_w1,
        'cross_v1_w2': cross_v1_w2,
        'cross_v2_w1': cross_v2_w1,
        'cross_v2_w2': cross_v2_w2,
        'd_v': G.degree(v1),
        'd_w': G.degree(w1),
        'internal_v1_v2': G.has_edge(v1, v2),
        'internal_w1_w2': G.has_edge(w1, w2),
    }


def main():
    print("Connecting to database...")
    conn = psycopg2.connect("dbname=smol")
    pairs = get_pairs(conn)

    switch_pairs = []
    for g6_1, g6_2 in pairs:
        G1 = nx.from_graph6_bytes(g6_1.encode())
        G2 = nx.from_graph6_bytes(g6_2.encode())
        assignment = find_switch_vertices(G1, G2)
        if assignment:
            switch_pairs.append((g6_1, G1, assignment))

    print(f"Found {len(switch_pairs)} switch pairs")

    working, nonworking = [], []
    processed = set()

    for idx, (g6, G, assignment) in enumerate(switch_pairs):
        if g6 in processed:
            continue
        processed.add(g6)

        v1, v2, w1, w2 = assignment
        f = compute_features(G, v1, v2, w1, w2)
        f['g6'] = g6
        working.append(f)

        for pv1, pv2, pw1, pw2 in find_all_potential_switches(G):
            if {pv1, pv2, pw1, pw2} == {v1, v2, w1, w2}:
                continue
            G_sw = perform_switch(G, pv1, pv2, pw1, pw2)
            dist = spectral_distance(G, G_sw)
            f = compute_features(G, pv1, pv2, pw1, pw2)
            f['g6'] = g6
            f['dist'] = dist
            if dist < 1e-10:
                working.append(f)
            else:
                nonworking.append(f)

        if (idx + 1) % 25 == 0:
            print(f"  [{idx+1}/{len(switch_pairs)}]", file=sys.stderr)

    non_B_working = [f for f in working if not f['condition_B']]
    non_B_nonworking = [f for f in nonworking if not f['condition_B']]

    print(f"\nNon-B working: {len(non_B_working)}")
    print(f"Non-B non-working: {len(non_B_nonworking)}")

    # Focus on sym_diff==2 cases
    w_sym2 = [f for f in non_B_working if f['sym_diff_v'] == 2 and f['sym_diff_w'] == 2]
    nw_sym2 = [f for f in non_B_nonworking if f['sym_diff_v'] == 2 and f['sym_diff_w'] == 2]

    print(f"\nFocusing on sym_diff==2 cases: W={len(w_sym2)}, NW={len(nw_sym2)}")

    print("\n" + "=" * 70)
    print("CROSS-CONNECTION PATTERNS IN SYM_DIFF==2 CASES")
    print("=" * 70)

    # The cross-connection pattern: (v1w1, v1w2, v2w1, v2w2)
    def cross_pattern(f):
        return (f['cross_v1_w1'], f['cross_v1_w2'], f['cross_v2_w1'], f['cross_v2_w2'])

    w_patterns = [cross_pattern(f) for f in w_sym2]
    nw_patterns = [cross_pattern(f) for f in nw_sym2]

    print("\nCross patterns (v1w1, v1w2, v2w1, v2w2):")
    from collections import Counter
    w_counts = Counter(w_patterns)
    nw_counts = Counter(nw_patterns)

    all_patterns = set(w_counts.keys()) | set(nw_counts.keys())
    print(f"\n{'Pattern':<25} {'Working':>10} {'Non-work':>10} {'Precision':>10}")
    print("-" * 60)

    for p in sorted(all_patterns):
        w = w_counts.get(p, 0)
        nw = nw_counts.get(p, 0)
        total = w + nw
        prec = w / total * 100 if total else 0
        marker = " ***" if nw == 0 and w > 0 else ""
        print(f"{str(p):<25} {w:>10} {nw:>10} {prec:>9.1f}%{marker}")

    # Test symmetric cross patterns
    print("\n" + "=" * 70)
    print("SYMMETRIC CROSS PATTERNS")
    print("=" * 70)

    def test(name, pred, w_set, nw_set):
        w = sum(1 for f in w_set if pred(f))
        nw = sum(1 for f in nw_set if pred(f))
        total = w + nw
        prec = w / total * 100 if total else 0
        cov = w / len(w_set) * 100 if w_set else 0
        perf = " *** PERFECT" if nw == 0 and w > 0 else ""
        print(f"{name:<55} W:{w:>3} NW:{nw:>3} Prec:{prec:>5.1f}% Cov:{cov:>5.1f}%{perf}")

    # Within sym_diff==2 cases
    print("\nWithin sym_diff==2:")

    test("cross_v1_w2 == cross_v2_w1 (switched pair)",
         lambda f: f['cross_v1_w2'] == f['cross_v2_w1'], w_sym2, nw_sym2)

    test("cross_v1_w1 == cross_v2_w2 (same pair)",
         lambda f: f['cross_v1_w1'] == f['cross_v2_w2'], w_sym2, nw_sym2)

    test("BOTH cross equalities",
         lambda f: f['cross_v1_w2'] == f['cross_v2_w1'] and f['cross_v1_w1'] == f['cross_v2_w2'],
         w_sym2, nw_sym2)

    test("cross_v1_w2 == cross_v2_w1 AND common_v == common_w",
         lambda f: f['cross_v1_w2'] == f['cross_v2_w1'] and f['common_v'] == f['common_w'],
         w_sym2, nw_sym2)

    test("BOTH cross equal AND (common_v > 0 OR common_w > 0)",
         lambda f: f['cross_v1_w2'] == f['cross_v2_w1'] and f['cross_v1_w1'] == f['cross_v2_w2'] and
                   (f['common_v'] > 0 or f['common_w'] > 0),
         w_sym2, nw_sym2)

    test("cross diagonal sum: v1w2 + v2w1 == v1w1 + v2w2",
         lambda f: f['cross_v1_w2'] + f['cross_v2_w1'] == f['cross_v1_w1'] + f['cross_v2_w2'],
         w_sym2, nw_sym2)

    test("common_v + common_w > 0",
         lambda f: f['common_v'] + f['common_w'] > 0, w_sym2, nw_sym2)

    test("common_v == common_w",
         lambda f: f['common_v'] == f['common_w'], w_sym2, nw_sym2)

    test("d_v == d_w",
         lambda f: f['d_v'] == f['d_w'], w_sym2, nw_sym2)

    # What about cases where all crosses are 0?
    print("\n\nCases with all crosses == 0:")
    w_no_cross = [f for f in w_sym2 if cross_pattern(f) == (0,0,0,0)]
    nw_no_cross = [f for f in nw_sym2 if cross_pattern(f) == (0,0,0,0)]
    print(f"  Working: {len(w_no_cross)}, Non-working: {len(nw_no_cross)}")

    if w_no_cross and nw_no_cross:
        print("\n  Sub-conditions for (0,0,0,0) cases:")
        test("    common_v == common_w", lambda f: f['common_v'] == f['common_w'],
             w_no_cross, nw_no_cross)
        test("    common_v > 0 OR common_w > 0", lambda f: f['common_v'] > 0 or f['common_w'] > 0,
             w_no_cross, nw_no_cross)
        test("    internal_v1_v2 OR internal_w1_w2",
             lambda f: f['internal_v1_v2'] or f['internal_w1_w2'], w_no_cross, nw_no_cross)

    # Final summary: best conditions found
    print("\n" + "=" * 70)
    print("BEST CONDITIONS SUMMARY (for non-Condition-B cases)")
    print("=" * 70)

    # All non-B cases
    print("\nAll non-Condition-B cases:")
    test("sym_diff_v == sym_diff_w",
         lambda f: f['sym_diff_v'] == f['sym_diff_w'], non_B_working, non_B_nonworking)
    test("sym_diff_v == sym_diff_w == 2",
         lambda f: f['sym_diff_v'] == 2 and f['sym_diff_w'] == 2, non_B_working, non_B_nonworking)
    test("cross_v1_w2 == cross_v2_w1 AND cross_v1_w1 == cross_v2_w2",
         lambda f: f['cross_v1_w2'] == f['cross_v2_w1'] and f['cross_v1_w1'] == f['cross_v2_w2'],
         non_B_working, non_B_nonworking)

    conn.close()


if __name__ == "__main__":
    main()
