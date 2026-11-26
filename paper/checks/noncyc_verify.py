"""Recheck every non-k-cycling family from job 3 at two more points (mod P1 and mod P2).
Families are grouped by (N, v1, v2) across all orders, which contains the per-order families.
A family survives if all members also agree at the new points; otherwise it is split."""

import duckdb

import noncyc_fast as nf

Y1, Y2 = 7_777_777, 31_415_927
con = duckdb.connect()
con.execute("SET threads TO 1")
con.execute("CREATE TEMP TABLE r AS SELECT *, CAST(regexp_extract(filename, 'n(\\d+)_c', 1) AS INT) n FROM read_parquet('out/noncyc/*.parquet', filename = true)")
print("graphs:", con.execute("SELECT count(*) FROM r").fetchone()[0])
for k in (3, 4):
    rows = con.execute(f"""SELECT graph6, n, non{k}cyc_N, non{k}cyc_v1, non{k}cyc_v2 FROM r WHERE NOT non{k}cyc_nilpotent AND
        (non{k}cyc_N, non{k}cyc_v1, non{k}cyc_v2) IN (SELECT (non{k}cyc_N, non{k}cyc_v1, non{k}cyc_v2) FROM r
        WHERE NOT non{k}cyc_nilpotent GROUP BY 1 HAVING count(*) > 1)""").fetchall()
    fams = {}
    for g6, n, N, a, b in rows:
        A = nf.decode(g6, n)
        w1, _ = nf.charval(A, n, k, Y1, nf.P1)
        w2, _ = nf.charval(A, n, k, Y2, nf.P2)
        fams.setdefault((N, a, b), set()).add((w1, w2))
    bad = sum(len(s) > 1 for s in fams.values())
    print(f"k={k}: {len(rows):,} graphs in {len(fams):,} families (any order); families that split at the new points: {bad}")
