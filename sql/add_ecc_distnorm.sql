-- Add two connected-graphs-only real matrices to the distance family:
--   distnorm : normalized distance Laplacian  I - T^{-1/2} Dist T^{-1/2}
--              (Reinhart 2019), T = diag(transmissions). Strongest distance-
--              family discriminator (validated vs Reinhart: n=8 -> 2, n=9 -> 8).
--   ecc      : eccentricity matrix  eps[i,j] = d(i,j) iff d = min(ecc(i),ecc(j)),
--              else 0 (Mahato et al. 2019). A weak discriminator (~half of
--              connected graphs are ecc-cospectral); first known enumeration.
--
-- Both are real symmetric, defined for connected graphs only. Backfill with:
--   uv run python scripts/backfill_matrix.py --matrix distnorm
--   uv run python scripts/backfill_matrix.py --matrix ecc

BEGIN;

ALTER TABLE graphs
  ADD COLUMN IF NOT EXISTS distnorm_eigenvalues double precision[],
  ADD COLUMN IF NOT EXISTS distnorm_spectral_hash char(16),
  ADD COLUMN IF NOT EXISTS ecc_eigenvalues double precision[],
  ADD COLUMN IF NOT EXISTS ecc_spectral_hash char(16);

CREATE INDEX IF NOT EXISTS idx_distnorm_hash ON graphs(distnorm_spectral_hash) WHERE distnorm_spectral_hash IS NOT NULL;
CREATE INDEX IF NOT EXISTS idx_n_distnorm_hash ON graphs(n, distnorm_spectral_hash) WHERE distnorm_spectral_hash IS NOT NULL;
CREATE INDEX IF NOT EXISTS idx_ecc_hash ON graphs(ecc_spectral_hash) WHERE ecc_spectral_hash IS NOT NULL;
CREATE INDEX IF NOT EXISTS idx_n_ecc_hash ON graphs(n, ecc_spectral_hash) WHERE ecc_spectral_hash IS NOT NULL;

ALTER TABLE cospectral_mates DROP CONSTRAINT IF EXISTS cospectral_mates_matrix_type_check;
ALTER TABLE cospectral_mates ADD CONSTRAINT cospectral_mates_matrix_type_check
  CHECK (matrix_type IN ('adj', 'kirchhoff', 'signless', 'lap', 'nb', 'nbl', 'dist', 'distlap', 'distsign', 'distnorm', 'ecc', 'kblock_family', 'yoon2', 'yoon3', 'non3cyc', 'non4cyc'));

COMMIT;
