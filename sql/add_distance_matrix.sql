-- Add distance matrix spectrum columns
-- Distance matrix is only defined for connected graphs, so these are nullable

ALTER TABLE graphs
ADD COLUMN IF NOT EXISTS dist_eigenvalues DOUBLE PRECISION[],
ADD COLUMN IF NOT EXISTS dist_spectral_hash CHAR(16);

-- Index for cospectral queries
CREATE INDEX IF NOT EXISTS idx_dist_hash ON graphs(dist_spectral_hash) WHERE dist_spectral_hash IS NOT NULL;

-- Composite index for n + spectral hash
CREATE INDEX IF NOT EXISTS idx_n_dist_hash ON graphs(n, dist_spectral_hash) WHERE dist_spectral_hash IS NOT NULL;

-- Composite index for comparing distance vs adjacency cospectrality
CREATE INDEX IF NOT EXISTS idx_adj_dist_hash ON graphs(adj_spectral_hash, dist_spectral_hash) WHERE dist_spectral_hash IS NOT NULL;

-- Update cospectral_mates table to allow 'dist' matrix type
-- First drop the old constraint, then add the new one
ALTER TABLE cospectral_mates DROP CONSTRAINT IF EXISTS cospectral_mates_matrix_type_check;
ALTER TABLE cospectral_mates ADD CONSTRAINT cospectral_mates_matrix_type_check
    CHECK (matrix_type IN ('adj', 'kirchhoff', 'signless', 'lap', 'nb', 'nbl', 'dist'));
