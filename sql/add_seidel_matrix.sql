-- Add Seidel matrix spectrum columns
-- Seidel matrix S = J - I - 2A is real symmetric and defined for all graphs.

ALTER TABLE graphs
ADD COLUMN IF NOT EXISTS seidel_eigenvalues DOUBLE PRECISION[],
ADD COLUMN IF NOT EXISTS seidel_spectral_hash CHAR(16);

-- Indexes for cospectral queries
CREATE INDEX IF NOT EXISTS idx_seidel_hash ON graphs(seidel_spectral_hash) WHERE seidel_spectral_hash IS NOT NULL;
CREATE INDEX IF NOT EXISTS idx_n_seidel_hash ON graphs(n, seidel_spectral_hash) WHERE seidel_spectral_hash IS NOT NULL;

-- Allow 'seidel' in the cospectral_mates matrix_type constraint
ALTER TABLE cospectral_mates DROP CONSTRAINT IF EXISTS cospectral_mates_matrix_type_check;
ALTER TABLE cospectral_mates ADD CONSTRAINT cospectral_mates_matrix_type_check
    CHECK (matrix_type IN ('adj', 'kirchhoff', 'signless', 'lap', 'nb', 'nbl', 'dist', 'seidel'));
