"""Per-n counts of graphs with a cospectral mate, all graphs and min-degree >= 2 graphs
(mates searched only among min-degree >= 2 graphs), for comparison with Jost, Mulas,
Torres (2023), Tables 1 and 2."""
import sys
import duckdb

con = duckdb.connect(sys.argv[1], read_only=True)
con.execute("SET threads TO 2")
for where, label in (("TRUE", "all graphs"), ("min_degree >= 2", "min degree >= 2")):
    print(label)
    for k in ("adj", "lap", "nb", "nbl"):
        rows = con.execute(f"""SELECT n, sum(c) FROM (SELECT n, count(*) c FROM graphs
            WHERE {where} AND {k}_spectral_hash IS NOT NULL GROUP BY n, {k}_spectral_hash HAVING count(*) > 1)
            GROUP BY n ORDER BY n""").fetchall()
        print(f"  {k:5}", {n: int(c) for n, c in rows}, "total", sum(int(c) for _, c in rows))
    print("  graphs per n:", dict(con.execute(f"SELECT n, count(*) FROM graphs WHERE {where} GROUP BY n ORDER BY n").fetchall()))
