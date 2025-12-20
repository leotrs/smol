#!/usr/bin/env python3
"""Look at exactly which edges are affected by the perturbation."""

import sys
from itertools import permutations

import networkx as nx
import numpy as np
import psycopg2

sys.path.insert(0, str(__file__).rsplit("/", 2)[0])


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


def analyze_one_switch(G1, G2, v1, v2, w1, w2):
    """Detailed analysis of one switch."""
    T1, edges1, idx1 = build_T_numpy(G1)
    T2, edges2, idx2 = build_T_numpy(G2)

    # Build unified edge set
    all_edges = list(set(edges1) | set(edges2))
    all_edges.sort()
    unified_idx = {e: i for i, e in enumerate(all_edges)}
    m = len(all_edges)

    # Build unified T matrices
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

    Delta = T2_unified - T1_unified

    # Identify nonzero entries
    nonzero = np.abs(Delta) > 1e-10
    nonzero_positions = list(zip(*np.where(nonzero)))

    # Categorize edges
    four = {v1, v2, w1, w2}
    switch_edges_G1 = {(v1, w1), (w1, v1), (v2, w2), (w2, v2)}
    switch_edges_G2 = {(v1, w2), (w2, v1), (v2, w1), (w1, v2)}
    switch_edges_G1 | switch_edges_G2

    def categorize_edge(e):
        """Categorize an edge based on its relationship to switch vertices."""
        if e in switch_edges_G1:
            return "switch_G1"
        if e in switch_edges_G2:
            return "switch_G2"
        if e[0] in four and e[1] in four:
            return "internal_non_switch"
        if e[0] in four or e[1] in four:
            return "boundary"
        return "external"

    # Analyze each nonzero entry
    entry_categories = []
    for i, j in nonzero_positions:
        e_row = all_edges[i]
        e_col = all_edges[j]
        cat_row = categorize_edge(e_row)
        cat_col = categorize_edge(e_col)
        entry_categories.append((cat_row, cat_col, e_row, e_col, Delta[i, j]))

    return {
        'entry_categories': entry_categories,
        'all_edges': all_edges,
        'unified_idx': unified_idx,
        'Delta': Delta,
        'four': four,
    }


def main():
    print("Loading first switch example...")

    conn = psycopg2.connect("dbname=smol")
    conn.cursor()
    # Use known switch from earlier analysis
    g6_1 = "H?`@Eah"
    g6_2 = "H?`@Cr`"
    G1 = nx.from_graph6_bytes(g6_1.encode())
    G2 = nx.from_graph6_bytes(g6_2.encode())
    n = G1.number_of_nodes()
    m = G1.number_of_edges()

    assignments = find_switch_vertices(G1, G2)
    if not assignments:
        print("No valid switch found!")
        return

    v1, v2, w1, w2 = assignments[0]

    print(f"G1: {g6_1}")
    print(f"G2: {g6_2}")
    print(f"n={n}, m={m}")
    print(f"Switch: v1={v1}, v2={v2}, w1={w1}, w2={w2}")
    print(f"Degrees: deg(v1)={G1.degree(v1)}, deg(v2)={G1.degree(v2)}, deg(w1)={G1.degree(w1)}, deg(w2)={G1.degree(w2)}")
    print()

    results = analyze_one_switch(G1, G2, v1, v2, w1, w2)

    print("=" * 70)
    print("NONZERO ENTRIES IN DELTA = T2 - T1")
    print("=" * 70)
    print()

    # Group by category
    from collections import defaultdict
    by_category = defaultdict(list)
    for cat_row, cat_col, e_row, e_col, val in results['entry_categories']:
        key = (cat_row, cat_col)
        by_category[key].append((e_row, e_col, val))

    print(f"{'Row Category':<20} {'Col Category':<20} {'Count':>8}")
    print("-" * 52)
    for (cat_row, cat_col), entries in sorted(by_category.items()):
        print(f"{cat_row:<20} {cat_col:<20} {len(entries):>8}")

    print()
    print("=" * 70)
    print("DETAILED ENTRIES BY CATEGORY")
    print("=" * 70)

    for (cat_row, cat_col), entries in sorted(by_category.items()):
        print(f"\n{cat_row} -> {cat_col} ({len(entries)} entries):")
        for e_row, e_col, val in entries[:10]:  # Show first 10
            print(f"  {e_row} -> {e_col}: {val:+.4f}")
        if len(entries) > 10:
            print(f"  ... and {len(entries) - 10} more")

    print()
    print("=" * 70)
    print("INTERPRETATION")
    print("=" * 70)
    print()

    four = results['four']
    print(f"The 4 switch vertices: {four}")
    print()
    print("Edge categories:")
    print("  switch_G1: edges that exist in G1 but not G2 (v1-w1, v2-w2)")
    print("  switch_G2: edges that exist in G2 but not G1 (v1-w2, v2-w1)")
    print("  boundary: edges with exactly one endpoint in {v1,v2,w1,w2}")
    print("  external: edges with no endpoint in {v1,v2,w1,w2}")
    print()

    # Check which boundary edges are affected
    boundary_rows = set()
    boundary_cols = set()
    for cat_row, cat_col, e_row, e_col, val in results['entry_categories']:
        if cat_row == 'boundary':
            boundary_rows.add(e_row)
        if cat_col == 'boundary':
            boundary_cols.add(e_col)

    print(f"Boundary edges with nonzero rows in Delta: {len(boundary_rows)}")
    for e in sorted(boundary_rows):
        print(f"  {e}")

    print(f"\nBoundary edges with nonzero cols in Delta: {len(boundary_cols)}")
    for e in sorted(boundary_cols):
        print(f"  {e}")

    conn.close()


if __name__ == "__main__":
    main()
