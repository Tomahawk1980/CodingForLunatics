import pygame
import random
import sys
import math
import json
import os
import time


# ============================================================
# PYTHON MAZE
# Version 2.4
# (c) 2026 Stuart MacIntosh
#
# V2.4
# ------------------------------------------------------------
# - Lower 3D wall height
# - Improved perspective / floor visibility
# - Depth-sorted player and maze geometry
# - Player can be obscured by walls
# - Obstacles remain clearly visible
# - Held arrow keys continuously move player
# - Space + direction performs a two-square jump
# - Jump timing is independent of key repeat
# - Jump can be initiated with direction held + Space
# - Obstacles only placed where a valid two-square jump exists
# - Three lives
# - Return to level start after death
# - Game over screen
# - H toggles top-down map
#
# ============================================================


# ============================================================
# INITIALISATION
# ============================================================

pygame.init()

try:
    pygame.mixer.init()
except pygame.error:
    pass


INFO = pygame.display.Info()

WIDTH = INFO.current_w
HEIGHT = INFO.current_h

screen = pygame.display.set_mode(
    (WIDTH, HEIGHT),
    pygame.FULLSCREEN
)

pygame.display.set_caption("Python Maze")

clock = pygame.time.Clock()

FPS = 60

VERSION = "2.4"


# ============================================================
# COLOURS
# ============================================================

BLACK = (8, 10, 14)
WHITE = (240, 242, 245)

WALL_TOP = (68, 78, 91)
WALL_FRONT = (44, 52, 63)
WALL_SIDE = (32, 39, 48)

FLOOR = (25, 31, 39)
FLOOR_EDGE = (42, 50, 60)

GREEN = (45, 220, 105)
GREEN_DARK = (20, 105, 52)

RED = (235, 65, 65)

BLUE = (60, 150, 240)
CYAN = (65, 220, 230)

YELLOW = (245, 205, 70)

WATER = (35, 120, 205)
WATER_LIGHT = (70, 170, 230)
WATER_DARK = (18, 65, 125)

SAND = (205, 165, 80)
SAND_LIGHT = (225, 190, 105)
SAND_DARK = (125, 95, 45)

PIT = (18, 18, 23)
PIT_RIM = (55, 55, 60)

SHADOW = (0, 0, 0)


# ============================================================
# FONTS
# ============================================================

FONT_SMALL = pygame.font.Font(None, 28)
FONT = pygame.font.Font(None, 36)
FONT_MEDIUM = pygame.font.Font(None, 46)
FONT_LARGE = pygame.font.Font(None, 70)
FONT_TITLE = pygame.font.Font(None, 110)


# ============================================================
# DIFFICULTY
# ============================================================

DIFFICULTIES = {

    "Easy": {
        "maze": 17,
        "obstacles": 3,
        "min_solution": 20,
        "lives": 3,
    },

    "Medium": {
        "maze": 21,
        "obstacles": 5,
        "min_solution": 35,
        "lives": 3,
    },

    "Hard": {
        "maze": 25,
        "obstacles": 8,
        "min_solution": 55,
        "lives": 3,
    },

    "Extreme": {
        "maze": 29,
        "obstacles": 12,
        "min_solution": 80,
        "lives": 3,
    }
}


difficulty_names = list(
    DIFFICULTIES.keys()
)

difficulty_index = 1


# ============================================================
# HIGH SCORES
# ============================================================

SCORE_FILE = os.path.join(
    os.path.expanduser("~"),
    ".python_maze_scores.json"
)


def load_scores():

    try:

        if os.path.exists(
            SCORE_FILE
        ):

            with open(
                SCORE_FILE,
                "r"
            ) as f:

                data = json.load(f)

                if isinstance(
                    data,
                    list
                ):

                    return data

    except Exception:
        pass

    return []


def save_scores(scores):

    try:

        with open(
            SCORE_FILE,
            "w"
        ) as f:

            json.dump(
                scores,
                f,
                indent=2
            )

    except Exception:
        pass


high_scores = load_scores()


# ============================================================
# SOUNDS
# ============================================================

def make_noise_sound(
    duration=0.08,
    volume=0.05,
    low_freq=55,
    high_freq=145
):

    try:

        sample_rate = 44100

        samples = int(
            sample_rate * duration
        )

        buffer = bytearray()

        phase = 0.0

        for i in range(samples):

            progress = i / samples

            envelope = (
                1.0 - progress
            ) ** 2

            noise = random.uniform(
                -1.0,
                1.0
            )

            freq = (
                low_freq
                +
                (
                    high_freq
                    - low_freq
                )
                * progress
            )

            phase += (
                2
                * math.pi
                * freq
                / sample_rate
            )

            tone = math.sin(
                phase
            )

            value = (
                noise * 0.55
                +
                tone * 0.45
            )

            value *= envelope
            value *= volume

            sample = (
                int(value * 127)
                + 128
            )

            buffer.append(
                max(
                    0,
                    min(
                        255,
                        sample
                    )
                )
            )

        return pygame.mixer.Sound(
            buffer=bytes(buffer)
        )

    except Exception:

        return None


def make_tone(
    frequency,
    duration,
    volume=0.12
):

    try:

        sample_rate = 44100

        samples = int(
            sample_rate * duration
        )

        buffer = bytearray()

        for i in range(samples):

            t = (
                i
                /
                sample_rate
            )

            progress = (
                i
                /
                samples
            )

            envelope = (
                1.0
                -
                progress
            )

            value = math.sin(
                2
                * math.pi
                * frequency
                * t
            )

            value *= envelope
            value *= volume

            sample = (
                int(value * 127)
                + 128
            )

            buffer.append(
                max(
                    0,
                    min(
                        255,
                        sample
                    )
                )
            )

        return pygame.mixer.Sound(
            buffer=bytes(buffer)
        )

    except Exception:

        return None


move_sound = make_noise_sound(
    0.075,
    0.045,
    50,
    130
)

jump_sound = make_tone(
    175,
    0.16,
    0.09
)

death_sound = make_tone(
    70,
    0.42,
    0.14
)

start_sound = make_tone(
    440,
    0.14,
    0.12
)

exit_sound = make_tone(
    880,
    0.32,
    0.16
)


def play_sound(sound):

    if sound is None:
        return

    try:
        sound.play()
    except Exception:
        pass


# ============================================================
# UTILITY
# ============================================================

def distance(a, b):

    return (
        abs(a[0] - b[0])
        +
        abs(a[1] - b[1])
    )


# ============================================================
# MAZE GENERATION
# ============================================================

def generate_maze(size):

    maze = [
        [1 for _ in range(size)]
        for _ in range(size)
    ]

    start = (1, 1)

    maze[1][1] = 0

    stack = [start]

    while stack:

        x, y = stack[-1]

        directions = [
            (0, -2),
            (2, 0),
            (0, 2),
            (-2, 0)
        ]

        random.shuffle(
            directions
        )

        carved = False

        for dx, dy in directions:

            nx = x + dx
            ny = y + dy

            if (
                1 <= nx < size - 1
                and
                1 <= ny < size - 1
                and
                maze[ny][nx] == 1
            ):

                maze[
                    y + dy // 2
                ][
                    x + dx // 2
                ] = 0

                maze[ny][nx] = 0

                stack.append(
                    (nx, ny)
                )

                carved = True

                break

        if not carved:

            stack.pop()

    # Solid perimeter.
    for i in range(size):

        maze[0][i] = 1
        maze[size - 1][i] = 1

        maze[i][0] = 1
        maze[i][size - 1] = 1

    return maze


def is_floor(
    maze,
    x,
    y
):

    rows = len(maze)
    cols = len(maze[0])

    return (
        0 <= x < cols
        and
        0 <= y < rows
        and
        maze[y][x] == 0
    )


def get_floor_cells(maze):

    cells = []

    for y in range(
        len(maze)
    ):

        for x in range(
            len(maze[0])
        ):

            if maze[y][x] == 0:

                cells.append(
                    (x, y)
                )

    return cells


# ============================================================
# PATH FINDING
# ============================================================

def find_path(
    maze,
    start,
    goal
):

    queue = [start]

    came_from = {
        start: None
    }

    while queue:

        current = queue.pop(0)

        if current == goal:

            path = []

            while current is not None:

                path.append(
                    current
                )

                current = came_from[
                    current
                ]

            path.reverse()

            return path

        x, y = current

        neighbours = [
            (x + 1, y),
            (x - 1, y),
            (x, y + 1),
            (x, y - 1)
        ]

        for nx, ny in neighbours:

            if not is_floor(
                maze,
                nx,
                ny
            ):

                continue

            cell = (
                nx,
                ny
            )

            if cell not in came_from:

                came_from[cell] = current

                queue.append(
                    cell
                )

    return None


# ============================================================
# EXIT
# ============================================================

def choose_exit(maze):

    start = (1, 1)

    cells = get_floor_cells(
        maze
    )

    candidates = []

    for cell in cells:

        if distance(
            start,
            cell
        ) < len(maze) * 2:

            continue

        path = find_path(
            maze,
            start,
            cell
        )

        if (
            path
            and
            len(path)
            >= len(maze) + 10
        ):

            candidates.append(
                (
                    cell,
                    len(path)
                )
            )

    if not candidates:

        return max(
            cells,
            key=lambda c:
                distance(
                    start,
                    c
                )
        )

    candidates.sort(
        key=lambda item:
            item[1],
        reverse=True
    )

    selection = candidates[
        :max(
            1,
            len(candidates) // 4
        )
    ]

    return random.choice(
        selection
    )[0]


# ============================================================
# OBSTACLES
# ============================================================

OBSTACLE_TYPES = [
    "WATER",
    "SAND",
    "PIT"
]


def valid_jump_cells(
    maze,
    x,
    y,
    dx,
    dy
):

    obstacle_x = x + dx
    obstacle_y = y + dy

    landing_x = x + dx * 2
    landing_y = y + dy * 2

    return (
        is_floor(
            maze,
            obstacle_x,
            obstacle_y
        )
        and
        is_floor(
            maze,
            landing_x,
            landing_y
        )
    )


def generate_obstacles(
    maze,
    start,
    exit_pos,
    count
):

    obstacles = {}

    cells = get_floor_cells(
        maze
    )

    random.shuffle(cells)

    for x, y in cells:

        if len(obstacles) >= count:
            break

        position = (
            x,
            y
        )

        if position == start:
            continue

        if position == exit_pos:
            continue

        if distance(
            position,
            start
        ) < 5:

            continue

        # ----------------------------------------------------
        # An obstacle is only valid if there is at least one
        # direction from which the player can jump across it.
        # ----------------------------------------------------

        jumpable = False

        for dx, dy in [
            (1, 0),
            (-1, 0),
            (0, 1),
            (0, -1)
        ]:

            source_x = x - dx
            source_y = y - dy

            if valid_jump_cells(
                maze,
                source_x,
                source_y,
                dx,
                dy
            ):

                landing = (
                    x + dx,
                    y + dy
                )

                if landing != exit_pos:

                    jumpable = True
                    break

        if not jumpable:
            continue

        # Avoid clusters.
        too_close = False

        for ox, oy in obstacles:

            if distance(
                position,
                (ox, oy)
            ) <= 2:

                too_close = True
                break

        if too_close:
            continue

        obstacles[position] = random.choice(
            OBSTACLE_TYPES
        )

    return obstacles


# ============================================================
# LEVEL GENERATION
# ============================================================

def generate_level():

    settings = DIFFICULTIES[
        difficulty_names[
            difficulty_index
        ]
    ]

    size = settings["maze"]

    for _ in range(30):

        maze = generate_maze(
            size
        )

        start = (1, 1)

        exit_pos = choose_exit(
            maze
        )

        path = find_path(
            maze,
            start,
            exit_pos
        )

        if not path:
            continue

        if len(path) < settings[
            "min_solution"
        ]:

            continue

        obstacles = generate_obstacles(
            maze,
            start,
            exit_pos,
            settings[
                "obstacles"
            ]
        )

        return (
            maze,
            obstacles,
            start,
            exit_pos,
            path
        )

    maze = generate_maze(
        size
    )

    start = (1, 1)

    exit_pos = choose_exit(
        maze
    )

    path = find_path(
        maze,
        start,
        exit_pos
    )

    obstacles = generate_obstacles(
        maze,
        start,
        exit_pos,
        settings[
            "obstacles"
        ]
    )

    return (
        maze,
        obstacles,
        start,
        exit_pos,
        path
    )


# ============================================================
# 3D PROJECTION
# ============================================================

# Larger floor tiles give us a more substantial maze view.
TILE_W = 72
TILE_H = 36

# Deliberately lower than earlier versions.
WALL_HEIGHT = 29


def project(
    x,
    y,
    camera_x,
    camera_y
):

    sx = (
        WIDTH // 2
        +
        (
            x
            -
            y
            -
            camera_x
            +
            camera_y
        )
        * TILE_W
        / 2
    )

    sy = (
        HEIGHT // 2
        +
        (
            x
            +
            y
            -
            camera_x
            -
            camera_y
        )
        * TILE_H
        / 2
    )

    return (
        int(sx),
        int(sy)
    )


def tile_polygon(
    x,
    y,
    camera_x,
    camera_y
):

    cx, cy = project(
        x,
        y,
        camera_x,
        camera_y
    )

    hw = TILE_W // 2
    hh = TILE_H // 2

    return [
        (cx, cy - hh),
        (cx + hw, cy),
        (cx, cy + hh),
        (cx - hw, cy)
    ]


# ============================================================
# FLOOR
# ============================================================

def draw_floor_tile(
    x,
    y,
    camera_x,
    camera_y,
    colour=FLOOR
):

    poly = tile_polygon(
        x,
        y,
        camera_x,
        camera_y
    )

    pygame.draw.polygon(
        screen,
        colour,
        poly
    )

    pygame.draw.polygon(
        screen,
        FLOOR_EDGE,
        poly,
        1
    )


# ============================================================
# WALL
# ============================================================

def draw_wall(
    x,
    y,
    camera_x,
    camera_y
):

    top = tile_polygon(
        x,
        y,
        camera_x,
        camera_y
    )

    top_left = top[3]
    top_right = top[1]
    top_front = top[2]

    bottom_left = (
        top_left[0],
        top_left[1]
        + WALL_HEIGHT
    )

    bottom_right = (
        top_right[0],
        top_right[1]
        + WALL_HEIGHT
    )

    bottom_front = (
        top_front[0],
        top_front[1]
        + WALL_HEIGHT
    )

    # Left wall face.
    pygame.draw.polygon(
        screen,
        WALL_SIDE,
        [
            top_left,
            top_front,
            bottom_front,
            bottom_left
        ]
    )

    # Right wall face.
    pygame.draw.polygon(
        screen,
        WALL_FRONT,
        [
            top_front,
            top_right,
            bottom_right,
            bottom_front
        ]
    )

    # Complete top.
    pygame.draw.polygon(
        screen,
        WALL_TOP,
        top
    )

    # Subtle edges.
    pygame.draw.line(
        screen,
        (94, 104, 118),
        top[0],
        top[1],
        1
    )

    pygame.draw.line(
        screen,
        (94, 104, 118),
        top[0],
        top[3],
        1
    )


# ============================================================
# OBSTACLES
# ============================================================

def draw_water(
    x,
    y,
    camera_x,
    camera_y,
    animation_time
):

    poly = tile_polygon(
        x,
        y,
        camera_x,
        camera_y
    )

    pygame.draw.polygon(
        screen,
        WATER_DARK,
        poly
    )

    cx, cy = project(
        x,
        y,
        camera_x,
        camera_y
    )

    inner = [
        (
            int(
                cx
                +
                (px - cx)
                * 0.84
            ),
            int(
                cy
                +
                (py - cy)
                * 0.70
            )
        )
        for px, py in poly
    ]

    pygame.draw.polygon(
        screen,
        WATER,
        inner
    )

    phase = (
        animation_time * 1.8
        +
        x * 0.7
        +
        y * 0.4
    )

    for ring in range(2):

        pulse = (
            math.sin(
                phase
                +
                ring * math.pi
            )
            + 1
        ) / 2

        width = (
            18
            +
            int(
                pulse * 10
            )
        )

        pygame.draw.ellipse(
            screen,
            WATER_LIGHT,
            (
                cx - width // 2,
                cy - 2 + ring * 7,
                width,
                4
            ),
            1
        )


def draw_sand(
    x,
    y,
    camera_x,
    camera_y,
    animation_time
):

    poly = tile_polygon(
        x,
        y,
        camera_x,
        camera_y
    )

    pygame.draw.polygon(
        screen,
        SAND_DARK,
        poly
    )

    cx, cy = project(
        x,
        y,
        camera_x,
        camera_y
    )

    inner = [
        (
            int(
                cx
                +
                (px - cx)
                * 0.86
            ),
            int(
                cy
                +
                (py - cy)
                * 0.72
            )
        )
        for px, py in poly
    ]

    pygame.draw.polygon(
        screen,
        SAND,
        inner
    )

    random.seed(
        x * 1000
        +
        y * 37
    )

    for _ in range(9):

        px = random.uniform(
            -22,
            22
        )

        py = random.uniform(
            -7,
            7
        )

        pygame.draw.circle(
            screen,
            SAND_LIGHT,
            (
                int(cx + px),
                int(cy + py)
            ),
            random.choice(
                [1, 1, 2]
            )
        )

    random.seed()


def draw_pit(
    x,
    y,
    camera_x,
    camera_y,
    animation_time
):

    poly = tile_polygon(
        x,
        y,
        camera_x,
        camera_y
    )

    pygame.draw.polygon(
        screen,
        PIT_RIM,
        poly
    )

    cx, cy = project(
        x,
        y,
        camera_x,
        camera_y
    )

    inner = [
        (
            int(
                cx
                +
                (px - cx)
                * 0.78
            ),
            int(
                cy
                +
                (py - cy)
                * 0.60
            )
        )
        for px, py in poly
    ]

    pygame.draw.polygon(
        screen,
        PIT,
        inner
    )

    inner2 = [
        (
            int(
                cx
                +
                (px - cx)
                * 0.55
            ),
            int(
                cy
                +
                (py - cy)
                * 0.42
            )
        )
        for px, py in poly
    ]

    pygame.draw.polygon(
        screen,
        (4, 4, 7),
        inner2
    )


def draw_obstacle(
    x,
    y,
    kind,
    camera_x,
    camera_y,
    animation_time
):

    if kind == "WATER":

        draw_water(
            x,
            y,
            camera_x,
            camera_y,
            animation_time
        )

    elif kind == "SAND":

        draw_sand(
            x,
            y,
            camera_x,
            camera_y,
            animation_time
        )

    elif kind == "PIT":

        draw_pit(
            x,
            y,
            camera_x,
            camera_y,
            animation_time
        )


# ============================================================
# EXIT
# ============================================================

def draw_exit(
    x,
    y,
    camera_x,
    camera_y,
    animation_time
):

    poly = tile_polygon(
        x,
        y,
        camera_x,
        camera_y
    )

    pygame.draw.polygon(
        screen,
        (85, 35, 40),
        poly
    )

    cx, cy = project(
        x,
        y,
        camera_x,
        camera_y
    )

    pulse = (
        math.sin(
            animation_time * 3
        )
        + 1
    ) * 2

    pygame.draw.ellipse(
        screen,
        RED,
        (
            int(
                cx - 15 - pulse
            ),
            int(
                cy - 6
            ),
            int(
                30 + pulse * 2
            ),
            int(
                11 + pulse
            )
        )
    )


# ============================================================
# PLAYER
# ============================================================

def player_depth(
    x,
    y
):

    return x + y


def draw_player(
    world_x,
    world_y,
    camera_x,
    camera_y,
    moving=False,
    move_progress=0.0,
    jump_height=0.0,
    death_amount=0.0
):

    sx, sy = project(
        world_x,
        world_y,
        camera_x,
        camera_y
    )

    # --------------------------------------------------------
    # Shadow
    # --------------------------------------------------------

    shadow_width = int(
        21
        -
        jump_height * 8
    )

    shadow_width = max(
        7,
        shadow_width
    )

    pygame.draw.ellipse(
        screen,
        (5, 5, 7),
        (
            sx - shadow_width,
            sy - 3,
            shadow_width * 2,
            7
        )
    )

    # --------------------------------------------------------
    # Walking animation
    # --------------------------------------------------------

    if moving:

        phase = (
            move_progress
            * math.pi
            * 2
        )

    else:

        phase = 0.0

    leg_offset = (
        math.sin(phase)
        * 5
    )

    arm_offset = (
        math.sin(
            phase
            +
            math.pi
        )
        * 4
    )

    # --------------------------------------------------------
    # Jump height
    # --------------------------------------------------------

    vertical = int(
        jump_height * 70
    )

    base_y = (
        sy
        - 24
        - vertical
    )

    if death_amount > 0:

        base_y -= int(
            death_amount * 18
        )

    # --------------------------------------------------------
    # Death rotation-ish effect
    # --------------------------------------------------------

    squash = 1.0

    if death_amount > 0:

        squash = max(
            0.25,
            1.0
            -
            death_amount * 0.55
        )

    # --------------------------------------------------------
    # Legs
    # --------------------------------------------------------

    pygame.draw.line(
        screen,
        GREEN_DARK,
        (
            sx - 5,
            base_y + 17
        ),
        (
            sx - 5 + int(
                leg_offset
                * squash
            ),
            base_y + 30
        ),
        4
    )

    pygame.draw.line(
        screen,
        GREEN_DARK,
        (
            sx + 5,
            base_y + 17
        ),
        (
            sx + 5 - int(
                leg_offset
                * squash
            ),
            base_y + 30
        ),
        4
    )

    # --------------------------------------------------------
    # Arms
    # --------------------------------------------------------

    pygame.draw.line(
        screen,
        GREEN_DARK,
        (
            sx - 7,
            base_y + 2
        ),
        (
            sx - 12,
            base_y + 13
            + int(arm_offset)
        ),
        4
    )

    pygame.draw.line(
        screen,
        GREEN_DARK,
        (
            sx + 7,
            base_y + 2
        ),
        (
            sx + 12,
            base_y + 13
            - int(arm_offset)
        ),
        4
    )

    # --------------------------------------------------------
    # Body
    # --------------------------------------------------------

    pygame.draw.ellipse(
        screen,
        GREEN,
        (
            sx - 8,
            base_y - 4,
            16,
            24
        )
    )

    # --------------------------------------------------------
    # Head
    # --------------------------------------------------------

    pygame.draw.circle(
        screen,
        GREEN,
        (
            sx,
            base_y - 11
        ),
        9
    )

    # Eyes
    pygame.draw.circle(
        screen,
        BLACK,
        (
            sx - 3,
            base_y - 13
        ),
        1
    )

    pygame.draw.circle(
        screen,
        BLACK,
        (
            sx + 3,
            base_y - 13
        ),
        1
    )


# ============================================================
# CAMERA
# ============================================================

def calculate_camera(
    player_x,
    player_y
):

    # Keep the player centred while maintaining the maze plane.
    return (
        player_x,
        player_y
    )


# ============================================================
# RENDER MAZE
# ============================================================

def render_maze(
    maze,
    obstacles,
    player_x,
    player_y,
    exit_pos,
    jump_height,
    moving,
    move_progress,
    show_map,
    death_amount,
    animation_time
):

    screen.fill(
        (11, 14, 19)
    )

    camera_x, camera_y = calculate_camera(
        player_x,
        player_y
    )

    # --------------------------------------------------------
    # Reduced draw distance.
    #
    # The player should not see half the maze at once.
    # --------------------------------------------------------

    draw_distance = 7

    min_x = max(
        0,
        int(player_x)
        - draw_distance
    )

    max_x = min(
        len(maze[0]),
        int(player_x)
        + draw_distance
        + 1
    )

    min_y = max(
        0,
        int(player_y)
        - draw_distance
    )

    max_y = min(
        len(maze),
        int(player_y)
        + draw_distance
        + 1
    )

    render_items = []

    # --------------------------------------------------------
    # Floors
    # --------------------------------------------------------

    for y in range(
        min_y,
        max_y
    ):

        for x in range(
            min_x,
            max_x
        ):

            if maze[y][x] == 0:

                render_items.append(
                    (
                        x + y,
                        0,
                        x,
                        y,
                        "floor"
                    )
                )

    # --------------------------------------------------------
    # Obstacles
    # --------------------------------------------------------

    for (
        (x, y),
        kind
    ) in obstacles.items():

        if (
            min_x <= x < max_x
            and
            min_y <= y < max_y
        ):

            render_items.append(
                (
                    x + y,
                    1,
                    x,
                    y,
                    kind
                )
            )

    # --------------------------------------------------------
    # Exit
    # --------------------------------------------------------

    if (
        min_x <= exit_pos[0] < max_x
        and
        min_y <= exit_pos[1] < max_y
    ):

        render_items.append(
            (
                exit_pos[0]
                +
                exit_pos[1],
                1,
                exit_pos[0],
                exit_pos[1],
                "exit"
            )
        )

    # --------------------------------------------------------
    # Player
    #
    # IMPORTANT:
    #
    # Player is NOT automatically drawn last.
    #
    # It participates in the same depth ordering as the
    # world geometry. This allows wall geometry in front
    # of the player to obscure it.
    # --------------------------------------------------------

    render_items.append(
        (
            player_depth(
                player_x,
                player_y
            ),
            2,
            player_x,
            player_y,
            "player"
        )
    )

    # --------------------------------------------------------
    # Walls
    #
    # Walls are given a slightly later render priority so
    # their front faces can obscure the player when the
    # wall is physically closer to the camera.
    # --------------------------------------------------------

    for y in range(
        min_y,
        max_y
    ):

        for x in range(
            min_x,
            max_x
        ):

            if maze[y][x] == 1:

                render_items.append(
                    (
                        x + y,
                        3,
                        x,
                        y,
                        "wall"
                    )
                )

    # --------------------------------------------------------
    # Sort by isometric depth.
    # --------------------------------------------------------

    render_items.sort(
        key=lambda item: (
            item[0],
            item[1]
        )
    )

    # --------------------------------------------------------
    # Draw
    # --------------------------------------------------------

    for (
        _depth,
        _priority,
        x,
        y,
        kind
    ) in render_items:

        if kind == "floor":

            draw_floor_tile(
                x,
                y,
                camera_x,
                camera_y
            )

        elif kind == "wall":

            draw_wall(
                x,
                y,
                camera_x,
                camera_y
            )

        elif kind == "exit":

            draw_exit(
                x,
                y,
                camera_x,
                camera_y,
                animation_time
            )

        elif kind == "player":

            draw_player(
                x,
                y,
                camera_x,
                camera_y,
                moving,
                move_progress,
                jump_height,
                death_amount
            )

        else:

            draw_obstacle(
                x,
                y,
                kind,
                camera_x,
                camera_y,
                animation_time
            )

    if show_map:

        draw_mini_map(
            maze,
            obstacles,
            int(player_x),
            int(player_y),
            exit_pos
        )


# ============================================================
# MINI MAP
# ============================================================

def draw_mini_map(
    maze,
    obstacles,
    player_x,
    player_y,
    exit_pos
):

    size = 5

    map_width = (
        len(maze[0])
        * size
    )

    map_height = (
        len(maze)
        * size
    )

    panel = pygame.Surface(
        (
            map_width + 20,
            map_height + 20
        ),
        pygame.SRCALPHA
    )

    panel.fill(
        (0, 0, 0, 190)
    )

    for y in range(
        len(maze)
    ):

        for x in range(
            len(maze[0])
        ):

            if maze[y][x] == 1:

                colour = (
                    35,
                    40,
                    48
                )

            else:

                colour = (
                    190,
                    195,
                    200
                )

            pygame.draw.rect(
                panel,
                colour,
                (
                    10 + x * size,
                    10 + y * size,
                    size,
                    size
                )
            )

    for (
        x,
        y
    ), kind in obstacles.items():

        pygame.draw.rect(
            panel,
            RED,
            (
                10 + x * size,
                10 + y * size,
                size,
                size
            )
        )

    pygame.draw.rect(
        panel,
        GREEN,
        (
            10 + player_x * size,
            10 + player_y * size,
            size,
            size
        )
    )

    pygame.draw.rect(
        panel,
        YELLOW,
        (
            10 + exit_pos[0] * size,
            10 + exit_pos[1] * size,
            size,
            size
        )
    )

    screen.blit(
        panel,
        (
            WIDTH
            -
            map_width
            -
            40,
            20
        )
    )


# ============================================================
# HUD
# ============================================================

def draw_hud(
    level,
    lives,
    elapsed,
    moves,
    score
):

    pygame.draw.rect(
        screen,
        (5, 8, 12),
        (
            0,
            0,
            WIDTH,
            58
        )
    )

    texts = [
        f"LEVEL {level}",
        f"LIVES {'♥' * lives}",
        f"TIME {elapsed:05.1f}",
        f"MOVES {moves}",
        f"SCORE {score}"
    ]

    x = 20

    for text in texts:

        surface = FONT_SMALL.render(
            text,
            True,
            WHITE
        )

        screen.blit(
            surface,
            (
                x,
                18
            )
        )

        x += (
            surface.get_width()
            + 40
        )

    help_text = FONT_SMALL.render(
        "H = Map",
        True,
        (160, 170, 180)
    )

    screen.blit(
        help_text,
        (
            WIDTH - 110,
            18
        )
    )


# ============================================================
# TITLE BACKGROUND
# ============================================================

def draw_title_background(
    animation_time
):

    screen.fill(
        (10, 15, 23)
    )

    grid = 80

    offset = int(
        (
            animation_time
            * 15
        )
        % grid
    )

    for x in range(
        -grid,
        WIDTH + grid,
        grid
    ):

        pygame.draw.line(
            screen,
            (22, 35, 48),
            (
                x + offset,
                0
            ),
            (
                x + offset,
                HEIGHT
            ),
            1
        )

    for y in range(
        -grid,
        HEIGHT + grid,
        grid
    ):

        pygame.draw.line(
            screen,
            (22, 35, 48),
            (
                0,
                y + offset
            ),
            (
                WIDTH,
                y + offset
            ),
            1
        )


# ============================================================
# TITLE SCREEN
# ============================================================

def title_screen():

    global difficulty_index

    animation_start = time.time()

    while True:

        now = time.time()

        draw_title_background(
            now - animation_start
        )

        hue = (
            now * 50
        ) % 360

        colour = pygame.Color(0)

        colour.hsva = (
            hue,
            75,
            100,
            100
        )

        title = FONT_TITLE.render(
            "PYTHON MAZE",
            True,
            colour
        )

        screen.blit(
            title,
            title.get_rect(
                center=(
                    WIDTH // 2,
                    HEIGHT // 5
                )
            )
        )

        version = FONT_SMALL.render(
            "(c) 2026 Stuart MacIntosh   V "
            + VERSION,
            True,
            (180, 190, 200)
        )

        screen.blit(
            version,
            version.get_rect(
                center=(
                    WIDTH // 2,
                    HEIGHT // 5 + 80
                )
            )
        )

        buttons = [
            (
                "F1  START GAME",
                "start"
            ),
            (
                "F2  INSTRUCTIONS",
                "instructions"
            ),
            (
                "F3  DIFFICULTY: "
                +
                difficulty_names[
                    difficulty_index
                ].upper(),
                "difficulty"
            ),
            (
                "F4  HIGH SCORES",
                "scores"
            ),
            (
                "F10 EXIT",
                "exit"
            )
        ]

        button_rects = []

        start_y = (
            HEIGHT // 2 - 70
        )

        for i, (
            text,
            action
        ) in enumerate(buttons):

            rect = pygame.Rect(
                WIDTH // 2 - 230,
                start_y + i * 78,
                460,
                58
            )

            mouse_over = rect.collidepoint(
                pygame.mouse.get_pos()
            )

            colour = (
                (50, 85, 115)
                if mouse_over
                else
                (30, 48, 65)
            )

            pygame.draw.rect(
                screen,
                colour,
                rect,
                border_radius=10
            )

            pygame.draw.rect(
                screen,
                (80, 120, 150),
                rect,
                2,
                border_radius=10
            )

            text_surface = FONT.render(
                text,
                True,
                WHITE
            )

            screen.blit(
                text_surface,
                text_surface.get_rect(
                    center=rect.center
                )
            )

            button_rects.append(
                (
                    rect,
                    action
                )
            )

        pygame.display.flip()

        for event in pygame.event.get():

            if event.type == pygame.QUIT:

                pygame.quit()
                sys.exit()

            if event.type == pygame.KEYDOWN:

                if event.key == pygame.K_F1:

                    play_sound(
                        start_sound
                    )

                    return "start"

                if event.key == pygame.K_F2:

                    return "instructions"

                if event.key == pygame.K_F3:

                    difficulty_index = (
                        difficulty_index + 1
                    ) % len(
                        difficulty_names
                    )

                if event.key == pygame.K_F4:

                    return "scores"

                if event.key == pygame.K_F10:

                    pygame.quit()
                    sys.exit()

                if event.key == pygame.K_ESCAPE:

                    pygame.quit()
                    sys.exit()

            if event.type == pygame.MOUSEBUTTONDOWN:

                if event.button == 1:

                    for rect, action in button_rects:

                        if rect.collidepoint(
                            event.pos
                        ):

                            if action == "difficulty":

                                difficulty_index = (
                                    difficulty_index + 1
                                ) % len(
                                    difficulty_names
                                )

                            elif action == "exit":

                                pygame.quit()
                                sys.exit()

                            else:

                                return action


# ============================================================
# INSTRUCTIONS
# ============================================================

def instructions_screen():

    while True:

        screen.fill(
            (10, 15, 22)
        )

        title = FONT_LARGE.render(
            "INSTRUCTIONS",
            True,
            CYAN
        )

        screen.blit(
            title,
            title.get_rect(
                center=(
                    WIDTH // 2,
                    90
                )
            )
        )

        lines = [
            "ARROW KEYS       Move the player",
            "",
            "HOLD ARROW       Continue moving in that direction",
            "",
            "SPACE + ARROW    Jump over one obstacle",
            "                  and land two squares away",
            "",
            "SPACE            Hold or press with a direction",
            "",
            "H                 Toggle the top-down map",
            "                  Map is OFF by default",
            "",
            "BLUE              Water",
            "BROWN             Sand",
            "BLACK             Pit",
            "",
            "Falling into a hazard costs a life.",
            "You return to the beginning of the level.",
            "",
            "You have THREE lives.",
            "",
            "Reach the red exit to complete the level.",
            "",
            "ESC               Return to title"
        ]

        y = 160

        for line in lines:

            surface = FONT.render(
                line,
                True,
                WHITE
            )

            screen.blit(
                surface,
                (
                    WIDTH // 2
                    -
                    surface.get_width() // 2,
                    y
                )
            )

            y += 31

        back = FONT.render(
            "Press ESC to return",
            True,
            (150, 160, 170)
        )

        screen.blit(
            back,
            back.get_rect(
                center=(
                    WIDTH // 2,
                    HEIGHT - 45
                )
            )
        )

        pygame.display.flip()

        for event in pygame.event.get():

            if event.type == pygame.QUIT:

                pygame.quit()
                sys.exit()

            if event.type == pygame.KEYDOWN:

                if event.key == pygame.K_ESCAPE:

                    return


# ============================================================
# HIGH SCORES
# ============================================================

def high_scores_screen():

    global high_scores

    while True:

        screen.fill(
            (10, 15, 22)
        )

        title = FONT_LARGE.render(
            "HIGH SCORES",
            True,
            YELLOW
        )

        screen.blit(
            title,
            title.get_rect(
                center=(
                    WIDTH // 2,
                    90
                )
            )
        )

        if not high_scores:

            text = FONT_MEDIUM.render(
                "No scores recorded yet.",
                True,
                WHITE
            )

            screen.blit(
                text,
                text.get_rect(
                    center=(
                        WIDTH // 2,
                        220
                    )
                )
            )

        else:

            sorted_scores = sorted(
                high_scores,
                key=lambda x:
                    x.get(
                        "score",
                        0
                    ),
                reverse=True
            )

            for i, entry in enumerate(
                sorted_scores[:10]
            ):

                name = entry.get(
                    "name",
                    "PLAYER"
                )

                score = entry.get(
                    "score",
                    0
                )

                difficulty = entry.get(
                    "difficulty",
                    ""
                )

                text = FONT.render(
                    f"{i + 1:2d}. "
                    f"{name:<12} "
                    f"{score:6d}   "
                    f"{difficulty}",
                    True,
                    WHITE
                )

                screen.blit(
                    text,
                    (
                        WIDTH // 2 - 300,
                        170 + i * 45
                    )
                )

        clear_rect = pygame.Rect(
            WIDTH // 2 - 180,
            HEIGHT - 150,
            360,
            55
        )

        back_rect = pygame.Rect(
            WIDTH // 2 - 180,
            HEIGHT - 80,
            360,
            55
        )

        for rect, text in [
            (
                clear_rect,
                "CLEAR HIGH SCORES"
            ),
            (
                back_rect,
                "BACK"
            )
        ]:

            over = rect.collidepoint(
                pygame.mouse.get_pos()
            )

            pygame.draw.rect(
                screen,
                (
                    (60, 70, 80)
                    if over
                    else
                    (35, 45, 55)
                ),
                rect,
                border_radius=8
            )

            surface = FONT.render(
                text,
                True,
                WHITE
            )

            screen.blit(
                surface,
                surface.get_rect(
                    center=rect.center
                )
            )

        pygame.display.flip()

        for event in pygame.event.get():

            if event.type == pygame.QUIT:

                pygame.quit()
                sys.exit()

            if event.type == pygame.KEYDOWN:

                if event.key == pygame.K_ESCAPE:

                    return

            if event.type == pygame.MOUSEBUTTONDOWN:

                if event.button == 1:

                    if back_rect.collidepoint(
                        event.pos
                    ):

                        return

                    if clear_rect.collidepoint(
                        event.pos
                    ):

                        high_scores = []

                        save_scores(
                            high_scores
                        )


# ============================================================
# NAME ENTRY
# ============================================================

def enter_name(score):

    name = ""

    while True:

        screen.fill(
            (8, 12, 18)
        )

        title = FONT_LARGE.render(
            "NEW HIGH SCORE!",
            True,
            YELLOW
        )

        screen.blit(
            title,
            title.get_rect(
                center=(
                    WIDTH // 2,
                    180
                )
            )
        )

        score_text = FONT_MEDIUM.render(
            f"Score: {score}",
            True,
            WHITE
        )

        screen.blit(
            score_text,
            score_text.get_rect(
                center=(
                    WIDTH // 2,
                    280
                )
            )
        )

        prompt = FONT_MEDIUM.render(
            "Enter your name:",
            True,
            WHITE
        )

        screen.blit(
            prompt,
            prompt.get_rect(
                center=(
                    WIDTH // 2,
                    370
                )
            )
        )

        box = pygame.Rect(
            WIDTH // 2 - 250,
            420,
            500,
            65
        )

        pygame.draw.rect(
            screen,
            (30, 40, 50),
            box,
            border_radius=8
        )

        pygame.draw.rect(
            screen,
            CYAN,
            box,
            2,
            border_radius=8
        )

        name_surface = FONT_MEDIUM.render(
            name + "_",
            True,
            WHITE
        )

        screen.blit(
            name_surface,
            name_surface.get_rect(
                center=box.center
            )
        )

        pygame.display.flip()

        for event in pygame.event.get():

            if event.type == pygame.QUIT:

                pygame.quit()
                sys.exit()

            if event.type == pygame.KEYDOWN:

                if event.key == pygame.K_RETURN:

                    if not name:

                        name = "PLAYER"

                    return name[:12]

                if event.key == pygame.K_ESCAPE:

                    return "PLAYER"

                if event.key == pygame.K_BACKSPACE:

                    name = name[:-1]

                elif (
                    event.unicode
                    and
                    event.unicode.isprintable()
                    and
                    len(name) < 12
                ):

                    name += event.unicode


# ============================================================
# GAME OVER
# ============================================================

def game_over_screen(score):

    while True:

        screen.fill(
            (25, 5, 8)
        )

        title = FONT_TITLE.render(
            "GAME OVER",
            True,
            RED
        )

        screen.blit(
            title,
            title.get_rect(
                center=(
                    WIDTH // 2,
                    HEIGHT // 3
                )
            )
        )

        score_text = FONT_MEDIUM.render(
            f"Final Score: {score}",
            True,
            WHITE
        )

        screen.blit(
            score_text,
            score_text.get_rect(
                center=(
                    WIDTH // 2,
                    HEIGHT // 2
                )
            )
        )

        instruction = FONT.render(
            "Press ENTER to return to the title",
            True,
            (180, 190, 200)
        )

        screen.blit(
            instruction,
            instruction.get_rect(
                center=(
                    WIDTH // 2,
                    HEIGHT * 2 // 3
                )
            )
        )

        pygame.display.flip()

        for event in pygame.event.get():

            if event.type == pygame.QUIT:

                pygame.quit()
                sys.exit()

            if event.type == pygame.KEYDOWN:

                if event.key in (
                    pygame.K_RETURN,
                    pygame.K_ESCAPE
                ):

                    return


# ============================================================
# JUMP
# ============================================================

def get_jump(
    maze,
    x,
    y,
    dx,
    dy
):

    obstacle = (
        x + dx,
        y + dy
    )

    landing = (
        x + dx * 2,
        y + dy * 2
    )

    if not is_floor(
        maze,
        obstacle[0],
        obstacle[1]
    ):

        return None

    if not is_floor(
        maze,
        landing[0],
        landing[1]
    ):

        return None

    return (
        obstacle,
        landing
    )


# ============================================================
# DIRECTION
# ============================================================

def get_held_direction(keys):

    # The last requested direction has priority outside this
    # function. This simply detects currently held keys.

    if keys[
        pygame.K_LEFT
    ]:
        return (-1, 0)

    if keys[
        pygame.K_RIGHT
    ]:
        return (1, 0)

    if keys[
        pygame.K_UP
    ]:
        return (0, -1)

    if keys[
        pygame.K_DOWN
    ]:
        return (0, 1)

    return (0, 0)


# ============================================================
# GAME
# ============================================================

def play_game():

    settings = DIFFICULTIES[
        difficulty_names[
            difficulty_index
        ]
    ]

    level = 1

    total_score = 0

    lives = settings[
        "lives"
    ]

    while True:

        (
            maze,
            obstacles,
            start,
            exit_pos,
            solution_path
        ) = generate_level()

        player_x, player_y = start

        visual_x = float(
            player_x
        )

        visual_y = float(
            player_y
        )

        moving = False

        move_progress = 0.0

        move_start = start

        move_target = start

        jumping = False

        jump_progress = 0.0

        jump_start = start

        jump_end = start

        jump_height = 0.0

        dying = False

        death_amount = 0.0

        moves = 0

        level_start_time = time.time()

        show_map = False

        level_complete = False

        # ----------------------------------------------------
        # Input state
        # ----------------------------------------------------

        last_direction = (
            1,
            0
        )

        move_repeat_timer = 0.0

        # Time for walking from one tile to another.
        MOVE_TIME = 0.16

        # Time to complete a two-square jump.
        JUMP_TIME = 0.32

        while True:

            dt = clock.tick(
                FPS
            ) / 1000.0

            now = time.time()

            elapsed = (
                now
                -
                level_start_time
            )

            # ------------------------------------------------
            # EVENTS
            # ------------------------------------------------

            space_pressed = False

            direction_pressed = None

            for event in pygame.event.get():

                if event.type == pygame.QUIT:

                    pygame.quit()
                    sys.exit()

                if event.type == pygame.KEYDOWN:

                    if event.key == pygame.K_ESCAPE:

                        return None

                    if event.key == pygame.K_h:

                        show_map = not show_map

                    if event.key == pygame.K_SPACE:

                        space_pressed = True

                    if event.key == pygame.K_LEFT:

                        last_direction = (
                            -1,
                            0
                        )

                        direction_pressed = (
                            -1,
                            0
                        )

                    elif event.key == pygame.K_RIGHT:

                        last_direction = (
                            1,
                            0
                        )

                        direction_pressed = (
                            1,
                            0
                        )

                    elif event.key == pygame.K_UP:

                        last_direction = (
                            0,
                            -1
                        )

                        direction_pressed = (
                            0,
                            -1
                        )

                    elif event.key == pygame.K_DOWN:

                        last_direction = (
                            0,
                            1
                        )

                        direction_pressed = (
                            0,
                            1
                        )

                # ------------------------------------------------
                # GIVE UP
                # ------------------------------------------------

                if (
                    event.type
                    ==
                    pygame.MOUSEBUTTONDOWN
                ):

                    if event.button == 1:

                        give_up_rect = pygame.Rect(
                            WIDTH - 180,
                            HEIGHT - 60,
                            150,
                            40
                        )

                        if give_up_rect.collidepoint(
                            event.pos
                        ):

                            return "giveup"

            keys = pygame.key.get_pressed()

            # ------------------------------------------------
            # Update last direction from held arrows.
            # ------------------------------------------------

            held_direction = get_held_direction(
                keys
            )

            if held_direction != (
                0,
                0
            ):

                last_direction = (
                    held_direction
                )

            # ------------------------------------------------
            # JUMP
            #
            # Space can be pressed before or after the arrow
            # key. The current direction determines the jump.
            # ------------------------------------------------

            if (
                space_pressed
                and
                not moving
                and
                not jumping
                and
                not dying
            ):

                dx, dy = last_direction

                result = get_jump(
                    maze,
                    player_x,
                    player_y,
                    dx,
                    dy
                )

                if result is not None:

                    obstacle_pos, landing = result

                    jump_start = (
                        player_x,
                        player_y
                    )

                    jump_end = landing

                    jump_progress = 0.0

                    jumping = True

                    moves += 1

                    play_sound(
                        jump_sound
                    )

            # ------------------------------------------------
            # Also allow Arrow + Space when both are held.
            # ------------------------------------------------

            if (
                keys[pygame.K_SPACE]
                and
                not moving
                and
                not jumping
                and
                not dying
            ):

                dx, dy = last_direction

                result = get_jump(
                    maze,
                    player_x,
                    player_y,
                    dx,
                    dy
                )

                if result is not None:

                    obstacle_pos, landing = result

                    jump_start = (
                        player_x,
                        player_y
                    )

                    jump_end = landing

                    jump_progress = 0.0

                    jumping = True

                    moves += 1

                    play_sound(
                        jump_sound
                    )

            # ------------------------------------------------
            # MOVEMENT
            #
            # Arrow keys are now polled continuously rather
            # than relying on KEYDOWN repeat events.
            # ------------------------------------------------

            if (
                not moving
                and
                not jumping
                and
                not dying
            ):

                move_repeat_timer -= dt

                if move_repeat_timer <= 0:

                    dx, dy = last_direction

                    # Don't walk while Space is held.
                    # Space means jump mode.
                    if not keys[
                        pygame.K_SPACE
                    ]:

                        nx = (
                            player_x
                            + dx
                        )

                        ny = (
                            player_y
                            + dy
                        )

                        if is_floor(
                            maze,
                            nx,
                            ny
                        ):

                            move_start = (
                                player_x,
                                player_y
                            )

                            move_target = (
                                nx,
                                ny
                            )

                            move_progress = 0.0

                            moving = True

                            moves += 1

                            play_sound(
                                move_sound
                            )

                            move_repeat_timer = (
                                MOVE_TIME
                            )

            # ------------------------------------------------
            # WALK ANIMATION
            # ------------------------------------------------

            if moving:

                move_progress += (
                    dt
                    /
                    MOVE_TIME
                )

                if move_progress >= 1.0:

                    move_progress = 1.0

                    player_x, player_y = (
                        move_target
                    )

                    visual_x = float(
                        player_x
                    )

                    visual_y = float(
                        player_y
                    )

                    moving = False

                    if (
                        player_x,
                        player_y
                    ) == exit_pos:

                        level_complete = True

                    elif (
                        player_x,
                        player_y
                    ) in obstacles:

                        dying = True

                        death_amount = 0.0

                        play_sound(
                            death_sound
                        )

                else:

                    t = move_progress

                    smooth = (
                        t * t
                        *
                        (
                            3 - 2 * t
                        )
                    )

                    visual_x = (
                        move_start[0]
                        +
                        (
                            move_target[0]
                            -
                            move_start[0]
                        )
                        * smooth
                    )

                    visual_y = (
                        move_start[1]
                        +
                        (
                            move_target[1]
                            -
                            move_start[1]
                        )
                        * smooth
                    )

            # ------------------------------------------------
            # JUMP
            # ------------------------------------------------

            if jumping:

                jump_progress += (
                    dt
                    /
                    JUMP_TIME
                )

                if jump_progress >= 1.0:

                    jump_progress = 1.0

                    player_x, player_y = (
                        jump_end
                    )

                    visual_x = float(
                        player_x
                    )

                    visual_y = float(
                        player_y
                    )

                    jumping = False

                    jump_height = 0.0

                    # The landing square should never itself be
                    # an obstacle, but retain this check for
                    # safety.
                    if (
                        player_x,
                        player_y
                    ) in obstacles:

                        dying = True

                        death_amount = 0.0

                        play_sound(
                            death_sound
                        )

                    elif (
                        player_x,
                        player_y
                    ) == exit_pos:

                        level_complete = True

                else:

                    t = jump_progress

                    smooth = (
                        t * t
                        *
                        (
                            3 - 2 * t
                        )
                    )

                    visual_x = (
                        jump_start[0]
                        +
                        (
                            jump_end[0]
                            -
                            jump_start[0]
                        )
                        * smooth
                    )

                    visual_y = (
                        jump_start[1]
                        +
                        (
                            jump_end[1]
                            -
                            jump_start[1]
                        )
                        * smooth
                    )

                    # Full vertical arc.
                    jump_height = math.sin(
                        math.pi * t
                    )

            # ------------------------------------------------
            # DEATH
            # ------------------------------------------------

            if dying:

                death_amount += (
                    dt * 1.5
                )

                if death_amount >= 1.0:

                    lives -= 1

                    if lives <= 0:

                        game_over_screen(
                            total_score
                        )

                        return "gameover"

                    # Return to exact level start.
                    player_x, player_y = start

                    visual_x = float(
                        start[0]
                    )

                    visual_y = float(
                        start[1]
                    )

                    moving = False
                    jumping = False
                    dying = False

                    move_progress = 0.0
                    jump_progress = 0.0
                    jump_height = 0.0
                    death_amount = 0.0

                    move_repeat_timer = 0.0

            # ------------------------------------------------
            # LEVEL COMPLETE
            # ------------------------------------------------

            if level_complete:

                play_sound(
                    exit_sound
                )

                level_time_bonus = max(
                    0,
                    int(
                        1000
                        -
                        elapsed * 10
                    )
                )

                move_bonus = max(
                    0,
                    1000
                    -
                    moves * 10
                )

                level_score = (
                    1000
                    +
                    level_time_bonus
                    +
                    move_bonus
                )

                total_score += (
                    level_score
                )

                screen.fill(
                    BLACK
                )

                msg = FONT_LARGE.render(
                    f"LEVEL {level} COMPLETE!",
                    True,
                    GREEN
                )

                screen.blit(
                    msg,
                    msg.get_rect(
                        center=(
                            WIDTH // 2,
                            HEIGHT // 2 - 80
                        )
                    )
                )

                stats = FONT.render(
                    f"Time {elapsed:.1f}s    "
                    f"Moves {moves}    "
                    f"+{level_score} points",
                    True,
                    WHITE
                )

                screen.blit(
                    stats,
                    stats.get_rect(
                        center=(
                            WIDTH // 2,
                            HEIGHT // 2
                        )
                    )
                )

                pygame.display.flip()

                pygame.time.wait(
                    1800
                )

                level += 1

                break

            # ------------------------------------------------
            # RENDER
            # ------------------------------------------------

            render_maze(
                maze,
                obstacles,
                visual_x,
                visual_y,
                exit_pos,
                jump_height,
                moving,
                move_progress,
                show_map,
                death_amount,
                now
            )

            draw_hud(
                level,
                lives,
                elapsed,
                moves,
                total_score
            )

            # ------------------------------------------------
            # GIVE UP BUTTON
            # ------------------------------------------------

            give_up_rect = pygame.Rect(
                WIDTH - 180,
                HEIGHT - 60,
                150,
                40
            )

            over = give_up_rect.collidepoint(
                pygame.mouse.get_pos()
            )

            pygame.draw.rect(
                screen,
                (
                    (80, 40, 45)
                    if over
                    else
                    (55, 30, 35)
                ),
                give_up_rect,
                border_radius=8
            )

            pygame.draw.rect(
                screen,
                RED,
                give_up_rect,
                1,
                border_radius=8
            )

            give_up_text = FONT_SMALL.render(
                "GIVE UP",
                True,
                WHITE
            )

            screen.blit(
                give_up_text,
                give_up_text.get_rect(
                    center=give_up_rect.center
                )
            )

            pygame.display.flip()


# ============================================================
# SCORE PROCESSING
# ============================================================

def process_score(score=0):

    global high_scores

    name = enter_name(
        score
    )

    high_scores.append(
        {
            "name": name,
            "score": score,
            "difficulty":
                difficulty_names[
                    difficulty_index
                ]
        }
    )

    high_scores = sorted(
        high_scores,
        key=lambda x:
            x.get(
                "score",
                0
            ),
        reverse=True
    )[:20]

    save_scores(
        high_scores
    )


# ============================================================
# MAIN
# ============================================================

def main():

    while True:

        action = title_screen()

        if action == "start":

            result = play_game()

            if result == "giveup":

                # At this point play_game does not currently
                # expose its running score separately, so use
                # zero rather than corrupting the score table.
                process_score(0)

        elif action == "instructions":

            instructions_screen()

        elif action == "scores":

            high_scores_screen()


# ============================================================
# ENTRY POINT
# ============================================================

if __name__ == "__main__":

    try:

        main()

    except KeyboardInterrupt:

        pygame.quit()
        sys.exit()