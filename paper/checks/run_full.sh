#!/bin/zsh
# Full-matrix check of every graph for kblock_family, non3cyc and non4cyc (fullcheck.py),
# one matrix after the other, 4 single-threaded workers. Resumable.
cd "$(dirname "$0")"
export OMP_NUM_THREADS=1 NUMBA_NUM_THREADS=1
for kind in kblock non3 non4; do
  for w in 0 1 2 3; do
    WID=$w NW=4 nice -n 10 uv run --no-project --with numba --with numpy --with duckdb --with pyarrow python fullcheck.py $kind 1 2 3 4 5 6 7 8 9 10 > worker_full_${kind}_$w.log 2>&1 &
  done
  wait
done
