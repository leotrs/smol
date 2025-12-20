#!/usr/bin/env python3
"""Analyze edge differences in NBL-cospectral pairs (min_degree >= 2 only)."""

import networkx as nx
import psycopg2
from collections import Counter, defaultdict
from itertools import permutations


def get_nbl_pairs_min_deg_2(conn):
    """Get NBL-cospectral pairs where both graphs have min_degree >= 2."""
    cur = conn.cursor()
    cur.execute("""
        SELECT g1.graph6, g2.graph6, g1.n
        FROM cospectral_mates cm
        JOIN graphs g1 ON cm.graph1_id = g1.id
        JOIN graphs g2 ON cm.graph2_id = g2.id
        WHERE cm.matrix_type = 'nbl'
          AND g1.min_degree >= 2
          AND g2.min_degree >= 2
    """)
    return cur.fetchall()


def is_simple_switch(G1, only_in_G1, only_in_G2):
    """Check if this is a simple 2-edge switch with degree conditions."""
    if len(only_in_G1) != 2 or len(only_in_G2) != 2:
        return False, None

    verts = set()
    for e in only_in_G1 | only_in_G2:
        verts.update(e)

    if len(verts) != 4:
        return False, None

    for perm in permutations(verts):
        v1, v2, w1, w2 = perm
        e1 = frozenset([v1, w1])
        e2 = frozenset([v2, w2])
        new_e1 = frozenset([v1, w2])
        new_e2 = frozenset([v2, w1])

        if only_in_G1 == {e1, e2} and only_in_G2 == {new_e1, new_e2}:
            if G1.degree(v1) == G1.degree(v2) and G1.degree(w1) == G1.degree(w2):
                return True, (v1, v2, w1, w2)

    return False, None


def is_cyclic_switch(G1, only_in_G1, only_in_G2, ell):
    """Check if this is an ℓ-edge cyclic switch with degree conditions."""
    if len(only_in_G1) != ell or len(only_in_G2) != ell:
        return False, None

    all_verts = set()
    for e in only_in_G1 | only_in_G2:
        all_verts.update(e)

    if len(all_verts) != 2 * ell:
        return False, None

    from itertools import combinations

    for v_set in combinations(all_verts, ell):
        v_set = set(v_set)
        w_set = all_verts - v_set

        v_to_w_old = {}
        valid_old = True
        for e in only_in_G1:
            e_list = list(e)
            v_in = [x for x in e_list if x in v_set]
            w_in = [x for x in e_list if x in w_set]
            if len(v_in) != 1 or len(w_in) != 1:
                valid_old = False
                break
            v_to_w_old[v_in[0]] = w_in[0]

        if not valid_old or len(v_to_w_old) != ell:
            continue

        v_to_w_new = {}
        valid_new = True
        for e in only_in_G2:
            e_list = list(e)
            v_in = [x for x in e_list if x in v_set]
            w_in = [x for x in e_list if x in w_set]
            if len(v_in) != 1 or len(w_in) != 1:
                valid_new = False
                break
            v_to_w_new[v_in[0]] = w_in[0]

        if not valid_new or len(v_to_w_new) != ell:
            continue

        # Check if permutation is a single ℓ-cycle
        w_perm = {v_to_w_old[v]: v_to_w_new[v] for v in v_set}

        visited = set()
        start = next(iter(w_set))
        current = start
        cycle_len = 0
        while current not in visited:
            visited.add(current)
            current = w_perm.get(current)
            cycle_len += 1
            if current is None:
                break

        if cycle_len == ell and current == start and len(visited) == ell:
            v_degs = [G1.degree(v) for v in v_set]
            w_degs = [G1.degree(w) for w in w_set]
            if len(set(v_degs)) == 1 and len(set(w_degs)) == 1:
                return True, {'v_set': v_set, 'w_set': w_set, 'ell': ell}

    return False, None


def main():
    print("Connecting to database...")
    conn = psycopg2.connect("dbname=smol")
    pairs = get_nbl_pairs_min_deg_2(conn)
    print(f"NBL-cospectral pairs (min_degree >= 2): {len(pairs)}")

    edge_diff_counts = Counter()
    simple_switches = []
    cyclic_switches = defaultdict(list)

    for i, (g6_1, g6_2, n) in enumerate(pairs):
        G1 = nx.from_graph6_bytes(g6_1.encode())
        G2 = nx.from_graph6_bytes(g6_2.encode())

        E1 = set(frozenset(e) for e in G1.edges())
        E2 = set(frozenset(e) for e in G2.edges())
        only_in_G1 = E1 - E2
        only_in_G2 = E2 - E1

        diff_size = len(only_in_G1)
        edge_diff_counts[diff_size] += 1

        if diff_size == 2:
            is_switch, assignment = is_simple_switch(G1, only_in_G1, only_in_G2)
            if is_switch:
                simple_switches.append((g6_1, g6_2, n, assignment))

        elif 3 <= diff_size <= 6:
            is_cyclic, info = is_cyclic_switch(G1, only_in_G1, only_in_G2, diff_size)
            if is_cyclic:
                cyclic_switches[diff_size].append((g6_1, g6_2, n, info))

        if (i + 1) % 5000 == 0:
            print(f"  Processed {i+1}/{len(pairs)}...")

    print("\n" + "=" * 70)
    print("EDGE DIFFERENCE DISTRIBUTION (edges in G1 but not G2)")
    print("=" * 70)
    for diff_size in sorted(edge_diff_counts.keys()):
        count = edge_diff_counts[diff_size]
        pct = 100 * count / len(pairs)
        print(f"  {diff_size} edges: {count:>5} pairs ({pct:>5.1f}%)")

    print("\n" + "=" * 70)
    print("SIMPLE 2-EDGE SWITCHES (ℓ=2, Theorem 4.2)")
    print("=" * 70)
    print(f"  Found: {len(simple_switches)} pairs")
    if simple_switches:
        print("  Examples:")
        for g6_1, g6_2, n, (v1, v2, w1, w2) in simple_switches[:3]:
            print(f"    n={n}: {g6_1} ↔ {g6_2}")
            print(f"           switch: ({v1},{w1}),({v2},{w2}) → ({v1},{w2}),({v2},{w1})")

    print("\n" + "=" * 70)
    print("CYCLIC ℓ-EDGE SWITCHES (ℓ≥3, Theorem 4.3)")
    print("=" * 70)
    total_cyclic = sum(len(v) for v in cyclic_switches.values())
    print(f"  Total found: {total_cyclic}")
    for ell in sorted(cyclic_switches.keys()):
        print(f"  ℓ={ell}: {len(cyclic_switches[ell])} pairs")
        for g6_1, g6_2, n, info in cyclic_switches[ell][:2]:
            print(f"    n={n}: {g6_1} ↔ {g6_2}")
            print(f"           V={info['v_set']}, W={info['w_set']}")

    # Summary
    explained = len(simple_switches) + total_cyclic
    print("\n" + "=" * 70)
    print("SUMMARY")
    print("=" * 70)
    print(f"  Total pairs (min_deg≥2): {len(pairs)}")
    print(f"  Simple 2-switches: {len(simple_switches)}")
    print(f"  Cyclic ℓ-switches: {total_cyclic}")
    print(f"  EXPLAINED by Thm 4.2/4.3: {explained} ({100*explained/len(pairs):.1f}%)")
    print(f"  NOT explained: {len(pairs) - explained} ({100*(len(pairs)-explained)/len(pairs):.1f}%)")

    conn.close()


if __name__ == "__main__":
    main()
