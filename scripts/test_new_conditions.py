#!/usr/bin/env python3
"""Search for new conditions that explain working switches not covered by Condition B."""

import sys
from itertools import permutations

import networkx as nx
import numpy as np
import psycopg2

sys.path.insert(0, str(__file__).rsplit("/", 2)[0])


def get_pairs(conn):
    cur = conn.cursor()
    cur.execute("""
        SELECT g1.graph6, g2.graph6, g1.n, g1.m
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


def compute_extended_features(G, v1, v2, w1, w2):
    """Compute extended features for switch analysis."""
    S = {v1, v2, w1, w2}

    # External neighborhoods
    ext_v1 = set(n for n in G.neighbors(v1) if n not in S)
    ext_v2 = set(n for n in G.neighbors(v2) if n not in S)
    ext_w1 = set(n for n in G.neighbors(w1) if n not in S)
    ext_w2 = set(n for n in G.neighbors(w2) if n not in S)

    f = {}

    # Basic Condition B
    f['ext_v_equal'] = ext_v1 == ext_v2
    f['ext_w_equal'] = ext_w1 == ext_w2
    f['condition_B'] = f['ext_v_equal'] or f['ext_w_equal']

    # Sizes
    f['ext_v1_size'] = len(ext_v1)
    f['ext_v2_size'] = len(ext_v2)
    f['ext_w1_size'] = len(ext_w1)
    f['ext_w2_size'] = len(ext_w2)

    # Symmetric differences
    f['sym_diff_v'] = len(ext_v1 ^ ext_v2)
    f['sym_diff_w'] = len(ext_w1 ^ ext_w2)
    f['sym_diff_equal'] = f['sym_diff_v'] == f['sym_diff_w']

    # Common external neighbors
    f['common_v'] = len(ext_v1 & ext_v2)
    f['common_w'] = len(ext_w1 & ext_w2)
    f['common_equal'] = f['common_v'] == f['common_w']

    # Cross-connections: do external neighbors of v connect to w's?
    # For each x in ext_v1, is x also in ext_w2?
    f['cross_v1_w2'] = len(ext_v1 & ext_w2)
    f['cross_v2_w1'] = len(ext_v2 & ext_w1)
    f['cross_v1_w1'] = len(ext_v1 & ext_w1)
    f['cross_v2_w2'] = len(ext_v2 & ext_w2)

    # Symmetric cross condition
    f['cross_switched_equal'] = f['cross_v1_w2'] == f['cross_v2_w1']
    f['cross_same_equal'] = f['cross_v1_w1'] == f['cross_v2_w2']

    # All four external neighborhoods union
    all_ext = ext_v1 | ext_v2 | ext_w1 | ext_w2
    f['total_ext'] = len(all_ext)

    # Bipartite structure: edges from {v1,v2} ext to {w1,w2} ext
    f['bipartite_v_to_w'] = 0
    for x in ext_v1 | ext_v2:
        for y in ext_w1 | ext_w2:
            if G.has_edge(x, y):
                f['bipartite_v_to_w'] += 1

    # Internal edges within S
    f['internal'] = sum(1 for u in S for w in S if u < w and G.has_edge(u, w))
    f['v1_v2_adj'] = G.has_edge(v1, v2)
    f['w1_w2_adj'] = G.has_edge(w1, w2)

    # Degrees
    f['deg_v'] = G.degree(v1)
    f['deg_w'] = G.degree(w1)

    # Second-order structure: degree sum of neighbors
    f['deg2_v1'] = sum(G.degree(n) for n in G.neighbors(v1))
    f['deg2_v2'] = sum(G.degree(n) for n in G.neighbors(v2))
    f['deg2_w1'] = sum(G.degree(n) for n in G.neighbors(w1))
    f['deg2_w2'] = sum(G.degree(n) for n in G.neighbors(w2))
    f['deg2_v_equal'] = f['deg2_v1'] == f['deg2_v2']
    f['deg2_w_equal'] = f['deg2_w1'] == f['deg2_w2']

    # Triangle counts involving switch vertices
    def triangles_at(v):
        nbrs = list(G.neighbors(v))
        count = 0
        for i, a in enumerate(nbrs):
            for b in nbrs[i+1:]:
                if G.has_edge(a, b):
                    count += 1
        return count

    f['tri_v1'] = triangles_at(v1)
    f['tri_v2'] = triangles_at(v2)
    f['tri_w1'] = triangles_at(w1)
    f['tri_w2'] = triangles_at(w2)
    f['tri_v_equal'] = f['tri_v1'] == f['tri_v2']
    f['tri_w_equal'] = f['tri_w1'] == f['tri_w2']

    # External neighborhood degree sequences
    def ext_deg_seq(ext_set):
        return tuple(sorted(G.degree(x) for x in ext_set))

    f['ext_deg_seq_v1'] = ext_deg_seq(ext_v1)
    f['ext_deg_seq_v2'] = ext_deg_seq(ext_v2)
    f['ext_deg_seq_w1'] = ext_deg_seq(ext_w1)
    f['ext_deg_seq_w2'] = ext_deg_seq(ext_w2)
    f['ext_deg_seq_v_equal'] = f['ext_deg_seq_v1'] == f['ext_deg_seq_v2']
    f['ext_deg_seq_w_equal'] = f['ext_deg_seq_w1'] == f['ext_deg_seq_w2']

    # Combined condition: same sizes and same common
    f['sizes_and_common'] = (len(ext_v1) == len(ext_v2) and
                             len(ext_w1) == len(ext_w2) and
                             f['common_v'] == f['common_w'])

    # New: size difference equality
    f['size_diff_v'] = abs(len(ext_v1) - len(ext_v2))
    f['size_diff_w'] = abs(len(ext_w1) - len(ext_w2))
    f['size_diff_equal'] = f['size_diff_v'] == f['size_diff_w']

    return f


def main():
    print("Connecting to database...")
    conn = psycopg2.connect("dbname=smol")

    print("Fetching NBL-cospectral pairs...")
    pairs = get_pairs(conn)

    # Find valid switch pairs
    switch_pairs = []
    for g6_1, g6_2, n, m in pairs:
        G1 = nx.from_graph6_bytes(g6_1.encode())
        G2 = nx.from_graph6_bytes(g6_2.encode())
        assignment = find_switch_vertices(G1, G2)
        if assignment:
            switch_pairs.append((g6_1, G1, assignment, True))  # Known working

    print(f"Found {len(switch_pairs)} known NBL-cospectral switch pairs")

    # Collect all switches and their features
    working = []
    nonworking = []

    processed_graphs = set()

    for idx, (g6, G, assignment, _) in enumerate(switch_pairs):
        if g6 in processed_graphs:
            continue
        processed_graphs.add(g6)

        v1, v2, w1, w2 = assignment

        # Known working switch
        f = compute_extended_features(G, v1, v2, w1, w2)
        f['g6'] = g6
        f['known'] = True
        working.append(f)

        # All other potential switches in this graph
        all_potential = find_all_potential_switches(G)

        for pv1, pv2, pw1, pw2 in all_potential:
            if {pv1, pv2, pw1, pw2} == {v1, v2, w1, w2}:
                continue

            G_switched = perform_switch(G, pv1, pv2, pw1, pw2)
            dist = spectral_distance(G, G_switched)

            f = compute_extended_features(G, pv1, pv2, pw1, pw2)
            f['g6'] = g6
            f['known'] = False
            f['dist'] = dist

            if dist < 1e-10:
                working.append(f)
            else:
                nonworking.append(f)

        if (idx + 1) % 25 == 0:
            print(f"  [{idx+1}/{len(switch_pairs)}]", file=sys.stderr)

    print(f"\nWorking switches: {len(working)}")
    print(f"Non-working switches: {len(nonworking)}")

    # Analyze condition B coverage
    cond_B_working = [f for f in working if f['condition_B']]
    non_cond_B_working = [f for f in working if not f['condition_B']]

    print(f"\nCondition B explains: {len(cond_B_working)}/{len(working)} working switches")
    print(f"Remaining to explain: {len(non_cond_B_working)}")

    # Look for conditions that separate non-Condition-B switches
    print("\n" + "=" * 70)
    print("SEARCHING FOR CONDITIONS (excluding Condition B cases)")
    print("=" * 70)

    # Only look at non-Condition-B cases
    target_working = non_cond_B_working
    target_nonworking = [f for f in nonworking if not f['condition_B']]

    print(f"\nTarget working (no Cond B): {len(target_working)}")
    print(f"Target non-working (no Cond B): {len(target_nonworking)}")

    conditions = [
        ('sym_diff_equal', 'Symmetric diff sizes equal'),
        ('common_equal', 'Common neighbor counts equal'),
        ('cross_switched_equal', 'Cross connections (switched) equal'),
        ('cross_same_equal', 'Cross connections (same) equal'),
        ('v1_v2_adj', 'v1 ~ v2'),
        ('w1_w2_adj', 'w1 ~ w2'),
        ('deg2_v_equal', '2nd-order degree v equal'),
        ('deg2_w_equal', '2nd-order degree w equal'),
        ('tri_v_equal', 'Triangle count v equal'),
        ('tri_w_equal', 'Triangle count w equal'),
        ('ext_deg_seq_v_equal', 'Ext neighbor deg seq v equal'),
        ('ext_deg_seq_w_equal', 'Ext neighbor deg seq w equal'),
        ('sizes_and_common', 'Sizes equal AND common equal'),
        ('size_diff_equal', 'Size differences equal'),
    ]

    print(f"\n{'Condition':<45} {'Work':>8} {'Non-W':>8} {'Prec':>8}")
    print("-" * 70)

    for key, label in conditions:
        w_true = sum(1 for f in target_working if f.get(key))
        nw_true = sum(1 for f in target_nonworking if f.get(key))

        w_pct = w_true / len(target_working) * 100 if target_working else 0
        nw_pct = nw_true / len(target_nonworking) * 100 if target_nonworking else 0

        # Precision: if condition is true, what % are working?
        total_true = w_true + nw_true
        precision = w_true / total_true * 100 if total_true > 0 else 0

        marker = ""
        if nw_true == 0 and w_true > 0:
            marker = " *** PERFECT"
        elif precision > 80:
            marker = " <--"

        print(f"{label:<45} {w_pct:>7.1f}% {nw_pct:>7.1f}% {precision:>7.1f}%{marker}")

    # Look for combinations
    print("\n" + "=" * 70)
    print("COMBINATION CONDITIONS")
    print("=" * 70)

    def check_combo(name, predicate):
        w_true = sum(1 for f in target_working if predicate(f))
        nw_true = sum(1 for f in target_nonworking if predicate(f))
        total = w_true + nw_true
        prec = w_true / total * 100 if total else 0
        perf = " *** PERFECT" if nw_true == 0 and w_true > 0 else ""
        print(f"{name:<55} W:{w_true:>4} NW:{nw_true:>4} Prec:{prec:>5.1f}%{perf}")

    check_combo("sym_diff_v == sym_diff_w == 0",
                lambda f: f['sym_diff_v'] == 0 and f['sym_diff_w'] == 0)

    check_combo("common_v == common_w AND sym_diff_v == sym_diff_w",
                lambda f: f['common_v'] == f['common_w'] and f['sym_diff_v'] == f['sym_diff_w'])

    check_combo("cross_v1_w2 == cross_v2_w1 AND cross_v1_w1 == cross_v2_w2",
                lambda f: f['cross_switched_equal'] and f['cross_same_equal'])

    check_combo("all external neighborhoods pairwise disjoint",
                lambda f: f['cross_v1_w2'] == 0 and f['cross_v2_w1'] == 0 and
                         f['cross_v1_w1'] == 0 and f['cross_v2_w2'] == 0 and
                         f['common_v'] == 0 and f['common_w'] == 0)

    check_combo("v1~v2 AND w1~w2",
                lambda f: f['v1_v2_adj'] and f['w1_w2_adj'])

    check_combo("ext sizes equal AND common equal",
                lambda f: f['ext_v1_size'] == f['ext_v2_size'] and
                         f['ext_w1_size'] == f['ext_w2_size'] and
                         f['common_v'] == f['common_w'])

    check_combo("deg2 both equal AND tri both equal",
                lambda f: f['deg2_v_equal'] and f['deg2_w_equal'] and
                         f['tri_v_equal'] and f['tri_w_equal'])

    check_combo("ext deg seq both equal",
                lambda f: f['ext_deg_seq_v_equal'] and f['ext_deg_seq_w_equal'])

    # Look at the working cases that fail all simple conditions
    print("\n" + "=" * 70)
    print("ANALYZING HARD CASES")
    print("=" * 70)

    hard_cases = [f for f in target_working if
                  not f['sym_diff_equal'] and
                  not f['common_equal'] and
                  not (f['cross_switched_equal'] and f['cross_same_equal'])]

    print(f"\nHard cases (no simple condition): {len(hard_cases)}/{len(target_working)}")

    if hard_cases:
        print("\nFirst 5 hard cases:")
        for i, f in enumerate(hard_cases[:5]):
            print(f"\n  Case {i+1}: {f['g6']}")
            print(f"    Degrees: v={f['deg_v']}, w={f['deg_w']}")
            print(f"    Ext sizes: v1={f['ext_v1_size']}, v2={f['ext_v2_size']}, w1={f['ext_w1_size']}, w2={f['ext_w2_size']}")
            print(f"    Common: v={f['common_v']}, w={f['common_w']}")
            print(f"    Sym diff: v={f['sym_diff_v']}, w={f['sym_diff_w']}")
            print(f"    Cross (switched): v1w2={f['cross_v1_w2']}, v2w1={f['cross_v2_w1']}")
            print(f"    Cross (same): v1w1={f['cross_v1_w1']}, v2w2={f['cross_v2_w2']}")
            print(f"    Internal: {f['internal']}, v1~v2={f['v1_v2_adj']}, w1~w2={f['w1_w2_adj']}")

    conn.close()


if __name__ == "__main__":
    main()
