"""
bench.py — Hybrid implementation (CPython: source -> bytecode -> interpreter)

Usage: python3 bench.py <workload> <n> <trials>
  workload: fib | string

Prints one line of JSON: per-trial times in milliseconds, measured
inside the program (so interpreter startup is excluded).
"""
import json
import sys
import time


# ---- Workload 1: naive recursive Fibonacci (stresses function calls) ----
def fib(n):
    if n < 2:
        return n
    return fib(n - 1) + fib(n - 2)


# ---- Workload 2: string processing (stresses loops + memory access) ----
def make_string(n):
    x = 42
    chars = []
    for _ in range(n):
        x = (x * 1664525 + 1013904223) & 0xFFFFFFFF  # LCG, mod 2^32
        chars.append(chr(ord("a") + (x >> 16) % 26))
    return "".join(chars)


def process_string(s):
    # Deliberately written as an explicit character loop (no s[::-1] or
    # str.count) so we measure the interpreter, not C-coded built-ins.
    n = len(s)
    rev = [""] * n
    vowels = 0
    for i in range(n):
        c = s[i]
        if c == "a" or c == "e" or c == "i" or c == "o" or c == "u":
            vowels += 1
        rev[n - 1 - i] = c
    h = 0
    for c in rev:
        h = (h * 31 + ord(c)) & 0xFFFFFFFF
    return vowels * 1000003 + h


def main():
    workload, n, trials = sys.argv[1], int(sys.argv[2]), int(sys.argv[3])
    s = make_string(n) if workload == "string" else None

    times, result = [], None
    for _ in range(trials):
        t0 = time.perf_counter()
        result = fib(n) if workload == "fib" else process_string(s)
        t1 = time.perf_counter()
        times.append(round((t1 - t0) * 1000, 4))

    print(json.dumps({"lang": "Python", "workload": workload, "n": n,
                      "times_ms": times, "result": result}))


if __name__ == "__main__":
    main()
