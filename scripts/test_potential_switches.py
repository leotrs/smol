#!/usr/bin/env python3
"""For potential switches that aren't cospectral, perform the switch and measure spectrum change."""

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


def is_switchable_pattern(G, v1, v2, w1, w2):
    """Check if edges v1-w1, v2-w2 can be switched."""
    if len({v1, v2, w1, w2}) != 4:
        return False
    if not G.has_edge(v1, w1) or not G.has_edge(v2, w2):
        return False
    if G.has_edge(v1, w2) or G.has_edge(v2, w1):
        return False
    if G.degree(v1) != G.degree(v2):
        return False
    if G.degree(w1) != G.degree(w2):
        return False
    return True


def perform_switch(G, v1, v2, w1, w2):
    """Create new graph with edges switched."""
    G2 = G.copy()
    G2.remove_edge(v1, w1)
    G2.remove_edge(v2, w2)
    G2.add_edge(v1, w2)
    G2.add_edge(v2, w1)
    return G2


def build_NBL(G):
    """Build the non-backtracking Laplacian L = I - D^{-1}B."""
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

    L = np.eye(m) - T
    return L


def spectral_distance(G1, G2):
    """Compute spectral distance between NBL matrices."""
    L1 = build_NBL(G1)
    L2 = build_NBL(G2)

    eig1 = np.sort(np.linalg.eigvals(L1))
    eig2 = np.sort(np.linalg.eigvals(L2))

    # L2 distance between eigenvalue vectors
    return np.linalg.norm(eig1 - eig2)


def find_all_potential_switches(G):
    """Find all potential switch configurations in G."""
    potential = []
    edges = list(G.edges())

    for i, (a, b) in enumerate(edges):
        for j, (c, d) in enumerate(edges):
            if i >= j:
                continue

            # Try all 4 orientations of the two edges
            for v1, w1 in [(a, b), (b, a)]:
                for v2, w2 in [(c, d), (d, c)]:
                    if is_switchable_pattern(G, v1, v2, w1, w2):
                        potential.append((v1, v2, w1, w2))

    return potential


def main():
    print("Connecting to database...")
    conn = psycopg2.connect("dbname=smol")

    print("Fetching NBL-cospectral pairs...")
    pairs = get_pairs(conn)

    # Find valid switches
    valid_switches = []
    for g6_1, g6_2, n, m in pairs:
        G1 = nx.from_graph6_bytes(g6_1.encode())
        G2 = nx.from_graph6_bytes(g6_2.encode())
        assignments = find_switch_vertices(G1, G2)
        if assignments:
            valid_switches.append((g6_1, g6_2, n, m, G1, G2, assignments[0]))

    print(f"Found {len(valid_switches)} NBL-cospectral switch pairs")
    print("=" * 70)

    # For each graph with a valid switch, find ALL potential switches
    # and compute spectrum change for each

    actual_switch_dists = []
    potential_switch_dists = []

    for idx, (g6_1, g6_2, n, m, G1, G2, assignment) in enumerate(valid_switches):
        v1, v2, w1, w2 = assignment

        # The actual switch - should have distance ~0
        dist_actual = spectral_distance(G1, G2)
        actual_switch_dists.append(dist_actual)

        # Find all other potential switches in G1
        all_potential = find_all_potential_switches(G1)

        for pv1, pv2, pw1, pw2 in all_potential:
            # Skip if this is the actual switch
            if {pv1, pv2, pw1, pw2} == {v1, v2, w1, w2}:
                continue

            # Perform the switch
            G_switched = perform_switch(G1, pv1, pv2, pw1, pw2)
            dist = spectral_distance(G1, G_switched)
            potential_switch_dists.append(dist)

        if (idx + 1) % 20 == 0:
            print(f"[{idx+1}/{len(valid_switches)}] processed", file=sys.stderr)

    print()
    print("=" * 70)
    print("SPECTRAL DISTANCE AFTER SWITCH")
    print("=" * 70)
    print()

    print(f"Actual cospectral switches: {len(actual_switch_dists)}")
    print(f"  Mean distance: {np.mean(actual_switch_dists):.6f}")
    print(f"  Max distance:  {np.max(actual_switch_dists):.6f}")
    print(f"  All < 1e-10:   {sum(1 for d in actual_switch_dists if d < 1e-10)}/{len(actual_switch_dists)}")

    print()
    print(f"Potential (non-cospectral) switches: {len(potential_switch_dists)}")
    print(f"  Mean distance: {np.mean(potential_switch_dists):.6f}")
    print(f"  Min distance:  {np.min(potential_switch_dists):.6f}")
    print(f"  Max distance:  {np.max(potential_switch_dists):.6f}")

    # Distribution
    print()
    print("Distribution of spectral distances for potential switches:")
    thresholds = [1e-10, 1e-6, 1e-3, 0.01, 0.1, 0.5, 1.0]
    for t in thresholds:
        count = sum(1 for d in potential_switch_dists if d < t)
        print(f"  < {t}: {count}/{len(potential_switch_dists)} ({100*count/len(potential_switch_dists):.1f}%)")

    print()
    print("=" * 70)

    # Are there any potential switches with very small spectral distance?
    near_cospectral = [(d, i) for i, d in enumerate(potential_switch_dists) if d < 0.01]
    if near_cospectral:
        print(f"Found {len(near_cospectral)} potential switches with dist < 0.01")

    conn.close()


if __name__ == "__main__":
    main()
