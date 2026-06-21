-- SQLite schema for SMOL database

-- Eigenvalue arrays are not stored: the API computes them on demand from
-- graph6 (and serves them lazily to the viz). Only the per-matrix spectral
-- hashes are kept, which is all cospectrality needs.
CREATE TABLE IF NOT EXISTS graphs (
    id                  INTEGER PRIMARY KEY AUTOINCREMENT,
    n                   INTEGER NOT NULL,
    m                   INTEGER NOT NULL,
    graph6              TEXT NOT NULL UNIQUE,

    adj_spectral_hash       TEXT NOT NULL,
    kirchhoff_spectral_hash TEXT NOT NULL,
    signless_spectral_hash  TEXT NOT NULL,
    lap_spectral_hash       TEXT NOT NULL,
    nb_spectral_hash        TEXT,
    nbl_spectral_hash       TEXT,

    -- Distance-based spectra: hash is NULL for disconnected graphs
    dist_spectral_hash      TEXT,
    distlap_spectral_hash   TEXT,
    distsign_spectral_hash  TEXT,
    distnorm_spectral_hash  TEXT,
    ecc_spectral_hash       TEXT,

    -- k-blocking family: composite hash over {M_k : k=2..Delta} (NULL for forests)
    kblock_family_spectral_hash TEXT,

    -- Yoon m-Laplacian hashes (NULL when n <= m)
    yoon2_spectral_hash TEXT,
    yoon3_spectral_hash TEXT,

    -- Non-k-cycling hashes (NULL when nilpotent)
    non3cyc_spectral_hash  TEXT,
    non4cyc_spectral_hash  TEXT,

    -- Structural properties
    is_bipartite        INTEGER NOT NULL,  -- 0/1 boolean
    is_planar           INTEGER NOT NULL,
    is_regular          INTEGER NOT NULL,
    diameter            INTEGER,  -- NULL if disconnected
    radius              INTEGER,  -- NULL if disconnected
    girth               INTEGER,  -- NULL if acyclic
    min_degree          INTEGER NOT NULL,
    max_degree          INTEGER NOT NULL,
    triangle_count      INTEGER NOT NULL,
    clique_number       INTEGER,
    chromatic_number    INTEGER,

    -- Network science properties
    algebraic_connectivity  REAL,
    clustering_coefficient  REAL,  -- Legacy column (duplicates global_clustering)
    assortativity           REAL,
    global_clustering       REAL,
    avg_local_clustering    REAL,
    avg_path_length         REAL,

    -- Tags (JSON array, e.g., ["complete", "regular", "eulerian"])
    tags                    TEXT DEFAULT '[]',

    -- Extra data (JSON object for future extensions)
    extra                   TEXT DEFAULT '{}',

    -- Timestamp
    created_at              TEXT
);

-- Structural-filter indexes (graph6 is already uniquely indexed by its UNIQUE
-- constraint, so no separate index is needed).
CREATE INDEX IF NOT EXISTS idx_graphs_n ON graphs(n);
CREATE INDEX IF NOT EXISTS idx_graphs_n_m ON graphs(n, m);
CREATE INDEX IF NOT EXISTS idx_graphs_bipartite ON graphs(is_bipartite);
CREATE INDEX IF NOT EXISTS idx_graphs_planar ON graphs(is_planar);
CREATE INDEX IF NOT EXISTS idx_graphs_regular ON graphs(is_regular);
CREATE INDEX IF NOT EXISTS idx_graphs_min_degree ON graphs(min_degree);
CREATE INDEX IF NOT EXISTS idx_graphs_diameter ON graphs(diameter);
CREATE INDEX IF NOT EXISTS idx_graphs_girth ON graphs(girth);

-- Cospectral-mate derivation: (n, hash) per matrix. The bare single-column hash
-- indexes are omitted because every mate query scopes by n, making these a
-- covering superset.
CREATE INDEX IF NOT EXISTS idx_n_adj_hash ON graphs(n, adj_spectral_hash);
CREATE INDEX IF NOT EXISTS idx_n_kirchhoff_hash ON graphs(n, kirchhoff_spectral_hash);
CREATE INDEX IF NOT EXISTS idx_n_signless_hash ON graphs(n, signless_spectral_hash);
CREATE INDEX IF NOT EXISTS idx_n_lap_hash ON graphs(n, lap_spectral_hash);
CREATE INDEX IF NOT EXISTS idx_n_nb_hash ON graphs(n, nb_spectral_hash);
CREATE INDEX IF NOT EXISTS idx_n_nbl_hash ON graphs(n, nbl_spectral_hash);
CREATE INDEX IF NOT EXISTS idx_n_dist_hash ON graphs(n, dist_spectral_hash);
CREATE INDEX IF NOT EXISTS idx_n_distlap_hash ON graphs(n, distlap_spectral_hash);
CREATE INDEX IF NOT EXISTS idx_n_distsign_hash ON graphs(n, distsign_spectral_hash);
CREATE INDEX IF NOT EXISTS idx_n_distnorm_hash ON graphs(n, distnorm_spectral_hash);
CREATE INDEX IF NOT EXISTS idx_n_ecc_hash ON graphs(n, ecc_spectral_hash);
CREATE INDEX IF NOT EXISTS idx_n_kblock_family_hash ON graphs(n, kblock_family_spectral_hash);
CREATE INDEX IF NOT EXISTS idx_n_yoon2_hash ON graphs(n, yoon2_spectral_hash);
CREATE INDEX IF NOT EXISTS idx_n_yoon3_hash ON graphs(n, yoon3_spectral_hash);
CREATE INDEX IF NOT EXISTS idx_n_non3cyc_hash ON graphs(n, non3cyc_spectral_hash);
CREATE INDEX IF NOT EXISTS idx_n_non4cyc_hash ON graphs(n, non4cyc_spectral_hash);

-- Pre-computed cospectral families table
-- One row per cospectral family (graphs sharing a spectrum for a matrix type),
-- replacing the old per-pair table which stored C(k,2) rows per family and
-- exploded for weak discriminators (ecc has families of 8000+ graphs). Members
-- are recovered with an indexed lookup on graphs.<matrix>_spectral_hash. Only
-- families of size >= 2 are stored. Populated by scripts/compute_cospectral_tables.py
CREATE TABLE IF NOT EXISTS cospectral_families (
    matrix_type   TEXT NOT NULL,
    n             INTEGER NOT NULL,
    spectral_hash TEXT NOT NULL,
    family_size   INTEGER NOT NULL CHECK (family_size >= 2),
    PRIMARY KEY (matrix_type, n, spectral_hash)
);

CREATE INDEX IF NOT EXISTS idx_families_matrix_n ON cospectral_families(matrix_type, n);

-- Switching mechanisms table
-- Stores detected switching mechanisms (like GM switching) that explain
-- why two graphs are cospectral for a particular matrix type.
-- Populated by scripts/populate_mechanisms.py
CREATE TABLE IF NOT EXISTS switching_mechanisms (
    graph1_id       INTEGER NOT NULL REFERENCES graphs(id) ON DELETE CASCADE,
    graph2_id       INTEGER NOT NULL REFERENCES graphs(id) ON DELETE CASCADE,
    matrix_type     TEXT NOT NULL,
    mechanism_type  TEXT NOT NULL,
    config          TEXT NOT NULL,  -- JSON
    detected_at     TEXT DEFAULT (datetime('now')),
    PRIMARY KEY (graph1_id, graph2_id, matrix_type, mechanism_type),
    CHECK (graph1_id < graph2_id)
);

CREATE INDEX IF NOT EXISTS idx_mechanisms_graph1 ON switching_mechanisms(graph1_id);
CREATE INDEX IF NOT EXISTS idx_mechanisms_graph2 ON switching_mechanisms(graph2_id);
CREATE INDEX IF NOT EXISTS idx_mechanisms_matrix ON switching_mechanisms(matrix_type);
CREATE INDEX IF NOT EXISTS idx_mechanisms_type ON switching_mechanisms(mechanism_type);

-- Stats cache table
CREATE TABLE IF NOT EXISTS stats_cache (
    key        TEXT PRIMARY KEY,
    value      TEXT NOT NULL,
    updated_at TEXT DEFAULT (datetime('now'))
);
