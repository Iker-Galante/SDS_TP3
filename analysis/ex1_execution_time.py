"""
Exercise 1.1: Execution time as a function of N.
Runs simulations for different N values and plots the execution time.
"""

import subprocess
import numpy as np
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import os
import csv
import sys

# Configuration
JAR_PATH = os.path.join(os.path.dirname(__file__), "..", "simulation", "target", "tp3-scanning-rate-1.0-SNAPSHOT.jar")
OUTPUT_BASE = os.path.join(os.path.dirname(__file__), "..", "output", "ex1")
TF = 500.0  # Fixed final simulation time (extended to 500s para mayor estadística)
DT = 0.1  # Output interval
N_VALUES = [10, 20, 50, 100, 150, 200, 250, 300]
SEEDS = [42, 123, 456, 789, 1024]  # Multiple seeds for averaging


def run_simulation(n, tf, seed, output_dir):
    """Run a single simulation and return the elapsed time in ms."""
    cmd = [
        "java", "-jar", JAR_PATH,
        "-N", str(n),
        "-tf", str(tf),
        "-dt", str(DT),
        "-o", output_dir,
        "-seed", str(seed),
        "-no-save"
    ]
    
    result = subprocess.run(cmd, capture_output=True, text=True)
    
    if result.returncode != 0:
        print(f"Error running N={n}, seed={seed}: {result.stderr}")
        return None
    
    # Parse timing from output
    timing_file = os.path.join(output_dir, f"timing_N{n}_seed{seed}.csv")
    with open(timing_file, 'r') as f:
        reader = csv.DictReader(f)
        for row in reader:
            return int(row['elapsed_ms'])
    
    return None


def main():
    os.makedirs(OUTPUT_BASE, exist_ok=True)
    
    print("Nota: NO se están guardando los estados del sistema durante esta simulación.")
    print("Esto se debe a que para TF grande y valores de N altos, puede volverse muy costoso el uso de I/O y espacio en disco.\n")

    results = {}  # N -> list of elapsed_ms
    
    for n in N_VALUES:
        results[n] = []
        for seed in SEEDS:
            out_dir = os.path.join(OUTPUT_BASE, f"N{n}_seed{seed}")
            print(f"Running N={n}, seed={seed}...")
            elapsed = run_simulation(n, TF, seed, out_dir)
            if elapsed is not None:
                results[n].append(elapsed)
                print(f"  -> {elapsed} ms")
    
    # Plot results
    fig, ax = plt.subplots(figsize=(10, 7))
    
    ns = sorted(results.keys())
    means = [np.mean(results[n]) for n in ns]
    stds = [np.std(results[n]) for n in ns]
    
    ax.errorbar(ns, means, yerr=stds, fmt='o-', capsize=5, linewidth=2, markersize=8,
                color='#2563eb', ecolor='#7c3aed', markerfacecolor='#7c3aed')
    
    ax.set_xlabel('Número de partículas (N)', fontsize=14)
    ax.set_ylabel('Tiempo de ejecución (ms)', fontsize=14)
    ax.set_title(f'Tiempo de ejecución vs N (tf={TF}s)', fontsize=16)
    ax.grid(True, alpha=0.3)
    ax.tick_params(labelsize=12)
    
    plt.tight_layout()
    plt.savefig(os.path.join(OUTPUT_BASE, 'execution_time_vs_N.png'), dpi=150, bbox_inches='tight')
    print(f"Plot saved to {OUTPUT_BASE}/execution_time_vs_N.png")
    
    # Print table
    print(f"\n{'N':>6} | {'Mean (ms)':>10} | {'Std (ms)':>10}")
    print("-" * 35)
    for n in ns:
        print(f"{n:>6} | {np.mean(results[n]):>10.1f} | {np.std(results[n]):>10.1f}")


if __name__ == "__main__":
    main()
