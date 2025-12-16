-- SMOL Graph Database Schema
-- Stores all connected non-isomorphic simple undirected graphs up to n vertices
-- with their spectral properties for four matrix types.

CREATE TABLE IF NOT EXISTS graphs (
    id              BIGSERIAL PRIMARY KEY,

    -- Graph structure
    n               SMALLINT NOT NULL,          -- vertex count
    m               SMALLINT NOT NULL,          -- edge count
    graph6          VARCHAR(32) NOT NULL,       -- canonical graph6 encoding

    -- Adjacency matrix spectrum (real eigenvalues)
    adj_eigenvalues     DOUBLE PRECISION[] NOT NULL,
    adj_spectral_hash   CHAR(16) NOT NULL,

    -- Laplacian spectrum (real eigenvalues)
    lap_eigenvalues     DOUBLE PRECISION[] NOT NULL,
    lap_spectral_hash   CHAR(16) NOT NULL,

    -- Non-backtracking spectrum (complex eigenvalues)
    nb_eigenvalues_re   DOUBLE PRECISION[] NOT NULL,
    nb_eigenvalues_im   DOUBLE PRECISION[] NOT NULL,
    nb_spectral_hash    CHAR(16) NOT NULL,

    -- NB Laplacian spectrum (complex eigenvalues)
    nbl_eigenvalues_re  DOUBLE PRECISION[] NOT NULL,
    nbl_eigenvalues_im  DOUBLE PRECISION[] NOT NULL,
    nbl_spectral_hash   CHAR(16) NOT NULL,

    -- Structural metadata
    is_bipartite        BOOLEAN NOT NULL,
    is_planar           BOOLEAN NOT NULL,
    is_regular          BOOLEAN NOT NULL,
    diameter            SMALLINT NOT NULL,
    girth               SMALLINT,               -- NULL if acyclic (tree)
    radius              SMALLINT NOT NULL,
    min_degree          SMALLINT NOT NULL,
    max_degree          SMALLINT NOT NULL,
    triangle_count      INTEGER NOT NULL,
    clique_number       SMALLINT,               -- expensive, computed later
    chromatic_number    SMALLINT,               -- expensive, computed later

    -- Tags (e.g., 'complete', 'cycle', 'tree', 'petersen', etc.)
    tags                TEXT[] DEFAULT '{}',

    -- Extensible metadata
    extra               JSONB DEFAULT '{}'::jsonb,

    created_at          TIMESTAMP DEFAULT NOW()
);

-- Indexes for filtering by structure
CREATE INDEX IF NOT EXISTS idx_graphs_n ON graphs(n);
CREATE INDEX IF NOT EXISTS idx_graphs_n_m ON graphs(n, m);
CREATE INDEX IF NOT EXISTS idx_graphs_bipartite ON graphs(is_bipartite);
CREATE INDEX IF NOT EXISTS idx_graphs_planar ON graphs(is_planar);
CREATE INDEX IF NOT EXISTS idx_graphs_regular ON graphs(is_regular);
CREATE INDEX IF NOT EXISTS idx_graphs_diameter ON graphs(diameter);
CREATE INDEX IF NOT EXISTS idx_graphs_girth ON graphs(girth) WHERE girth IS NOT NULL;

-- Indexes for co-spectral queries
CREATE INDEX IF NOT EXISTS idx_adj_hash ON graphs(adj_spectral_hash);
CREATE INDEX IF NOT EXISTS idx_lap_hash ON graphs(lap_spectral_hash);
CREATE INDEX IF NOT EXISTS idx_nb_hash ON graphs(nb_spectral_hash);
CREATE INDEX IF NOT EXISTS idx_nbl_hash ON graphs(nbl_spectral_hash);

-- Composite indexes for cospectral mate queries (n + spectral_hash)
CREATE INDEX IF NOT EXISTS idx_n_adj_hash ON graphs(n, adj_spectral_hash);
CREATE INDEX IF NOT EXISTS idx_n_lap_hash ON graphs(n, lap_spectral_hash);
CREATE INDEX IF NOT EXISTS idx_n_nb_hash ON graphs(n, nb_spectral_hash);
CREATE INDEX IF NOT EXISTS idx_n_nbl_hash ON graphs(n, nbl_spectral_hash);

-- Composite indexes for "same X spectrum, different Y spectrum" queries
CREATE INDEX IF NOT EXISTS idx_adj_nb_hash ON graphs(adj_spectral_hash, nb_spectral_hash);
CREATE INDEX IF NOT EXISTS idx_adj_lap_hash ON graphs(adj_spectral_hash, lap_spectral_hash);

-- Unique constraint on graph6
CREATE UNIQUE INDEX IF NOT EXISTS idx_graph6 ON graphs(graph6);

-- GIN index on extra JSONB
CREATE INDEX IF NOT EXISTS idx_extra ON graphs USING GIN(extra);

-- GIN index on tags for array containment queries
CREATE INDEX IF NOT EXISTS idx_tags ON graphs USING GIN(tags);

-- Pre-computed cospectral pairs table
-- Stores all pairs of graphs that share the same spectrum for a given matrix type.
-- For a cospectral family of k graphs, we store C(k,2) = k*(k-1)/2 pairs.
-- This redundancy is intentional: it enables O(1) lookup of all cospectral mates
-- for any graph, without needing to scan the entire graphs table.
-- Example: family {A, B, C} stores pairs (A,B), (A,C), (B,C).
-- Populated by scripts/compute_cospectral_pairs.py
CREATE TABLE IF NOT EXISTS cospectral_pairs (
    id              BIGSERIAL PRIMARY KEY,
    graph1_id       BIGINT NOT NULL REFERENCES graphs(id),
    graph2_id       BIGINT NOT NULL REFERENCES graphs(id),
    matrix_type     VARCHAR(3) NOT NULL CHECK (matrix_type IN ('adj', 'lap', 'nb', 'nbl')),

    CONSTRAINT graph_order CHECK (graph1_id < graph2_id),
    UNIQUE (graph1_id, graph2_id, matrix_type)
);

CREATE INDEX IF NOT EXISTS idx_cospectral_matrix ON cospectral_pairs(matrix_type);
CREATE INDEX IF NOT EXISTS idx_cospectral_graph1 ON cospectral_pairs(graph1_id);
CREATE INDEX IF NOT EXISTS idx_cospectral_graph2 ON cospectral_pairs(graph2_id);

-- Stats cache table
CREATE TABLE IF NOT EXISTS stats_cache (
    key             VARCHAR(64) PRIMARY KEY,
    value           JSONB NOT NULL,
    updated_at      TIMESTAMP DEFAULT NOW()
);
