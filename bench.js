/*
 * bench.js — JIT implementation (Node.js / V8: interpreter + JIT compiler)
 *
 * Usage: node bench.js <workload> <n> <trials>
 *   workload: fib | string
 *
 * Prints one line of JSON: per-trial times in milliseconds, measured
 * inside the program (so runtime startup is excluded). The first trial
 * includes JIT warm-up; later trials run already-compiled machine code.
 */

// ---- Workload 1: naive recursive Fibonacci (stresses function calls) ----
function fib(n) {
  if (n < 2) return n;
  return fib(n - 1) + fib(n - 2);
}

// ---- Workload 2: string processing (stresses loops + memory access) ----
function makeString(n) {
  let x = 42;
  const chars = new Array(n);
  for (let i = 0; i < n; i++) {
    x = (Math.imul(x, 1664525) + 1013904223) >>> 0; // LCG, mod 2^32
    chars[i] = String.fromCharCode(97 + ((x >>> 16) % 26));
  }
  return chars.join("");
}

function processString(s) {
  // Explicit character loop, matching the C and Python versions.
  const n = s.length;
  const rev = new Array(n);
  let vowels = 0;
  for (let i = 0; i < n; i++) {
    const c = s[i];
    if (c === "a" || c === "e" || c === "i" || c === "o" || c === "u") vowels++;
    rev[n - 1 - i] = c;
  }
  let h = 0;
  for (let i = 0; i < n; i++) h = (Math.imul(h, 31) + rev[i].charCodeAt(0)) >>> 0;
  return vowels * 1000003 + h;
}

function main() {
  const [workload, nStr, trialsStr] = process.argv.slice(2);
  const n = parseInt(nStr, 10);
  const trials = parseInt(trialsStr, 10);
  const s = workload === "string" ? makeString(n) : null;

  const times = [];
  let result = null;
  for (let t = 0; t < trials; t++) {
    const t0 = process.hrtime.bigint();
    result = workload === "fib" ? fib(n) : processString(s);
    const t1 = process.hrtime.bigint();
    times.push(Number(t1 - t0) / 1e6);
  }
  console.log(JSON.stringify({ lang: "JavaScript", workload, n,
    times_ms: times.map((x) => Math.round(x * 1e4) / 1e4), result }));
}

main();
