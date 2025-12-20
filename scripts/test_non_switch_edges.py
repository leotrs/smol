#!/usr/bin/env python3
"""Check if permutation-equal rows and same diagonal are specific to switch edges.

For each valid switch, compare:
- Switch edges: [v1,w1] vs [v2,w2] and [w1,v1] vs [w2,v2]
- Non-switch edges: all other pairs of directed edges
"""

import sys
from itertools import combinations, permutations

import networkx as nx
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


def rows_permutation_equal(M, i, j):
    row_i = sorted(M.row(i))
    row_j = sorted(M.row(j))
    return row_i == row_j


def same_diagonal(M, i, j):
    return M[i, i] == M[j, j]


def check_all_pairs(T, edge_to_idx, directed_edges, switch_indices, max_k=2):
    """Check conditions for all edge pairs, separating switch vs non-switch."""
    m = T.rows

    # Compute T^k for k=1,2
    T1 = T
    T2 = T * T

    switch_set = set(switch_indices)

    results = {
        'switch_perm_k1': 0,
        'switch_diag_k1': 0,
        'switch_diag_k2': 0,
        'switch_total': 0,
        'nonswitch_perm_k1': 0,
        'nonswitch_diag_k1': 0,
        'nonswitch_diag_k2': 0,
        'nonswitch_total': 0,
    }

    # Check all pairs of directed edges
    for i, j in combinations(range(m), 2):
        is_switch_pair = (i in switch_set and j in switch_set)

        perm_k1 = rows_permutation_equal(T1, i, j)
        diag_k1 = same_diagonal(T1, i, j)
        diag_k2 = same_diagonal(T2, i, j)

        if is_switch_pair:
            results['switch_total'] += 1
            if perm_k1:
                results['switch_perm_k1'] += 1
            if diag_k1:
                results['switch_diag_k1'] += 1
            if diag_k2:
                results['switch_diag_k2'] += 1
        else:
            results['nonswitch_total'] += 1
            if perm_k1:
                results['nonswitch_perm_k1'] += 1
            if diag_k1:
                results['nonswitch_diag_k1'] += 1
            if diag_k2:
                results['nonswitch_diag_k2'] += 1

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
    print()

    # Aggregate stats
    totals = {
        'switch_perm_k1': 0,
        'switch_diag_k1': 0,
        'switch_diag_k2': 0,
        'switch_total': 0,
        'nonswitch_perm_k1': 0,
        'nonswitch_diag_k1': 0,
        'nonswitch_diag_k2': 0,
        'nonswitch_total': 0,
    }

    for i, (g6_1, g6_2, n, m, G1, assignment) in enumerate(valid_switches):
        v1, v2, w1, w2 = assignment

        T, directed_edges, edge_to_idx = build_T_sympy(G1)

        # Get indices of switch edges
        switch_indices = [
            edge_to_idx[(v1, w1)],
            edge_to_idx[(v2, w2)],
            edge_to_idx[(w1, v1)],
            edge_to_idx[(w2, v2)],
        ]

        results = check_all_pairs(T, edge_to_idx, directed_edges, switch_indices)

        for key in totals:
            totals[key] += results[key]

        if (i + 1) % 20 == 0:
            print(f"[{i+1}/{len(valid_switches)}] processed", file=sys.stderr)

    print()
    print("=" * 70)
    print("AGGREGATE RESULTS ACROSS ALL 92 SWITCHES")
    print("=" * 70)
    print()

    print("SWITCH EDGE PAIRS (the 4 directed edges involved in switch):")
    print(f"  Total pairs checked: {totals['switch_total']}")
    print(f"  Permutation-equal rows at k=1: {totals['switch_perm_k1']} ({100*totals['switch_perm_k1']/totals['switch_total']:.1f}%)")
    print(f"  Same diagonal at k=1: {totals['switch_diag_k1']} ({100*totals['switch_diag_k1']/totals['switch_total']:.1f}%)")
    print(f"  Same diagonal at k=2: {totals['switch_diag_k2']} ({100*totals['switch_diag_k2']/totals['switch_total']:.1f}%)")
    print()

    print("NON-SWITCH EDGE PAIRS (all other directed edge pairs):")
    print(f"  Total pairs checked: {totals['nonswitch_total']}")
    print(f"  Permutation-equal rows at k=1: {totals['nonswitch_perm_k1']} ({100*totals['nonswitch_perm_k1']/totals['nonswitch_total']:.1f}%)")
    print(f"  Same diagonal at k=1: {totals['nonswitch_diag_k1']} ({100*totals['nonswitch_diag_k1']/totals['nonswitch_total']:.1f}%)")
    print(f"  Same diagonal at k=2: {totals['nonswitch_diag_k2']} ({100*totals['nonswitch_diag_k2']/totals['nonswitch_total']:.1f}%)")
    print()
    print("=" * 70)

    conn.close()


if __name__ == "__main__":
    main()
