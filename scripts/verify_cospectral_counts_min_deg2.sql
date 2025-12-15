-- Verify cospectral counts for graphs with minimum degree >= 2
-- Reference: Table 2 from "Graphs determined by their spectrum"
--
-- Published counts (graphs with at least one cospectral mate, min_degree >= 2):
--   n    | #graphs    |   adj     |   lap    |    nb   |  nbl
-- -------|------------|-----------|----------|---------|-------
--   ≤6   |     76     |     0     |    2     |    0    |   0
--    7   |    510     |    26     |    4     |    0    |   0
--    8   |   7459     |   744     |   11     |    2    |   0
--    9   | 197867     | 32713     |  243     |    6    |   0
--   10   |9808968     |1976884    |16114     |10130    | 156
--
-- VERIFICATION RESULTS (Dec 2024):
--   adj: ✓ Perfect match (0, 26, 744, 32713, 1976884)
--   lap: ✓ Perfect match (2, 4, 11, 243, 16114)
--   nb:  ✓ Perfect match (0, 0, 2, 6, 10130)
--   nbl: ✓ Perfect match (0, 0, 0, 0, 156)
--
-- ALL FOUR MATRICES MATCH PERFECTLY FOR min_degree >= 2!

--------------------------------------------------------------------------------
-- Adjacency cospectral counts (min_degree >= 2)
--------------------------------------------------------------------------------
WITH hash_counts AS (
    SELECT adj_spectral_hash, n, COUNT(*) as cnt
    FROM graphs
    WHERE min_degree >= 2
    GROUP BY adj_spectral_hash, n
    HAVING COUNT(*) > 1
)
SELECT g.n, COUNT(*) as adj_cospectral
FROM graphs g
JOIN hash_counts h ON g.adj_spectral_hash = h.adj_spectral_hash AND g.n = h.n
WHERE g.min_degree >= 2
GROUP BY g.n
ORDER BY g.n;

-- Expected: n=7→26, n=8→744, n=9→32713, n=10→1976884

--------------------------------------------------------------------------------
-- Laplacian cospectral counts (min_degree >= 2)
--------------------------------------------------------------------------------
WITH hash_counts AS (
    SELECT lap_spectral_hash, n, COUNT(*) as cnt
    FROM graphs
    WHERE min_degree >= 2
    GROUP BY lap_spectral_hash, n
    HAVING COUNT(*) > 1
)
SELECT g.n, COUNT(*) as lap_cospectral
FROM graphs g
JOIN hash_counts h ON g.lap_spectral_hash = h.lap_spectral_hash AND g.n = h.n
WHERE g.min_degree >= 2
GROUP BY g.n
ORDER BY g.n;

-- Expected: n=6→2, n=7→4, n=8→11, n=9→243, n=10→16114

--------------------------------------------------------------------------------
-- NB (Non-Backtracking) cospectral counts (min_degree >= 2)
--------------------------------------------------------------------------------
WITH hash_counts AS (
    SELECT nb_spectral_hash, n, COUNT(*) as cnt
    FROM graphs
    WHERE min_degree >= 2
    GROUP BY nb_spectral_hash, n
    HAVING COUNT(*) > 1
)
SELECT g.n, COUNT(*) as nb_cospectral
FROM graphs g
JOIN hash_counts h ON g.nb_spectral_hash = h.nb_spectral_hash AND g.n = h.n
WHERE g.min_degree >= 2
GROUP BY g.n
ORDER BY g.n;

-- Expected: n=8→2, n=9→6, n=10→10130

--------------------------------------------------------------------------------
-- NBL (Non-Backtracking Laplacian) cospectral counts (min_degree >= 2)
--------------------------------------------------------------------------------
WITH hash_counts AS (
    SELECT nbl_spectral_hash, n, COUNT(*) as cnt
    FROM graphs
    WHERE min_degree >= 2
    GROUP BY nbl_spectral_hash, n
    HAVING COUNT(*) > 1
)
SELECT g.n, COUNT(*) as nbl_cospectral
FROM graphs g
JOIN hash_counts h ON g.nbl_spectral_hash = h.nbl_spectral_hash AND g.n = h.n
WHERE g.min_degree >= 2
GROUP BY g.n
ORDER BY g.n;

-- Expected: n=10→156
