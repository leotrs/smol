"""Fixed-point exact k-blocking family hash for every graph (see kblock_fast.py).
Usage: WID=0 NW=2 uv run --no-project --with numba --with numpy --with duckdb --with pyarrow python kblock_job.py N [N ...]"""
import sys

import kblock_fast as kf
import noncyc_fast as nf


def hashes(g6s, n):
    return {"kblock_family_spectral_hash": [kf.kblock_hash(nf.decode(s, n)) for s in g6s]}


if __name__ == "__main__":
    from chunks import run
    run("kblock", [int(x) for x in sys.argv[1:]], 50_000, hashes)
