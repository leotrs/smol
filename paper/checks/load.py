"""Load the archived SMOL graphs table (Zenodo 10.5281/zenodo.20794132) into a DuckDB file."""
import sys
import duckdb

src, out = sys.argv[1], sys.argv[2]
con = duckdb.connect(out)
con.execute("SET threads TO 4")
con.execute(f"CREATE OR REPLACE TABLE graphs AS SELECT * FROM read_csv('{src}', header=true, all_varchar=false, sample_size=-1)")
print(con.execute("SELECT n, count(*) FROM graphs GROUP BY n ORDER BY n").fetchall())
