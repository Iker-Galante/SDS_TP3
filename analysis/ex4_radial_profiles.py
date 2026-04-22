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

import numpy as np
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import os

# Configuration
OUTPUT_BASE = os.path.join(os.path.dirname(__file__), "..", "output", "ex2")  # Reuse ex2 data
PLOT_DIR = os.path.join(os.path.dirname(__file__), "..", "output", "ex4")
N_VALUES = [10, 20, 50, 100, 150, 200, 250, 300]
NUM_REALIZATIONS = 10
BASE_SEED = 100
DS = 0.2  # Layer width
ENCLOSURE_DIAMETER = 80.0
OBSTACLE_RADIUS = 1.0
PARTICLE_RADIUS = 1.0


def parse_xyz_file(filepath):
    """
    Parse XYZ extended format file and return list of frames.
    Each frame is a dict with 'time' and 'particles' (array with id, x, y, vx, vy, radius, state).
    """
    frames = []
    
    with open(filepath, 'r') as f:
        while True:
            # Read number of particles
            line = f.readline()
            if not line:
                break
            
            try:
                n_total = int(line.strip())
            except ValueError:
                break
            
            # Read properties line
            props_line = f.readline().strip()
            
            # Extract time
            time = 0.0
            for part in props_line.split():
                if part.startswith("Time="):
                    time = float(part.split("=")[1])
                    break
            
            # Read particle data
            particles = []
            for _ in range(n_total):
                pline = f.readline().strip()
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
                radius = float(tokens[7])
                state = int(tokens[8])
                particles.append((pid, x, y, vx, vy, radius, state))
            
            frames.append({
                'time': time,
                'particles': particles
            })
    
    return frames


def compute_radial_profiles(frames, max_s=None):
    """
    Compute radial profiles averaged over all frames.
    
    For each frame and each concentric layer at distance S from center:
    1. Select fresh particles (state=0) with Rj·vj < 0 (moving inward)
    2. Count particles in each layer and compute density ρ = count / area
    3. Compute mean inward velocity v_fin = (Rj·vj)/|Rj|
    
    Returns: S_centers, rho_fin_mean, v_fin_mean, rho_fin_std, v_fin_std
    """
    if max_s is None:
        max_s = ENCLOSURE_DIAMETER / 2.0 - PARTICLE_RADIUS
    
    # Define layer edges
    s_min = OBSTACLE_RADIUS + PARTICLE_RADIUS  # Start outside contact distance 2.0
    s_edges = np.arange(s_min, max_s, DS)
    s_centers = (s_edges[:-1] + s_edges[1:]) / 2.0
    n_layers = len(s_centers)
    
    if n_layers == 0:
        return None, None, None, None, None
    
    # Layer areas (annular rings)
    layer_areas = np.pi * (s_edges[1:] ** 2 - s_edges[:-1] ** 2)
    
    # Accumulate per-frame profiles
    all_rho = []  # shape: (n_frames, n_layers)
    all_vfin = []  # shape: (n_frames, n_layers)
    
    for frame in frames:
        counts = np.zeros(n_layers)
        vfin_sum = np.zeros(n_layers)
        vfin_count = np.zeros(n_layers)
        
        for pid, x, y, vx, vy, radius, state in frame['particles']:
            # Skip non-movable particles (obstacle, boundary)
            if state == 2 or state == 3:
                continue
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
            if 0 <= layer_idx < n_layers:
                counts[layer_idx] += 1
                # Radial velocity component: v_fin = (Rj·vj) / |Rj|
                v_radial = rdotv / r_dist
                vfin_sum[layer_idx] += v_radial
                vfin_count[layer_idx] += 1
        
        # Density in each layer
        rho = counts / layer_areas
        all_rho.append(rho)
        
        # Mean v_fin in each layer (handle empty layers)
        vfin_mean = np.full(n_layers, np.nan)
        for k in range(n_layers):
            if vfin_count[k] > 0:
                vfin_mean[k] = vfin_sum[k] / vfin_count[k]
        all_vfin.append(vfin_mean)
    
    all_rho = np.array(all_rho)
    all_vfin = np.array(all_vfin)
    
    # Average over frames
    rho_mean = np.mean(all_rho, axis=0)
    rho_std = np.std(all_rho, axis=0)
    import warnings
    with warnings.catch_warnings():
        warnings.simplefilter("ignore", category=RuntimeWarning)
        vfin_mean = np.nanmean(all_vfin, axis=0)
        vfin_std = np.nanstd(all_vfin, axis=0)
    
    return s_centers, rho_mean, vfin_mean, rho_std, vfin_std


def main():
    os.makedirs(PLOT_DIR, exist_ok=True)
    
    # Collect radial profiles for each N (averaged over realizations)
    profiles = {}  # N -> (s_centers, rho_mean, vfin_mean)
    
    for n in N_VALUES:
        print(f"Processing N={n}...")
        all_rho_accum = []
        all_vfin_accum = []
        s_centers_ref = None
        
        for real in range(NUM_REALIZATIONS):
            seed = BASE_SEED + real
            xyz_file = os.path.join(OUTPUT_BASE, f"N{n}_seed{seed}", f"simulation_N{n}_seed{seed}.xyz")
            
            if not os.path.exists(xyz_file):
                print(f"  Skipping seed {seed} (file not found)")
                continue
            
            print(f"  Loading realization {real+1}...")
            frames = parse_xyz_file(xyz_file)
            
            if not frames:
                continue
            
            # Skip first 20% of frames (transient)
            start_frame = max(1, len(frames) // 5)
            frames = frames[start_frame:]
            
            s_centers, rho_m, vfin_m, rho_s, vfin_s = compute_radial_profiles(frames)
            
            if s_centers is None:
                continue
            
            s_centers_ref = s_centers
            all_rho_accum.append(rho_m)
            all_vfin_accum.append(vfin_m)
        
        if s_centers_ref is not None and all_rho_accum:
            # Average over realizations
            rho_final = np.mean(all_rho_accum, axis=0)
            import warnings
            with warnings.catch_warnings():
                warnings.simplefilter("ignore", category=RuntimeWarning)
                vfin_final = np.nanmean(all_vfin_accum, axis=0)
                vfin_final = np.nan_to_num(vfin_final, nan=0.0)
            profiles[n] = (s_centers_ref, rho_final, vfin_final)
    
    if not profiles:
        print("No data to plot.")
        return
    
    # --- Plot 1: Radial profiles for a selected N ---
    for example_n in [100, 200, 300]:
        if example_n not in profiles:
            continue
        
        s, rho, vfin = profiles[example_n]
        jin = rho * np.abs(vfin)
        
        fig, (ax1, ax2, ax3) = plt.subplots(3, 1, figsize=(12, 14), sharex=True)
        
        ax1.plot(s, rho, 'b-', linewidth=2, label='$\\langle \\rho_{fin} \\rangle(S)$')
        ax1.set_ylabel('$\\langle \\rho_{fin} \\rangle$ (1/m²)', fontsize=14)
        ax1.set_title(f'Perfiles radiales de partículas frescas entrantes (N={example_n})', fontsize=16)
        ax1.legend(fontsize=12)
        ax1.grid(True, alpha=0.3)
        ax1.tick_params(labelsize=12)
        
        ax2.plot(s, np.abs(vfin), 'r-', linewidth=2, label='$|\\langle v_{fin} \\rangle(S)|$')
        ax2.set_ylabel('$|\\langle v_{fin} \\rangle|$ (m/s)', fontsize=14)
        ax2.legend(fontsize=12)
        ax2.grid(True, alpha=0.3)
        ax2.tick_params(labelsize=12)
        
        ax3.plot(s, jin, 'g-', linewidth=2, label='$J_{in}(S)$')
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
    s, rho, vfin = profiles[example_n]
    jin = rho * np.abs(vfin)
    
    fig, ax = plt.subplots(figsize=(12, 8))
    
    # Normalize for comparison
    rho_norm = rho / np.max(rho) if np.max(rho) > 0 else rho
    vfin_norm = np.abs(vfin) / np.max(np.abs(vfin)) if np.max(np.abs(vfin)) > 0 else np.abs(vfin)
    jin_norm = jin / np.max(jin) if np.max(jin) > 0 else jin
    
    ax.plot(s, rho_norm, 'b-', linewidth=2, label='$\\langle \\rho_{fin} \\rangle(S)$ (normalizado)')
    ax.plot(s, vfin_norm, 'r-', linewidth=2, label='$|\\langle v_{fin} \\rangle(S)|$ (normalizado)')
    ax.plot(s, jin_norm, 'g-', linewidth=2, label='$J_{in}(S)$ (normalizado)')
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
    vfin_at_s2 = []
    
    for n in sorted(profiles.keys()):
        s, rho, vfin = profiles[n]
        
        # Find index closest to target_s
        idx = np.argmin(np.abs(s - target_s))
        
        if abs(s[idx] - target_s) < DS:  # Within one layer width
            ns_plot.append(n)
            rho_at_s2.append(rho[idx])
            vfin_at_s2.append(np.abs(vfin[idx]))
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
