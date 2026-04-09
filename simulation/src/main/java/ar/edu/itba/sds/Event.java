package ar.edu.itba.sds;

/**
 * Represents a collision event in the Event-Driven Molecular Dynamics simulation.
 * Events are ordered by time and validated using collision counts.
 */
public class Event implements Comparable<Event> {

    public enum Type {
        PARTICLE_PARTICLE,   // collision between two movable particles
        PARTICLE_WALL,       // collision with the circular enclosure wall
        PARTICLE_OBSTACLE    // collision with the fixed central obstacle
    }

    private final double time;
    private final Type type;
    private final Particle a; // first particle (always present)
    private final Particle b; // second particle (null for wall collisions)
    private final int countA; // collision count of particle a when event was created
    private final int countB; // collision count of particle b when event was created

    public Event(double time, Type type, Particle a, Particle b) {
        this.time = time;
        this.type = type;
        this.a = a;
        this.b = b;
        this.countA = (a != null) ? a.getCollisionCount() : -1;
        this.countB = (b != null) ? b.getCollisionCount() : -1;
    }

    // Factory methods
    public static Event particleParticle(double time, Particle a, Particle b) {
        return new Event(time, Type.PARTICLE_PARTICLE, a, b);
    }

    public static Event particleWall(double time, Particle p) {
        return new Event(time, Type.PARTICLE_WALL, p, null);
    }

    public static Event particleObstacle(double time, Particle p, Particle obstacle) {
        return new Event(time, Type.PARTICLE_OBSTACLE, p, obstacle);
    }

    /**
     * Check if this event is still valid (no intervening collisions have occurred).
     */
    public boolean isValid() {
        if (a != null && a.getCollisionCount() != countA) return false;
        if (b != null && b.getCollisionCount() != countB) return false;
        return true;
    }

    @Override
    public int compareTo(Event other) {
        return Double.compare(this.time, other.time);
    }

    // Getters
    public double getTime() { return time; }
    public Type getType() { return type; }
    public Particle getA() { return a; }
    public Particle getB() { return b; }

    @Override
    public String toString() {
        return String.format("Event{t=%.6f, type=%s, a=%d, b=%s}",
                time, type,
                a != null ? a.getId() : -1,
                b != null ? String.valueOf(b.getId()) : "wall");
    }
}
