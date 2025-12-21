#!/usr/bin/env python3
"""Simple non-parallel version to compute Kirchhoff and Signless."""

import os
import sys
import time
import psycopg2
from psycopg2.extras import execute_values
import networkx as nx
import numpy as np

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from db.spectrum import compute_real_eigenvalues, spectral_hash_real

DATABASE_URL = os.environ.get("DATABASE_URL", "dbname=smol")

def compute_both(G):
    """Compute both Kirchhoff and Signless efficiently (shared A and D computation)."""
    # Compute adjacency matrix once
    A = nx.to_numpy_array(G, dtype=np.float64)
    degrees = A.sum(axis=1)
    D = np.diag(degrees)

    # Kirchhoff: L = D - A
    L_k = D - A
    k_eigs = compute_real_eigenvalues(L_k)
    k_hash = spectral_hash_real(k_eigs)

    # Signless: Q = D + A
    Q_s = D + A
    s_eigs = compute_real_eigenvalues(Q_s)
    s_hash = spectral_hash_real(s_eigs)

    return k_eigs.tolist(), k_hash, s_eigs.tolist(), s_hash

# Separate connections for reading and writing
read_conn = psycopg2.connect(DATABASE_URL)
write_conn = psycopg2.connect(DATABASE_URL)

cur = read_conn.cursor('fetch_missing')
cur.itersize = 1000

print("Fetching graphs...", flush=True)
cur.execute("""
    SELECT id, graph6
    FROM graphs
    WHERE kirchhoff_eigenvalues IS NULL OR signless_eigenvalues IS NULL
    ORDER BY n, id
""")

print("Processing...", flush=True)
count = 0
start = time.time()
batch = []
batch_size = 1000

for graph_id, graph6 in cur:
    G = nx.from_graph6_bytes(graph6.encode())
    k_eigs, k_hash, s_eigs, s_hash = compute_both(G)

    batch.append((k_eigs, k_hash, s_eigs, s_hash, graph_id))
    count += 1

    if len(batch) >= batch_size:
        # Batch update using separate connection
        cur2 = write_conn.cursor()
        execute_values(
            cur2,
            """
            UPDATE graphs AS g SET
                kirchhoff_eigenvalues = v.k_eigs,
                kirchhoff_spectral_hash = v.k_hash,
                signless_eigenvalues = v.s_eigs,
                signless_spectral_hash = v.s_hash
            FROM (VALUES %s) AS v(k_eigs, k_hash, s_eigs, s_hash, id)
            WHERE g.id = v.id
            """,
            batch
        )
        cur2.close()
        write_conn.commit()
        batch = []

        elapsed = time.time() - start
        rate = count / elapsed
        print(f"  {count:,} - {rate:.0f}/sec", flush=True)

# Final batch
if batch:
    cur2 = write_conn.cursor()
    execute_values(
        cur2,
        """
        UPDATE graphs AS g SET
            kirchhoff_eigenvalues = v.k_eigs,
            kirchhoff_spectral_hash = v.k_hash,
            signless_eigenvalues = v.s_eigs,
            signless_spectral_hash = v.s_hash
        FROM (VALUES %s) AS v(k_eigs, k_hash, s_eigs, s_hash, id)
        WHERE g.id = v.id
        """,
        batch
    )
    cur2.close()
    write_conn.commit()

read_conn.close()
write_conn.close()

elapsed = time.time() - start
print(f"Done! {count:,} graphs in {elapsed/60:.1f}m ({count/elapsed:.0f}/sec)", flush=True)
