package ar.edu.itba.sds;

import java.io.*;
import java.util.*;

/**
 * Main entry point for the Event-Driven Molecular Dynamics simulation.
 *
 * Usage:
 *   java -jar tp3.jar -N <particles> -tf <final_time> -o <output_dir>
 *                      [-seed <seed>] [-dt <output_interval>]
 *                      [-L <enclosure_diameter>] [-r <particle_radius>]
 *                      [-r0 <obstacle_radius>] [-v0 <initial_speed>]
 *                      [-m <particle_mass>]
 */
public class Main {

    // Default parameters from the problem statement
    private static double L = 80.0;        // enclosure diameter [m]
    private static double r0 = 1.0;        // obstacle radius [m]
    private static double r = 1.0;         // particle radius [m]
    private static double v0 = 1.0;        // initial speed [m/s]
    private static double m = 1.0;         // particle mass [kg]
    private static int N = 100;            // number of particles
    private static double tf = 5.0;        // final time [s]
    private static double dt = 0.05;       // output interval [s]
    private static long seed = 42;         // random seed
    private static String outputDir = "output";

    public static void main(String[] args) {
        parseArgs(args);

        System.out.printf("=== Event-Driven MD Simulation ===%n");
        System.out.printf("N=%d, L=%.1f, r0=%.1f, r=%.1f, v0=%.1f, m=%.1f%n", N, L, r0, r, v0, m);
        System.out.printf("tf=%.1f, dt=%.4f, seed=%d%n", tf, dt, seed);
        System.out.printf("Output: %s%n", outputDir);

        Random rng = new Random(seed);

        // Create the fixed central obstacle
        Particle obstacle = Particle.createObstacle(0.0, 0.0, r0);

        // Generate initial positions (no overlap, inside enclosure, outside obstacle)
        List<Particle> particles = generateInitialConditions(N, rng, obstacle);
        System.out.printf("Generated %d particles successfully%n", particles.size());

        // Setup output writer
        try {
            OutputWriter writer = new OutputWriter(outputDir, N, (int) seed, obstacle, L);

            // Create and run simulation
            EventDrivenMD sim = new EventDrivenMD(particles, obstacle, L, tf, dt, writer);
            sim.initialize();

            long startTime = System.currentTimeMillis();
            sim.run();
            long elapsedMs = System.currentTimeMillis() - startTime;

            System.out.printf("Simulation completed in %d ms (%d events processed)%n",
                    elapsedMs, sim.getTotalEvents());

            // Write analysis data
            sim.writeSnapshots(outputDir, N, (int) seed);
            writer.writeTimingSummary(outputDir, N, (int) seed, tf, elapsedMs, sim.getTotalEvents());
            writer.close();

            // Write particle states for radial profile analysis
            writeParticleStates(outputDir, N, (int) seed, particles);

            System.out.printf("Cumulative fresh-to-used transitions (Cfc): %d%n", sim.getCumulativeFreshToUsed());

        } catch (IOException e) {
            System.err.println("Error writing output: " + e.getMessage());
            e.printStackTrace();
            System.exit(1);
        }
    }

    /**
     * Generate N particles with random positions (no overlap) and random velocity directions.
     */
    private static List<Particle> generateInitialConditions(int n, Random rng, Particle obstacle) {
        List<Particle> particles = new ArrayList<>();
        double maxR = L / 2.0 - r; // max radial distance for particle center
        double minR = r0 + r;       // min radial distance (outside obstacle)
        int maxAttempts = 100000;

        for (int i = 0; i < n; i++) {
            boolean placed = false;
            for (int attempt = 0; attempt < maxAttempts; attempt++) {
                // Random position in the annular region
                // Use sqrt for uniform distribution in area
                double radialDist = Math.sqrt(rng.nextDouble() * (maxR * maxR - minR * minR) + minR * minR);
                double angle = rng.nextDouble() * 2 * Math.PI;
                double px = radialDist * Math.cos(angle);
                double py = radialDist * Math.sin(angle);

                // Random velocity direction, fixed speed
                double vAngle = rng.nextDouble() * 2 * Math.PI;
                double pvx = v0 * Math.cos(vAngle);
                double pvy = v0 * Math.sin(vAngle);

                Particle candidate = Particle.createMovable(i + 1, px, py, pvx, pvy, r, m);

                // Check no overlap with obstacle
                if (candidate.isOverlapping(obstacle)) continue;

                // Check no overlap with existing particles
                boolean overlaps = false;
                for (Particle existing : particles) {
                    if (candidate.isOverlapping(existing)) {
                        overlaps = true;
                        break;
                    }
                }
                if (overlaps) continue;

                // Check inside enclosure
                double dist = Math.sqrt(px * px + py * py);
                if (dist + r > L / 2.0) continue;

                particles.add(candidate);
                placed = true;
                break;
            }
            if (!placed) {
                System.err.printf("Could not place particle %d after %d attempts. " +
                        "Try fewer particles or a larger enclosure.%n", i + 1, maxAttempts);
                System.exit(1);
            }
        }
        return particles;
    }

    /**
     * Write final particle states for radial profile analysis (exercise 1.4).
     */
    private static void writeParticleStates(String outputDir, int n, int seed, List<Particle> particles) throws IOException {
        // This is handled by the snapshot/XYZ output - no separate file needed
        // The XYZ file contains all the needed data at each timestep
    }

    /**
     * Parse command-line arguments.
     */
    private static void parseArgs(String[] args) {
        for (int i = 0; i < args.length; i++) {
            switch (args[i]) {
                case "-N":
                    N = Integer.parseInt(args[++i]);
                    break;
                case "-tf":
                    tf = Double.parseDouble(args[++i]);
                    break;
                case "-o":
                    outputDir = args[++i];
                    break;
                case "-seed":
                    seed = Long.parseLong(args[++i]);
                    break;
                case "-dt":
                    dt = Double.parseDouble(args[++i]);
                    break;
                case "-L":
                    L = Double.parseDouble(args[++i]);
                    break;
                case "-r":
                    r = Double.parseDouble(args[++i]);
                    break;
                case "-r0":
                    r0 = Double.parseDouble(args[++i]);
                    break;
                case "-v0":
                    v0 = Double.parseDouble(args[++i]);
                    break;
                case "-m":
                    m = Double.parseDouble(args[++i]);
                    break;
                case "-h":
                case "--help":
                    printHelp();
                    System.exit(0);
                    break;
                default:
                    System.err.println("Unknown argument: " + args[i]);
                    printHelp();
                    System.exit(1);
            }
        }
    }

    private static void printHelp() {
        System.out.println("Usage: java -jar tp3.jar [options]");
        System.out.println("Options:");
        System.out.println("  -N <int>        Number of particles (default: 100)");
        System.out.println("  -tf <double>    Final simulation time in seconds (default: 5.0)");
        System.out.println("  -o <dir>        Output directory (default: output)");
        System.out.println("  -seed <long>    Random seed (default: 42)");
        System.out.println("  -dt <double>    Output time interval in seconds (default: 0.05)");
        System.out.println("  -L <double>     Enclosure diameter in meters (default: 80.0)");
        System.out.println("  -r <double>     Particle radius in meters (default: 1.0)");
        System.out.println("  -r0 <double>    Obstacle radius in meters (default: 1.0)");
        System.out.println("  -v0 <double>    Initial speed in m/s (default: 1.0)");
        System.out.println("  -m <double>     Particle mass in kg (default: 1.0)");
        System.out.println("  -h, --help      Show this help message");
    }
}
