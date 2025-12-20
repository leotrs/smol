#!/usr/bin/env python3
"""Find what distinguishes actual switches from potential switches.

Focus on:
- Exact neighborhood structure
- Induced subgraph on the 4 vertices
- Combined conditions on forward+reverse pairs
"""

import sys
from collections import Counter
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
    if len({a, b, c, d}) != 4:
        return False
    if G.has_edge(a, d) or G.has_edge(c, b):
        return False
    return True


def get_induced_subgraph_signature(G, a, b, c, d):
    """Get a signature of the induced subgraph on {a,b,c,d}.

    For edges [a,b] and [c,d] with non-adjacency a≁d, c≁b:
    - a~b and c~d are given (they're our edges)
    - a≁d and c≁b are given (switchable pattern)
    - What about: a~c? b~d? a~c? b~c? etc.
    """
    verts = [a, b, c, d]
    # Count edges in induced subgraph
    edges = []
    for i, u in enumerate(verts):
        for j, v in enumerate(verts):
            if i < j and G.has_edge(u, v):
                edges.append((i, j))
    return tuple(sorted(edges))


def get_external_neighborhood(G, v, exclude_set):
    """Get neighbors of v excluding vertices in exclude_set."""
    return frozenset(n for n in G.neighbors(v) if n not in exclude_set)


def degree_sequence_of_neighbors(G, v, exclude_set):
    """Get sorted degree sequence of v's neighbors (excluding some vertices)."""
    neighbors = [n for n in G.neighbors(v) if n not in exclude_set]
    return tuple(sorted([G.degree(n) for n in neighbors]))


def check_conditions(G, a, b, c, d):
    """Check various structural conditions for vertices a,b,c,d."""
    results = {}
    four = {a, b, c, d}

    # External neighborhoods (excluding the 4 switch vertices)
    ext_N_a = get_external_neighborhood(G, a, four)
    ext_N_b = get_external_neighborhood(G, b, four)
    ext_N_c = get_external_neighborhood(G, c, four)
    ext_N_d = get_external_neighborhood(G, d, four)

    # Condition: external neighborhoods match
    results['ext_N_sources_equal'] = (ext_N_a == ext_N_c)
    results['ext_N_targets_equal'] = (ext_N_b == ext_N_d)
    results['ext_N_both_equal'] = results['ext_N_sources_equal'] and results['ext_N_targets_equal']

    # Condition: external neighborhoods have same SIZE
    results['ext_N_sources_same_size'] = (len(ext_N_a) == len(ext_N_c))
    results['ext_N_targets_same_size'] = (len(ext_N_b) == len(ext_N_d))

    # Condition: degree sequences of external neighbors match
    deg_seq_a = degree_sequence_of_neighbors(G, a, four)
    deg_seq_b = degree_sequence_of_neighbors(G, b, four)
    deg_seq_c = degree_sequence_of_neighbors(G, c, four)
    deg_seq_d = degree_sequence_of_neighbors(G, d, four)
    results['deg_seq_sources_equal'] = (deg_seq_a == deg_seq_c)
    results['deg_seq_targets_equal'] = (deg_seq_b == deg_seq_d)
    results['deg_seq_both_equal'] = results['deg_seq_sources_equal'] and results['deg_seq_targets_equal']

    # Induced subgraph signature
    results['induced_sig'] = get_induced_subgraph_signature(G, a, b, c, d)
    results['induced_edge_count'] = len(results['induced_sig'])

    # Specific adjacencies within the 4 vertices
    results['a_adj_c'] = G.has_edge(a, c)  # sources adjacent
    results['b_adj_d'] = G.has_edge(b, d)  # targets adjacent
    # Note: a~b, c~d are given (our edges), a≁d, c≁b are given (switchable)

    # What about a~d's "parallel" edge c~b? Both should be non-edges for switchable
    # But what about the "cross" edges a~c and b~d?

    # Symmetry: do a,c have same relationship to b,d?
    results['symmetric_cross'] = (G.has_edge(a, c) == G.has_edge(b, d))

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
            valid_switches.append((g6_1, g6_2, n, m, G1, assignments[0]))

    print(f"Found {len(valid_switches)} valid switches")
    print("=" * 70)

    switch_stats = []
    nonswitch_stats = []

    for idx, (g6_1, g6_2, n, m, G1, assignment) in enumerate(valid_switches):
        v1, v2, w1, w2 = assignment

        T_np, directed_edges, edge_to_idx = build_T_numpy(G1)
        num_edges = len(directed_edges)

        # The actual switch involves edges [v1,w1] and [v2,w2]
        # In terms of (a,b,c,d): a=v1, b=w1, c=v2, d=w2
        switch_quads = {(v1, w1, v2, w2), (w1, v1, w2, v2)}

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

                results = check_conditions(G1, a, b, c, d)
                results['is_switch'] = (a, b, c, d) in switch_quads

                if results['is_switch']:
                    switch_stats.append(results)
                else:
                    nonswitch_stats.append(results)

        if (idx + 1) % 20 == 0:
            print(f"[{idx+1}/{len(valid_switches)}] processed", file=sys.stderr)

    print()
    print("=" * 70)
    print("RESULTS")
    print("=" * 70)
    print()
    print(f"Actual switches: {len(switch_stats)}")
    print(f"Potential switches (non-switch): {len(nonswitch_stats)}")
    print()

    conditions = [
        ('ext_N_sources_equal', 'External neighbors EQUAL (sources)'),
        ('ext_N_targets_equal', 'External neighbors EQUAL (targets)'),
        ('ext_N_both_equal', 'External neighbors EQUAL (both)'),
        ('ext_N_sources_same_size', 'External neighbors SAME SIZE (sources)'),
        ('ext_N_targets_same_size', 'External neighbors SAME SIZE (targets)'),
        ('deg_seq_sources_equal', 'Neighbor degree sequence EQUAL (sources)'),
        ('deg_seq_targets_equal', 'Neighbor degree sequence EQUAL (targets)'),
        ('deg_seq_both_equal', 'Neighbor degree sequence EQUAL (both)'),
        ('a_adj_c', 'Sources adjacent (a~c)'),
        ('b_adj_d', 'Targets adjacent (b~d)'),
        ('symmetric_cross', 'Symmetric cross adjacency (a~c iff b~d)'),
    ]

    print(f"{'Condition':<50} {'Switch':>10} {'Non-Sw':>10}")
    print("-" * 72)

    for key, label in conditions:
        sw = sum(1 for s in switch_stats if s.get(key)) / len(switch_stats) * 100 if switch_stats else 0
        nsw = sum(1 for s in nonswitch_stats if s.get(key)) / len(nonswitch_stats) * 100 if nonswitch_stats else 0
        marker = " <--" if abs(sw - nsw) > 30 else ""
        print(f"{label:<50} {sw:>9.1f}% {nsw:>9.1f}%{marker}")

    print()
    print("=" * 70)
    print("Induced subgraph patterns (edges among {a,b,c,d}):")
    print("  Note: (0,1)=a~b, (2,3)=c~d always present; (0,3)=a~d, (1,2)=b~c always absent")
    print("-" * 72)

    switch_sigs = Counter(s['induced_sig'] for s in switch_stats)
    nonswitch_sigs = Counter(s['induced_sig'] for s in nonswitch_stats)

    all_sigs = set(switch_sigs.keys()) | set(nonswitch_sigs.keys())
    print(f"{'Induced edges':<40} {'Switch':>10} {'Non-Sw':>10}")
    print("-" * 72)
    for sig in sorted(all_sigs, key=lambda x: (len(x), x)):
        sw = switch_sigs.get(sig, 0)
        nsw = nonswitch_sigs.get(sig, 0)
        sw_pct = sw / len(switch_stats) * 100 if switch_stats else 0
        nsw_pct = nsw / len(nonswitch_stats) * 100 if nonswitch_stats else 0
        print(f"{str(sig):<40} {sw_pct:>9.1f}% {nsw_pct:>9.1f}%")

    print()
    print("=" * 70)

    conn.close()


if __name__ == "__main__":
    main()
