#!/usr/bin/env python3
"""Compare G1 and G2 together - look at what the switch preserves.

The switch changes {v1-w1, v2-w2} to {v1-w2, v2-w1}.
Look at both Hashimoto graphs and what's invariant.
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


def build_hashimoto_graph(G):
    """Build the Hashimoto graph."""
    H = nx.DiGraph()
    directed_edges = []
    for u, v in G.edges():
        directed_edges.append((u, v))
        directed_edges.append((v, u))
    H.add_nodes_from(directed_edges)
    for (u, v) in directed_edges:
        for w in G.neighbors(v):
            if w != u:
                H.add_edge((u, v), (v, w))
    return H, directed_edges


def get_hashimoto_edge_set(H):
    """Get the set of edges in H as frozenset for comparison."""
    return frozenset(H.edges())


def compare_hashimoto_graphs(H1, H2, v1, v2, w1, w2):
    """Compare the two Hashimoto graphs."""
    results = {}

    # Edges only in H1 vs only in H2
    E1 = set(H1.edges())
    E2 = set(H2.edges())

    only_in_H1 = E1 - E2
    only_in_H2 = E2 - E1
    common = E1 & E2

    results['edges_only_H1'] = len(only_in_H1)
    results['edges_only_H2'] = len(only_in_H2)
    results['edges_common'] = len(common)
    results['edges_total_H1'] = len(E1)
    results['edges_total_H2'] = len(E2)

    # Which edges changed?
    # The switch removes (v1,w1), (w1,v1), (v2,w2), (w2,v2)
    # and adds (v1,w2), (w2,v1), (v2,w1), (w1,v2)
    removed_nodes = {(v1, w1), (w1, v1), (v2, w2), (w2, v2)}

    # Edges in H that involve removed nodes
    edges_involving_removed = set()
    for e in E1:
        if e[0] in removed_nodes or e[1] in removed_nodes:
            edges_involving_removed.add(e)

    results['edges_involving_removed_nodes'] = len(edges_involving_removed)

    # Check if only_in_H1 are exactly the edges involving removed nodes
    results['H1_diff_is_removed'] = (only_in_H1 == edges_involving_removed)

    return results, only_in_H1, only_in_H2


def build_T_matrix(G):
    """Build the transition matrix T = D^{-1}B."""
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
    return T, directed_edges, edge_to_idx


def analyze_T_relationship(G1, G2, v1, v2, w1, w2):
    """Analyze how T1 and T2 relate."""
    T1, edges1, idx1 = build_T_matrix(G1)
    T2, edges2, idx2 = build_T_matrix(G2)

    results = {}

    # The matrices have different indexing because nodes changed
    # We need to find a correspondence

    # Nodes that exist in both: all except the switched ones
    common_nodes_G1 = [e for e in edges1 if e not in {(v1, w1), (w1, v1), (v2, w2), (w2, v2)}]
    common_nodes_G2 = [e for e in edges2 if e not in {(v1, w2), (w2, v1), (v2, w1), (w1, v2)}]

    # These should be the same set
    results['common_nodes_match'] = (set(common_nodes_G1) == set(common_nodes_G2))
    results['num_common_nodes'] = len(common_nodes_G1)

    # Extract submatrices for common nodes
    common_idx1 = [idx1[e] for e in common_nodes_G1]
    common_idx2 = [idx2[e] for e in common_nodes_G1]  # same nodes, different matrix

    T1_sub = T1[np.ix_(common_idx1, common_idx1)]
    T2_sub = T2[np.ix_(common_idx2, common_idx2)]

    # Are the submatrices equal?
    results['submatrix_equal'] = np.allclose(T1_sub, T2_sub)
    results['submatrix_diff_norm'] = np.linalg.norm(T1_sub - T2_sub)

    # Eigenvalues of full matrices
    eig1 = np.sort(np.linalg.eigvals(T1))
    eig2 = np.sort(np.linalg.eigvals(T2))
    results['eigenvalues_close'] = np.allclose(eig1, eig2)

    return results


def analyze_switch_structure(G1, G2, v1, v2, w1, w2):
    """Analyze the structural relationship between the switch edges."""
    results = {}

    # In G1: edges are v1-w1 and v2-w2
    # In G2: edges are v1-w2 and v2-w1

    # The 4 vertices form a specific pattern
    # Look at their neighborhoods OUTSIDE the 4 vertices
    four = {v1, v2, w1, w2}

    ext_N_v1 = frozenset(n for n in G1.neighbors(v1) if n not in four)
    ext_N_v2 = frozenset(n for n in G1.neighbors(v2) if n not in four)
    ext_N_w1 = frozenset(n for n in G1.neighbors(w1) if n not in four)
    ext_N_w2 = frozenset(n for n in G1.neighbors(w2) if n not in four)

    results['ext_N_v1'] = ext_N_v1
    results['ext_N_v2'] = ext_N_v2
    results['ext_N_w1'] = ext_N_w1
    results['ext_N_w2'] = ext_N_w2

    # Key question: is there a "swap" symmetry?
    # If we swap v1<->v2 and w1<->w2, do external neighborhoods swap?
    results['v_swap_symmetric'] = (ext_N_v1 == ext_N_v2)
    results['w_swap_symmetric'] = (ext_N_w1 == ext_N_w2)
    results['both_swap_symmetric'] = results['v_swap_symmetric'] and results['w_swap_symmetric']

    # What about: N(v1) union N(v2) vs N(w1) union N(w2)?
    results['v_union'] = ext_N_v1 | ext_N_v2
    results['w_union'] = ext_N_w1 | ext_N_w2

    # Intersection
    results['v_intersection'] = ext_N_v1 & ext_N_v2
    results['w_intersection'] = ext_N_w1 & ext_N_w2

    # Key insight: maybe the UNION of neighborhoods is preserved?
    # In G1: edges touch v1,w1 and v2,w2
    # In G2: edges touch v1,w2 and v2,w1
    # The set of external neighbors reachable from each edge might swap

    # Edge v1-w1 in G1 can reach ext_N_v1 | ext_N_w1
    # Edge v2-w2 in G1 can reach ext_N_v2 | ext_N_w2
    # Edge v1-w2 in G2 can reach ext_N_v1 | ext_N_w2
    # Edge v2-w1 in G2 can reach ext_N_v2 | ext_N_w1

    reach_e1_G1 = ext_N_v1 | ext_N_w1
    reach_e2_G1 = ext_N_v2 | ext_N_w2
    reach_e1_G2 = ext_N_v1 | ext_N_w2  # v1-w2 in G2
    reach_e2_G2 = ext_N_v2 | ext_N_w1  # v2-w1 in G2

    results['reach_e1_G1'] = reach_e1_G1
    results['reach_e2_G1'] = reach_e2_G1
    results['reach_e1_G2'] = reach_e1_G2
    results['reach_e2_G2'] = reach_e2_G2

    # Does the multiset of reachable sets stay the same?
    results['reach_multiset_preserved'] = (
        {frozenset(reach_e1_G1), frozenset(reach_e2_G1)} ==
        {frozenset(reach_e1_G2), frozenset(reach_e2_G2)}
    )

    # Stronger: reach_e1_G1 = reach_e1_G2 and reach_e2_G1 = reach_e2_G2?
    results['reach_exact_preserved'] = (
        reach_e1_G1 == reach_e1_G2 and reach_e2_G1 == reach_e2_G2
    )

    # Or swapped: reach_e1_G1 = reach_e2_G2 and reach_e2_G1 = reach_e1_G2?
    results['reach_swapped'] = (
        reach_e1_G1 == reach_e2_G2 and reach_e2_G1 == reach_e1_G2
    )

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
    print("Comparing G1 and G2...")
    print("=" * 70)

    all_stats = []

    for idx, (g6_1, g6_2, n, m, G1, G2, assignment) in enumerate(valid_switches):
        v1, v2, w1, w2 = assignment

        # Compare Hashimoto graphs
        H1, _ = build_hashimoto_graph(G1)
        H2, _ = build_hashimoto_graph(G2)
        h_results, _, _ = compare_hashimoto_graphs(H1, H2, v1, v2, w1, w2)

        # Analyze T matrices
        t_results = analyze_T_relationship(G1, G2, v1, v2, w1, w2)

        # Analyze switch structure
        s_results = analyze_switch_structure(G1, G2, v1, v2, w1, w2)

        results = {**h_results, **t_results, **s_results}
        results['g6_1'] = g6_1
        results['g6_2'] = g6_2
        all_stats.append(results)

        if (idx + 1) % 20 == 0:
            print(f"[{idx+1}/{len(valid_switches)}] processed", file=sys.stderr)

    print()
    print("=" * 70)
    print("COMPARISON OF G1 AND G2")
    print("=" * 70)
    print()

    conditions = [
        ('common_nodes_match', 'Common directed edges match'),
        ('submatrix_equal', 'T submatrix (common edges) equal'),
        ('eigenvalues_close', 'T eigenvalues equal (NBL cospectral)'),
        ('v_swap_symmetric', 'N(v1) = N(v2) externally'),
        ('w_swap_symmetric', 'N(w1) = N(w2) externally'),
        ('both_swap_symmetric', 'BOTH v and w swap-symmetric'),
        ('reach_multiset_preserved', 'Edge reach multiset preserved'),
        ('reach_exact_preserved', 'Edge reach exactly preserved'),
        ('reach_swapped', 'Edge reach swapped'),
    ]

    print(f"{'Condition':<45} {'% True':>10}")
    print("-" * 60)

    for key, label in conditions:
        pct = sum(1 for s in all_stats if s.get(key)) / len(all_stats) * 100
        marker = " <-- !" if pct == 100 else (" <--" if pct > 90 else "")
        print(f"{label:<45} {pct:>9.1f}%{marker}")

    print()
    print("=" * 70)
    print("Detailed reach analysis:")
    print("-" * 60)

    # Count different reach patterns
    exact = sum(1 for s in all_stats if s['reach_exact_preserved'])
    swapped = sum(1 for s in all_stats if s['reach_swapped'])
    multiset = sum(1 for s in all_stats if s['reach_multiset_preserved'])
    neither = sum(1 for s in all_stats if not s['reach_multiset_preserved'])

    print(f"  Reach exactly preserved: {exact}/{len(all_stats)} ({100*exact/len(all_stats):.1f}%)")
    print(f"  Reach swapped: {swapped}/{len(all_stats)} ({100*swapped/len(all_stats):.1f}%)")
    print(f"  Reach multiset preserved: {multiset}/{len(all_stats)} ({100*multiset/len(all_stats):.1f}%)")
    print(f"  Neither: {neither}/{len(all_stats)} ({100*neither/len(all_stats):.1f}%)")

    print()
    print("=" * 70)

    # Show some examples where reach is swapped
    if swapped > 0:
        print("Examples where reach is SWAPPED:")
        print("-" * 60)
        for s in all_stats[:5]:
            if s['reach_swapped']:
                print(f"  {s['g6_1']} <-> {s['g6_2']}")
                print(f"    reach_e1_G1 = {s['reach_e1_G1']}")
                print(f"    reach_e2_G1 = {s['reach_e2_G1']}")
                print(f"    reach_e1_G2 = {s['reach_e1_G2']}")
                print(f"    reach_e2_G2 = {s['reach_e2_G2']}")
                print()

    conn.close()


if __name__ == "__main__":
    main()
