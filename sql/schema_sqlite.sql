-- SQLite schema for SMOL database

CREATE TABLE IF NOT EXISTS graphs (
    id                  INTEGER PRIMARY KEY AUTOINCREMENT,
    n                   INTEGER NOT NULL,
    m                   INTEGER NOT NULL,
    graph6              TEXT NOT NULL UNIQUE,

    -- Adjacency spectrum (JSON array)
    adj_eigenvalues     TEXT NOT NULL,
    adj_spectral_hash   TEXT NOT NULL,

    -- Laplacian spectrum (JSON array)
    lap_eigenvalues     TEXT NOT NULL,
    lap_spectral_hash   TEXT NOT NULL,

    -- Non-backtracking spectrum (JSON arrays for complex)
    nb_eigenvalues_re   TEXT NOT NULL,
    nb_eigenvalues_im   TEXT NOT NULL,
    nb_spectral_hash    TEXT NOT NULL,

    -- NB Laplacian spectrum (JSON arrays for complex)
    nbl_eigenvalues_re  TEXT NOT NULL,
    nbl_eigenvalues_im  TEXT NOT NULL,
    nbl_spectral_hash   TEXT NOT NULL,

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
    global_clustering       REAL,
    avg_local_clustering    REAL,
    avg_path_length         REAL,
    assortativity           REAL,
    degree_sequence         TEXT,  -- JSON array
    betweenness_centrality  TEXT,  -- JSON array
    closeness_centrality    TEXT,  -- JSON array
    eigenvector_centrality  TEXT,  -- JSON array

    -- Tags (JSON array, e.g., ["complete", "regular", "eulerian"])
    tags                    TEXT DEFAULT '[]'
);

-- Indexes for common queries
CREATE INDEX IF NOT EXISTS idx_graphs_n ON graphs(n);
CREATE INDEX IF NOT EXISTS idx_graphs_n_m ON graphs(n, m);
CREATE INDEX IF NOT EXISTS idx_graphs_graph6 ON graphs(graph6);
CREATE INDEX IF NOT EXISTS idx_graphs_adj_hash ON graphs(adj_spectral_hash);
CREATE INDEX IF NOT EXISTS idx_graphs_lap_hash ON graphs(lap_spectral_hash);
CREATE INDEX IF NOT EXISTS idx_graphs_nb_hash ON graphs(nb_spectral_hash);
CREATE INDEX IF NOT EXISTS idx_graphs_nbl_hash ON graphs(nbl_spectral_hash);
CREATE INDEX IF NOT EXISTS idx_graphs_bipartite ON graphs(is_bipartite);
CREATE INDEX IF NOT EXISTS idx_graphs_planar ON graphs(is_planar);
CREATE INDEX IF NOT EXISTS idx_graphs_regular ON graphs(is_regular);
CREATE INDEX IF NOT EXISTS idx_graphs_min_degree ON graphs(min_degree);
CREATE INDEX IF NOT EXISTS idx_graphs_diameter ON graphs(diameter);

-- Composite indexes for cospectral mate queries (n + spectral_hash)
CREATE INDEX IF NOT EXISTS idx_n_adj_hash ON graphs(n, adj_spectral_hash);
CREATE INDEX IF NOT EXISTS idx_n_lap_hash ON graphs(n, lap_spectral_hash);
CREATE INDEX IF NOT EXISTS idx_n_nb_hash ON graphs(n, nb_spectral_hash);
CREATE INDEX IF NOT EXISTS idx_n_nbl_hash ON graphs(n, nbl_spectral_hash);

-- Pre-computed cospectral mates table
-- Stores all pairs of graphs that share the same spectrum for a given matrix type.
-- For a cospectral family of k graphs, we store C(k,2) = k*(k-1)/2 pairs.
-- This redundancy is intentional: it enables O(1) lookup of all cospectral mates
-- for any graph, without needing to scan the entire graphs table.
-- Example: family {A, B, C} stores pairs (A,B), (A,C), (B,C).
-- Populated by scripts/compute_cospectral_tables.py
CREATE TABLE IF NOT EXISTS cospectral_mates (
    id          INTEGER PRIMARY KEY AUTOINCREMENT,
    graph1_id   INTEGER NOT NULL REFERENCES graphs(id),
    graph2_id   INTEGER NOT NULL REFERENCES graphs(id),
    matrix_type TEXT NOT NULL CHECK (matrix_type IN ('adj', 'lap', 'nb', 'nbl')),
    UNIQUE (graph1_id, graph2_id, matrix_type),
    CHECK (graph1_id < graph2_id)
);

CREATE INDEX IF NOT EXISTS idx_mates_matrix ON cospectral_mates(matrix_type);
CREATE INDEX IF NOT EXISTS idx_mates_graph1 ON cospectral_mates(graph1_id);
CREATE INDEX IF NOT EXISTS idx_mates_graph2 ON cospectral_mates(graph2_id);

-- Cospectral index table
-- One row per graph that has at least one cospectral mate.
-- Denormalizes n, m, min_degree for instant aggregate queries.
-- Populated by scripts/compute_cospectral_tables.py
CREATE TABLE IF NOT EXISTS cospectral_index (
    graph_id    INTEGER NOT NULL REFERENCES graphs(id),
    n           INTEGER NOT NULL,
    m           INTEGER NOT NULL,
    min_degree  INTEGER NOT NULL,
    matrix_type TEXT NOT NULL CHECK (matrix_type IN ('adj', 'lap', 'nb', 'nbl')),
    PRIMARY KEY (graph_id, matrix_type)
);

CREATE INDEX IF NOT EXISTS idx_cospectral_n ON cospectral_index(matrix_type, n);
CREATE INDEX IF NOT EXISTS idx_cospectral_m ON cospectral_index(matrix_type, m);
CREATE INDEX IF NOT EXISTS idx_cospectral_n_mindeg ON cospectral_index(matrix_type, n, min_degree);
CREATE INDEX IF NOT EXISTS idx_cospectral_m_mindeg ON cospectral_index(matrix_type, m, min_degree);

-- Stats cache table
CREATE TABLE IF NOT EXISTS stats_cache (
    key        TEXT PRIMARY KEY,
    value      TEXT NOT NULL,
    updated_at TEXT DEFAULT (datetime('now'))
);
