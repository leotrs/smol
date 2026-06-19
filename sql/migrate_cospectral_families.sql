-- Migrate from per-pair cospectral_mates to per-family cospectral_families.
--
-- The old table stored C(k,2) pairs per cospectral family, which is quadratic in
-- family size and infeasible for weak discriminators (ecc families reach 8000+).
-- The new table stores one row per family of size >= 2, keyed by (matrix_type, n,
-- hash). Family members are recovered at query time via the idx_n_<matrix>_hash
-- indexes on graphs. switching_mechanisms loses its FK into the pairs table but
-- keeps its (graph1_id, graph2_id, matrix_type) columns as self-contained data.

BEGIN;

CREATE TABLE IF NOT EXISTS cospectral_families (
    matrix_type     VARCHAR(20) NOT NULL,
    n               SMALLINT NOT NULL,
    spectral_hash   CHAR(16) NOT NULL,
    family_size     INTEGER NOT NULL CHECK (family_size >= 2),
    PRIMARY KEY (matrix_type, n, spectral_hash)
);
CREATE INDEX IF NOT EXISTS idx_families_matrix_n ON cospectral_families(matrix_type, n);

-- switching_mechanisms keeps its pair columns but no longer references the pairs table.
ALTER TABLE switching_mechanisms
    DROP CONSTRAINT IF EXISTS switching_mechanisms_graph1_id_graph2_id_matrix_type_fkey;

DROP TABLE IF EXISTS cospectral_mates CASCADE;

COMMIT;
