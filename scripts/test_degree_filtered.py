#!/usr/bin/env python3
"""Check conditions only on edge pairs satisfying degree conditions.

For directed edges [a,b] and [c,d], require:
- deg(a) = deg(c)  (source vertices have same degree)
- deg(b) = deg(d)  (target vertices have same degree)
"""

import sys
from itertools import permutations

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


def rows_equal(M, i, j):
    return M.row(i) == M.row(j)


def check_degree_filtered_pairs(G, T, edge_to_idx, directed_edges, switch_edges_set, max_k=5):
    """Check conditions only for edge pairs satisfying degree conditions."""
    m = T.rows

    # Precompute T^k
    Tk_list = [None, T]  # Tk_list[k] = T^k
    Tk = T
    for k in range(2, max_k + 1):
        Tk = Tk * T
        Tk_list.append(Tk)

    results = {
        'switch': {'total': 0, 'perm_k1': 0, 'diag_k1': 0, 'diag_k2': 0, 'exact_any': 0},
        'nonswitch': {'total': 0, 'perm_k1': 0, 'diag_k1': 0, 'diag_k2': 0, 'exact_any': 0},
    }

    # Check all pairs of directed edges that satisfy degree conditions
    for i in range(m):
        for j in range(i + 1, m):
            e_i = directed_edges[i]  # (a, b)
            e_j = directed_edges[j]  # (c, d)

            # Degree condition: deg(a) = deg(c) and deg(b) = deg(d)
            if G.degree(e_i[0]) != G.degree(e_j[0]):
                continue
            if G.degree(e_i[1]) != G.degree(e_j[1]):
                continue

            is_switch = (i in switch_edges_set and j in switch_edges_set)
            key = 'switch' if is_switch else 'nonswitch'

            results[key]['total'] += 1

            if rows_permutation_equal(Tk_list[1], i, j):
                results[key]['perm_k1'] += 1

            if same_diagonal(Tk_list[1], i, j):
                results[key]['diag_k1'] += 1

            if same_diagonal(Tk_list[2], i, j):
                results[key]['diag_k2'] += 1

            # Check exact row equality for any k
            for k in range(1, max_k + 1):
                if rows_equal(Tk_list[k], i, j):
                    results[key]['exact_any'] += 1
                    break

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
    print("Checking only edge pairs that satisfy degree conditions...")
    print("=" * 70)
    print()

    # Aggregate stats
    totals = {
        'switch': {'total': 0, 'perm_k1': 0, 'diag_k1': 0, 'diag_k2': 0, 'exact_any': 0},
        'nonswitch': {'total': 0, 'perm_k1': 0, 'diag_k1': 0, 'diag_k2': 0, 'exact_any': 0},
    }

    for i, (g6_1, g6_2, n, m, G1, assignment) in enumerate(valid_switches):
        v1, v2, w1, w2 = assignment

        T, directed_edges, edge_to_idx = build_T_sympy(G1)

        switch_edges_set = {
            edge_to_idx[(v1, w1)],
            edge_to_idx[(v2, w2)],
            edge_to_idx[(w1, v1)],
            edge_to_idx[(w2, v2)],
        }

        results = check_degree_filtered_pairs(G1, T, edge_to_idx, directed_edges, switch_edges_set)

        for key in ['switch', 'nonswitch']:
            for metric in totals[key]:
                totals[key][metric] += results[key][metric]

        if (i + 1) % 20 == 0:
            print(f"[{i+1}/{len(valid_switches)}] processed", file=sys.stderr)

    print()
    print("=" * 70)
    print("RESULTS: Only edge pairs satisfying degree conditions")
    print("         deg(source1) = deg(source2) AND deg(target1) = deg(target2)")
    print("=" * 70)
    print()

    for key, label in [('switch', 'SWITCH EDGE PAIRS'), ('nonswitch', 'NON-SWITCH EDGE PAIRS')]:
        t = totals[key]
        print(f"{label}:")
        print(f"  Total pairs (with degree match): {t['total']}")
        if t['total'] > 0:
            print(f"  Permutation-equal rows at k=1: {t['perm_k1']} ({100*t['perm_k1']/t['total']:.1f}%)")
            print(f"  Same diagonal at k=1: {t['diag_k1']} ({100*t['diag_k1']/t['total']:.1f}%)")
            print(f"  Same diagonal at k=2: {t['diag_k2']} ({100*t['diag_k2']/t['total']:.1f}%)")
            print(f"  Exact row equality (any k≤5): {t['exact_any']} ({100*t['exact_any']/t['total']:.1f}%)")
        print()

    print("=" * 70)

    conn.close()


if __name__ == "__main__":
    main()
