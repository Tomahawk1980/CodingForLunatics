import pygame
import math
import random
import sys


# ============================================================
# N-BODY GRAVITATIONAL SIMULATION
# Version 1.3
#
# Features:
#   - 2 to 10 gravitational bodies
#   - Newtonian N-body gravity
#   - Earth-mass based body masses
#   - Live mass adjustment
#   - Body size changes with mass
#   - Body selection panel
#   - Simulation speed controls
#   - Orbital trails
#   - Full screen
# ============================================================


pygame.init()


# ============================================================
# DISPLAY
# ============================================================

screen = pygame.display.set_mode(
    (0, 0),
    pygame.FULLSCREEN
)

pygame.display.set_caption(
    "N-Body Gravitational Simulation"
)

WIDTH, HEIGHT = screen.get_size()

clock = pygame.time.Clock()


# ============================================================
# FONTS
# ============================================================

font_large = pygame.font.SysFont(
    "arial",
    42,
    bold=True
)

font_medium = pygame.font.SysFont(
    "arial",
    28
)

font_small = pygame.font.SysFont(
    "arial",
    20
)

font_tiny = pygame.font.SysFont(
    "arial",
    16
)


# ============================================================
# COLOURS
# ============================================================

BLACK = (5, 5, 10)

WHITE = (240, 240, 240)

GREY = (150, 150, 150)

DARK_GREY = (55, 55, 65)

MID_GREY = (85, 85, 95)

GREEN = (60, 160, 80)

DARK_GREEN = (40, 100, 55)

YELLOW = (255, 220, 80)

RED = (255, 90, 80)

BLUE = (80, 150, 255)


# ============================================================
# BODY COLOURS
# ============================================================

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


# ============================================================
# PHYSICS CONSTANTS
# ============================================================

# This is a scaled gravitational constant.
#
# Mass is expressed in Earth masses.
#
# 1.0 = one Earth mass.

G = 1800.0


# Base physics timestep.

DT = 0.0018


# Number of physics calculations per rendered frame.

PHYSICS_SUBSTEPS = 6


# Prevents gravitational singularities when bodies get
# extremely close together.

SOFTENING = 12.0


# Maximum number of trail points.

MAX_TRAIL_POINTS = 350


# ============================================================
# MASS SETTINGS
# ============================================================

EARTH_MASS = 1.0


# Mass adjustment amount.

MASS_STEP = 0.1


# Minimum allowed mass.

MIN_MASS = 0.1


# Maximum allowed mass.

MAX_MASS = 1000.0


# ============================================================
# BODY SIZE
# ============================================================

# Visual radius for a 1 Earth-mass object.

EARTH_RADIUS_PIXELS = 7.0


# ============================================================
# SIMULATION SPEED
# ============================================================

SPEED_LEVELS = [

    0.25,
    0.5,
    1.0,
    2.0,
    4.0,
    8.0,
    16.0,
    32.0,
    64.0

]


# Start at 1×.

speed_index = 2


# ============================================================
# WORLD
# ============================================================

CENTER_X = WIDTH / 2

CENTER_Y = HEIGHT / 2

WORLD_SCALE = min(
    WIDTH,
    HEIGHT
) * 0.40


# ============================================================
# BODY CLASS
# ============================================================

class Body:

    def __init__(
        self,
        x,
        y,
        vx,
        vy,
        mass,
        colour
    ):

        self.x = x

        self.y = y

        self.vx = vx

        self.vy = vy

        # Mass is expressed in Earth masses.

        self.mass = mass

        self.colour = colour

        self.ax = 0.0

        self.ay = 0.0

        self.trail = []


    # --------------------------------------------------------
    # VISUAL SIZE
    # --------------------------------------------------------

    def radius(self):

        # Planetary radius roughly scales with the cube root
        # of mass for objects of broadly similar density.
        #
        # This gives:
        #
        # 1 Earth mass  -> 1x radius
        # 8 Earth mass  -> 2x radius
        #
        # We also apply sensible visual limits.

        visual_radius = (
            EARTH_RADIUS_PIXELS *
            (self.mass ** (1.0 / 3.0))
        )

        return max(
            3,
            min(
                30,
                int(visual_radius)
            )
        )


    # --------------------------------------------------------
    # SCREEN POSITION
    # --------------------------------------------------------

    def screen_position(self):

        return (
            int(CENTER_X + self.x),
            int(CENTER_Y + self.y)
        )


# ============================================================
# CALCULATE GRAVITATIONAL ACCELERATIONS
# ============================================================

def calculate_accelerations(bodies):

    # Reset acceleration.

    for body in bodies:

        body.ax = 0.0

        body.ay = 0.0


    # Every body interacts with every other body.

    for i in range(len(bodies)):

        body_a = bodies[i]

        for j in range(
            i + 1,
            len(bodies)
        ):

            body_b = bodies[j]


            dx = (
                body_b.x -
                body_a.x
            )

            dy = (
                body_b.y -
                body_a.y
            )


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


            # Newtonian gravity:
            #
            # a = G M / r²
            #
            # The direction is supplied by dx / r and dy / r.

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
# LEAPFROG PHYSICS INTEGRATION
# ============================================================

def physics_step(
    bodies,
    dt
):

    # --------------------------------------------------------
    # FIRST ACCELERATION
    # --------------------------------------------------------

    calculate_accelerations(
        bodies
    )


    # --------------------------------------------------------
    # FIRST HALF VELOCITY UPDATE
    # --------------------------------------------------------

    for body in bodies:

        body.vx += (
            body.ax *
            dt *
            0.5
        )

        body.vy += (
            body.ay *
            dt *
            0.5
        )


    # --------------------------------------------------------
    # POSITION UPDATE
    # --------------------------------------------------------

    for body in bodies:

        body.x += (
            body.vx *
            dt
        )

        body.y += (
            body.vy *
            dt
        )


    # --------------------------------------------------------
    # SECOND ACCELERATION
    # --------------------------------------------------------

    calculate_accelerations(
        bodies
    )


    # --------------------------------------------------------
    # SECOND HALF VELOCITY UPDATE
    # --------------------------------------------------------

    for body in bodies:

        body.vx += (
            body.ax *
            dt *
            0.5
        )

        body.vy += (
            body.ay *
            dt *
            0.5
        )


# ============================================================
# CREATE INITIAL SYSTEM
# ============================================================

def create_system(
    number_of_bodies
):

    bodies = []


    # --------------------------------------------------------
    # CENTRAL BODY
    # --------------------------------------------------------

    # The central object is deliberately massive compared with
    # the surrounding planets, but its mass is now expressed
    # in Earth masses.
    #
    # 50 Earth masses is large enough to produce interesting
    # orbital behaviour without being absurdly enormous.

    central_mass = 50.0


    central = Body(
        0.0,
        0.0,
        0.0,
        0.0,
        central_mass,
        BODY_COLOURS[0]
    )


    bodies.append(
        central
    )


    # --------------------------------------------------------
    # ORBITING BODIES
    # --------------------------------------------------------

    for i in range(
        1,
        number_of_bodies
    ):

        angle = (
            2.0 *
            math.pi *
            (i - 1) /
            max(
                1,
                number_of_bodies - 1
            )
        )


        radius = random.uniform(
            WORLD_SCALE * 0.22,
            WORLD_SCALE * 0.72
        )


        x = (
            math.cos(angle) *
            radius
        )

        y = (
            math.sin(angle) *
            radius
        )


        # Planet masses in Earth masses.

        mass = random.uniform(
            0.5,
            3.0
        )


        # Approximate circular orbital velocity.

        orbital_velocity = math.sqrt(
            G *
            central_mass /
            radius
        )


        # Slightly perturb the velocity.

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

        vx += random.uniform(
            -2.0,
            2.0
        )

        vy += random.uniform(
            -2.0,
            2.0
        )


        body = Body(
            x,
            y,
            vx,
            vy,
            mass,
            BODY_COLOURS[
                i %
                len(BODY_COLOURS)
            ]
        )


        bodies.append(
            body
        )


    # --------------------------------------------------------
    # MOVE CENTRE OF MASS TO ORIGIN
    # --------------------------------------------------------

    total_mass = sum(
        body.mass
        for body in bodies
    )


    centre_x = sum(
        body.x *
        body.mass
        for body in bodies
    ) / total_mass


    centre_y = sum(
        body.y *
        body.mass
        for body in bodies
    ) / total_mass


    centre_vx = sum(
        body.vx *
        body.mass
        for body in bodies
    ) / total_mass


    centre_vy = sum(
        body.vy *
        body.mass
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

    for (
        x,
        y,
        brightness
    ) in stars:

        pygame.draw.circle(
            screen,
            (
                brightness,
                brightness,
                brightness
            ),
            (
                x,
                y
            ),
            1
        )


# ============================================================
# MASS FORMATTING
# ============================================================

def format_mass(
    mass
):

    if mass < 10:

        return f"{mass:.1f}"

    if mass < 100:

        return f"{mass:.1f}"

    if mass < 1000:

        return f"{mass:.0f}"

    return f"{mass:,.0f}"


# ============================================================
# DRAW BODY KEY
# ============================================================

def draw_body_key(
    bodies,
    selected_index
):

    panel_x = 15

    panel_y = 220

    panel_width = 310

    row_height = 46

    panel_height = (
        55 +
        len(bodies) *
        row_height +
        70
    )


    # --------------------------------------------------------
    # PANEL
    # --------------------------------------------------------

    panel = pygame.Surface(
        (
            panel_width,
            panel_height
        ),
        pygame.SRCALPHA
    )


    panel.fill(
        (
            0,
            0,
            0,
            175
        )
    )


    screen.blit(
        panel,
        (
            panel_x,
            panel_y
        )
    )


    # --------------------------------------------------------
    # TITLE
    # --------------------------------------------------------

    title = font_small.render(
        "BODY KEY",
        True,
        WHITE
    )


    screen.blit(
        title,
        (
            panel_x + 15,
            panel_y + 12
        )
    )


    # --------------------------------------------------------
    # BODY ROWS
    # --------------------------------------------------------

    row_start = (
        panel_y +
        48
    )


    for i, body in enumerate(
        bodies
    ):

        row_y = (
            row_start +
            i *
            row_height
        )


        row_rect = pygame.Rect(
            panel_x + 8,
            row_y,
            panel_width - 16,
            row_height - 4
        )


        # Selected body.

        if i == selected_index:

            pygame.draw.rect(
                screen,
                (
                    65,
                    75,
                    95
                ),
                row_rect,
                border_radius=6
            )


        # Body colour.

        pygame.draw.circle(
            screen,
            body.colour,
            (
                panel_x + 28,
                row_y + 20
            ),
            max(
                4,
                min(
                    10,
                    body.radius()
                )
            )
        )


        # Body name.

        body_name = font_tiny.render(
            f"Body {i + 1}",
            True,
            WHITE
        )


        screen.blit(
            body_name,
            (
                panel_x + 48,
                row_y + 5
            )
        )


        # Mass.

        mass_text = font_tiny.render(
            f"{format_mass(body.mass)} Earth",
            True,
            YELLOW
        )


        screen.blit(
            mass_text,
            (
                panel_x + 48,
                row_y + 23
            )
        )


    # --------------------------------------------------------
    # MASS CONTROLS
    # --------------------------------------------------------

    controls_y = (
        row_start +
        len(bodies) *
        row_height +
        10
    )


    selected_mass = bodies[
        selected_index
    ].mass


    selected_text = font_tiny.render(
        "Selected body mass",
        True,
        GREY
    )


    screen.blit(
        selected_text,
        (
            panel_x + 15,
            controls_y
        )
    )


    mass_display = font_small.render(
        f"{format_mass(selected_mass)} Earth",
        True,
        YELLOW
    )


    screen.blit(
        mass_display,
        mass_display.get_rect(
            center=(
                panel_x +
                panel_width // 2,
                controls_y + 38
            )
        )
    )


    # --------------------------------------------------------
    # MINUS BUTTON
    # --------------------------------------------------------

    minus_rect = pygame.Rect(
        panel_x + 25,
        controls_y + 15,
        70,
        40
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
    # PLUS BUTTON
    # --------------------------------------------------------

    plus_rect = pygame.Rect(
        panel_x +
        panel_width -
        95,
        controls_y + 15,
        70,
        40
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


    return (
        minus_rect,
        plus_rect
    )


# ============================================================
# DRAW BODIES
# ============================================================

def draw_bodies(
    bodies,
    selected_index
):

    for i, body in enumerate(
        bodies
    ):

        # ----------------------------------------------------
        # TRAIL
        # ----------------------------------------------------

        if len(
            body.trail
        ) > 1:

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

        sx, sy = (
            body.screen_position()
        )


        radius = body.radius()


        # ----------------------------------------------------
        # GLOW
        # ----------------------------------------------------

        glow_radius = (
            radius +
            8
        )


        glow_surface = pygame.Surface(
            (
                glow_radius * 2 + 2,
                glow_radius * 2 + 2
            ),
            pygame.SRCALPHA
        )


        pygame.draw.circle(
            glow_surface,
            (
                *body.colour,
                35
            ),
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


        # ----------------------------------------------------
        # SELECTED OUTLINE
        # ----------------------------------------------------

        if i == selected_index:

            pygame.draw.circle(
                screen,
                WHITE,
                (
                    sx,
                    sy
                ),
                radius + 4,
                2
            )


        # ----------------------------------------------------
        # BODY
        # ----------------------------------------------------

        pygame.draw.circle(
            screen,
            body.colour,
            (
                sx,
                sy
            ),
            radius
        )


        # ----------------------------------------------------
        # HIGHLIGHT
        # ----------------------------------------------------

        pygame.draw.circle(
            screen,
            WHITE,
            (
                sx -
                radius // 3,
                sy -
                radius // 3
            ),
            max(
                1,
                radius // 3
            )
        )


# ============================================================
# DRAW SPEED CONTROLS
# ============================================================

def draw_speed_controls():

    button_width = 55

    button_height = 38

    gap = 8


    total_width = (
        button_width * 2 +
        gap
    )


    x_start = (
        WIDTH -
        total_width -
        25
    )


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


    return (
        minus_rect,
        plus_rect
    )


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
                # OBJECT COUNT
                # ------------------------------------------------

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


                # ------------------------------------------------
                # START
                # ------------------------------------------------

                if event.key in (
                    pygame.K_RETURN,
                    pygame.K_SPACE
                ):

                    return selected


            # ----------------------------------------------------
            # MOUSE
            # ----------------------------------------------------

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

        screen.fill(
            BLACK
        )

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


        # ----------------------------------------------------
        # MINUS
        # ----------------------------------------------------

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


        # ----------------------------------------------------
        # PLUS
        # ----------------------------------------------------

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


        # ----------------------------------------------------
        # START
        # ----------------------------------------------------

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

def run_simulation(
    number_of_bodies
):

    global speed_index


    # --------------------------------------------------------
    # CREATE SYSTEM
    # --------------------------------------------------------

    bodies = create_system(
        number_of_bodies
    )


    simulation_time = 0.0


    paused = False


    # Body selected in the key.

    selected_body = 0


    # Reset speed.

    speed_index = 2


    # Initial trail positions.

    for body in bodies:

        body.trail.append(
            body.screen_position()
        )


    # ========================================================
    # MAIN LOOP
    # ========================================================

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

                    selected_body = 0

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
                # SPEED DOWN
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
                # NORMAL SPEED
                # ------------------------------------------------

                if event.key == pygame.K_0:

                    speed_index = (
                        SPEED_LEVELS.index(
                            1.0
                        )
                    )


                # ------------------------------------------------
                # SELECT PREVIOUS BODY
                # ------------------------------------------------

                if event.key == pygame.K_LEFT:

                    selected_body -= 1

                    if selected_body < 0:

                        selected_body = (
                            len(bodies) - 1
                        )


                # ------------------------------------------------
                # SELECT NEXT BODY
                # ------------------------------------------------

                if event.key == pygame.K_RIGHT:

                    selected_body += 1

                    if selected_body >= len(bodies):

                        selected_body = 0


                # ------------------------------------------------
                # INCREASE MASS
                # ------------------------------------------------

                if event.key in (
                    pygame.K_KP_PLUS,
                    pygame.K_PLUS
                ):

                    bodies[
                        selected_body
                    ].mass = min(
                        MAX_MASS,
                        bodies[
                            selected_body
                        ].mass +
                        MASS_STEP
                    )


                # ------------------------------------------------
                # DECREASE MASS
                # ------------------------------------------------

                if event.key in (
                    pygame.K_KP_MINUS,
                ):

                    bodies[
                        selected_body
                    ].mass = max(
                        MIN_MASS,
                        bodies[
                            selected_body
                        ].mass -
                        MASS_STEP
                    )


            # ====================================================
            # MOUSE
            # ====================================================

            if event.type == pygame.MOUSEBUTTONDOWN:

                mouse_pos = (
                    pygame.mouse.get_pos()
                )


                # ------------------------------------------------
                # SPEED CONTROLS
                # ------------------------------------------------

                speed_minus_rect, speed_plus_rect = (
                    draw_speed_controls()
                )


                if speed_minus_rect.collidepoint(
                    mouse_pos
                ):

                    speed_index = max(
                        0,
                        speed_index - 1
                    )


                if speed_plus_rect.collidepoint(
                    mouse_pos
                ):

                    speed_index = min(
                        len(SPEED_LEVELS) - 1,
                        speed_index + 1
                    )


                # ------------------------------------------------
                # BODY KEY
                # ------------------------------------------------

                key_panel_y = 220

                row_start = (
                    key_panel_y +
                    48
                )

                row_height = 46


                for i in range(
                    len(bodies)
                ):

                    row_y = (
                        row_start +
                        i *
                        row_height
                    )


                    row_rect = pygame.Rect(
                        23,
                        row_y,
                        294,
                        row_height - 4
                    )


                    if row_rect.collidepoint(
                        mouse_pos
                    ):

                        selected_body = i


                # ------------------------------------------------
                # MASS BUTTONS
                # ------------------------------------------------

                # Calculate where the mass controls are.

                controls_y = (
                    row_start +
                    len(bodies) *
                    row_height +
                    10
                )


                mass_minus_rect = pygame.Rect(
                    40,
                    controls_y + 15,
                    70,
                    40
                )


                mass_plus_rect = pygame.Rect(
                    230,
                    controls_y + 15,
                    70,
                    40
                )


                if mass_minus_rect.collidepoint(
                    mouse_pos
                ):

                    bodies[
                        selected_body
                    ].mass = max(
                        MIN_MASS,
                        bodies[
                            selected_body
                        ].mass -
                        MASS_STEP
                    )


                if mass_plus_rect.collidepoint(
                    mouse_pos
                ):

                    bodies[
                        selected_body
                    ].mass = min(
                        MAX_MASS,
                        bodies[
                            selected_body
                        ].mass +
                        MASS_STEP
                    )


        # ====================================================
        # SIMULATION SPEED
        # ====================================================

        simulation_speed = SPEED_LEVELS[
            speed_index
        ]


        # ====================================================
        # PHYSICS
        # ====================================================

        if not paused:

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


                simulation_time += (
                    physics_dt
                )


        # ====================================================
        # TRAILS
        # ====================================================

        if not paused:

            for body in bodies:

                position = (
                    body.screen_position()
                )


                if len(
                    body.trail
                ) == 0:

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


                    if (
                        dx * dx +
                        dy * dy
                    ) > 4:

                        body.trail.append(
                            position
                        )


                if len(
                    body.trail
                ) > MAX_TRAIL_POINTS:

                    body.trail.pop(0)


        # ====================================================
        # DRAW
        # ====================================================

        screen.fill(
            BLACK
        )


        draw_starfield()


        draw_bodies(
            bodies,
            selected_body
        )


        # ====================================================
        # TOP INFORMATION PANEL
        # ====================================================

        panel = pygame.Surface(
            (
                370,
                190
            ),
            pygame.SRCALPHA
        )


        panel.fill(
            (
                0,
                0,
                0,
                165
            )
        )


        screen.blit(
            panel,
            (
                15,
                15
            )
        )


        title = font_small.render(
            "N-BODY GRAVITY",
            True,
            WHITE
        )


        screen.blit(
            title,
            (
                30,
                25
            )
        )


        time_text = font_small.render(
            f"Simulation time: "
            f"{simulation_time:,.2f}",
            True,
            YELLOW
        )


        screen.blit(
            time_text,
            (
                30,
                55
            )
        )


        bodies_text = font_small.render(
            f"Bodies: {len(bodies)}",
            True,
            WHITE
        )


        screen.blit(
            bodies_text,
            (
                30,
                82
            )
        )


        speed_text = font_small.render(
            f"Simulation speed: "
            f"{simulation_speed:g}×",
            True,
            GREEN
        )


        screen.blit(
            speed_text,
            (
                30,
                109
            )
        )


        selected_text = font_tiny.render(
            f"Selected: Body "
            f"{selected_body + 1}",
            True,
            WHITE
        )


        screen.blit(
            selected_text,
            (
                30,
                140
            )
        )


        # ====================================================
        # SPEED CONTROLS
        # ====================================================

        speed_minus_rect, speed_plus_rect = (
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
        # BODY KEY
        # ====================================================

        draw_body_key(
            bodies,
            selected_body
        )


        # ====================================================
        # PAUSE STATUS
        # ====================================================

        if paused:

            paused_text = font_medium.render(
                "PAUSED",
                True,
                RED
            )


            screen.blit(
                paused_text,
                (
                    WIDTH // 2 -
                    55,
                    30
                )
            )


        # ====================================================
        # BOTTOM CONTROLS
        # ====================================================

        controls = font_tiny.render(
            "SPACE: pause    "
            "R: restart    "
            "← / →: select body    "
            "+ / −: mass    "
            "ESC: menu    "
            "CTRL+X: exit",
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