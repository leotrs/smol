"""Database operations for the spectral graph database."""

import os

import psycopg2


def get_connection_string() -> str:
    """Get database connection string from environment or use default."""
    return os.environ.get("SMOL_DB_URL", "postgresql://localhost/smol")


def connect():
    """Create a database connection."""
    return psycopg2.connect(get_connection_string())


def init_schema(conn) -> None:
    """Initialize the database schema."""
    schema_path = os.path.join(os.path.dirname(__file__), "..", "sql", "schema.sql")
    with open(schema_path) as f:
        schema_sql = f.read()

    with conn.cursor() as cur:
        cur.execute(schema_sql)
    conn.commit()
