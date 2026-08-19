import pygame
import math
import random
import sys


# ============================================================
# N-BODY GRAVITATIONAL SIMULATION
# VERSION 1.4
#
# Astronomical-unit based N-body simulator
#
# Units:
#   Mass     = Earth masses
#   Distance = Astronomical Units (AU)
#   Time     = Years
#
# 1 Earth mass = 1.0
# 1 Solar mass = approximately 332,946 Earth masses
#
# Controls:
#
#   LEFT / RIGHT       Select body
#   + / -              Increase / decrease mass
#   [ / ]              Simulation speed down / up
#   0                  Reset speed to 1x
#   SPACE              Pause
#   R                  Restart system
#   ESC                Return to menu
#   CTRL + X           Exit
#
# Mouse:
#   Click body in key  Select body
#   Click +/-          Change mass
#   Click speed +/-    Change simulation speed
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
    "N-Body Gravitational Simulation v1.4"
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

BLACK = (3, 4, 9)

WHITE = (240, 240, 240)

GREY = (150, 150, 150)

DARK_GREY = (55, 55, 65)

MID_GREY = (80, 80, 95)

GREEN = (70, 180, 90)

YELLOW = (255, 220, 80)

RED = (255, 90, 80)

BLUE = (80, 150, 255)


# ============================================================
# BODY COLOURS
# ============================================================

BODY_COLOURS = [

    (255, 210, 70),      # Star / yellow
    (100, 160, 255),     # Blue
    (255, 100, 80),      # Red
    (100, 230, 130),     # Green
    (220, 120, 255),     # Purple
    (255, 160, 70),      # Orange
    (80, 220, 220),      # Cyan
    (255, 110, 190),     # Pink
    (160, 160, 255),     # Light blue
    (180, 255, 150)      # Light green

]


# ============================================================
# ASTRONOMICAL CONSTANTS
# ============================================================

# Solar mass in Earth masses.

SOLAR_MASS = 332946.0


# Earth mass.

EARTH_MASS = 1.0


# Gravitational constant in:
#
# AU^3 / (Earth masses * year^2)
#
# Derived from:
#
#     G = 4 pi^2 / solar_mass
#
# when using AU, years and solar masses.

G = (
    4.0 *
    math.pi *
    math.pi
) / SOLAR_MASS


# ============================================================
# PHYSICS TIMESTEP
# ============================================================

# One physics step is approximately 1/3650 of a year.
#
# About 0.1 days.
#
# This is deliberately small so that planetary orbits remain
# numerically stable.

PHYSICS_DT = 1.0 / 3650.0


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


speed_index = 2


# ============================================================
# SIMULATION TIME LIMITS
# ============================================================

# At high speeds there can be many physics calculations per
# frame. This limit prevents the UI from becoming completely
# overwhelmed if the computer cannot keep up.

MAX_PHYSICS_STEPS_PER_FRAME = 120


# ============================================================
# COLLISION SETTINGS
# ============================================================

# Collision radii are visual/physical approximations.
#
# We use AU here.

EARTH_RADIUS_AU = 4.25875e-5


# Visual scaling for planets.

EARTH_VISUAL_RADIUS = 5.0


# Visual scaling for star.

STAR_VISUAL_RADIUS = 18.0


# ============================================================
# WORLD / CAMERA
# ============================================================

CENTER_X = WIDTH / 2

CENTER_Y = HEIGHT / 2


# The visible horizontal region is approximately +/- 5 AU.

VIEW_AU = 5.0


# Convert AU into screen pixels.

PIXELS_PER_AU = (
    min(WIDTH, HEIGHT) * 0.42
) / VIEW_AU


# ============================================================
# TRAILS
# ============================================================

MAX_TRAIL_POINTS = 500


TRAIL_SAMPLE_INTERVAL = 0.002


# ============================================================
# BODY CLASS
# ============================================================

class Body:

    def __init__(
        self,
        name,
        x,
        y,
        vx,
        vy,
        mass,
        colour,
        is_star=False
    ):

        self.name = name

        self.x = x

        self.y = y

        self.vx = vx

        self.vy = vy

        self.mass = mass

        self.colour = colour

        self.is_star = is_star

        self.ax = 0.0

        self.ay = 0.0

        self.trail = []

        self.alive = True


    # ========================================================
    # VISUAL RADIUS
    # ========================================================

    def visual_radius(self):

        if self.is_star:

            # Star radius scales very gently with mass.

            radius = (
                STAR_VISUAL_RADIUS *
                (self.mass / SOLAR_MASS) ** 0.1
            )

            return max(
                14,
                min(
                    40,
                    int(radius)
                )
            )


        # Planet radius.
        #
        # Approximate constant-density relationship:
        #
        #     R proportional to M^(1/3)

        radius = (
            EARTH_VISUAL_RADIUS *
            self.mass ** (1.0 / 3.0)
        )


        return max(
            3,
            min(
                28,
                int(radius)
            )
        )


    # ========================================================
    # COLLISION RADIUS
    # ========================================================

    def physical_radius(self):

        if self.is_star:

            # Approximate Sun radius in AU.

            return 0.00465


        return (
            EARTH_RADIUS_AU *
            self.mass ** (1.0 / 3.0)
        )


    # ========================================================
    # SCREEN POSITION
    # ========================================================

    def screen_position(self):

        return (

            int(
                CENTER_X +
                self.x *
                PIXELS_PER_AU
            ),

            int(
                CENTER_Y +
                self.y *
                PIXELS_PER_AU
            )

        )


# ============================================================
# CREATE STARFIELD
# ============================================================

def create_starfield():

    stars = []

    for _ in range(350):

        x = random.randint(
            0,
            WIDTH - 1
        )

        y = random.randint(
            0,
            HEIGHT - 1
        )

        brightness = random.randint(
            40,
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


# ============================================================
# DRAW STARFIELD
# ============================================================

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
# CALCULATE GRAVITATIONAL ACCELERATION
# ============================================================

def calculate_accelerations(
    bodies
):

    for body in bodies:

        body.ax = 0.0

        body.ay = 0.0


    # --------------------------------------------------------
    # EVERY BODY INTERACTS WITH EVERY OTHER BODY
    # --------------------------------------------------------

    for i in range(
        len(bodies)
    ):

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


            # Small numerical softening.
            #
            # This is deliberately extremely small in AU.

            softening = 1e-8


            softened_distance_squared = (
                distance_squared +
                softening
            )


            distance = math.sqrt(
                softened_distance_squared
            )


            if distance <= 0:

                continue


            # ------------------------------------------------
            # GRAVITY
            # ------------------------------------------------

            factor = (
                G /
                (
                    softened_distance_squared *
                    distance
                )
            )


            # Acceleration on A caused by B.

            body_a.ax += (
                factor *
                body_b.mass *
                dx
            )

            body_a.ay += (
                factor *
                body_b.mass *
                dy
            )


            # Acceleration on B caused by A.

            body_b.ax -= (
                factor *
                body_a.mass *
                dx
            )

            body_b.ay -= (
                factor *
                body_a.mass *
                dy
            )


# ============================================================
# VELOCITY VERLET INTEGRATOR
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
    # HALF VELOCITY UPDATE
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
# CREATE STABLE SYSTEM
# ============================================================

def create_system(
    number_of_bodies
):

    bodies = []


    # ========================================================
    # CENTRAL STAR
    # ========================================================

    star = Body(

        "Star",

        0.0,
        0.0,

        0.0,
        0.0,

        SOLAR_MASS,

        BODY_COLOURS[0],

        True

    )


    bodies.append(
        star
    )


    # ========================================================
    # ORBITAL DISTANCES
    # ========================================================

    # Deliberately spaced orbital radii.
    #
    # This is NOT random because we want the starting system
    # to be stable enough to experiment with.
    #
    # The first few are roughly analogous to a planetary
    # system rather than all being crammed together.

    orbital_distances = [

        0.45,
        0.70,
        1.00,
        1.40,
        1.90,
        2.50,
        3.20,
        4.00,
        4.70

    ]


    # Example starting masses in Earth masses.

    starting_masses = [

        0.35,
        0.75,
        1.00,
        0.60,
        1.50,
        0.40,
        2.00,
        0.80,
        1.20

    ]


    # ========================================================
    # CREATE PLANETS
    # ========================================================

    for i in range(
        number_of_bodies - 1
    ):

        radius = orbital_distances[i]


        # Slight angular offset.

        angle = (
            i *
            math.radians(25.0)
        )


        x = (
            math.cos(angle) *
            radius
        )

        y = (
            math.sin(angle) *
            radius
        )


        mass = starting_masses[i]


        # ----------------------------------------------------
        # CIRCULAR ORBITAL VELOCITY
        # ----------------------------------------------------
        #
        # v = sqrt(GM/r)
        #
        # Using the actual solar mass.

        velocity = math.sqrt(
            G *
            SOLAR_MASS /
            radius
        )


        # Tangential velocity.

        vx = (
            -math.sin(angle) *
            velocity
        )

        vy = (
            math.cos(angle) *
            velocity
        )


        planet = Body(

            f"Planet {i + 1}",

            x,
            y,

            vx,
            vy,

            mass,

            BODY_COLOURS[
                (i + 1) %
                len(BODY_COLOURS)
            ],

            False

        )


        bodies.append(
            planet
        )


    # ========================================================
    # REMOVE CENTRE-OF-MASS DRIFT
    # ========================================================

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


    # ========================================================
    # INITIAL TRAILS
    # ========================================================

    for body in bodies:

        body.trail.append(
            body.screen_position()
        )


    return bodies


# ============================================================
# COLLISION / MERGE
# ============================================================

def merge_bodies(
    body_a,
    body_b
):

    # --------------------------------------------------------
    # STAR + PLANET
    # --------------------------------------------------------

    if body_a.is_star:

        star = body_a

        other = body_b

    elif body_b.is_star:

        star = body_b

        other = body_a

    else:

        star = None


    if star is not None:

        # Planet is absorbed by star.

        star.mass += (
            other.mass
        )


        # Momentum conservation.

        total_mass = (
            star.mass
        )


        star.vx = (
            star.vx *
            (
                star.mass -
                other.mass
            ) +
            other.vx *
            other.mass
        ) / total_mass


        star.vy = (
            star.vy *
            (
                star.mass -
                other.mass
            ) +
            other.vy *
            other.mass
        ) / total_mass


        other.alive = False

        return star


    # --------------------------------------------------------
    # PLANET + PLANET
    # --------------------------------------------------------

    total_mass = (
        body_a.mass +
        body_b.mass
    )


    # Centre of mass.

    new_x = (
        body_a.x *
        body_a.mass +
        body_b.x *
        body_b.mass
    ) / total_mass


    new_y = (
        body_a.y *
        body_a.mass +
        body_b.y *
        body_b.mass
    ) / total_mass


    # Momentum conservation.

    new_vx = (
        body_a.vx *
        body_a.mass +
        body_b.vx *
        body_b.mass
    ) / total_mass


    new_vy = (
        body_a.vy *
        body_a.mass +
        body_b.vy *
        body_b.mass
    ) / total_mass


    body_a.x = new_x

    body_a.y = new_y

    body_a.vx = new_vx

    body_a.vy = new_vy

    body_a.mass = total_mass


    body_b.alive = False


    return body_a


# ============================================================
# CHECK COLLISIONS
# ============================================================

def check_collisions(
    bodies,
    selected_body
):

    changed = True


    while changed:

        changed = False


        for i in range(
            len(bodies)
        ):

            if not bodies[i].alive:

                continue


            for j in range(
                i + 1,
                len(bodies)
            ):

                if not bodies[j].alive:

                    continue


                body_a = bodies[i]

                body_b = bodies[j]


                dx = (
                    body_b.x -
                    body_a.x
                )

                dy = (
                    body_b.y -
                    body_a.y
                )


                distance = math.sqrt(
                    dx * dx +
                    dy * dy
                )


                collision_distance = (
                    body_a.physical_radius() +
                    body_b.physical_radius()
                )


                if distance <= collision_distance:

                    surviving_body = merge_bodies(
                        body_a,
                        body_b
                    )


                    # Keep selection pointing at the surviving
                    # body where possible.

                    if (
                        selected_body == j
                    ):

                        selected_body = i


                    changed = True

                    break


            if changed:

                break


        if changed:

            bodies[:] = [
                body
                for body in bodies
                if body.alive
            ]


    return selected_body


# ============================================================
# FORMAT MASS
# ============================================================

def format_mass(
    mass
):

    if mass < 10:

        return f"{mass:.2f}"


    if mass < 100:

        return f"{mass:.1f}"


    if mass < 1000:

        return f"{mass:.0f}"


    if mass < 100000:

        return f"{mass:,.0f}"


    return f"{mass:,.0f}"


# ============================================================
# DRAW BODY
# ============================================================

def draw_body(
    body,
    selected
):

    sx, sy = (
        body.screen_position()
    )


    radius = body.visual_radius()


    # --------------------------------------------------------
    # TRAIL
    # --------------------------------------------------------

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


    # --------------------------------------------------------
    # GLOW
    # --------------------------------------------------------

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
            body.colour[0],
            body.colour[1],
            body.colour[2],
            40
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


    # --------------------------------------------------------
    # SELECTION RING
    # --------------------------------------------------------

    if selected:

        pygame.draw.circle(

            screen,

            WHITE,

            (
                sx,
                sy
            ),

            radius + 5,

            2

        )


    # --------------------------------------------------------
    # BODY
    # --------------------------------------------------------

    pygame.draw.circle(

        screen,

        body.colour,

        (
            sx,
            sy
        ),

        radius

    )


    # --------------------------------------------------------
    # HIGHLIGHT
    # --------------------------------------------------------

    highlight_radius = max(
        1,
        radius // 3
    )


    pygame.draw.circle(

        screen,

        WHITE,

        (
            sx -
            radius // 3,

            sy -
            radius // 3
        ),

        highlight_radius

    )


# ============================================================
# DRAW BODY KEY
# ============================================================

def draw_body_key(
    bodies,
    selected_index
):

    panel_x = 15

    panel_y = 220

    panel_width = 325

    row_height = 48


    panel_height = (
        55 +
        len(bodies) *
        row_height +
        115
    )


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
            180
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


        # Selected row.

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


        # Body marker.

        marker_radius = max(

            4,

            min(
                9,
                body.visual_radius()
            )

        )


        pygame.draw.circle(

            screen,

            body.colour,

            (
                panel_x + 25,
                row_y + 21
            ),

            marker_radius

        )


        # Name.

        name_text = font_tiny.render(

            body.name,

            True,

            WHITE

        )


        screen.blit(

            name_text,

            (
                panel_x + 45,
                row_y + 5
            )

        )


        # Mass.

        if body.is_star:

            mass_label = (
                f"{format_mass(body.mass)} Earth"
            )

        else:

            mass_label = (
                f"{format_mass(body.mass)} Earth"
            )


        mass_text = font_tiny.render(

            mass_label,

            True,

            YELLOW

        )


        screen.blit(

            mass_text,

            (
                panel_x + 45,
                row_y + 24
            )

        )


    # ========================================================
    # MASS CONTROL AREA
    # ========================================================

    controls_y = (
        row_start +
        len(bodies) *
        row_height +
        8
    )


    pygame.draw.line(

        screen,

        MID_GREY,

        (
            panel_x + 15,
            controls_y
        ),

        (
            panel_x +
            panel_width -
            15,

            controls_y
        ),

        1

    )


    selected_mass = bodies[
        selected_index
    ].mass


    selected_label = font_tiny.render(

        "SELECTED BODY MASS",

        True,

        GREY

    )


    screen.blit(

        selected_label,

        (
            panel_x + 15,
            controls_y + 8
        )

    )


    mass_display = font_small.render(

        f"{format_mass(selected_mass)} Earth masses",

        True,

        YELLOW

    )


    screen.blit(

        mass_display,

        mass_display.get_rect(

            center=(

                panel_x +
                panel_width // 2,

                controls_y + 35

            )

        )

    )


    # --------------------------------------------------------
    # MINUS BUTTON
    # --------------------------------------------------------

    minus_rect = pygame.Rect(

        panel_x + 25,

        controls_y + 53,

        80,

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
        105,

        controls_y + 53,

        80,

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
                # UP / DOWN
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


        # ====================================================
        # DRAW
        # ====================================================

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


        # ----------------------------------------------------
        # INFORMATION
        # ----------------------------------------------------

        info = font_tiny.render(

            "Masses are measured in Earth masses",

            True,

            GREY

        )


        screen.blit(

            info,

            info.get_rect(

                center=(

                    WIDTH // 2,

                    HEIGHT * 0.84

                )

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


    # --------------------------------------------------------
    # STATE
    # --------------------------------------------------------

    simulation_time = 0.0

    paused = False

    selected_body = 0

    speed_index = 2

    trail_timer = 0.0


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
                # ESC
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

                    trail_timer = 0.0

                    speed_index = 2


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

                    pygame.K_PLUS,

                    pygame.K_KP_PLUS,

                    pygame.K_EQUALS

                ):

                    if not bodies[
                        selected_body
                    ].is_star:

                        bodies[
                            selected_body
                        ].mass = min(

                            10000.0,

                            bodies[
                                selected_body
                            ].mass + 0.1

                        )


                # ------------------------------------------------
                # DECREASE MASS
                # ------------------------------------------------

                if event.key in (

                    pygame.K_MINUS,

                    pygame.K_KP_MINUS

                ):

                    if not bodies[
                        selected_body
                    ].is_star:

                        bodies[
                            selected_body
                        ].mass = max(

                            0.01,

                            bodies[
                                selected_body
                            ].mass - 0.1

                        )


                # ------------------------------------------------
                # SPEED DOWN
                # ------------------------------------------------

                if event.key == pygame.K_LEFTBRACKET:

                    speed_index = max(

                        0,

                        speed_index - 1

                    )


                # ------------------------------------------------
                # SPEED UP
                # ------------------------------------------------

                if event.key == pygame.K_RIGHTBRACKET:

                    speed_index = min(

                        len(SPEED_LEVELS) - 1,

                        speed_index + 1

                    )


                # ------------------------------------------------
                # SPEED RESET
                # ------------------------------------------------

                if event.key == pygame.K_0:

                    speed_index = (
                        SPEED_LEVELS.index(
                            1.0
                        )
                    )


            # ====================================================
            # MOUSE
            # ====================================================

            if event.type == pygame.MOUSEBUTTONDOWN:

                mouse_pos = pygame.mouse.get_pos()


                # ------------------------------------------------
                # SPEED BUTTONS
                # ------------------------------------------------

                speed_minus, speed_plus = (
                    draw_speed_controls()
                )


                if speed_minus.collidepoint(
                    mouse_pos
                ):

                    speed_index = max(

                        0,

                        speed_index - 1

                    )


                if speed_plus.collidepoint(
                    mouse_pos
                ):

                    speed_index = min(

                        len(SPEED_LEVELS) - 1,

                        speed_index + 1

                    )


                # ------------------------------------------------
                # BODY KEY
                # ------------------------------------------------

                panel_x = 15

                panel_y = 220

                row_start = (
                    panel_y +
                    48
                )

                row_height = 48


                for i in range(
                    len(bodies)
                ):

                    row_y = (
                        row_start +
                        i *
                        row_height
                    )


                    row_rect = pygame.Rect(

                        panel_x + 8,

                        row_y,

                        309,

                        row_height - 4

                    )


                    if row_rect.collidepoint(
                        mouse_pos
                    ):

                        selected_body = i


                # ------------------------------------------------
                # MASS BUTTONS
                # ------------------------------------------------

                controls_y = (
                    row_start +
                    len(bodies) *
                    row_height +
                    8
                )


                mass_minus_rect = pygame.Rect(

                    panel_x + 25,

                    controls_y + 53,

                    80,

                    40

                )


                mass_plus_rect = pygame.Rect(

                    panel_x + 325 - 105,

                    controls_y + 53,

                    80,

                    40

                )


                if mass_minus_rect.collidepoint(
                    mouse_pos
                ):

                    if not bodies[
                        selected_body
                    ].is_star:

                        bodies[
                            selected_body
                        ].mass = max(

                            0.01,

                            bodies[
                                selected_body
                            ].mass - 0.1

                        )


                if mass_plus_rect.collidepoint(
                    mouse_pos
                ):

                    if not bodies[
                        selected_body
                    ].is_star:

                        bodies[
                            selected_body
                        ].mass = min(

                            10000.0,

                            bodies[
                                selected_body
                            ].mass + 0.1

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

            # Amount of simulation time to process this frame.

            target_simulation_time = (
                PHYSICS_DT *
                simulation_speed *
                60.0
            )


            # Number of fixed physics steps.

            physics_steps = max(

                1,

                int(
                    target_simulation_time /
                    PHYSICS_DT
                )

            )


            # Prevent runaway CPU usage.

            physics_steps = min(

                physics_steps,

                MAX_PHYSICS_STEPS_PER_FRAME

            )


            for _ in range(
                physics_steps
            ):

                physics_step(

                    bodies,

                    PHYSICS_DT

                )


                simulation_time += (
                    PHYSICS_DT
                )


                trail_timer += (
                    PHYSICS_DT
                )


                # ------------------------------------------------
                # COLLISIONS
                # ------------------------------------------------

                selected_body = (
                    check_collisions(
                        bodies,
                        selected_body
                    )
                )


                if len(bodies) == 0:

                    return


                if selected_body >= len(
                    bodies
                ):

                    selected_body = (
                        len(bodies) - 1
                    )


                # ------------------------------------------------
                # TRAIL SAMPLE
                # ------------------------------------------------

                if trail_timer >= TRAIL_SAMPLE_INTERVAL:

                    for body in bodies:

                        body.trail.append(

                            body.screen_position()

                        )


                        if len(
                            body.trail
                        ) > MAX_TRAIL_POINTS:

                            body.trail.pop(0)


                    trail_timer = 0.0


        # ====================================================
        # DRAW
        # ====================================================

        screen.fill(
            BLACK
        )


        draw_starfield()


        # ----------------------------------------------------
        # BODY TRAILS / BODIES
        # ----------------------------------------------------

        for i, body in enumerate(
            bodies
        ):

            draw_body(

                body,

                i == selected_body

            )


        # ====================================================
        # INFORMATION PANEL
        # ====================================================

        panel = pygame.Surface(

            (
                390,
                205
            ),

            pygame.SRCALPHA

        )


        panel.fill(

            (
                0,
                0,
                0,
                180
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

            "N-BODY GRAVITY v1.4",

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
            f"{simulation_time:,.2f} years",

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
            f"{simulation_speed:g}x",

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


        selected_name = bodies[
            selected_body
        ].name


        selected_mass = bodies[
            selected_body
        ].mass


        selected_text = font_tiny.render(

            f"Selected: {selected_name}    "
            f"{format_mass(selected_mass)} Earth masses",

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


        # ----------------------------------------------------
        # PAUSED
        # ----------------------------------------------------

        if paused:

            paused_text = font_medium.render(

                "PAUSED",

                True,

                RED

            )


            screen.blit(

                paused_text,

                (
                    30,
                    166
                )

            )


        # ====================================================
        # SPEED CONTROLS
        # ====================================================

        speed_minus, speed_plus = (
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
                WIDTH - 205,
                75
            )

        )


        speed_keys = font_tiny.render(

            "[ / ]    0 = 1x",

            True,

            GREY

        )


        screen.blit(

            speed_keys,

            (
                WIDTH - 185,
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
        # BOTTOM HELP
        # ====================================================

        controls = font_tiny.render(

            "← / → select    "
            "+ / − mass    "
            "[ / ] speed    "
            "SPACE pause    "
            "R restart    "
            "ESC menu    "
            "CTRL+X exit",

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


        # ====================================================
        # DISPLAY
        # ====================================================

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