"""
run_benchmarks.py — runs every implementation across input sizes and
summarizes the results.

Usage: python3 run_benchmarks.py

Produces:
  results/raw.json      every trial time from every run
  results/summary.csv   one row per (workload, n, language)
  results/startup.csv   cost of just starting each program (fib(1), 1 trial)
"""
import csv
import json
import os
import statistics
import subprocess
import time

HERE = os.path.dirname(os.path.abspath(__file__))
OUT = os.path.join(HERE, "results")
TRIALS = 10

IMPLEMENTATIONS = {
    "C -O2 (compiled, optimized)": ["./bench_c_O2"],
    "C -O0 (compiled, unoptimized)": ["./bench_c_O0"],
    "Python (hybrid, bytecode)": ["python3", "bench.py"],
    "JavaScript (JIT, V8)": ["node", "bench.js"],
}

SIZES = {
    "fib": [20, 25, 30, 32, 35],
    "string": [10_000, 100_000, 1_000_000, 10_000_000],
}


def build():
    for flag in ("O2", "O0"):
        subprocess.run(["gcc", f"-{flag}", "-o", f"bench_c_{flag}", "bench.c"],
                       cwd=HERE, check=True)


def run(cmd, workload, n, trials):
    out = subprocess.run(cmd + [workload, str(n), str(trials)], cwd=HERE,
                         capture_output=True, text=True, check=True)
    return json.loads(out.stdout)


def main():
    os.makedirs(OUT, exist_ok=True)
    build()
    raw, rows = [], []

    for workload, sizes in SIZES.items():
        for n in sizes:
            results = {}
            for label, cmd in IMPLEMENTATIONS.items():
                r = run(cmd, workload, n, TRIALS)
                r["impl"] = label
                raw.append(r)
                results[label] = r["result"]
                t = r["times_ms"]
                steady = t[1:]
                rows.append({
                    "workload": workload, "n": n, "implementation": label,
                    "mean_ms": round(statistics.mean(t), 4),
                    "median_ms": round(statistics.median(t), 4),
                    "stdev_ms": round(statistics.stdev(t), 4),
                    "first_trial_ms": t[0],
                    "steady_mean_ms": round(statistics.mean(steady), 4),
                })
                print(f"{workload:6} n={n:<10} {label:32} "
                      f"median {statistics.median(t):12.3f} ms")
            # Every language must compute the same answer.
            assert len(set(results.values())) == 1, (workload, n, results)

    # Startup cost: wall-clock time to launch the process and do almost nothing.
    startup = []
    for label, cmd in IMPLEMENTATIONS.items():
        samples = []
        for _ in range(TRIALS):
            t0 = time.perf_counter()
            run(cmd, "fib", 1, 1)
            samples.append((time.perf_counter() - t0) * 1000)
        startup.append({"implementation": label,
                        "median_startup_ms": round(statistics.median(samples), 3)})

    with open(os.path.join(OUT, "raw.json"), "w") as f:
        json.dump(raw, f, indent=1)
    with open(os.path.join(OUT, "summary.csv"), "w", newline="") as f:
        w = csv.DictWriter(f, fieldnames=rows[0].keys())
        w.writeheader()
        w.writerows(rows)
    with open(os.path.join(OUT, "startup.csv"), "w", newline="") as f:
        w = csv.DictWriter(f, fieldnames=startup[0].keys())
        w.writeheader()
        w.writerows(startup)
    print("\nStartup:", startup)


if __name__ == "__main__":
    main()
