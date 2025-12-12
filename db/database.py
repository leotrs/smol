"""Database operations for the spectral graph database."""

import os
from contextlib import contextmanager

import psycopg2
from psycopg2.extras import execute_values

from .graph_data import GraphRecord


def get_connection_string() -> str:
    """Get database connection string from environment or use default."""
    return os.environ.get("SMOL_DB_URL", "postgresql://localhost/smol")


def connect():
    """Create a database connection."""
    return psycopg2.connect(get_connection_string())


@contextmanager
def get_connection():
    """Context manager for database connections."""
    conn = connect()
    try:
        yield conn
    finally:
        conn.close()


def init_schema(conn) -> None:
    """Initialize the database schema."""
    schema_path = os.path.join(os.path.dirname(__file__), "..", "sql", "schema.sql")
    with open(schema_path) as f:
        schema_sql = f.read()

    with conn.cursor() as cur:
        cur.execute(schema_sql)
    conn.commit()


INSERT_SQL = """
INSERT INTO graphs (
    n, m, graph6,
    adj_eigenvalues, adj_spectral_hash,
    lap_eigenvalues, lap_spectral_hash,
    nb_eigenvalues_re, nb_eigenvalues_im, nb_spectral_hash,
    nbl_eigenvalues_re, nbl_eigenvalues_im, nbl_spectral_hash,
    is_bipartite, is_planar, is_regular,
    diameter, girth, radius,
    min_degree, max_degree, triangle_count
) VALUES %s
ON CONFLICT (graph6) DO NOTHING
"""


def insert_batch(conn, records: list[GraphRecord]) -> int:
    """
    Insert a batch of graph records into the database.

    Args:
        conn: Database connection
        records: List of GraphRecord objects

    Returns:
        Number of rows inserted
    """
    if not records:
        return 0

    tuples = [r.to_db_tuple() for r in records]

    with conn.cursor() as cur:
        execute_values(cur, INSERT_SQL, tuples)
        inserted = cur.rowcount

    conn.commit()
    return inserted


def count_graphs(conn, n: int | None = None) -> int:
    """Count graphs in the database, optionally filtered by vertex count."""
    with conn.cursor() as cur:
        if n is not None:
            cur.execute("SELECT COUNT(*) FROM graphs WHERE n = %s", (n,))
        else:
            cur.execute("SELECT COUNT(*) FROM graphs")
        return cur.fetchone()[0]


MATRIX_TYPES = ("adj", "lap", "nb", "nbl")


def find_and_store_cospectral_pairs(conn, matrix_type: str) -> int:
    """
    Find all co-spectral pairs for a matrix type and store them.

    Args:
        conn: Database connection
        matrix_type: One of 'adj', 'lap', 'nb', 'nbl'

    Returns:
        Number of pairs inserted
    """
    if matrix_type not in MATRIX_TYPES:
        raise ValueError(f"matrix_type must be one of {MATRIX_TYPES}")

    hash_col = f"{matrix_type}_spectral_hash"

    query = f"""
    INSERT INTO cospectral_pairs (graph1_id, graph2_id, matrix_type)
    SELECT g1.id, g2.id, %s
    FROM graphs g1
    JOIN graphs g2 ON g1.{hash_col} = g2.{hash_col}
    WHERE g1.id < g2.id
    ON CONFLICT (graph1_id, graph2_id, matrix_type) DO NOTHING
    """

    with conn.cursor() as cur:
        cur.execute(query, (matrix_type,))
        inserted = cur.rowcount

    conn.commit()
    return inserted


def find_all_cospectral_pairs(conn) -> dict[str, int]:
    """
    Find and store co-spectral pairs for all matrix types.

    Returns:
        Dict mapping matrix_type to number of pairs found
    """
    results = {}
    for matrix_type in MATRIX_TYPES:
        results[matrix_type] = find_and_store_cospectral_pairs(conn, matrix_type)
    return results


def count_cospectral_pairs(conn, matrix_type: str | None = None) -> int:
    """Count co-spectral pairs, optionally filtered by matrix type."""
    with conn.cursor() as cur:
        if matrix_type:
            cur.execute(
                "SELECT COUNT(*) FROM cospectral_pairs WHERE matrix_type = %s",
                (matrix_type,),
            )
        else:
            cur.execute("SELECT COUNT(*) FROM cospectral_pairs")
        return cur.fetchone()[0]
