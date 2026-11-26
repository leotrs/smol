"""Shared chunk loop for the recomputation jobs: resumable and logged.

Each (n, chunk) is written to OUT/<job>_n<n>_c<chunk>.parquet through a temporary file
and a rename, so a killed run leaves no partial outputs, and a rerun skips the chunks that
already exist. Every finished chunk appends one line to progress_<job>.log.
Workers split the chunks by WID and NW (environment variables)."""
import os
import time

import duckdb
import pyarrow as pa
import pyarrow.parquet as pq

HERE = os.path.dirname(os.path.abspath(__file__))
DB = os.path.join(HERE, "data", "smol.duckdb")


def run(job, ns, step, compute):
    """compute(list of graph6, n) -> dict of column name -> array."""
    out = os.path.join(HERE, "out", job)
    wid, nw = int(os.environ.get("WID", 0)), int(os.environ.get("NW", 1))
    con = duckdb.connect(DB, read_only=True)
    for n in ns:
        g6 = [r[0] for r in con.execute(f"SELECT graph6 FROM graphs WHERE n = {n} ORDER BY graph6").fetchall()]
        nchunks = (len(g6) + step - 1) // step
        for c in range(nchunks):
            path = os.path.join(out, f"{job}_n{n}_c{c:04d}.parquet")
            if c % nw != wid or os.path.exists(path):
                continue
            t0 = time.time()
            chunk = g6[c * step:(c + 1) * step]
            cols = compute(chunk, n)
            pq.write_table(pa.table({"graph6": chunk, **cols}), path + ".tmp")
            os.rename(path + ".tmp", path)
            with open(os.path.join(HERE, f"progress_{job}.log"), "a") as f:
                f.write(f"{time.strftime('%Y-%m-%d %H:%M:%S')} worker {wid} n={n} chunk {c + 1}/{nchunks} "
                        f"graphs {len(chunk)} secs {time.time() - t0:.1f}\n")
