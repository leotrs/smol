-- SMOL Graph Database Schema
-- Stores all connected non-isomorphic simple undirected graphs up to n vertices
-- with their spectral properties for seven matrix types.

CREATE TABLE IF NOT EXISTS graphs (
    id              BIGSERIAL PRIMARY KEY,

    -- Graph structure
    n               SMALLINT NOT NULL,          -- vertex count
    m               SMALLINT NOT NULL,          -- edge count
    graph6          VARCHAR(32) NOT NULL,       -- canonical graph6 encoding

    -- Adjacency matrix spectrum (real eigenvalues)
    adj_eigenvalues         DOUBLE PRECISION[],
    adj_spectral_hash       CHAR(16) NOT NULL,

    -- Kirchhoff (combinatorial) Laplacian spectrum (real eigenvalues)
    kirchhoff_eigenvalues   DOUBLE PRECISION[],
    kirchhoff_spectral_hash CHAR(16) NOT NULL,

    -- Signless Laplacian spectrum (real eigenvalues)
    signless_eigenvalues    DOUBLE PRECISION[],
    signless_spectral_hash  CHAR(16) NOT NULL,

    -- Normalized Laplacian spectrum (real eigenvalues)
    lap_eigenvalues         DOUBLE PRECISION[],
    lap_spectral_hash       CHAR(16) NOT NULL,

    -- Non-backtracking spectrum (complex eigenvalues)
    nb_eigenvalues_re   DOUBLE PRECISION[],
    nb_eigenvalues_im   DOUBLE PRECISION[],
    nb_spectral_hash    CHAR(16) NOT NULL,

    -- NB Laplacian spectrum (complex eigenvalues)
    nbl_eigenvalues_re  DOUBLE PRECISION[],
    nbl_eigenvalues_im  DOUBLE PRECISION[],
    nbl_spectral_hash   CHAR(16) NOT NULL,

    -- Structural metadata
    is_bipartite        BOOLEAN NOT NULL,
    is_planar           BOOLEAN NOT NULL,
    is_regular          BOOLEAN NOT NULL,
    diameter            SMALLINT,               -- NULL if disconnected
    girth               SMALLINT,               -- NULL if acyclic (tree)
    radius              SMALLINT,               -- NULL if disconnected
    min_degree          SMALLINT NOT NULL,
    max_degree          SMALLINT NOT NULL,
    triangle_count      INTEGER NOT NULL,
    clique_number       SMALLINT,               -- expensive, computed later
    chromatic_number    SMALLINT,               -- expensive, computed later

    -- Network science properties
    algebraic_connectivity  DOUBLE PRECISION,
    global_clustering       DOUBLE PRECISION,
    avg_local_clustering    DOUBLE PRECISION,
    avg_path_length         DOUBLE PRECISION,
    assortativity           DOUBLE PRECISION,

    -- Tags (e.g., 'complete', 'cycle', 'tree', 'petersen', etc.)
    -- NULL = not computed, '{}' = computed but no tags, array = tags found
    tags                TEXT[] DEFAULT NULL,

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
CREATE INDEX IF NOT EXISTS idx_kirchhoff_hash ON graphs(kirchhoff_spectral_hash);
CREATE INDEX IF NOT EXISTS idx_signless_hash ON graphs(signless_spectral_hash);
CREATE INDEX IF NOT EXISTS idx_lap_hash ON graphs(lap_spectral_hash);
CREATE INDEX IF NOT EXISTS idx_nb_hash ON graphs(nb_spectral_hash);
CREATE INDEX IF NOT EXISTS idx_nbl_hash ON graphs(nbl_spectral_hash);

-- Composite indexes for cospectral mate queries (n + spectral_hash)
CREATE INDEX IF NOT EXISTS idx_n_adj_hash ON graphs(n, adj_spectral_hash);
CREATE INDEX IF NOT EXISTS idx_n_kirchhoff_hash ON graphs(n, kirchhoff_spectral_hash);
CREATE INDEX IF NOT EXISTS idx_n_signless_hash ON graphs(n, signless_spectral_hash);
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

-- Pre-computed cospectral mates table
-- One row per cospectral family (a set of graphs sharing a spectrum for a given
-- matrix type), instead of one row per pair. The pair-based design stored
-- C(k,2) rows per family, which exploded for weak discriminators (e.g. ecc has
-- families of 8000+ graphs). A family is identified by (matrix_type, n, hash);
-- its members are recovered with an indexed lookup on graphs.<matrix>_spectral_hash.
-- Only families of size >= 2 are stored. Populated by scripts/compute_cospectral_tables.py
CREATE TABLE IF NOT EXISTS cospectral_families (
    matrix_type     VARCHAR(20) NOT NULL,
    n               SMALLINT NOT NULL,
    spectral_hash   CHAR(16) NOT NULL,
    family_size     INTEGER NOT NULL CHECK (family_size >= 2),

    PRIMARY KEY (matrix_type, n, spectral_hash)
);

CREATE INDEX IF NOT EXISTS idx_families_matrix_n ON cospectral_families(matrix_type, n);

-- Stats cache table
CREATE TABLE IF NOT EXISTS stats_cache (
    key             VARCHAR(64) PRIMARY KEY,
    value           JSONB NOT NULL,
    updated_at      TIMESTAMP DEFAULT NOW()
);
