package ar.edu.itba.sds;

/**
 * Computes collision times analytically for Event-Driven Molecular Dynamics.
 * All collisions involve particles moving in uniform rectilinear motion.
 */
public class CollisionCalculator {

    private static final double EPS = 1e-10;

    /**
     * Time until two movable particles collide.
     * Returns Double.POSITIVE_INFINITY if they never collide.
     *
     * Solves: |r_i(t) - r_j(t)| = sigma, where sigma = r_i + r_j
     * With r_i(t) = r_i + v_i * dt, same for j.
     * Let dr = r_j - r_i, dv = v_j - v_i
     * |dr + dv*dt|^2 = sigma^2
     * |dv|^2 dt^2 + 2(dr.dv)dt + (|dr|^2 - sigma^2) = 0
     */
    public static double timeToParticleCollision(Particle p1, Particle p2) {
        double dx = p2.getX() - p1.getX();
        double dy = p2.getY() - p1.getY();
        double dvx = p2.getVx() - p1.getVx();
        double dvy = p2.getVy() - p1.getVy();

        double sigma = p1.getRadius() + p2.getRadius();

        double dvdr = dvx * dx + dvy * dy;
        // Particles must be approaching each other
        if (dvdr >= 0) return Double.POSITIVE_INFINITY;

        double dvdv = dvx * dvx + dvy * dvy;
        double drdr = dx * dx + dy * dy;

        double d = dvdr * dvdr - dvdv * (drdr - sigma * sigma);
        // No real solution: particles never meet
        if (d < 0) return Double.POSITIVE_INFINITY;

        double dt = -(dvdr + Math.sqrt(d)) / dvdv;
        if (dt < EPS) return Double.POSITIVE_INFINITY;

        return dt;
    }

    /**
     * Time until particle collides with the circular enclosure wall.
     * The enclosure is centered at origin with diameter L, so wall radius = L/2.
     * The particle center must stay at distance >= radius from the wall,
     * so the effective radius is R_eff = L/2 - particle.radius.
     *
     * Solves: |r(t)|^2 = R_eff^2
     * |(x + vx*dt, y + vy*dt)|^2 = R_eff^2
     * (vx^2+vy^2)dt^2 + 2(x*vx+y*vy)dt + (x^2+y^2 - R_eff^2) = 0
     *
     * We want the smallest positive root (the particle hits the wall from inside).
     */
    public static double timeToWallCollision(Particle p, double enclosureDiameter) {
        double rEff = enclosureDiameter / 2.0 - p.getRadius();

        double x = p.getX();
        double y = p.getY();
        double vx = p.getVx();
        double vy = p.getVy();

        double a = vx * vx + vy * vy;
        if (a < EPS) return Double.POSITIVE_INFINITY; // stationary particle

        double b = x * vx + y * vy;
        double c = x * x + y * y - rEff * rEff;

        double discriminant = b * b - a * c;
        if (discriminant < 0) return Double.POSITIVE_INFINITY;

        double sqrtD = Math.sqrt(discriminant);

        // Two roots: (-b ± sqrt(d)) / a
        // We want the smallest positive one
        // Since particle is inside the circle, c < 0 (or ~0 if at the wall)
        // The positive root is (-b + sqrtD) / a
        double t1 = (-b - sqrtD) / a;
        double t2 = (-b + sqrtD) / a;

        // t2 should be the one where the particle exits (hits wall from inside)
        if (t2 > EPS) return t2;
        if (t1 > EPS) return t1;

        return Double.POSITIVE_INFINITY;
    }

    /**
     * Time until particle collides with the fixed central obstacle.
     * The obstacle is at origin with radius r0.
     * Contact occurs when center-to-center distance = r0 + particle.radius.
     *
     * Solves: |r(t)|^2 = (r0 + r_p)^2
     * Same quadratic as wall, but we want the particle to approach from outside.
     */
    public static double timeToObstacleCollision(Particle p, Particle obstacle) {
        double contactDist = obstacle.getRadius() + p.getRadius();

        // Relative position from obstacle center
        double dx = p.getX() - obstacle.getX();
        double dy = p.getY() - obstacle.getY();
        double vx = p.getVx();
        double vy = p.getVy();

        double a = vx * vx + vy * vy;
        if (a < EPS) return Double.POSITIVE_INFINITY;

        double b = dx * vx + dy * vy;
        // Particle must be moving toward the obstacle
        if (b >= 0) return Double.POSITIVE_INFINITY;

        double c = dx * dx + dy * dy - contactDist * contactDist;

        double discriminant = b * b - a * c;
        if (discriminant < 0) return Double.POSITIVE_INFINITY;

        double sqrtD = Math.sqrt(discriminant);

        // We want the smallest positive root (first contact)
        double t1 = (-b - sqrtD) / a;
        double t2 = (-b + sqrtD) / a;

        if (t1 > EPS) return t1;
        if (t2 > EPS) return t2;

        return Double.POSITIVE_INFINITY;
    }
}
