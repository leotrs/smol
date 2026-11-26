#!/bin/zsh
# Job 3 (exact non-k-cycling keys), 2 single-threaded workers, started only after run_all.sh
# (jobs 1 and 2) has exited. Rerunning resumes: finished chunks are skipped.
cd "$(dirname "$0")"
while pgrep -f run_all.sh > /dev/null; do sleep 60; done
export OMP_NUM_THREADS=1 OPENBLAS_NUM_THREADS=1 VECLIB_MAXIMUM_THREADS=1 MKL_NUM_THREADS=1 NUMBA_NUM_THREADS=1
for w in 0 1; do
  WID=$w NW=2 nice -n 10 uv run --no-project --with numba --with numpy --with duckdb --with pyarrow python noncyc_job.py 1 2 3 4 5 6 7 8 9 10 > worker_noncyc_$w.log 2>&1 &
done
wait
