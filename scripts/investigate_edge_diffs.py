#!/usr/bin/env python3
"""Investigate edge differences more closely."""

import networkx as nx
import psycopg2
from collections import Counter


def get_all_nbl_pairs(conn):
    cur = conn.cursor()
    cur.execute("""
        SELECT g1.graph6, g2.graph6, g1.n, g1.m, g2.m
        FROM cospectral_mates cm
        JOIN graphs g1 ON cm.graph1_id = g1.id
        JOIN graphs g2 ON cm.graph2_id = g2.id
        WHERE cm.matrix_type = 'nbl'
    """)
    return cur.fetchall()


def main():
    conn = psycopg2.connect("dbname=smol")
    pairs = get_all_nbl_pairs(conn)

    # Check if pairs have same number of edges
    same_m = sum(1 for _, _, _, m1, m2 in pairs if m1 == m2)
    diff_m = sum(1 for _, _, _, m1, m2 in pairs if m1 != m2)

    print(f"Pairs with same edge count: {same_m}")
    print(f"Pairs with different edge count: {diff_m}")

    if diff_m > 0:
        print("\nWARNING: Some pairs have different edge counts!")
        # Show examples
        for g6_1, g6_2, n, m1, m2 in pairs[:20]:
            if m1 != m2:
                print(f"  n={n}: {g6_1} (m={m1}) vs {g6_2} (m={m2})")

    # For same-edge pairs, analyze symmetric difference
    print("\n" + "=" * 70)
    print("SYMMETRIC DIFFERENCE (for pairs with same edge count)")
    print("=" * 70)

    sym_diff_counts = Counter()
    examples = {}

    for g6_1, g6_2, n, m1, m2 in pairs:
        if m1 != m2:
            continue

        G1 = nx.from_graph6_bytes(g6_1.encode())
        G2 = nx.from_graph6_bytes(g6_2.encode())

        E1 = set(frozenset(e) for e in G1.edges())
        E2 = set(frozenset(e) for e in G2.edges())

        sym_diff = len(E1 ^ E2)  # |E1 △ E2|
        sym_diff_counts[sym_diff] += 1

        if sym_diff not in examples:
            examples[sym_diff] = (g6_1, g6_2, n)

    for sd in sorted(sym_diff_counts.keys()):
        count = sym_diff_counts[sd]
        pct = 100 * count / same_m
        g1, g2, n = examples[sd]
        print(f"  sym_diff={sd:>2}: {count:>6} pairs ({pct:>5.1f}%)  example: n={n}")

    # Look at sym_diff=0 cases (should be isomorphic)
    if 0 in sym_diff_counts:
        print("\n  sym_diff=0 means identical edge sets - checking if isomorphic...")
        iso_count = 0
        non_iso_count = 0
        for g6_1, g6_2, n, m1, m2 in pairs[:1000]:
            if m1 != m2:
                continue
            G1 = nx.from_graph6_bytes(g6_1.encode())
            G2 = nx.from_graph6_bytes(g6_2.encode())
            E1 = set(frozenset(e) for e in G1.edges())
            E2 = set(frozenset(e) for e in G2.edges())
            if E1 == E2:
                if nx.is_isomorphic(G1, G2):
                    iso_count += 1
                else:
                    non_iso_count += 1
                    print(f"    Non-isomorphic with same edges?? {g6_1} vs {g6_2}")
        print(f"  Checked: {iso_count} isomorphic, {non_iso_count} non-isomorphic (among sym_diff=0)")

    # Look at sym_diff=2 cases more closely (the 2-edge switch candidates)
    print("\n" + "=" * 70)
    print("ANALYZING sym_diff=2 CASES (potential switches)")
    print("=" * 70)

    switch_candidates = []
    non_switch = []

    for g6_1, g6_2, n, m1, m2 in pairs:
        if m1 != m2:
            continue

        G1 = nx.from_graph6_bytes(g6_1.encode())
        G2 = nx.from_graph6_bytes(g6_2.encode())

        E1 = set(frozenset(e) for e in G1.edges())
        E2 = set(frozenset(e) for e in G2.edges())

        if len(E1 ^ E2) != 4:  # sym_diff = 2 means 2 edges each side
            continue

        only_in_G1 = E1 - E2
        only_in_G2 = E2 - E1

        if len(only_in_G1) != 2:
            continue

        # Check if it's a valid switch (4 distinct vertices)
        verts = set()
        for e in only_in_G1 | only_in_G2:
            verts.update(e)

        if len(verts) == 4:
            # Check degree conditions
            v_list = list(verts)
            [G1.degree(v) for v in v_list]

            # For a switch, we need pairs of equal degrees
            from itertools import permutations
            is_switch = False
            for perm in permutations(v_list):
                v1, v2, w1, w2 = perm
                e1 = frozenset([v1, w1])
                e2 = frozenset([v2, w2])
                if only_in_G1 == {e1, e2}:
                    if G1.degree(v1) == G1.degree(v2) and G1.degree(w1) == G1.degree(w2):
                        is_switch = True
                        break

            if is_switch:
                switch_candidates.append((g6_1, g6_2, n))
            else:
                non_switch.append((g6_1, g6_2, n, [G1.degree(v) for v in verts]))
        else:
            non_switch.append((g6_1, g6_2, n, f"{len(verts)} verts"))

    print(f"  4-edge symmetric diff with 4 vertices AND degree conditions: {len(switch_candidates)}")
    print(f"  4-edge symmetric diff but NOT a valid switch: {len(non_switch)}")

    if non_switch:
        print("\n  Examples of non-switch 4-edge diff:")
        for item in non_switch[:5]:
            print(f"    {item}")

    conn.close()


if __name__ == "__main__":
    main()
