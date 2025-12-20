#!/usr/bin/env python3
"""Test if having common external neighbors is a necessary/sufficient condition."""

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
                    if is_switchable_pattern(G, v1, v2, w1, w2):
                        potential.append((v1, v2, w1, w2))
    return potential


def compute_conditions(G, v1, v2, w1, w2):
    """Compute various conditions for a switch."""
    S = {v1, v2, w1, w2}

    ext_v1 = set(n for n in G.neighbors(v1) if n not in S)
    ext_v2 = set(n for n in G.neighbors(v2) if n not in S)
    ext_w1 = set(n for n in G.neighbors(w1) if n not in S)
    ext_w2 = set(n for n in G.neighbors(w2) if n not in S)

    return {
        'condition_B': ext_v1 == ext_v2 or ext_w1 == ext_w2,
        'common_v_nonempty': len(ext_v1 & ext_v2) > 0,
        'common_w_nonempty': len(ext_w1 & ext_w2) > 0,
        'common_both_nonempty': len(ext_v1 & ext_v2) > 0 and len(ext_w1 & ext_w2) > 0,
        'common_v': len(ext_v1 & ext_v2),
        'common_w': len(ext_w1 & ext_w2),
        'sym_diff_v': len(ext_v1 ^ ext_v2),
        'sym_diff_w': len(ext_w1 ^ ext_w2),
        'sym_diff_equal': len(ext_v1 ^ ext_v2) == len(ext_w1 ^ ext_w2),
        'common_equal': len(ext_v1 & ext_v2) == len(ext_w1 & ext_w2),
        'ext_v1': ext_v1,
        'ext_v2': ext_v2,
        'ext_w1': ext_w1,
        'ext_w2': ext_w2,
    }


def main():
    print("Connecting to database...")
    conn = psycopg2.connect("dbname=smol")

    print("Fetching NBL-cospectral pairs...")
    pairs = get_pairs(conn)

    # Find valid switch pairs
    switch_pairs = []
    for g6_1, g6_2 in pairs:
        G1 = nx.from_graph6_bytes(g6_1.encode())
        G2 = nx.from_graph6_bytes(g6_2.encode())
        assignment = find_switch_vertices(G1, G2)
        if assignment:
            switch_pairs.append((g6_1, G1, assignment))

    print(f"Found {len(switch_pairs)} known switch pairs")

    # Collect stats
    working = []  # Cospectral switches
    nonworking = []  # Non-cospectral switches

    processed_graphs = set()

    for idx, (g6, G, assignment) in enumerate(switch_pairs):
        if g6 in processed_graphs:
            continue
        processed_graphs.add(g6)

        v1, v2, w1, w2 = assignment
        conds = compute_conditions(G, v1, v2, w1, w2)
        conds['known'] = True
        working.append(conds)

        # All other potential switches
        all_potential = find_all_potential_switches(G)
        for pv1, pv2, pw1, pw2 in all_potential:
            if {pv1, pv2, pw1, pw2} == {v1, v2, w1, w2}:
                continue

            G_switched = perform_switch(G, pv1, pv2, pw1, pw2)
            dist = spectral_distance(G, G_switched)

            conds = compute_conditions(G, pv1, pv2, pw1, pw2)
            conds['dist'] = dist

            if dist < 1e-10:
                working.append(conds)
            else:
                nonworking.append(conds)

        if (idx + 1) % 25 == 0:
            print(f"  [{idx+1}/{len(switch_pairs)}]", file=sys.stderr)

    print(f"\nWorking: {len(working)}, Non-working: {len(nonworking)}")

    # Separate by Condition B
    cond_B_working = [c for c in working if c['condition_B']]
    non_B_working = [c for c in working if not c['condition_B']]
    non_B_nonworking = [c for c in nonworking if not c['condition_B']]

    print(f"\nCondition B working: {len(cond_B_working)}")
    print(f"Non-Condition-B working: {len(non_B_working)}")
    print(f"Non-Condition-B non-working: {len(non_B_nonworking)}")

    # Test new conditions on non-Condition-B cases
    print("\n" + "=" * 70)
    print("CONDITIONS ON NON-CONDITION-B CASES")
    print("=" * 70)

    conditions = [
        ('common_v_nonempty', 'Common N_ext(v) nonempty'),
        ('common_w_nonempty', 'Common N_ext(w) nonempty'),
        ('common_both_nonempty', 'BOTH common nonempty'),
        ('sym_diff_equal', 'Sym diff sizes equal'),
        ('common_equal', 'Common sizes equal'),
    ]

    print(f"\n{'Condition':<35} {'Work':>8} {'Non-W':>8} {'Prec':>8} {'FP':>8}")
    print("-" * 70)

    for key, label in conditions:
        w_true = sum(1 for c in non_B_working if c.get(key))
        nw_true = sum(1 for c in non_B_nonworking if c.get(key))
        total = w_true + nw_true
        precision = w_true / total * 100 if total else 0
        fp_rate = nw_true / len(non_B_nonworking) * 100 if non_B_nonworking else 0

        marker = ""
        if nw_true == 0 and w_true > 0:
            marker = " *** PERFECT"

        print(f"{label:<35} {w_true:>7} {nw_true:>8} {precision:>7.1f}% {fp_rate:>7.1f}%{marker}")

    # Combinations
    print("\n" + "=" * 70)
    print("COMBINATION CONDITIONS")
    print("=" * 70)

    def check_combo(name, pred):
        w = sum(1 for c in non_B_working if pred(c))
        nw = sum(1 for c in non_B_nonworking if pred(c))
        total = w + nw
        prec = w / total * 100 if total else 0
        perf = " *** PERFECT" if nw == 0 and w > 0 else ""
        cov = w / len(non_B_working) * 100 if non_B_working else 0
        print(f"{name:<50} W:{w:>4} NW:{nw:>4} Prec:{prec:>5.1f}% Cov:{cov:>5.1f}%{perf}")

    check_combo("common_both AND sym_diff_equal",
                lambda c: c['common_both_nonempty'] and c['sym_diff_equal'])

    check_combo("common_v > 0 AND common_w > 0 AND common_equal",
                lambda c: c['common_v'] > 0 and c['common_w'] > 0 and c['common_equal'])

    check_combo("sym_diff_v == sym_diff_w AND common_v == common_w",
                lambda c: c['sym_diff_equal'] and c['common_equal'])

    check_combo("common_v == common_w > 0",
                lambda c: c['common_v'] == c['common_w'] and c['common_v'] > 0)

    check_combo("sym_diff_v == sym_diff_w == 2",
                lambda c: c['sym_diff_v'] == 2 and c['sym_diff_w'] == 2)

    # Analyze non-B working cases that don't satisfy common_both
    odd_cases = [c for c in non_B_working if not c['common_both_nonempty']]
    print(f"\n\nNon-B working without common_both: {len(odd_cases)}/{len(non_B_working)}")

    if odd_cases:
        print("\nDetails of cases without common external neighbors in both pairs:")
        for i, c in enumerate(odd_cases[:10]):
            print(f"\n  Case {i+1}:")
            print(f"    N_ext(v1)={c['ext_v1']}, N_ext(v2)={c['ext_v2']}")
            print(f"    N_ext(w1)={c['ext_w1']}, N_ext(w2)={c['ext_w2']}")
            print(f"    Common: v={c['common_v']}, w={c['common_w']}")
            print(f"    Sym diff: v={c['sym_diff_v']}, w={c['sym_diff_w']}")

    conn.close()


if __name__ == "__main__":
    main()
