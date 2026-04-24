"""
Exercise 1.4: Radial profiles of fresh incoming particles (Pfin).

For each N:
1. Read XYZ simulation data frame by frame
2. Select fresh particles (state=0) with radial velocity pointing inward (Rj·vj < 0)
3. Compute radial density <ρ_fin>(S) in concentric layers of width dS=0.2m
4. Compute radial inward velocity <v_fin>(S) = <(Rj·vj)/|Rj|>
5. Compute flux Jin(S) = <ρ_fin>(S) * |<v_fin>(S)|
6. Plot profiles and Jin, ρ_fin, v_fin near S=2 as function of N
"""
from dataclasses import dataclass
from datetime import datetime
import multiprocessing
from multiprocessing.pool import AsyncResult
from time import sleep
from typing import Dict, List, Tuple

import numpy as np
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import os

# Configuration
OUTPUT_BASE = os.path.join(os.path.dirname(__file__), "..", "output", "ex2")  # Reuse ex2 data
PLOT_DIR = os.path.join(os.path.dirname(__file__), "..", "output", "ex4")
N_VALUES = [10, 20, 50, 100, 150, 200]
NUM_REALIZATIONS = 20
BASE_SEED = 100
DS = 0.2  # Layer width
ENCLOSURE_DIAMETER = 80.0
OBSTACLE_RADIUS = 1.0
PARTICLE_RADIUS = 1.0

@dataclass
class Stats():
    sum: float = 0
    sumsquared: float = 0
    count: int = 0

    def register(self, value):
        self.sum += value
        self.sumsquared += value**2
        self.count += 1

    def divide(self, value):
        self.sum = self.sum / value
        self.sumsquared = self.sumsquared / value**2

    def mean_of_sum(self):
        return self.sum / self.count

    def std_of_sum(self):
        return np.sqrt(self.sumsquared / self.count - self.mean_of_sum()**2)

    def runStats(self):
        return self.mean_of_sum(), self.std_of_sum()
    
    def combine(self, other: Stats):
        self.sum += other.sum
        self.sumsquared += other.sumsquared
        self.count += other.count
        return self
    
class parse_xyz_file():
    """
    Parse XYZ extended format file and return list of frames.
    Each frame is a dict with 'time' and 'particles' (array with id, x, y, vx, vy, radius, state).
    """

    def __init__(self, filepath):
        self.file = open(filepath, 'r', buffering=2**27)

    def __del__(self):
        if hasattr(self, 'file'):
            self.file.close()
    
    def __iter__(self):
        return self
    
    def __next__(self):
        # Read number of particles
        line = self.file.readline()
        if not line: raise StopIteration

        n_total = int(line.strip())
        
        # Read properties line
        props_line = self.file.readline().strip()
        
        # Extract time
        time = 0.0
        for part in props_line.split():
            if part.startswith("Time="):
                time = float(part.split("=")[1])
                break
        
        # Read particle data
        particles = []
        for _ in range(n_total):
            pline = self.file.readline().strip()
            if not pline:
                break
            tokens = pline.split()
            pid = int(tokens[0])
            x = float(tokens[1])
            y = float(tokens[2])
            # z = tokens[3]
            vx = float(tokens[4])
            vy = float(tokens[5])
            # vz = tokens[6]
            #radius = float(tokens[7])
            state = int(tokens[8])
            particles.append((pid, x, y, vx, vy, 1, state))
        
        return{
            'time': time,
            'particles': particles
        }

def compute_layers(max_s: float | None = None):
    if max_s is None:
        max_s = ENCLOSURE_DIAMETER / 2.0 - PARTICLE_RADIUS
    
    # Define layer edges
    s_min = OBSTACLE_RADIUS + PARTICLE_RADIUS  # Start outside contact distance 2.0
    s_edges = np.arange(s_min, max_s, DS)
    s_centers = (s_edges[:-1] + s_edges[1:]) / 2.0
    
    # Layer areas (annular rings)
    layer_areas = np.pi * (s_edges[1:] ** 2 - s_edges[:-1] ** 2)
    return s_centers, layer_areas

def compute_radial_profiles(file, s_centers, n):
    """
    Compute radial profiles averaged over all frames.
    
    For each frame and each concentric layer at distance S from center:
    1. Select fresh particles (state=0) with Rj·vj < 0 (moving inward)
    2. Count particles in each layer and compute density ρ = count / area
    3. Compute mean inward velocity v_fin = (Rj·vj)/|Rj|
    
    Returns: S_centers, rho_fin_mean, v_fin_mean, rho_fin_std, v_fin_std
    """
    s_min = OBSTACLE_RADIUS + PARTICLE_RADIUS  # Start outside contact distance 2.0

    frames = parse_xyz_file(file)
    # Accumulate per-layer profiles
    rho = [Stats() for i in range(0, len(s_centers))]  
    vfin = [Stats() for i in range(0, len(s_centers))] 
    
    for frame in frames:   
        counter = [0 for i in range(0, len(s_centers))]     
        for pid, x, y, vx, vy, radius, state in frame['particles']:
            # Only fresh particles
            if state != 0:
                continue
            
            # Radial distance from center
            r_dist = np.sqrt(x * x + y * y)
            if r_dist < 1e-10:
                continue
            
            # Radial velocity (Rj · vj)
            rdotv = x * vx + y * vy
            
            # Only particles moving inward: Rj · vj < 0
            if rdotv >= 0:
                continue
            
            # Find which layer this particle belongs to
            layer_idx = int((r_dist - s_min) / DS)
            if 0 <= layer_idx < len(s_centers):
                # Radial velocity component: v_fin = (Rj·vj) / |Rj|
                v_radial = rdotv / r_dist
                vfin[layer_idx].register(v_radial)
                counter[layer_idx] += 1

        for idx, r in enumerate(rho):
            r.register(counter[idx])
    
    return n, rho, vfin


def main():
    os.makedirs(PLOT_DIR, exist_ok=True)
    
    # Collect radial profiles for each N (averaged over realizations)
    profiles: Dict[int, Tuple[List[Stats], List[Stats]]] = {}  # N -> (rho_mean, vfin_mean)
    centers, areas = compute_layers()

    jobs: List[AsyncResult] = []
    with multiprocessing.Pool(processes=multiprocessing.cpu_count()) as pool:
        for n in N_VALUES[::-1]:
            print(f"Processing N={n}...")
            profiles[n] = ([Stats() for i in centers], [Stats() for i in centers]) #(rho, vfin)

            for real in range(NUM_REALIZATIONS):
                seed = BASE_SEED + real*200
                xyz_file = os.path.join(OUTPUT_BASE, f"N{n}_seed{seed}", f"simulation_N{n}_seed{seed}.xyz")
                
                if not os.path.exists(xyz_file):
                    print(f"  Skipping seed {seed} (file not found)")
                    continue
                
                print(f"  Loading realization {real+1}...")
              
                jobs.append(pool.apply_async(compute_radial_profiles, args=(xyz_file, centers, n)))
                #n, rho, vfin = compute_radial_profiles(frames, centers, n)
        totalJobs = len(jobs)
        initTimestamp = datetime.now()
        print("\033[2K\rPlease wait...", end='')
        while len(jobs):
            for job in jobs:
                if job.ready():
                    ans = job.get()
                    jobs.remove(job)
                    profiles[ans[0]] = ([i.combine(j) for i, j in zip(ans[1], profiles[ans[0]][0])], [i.combine(j) for i, j in zip(ans[2], profiles[ans[0]][1])])
            printText = f"Loaded {totalJobs - len(jobs)} simulations ({(totalJobs-len(jobs))*100/totalJobs:5.2f}%), elapsed: {str(datetime.now() - initTimestamp).split('.')[0]}, remaining: {str((datetime.now() - initTimestamp) / ((totalJobs-len(jobs)+1)/totalJobs) * (len(jobs)) / totalJobs).split('.')[0]}"
            print(f"\033[2K\r\033[7m{printText[0:int(len(printText)*(totalJobs-len(jobs))/totalJobs)]}\033[0m{printText[int(len(printText)*(totalJobs-len(jobs))/totalJobs):]}", end='')
            sleep(1)
        print(f"\nDone.")
            
        for n in profiles:
            for idx, rho in enumerate(profiles[n][0]):
                rho.divide(areas[idx])
    
    if not profiles:
        print("No data to plot.")
        return
    
    # --- Plot 1: Radial profiles for a selected N ---
    for example_n in [100, 200, 300]:
        if example_n not in profiles:
            continue
        
        rho_elem, vfin_elem = profiles[example_n]
        rho = np.array([i.mean_of_sum() for i in rho_elem])
        vfin = np.array([i.mean_of_sum() for i in vfin_elem])
        jin = rho * np.abs(vfin)
        
        fig, (ax1, ax2, ax3) = plt.subplots(3, 1, figsize=(12, 14), sharex=True)
        
        ax1.plot(centers, rho, 'b-', linewidth=2, label='$\\langle \\rho_{fin} \\rangle(S)$')
        #ax1.errorbar(centers, rho, yerr=np.array([i.std_of_sum() for i in rho_elem]),fmt='o-', capsize=5, linewidth=2, markersize=8)
        ax1.set_ylabel('$\\langle \\rho_{fin} \\rangle$ (1/m²)', fontsize=14)
        ax1.set_title(f'Perfiles radiales de partículas frescas entrantes (N={example_n})', fontsize=16)
        ax1.legend(fontsize=12)
        ax1.grid(True, alpha=0.3)
        ax1.tick_params(labelsize=12)
        
        ax2.plot(centers, np.abs(vfin), 'r-', linewidth=2, label='$|\\langle v_{fin} \\rangle(S)|$')
        #ax2.errorbar(centers, np.abs(vfin), yerr=np.array([i.std_of_sum() for i in vfin_elem]), fmt='o-', capsize=5, linewidth=2, markersize=8)
        ax2.set_ylabel('$|\\langle v_{fin} \\rangle|$ (m/s)', fontsize=14)
        ax2.legend(fontsize=12)
        ax2.grid(True, alpha=0.3)
        ax2.tick_params(labelsize=12)
        
        ax3.plot(centers, jin, 'g-', linewidth=2, label='$J_{in}(S)$')
        ax3.set_xlabel('S (distancia radial desde el centro) [m]', fontsize=14)
        ax3.set_ylabel('$J_{in}$ (1/(m·s))', fontsize=14)
        ax3.legend(fontsize=12)
        ax3.grid(True, alpha=0.3)
        ax3.tick_params(labelsize=12)
        
        plt.tight_layout()
        plt.savefig(os.path.join(PLOT_DIR, f'radial_profiles_N{example_n}.png'), dpi=150, bbox_inches='tight')
        plt.close()
    
    # --- Plot 2: All three quantities in one figure for comparison ---
    example_n = max(n for n in profiles.keys())
    rho_elem, vfin_elem = profiles[example_n]
    rho = np.array([i.mean_of_sum() for i in rho_elem])
    vfin = np.array([i.mean_of_sum() for i in vfin_elem])
    jin = rho * np.abs(vfin)
    
    fig, ax = plt.subplots(figsize=(12, 8))
    
    # Normalize for comparison
    rho_norm = rho / np.max(rho) if np.max(rho) > 0 else rho
    vfin_norm = np.abs(vfin) / np.max(np.abs(vfin)) if np.max(np.abs(vfin)) > 0 else np.abs(vfin)
    jin_norm = jin / np.max(jin) if np.max(jin) > 0 else jin
    
    #ax.plot(centers, rho_norm, fmt='b-', linewidth=2, label='$\\langle \\rho_{fin} \\rangle(S)$ (normalizado)')
    ax.plot(centers, rho_norm, 'b-', linewidth=2, label='$\\langle \\rho_{fin} \\rangle(S)$ (normalizado)')
    ax.plot(centers, vfin_norm, 'r-', linewidth=2, label='$|\\langle v_{fin} \\rangle(S)|$ (normalizado)')
    ax.plot(centers, jin_norm, 'g-', linewidth=2, label='$J_{in}(S)$ (normalizado)')

    ax.set_xlabel('S (m)', fontsize=14)
    ax.set_ylabel('Valor normalizado', fontsize=14)
    ax.set_title(f'Perfiles radiales normalizados (N={example_n})', fontsize=16)
    ax.legend(fontsize=12)
    ax.grid(True, alpha=0.3)
    ax.tick_params(labelsize=12)
    
    plt.tight_layout()
    plt.savefig(os.path.join(PLOT_DIR, f'radial_profiles_combined_N{example_n}.png'), dpi=150, bbox_inches='tight')
    plt.close()
    
    # --- Plot 3: Jin, ρ_fin, v_fin at S≈2 as function of N ---
    target_s = 2.0  # S ≈ 2m (near the obstacle contact distance)
    
    ns_plot = []
    jin_at_s2 = []
    rho_at_s2 = []
    rho_sdev_at_s2 = []
    vfin_at_s2 = []
    vfin_sdev_at_s2 = []

    for n in sorted(profiles.keys()):
        rho_elem, vfin_elem = profiles[n]
        rho = np.array([i.mean_of_sum() for i in rho_elem])
        vfin = np.array([i.mean_of_sum() for i in vfin_elem])
        jin = rho * np.abs(vfin)        
        # Find index closest to target_s
        idx = np.argmin(np.abs(centers - target_s))
        
        if abs(centers[idx] - target_s) < DS:  # Within one layer width
            ns_plot.append(n)
            rho_at_s2.append(rho[idx])
            rho_sdev_at_s2.append(rho_elem[idx].std_of_sum())
            vfin_at_s2.append(np.abs(vfin[idx]))
            vfin_sdev_at_s2.append(vfin_elem[idx].std_of_sum())
            jin_at_s2.append(rho[idx] * np.abs(vfin[idx]))
    
    if ns_plot:
        fig, (ax1, ax2, ax3) = plt.subplots(1, 3, figsize=(18, 6))
        
        ax1.plot(ns_plot, jin_at_s2, 'go-', linewidth=2, markersize=8, label='$J_{in}$')
        ax1.set_xlabel('N', fontsize=14)
        ax1.set_ylabel('$J_{in}(S\\approx2)$', fontsize=14)
        ax1.set_title('Flujo entrante', fontsize=14)
        ax1.grid(True, alpha=0.3)
        ax1.tick_params(labelsize=12)
        
        ax2.plot(ns_plot, rho_at_s2, 'bo-', linewidth=2, markersize=8, label='$\\langle \\rho_{fin} \\rangle$')
        #ax2.errorbar(ns_plot, rho_sdev_at_s2)
        ax2.set_xlabel('N', fontsize=14)
        ax2.set_ylabel('$\\langle \\rho_{fin} \\rangle(S\\approx2)$', fontsize=14)
        ax2.set_title('Densidad', fontsize=14)
        ax2.grid(True, alpha=0.3)
        ax2.tick_params(labelsize=12)
        
        ax3.plot(ns_plot, vfin_at_s2, 'ro-', linewidth=2, markersize=8, label='$|\\langle v_{fin} \\rangle|$')
        ax3.set_xlabel('N', fontsize=14)
        ax3.set_ylabel('$|\\langle v_{fin} \\rangle(S\\approx2)|$', fontsize=14)
        ax3.set_title('Velocidad radial', fontsize=14)
        ax3.grid(True, alpha=0.3)
        ax3.tick_params(labelsize=12)
        
        fig.suptitle('Cantidades en S≈2m en función de N', fontsize=16, y=1.02)
        plt.tight_layout()
        plt.savefig(os.path.join(PLOT_DIR, 'radial_at_S2_vs_N.png'), dpi=150, bbox_inches='tight')
        plt.close()
    
    print(f"Plots saved to {PLOT_DIR}/")


if __name__ == "__main__":
    main()
