import pygame
import math
import random
import sys


# ============================================================
# N-BODY GRAVITATIONAL SIMULATION
# Version 1.0
# ============================================================

pygame.init()

# ------------------------------------------------------------
# DISPLAY
# ------------------------------------------------------------

screen = pygame.display.set_mode((0, 0), pygame.FULLSCREEN)
pygame.display.set_caption("N-Body Gravitational Simulation")

WIDTH, HEIGHT = screen.get_size()

clock = pygame.time.Clock()

# ------------------------------------------------------------
# FONTS
# ------------------------------------------------------------

font_large = pygame.font.SysFont("arial", 42, bold=True)
font_medium = pygame.font.SysFont("arial", 28)
font_small = pygame.font.SysFont("arial", 20)
font_tiny = pygame.font.SysFont("arial", 16)

# ------------------------------------------------------------
# COLOURS
# ------------------------------------------------------------

BLACK = (5, 5, 10)
WHITE = (240, 240, 240)
GREY = (150, 150, 150)
DARK_GREY = (70, 70, 80)
YELLOW = (255, 220, 80)

BODY_COLOURS = [
    (255, 80, 80),       # Red
    (80, 160, 255),      # Blue
    (100, 255, 120),     # Green
    (255, 170, 60),      # Orange
    (210, 100, 255),     # Purple
    (255, 100, 200),     # Pink
    (80, 230, 220),      # Cyan
    (255, 255, 100),     # Yellow
    (160, 160, 255),     # Light blue
    (180, 255, 150),     # Light green
]

# ------------------------------------------------------------
# PHYSICS CONSTANTS
# ------------------------------------------------------------

# This is a scaled gravitational constant.
#
# We deliberately don't use real SI units because the screen
# operates in arbitrary "simulation units".
#
# The important thing is that Newtonian gravity is calculated
# consistently between all bodies.

G = 1800.0

# Physics time multiplier.
#
# Increasing this makes the simulation run faster in simulated
# time while the rendering remains smooth.

TIME_SCALE = 1.0

# Number of physics calculations performed per rendered frame.
#
# Higher values improve stability, particularly when bodies
# come close together.

PHYSICS_SUBSTEPS = 6

# Base simulation timestep.

DT = 0.0018

# Small gravitational softening value.
#
# This prevents the acceleration approaching infinity when two
# bodies get extremely close together. It is very small compared
# with the normal orbital distances.

SOFTENING = 12.0

# Maximum trail length.

MAX_TRAIL_POINTS = 350

# ------------------------------------------------------------
# VIEW / WORLD SCALE
# ------------------------------------------------------------

# Simulation coordinates are centred around the middle of the
# screen.

WORLD_SCALE = min(WIDTH, HEIGHT) * 0.40

CENTER_X = WIDTH / 2
CENTER_Y = HEIGHT / 2


# ============================================================
# BODY CLASS
# ============================================================

class Body:

    def __init__(self, x, y, vx, vy, mass, radius, colour):

        self.x = x
        self.y = y

        self.vx = vx
        self.vy = vy

        self.mass = mass
        self.radius = radius

        self.colour = colour

        self.ax = 0.0
        self.ay = 0.0

        self.trail = []

    def screen_position(self):

        sx = int(CENTER_X + self.x)
        sy = int(CENTER_Y + self.y)

        return sx, sy


# ============================================================
# CALCULATE ACCELERATIONS
# ============================================================

def calculate_accelerations(bodies):

    for body in bodies:

        body.ax = 0.0
        body.ay = 0.0

    # Every body interacts with every other body.
    #
    # This is the actual N-body calculation.

    for i in range(len(bodies)):

        a = bodies[i]

        for j in range(i + 1, len(bodies)):

            b = bodies[j]

            dx = b.x - a.x
            dy = b.y - a.y

            distance_squared = dx * dx + dy * dy

            # Softened distance.
            softened_distance_squared = (
                distance_squared +
                SOFTENING * SOFTENING
            )

            distance = math.sqrt(softened_distance_squared)

            if distance == 0:
                continue

            # Newtonian gravitational acceleration.
            #
            # Acceleration of A caused by B:
            #
            #     a = G * M / r²
            #
            # Using the direction vector gives:
            #
            #     ax = G * M * dx / r³

            force_factor = G / (
                softened_distance_squared * distance
            )

            ax_a = force_factor * b.mass * dx
            ay_a = force_factor * b.mass * dy

            ax_b = -force_factor * a.mass * dx
            ay_b = -force_factor * a.mass * dy

            a.ax += ax_a
            a.ay += ay_a

            b.ax += ax_b
            b.ay += ay_b


# ============================================================
# LEAPFROG INTEGRATOR
# ============================================================

def physics_step(bodies, dt):

    # Calculate acceleration at current position.

    calculate_accelerations(bodies)

    # First half velocity update.

    for body in bodies:

        body.vx += body.ax * dt * 0.5
        body.vy += body.ay * dt * 0.5

    # Position update.

    for body in bodies:

        body.x += body.vx * dt
        body.y += body.vy * dt

    # Calculate new acceleration.

    calculate_accelerations(bodies)

    # Second half velocity update.

    for body in bodies:

        body.vx += body.ax * dt * 0.5
        body.vy += body.ay * dt * 0.5


# ============================================================
# CREATE INITIAL SYSTEM
# ============================================================

def create_system(number_of_bodies):

    bodies = []

    # --------------------------------------------------------
    # CENTRAL MASS
    # --------------------------------------------------------

    # For larger systems, create a somewhat heavier central body
    # so that we get an interesting initial gravitational system.

    central_mass = 900.0

    central = Body(
        0.0,
        0.0,
        0.0,
        0.0,
        central_mass,
        11,
        BODY_COLOURS[0]
    )

    bodies.append(central)

    # --------------------------------------------------------
    # ORBITING BODIES
    # --------------------------------------------------------

    for i in range(1, number_of_bodies):

        # Spread bodies around the centre.

        angle = (
            (2.0 * math.pi * (i - 1) /
             max(1, number_of_bodies - 1))
        )

        # Randomise the orbital distance slightly.

        radius = random.uniform(
            WORLD_SCALE * 0.22,
            WORLD_SCALE * 0.72
        )

        x = math.cos(angle) * radius
        y = math.sin(angle) * radius

        # Different bodies have slightly different masses.

        mass = random.uniform(20.0, 65.0)

        # Circular orbital velocity around the central mass.
        #
        # v = sqrt(GM/r)

        orbital_velocity = math.sqrt(
            G * central_mass / radius
        )

        # Add a small variation so the system isn't perfectly
        # symmetrical.

        velocity_variation = random.uniform(0.92, 1.08)

        orbital_velocity *= velocity_variation

        # Tangential velocity.

        vx = -math.sin(angle) * orbital_velocity
        vy = math.cos(angle) * orbital_velocity

        # Small random perturbation.

        vx += random.uniform(-2.0, 2.0)
        vy += random.uniform(-2.0, 2.0)

        body = Body(
            x,
            y,
            vx,
            vy,
            mass,
            random.randint(6, 9),
            BODY_COLOURS[i % len(BODY_COLOURS)]
        )

        bodies.append(body)

    # --------------------------------------------------------
    # MOVE SYSTEM SO CENTRE OF MASS IS STATIONARY
    # --------------------------------------------------------

    total_mass = sum(body.mass for body in bodies)

    centre_x = sum(
        body.x * body.mass
        for body in bodies
    ) / total_mass

    centre_y = sum(
        body.y * body.mass
        for body in bodies
    ) / total_mass

    centre_vx = sum(
        body.vx * body.mass
        for body in bodies
    ) / total_mass

    centre_vy = sum(
        body.vy * body.mass
        for body in bodies
    ) / total_mass

    for body in bodies:

        body.x -= centre_x
        body.y -= centre_y

        body.vx -= centre_vx
        body.vy -= centre_vy

    return bodies


# ============================================================
# DRAW STARFIELD
# ============================================================

def create_starfield():

    stars = []

    for _ in range(250):

        x = random.randint(0, WIDTH - 1)
        y = random.randint(0, HEIGHT - 1)

        brightness = random.randint(50, 150)

        stars.append(
            (x, y, brightness)
        )

    return stars


stars = create_starfield()


def draw_starfield():

    for x, y, brightness in stars:

        pygame.draw.circle(
            screen,
            (brightness, brightness, brightness),
            (x, y),
            1
        )


# ============================================================
# DRAW BODIES
# ============================================================

def draw_bodies(bodies, show_trails=True):

    for body in bodies:

        # ----------------------------------------------------
        # TRAIL
        # ----------------------------------------------------

        if show_trails and len(body.trail) > 1:

            pygame.draw.lines(
                screen,
                body.colour,
                False,
                body.trail,
                1
            )

        # ----------------------------------------------------
        # BODY
        # ----------------------------------------------------

        sx, sy = body.screen_position()

        # Glow effect.

        glow_radius = body.radius + 6

        glow_surface = pygame.Surface(
            (
                glow_radius * 2 + 2,
                glow_radius * 2 + 2
            ),
            pygame.SRCALPHA
        )

        pygame.draw.circle(
            glow_surface,
            (*body.colour, 35),
            (glow_radius, glow_radius),
            glow_radius
        )

        screen.blit(
            glow_surface,
            (
                sx - glow_radius,
                sy - glow_radius
            )
        )

        pygame.draw.circle(
            screen,
            body.colour,
            (sx, sy),
            body.radius
        )

        # Small white highlight.

        highlight_radius = max(1, body.radius // 3)

        pygame.draw.circle(
            screen,
            (255, 255, 255),
            (
                sx - body.radius // 3,
                sy - body.radius // 3
            ),
            highlight_radius
        )


# ============================================================
# SELECTION SCREEN
# ============================================================

def selection_screen():

    selected = 3

    running = True

    while running:

        clock.tick(60)

        for event in pygame.event.get():

            if event.type == pygame.QUIT:
                pygame.quit()
                sys.exit()

            if event.type == pygame.KEYDOWN:

                # Ctrl + X

                if (
                    event.key == pygame.K_x
                    and pygame.key.get_mods() & pygame.KMOD_CTRL
                ):
                    pygame.quit()
                    sys.exit()

                if event.key == pygame.K_UP:

                    selected += 1

                    if selected > 10:
                        selected = 10

                if event.key == pygame.K_DOWN:

                    selected -= 1

                    if selected < 2:
                        selected = 2

                if event.key in (
                    pygame.K_RETURN,
                    pygame.K_SPACE
                ):

                    return selected

            if event.type == pygame.MOUSEBUTTONDOWN:

                mouse_x, mouse_y = pygame.mouse.get_pos()

                # Start button.

                if (
                    WIDTH * 0.35
                    < mouse_x
                    < WIDTH * 0.65
                    and HEIGHT * 0.70
                    < mouse_y
                    < HEIGHT * 0.80
                ):

                    return selected

                # Increase.

                if (
                    WIDTH * 0.65
                    < mouse_x
                    < WIDTH * 0.80
                    and HEIGHT * 0.40
                    < mouse_y
                    < HEIGHT * 0.55
                ):

                    selected = min(10, selected + 1)

                # Decrease.

                if (
                    WIDTH * 0.20
                    < mouse_x
                    < WIDTH * 0.35
                    and HEIGHT * 0.40
                    < mouse_y
                    < HEIGHT * 0.55
                ):

                    selected = max(2, selected - 1)

        # ----------------------------------------------------
        # DRAW
        # ----------------------------------------------------

        screen.fill(BLACK)

        draw_starfield()

        title = font_large.render(
            "N-BODY GRAVITATIONAL SIMULATION",
            True,
            WHITE
        )

        screen.blit(
            title,
            title.get_rect(
                center=(WIDTH // 2, HEIGHT * 0.18)
            )
        )

        subtitle = font_medium.render(
            "Select number of gravitational bodies",
            True,
            GREY
        )

        screen.blit(
            subtitle,
            subtitle.get_rect(
                center=(WIDTH // 2, HEIGHT * 0.28)
            )
        )

        # Number.

        number_text = font_large.render(
            str(selected),
            True,
            YELLOW
        )

        screen.blit(
            number_text,
            number_text.get_rect(
                center=(WIDTH // 2, HEIGHT * 0.47)
            )
        )

        # Left button.

        pygame.draw.rect(
            screen,
            DARK_GREY,
            (
                WIDTH * 0.20,
                HEIGHT * 0.40,
                WIDTH * 0.15,
                HEIGHT * 0.15
            ),
            border_radius=10
        )

        minus = font_large.render(
            "−",
            True,
            WHITE
        )

        screen.blit(
            minus,
            minus.get_rect(
                center=(
                    WIDTH * 0.275,
                    HEIGHT * 0.475
                )
            )
        )

        # Right button.

        pygame.draw.rect(
            screen,
            DARK_GREY,
            (
                WIDTH * 0.65,
                HEIGHT * 0.40,
                WIDTH * 0.15,
                HEIGHT * 0.15
            ),
            border_radius=10
        )

        plus = font_large.render(
            "+",
            True,
            WHITE
        )

        screen.blit(
            plus,
            plus.get_rect(
                center=(
                    WIDTH * 0.725,
                    HEIGHT * 0.475
                )
            )
        )

        # Start button.

        pygame.draw.rect(
            screen,
            (40, 100, 60),
            (
                WIDTH * 0.35,
                HEIGHT * 0.70,
                WIDTH * 0.30,
                HEIGHT * 0.10
            ),
            border_radius=10
        )

        start_text = font_medium.render(
            "START SIMULATION",
            True,
            WHITE
        )

        screen.blit(
            start_text,
            start_text.get_rect(
                center=(
                    WIDTH // 2,
                    HEIGHT * 0.75
                )
            )
        )

        instructions = font_small.render(
            "↑ / ↓ to select     ENTER to start     CTRL + X to exit",
            True,
            GREY
        )

        screen.blit(
            instructions,
            instructions.get_rect(
                center=(WIDTH // 2, HEIGHT * 0.90)
            )
        )

        pygame.display.flip()


# ============================================================
# SIMULATION
# ============================================================

def run_simulation(number_of_bodies):

    bodies = create_system(number_of_bodies)

    simulation_time = 0.0

    paused = False

    running = True

    # Initial trails.

    for body in bodies:

        body.trail.append(
            body.screen_position()
        )

    while running:

        clock.tick(60)

        # ----------------------------------------------------
        # EVENTS
        # ----------------------------------------------------

        for event in pygame.event.get():

            if event.type == pygame.QUIT:

                pygame.quit()
                sys.exit()

            if event.type == pygame.KEYDOWN:

                # CTRL + X

                if (
                    event.key == pygame.K_x
                    and pygame.key.get_mods() & pygame.KMOD_CTRL
                ):

                    pygame.quit()
                    sys.exit()

                # Escape returns to selection screen.

                if event.key == pygame.K_ESCAPE:

                    return

                # Pause.

                if event.key == pygame.K_SPACE:

                    paused = not paused

                # Restart.

                if event.key == pygame.K_r:

                    bodies = create_system(number_of_bodies)

                    simulation_time = 0.0

                    for body in bodies:

                        body.trail.clear()

                        body.trail.append(
                            body.screen_position()
                        )

        # ----------------------------------------------------
        # PHYSICS
        # ----------------------------------------------------

        if not paused:

            for _ in range(PHYSICS_SUBSTEPS):

                physics_step(
                    bodies,
                    DT * TIME_SCALE
                )

                simulation_time += DT * TIME_SCALE

        # ----------------------------------------------------
        # UPDATE TRAILS
        # ----------------------------------------------------

        if not paused:

            for body in bodies:

                position = body.screen_position()

                # Only add a trail point if it moved enough.

                if len(body.trail) == 0:

                    body.trail.append(position)

                else:

                    last_x, last_y = body.trail[-1]

                    dx = position[0] - last_x
                    dy = position[1] - last_y

                    if dx * dx + dy * dy > 4:

                        body.trail.append(position)

                if len(body.trail) > MAX_TRAIL_POINTS:

                    body.trail.pop(0)

        # ----------------------------------------------------
        # DRAW
        # ----------------------------------------------------

        screen.fill(BLACK)

        draw_starfield()

        draw_bodies(
            bodies,
            show_trails=True
        )

        # ----------------------------------------------------
        # INFORMATION PANEL
        # ----------------------------------------------------

        # Semi-transparent panel.

        panel = pygame.Surface(
            (330, 150),
            pygame.SRCALPHA
        )

        panel.fill((0, 0, 0, 150))

        screen.blit(
            panel,
            (15, 15)
        )

        title = font_small.render(
            "N-BODY GRAVITY",
            True,
            WHITE
        )

        screen.blit(
            title,
            (30, 25)
        )

        time_text = font_small.render(
            f"Simulation time: {simulation_time:,.2f}",
            True,
            YELLOW
        )

        screen.blit(
            time_text,
            (30, 55)
        )

        bodies_text = font_small.render(
            f"Bodies: {len(bodies)}",
            True,
            WHITE
        )

        screen.blit(
            bodies_text,
            (30, 82)
        )

        if paused:

            status = font_small.render(
                "PAUSED",
                True,
                (255, 180, 80)
            )

        else:

            status = font_tiny.render(
                "Running",
                True,
                GREY
            )

        screen.blit(
            status,
            (30, 110)
        )

        controls = font_tiny.render(
            "SPACE: pause   R: restart   ESC: menu   CTRL+X: exit",
            True,
            GREY
        )

        screen.blit(
            controls,
            (
                20,
                HEIGHT - 30
            )
        )

        pygame.display.flip()


# ============================================================
# MAIN PROGRAM
# ============================================================

def main():

    while True:

        number_of_bodies = selection_screen()

        run_simulation(number_of_bodies)


if __name__ == "__main__":

    main()