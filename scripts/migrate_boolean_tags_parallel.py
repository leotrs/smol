#!/usr/bin/env python3
"""Migrate bipartite/planar/regular from boolean columns to tags array.

Uses parallel workers for speed. Each worker updates a chunk independently.

Usage:
    python scripts/migrate_boolean_tags_parallel.py [--workers 8] [--chunk-size 50000]
"""

import argparse
import os
from multiprocessing import Pool, cpu_count
import psycopg2

DATABASE_URL = os.environ.get("DATABASE_URL", "dbname=smol")


def update_chunk(args):
    """Worker function: update one chunk of IDs."""
    tag_name, chunk_ids, chunk_num, total_chunks = args

    conn = psycopg2.connect(DATABASE_URL)
    cur = conn.cursor()

    # Simple UPDATE by ID - no complex WHERE clause
    cur.execute(f"""
        UPDATE graphs
        SET tags = array_append(COALESCE(tags, '{{}}'), %s)
        WHERE id = ANY(%s)
    """, (tag_name, chunk_ids))

    updated = cur.rowcount
    conn.commit()
    conn.close()

    return (chunk_num, updated)


def migrate_tag_parallel(tag_name, boolean_column, workers, chunk_size):
    """Migrate one boolean column to tag using parallel workers."""
    conn = psycopg2.connect(DATABASE_URL)
    cur = conn.cursor()

    # Get all IDs that need updating
    cur.execute(f"""
        SELECT id
        FROM graphs
        WHERE {boolean_column} = true
          AND (tags IS NULL OR '{tag_name}' != ALL(tags))
        ORDER BY id
    """)

    ids = [row[0] for row in cur.fetchall()]
    conn.close()

    if not ids:
        print(f"  All {tag_name} tags already migrated")
        return

    total = len(ids)
    print(f"  Migrating {total:,} {tag_name} tags with {workers} workers...")

    # Split IDs into chunks
    chunks = []
    for i in range(0, len(ids), chunk_size):
        chunk = ids[i:i + chunk_size]
        chunk_num = len(chunks) + 1
        total_chunks = (len(ids) + chunk_size - 1) // chunk_size
        chunks.append((tag_name, chunk, chunk_num, total_chunks))

    # Process chunks in parallel
    with Pool(workers) as pool:
        for chunk_num, updated in pool.imap_unordered(update_chunk, chunks):
            print(f"    Chunk {chunk_num}/{len(chunks)}: updated {updated:,}")

    print(f"  ✓ Updated {total:,} {tag_name} tags")


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--workers", type=int, default=min(8, cpu_count()), help="Number of parallel workers")
    parser.add_argument("--chunk-size", type=int, default=50000, help="Rows per chunk")
    args = parser.parse_args()

    print(f"Migrating boolean columns to tags ({args.workers} workers)...")

    # Migrate each tag
    migrate_tag_parallel("bipartite", "is_bipartite", args.workers, args.chunk_size)
    migrate_tag_parallel("planar", "is_planar", args.workers, args.chunk_size)
    migrate_tag_parallel("regular", "is_regular", args.workers, args.chunk_size)

    # Ensure tags column is never NULL
    print("\nConverting NULL tags to empty arrays...")
    conn = psycopg2.connect(DATABASE_URL)
    cur = conn.cursor()
    cur.execute("UPDATE graphs SET tags = '{}' WHERE tags IS NULL")
    null_count = cur.rowcount
    conn.commit()
    conn.close()
    print(f"  Updated {null_count:,} graphs")

    print("\n✓ Migration complete!")


if __name__ == "__main__":
    main()
