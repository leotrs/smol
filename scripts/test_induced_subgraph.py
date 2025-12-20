#!/usr/bin/env python3
"""Look for conditions on the 4-vertex induced subgraph that distinguish switches.

Focus on:
- Complete characterization of induced subgraph
- How the 4 vertices connect externally (as a unit)
- Symmetry/structural conditions on the local cluster
"""

import sys
from collections import Counter
from itertools import combinations, permutations

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


def get_external_neighbors(G, vertices):
    """Get all neighbors of the vertex set that are outside the set."""
    four = set(vertices)
    external = set()
    for v in vertices:
        for n in G.neighbors(v):
            if n not in four:
                external.add(n)
    return external


def get_boundary_signature(G, a, b, c, d):
    """Get signature of how each of the 4 vertices connects externally.

    Returns tuple of (external_degree_a, external_degree_b, external_degree_c, external_degree_d)
    sorted in a canonical way.
    """
    four = {a, b, c, d}
    ext_deg = {}
    for v in [a, b, c, d]:
        ext_deg[v] = len([n for n in G.neighbors(v) if n not in four])
    return (ext_deg[a], ext_deg[b], ext_deg[c], ext_deg[d])


def get_external_connection_pattern(G, a, b, c, d):
    """For each external neighbor, which of {a,b,c,d} is it connected to?"""
    external = get_external_neighbors(G, [a, b, c, d])

    patterns = []
    for ext in external:
        connected_to = tuple(sorted([v for v in [a, b, c, d] if G.has_edge(ext, v)]))
        patterns.append(connected_to)

    return Counter(patterns)


def check_conditions(G, a, b, c, d):
    """Check structural conditions on the 4-vertex subgraph."""
    results = {}
    four = {a, b, c, d}

    # External degrees for each vertex
    ext_deg_a = len([n for n in G.neighbors(a) if n not in four])
    ext_deg_b = len([n for n in G.neighbors(b) if n not in four])
    ext_deg_c = len([n for n in G.neighbors(c) if n not in four])
    ext_deg_d = len([n for n in G.neighbors(d) if n not in four])

    # Condition: sources have same external degree
    results['ext_deg_sources_equal'] = (ext_deg_a == ext_deg_c)
    # Condition: targets have same external degree
    results['ext_deg_targets_equal'] = (ext_deg_b == ext_deg_d)
    # Both
    results['ext_deg_both_equal'] = results['ext_deg_sources_equal'] and results['ext_deg_targets_equal']

    # Condition: "parallel" vertices have same external degree
    # In the switch v1~w1, v2~w2: parallel means (v1,v2) and (w1,w2)
    # Here a=v1, b=w1, c=v2, d=w2
    # So parallel: (a,c) are sources, (b,d) are targets - same as above

    # External connection pattern
    ext_pattern = get_external_connection_pattern(G, a, b, c, d)
    results['ext_pattern'] = ext_pattern
    results['num_external'] = sum(ext_pattern.values())

    # Check if external neighbors connect symmetrically
    # Symmetric means: for each external neighbor, it connects to {a,b} iff another connects to {c,d}
    # Or: the multiset of connection patterns is "balanced"

    # Count how many externals connect to just one vertex
    single_connections = sum(v for k, v in ext_pattern.items() if len(k) == 1)
    results['single_connection_externals'] = single_connections

    # Count how many externals connect to a source (a or c)
    sum(v for k, v in ext_pattern.items() if a in k or c in k)
    sum(v for k, v in ext_pattern.items() if b in k or d in k)

    # External neighbors of a that aren't neighbors of c (and vice versa)
    ext_N_a = set(n for n in G.neighbors(a) if n not in four)
    ext_N_b = set(n for n in G.neighbors(b) if n not in four)
    ext_N_c = set(n for n in G.neighbors(c) if n not in four)
    ext_N_d = set(n for n in G.neighbors(d) if n not in four)

    # Symmetric difference - neighbors exclusive to a vs exclusive to c
    results['ext_N_a_only'] = len(ext_N_a - ext_N_c)
    results['ext_N_c_only'] = len(ext_N_c - ext_N_a)
    results['ext_N_b_only'] = len(ext_N_b - ext_N_d)
    results['ext_N_d_only'] = len(ext_N_d - ext_N_b)

    # Key condition: symmetric external structure
    # |N(a) \ N(c)| = |N(c) \ N(a)| for sources
    results['symmetric_source_diff'] = (len(ext_N_a - ext_N_c) == len(ext_N_c - ext_N_a))
    results['symmetric_target_diff'] = (len(ext_N_b - ext_N_d) == len(ext_N_d - ext_N_b))
    results['symmetric_both_diff'] = results['symmetric_source_diff'] and results['symmetric_target_diff']

    # Cross-connections within the 4 vertices
    results['a_adj_c'] = G.has_edge(a, c)
    results['b_adj_d'] = G.has_edge(b, d)
    results['both_cross'] = results['a_adj_c'] and results['b_adj_d']
    results['neither_cross'] = not results['a_adj_c'] and not results['b_adj_d']
    results['one_cross'] = (results['a_adj_c'] != results['b_adj_d'])

    # Total internal edges (among the 4 vertices)
    internal_edges = 0
    for u, v in combinations([a, b, c, d], 2):
        if G.has_edge(u, v):
            internal_edges += 1
    results['internal_edges'] = internal_edges

    # Does the subgraph form a 4-cycle? (a-b-d-c-a)
    # That requires: a~b, b~d, d~c, c~a (the switch edges + both cross edges)
    # But a≁d and b≁c (switchable pattern)
    results['forms_4cycle'] = (results['a_adj_c'] and results['b_adj_d'])

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
    print("=" * 70)

    switch_stats = []
    nonswitch_stats = []

    for idx, (g6_1, g6_2, n, m, G1, G2, assignment) in enumerate(valid_switches):
        v1, v2, w1, w2 = assignment

        # For actual switch: a=v1, b=w1, c=v2, d=w2
        results = check_conditions(G1, v1, w1, v2, w2)
        results['is_switch'] = True
        switch_stats.append(results)

        # Check non-switch pairs
        for u, v in G1.edges():
            for x, y in G1.edges():
                if (u, v) >= (x, y):
                    continue
                a, b, c, d = u, v, x, y

                # Skip if this IS the switch
                if {a, b, c, d} == {v1, v2, w1, w2}:
                    continue

                # Degree conditions
                if G1.degree(a) != G1.degree(c):
                    continue
                if G1.degree(b) != G1.degree(d):
                    continue

                # Switchable pattern
                if not is_switchable_pattern(G1, a, b, c, d):
                    continue

                results = check_conditions(G1, a, b, c, d)
                results['is_switch'] = False
                nonswitch_stats.append(results)

        if (idx + 1) % 20 == 0:
            print(f"[{idx+1}/{len(valid_switches)}] processed", file=sys.stderr)

    print()
    print("=" * 70)
    print("RESULTS")
    print("=" * 70)
    print()
    print(f"Actual switches: {len(switch_stats)}")
    print(f"Potential switches: {len(nonswitch_stats)}")
    print()

    conditions = [
        ('ext_deg_sources_equal', 'External degree equal (sources a,c)'),
        ('ext_deg_targets_equal', 'External degree equal (targets b,d)'),
        ('ext_deg_both_equal', 'External degree equal (BOTH)'),
        ('symmetric_source_diff', '|N(a)\\N(c)| = |N(c)\\N(a)|'),
        ('symmetric_target_diff', '|N(b)\\N(d)| = |N(d)\\N(b)|'),
        ('symmetric_both_diff', 'Symmetric diff (BOTH)'),
        ('a_adj_c', 'Sources adjacent (a~c)'),
        ('b_adj_d', 'Targets adjacent (b~d)'),
        ('both_cross', 'BOTH cross edges (4-cycle)'),
        ('neither_cross', 'NEITHER cross edge'),
        ('one_cross', 'Exactly ONE cross edge'),
    ]

    print(f"{'Condition':<45} {'Switch':>10} {'Non-Sw':>10} {'Diff':>8}")
    print("-" * 75)

    for key, label in conditions:
        sw = sum(1 for s in switch_stats if s.get(key)) / len(switch_stats) * 100 if switch_stats else 0
        nsw = sum(1 for s in nonswitch_stats if s.get(key)) / len(nonswitch_stats) * 100 if nonswitch_stats else 0
        diff = sw - nsw
        marker = " <--" if abs(diff) > 30 else ""
        print(f"{label:<45} {sw:>9.1f}% {nsw:>9.1f}% {diff:>+7.1f}{marker}")

    print()
    print("=" * 70)
    print("Internal edge counts:")
    print("-" * 75)

    for num_edges in range(2, 7):
        sw = sum(1 for s in switch_stats if s.get('internal_edges') == num_edges)
        nsw = sum(1 for s in nonswitch_stats if s.get('internal_edges') == num_edges)
        sw_pct = sw / len(switch_stats) * 100 if switch_stats else 0
        nsw_pct = nsw / len(nonswitch_stats) * 100 if nonswitch_stats else 0
        print(f"  {num_edges} internal edges: Switch={sw_pct:5.1f}%, Non-switch={nsw_pct:5.1f}%")

    print()
    print("=" * 70)
    print("Looking for conditions with large separation...")
    print("-" * 75)

    # Try combinations of conditions
    combos = [
        ('ext_deg_both_equal', 'symmetric_both_diff'),
        ('ext_deg_both_equal', 'both_cross'),
        ('symmetric_both_diff', 'both_cross'),
        ('ext_deg_both_equal', 'symmetric_both_diff', 'both_cross'),
    ]

    for combo in combos:
        sw_match = sum(1 for s in switch_stats if all(s.get(c) for c in combo))
        nsw_match = sum(1 for s in nonswitch_stats if all(s.get(c) for c in combo))
        sw_pct = sw_match / len(switch_stats) * 100 if switch_stats else 0
        nsw_pct = nsw_match / len(nonswitch_stats) * 100 if nonswitch_stats else 0
        print(f"  {' AND '.join(combo)}")
        print(f"    Switch: {sw_pct:.1f}%, Non-switch: {nsw_pct:.1f}%")
        print()

    conn.close()


if __name__ == "__main__":
    main()
