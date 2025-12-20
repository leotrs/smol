#!/usr/bin/env python3
"""Check why no cyclic switches were found - degree conditions too strict?"""

import networkx as nx
import psycopg2


def get_nbl_pairs_min_deg_2(conn):
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


def analyze_bipartite_structure(G1, only_in_G1, only_in_G2, ell):
    """Check if edge diff has bipartite structure (could be cyclic switch)."""
    all_verts = set()
    for e in only_in_G1 | only_in_G2:
        all_verts.update(e)

    # Need exactly 2ℓ vertices for bipartite matching
    if len(all_verts) != 2 * ell:
        return None

    from itertools import combinations

    for v_set in combinations(all_verts, ell):
        v_set = set(v_set)
        w_set = all_verts - v_set

        # Check if both old and new edges form perfect matchings V↔W
        v_to_w_old = {}
        valid = True
        for e in only_in_G1:
            e_list = list(e)
            v_in = [x for x in e_list if x in v_set]
            w_in = [x for x in e_list if x in w_set]
            if len(v_in) != 1 or len(w_in) != 1:
                valid = False
                break
            v_to_w_old[v_in[0]] = w_in[0]

        if not valid or len(v_to_w_old) != ell:
            continue

        v_to_w_new = {}
        for e in only_in_G2:
            e_list = list(e)
            v_in = [x for x in e_list if x in v_set]
            w_in = [x for x in e_list if x in w_set]
            if len(v_in) != 1 or len(w_in) != 1:
                valid = False
                break
            v_to_w_new[v_in[0]] = w_in[0]

        if not valid or len(v_to_w_new) != ell:
            continue

        # Found bipartite structure! Check permutation type
        w_perm = {v_to_w_old[v]: v_to_w_new[v] for v in v_set}

        # Find cycle structure
        cycles = []
        visited = set()
        for start in w_set:
            if start in visited:
                continue
            cycle = []
            current = start
            while current not in visited:
                visited.add(current)
                cycle.append(current)
                current = w_perm.get(current)
                if current is None:
                    break
            if cycle:
                cycles.append(len(cycle))

        # Check degree conditions
        v_degs = sorted([G1.degree(v) for v in v_set])
        w_degs = sorted([G1.degree(w) for w in w_set])

        return {
            'v_set': v_set,
            'w_set': w_set,
            'cycle_structure': sorted(cycles, reverse=True),
            'v_degrees': v_degs,
            'w_degrees': w_degs,
            'v_all_equal': len(set(v_degs)) == 1,
            'w_all_equal': len(set(w_degs)) == 1,
        }

    return None


def main():
    conn = psycopg2.connect("dbname=smol")
    pairs = get_nbl_pairs_min_deg_2(conn)

    print(f"Analyzing {len(pairs)} NBL-cospectral pairs (min_deg >= 2)\n")

    by_diff = {}
    for g6_1, g6_2, n in pairs:
        G1 = nx.from_graph6_bytes(g6_1.encode())
        G2 = nx.from_graph6_bytes(g6_2.encode())

        E1 = set(frozenset(e) for e in G1.edges())
        E2 = set(frozenset(e) for e in G2.edges())
        only_in_G1 = E1 - E2
        only_in_G2 = E2 - E1
        ell = len(only_in_G1)

        if ell not in by_diff:
            by_diff[ell] = []
        by_diff[ell].append((g6_1, g6_2, n, G1, only_in_G1, only_in_G2))

    for ell in sorted(by_diff.keys()):
        if ell < 3:
            continue

        print("=" * 70)
        print(f"ℓ = {ell} edges differ ({len(by_diff[ell])} pairs)")
        print("=" * 70)

        has_bipartite = 0
        has_single_cycle = 0
        degree_ok = 0

        for g6_1, g6_2, n, G1, only_in_G1, only_in_G2 in by_diff[ell]:
            info = analyze_bipartite_structure(G1, only_in_G1, only_in_G2, ell)

            if info:
                has_bipartite += 1
                is_single_cycle = (info['cycle_structure'] == [ell])
                if is_single_cycle:
                    has_single_cycle += 1
                if info['v_all_equal'] and info['w_all_equal']:
                    degree_ok += 1

                print(f"\n  {g6_1} ↔ {g6_2} (n={n})")
                print(f"    Cycle structure: {info['cycle_structure']}")
                print(f"    V degrees: {info['v_degrees']} (all equal: {info['v_all_equal']})")
                print(f"    W degrees: {info['w_degrees']} (all equal: {info['w_all_equal']})")

                if is_single_cycle and info['v_all_equal'] and info['w_all_equal']:
                    print("    *** SHOULD BE CYCLIC SWITCH! ***")

        print(f"\n  Summary for ℓ={ell}:")
        print(f"    Has bipartite structure: {has_bipartite}/{len(by_diff[ell])}")
        print(f"    Has single ℓ-cycle: {has_single_cycle}/{len(by_diff[ell])}")
        print(f"    Degree conditions met: {degree_ok}/{len(by_diff[ell])}")

    conn.close()


if __name__ == "__main__":
    main()
