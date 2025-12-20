#!/usr/bin/env python3
"""Deploy a subset of graphs to Fly.io.

Exports specific graphs from local PostgreSQL to SQLite, uploads to Fly.io,
and merges into the existing database.

Usage:
    python scripts/deploy_subset.py --graph6-file /tmp/nbl_cospectral_156.txt
"""

import argparse
import json
import sqlite3
import subprocess
import sys
from pathlib import Path

import psycopg2


COLUMNS = [
    "n", "m", "graph6",
    "adj_eigenvalues", "adj_spectral_hash",
    "lap_eigenvalues", "lap_spectral_hash",
    "nb_eigenvalues_re", "nb_eigenvalues_im", "nb_spectral_hash",
    "nbl_eigenvalues_re", "nbl_eigenvalues_im", "nbl_spectral_hash",
    "is_bipartite", "is_planar", "is_regular",
    "diameter", "radius", "girth",
    "min_degree", "max_degree", "triangle_count",
    "clique_number", "chromatic_number",
    "algebraic_connectivity", "clustering_coefficient", "assortativity",
    "global_clustering", "avg_local_clustering", "avg_path_length",
    "tags", "extra",
]


def get_graphs_from_postgres(graph6_list: list[str]) -> list[dict]:
    """Fetch graph data from PostgreSQL."""
    conn = psycopg2.connect("dbname=smol")

    placeholders = ",".join(["%s"] * len(graph6_list))
    query = f"SELECT {', '.join(COLUMNS)} FROM graphs WHERE graph6 IN ({placeholders})"

    with conn.cursor() as cur:
        cur.execute(query, graph6_list)
        rows = cur.fetchall()

    conn.close()
    return [dict(zip(COLUMNS, row)) for row in rows]


def array_to_text(arr) -> str | None:
    """Convert PostgreSQL array to SQLite-compatible JSON array."""
    if arr is None:
        return None
    return json.dumps(list(arr))


def create_sqlite_export(graphs: list[dict], output_path: Path) -> None:
    """Create SQLite file with the graphs."""
    conn = sqlite3.connect(output_path)
    cur = conn.cursor()

    cur.execute("""
        CREATE TABLE IF NOT EXISTS graphs_import (
            n INTEGER NOT NULL,
            m INTEGER NOT NULL,
            graph6 TEXT NOT NULL PRIMARY KEY,
            adj_eigenvalues TEXT NOT NULL,
            adj_spectral_hash TEXT NOT NULL,
            lap_eigenvalues TEXT NOT NULL,
            lap_spectral_hash TEXT NOT NULL,
            nb_eigenvalues_re TEXT NOT NULL,
            nb_eigenvalues_im TEXT NOT NULL,
            nb_spectral_hash TEXT NOT NULL,
            nbl_eigenvalues_re TEXT NOT NULL,
            nbl_eigenvalues_im TEXT NOT NULL,
            nbl_spectral_hash TEXT NOT NULL,
            is_bipartite INTEGER NOT NULL,
            is_planar INTEGER NOT NULL,
            is_regular INTEGER NOT NULL,
            diameter INTEGER,
            radius INTEGER,
            girth INTEGER,
            min_degree INTEGER NOT NULL,
            max_degree INTEGER NOT NULL,
            triangle_count INTEGER NOT NULL,
            clique_number INTEGER,
            chromatic_number INTEGER,
            algebraic_connectivity REAL,
            clustering_coefficient REAL,
            assortativity REAL,
            global_clustering REAL,
            avg_local_clustering REAL,
            avg_path_length REAL,
            tags TEXT DEFAULT '[]',
            extra TEXT DEFAULT '{}'
        )
    """)

    for g in graphs:
        cur.execute("""
            INSERT INTO graphs_import (
                n, m, graph6,
                adj_eigenvalues, adj_spectral_hash,
                lap_eigenvalues, lap_spectral_hash,
                nb_eigenvalues_re, nb_eigenvalues_im, nb_spectral_hash,
                nbl_eigenvalues_re, nbl_eigenvalues_im, nbl_spectral_hash,
                is_bipartite, is_planar, is_regular,
                diameter, radius, girth,
                min_degree, max_degree, triangle_count,
                clique_number, chromatic_number,
                algebraic_connectivity, clustering_coefficient, assortativity,
                global_clustering, avg_local_clustering, avg_path_length,
                tags, extra
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            g["n"], g["m"], g["graph6"],
            array_to_text(g["adj_eigenvalues"]), g["adj_spectral_hash"],
            array_to_text(g["lap_eigenvalues"]), g["lap_spectral_hash"],
            array_to_text(g["nb_eigenvalues_re"]), array_to_text(g["nb_eigenvalues_im"]), g["nb_spectral_hash"],
            array_to_text(g["nbl_eigenvalues_re"]), array_to_text(g["nbl_eigenvalues_im"]), g["nbl_spectral_hash"],
            int(g["is_bipartite"]), int(g["is_planar"]), int(g["is_regular"]),
            g["diameter"], g["radius"], g["girth"],
            g["min_degree"], g["max_degree"], g["triangle_count"],
            g["clique_number"], g["chromatic_number"],
            g["algebraic_connectivity"], g["clustering_coefficient"], g["assortativity"],
            g["global_clustering"], g["avg_local_clustering"], g["avg_path_length"],
            array_to_text(g["tags"]) if g["tags"] else "[]",
            json.dumps(g["extra"]) if g["extra"] else "{}"
        ))

    conn.commit()
    conn.close()


def upload_and_merge(sqlite_path: Path) -> None:
    """Upload SQLite file to Fly.io and merge into existing database."""
    remote_import_path = "/data/import.db"

    print("Uploading to Fly.io...")
    sftp_commands = f"put {sqlite_path} {remote_import_path}\n"
    result = subprocess.run(
        ["fly", "sftp", "shell"],
        input=sftp_commands,
        capture_output=True,
        text=True,
    )
    if result.returncode != 0:
        print(f"Upload failed: {result.stderr}")
        sys.exit(1)

    print("Merging into existing database...")

    # Write Python script to temp file and upload
    python_script = '''
import sqlite3

conn = sqlite3.connect("/data/smol.db")
conn.execute("ATTACH DATABASE '/data/import.db' AS import_db")

before = conn.execute("SELECT COUNT(*) FROM graphs WHERE n=10").fetchone()[0]
print("n=10 graphs before:", before)

result = conn.execute("""
    INSERT OR IGNORE INTO graphs (
        n, m, graph6,
        adj_eigenvalues, adj_spectral_hash,
        lap_eigenvalues, lap_spectral_hash,
        nb_eigenvalues_re, nb_eigenvalues_im, nb_spectral_hash,
        nbl_eigenvalues_re, nbl_eigenvalues_im, nbl_spectral_hash,
        is_bipartite, is_planar, is_regular,
        diameter, radius, girth,
        min_degree, max_degree, triangle_count,
        clique_number, chromatic_number,
        algebraic_connectivity, clustering_coefficient, assortativity,
        global_clustering, avg_local_clustering, avg_path_length,
        tags, extra
    )
    SELECT
        n, m, graph6,
        adj_eigenvalues, adj_spectral_hash,
        lap_eigenvalues, lap_spectral_hash,
        nb_eigenvalues_re, nb_eigenvalues_im, nb_spectral_hash,
        nbl_eigenvalues_re, nbl_eigenvalues_im, nbl_spectral_hash,
        is_bipartite, is_planar, is_regular,
        diameter, radius, girth,
        min_degree, max_degree, triangle_count,
        clique_number, chromatic_number,
        algebraic_connectivity, clustering_coefficient, assortativity,
        global_clustering, avg_local_clustering, avg_path_length,
        tags, extra
    FROM import_db.graphs_import
""")
inserted = conn.total_changes
print("Inserted:", inserted, "graphs")

conn.execute("""
    CREATE TEMP TABLE new_ids AS
    SELECT g.id, g.adj_spectral_hash, g.lap_spectral_hash, g.nb_spectral_hash, g.nbl_spectral_hash
    FROM graphs g
    WHERE g.graph6 IN (SELECT graph6 FROM import_db.graphs_import)
""")

for matrix in ["adj", "lap", "nb", "nbl"]:
    hash_col = matrix + "_spectral_hash"
    conn.execute("""
        INSERT OR IGNORE INTO cospectral_mates (graph1_id, graph2_id, matrix_type)
        SELECT DISTINCT
            MIN(n.id, g2.id), MAX(n.id, g2.id), ?
        FROM new_ids n
        JOIN graphs g2 ON n.""" + hash_col + """ = g2.""" + hash_col + """ AND n.id != g2.id
    """, (matrix,))

conn.commit()
print("Cospectral mates updated")

after = conn.execute("SELECT COUNT(*) FROM graphs WHERE n=10").fetchone()[0]
mates = conn.execute("SELECT COUNT(*) FROM cospectral_mates WHERE matrix_type='nbl' AND graph1_id IN (SELECT id FROM graphs WHERE n=10)").fetchone()[0]
print("n=10 graphs after:", after)
print("NBL mates for n=10:", mates)

conn.execute("DROP TABLE new_ids")
conn.execute("DETACH DATABASE import_db")
conn.close()

import os
os.remove("/data/import.db")
print("Done!")
'''

    # Upload script
    script_path = Path("/tmp/merge_script.py")
    script_path.write_text(python_script)
    sftp_commands = f"put {script_path} /data/merge_script.py\n"
    subprocess.run(["fly", "sftp", "shell"], input=sftp_commands, capture_output=True, text=True)

    result = subprocess.run(
        ["fly", "ssh", "console", "-C", "python3 /data/merge_script.py && rm /data/merge_script.py"],
        capture_output=True,
        text=True,
    )
    print(result.stdout)
    if result.stderr:
        print(f"Stderr: {result.stderr}")


def main():
    parser = argparse.ArgumentParser(description="Deploy subset of graphs to Fly.io")
    parser.add_argument("--graph6-file", type=str, required=True,
                        help="File with graph6 strings (one per line)")
    args = parser.parse_args()

    graph6_list = Path(args.graph6_file).read_text().strip().split("\n")
    print(f"Loading {len(graph6_list)} graphs from PostgreSQL...")

    graphs = get_graphs_from_postgres(graph6_list)
    print(f"  Found {len(graphs)} graphs")

    if len(graphs) != len(graph6_list):
        missing = set(graph6_list) - {g["graph6"] for g in graphs}
        print(f"  Warning: {len(missing)} graphs not found")
        for m in list(missing)[:5]:
            print(f"    Missing: {repr(m)}")

    sqlite_path = Path("/tmp/graphs_subset.db")
    print(f"Creating SQLite export at {sqlite_path}...")
    create_sqlite_export(graphs, sqlite_path)
    print(f"  Size: {sqlite_path.stat().st_size / 1024:.1f} KB")

    upload_and_merge(sqlite_path)
    sqlite_path.unlink()
    print("\nDeployment complete!")


if __name__ == "__main__":
    main()
