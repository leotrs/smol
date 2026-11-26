#!/bin/zsh
# Job 1 (independent exact keys), then job 2 (SMOL's 8-decimal float hashes), 4 single-threaded
# workers each, never both at once. Rerunning resumes: finished chunks are skipped.
# Progress: uv run --no-project python status.py   (or tail -f progress_keys.log / progress_float.log)
cd "$(dirname "$0")"
export OMP_NUM_THREADS=1 OPENBLAS_NUM_THREADS=1 VECLIB_MAXIMUM_THREADS=1 MKL_NUM_THREADS=1
for w in 0 1 2 3; do
  WID=$w NW=4 nice -n 10 uv run --no-project --with numpy --with duckdb --with pyarrow python charkeys.py 1 2 3 4 5 6 7 8 9 10 > worker_keys_$w.log 2>&1 &
done
wait
for w in 0 1 2 3; do
  WID=$w NW=4 nice -n 10 uv run --project ~/research/smol --with duckdb --with pyarrow python floatkeys.py 1 2 3 4 5 6 7 8 9 10 > worker_float_$w.log 2>&1 &
done
wait
