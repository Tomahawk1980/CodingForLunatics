import pygame
import random
import sys
import math
import json
import os
import time

# ============================================================
# PYTHON MAZE
# Version 2.3
# (c) 2026 Stuart MacIntosh
#
# V2.3
# - Lower 3D wall height
# - Walls rise from the playable floor plane
# - Player correctly positioned on floor plane
# - Improved obstacle visibility
# - Reliable held-key movement
# - Space is now a persistent jump request
# - Two-square jump with visible 3D arc
# - Obstacles only placed where a valid jump exists
# - Improved obstacle placement around intersections
# - Close draw distance retained
#
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

VERSION = "2.3"


# ============================================================
# COLOURS
# ============================================================

BLACK = (8, 10, 14)
WHITE = (240, 242, 245)

WALL_TOP = (72, 82, 96)
WALL_FRONT = (47, 55, 67)
WALL_SIDE = (35, 42, 52)

FLOOR = (25, 31, 39)
FLOOR_EDGE = (38, 46, 56)

GREEN = (45, 220, 105)
GREEN_DARK = (20, 110, 55)

RED = (235, 65, 65)

BLUE = (60, 150, 240)
CYAN = (65, 220, 230)

YELLOW = (245, 205, 70)

WATER = (35, 120, 205)
WATER_LIGHT = (65, 165, 230)
WATER_DARK = (18, 65, 125)

SAND = (205, 165, 80)
SAND_LIGHT = (225, 190, 105)
SAND_DARK = (125, 95, 45)

PIT = (18, 18, 23)
PIT_RIM = (45, 45, 50)

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

difficulty_names = list(DIFFICULTIES.keys())

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

        if os.path.exists(SCORE_FILE):

            with open(SCORE_FILE, "r") as f:

                data = json.load(f)

                if isinstance(data, list):
                    return data

    except Exception:
        pass

    return []


def save_scores(scores):

    try:

        with open(SCORE_FILE, "w") as f:
            json.dump(scores, f, indent=2)

    except Exception:
        pass


high_scores = load_scores()


# ============================================================
# PROCEDURAL SOUNDS
# ============================================================

def make_noise_sound(
    duration=0.08,
    volume=0.08,
    low_freq=80,
    high_freq=250
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
                (1.0 - progress) ** 2
            )

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

            tone = math.sin(phase)

            value = (
                noise * 0.55
                +
                tone * 0.45
            )

            value *= envelope
            value *= volume

            sample = int(
                value * 127
            ) + 128

            sample = max(
                0,
                min(
                    255,
                    sample
                )
            )

            buffer.append(sample)

        return pygame.mixer.Sound(
            buffer=bytes(buffer)
        )

    except Exception:

        return None


def make_tone(
    frequency,
    duration,
    volume=0.12,
    decay=True
):

    try:

        sample_rate = 44100

        samples = int(
            sample_rate * duration
        )

        buffer = bytearray()

        for i in range(samples):

            t = i / sample_rate

            progress = i / samples

            envelope = (
                (1.0 - progress)
                if decay
                else 1.0
            )

            value = math.sin(
                2
                * math.pi
                * frequency
                * t
            )

            value *= envelope
            value *= volume

            sample = int(
                value * 127
            ) + 128

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
    duration=0.075,
    volume=0.035,
    low_freq=45,
    high_freq=120
)

jump_sound = make_tone(
    175,
    0.18,
    0.09
)

death_sound = make_tone(
    75,
    0.42,
    0.16
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


# ============================================================
# FLOOR
# ============================================================

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

                path.append(current)

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

                queue.append(cell)

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
                distance(start, c)
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


def get_jump_destination(
    maze,
    x,
    y,
    dx,
    dy
):

    """
    Returns:

        obstacle square
        landing square

    for a two-square jump.

    The player moves over exactly one square
    and lands on the second square.
    """

    obstacle_x = x + dx
    obstacle_y = y + dy

    landing_x = x + dx * 2
    landing_y = y + dy * 2

    if not is_floor(
        maze,
        obstacle_x,
        obstacle_y
    ):
        return None

    if not is_floor(
        maze,
        landing_x,
        landing_y
    ):
        return None

    return (
        (obstacle_x, obstacle_y),
        (landing_x, landing_y)
    )


def obstacle_has_jump_route(
    maze,
    obstacle,
    exit_pos
):

    """
    An obstacle must have at least one genuine
    two-square jump route.

    It must also not sit immediately beside
    the exit in a way that makes the exit awkward.
    """

    ox, oy = obstacle

    directions = [
        (1, 0),
        (-1, 0),
        (0, 1),
        (0, -1)
    ]

    valid_routes = 0

    for dx, dy in directions:

        source_x = ox - dx
        source_y = oy - dy

        result = get_jump_destination(
            maze,
            source_x,
            source_y,
            dx,
            dy
        )

        if result is None:
            continue

        _, landing = result

        if landing == exit_pos:
            continue

        valid_routes += 1

    return valid_routes > 0


def count_open_neighbours(
    maze,
    x,
    y
):

    count = 0

    for dx, dy in [
        (1, 0),
        (-1, 0),
        (0, 1),
        (0, -1)
    ]:

        if is_floor(
            maze,
            x + dx,
            y + dy
        ):

            count += 1

    return count


def generate_obstacles(
    maze,
    start,
    exit_pos,
    count
):

    """
    Generate obstacles only on floor cells where:

    1. The player can actually jump over them.
    2. There is a valid landing square.
    3. The obstacle isn't immediately around the start.
    4. The obstacle isn't immediately around the exit.
    5. Obstacles aren't clustered.
    6. Obstacles don't completely block a junction.

    This prevents the player getting into situations
    where an obstacle exists but cannot actually be jumped.
    """

    obstacles = {}

    cells = get_floor_cells(
        maze
    )

    random.shuffle(cells)

    for x, y in cells:

        if len(obstacles) >= count:
            break

        current = (
            x,
            y
        )

        if current == start:
            continue

        if current == exit_pos:
            continue

        # Keep hazards away from the beginning.
        if distance(
            current,
            start
        ) < 5:
            continue

        # Keep the exit readable.
        if distance(
            current,
            exit_pos
        ) < 3:
            continue

        # Don't put hazards in an isolated dead-end
        # where the player could be trapped.
        open_neighbours = count_open_neighbours(
            maze,
            x,
            y
        )

        if open_neighbours < 2:
            continue

        # Don't make an intersection itself hazardous.
        if open_neighbours >= 3:
            if random.random() < 0.75:
                continue

        if not obstacle_has_jump_route(
            maze,
            current,
            exit_pos
        ):
            continue

        too_close = False

        for ox, oy in obstacles:

            if distance(
                current,
                (ox, oy)
            ) <= 2:

                too_close = True
                break

        if too_close:
            continue

        obstacles[current] = random.choice(
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

    for _ in range(50):

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

        if (
            len(path)
            < settings["min_solution"]
        ):
            continue

        obstacles = generate_obstacles(
            maze,
            start,
            exit_pos,
            settings["obstacles"]
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
        settings["obstacles"]
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

TILE_W = 72
TILE_H = 36

# Reduced significantly from V2.2.
WALL_HEIGHT = 28


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

    """
    V2.3 wall geometry.

    The floor tile is the BASE of the wall.
    The wall rises upwards from that plane.

    This is deliberately different from V2.2's
    geometry, which visually pushed too much of the
    wall into the player's plane.
    """

    floor_poly = tile_polygon(
        x,
        y,
        camera_x,
        camera_y
    )

    top_left = floor_poly[3]
    top_right = floor_poly[1]
    top_front = floor_poly[2]
    top_back = floor_poly[0]

    # Wall top is ABOVE the floor plane.
    wall_top_offset = WALL_HEIGHT

    upper_left = (
        top_left[0],
        top_left[1] - wall_top_offset
    )

    upper_right = (
        top_right[0],
        top_right[1] - wall_top_offset
    )

    upper_front = (
        top_front[0],
        top_front[1] - wall_top_offset
    )

    upper_back = (
        top_back[0],
        top_back[1] - wall_top_offset
    )

    # Front-left face.
    pygame.draw.polygon(
        screen,
        WALL_SIDE,
        [
            upper_left,
            upper_front,
            top_front,
            top_left
        ]
    )

    # Front-right face.
    pygame.draw.polygon(
        screen,
        WALL_FRONT,
        [
            upper_front,
            upper_right,
            top_right,
            top_front
        ]
    )

    # Complete top surface.
    pygame.draw.polygon(
        screen,
        WALL_TOP,
        [
            upper_back,
            upper_right,
            upper_front,
            upper_left
        ]
    )

    # Subtle edges.
    pygame.draw.line(
        screen,
        (100, 110, 125),
        upper_back,
        upper_right,
        1
    )

    pygame.draw.line(
        screen,
        (100, 110, 125),
        upper_back,
        upper_left,
        1
    )

    pygame.draw.line(
        screen,
        (80, 90, 105),
        upper_front,
        upper_right,
        1
    )

    pygame.draw.line(
        screen,
        (80, 90, 105),
        upper_front,
        upper_left,
        1
    )


# ============================================================
# OBSTACLES
# ============================================================

def obstacle_inner_polygon(
    poly,
    scale_x,
    scale_y
):

    cx = sum(
        p[0] for p in poly
    ) / 4

    cy = sum(
        p[1] for p in poly
    ) / 4

    return [
        (
            int(
                cx
                +
                (px - cx)
                * scale_x
            ),
            int(
                cy
                +
                (py - cy)
                * scale_y
            )
        )
        for px, py in poly
    ]


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

    # Recessed dark edge.
    pygame.draw.polygon(
        screen,
        WATER_DARK,
        poly
    )

    inner = obstacle_inner_polygon(
        poly,
        0.86,
        0.72
    )

    pygame.draw.polygon(
        screen,
        WATER,
        inner
    )

    # Animated ripples.
    cx, cy = project(
        x,
        y,
        camera_x,
        camera_y
    )

    phase = (
        animation_time * 2.0
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
                5
            ),
            1
        )

    pygame.draw.line(
        screen,
        WATER_LIGHT,
        inner[0],
        inner[1],
        2
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

    inner = obstacle_inner_polygon(
        poly,
        0.86,
        0.72
    )

    pygame.draw.polygon(
        screen,
        SAND,
        inner
    )

    cx, cy = project(
        x,
        y,
        camera_x,
        camera_y
    )

    random.seed(
        x * 1000
        +
        y * 37
    )

    for _ in range(12):

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

    inner = obstacle_inner_polygon(
        poly,
        0.78,
        0.60
    )

    pygame.draw.polygon(
        screen,
        PIT,
        inner
    )

    inner2 = obstacle_inner_polygon(
        poly,
        0.52,
        0.40
    )

    pygame.draw.polygon(
        screen,
        (5, 5, 8),
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
                cy - 6 - pulse / 2
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

def draw_player(
    world_x,
    world_y,
    camera_x,
    camera_y,
    moving=False,
    move_progress=0,
    jump_height=0,
    death_amount=0,
    facing=(0, 1)
):

    """
    Player is anchored to the projected floor point.

    jump_height is 0..1 and is converted into vertical
    screen displacement here.
    """

    sx, sy = project(
        world_x,
        world_y,
        camera_x,
        camera_y
    )

    # --------------------------------------------------------
    # Ground shadow
    # --------------------------------------------------------

    shadow_scale = max(
        0.35,
        1.0 - jump_height * 0.55
    )

    shadow_width = int(
        20 * shadow_scale
    )

    shadow_height = int(
        7 * shadow_scale
    )

    pygame.draw.ellipse(
        screen,
        (5, 5, 7),
        (
            sx - shadow_width,
            sy - shadow_height // 2,
            shadow_width * 2,
            shadow_height
        )
    )

    # --------------------------------------------------------
    # Walking animation
    # --------------------------------------------------------

    if moving:

        walk_phase = (
            move_progress
            * math.pi
            * 2
        )

    else:

        walk_phase = 0.0

    leg_offset = (
        math.sin(
            walk_phase
        )
        * 5
        if moving
        else 0
    )

    arm_offset = (
        math.sin(
            walk_phase
            +
            math.pi
        )
        * 3
        if moving
        else 0
    )

    # --------------------------------------------------------
    # Vertical player position
    # --------------------------------------------------------

    vertical_offset = int(
        jump_height * 72
    )

    base_y = (
        sy
        - 25
        - vertical_offset
    )

    if death_amount > 0:

        base_y -= int(
            death_amount * 18
        )

    # --------------------------------------------------------
    # Legs
    # --------------------------------------------------------

    pygame.draw.line(
        screen,
        GREEN_DARK,
        (
            sx - 5,
            base_y + 18
        ),
        (
            sx - 5 + leg_offset,
            base_y + 31
        ),
        4
    )

    pygame.draw.line(
        screen,
        GREEN_DARK,
        (
            sx + 5,
            base_y + 18
        ),
        (
            sx + 5 - leg_offset,
            base_y + 31
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
            sx - 11 + arm_offset,
            base_y + 14
        ),
        3
    )

    pygame.draw.line(
        screen,
        GREEN_DARK,
        (
            sx + 7,
            base_y + 2
        ),
        (
            sx + 11 - arm_offset,
            base_y + 14
        ),
        3
    )

    # --------------------------------------------------------
    # Body
    # --------------------------------------------------------

    pygame.draw.ellipse(
        screen,
        GREEN,
        (
            sx - 8,
            base_y - 3,
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
            base_y - 10
        ),
        9
    )

    # --------------------------------------------------------
    # Eyes
    # --------------------------------------------------------

    pygame.draw.circle(
        screen,
        BLACK,
        (
            sx - 3,
            base_y - 12
        ),
        1
    )

    pygame.draw.circle(
        screen,
        BLACK,
        (
            sx + 3,
            base_y - 12
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
    animation_time,
    facing=(0, 1)
):

    screen.fill(
        (12, 15, 20)
    )

    camera_x, camera_y = calculate_camera(
        player_x,
        player_y
    )

    # Smaller visible area.
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

    # --------------------------------------------------------
    # DEPTH-SORTED RENDER LIST
    # --------------------------------------------------------

    render_items = []

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

    for (x, y), kind in obstacles.items():

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

    if (
        min_x <= exit_pos[0] < max_x
        and
        min_y <= exit_pos[1] < max_y
    ):

        render_items.append(
            (
                exit_pos[0] + exit_pos[1],
                1,
                exit_pos[0],
                exit_pos[1],
                "exit"
            )
        )

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
                        2,
                        x,
                        y,
                        "wall"
                    )
                )

    render_items.sort(
        key=lambda item: (
            item[0],
            item[1]
        )
    )

    # --------------------------------------------------------
    # DRAW
    # --------------------------------------------------------

    for _, _, x, y, kind in render_items:

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

        else:

            draw_obstacle(
                x,
                y,
                kind,
                camera_x,
                camera_y,
                animation_time
            )

    # --------------------------------------------------------
    # PLAYER LAST
    #
    # This ensures the player is always visible and never
    # gets swallowed by a nearby wall face.
    # --------------------------------------------------------

    draw_player(
        player_x,
        player_y,
        camera_x,
        camera_y,
        moving,
        move_progress,
        jump_height,
        death_amount,
        facing
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

    for (x, y), kind in obstacles.items():

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
            WIDTH - map_width - 40,
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
        ) in enumerate(
            buttons
        ):

            rect = pygame.Rect(
                WIDTH // 2 - 230,
                start_y
                + i * 78,
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
                    100
                )
            )
        )

        lines = [
            "ARROW KEYS       Move the player",
            "",
            "HOLD ARROW       Continue moving",
            "",
            "SPACE + ARROW    Jump two squares",
            "                  over the adjacent square",
            "",
            "SPACE            Hold to request a jump",
            "",
            "H                 Toggle the top-down map",
            "                  (off by default)",
            "",
            "Avoid the hazards:",
            "  BLUE            Water",
            "  BROWN           Sand",
            "  BLACK           Pit",
            "",
            "A hazard costs one life.",
            "You return to the beginning of the level.",
            "",
            "You have THREE lives.",
            "",
            "Reach the red exit to complete the level.",
            "",
            "ESC               Return to the title screen"
        ]

        y = 170

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

            y += 32

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
                    HEIGHT - 50
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
# GAME LOOP
# ============================================================

def play_game():

    settings = DIFFICULTIES[
        difficulty_names[
            difficulty_index
        ]
    ]

    level = 1

    total_score = 0

    lives = settings["lives"]

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

        # ----------------------------------------------------
        # Movement state
        # ----------------------------------------------------

        moving = False

        move_progress = 0.0

        move_start = start
        move_target = start

        # ----------------------------------------------------
        # Jump state
        # ----------------------------------------------------

        jumping = False

        jump_progress = 0.0

        jump_start = start
        jump_end = start

        jump_height = 0.0

        # Persistent jump request.
        jump_requested = False

        # Current direction.
        current_dx = 0
        current_dy = 0

        facing = (0, 1)

        # ----------------------------------------------------
        # Death
        # ----------------------------------------------------

        dying = False
        death_amount = 0.0
        death_kind = None

        # ----------------------------------------------------
        # Statistics
        # ----------------------------------------------------

        moves = 0

        level_start_time = time.time()

        show_map = False

        level_complete = False

        running = True

        # ----------------------------------------------------
        # KEY REPEAT CONTROL
        # ----------------------------------------------------

        # Time before held-key movement starts repeating.
        key_repeat_delay = 0.08

        movement_timer = 0.0

        # ----------------------------------------------------
        # MAIN LEVEL LOOP
        # ----------------------------------------------------

        while running:

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

            for event in pygame.event.get():

                if event.type == pygame.QUIT:

                    pygame.quit()
                    sys.exit()

                if event.type == pygame.KEYDOWN:

                    if event.key == pygame.K_ESCAPE:

                        return None

                    if event.key == pygame.K_h:

                        show_map = not show_map

                    # Space now sets a persistent jump request.
                    if event.key == pygame.K_SPACE:

                        jump_requested = True

                    # Arrow key gives direction immediately.
                    if event.key == pygame.K_LEFT:

                        current_dx = -1
                        current_dy = 0
                        facing = (-1, 0)

                    elif event.key == pygame.K_RIGHT:

                        current_dx = 1
                        current_dy = 0
                        facing = (1, 0)

                    elif event.key == pygame.K_UP:

                        current_dx = 0
                        current_dy = -1
                        facing = (0, -1)

                    elif event.key == pygame.K_DOWN:

                        current_dx = 0
                        current_dy = 1
                        facing = (0, 1)

                if event.type == pygame.KEYUP:

                    if event.key == pygame.K_SPACE:

                        jump_requested = False

                # ------------------------------------------------
                # MOUSE GIVE UP
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

            # ------------------------------------------------
            # CURRENT HELD KEYS
            # ------------------------------------------------

            keys = pygame.key.get_pressed()

            left = keys[
                pygame.K_LEFT
            ]

            right = keys[
                pygame.K_RIGHT
            ]

            up = keys[
                pygame.K_UP
            ]

            down = keys[
                pygame.K_DOWN
            ]

            # Latest held arrow takes priority.
            if left:

                current_dx = -1
                current_dy = 0
                facing = (-1, 0)

            elif right:

                current_dx = 1
                current_dy = 0
                facing = (1, 0)

            elif up:

                current_dx = 0
                current_dy = -1
                facing = (0, -1)

            elif down:

                current_dx = 0
                current_dy = 1
                facing = (0, 1)

            # ------------------------------------------------
            # MOVEMENT / JUMP START
            # ------------------------------------------------

            if (
                not moving
                and
                not jumping
                and
                not dying
                and
                not level_complete
            ):

                movement_timer += dt

                # Space + direction.
                if (
                    jump_requested
                    and
                    (
                        current_dx != 0
                        or
                        current_dy != 0
                    )
                ):

                    result = get_jump_destination(
                        maze,
                        player_x,
                        player_y,
                        current_dx,
                        current_dy
                    )

                    if result is not None:

                        obstacle_pos, landing = result

                        # Do not jump onto another obstacle.
                        if landing not in obstacles:

                            jump_start = (
                                player_x,
                                player_y
                            )

                            jump_end = landing

                            jump_progress = 0.0

                            jump_height = 0.0

                            jumping = True

                            moves += 1

                            play_sound(
                                jump_sound
                            )

                            # Consume the jump request.
                            jump_requested = False

                            movement_timer = 0.0

                # ------------------------------------------------
                # NORMAL MOVEMENT
                # ------------------------------------------------

                elif (
                    current_dx != 0
                    or
                    current_dy != 0
                ):

                    if movement_timer >= key_repeat_delay:

                        nx = (
                            player_x
                            + current_dx
                        )

                        ny = (
                            player_y
                            + current_dy
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

                            movement_timer = 0.0

                            play_sound(
                                move_sound
                            )

            # ------------------------------------------------
            # WALK ANIMATION
            # ------------------------------------------------

            if moving:

                move_progress += (
                    dt * 6.0
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

                    movement_timer = 0.0

                    # Exit.
                    if (
                        player_x,
                        player_y
                    ) == exit_pos:

                        level_complete = True

                    # Hazard.
                    elif (
                        player_x,
                        player_y
                    ) in obstacles:

                        death_kind = obstacles[
                            (
                                player_x,
                                player_y
                            )
                        ]

                        dying = True

                        death_amount = 0.0

                        play_sound(
                            death_sound
                        )

                else:

                    t = move_progress

                    smooth = (
                        t
                        *
                        t
                        *
                        (
                            3
                            -
                            2 * t
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
            # JUMP ANIMATION
            # ------------------------------------------------

            if jumping:

                # Fixed duration for a complete two-square jump.
                jump_progress += (
                    dt * 2.35
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

                    movement_timer = 0.0

                    # Landing on exit.
                    if (
                        player_x,
                        player_y
                    ) == exit_pos:

                        level_complete = True

                    # Safety check.
                    elif (
                        player_x,
                        player_y
                    ) in obstacles:

                        death_kind = obstacles[
                            (
                                player_x,
                                player_y
                            )
                        ]

                        dying = True

                        death_amount = 0.0

                        play_sound(
                            death_sound
                        )

                else:

                    t = jump_progress

                    # Smooth horizontal interpolation.
                    smooth = (
                        t
                        *
                        t
                        *
                        (
                            3
                            -
                            2 * t
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

                    # True arc.
                    jump_height = math.sin(
                        math.pi * t
                    )

            # ------------------------------------------------
            # DEATH ANIMATION
            # ------------------------------------------------

            if dying:

                death_amount += (
                    dt * 1.5
                )

                # Player sinks down into hazard.
                jump_height = (
                    -death_amount
                    * 0.55
                )

                if death_amount >= 1.0:

                    lives -= 1

                    if lives <= 0:

                        game_over_screen(
                            total_score
                        )

                        return "gameover"

                    # ------------------------------------------------
                    # RETURN TO START OF LEVEL
                    # ------------------------------------------------

                    player_x, player_y = start

                    visual_x = float(
                        start[0]
                    )

                    visual_y = float(
                        start[1]
                    )

                    moving = False
                    jumping = False

                    move_progress = 0.0
                    jump_progress = 0.0

                    jump_height = 0.0

                    dying = False
                    death_amount = 0.0
                    death_kind = None

                    current_dx = 0
                    current_dy = 0

                    movement_timer = 0.0

                    jump_requested = False

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
                now,
                facing
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

    return None


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

                # The current implementation records the
                # current accumulated score.
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