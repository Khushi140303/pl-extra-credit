/*
 * bench.c — Compiled implementation (C)
 *
 * Usage: ./bench_c <workload> <n> <trials>
 *   workload: fib | string
 *
 * Prints one line of JSON: per-trial times in milliseconds, measured
 * inside the program (so process startup is excluded).
 */
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <stdint.h>
#include <time.h>

/* ---- Workload 1: naive recursive Fibonacci (stresses function calls) ---- */
static long fib(int n) {
    if (n < 2) return n;
    return fib(n - 1) + fib(n - 2);
}

/* ---- Workload 2: string processing (stresses loops + memory access) ----
 * Generate a deterministic pseudo-random lowercase string of length n,
 * then, character by character: count vowels, build the reversed string,
 * and compute a 32-bit hash of the reversed string.
 */
static char *make_string(long n) {
    char *s = malloc(n + 1);
    uint32_t x = 42;
    for (long i = 0; i < n; i++) {
        x = x * 1664525u + 1013904223u;          /* LCG, mod 2^32 */
        s[i] = 'a' + (char)((x >> 16) % 26);
    }
    s[n] = '\0';
    return s;
}

static long process_string(const char *s, long n) {
    char *rev = malloc(n + 1);
    long vowels = 0;
    for (long i = 0; i < n; i++) {
        char c = s[i];
        if (c == 'a' || c == 'e' || c == 'i' || c == 'o' || c == 'u') vowels++;
        rev[n - 1 - i] = c;
    }
    rev[n] = '\0';
    uint32_t h = 0;
    for (long i = 0; i < n; i++) h = h * 31u + (unsigned char)rev[i];
    free(rev);
    return vowels * 1000003L + h;   /* combine so both results are checked */
}

static double now_ms(void) {
    struct timespec ts;
    clock_gettime(CLOCK_MONOTONIC, &ts);
    return ts.tv_sec * 1000.0 + ts.tv_nsec / 1e6;
}

int main(int argc, char **argv) {
    if (argc != 4) { fprintf(stderr, "usage: %s fib|string n trials\n", argv[0]); return 1; }
    const char *workload = argv[1];
    long n = atol(argv[2]);
    int trials = atoi(argv[3]);

    char *s = NULL;
    if (strcmp(workload, "string") == 0) s = make_string(n);

    long result = 0;
    printf("{\"lang\":\"C\",\"workload\":\"%s\",\"n\":%ld,\"times_ms\":[", workload, n);
    for (int t = 0; t < trials; t++) {
        double t0 = now_ms();
        result = (strcmp(workload, "fib") == 0) ? fib((int)n) : process_string(s, n);
        double t1 = now_ms();
        printf("%s%.4f", t ? "," : "", t1 - t0);
    }
    printf("],\"result\":%ld}\n", result);
    free(s);
    return 0;
}
