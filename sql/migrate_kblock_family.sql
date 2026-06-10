-- Migrate from the standalone kblock3 / kblock4 matrices to the single
-- composite k-blocking family invariant.
--
-- kblock_family is a graded hash over {M_k : k = 2 .. Delta(G)} (each M_k = the
-- degree-weighted non-backtracking companion on the degree->=k 2-core, with
-- |states(M_k)| folded in), iterating up from k=2 and stopping at the first
-- empty cycle core. NULL for forests. It is a multi-matrix signature, so it has
-- no eigenvalue arrays -- only a hash. Backfill with:
--   uv run python scripts/backfill_matrix.py --matrix kblock_family

BEGIN;

ALTER TABLE graphs ADD COLUMN IF NOT EXISTS kblock_family_spectral_hash TEXT;
CREATE INDEX IF NOT EXISTS idx_kblock_family_hash ON graphs(kblock_family_spectral_hash);
CREATE INDEX IF NOT EXISTS idx_n_kblock_family_hash ON graphs(n, kblock_family_spectral_hash);

ALTER TABLE graphs
  DROP COLUMN IF EXISTS kblock3_eigenvalues_re, DROP COLUMN IF EXISTS kblock3_eigenvalues_im, DROP COLUMN IF EXISTS kblock3_spectral_hash,
  DROP COLUMN IF EXISTS kblock4_eigenvalues_re, DROP COLUMN IF EXISTS kblock4_eigenvalues_im, DROP COLUMN IF EXISTS kblock4_spectral_hash;

-- 'kblock_family' is 13 chars; widen the (formerly varchar(10)) column.
ALTER TABLE cospectral_mates ALTER COLUMN matrix_type TYPE varchar(20);
DELETE FROM cospectral_mates WHERE matrix_type IN ('kblock3', 'kblock4');
ALTER TABLE cospectral_mates DROP CONSTRAINT IF EXISTS cospectral_mates_matrix_type_check;
ALTER TABLE cospectral_mates ADD CONSTRAINT cospectral_mates_matrix_type_check
  CHECK (matrix_type IN ('adj', 'kirchhoff', 'signless', 'lap', 'nb', 'nbl', 'dist', 'distlap', 'distsign', 'kblock_family', 'yoon2', 'yoon3', 'non3cyc', 'non4cyc'));

COMMIT;
