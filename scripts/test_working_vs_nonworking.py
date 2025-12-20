#!/usr/bin/env python3
"""Compare working switches (dist~0) vs non-working switches (dist>0)."""

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


def is_switchable_pattern(G, v1, v2, w1, w2):
    if len({v1, v2, w1, w2}) != 4:
        return False
    if not G.has_edge(v1, w1) or not G.has_edge(v2, w2):
        return False
    if G.has_edge(v1, w2) or G.has_edge(v2, w1):
        return False
    if G.degree(v1) != G.degree(v2):
        return False
    if G.degree(w1) != G.degree(w2):
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
    L = np.eye(m) - T
    return L


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


def compute_features(G, v1, v2, w1, w2):
    """Compute features for a potential switch."""
    four = {v1, v2, w1, w2}

    # External neighborhoods
    ext_N_v1 = set(n for n in G.neighbors(v1) if n not in four)
    ext_N_v2 = set(n for n in G.neighbors(v2) if n not in four)
    ext_N_w1 = set(n for n in G.neighbors(w1) if n not in four)
    ext_N_w2 = set(n for n in G.neighbors(w2) if n not in four)

    features = {}

    # External neighborhood equality
    features['ext_N_v_equal'] = (ext_N_v1 == ext_N_v2)
    features['ext_N_w_equal'] = (ext_N_w1 == ext_N_w2)
    features['ext_N_both_equal'] = features['ext_N_v_equal'] and features['ext_N_w_equal']

    # External neighborhood sizes
    features['ext_N_v1_size'] = len(ext_N_v1)
    features['ext_N_v2_size'] = len(ext_N_v2)
    features['ext_N_w1_size'] = len(ext_N_w1)
    features['ext_N_w2_size'] = len(ext_N_w2)

    # Common external neighbors
    features['common_ext_N_v'] = len(ext_N_v1 & ext_N_v2)
    features['common_ext_N_w'] = len(ext_N_w1 & ext_N_w2)

    # Cross edges within the 4 vertices
    features['v1_v2_adj'] = G.has_edge(v1, v2)
    features['w1_w2_adj'] = G.has_edge(w1, w2)
    features['v1_w2_adj'] = G.has_edge(v1, w2)  # Always False by pattern
    features['v2_w1_adj'] = G.has_edge(v2, w1)  # Always False by pattern

    # Internal edges count
    internal = 0
    for u in four:
        for v in four:
            if u < v and G.has_edge(u, v):
                internal += 1
    features['internal_edges'] = internal

    # Degrees
    features['deg_v'] = G.degree(v1)  # = G.degree(v2)
    features['deg_w'] = G.degree(w1)  # = G.degree(w2)

    # Second-order degrees
    features['deg2_v1'] = sum(G.degree(n) for n in G.neighbors(v1))
    features['deg2_v2'] = sum(G.degree(n) for n in G.neighbors(v2))
    features['deg2_w1'] = sum(G.degree(n) for n in G.neighbors(w1))
    features['deg2_w2'] = sum(G.degree(n) for n in G.neighbors(w2))

    features['deg2_v_equal'] = (features['deg2_v1'] == features['deg2_v2'])
    features['deg2_w_equal'] = (features['deg2_w1'] == features['deg2_w2'])
    features['deg2_both_equal'] = features['deg2_v_equal'] and features['deg2_w_equal']

    # Neighbor degree sequences
    def deg_seq(v):
        return tuple(sorted(G.degree(n) for n in G.neighbors(v) if n not in four))

    features['deg_seq_v1'] = deg_seq(v1)
    features['deg_seq_v2'] = deg_seq(v2)
    features['deg_seq_w1'] = deg_seq(w1)
    features['deg_seq_w2'] = deg_seq(w2)

    features['deg_seq_v_equal'] = (features['deg_seq_v1'] == features['deg_seq_v2'])
    features['deg_seq_w_equal'] = (features['deg_seq_w1'] == features['deg_seq_w2'])
    features['deg_seq_both_equal'] = features['deg_seq_v_equal'] and features['deg_seq_w_equal']

    return features


def main():
    print("Connecting to database...")
    conn = psycopg2.connect("dbname=smol")

    print("Fetching NBL-cospectral pairs...")
    pairs = get_pairs(conn)

    valid_switches = []
    for g6_1, g6_2, n, m in pairs:
        G1 = nx.from_graph6_bytes(g6_1.encode())
        G2 = nx.from_graph6_bytes(g6_2.encode())
        assignments = find_switch_vertices(G1, G2)
        if assignments:
            valid_switches.append((g6_1, g6_2, n, m, G1, G2, assignments[0]))

    print(f"Found {len(valid_switches)} NBL-cospectral switch pairs")
    print("=" * 70)

    working = []  # Switches with spectral dist ~0
    nonworking = []  # Switches with spectral dist > 0

    for idx, (g6_1, g6_2, n, m, G1, G2, assignment) in enumerate(valid_switches):
        v1, v2, w1, w2 = assignment

        # The known switch
        features = compute_features(G1, v1, v2, w1, w2)
        features['is_known'] = True
        working.append(features)

        # All other potential switches
        all_potential = find_all_potential_switches(G1)

        for pv1, pv2, pw1, pw2 in all_potential:
            if {pv1, pv2, pw1, pw2} == {v1, v2, w1, w2}:
                continue

            G_switched = perform_switch(G1, pv1, pv2, pw1, pw2)
            dist = spectral_distance(G1, G_switched)

            features = compute_features(G1, pv1, pv2, pw1, pw2)
            features['dist'] = dist
            features['is_known'] = False

            if dist < 1e-10:
                working.append(features)
            else:
                nonworking.append(features)

        if (idx + 1) % 20 == 0:
            print(f"[{idx+1}/{len(valid_switches)}] processed", file=sys.stderr)

    print()
    print("=" * 70)
    print("COMPARISON: WORKING vs NON-WORKING SWITCHES")
    print("=" * 70)
    print()
    print(f"Working (cospectral): {len(working)}")
    print(f"Non-working: {len(nonworking)}")
    print()

    bool_features = [
        ('ext_N_v_equal', 'External N(v1) = N(v2)'),
        ('ext_N_w_equal', 'External N(w1) = N(w2)'),
        ('ext_N_both_equal', 'BOTH external N equal'),
        ('v1_v2_adj', 'v1 ~ v2 (sources adjacent)'),
        ('w1_w2_adj', 'w1 ~ w2 (targets adjacent)'),
        ('deg2_v_equal', 'Second-order deg v equal'),
        ('deg2_w_equal', 'Second-order deg w equal'),
        ('deg2_both_equal', 'BOTH second-order deg equal'),
        ('deg_seq_v_equal', 'Neighbor deg seq v equal'),
        ('deg_seq_w_equal', 'Neighbor deg seq w equal'),
        ('deg_seq_both_equal', 'BOTH neighbor deg seq equal'),
    ]

    print(f"{'Feature':<40} {'Working':>10} {'Non-work':>10} {'Diff':>8}")
    print("-" * 70)

    for key, label in bool_features:
        w_pct = sum(1 for f in working if f.get(key)) / len(working) * 100
        nw_pct = sum(1 for f in nonworking if f.get(key)) / len(nonworking) * 100
        diff = w_pct - nw_pct
        marker = " <--" if abs(diff) > 20 else ""
        print(f"{label:<40} {w_pct:>9.1f}% {nw_pct:>9.1f}% {diff:>+7.1f}{marker}")

    print()
    print("=" * 70)
    print("Internal edges distribution:")
    print("-" * 70)

    for num in range(2, 5):
        w_count = sum(1 for f in working if f.get('internal_edges') == num)
        nw_count = sum(1 for f in nonworking if f.get('internal_edges') == num)
        w_pct = w_count / len(working) * 100
        nw_pct = nw_count / len(nonworking) * 100
        print(f"  {num} internal edges: Working={w_pct:5.1f}%, Non-working={nw_pct:5.1f}%")

    print()
    print("=" * 70)

    # Look for conditions that perfectly separate
    print("Looking for perfect separators...")
    print("-" * 70)

    for key, label in bool_features:
        w_true = sum(1 for f in working if f.get(key))
        nw_true = sum(1 for f in nonworking if f.get(key))
        w_false = len(working) - w_true
        nw_false = len(nonworking) - nw_true

        # Check if condition=True implies working
        if nw_true == 0 and w_true > 0:
            print(f"  {label} = True => ALWAYS WORKING ({w_true} cases)")

        # Check if condition=False implies non-working
        if w_false == 0 and nw_false > 0:
            print(f"  {label} = False => ALWAYS NON-WORKING ({nw_false} cases)")

    conn.close()


if __name__ == "__main__":
    main()
