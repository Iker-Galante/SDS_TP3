package ar.edu.itba.sds;

import java.io.IOException;
import java.util.*;

/**
 * Event-Driven Molecular Dynamics simulation engine.
 * Particles move in uniform rectilinear motion between elastic collisions.
 * The system consists of a circular enclosure with a fixed central obstacle.
 */
public class EventDrivenMD {

    private final List<Particle> particles;
    private final Particle obstacle;
    private final double enclosureDiameter;
    private final double tf; // final simulation time
    private final PriorityQueue<Event> eventQueue;
    private double currentTime;
    private long totalEvents;
    private final OutputWriter writer;

    // For tracking state changes (exercise 1.2)
    private int cumulativeFreshToUsed; // Cfc(t)
    private int used;

    // Output control
    private final double outputInterval; // time interval between output frames
    private double nextOutputTime;

    // Snapshot data for analysis: records (time, Cfc, N_used) at each output frame
    private final List<double[]> snapshots;

    public EventDrivenMD(List<Particle> particles, Particle obstacle, double enclosureDiameter,
                         double tf, double outputInterval, OutputWriter writer) {
        this.particles = particles;
        this.obstacle = obstacle;
        this.enclosureDiameter = enclosureDiameter;
        this.tf = tf;
        this.outputInterval = outputInterval;
        this.writer = writer;
        this.eventQueue = new PriorityQueue<>();
        this.currentTime = 0;
        this.totalEvents = 0;
        this.cumulativeFreshToUsed = 0;
        this.nextOutputTime = 0;
        this.snapshots = new ArrayList<>();
    }

    /**
     * Initialize all possible events at t=0.
     */
    public void initialize() {
        // Calculate all initial events
        for (int i = 0; i < particles.size(); i++) {
            predictCollisions(particles.get(i));
        }
    }

    /**
     * Predict all future collisions for a given particle.
     */
    private void predictCollisions(Particle p) {
        if (p.isFixed()) return;

        // Particle-particle collisions
        for (Particle other : particles) {
            if (p.getId() == other.getId()) continue;
            double dt = CollisionCalculator.timeToParticleCollision(p, other);
            if (currentTime + dt <= tf) {
                eventQueue.add(Event.particleParticle(currentTime + dt, p, other));
            }
        }

        // Particle-wall collision
        double dtWall = CollisionCalculator.timeToWallCollision(p, enclosureDiameter);
        if (currentTime + dtWall <= tf) {
            eventQueue.add(Event.particleWall(currentTime + dtWall, p));
        }

        // Particle-obstacle collision
        double dtObs = CollisionCalculator.timeToObstacleCollision(p, obstacle);
        if (currentTime + dtObs <= tf) {
            eventQueue.add(Event.particleObstacle(currentTime + dtObs, p, obstacle));
        }
    }

    /**
     * Run the simulation.
     */
    public void run() {
        // Write initial state
        writeOutputIfNeeded();

        while (!eventQueue.isEmpty()) {
            Event event = eventQueue.poll();

            // Skip invalid events
            if (!event.isValid()) continue;

            // Check if past final time
            if (event.getTime() > tf) break;

            double dt = event.getTime() - currentTime;

            // Advance all particles to event time
            for (Particle p : particles) {
                p.advance(dt);
            }
            currentTime = event.getTime();

            // Process the collision
            processEvent(event);
            totalEvents++;

            // Write output frames at regular intervals
            writeOutputIfNeeded();
        }

        // Advance to final time and write last frame if needed
        if (currentTime < tf) {
            double dt = tf - currentTime;
            for (Particle p : particles) {
                p.advance(dt);
            }
            currentTime = tf;
            // Force write final state
            recordSnapshot();
            writer.writeFrame(currentTime, particles);
        }
    }

    /**
     * Process a collision event: resolve collision, update states, recalculate events.
     */
    private void processEvent(Event event) {
        Particle a = event.getA();
        String stateChange = "NONE";

        switch (event.getType()) {
            case PARTICLE_PARTICLE:
                Particle b = event.getB();
                a.bounceOff(b);
                writer.writeEvent(currentTime, event.getType(), a.getId(), b.getId(), stateChange);
                // Recalculate events for both particles
                predictCollisions(a);
                predictCollisions(b);
                break;

            case PARTICLE_WALL:
                // Check state change: USED -> FRESH when hitting wall
                if (!a.isFresh()) {
                    a.setFresh(true);
                    stateChange = "USED_TO_FRESH";
                    used--;
                }
                a.bounceOffWall();
                writer.writeEvent(currentTime, event.getType(), a.getId(), -1, stateChange);
                predictCollisions(a);
                break;

            case PARTICLE_OBSTACLE:
                // Check state change: FRESH -> USED when hitting obstacle
                if (a.isFresh()) {
                    a.setFresh(false);
                    cumulativeFreshToUsed++;
                    stateChange = "FRESH_TO_USED";
                    used++;
                }
                a.bounceOff(obstacle);
                writer.writeEvent(currentTime, event.getType(), a.getId(), -1, stateChange);
                predictCollisions(a);
                break;
        }
    }

    /**
     * Write output frame if we've passed the next output time.
     */
    private void writeOutputIfNeeded() {
        if (currentTime >= nextOutputTime && currentTime <= tf) {
            recordSnapshot();
            writer.writeFrame(currentTime, particles);
            nextOutputTime += outputInterval;
        }
    }

    /**
     * Record a snapshot for analysis.
     */
    private void recordSnapshot() {
        // [time, Cfc, N_used]
        snapshots.add(new double[]{currentTime, cumulativeFreshToUsed, used});
    }

    /**
     * Write snapshots to a CSV file for analysis.
     */
    public void writeSnapshots(String outputDir, int n, int seed) throws IOException {
        String file = String.format("%s/snapshots_N%d_seed%d.csv", outputDir, n, seed);
        try (java.io.PrintWriter pw = new java.io.PrintWriter(new java.io.FileWriter(file))) {
            pw.println("time,Cfc,N_used");
            for (double[] s : snapshots) {
                pw.printf(Locale.US, "%.10f,%.0f,%.0f%n", s[0], s[1], s[2]);
            }
        }
    }

    // Accessors
    public double getCurrentTime() { return currentTime; }
    public long getTotalEvents() { return totalEvents; }
    public int getCumulativeFreshToUsed() { return cumulativeFreshToUsed; }
    public List<Particle> getParticles() { return particles; }
}
