"""
Exercise 1.3: Fraction of used particles Fu(t) = Nu(t) / N.

For each N:
1. Compute Fu(t) from snapshot data
2. Average Fu(t) across realizations
3. Identify steady-state time and steady-state value Fest
4. Plot Fu(t) for different N
5. Report Fest(N) and time-to-steady-state(N)
"""

import numpy as np
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import os
import csv
import glob

# Configuration
OUTPUT_BASE = os.path.join(os.path.dirname(__file__), "..", "output", "ex2")  # Reuse ex2 data
PLOT_DIR = os.path.join(os.path.dirname(__file__), "..", "output", "ex3")
N_VALUES = [10, 20, 50, 100, 150, 200, 250, 300, 400]
NUM_REALIZATIONS = 10
BASE_SEED = 100


def load_fu_data(output_base, n, seed):
    """Load Fu(t) data from snapshots."""
    snapshot_file = os.path.join(output_base, f"N{n}_seed{seed}", f"snapshots_N{n}_seed{seed}.csv")
    
    if not os.path.exists(snapshot_file):
        return None, None
    
    times = []
    fu_values = []
    
    with open(snapshot_file, 'r') as f:
        reader = csv.DictReader(f)
        for row in reader:
            t = float(row['time'])
            n_used = float(row['N_used'])
            n_total = float(row['N_total'])
            times.append(t)
            fu_values.append(n_used / n_total if n_total > 0 else 0)
    
    return np.array(times), np.array(fu_values)


def find_steady_state(times, fu, window_fraction=0.1, threshold=0.01):
    """
    Find the time to reach steady state and the steady state value.
    Uses a sliding window approach: when the standard deviation within
    the last window_fraction of the data is below threshold * mean,
    we consider it steady.
    """
    if len(times) < 10:
        return times[-1], fu[-1]
    
    # Steady state value: average of last 20% of data
    n_last = max(int(len(fu) * 0.2), 5)
    fest = np.mean(fu[-n_last:])
    
    if fest < 1e-6:
        return times[-1], 0.0
    
    # Find time when Fu first reaches within threshold of Fest
    tol = max(threshold * fest, 0.01)
    t_steady = times[-1]
    
    window_size = max(int(len(fu) * window_fraction), 3)
    
    for i in range(window_size, len(fu)):
        window = fu[i - window_size:i]
        if len(window) > 0 and abs(np.mean(window) - fest) < tol:
            t_steady = times[i - window_size]
            break
    
    return t_steady, fest


def main():
    os.makedirs(PLOT_DIR, exist_ok=True)
    
    # Collect data
    all_fu = {}  # N -> list of (times, fu) tuples
    
    for n in N_VALUES:
        all_fu[n] = []
        for real in range(NUM_REALIZATIONS):
            seed = BASE_SEED + real
            times, fu = load_fu_data(OUTPUT_BASE, n, seed)
            if times is not None:
                all_fu[n].append((times, fu))
    
    # --- Plot 1: Fu(t) for different N values ---
    fig, ax = plt.subplots(figsize=(12, 8))
    
    plot1_n_values = [100, 200, 300,400]
    colors = plt.cm.viridis(np.linspace(0.1, 0.9, len(plot1_n_values)))
    
    for idx, n in enumerate(plot1_n_values):
        if n not in all_fu or not all_fu[n]:
            continue
        
        # Find common time grid for averaging
        min_len = min(len(d[0]) for d in all_fu[n])
        common_times = all_fu[n][0][0][:min_len]
        
        # Stack all realizations
        fu_matrix = np.array([d[1][:min_len] for d in all_fu[n]])
        fu_mean = np.mean(fu_matrix, axis=0)
        fu_std = np.std(fu_matrix, axis=0)
        
        ax.plot(common_times, fu_mean, color=colors[idx], linewidth=2, label=f'N={n}')
        ax.fill_between(common_times, fu_mean - fu_std, fu_mean + fu_std,
                        alpha=0.15, color=colors[idx])
    
    ax.set_xlabel('Tiempo (s)', fontsize=14)
    ax.set_ylabel('$F_u(t) = N_u(t)/N$', fontsize=14)
    ax.set_title('Fracción de partículas usadas vs tiempo', fontsize=16)
    ax.legend(fontsize=11, loc='best')
    ax.grid(True, alpha=0.3)
    ax.tick_params(labelsize=12)
    
    plt.tight_layout()
    plt.savefig(os.path.join(PLOT_DIR, 'Fu_vs_t.png'), dpi=150, bbox_inches='tight')
    
    # --- Compute steady state values ---
    fest_values = {}  # N -> (mean_fest, std_fest, mean_t_steady, std_t_steady)
    
    for n in N_VALUES:
        fests = []
        t_steadys = []
        for times, fu in all_fu[n]:
            t_s, f_s = find_steady_state(times, fu)
            fests.append(f_s)
            t_steadys.append(t_s)
        
        if fests:
            fest_values[n] = (np.mean(fests), np.std(fests), np.mean(t_steadys), np.std(t_steadys))
    
    # --- Plot 2: Fest(N) ---
    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(14, 6))
    
    ns = sorted(fest_values.keys())
    fest_means = [fest_values[n][0] for n in ns]
    fest_stds = [fest_values[n][1] for n in ns]
    t_steady_means = [fest_values[n][2] for n in ns]
    t_steady_stds = [fest_values[n][3] for n in ns]
    
    ax1.errorbar(ns, fest_means, yerr=fest_stds, fmt='o-', capsize=5, linewidth=2,
                 markersize=8, color='#7c3aed', ecolor='#2563eb')
    ax1.set_xlabel('N', fontsize=14)
    ax1.set_ylabel('$F_{est}$', fontsize=14)
    ax1.set_title('Valor estacionario $F_{est}$ vs N', fontsize=16)
    ax1.grid(True, alpha=0.3)
    ax1.tick_params(labelsize=12)
    
    ax2.errorbar(ns, t_steady_means, yerr=t_steady_stds, fmt='s-', capsize=5, linewidth=2,
                 markersize=8, color='#2563eb', ecolor='#7c3aed')
    ax2.set_xlabel('N', fontsize=14)
    ax2.set_ylabel('Tiempo al estacionario (s)', fontsize=14)
    ax2.set_title('Tiempo al estacionario vs N', fontsize=16)
    ax2.grid(True, alpha=0.3)
    ax2.tick_params(labelsize=12)
    
    plt.tight_layout()
    plt.savefig(os.path.join(PLOT_DIR, 'Fest_and_tsteady_vs_N.png'), dpi=150, bbox_inches='tight')
    plt.close(fig)
    
    # Print table
    print(f"\n{'N':>6} | {'Fest':>8} | {'σ_Fest':>8} | {'t_steady':>10} | {'σ_t':>10}")
    print("-" * 55)
    for n in ns:
        vals = fest_values[n]
        print(f"{n:>6} | {vals[0]:>8.4f} | {vals[1]:>8.4f} | {vals[2]:>10.2f} | {vals[3]:>10.2f}")
    
    print(f"\nPlots saved to {PLOT_DIR}/")


if __name__ == "__main__":
    main()
