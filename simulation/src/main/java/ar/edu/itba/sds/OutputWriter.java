package ar.edu.itba.sds;

import java.io.*;
import java.util.List;
import java.util.Locale;

/**
 * Writes simulation output in XYZ extended format compatible with OVITO.
 * Also writes event logs for analysis.
 */
public class OutputWriter {

    private PrintWriter xyzWriter;
    private PrintWriter eventWriter;
    private final Particle obstacle;
    private final double enclosureDiameter;
    private final boolean saveState;

    public OutputWriter(String outputDir, int n, int seed, Particle obstacle, double enclosureDiameter, boolean saveState) throws IOException {
        this.saveState = saveState;
        this.obstacle = obstacle;
        this.enclosureDiameter = enclosureDiameter;

        File dir = new File(outputDir);
        if (!dir.exists()) dir.mkdirs();

        if (saveState) {
            String xyzFile = String.format("%s/simulation_N%d_seed%d.xyz", outputDir, n, seed);
            String eventFile = String.format("%s/events_N%d_seed%d.csv", outputDir, n, seed);

            this.xyzWriter = new PrintWriter(new BufferedWriter(new FileWriter(xyzFile)));
            this.eventWriter = new PrintWriter(new BufferedWriter(new FileWriter(eventFile)));

            // Write event log header
            eventWriter.println("time,event_type,particle_id,particle_id2,state_change");
        } else {
            this.xyzWriter = null;
            this.eventWriter = null;
        }
    }

    /**
     * Write a frame in XYZ extended format.
     * Includes the obstacle as first entry and boundary particles for the enclosure.
     */
    public void writeFrame(double time, List<Particle> particles) {
        if (!saveState) return;

        // Number of boundary visualization particles
        int nBoundary = 360; // one per degree
        int totalParticles = 1 + particles.size() + nBoundary; // obstacle + particles + boundary

        xyzWriter.printf(Locale.US, "%d%n", totalParticles);
        // Properties line with Lattice for OVITO to recognize the box
        xyzWriter.printf(Locale.US,
                "Lattice=\"%.1f 0.0 0.0 0.0 %.1f 0.0 0.0 0.0 1.0\" " +
                "Properties=id:I:1:pos:R:3:velo:R:3:radius:R:1:state:I:1 " +
                "Time=%.6f%n",
                enclosureDiameter, enclosureDiameter, time);

        // Write obstacle
        xyzWriter.printf(Locale.US, "%d %.6f %.6f 0.0 0.0 0.0 0.0 %.6f %d%n",
                0, obstacle.getX(), obstacle.getY(),
                obstacle.getRadius(), obstacle.getStateCode());

        // Write movable particles
        for (Particle p : particles) {
            xyzWriter.printf(Locale.US, "%d %.6f %.6f 0.0 %.6f %.6f 0.0 %.6f %d%n",
                    p.getId(), p.getX(), p.getY(),
                    p.getVx(), p.getVy(),
                    p.getRadius(), p.getStateCode());
        }

        // Write boundary particles (small, for visualization)
        double R = enclosureDiameter / 2.0;
        for (int i = 0; i < nBoundary; i++) {
            double angle = 2.0 * Math.PI * i / nBoundary;
            double bx = R * Math.cos(angle);
            double by = R * Math.sin(angle);
            xyzWriter.printf(Locale.US, "%d %.6f %.6f 0.0 0.0 0.0 0.0 %.6f %d%n",
                    particles.size() + 1 + i, bx, by, 0.15, 3); // state=3 for boundary
        }

        xyzWriter.flush();
    }

    /**
     * Log an event for analysis.
     * state_change: "FRESH_TO_USED", "USED_TO_FRESH", or "NONE"
     */
    public void writeEvent(double time, Event.Type type, int particleId, int particleId2, String stateChange) {
        if (!saveState) return;
        eventWriter.printf(Locale.US, "%.10f,%s,%d,%d,%s%n",
                time, type.name(), particleId, particleId2, stateChange);
    }

    /**
     * Write a summary line with timing information.
     */
    public void writeTimingSummary(String outputDir, int n, int seed, double tf, long elapsedMs, long totalEvents) throws IOException {
        String timingFile = String.format("%s/timing_N%d_seed%d.csv", outputDir, n, seed);
        try (PrintWriter pw = new PrintWriter(new FileWriter(timingFile))) {
            pw.println("N,seed,tf,elapsed_ms,total_events");
            pw.printf(Locale.US, "%d,%d,%.2f,%d,%d%n", n, seed, tf, elapsedMs, totalEvents);
        }
    }

    public void close() {
        if (xyzWriter != null) xyzWriter.close();
        if (eventWriter != null) eventWriter.close();
    }
}
