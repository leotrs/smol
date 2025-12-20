#!/usr/bin/env python3
"""Test alternative conditions on valid switch pairs.

Conditions tested:
1. Rows proportional (scalar multiple)
2. Same row sums at T^k (note: trivially true for stochastic matrices)
3. Rows equal up to permutation
9. Same diagonal entries (T^k)_{ii}
11. Local automorphism swapping v1↔v2, w1↔w2
"""

import sys
from itertools import permutations

import networkx as nx
import psycopg2
from sympy import Matrix, Rational

sys.path.insert(0, str(__file__).rsplit("/", 2)[0])


def get_pairs(conn, limit=None):
    """Get NBL-cospectral pairs."""
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


def find_switch_vertices(G1, G2):
    """Find valid (v1, v2, w1, w2) assignments if graphs differ by a switch."""
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


def rows_proportional(M, i, j):
    """Check if rows i and j are proportional (scalar multiple)."""
    row_i = M.row(i)
    row_j = M.row(j)

    # Find first non-zero entry to get ratio
    ratio = None
    for k in range(M.cols):
        if row_i[k] != 0 and row_j[k] != 0:
            ratio = row_i[k] / row_j[k]
            break
        elif row_i[k] != 0 or row_j[k] != 0:
            # One is zero, other isn't - not proportional
            return False, None

    if ratio is None:
        # Both rows are zero
        return True, 0

    # Check all entries have same ratio
    for k in range(M.cols):
        if row_j[k] == 0:
            if row_i[k] != 0:
                return False, None
        else:
            if row_i[k] / row_j[k] != ratio:
                return False, None

    return True, ratio


def rows_permutation_equal(M, i, j):
    """Check if rows i and j are equal up to permutation."""
    row_i = sorted(M.row(i))
    row_j = sorted(M.row(j))
    return row_i == row_j


def same_diagonal(M, i, j):
    """Check if diagonal entries M[i,i] and M[j,j] are equal."""
    return M[i, i] == M[j, j]


def has_local_automorphism(G, v1, v2, w1, w2):
    """Check if there's an automorphism swapping v1↔v2 and w1↔w2."""
    try:

        # Check if swapping v1↔v2 and w1↔w2 gives an automorphism
        # This means: for all other vertices u, the adjacencies are preserved

        # Build the permutation
        perm = {v1: v2, v2: v1, w1: w2, w2: w1}
        for v in G.nodes():
            if v not in perm:
                perm[v] = v

        # Check if this permutation is an automorphism
        for u in G.nodes():
            for v in G.neighbors(u):
                # u~v in G should imply perm[u]~perm[v] in G
                if not G.has_edge(perm[u], perm[v]):
                    return False
        return True
    except Exception:
        return False


def test_conditions(T, edge_to_idx, v1, v2, w1, w2, G, max_k=20):
    """Test all conditions for various k values."""
    m = T.rows

    idx_v1w1 = edge_to_idx[(v1, w1)]
    idx_v2w2 = edge_to_idx[(v2, w2)]
    idx_w1v1 = edge_to_idx[(w1, v1)]
    idx_w2v2 = edge_to_idx[(w2, v2)]

    results = {
        'proportional': [],      # (k, ratio) where rows are proportional
        'perm_equal': [],        # k where rows equal up to permutation
        'same_diag': [],         # k where diagonal entries match
    }

    # Test local automorphism (doesn't depend on k)
    results['local_auto'] = has_local_automorphism(G, v1, v2, w1, w2)

    Tk = Matrix.eye(m)

    for k in range(1, max_k + 1):
        Tk = Tk * T

        # Condition 1: Rows proportional
        prop1, ratio1 = rows_proportional(Tk, idx_v1w1, idx_v2w2)
        prop2, ratio2 = rows_proportional(Tk, idx_w1v1, idx_w2v2)
        if prop1 and prop2:
            results['proportional'].append((k, ratio1, ratio2))

        # Condition 3: Rows equal up to permutation
        perm1 = rows_permutation_equal(Tk, idx_v1w1, idx_v2w2)
        perm2 = rows_permutation_equal(Tk, idx_w1v1, idx_w2v2)
        if perm1 and perm2:
            results['perm_equal'].append(k)

        # Condition 9: Same diagonal entries
        diag1 = same_diagonal(Tk, idx_v1w1, idx_v2w2)
        diag2 = same_diagonal(Tk, idx_w1v1, idx_w2v2)
        if diag1 and diag2:
            results['same_diag'].append(k)

    return results


def main():
    print("Connecting to database...")
    conn = psycopg2.connect("dbname=smol")

    print("Fetching NBL-cospectral pairs...")
    pairs = get_pairs(conn)
    print(f"Found {len(pairs)} pairs")
    print("=" * 70)

    # Collect all valid switches first
    valid_switches = []
    for g6_1, g6_2, n, m in pairs:
        G1 = nx.from_graph6_bytes(g6_1.encode())
        G2 = nx.from_graph6_bytes(g6_2.encode())
        assignments = find_switch_vertices(G1, G2)
        if assignments:
            valid_switches.append((g6_1, g6_2, n, m, G1, assignments[0]))

    print(f"Found {len(valid_switches)} valid single-edge switches")
    print("Testing conditions on each...")
    print("=" * 70)
    print()

    # Track which conditions are satisfied
    condition_counts = {
        'proportional': 0,
        'perm_equal': 0,
        'same_diag': 0,
        'local_auto': 0,
    }

    for i, (g6_1, g6_2, n, m, G1, assignment) in enumerate(valid_switches):
        v1, v2, w1, w2 = assignment

        T, directed_edges, edge_to_idx = build_T_sympy(G1)
        results = test_conditions(T, edge_to_idx, v1, v2, w1, w2, G1, max_k=50)

        # Check if any condition was satisfied
        any_satisfied = False

        if results['proportional']:
            condition_counts['proportional'] += 1
            any_satisfied = True

        if results['perm_equal']:
            condition_counts['perm_equal'] += 1
            any_satisfied = True

        if results['same_diag']:
            condition_counts['same_diag'] += 1
            any_satisfied = True

        if results['local_auto']:
            condition_counts['local_auto'] += 1
            any_satisfied = True

        # Print details if something interesting found
        if any_satisfied:
            print(f"Switch {i+1}: {g6_1} ↔ {g6_2} (n={n}, m={m})")
            print(f"  Vertices: v1={v1}, v2={v2}, w1={w1}, w2={w2}")
            if results['local_auto']:
                print("  ✓ Local automorphism exists!")
            if results['proportional']:
                ks = [k for k, r1, r2 in results['proportional'][:5]]
                print(f"  ✓ Proportional rows at k={ks}...")
            if results['perm_equal']:
                print(f"  ✓ Permutation-equal rows at k={results['perm_equal'][:5]}...")
            if results['same_diag']:
                print(f"  ✓ Same diagonal at k={results['same_diag'][:5]}...")
            print()

        if (i + 1) % 10 == 0:
            print(f"[{i+1}/{len(valid_switches)}] processed", file=sys.stderr)

    print()
    print("=" * 70)
    print("SUMMARY")
    print("=" * 70)
    print(f"Total valid switches: {len(valid_switches)}")
    print()
    print("Conditions satisfied:")
    print(f"  1. Rows proportional:        {condition_counts['proportional']}/{len(valid_switches)}")
    print(f"  3. Rows permutation-equal:   {condition_counts['perm_equal']}/{len(valid_switches)}")
    print(f"  9. Same diagonal (T^k)_ii:   {condition_counts['same_diag']}/{len(valid_switches)}")
    print(f" 11. Local automorphism:       {condition_counts['local_auto']}/{len(valid_switches)}")
    print("=" * 70)

    # Note about condition 2
    print()
    print("Note: Condition 2 (same row sums) is trivially satisfied for all k")
    print("since T is row-stochastic, so T^k is also row-stochastic.")

    conn.close()


if __name__ == "__main__":
    main()
