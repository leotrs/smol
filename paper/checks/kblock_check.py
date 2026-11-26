"""k-blocking family: exact classes (job 1) versus SMOL's float signature. Prints counts and
checks a sample of exact classes that SMOL splits with sympy, member by member."""
import sys
import networkx as nx
import sympy

sys.path.insert(0, "/Users/leo.torres/research/smol")
from db.matrices import cycle_core, kblocking_matrix, kblocking_size  # noqa: E402

exec(open("compare_keys.py").read().split('print("joined rows:"')[0])
q = """SELECT n, kbfam, count(*) c, count(DISTINCT kblock_family_spectral_hash) s, list(graph6) g
       FROM j WHERE kblock_family_spectral_hash IS NOT NULL GROUP BY n, kbfam"""
con.execute(f"CREATE TEMP TABLE cls AS {q}")
for label, cond in (("exact", "c > 1"),):
    print("exact: families, members, largest =", con.execute("SELECT count(*), sum(c), max(c) FROM cls WHERE c > 1").fetchone())
print("SMOL : families, members, largest =", con.execute("""SELECT count(*), sum(c), max(c) FROM (SELECT count(*) c FROM j
      WHERE kblock_family_spectral_hash IS NOT NULL GROUP BY n, kblock_family_spectral_hash HAVING count(*) > 1)""").fetchone())
print("exact classes that SMOL splits:", con.execute("SELECT count(*), sum(c) FROM cls WHERE s > 1").fetchone(),
      "by n:", con.execute("SELECT n, count(*) FROM cls WHERE s > 1 GROUP BY n ORDER BY n").fetchall())
x = sympy.symbols("x")
def sig(g):
    G = nx.from_graph6_bytes(g.encode())
    out, k = [], 2
    while cycle_core(G, k).number_of_edges() > 0:
        M = sympy.Matrix(kblocking_matrix(G, k).astype(int))
        out.append((k, str(M.charpoly(x).as_expr()), kblocking_size(G, k)))
        k += 1
    return tuple(out)
for n, gs in con.execute("SELECT n, g FROM cls WHERE s > 1 ORDER BY n, c LIMIT 6").fetchall():
    sigs = {sig(g) for g in gs}
    print(f"n={n}: {gs} -> exact k-blocking family identical for all members: {len(sigs) == 1}")
