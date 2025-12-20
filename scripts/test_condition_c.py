#!/usr/bin/env python3
"""Test Condition C: Cross-column equality with non-zero values."""

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


def build_NBL(G):
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
    L1 = build_NBL(G1)
    L2 = build_NBL(G2)
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


def compute_conditions(G, v1, v2, w1, w2):
    S = {v1, v2, w1, w2}

    ext_v1 = set(n for n in G.neighbors(v1) if n not in S)
    ext_v2 = set(n for n in G.neighbors(v2) if n not in S)
    ext_w1 = set(n for n in G.neighbors(w1) if n not in S)
    ext_w2 = set(n for n in G.neighbors(w2) if n not in S)

    # Cross-intersection counts
    cross_v1_w1 = len(ext_v1 & ext_w1)
    cross_v1_w2 = len(ext_v1 & ext_w2)
    cross_v2_w1 = len(ext_v2 & ext_w1)
    cross_v2_w2 = len(ext_v2 & ext_w2)

    # Condition B
    condition_B = (ext_v1 == ext_v2) or (ext_w1 == ext_w2)

    # Symmetric difference
    sym_diff_v = len(ext_v1 ^ ext_v2)
    sym_diff_w = len(ext_w1 ^ ext_w2)

    # Condition C: Column-equal with non-zero values
    # Column w1: cross_v1_w1 == cross_v2_w1 > 0
    # Column w2: cross_v1_w2 == cross_v2_w2 > 0
    col_w1_equal = cross_v1_w1 == cross_v2_w1
    col_w2_equal = cross_v1_w2 == cross_v2_w2
    col_w1_nonzero = cross_v1_w1 > 0  # (= cross_v2_w1 if equal)
    col_w2_nonzero = cross_v1_w2 > 0

    condition_C = (col_w1_equal and col_w2_equal and col_w1_nonzero and col_w2_nonzero)

    # Also test: row-equal (v-side instead of w-side)
    # Row v1: cross_v1_w1 == cross_v1_w2 > 0
    # Row v2: cross_v2_w1 == cross_v2_w2 > 0
    row_v1_equal = cross_v1_w1 == cross_v1_w2
    row_v2_equal = cross_v2_w1 == cross_v2_w2
    row_v1_nonzero = cross_v1_w1 > 0
    row_v2_nonzero = cross_v2_w1 > 0

    condition_C_row = (row_v1_equal and row_v2_equal and row_v1_nonzero and row_v2_nonzero)

    return {
        'condition_B': condition_B,
        'condition_C': condition_C,
        'condition_C_row': condition_C_row,
        'sym_diff_v': sym_diff_v,
        'sym_diff_w': sym_diff_w,
        'sym_diff_equal_2': sym_diff_v == 2 and sym_diff_w == 2,
        'cross_pattern': (cross_v1_w1, cross_v1_w2, cross_v2_w1, cross_v2_w2),
        'col_equal': col_w1_equal and col_w2_equal,
        'all_nonzero': cross_v1_w1 > 0 and cross_v1_w2 > 0 and cross_v2_w1 > 0 and cross_v2_w2 > 0,
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
        c = compute_conditions(G, v1, v2, w1, w2)
        working.append(c)

        for pv1, pv2, pw1, pw2 in find_all_potential_switches(G):
            if {pv1, pv2, pw1, pw2} == {v1, v2, w1, w2}:
                continue
            G_sw = perform_switch(G, pv1, pv2, pw1, pw2)
            dist = spectral_distance(G, G_sw)
            c = compute_conditions(G, pv1, pv2, pw1, pw2)
            c['dist'] = dist
            if dist < 1e-10:
                working.append(c)
            else:
                nonworking.append(c)

        if (idx + 1) % 25 == 0:
            print(f"  [{idx+1}/{len(switch_pairs)}]", file=sys.stderr)

    print(f"\nTotal working: {len(working)}")
    print(f"Total non-working: {len(nonworking)}")

    # Condition B stats
    cond_B_working = sum(1 for c in working if c['condition_B'])
    cond_B_nonworking = sum(1 for c in nonworking if c['condition_B'])
    print(f"\nCondition B: Working={cond_B_working}, Non-working={cond_B_nonworking}")

    # Focus on non-Condition-B cases
    non_B_working = [c for c in working if not c['condition_B']]
    non_B_nonworking = [c for c in nonworking if not c['condition_B']]

    print(f"\nNon-Condition-B: Working={len(non_B_working)}, Non-working={len(non_B_nonworking)}")

    # Test Condition C on all non-B cases
    print("\n" + "=" * 70)
    print("CONDITION C: Column-equal AND all-nonzero cross-intersections")
    print("=" * 70)

    def test(name, pred, w_set, nw_set):
        w = sum(1 for c in w_set if pred(c))
        nw = sum(1 for c in nw_set if pred(c))
        total = w + nw
        prec = w / total * 100 if total else 0
        cov = w / len(w_set) * 100 if w_set else 0
        fp = nw
        perf = " *** PERFECT (0 FP)" if nw == 0 and w > 0 else ""
        print(f"{name:<50} W:{w:>4} FP:{fp:>4} Prec:{prec:>5.1f}% Cov:{cov:>5.1f}%{perf}")

    print("\nOn ALL non-Condition-B cases:")
    test("Condition C (col-equal + all nonzero)", lambda c: c['condition_C'], non_B_working, non_B_nonworking)
    test("Condition C row variant", lambda c: c['condition_C_row'], non_B_working, non_B_nonworking)
    test("col_equal only", lambda c: c['col_equal'], non_B_working, non_B_nonworking)
    test("all_nonzero only", lambda c: c['all_nonzero'], non_B_working, non_B_nonworking)
    test("col_equal AND all_nonzero", lambda c: c['col_equal'] and c['all_nonzero'], non_B_working, non_B_nonworking)

    # Within sym_diff==2 cases
    sym2_working = [c for c in non_B_working if c['sym_diff_equal_2']]
    sym2_nonworking = [c for c in non_B_nonworking if c['sym_diff_equal_2']]

    print(f"\nOn sym_diff==2 cases (W={len(sym2_working)}, NW={len(sym2_nonworking)}):")
    test("Condition C (col-equal + all nonzero)", lambda c: c['condition_C'], sym2_working, sym2_nonworking)
    test("Condition C row variant", lambda c: c['condition_C_row'], sym2_working, sym2_nonworking)
    test("col_equal only", lambda c: c['col_equal'], sym2_working, sym2_nonworking)
    test("all_nonzero only", lambda c: c['all_nonzero'], sym2_working, sym2_nonworking)

    # Summary
    print("\n" + "=" * 70)
    print("SUMMARY OF SUFFICIENT CONDITIONS")
    print("=" * 70)

    print("\n1. Condition B (external neighborhood equality):")
    print(f"   Explains {cond_B_working}/{len(working)} working switches")
    print(f"   False positives: {cond_B_nonworking}")

    cond_C_working = sum(1 for c in non_B_working if c['condition_C'])
    cond_C_nonworking = sum(1 for c in non_B_nonworking if c['condition_C'])

    print("\n2. Condition C (cross-column equal + nonzero):")
    print(f"   Explains {cond_C_working}/{len(non_B_working)} non-B working switches")
    print(f"   False positives: {cond_C_nonworking}")

    # What's left?
    explained = cond_B_working + cond_C_working
    print(f"\n3. Total explained: {explained}/{len(working)} ({100*explained/len(working):.1f}%)")
    print(f"   Remaining unexplained: {len(working) - explained}")

    conn.close()


if __name__ == "__main__":
    main()
