#!/usr/bin/env python3
"""Analyze switch edges in the Hashimoto graph (directed line graph, no backtracking).

The Hashimoto graph H(G) has:
- Nodes: directed edges (u,v) of G
- Edges: (u,v) -> (v,w) if w ≠ u (no backtracking)

This is the graph on which T operates.
"""

import sys
from itertools import permutations

import networkx as nx
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


def is_switchable_pattern(G, a, b, c, d):
    if len({a, b, c, d}) != 4:
        return False
    if G.has_edge(a, d) or G.has_edge(c, b):
        return False
    return True


def build_hashimoto_graph(G):
    """Build the Hashimoto graph (directed line graph, no backtracking)."""
    H = nx.DiGraph()

    # Nodes are directed edges of G
    directed_edges = []
    for u, v in G.edges():
        directed_edges.append((u, v))
        directed_edges.append((v, u))

    H.add_nodes_from(directed_edges)

    # Edge from (u,v) to (v,w) if w != u
    for (u, v) in directed_edges:
        for w in G.neighbors(v):
            if w != u:
                H.add_edge((u, v), (v, w))

    return H, directed_edges


def get_hashimoto_neighborhood(H, node, depth=1):
    """Get the neighborhood of a node in H up to given depth."""
    if depth == 1:
        return set(H.successors(node)), set(H.predecessors(node))
    else:
        # BFS for deeper neighborhoods
        out_neighbors = set()
        in_neighbors = set()
        frontier = {node}
        for _ in range(depth):
            new_frontier = set()
            for n in frontier:
                for s in H.successors(n):
                    out_neighbors.add(s)
                    new_frontier.add(s)
            frontier = new_frontier

        frontier = {node}
        for _ in range(depth):
            new_frontier = set()
            for n in frontier:
                for p in H.predecessors(n):
                    in_neighbors.add(p)
                    new_frontier.add(p)
            frontier = new_frontier

        return out_neighbors, in_neighbors


def check_hashimoto_conditions(G, H, a, b, c, d):
    """Check conditions on the Hashimoto graph for edge pair [a,b] vs [c,d]."""
    results = {}

    e1 = (a, b)  # directed edge
    e2 = (c, d)  # directed edge
    e1_rev = (b, a)
    e2_rev = (d, c)

    # Out-degree and in-degree in H
    results['H_out_deg_e1'] = H.out_degree(e1)
    results['H_out_deg_e2'] = H.out_degree(e2)
    results['H_in_deg_e1'] = H.in_degree(e1)
    results['H_in_deg_e2'] = H.in_degree(e2)

    results['H_out_deg_equal'] = (H.out_degree(e1) == H.out_degree(e2))
    results['H_in_deg_equal'] = (H.in_degree(e1) == H.in_degree(e2))

    # Successors and predecessors
    succ_e1 = set(H.successors(e1))
    succ_e2 = set(H.successors(e2))
    pred_e1 = set(H.predecessors(e1))
    pred_e2 = set(H.predecessors(e2))

    # Do they have common successors/predecessors?
    results['common_successors'] = len(succ_e1 & succ_e2)
    results['common_predecessors'] = len(pred_e1 & pred_e2)

    # Is there a path from e1 to e2 or vice versa?
    try:
        results['dist_e1_to_e2'] = nx.shortest_path_length(H, e1, e2)
    except nx.NetworkXNoPath:
        results['dist_e1_to_e2'] = -1

    try:
        results['dist_e2_to_e1'] = nx.shortest_path_length(H, e2, e1)
    except nx.NetworkXNoPath:
        results['dist_e2_to_e1'] = -1

    # Are e1 and e2 in each other's neighborhoods?
    results['e2_in_succ_e1'] = e2 in succ_e1
    results['e1_in_succ_e2'] = e1 in succ_e2
    results['e2_in_pred_e1'] = e2 in pred_e1
    results['e1_in_pred_e2'] = e1 in pred_e2

    # Successor/predecessor signature (sorted degrees of successors)
    succ_out_degs_e1 = tuple(sorted([H.out_degree(s) for s in succ_e1]))
    succ_out_degs_e2 = tuple(sorted([H.out_degree(s) for s in succ_e2]))
    results['succ_deg_seq_equal'] = (succ_out_degs_e1 == succ_out_degs_e2)

    pred_in_degs_e1 = tuple(sorted([H.in_degree(p) for p in pred_e1]))
    pred_in_degs_e2 = tuple(sorted([H.in_degree(p) for p in pred_e2]))
    results['pred_deg_seq_equal'] = (pred_in_degs_e1 == pred_in_degs_e2)

    # Check reverse edges too
    set(H.successors(e1_rev))
    set(H.successors(e2_rev))
    set(H.predecessors(e1_rev))
    set(H.predecessors(e2_rev))

    results['H_out_deg_rev_equal'] = (H.out_degree(e1_rev) == H.out_degree(e2_rev))
    results['H_in_deg_rev_equal'] = (H.in_degree(e1_rev) == H.in_degree(e2_rev))

    # Combined: both forward and reverse have equal degrees
    results['H_all_deg_equal'] = (
        results['H_out_deg_equal'] and results['H_in_deg_equal'] and
        results['H_out_deg_rev_equal'] and results['H_in_deg_rev_equal']
    )

    # Symmetric successor structure
    # succ(e1) and succ(e2) should be "isomorphic" in some sense
    # One way: same multiset of (out_degree, in_degree) pairs
    succ_sig_e1 = tuple(sorted([(H.out_degree(s), H.in_degree(s)) for s in succ_e1]))
    succ_sig_e2 = tuple(sorted([(H.out_degree(s), H.in_degree(s)) for s in succ_e2]))
    results['succ_structure_equal'] = (succ_sig_e1 == succ_sig_e2)

    pred_sig_e1 = tuple(sorted([(H.out_degree(p), H.in_degree(p)) for p in pred_e1]))
    pred_sig_e2 = tuple(sorted([(H.out_degree(p), H.in_degree(p)) for p in pred_e2]))
    results['pred_structure_equal'] = (pred_sig_e1 == pred_sig_e2)

    # Do successors overlap with the 4 switch edges?
    switch_edges = {e1, e2, e1_rev, e2_rev}
    results['succ_e1_has_switch'] = len(succ_e1 & switch_edges) > 0
    results['succ_e2_has_switch'] = len(succ_e2 & switch_edges) > 0
    results['pred_e1_has_switch'] = len(pred_e1 & switch_edges) > 0
    results['pred_e2_has_switch'] = len(pred_e2 & switch_edges) > 0

    # Mutual reachability in 2 steps
    succ2_e1 = set()
    for s in succ_e1:
        succ2_e1.update(H.successors(s))
    succ2_e2 = set()
    for s in succ_e2:
        succ2_e2.update(H.successors(s))

    results['e2_in_succ2_e1'] = e2 in succ2_e1
    results['e1_in_succ2_e2'] = e1 in succ2_e2
    results['mutual_reach_2'] = results['e2_in_succ2_e1'] and results['e1_in_succ2_e2']

    return results


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

    print(f"Found {len(valid_switches)} valid switches")
    print("Building Hashimoto graphs and checking conditions...")
    print("=" * 70)

    switch_stats = []
    nonswitch_stats = []

    for idx, (g6_1, g6_2, n, m, G1, G2, assignment) in enumerate(valid_switches):
        v1, v2, w1, w2 = assignment

        H, directed_edges = build_hashimoto_graph(G1)

        # Actual switch: edges [v1,w1] and [v2,w2]
        results = check_hashimoto_conditions(G1, H, v1, w1, v2, w2)
        results['is_switch'] = True
        switch_stats.append(results)

        # Check non-switch pairs
        for (a, b) in directed_edges:
            for (c, d) in directed_edges:
                if (a, b) >= (c, d):
                    continue

                # Skip if this IS the switch
                if {a, b, c, d} == {v1, v2, w1, w2}:
                    continue

                # Degree conditions (on original graph)
                if G1.degree(a) != G1.degree(c):
                    continue
                if G1.degree(b) != G1.degree(d):
                    continue

                # Switchable pattern
                if not is_switchable_pattern(G1, a, b, c, d):
                    continue

                results = check_hashimoto_conditions(G1, H, a, b, c, d)
                results['is_switch'] = False
                nonswitch_stats.append(results)

        if (idx + 1) % 20 == 0:
            print(f"[{idx+1}/{len(valid_switches)}] processed", file=sys.stderr)

    print()
    print("=" * 70)
    print("HASHIMOTO GRAPH CONDITIONS")
    print("=" * 70)
    print()
    print(f"Actual switches: {len(switch_stats)}")
    print(f"Potential switches: {len(nonswitch_stats)}")
    print()

    conditions = [
        ('H_out_deg_equal', 'H: out-degree equal'),
        ('H_in_deg_equal', 'H: in-degree equal'),
        ('H_out_deg_rev_equal', 'H: out-degree equal (reverse)'),
        ('H_in_deg_rev_equal', 'H: in-degree equal (reverse)'),
        ('H_all_deg_equal', 'H: ALL degrees equal (fwd+rev)'),
        ('succ_deg_seq_equal', 'H: successor degree seq equal'),
        ('pred_deg_seq_equal', 'H: predecessor degree seq equal'),
        ('succ_structure_equal', 'H: successor structure equal'),
        ('pred_structure_equal', 'H: predecessor structure equal'),
        ('e2_in_succ_e1', 'H: e2 is successor of e1'),
        ('e1_in_succ_e2', 'H: e1 is successor of e2'),
        ('mutual_reach_2', 'H: mutually reachable in 2 steps'),
        ('succ_e1_has_switch', 'H: succ(e1) contains switch edge'),
        ('succ_e2_has_switch', 'H: succ(e2) contains switch edge'),
    ]

    print(f"{'Condition':<45} {'Switch':>10} {'Non-Sw':>10} {'Diff':>8}")
    print("-" * 75)

    for key, label in conditions:
        sw = sum(1 for s in switch_stats if s.get(key)) / len(switch_stats) * 100 if switch_stats else 0
        nsw = sum(1 for s in nonswitch_stats if s.get(key)) / len(nonswitch_stats) * 100 if nonswitch_stats else 0
        diff = sw - nsw
        marker = " <--" if abs(diff) > 20 else ""
        print(f"{label:<45} {sw:>9.1f}% {nsw:>9.1f}% {diff:>+7.1f}{marker}")

    print()
    print("=" * 70)
    print("Distance between e1 and e2 in H:")
    print("-" * 75)

    for dist in range(-1, 6):
        sw = sum(1 for s in switch_stats if s.get('dist_e1_to_e2') == dist)
        nsw = sum(1 for s in nonswitch_stats if s.get('dist_e1_to_e2') == dist)
        sw_pct = sw / len(switch_stats) * 100 if switch_stats else 0
        nsw_pct = nsw / len(nonswitch_stats) * 100 if nonswitch_stats else 0
        label = "no path" if dist == -1 else f"dist={dist}"
        print(f"  {label}: Switch={sw_pct:5.1f}%, Non-switch={nsw_pct:5.1f}%")

    print()
    print("=" * 70)
    print("Common successors/predecessors:")
    print("-" * 75)

    for num in range(6):
        sw = sum(1 for s in switch_stats if s.get('common_successors') == num)
        nsw = sum(1 for s in nonswitch_stats if s.get('common_successors') == num)
        sw_pct = sw / len(switch_stats) * 100 if switch_stats else 0
        nsw_pct = nsw / len(nonswitch_stats) * 100 if nonswitch_stats else 0
        print(f"  {num} common successors: Switch={sw_pct:5.1f}%, Non-switch={nsw_pct:5.1f}%")

    conn.close()


if __name__ == "__main__":
    main()
