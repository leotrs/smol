#!/usr/bin/env python3
"""Analyze the rank-4 perturbation that preserves NBL spectrum.

T1 and T2 differ only in 4 rows/columns (the switch edges).
What structure does this perturbation have?
"""

import sys
from itertools import permutations

import networkx as nx
import numpy as np
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
        if d > 0:
            for w in G.neighbors(v):
                if w != u:
                    T[i, edge_to_idx[(v, w)]] = 1.0 / d
    return T, directed_edges, edge_to_idx


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
        if d > 0:
            for w in G.neighbors(v):
                if w != u:
                    T[i, edge_to_idx[(v, w)]] = Rational(1, d)
    return T, directed_edges, edge_to_idx


def analyze_perturbation(G1, G2, v1, v2, w1, w2):
    """Analyze the perturbation T2 - T1."""
    T1, edges1, idx1 = build_T_numpy(G1)
    T2, edges2, idx2 = build_T_numpy(G2)

    # Build correspondence between indices
    # Edges in G1: includes (v1,w1), (w1,v1), (v2,w2), (w2,v2)
    # Edges in G2: includes (v1,w2), (w2,v1), (v2,w1), (w1,v2)

    # Common edges (same in both)
    [e for e in edges1 if e in idx2]

    # For comparison, we need to align the matrices
    # Let's work with a unified edge set

    all_edges = list(set(edges1) | set(edges2))
    all_edges.sort()
    unified_idx = {e: i for i, e in enumerate(all_edges)}
    m = len(all_edges)

    # Build unified T1 and T2
    T1_unified = np.zeros((m, m))
    T2_unified = np.zeros((m, m))

    for e in edges1:
        i = unified_idx[e]
        for e2 in edges1:
            j = unified_idx[e2]
            T1_unified[i, j] = T1[idx1[e], idx1[e2]]

    for e in edges2:
        i = unified_idx[e]
        for e2 in edges2:
            j = unified_idx[e2]
            T2_unified[i, j] = T2[idx2[e], idx2[e2]]

    # Compute perturbation
    Delta = T2_unified - T1_unified

    results = {}
    results['Delta_rank'] = np.linalg.matrix_rank(Delta, tol=1e-10)
    results['Delta_norm'] = np.linalg.norm(Delta)
    results['Delta_nonzero'] = np.sum(np.abs(Delta) > 1e-10)

    # Which rows/cols are nonzero in Delta?
    nonzero_rows = np.where(np.any(np.abs(Delta) > 1e-10, axis=1))[0]
    nonzero_cols = np.where(np.any(np.abs(Delta) > 1e-10, axis=0))[0]

    results['nonzero_rows'] = len(nonzero_rows)
    results['nonzero_cols'] = len(nonzero_cols)

    # Identify which edges these correspond to
    nonzero_row_edges = [all_edges[i] for i in nonzero_rows]
    nonzero_col_edges = [all_edges[i] for i in nonzero_cols]

    switch_edges_G1 = {(v1, w1), (w1, v1), (v2, w2), (w2, v2)}
    switch_edges_G2 = {(v1, w2), (w2, v1), (v2, w1), (w1, v2)}
    all_switch_edges = switch_edges_G1 | switch_edges_G2

    results['row_edges_are_switch'] = all(e in all_switch_edges for e in nonzero_row_edges)
    results['col_edges_are_switch'] = all(e in all_switch_edges for e in nonzero_col_edges)

    # Extract the 8x8 submatrix corresponding to switch edges
    switch_edge_list = sorted(all_switch_edges)
    switch_idx = [unified_idx[e] for e in switch_edge_list]

    Delta_switch = Delta[np.ix_(switch_idx, switch_idx)]
    results['Delta_switch_rank'] = np.linalg.matrix_rank(Delta_switch, tol=1e-10)

    # Check structure of Delta
    # Is Delta = UV^T for low-rank factorization?
    U, S, Vt = np.linalg.svd(Delta)
    nonzero_sing = np.sum(S > 1e-10)
    results['Delta_svd_rank'] = nonzero_sing

    return results, Delta, all_edges, unified_idx


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
    print("Analyzing perturbations...")
    print("=" * 70)

    all_stats = []

    for idx, (g6_1, g6_2, n, m, G1, G2, assignment) in enumerate(valid_switches):
        v1, v2, w1, w2 = assignment

        results, Delta, all_edges, unified_idx = analyze_perturbation(G1, G2, v1, v2, w1, w2)
        results['g6_1'] = g6_1
        results['g6_2'] = g6_2
        all_stats.append(results)

        if (idx + 1) % 20 == 0:
            print(f"[{idx+1}/{len(valid_switches)}] processed", file=sys.stderr)

    print()
    print("=" * 70)
    print("PERTURBATION ANALYSIS: Delta = T2 - T1")
    print("=" * 70)
    print()

    # Rank distribution
    print("Rank of Delta:")
    rank_counts = {}
    for s in all_stats:
        r = s['Delta_rank']
        rank_counts[r] = rank_counts.get(r, 0) + 1
    for r in sorted(rank_counts.keys()):
        print(f"  Rank {r}: {rank_counts[r]} ({100*rank_counts[r]/len(all_stats):.1f}%)")

    print()
    print("Nonzero rows/cols in Delta:")
    for key in ['nonzero_rows', 'nonzero_cols']:
        counts = {}
        for s in all_stats:
            v = s[key]
            counts[v] = counts.get(v, 0) + 1
        print(f"  {key}:")
        for v in sorted(counts.keys()):
            print(f"    {v}: {counts[v]} ({100*counts[v]/len(all_stats):.1f}%)")

    print()
    print("Are nonzero rows/cols exactly the switch edges?")
    rows_switch = sum(1 for s in all_stats if s['row_edges_are_switch'])
    cols_switch = sum(1 for s in all_stats if s['col_edges_are_switch'])
    print(f"  Rows are switch edges: {rows_switch}/{len(all_stats)} ({100*rows_switch/len(all_stats):.1f}%)")
    print(f"  Cols are switch edges: {cols_switch}/{len(all_stats)} ({100*cols_switch/len(all_stats):.1f}%)")

    print()
    print("=" * 70)

    # Show one example in detail
    print("DETAILED EXAMPLE:")
    print("-" * 70)

    ex = all_stats[0]
    g6_1, g6_2 = ex['g6_1'], ex['g6_2']
    G1 = nx.from_graph6_bytes(g6_1.encode())
    G2 = nx.from_graph6_bytes(g6_2.encode())
    assignment = find_switch_vertices(G1, G2)[0]
    v1, v2, w1, w2 = assignment

    print(f"G1: {g6_1}")
    print(f"G2: {g6_2}")
    print(f"Switch vertices: v1={v1}, v2={v2}, w1={w1}, w2={w2}")
    print(f"G1 edges: {v1}-{w1}, {v2}-{w2}")
    print(f"G2 edges: {v1}-{w2}, {v2}-{w1}")
    print()

    _, Delta, all_edges, unified_idx = analyze_perturbation(G1, G2, v1, v2, w1, w2)

    switch_edges_G1 = [(v1, w1), (w1, v1), (v2, w2), (w2, v2)]
    switch_edges_G2 = [(v1, w2), (w2, v1), (v2, w1), (w1, v2)]

    print("Switch edges in G1:", switch_edges_G1)
    print("Switch edges in G2:", switch_edges_G2)
    print()

    # Show the Delta matrix restricted to switch edges
    all_switch = sorted(set(switch_edges_G1) | set(switch_edges_G2))
    switch_idx = [unified_idx[e] for e in all_switch]

    print("Delta restricted to switch edges:")
    print("Edges:", all_switch)
    Delta_sub = Delta[np.ix_(switch_idx, switch_idx)]
    print(np.round(Delta_sub, 3))

    print()
    print("=" * 70)

    conn.close()


if __name__ == "__main__":
    main()
