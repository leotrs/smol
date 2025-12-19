#!/usr/bin/env python3
"""Add Kirchhoff and Signless Laplacian columns to existing database.

This migration script:
1. Adds the new matrix columns to the graphs table
2. Creates indexes for the new spectral hash columns
"""

import psycopg2
import psycopg2.extras

DATABASE_URL = "dbname=smol"


def migrate():
    """Add new matrix columns and indexes."""
    conn = psycopg2.connect(DATABASE_URL)
    cur = conn.cursor(cursor_factory=psycopg2.extras.DictCursor)

    try:
        print("Adding Kirchhoff Laplacian columns...")
        cur.execute("""
            ALTER TABLE graphs
            ADD COLUMN IF NOT EXISTS kirchhoff_eigenvalues DOUBLE PRECISION[],
            ADD COLUMN IF NOT EXISTS kirchhoff_spectral_hash CHAR(16)
        """)

        print("Adding Signless Laplacian columns...")
        cur.execute("""
            ALTER TABLE graphs
            ADD COLUMN IF NOT EXISTS signless_eigenvalues DOUBLE PRECISION[],
            ADD COLUMN IF NOT EXISTS signless_spectral_hash CHAR(16)
        """)

        conn.commit()
        print("✓ Columns added")

        print("\nCreating indexes...")
        cur.execute("""
            CREATE INDEX IF NOT EXISTS idx_kirchhoff_hash
            ON graphs(kirchhoff_spectral_hash)
        """)
        cur.execute("""
            CREATE INDEX IF NOT EXISTS idx_signless_hash
            ON graphs(signless_spectral_hash)
        """)
        cur.execute("""
            CREATE INDEX IF NOT EXISTS idx_n_kirchhoff_hash
            ON graphs(n, kirchhoff_spectral_hash)
        """)
        cur.execute("""
            CREATE INDEX IF NOT EXISTS idx_n_signless_hash
            ON graphs(n, signless_spectral_hash)
        """)

        conn.commit()
        print("✓ Indexes created")

        # Check migration status
        cur.execute("""
            SELECT
                COUNT(*) as total,
                COUNT(kirchhoff_eigenvalues) as kirchhoff_filled,
                COUNT(signless_eigenvalues) as signless_filled
            FROM graphs
        """)
        row = cur.fetchone()

        print("\nMigration complete:")
        print(f"  Total graphs: {row['total']}")
        print(f"  Kirchhoff filled: {row['kirchhoff_filled']}")
        print(f"  Signless filled: {row['signless_filled']}")
        print(f"  Rows needing backfill: {row['total']}")

    finally:
        cur.close()
        conn.close()


if __name__ == "__main__":
    migrate()
