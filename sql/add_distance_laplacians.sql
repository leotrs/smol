-- Add distance Laplacian and distance signless Laplacian spectrum columns.
-- D_L = Tr - Dist and D_Q = Tr + Dist (Tr = transmission diagonal). Both are
-- real symmetric and only defined for connected graphs, so columns are nullable.

ALTER TABLE graphs
ADD COLUMN IF NOT EXISTS distlap_eigenvalues DOUBLE PRECISION[],
ADD COLUMN IF NOT EXISTS distlap_spectral_hash CHAR(16),
ADD COLUMN IF NOT EXISTS distsign_eigenvalues DOUBLE PRECISION[],
ADD COLUMN IF NOT EXISTS distsign_spectral_hash CHAR(16);

CREATE INDEX IF NOT EXISTS idx_distlap_hash ON graphs(distlap_spectral_hash) WHERE distlap_spectral_hash IS NOT NULL;
CREATE INDEX IF NOT EXISTS idx_n_distlap_hash ON graphs(n, distlap_spectral_hash) WHERE distlap_spectral_hash IS NOT NULL;
CREATE INDEX IF NOT EXISTS idx_distsign_hash ON graphs(distsign_spectral_hash) WHERE distsign_spectral_hash IS NOT NULL;
CREATE INDEX IF NOT EXISTS idx_n_distsign_hash ON graphs(n, distsign_spectral_hash) WHERE distsign_spectral_hash IS NOT NULL;

ALTER TABLE cospectral_mates DROP CONSTRAINT IF EXISTS cospectral_mates_matrix_type_check;
ALTER TABLE cospectral_mates ADD CONSTRAINT cospectral_mates_matrix_type_check
    CHECK (matrix_type IN ('adj', 'kirchhoff', 'signless', 'lap', 'nb', 'nbl', 'dist', 'seidel', 'distlap', 'distsign'));
