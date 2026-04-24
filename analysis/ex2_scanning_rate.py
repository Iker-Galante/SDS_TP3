"""
Exercise 1.2: Scanning Rate (J) as a function of N.

For each N, runs multiple realizations and:
1. Computes Cfc(t) - cumulative count of fresh particles that become used
2. Fits a linear interpolation to Cfc(t) to get the scanning rate J (slope)
3. Computes mean and std of J across realizations
4. Plots <J>(N) with error bars
"""

from datetime import datetime
import subprocess
from time import sleep
import numpy as np
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import os
import csv
from scipy import stats
import multiprocessing
from multiprocessing.pool import ThreadPool

# Configuration
JAR_PATH = os.path.join(os.path.dirname(__file__), "..", "simulation", "target", "tp3-scanning-rate-1.0-SNAPSHOT.jar")
OUTPUT_BASE = os.path.join(os.path.dirname(__file__), "..", "output", "ex2")
TF = 2000.0  # Longer simulation for better statistics
DT = 0.0   # Output interval
N_VALUES = [10, 20, 50, 100, 150, 200, 250, 300, 400]
NUM_REALIZATIONS = 5
BASE_SEED = 100


def run_simulation(n, tf, seed, output_dir):
    """Run a single simulation."""
    cmd = [
        "java", "-jar", JAR_PATH,
        "-N", str(n),
        "-tf", str(tf),
        "-dt", str(DT),
        "-o", output_dir,
        "-seed", str(seed)
    ]
    
    result = subprocess.run(cmd, capture_output=True, text=True)
    if result.returncode != 0:
        print(f"Error: {result.stderr}")
        return False
    return True


def load_snapshots(output_dir, n, seed):
    """Load snapshot data and return (time, Cfc) arrays."""
    snapshot_file = os.path.join(output_dir, f"snapshots_N{n}_seed{seed}.csv")
    times = []
    cfc_values = []
    
    with open(snapshot_file, 'r') as f:
        reader = csv.DictReader(f)
        for row in reader:
            times.append(float(row['time']))
            cfc_values.append(float(row['Cfc']))
    
    return np.array(times), np.array(cfc_values)


def compute_scanning_rate(times, cfc):
    """Compute scanning rate J as the slope of linear fit of Cfc(t)."""
    if len(times) < 2:
        return 0.0
    
    # Use linear regression
    slope, intercept, r_value, p_value, std_err = stats.linregress(times, cfc)
    return slope


def main():
    os.makedirs(OUTPUT_BASE, exist_ok=True)
    
    all_J = {}  # N -> list of J values across realizations
    jobs = []

    with ThreadPool(processes=multiprocessing.cpu_count()) as pool:
        for n in N_VALUES:
            for real in range(NUM_REALIZATIONS):
                seed = BASE_SEED + real
                out_dir = os.path.join(OUTPUT_BASE, f"N{n}_seed{seed}")
                print(f"Running N={n}, realization {real+1}/{NUM_REALIZATIONS} (seed={seed})...")
                jobs.append(pool.apply_async(run_simulation, args=(n, TF, seed, out_dir)))

        totalJobs = len(jobs)
        print(totalJobs)
        initTimestamp = datetime.now()
        print("\033[2K\rPlease wait...", end='')
        while len(jobs):
            for job in jobs:
                if job.ready():
                    ans = job.get()
                    jobs.remove(job)
                    printText = f"Ran {totalJobs - len(jobs)} jobs ({(totalJobs-len(jobs))*100/totalJobs:5.2f}%), elapsed: {str(datetime.now() - initTimestamp).split('.')[0]}, remaining: {str((datetime.now() - initTimestamp) / ((totalJobs-len(jobs)+1)/totalJobs) * (len(jobs)) / totalJobs).split('.')[0]}"
                    print(f"\033[2K\r\033[7m{printText[0:int(len(printText)*(totalJobs-len(jobs))/totalJobs)]}\033[0m{printText[int(len(printText)*(totalJobs-len(jobs))/totalJobs):]}", end='')
                    if not ans:
                        print("Something went wrong")
                        return
            sleep(1)
        print(f"\nDone.")
        for n in N_VALUES:
            all_J[n] = []
            for real in range(NUM_REALIZATIONS):
                seed = BASE_SEED + real
                out_dir = os.path.join(OUTPUT_BASE, f"N{n}_seed{seed}")
                times, cfc = load_snapshots(out_dir, n, seed)
                J = compute_scanning_rate(times, cfc)
                all_J[n].append(J)
                print(f"  Cfc_final={cfc[-1]:.0f}, J={J:.4f}")
    
    # --- Plot 1: Example Cfc(t) for one N ---
    example_n = 200
    if example_n in all_J:
        fig, ax = plt.subplots(figsize=(10, 7))
        for real in range(min(3, NUM_REALIZATIONS)):
            seed = BASE_SEED + real
            out_dir = os.path.join(OUTPUT_BASE, f"N{example_n}_seed{seed}")
            times, cfc = load_snapshots(out_dir, example_n, seed)
            ax.plot(times, cfc, alpha=0.7, label=f'Realización {real+1}')
        
        ax.set_xlabel('Tiempo (s)', fontsize=14)
        ax.set_ylabel('$C_{fc}(t)$', fontsize=14)
        ax.set_title(f'Conteo acumulado de cambios fresco→usado (N={example_n})', fontsize=16)
        ax.legend(fontsize=12)
        ax.grid(True, alpha=0.3)
        ax.tick_params(labelsize=12)
        plt.tight_layout()
        plt.savefig(os.path.join(OUTPUT_BASE, f'Cfc_vs_t_N{example_n}.png'), dpi=150, bbox_inches='tight')
        plt.close()
    
    # --- Plot 2: <J>(N) with error bars ---
    fig, ax = plt.subplots(figsize=(10, 7))
    
    ns = sorted(all_J.keys())
    J_means = [np.mean(all_J[n]) for n in ns]
    J_stds = [np.std(all_J[n]) for n in ns]
    
    ax.errorbar(ns, J_means, yerr=J_stds, fmt='s-', capsize=5, linewidth=2, markersize=8,
                color='#2563eb', ecolor='#7c3aed', markerfacecolor='#7c3aed')
    
    ax.set_xlabel('Número de partículas (N)', fontsize=14)
    ax.set_ylabel('$\\langle J \\rangle$ (scanning rate) [1/s]', fontsize=14)
    ax.set_title('Scanning Rate vs N', fontsize=16)
    ax.grid(True, alpha=0.3)
    ax.tick_params(labelsize=12)
    
    plt.tight_layout()
    plt.savefig(os.path.join(OUTPUT_BASE, 'scanning_rate_vs_N.png'), dpi=150, bbox_inches='tight')
    plt.close()
    
    # Print table
    print(f"\n{'N':>6} | {'<J>':>10} | {'σ_J':>10}")
    print("-" * 35)
    for n in ns:
        print(f"{n:>6} | {np.mean(all_J[n]):>10.4f} | {np.std(all_J[n]):>10.4f}")
    
    print(f"\nPlots saved to {OUTPUT_BASE}/")


if __name__ == "__main__":
    main()
