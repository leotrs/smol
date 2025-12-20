#!/usr/bin/env python3
"""Test conditions on edges that satisfy ALL prerequisites.

Filter to edge pairs where:
- deg(a) = deg(c), deg(b) = deg(d)  (degree conditions)
- a≁d AND c≁b  (non-adjacency / switchable pattern)
- 4 distinct vertices

Then see what else distinguishes actual switches from these "potential" switches.
"""

import sys
from itertools import permutations

import networkx as nx
import numpy as np
import psycopg2

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


def is_switchable_pattern(G, a, b, c, d):
    """Check if edges [a,b] and [c,d] have the switchable pattern."""
    # 4 distinct vertices
    if len({a, b, c, d}) != 4:
        return False
    # Non-adjacency: a≁d and c≁b
    if G.has_edge(a, d) or G.has_edge(c, b):
        return False
    return True


def check_conditions(G, T_np, directed_edges, edge_to_idx, i, j):
    """Check various conditions for a fully-qualified edge pair."""
    e_i = directed_edges[i]  # (a, b)
    e_j = directed_edges[j]  # (c, d)
    a, b = e_i
    c, d = e_j

    results = {}

    # Neighborhood structure
    N_a = set(G.neighbors(a))
    N_b = set(G.neighbors(b))
    N_c = set(G.neighbors(c))
    N_d = set(G.neighbors(d))

    results['common_N_source'] = len(N_a & N_c)
    results['common_N_target'] = len(N_b & N_d)

    # Are sources adjacent? Are targets adjacent?
    results['sources_adjacent'] = G.has_edge(a, c)
    results['targets_adjacent'] = G.has_edge(b, d)

    # Neighborhood overlap ratios
    results['jaccard_source'] = len(N_a & N_c) / len(N_a | N_c) if len(N_a | N_c) > 0 else 0
    results['jaccard_target'] = len(N_b & N_d) / len(N_b | N_d) if len(N_b | N_d) > 0 else 0

    # Compute T^k
    T1 = T_np
    T2 = T_np @ T_np
    T2 @ T_np

    # Row differences
    results['row_diff_L1_k1'] = np.sum(np.abs(T1[i] - T1[j]))
    results['row_diff_L1_k2'] = np.sum(np.abs(T2[i] - T2[j]))
    results['row_diff_L2_k1'] = np.linalg.norm(T1[i] - T1[j])
    results['row_diff_L2_k2'] = np.linalg.norm(T2[i] - T2[j])

    # Cross entries
    results['cross_ij_k1'] = T1[i, j]
    results['cross_ji_k1'] = T1[j, i]
    results['cross_ij_k2'] = T2[i, j]
    results['cross_ji_k2'] = T2[j, i]
    results['cross_diff_k2'] = abs(T2[i, j] - T2[j, i])

    # Get reverse edge indices
    rev_i = edge_to_idx.get((b, a))
    rev_j = edge_to_idx.get((d, c))

    # Check if the "parallel" reverse edges also exist and have similar structure
    if rev_i is not None and rev_j is not None:
        results['rev_row_diff_L2_k1'] = np.linalg.norm(T1[rev_i] - T1[rev_j])
        results['rev_row_diff_L2_k2'] = np.linalg.norm(T2[rev_i] - T2[rev_j])

    # Distance in graph between vertices
    try:
        results['dist_a_c'] = nx.shortest_path_length(G, a, c)
    except nx.NetworkXNoPath:
        results['dist_a_c'] = -1
    try:
        results['dist_b_d'] = nx.shortest_path_length(G, b, d)
    except nx.NetworkXNoPath:
        results['dist_b_d'] = -1

    # Second-order degree: sum of neighbor degrees
    results['deg2_a'] = sum(G.degree(n) for n in G.neighbors(a))
    results['deg2_c'] = sum(G.degree(n) for n in G.neighbors(c))
    results['deg2_b'] = sum(G.degree(n) for n in G.neighbors(b))
    results['deg2_d'] = sum(G.degree(n) for n in G.neighbors(d))
    results['deg2_source_match'] = results['deg2_a'] == results['deg2_c']
    results['deg2_target_match'] = results['deg2_b'] == results['deg2_d']

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
    print("Filtering to edges with degree + non-adjacency + 4 distinct vertices...")
    print("=" * 70)

    switch_stats = []
    nonswitch_stats = []

    for idx, (g6_1, g6_2, n, m, G1, assignment) in enumerate(valid_switches):
        v1, v2, w1, w2 = assignment

        T_np, directed_edges, edge_to_idx = build_T_numpy(G1)
        num_edges = len(directed_edges)

        # Switch edge indices
        switch_pairs = {
            (edge_to_idx[(v1, w1)], edge_to_idx[(v2, w2)]),
            (edge_to_idx[(w1, v1)], edge_to_idx[(w2, v2)]),
        }

        # Check ALL edge pairs with full filter
        for i in range(num_edges):
            for j in range(i + 1, num_edges):
                e_i = directed_edges[i]
                e_j = directed_edges[j]
                a, b = e_i
                c, d = e_j

                # Degree conditions
                if G1.degree(a) != G1.degree(c):
                    continue
                if G1.degree(b) != G1.degree(d):
                    continue

                # Switchable pattern
                if not is_switchable_pattern(G1, a, b, c, d):
                    continue

                results = check_conditions(G1, T_np, directed_edges, edge_to_idx, i, j)
                results['is_switch'] = (i, j) in switch_pairs or (j, i) in switch_pairs

                if results['is_switch']:
                    switch_stats.append(results)
                else:
                    nonswitch_stats.append(results)

        if (idx + 1) % 20 == 0:
            print(f"[{idx+1}/{len(valid_switches)}] processed", file=sys.stderr)

    print()
    print("=" * 70)
    print("RESULTS: Edges satisfying degree + non-adjacency + 4 distinct")
    print("=" * 70)
    print()
    print(f"Actual switch pairs: {len(switch_stats)}")
    print(f"'Potential' switch pairs (non-switch): {len(nonswitch_stats)}")
    print()

    # Boolean conditions
    bool_conditions = [
        ('sources_adjacent', 'Sources adjacent (a~c)'),
        ('targets_adjacent', 'Targets adjacent (b~d)'),
        ('deg2_source_match', 'Second-order degree match (sources)'),
        ('deg2_target_match', 'Second-order degree match (targets)'),
    ]

    print("Boolean conditions:")
    print("-" * 60)
    print(f"{'Condition':<45} {'Switch':>8} {'Non-Sw':>8}")
    print("-" * 60)

    for key, label in bool_conditions:
        sw = sum(1 for s in switch_stats if s.get(key)) / len(switch_stats) * 100 if switch_stats else 0
        nsw = sum(1 for s in nonswitch_stats if s.get(key)) / len(nonswitch_stats) * 100 if nonswitch_stats else 0
        print(f"{label:<45} {sw:>7.0f}% {nsw:>7.0f}%")

    print()
    print("Numeric conditions (mean values):")
    print("-" * 60)

    numeric_conditions = [
        ('common_N_source', 'Common neighbors (sources)'),
        ('common_N_target', 'Common neighbors (targets)'),
        ('jaccard_source', 'Jaccard similarity (sources)'),
        ('jaccard_target', 'Jaccard similarity (targets)'),
        ('row_diff_L2_k1', 'Row difference L2 at k=1'),
        ('row_diff_L2_k2', 'Row difference L2 at k=2'),
        ('cross_diff_k2', 'Cross-entry difference at k=2'),
        ('dist_a_c', 'Distance between sources'),
        ('dist_b_d', 'Distance between targets'),
    ]

    print(f"{'Condition':<45} {'Switch':>8} {'Non-Sw':>8}")
    print("-" * 60)

    for key, label in numeric_conditions:
        sw_vals = [s[key] for s in switch_stats if s.get(key) is not None and s[key] >= 0]
        nsw_vals = [s[key] for s in nonswitch_stats if s.get(key) is not None and s[key] >= 0]
        sw_mean = np.mean(sw_vals) if sw_vals else 0
        nsw_mean = np.mean(nsw_vals) if nsw_vals else 0
        print(f"{label:<45} {sw_mean:>8.3f} {nsw_mean:>8.3f}")

    print()
    print("=" * 70)

    # Check combined conditions
    print()
    print("Combined conditions:")
    print("-" * 60)

    # Both second-order degrees match
    sw_both_deg2 = sum(1 for s in switch_stats if s['deg2_source_match'] and s['deg2_target_match'])
    nsw_both_deg2 = sum(1 for s in nonswitch_stats if s['deg2_source_match'] and s['deg2_target_match'])
    print(f"Both second-order degrees match: Switch={sw_both_deg2}/{len(switch_stats)}, Non-switch={nsw_both_deg2}/{len(nonswitch_stats)}")

    # Neither sources nor targets adjacent
    sw_neither_adj = sum(1 for s in switch_stats if not s['sources_adjacent'] and not s['targets_adjacent'])
    nsw_neither_adj = sum(1 for s in nonswitch_stats if not s['sources_adjacent'] and not s['targets_adjacent'])
    print(f"Neither sources nor targets adjacent: Switch={sw_neither_adj}/{len(switch_stats)}, Non-switch={nsw_neither_adj}/{len(nonswitch_stats)}")

    # Row diff near zero
    sw_small_diff = sum(1 for s in switch_stats if s['row_diff_L2_k1'] < 0.01)
    nsw_small_diff = sum(1 for s in nonswitch_stats if s['row_diff_L2_k1'] < 0.01)
    print(f"Row diff L2 < 0.01 at k=1: Switch={sw_small_diff}/{len(switch_stats)}, Non-switch={nsw_small_diff}/{len(nonswitch_stats)}")

    print()
    print("=" * 70)

    conn.close()


if __name__ == "__main__":
    main()
