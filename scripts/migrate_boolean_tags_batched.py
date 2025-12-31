#!/usr/bin/env python3
"""Migrate bipartite/planar/regular from boolean columns to tags array.

Uses batched updates for speed. Processes in chunks with progress reporting.

Usage:
    python scripts/migrate_boolean_tags_batched.py [--batch-size 50000]
"""

import argparse
import os
import psycopg2

DATABASE_URL = os.environ.get("DATABASE_URL", "dbname=smol")


def migrate_tag(conn, tag_name, boolean_column, batch_size):
    """Migrate one boolean column to tag in batches."""
    cur = conn.cursor()

    # Count how many need updating
    cur.execute(f"""
        SELECT COUNT(*)
        FROM graphs
        WHERE {boolean_column} = true
          AND (tags IS NULL OR '{tag_name}' != ALL(tags))
    """)
    total = cur.fetchone()[0]

    if total == 0:
        print(f"  All {tag_name} tags already migrated")
        return

    print(f"  Migrating {total:,} {tag_name} tags...")

    # Get IDs to update
    cur.execute(f"""
        SELECT id
        FROM graphs
        WHERE {boolean_column} = true
          AND (tags IS NULL OR '{tag_name}' != ALL(tags))
        ORDER BY id
    """)

    ids = [row[0] for row in cur.fetchall()]
    updated = 0

    # Process in batches
    for i in range(0, len(ids), batch_size):
        batch_ids = ids[i:i + batch_size]

        cur.execute(f"""
            UPDATE graphs
            SET tags = array_append(COALESCE(tags, '{{}}'), '{tag_name}')
            WHERE id = ANY(%s)
        """, (batch_ids,))

        conn.commit()
        updated += len(batch_ids)

        pct = 100 * updated / total
        print(f"    {updated:,}/{total:,} ({pct:.1f}%)")

    print(f"  ✓ Updated {updated:,} {tag_name} tags")


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--batch-size", type=int, default=50000, help="Batch size")
    args = parser.parse_args()

    conn = psycopg2.connect(DATABASE_URL)

    print("Migrating boolean columns to tags (batched)...")

    # Migrate each tag
    migrate_tag(conn, "bipartite", "is_bipartite", args.batch_size)
    migrate_tag(conn, "planar", "is_planar", args.batch_size)
    migrate_tag(conn, "regular", "is_regular", args.batch_size)

    # Ensure tags column is never NULL
    print("\nConverting NULL tags to empty arrays...")
    cur = conn.cursor()
    cur.execute("UPDATE graphs SET tags = '{}' WHERE tags IS NULL")
    null_count = cur.rowcount
    conn.commit()
    print(f"  Updated {null_count:,} graphs")

    print("\n✓ Migration complete!")
    conn.close()


if __name__ == "__main__":
    main()
