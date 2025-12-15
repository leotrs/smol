"""Database access layer for the API.

Supports both PostgreSQL and SQLite backends.
Set DATABASE_URL to either:
  - PostgreSQL: postgresql://user:pass@host:5432/db or dbname=smol
  - SQLite: sqlite:///path/to/file.db
"""

import json
import os
import sqlite3
from contextlib import contextmanager
from typing import Any

DATABASE_URL = os.environ.get("DATABASE_URL", "dbname=smol")

# Detect backend type
IS_SQLITE = DATABASE_URL.startswith("sqlite:")


def _get_sqlite_path() -> str:
    """Extract file path from sqlite:/// URL."""
    return DATABASE_URL.replace("sqlite:///", "").replace("sqlite:", "")


@contextmanager
def get_db():
    """Get database connection (works with both PG and SQLite)."""
    if IS_SQLITE:
        conn = sqlite3.connect(_get_sqlite_path())
        conn.row_factory = sqlite3.Row
        try:
            yield conn
        finally:
            conn.close()
    else:
        import psycopg2
        conn = psycopg2.connect(DATABASE_URL)
        try:
            yield conn
        finally:
            conn.close()


def _placeholder() -> str:
    """Return the correct placeholder for the current backend."""
    return "?" if IS_SQLITE else "%s"


def _parse_row(row: Any) -> dict[str, Any] | None:
    """Convert database row to dict, handling SQLite JSON fields."""
    if row is None:
        return None

    if IS_SQLITE:
        d = dict(row)
        # Parse JSON array fields
        json_fields = [
            "adj_eigenvalues", "lap_eigenvalues",
            "nb_eigenvalues_re", "nb_eigenvalues_im",
            "nbl_eigenvalues_re", "nbl_eigenvalues_im",
            "degree_sequence", "betweenness_centrality",
            "closeness_centrality", "eigenvector_centrality",
        ]
        for field in json_fields:
            if field in d and d[field] is not None:
                d[field] = json.loads(d[field])
        # Convert integer booleans
        for field in ["is_bipartite", "is_planar", "is_regular"]:
            if field in d:
                d[field] = bool(d[field])
        return d
    else:
        return dict(row)


def _parse_rows(rows: list) -> list[dict[str, Any]]:
    """Convert list of database rows to list of dicts."""
    return [_parse_row(row) for row in rows]


def _get_cursor(conn):
    """Get appropriate cursor for the backend."""
    if IS_SQLITE:
        return conn.cursor()
    else:
        from psycopg2.extras import RealDictCursor
        return conn.cursor(cursor_factory=RealDictCursor)


def fetch_graph(graph6: str) -> dict[str, Any] | None:
    """Fetch a single graph by graph6 string."""
    ph = _placeholder()
    with get_db() as conn:
        cur = _get_cursor(conn)
        cur.execute(
            f"""
            SELECT graph6, n, m,
                   is_bipartite, is_planar, is_regular,
                   diameter, girth, radius,
                   min_degree, max_degree, triangle_count,
                   clique_number, chromatic_number,
                   algebraic_connectivity, global_clustering, avg_local_clustering,
                   avg_path_length, assortativity,
                   degree_sequence, betweenness_centrality, closeness_centrality, eigenvector_centrality,
                   adj_eigenvalues, adj_spectral_hash,
                   lap_eigenvalues, lap_spectral_hash,
                   nb_eigenvalues_re, nb_eigenvalues_im, nb_spectral_hash,
                   nbl_eigenvalues_re, nbl_eigenvalues_im, nbl_spectral_hash
            FROM graphs
            WHERE graph6 = {ph}
            """,
            (graph6,),
        )
        return _parse_row(cur.fetchone())


def fetch_cospectral_mates(
    graph6: str, n: int, hashes: dict[str, str]
) -> dict[str, list[str]]:
    """Fetch cospectral mates for each matrix type."""
    ph = _placeholder()
    mates = {}
    with get_db() as conn:
        cur = conn.cursor()
        for matrix, hash_val in hashes.items():
            hash_col = f"{matrix}_spectral_hash"
            cur.execute(
                f"""
                SELECT graph6 FROM graphs
                WHERE {hash_col} = {ph} AND graph6 != {ph} AND n = {ph}
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
    ph = _placeholder()
    conditions = []
    params = []

    if connected:
        conditions.append("diameter IS NOT NULL")

    if n is not None:
        conditions.append(f"n = {ph}")
        params.append(n)
    if n_min is not None:
        conditions.append(f"n >= {ph}")
        params.append(n_min)
    if n_max is not None:
        conditions.append(f"n <= {ph}")
        params.append(n_max)
    if m is not None:
        conditions.append(f"m = {ph}")
        params.append(m)
    if m_min is not None:
        conditions.append(f"m >= {ph}")
        params.append(m_min)
    if m_max is not None:
        conditions.append(f"m <= {ph}")
        params.append(m_max)
    if bipartite is not None:
        conditions.append(f"is_bipartite = {ph}")
        params.append((1 if bipartite else 0) if IS_SQLITE else bipartite)
    if planar is not None:
        conditions.append(f"is_planar = {ph}")
        params.append((1 if planar else 0) if IS_SQLITE else planar)
    if regular is not None:
        conditions.append(f"is_regular = {ph}")
        params.append((1 if regular else 0) if IS_SQLITE else regular)

    where = " AND ".join(conditions) if conditions else "1=1"
    params.extend([limit, offset])

    with get_db() as conn:
        cur = _get_cursor(conn)
        cur.execute(
            f"""
            SELECT graph6, n, m,
                   is_bipartite, is_planar, is_regular,
                   diameter, girth, radius,
                   min_degree, max_degree, triangle_count,
                   clique_number, chromatic_number,
                   algebraic_connectivity, global_clustering, avg_local_clustering,
                   avg_path_length, assortativity,
                   degree_sequence, betweenness_centrality, closeness_centrality, eigenvector_centrality
            FROM graphs
            WHERE {where}
            ORDER BY n, m, graph6
            LIMIT {ph} OFFSET {ph}
            """,
            params,
        )
        return _parse_rows(cur.fetchall())


def fetch_random_graph() -> dict[str, Any] | None:
    """Fetch a random connected graph."""
    import random
    ph = _placeholder()

    with get_db() as conn:
        cur = conn.cursor()
        cur.execute("SELECT MIN(id), MAX(id) FROM graphs WHERE diameter IS NOT NULL")
        row = cur.fetchone()
        if not row or not row[0]:
            return None
        min_id, max_id = int(row[0]), int(row[1])

        cur = _get_cursor(conn)
        for _ in range(10):  # retry a few times in case of gaps
            rand_id = random.randint(min_id, max_id)
            cur.execute(
                f"""
                SELECT graph6, n, m,
                       is_bipartite, is_planar, is_regular,
                       diameter, girth, radius,
                       min_degree, max_degree, triangle_count,
                       clique_number, chromatic_number,
                       algebraic_connectivity, global_clustering, avg_local_clustering,
                       avg_path_length, assortativity,
                       degree_sequence, betweenness_centrality, closeness_centrality, eigenvector_centrality,
                       adj_eigenvalues, adj_spectral_hash,
                       lap_eigenvalues, lap_spectral_hash,
                       nb_eigenvalues_re, nb_eigenvalues_im, nb_spectral_hash,
                       nbl_eigenvalues_re, nbl_eigenvalues_im, nbl_spectral_hash
                FROM graphs
                WHERE id >= {ph} AND diameter IS NOT NULL
                LIMIT 1
                """,
                (rand_id,),
            )
            row = cur.fetchone()
            if row:
                return _parse_row(row)
        return None


def fetch_random_cospectral_class(matrix: str = "adj") -> list[str]:
    """Fetch a random cospectral class (graphs sharing same spectrum)."""
    import random
    ph = _placeholder()
    hash_col = f"{matrix}_spectral_hash"

    with get_db() as conn:
        cur = conn.cursor()

        # Get ID range
        cur.execute("SELECT MIN(id), MAX(id) FROM graphs WHERE diameter IS NOT NULL")
        row = cur.fetchone()
        if not row or not row[0]:
            return []
        min_id, max_id = int(row[0]), int(row[1])

        # Try random graphs until we find one with cospectral mates
        for _ in range(50):
            rand_id = random.randint(min_id, max_id)
            cur.execute(
                f"""
                SELECT {hash_col}, n FROM graphs
                WHERE id >= {ph} AND diameter IS NOT NULL
                LIMIT 1
                """,
                (rand_id,),
            )
            row = cur.fetchone()
            if not row:
                continue

            hash_val, n = row

            # Check if this hash has multiple graphs
            cur.execute(
                f"""
                SELECT graph6 FROM graphs
                WHERE {hash_col} = {ph} AND n = {ph} AND diameter IS NOT NULL
                ORDER BY graph6
                LIMIT 10
                """,
                (hash_val, n),
            )
            graphs = [r[0] for r in cur.fetchall()]
            if len(graphs) > 1:
                return graphs

        return []


def fetch_similar_graphs(
    graph6: str,
    matrix: str = "adj",
    limit: int = 10,
) -> list[tuple[dict[str, Any], float]]:
    """Find graphs with similar spectrum using L2 distance.

    Returns list of (graph_row, distance) tuples sorted by distance.
    Only searches graphs with same n (vertex count).
    """
    import math
    ph = _placeholder()

    # Get target graph
    target = fetch_graph(graph6)
    if not target:
        return []

    n = target["n"]

    if matrix in ("adj", "lap"):
        target_eigs = target[f"{matrix}_eigenvalues"]
        target_hash = target[f"{matrix}_spectral_hash"]
        eig_col = f"{matrix}_eigenvalues"
        hash_col = f"{matrix}_spectral_hash"
    else:
        # For complex eigenvalues (nb, nbl), use magnitude
        re_col = f"{matrix}_eigenvalues_re"
        im_col = f"{matrix}_eigenvalues_im"
        target_re = target[re_col]
        target_im = target[im_col]
        target_eigs = [math.sqrt(r**2 + i**2) for r, i in zip(target_re, target_im)]
        target_eigs.sort()
        target_hash = target[f"{matrix}_spectral_hash"]
        eig_col = None
        hash_col = f"{matrix}_spectral_hash"

    with get_db() as conn:
        cur = _get_cursor(conn)

        if IS_SQLITE:
            # SQLite doesn't support UNION ALL with ORDER BY random() the same way
            # Use separate queries
            if eig_col:
                cur.execute(
                    f"""
                    SELECT graph6, n, m,
                           is_bipartite, is_planar, is_regular,
                           diameter, girth, radius,
                           min_degree, max_degree, triangle_count,
                           {eig_col}
                    FROM graphs
                    WHERE n = {ph} AND {hash_col} = {ph} AND graph6 != {ph}
                    LIMIT 50
                    """,
                    (n, target_hash, graph6),
                )
                cospectral = cur.fetchall()

                cur.execute(
                    f"""
                    SELECT graph6, n, m,
                           is_bipartite, is_planar, is_regular,
                           diameter, girth, radius,
                           min_degree, max_degree, triangle_count,
                           {eig_col}
                    FROM graphs
                    WHERE n = {ph} AND {hash_col} != {ph} AND graph6 != {ph}
                    ORDER BY random()
                    LIMIT 450
                    """,
                    (n, target_hash, graph6),
                )
                others = cur.fetchall()
                candidates = list(cospectral) + list(others)
            else:
                cur.execute(
                    f"""
                    SELECT graph6, n, m,
                           is_bipartite, is_planar, is_regular,
                           diameter, girth, radius,
                           min_degree, max_degree, triangle_count,
                           {matrix}_eigenvalues_re, {matrix}_eigenvalues_im
                    FROM graphs
                    WHERE n = {ph} AND {hash_col} = {ph} AND graph6 != {ph}
                    LIMIT 50
                    """,
                    (n, target_hash, graph6),
                )
                cospectral = cur.fetchall()

                cur.execute(
                    f"""
                    SELECT graph6, n, m,
                           is_bipartite, is_planar, is_regular,
                           diameter, girth, radius,
                           min_degree, max_degree, triangle_count,
                           {matrix}_eigenvalues_re, {matrix}_eigenvalues_im
                    FROM graphs
                    WHERE n = {ph} AND {hash_col} != {ph} AND graph6 != {ph}
                    ORDER BY random()
                    LIMIT 450
                    """,
                    (n, target_hash, graph6),
                )
                others = cur.fetchall()
                candidates = list(cospectral) + list(others)
        else:
            # PostgreSQL version with UNION ALL
            if eig_col:
                cur.execute(
                    f"""
                    (SELECT graph6, n, m,
                           is_bipartite, is_planar, is_regular,
                           diameter, girth, radius,
                           min_degree, max_degree, triangle_count,
                           {eig_col}
                    FROM graphs
                    WHERE n = {ph} AND {hash_col} = {ph} AND graph6 != {ph}
                    LIMIT 50)
                    UNION ALL
                    (SELECT graph6, n, m,
                           is_bipartite, is_planar, is_regular,
                           diameter, girth, radius,
                           min_degree, max_degree, triangle_count,
                           {eig_col}
                    FROM graphs
                    WHERE n = {ph} AND {hash_col} != {ph} AND graph6 != {ph}
                    ORDER BY random()
                    LIMIT 450)
                    """,
                    (n, target_hash, graph6, n, target_hash, graph6),
                )
            else:
                cur.execute(
                    f"""
                    (SELECT graph6, n, m,
                           is_bipartite, is_planar, is_regular,
                           diameter, girth, radius,
                           min_degree, max_degree, triangle_count,
                           {matrix}_eigenvalues_re, {matrix}_eigenvalues_im
                    FROM graphs
                    WHERE n = {ph} AND {hash_col} = {ph} AND graph6 != {ph}
                    LIMIT 50)
                    UNION ALL
                    (SELECT graph6, n, m,
                           is_bipartite, is_planar, is_regular,
                           diameter, girth, radius,
                           min_degree, max_degree, triangle_count,
                           {matrix}_eigenvalues_re, {matrix}_eigenvalues_im
                    FROM graphs
                    WHERE n = {ph} AND {hash_col} != {ph} AND graph6 != {ph}
                    ORDER BY random()
                    LIMIT 450)
                    """,
                    (n, target_hash, graph6, n, target_hash, graph6),
                )
            candidates = cur.fetchall()

    # Compute L2 distances
    results = []
    for row in candidates:
        row_dict = _parse_row(row)
        if eig_col:
            eigs = row_dict[eig_col]
        else:
            re_vals = row_dict[f"{matrix}_eigenvalues_re"]
            im_vals = row_dict[f"{matrix}_eigenvalues_im"]
            eigs = sorted([math.sqrt(r**2 + i**2) for r, i in zip(re_vals, im_vals)])

        if len(eigs) != len(target_eigs):
            continue

        # L2 distance
        dist = math.sqrt(sum((a - b) ** 2 for a, b in zip(eigs, target_eigs)))
        results.append((row_dict, dist))

    # Sort by distance and return top N
    results.sort(key=lambda x: x[1])
    return results[:limit]


def get_stats() -> dict[str, Any]:
    """Get database statistics from cache."""
    with get_db() as conn:
        cur = conn.cursor()

        # Try to get from cache first
        cur.execute(
            "SELECT value FROM stats_cache WHERE key = 'main_stats'"
        )
        row = cur.fetchone()
        if row:
            stats = row[0]
            # Handle SQLite returning string vs PG returning dict
            if isinstance(stats, str):
                stats = json.loads(stats)
            # Convert string keys back to int for counts_by_n
            if isinstance(stats.get("counts_by_n"), dict):
                stats["counts_by_n"] = {
                    int(k): v for k, v in stats["counts_by_n"].items()
                }
            if isinstance(stats.get("cospectral_counts"), dict):
                for matrix in stats["cospectral_counts"]:
                    stats["cospectral_counts"][matrix] = {
                        int(k): v
                        for k, v in stats["cospectral_counts"][matrix].items()
                    }
            return stats

        # Fallback: compute on the fly (slow)
        cur.execute("SELECT COUNT(*) FROM graphs")
        total = cur.fetchone()[0]

        cur.execute("SELECT COUNT(*) FROM graphs WHERE diameter IS NOT NULL")
        connected = cur.fetchone()[0]

        cur.execute(
            """
            SELECT n, COUNT(*) FROM graphs
            WHERE diameter IS NOT NULL
            GROUP BY n ORDER BY n
            """
        )
        counts_by_n = {r[0]: r[1] for r in cur.fetchall()}

        cospectral = {}
        for matrix in ["adj", "lap", "nb", "nbl"]:
            hash_col = f"{matrix}_spectral_hash"
            # SQLite-compatible query
            cur.execute(
                f"""
                SELECT n, COUNT(*) as cospectral_count
                FROM (
                    SELECT n, {hash_col}
                    FROM graphs
                    WHERE diameter IS NOT NULL
                    GROUP BY n, {hash_col}
                    HAVING COUNT(*) > 1
                )
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
