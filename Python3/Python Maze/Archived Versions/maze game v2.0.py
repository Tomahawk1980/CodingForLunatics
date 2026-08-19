import pygame
import random
import sys
import math
import json
import os
import time

# ============================================================
# PYTHON MAZE
# (c) 2026 Stuart MacIntosh
# Version 2.1
# ============================================================

pygame.init()

try:
    pygame.mixer.init()
except pygame.error:
    pass

# ============================================================
# DISPLAY
# ============================================================

INFO = pygame.display.Info()
WIDTH = INFO.current_w
HEIGHT = INFO.current_h

screen = pygame.display.set_mode(
    (WIDTH, HEIGHT),
    pygame.FULLSCREEN
)

pygame.display.set_caption("Python Maze")

clock = pygame.time.Clock()

# ============================================================
# COLOURS
# ============================================================

BLACK = (5, 7, 10)
BACKGROUND = (12, 18, 26)

WHITE = (235, 238, 242)
LIGHT_GREY = (175, 182, 192)
GREY = (110, 120, 135)
DARK_GREY = (45, 52, 62)

GREEN = (45, 220, 95)
LIGHT_GREEN = (105, 255, 145)
DARK_GREEN = (20, 105, 50)

RED = (225, 55, 55)
BLUE = (55, 145, 235)
CYAN = (55, 200, 215)
YELLOW = (245, 205, 65)
ORANGE = (235, 145, 55)

WALL_TOP = (82, 91, 105)
WALL_LEFT = (47, 54, 64)
WALL_RIGHT = (61, 70, 82)

FLOOR = (58, 65, 75)
FLOOR_DARK = (44, 50, 59)

WATER = (35, 105, 170)
SAND = (195, 160, 90)
PIT = (30, 31, 37)

# ============================================================
# VERSION
# ============================================================

VERSION = "2.1"

# ============================================================
# FONTS
# ============================================================

FONT_SMALL = pygame.font.Font(None, 28)
FONT = pygame.font.Font(None, 38)
FONT_MEDIUM = pygame.font.Font(None, 52)
FONT_LARGE = pygame.font.Font(None, 74)
FONT_TITLE = pygame.font.Font(None, 112)

# ============================================================
# GAME CONSTANTS
# ============================================================

START_POS = (1, 1)

DIRECTIONS = [
    (0, -1),
    (1, 0),
    (0, 1),
    (-1, 0)
]

DRAW_DISTANCE = 7

# Isometric tile dimensions.
# The floor plane and walls use these exact coordinates.
TILE_WIDTH = 82
TILE_DEPTH = 42
WALL_HEIGHT = 52

WALK_TIME = 0.16
JUMP_TIME = 0.48

MAX_LIVES = 3

HIGH_SCORE_FILE = os.path.join(
    os.path.dirname(os.path.abspath(__file__)),
    "python_maze_scores.json"
)

# ============================================================
# SOUND
# ============================================================

def make_tone(frequency, duration, volume=0.12):

    try:

        sample_rate = 44100
        samples = int(sample_rate * duration)

        buffer = bytearray()

        for i in range(samples):

            value = int(
                32767 *
                volume *
                math.sin(
                    2 * math.pi *
                    frequency *
                    i /
                    sample_rate
                )
            )

            buffer.extend(
                int(value).to_bytes(
                    2,
                    "little",
                    signed=True
                )
            )

        return pygame.mixer.Sound(
            buffer=bytes(buffer)
        )

    except Exception:
        return None


MOVE_SOUND = make_tone(
    480,
    0.045,
    0.07
)

JUMP_SOUND = make_tone(
    650,
    0.10,
    0.10
)

LAND_SOUND = make_tone(
    850,
    0.07,
    0.08
)

START_SOUND = make_tone(
    520,
    0.16,
    0.10
)

DEATH_SOUND = make_tone(
    130,
    0.35,
    0.12
)

WIN_SOUND = make_tone(
    900,
    0.20,
    0.12
)

# ============================================================
# HIGH SCORES
# ============================================================

def load_scores():

    if not os.path.exists(HIGH_SCORE_FILE):
        return []

    try:

        with open(
            HIGH_SCORE_FILE,
            "r"
        ) as f:

            scores = json.load(f)

        if isinstance(scores, list):
            return scores

    except Exception:
        pass

    return []


def save_scores(scores):

    try:

        with open(
            HIGH_SCORE_FILE,
            "w"
        ) as f:

            json.dump(
                scores,
                f,
                indent=2
            )

    except Exception:
        pass


def clear_scores():
    save_scores([])


def add_high_score(
    name,
    score,
    level,
    moves,
    elapsed
):

    scores = load_scores()

    scores.append({
        "name": name,
        "score": score,
        "level": level,
        "moves": moves,
        "time": round(elapsed, 1)
    })

    scores.sort(
        key=lambda s: s.get(
            "score",
            0
        ),
        reverse=True
    )

    save_scores(
        scores[:10]
    )

# ============================================================
# TEXT
# ============================================================

def draw_text(
    text,
    font,
    colour,
    x,
    y,
    centre=False
):

    surface = font.render(
        text,
        True,
        colour
    )

    if centre:

        rect = surface.get_rect(
            center=(x, y)
        )

    else:

        rect = surface.get_rect(
            topleft=(x, y)
        )

    screen.blit(
        surface,
        rect
    )

    return rect


def draw_panel(
    rect,
    alpha=225
):

    panel = pygame.Surface(
        rect.size,
        pygame.SRCALPHA
    )

    panel.fill(
        (9, 13, 19, alpha)
    )

    pygame.draw.rect(
        panel,
        (75, 90, 108, 200),
        panel.get_rect(),
        2
    )

    screen.blit(
        panel,
        rect.topleft
    )

# ============================================================
# MAZE GENERATION
# ============================================================

def generate_maze(
    rows,
    cols
):

    maze = [
        [1 for _ in range(cols)]
        for _ in range(rows)
    ]

    stack = [(1, 1)]

    maze[1][1] = 0

    while stack:

        x, y = stack[-1]

        neighbours = []

        directions = DIRECTIONS.copy()
        random.shuffle(directions)

        for dx, dy in directions:

            nx = x + dx * 2
            ny = y + dy * 2

            if (
                1 <= nx < cols - 1
                and
                1 <= ny < rows - 1
                and
                maze[ny][nx] == 1
            ):

                neighbours.append(
                    (
                        dx,
                        dy,
                        nx,
                        ny
                    )
                )

        if neighbours:

            dx, dy, nx, ny = random.choice(
                neighbours
            )

            maze[y + dy][x + dx] = 0
            maze[ny][nx] = 0

            stack.append(
                (nx, ny)
            )

        else:

            stack.pop()

    return maze

# ============================================================
# PATH FINDING
# ============================================================

def shortest_path(
    maze,
    start,
    end
):

    queue = [
        (start, [])
    ]

    visited = {
        start
    }

    while queue:

        position, path = queue.pop(0)

        if position == end:
            return path

        x, y = position

        for dx, dy in DIRECTIONS:

            nx = x + dx
            ny = y + dy

            if (
                0 <= nx < len(maze[0])
                and
                0 <= ny < len(maze)
                and
                maze[ny][nx] == 0
                and
                (nx, ny) not in visited
            ):

                visited.add(
                    (nx, ny)
                )

                queue.append(
                    (
                        (nx, ny),
                        path + [(nx, ny)]
                    )
                )

    return None


def reachable_cells(
    maze,
    start
):

    queue = [start]
    visited = {start}

    while queue:

        x, y = queue.pop(0)

        for dx, dy in DIRECTIONS:

            nx = x + dx
            ny = y + dy

            if (
                0 <= nx < len(maze[0])
                and
                0 <= ny < len(maze)
                and
                maze[ny][nx] == 0
                and
                (nx, ny) not in visited
            ):

                visited.add(
                    (nx, ny)
                )

                queue.append(
                    (nx, ny)
                )

    return visited

# ============================================================
# EXIT
# ============================================================

def choose_exit(
    maze
):

    reachable = reachable_cells(
        maze,
        START_POS
    )

    candidates = []

    for position in reachable:

        if position == START_POS:
            continue

        distance = (
            abs(
                position[0] -
                START_POS[0]
            )
            +
            abs(
                position[1] -
                START_POS[1]
            )
        )

        if distance >= 10:
            candidates.append(
                position
            )

    if not candidates:
        candidates = list(
            reachable
        )

    return max(
        candidates,
        key=lambda p:
        abs(
            p[0] -
            START_POS[0]
        )
        +
        abs(
            p[1] -
            START_POS[1]
        )
    )

# ============================================================
# OBSTACLES
# ============================================================

OBSTACLE_TYPES = (
    "pit",
    "water",
    "sand"
)


def generate_obstacles(
    maze,
    exit_pos,
    count
):

    obstacles = {}

    rows = len(maze)
    cols = len(maze[0])

    candidates = []

    for y in range(
        1,
        rows - 1
    ):

        for x in range(
            1,
            cols - 1
        ):

            position = (
                x,
                y
            )

            if maze[y][x] != 0:
                continue

            if position == START_POS:
                continue

            if position == exit_pos:
                continue

            # Keep the opening area clear.
            if (
                abs(
                    x -
                    START_POS[0]
                )
                +
                abs(
                    y -
                    START_POS[1]
                )
                <= 2
            ):
                continue

            candidates.append(
                position
            )

    random.shuffle(
        candidates
    )

    for position in candidates:

        if len(obstacles) >= count:
            break

        x, y = position

        neighbours = 0

        for dx, dy in DIRECTIONS:

            nx = x + dx
            ny = y + dy

            if (
                0 <= nx < cols
                and
                0 <= ny < rows
                and
                maze[ny][nx] == 0
            ):

                neighbours += 1

        # An obstacle needs at least two available
        # adjacent squares so that it can be jumped
        # over from a sensible direction.
        if neighbours < 2:
            continue

        too_close = False

        for other in obstacles:

            if (
                abs(
                    other[0] -
                    x
                )
                +
                abs(
                    other[1] -
                    y
                )
                <= 1
            ):

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

def generate_level(
    difficulty
):

    if difficulty == "Easy":

        size = 17
        obstacle_count = 4

    elif difficulty == "Medium":

        size = 21
        obstacle_count = 7

    elif difficulty == "Hard":

        size = 25
        obstacle_count = 10

    else:

        size = 29
        obstacle_count = 14

    while True:

        maze = generate_maze(
            size,
            size
        )

        exit_pos = choose_exit(
            maze
        )

        path = shortest_path(
            maze,
            START_POS,
            exit_pos
        )

        if not path:
            continue

        obstacles = generate_obstacles(
            maze,
            exit_pos,
            obstacle_count
        )

        return (
            maze,
            obstacles,
            exit_pos
        )

# ============================================================
# 3D PROJECTION
# ============================================================

def iso_project(
    grid_x,
    grid_y,
    camera_x,
    camera_y
):

    """
    Convert maze coordinates to the actual floor plane.

    IMPORTANT:
    This is the coordinate system used for BOTH the floor
    and the bottom of every wall.

    The walls therefore rise FROM the floor rather than
    appearing underneath it.
    """

    dx = grid_x - camera_x
    dy = grid_y - camera_y

    screen_x = (
        WIDTH // 2
        +
        (dx - dy) *
        TILE_WIDTH / 2
    )

    screen_y = (
        HEIGHT // 2
        - 35
        +
        (dx + dy) *
        TILE_DEPTH / 2
    )

    return (
        screen_x,
        screen_y
    )

# ============================================================
# FLOOR
# ============================================================

def floor_points(
    sx,
    sy
):

    return [
        (
            sx,
            sy - TILE_DEPTH / 2
        ),
        (
            sx + TILE_WIDTH / 2,
            sy
        ),
        (
            sx,
            sy + TILE_DEPTH / 2
        ),
        (
            sx - TILE_WIDTH / 2,
            sy
        )
    ]


def draw_floor(
    sx,
    sy,
    colour=FLOOR
):

    points = floor_points(
        sx,
        sy
    )

    pygame.draw.polygon(
        screen,
        colour,
        points
    )

    pygame.draw.polygon(
        screen,
        FLOOR_DARK,
        points,
        1
    )

# ============================================================
# 3D WALL BLOCK
# ============================================================

def draw_wall_block(
    sx,
    sy
):

    """
    A proper solid 3D block.

    The top sits directly on the floor plane.
    The two visible sides descend from that top face.

    There is deliberately NO separate floating block.
    """

    top = floor_points(
        sx,
        sy
    )

    # Left visible side
    left = [
        top[3],
        top[2],
        (
            top[2][0],
            top[2][1] + WALL_HEIGHT
        ),
        (
            top[3][0],
            top[3][1] + WALL_HEIGHT
        )
    ]

    # Right visible side
    right = [
        top[2],
        top[1],
        (
            top[1][0],
            top[1][1] + WALL_HEIGHT
        ),
        (
            top[2][0],
            top[2][1] + WALL_HEIGHT
        )
    ]

    # Draw sides first
    pygame.draw.polygon(
        screen,
        WALL_LEFT,
        left
    )

    pygame.draw.polygon(
        screen,
        WALL_RIGHT,
        right
    )

    # Then top
    pygame.draw.polygon(
        screen,
        WALL_TOP,
        top
    )

    # Crisp outlines
    pygame.draw.polygon(
        screen,
        (25, 29, 36),
        left,
        1
    )

    pygame.draw.polygon(
        screen,
        (25, 29, 36),
        right,
        1
    )

    pygame.draw.polygon(
        screen,
        (30, 34, 41),
        top,
        1
    )

# ============================================================
# OBSTACLE GRAPHICS
# ============================================================

def draw_water(
    sx,
    sy,
    animation_time
):

    draw_floor(
        sx,
        sy,
        WATER
    )

    wave = math.sin(
        animation_time * 3
    ) * 3

    pygame.draw.arc(
        screen,
        (100, 180, 225),
        (
            int(sx - 25 + wave),
            int(sy - 9),
            50,
            18
        ),
        0,
        math.pi,
        2
    )

    pygame.draw.arc(
        screen,
        (75, 150, 205),
        (
            int(sx - 17 - wave),
            int(sy - 2),
            34,
            12
        ),
        0,
        math.pi,
        2
    )


def draw_sand(
    sx,
    sy,
    animation_time
):

    draw_floor(
        sx,
        sy,
        SAND
    )

    for i in range(7):

        angle = (
            i * math.pi * 2 / 7
        )

        px = sx + math.cos(angle) * 22
        py = sy + math.sin(angle) * 9

        pygame.draw.circle(
            screen,
            (150, 120, 65),
            (
                int(px),
                int(py)
            ),
            2
        )


def draw_pit(
    sx,
    sy
):

    draw_floor(
        sx,
        sy,
        (39, 42, 48)
    )

    pygame.draw.ellipse(
        screen,
        (8, 9, 12),
        (
            int(sx - 25),
            int(sy - 11),
            50,
            22
        )
    )

    pygame.draw.ellipse(
        screen,
        (17, 18, 23),
        (
            int(sx - 17),
            int(sy - 7),
            34,
            14
        )
    )


def draw_obstacle(
    sx,
    sy,
    obstacle,
    animation_time
):

    if obstacle == "water":

        draw_water(
            sx,
            sy,
            animation_time
        )

    elif obstacle == "sand":

        draw_sand(
            sx,
            sy,
            animation_time
        )

    else:

        draw_pit(
            sx,
            sy
        )

# ============================================================
# EXIT
# ============================================================

def draw_exit(
    sx,
    sy,
    animation_time
):

    pulse = (
        math.sin(
            animation_time * 4
        )
        + 1
    ) / 2

    draw_floor(
        sx,
        sy,
        (
            30,
            int(
                110 +
                pulse * 35
            ),
            50
        )
    )

    pygame.draw.ellipse(
        screen,
        (
            80,
            225,
            100
        ),
        (
            int(sx - 19),
            int(sy - 9),
            38,
            18
        ),
        3
    )

# ============================================================
# PLAYER
# ============================================================

def draw_player(
    sx,
    sy,
    moving,
    jumping,
    jump_height,
    direction,
    animation_time
):

    # --------------------------------------------------------
    # Shadow
    # --------------------------------------------------------

    shadow_scale = max(
        0.25,
        1.0 -
        jump_height / 80
    )

    pygame.draw.ellipse(
        screen,
        (15, 17, 20),
        (
            int(
                sx -
                15 *
                shadow_scale
            ),
            int(
                sy -
                6 *
                shadow_scale
            ),
            int(
                30 *
                shadow_scale
            ),
            int(
                12 *
                shadow_scale
            )
        )
    )

    # --------------------------------------------------------
    # Walking animation
    # --------------------------------------------------------

    if moving:

        walk_phase = math.sin(
            animation_time * 20
        )

    else:

        walk_phase = 0

    leg_1 = walk_phase * 5
    leg_2 = -walk_phase * 5

    base_y = sy - jump_height

    # --------------------------------------------------------
    # Legs
    # --------------------------------------------------------

    pygame.draw.line(
        screen,
        DARK_GREEN,
        (
            int(sx - 4),
            int(base_y - 3)
        ),
        (
            int(sx - 5 + leg_1),
            int(base_y + 13)
        ),
        4
    )

    pygame.draw.line(
        screen,
        DARK_GREEN,
        (
            int(sx + 4),
            int(base_y - 3)
        ),
        (
            int(sx + 5 + leg_2),
            int(base_y + 13)
        ),
        4
    )

    # --------------------------------------------------------
    # Body
    # --------------------------------------------------------

    body = pygame.Rect(
        int(sx - 8),
        int(base_y - 36),
        16,
        34
    )

    pygame.draw.rect(
        screen,
        GREEN,
        body,
        border_radius=5
    )

    pygame.draw.line(
        screen,
        LIGHT_GREEN,
        (
            body.left + 3,
            body.top + 5
        ),
        (
            body.left + 3,
            body.bottom - 6
        ),
        2
    )

    # --------------------------------------------------------
    # Head
    # --------------------------------------------------------

    head_y = base_y - 45

    pygame.draw.circle(
        screen,
        GREEN,
        (
            int(sx),
            int(head_y)
        ),
        10
    )

    # --------------------------------------------------------
    # Eyes
    # --------------------------------------------------------

    dx, dy = direction

    eye_x = sx + dx * 4
    eye_y = head_y + dy * 3

    pygame.draw.circle(
        screen,
        BLACK,
        (
            int(eye_x),
            int(eye_y)
        ),
        2
    )

# ============================================================
# MAZE RENDERER
# ============================================================

def render_maze(
    maze,
    obstacles,
    exit_pos,
    visual_x,
    visual_y,
    player_x,
    player_y,
    moving,
    jumping,
    jump_height,
    direction,
    animation_time,
    show_map
):

    screen.fill(
        BACKGROUND
    )

    rows = len(maze)
    cols = len(maze[0])

    # --------------------------------------------------------
    # Camera
    # --------------------------------------------------------

    camera_x = visual_x
    camera_y = visual_y

    tiles = []

    min_x = max(
        0,
        int(
            visual_x -
            DRAW_DISTANCE
        )
    )

    max_x = min(
        cols - 1,
        int(
            visual_x +
            DRAW_DISTANCE
        )
    )

    min_y = max(
        0,
        int(
            visual_y -
            DRAW_DISTANCE
        )
    )

    max_y = min(
        rows - 1,
        int(
            visual_y +
            DRAW_DISTANCE
        )
    )

    # --------------------------------------------------------
    # Collect visible tiles
    # --------------------------------------------------------

    for y in range(
        min_y,
        max_y + 1
    ):

        for x in range(
            min_x,
            max_x + 1
        ):

            distance = (
                abs(
                    x -
                    visual_x
                )
                +
                abs(
                    y -
                    visual_y
                )
            )

            if distance > DRAW_DISTANCE * 1.7:
                continue

            sx, sy = iso_project(
                x,
                y,
                camera_x,
                camera_y
            )

            tiles.append(
                (
                    x + y,
                    x,
                    y,
                    sx,
                    sy
                )
            )

    # --------------------------------------------------------
    # Back to front
    # --------------------------------------------------------

    tiles.sort(
        key=lambda item:
        item[0]
    )

    for _, x, y, sx, sy in tiles:

        # ----------------------------------------------------
        # FLOOR
        # ----------------------------------------------------

        if maze[y][x] == 0:

            if (
                x,
                y
            ) == exit_pos:

                draw_exit(
                    sx,
                    sy,
                    animation_time
                )

            elif (
                x,
                y
            ) in obstacles:

                draw_obstacle(
                    sx,
                    sy,
                    obstacles[
                        (x, y)
                    ],
                    animation_time
                )

            else:

                draw_floor(
                    sx,
                    sy
                )

        # ----------------------------------------------------
        # WALL
        # ----------------------------------------------------

        else:

            # The floor tile exists underneath the wall,
            # then the wall rises directly from that plane.
            draw_wall_block(
                sx,
                sy
            )

    # --------------------------------------------------------
    # PLAYER
    # --------------------------------------------------------

    player_sx, player_sy = iso_project(
        visual_x,
        visual_y,
        camera_x,
        camera_y
    )

    draw_player(
        player_sx,
        player_sy,
        moving,
        jumping,
        jump_height,
        direction,
        animation_time
    )

    # --------------------------------------------------------
    # HUD
    # --------------------------------------------------------

    pygame.draw.rect(
        screen,
        (8, 12, 18),
        (
            0,
            0,
            WIDTH,
            66
        )
    )

    pygame.draw.line(
        screen,
        (70, 82, 98),
        (
            0,
            65
        ),
        (
            WIDTH,
            65
        )
    )

    if show_map:

        draw_minimap(
            maze,
            obstacles,
            exit_pos,
            player_x,
            player_y
        )

# ============================================================
# MINIMAP
# ============================================================

def draw_minimap(
    maze,
    obstacles,
    exit_pos,
    player_x,
    player_y
):

    rect = pygame.Rect(
        20,
        85,
        270,
        270
    )

    draw_panel(
        rect,
        235
    )

    rows = len(maze)
    cols = len(maze[0])

    cell = min(
        245 / cols,
        245 / rows
    )

    ox = rect.x + 12
    oy = rect.y + 12

    for y in range(rows):

        for x in range(cols):

            if maze[y][x] == 1:

                colour = (
                    35,
                    41,
                    49
                )

            else:

                colour = (
                    120,
                    125,
                    135
                )

            pygame.draw.rect(
                screen,
                colour,
                (
                    int(
                        ox +
                        x * cell
                    ),
                    int(
                        oy +
                        y * cell
                    ),
                    max(
                        1,
                        int(cell)
                    ),
                    max(
                        1,
                        int(cell)
                    )
                )
            )

    ex, ey = exit_pos

    pygame.draw.rect(
        screen,
        GREEN,
        (
            int(
                ox +
                ex * cell
            ),
            int(
                oy +
                ey * cell
            ),
            max(
                2,
                int(cell)
            ),
            max(
                2,
                int(cell)
            )
        )
    )

    pygame.draw.rect(
        screen,
        RED,
        (
            int(
                ox +
                player_x * cell
            ),
            int(
                oy +
                player_y * cell
            ),
            max(
                2,
                int(cell)
            ),
            max(
                2,
                int(cell)
            )
        )
    )

# ============================================================
# TITLE BACKGROUND
# ============================================================

def draw_title_background(
    animation_time
):

    screen.fill(
        (12, 22, 31)
    )

    # Brighter animated maze-like background.
    spacing = 90

    offset = (
        animation_time * 18
    ) % spacing

    for x in range(
        -spacing,
        WIDTH + spacing,
        spacing
    ):

        pygame.draw.line(
            screen,
            (22, 48, 59),
            (
                int(x + offset),
                0
            ),
            (
                int(
                    x +
                    offset -
                    250
                ),
                HEIGHT
            ),
            2
        )

    for y in range(
        -spacing,
        HEIGHT + spacing,
        spacing
    ):

        pygame.draw.line(
            screen,
            (18, 43, 54),
            (
                0,
                int(y + offset)
            ),
            (
                WIDTH,
                int(
                    y +
                    offset -
                    130
                )
            ),
            2
        )

    # Animated small maze segments.
    for i in range(25):

        x = (
            i * 137
            +
            int(
                animation_time * 12
            )
        ) % WIDTH

        y = (
            i * 83
            +
            int(
                animation_time * 7
            )
        ) % HEIGHT

        pygame.draw.line(
            screen,
            (30, 70, 78),
            (
                x,
                y
            ),
            (
                x + 38,
                y
            ),
            3
        )

        pygame.draw.line(
            screen,
            (30, 70, 78),
            (
                x + 38,
                y
            ),
            (
                x + 38,
                y + 38
            ),
            3
        )

# ============================================================
# TITLE SCREEN
# ============================================================

def title_screen():

    difficulties = [
        "Easy",
        "Medium",
        "Hard",
        "Extreme"
    ]

    difficulty_index = 1

    while True:

        animation_time = time.time()

        draw_title_background(
            animation_time
        )

        # ----------------------------------------------------
        # Title
        # ----------------------------------------------------

        pulse = (
            math.sin(
                animation_time * 1.5
            )
            + 1
        ) / 2

        title_colour = (
            int(
                65 +
                pulse * 45
            ),
            int(
                205 +
                pulse * 40
            ),
            int(
                120 +
                pulse * 80
            )
        )

        draw_text(
            "PYTHON MAZE",
            FONT_TITLE,
            title_colour,
            WIDTH // 2,
            150,
            True
        )

        draw_text(
            "(c) 2026 Stuart MacIntosh   V "
            + VERSION,
            FONT_SMALL,
            LIGHT_GREY,
            WIDTH // 2,
            220,
            True
        )

        # ----------------------------------------------------
        # Menu
        # ----------------------------------------------------

        options = [
            "F1   START GAME",
            "F2   INSTRUCTIONS",
            "F3   DIFFICULTY",
            "F4   HIGH SCORES",
            "F10  EXIT"
        ]

        buttons = []

        start_y = 310

        mouse_pos = pygame.mouse.get_pos()

        for i, option in enumerate(
            options
        ):

            rect = pygame.Rect(
                WIDTH // 2 - 275,
                start_y +
                i * 72,
                550,
                56
            )

            buttons.append(
                rect
            )

            hover = rect.collidepoint(
                mouse_pos
            )

            if hover:

                colour = (
                    38,
                    76,
                    87
                )

            else:

                colour = (
                    22,
                    36,
                    45
                )

            pygame.draw.rect(
                screen,
                colour,
                rect,
                border_radius=8
            )

            pygame.draw.rect(
                screen,
                (65, 110, 120),
                rect,
                2,
                border_radius=8
            )

            draw_text(
                option,
                FONT,
                WHITE,
                rect.centerx,
                rect.centery,
                True
            )

        draw_text(
            "Starting difficulty: "
            +
            difficulties[
                difficulty_index
            ],
            FONT_SMALL,
            YELLOW,
            WIDTH // 2,
            HEIGHT - 70,
            True
        )

        draw_text(
            "Use the function keys or click an option",
            FONT_SMALL,
            LIGHT_GREY,
            WIDTH // 2,
            HEIGHT - 35,
            True
        )

        pygame.display.flip()

        for event in pygame.event.get():

            if event.type == pygame.QUIT:

                pygame.quit()
                sys.exit()

            if event.type == pygame.KEYDOWN:

                if event.key == pygame.K_F1:

                    if START_SOUND:
                        START_SOUND.play()

                    return difficulties[
                        difficulty_index
                    ]

                elif event.key == pygame.K_F2:

                    instructions_screen()

                elif event.key == pygame.K_F3:

                    difficulty_index = (
                        difficulty_index + 1
                    ) % len(difficulties)

                elif event.key == pygame.K_F4:

                    high_scores_screen()

                elif event.key == pygame.K_F10:

                    pygame.quit()
                    sys.exit()

            elif event.type == pygame.MOUSEBUTTONDOWN:

                if event.button != 1:
                    continue

                for i, rect in enumerate(
                    buttons
                ):

                    if rect.collidepoint(
                        event.pos
                    ):

                        if i == 0:

                            if START_SOUND:
                                START_SOUND.play()

                            return difficulties[
                                difficulty_index
                            ]

                        elif i == 1:

                            instructions_screen()

                        elif i == 2:

                            difficulty_index = (
                                difficulty_index + 1
                            ) % len(difficulties)

                        elif i == 3:

                            high_scores_screen()

                        elif i == 4:

                            pygame.quit()
                            sys.exit()

# ============================================================
# INSTRUCTIONS
# ============================================================

def instructions_screen():

    while True:

        screen.fill(
            (9, 15, 22)
        )

        draw_text(
            "PYTHON MAZE",
            FONT_LARGE,
            GREEN,
            WIDTH // 2,
            80,
            True
        )

        draw_text(
            "INSTRUCTIONS",
            FONT_MEDIUM,
            WHITE,
            WIDTH // 2,
            145,
            True
        )

        panel = pygame.Rect(
            WIDTH // 2 - 500,
            195,
            1000,
            535
        )

        draw_panel(
            panel,
            240
        )

        instructions = [
            (
                "ARROW KEYS",
                "Walk one square in that direction"
            ),
            (
                "ARROW + SPACE",
                "Jump over the adjacent square and land on the second"
            ),
            (
                "SPACE",
                "Jump using your current direction"
            ),
            (
                "H",
                "Show / hide the top-down map"
            ),
            (
                "ESC",
                "Return to the title screen"
            ),
            (
                "",
                ""
            ),
            (
                "OBSTACLES",
                "Pits, water and sand are dangerous"
            ),
            (
                "JUMPING",
                "Jump over an obstacle to reach the square beyond it"
            ),
            (
                "LIVES",
                "You have three lives"
            ),
            (
                "DEATH",
                "Dying returns you to the start of the level"
            ),
            (
                "",
                ""
            ),
            (
                "TIP",
                "The map is hidden by default"
            ),
            (
                "TIP",
                "The 3D walls show the actual maze structure"
            )
        ]

        y = panel.y + 25

        for key, description in instructions:

            if not key:

                y += 12
                continue

            draw_text(
                key,
                FONT,
                YELLOW,
                panel.x + 35,
                y
            )

            draw_text(
                description,
                FONT_SMALL,
                LIGHT_GREY,
                panel.x + 250,
                y + 7
            )

            y += 37

        draw_text(
            "Press ESC to return",
            FONT,
            GREY,
            WIDTH // 2,
            HEIGHT - 35,
            True
        )

        pygame.display.flip()

        for event in pygame.event.get():

            if event.type == pygame.QUIT:

                pygame.quit()
                sys.exit()

            if event.type == pygame.KEYDOWN:

                if event.key in (
                    pygame.K_ESCAPE,
                    pygame.K_F2
                ):

                    return

# ============================================================
# HIGH SCORES
# ============================================================

def high_scores_screen():

    while True:

        screen.fill(
            (8, 12, 18)
        )

        draw_text(
            "HIGH SCORES",
            FONT_LARGE,
            YELLOW,
            WIDTH // 2,
            85,
            True
        )

        panel = pygame.Rect(
            WIDTH // 2 - 500,
            165,
            1000,
            520
        )

        draw_panel(
            panel,
            240
        )

        headers = [
            "POS",
            "NAME",
            "SCORE",
            "LEVEL",
            "MOVES",
            "TIME"
        ]

        header_x = [
            40,
            120,
            510,
            650,
            770,
            895
        ]

        for header, x in zip(
            headers,
            header_x
        ):

            draw_text(
                header,
                FONT_SMALL,
                YELLOW,
                panel.x + x,
                panel.y + 22
            )

        scores = load_scores()

        if not scores:

            draw_text(
                "No high scores yet",
                FONT,
                GREY,
                panel.centerx,
                panel.centery,
                True
            )

        else:

            y = panel.y + 70

            for index, score in enumerate(
                scores[:10]
            ):

                draw_text(
                    str(index + 1),
                    FONT_SMALL,
                    WHITE,
                    panel.x + 45,
                    y
                )

                draw_text(
                    score.get(
                        "name",
                        "PLAYER"
                    ),
                    FONT_SMALL,
                    WHITE,
                    panel.x + 120,
                    y
                )

                draw_text(
                    str(
                        score.get(
                            "score",
                            0
                        )
                    ),
                    FONT_SMALL,
                    WHITE,
                    panel.x + 510,
                    y
                )

                draw_text(
                    str(
                        score.get(
                            "level",
                            0
                        )
                    ),
                    FONT_SMALL,
                    WHITE,
                    panel.x + 650,
                    y
                )

                draw_text(
                    str(
                        score.get(
                            "moves",
                            0
                        )
                    ),
                    FONT_SMALL,
                    WHITE,
                    panel.x + 770,
                    y
                )

                draw_text(
                    f"{score.get('time', 0):.1f}s",
                    FONT_SMALL,
                    WHITE,
                    panel.x + 895,
                    y
                )

                y += 38

        clear_rect = pygame.Rect(
            WIDTH // 2 - 230,
            HEIGHT - 90,
            200,
            50
        )

        back_rect = pygame.Rect(
            WIDTH // 2 + 30,
            HEIGHT - 90,
            200,
            50
        )

        for rect, label in (
            (
                clear_rect,
                "CLEAR SCORES"
            ),
            (
                back_rect,
                "BACK"
            )
        ):

            hover = rect.collidepoint(
                pygame.mouse.get_pos()
            )

            colour = (
                45,
                60,
                72
            ) if hover else (
                27,
                35,
                45
            )

            pygame.draw.rect(
                screen,
                colour,
                rect,
                border_radius=7
            )

            pygame.draw.rect(
                screen,
                (80, 95, 110),
                rect,
                2,
                border_radius=7
            )

            draw_text(
                label,
                FONT_SMALL,
                WHITE,
                rect.centerx,
                rect.centery,
                True
            )

        pygame.display.flip()

        for event in pygame.event.get():

            if event.type == pygame.QUIT:

                pygame.quit()
                sys.exit()

            if event.type == pygame.KEYDOWN:

                if event.key in (
                    pygame.K_ESCAPE,
                    pygame.K_F4
                ):

                    return

                if event.key == pygame.K_c:

                    clear_scores()

            elif event.type == pygame.MOUSEBUTTONDOWN:

                if event.button != 1:
                    continue

                if clear_rect.collidepoint(
                    event.pos
                ):

                    clear_scores()

                elif back_rect.collidepoint(
                    event.pos
                ):

                    return

# ============================================================
# NAME ENTRY
# ============================================================

def name_entry():

    name = ""

    while True:

        screen.fill(
            (8, 12, 18)
        )

        draw_text(
            "NEW HIGH SCORE",
            FONT_LARGE,
            YELLOW,
            WIDTH // 2,
            180,
            True
        )

        draw_text(
            "Enter your name",
            FONT,
            WHITE,
            WIDTH // 2,
            270,
            True
        )

        box = pygame.Rect(
            WIDTH // 2 - 300,
            325,
            600,
            70
        )

        pygame.draw.rect(
            screen,
            (24, 33, 43),
            box,
            border_radius=8
        )

        pygame.draw.rect(
            screen,
            GREEN,
            box,
            2,
            border_radius=8
        )

        cursor = "_"

        draw_text(
            name + cursor,
            FONT_MEDIUM,
            WHITE,
            box.centerx,
            box.centery,
            True
        )

        draw_text(
            "Press ENTER to save",
            FONT_SMALL,
            GREY,
            WIDTH // 2,
            450,
            True
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

                elif event.key == pygame.K_BACKSPACE:

                    name = name[:-1]

                elif (
                    len(name) < 12
                    and
                    event.unicode.isprintable()
                ):

                    name += event.unicode.upper()

# ============================================================
# GAME OVER
# ============================================================

def game_over_screen():

    while True:

        screen.fill(
            (22, 7, 10)
        )

        draw_text(
            "GAME OVER",
            FONT_TITLE,
            RED,
            WIDTH // 2,
            230,
            True
        )

        draw_text(
            "All three lives have been lost.",
            FONT,
            WHITE,
            WIDTH // 2,
            345,
            True
        )

        draw_text(
            "Press ENTER to return to the title screen",
            FONT_SMALL,
            LIGHT_GREY,
            WIDTH // 2,
            430,
            True
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
# DEATH ANIMATION
# ============================================================

def death_animation(
    maze,
    obstacles,
    exit_pos,
    player_x,
    player_y,
    direction,
    obstacle_type
):

    duration = 0.75

    start = time.time()

    while True:

        elapsed = (
            time.time() -
            start
        )

        if elapsed >= duration:
            break

        progress = (
            elapsed /
            duration
        )

        render_maze(
            maze,
            obstacles,
            exit_pos,
            player_x,
            player_y,
            player_x,
            player_y,
            False,
            False,
            0,
            direction,
            time.time(),
            False
        )

        sx, sy = iso_project(
            player_x,
            player_y,
            player_x,
            player_y
        )

        # Different sinking behaviours.
        if obstacle_type == "pit":

            sink = progress * 48

        elif obstacle_type == "water":

            sink = progress * 30

        else:

            sink = progress * 38

        scale = (
            1 -
            progress * 0.65
        )

        pygame.draw.ellipse(
            screen,
            GREEN,
            (
                int(
                    sx -
                    9 * scale
                ),
                int(
                    sy -
                    45 * scale +
                    sink
                ),
                int(
                    18 * scale
                ),
                int(
                    40 * scale
                )
            )
        )

        pygame.display.flip()

        clock.tick(60)

    if DEATH_SOUND:
        DEATH_SOUND.play()

# ============================================================
# JUMP CALCULATION
# ============================================================

def jump_height(
    progress
):

    """
    Smooth jump arc.

    0.0 = takeoff
    0.5 = maximum height
    1.0 = landing
    """

    return (
        math.sin(
            math.pi *
            progress
        )
        *
        70
    )

# ============================================================
# FIND DIRECTION
# ============================================================

def keyboard_direction():

    keys = pygame.key.get_pressed()

    if keys[pygame.K_UP]:
        return (0, -1)

    if keys[pygame.K_DOWN]:
        return (0, 1)

    if keys[pygame.K_LEFT]:
        return (-1, 0)

    if keys[pygame.K_RIGHT]:
        return (1, 0)

    return None

# ============================================================
# VALID CELL
# ============================================================

def valid_cell(
    maze,
    x,
    y
):

    return (
        0 <= y < len(maze)
        and
        0 <= x < len(maze[0])
        and
        maze[y][x] == 0
    )

# ============================================================
# PLAY GAME
# ============================================================

def play_game(
    difficulty
):

    maze, obstacles, exit_pos = generate_level(
        difficulty
    )

    player_x = START_POS[0]
    player_y = START_POS[1]

    visual_x = float(
        player_x
    )

    visual_y = float(
        player_y
    )

    lives = MAX_LIVES

    moves = 0

    level = 1

    total_score = 0

    game_start = time.time()

    show_map = False

    moving = False
    jumping = False

    direction = (0, 1)

    movement_start_x = player_x
    movement_start_y = player_y

    movement_target_x = player_x
    movement_target_y = player_y

    movement_progress = 0.0

    jump_height_value = 0

    # --------------------------------------------------------
    # MAIN GAME
    # --------------------------------------------------------

    while True:

        level_start = time.time()

        level_running = True

        while level_running:

            dt = (
                clock.tick(60)
                /
                1000.0
            )

            animation_time = time.time()

            # ------------------------------------------------
            # EVENTS
            # ------------------------------------------------

            for event in pygame.event.get():

                if event.type == pygame.QUIT:

                    pygame.quit()
                    sys.exit()

                if event.type == pygame.KEYDOWN:

                    if event.key == pygame.K_ESCAPE:

                        return total_score

                    if event.key == pygame.K_h:

                        show_map = not show_map

            # ------------------------------------------------
            # MOVEMENT INPUT
            # ------------------------------------------------

            if not moving:

                keys = pygame.key.get_pressed()

                requested_direction = keyboard_direction()

                if requested_direction is not None:

                    dx, dy = requested_direction

                    direction = requested_direction

                    # ------------------------------------------------
                    # JUMP HAS PRIORITY
                    # ------------------------------------------------

                    if keys[pygame.K_SPACE]:

                        # Jump TWO squares.
                        #
                        # Square 1 is jumped over.
                        # Square 2 is the landing square.

                        landing_x = (
                            player_x +
                            dx * 2
                        )

                        landing_y = (
                            player_y +
                            dy * 2
                        )

                        middle_x = (
                            player_x +
                            dx
                        )

                        middle_y = (
                            player_y +
                            dy
                        )

                        if (
                            valid_cell(
                                maze,
                                middle_x,
                                middle_y
                            )
                            and
                            valid_cell(
                                maze,
                                landing_x,
                                landing_y
                            )
                        ):

                            movement_start_x = (
                                player_x
                            )

                            movement_start_y = (
                                player_y
                            )

                            movement_target_x = (
                                landing_x
                            )

                            movement_target_y = (
                                landing_y
                            )

                            movement_progress = 0

                            moving = True

                            jumping = True

                            jump_height_value = 0

                            moves += 1

                            if JUMP_SOUND:
                                JUMP_SOUND.play()

                    else:

                        # Normal one-square walking.

                        nx = (
                            player_x +
                            dx
                        )

                        ny = (
                            player_y +
                            dy
                        )

                        if valid_cell(
                            maze,
                            nx,
                            ny
                        ):

                            movement_start_x = (
                                player_x
                            )

                            movement_start_y = (
                                player_y
                            )

                            movement_target_x = nx
                            movement_target_y = ny

                            movement_progress = 0

                            moving = True

                            jumping = False

                            jump_height_value = 0

                            moves += 1

                            if MOVE_SOUND:
                                MOVE_SOUND.play()

            # ------------------------------------------------
            # ANIMATE MOVEMENT
            # ------------------------------------------------

            if moving:

                duration = (
                    JUMP_TIME
                    if jumping
                    else WALK_TIME
                )

                movement_progress += (
                    dt /
                    duration
                )

                progress = min(
                    movement_progress,
                    1.0
                )

                # Smoothstep.
                smooth = (
                    progress *
                    progress *
                    (
                        3 -
                        2 *
                        progress
                    )
                )

                visual_x = (
                    movement_start_x
                    +
                    (
                        movement_target_x
                        -
                        movement_start_x
                    )
                    *
                    smooth
                )

                visual_y = (
                    movement_start_y
                    +
                    (
                        movement_target_y
                        -
                        movement_start_y
                    )
                    *
                    smooth
                )

                if jumping:

                    jump_height_value = jump_height(
                        progress
                    )

                else:

                    jump_height_value = 0

                # ------------------------------------------------
                # MOVEMENT COMPLETE
                # ------------------------------------------------

                if progress >= 1:

                    player_x = (
                        movement_target_x
                    )

                    player_y = (
                        movement_target_y
                    )

                    visual_x = float(
                        player_x
                    )

                    visual_y = float(
                        player_y
                    )

                    was_jumping = jumping

                    moving = False
                    jumping = False

                    jump_height_value = 0

                    if was_jumping and LAND_SOUND:

                        LAND_SOUND.play()

                    # ------------------------------------------------
                    # OBSTACLE
                    # ------------------------------------------------

                    landed_obstacle = (
                        player_x,
                        player_y
                    ) in obstacles

                    if landed_obstacle:

                        obstacle_type = obstacles[
                            (
                                player_x,
                                player_y
                            )
                        ]

                        death_animation(
                            maze,
                            obstacles,
                            exit_pos,
                            player_x,
                            player_y,
                            direction,
                            obstacle_type
                        )

                        lives -= 1

                        if lives <= 0:

                            game_over_screen()

                            return total_score

                        # --------------------------------------------
                        # RESET TO LEVEL START
                        # --------------------------------------------

                        player_x = START_POS[0]
                        player_y = START_POS[1]

                        visual_x = float(
                            player_x
                        )

                        visual_y = float(
                            player_y
                        )

                        movement_start_x = player_x
                        movement_start_y = player_y

                        movement_target_x = player_x
                        movement_target_y = player_y

                        movement_progress = 0

                        moving = False
                        jumping = False

                        jump_height_value = 0

                        continue

                    # ------------------------------------------------
                    # EXIT
                    # ------------------------------------------------

                    if (
                        player_x,
                        player_y
                    ) == exit_pos:

                        level_running = False

            # ------------------------------------------------
            # RENDER
            # ------------------------------------------------

            render_maze(
                maze,
                obstacles,
                exit_pos,
                visual_x,
                visual_y,
                player_x,
                player_y,
                moving,
                jumping,
                jump_height_value,
                direction,
                animation_time,
                show_map
            )

            # ------------------------------------------------
            # HUD
            # ------------------------------------------------

            elapsed = (
                time.time()
                -
                game_start
            )

            draw_text(
                f"LEVEL {level}",
                FONT,
                WHITE,
                22,
                16
            )

            draw_text(
                f"LIVES {lives}",
                FONT,
                GREEN,
                185,
                16
            )

            draw_text(
                f"MOVES {moves}",
                FONT_SMALL,
                LIGHT_GREY,
                335,
                22
            )

            draw_text(
                f"TIME {elapsed:.1f}s",
                FONT_SMALL,
                LIGHT_GREY,
                500,
                22
            )

            draw_text(
                "H = MAP",
                FONT_SMALL,
                GREY,
                WIDTH - 130,
                22
            )

            pygame.display.flip()

        # ====================================================
        # LEVEL COMPLETE
        # ====================================================

        level_time = (
            time.time()
            -
            level_start
        )

        level_score = max(
            100,
            int(
                10000
                +
                level * 1500
                -
                moves * 20
                -
                level_time * 25
            )
        )

        total_score += level_score

        if WIN_SOUND:
            WIN_SOUND.play()

        screen.fill(
            (8, 18, 12)
        )

        draw_text(
            "LEVEL COMPLETE!",
            FONT_TITLE,
            GREEN,
            WIDTH // 2,
            220,
            True
        )

        draw_text(
            f"Level {level}",
            FONT_MEDIUM,
            WHITE,
            WIDTH // 2,
            330,
            True
        )

        draw_text(
            f"Time: {level_time:.1f} seconds",
            FONT,
            LIGHT_GREY,
            WIDTH // 2,
            395,
            True
        )

        draw_text(
            f"Moves: {moves}",
            FONT,
            LIGHT_GREY,
            WIDTH // 2,
            440,
            True
        )

        draw_text(
            f"Level score: {level_score}",
            FONT,
            YELLOW,
            WIDTH // 2,
            485,
            True
        )

        draw_text(
            f"Total score: {total_score}",
            FONT,
            YELLOW,
            WIDTH // 2,
            530,
            True
        )

        draw_text(
            "Press ENTER for the next level",
            FONT_SMALL,
            GREY,
            WIDTH // 2,
            610,
            True
        )

        pygame.display.flip()

        waiting = True

        while waiting:

            clock.tick(30)

            for event in pygame.event.get():

                if event.type == pygame.QUIT:

                    pygame.quit()
                    sys.exit()

                if event.type == pygame.KEYDOWN:

                    if event.key == pygame.K_ESCAPE:

                        return total_score

                    if event.key == pygame.K_RETURN:

                        waiting = False

        # ----------------------------------------------------
        # Next level
        # ----------------------------------------------------

        level += 1

        maze, obstacles, exit_pos = generate_level(
            difficulty
        )

        player_x = START_POS[0]
        player_y = START_POS[1]

        visual_x = float(
            player_x
        )

        visual_y = float(
            player_y
        )

        moving = False
        jumping = False

        jump_height_value = 0

        direction = (0, 1)

        movement_progress = 0

        # Gradually increase difficulty.
        if level > 3:

            if difficulty == "Easy":

                difficulty = "Medium"

            elif difficulty == "Medium":

                difficulty = "Hard"

            elif difficulty == "Hard":

                difficulty = "Extreme"

# ============================================================
# MAIN
# ============================================================

def main():

    while True:

        difficulty = title_screen()

        result = play_game(
            difficulty
        )

        if result is None:
            continue

        name = name_entry()

        add_high_score(
            name,
            result,
            1,
            0,
            0
        )

        high_scores_screen()


# ============================================================
# START
# ============================================================

if __name__ == "__main__":

    try:

        main()

    except KeyboardInterrupt:

        pass

    finally:

        pygame.quit()
        sys.exit()