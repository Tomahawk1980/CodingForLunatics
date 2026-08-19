import pygame
import math
import random
import sys


# ============================================================
# N-BODY GRAVITATIONAL SIMULATION
# VERSION 1.5
# ============================================================
#
# Units:
#   Mass     = Earth masses
#   Distance = Astronomical Units (AU)
#   Time     = Years
#
# Controls:
#
#   LEFT / RIGHT       Select body
#   + / -              Change selected planet mass
#   [ / ]              Simulation speed
#   0                  Reset speed to 1x
#   SPACE              Pause
#   R                  Restart
#   V                  Toggle velocity vector
#   G                  Toggle gravity influence
#   ESC                Return to menu
#   CTRL + X           Exit
#
# Mouse:
#   Click body in list       Select body
#   Click + / -              Change mass
#   Click speed +/-          Change speed
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
    "N-Body Gravitational Simulation v1.5"
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

GREEN = (70, 200, 100)

YELLOW = (255, 220, 80)

RED = (255, 90, 80)

BLUE = (80, 150, 255)

CYAN = (80, 220, 220)


# ============================================================
# BODY COLOURS
# ============================================================

BODY_COLOURS = [

    (255, 210, 70),
    (90, 150, 255),
    (255, 90, 80),
    (100, 230, 130),
    (220, 120, 255),
    (255, 160, 70),
    (80, 220, 220),
    (255, 110, 190),
    (160, 160, 255),
    (180, 255, 150)

]


# ============================================================
# MASS LEVELS
# ============================================================

# These deliberately jump between useful scales so that
# changing the mass produces an obvious physical effect.

MASS_LEVELS = [

    0.10,
    0.25,
    0.50,
    1.0,
    2.0,
    5.0,
    10.0,
    20.0,
    50.0,
    100.0,
    200.0,
    500.0,
    1000.0,
    2000.0,
    5000.0,
    10000.0

]


# ============================================================
# ASTRONOMICAL CONSTANTS
# ============================================================

# Solar mass in Earth masses.

SOLAR_MASS = 332946.0


# Gravitational constant in:
#
# AU^3 / (Earth masses * year^2)

G = (
    4.0 *
    math.pi *
    math.pi
) / SOLAR_MASS


# ============================================================
# PHYSICS
# ============================================================

# Fixed timestep.
#
# Approximately 0.1 days.

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


MAX_PHYSICS_STEPS_PER_FRAME = 120


# ============================================================
# PHYSICAL RADII
# ============================================================

# Earth radius in AU.

EARTH_RADIUS_AU = 4.25875e-5


# ============================================================
# CAMERA
# ============================================================

CENTER_X = WIDTH / 2

CENTER_Y = HEIGHT / 2


# View approximately +/- 5 AU.

VIEW_AU = 5.0


PIXELS_PER_AU = (
    min(WIDTH, HEIGHT) *
    0.42
) / VIEW_AU


# ============================================================
# TRAILS
# ============================================================

MAX_TRAIL_POINTS = 600

TRAIL_SAMPLE_INTERVAL = 0.002


# ============================================================
# DISPLAY OPTIONS
# ============================================================

show_velocity = True

show_gravity = True


# ============================================================
# BODY
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

            radius = (
                18 *
                (self.mass / SOLAR_MASS) ** 0.1
            )

            return max(
                14,
                min(
                    40,
                    int(radius)
                )
            )


        # Constant-density approximation:
        #
        # radius proportional to cube root of mass.

        radius = (
            5.0 *
            self.mass ** (1.0 / 3.0)
        )


        return max(
            3,
            min(
                32,
                int(radius)
            )
        )


    # ========================================================
    # PHYSICAL RADIUS
    # ========================================================

    def physical_radius(self):

        if self.is_star:

            # Approximate solar radius.

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
# STARFIELD
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
# GRAVITY
# ============================================================

def calculate_accelerations(
    bodies
):

    for body in bodies:

        body.ax = 0.0
        body.ay = 0.0


    for i in range(
        len(bodies)
    ):

        a = bodies[i]


        for j in range(
            i + 1,
            len(bodies)
        ):

            b = bodies[j]


            dx = b.x - a.x

            dy = b.y - a.y


            distance_squared = (
                dx * dx +
                dy * dy
            )


            # Very small numerical softening.

            softening = 1e-8


            r2 = (
                distance_squared +
                softening
            )


            distance = math.sqrt(
                r2
            )


            if distance <= 0:

                continue


            factor = (
                G /
                (
                    r2 *
                    distance
                )
            )


            # Acceleration of A caused by B.

            a.ax += (
                factor *
                b.mass *
                dx
            )

            a.ay += (
                factor *
                b.mass *
                dy
            )


            # Acceleration of B caused by A.

            b.ax -= (
                factor *
                a.mass *
                dx
            )

            b.ay -= (
                factor *
                a.mass *
                dy
            )


# ============================================================
# VELOCITY VERLET
# ============================================================

def physics_step(
    bodies,
    dt
):

    calculate_accelerations(
        bodies
    )


    # First half velocity update.

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


    # Position update.

    for body in bodies:

        body.x += (
            body.vx *
            dt
        )

        body.y += (
            body.vy *
            dt
        )


    # New acceleration.

    calculate_accelerations(
        bodies
    )


    # Second half velocity update.

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
# CREATE SYSTEM
# ============================================================

def create_system(
    number_of_bodies
):

    bodies = []


    # ========================================================
    # STAR
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
    # PLANET ORBITS
    # ========================================================

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


    # Initial masses.

    starting_masses = [

        0.35,
        0.75,
        1.0,
        0.60,
        1.50,
        0.40,
        2.0,
        0.80,
        1.20

    ]


    for i in range(
        number_of_bodies - 1
    ):

        radius = (
            orbital_distances[i]
        )


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


        mass = (
            starting_masses[i]
        )


        # Keplerian orbital velocity.

        velocity = math.sqrt(

            G *
            SOLAR_MASS /
            radius

        )


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
    # TRAILS
    # ========================================================

    for body in bodies:

        body.trail.append(
            body.screen_position()
        )


    return bodies


# ============================================================
# FIND MASS LEVEL
# ============================================================

def find_mass_index(
    mass
):

    closest_index = 0

    closest_difference = float(
        "inf"
    )


    for i, level in enumerate(
        MASS_LEVELS
    ):

        difference = abs(
            level -
            mass
        )


        if difference < closest_difference:

            closest_difference = (
                difference
            )

            closest_index = i


    return closest_index


# ============================================================
# CHANGE MASS
# ============================================================

def change_mass(
    body,
    direction
):

    if body.is_star:

        return


    current_index = find_mass_index(
        body.mass
    )


    new_index = (
        current_index +
        direction
    )


    new_index = max(

        0,

        min(

            len(MASS_LEVELS) - 1,

            new_index

        )

    )


    body.mass = MASS_LEVELS[
        new_index
    ]


# ============================================================
# COLLISION / MERGE
# ============================================================

def merge_bodies(
    a,
    b
):

    # ========================================================
    # STAR ABSORBS PLANET
    # ========================================================

    if a.is_star:

        star = a
        planet = b

    elif b.is_star:

        star = b
        planet = a

    else:

        star = None


    if star is not None:

        old_star_mass = (
            star.mass
        )

        planet_mass = (
            planet.mass
        )


        new_mass = (
            old_star_mass +
            planet_mass
        )


        # Momentum conservation.

        star.vx = (

            star.vx *
            old_star_mass +

            planet.vx *
            planet_mass

        ) / new_mass


        star.vy = (

            star.vy *
            old_star_mass +

            planet.vy *
            planet_mass

        ) / new_mass


        star.mass = new_mass

        planet.alive = False


        return star


    # ========================================================
    # PLANET + PLANET
    # ========================================================

    total_mass = (
        a.mass +
        b.mass
    )


    # Centre of mass.

    a.x = (

        a.x *
        a.mass +

        b.x *
        b.mass

    ) / total_mass


    a.y = (

        a.y *
        a.mass +

        b.y *
        b.mass

    ) / total_mass


    # Momentum conservation.

    a.vx = (

        a.vx *
        a.mass +

        b.vx *
        b.mass

    ) / total_mass


    a.vy = (

        a.vy *
        a.mass +

        b.vy *
        b.mass

    ) / total_mass


    a.mass = total_mass


    b.alive = False


    return a


# ============================================================
# COLLISION DETECTION
# ============================================================

def check_collisions(
    bodies,
    selected_body
):

    collision_found = True


    while collision_found:

        collision_found = False


        for i in range(
            len(bodies)
        ):

            for j in range(
                i + 1,
                len(bodies)
            ):

                a = bodies[i]

                b = bodies[j]


                dx = b.x - a.x

                dy = b.y - a.y


                distance = math.sqrt(

                    dx * dx +
                    dy * dy

                )


                collision_distance = (

                    a.physical_radius() +
                    b.physical_radius()

                )


                if distance <= collision_distance:

                    survivor = merge_bodies(
                        a,
                        b
                    )


                    if selected_body == j:

                        selected_body = i


                    collision_found = True

                    break


            if collision_found:

                break


        if collision_found:

            bodies[:] = [

                body

                for body in bodies

                if body.alive

            ]


    if selected_body >= len(
        bodies
    ):

        selected_body = (
            len(bodies) - 1
        )


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

        return f"{mass:.0f}"


    return f"{mass:,.0f}"


# ============================================================
# DRAW GRAVITY INFLUENCE
# ============================================================

def draw_gravity_influence(
    body
):

    if body.is_star:

        return


    sx, sy = (
        body.screen_position()
    )


    # Hill sphere approximation around the selected body.
    #
    # r_H = a * (m / 3M)^(1/3)
    #
    # Here we use the distance from the star.

    distance_from_star = math.sqrt(

        body.x * body.x +
        body.y * body.y

    )


    if distance_from_star <= 0:

        return


    hill_radius = (

        distance_from_star *

        (
            body.mass /
            (
                3.0 *
                SOLAR_MASS
            )
        ) ** (1.0 / 3.0)

    )


    radius_pixels = int(

        hill_radius *
        PIXELS_PER_AU

    )


    # Don't draw tiny or enormous circles.

    if radius_pixels < 10:

        radius_pixels = 10


    if radius_pixels > min(
        WIDTH,
        HEIGHT
    ):

        radius_pixels = min(
            WIDTH,
            HEIGHT
        )


    # Transparent overlay.

    overlay = pygame.Surface(

        (
            WIDTH,
            HEIGHT
        ),

        pygame.SRCALPHA

    )


    pygame.draw.circle(

        overlay,

        (
            body.colour[0],
            body.colour[1],
            body.colour[2],
            25
        ),

        (
            sx,
            sy
        ),

        radius_pixels

    )


    pygame.draw.circle(

        overlay,

        (
            body.colour[0],
            body.colour[1],
            body.colour[2],
            110
        ),

        (
            sx,
            sy
        ),

        radius_pixels,

        1

    )


    screen.blit(
        overlay,
        (0, 0)
    )


# ============================================================
# DRAW VELOCITY VECTOR
# ============================================================

def draw_velocity_vector(
    body
):

    sx, sy = (
        body.screen_position()
    )


    velocity = math.sqrt(

        body.vx * body.vx +
        body.vy * body.vy

    )


    if velocity <= 0:

        return


    # Scale velocity vector so that normal planetary orbital
    # velocities produce useful screen lengths.

    vector_scale = (
        0.18 *
        PIXELS_PER_AU
    )


    length = (
        velocity *
        vector_scale
    )


    # Keep display manageable.

    length = max(
        15,
        min(
            180,
            length
        )
    )


    direction_x = (
        body.vx /
        velocity
    )

    direction_y = (
        body.vy /
        velocity
    )


    end_x = int(

        sx +
        direction_x *
        length

    )


    end_y = int(

        sy +
        direction_y *
        length

    )


    pygame.draw.line(

        screen,

        CYAN,

        (
            sx,
            sy
        ),

        (
            end_x,
            end_y
        ),

        2

    )


    # Arrowhead.

    angle = math.atan2(

        end_y - sy,

        end_x - sx

    )


    arrow_size = 8


    left_angle = (
        angle +
        math.radians(150)
    )


    right_angle = (
        angle -
        math.radians(150)
    )


    pygame.draw.polygon(

        screen,

        CYAN,

        [

            (
                end_x,
                end_y
            ),

            (

                end_x +
                math.cos(left_angle) *
                arrow_size,

                end_y +
                math.sin(left_angle) *
                arrow_size

            ),

            (

                end_x +
                math.cos(right_angle) *
                arrow_size,

                end_y +
                math.sin(right_angle) *
                arrow_size

            )

        ]

    )


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


    # ========================================================
    # TRAIL
    # ========================================================

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


    # ========================================================
    # GLOW
    # ========================================================

    radius = (
        body.visual_radius()
    )


    glow_radius = (
        radius +
        10
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
            45

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


    # ========================================================
    # SELECTION RING
    # ========================================================

    if selected:

        pygame.draw.circle(

            screen,

            WHITE,

            (
                sx,
                sy
            ),

            radius + 6,

            2

        )


    # ========================================================
    # BODY
    # ========================================================

    pygame.draw.circle(

        screen,

        body.colour,

        (
            sx,
            sy
        ),

        radius

    )


    # ========================================================
    # HIGHLIGHT
    # ========================================================

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

    panel_width = 340

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
            185
        )

    )


    screen.blit(

        panel,

        (
            panel_x,
            panel_y
        )

    )


    # ========================================================
    # TITLE
    # ========================================================

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


    row_start = (
        panel_y +
        48
    )


    # ========================================================
    # BODY ROWS
    # ========================================================

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

        mass_text = font_tiny.render(

            f"{format_mass(body.mass)} Earth",

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
    # MASS CONTROLS
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


    selected = bodies[
        selected_index
    ]


    label = font_tiny.render(

        "SELECTED MASS",

        True,

        GREY

    )


    screen.blit(

        label,

        (
            panel_x + 15,
            controls_y + 7
        )

    )


    mass_text = font_small.render(

        f"{format_mass(selected.mass)} Earth masses",

        True,

        YELLOW

    )


    screen.blit(

        mass_text,

        mass_text.get_rect(

            center=(

                panel_x +
                panel_width // 2,

                controls_y + 34

            )

        )

    )


    # --------------------------------------------------------
    # MINUS
    # --------------------------------------------------------

    minus_rect = pygame.Rect(

        panel_x + 25,

        controls_y + 52,

        85,

        42

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

        panel_x +
        panel_width -
        110,

        controls_y + 52,

        85,

        42

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


    # --------------------------------------------------------
    # SCALE INFORMATION
    # --------------------------------------------------------

    scale_text = font_tiny.render(

        "0.1 → 10,000 Earth masses",

        True,

        GREY

    )


    screen.blit(

        scale_text,

        scale_text.get_rect(

            center=(

                panel_x +
                panel_width // 2,

                controls_y + 108

            )

        )

    )


    return (
        minus_rect,
        plus_rect
    )


# ============================================================
# SPEED CONTROLS
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


    # Minus.

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


    # Plus.

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
# MENU
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

                # Ctrl + X.

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
        # DRAW MENU
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


        # Minus.

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


        # Plus.

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


        # Start.

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


        info = font_tiny.render(

            "Mass is measured in Earth masses",

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
    global show_velocity
    global show_gravity


    bodies = create_system(
        number_of_bodies
    )


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

                # Ctrl + X.

                if (

                    event.key == pygame.K_x

                    and

                    pygame.key.get_mods()
                    & pygame.KMOD_CTRL

                ):

                    pygame.quit()

                    sys.exit()


                # ESC.

                if event.key == pygame.K_ESCAPE:

                    return


                # Pause.

                if event.key == pygame.K_SPACE:

                    paused = not paused


                # Restart.

                if event.key == pygame.K_r:

                    bodies = create_system(
                        number_of_bodies
                    )

                    simulation_time = 0.0

                    selected_body = 0

                    trail_timer = 0.0

                    speed_index = 2


                # Previous body.

                if event.key == pygame.K_LEFT:

                    selected_body -= 1

                    if selected_body < 0:

                        selected_body = (
                            len(bodies) - 1
                        )


                # Next body.

                if event.key == pygame.K_RIGHT:

                    selected_body += 1

                    if selected_body >= len(bodies):

                        selected_body = 0


                # Increase mass.

                if event.key in (

                    pygame.K_PLUS,
                    pygame.K_KP_PLUS,
                    pygame.K_EQUALS

                ):

                    change_mass(

                        bodies[
                            selected_body
                        ],

                        1

                    )


                # Decrease mass.

                if event.key in (

                    pygame.K_MINUS,
                    pygame.K_KP_MINUS

                ):

                    change_mass(

                        bodies[
                            selected_body
                        ],

                        -1

                    )


                # Speed down.

                if event.key == pygame.K_LEFTBRACKET:

                    speed_index = max(

                        0,

                        speed_index - 1

                    )


                # Speed up.

                if event.key == pygame.K_RIGHTBRACKET:

                    speed_index = min(

                        len(SPEED_LEVELS) - 1,

                        speed_index + 1

                    )


                # Speed reset.

                if event.key == pygame.K_0:

                    speed_index = (
                        SPEED_LEVELS.index(
                            1.0
                        )
                    )


                # Velocity vectors.

                if event.key == pygame.K_v:

                    show_velocity = (
                        not show_velocity
                    )


                # Gravity influence.

                if event.key == pygame.K_g:

                    show_gravity = (
                        not show_gravity
                    )


            # =================================================
            # MOUSE
            # =================================================

            if event.type == pygame.MOUSEBUTTONDOWN:

                mouse_pos = pygame.mouse.get_pos()


                # ------------------------------------------------
                # SPEED
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
                # BODY ROWS
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

                        324,

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

                    controls_y + 52,

                    85,

                    42

                )


                mass_plus_rect = pygame.Rect(

                    panel_x + 340 - 110,

                    controls_y + 52,

                    85,

                    42

                )


                if mass_minus_rect.collidepoint(
                    mouse_pos
                ):

                    change_mass(

                        bodies[
                            selected_body
                        ],

                        -1

                    )


                if mass_plus_rect.collidepoint(
                    mouse_pos
                ):

                    change_mass(

                        bodies[
                            selected_body
                        ],

                        1

                    )


        # ====================================================
        # SPEED
        # ====================================================

        simulation_speed = SPEED_LEVELS[
            speed_index
        ]


        # ====================================================
        # PHYSICS
        # ====================================================

        if not paused:

            target_time = (

                PHYSICS_DT *
                simulation_speed *
                60.0

            )


            physics_steps = max(

                1,

                int(
                    target_time /
                    PHYSICS_DT
                )

            )


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


                # Collision detection.

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


                # Trail sampling.

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


        selected = bodies[
            selected_body
        ]


        # ----------------------------------------------------
        # GRAVITY INFLUENCE
        # ----------------------------------------------------

        if show_gravity:

            draw_gravity_influence(
                selected
            )


        # ----------------------------------------------------
        # BODIES
        # ----------------------------------------------------

        for i, body in enumerate(
            bodies
        ):

            draw_body(

                body,

                i == selected_body

            )


        # ----------------------------------------------------
        # VELOCITY VECTOR
        # ----------------------------------------------------

        if show_velocity:

            draw_velocity_vector(
                selected
            )


        # ====================================================
        # TOP INFORMATION PANEL
        # ====================================================

        panel = pygame.Surface(

            (
                430,
                230
            ),

            pygame.SRCALPHA

        )


        panel.fill(

            (
                0,
                0,
                0,
                185
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

            "N-BODY GRAVITY v1.5",

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


        selected_text = font_tiny.render(

            f"Selected: "
            f"{selected.name}",

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


        mass_text = font_tiny.render(

            f"Mass: "
            f"{format_mass(selected.mass)} "
            f"Earth masses",

            True,

            YELLOW

        )


        screen.blit(

            mass_text,

            (
                30,
                164
            )

        )


        # ====================================================
        # STATUS
        # ====================================================

        status_text = font_tiny.render(

            "V: velocity  "
            "G: gravity influence",

            True,

            GREY

        )


        screen.blit(

            status_text,

            (
                30,
                190
            )

        )


        if paused:

            paused_text = font_medium.render(

                "PAUSED",

                True,

                RED

            )


            screen.blit(

                paused_text,

                (
                    300,
                    180
                )

            )


        # ====================================================
        # SPEED CONTROLS
        # ====================================================

        draw_speed_controls()


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
        # BOTTOM CONTROLS
        # ====================================================

        controls = font_tiny.render(

            "← / → select    "
            "+ / − mass    "
            "[ / ] speed    "
            "SPACE pause    "
            "V velocity    "
            "G gravity    "
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