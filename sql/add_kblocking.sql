-- Add k-blocking operator spectrum columns (Torres 2026, "The rich are loopy").
-- Spectrum of M_k computed via the degree-weighted non-backtracking companion
-- D_k B_k on the cycle core H_k. Complex spectrum; NULL when the cycle core is
-- empty/trivial (so those graphs are not grouped as cospectral).

ALTER TABLE graphs
ADD COLUMN IF NOT EXISTS kblock3_eigenvalues_re DOUBLE PRECISION[],
ADD COLUMN IF NOT EXISTS kblock3_eigenvalues_im DOUBLE PRECISION[],
ADD COLUMN IF NOT EXISTS kblock3_spectral_hash CHAR(16),
ADD COLUMN IF NOT EXISTS kblock4_eigenvalues_re DOUBLE PRECISION[],
ADD COLUMN IF NOT EXISTS kblock4_eigenvalues_im DOUBLE PRECISION[],
ADD COLUMN IF NOT EXISTS kblock4_spectral_hash CHAR(16);

CREATE INDEX IF NOT EXISTS idx_kblock3_hash ON graphs(kblock3_spectral_hash) WHERE kblock3_spectral_hash IS NOT NULL;
CREATE INDEX IF NOT EXISTS idx_n_kblock3_hash ON graphs(n, kblock3_spectral_hash) WHERE kblock3_spectral_hash IS NOT NULL;
CREATE INDEX IF NOT EXISTS idx_kblock4_hash ON graphs(kblock4_spectral_hash) WHERE kblock4_spectral_hash IS NOT NULL;
CREATE INDEX IF NOT EXISTS idx_n_kblock4_hash ON graphs(n, kblock4_spectral_hash) WHERE kblock4_spectral_hash IS NOT NULL;

ALTER TABLE cospectral_mates DROP CONSTRAINT IF EXISTS cospectral_mates_matrix_type_check;
ALTER TABLE cospectral_mates ADD CONSTRAINT cospectral_mates_matrix_type_check
    CHECK (matrix_type IN ('adj','kirchhoff','signless','lap','nb','nbl','dist','seidel','distlap','distsign','kblock3','kblock4'));
