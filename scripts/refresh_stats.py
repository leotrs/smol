#!/usr/bin/env python3
"""Refresh the stats cache."""

import json
import os
import psycopg2


def get_conn():
    return psycopg2.connect(os.environ.get("DATABASE_URL", "dbname=smol"))


def compute_stats(conn) -> dict:
    """Compute all stats (slow - runs aggregation queries)."""
    cur = conn.cursor()

    # Total counts
    cur.execute("SELECT COUNT(*) FROM graphs")
    total = cur.fetchone()[0]

    cur.execute("SELECT COUNT(*) FROM graphs WHERE diameter IS NOT NULL")
    connected = cur.fetchone()[0]

    # Counts by n
    cur.execute(
        """
        SELECT n, COUNT(*) FROM graphs
        WHERE diameter IS NOT NULL
        GROUP BY n ORDER BY n
        """
    )
    counts_by_n = {str(r[0]): r[1] for r in cur.fetchall()}

    # Cospectral counts (all graphs, not just connected)
    cospectral = {}
    for matrix in ["adj", "lap", "nb", "nbl"]:
        hash_col = f"{matrix}_spectral_hash"
        cur.execute(
            f"""
            WITH groups AS (
                SELECT n, {hash_col}, COUNT(*) as cnt
                FROM graphs
                GROUP BY n, {hash_col}
                HAVING COUNT(*) > 1
            )
            SELECT n, SUM(cnt)::int as cospectral_count
            FROM groups
            GROUP BY n
            ORDER BY n
            """
        )
        cospectral[matrix] = {str(r[0]): r[1] for r in cur.fetchall()}

    # Network property computation progress
    cur.execute(
        """
        SELECT
            COUNT(*) as total,
            COUNT(clique_number) as has_clique,
            COUNT(global_clustering) as has_clustering,
            COUNT(degree_sequence) as has_degree_seq
        FROM graphs
        """
    )
    row = cur.fetchone()
    property_stats = {
        "total": row[0],
        "computed": row[1],  # use clique_number as proxy
        "percent": round(100 * row[1] / row[0], 1) if row[0] > 0 else 0,
    }

    # Property value distributions (only if enough data)
    property_ranges = {}
    if row[1] > 1000:  # Only compute if we have enough data
        for prop, col in [
            ("clustering", "global_clustering"),
            ("assortativity", "assortativity"),
            ("path_length", "avg_path_length"),
        ]:
            cur.execute(
                f"""
                SELECT
                    MIN({col})::float,
                    MAX({col})::float,
                    AVG({col})::float
                FROM graphs
                WHERE {col} IS NOT NULL
                """
            )
            r = cur.fetchone()
            if r[0] is not None:
                property_ranges[prop] = {
                    "min": round(r[0], 4),
                    "max": round(r[1], 4),
                    "avg": round(r[2], 4),
                }

    return {
        "total_graphs": total,
        "connected_graphs": connected,
        "counts_by_n": counts_by_n,
        "cospectral_counts": cospectral,
        "property_stats": property_stats,
        "property_ranges": property_ranges,
    }


def refresh_cache():
    """Compute stats and store in cache table."""
    conn = get_conn()
    cur = conn.cursor()

    # Ensure table exists
    cur.execute(
        """
        CREATE TABLE IF NOT EXISTS stats_cache (
            key VARCHAR(64) PRIMARY KEY,
            value JSONB NOT NULL,
            updated_at TIMESTAMP DEFAULT NOW()
        )
        """
    )

    print("Computing stats (this may take a while)...")
    stats = compute_stats(conn)

    print("Updating cache...")
    cur.execute(
        """
        INSERT INTO stats_cache (key, value, updated_at)
        VALUES ('main_stats', %s, NOW())
        ON CONFLICT (key) DO UPDATE
        SET value = EXCLUDED.value, updated_at = NOW()
        """,
        (json.dumps(stats),),
    )

    conn.commit()
    conn.close()

    print("Stats cache refreshed.")
    print(f"  Total graphs: {stats['total_graphs']:,}")
    print(f"  Connected graphs: {stats['connected_graphs']:,}")


if __name__ == "__main__":
    refresh_cache()
