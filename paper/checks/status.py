"""Progress of the recomputation jobs: chunks done per n, graphs done, rate, and ETA.
Run: uv run --no-project python status.py"""
import glob
import os
import re
import time

HERE = os.path.dirname(os.path.abspath(__file__))
CENSUS = {1: 1, 2: 2, 3: 4, 4: 11, 5: 34, 6: 156, 7: 1044, 8: 12346, 9: 274668, 10: 12005168}
JOBS = {"keys": (50_000, range(1, 11)), "float": (5_000, range(1, 11)), "noncyc": (20_000, range(1, 11)), "kblock": (50_000, range(1, 11)), "full_kblock": (20_000, range(1, 11)), "full_non3": (20_000, range(1, 11)), "full_non4": (20_000, range(1, 11))}
for job, (step, ns) in JOBS.items():
    total = sum(CENSUS[n] for n in ns)
    done = 0
    per_n = []
    for n in ns:
        k = len(glob.glob(os.path.join(HERE, "out", job, f"{job}_n{n}_c*.parquet")))
        nch = (CENSUS[n] + step - 1) // step
        done += min(k * step, CENSUS[n])
        per_n.append(f"n={n}: {k}/{nch}")
    log = os.path.join(HERE, f"progress_{job}.log")
    rate = ""
    if os.path.exists(log):
        lines = open(log).read().splitlines()[-200:]
        ts = [time.mktime(time.strptime(l[:19], "%Y-%m-%d %H:%M:%S")) for l in lines]
        gs = [int(re.search(r"graphs (\d+)", l).group(1)) for l in lines]
        if len(ts) > 1 and ts[-1] > ts[0]:
            r = sum(gs[1:]) / (ts[-1] - ts[0])
            rate = f", {r:,.0f} graphs/s, ETA {(total - done) / r / 60:,.0f} min"
            if time.time() - ts[-1] > 600:
                rate += f" (no chunk finished in the last {(time.time() - ts[-1]) / 60:.0f} min)"
    print(f"{job}: {done:,}/{total:,} graphs ({100 * done / total:.1f}%){rate}")
    print("   " + "  ".join(per_n))
