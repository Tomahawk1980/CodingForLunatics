import pygame
import math
import random
import sys


# ============================================================
# N-BODY GRAVITATIONAL SIMULATION
# Version 1.2
# ============================================================

pygame.init()

# ============================================================
# DISPLAY
# ============================================================

screen = pygame.display.set_mode((0, 0), pygame.FULLSCREEN)
pygame.display.set_caption("N-Body Gravitational Simulation")

WIDTH, HEIGHT = screen.get_size()

clock = pygame.time.Clock()

# ============================================================
# FONTS
# ============================================================

font_large = pygame.font.SysFont("arial", 42, bold=True)
font_medium = pygame.font.SysFont("arial", 28)
font_small = pygame.font.SysFont("arial", 20)
font_tiny = pygame.font.SysFont("arial", 16)

# ============================================================
# COLOURS
# ============================================================

BLACK = (5, 5, 10)
WHITE = (240, 240, 240)
GREY = (150, 150, 150)
DARK_GREY = (65, 65, 75)
GREEN = (60, 150, 80)
YELLOW = (255, 220, 80)
RED = (255, 100, 80)

BODY_COLOURS = [
    (255, 80, 80),
    (80, 160, 255),
    (100, 255, 120),
    (255, 170, 60),
    (210, 100, 255),
    (255, 100, 200),
    (80, 230, 220),
    (255, 255, 100),
    (160, 160, 255),
    (180, 255, 150),
]

# ============================================================
# PHYSICS
# ============================================================

G = 1800.0

# Base physics timestep.
#
# This stays small for numerical stability.

DT = 0.0018

# Number of physics calculations per rendered frame.

PHYSICS_SUBSTEPS = 6

# Prevents extreme acceleration when two bodies get very close.

SOFTENING = 12.0

# Maximum number of points in each orbital trail.

MAX_TRAIL_POINTS = 350

# ============================================================
# SIMULATION SPEED
# ============================================================

# Available speed multipliers.

SPEED_LEVELS = [
    0.25,
    0.5,
    1.0,
    2.0,
    4.0,
    8.0,
    16.0,
    32.0,
    64.0,
]

# Start at normal speed.

speed_index = 2


# ============================================================
# WORLD
# ============================================================

CENTER_X = WIDTH / 2
CENTER_Y = HEIGHT / 2

WORLD_SCALE = min(WIDTH, HEIGHT) * 0.40


# ============================================================
# BODY
# ============================================================

class Body:

    def __init__(
        self,
        x,
        y,
        vx,
        vy,
        mass,
        radius,
        colour
    ):

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

        return (
            int(CENTER_X + self.x),
            int(CENTER_Y + self.y)
        )


# ============================================================
# ACCELERATION CALCULATION
# ============================================================

def calculate_accelerations(bodies):

    # Reset acceleration.

    for body in bodies:

        body.ax = 0.0
        body.ay = 0.0

    # Calculate every pairwise interaction.

    for i in range(len(bodies)):

        body_a = bodies[i]

        for j in range(i + 1, len(bodies)):

            body_b = bodies[j]

            dx = body_b.x - body_a.x
            dy = body_b.y - body_a.y

            distance_squared = (
                dx * dx +
                dy * dy
            )

            softened_distance_squared = (
                distance_squared +
                SOFTENING * SOFTENING
            )

            distance = math.sqrt(
                softened_distance_squared
            )

            if distance <= 0:
                continue

            # Gravitational acceleration factor.
            #
            # a = G * M / r^3 * direction

            factor = G / (
                softened_distance_squared *
                distance
            )

            # Acceleration of A caused by B.

            ax_a = (
                factor *
                body_b.mass *
                dx
            )

            ay_a = (
                factor *
                body_b.mass *
                dy
            )

            # Acceleration of B caused by A.

            ax_b = (
                -factor *
                body_a.mass *
                dx
            )

            ay_b = (
                -factor *
                body_a.mass *
                dy
            )

            body_a.ax += ax_a
            body_a.ay += ay_a

            body_b.ax += ax_b
            body_b.ay += ay_b


# ============================================================
# PHYSICS STEP
# ============================================================

def physics_step(bodies, dt):

    # --------------------------------------------------------
    # FIRST ACCELERATION
    # --------------------------------------------------------

    calculate_accelerations(bodies)

    # --------------------------------------------------------
    # HALF VELOCITY STEP
    # --------------------------------------------------------

    for body in bodies:

        body.vx += body.ax * dt * 0.5
        body.vy += body.ay * dt * 0.5

    # --------------------------------------------------------
    # POSITION STEP
    # --------------------------------------------------------

    for body in bodies:

        body.x += body.vx * dt
        body.y += body.vy * dt

    # --------------------------------------------------------
    # SECOND ACCELERATION
    # --------------------------------------------------------

    calculate_accelerations(bodies)

    # --------------------------------------------------------
    # SECOND HALF VELOCITY STEP
    # --------------------------------------------------------

    for body in bodies:

        body.vx += body.ax * dt * 0.5
        body.vy += body.ay * dt * 0.5


# ============================================================
# CREATE INITIAL SYSTEM
# ============================================================

def create_system(number_of_bodies):

    bodies = []

    # --------------------------------------------------------
    # CENTRAL BODY
    # --------------------------------------------------------

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

        angle = (
            2.0 *
            math.pi *
            (i - 1) /
            max(1, number_of_bodies - 1)
        )

        radius = random.uniform(
            WORLD_SCALE * 0.22,
            WORLD_SCALE * 0.72
        )

        x = math.cos(angle) * radius
        y = math.sin(angle) * radius

        mass = random.uniform(
            20.0,
            65.0
        )

        # Circular orbital velocity.

        orbital_velocity = math.sqrt(
            G * central_mass / radius
        )

        # Slightly randomise the velocity.

        orbital_velocity *= random.uniform(
            0.92,
            1.08
        )

        # Tangential velocity.

        vx = (
            -math.sin(angle) *
            orbital_velocity
        )

        vy = (
            math.cos(angle) *
            orbital_velocity
        )

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
            BODY_COLOURS[
                i % len(BODY_COLOURS)
            ]
        )

        bodies.append(body)

    # --------------------------------------------------------
    # CENTRE OF MASS
    # --------------------------------------------------------

    total_mass = sum(
        body.mass
        for body in bodies
    )

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
# STARFIELD
# ============================================================

def create_starfield():

    stars = []

    for _ in range(250):

        x = random.randint(
            0,
            WIDTH - 1
        )

        y = random.randint(
            0,
            HEIGHT - 1
        )

        brightness = random.randint(
            50,
            150
        )

        stars.append(
            (
                x,
                y,
                brightness
            )
        )

    return stars


stars = create_starfield()


def draw_starfield():

    for x, y, brightness in stars:

        pygame.draw.circle(
            screen,
            (
                brightness,
                brightness,
                brightness
            ),
            (x, y),
            1
        )


# ============================================================
# DRAW BODIES
# ============================================================

def draw_bodies(bodies):

    for body in bodies:

        # ----------------------------------------------------
        # TRAIL
        # ----------------------------------------------------

        if len(body.trail) > 1:

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
            (
                glow_radius,
                glow_radius
            ),
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

        # Highlight.

        pygame.draw.circle(
            screen,
            WHITE,
            (
                sx - body.radius // 3,
                sy - body.radius // 3
            ),
            max(
                1,
                body.radius // 3
            )
        )


# ============================================================
# SPEED BUTTONS
# ============================================================

def draw_speed_controls():

    button_width = 55
    button_height = 38

    gap = 8

    total_width = (
        button_width * 2 +
        gap
    )

    x_start = WIDTH - total_width - 25
    y = 25

    # --------------------------------------------------------
    # MINUS
    # --------------------------------------------------------

    minus_rect = pygame.Rect(
        x_start,
        y,
        button_width,
        button_height
    )

    pygame.draw.rect(
        screen,
        DARK_GREY,
        minus_rect,
        border_radius=7
    )

    minus_text = font_medium.render(
        "−",
        True,
        WHITE
    )

    screen.blit(
        minus_text,
        minus_text.get_rect(
            center=minus_rect.center
        )
    )

    # --------------------------------------------------------
    # PLUS
    # --------------------------------------------------------

    plus_rect = pygame.Rect(
        x_start +
        button_width +
        gap,
        y,
        button_width,
        button_height
    )

    pygame.draw.rect(
        screen,
        DARK_GREY,
        plus_rect,
        border_radius=7
    )

    plus_text = font_medium.render(
        "+",
        True,
        WHITE
    )

    screen.blit(
        plus_text,
        plus_text.get_rect(
            center=plus_rect.center
        )
    )

    return minus_rect, plus_rect


# ============================================================
# SELECTION SCREEN
# ============================================================

def selection_screen():

    selected = 3

    while True:

        clock.tick(60)

        for event in pygame.event.get():

            if event.type == pygame.QUIT:

                pygame.quit()
                sys.exit()

            if event.type == pygame.KEYDOWN:

                # Ctrl + X

                if (
                    event.key == pygame.K_x
                    and
                    pygame.key.get_mods()
                    & pygame.KMOD_CTRL
                ):

                    pygame.quit()
                    sys.exit()

                if event.key == pygame.K_UP:

                    selected = min(
                        10,
                        selected + 1
                    )

                if event.key == pygame.K_DOWN:

                    selected = max(
                        2,
                        selected - 1
                    )

                if event.key in (
                    pygame.K_RETURN,
                    pygame.K_SPACE
                ):

                    return selected

            if event.type == pygame.MOUSEBUTTONDOWN:

                mouse_x, mouse_y = (
                    pygame.mouse.get_pos()
                )

                # Minus.

                if (
                    WIDTH * 0.20
                    < mouse_x
                    < WIDTH * 0.35
                    and
                    HEIGHT * 0.40
                    < mouse_y
                    < HEIGHT * 0.55
                ):

                    selected = max(
                        2,
                        selected - 1
                    )

                # Plus.

                if (
                    WIDTH * 0.65
                    < mouse_x
                    < WIDTH * 0.80
                    and
                    HEIGHT * 0.40
                    < mouse_y
                    < HEIGHT * 0.55
                ):

                    selected = min(
                        10,
                        selected + 1
                    )

                # Start.

                if (
                    WIDTH * 0.35
                    < mouse_x
                    < WIDTH * 0.65
                    and
                    HEIGHT * 0.70
                    < mouse_y
                    < HEIGHT * 0.80
                ):

                    return selected

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
                center=(
                    WIDTH // 2,
                    HEIGHT * 0.18
                )
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
                center=(
                    WIDTH // 2,
                    HEIGHT * 0.28
                )
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
                center=(
                    WIDTH // 2,
                    HEIGHT * 0.47
                )
            )
        )

        # Minus button.

        minus_rect = pygame.Rect(
            WIDTH * 0.20,
            HEIGHT * 0.40,
            WIDTH * 0.15,
            HEIGHT * 0.15
        )

        pygame.draw.rect(
            screen,
            DARK_GREY,
            minus_rect,
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
                center=minus_rect.center
            )
        )

        # Plus button.

        plus_rect = pygame.Rect(
            WIDTH * 0.65,
            HEIGHT * 0.40,
            WIDTH * 0.15,
            HEIGHT * 0.15
        )

        pygame.draw.rect(
            screen,
            DARK_GREY,
            plus_rect,
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
                center=plus_rect.center
            )
        )

        # Start button.

        start_rect = pygame.Rect(
            WIDTH * 0.35,
            HEIGHT * 0.70,
            WIDTH * 0.30,
            HEIGHT * 0.10
        )

        pygame.draw.rect(
            screen,
            GREEN,
            start_rect,
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
                center=start_rect.center
            )
        )

        instructions = font_small.render(
            "↑ / ↓ select    ENTER start    CTRL + X exit",
            True,
            GREY
        )

        screen.blit(
            instructions,
            instructions.get_rect(
                center=(
                    WIDTH // 2,
                    HEIGHT * 0.90
                )
            )
        )

        pygame.display.flip()


# ============================================================
# SIMULATION
# ============================================================

def run_simulation(number_of_bodies):

    global speed_index

    bodies = create_system(
        number_of_bodies
    )

    simulation_time = 0.0

    paused = False

    # Reset speed whenever a new simulation starts.

    speed_index = 2

    # Initial trail points.

    for body in bodies:

        body.trail.append(
            body.screen_position()
        )

    while True:

        clock.tick(60)

        # ====================================================
        # EVENTS
        # ====================================================

        for event in pygame.event.get():

            if event.type == pygame.QUIT:

                pygame.quit()
                sys.exit()

            if event.type == pygame.KEYDOWN:

                # ------------------------------------------------
                # CTRL + X
                # ------------------------------------------------

                if (
                    event.key == pygame.K_x
                    and
                    pygame.key.get_mods()
                    & pygame.KMOD_CTRL
                ):

                    pygame.quit()
                    sys.exit()

                # ------------------------------------------------
                # ESCAPE
                # ------------------------------------------------

                if event.key == pygame.K_ESCAPE:

                    return

                # ------------------------------------------------
                # PAUSE
                # ------------------------------------------------

                if event.key == pygame.K_SPACE:

                    paused = not paused

                # ------------------------------------------------
                # RESTART
                # ------------------------------------------------

                if event.key == pygame.K_r:

                    bodies = create_system(
                        number_of_bodies
                    )

                    simulation_time = 0.0

                    speed_index = 2

                    for body in bodies:

                        body.trail.clear()

                        body.trail.append(
                            body.screen_position()
                        )

                # ------------------------------------------------
                # SPEED UP
                # ------------------------------------------------

                if event.key in (
                    pygame.K_PLUS,
                    pygame.K_EQUALS
                ):

                    speed_index = min(
                        len(SPEED_LEVELS) - 1,
                        speed_index + 1
                    )

                # ------------------------------------------------
                # SLOW DOWN
                # ------------------------------------------------

                if event.key in (
                    pygame.K_MINUS,
                    pygame.K_KP_MINUS
                ):

                    speed_index = max(
                        0,
                        speed_index - 1
                    )

                # ------------------------------------------------
                # RESET SPEED
                # ------------------------------------------------

                if event.key == pygame.K_0:

                    # Find 1×.

                    speed_index = SPEED_LEVELS.index(
                        1.0
                    )

            # ====================================================
            # MOUSE
            # ====================================================

            if event.type == pygame.MOUSEBUTTONDOWN:

                mouse_pos = pygame.mouse.get_pos()

                minus_rect, plus_rect = (
                    draw_speed_controls()
                )

                if minus_rect.collidepoint(
                    mouse_pos
                ):

                    speed_index = max(
                        0,
                        speed_index - 1
                    )

                if plus_rect.collidepoint(
                    mouse_pos
                ):

                    speed_index = min(
                        len(SPEED_LEVELS) - 1,
                        speed_index + 1
                    )

        # ====================================================
        # CURRENT SPEED
        # ====================================================

        simulation_speed = SPEED_LEVELS[
            speed_index
        ]

        # ====================================================
        # PHYSICS
        # ====================================================

        if not paused:

            # We keep the number of physics substeps constant.
            #
            # The amount of simulated time represented by each
            # physics step changes according to the speed setting.

            physics_dt = (
                DT *
                simulation_speed
            )

            for _ in range(
                PHYSICS_SUBSTEPS
            ):

                physics_step(
                    bodies,
                    physics_dt
                )

                simulation_time += physics_dt

        # ====================================================
        # TRAILS
        # ====================================================

        if not paused:

            for body in bodies:

                position = (
                    body.screen_position()
                )

                if len(body.trail) == 0:

                    body.trail.append(
                        position
                    )

                else:

                    last_x, last_y = (
                        body.trail[-1]
                    )

                    dx = (
                        position[0] -
                        last_x
                    )

                    dy = (
                        position[1] -
                        last_y
                    )

                    # Only add a new trail point
                    # after the body has moved enough.

                    if (
                        dx * dx +
                        dy * dy
                    ) > 4:

                        body.trail.append(
                            position
                        )

                if len(body.trail) > MAX_TRAIL_POINTS:

                    body.trail.pop(0)

        # ====================================================
        # DRAW
        # ====================================================

        screen.fill(BLACK)

        draw_starfield()

        draw_bodies(bodies)

        # ====================================================
        # INFORMATION PANEL
        # ====================================================

        panel = pygame.Surface(
            (360, 190),
            pygame.SRCALPHA
        )

        panel.fill(
            (0, 0, 0, 165)
        )

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
            f"Simulation time: "
            f"{simulation_time:,.2f}",
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

        speed_text = font_small.render(
            f"Simulation speed: "
            f"{simulation_speed:g}×",
            True,
            GREEN
        )

        screen.blit(
            speed_text,
            (30, 109)
        )

        if paused:

            status_text = font_small.render(
                "PAUSED",
                True,
                RED
            )

        else:

            status_text = font_tiny.render(
                "Running",
                True,
                GREY
            )

        screen.blit(
            status_text,
            (30, 140)
        )

        # ====================================================
        # SPEED CONTROLS
        # ====================================================

        minus_rect, plus_rect = (
            draw_speed_controls()
        )

        speed_label = font_tiny.render(
            "SIMULATION SPEED",
            True,
            GREY
        )

        screen.blit(
            speed_label,
            (
                WIDTH - 200,
                75
            )
        )

        keyboard_label = font_tiny.render(
            "+ / −    0 = normal",
            True,
            GREY
        )

        screen.blit(
            keyboard_label,
            (
                WIDTH - 205,
                98
            )
        )

        # ====================================================
        # BOTTOM CONTROLS
        # ====================================================

        controls = font_tiny.render(
            "SPACE: pause    R: restart    "
            "ESC: menu    CTRL+X: exit",
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
# MAIN
# ============================================================

def main():

    while True:

        number_of_bodies = (
            selection_screen()
        )

        run_simulation(
            number_of_bodies
        )


# ============================================================
# START
# ============================================================

if __name__ == "__main__":

    main()