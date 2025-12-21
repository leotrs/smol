#!/usr/bin/env python3
"""Compute tags for all graphs in the database.

Only processes graphs where tags IS NULL (not yet computed).
After computation, tags will be either:
- Empty array '{}' if no tags apply
- Array of strings if tags were found

Usage:
    python scripts/compute_tags.py [--batch-size 1000]
    python scripts/compute_tags.py --recompute  # Recompute all tags
"""

import argparse
import os
import sys

import networkx as nx
import psycopg2

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from db.tags import compute_tags

DATABASE_URL = os.environ.get("DATABASE_URL", "dbname=smol")


def main():
    parser = argparse.ArgumentParser(description="Compute tags for graphs")
    parser.add_argument("--batch-size", type=int, default=1000, help="Batch size for updates")
    parser.add_argument("--recompute", action="store_true", help="Recompute all tags, not just empty ones")
    args = parser.parse_args()

    conn = psycopg2.connect(DATABASE_URL)
    cur = conn.cursor()

    # Count graphs needing tags
    if args.recompute:
        cur.execute("SELECT COUNT(*) FROM graphs")
    else:
        cur.execute("SELECT COUNT(*) FROM graphs WHERE tags IS NULL")
    total = cur.fetchone()[0]
    action = "Recomputing" if args.recompute else "Computing"
    print(f"{action} tags for {total:,} graphs...")

    # Fetch graphs in batches
    if args.recompute:
        cur.execute("SELECT id, graph6 FROM graphs ORDER BY id")
    else:
        cur.execute(
            """
            SELECT id, graph6
            FROM graphs
            WHERE tags IS NULL
            ORDER BY id
            """
        )

    updates = []
    count = 0

    for graph_id, graph6 in cur:
        G = nx.from_graph6_bytes(graph6.encode())
        tags = compute_tags(G)

        updates.append((tags, graph_id))

        if len(updates) >= args.batch_size:
            update_batch(conn, updates)
            count += len(updates)
            print(f"  {count:,}/{total:,} ({100*count/total:.1f}%)")
            updates = []

    if updates:
        update_batch(conn, updates)
        count += len(updates)

    print(f"Updated {count:,} graphs")
    conn.close()


def update_batch(conn, updates):
    """Update tags for a batch of graphs."""
    cur = conn.cursor()
    for tags, graph_id in updates:
        cur.execute(
            "UPDATE graphs SET tags = %s WHERE id = %s",
            (tags, graph_id),
        )
    conn.commit()


if __name__ == "__main__":
    main()
