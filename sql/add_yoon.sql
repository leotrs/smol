-- Add Yoon m-Laplacian spectrum columns (m=2, m=3).
-- L^(m)_G is the Laplacian of a reweighted (signed) graph; real symmetric.
-- Only defined for n > m, so columns are nullable (NULL for n <= m).

ALTER TABLE graphs
ADD COLUMN IF NOT EXISTS yoon2_eigenvalues DOUBLE PRECISION[],
ADD COLUMN IF NOT EXISTS yoon2_spectral_hash CHAR(16),
ADD COLUMN IF NOT EXISTS yoon3_eigenvalues DOUBLE PRECISION[],
ADD COLUMN IF NOT EXISTS yoon3_spectral_hash CHAR(16);

CREATE INDEX IF NOT EXISTS idx_yoon2_hash ON graphs(yoon2_spectral_hash) WHERE yoon2_spectral_hash IS NOT NULL;
CREATE INDEX IF NOT EXISTS idx_n_yoon2_hash ON graphs(n, yoon2_spectral_hash) WHERE yoon2_spectral_hash IS NOT NULL;
CREATE INDEX IF NOT EXISTS idx_yoon3_hash ON graphs(yoon3_spectral_hash) WHERE yoon3_spectral_hash IS NOT NULL;
CREATE INDEX IF NOT EXISTS idx_n_yoon3_hash ON graphs(n, yoon3_spectral_hash) WHERE yoon3_spectral_hash IS NOT NULL;

ALTER TABLE cospectral_mates DROP CONSTRAINT IF EXISTS cospectral_mates_matrix_type_check;
ALTER TABLE cospectral_mates ADD CONSTRAINT cospectral_mates_matrix_type_check
    CHECK (matrix_type IN ('adj','kirchhoff','signless','lap','nb','nbl','dist','seidel','distlap','distsign','kblock3','kblock4','yoon2','yoon3'));
