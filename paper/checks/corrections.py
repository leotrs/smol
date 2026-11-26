"""Build the corrected hashes for the three matrices that SMOL classified by rounding:
kblock_family (from kblock_job.py, fixed points) and non3cyc, non4cyc (from job 3, rechecked).
Hash = first 16 hex digits of sha256 of a string of exact characteristic-polynomial values
(see charkeys.py and noncyc_job.py for the points and primes). NULL where the old pipeline
gave NULL: forests for kblock_family, nilpotent matrices for non-k-cycling.
Writes out/corrections.parquet (graph6, n, three hashes) and out/families_corrected.csv."""
import duckdb

exec(open("compare_keys.py").read().split('print("joined rows:"')[0])
con.execute("CREATE TEMP TABLE r AS SELECT * FROM read_parquet('out/noncyc/*.parquet')")
con.execute("""COPY (SELECT j.graph6, j.n,
    kb.kblock_family_spectral_hash,
    CASE WHEN r.non3cyc_nilpotent THEN NULL ELSE left(sha256(concat_ws('|', 'non3cyc-exact', r.non3cyc_N, r.non3cyc_v1, r.non3cyc_v2)), 16) END AS non3cyc_spectral_hash,
    CASE WHEN r.non4cyc_nilpotent THEN NULL ELSE left(sha256(concat_ws('|', 'non4cyc-exact', r.non4cyc_N, r.non4cyc_v1, r.non4cyc_v2)), 16) END AS non4cyc_spectral_hash
  FROM j JOIN r USING (graph6) JOIN read_parquet('out/kblock/*.parquet') kb USING (graph6)) TO 'out/corrections.parquet' (FORMAT parquet)""")
c = duckdb.connect(); c.execute("SET threads TO 1")
c.execute("""COPY (SELECT matrix_type, n, spectral_hash, count(*) AS family_size FROM (
    SELECT 'kblock_family' matrix_type, n, kblock_family_spectral_hash spectral_hash FROM 'out/corrections.parquet' UNION ALL
    SELECT 'non3cyc', n, non3cyc_spectral_hash FROM 'out/corrections.parquet' UNION ALL
    SELECT 'non4cyc', n, non4cyc_spectral_hash FROM 'out/corrections.parquet')
  WHERE spectral_hash IS NOT NULL GROUP BY ALL HAVING count(*) > 1 ORDER BY ALL) TO 'out/families_corrected.csv' (HEADER)""")
print(c.execute("SELECT matrix_type, count(*), sum(family_size), max(family_size) FROM 'out/families_corrected.csv' GROUP BY 1 ORDER BY 1").fetchall())
print("hash collisions across classes:", c.execute("""SELECT count(*) FROM (SELECT non3cyc_spectral_hash h FROM 'out/corrections.parquet' WHERE h IS NOT NULL GROUP BY n, h HAVING count(*) > 1)""").fetchone())
