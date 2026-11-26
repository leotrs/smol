"""Compare SMOL's archived families with the independent exact keys of job 1 (out/keys), for
the 13 exactly classified matrices and the k-blocking family. For each matrix the graphs with
a SMOL hash are grouped twice, by (n, SMOL hash) and by (n, independent key). The two
partitions are identical exactly when the three distinct counts printed agree. Also checks
that SMOL's NULL hashes fall exactly where the matrix is undefined."""
import duckdb

con = duckdb.connect()
con.execute("SET threads TO 1")
con.execute("ATTACH 'data/smol.duckdb' AS a (READ_ONLY)")
con.execute("CREATE TEMP TABLE k AS SELECT * FROM read_parquet('out/keys/*.parquet')")
con.execute("""CREATE TEMP TABLE j AS SELECT g.*, k.* EXCLUDE (graph6, n, m),
  -- k-blocking family signature: members k = 2, 3, ... until the first empty cycle core
  CASE WHEN k.kb2_m = 0 THEN NULL ELSE concat_ws('|',
    concat(k.kb2, ':', k.kb2_m, ':', k.kb2_size),
    CASE WHEN k.kb3_m > 0 THEN concat(k.kb3, ':', k.kb3_m, ':', k.kb3_size) END,
    CASE WHEN k.kb3_m > 0 AND k.kb4_m > 0 THEN concat(k.kb4, ':', k.kb4_m, ':', k.kb4_size) END,
    CASE WHEN k.kb3_m > 0 AND k.kb4_m > 0 AND k.kb5_m > 0 THEN concat(k.kb5, ':', k.kb5_m, ':', k.kb5_size) END,
    CASE WHEN k.kb3_m > 0 AND k.kb4_m > 0 AND k.kb5_m > 0 AND k.kb6_m > 0 THEN concat(k.kb6, ':', k.kb6_m, ':', k.kb6_size) END,
    CASE WHEN k.kb3_m > 0 AND k.kb4_m > 0 AND k.kb5_m > 0 AND k.kb6_m > 0 AND k.kb7_m > 0 THEN concat(k.kb7, ':', k.kb7_m, ':', k.kb7_size) END,
    CASE WHEN k.kb3_m > 0 AND k.kb4_m > 0 AND k.kb5_m > 0 AND k.kb6_m > 0 AND k.kb7_m > 0 AND k.kb8_m > 0 THEN concat(k.kb8, ':', k.kb8_m, ':', k.kb8_size) END,
    CASE WHEN k.kb3_m > 0 AND k.kb4_m > 0 AND k.kb5_m > 0 AND k.kb6_m > 0 AND k.kb7_m > 0 AND k.kb8_m > 0 AND k.kb9_m > 0 THEN concat(k.kb9, ':', k.kb9_m, ':', k.kb9_size) END)
  END AS kbfam
  FROM a.graphs g JOIN k USING (graph6)""")
print("joined rows:", con.execute("SELECT count(*) FROM j").fetchone()[0])
MAT = {  # matrix: (my key expression, condition under which the matrix is undefined)
    "adj": ("adj", "FALSE"), "kirchhoff": ("kirchhoff", "FALSE"), "signless": ("signless", "FALSE"),
    "lap": ("lap", "FALSE"), "dist": ("dist", "NOT connected"), "distlap": ("distlap", "NOT connected"),
    "distsign": ("distsign", "NOT connected"), "distnorm": ("distnorm", "NOT connected OR n < 2"),
    "ecc": ("ecc", "NOT connected"), "yoon2": ("yoon2", "n <= 2"), "yoon3": ("yoon3", "n <= 3"),
    "nb": ("concat(nb, ':', m)", "m = 0"), "nbl": ("concat(nbl, ':', m)", "m = 0"),
    "kblock_family": ("kbfam", "kbfam IS NULL"),
}
print(f"{'matrix':14} {'NULLs as expected':>18} {'SMOL classes':>13} {'my classes':>11} {'joint':>9}  verdict")
for mx, (kexpr, undef) in MAT.items():
    h = f"{mx}_spectral_hash"
    bad_null = con.execute(f"SELECT count(*) FROM j WHERE ({h} IS NULL) != ({undef})").fetchone()[0]
    a, b, c = con.execute(f"""SELECT count(DISTINCT (n, {h})), count(DISTINCT (n, {kexpr})), count(DISTINCT (n, {h}, {kexpr}))
                              FROM j WHERE {h} IS NOT NULL""").fetchone()
    verdict = "identical" if a == b == c and bad_null == 0 else "DIFFERENT"
    print(f"{mx:14} {('yes' if bad_null == 0 else f'{bad_null} off'):>18} {a:>13,} {b:>11,} {c:>9,}  {verdict}")
