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

    # Counts by n for min_degree >= 2
    cur.execute(
        """
        SELECT n, COUNT(*) FROM graphs
        WHERE diameter IS NOT NULL AND min_degree >= 2
        GROUP BY n ORDER BY n
        """
    )
    counts_by_n_mindeg2 = {str(r[0]): r[1] for r in cur.fetchall()}

    # Cospectral counts from pre-computed pairs table
    cospectral = {}
    for matrix in ["adj", "kirchhoff", "signless", "lap", "nb", "nbl"]:
        cur.execute(
            """
            WITH all_graphs AS (
                SELECT graph1_id as gid FROM cospectral_mates WHERE matrix_type = %s
                UNION
                SELECT graph2_id FROM cospectral_mates WHERE matrix_type = %s
            )
            SELECT g.n, COUNT(*) as cospectral_count
            FROM all_graphs a
            JOIN graphs g ON a.gid = g.id
            GROUP BY g.n
            ORDER BY g.n
            """,
            (matrix, matrix),
        )
        cospectral[matrix] = {str(r[0]): r[1] for r in cur.fetchall()}

    # Cospectral counts for min_degree >= 2
    cospectral_mindeg2 = {}
    for matrix in ["adj", "kirchhoff", "signless", "lap", "nb", "nbl"]:
        cur.execute(
            """
            WITH all_graphs AS (
                SELECT graph1_id as gid FROM cospectral_mates WHERE matrix_type = %s
                UNION
                SELECT graph2_id FROM cospectral_mates WHERE matrix_type = %s
            )
            SELECT g.n, COUNT(*) as cospectral_count
            FROM all_graphs a
            JOIN graphs g ON a.gid = g.id
            WHERE g.min_degree >= 2
            GROUP BY g.n
            ORDER BY g.n
            """,
            (matrix, matrix),
        )
        cospectral_mindeg2[matrix] = {str(r[0]): r[1] for r in cur.fetchall()}

    # Tag counts
    cur.execute(
        """
        SELECT tag, COUNT(*) as count
        FROM graphs, unnest(tags) as tag
        WHERE tags IS NOT NULL
        GROUP BY tag
        ORDER BY count DESC
        """
    )
    tag_counts = {r[0]: r[1] for r in cur.fetchall()}

    # Network property computation progress
    cur.execute(
        """
        SELECT
            COUNT(*) as total,
            COUNT(clique_number) as has_clique,
            COUNT(global_clustering) as has_clustering
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
        "counts_by_n_mindeg2": counts_by_n_mindeg2,
        "cospectral_counts_mindeg2": cospectral_mindeg2,
        "tag_counts": tag_counts,
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
