"""Recompute cospectral-family totals per matrix from the hash columns of the archived graphs
table, and compare them to the archived cospectral_families table."""
import sys
import duckdb

db, fam_csv = sys.argv[1], sys.argv[2]
M = ["adj", "kirchhoff", "signless", "lap", "nb", "nbl", "dist", "distlap", "distsign",
     "distnorm", "ecc", "kblock_family", "yoon2", "yoon3", "non3cyc", "non4cyc"]
con = duckdb.connect(db, read_only=True)
con.execute("SET threads TO 4")
con.execute(f"CREATE TEMP TABLE cf AS SELECT * FROM read_csv('{fam_csv}', header=true)")
print(f"{'matrix':14} {'families':>10} {'members':>10} {'largest':>8} | archived table: families members largest")
for k in M:
    f, mem, big = con.execute(f"""
        SELECT count(*), sum(c), max(c) FROM (
          SELECT count(*) c FROM graphs WHERE {k}_spectral_hash IS NOT NULL
          GROUP BY n, {k}_spectral_hash HAVING count(*) >= 2)""").fetchone()
    a = con.execute(f"SELECT count(*), sum(family_size), max(family_size) FROM cf WHERE matrix_type = '{k}'").fetchone()
    print(f"{k:14} {f:>10,} {mem:>10,} {big:>8,} | {a[0]:>10,} {a[1]:>10,} {a[2]:>8,}")
print("matrix types in archived table:", [r[0] for r in con.execute("SELECT DISTINCT matrix_type FROM cf ORDER BY 1").fetchall()])
