-- Add Arrigo-Noferini non-k-cycling matrix spectrum columns (k=3, k=4).
-- P_k is non-symmetric, so the spectrum is complex (real + imaginary parts).
-- Nilpotent cases (trees, cycles all shorter than k) are stored as NULL.

ALTER TABLE graphs
ADD COLUMN IF NOT EXISTS non3cyc_eigenvalues_re DOUBLE PRECISION[],
ADD COLUMN IF NOT EXISTS non3cyc_eigenvalues_im DOUBLE PRECISION[],
ADD COLUMN IF NOT EXISTS non3cyc_spectral_hash CHAR(16),
ADD COLUMN IF NOT EXISTS non4cyc_eigenvalues_re DOUBLE PRECISION[],
ADD COLUMN IF NOT EXISTS non4cyc_eigenvalues_im DOUBLE PRECISION[],
ADD COLUMN IF NOT EXISTS non4cyc_spectral_hash CHAR(16);

CREATE INDEX IF NOT EXISTS idx_non3cyc_hash ON graphs(non3cyc_spectral_hash) WHERE non3cyc_spectral_hash IS NOT NULL;
CREATE INDEX IF NOT EXISTS idx_n_non3cyc_hash ON graphs(n, non3cyc_spectral_hash) WHERE non3cyc_spectral_hash IS NOT NULL;
CREATE INDEX IF NOT EXISTS idx_non4cyc_hash ON graphs(non4cyc_spectral_hash) WHERE non4cyc_spectral_hash IS NOT NULL;
CREATE INDEX IF NOT EXISTS idx_n_non4cyc_hash ON graphs(n, non4cyc_spectral_hash) WHERE non4cyc_spectral_hash IS NOT NULL;

ALTER TABLE cospectral_mates DROP CONSTRAINT IF EXISTS cospectral_mates_matrix_type_check;
ALTER TABLE cospectral_mates ADD CONSTRAINT cospectral_mates_matrix_type_check
    CHECK (matrix_type IN ('adj','kirchhoff','signless','lap','nb','nbl','dist','seidel','distlap','distsign','kblock3','kblock4','yoon2','yoon3','non3cyc','non4cyc'));
