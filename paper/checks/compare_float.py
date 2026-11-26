"""8-decimal float classification (job 2, SMOL's own float code) versus the exact one (archive,
confirmed by job 1), per matrix and n. Only graphs with an exact hash are compared.
  mates_f / mates_e : graphs with a cospectral mate, float / exact
  fam_f / fam_e     : number of families of size >= 2, float / exact
  split             : exact families whose members fall in more than one float class
  fully_split       : exact families whose members are all float singletons
  merged            : float classes holding graphs with different exact hashes (false merges)
  lost              : graphs in an exact family that have no float mate at all"""
import duckdb

con = duckdb.connect()
con.execute("SET threads TO 1")
con.execute("ATTACH 'data/smol.duckdb' AS a (READ_ONLY)")
con.execute("CREATE TEMP TABLE f AS SELECT * FROM read_parquet('out/float/*.parquet')")
M = ["adj", "kirchhoff", "signless", "lap", "dist", "distlap", "distsign", "distnorm", "ecc", "yoon2", "yoon3", "nb", "nbl"]
sel = ", ".join(f"g.{k}_spectral_hash AS {k}_e, f.{k} AS {k}_f" for k in M)
con.execute(f"CREATE TEMP TABLE j AS SELECT g.graph6, g.n, {sel} FROM a.graphs g JOIN f USING (graph6)")
print("joined", con.execute("SELECT count(*) FROM j").fetchone()[0])
cols = "n, mates_f, mates_e, fam_f, fam_e, split, fully_split, merged, lost"
print("matrix", cols)
for k in M:
    rows = con.execute(f"""
      WITH x AS (SELECT n, {k}_e e, {k}_f fl FROM j WHERE {k}_e IS NOT NULL),
      ce AS (SELECT n, e, count(*) c, count(DISTINCT fl) nf FROM x GROUP BY n, e),
      cf AS (SELECT n, fl, count(*) c, count(DISTINCT e) ne FROM x GROUP BY n, fl),
      xx AS (SELECT x.*, ce.c ce, cf.c cfc FROM x JOIN ce USING (n, e) JOIN cf USING (n, fl)),
      fs AS (SELECT n, e, bool_and(cfc = 1) allsingle FROM xx WHERE ce > 1 GROUP BY n, e)
      SELECT n,
        (SELECT coalesce(sum(c), 0) FROM cf WHERE cf.n = t.n AND c > 1),
        (SELECT coalesce(sum(c), 0) FROM ce WHERE ce.n = t.n AND c > 1),
        (SELECT count(*) FROM cf WHERE cf.n = t.n AND c > 1),
        (SELECT count(*) FROM ce WHERE ce.n = t.n AND c > 1),
        (SELECT count(*) FROM ce WHERE ce.n = t.n AND c > 1 AND nf > 1),
        (SELECT count(*) FROM fs WHERE fs.n = t.n AND allsingle),
        (SELECT count(*) FROM cf WHERE cf.n = t.n AND ne > 1),
        (SELECT count(*) FROM xx WHERE xx.n = t.n AND ce > 1 AND cfc = 1)
      FROM (SELECT DISTINCT n FROM x) t ORDER BY n""").fetchall()
    diff = [r for r in rows if r[1] != r[2] or r[3] != r[4] or any(r[5:])]
    print(k, "agree at every n" if not diff else "", *[r for r in diff])
