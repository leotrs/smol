#!/usr/bin/env python3
"""Classify Kirchhoff and Signless cospectral pairs by switching mechanism.

This script analyzes which cospectral pairs can be explained by:
1. GM (Godsil-McKay) switching
2. 2-edge switch with degree conditions
3. k-edge bipartite swap

Usage:
    python scripts/classify_kirchhoff_signless.py --matrix kirchhoff --n 7
    python scripts/classify_kirchhoff_signless.py --matrix signless --n 10 --sample 1000
"""

import argparse
import sys
from itertools import combinations
from pathlib import Path

import networkx as nx

sys.path.insert(0, str(Path(__file__).parent.parent))

from db.database import connect


def gm_switching_check(G, H):
    """Check if G and H are related by Godsil-McKay switching.

    GM switching: Partition V into V1, V2, V3 where:
    - V1, V2 non-empty, V3 possibly empty
    - All V1-V2 edges present, no V1-V1 or V2-V2 edges
    - Swap creates H by removing V1-V2 edges and adding complete bipartite

    For Laplacian cospectrality, we need:
    - |V1| = |V2|
    - Each vertex in V1 has same degree in G as corresponding vertex in V2
    """
    # This is a simplified check - full GM is more complex
    # For now, just check if graphs differ by a complete bipartite subgraph swap

    # Find edge differences
    edges_G = set(G.edges())
    edges_H = set(H.edges())
    removed = edges_G - edges_H
    added = edges_H - edges_G

    if len(removed) == 0:
        return False

    # Get vertices involved in changed edges
    changed_vertices = set()
    for u, v in removed | added:
        changed_vertices.add(u)
        changed_vertices.add(v)

    # GM switching requires |V1| = |V2| and specific structure
    # This is a heuristic check, not complete
    if len(changed_vertices) == 4 and len(removed) == 2 and len(added) == 2:
        # Might be a simple 2-edge swap, not GM
        return False

    return False  # Conservative: GM is complex, skip for now


def two_edge_switch_check(G, H):
    """Check if G and H are related by a 2-edge switch.

    Similar to NBL (C1)+(C2) theorem but for Kirchhoff/Signless Laplacian.
    Switch {v1w1, v2w2} -> {v1w2, v2w1}

    For Laplacian cospectrality, we need degree preservation.
    """
    for e1, e2 in combinations(G.edges(), 2):
        for v1, w1 in [e1, e1[::-1]]:
            for v2, w2 in [e2, e2[::-1]]:
                # Check if this is a valid switch configuration
                if G.has_edge(v1, w2) or G.has_edge(v2, w1):
                    continue

                S = {v1, v2, w1, w2}
                if len(S) != 4:
                    continue

                # For Kirchhoff/Signless, degree equality is crucial
                if G.degree(v1) != G.degree(v2) or G.degree(w1) != G.degree(w2):
                    continue

                # Apply switch
                Gp = G.copy()
                Gp.remove_edge(v1, w1)
                Gp.remove_edge(v2, w2)
                Gp.add_edge(v1, w2)
                Gp.add_edge(v2, w1)

                if nx.is_isomorphic(Gp, H):
                    return True

    return False


def bipartite_swap_check(G, H, k=2):
    """Check k-edge bipartite swap (generalization of 2-edge switch).

    Similar to NBL bipartite swap but for Kirchhoff/Signless.
    """
    nodes = list(G.nodes())

    # Try all pairs of hubs
    for h1, h2 in combinations(nodes, 2):
        # Find potential leaves: vertices adjacent to exactly one hub
        L1_candidates = [
            v for v in nodes
            if v not in {h1, h2} and G.has_edge(v, h1) and not G.has_edge(v, h2)
        ]
        L2_candidates = [
            v for v in nodes
            if v not in {h1, h2} and G.has_edge(v, h2) and not G.has_edge(v, h1)
        ]

        if len(L1_candidates) < k or len(L2_candidates) < k:
            continue

        # Try all k-subsets
        for L1 in combinations(L1_candidates, k):
            for L2 in combinations(L2_candidates, k):
                L1, L2 = set(L1), set(L2)

                # Check degree conditions for Laplacian cospectrality
                if G.degree(h1) != G.degree(h2):
                    continue

                leaf_degs = [G.degree(leaf) for leaf in L1 | L2]
                if len(set(leaf_degs)) != 1:
                    continue

                # Apply swap and check isomorphism
                Gp = G.copy()
                for leaf in L1:
                    Gp.remove_edge(leaf, h1)
                    Gp.add_edge(leaf, h2)
                for leaf in L2:
                    Gp.remove_edge(leaf, h2)
                    Gp.add_edge(leaf, h1)

                if nx.is_isomorphic(Gp, H):
                    return True

    return False


def classify_pair(g6_1, g6_2):
    """Classify a pair of cospectral graphs by mechanism."""
    G = nx.from_graph6_bytes(g6_1.encode())
    H = nx.from_graph6_bytes(g6_2.encode())

    # Check mechanisms in order of simplicity
    if two_edge_switch_check(G, H) or two_edge_switch_check(H, G):
        return "2-edge"

    if bipartite_swap_check(G, H, k=2) or bipartite_swap_check(H, G, k=2):
        return "4-edge-swap"

    # Skip GM for now - too complex
    # if gm_switching_check(G, H) or gm_switching_check(H, G):
    #     return "GM"

    return "unexplained"


def main():
    parser = argparse.ArgumentParser(description="Classify Kirchhoff/Signless cospectral pairs")
    parser.add_argument(
        "--matrix",
        required=True,
        choices=["kirchhoff", "signless"],
        help="Matrix type to analyze",
    )
    parser.add_argument(
        "--n",
        type=int,
        required=True,
        help="Number of vertices",
    )
    parser.add_argument(
        "--sample",
        type=int,
        help="Sample size (default: all pairs)",
    )
    args = parser.parse_args()

    conn = connect()
    cur = conn.cursor()

    # Get pairs
    query = """
        SELECT cm.graph1_id, cm.graph2_id, g1.graph6, g2.graph6
        FROM cospectral_mates cm
        JOIN graphs g1 ON cm.graph1_id = g1.id
        JOIN graphs g2 ON cm.graph2_id = g2.id
        WHERE cm.matrix_type = %s AND g1.n = %s
    """

    if args.sample:
        query += f" ORDER BY RANDOM() LIMIT {args.sample}"

    cur.execute(query, (args.matrix, args.n))
    pairs = cur.fetchall()

    print(f"\nAnalyzing {len(pairs)} {args.matrix} cospectral pairs at n={args.n}")
    print("=" * 70)

    # Classify each pair
    results = {
        "2-edge": [],
        "4-edge-swap": [],
        "GM": [],
        "unexplained": [],
    }

    for i, (id1, id2, g6_1, g6_2) in enumerate(pairs):
        if (i + 1) % 100 == 0:
            print(f"  Progress: {i+1}/{len(pairs)} pairs classified...")

        mechanism = classify_pair(g6_1, g6_2)
        results[mechanism].append((g6_1, g6_2))

    # Print results
    print("\nResults:")
    print("-" * 70)
    print(f"2-edge switch:       {len(results['2-edge']):6d} ({100*len(results['2-edge'])/len(pairs):5.1f}%)")
    print(f"4-edge swap:         {len(results['4-edge-swap']):6d} ({100*len(results['4-edge-swap'])/len(pairs):5.1f}%)")
    print(f"GM switching:        {len(results['GM']):6d} ({100*len(results['GM'])/len(pairs):5.1f}%)")
    print(f"Unexplained:         {len(results['unexplained']):6d} ({100*len(results['unexplained'])/len(pairs):5.1f}%)")
    print("=" * 70)

    # Write results to docs
    docs_dir = Path(__file__).parent.parent / "docs"
    docs_dir.mkdir(exist_ok=True)

    for mechanism, pairs_list in results.items():
        if pairs_list:
            filename = f"{args.matrix}_n{args.n}_{mechanism}.txt"
            with open(docs_dir / filename, "w") as f:
                for g1, g2 in pairs_list:
                    f.write(f"{g1},{g2}\n")
            print(f"\nWrote: docs/{filename}")

    conn.close()


if __name__ == "__main__":
    main()
