"""
make_charts.py — turns results/summary.csv into the charts and table
used in the paper.

Usage: python3 make_charts.py
Produces results/runtime_vs_size.png, results/jit_warmup.png and
results/table.md
"""
import csv
import os
from collections import defaultdict

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

HERE = os.path.dirname(os.path.abspath(__file__))
OUT = os.path.join(HERE, "results")

# Fixed categorical order (colorblind-validated); markers give a second cue.
STYLE = {
    "C -O2 (compiled, optimized)":   ("#2a78d6", "o", "C -O2"),
    "C -O0 (compiled, unoptimized)": ("#eb6834", "s", "C -O0"),
    "Python (hybrid, bytecode)":     ("#1baf7a", "^", "Python"),
    "JavaScript (JIT, V8)":          ("#eda100", "D", "JavaScript"),
}
INK, MUTED, GRID, SURFACE = "#1f1f1e", "#6b6a64", "#e6e5e0", "#fcfcfb"

rows = list(csv.DictReader(open(os.path.join(OUT, "summary.csv"))))
data = defaultdict(lambda: defaultdict(list))
for r in rows:
    data[r["workload"]][r["implementation"]].append(
        (int(r["n"]), float(r["median_ms"]), float(r["first_trial_ms"]),
         float(r["steady_mean_ms"])))


def style_axes(ax):
    ax.set_facecolor(SURFACE)
    for side in ("top", "right"):
        ax.spines[side].set_visible(False)
    for side in ("left", "bottom"):
        ax.spines[side].set_color(GRID)
    ax.tick_params(colors=MUTED, labelsize=9)
    ax.grid(True, which="major", color=GRID, linewidth=0.8)
    ax.set_axisbelow(True)


plt.rcParams["font.family"] = "DejaVu Sans"

# ---- Chart 1: median runtime vs input size, one panel per workload ----
fig, axes = plt.subplots(1, 2, figsize=(11, 4.6), facecolor=SURFACE)
titles = {"fib": "Recursive Fibonacci", "string": "String processing"}
xlabels = {"fib": "n (fib(n))", "string": "string length (characters)"}
for ax, workload in zip(axes, ["fib", "string"]):
    style_axes(ax)
    ends = []
    for impl, (color, marker, short) in STYLE.items():
        pts = sorted(data[workload][impl])
        xs = [p[0] for p in pts]
        ys = [p[1] for p in pts]
        ax.plot(xs, ys, color=color, linewidth=2, marker=marker, markersize=7,
                markeredgecolor=SURFACE, markeredgewidth=1.5, label=short)
        ends.append([ys[-1], short, xs[-1], ys[-1]])
    # Spread end labels apart (in log space) so close lines don't collide.
    ends.sort()
    for i in range(1, len(ends)):
        ends[i][0] = max(ends[i][0], ends[i - 1][0] * 1.7)
    for label_y, short, x_end, y_end in ends:
        x_label = x_end + 0.6 if workload == "fib" else x_end * 1.5
        ax.text(x_label, label_y, short, va="center", ha="left", fontsize=9,
                color=INK)
    if workload == "fib":
        ax.set_xticks(SIZES_FIB := sorted({p[0] for p in
                      data["fib"]["C -O2 (compiled, optimized)"]}))
    ax.set_yscale("log")
    if workload == "string":
        ax.set_xscale("log")
    ax.set_title(titles[workload], loc="left", fontsize=12, color=INK,
                 fontweight="bold")
    ax.set_xlabel(xlabels[workload], color=MUTED, fontsize=9)
    ax.set_ylabel("median time per run (ms, log scale)", color=MUTED,
                  fontsize=9)
    ax.margins(x=0.18)
axes[0].legend(frameon=False, fontsize=9, loc="upper left")
fig.suptitle("Runtime by implementation method (lower is faster)",
             x=0.01, ha="left", fontsize=13, color=INK)
fig.tight_layout()
fig.savefig(os.path.join(OUT, "runtime_vs_size.png"), dpi=200)
plt.close(fig)

# ---- Chart 2: JIT warm-up — time of each trial for fib(20) ----
# Reads every individual trial from raw.json so the warm-up is visible
# run by run (an average of later runs would hide where it happens).
import json
raw = json.load(open(os.path.join(OUT, "raw.json")))
trials = {r["impl"]: r["times_ms"] for r in raw
          if r["workload"] == "fib" and r["n"] == 20}
fig, ax = plt.subplots(figsize=(7.5, 4.2), facecolor=SURFACE)
style_axes(ax)
t = list(range(1, len(trials["JavaScript (JIT, V8)"]) + 1))
for impl, (color, marker, short) in STYLE.items():
    if impl == "C -O0 (compiled, unoptimized)":
        continue
    ys = trials[impl]
    ax.plot(t, ys, color=color, linewidth=2, marker=marker, markersize=6,
            markeredgecolor=SURFACE, markeredgewidth=1.2)
    ax.annotate(short, (t[-1], ys[-1]), xytext=(8, 0),
                textcoords="offset points", va="center", fontsize=9, color=INK)
js = trials["JavaScript (JIT, V8)"]
peak = max(range(len(js)), key=lambda i: js[i])
ax.annotate(f"trial {peak + 1}: {js[peak]:.2f} ms\n(likely V8 compiling fib)",
            (peak + 1, js[peak]), xytext=(10, -2), textcoords="offset points",
            fontsize=8.5, color=INK, va="top")
ax.set_yscale("log")
ax.set_xticks(t)
ax.set_xlim(0.6, len(t) + 1.6)
ax.set_xlabel("trial (10 back-to-back calls in one process)", color=MUTED,
              fontsize=9)
ax.set_ylabel("time per call (ms, log scale)", color=MUTED, fontsize=9)
ax.set_title("fib(20): JavaScript speeds up once V8 compiles it; Python never does",
             loc="left", fontsize=11, color=INK, fontweight="bold")
fig.tight_layout()
fig.savefig(os.path.join(OUT, "jit_warmup.png"), dpi=200)
plt.close(fig)

# ---- Table: medians and slowdown relative to optimized C ----
lines = ["| Workload | n | C -O2 (ms) | C -O0 (ms) | Python (ms) | JavaScript (ms) "
         "| Python ÷ C -O2 | JS ÷ C -O2 |",
         "|---|---|---|---|---|---|---|---|"]
for workload in ["fib", "string"]:
    ns = sorted({p[0] for p in data[workload]["C -O2 (compiled, optimized)"]})
    for n in ns:
        med = {impl: next(p[1] for p in data[workload][impl] if p[0] == n)
               for impl in STYLE}
        c2 = med["C -O2 (compiled, optimized)"]
        lines.append(
            f"| {workload} | {n:,} | {c2:.3f} | "
            f"{med['C -O0 (compiled, unoptimized)']:.3f} | "
            f"{med['Python (hybrid, bytecode)']:.3f} | "
            f"{med['JavaScript (JIT, V8)']:.3f} | "
            f"{med['Python (hybrid, bytecode)'] / c2:.0f}× | "
            f"{med['JavaScript (JIT, V8)'] / c2:.1f}× |")
open(os.path.join(OUT, "table.md"), "w").write("\n".join(lines) + "\n")
print("\n".join(lines))
