package ar.edu.itba.sds;

public class Particle {
    private final int id;
    private double x;
    private double y;
    private double vx;
    private double vy;
    private final double radius;
    private final double mass;
    private boolean fresh; // true = FRESH (green), false = USED (violet)
    private int collisionCount; // for event invalidation

    // Fixed obstacle flag
    private final boolean fixed;

    public Particle(int id, double x, double y, double vx, double vy, double radius, double mass, boolean fresh, boolean fixed) {
        this.id = id;
        this.x = x;
        this.y = y;
        this.vx = vx;
        this.vy = vy;
        this.radius = radius;
        this.mass = mass;
        this.fresh = fresh;
        this.fixed = fixed;
        this.collisionCount = 0;
    }

    // Factory for movable particles
    public static Particle createMovable(int id, double x, double y, double vx, double vy, double radius, double mass) {
        return new Particle(id, x, y, vx, vy, radius, mass, true, false);
    }

    // Factory for the fixed obstacle
    public static Particle createObstacle(double x, double y, double radius) {
        return new Particle(-1, x, y, 0, 0, radius, Double.POSITIVE_INFINITY, false, true);
    }

    /**
     * Advance particle position by dt (uniform rectilinear motion)
     */
    public void advance(double dt) {
        if (!fixed) {
            this.x += this.vx * dt;
            this.y += this.vy * dt;
        }
    }

    /**
     * Bounce off another particle (elastic collision)
     */
    public void bounceOff(Particle other) {
        double dx = other.x - this.x;
        double dy = other.y - this.y;
        double dvx = other.vx - this.vx;
        double dvy = other.vy - this.vy;
        double dvdr = dvx * dx + dvy * dy;
        double sigma = this.radius + other.radius;

        if (other.isFixed()) {
            // Collision with fixed obstacle: reflect velocity along normal
            double dist = Math.sqrt(dx * dx + dy * dy);
            double nx = dx / dist;
            double ny = dy / dist;
            double vn = this.vx * nx + this.vy * ny;
            this.vx -= 2 * vn * nx;
            this.vy -= 2 * vn * ny;
            this.collisionCount++;
            other.collisionCount++;
        } else {
            // Elastic collision between two movable particles
            double totalMass = this.mass + other.mass;
            double j = 2 * this.mass * other.mass * dvdr / (sigma * totalMass);
            double jx = j * dx / sigma;
            double jy = j * dy / sigma;

            this.vx += jx / this.mass;
            this.vy += jy / this.mass;
            other.vx -= jx / other.mass;
            other.vy -= jy / other.mass;

            this.collisionCount++;
            other.collisionCount++;
        }
    }

    /**
     * Bounce off the circular wall (specular reflection).
     * The wall is centered at (0,0) with inner radius R = enclosureRadius - particleRadius.
     */
    public void bounceOffWall() {
        double dist = Math.sqrt(x * x + y * y);
        if (dist == 0) return; // at center, shouldn't happen
        // Normal pointing inward (from wall toward center)
        double nx = -x / dist;
        double ny = -y / dist;
        double vn = vx * nx + vy * ny;
        vx -= 2 * vn * nx;
        vy -= 2 * vn * ny;
        this.collisionCount++;
    }

    public double distanceTo(Particle other) {
        double dx = other.x - this.x;
        double dy = other.y - this.y;
        return Math.sqrt(dx * dx + dy * dy);
    }

    public boolean isOverlapping(Particle other) {
        double dist = distanceTo(other);
        return dist < (this.radius + other.radius) * 0.999; // small tolerance
    }

    public double speed() {
        return Math.sqrt(vx * vx + vy * vy);
    }

    public double kineticEnergy() {
        if (fixed) return 0;
        return 0.5 * mass * (vx * vx + vy * vy);
    }

    // Getters and setters
    public int getId() { return id; }
    public double getX() { return x; }
    public double getY() { return y; }
    public double getVx() { return vx; }
    public double getVy() { return vy; }
    public double getRadius() { return radius; }
    public double getMass() { return mass; }
    public boolean isFresh() { return fresh; }
    public boolean isFixed() { return fixed; }
    public int getCollisionCount() { return collisionCount; }

    public void setFresh(boolean fresh) { this.fresh = fresh; }

    public void setX(double x) { this.x = x; }
    public void setY(double y) { this.y = y; }
    public void setVx(double vx) { this.vx = vx; }
    public void setVy(double vy) { this.vy = vy; }

    /**
     * Returns the state as an integer for output:
     * 0 = FRESH, 1 = USED, 2 = FIXED OBSTACLE
     */
    public int getStateCode() {
        if (fixed) return 2;
        return fresh ? 0 : 1;
    }

    @Override
    public String toString() {
        return String.format("Particle{id=%d, pos=(%.4f,%.4f), vel=(%.4f,%.4f), r=%.2f, state=%s}",
                id, x, y, vx, vy, radius, fixed ? "FIXED" : (fresh ? "FRESH" : "USED"));
    }
}
