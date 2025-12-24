"""Database access layer for the API.

Supports both PostgreSQL (sync) and SQLite (async) backends.
Set DATABASE_URL to either:
  - PostgreSQL: postgresql://user:pass@host:5432/db or dbname=smol
  - SQLite: sqlite:///path/to/file.db
"""

import json
import os
from contextlib import asynccontextmanager
from typing import Any

DATABASE_URL = os.environ.get("DATABASE_URL", "dbname=smol")

IS_SQLITE = DATABASE_URL.startswith("sqlite:")

# Track whether tags column exists (checked on first query)
_tags_column_exists: bool | None = None


def _get_sqlite_path() -> str:
    """Extract file path from sqlite:/// URL."""
    return DATABASE_URL.replace("sqlite:///", "").replace("sqlite:", "")


@asynccontextmanager
async def get_db():
    """Get database connection (async for SQLite, sync wrapped for PG)."""
    if IS_SQLITE:
        import aiosqlite
        conn = await aiosqlite.connect(_get_sqlite_path())
        conn.row_factory = aiosqlite.Row
        try:
            yield conn
        finally:
            await conn.close()
    else:
        import psycopg2
        conn = psycopg2.connect(DATABASE_URL)
        try:
            yield conn
        finally:
            conn.close()


async def _check_tags_column() -> bool:
    """Check if tags column exists in the graphs table."""
    global _tags_column_exists
    if _tags_column_exists is not None:
        return _tags_column_exists

    async with get_db() as conn:
        if IS_SQLITE:
            cursor = await conn.execute("PRAGMA table_info(graphs)")
            columns = [row[1] for row in await cursor.fetchall()]
            _tags_column_exists = "tags" in columns
        else:
            cur = conn.cursor()
            cur.execute("""
                SELECT column_name FROM information_schema.columns
                WHERE table_name = 'graphs' AND column_name = 'tags'
            """)
            _tags_column_exists = cur.fetchone() is not None
    return _tags_column_exists


def _placeholder() -> str:
    """Return the correct placeholder for the current backend."""
    return "?" if IS_SQLITE else "%s"


def _parse_row(row: Any) -> dict[str, Any] | None:
    """Convert database row to dict, handling SQLite JSON fields."""
    if row is None:
        return None

    if IS_SQLITE:
        d = dict(row)
        json_fields = [
            "adj_eigenvalues", "kirchhoff_eigenvalues", "signless_eigenvalues", "lap_eigenvalues",
            "nb_eigenvalues_re", "nb_eigenvalues_im",
            "nbl_eigenvalues_re", "nbl_eigenvalues_im",
            "tags",
        ]
        for field in json_fields:
            if field in d and d[field] is not None:
                d[field] = json.loads(d[field])
        for field in ["is_bipartite", "is_planar", "is_regular"]:
            if field in d:
                d[field] = bool(d[field])
        # Ensure tags always exists (for databases without the column)
        if "tags" not in d:
            d["tags"] = []
        return d
    else:
        d = dict(row)
        if "tags" not in d:
            d["tags"] = []
        return d


def _parse_rows(rows: list) -> list[dict[str, Any]]:
    """Convert list of database rows to list of dicts."""
    return [_parse_row(row) for row in rows]


def _tags_col(has_tags: bool) -> str:
    """Return tags column selection if it exists."""
    return ", tags" if has_tags else ""


async def fetch_graph(graph6: str) -> dict[str, Any] | None:
    """Fetch a single graph by graph6 string."""
    ph = _placeholder()
    has_tags = await _check_tags_column()
    tags_col = _tags_col(has_tags)

    async with get_db() as conn:
        if IS_SQLITE:
            cursor = await conn.execute(
                f"""
                SELECT graph6, n, m,
                       is_bipartite, is_planar, is_regular,
                       diameter, girth, radius,
                       min_degree, max_degree, triangle_count,
                       clique_number, chromatic_number,
                       algebraic_connectivity, global_clustering, avg_local_clustering,
                       avg_path_length, assortativity,
                       adj_eigenvalues, adj_spectral_hash,
                       kirchhoff_eigenvalues, kirchhoff_spectral_hash,
                       signless_eigenvalues, signless_spectral_hash,
                       lap_eigenvalues, lap_spectral_hash,
                       nb_eigenvalues_re, nb_eigenvalues_im, nb_spectral_hash,
                       nbl_eigenvalues_re, nbl_eigenvalues_im, nbl_spectral_hash
                       {tags_col}
                FROM graphs
                WHERE graph6 = {ph}
                """,
                (graph6,),
            )
            row = await cursor.fetchone()
            return _parse_row(row)
        else:
            from psycopg2.extras import RealDictCursor
            cur = conn.cursor(cursor_factory=RealDictCursor)
            cur.execute(
                f"""
                SELECT graph6, n, m,
                       is_bipartite, is_planar, is_regular,
                       diameter, girth, radius,
                       min_degree, max_degree, triangle_count,
                       clique_number, chromatic_number,
                       algebraic_connectivity, global_clustering, avg_local_clustering,
                       avg_path_length, assortativity,
                       adj_eigenvalues, adj_spectral_hash,
                       kirchhoff_eigenvalues, kirchhoff_spectral_hash,
                       signless_eigenvalues, signless_spectral_hash,
                       lap_eigenvalues, lap_spectral_hash,
                       nb_eigenvalues_re, nb_eigenvalues_im, nb_spectral_hash,
                       nbl_eigenvalues_re, nbl_eigenvalues_im, nbl_spectral_hash
                       {tags_col}
                FROM graphs
                WHERE graph6 = {ph}
                """,
                (graph6,),
            )
            return _parse_row(cur.fetchone())


async def fetch_cospectral_mates(
    graph6: str, n: int, hashes: dict[str, str]
) -> dict[str, list[str]]:
    """Fetch cospectral mates for each matrix type using pre-computed pairs."""
    ph = _placeholder()
    mates = {m: [] for m in hashes}

    async with get_db() as conn:
        if IS_SQLITE:
            # Get graph id first
            cursor = await conn.execute(
                f"SELECT id FROM graphs WHERE graph6 = {ph}", (graph6,)
            )
            row = await cursor.fetchone()
            if not row:
                return mates
            graph_id = row[0]

            for matrix in hashes:
                cursor = await conn.execute(
                    f"""
                    SELECT g.graph6 FROM cospectral_mates cp
                    JOIN graphs g ON g.id = CASE
                        WHEN cp.graph1_id = {ph} THEN cp.graph2_id
                        ELSE cp.graph1_id
                    END
                    WHERE (cp.graph1_id = {ph} OR cp.graph2_id = {ph})
                      AND cp.matrix_type = {ph}
                    """,
                    (graph_id, graph_id, graph_id, matrix),
                )
                rows = await cursor.fetchall()
                mates[matrix] = [r[0] for r in rows]
        else:
            cur = conn.cursor()
            cur.execute(f"SELECT id FROM graphs WHERE graph6 = {ph}", (graph6,))
            row = cur.fetchone()
            if not row:
                return mates
            graph_id = row[0]

            for matrix in hashes:
                cur.execute(
                    f"""
                    SELECT g.graph6 FROM cospectral_mates cp
                    JOIN graphs g ON g.id = CASE
                        WHEN cp.graph1_id = {ph} THEN cp.graph2_id
                        ELSE cp.graph1_id
                    END
                    WHERE (cp.graph1_id = {ph} OR cp.graph2_id = {ph})
                      AND cp.matrix_type = {ph}
                    """,
                    (graph_id, graph_id, graph_id, matrix),
                )
                mates[matrix] = [r[0] for r in cur.fetchall()]
    return mates


async def query_graphs(
    n: int | None = None,
    n_min: int | None = None,
    n_max: int | None = None,
    m: int | None = None,
    m_min: int | None = None,
    m_max: int | None = None,
    min_degree: int | None = None,
    max_degree: int | None = None,
    diameter: int | None = None,
    radius: int | None = None,
    girth: int | None = None,
    triangle_count: int | None = None,
    bipartite: bool | None = None,
    planar: bool | None = None,
    regular: bool | None = None,
    tags: list[str] | None = None,
    has_mechanism: str | None = None,
    connected: bool = True,
    limit: int = 100,
    offset: int = 0,
    sort_by: str = "n",
    sort_order: str = "asc",
    max_count: int | None = None,
) -> tuple[list[dict[str, Any]], int]:
    """Query graphs with filters. Returns (results, total_count).

    If max_count is set, counting stops at max_count + 1 for performance.
    """
    ph = _placeholder()
    has_tags = await _check_tags_column()
    tags_col = _tags_col(has_tags)
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
    if min_degree is not None:
        conditions.append(f"min_degree = {ph}")
        params.append(min_degree)
    if max_degree is not None:
        conditions.append(f"max_degree = {ph}")
        params.append(max_degree)
    if diameter is not None:
        conditions.append(f"diameter = {ph}")
        params.append(diameter)
    if radius is not None:
        conditions.append(f"radius = {ph}")
        params.append(radius)
    if girth is not None:
        conditions.append(f"girth = {ph}")
        params.append(girth)
    if triangle_count is not None:
        conditions.append(f"triangle_count = {ph}")
        params.append(triangle_count)
    if bipartite is not None:
        conditions.append(f"is_bipartite = {ph}")
        params.append((1 if bipartite else 0) if IS_SQLITE else bipartite)
    if planar is not None:
        conditions.append(f"is_planar = {ph}")
        params.append((1 if planar else 0) if IS_SQLITE else planar)
    if regular is not None:
        conditions.append(f"is_regular = {ph}")
        params.append((1 if regular else 0) if IS_SQLITE else regular)
    if tags and has_tags:
        for tag in tags:
            if IS_SQLITE:
                conditions.append(f"EXISTS (SELECT 1 FROM json_each(tags) WHERE value = {ph})")
            else:
                conditions.append(f"{ph} = ANY(tags)")
            params.append(tag)

    # Mechanism filter
    if has_mechanism:
        if has_mechanism == "any":
            # Has any mechanism
            conditions.append("graphs.id IN (SELECT DISTINCT graph1_id FROM switching_mechanisms UNION SELECT DISTINCT graph2_id FROM switching_mechanisms)")
        elif has_mechanism == "none":
            # No known mechanism
            conditions.append("graphs.id NOT IN (SELECT DISTINCT graph1_id FROM switching_mechanisms UNION SELECT DISTINCT graph2_id FROM switching_mechanisms)")
        else:
            # Specific mechanism type (e.g., "gm")
            conditions.append(f"graphs.id IN (SELECT DISTINCT graph1_id FROM switching_mechanisms WHERE mechanism_type = {ph} UNION SELECT DISTINCT graph2_id FROM switching_mechanisms WHERE mechanism_type = {ph})")
            params.extend([has_mechanism, has_mechanism])

    where = " AND ".join(conditions) if conditions else "1=1"

    # Validate sort column
    valid_sort_columns = ["graph6", "n", "m", "diameter", "girth", "radius", "min_degree", "max_degree", "triangle_count"]
    if sort_by not in valid_sort_columns:
        sort_by = "n"
    sort_direction = "DESC" if sort_order.lower() == "desc" else "ASC"
    order_clause = f"ORDER BY {sort_by} {sort_direction}, n, m, graph6"

    # Get total count first
    count_params = params.copy()

    async with get_db() as conn:
        if IS_SQLITE:
            # Get count (with optional limit for performance)
            if max_count is not None:
                count_params.append(max_count + 1)
                cursor = await conn.execute(
                    f"SELECT COUNT(*) FROM (SELECT 1 FROM graphs WHERE {where} LIMIT {ph}) AS subq",
                    count_params,
                )
            else:
                cursor = await conn.execute(
                    f"SELECT COUNT(*) FROM graphs WHERE {where}",
                    count_params,
                )
            row = await cursor.fetchone()
            total_count = row[0] if row else 0

            # Get results
            params.extend([limit, offset])
            cursor = await conn.execute(
                f"""
                SELECT graph6, n, m,
                       is_bipartite, is_planar, is_regular,
                       diameter, girth, radius,
                       min_degree, max_degree, triangle_count,
                       clique_number, chromatic_number,
                       algebraic_connectivity, global_clustering, avg_local_clustering,
                       avg_path_length, assortativity
                       {tags_col}
                FROM graphs
                WHERE {where}
                {order_clause}
                LIMIT {ph} OFFSET {ph}
                """,
                params,
            )
            rows = await cursor.fetchall()
            return _parse_rows(rows), total_count
        else:
            from psycopg2.extras import RealDictCursor
            # Get count (with optional limit for performance)
            cur = conn.cursor()
            if max_count is not None:
                count_params.append(max_count + 1)
                cur.execute(
                    f"SELECT COUNT(*) FROM (SELECT 1 FROM graphs WHERE {where} LIMIT {ph}) AS subq",
                    count_params,
                )
            else:
                cur.execute(
                    f"SELECT COUNT(*) FROM graphs WHERE {where}",
                    count_params,
                )
            row = cur.fetchone()
            total_count = row[0] if row else 0

            # Get results
            params.extend([limit, offset])
            cur = conn.cursor(cursor_factory=RealDictCursor)
            cur.execute(
                f"""
                SELECT graph6, n, m,
                       is_bipartite, is_planar, is_regular,
                       diameter, girth, radius,
                       min_degree, max_degree, triangle_count,
                       clique_number, chromatic_number,
                       algebraic_connectivity, global_clustering, avg_local_clustering,
                       avg_path_length, assortativity
                       {tags_col}
                FROM graphs
                WHERE {where}
                {order_clause}
                LIMIT {ph} OFFSET {ph}
                """,
                params,
            )
            return _parse_rows(cur.fetchall()), total_count


async def fetch_random_graph() -> dict[str, Any] | None:
    """Fetch a random connected graph."""
    import random
    ph = _placeholder()
    has_tags = await _check_tags_column()
    tags_col = _tags_col(has_tags)

    async with get_db() as conn:
        if IS_SQLITE:
            cursor = await conn.execute(
                "SELECT MIN(id), MAX(id) FROM graphs WHERE diameter IS NOT NULL"
            )
            row = await cursor.fetchone()
            if not row or not row[0]:
                return None
            min_id, max_id = int(row[0]), int(row[1])

            for _ in range(10):
                rand_id = random.randint(min_id, max_id)
                cursor = await conn.execute(
                    f"""
                    SELECT graph6, n, m,
                           is_bipartite, is_planar, is_regular,
                           diameter, girth, radius,
                           min_degree, max_degree, triangle_count,
                           clique_number, chromatic_number,
                           algebraic_connectivity, global_clustering, avg_local_clustering,
                           avg_path_length, assortativity,
                           adj_eigenvalues, adj_spectral_hash,
                           kirchhoff_eigenvalues, kirchhoff_spectral_hash,
                           signless_eigenvalues, signless_spectral_hash,
                           lap_eigenvalues, lap_spectral_hash,
                           nb_eigenvalues_re, nb_eigenvalues_im, nb_spectral_hash,
                           nbl_eigenvalues_re, nbl_eigenvalues_im, nbl_spectral_hash
                           {tags_col}
                    FROM graphs
                    WHERE id >= {ph} AND diameter IS NOT NULL
                    LIMIT 1
                    """,
                    (rand_id,),
                )
                row = await cursor.fetchone()
                if row:
                    return _parse_row(row)
            return None
        else:
            cur = conn.cursor()
            cur.execute("SELECT MIN(id), MAX(id) FROM graphs WHERE diameter IS NOT NULL")
            row = cur.fetchone()
            if not row or not row[0]:
                return None
            min_id, max_id = int(row[0]), int(row[1])

            from psycopg2.extras import RealDictCursor
            cur = conn.cursor(cursor_factory=RealDictCursor)
            for _ in range(10):
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
                           adj_eigenvalues, adj_spectral_hash,
                           kirchhoff_eigenvalues, kirchhoff_spectral_hash,
                           signless_eigenvalues, signless_spectral_hash,
                           lap_eigenvalues, lap_spectral_hash,
                           nb_eigenvalues_re, nb_eigenvalues_im, nb_spectral_hash,
                           nbl_eigenvalues_re, nbl_eigenvalues_im, nbl_spectral_hash
                           {tags_col}
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


async def fetch_random_cospectral_class(matrix: str = "adj") -> list[str]:
    """Fetch a random cospectral class using pre-computed pairs."""
    ph = _placeholder()

    async with get_db() as conn:
        if IS_SQLITE:
            # Get a random pair directly using ORDER BY RANDOM()
            cursor = await conn.execute(
                f"""
                SELECT graph1_id, graph2_id
                FROM cospectral_mates
                WHERE matrix_type = {ph}
                ORDER BY RANDOM()
                LIMIT 1
                """,
                (matrix,),
            )
            row = await cursor.fetchone()
            if not row:
                return []

            seed_id1, seed_id2 = row

            # Get all graphs in this cospectral family by finding all pairs involving these graphs
            cursor = await conn.execute(
                f"""
                WITH family_ids AS (
                    SELECT DISTINCT graph1_id as gid FROM cospectral_mates
                    WHERE matrix_type = {ph} AND (graph1_id = {ph} OR graph2_id = {ph})
                    UNION
                    SELECT DISTINCT graph2_id as gid FROM cospectral_mates
                    WHERE matrix_type = {ph} AND (graph1_id = {ph} OR graph2_id = {ph})
                )
                SELECT g.graph6
                FROM family_ids f
                JOIN graphs g ON g.id = f.gid
                ORDER BY g.graph6
                LIMIT 10
                """,
                (matrix, seed_id1, seed_id1, matrix, seed_id2, seed_id2),
            )
            graphs = [r[0] for r in await cursor.fetchall()]
            return graphs
        else:
            cur = conn.cursor()
            # Get a random pair directly using ORDER BY RANDOM()
            cur.execute(
                f"""
                SELECT graph1_id, graph2_id
                FROM cospectral_mates
                WHERE matrix_type = {ph}
                ORDER BY RANDOM()
                LIMIT 1
                """,
                (matrix,),
            )
            row = cur.fetchone()
            if not row:
                return []

            seed_id1, seed_id2 = row

            # Get all graphs in this cospectral family by finding all pairs involving these graphs
            cur.execute(
                f"""
                WITH family_ids AS (
                    SELECT DISTINCT graph1_id as gid FROM cospectral_mates
                    WHERE matrix_type = {ph} AND (graph1_id = {ph} OR graph2_id = {ph})
                    UNION
                    SELECT DISTINCT graph2_id as gid FROM cospectral_mates
                    WHERE matrix_type = {ph} AND (graph1_id = {ph} OR graph2_id = {ph})
                )
                SELECT g.graph6
                FROM family_ids f
                JOIN graphs g ON g.id = f.gid
                ORDER BY g.graph6
                LIMIT 10
                """,
                (matrix, seed_id1, seed_id1, matrix, seed_id2, seed_id2),
            )
            graphs = [r[0] for r in cur.fetchall()]
            return graphs


async def fetch_similar_graphs(
    graph6: str,
    matrix: str = "adj",
    limit: int = 10,
) -> list[tuple[dict[str, Any], float]]:
    """Find graphs with similar spectrum using Earth Mover's Distance.

    For real eigenvalues (adj, kirchhoff, signless, lap): Uses 1D Wasserstein distance.
    For complex eigenvalues (nb, nbl): Uses 2D Wasserstein distance on (re, im) pairs.
    """
    import numpy as np
    from scipy.stats import wasserstein_distance
    import ot  # Python Optimal Transport
    ph = _placeholder()

    target = await fetch_graph(graph6)
    if not target:
        return []

    n = target["n"]
    is_complex = matrix in ("nb", "nbl")

    if not is_complex:
        target_eigs = target[f"{matrix}_eigenvalues"]
        target_hash = target[f"{matrix}_spectral_hash"]
        eig_col = f"{matrix}_eigenvalues"
        hash_col = f"{matrix}_spectral_hash"
    else:
        re_col = f"{matrix}_eigenvalues_re"
        im_col = f"{matrix}_eigenvalues_im"
        target_re = target[re_col]
        target_im = target[im_col]
        target_eigs = np.column_stack([target_re, target_im])
        target_hash = target[f"{matrix}_spectral_hash"]
        eig_col = None
        hash_col = f"{matrix}_spectral_hash"

    async with get_db() as conn:
        if IS_SQLITE:
            if eig_col:
                cursor = await conn.execute(
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
                cospectral = await cursor.fetchall()

                cursor = await conn.execute(
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
                others = await cursor.fetchall()
                candidates = list(cospectral) + list(others)
            else:
                cursor = await conn.execute(
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
                cospectral = await cursor.fetchall()

                cursor = await conn.execute(
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
                others = await cursor.fetchall()
                candidates = list(cospectral) + list(others)
        else:
            from psycopg2.extras import RealDictCursor
            cur = conn.cursor(cursor_factory=RealDictCursor)
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

    results = []
    for row in candidates:
        row_dict = _parse_row(row)
        if not is_complex:
            eigs = row_dict[eig_col]
            if len(eigs) != len(target_eigs):
                continue
            dist = wasserstein_distance(target_eigs, eigs)
        else:
            re_vals = row_dict[f"{matrix}_eigenvalues_re"]
            im_vals = row_dict[f"{matrix}_eigenvalues_im"]
            eigs = np.column_stack([re_vals, im_vals])
            if len(eigs) != len(target_eigs):
                continue

            # 2D Wasserstein distance for complex eigenvalues
            n_eigs = len(eigs)
            # Uniform weights for both distributions
            a = np.ones(n_eigs) / n_eigs
            b = np.ones(n_eigs) / n_eigs
            # Compute pairwise Euclidean distances in complex plane
            M = ot.dist(target_eigs, eigs, metric='euclidean')
            # Compute Earth Mover's Distance
            dist = ot.emd2(a, b, M)

        results.append((row_dict, dist))

    results.sort(key=lambda x: x[1])
    return results[:limit]


async def get_stats() -> dict[str, Any]:
    """Get database statistics from cache."""
    ph = _placeholder()
    async with get_db() as conn:
        if IS_SQLITE:
            cursor = await conn.execute(
                "SELECT value FROM stats_cache WHERE key = 'main_stats'"
            )
            row = await cursor.fetchone()
        else:
            cur = conn.cursor()
            cur.execute("SELECT value FROM stats_cache WHERE key = 'main_stats'")
            row = cur.fetchone()

        if row:
            stats = row[0]
            if isinstance(stats, str):
                stats = json.loads(stats)
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
            if isinstance(stats.get("mechanism_stats"), dict):
                stats["mechanism_stats"] = {
                    int(k): v for k, v in stats["mechanism_stats"].items()
                }
            return stats

        # Fallback: compute on the fly (slow)
        if IS_SQLITE:
            cursor = await conn.execute("SELECT COUNT(*) FROM graphs")
            total = (await cursor.fetchone())[0]

            cursor = await conn.execute(
                "SELECT COUNT(*) FROM graphs WHERE diameter IS NOT NULL"
            )
            connected = (await cursor.fetchone())[0]

            cursor = await conn.execute(
                """
                SELECT n, COUNT(*) FROM graphs
                WHERE diameter IS NOT NULL
                GROUP BY n ORDER BY n
                """
            )
            counts_by_n = {r[0]: r[1] for r in await cursor.fetchall()}

            cospectral = {}
            for matrix in ["adj", "lap", "nb", "nbl"]:
                hash_col = f"{matrix}_spectral_hash"
                cursor = await conn.execute(
                    f"""
                    SELECT g.n, COUNT(DISTINCT g.{hash_col})
                    FROM cospectral_mates cp
                    JOIN graphs g ON g.id = cp.graph1_id
                    WHERE cp.matrix_type = {ph}
                    GROUP BY g.n
                    ORDER BY g.n
                    """,
                    (matrix,),
                )
                cospectral[matrix] = {r[0]: r[1] for r in await cursor.fetchall()}
        else:
            cur = conn.cursor()
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
                cur.execute(
                    f"""
                    SELECT g.n, COUNT(DISTINCT g.{hash_col})
                    FROM cospectral_mates cp
                    JOIN graphs g ON g.id = cp.graph1_id
                    WHERE cp.matrix_type = {ph}
                    GROUP BY g.n
                    ORDER BY g.n
                    """,
                    (matrix,),
                )
                cospectral[matrix] = {r[0]: r[1] for r in cur.fetchall()}

        return {
            "total_graphs": total,
            "connected_graphs": connected,
            "counts_by_n": counts_by_n,
            "cospectral_counts": cospectral,
        }


async def fetch_graph_mechanisms(
    graph6: str, matrix_type: str | None = None
) -> dict[str, Any]:
    """Fetch all mechanisms for a specific graph."""
    ph = _placeholder()

    async with get_db() as conn:
        if IS_SQLITE:
            # Get graph info
            cursor = await conn.execute(
                f"SELECT id, n, m FROM graphs WHERE graph6 = {ph}", (graph6,)
            )
            graph_row = await cursor.fetchone()
            if not graph_row:
                return {"error": "Graph not found"}

            graph_id, n, m = graph_row

            # Get mechanisms
            query = f"""
                SELECT
                    CASE
                        WHEN sm.graph1_id = {ph} THEN g2.graph6
                        ELSE g1.graph6
                    END as mate_graph6,
                    sm.matrix_type,
                    sm.mechanism_type,
                    sm.config
                FROM switching_mechanisms sm
                JOIN graphs g1 ON sm.graph1_id = g1.id
                JOIN graphs g2 ON sm.graph2_id = g2.id
                WHERE (sm.graph1_id = {ph} OR sm.graph2_id = {ph})
            """
            params = [graph_id, graph_id, graph_id]

            if matrix_type:
                query += f" AND sm.matrix_type = {ph}"
                params.append(matrix_type)

            query += " ORDER BY sm.matrix_type, sm.mechanism_type"

            cursor = await conn.execute(query, params)
            rows = await cursor.fetchall()

        else:
            from psycopg2.extras import RealDictCursor
            cur = conn.cursor(cursor_factory=RealDictCursor)

            cur.execute("SELECT id, n, m FROM graphs WHERE graph6 = %s", (graph6,))
            graph_row = cur.fetchone()
            if not graph_row:
                return {"error": "Graph not found"}

            graph_id, n, m = graph_row["id"], graph_row["n"], graph_row["m"]

            query = """
                SELECT
                    CASE
                        WHEN sm.graph1_id = %s THEN g2.graph6
                        ELSE g1.graph6
                    END as mate_graph6,
                    sm.matrix_type,
                    sm.mechanism_type,
                    sm.config
                FROM switching_mechanisms sm
                JOIN graphs g1 ON sm.graph1_id = g1.id
                JOIN graphs g2 ON sm.graph2_id = g2.id
                WHERE (sm.graph1_id = %s OR sm.graph2_id = %s)
            """
            params = [graph_id, graph_id, graph_id]

            if matrix_type:
                query += " AND sm.matrix_type = %s"
                params.append(matrix_type)

            query += " ORDER BY sm.matrix_type, sm.mechanism_type"

            cur.execute(query, params)
            rows = cur.fetchall()

        # Organize by matrix type
        mechanisms = {}
        for row in rows:
            if IS_SQLITE:
                mate_g6, mat_type, mech_type, config_str = row
                config = json.loads(config_str) if isinstance(config_str, str) else config_str
            else:
                mate_g6 = row["mate_graph6"]
                mat_type = row["matrix_type"]
                mech_type = row["mechanism_type"]
                config = row["config"]

            if mat_type not in mechanisms:
                mechanisms[mat_type] = []

            mechanisms[mat_type].append({
                "mate": mate_g6,
                "mechanism": mech_type,
                "config": config
            })

        return {
            "graph6": graph6,
            "n": n,
            "m": m,
            "mechanisms": mechanisms
        }


async def fetch_mechanism_stats(
    n: int | None = None, matrix_type: str = "adj"
) -> dict[str, Any]:
    """Get statistics about mechanism coverage."""
    ph = _placeholder()

    async with get_db() as conn:
        if IS_SQLITE:
            # Total graphs with mates
            query_total = f"""
                WITH all_graphs AS (
                    SELECT graph1_id as gid FROM cospectral_mates WHERE matrix_type = {ph}
                    UNION
                    SELECT graph2_id FROM cospectral_mates WHERE matrix_type = {ph}
                )
                SELECT COUNT(DISTINCT a.gid)
                FROM all_graphs a
                JOIN graphs g ON a.gid = g.id
            """
            params_total = [matrix_type, matrix_type]

            if n is not None:
                query_total += f" WHERE g.n = {ph}"
                params_total.append(n)

            cursor = await conn.execute(query_total, params_total)
            row = await cursor.fetchone()
            total_graphs = row[0] if row else 0

            # Mechanism breakdown - simplified query for SQLite
            query_mechs = f"""
                SELECT sm.mechanism_type, COUNT(DISTINCT sm.graph1_id || ',' || sm.graph2_id) as pair_count
                FROM switching_mechanisms sm
                JOIN graphs g1 ON sm.graph1_id = g1.id
                WHERE sm.matrix_type = {ph}
            """
            params_mechs = [matrix_type]

            if n is not None:
                query_mechs += f" AND g1.n = {ph}"
                params_mechs.append(n)

            query_mechs += " GROUP BY sm.mechanism_type"

            cursor = await conn.execute(query_mechs, params_mechs)
            mech_rows = await cursor.fetchall()

        else:
            from psycopg2.extras import RealDictCursor
            cur = conn.cursor(cursor_factory=RealDictCursor)

            query_total = """
                WITH all_graphs AS (
                    SELECT graph1_id as gid FROM cospectral_mates WHERE matrix_type = %s
                    UNION
                    SELECT graph2_id FROM cospectral_mates WHERE matrix_type = %s
                )
                SELECT COUNT(DISTINCT a.gid)
                FROM all_graphs a
                JOIN graphs g ON a.gid = g.id
            """
            params_total = [matrix_type, matrix_type]

            if n is not None:
                query_total += " WHERE g.n = %s"
                params_total.append(n)

            cur.execute(query_total, params_total)
            result = cur.fetchone()
            total_graphs = result["count"] if result else 0

            query_mechs = """
                SELECT sm.mechanism_type, COUNT(DISTINCT sm.graph1_id || ',' || sm.graph2_id) as pair_count
                FROM switching_mechanisms sm
                JOIN graphs g1 ON sm.graph1_id = g1.id
                WHERE sm.matrix_type = %s
            """
            params_mechs = [matrix_type]

            if n is not None:
                query_mechs += " AND g1.n = %s"
                params_mechs.append(n)

            query_mechs += " GROUP BY sm.mechanism_type"

            cur.execute(query_mechs, params_mechs)
            mech_rows = cur.fetchall()

        mechanisms = {}
        for row in mech_rows:
            if IS_SQLITE:
                mech_type, pair_count = row
            else:
                mech_type = row["mechanism_type"]
                pair_count = row["pair_count"]

            # Estimate graph count (each pair contributes 2 graphs, but with overlap)
            # This is a rough estimate
            mechanisms[mech_type] = {
                "pairs": pair_count,
                "coverage": pair_count / (total_graphs / 2) if total_graphs > 0 else 0
            }

        return {
            "n": n,
            "matrix_type": matrix_type,
            "total_graphs": total_graphs,
            "mechanisms": mechanisms
        }


async def fetch_all_mechanism_stats(matrix_type: str = "adj") -> dict[int, dict[str, Any]]:
    """Get mechanism statistics grouped by n."""
    ph = _placeholder()

    async with get_db() as conn:
        if IS_SQLITE:
            # Get all mechanism data grouped by n
            query = f"""
                SELECT
                    g.n,
                    sm.mechanism_type,
                    COUNT(DISTINCT sm.graph1_id || ',' || sm.graph2_id) as pair_count,
                    COUNT(DISTINCT g.id) as graph_count
                FROM switching_mechanisms sm
                JOIN graphs g ON (sm.graph1_id = g.id OR sm.graph2_id = g.id)
                WHERE sm.matrix_type = {ph}
                GROUP BY g.n, sm.mechanism_type
            """
            cursor = await conn.execute(query, [matrix_type])
            rows = await cursor.fetchall()

            # Get total graphs with mates for each n
            query_totals = f"""
                WITH all_graphs AS (
                    SELECT graph1_id as gid FROM cospectral_mates WHERE matrix_type = {ph}
                    UNION
                    SELECT graph2_id FROM cospectral_mates WHERE matrix_type = {ph}
                )
                SELECT g.n, COUNT(DISTINCT a.gid) as total
                FROM all_graphs a
                JOIN graphs g ON a.gid = g.id
                GROUP BY g.n
            """
            cursor = await conn.execute(query_totals, [matrix_type, matrix_type])
            totals_rows = await cursor.fetchall()

        else:
            from psycopg2.extras import RealDictCursor
            cur = conn.cursor(cursor_factory=RealDictCursor)

            query = """
                SELECT
                    g.n,
                    sm.mechanism_type,
                    COUNT(DISTINCT sm.graph1_id || ',' || sm.graph2_id) as pair_count,
                    COUNT(DISTINCT g.id) as graph_count
                FROM switching_mechanisms sm
                JOIN graphs g ON (sm.graph1_id = g.id OR sm.graph2_id = g.id)
                WHERE sm.matrix_type = %s
                GROUP BY g.n, sm.mechanism_type
            """
            cur.execute(query, [matrix_type])
            rows = cur.fetchall()

            query_totals = """
                WITH all_graphs AS (
                    SELECT graph1_id as gid FROM cospectral_mates WHERE matrix_type = %s
                    UNION
                    SELECT graph2_id FROM cospectral_mates WHERE matrix_type = %s
                )
                SELECT g.n, COUNT(DISTINCT a.gid) as total
                FROM all_graphs a
                JOIN graphs g ON a.gid = g.id
                GROUP BY g.n
            """
            cur.execute(query_totals, [matrix_type, matrix_type])
            totals_rows = cur.fetchall()

        # Build totals map
        totals = {}
        for row in totals_rows:
            if IS_SQLITE:
                n, total = row
            else:
                n = row["n"]
                total = row["total"]
            totals[n] = total

        # Build result grouped by n
        result = {}
        for row in rows:
            if IS_SQLITE:
                n, mech_type, pair_count, graph_count = row
            else:
                n = row["n"]
                mech_type = row["mechanism_type"]
                pair_count = row["pair_count"]
                graph_count = row["graph_count"]

            if n not in result:
                result[n] = {
                    "total_graphs": totals.get(n, 0),
                    "mechanisms": {}
                }

            total = totals.get(n, 0)
            result[n]["mechanisms"][mech_type] = {
                "graphs": graph_count,
                "pairs": pair_count,
                "coverage": graph_count / total if total > 0 else 0
            }

        return result
