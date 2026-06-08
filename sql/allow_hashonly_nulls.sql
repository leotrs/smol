-- Allow NULL eigenvalue arrays so graphs can be stored hash-only (the spectral
-- hash is all cospectrality needs). Used for n=10, which is local-only and
-- generated with SMOL_HASH_ONLY=1 (compute-bound rather than insert-bound).
ALTER TABLE graphs
  ALTER COLUMN adj_eigenvalues       DROP NOT NULL,
  ALTER COLUMN kirchhoff_eigenvalues DROP NOT NULL,
  ALTER COLUMN signless_eigenvalues  DROP NOT NULL,
  ALTER COLUMN lap_eigenvalues       DROP NOT NULL,
  ALTER COLUMN nb_eigenvalues_re     DROP NOT NULL,
  ALTER COLUMN nb_eigenvalues_im     DROP NOT NULL,
  ALTER COLUMN nbl_eigenvalues_re    DROP NOT NULL,
  ALTER COLUMN nbl_eigenvalues_im    DROP NOT NULL;
