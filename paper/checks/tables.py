"""Generate every cospectrality table of the EJC note from the archived SMOL data.

Counts are numbers of graphs with at least one cospectral mate. Families are grouped by
(n, hash) for the tables by order, and by (m, hash) across all orders for the tables by
number of edges, which only makes sense for the matrices indexed by edges or paths.

Writes CSV files to ../tables/ and RSM table snippets to ../tables/*.rsm.
Run: uv run --no-project --with duckdb python tables.py
"""
import csv
import os

import duckdb

HERE = os.path.dirname(os.path.abspath(__file__))
OUT = os.path.join(HERE, "..", "tables")
MATRICES = [  # key, name in tables, exact?
    ("adj", "Adjacency", True), ("kirchhoff", "Kirchhoff Laplacian", True),
    ("signless", "Signless Laplacian", True), ("lap", "Normalized Laplacian", True),
    ("dist", "Distance", True), ("distlap", "Distance Laplacian", True),
    ("distsign", "Distance signless Laplacian", True),
    ("distnorm", "Normalized distance Laplacian", True), ("ecc", "Eccentricity", True),
    ("yoon2", "Yoon 2-Laplacian", True), ("yoon3", "Yoon 3-Laplacian", True),
    ("nb", "Non-backtracking", True), ("nbl", "Non-backtracking Laplacian", True),
    ("kblock_family", "$k$-blocking family", True),
    ("non3cyc", "Non-3-cycling", False), ("non4cyc", "Non-4-cycling", False),
]
EDGE_INDEXED = ["nb", "nbl", "kblock_family", "non3cyc", "non4cyc"]
RESTRICT = {"all": "TRUE", "mindeg2": "min_degree >= 2", "connected": "dist_spectral_hash IS NOT NULL"}


def fmt(x):
    return f"{x:,}" if x else "0"


def mates(con, key, where, group):
    rows = con.execute(f"""SELECT {group}, sum(c) FROM (SELECT {group}, count(*) c FROM graphs
        WHERE {where} AND {key}_spectral_hash IS NOT NULL GROUP BY {group}, {key}_spectral_hash
        HAVING count(*) > 1) GROUP BY {group}""").fetchall()
    return {r[0]: int(r[1]) for r in rows}


def rsm_table(label, caption, head, rows):
    lines = [f":table: {{\n  :label: {label}\n}}\n", "  :thead:", "    :tr: " + " : ".join(head) + " ::", "  ::",
             "  :tbody:"]
    lines += ["    :tr: " + " : ".join(r) + " ::" for r in rows]
    lines += ["  ::", "", f"  :caption: {caption}", "", "::", ""]
    return "\n".join(lines)


def main(db):
    os.makedirs(OUT, exist_ok=True)
    con = duckdb.connect(db, read_only=True)
    con.execute("SET threads TO 2")
    ns = list(range(1, 11))

    # Tables by order n.
    for r, where in RESTRICT.items():
        sizes = dict(con.execute(f"SELECT n, count(*) FROM graphs WHERE {where} GROUP BY n").fetchall())
        data = {k: mates(con, k, where, "n") for k, _, _ in MATRICES}
        first = min(n for n in ns if any(data[k].get(n) for k in data))
        cols = [n for n in ns if n >= first]
        with open(os.path.join(OUT, f"by_n_{r}.csv"), "w", newline="") as f:
            w = csv.writer(f)
            w.writerow(["matrix", "exact"] + [f"n={n}" for n in ns] + ["total"])
            w.writerow(["graphs", ""] + [sizes.get(n, 0) for n in ns] + [sum(sizes.values())])
            for k, _, ex in MATRICES:
                w.writerow([k, ex] + [data[k].get(n, 0) for n in ns] + [sum(data[k].values())])
        head = ["matrix"] + [f"$n = {n}$" if n == first else str(n) for n in cols] + ["total"]
        if first > 1:
            head[1] = f"$n \\le {first}$"
        def cell(d, n):
            return fmt(sum(v for m, v in d.items() if m <= n)) if n == first else fmt(d.get(n, 0))
        rows = [["graphs"] + [cell(sizes, n) for n in cols] + [fmt(sum(sizes.values()))]]
        for k, name, ex in MATRICES:
            rows.append([name + ("" if ex else "$^*$")] + [cell(data[k], n) for n in cols]
                        + [fmt(sum(data[k].values()))])
        with open(os.path.join(OUT, f"by_n_{r}.rsm"), "w") as f:
            f.write(rsm_table(f"tbl-n-{r}", f"Number of graphs with a cospectral mate, by order ({r}).",
                              head, rows))

    # Tables by order and number of edges (supplement, CSV only).
    for r, where in RESTRICT.items():
        with open(os.path.join(OUT, f"by_nm_{r}.csv"), "w", newline="") as f:
            w = csv.writer(f)
            w.writerow(["n", "m", "graphs"] + [k for k, _, _ in MATRICES])
            sizes = dict(((a, b), c) for a, b, c in con.execute(
                f"SELECT n, m, count(*) FROM graphs WHERE {where} GROUP BY n, m").fetchall())
            data = {k: mates(con, k, where, "n, m") for k, _, _ in MATRICES}
            for (n, m) in sorted(sizes):
                w.writerow([n, m, sizes[(n, m)]] + [data[k].get((n, m), 0) for k, _, _ in MATRICES])

    # Tables by number of edges, mates of any order (edge- and path-indexed matrices).
    with open(os.path.join(OUT, "by_m_cross.csv"), "w", newline="") as f:
        w = csv.writer(f)
        res = {}
        for r in ("all", "mindeg2"):
            where = RESTRICT[r]
            res[r] = ({a: c for a, c in con.execute(f"SELECT m, count(*) FROM graphs WHERE {where} GROUP BY m").fetchall()},
                      {k: mates(con, k, where, "m") for k in EDGE_INDEXED})
        w.writerow(["m"] + [f"{r}:{c}" for r in res for c in ["graphs"] + EDGE_INDEXED])
        for m in range(0, 46):
            w.writerow([m] + [x for r in res for x in [res[r][0].get(m, 0)] + [res[r][1][k].get(m, 0) for k in EDGE_INDEXED]])
    print("wrote", sorted(os.listdir(OUT)))


if __name__ == "__main__":
    import sys
    main(sys.argv[1] if len(sys.argv) > 1 else os.path.join(HERE, "data", "smol.duckdb"))
