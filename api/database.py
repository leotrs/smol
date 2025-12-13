"""Database access layer for the API."""

import os
from contextlib import contextmanager
from typing import Any

import psycopg2
from psycopg2.extras import RealDictCursor


def get_connection_string() -> str:
    return os.environ.get("DATABASE_URL", "dbname=smol")


@contextmanager
def get_db():
    conn = psycopg2.connect(get_connection_string())
    try:
        yield conn
    finally:
        conn.close()


def fetch_graph(graph6: str) -> dict[str, Any] | None:
    """Fetch a single graph by graph6 string."""
    with get_db() as conn:
        cur = conn.cursor(cursor_factory=RealDictCursor)
        cur.execute(
            """
            SELECT graph6, n, m,
                   is_bipartite, is_planar, is_regular,
                   diameter, girth, radius,
                   min_degree, max_degree, triangle_count,
                   adj_eigenvalues, adj_spectral_hash,
                   lap_eigenvalues, lap_spectral_hash,
                   nb_eigenvalues_re, nb_eigenvalues_im, nb_spectral_hash,
                   nbl_eigenvalues_re, nbl_eigenvalues_im, nbl_spectral_hash
            FROM graphs
            WHERE graph6 = %s
            """,
            (graph6,),
        )
        return cur.fetchone()


def fetch_cospectral_mates(
    graph6: str, n: int, hashes: dict[str, str]
) -> dict[str, list[str]]:
    """Fetch cospectral mates for each matrix type."""
    mates = {}
    with get_db() as conn:
        cur = conn.cursor()
        for matrix, hash_val in hashes.items():
            hash_col = f"{matrix}_spectral_hash"
            cur.execute(
                f"""
                SELECT graph6 FROM graphs
                WHERE {hash_col} = %s AND graph6 != %s AND n = %s
                """,
                (hash_val, graph6, n),
            )
            mates[matrix] = [r[0] for r in cur.fetchall()]
    return mates


def query_graphs(
    n: int | None = None,
    n_min: int | None = None,
    n_max: int | None = None,
    m: int | None = None,
    m_min: int | None = None,
    m_max: int | None = None,
    bipartite: bool | None = None,
    planar: bool | None = None,
    regular: bool | None = None,
    connected: bool = True,
    limit: int = 100,
    offset: int = 0,
) -> list[dict[str, Any]]:
    """Query graphs with filters."""
    conditions = []
    params = []

    if connected:
        conditions.append("diameter IS NOT NULL")

    if n is not None:
        conditions.append("n = %s")
        params.append(n)
    if n_min is not None:
        conditions.append("n >= %s")
        params.append(n_min)
    if n_max is not None:
        conditions.append("n <= %s")
        params.append(n_max)
    if m is not None:
        conditions.append("m = %s")
        params.append(m)
    if m_min is not None:
        conditions.append("m >= %s")
        params.append(m_min)
    if m_max is not None:
        conditions.append("m <= %s")
        params.append(m_max)
    if bipartite is not None:
        conditions.append("is_bipartite = %s")
        params.append(bipartite)
    if planar is not None:
        conditions.append("is_planar = %s")
        params.append(planar)
    if regular is not None:
        conditions.append("is_regular = %s")
        params.append(regular)

    where = " AND ".join(conditions) if conditions else "TRUE"
    params.extend([limit, offset])

    with get_db() as conn:
        cur = conn.cursor(cursor_factory=RealDictCursor)
        cur.execute(
            f"""
            SELECT graph6, n, m,
                   is_bipartite, is_planar, is_regular,
                   diameter, girth, radius,
                   min_degree, max_degree, triangle_count
            FROM graphs
            WHERE {where}
            ORDER BY n, m, graph6
            LIMIT %s OFFSET %s
            """,
            params,
        )
        return cur.fetchall()


def get_stats() -> dict[str, Any]:
    """Get database statistics."""
    with get_db() as conn:
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
        counts_by_n = {r[0]: r[1] for r in cur.fetchall()}

        # Cospectral counts
        cospectral = {}
        for matrix in ["adj", "lap", "nb", "nbl"]:
            hash_col = f"{matrix}_spectral_hash"
            cur.execute(
                f"""
                WITH groups AS (
                    SELECT n, {hash_col}, COUNT(*) as cnt
                    FROM graphs
                    WHERE diameter IS NOT NULL
                    GROUP BY n, m, {hash_col}
                    HAVING COUNT(*) > 1
                )
                SELECT n, SUM(cnt)::int as cospectral_count
                FROM groups
                GROUP BY n
                ORDER BY n
                """
            )
            cospectral[matrix] = {r[0]: r[1] for r in cur.fetchall()}

        return {
            "total_graphs": total,
            "connected_graphs": connected,
            "counts_by_n": counts_by_n,
            "cospectral_counts": cospectral,
        }
