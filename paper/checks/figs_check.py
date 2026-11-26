"""Check the hard-coded families in make_figures.py against the archived hashes."""
import sys
import duckdb
sys.path.insert(0, "/Users/leo.torres/research/smol/paper")
import make_figures as mf

KEY = {"Adjacency": "adj", "Kirchhoff Laplacian": "kirchhoff", "Signless Laplacian": "signless",
       "Normalized Laplacian": "lap", "Non-backtracking": "nb", "Non-backtracking Laplacian": "nbl",
       "Distance": "dist", "Distance Laplacian": "distlap", "Distance Signless": "distsign",
       "Normalized Distance": "distnorm", "Eccentricity": "ecc", "k-blocking family": "kblock_family",
       "Yoon 2-Laplacian": "yoon2", "Yoon 3-Laplacian": "yoon3", "Non-3-cycling": "non3cyc",
       "Non-4-cycling": "non4cyc"}
con = duckdb.connect(sys.argv[1], read_only=True)
con.execute("SET threads TO 2")
for label, fams, where in (("connected", mf.FAM_CONNECTED, "dist_spectral_hash IS NOT NULL"),
                           ("min degree >= 2", mf.FAM_MINDEG2, "min_degree >= 2")):
    print("==", label)
    for name, mem in fams:
        k = KEY[name]
        h = f"{k}_spectral_hash"
        nmin = con.execute(f"""SELECT min(n) FROM (SELECT n FROM graphs WHERE {where} AND {h} IS NOT NULL
                               GROUP BY n, {h} HAVING count(*) > 1)""").fetchone()[0]
        nfam = con.execute(f"""SELECT count(*), list(c) FROM (SELECT count(*) c FROM graphs WHERE {where} AND {h} IS NOT NULL
                               AND n = {nmin if nmin else 0} GROUP BY {h} HAVING count(*) > 1)""").fetchone() if nmin else (0, [])
        if mem is None:
            print(f"  {name:28} figure: none   archive: smallest n = {nmin}, families there = {nfam[0]} sizes {sorted(nfam[1])[:10]}")
            continue
        rows = con.execute(f"SELECT graph6, n, {h}, {where} FROM graphs WHERE graph6 IN ({','.join(repr(g) for g in mem)})").fetchall()
        hs = {r[2] for r in rows}
        n_fig = rows[0][1]
        ok_restrict = all(r[3] for r in rows)
        whole = con.execute(f"SELECT count(*) FROM graphs WHERE {where} AND n = {n_fig} AND {h} = ?", [rows[0][2]]).fetchone()[0]
        flag = "" if (len(rows) == len(mem) and len(hs) == 1 and ok_restrict and whole == len(mem) and n_fig == nmin) else "   <-- CHECK"
        print(f"  {name:28} figure n={n_fig} size {len(mem)} | same hash {len(hs) == 1}, restriction ok {ok_restrict}, "
              f"whole family size {whole}, smallest n {nmin}, families at that n {nfam[0]}{flag}")
