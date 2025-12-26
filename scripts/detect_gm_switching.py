#!/usr/bin/env python3
"""Detect Godsil-McKay switching in cospectral graph pairs.

GM Switching: Given graph G with vertex partition V = V1 ∪ V2 ∪ V3 where:
- V1, V2 are non-empty disjoint sets with |V1| = |V2|
- G[V1 ∪ V2] forms a complete bipartite graph K_{|V1|,|V2|}
- No edges within V1 or V2

The GM switch creates G' by:
- Removing all edges between V1 and V2
- Adding edges to make V1 and V2 into cliques

G and G' are cospectral (adjacency matrix).

Usage:
    python scripts/detect_gm_switching.py --n 7 --sample 100
    python scripts/detect_gm_switching.py --n 10
"""

import argparse
import sys
from itertools import combinations
from pathlib import Path

import networkx as nx

sys.path.insert(0, str(Path(__file__).parent.parent))

from db.database import connect


def is_gm_switching(G, H):
    """Check if G and H are related by GM switching.

    Returns True if there exists a partition V = V1 ∪ V2 ∪ V3 such that
    applying GM switching to G yields a graph isomorphic to H.
    """
    n = G.number_of_nodes()
    nodes = list(G.nodes())

    # Try all possible sizes for V1 (V2 must have same size)
    for size in range(1, n // 2 + 1):
        # Try all combinations of vertices for V1
        for V1 in combinations(nodes, size):
            V1 = set(V1)

            # Try all combinations for V2 from remaining vertices
            remaining = set(nodes) - V1
            for V2 in combinations(remaining, size):
                V2 = set(V2)

                # Check GM conditions in G:
                # 1. No edges within V1
                if any(G.has_edge(u, v) for u, v in combinations(V1, 2)):
                    continue

                # 2. No edges within V2
                if any(G.has_edge(u, v) for u, v in combinations(V2, 2)):
                    continue

                # 3. Complete bipartite between V1 and V2
                if not all(G.has_edge(u, v) for u in V1 for v in V2):
                    continue

                # Valid GM configuration found - apply switch
                Gp = G.copy()

                # Remove all V1-V2 edges
                for u in V1:
                    for v in V2:
                        Gp.remove_edge(u, v)

                # Add cliques on V1 and V2
                for u, v in combinations(V1, 2):
                    Gp.add_edge(u, v)
                for u, v in combinations(V2, 2):
                    Gp.add_edge(u, v)

                # Check if Gp is isomorphic to H
                if nx.is_isomorphic(Gp, H):
                    return True

    return False


def check_gm_pair(g6_1, g6_2):
    """Check if a pair of graph6 strings are related by GM switching."""
    G = nx.from_graph6_bytes(g6_1.encode())
    H = nx.from_graph6_bytes(g6_2.encode())

    # Check both directions
    return is_gm_switching(G, H) or is_gm_switching(H, G)


def main():
    parser = argparse.ArgumentParser(description="Detect GM switching in cospectral pairs")
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

    # Get adjacency cospectral pairs
    query = """
        SELECT cm.graph1_id, cm.graph2_id, g1.graph6, g2.graph6
        FROM cospectral_mates cm
        JOIN graphs g1 ON cm.graph1_id = g1.id
        JOIN graphs g2 ON cm.graph2_id = g2.id
        WHERE cm.matrix_type = 'adj' AND g1.n = %s
    """

    if args.sample:
        query += f" ORDER BY RANDOM() LIMIT {args.sample}"

    cur.execute(query, (args.n,))
    pairs = cur.fetchall()

    print(f"\nAnalyzing {len(pairs)} adjacency cospectral pairs at n={args.n}")
    print("=" * 70)

    gm_pairs = []
    non_gm_pairs = []

    for i, (id1, id2, g6_1, g6_2) in enumerate(pairs):
        if (i + 1) % 10 == 0:
            print(f"  Progress: {i+1}/{len(pairs)} pairs checked...")

        if check_gm_pair(g6_1, g6_2):
            gm_pairs.append((g6_1, g6_2))
        else:
            non_gm_pairs.append((g6_1, g6_2))

    # Print results
    print("\nResults:")
    print("-" * 70)
    print(f"GM switching:        {len(gm_pairs):6d} ({100*len(gm_pairs)/len(pairs):5.1f}%)")
    print(f"Non-GM:              {len(non_gm_pairs):6d} ({100*len(non_gm_pairs)/len(pairs):5.1f}%)")
    print("=" * 70)

    # Write results
    docs_dir = Path(__file__).parent.parent / "docs"
    docs_dir.mkdir(exist_ok=True)

    if gm_pairs:
        filename = f"adj_n{args.n}_gm_switching.txt"
        with open(docs_dir / filename, "w") as f:
            for g1, g2 in gm_pairs:
                f.write(f"{g1},{g2}\n")
        print(f"\nWrote GM pairs: docs/{filename}")

    if non_gm_pairs and args.sample:
        filename = f"adj_n{args.n}_non_gm_sample.txt"
        with open(docs_dir / filename, "w") as f:
            for g1, g2 in non_gm_pairs:
                f.write(f"{g1},{g2}\n")
        print(f"Wrote non-GM pairs: docs/{filename}")

    conn.close()


if __name__ == "__main__":
    main()
