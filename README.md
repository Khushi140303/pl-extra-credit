# Same Function, Three Implementation Methods

Extra credit project for Programming Languages (Prof. Katz-Braunschweig).
Khushi Agarwal (ka2653). Due November 25, 2026.

The same two functions are written in three languages, each representing a
different implementation method from Chapter 1 (Sebesta):

| File | Language | Implementation method |
|---|---|---|
| `bench.c` | C (gcc) | Compilation: source is translated to machine code before it runs |
| `bench.py` | Python (CPython) | Hybrid: source is translated to bytecode, then the bytecode is interpreted |
| `bench.js` | JavaScript (Node.js / V8) | JIT: code starts interpreted, and frequently used functions are compiled to machine code while the program runs |

C is built twice, with `-O0` (no optimization) and `-O2` (optimized), to show
what the optimization phase of a compiler contributes.

## The two workloads

1. **Recursive Fibonacci** `fib(n)`: millions of function calls, so it
   measures how cheaply each method handles calls and returns.
2. **String processing**: on a pseudo-random lowercase string of length n, loop
   character by character to count vowels, build the reversed string, and hash
   the reversed string. It measures loop and memory-access speed. The loops are
   written out explicitly in every language. Python built-ins such as
   `s[::-1]` are avoided because they run in C and would hide the interpreter's
   real cost.

Every language must produce the same answer for each input. The runner checks
this and stops if any result differs.

## How to run

Requirements: gcc, Python 3, Node.js, and matplotlib for the charts.

```
python3 run_benchmarks.py   # compiles C, runs everything, writes results/
python3 make_charts.py      # writes the charts and table from results/summary.csv
```

Each program times itself internally, so process startup is excluded. Every
configuration runs 10 trials, and the tables report the median.
`results/startup.csv` measures startup separately.

## Files in `results/`

- `summary.csv`: mean, median, standard deviation, first-trial, and
  steady-state times for every configuration
- `raw.json`: every individual trial time
- `startup.csv`: time to launch each program and do almost nothing
- `table.md`: median times and slowdown relative to optimized C
- `runtime_vs_size.png`: runtime versus input size for both workloads
- `jit_warmup.png`: JavaScript's first run versus later runs

## Key findings (MacBook Pro 14-inch 2023, Apple M2 Pro, 16 GB, macOS Tahoe 26.6.2; Apple clang 21.0.0, Python 3.15.2, Node 23.11.0)

- **Compiled C is fastest.** Python was 24–26× slower than optimized C on
  Fibonacci and 47–58× slower on string processing. JavaScript was
  1.9–2.4× slower once warmed up.
- **The JIT closes most of the gap.** JavaScript ran the same code about 11×
  faster than Python on Fibonacci and about 20× faster on string processing.
- **JIT warm-up is visible.** On `fib(20)`, JavaScript's first two runs took
  about 0.45–0.49 ms, the third spiked to 2.54 ms (likely V8 compiling the
  function), and every run after that took about 0.058 ms, 8× faster than the
  first run. On the 10,000-character string, most runs finished before the
  compiled code was ready, so JavaScript was 14.9× slower than C there.
- **Compiler optimization matters less for memory-heavy work.** `-O2` was
  about 1.8× faster than `-O0` on Fibonacci but only about 1.6× faster on
  string processing, which is consistent with the von Neumann bottleneck.
- **Startup goes the other way.** C launched in about 2.1 ms, Python in
  19.9 ms, and Node in 26.0 ms. For small inputs, Python finished sooner
  than JavaScript once startup is included.

The full analysis is in the accompanying paper (PDF).
