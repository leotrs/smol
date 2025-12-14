-- Verify cospectral counts against published data
-- Reference: Table 1 from "Graphs not determined by their spectrum"
--
-- Published counts (graphs with at least one cospectral mate):
--   n    | #graphs  |    A    |    L    |   NBL
-- -------|----------|---------|---------|--------
--   ≤4   |    17    |    0    |    4    |    4
--    5   |    34    |    2    |   12    |    8
--    6   |   156    |   10    |   32    |   26
--    7   |  1044    |  110    |  108    |  100
--    8   | 12346    | 1722    |  413    |  574
--    9   |274668    |51039    | 1824    | 4622
--   10   |12005168  |2560606  |26869    |57356

-- NOTE: Published data includes ALL graphs (connected + disconnected).
-- Our database includes disconnected graphs, matching the published counts.

-- LAPLACIAN DISCREPANCY at n≤4:
-- We find 6 graphs (2 at n=3, 4 at n=4), published shows 4.
-- At n=3: BO (K₂ + isolated vertex) and BW (P₃) are L-cospectral with eigenvalues {0,1,2}.
-- The discrepancy likely comes from whether disconnected-connected pairs are counted.
-- For n≥5, our counts match exactly.

--------------------------------------------------------------------------------
-- Adjacency cospectral counts
--------------------------------------------------------------------------------
WITH hash_counts AS (
    SELECT adj_spectral_hash, n, COUNT(*) as cnt
    FROM graphs
    GROUP BY adj_spectral_hash, n
    HAVING COUNT(*) > 1
)
SELECT g.n, COUNT(*) as adj_cospectral
FROM graphs g
JOIN hash_counts h ON g.adj_spectral_hash = h.adj_spectral_hash AND g.n = h.n
GROUP BY g.n
ORDER BY g.n;

-- Expected: n=5→2, n=6→10, n=7→110, n=8→1722, n=9→51039, n=10→2560606

--------------------------------------------------------------------------------
-- Laplacian cospectral counts
--------------------------------------------------------------------------------
WITH hash_counts AS (
    SELECT lap_spectral_hash, n, COUNT(*) as cnt
    FROM graphs
    GROUP BY lap_spectral_hash, n
    HAVING COUNT(*) > 1
)
SELECT g.n, COUNT(*) as lap_cospectral
FROM graphs g
JOIN hash_counts h ON g.lap_spectral_hash = h.lap_spectral_hash AND g.n = h.n
GROUP BY g.n
ORDER BY g.n;

-- Expected: n=5→12, n=6→32, n=7→108, n=8→413, n=9→1824, n=10→26869

--------------------------------------------------------------------------------
-- NBL (Non-Backtracking Laplacian) cospectral counts
--------------------------------------------------------------------------------
WITH hash_counts AS (
    SELECT nbl_spectral_hash, n, COUNT(*) as cnt
    FROM graphs
    GROUP BY nbl_spectral_hash, n
    HAVING COUNT(*) > 1
)
SELECT g.n, COUNT(*) as nbl_cospectral
FROM graphs g
JOIN hash_counts h ON g.nbl_spectral_hash = h.nbl_spectral_hash AND g.n = h.n
GROUP BY g.n
ORDER BY g.n;

-- Expected: n=4→4, n=5→8, n=6→26, n=7→100, n=8→574, n=9→4622, n=10→57356

--------------------------------------------------------------------------------
-- NB (Non-Backtracking) cospectral counts - DISCREPANCY INVESTIGATION
--------------------------------------------------------------------------------
-- Published $\mathcal{A}$ column:
--   n≤4→4, n=5→11, n=6→57, n=7→363, n=8→3760, n=9→64221, n=10→1936969
--
-- Our NB counts (all graphs):
--   n=4→4, n=5→15, n=6→75, n=7→449, n=8→4297, n=9→68749, n=10→2000415
--
-- DISCREPANCY: Our counts are consistently higher for n≥5.
--
-- Key finding: All trees/forests have ALL-ZERO NB eigenvalues (NB matrix is nilpotent).
-- This means all forests with same (n,m) are trivially NB-cospectral.
--
-- Filtering attempts:
--   - "cyclic only" (girth IS NOT NULL): matches at n=6 (57) but not elsewhere
--   - "connected only": undercounts
--   - "cyclic + trees": n=5→10 (vs 11), n=6→63, n=7→425, n=8→4246
--
-- IMPORTANT: When restricted to min_degree >= 2, our NB counts MATCH PERFECTLY.
-- See verify_cospectral_counts_min_deg2.sql for those results.
--
-- Possible explanations for all-graphs discrepancy:
--   1. Published may exclude trivial tree cospectrality
--   2. Column $\mathcal{A}$ might be signless Laplacian Q=D+A (we don't have this)
--   3. Different NB matrix definition for graphs with pendant vertices

WITH hash_counts AS (
    SELECT nb_spectral_hash, n, COUNT(*) as cnt
    FROM graphs
    GROUP BY nb_spectral_hash, n
    HAVING COUNT(*) > 1
)
SELECT g.n, COUNT(*) as nb_cospectral
FROM graphs g
JOIN hash_counts h ON g.nb_spectral_hash = h.nb_spectral_hash AND g.n = h.n
GROUP BY g.n
ORDER BY g.n;

-- Our result: n=4→4, n=5→15, n=6→75, n=7→449, n=8→4297
-- Published:  n≤4→4, n=5→11, n=6→57, n=7→363, n=8→3760
