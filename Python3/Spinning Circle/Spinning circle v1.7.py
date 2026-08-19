# ============================================================
# Rotating Circle Physics Simulation
# Version 1.7
# ============================================================

import pygame
import random
import math
import sys
import array


# ============================================================
# PYGAME INITIALISATION
# ============================================================

pygame.mixer.pre_init(
    frequency=44100,
    size=-16,
    channels=1,
    buffer=512
)

pygame.init()


# ============================================================
# DISPLAY DETECTION
# ============================================================

display_info = pygame.display.Info()

WIDTH = display_info.current_w
HEIGHT = display_info.current_h

if WIDTH <= 0 or HEIGHT <= 0:
    WIDTH = 1920
    HEIGHT = 1080


# ============================================================
# FULLSCREEN DISPLAY
# ============================================================

screen = pygame.display.set_mode(
    (WIDTH, HEIGHT),
    pygame.FULLSCREEN
)

pygame.display.set_caption(
    "Rotating Circle Physics"
)


# ============================================================
# CLOCK
# ============================================================

clock = pygame.time.Clock()


# ============================================================
# GENERAL SETTINGS
# ============================================================

FPS = 120

MAX_BALLS = 100


# ============================================================
# CIRCLE SETTINGS
# ============================================================

CIRCLE_RADIUS = int(
    min(WIDTH, HEIGHT) * 0.32
)

WALL_THICKNESS = 3


# ============================================================
# GAP SETTINGS
# ============================================================

PIXELS_PER_CM = 10

GAP_WIDTH_CM = 20

GAP_WIDTH_PIXELS = (
    GAP_WIDTH_CM
    * PIXELS_PER_CM
)


# ============================================================
# BALL SETTINGS
# ============================================================

BALL_RADIUS = 10


# ============================================================
# GRAVITY
# ============================================================

GRAVITY = 250.0


# ============================================================
# ROTATION
# ============================================================
#
# One complete revolution every 15 seconds.
#
# ============================================================

ROTATION_PERIOD = 15.0

ANGULAR_SPEED = (
    2.0
    * math.pi
    / ROTATION_PERIOD
)


# ============================================================
# COLLISION SETTINGS
# ============================================================

BOUNCE_RESTITUTION = 1.0


# ============================================================
# BOUNCE HEIGHT
# ============================================================
#
# Calculate the velocity required for a ball to travel from
# the bottom of the circle towards the top.
#
# v² = u² + 2gh
#
# Therefore:
#
# u = sqrt(2gh)
#
# ============================================================

BOUNCE_HEIGHT = (
    (CIRCLE_RADIUS - BALL_RADIUS)
    * 1.85
)

REQUIRED_BOUNCE_SPEED = math.sqrt(
    2.0
    * GRAVITY
    * BOUNCE_HEIGHT
)


# ============================================================
# BALL SPEED
# ============================================================

INITIAL_SPEED_MIN = (
    REQUIRED_BOUNCE_SPEED
    * 0.90
)

INITIAL_SPEED_MAX = (
    REQUIRED_BOUNCE_SPEED
    * 1.10
)

SPAWN_SPEED_MIN = (
    REQUIRED_BOUNCE_SPEED
    * 0.90
)

SPAWN_SPEED_MAX = (
    REQUIRED_BOUNCE_SPEED
    * 1.10
)


# ============================================================
# COLOURS
# ============================================================

BACKGROUND = (
    10,
    12,
    18
)

WALL_COLOUR = (
    220,
    220,
    230
)

TEXT_COLOUR = (
    235,
    235,
    235
)

ORIGINAL_BALL_COLOUR = (
    80,
    190,
    255
)


# ============================================================
# CIRCLE CENTRE
# ============================================================

CENTER_X = WIDTH // 2
CENTER_Y = HEIGHT // 2


# ============================================================
# GAP ANGLE
# ============================================================

GAP_ANGLE_WIDTH = (
    GAP_WIDTH_PIXELS
    / CIRCLE_RADIUS
)

GAP_ANGLE_HALF_WIDTH = (
    GAP_ANGLE_WIDTH
    / 2.0
)

gap_angle = 0.0


# ============================================================
# FONTS
# ============================================================

font_size = max(
    20,
    int(
        min(WIDTH, HEIGHT)
        * 0.022
    )
)

small_font_size = max(
    17,
    int(
        min(WIDTH, HEIGHT)
        * 0.018
    )
)

big_font_size = max(
    32,
    int(
        min(WIDTH, HEIGHT)
        * 0.045
    )
)

font = pygame.font.SysFont(
    "Arial",
    font_size
)

small_font = pygame.font.SysFont(
    "Arial",
    small_font_size
)

big_font = pygame.font.SysFont(
    "Arial",
    big_font_size
)


# ============================================================
# SOUND GENERATION
# ============================================================

def create_tone(
    frequency,
    duration,
    volume
):

    sample_rate = 44100

    samples = int(
        sample_rate
        * duration
    )

    amplitude = int(
        32767
        * volume
    )

    buffer = array.array(
        "h"
    )

    for i in range(samples):

        t = (
            i
            / sample_rate
        )

        envelope = math.exp(
            -5.0
            * t
            / duration
        )

        sample = int(
            amplitude
            * envelope
            * math.sin(
                2.0
                * math.pi
                * frequency
                * t
            )
        )

        buffer.append(
            sample
        )

    return pygame.mixer.Sound(
        buffer=buffer.tobytes()
    )


bounce_sound = create_tone(
    520,
    0.045,
    0.22
)

new_ball_sound = create_tone(
    880,
    0.12,
    0.28
)


# ============================================================
# ANGLE FUNCTIONS
# ============================================================

def normalize_angle(
    angle
):

    return angle % (
        2.0
        * math.pi
    )


def angle_difference(
    a,
    b
):

    return (
        (
            a
            - b
            + math.pi
        )
        % (
            2.0
            * math.pi
        )
    ) - math.pi


# ============================================================
# RANDOM BALL COLOUR
# ============================================================

def random_ball_colour():

    while True:

        colour = (
            random.randint(
                70,
                255
            ),
            random.randint(
                70,
                255
            ),
            random.randint(
                70,
                255
            )
        )

        if sum(colour) >= 300:

            return colour


# ============================================================
# RANDOM INTERNAL SPAWN POSITION
# ============================================================
#
# Balls are deliberately spawned well inside the circle.
#
# They are NOT spawned based on the position of the ball that
# passed through the gap.
#
# ============================================================

def random_internal_position():

    usable_radius = (
        CIRCLE_RADIUS
        - BALL_RADIUS
        - 60
    )

    spawn_radius = (
        usable_radius
        * 0.70
    )

    r = math.sqrt(
        random.random()
    ) * spawn_radius

    angle = random.uniform(
        0.0,
        2.0 * math.pi
    )

    x = (
        CENTER_X
        + math.cos(angle)
        * r
    )

    y = (
        CENTER_Y
        + math.sin(angle)
        * r
    )

    return x, y


# ============================================================
# BALL CLASS
# ============================================================

class Ball:

    def __init__(
        self,
        x=None,
        y=None,
        vx=None,
        vy=None,
        colour=None
    ):

        # ----------------------------------------------------
        # Position
        # ----------------------------------------------------

        if x is None or y is None:

            x, y = (
                random_internal_position()
            )

        self.x = x
        self.y = y

        # ----------------------------------------------------
        # Velocity
        # ----------------------------------------------------

        if vx is None or vy is None:

            angle = random.uniform(
                0.0,
                2.0 * math.pi
            )

            speed = random.uniform(
                INITIAL_SPEED_MIN,
                INITIAL_SPEED_MAX
            )

            self.vx = (
                math.cos(angle)
                * speed
            )

            self.vy = (
                math.sin(angle)
                * speed
            )

        else:

            self.vx = vx
            self.vy = vy

        # ----------------------------------------------------
        # Colour
        # ----------------------------------------------------

        if colour is None:

            self.colour = (
                random_ball_colour()
            )

        else:

            self.colour = colour

        # ----------------------------------------------------
        # Gap cooldown
        # ----------------------------------------------------

        self.gap_cooldown = 0.0

    # ========================================================
    # UPDATE
    # ========================================================

    def update(
        self,
        dt
    ):

        # Gravity

        self.vy += (
            GRAVITY
            * dt
        )

        # ----------------------------------------------------
        # IMPORTANT:
        #
        # There is NO damping here.
        #
        # Velocity is never artificially reduced.
        # ----------------------------------------------------

        self.x += (
            self.vx
            * dt
        )

        self.y += (
            self.vy
            * dt
        )

        if self.gap_cooldown > 0.0:

            self.gap_cooldown -= dt

    # ========================================================
    # DRAW
    # ========================================================

    def draw(
        self,
        surface
    ):

        pygame.draw.circle(
            surface,
            self.colour,
            (
                int(self.x),
                int(self.y)
            ),
            BALL_RADIUS
        )

    # ========================================================
    # ANGLE FROM CENTRE
    # ========================================================

    def angle_from_centre(self):

        return math.atan2(
            self.y
            - CENTER_Y,
            self.x
            - CENTER_X
        )

    # ========================================================
    # GAP TEST
    # ========================================================

    def is_inside_gap(self):

        difference = (
            angle_difference(
                self.angle_from_centre(),
                gap_angle
            )
        )

        return (
            abs(difference)
            <= GAP_ANGLE_HALF_WIDTH
        )

    # ========================================================
    # WALL COLLISION
    # ========================================================

    def handle_boundary(self):

        dx = (
            self.x
            - CENTER_X
        )

        dy = (
            self.y
            - CENTER_Y
        )

        distance = math.sqrt(
            dx * dx
            + dy * dy
        )

        if distance == 0.0:

            return False

        wall_radius = (
            CIRCLE_RADIUS
            - BALL_RADIUS
        )

        # ----------------------------------------------------
        # Still inside circle
        # ----------------------------------------------------

        if distance < wall_radius:

            return False

        # ====================================================
        # GAP
        # ====================================================

        if self.is_inside_gap():

            if self.gap_cooldown <= 0.0:

                self.gap_cooldown = 0.75

                return True

            return False

        # ====================================================
        # WALL COLLISION
        # ====================================================

        nx = (
            dx
            / distance
        )

        ny = (
            dy
            / distance
        )

        # ----------------------------------------------------
        # Push ball back inside
        # ----------------------------------------------------

        self.x = (
            CENTER_X
            + nx
            * wall_radius
        )

        self.y = (
            CENTER_Y
            + ny
            * wall_radius
        )

        # ====================================================
        # ROTATING WALL VELOCITY
        # ====================================================

        rx = (
            self.x
            - CENTER_X
        )

        ry = (
            self.y
            - CENTER_Y
        )

        wall_vx = (
            -ANGULAR_SPEED
            * ry
        )

        wall_vy = (
            ANGULAR_SPEED
            * rx
        )

        # ====================================================
        # VELOCITY RELATIVE TO WALL
        # ====================================================

        relative_vx = (
            self.vx
            - wall_vx
        )

        relative_vy = (
            self.vy
            - wall_vy
        )

        velocity_normal = (
            relative_vx * nx
            + relative_vy * ny
        )

        # ====================================================
        # ELASTIC REFLECTION
        # ====================================================

        if velocity_normal > 0.0:

            relative_vx -= (
                (
                    1.0
                    + BOUNCE_RESTITUTION
                )
                * velocity_normal
                * nx
            )

            relative_vy -= (
                (
                    1.0
                    + BOUNCE_RESTITUTION
                )
                * velocity_normal
                * ny
            )

            self.vx = (
                relative_vx
                + wall_vx
            )

            self.vy = (
                relative_vy
                + wall_vy
            )

            bounce_sound.play()

        return False


# ============================================================
# BALL-TO-BALL ELASTIC COLLISION
# ============================================================

def handle_ball_collision(
    ball_a,
    ball_b
):

    dx = (
        ball_b.x
        - ball_a.x
    )

    dy = (
        ball_b.y
        - ball_a.y
    )

    distance_squared = (
        dx * dx
        + dy * dy
    )

    minimum_distance = (
        BALL_RADIUS
        * 2.0
    )

    minimum_distance_squared = (
        minimum_distance
        * minimum_distance
    )

    # --------------------------------------------------------
    # No collision
    # --------------------------------------------------------

    if (
        distance_squared
        >= minimum_distance_squared
    ):

        return False

    # ========================================================
    # HANDLE EXACT OVERLAP
    # ========================================================

    if distance_squared < 0.000001:

        angle = random.uniform(
            0.0,
            2.0 * math.pi
        )

        nx = math.cos(angle)
        ny = math.sin(angle)

        distance = 0.000001

    else:

        distance = math.sqrt(
            distance_squared
        )

        nx = (
            dx
            / distance
        )

        ny = (
            dy
            / distance
        )

    # ========================================================
    # SEPARATE OVERLAPPING BALLS
    # ========================================================

    overlap = (
        minimum_distance
        - distance
    )

    correction = (
        overlap
        / 2.0
    )

    ball_a.x -= (
        nx
        * correction
    )

    ball_a.y -= (
        ny
        * correction
    )

    ball_b.x += (
        nx
        * correction
    )

    ball_b.y += (
        ny
        * correction
    )

    # ========================================================
    # RELATIVE VELOCITY
    # ========================================================

    relative_vx = (
        ball_b.vx
        - ball_a.vx
    )

    relative_vy = (
        ball_b.vy
        - ball_a.vy
    )

    velocity_along_normal = (
        relative_vx * nx
        + relative_vy * ny
    )

    # --------------------------------------------------------
    # Already moving apart
    # --------------------------------------------------------

    if velocity_along_normal >= 0.0:

        return False

    # ========================================================
    # PERFECTLY ELASTIC COLLISION
    # ========================================================
    #
    # Equal masses.
    #
    # Restitution = 1.
    #
    # ========================================================

    impulse = (
        -(1.0 + BOUNCE_RESTITUTION)
        * velocity_along_normal
        / 2.0
    )

    impulse_x = (
        impulse
        * nx
    )

    impulse_y = (
        impulse
        * ny
    )

    ball_a.vx -= impulse_x
    ball_a.vy -= impulse_y

    ball_b.vx += impulse_x
    ball_b.vy += impulse_y

    return True


# ============================================================
# INITIAL BALL
# ============================================================

balls = [
    Ball(
        colour=ORIGINAL_BALL_COLOUR
    )
]


# ============================================================
# SPAWN THREE BALLS
# ============================================================

def spawn_three_balls():

    for _ in range(3):

        if len(balls) >= MAX_BALLS:

            return

        # ----------------------------------------------------
        # Completely independent random position.
        # ----------------------------------------------------

        x, y = (
            random_internal_position()
        )

        # ----------------------------------------------------
        # Random direction.
        # ----------------------------------------------------

        angle = random.uniform(
            0.0,
            2.0 * math.pi
        )

        speed = random.uniform(
            SPAWN_SPEED_MIN,
            SPAWN_SPEED_MAX
        )

        vx = (
            math.cos(angle)
            * speed
        )

        vy = (
            math.sin(angle)
            * speed
        )

        new_ball = Ball(
            x=x,
            y=y,
            vx=vx,
            vy=vy,
            colour=random_ball_colour()
        )

        # Prevent immediately triggering the gap.

        new_ball.gap_cooldown = 1.0

        balls.append(
            new_ball
        )

        new_ball_sound.play()


# ============================================================
# DRAW ROTATING CIRCLE
# ============================================================

def draw_rotating_circle(
    surface
):

    segments = 720

    previous_point = None

    for i in range(
        segments + 1
    ):

        angle = (
            2.0
            * math.pi
            * i
            / segments
        )

        difference = (
            angle_difference(
                angle,
                gap_angle
            )
        )

        # ----------------------------------------------------
        # Gap
        # ----------------------------------------------------

        if (
            abs(difference)
            <= GAP_ANGLE_HALF_WIDTH
        ):

            previous_point = None

            continue

        x = (
            CENTER_X
            + math.cos(angle)
            * CIRCLE_RADIUS
        )

        y = (
            CENTER_Y
            + math.sin(angle)
            * CIRCLE_RADIUS
        )

        current_point = (
            int(x),
            int(y)
        )

        if previous_point is not None:

            pygame.draw.line(
                surface,
                WALL_COLOUR,
                previous_point,
                current_point,
                WALL_THICKNESS
            )

        previous_point = (
            current_point
        )


# ============================================================
# MAIN LOOP
# ============================================================

running = True

simulation_finished = False

simulation_time = 0.0


while running:

    # ========================================================
    # DELTA TIME
    # ========================================================

    dt = (
        clock.tick(FPS)
        / 1000.0
    )

    # Prevent a large frame time from destabilising physics.

    dt = min(
        dt,
        0.025
    )

    # ========================================================
    # EVENTS
    # ========================================================

    for event in pygame.event.get():

        if event.type == pygame.QUIT:

            running = False

        elif event.type == pygame.KEYDOWN:

            # ------------------------------------------------
            # CTRL + X
            # ------------------------------------------------

            if (
                event.key == pygame.K_x
                and (
                    pygame.key.get_mods()
                    & pygame.KMOD_CTRL
                )
            ):

                running = False

    # ========================================================
    # SIMULATION
    # ========================================================

    if not simulation_finished:

        simulation_time += dt

        # ====================================================
        # ROTATE GAP
        # ====================================================

        gap_angle += (
            ANGULAR_SPEED
            * dt
        )

        gap_angle = (
            normalize_angle(
                gap_angle
            )
        )

        # ====================================================
        # UPDATE BALLS
        # ====================================================

        spawn_count = 0

        for ball in balls:

            ball.update(
                dt
            )

            if ball.handle_boundary():

                spawn_count += 1

        # ====================================================
        # BALL-TO-BALL COLLISIONS
        # ====================================================
        #
        # Every pair is checked once.
        #
        # ====================================================

        collision_count = 0

        for i in range(
            len(balls)
        ):

            for j in range(
                i + 1,
                len(balls)
            ):

                if handle_ball_collision(
                    balls[i],
                    balls[j]
                ):

                    collision_count += 1

        # ====================================================
        # PLAY COLLISION SOUND
        # ====================================================

        # Avoid playing hundreds of sounds simultaneously.

        if collision_count > 0:

            bounce_sound.play()


        # ====================================================
        # SPAWN NEW BALLS
        # ====================================================

        for _ in range(
            spawn_count
        ):

            spawn_three_balls()

        # ====================================================
        # BALL LIMIT
        # ====================================================

        if len(balls) >= MAX_BALLS:

            simulation_finished = True

    # ========================================================
    # DRAW
    # ========================================================

    screen.fill(
        BACKGROUND
    )

    # --------------------------------------------------------
    # Circle
    # --------------------------------------------------------

    draw_rotating_circle(
        screen
    )

    # --------------------------------------------------------
    # Balls
    # --------------------------------------------------------

    for ball in balls:

        ball.draw(
            screen
        )

    # ========================================================
    # INFORMATION
    # ========================================================

    y = 25

    information = [
        f"Balls: {len(balls)} / {MAX_BALLS}",
        (
            f"Simulation time: "
            f"{simulation_time:.1f} seconds"
        ),
        (
            f"Rotation: "
            f"1 revolution / "
            f"{ROTATION_PERIOD:.0f} seconds"
        ),
        (
            f"Gap: "
            f"{GAP_WIDTH_CM} cm"
        ),
        (
            f"Gravity: "
            f"{GRAVITY:.0f} px/s²"
        ),
        (
            f"Bounce speed: "
            f"{REQUIRED_BOUNCE_SPEED:.0f} px/s"
        ),
        (
            "Ball collisions: "
            "ELASTIC"
        ),
        (
            "Wall collisions: "
            "ELASTIC"
        ),
        (
            "Air resistance: OFF"
        ),
        (
            f"Fullscreen: "
            f"{WIDTH} x {HEIGHT}"
        )
    ]

    for line in information:

        text = small_font.render(
            line,
            True,
            TEXT_COLOUR
        )

        screen.blit(
            text,
            (
                25,
                y
            )
        )

        y += (
            small_font_size
            + 7
        )

    # ========================================================
    # CONTROLS
    # ========================================================

    controls = small_font.render(
        "CTRL + X  Exit",
        True,
        TEXT_COLOUR
    )

    screen.blit(
        controls,
        (
            25,
            HEIGHT - 45
        )
    )

    # ========================================================
    # SIMULATION COMPLETE
    # ========================================================

    if simulation_finished:

        overlay = pygame.Surface(
            (
                WIDTH,
                HEIGHT
            ),
            pygame.SRCALPHA
        )

        overlay.fill(
            (
                0,
                0,
                0,
                120
            )
        )

        screen.blit(
            overlay,
            (
                0,
                0
            )
        )

        text = big_font.render(
            "100 BALLS - SIMULATION COMPLETE",
            True,
            TEXT_COLOUR
        )

        rect = text.get_rect(
            center=(
                CENTER_X,
                CENTER_Y
            )
        )

        screen.blit(
            text,
            rect
        )

        text = font.render(
            (
                f"Final simulation time: "
                f"{simulation_time:.1f} seconds"
            ),
            True,
            TEXT_COLOUR
        )

        rect = text.get_rect(
            center=(
                CENTER_X,
                CENTER_Y
                + big_font_size
                + 20
            )
        )

        screen.blit(
            text,
            rect
        )

    # ========================================================
    # DISPLAY
    # ========================================================

    pygame.display.flip()


# ============================================================
# CLEANUP
# ============================================================

pygame.quit()

sys.exit()