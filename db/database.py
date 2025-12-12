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


def get_cospectral_pairs(
    conn, matrix_type: str = "adj", limit: int = 100
) -> list[tuple[int, int, str]]:
    """
    Find co-spectral pairs for a given matrix type.

    Args:
        conn: Database connection
        matrix_type: One of 'adj', 'lap', 'nb', 'nbl'
        limit: Maximum number of pairs to return

    Returns:
        List of (graph1_id, graph2_id, spectral_hash) tuples
    """
    hash_col = f"{matrix_type}_spectral_hash"

    query = f"""
    SELECT g1.id, g2.id, g1.{hash_col}
    FROM graphs g1
    JOIN graphs g2 ON g1.{hash_col} = g2.{hash_col}
    WHERE g1.id < g2.id
    LIMIT %s
    """

    with conn.cursor() as cur:
        cur.execute(query, (limit,))
        return cur.fetchall()
