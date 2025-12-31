#!/usr/bin/env python3
"""Migrate bipartite/planar/regular from boolean columns to tags array.

This is much faster than recomputing tags from scratch.
Adds 'bipartite', 'planar', 'regular' to existing tags based on boolean columns.

Usage:
    python scripts/migrate_boolean_tags.py
"""

import os
import psycopg2

DATABASE_URL = os.environ.get("DATABASE_URL", "dbname=smol")


def main():
    conn = psycopg2.connect(DATABASE_URL)
    cur = conn.cursor()

    print("Migrating boolean columns to tags...")

    # Count total graphs
    cur.execute("SELECT COUNT(*) FROM graphs")
    total = cur.fetchone()[0]
    print(f"Total graphs: {total:,}")

    # Add 'bipartite' tag where is_bipartite = true and 'bipartite' not already in tags
    print("\nAdding 'bipartite' tag...")
    cur.execute("""
        UPDATE graphs
        SET tags = array_append(COALESCE(tags, '{}'), 'bipartite')
        WHERE is_bipartite = true
          AND (tags IS NULL OR 'bipartite' != ALL(tags))
    """)
    bipartite_count = cur.rowcount
    conn.commit()
    print(f"  Updated {bipartite_count:,} graphs")

    # Add 'planar' tag where is_planar = true and 'planar' not already in tags
    print("\nAdding 'planar' tag...")
    cur.execute("""
        UPDATE graphs
        SET tags = array_append(COALESCE(tags, '{}'), 'planar')
        WHERE is_planar = true
          AND (tags IS NULL OR 'planar' != ALL(tags))
    """)
    planar_count = cur.rowcount
    conn.commit()
    print(f"  Updated {planar_count:,} graphs")

    # Add 'regular' tag where is_regular = true and 'regular' not already in tags
    print("\nAdding 'regular' tag...")
    cur.execute("""
        UPDATE graphs
        SET tags = array_append(COALESCE(tags, '{}'), 'regular')
        WHERE is_regular = true
          AND (tags IS NULL OR 'regular' != ALL(tags))
    """)
    regular_count = cur.rowcount
    conn.commit()
    print(f"  Updated {regular_count:,} graphs")

    # Ensure tags column is never NULL (convert NULL to empty array)
    print("\nConverting NULL tags to empty arrays...")
    cur.execute("""
        UPDATE graphs
        SET tags = '{}'
        WHERE tags IS NULL
    """)
    null_count = cur.rowcount
    conn.commit()
    print(f"  Updated {null_count:,} graphs")

    print("\n✓ Migration complete!")
    conn.close()


if __name__ == "__main__":
    main()
