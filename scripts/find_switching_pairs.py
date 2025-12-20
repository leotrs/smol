#!/usr/bin/env python3
"""Find NBL-cospectral pairs where the T^k row coincidence theorem applies.

Searches through NBL-cospectral pairs to find ones where:
1. Graphs differ by exactly the edge-switch pattern
2. Degree conditions are satisfied
3. T^k rows coincide at some finite k

Usage:
    python scripts/find_switching_pairs.py [--max-k 100] [--limit 1000]
"""

import argparse
import sys
import time
from itertools import permutations

import networkx as nx
import psycopg2
from sympy import Matrix, Rational

sys.path.insert(0, str(__file__).rsplit("/", 2)[0])


def get_pairs(conn, limit=None, min_degree=2):
    """Get NBL-cospectral pairs."""
    cur = conn.cursor()
    query = f"""
        SELECT g1.graph6, g2.graph6, g1.n, g1.m
        FROM cospectral_mates cm
        JOIN graphs g1 ON cm.graph1_id = g1.id
        JOIN graphs g2 ON cm.graph2_id = g2.id
        WHERE cm.matrix_type = 'nbl'
          AND g1.min_degree >= {min_degree}
          AND g2.min_degree >= {min_degree}
        ORDER BY g1.m, g1.n
    """
    if limit:
        query += f" LIMIT {limit}"
    cur.execute(query)
    return cur.fetchall()


def build_T_sympy(G):
    """Build transition matrix T = D^{-1}B with sympy exact rationals."""
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


def rows_equal(M, i, j):
    """Check if rows i and j are exactly equal."""
    return M.row(i) == M.row(j)


def cols_equal(M, i, j):
    """Check if columns i and j are exactly equal."""
    return M.col(i) == M.col(j)


def find_switch_vertices(G1, G2):
    """Find valid (v1, v2, w1, w2) assignments if graphs differ by a switch."""
    E1 = set(G1.edges())
    E2 = set(G2.edges())

    only_in_G1 = E1 - E2
    only_in_G2 = E2 - E1

    # Must be exactly 2 edges different
    if len(only_in_G1) != 2 or len(only_in_G2) != 2:
        return None

    # Get all vertices involved
    verts = set()
    for e in only_in_G1:
        verts.update(e)
    for e in only_in_G2:
        verts.update(e)

    # Must be exactly 4 vertices
    if len(verts) != 4:
        return None

    # Find valid assignments
    valid = []
    for perm in permutations(verts):
        v1, v2, w1, w2 = perm

        # Check G1 pattern: v1~w1, v2~w2, v1≁w2, v2≁w1
        if not (G1.has_edge(v1, w1) and G1.has_edge(v2, w2) and
                not G1.has_edge(v1, w2) and not G1.has_edge(v2, w1)):
            continue

        # Check G2 pattern: v1~w2, v2~w1
        if not (G2.has_edge(v1, w2) and G2.has_edge(v2, w1)):
            continue

        # Check degree conditions
        if G1.degree(v1) != G1.degree(v2):
            continue
        if G1.degree(w1) != G1.degree(w2):
            continue

        valid.append((v1, v2, w1, w2))

    return valid if valid else None


def check_Tk_condition(T, edge_to_idx, v1, v2, w1, w2, max_k):
    """Check if T^k rows or columns coincide at some k <= max_k."""
    m = T.rows

    idx_v1w1 = edge_to_idx[(v1, w1)]
    idx_v2w2 = edge_to_idx[(v2, w2)]
    idx_w1v1 = edge_to_idx[(w1, v1)]
    idx_w2v2 = edge_to_idx[(w2, v2)]

    Tk = Matrix.eye(m)

    for k in range(1, max_k + 1):
        Tk = Tk * T

        # Check rows
        r1 = rows_equal(Tk, idx_v1w1, idx_v2w2)
        r2 = rows_equal(Tk, idx_w1v1, idx_w2v2)

        # Check columns
        c1 = cols_equal(Tk, idx_v1w1, idx_v2w2)
        c2 = cols_equal(Tk, idx_w1v1, idx_w2v2)

        if r1 and r2:
            return ("rows", k)
        if c1 and c2:
            return ("cols", k)

    return None


def main():
    parser = argparse.ArgumentParser(description="Find switching pairs where theorem applies")
    parser.add_argument("--max-k", type=int, default=100, help="Maximum k to check")
    parser.add_argument("--limit", type=int, default=None, help="Limit number of pairs to check")
    parser.add_argument("--min-degree", type=int, default=1, help="Minimum degree filter")
    args = parser.parse_args()

    print("Connecting to database...")
    conn = psycopg2.connect("dbname=smol")

    print(f"Fetching NBL-cospectral pairs (min_degree >= {args.min_degree})...")
    pairs = get_pairs(conn, args.limit, args.min_degree)
    print(f"Found {len(pairs)} pairs to check")
    print(f"Will check T^k for k up to {args.max_k}")
    print("=" * 70)
    print()
    sys.stdout.flush()

    start_time = time.time()
    checked = 0
    is_switch = 0
    theorem_applies = 0

    for i, (g6_1, g6_2, n, m) in enumerate(pairs):
        G1 = nx.from_graph6_bytes(g6_1.encode())
        G2 = nx.from_graph6_bytes(g6_2.encode())

        # Check if it's a valid switch
        valid_assignments = find_switch_vertices(G1, G2)

        checked += 1

        if valid_assignments is None:
            # Not a simple switch (might be double switch or other)
            if checked % 100 == 0:
                elapsed = time.time() - start_time
                rate = checked / elapsed
                print(f"[{checked}/{len(pairs)}] ({elapsed:.0f}s, {rate:.1f}/s) "
                      f"switches={is_switch}, theorem_applies={theorem_applies}")
                sys.stdout.flush()
            continue

        is_switch += 1

        # Build T matrix
        T, directed_edges, edge_to_idx = build_T_sympy(G1)

        # Check each valid assignment
        for v1, v2, w1, w2 in valid_assignments:
            result = check_Tk_condition(T, edge_to_idx, v1, v2, w1, w2, args.max_k)

            if result is not None:
                theorem_applies += 1
                mode, k = result
                elapsed = time.time() - start_time
                print()
                print("!" * 70)
                print(f"FOUND! Theorem applies at k={k} ({mode})")
                print(f"  G1: {g6_1}")
                print(f"  G2: {g6_2}")
                print(f"  n={n}, m={m}")
                print(f"  Switch: v1={v1}, v2={v2}, w1={w1}, w2={w2}")
                print(f"  Time: {elapsed:.1f}s, checked {checked} pairs")
                print("!" * 70)
                print()
                sys.stdout.flush()
                break  # Found for this pair, move to next

        # Progress report
        if checked % 10 == 0:
            elapsed = time.time() - start_time
            rate = checked / elapsed if elapsed > 0 else 0
            print(f"[{checked}/{len(pairs)}] ({elapsed:.0f}s, {rate:.1f}/s) "
                  f"n={n} m={m} switches={is_switch}, theorem_applies={theorem_applies}")
            sys.stdout.flush()

    # Final summary
    elapsed = time.time() - start_time
    print()
    print("=" * 70)
    print("FINAL SUMMARY")
    print("=" * 70)
    print(f"Total pairs checked: {checked}")
    print(f"Valid switches found: {is_switch}")
    print(f"Theorem applies: {theorem_applies}")
    print(f"Total time: {elapsed:.1f}s")
    print("=" * 70)

    conn.close()


if __name__ == "__main__":
    main()
