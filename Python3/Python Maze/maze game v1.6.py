import pygame
import random
import sys
import json
import math
import colorsys

from pathlib import Path
from collections import deque


# ============================================================
# PYTHON MAZE
# ------------------------------------------------------------
# (c) 2026 Stuart MacIntosh V 1.6
# ============================================================


# ============================================================
# CONFIGURATION
# ============================================================

GAME_TITLE = "Python Maze"
VERSION = "(c) 2026 Stuart MacIntosh V 1.6"

MAX_LEVELS = 50

# Movement repeat speed while an arrow key is held.
MOVE_DELAY = 100  # milliseconds

# Maximum number of maze generation attempts.
MAX_GENERATION_ATTEMPTS = 300

# High-score file.
HIGH_SCORE_FILE = (
    Path.home() / ".python_maze_highscores.json"
)


# ============================================================
# INITIALISE PYGAME
# ============================================================

pygame.init()

try:
    pygame.mixer.init(
        frequency=44100,
        size=-16,
        channels=1,
        buffer=512
    )
    AUDIO_AVAILABLE = True
except pygame.error:
    AUDIO_AVAILABLE = False


INFO = pygame.display.Info()

WIDTH = INFO.current_w
HEIGHT = INFO.current_h

screen = pygame.display.set_mode(
    (WIDTH, HEIGHT),
    pygame.FULLSCREEN
)

pygame.display.set_caption(
    GAME_TITLE
)

clock = pygame.time.Clock()


# ============================================================
# COLOURS
# ============================================================

BLACK = (0, 0, 0)
WHITE = (255, 255, 255)
GREEN = (0, 255, 0)
RED = (255, 0, 0)
BLUE = (80, 160, 255)
GREY = (130, 130, 130)
DARK_GREY = (25, 25, 25)
DARK_RED = (65, 10, 10)
HOVER_RED = (115, 20, 20)


# ============================================================
# FONTS
# ============================================================

TITLE_FONT = pygame.font.SysFont(
    "arial",
    100,
    bold=True
)

LARGE_FONT = pygame.font.SysFont(
    "arial",
    52,
    bold=True
)

MEDIUM_FONT = pygame.font.SysFont(
    "arial",
    34
)

SMALL_FONT = pygame.font.SysFont(
    "arial",
    26
)

TINY_FONT = pygame.font.SysFont(
    "arial",
    21
)

SCORE_FONT = pygame.font.SysFont(
    "consolas",
    23
)


# ============================================================
# DIRECTIONS
# ============================================================

DIRECTIONS = [
    (0, -1),    # Up
    (1, 0),     # Right
    (0, 1),     # Down
    (-1, 0)     # Left
]


# ============================================================
# DIFFICULTIES
# ============================================================

DIFFICULTIES = {
    "Easy": {
        "solution_multiplier": 0.70,
        "dead_end_multiplier": 0.65,
        "depth_multiplier": 0.65,
        "score_multiplier": 0.75
    },

    "Medium": {
        "solution_multiplier": 1.00,
        "dead_end_multiplier": 1.00,
        "depth_multiplier": 1.00,
        "score_multiplier": 1.00
    },

    "Hard": {
        "solution_multiplier": 1.25,
        "dead_end_multiplier": 1.25,
        "depth_multiplier": 1.25,
        "score_multiplier": 1.50
    },

    "Extreme": {
        "solution_multiplier": 1.50,
        "dead_end_multiplier": 1.50,
        "depth_multiplier": 1.55,
        "score_multiplier": 2.00
    }
}

difficulty_names = list(
    DIFFICULTIES.keys()
)

selected_difficulty_index = 1


# ============================================================
# SOUND GENERATION
# ============================================================

def create_tone(
    frequency,
    duration,
    volume=0.15
):
    """
    Generate a simple sine-wave sound in memory.
    """

    if not AUDIO_AVAILABLE:
        return None

    sample_rate = 44100

    samples = int(
        sample_rate * duration
    )

    data = bytearray()

    attack_samples = max(
        1,
        int(sample_rate * 0.005)
    )

    release_samples = max(
        1,
        int(sample_rate * 0.025)
    )

    for i in range(samples):

        time = i / sample_rate

        value = math.sin(
            2 * math.pi * frequency * time
        )

        if i < attack_samples:

            envelope = (
                i / attack_samples
            )

        elif i > samples - release_samples:

            envelope = (
                (samples - i)
                /
                release_samples
            )

        else:

            envelope = 1.0

        sample = int(
            value
            *
            volume
            *
            envelope
            *
            32767
        )

        data += int(sample).to_bytes(
            2,
            byteorder="little",
            signed=True
        )

    try:

        return pygame.mixer.Sound(
            buffer=bytes(data)
        )

    except pygame.error:

        return None


def create_chime():
    """
    Generate a pleasant two-note completion sound.
    """

    if not AUDIO_AVAILABLE:
        return None

    sample_rate = 44100
    duration = 0.65

    samples = int(
        sample_rate * duration
    )

    data = bytearray()

    for i in range(samples):

        time = i / sample_rate

        if time < 0.27:
            frequency = 660
        else:
            frequency = 880

        value = math.sin(
            2 * math.pi * frequency * time
        )

        if time < 0.03:

            envelope = time / 0.03

        elif time > duration - 0.1:

            envelope = (
                (duration - time)
                /
                0.1
            )

        else:

            envelope = 1.0

        sample = int(
            value
            *
            0.22
            *
            envelope
            *
            32767
        )

        data += int(sample).to_bytes(
            2,
            byteorder="little",
            signed=True
        )

    try:

        return pygame.mixer.Sound(
            buffer=bytes(data)
        )

    except pygame.error:

        return None


MOVE_SOUND = create_tone(
    950,
    0.025,
    0.08
)

START_SOUND = create_tone(
    523,
    0.18,
    0.12
)

CHIME_SOUND = create_chime()


def play_sound(sound):

    if sound is not None:

        try:
            sound.play()

        except pygame.error:
            pass


# ============================================================
# DIFFICULTY SETTINGS
# ============================================================

def get_level_requirements(level):
    """
    Return maze difficulty requirements for a level.
    """

    if level <= 10:

        solution = 20 + ((level - 1) * 2)
        dead_ends = 3 + (level // 3)
        depth = 5 + (level // 3)

    elif level <= 20:

        solution = 40 + ((level - 11) * 3)
        dead_ends = 6 + ((level - 11) // 2)
        depth = 8 + ((level - 11) // 2)

    elif level <= 30:

        solution = 70 + ((level - 21) * 4)
        dead_ends = 10 + ((level - 21) // 2)
        depth = 11 + ((level - 21) // 2)

    elif level <= 40:

        solution = 110 + ((level - 31) * 5)
        dead_ends = 15 + ((level - 31) // 2)
        depth = 14 + ((level - 31) // 2)

    else:

        solution = 160 + ((level - 41) * 6)
        dead_ends = 20 + ((level - 41) // 2)
        depth = 17 + ((level - 41) // 2)

    difficulty = DIFFICULTIES[
        difficulty_names[
            selected_difficulty_index
        ]
    ]

    solution = max(
        10,
        int(
            solution
            *
            difficulty[
                "solution_multiplier"
            ]
        )
    )

    dead_ends = max(
        2,
        int(
            dead_ends
            *
            difficulty[
                "dead_end_multiplier"
            ]
        )
    )

    depth = max(
        3,
        int(
            depth
            *
            difficulty[
                "depth_multiplier"
            ]
        )
    )

    return (
        solution,
        dead_ends,
        depth
    )


# ============================================================
# MAZE GENERATION
# ============================================================

def generate_basic_maze(
    rows,
    cols
):
    """
    Generate a branchy maze using randomised Prim.

    The outside perimeter always remains completely solid.
    """

    if rows % 2 == 0:
        rows -= 1

    if cols % 2 == 0:
        cols -= 1

    # 1 = wall
    # 0 = path

    maze = [
        [1 for _ in range(cols)]
        for _ in range(rows)
    ]

    start_x = 1
    start_y = 1

    maze[start_y][start_x] = 0

    frontier = []

    def add_frontier(x, y):

        for dx, dy in DIRECTIONS:

            nx = x + (dx * 2)
            ny = y + (dy * 2)

            if (
                0 < nx < cols - 1
                and
                0 < ny < rows - 1
                and
                maze[ny][nx] == 1
            ):

                frontier.append(
                    (
                        x,
                        y,
                        nx,
                        ny
                    )
                )

    add_frontier(
        start_x,
        start_y
    )

    while frontier:

        index = random.randrange(
            len(frontier)
        )

        x, y, nx, ny = frontier.pop(
            index
        )

        if maze[ny][nx] == 0:
            continue

        wall_x = (
            x + nx
        ) // 2

        wall_y = (
            y + ny
        ) // 2

        maze[wall_y][wall_x] = 0

        maze[ny][nx] = 0

        add_frontier(
            nx,
            ny
        )

    return maze


# ============================================================
# ENTRANCE
# ============================================================

def create_entrance(maze):

    maze[1][1] = 0
    maze[0][1] = 0


# ============================================================
# POSSIBLE EXITS
# ============================================================

def get_possible_exits(maze):

    rows = len(maze)
    cols = len(maze[0])

    exits = []

    # Top edge.
    for x in range(
        3,
        cols - 1,
        2
    ):

        if maze[1][x] == 0:

            exits.append(
                (x, 0)
            )

    # Right edge.
    for y in range(
        1,
        rows - 1,
        2
    ):

        if maze[y][cols - 2] == 0:

            exits.append(
                (
                    cols - 1,
                    y
                )
            )

    # Bottom edge.
    for x in range(
        1,
        cols - 1,
        2
    ):

        if maze[rows - 2][x] == 0:

            exits.append(
                (
                    x,
                    rows - 1
                )
            )

    # Left edge.
    for y in range(
        1,
        rows - 1,
        2
    ):

        if maze[y][1] == 0:

            exits.append(
                (
                    0,
                    y
                )
            )

    return exits


# ============================================================
# BFS DISTANCES
# ============================================================

def find_distances(
    maze,
    start
):
    """
    Find shortest distance from start to every reachable cell.
    """

    rows = len(maze)
    cols = len(maze[0])

    distances = {
        start: 0
    }

    queue = deque(
        [start]
    )

    while queue:

        x, y = queue.popleft()

        distance = distances[
            (x, y)
        ]

        for dx, dy in DIRECTIONS:

            nx = x + dx
            ny = y + dy

            if not (
                0 <= nx < cols
                and
                0 <= ny < rows
            ):
                continue

            if maze[ny][nx] != 0:
                continue

            position = (
                nx,
                ny
            )

            if position in distances:
                continue

            distances[position] = (
                distance + 1
            )

            queue.append(
                position
            )

    return distances


# ============================================================
# OPEN NEIGHBOURS
# ============================================================

def get_open_neighbours(
    maze,
    x,
    y
):

    rows = len(maze)
    cols = len(maze[0])

    neighbours = []

    for dx, dy in DIRECTIONS:

        nx = x + dx
        ny = y + dy

        if not (
            0 <= nx < cols
            and
            0 <= ny < rows
        ):
            continue

        if maze[ny][nx] == 0:

            neighbours.append(
                (nx, ny)
            )

    return neighbours


# ============================================================
# DEAD END ANALYSIS
# ============================================================

def analyse_dead_ends(
    maze,
    entrance
):
    """
    Analyse dead ends.

    Returns:

        number of dead ends
        deepest dead end
        all dead-end depths
    """

    rows = len(maze)
    cols = len(maze[0])

    dead_end_cells = []

    for y in range(
        1,
        rows - 1
    ):

        for x in range(
            1,
            cols - 1
        ):

            if maze[y][x] != 0:
                continue

            position = (
                x,
                y
            )

            if position == entrance:
                continue

            neighbours = get_open_neighbours(
                maze,
                x,
                y
            )

            if len(neighbours) == 1:

                dead_end_cells.append(
                    position
                )

    depths = []

    for dead_end in dead_end_cells:

        current = dead_end
        previous = None
        depth = 0

        while True:

            neighbours = get_open_neighbours(
                maze,
                current[0],
                current[1]
            )

            # Junction reached.
            if len(neighbours) > 2:
                break

            next_cells = [
                cell
                for cell in neighbours
                if cell != previous
            ]

            if not next_cells:
                break

            if current == entrance:
                break

            previous = current
            current = next_cells[0]

            depth += 1

        depths.append(
            depth
        )

    if depths:

        deepest = max(
            depths
        )

    else:

        deepest = 0

    return (
        len(dead_end_cells),
        deepest,
        depths
    )


# ============================================================
# GENERATE VALIDATED MAZE
# ============================================================

def generate_maze(
    rows,
    cols,
    minimum_solution,
    minimum_dead_ends,
    minimum_depth
):
    """
    Generate a maze meeting the requested requirements.
    """

    entrance = (1, 0)

    best_candidate = None

    for _ in range(
        MAX_GENERATION_ATTEMPTS
    ):

        maze = generate_basic_maze(
            rows,
            cols
        )

        create_entrance(
            maze
        )

        (
            dead_end_count,
            maximum_depth,
            depth_list
        ) = analyse_dead_ends(
            maze,
            entrance
        )

        if dead_end_count < minimum_dead_ends:
            continue

        if maximum_depth < minimum_depth:
            continue

        distances = find_distances(
            maze,
            entrance
        )

        possible_exits = get_possible_exits(
            maze
        )

        suitable_exits = []

        for exit_position in possible_exits:

            exit_x, exit_y = exit_position

            if exit_y == 0:

                internal = (
                    exit_x,
                    1
                )

            elif exit_y == rows - 1:

                internal = (
                    exit_x,
                    rows - 2
                )

            elif exit_x == 0:

                internal = (
                    1,
                    exit_y
                )

            else:

                internal = (
                    cols - 2,
                    exit_y
                )

            if internal not in distances:
                continue

            solution_length = (
                distances[internal] + 1
            )

            if solution_length < minimum_solution:
                continue

            suitable_exits.append(
                (
                    exit_position,
                    solution_length
                )
            )

        if not suitable_exits:
            continue

        suitable_exits.sort(
            key=lambda item: item[1],
            reverse=True
        )

        candidate_count = max(
            1,
            len(suitable_exits) // 2
        )

        (
            exit_position,
            solution_length
        ) = random.choice(
            suitable_exits[
                :candidate_count
            ]
        )

        quality = (
            solution_length
            +
            maximum_depth * 5
            +
            dead_end_count * 2
        )

        if (
            best_candidate is None
            or
            quality > best_candidate["quality"]
        ):

            best_candidate = {
                "maze": maze,
                "exit": exit_position,
                "solution": solution_length,
                "dead_ends": dead_end_count,
                "depth": maximum_depth,
                "quality": quality
            }

    # --------------------------------------------------------
    # Preferred result.
    # --------------------------------------------------------

    if best_candidate is not None:

        maze = best_candidate["maze"]

        exit_position = (
            best_candidate["exit"]
        )

        exit_x, exit_y = exit_position

        maze[exit_y][exit_x] = 0

        return (
            maze,
            exit_position,
            best_candidate["solution"],
            best_candidate["dead_ends"],
            best_candidate["depth"]
        )

    # --------------------------------------------------------
    # Safety fallback.
    # --------------------------------------------------------

    maze = generate_basic_maze(
        rows,
        cols
    )

    create_entrance(
        maze
    )

    distances = find_distances(
        maze,
        entrance
    )

    possible_exits = get_possible_exits(
        maze
    )

    best_exit = None
    best_distance = -1

    for exit_position in possible_exits:

        exit_x, exit_y = exit_position

        if exit_y == 0:

            internal = (
                exit_x,
                1
            )

        elif exit_y == rows - 1:

            internal = (
                exit_x,
                rows - 2
            )

        elif exit_x == 0:

            internal = (
                1,
                exit_y
            )

        else:

            internal = (
                cols - 2,
                exit_y
            )

        if internal not in distances:
            continue

        distance = (
            distances[internal] + 1
        )

        if distance > best_distance:

            best_distance = distance
            best_exit = exit_position

    if best_exit is None:

        best_exit = (
            cols - 1,
            rows - 2
        )

        best_distance = 0

    exit_x, exit_y = best_exit

    maze[exit_y][exit_x] = 0

    (
        dead_ends,
        deepest,
        _
    ) = analyse_dead_ends(
        maze,
        entrance
    )

    return (
        maze,
        best_exit,
        best_distance,
        dead_ends,
        deepest
    )


# ============================================================
# DRAW BUTTON
# ============================================================

def draw_button(
    rect,
    text,
    font,
    text_colour,
    fill_colour,
    border_colour=WHITE,
    border_width=2
):

    pygame.draw.rect(
        screen,
        fill_colour,
        rect,
        border_radius=6
    )

    pygame.draw.rect(
        screen,
        border_colour,
        rect,
        border_width,
        border_radius=6
    )

    surface = font.render(
        text,
        True,
        text_colour
    )

    text_rect = surface.get_rect(
        center=rect.center
    )

    screen.blit(
        surface,
        text_rect
    )


# ============================================================
# TEXT HELPERS
# ============================================================

def draw_centered(
    text,
    font,
    colour,
    y
):

    surface = font.render(
        text,
        True,
        colour
    )

    rect = surface.get_rect(
        center=(
            WIDTH // 2,
            y
        )
    )

    screen.blit(
        surface,
        rect
    )


def draw_text(
    text,
    font,
    colour,
    x,
    y
):

    surface = font.render(
        text,
        True,
        colour
    )

    screen.blit(
        surface,
        (
            x,
            y
        )
    )


# ============================================================
# MAZE DRAWING
# ============================================================

def draw_maze(
    maze,
    cell_size,
    offset_x,
    offset_y,
    player_x,
    player_y,
    exit_x,
    exit_y
):
    """
    Draw the maze.

    The outside is treated as a frame, so there is no
    alternating wall/path pattern around the perimeter.
    """

    rows = len(maze)
    cols = len(maze[0])

    maze_width = (
        cols * cell_size
    )

    maze_height = (
        rows * cell_size
    )

    # --------------------------------------------------------
    # Solid outer frame.
    # --------------------------------------------------------

    pygame.draw.rect(
        screen,
        BLACK,
        (
            offset_x - 5,
            offset_y - 5,
            maze_width + 10,
            maze_height + 10
        )
    )

    # --------------------------------------------------------
    # Draw paths only.
    # --------------------------------------------------------

    for row in range(rows):

        for col in range(cols):

            if maze[row][col] != 0:
                continue

            pygame.draw.rect(
                screen,
                WHITE,
                (
                    offset_x
                    +
                    col * cell_size,

                    offset_y
                    +
                    row * cell_size,

                    cell_size,
                    cell_size
                )
            )

    # --------------------------------------------------------
    # Player.
    # --------------------------------------------------------

    pygame.draw.rect(
        screen,
        GREEN,
        (
            offset_x
            +
            player_x * cell_size,

            offset_y
            +
            player_y * cell_size,

            cell_size,
            cell_size
        )
    )

    # --------------------------------------------------------
    # Exit.
    # --------------------------------------------------------

    pygame.draw.rect(
        screen,
        RED,
        (
            offset_x
            +
            exit_x * cell_size,

            offset_y
            +
            exit_y * cell_size,

            cell_size,
            cell_size
        )
    )


# ============================================================
# COLOUR-CYCLING LOGO
# ============================================================

def get_logo_colour():

    time = pygame.time.get_ticks()

    hue = (
        time % 5000
    ) / 5000.0

    rgb = colorsys.hsv_to_rgb(
        hue,
        0.85,
        1.0
    )

    return tuple(
        int(value * 255)
        for value in rgb
    )


# ============================================================
# TITLE SCREEN
# ============================================================

def title_screen():

    global selected_difficulty_index

    while True:

        for event in pygame.event.get():

            if event.type == pygame.QUIT:

                return "exit"

            if event.type == pygame.KEYDOWN:

                if event.key == pygame.K_F1:

                    return "start"

                elif event.key == pygame.K_F2:

                    return "instructions"

                elif event.key == pygame.K_F3:

                    selected_difficulty_index = (
                        selected_difficulty_index + 1
                    ) % len(difficulty_names)

                elif event.key == pygame.K_F4:

                    return "scores"

                elif event.key == pygame.K_F10:

                    return "exit"

        screen.fill(BLACK)

        # ----------------------------------------------------
        # Logo.
        # ----------------------------------------------------

        draw_centered(
            GAME_TITLE,
            TITLE_FONT,
            get_logo_colour(),
            HEIGHT // 5
        )

        # ----------------------------------------------------
        # Version.
        # ----------------------------------------------------

        draw_centered(
            VERSION,
            SMALL_FONT,
            GREY,
            HEIGHT // 5 + 75
        )

        difficulty = difficulty_names[
            selected_difficulty_index
        ]

        draw_centered(
            f"Starting difficulty: {difficulty}",
            LARGE_FONT,
            WHITE,
            HEIGHT // 2 - 50
        )

        draw_centered(
            "F1  Start Game",
            MEDIUM_FONT,
            WHITE,
            HEIGHT // 2 + 30
        )

        draw_centered(
            "F2  Instructions",
            MEDIUM_FONT,
            WHITE,
            HEIGHT // 2 + 75
        )

        draw_centered(
            "F3  Change Difficulty",
            MEDIUM_FONT,
            WHITE,
            HEIGHT // 2 + 120
        )

        draw_centered(
            "F4  High Scores",
            MEDIUM_FONT,
            WHITE,
            HEIGHT // 2 + 165
        )

        draw_centered(
            "F10  Exit",
            MEDIUM_FONT,
            WHITE,
            HEIGHT // 2 + 210
        )

        draw_centered(
            "Arrow keys to navigate",
            SMALL_FONT,
            GREY,
            HEIGHT - 50
        )

        pygame.display.flip()

        clock.tick(60)


# ============================================================
# INSTRUCTIONS SCREEN
# ============================================================

def instructions_screen():

    while True:

        for event in pygame.event.get():

            if event.type == pygame.QUIT:

                return

            if event.type == pygame.KEYDOWN:

                if event.key == pygame.K_F2:
                    return

                if event.key == pygame.K_ESCAPE:
                    return

                if event.key == pygame.K_F10:

                    pygame.quit()
                    sys.exit()

        screen.fill(BLACK)

        draw_centered(
            "PYTHON MAZE",
            LARGE_FONT,
            BLUE,
            90
        )

        instructions = [
            "Navigate the green square through the maze.",
            "",
            "Find the red exit.",
            "",
            "Hold an arrow key to keep moving.",
            "",
            "The mazes contain deliberate dead ends",
            "and misleading branches.",
            "",
            "F1   Start Game",
            "F2   Instructions",
            "F3   Change difficulty",
            "F4   High scores",
            "F10  Exit",
            "",
            "Click GIVE UP during a game to abandon",
            "the current run and record a score.",
            "",
            "Press F2 or ESC to return."
        ]

        y = 160

        for line in instructions:

            draw_centered(
                line,
                SMALL_FONT,
                WHITE if line else GREY,
                y
            )

            y += 30

        pygame.display.flip()

        clock.tick(60)


# ============================================================
# HIGH-SCORE STORAGE
# ============================================================

def load_high_scores():

    try:

        if not HIGH_SCORE_FILE.exists():

            return []

        with HIGH_SCORE_FILE.open(
            "r",
            encoding="utf-8"
        ) as file:

            data = json.load(
                file
            )

        if isinstance(
            data,
            list
        ):

            return data

    except (
        OSError,
        ValueError,
        TypeError
    ):

        pass

    return []


def save_high_scores(
    scores
):

    try:

        with HIGH_SCORE_FILE.open(
            "w",
            encoding="utf-8"
        ) as file:

            json.dump(
                scores,
                file,
                indent=2
            )

    except OSError:

        pass


def add_high_score(
    name,
    score,
    difficulty,
    elapsed_seconds,
    moves,
    status
):
    """
    Save a named score.

    status is either:

        COMPLETED
        GAVE UP
    """

    scores = load_high_scores()

    scores.append(
        {
            "name": name,
            "score": score,
            "difficulty": difficulty,
            "time": elapsed_seconds,
            "moves": moves,
            "status": status
        }
    )

    scores.sort(
        key=lambda item: item.get(
            "score",
            0
        ),
        reverse=True
    )

    scores = scores[:10]

    save_high_scores(
        scores
    )


def clear_high_scores():

    try:

        if HIGH_SCORE_FILE.exists():

            HIGH_SCORE_FILE.unlink()

    except OSError:

        pass


# ============================================================
# TIME FORMATTING
# ============================================================

def format_time(
    seconds
):

    try:

        seconds = float(
            seconds
        )

    except (
        ValueError,
        TypeError
    ):

        seconds = 0

    minutes = int(
        seconds // 60
    )

    remaining = int(
        seconds % 60
    )

    return (
        f"{minutes:02d}:{remaining:02d}"
    )


# ============================================================
# NAME ENTRY
# ============================================================

def name_entry_screen(
    score,
    difficulty,
    elapsed_seconds,
    moves,
    status
):
    """
    Ask the player for their name before saving the score.
    """

    name = ""

    max_name_length = 16

    try:
        pygame.key.start_text_input()
    except AttributeError:
        pass

    while True:

        for event in pygame.event.get():

            if event.type == pygame.QUIT:

                try:
                    pygame.key.stop_text_input()
                except AttributeError:
                    pass

                pygame.quit()
                sys.exit()

            if event.type == pygame.TEXTINPUT:

                if len(name) < max_name_length:

                    for character in event.text:

                        if character.isprintable():

                            name += character

            elif event.type == pygame.KEYDOWN:

                if event.key == pygame.K_BACKSPACE:

                    name = name[:-1]

                elif event.key == pygame.K_RETURN:

                    if name.strip():

                        add_high_score(
                            name.strip(),
                            score,
                            difficulty,
                            elapsed_seconds,
                            moves,
                            status
                        )

                        try:
                            pygame.key.stop_text_input()
                        except AttributeError:
                            pass

                        return "saved"

                elif event.key == pygame.K_ESCAPE:

                    try:
                        pygame.key.stop_text_input()
                    except AttributeError:
                        pass

                    return "cancel"

                elif event.key == pygame.K_F10:

                    try:
                        pygame.key.stop_text_input()
                    except AttributeError:
                        pass

                    pygame.quit()
                    sys.exit()

        screen.fill(BLACK)

        # ----------------------------------------------------
        # Heading.
        # ----------------------------------------------------

        if status == "COMPLETED":

            draw_centered(
                "MAZE COMPLETE!",
                LARGE_FONT,
                GREEN,
                130
            )

        else:

            draw_centered(
                "GAME OVER",
                LARGE_FONT,
                RED,
                130
            )

            draw_centered(
                "You gave up.",
                MEDIUM_FONT,
                WHITE,
                185
            )

        # ----------------------------------------------------
        # Details.
        # ----------------------------------------------------

        draw_centered(
            f"Score: {score}",
            SMALL_FONT,
            WHITE,
            260
        )

        draw_centered(
            f"Time: {format_time(elapsed_seconds)}",
            SMALL_FONT,
            WHITE,
            295
        )

        draw_centered(
            f"Moves: {moves}",
            SMALL_FONT,
            WHITE,
            330
        )

        draw_centered(
            f"Difficulty: {difficulty}",
            SMALL_FONT,
            WHITE,
            365
        )

        # ----------------------------------------------------
        # Name.
        # ----------------------------------------------------

        draw_centered(
            "Enter your name for the high scores:",
            MEDIUM_FONT,
            BLUE,
            425
        )

        name_rect = pygame.Rect(
            (WIDTH // 2) - 250,
            455,
            500,
            60
        )

        pygame.draw.rect(
            screen,
            DARK_GREY,
            name_rect,
            border_radius=6
        )

        pygame.draw.rect(
            screen,
            BLUE,
            name_rect,
            2,
            border_radius=6
        )

        if name:

            display_name = name

        else:

            display_name = (
                "Type your name..."
            )

        draw_centered(
            display_name,
            MEDIUM_FONT,
            WHITE if name else GREY,
            485
        )

        draw_centered(
            "ENTER = Save     ESC = Cancel",
            SMALL_FONT,
            GREY,
            565
        )

        pygame.display.flip()

        clock.tick(60)


# ============================================================
# CONFIRM CLEAR SCORES
# ============================================================

def confirm_clear_scores():

    while True:

        for event in pygame.event.get():

            if event.type == pygame.QUIT:

                pygame.quit()
                sys.exit()

            if event.type == pygame.KEYDOWN:

                if event.key == pygame.K_y:

                    clear_high_scores()

                    return True

                if event.key in (
                    pygame.K_n,
                    pygame.K_ESCAPE
                ):

                    return False

                if event.key == pygame.K_F10:

                    pygame.quit()
                    sys.exit()

        screen.fill(BLACK)

        draw_centered(
            "CLEAR ALL HIGH SCORES?",
            LARGE_FONT,
            RED,
            HEIGHT // 2 - 100
        )

        draw_centered(
            "This cannot be undone.",
            MEDIUM_FONT,
            WHITE,
            HEIGHT // 2 - 35
        )

        draw_centered(
            "Press Y to confirm",
            SMALL_FONT,
            GREEN,
            HEIGHT // 2 + 35
        )

        draw_centered(
            "Press N or ESC to cancel",
            SMALL_FONT,
            GREY,
            HEIGHT // 2 + 75
        )

        pygame.display.flip()

        clock.tick(60)


# ============================================================
# HIGH-SCORES SCREEN
# ============================================================

def high_scores_screen():

    clear_button = pygame.Rect(
        (WIDTH // 2) - 140,
        HEIGHT - 110,
        280,
        55
    )

    while True:

        for event in pygame.event.get():

            if event.type == pygame.QUIT:

                pygame.quit()
                sys.exit()

            if event.type == pygame.KEYDOWN:

                if event.key == pygame.K_F4:
                    return

                if event.key == pygame.K_ESCAPE:
                    return

                if event.key == pygame.K_F10:

                    pygame.quit()
                    sys.exit()

            elif event.type == pygame.MOUSEBUTTONDOWN:

                if event.button == 1:

                    if clear_button.collidepoint(
                        event.pos
                    ):

                        confirm_clear_scores()

        screen.fill(BLACK)

        draw_centered(
            "HIGH SCORES",
            LARGE_FONT,
            BLUE,
            70
        )

        scores = load_high_scores()

        # ----------------------------------------------------
        # Column positions.
        # ----------------------------------------------------

        left = (
            WIDTH // 2 - 510
        )

        draw_text(
            "POS",
            SCORE_FONT,
            GREY,
            left,
            130
        )

        draw_text(
            "NAME",
            SCORE_FONT,
            GREY,
            left + 55,
            130
        )

        draw_text(
            "SCORE",
            SCORE_FONT,
            GREY,
            left + 220,
            130
        )

        draw_text(
            "DIFFICULTY",
            SCORE_FONT,
            GREY,
            left + 330,
            130
        )

        draw_text(
            "STATUS",
            SCORE_FONT,
            GREY,
            left + 490,
            130
        )

        draw_text(
            "TIME",
            SCORE_FONT,
            GREY,
            left + 615,
            130
        )

        draw_text(
            "MOVES",
            SCORE_FONT,
            GREY,
            left + 715,
            130
        )

        # ----------------------------------------------------
        # Scores.
        # ----------------------------------------------------

        if not scores:

            draw_centered(
                "No scores recorded yet.",
                MEDIUM_FONT,
                GREY,
                230
            )

        else:

            y = 175

            for index, entry in enumerate(
                scores,
                start=1
            ):

                name = entry.get(
                    "name",
                    "Unknown"
                )

                if len(name) > 13:

                    name = name[:13]

                score = entry.get(
                    "score",
                    0
                )

                difficulty = entry.get(
                    "difficulty",
                    ""
                )

                status = entry.get(
                    "status",
                    "UNKNOWN"
                )

                elapsed = entry.get(
                    "time",
                    0
                )

                moves = entry.get(
                    "moves",
                    0
                )

                if status == "COMPLETED":

                    status_colour = GREEN

                elif status == "GAVE UP":

                    status_colour = RED

                else:

                    status_colour = GREY

                draw_text(
                    str(index),
                    SCORE_FONT,
                    WHITE,
                    left,
                    y
                )

                draw_text(
                    name,
                    SCORE_FONT,
                    WHITE,
                    left + 55,
                    y
                )

                draw_text(
                    f"{score:,}",
                    SCORE_FONT,
                    WHITE,
                    left + 220,
                    y
                )

                draw_text(
                    difficulty,
                    SCORE_FONT,
                    WHITE,
                    left + 330,
                    y
                )

                draw_text(
                    status,
                    SCORE_FONT,
                    status_colour,
                    left + 490,
                    y
                )

                draw_text(
                    format_time(elapsed),
                    SCORE_FONT,
                    WHITE,
                    left + 615,
                    y
                )

                draw_text(
                    str(moves),
                    SCORE_FONT,
                    WHITE,
                    left + 715,
                    y
                )

                y += 38

        # ----------------------------------------------------
        # Clear Scores button.
        # ----------------------------------------------------

        mouse_position = pygame.mouse.get_pos()

        if clear_button.collidepoint(
            mouse_position
        ):

            button_colour = HOVER_RED

        else:

            button_colour = DARK_RED

        draw_button(
            clear_button,
            "CLEAR SCORES",
            SMALL_FONT,
            WHITE,
            button_colour,
            RED
        )

        draw_centered(
            "F4 or ESC = Return",
            SMALL_FONT,
            GREY,
            HEIGHT - 40
        )

        pygame.display.flip()

        clock.tick(60)


# ============================================================
# SCORE CALCULATION
# ============================================================

def calculate_score(
    level,
    elapsed_seconds,
    moves,
    difficulty
):
    """
    Calculate score based on level, time and moves.

    Difficulty affects the multiplier.
    """

    multiplier = DIFFICULTIES[
        difficulty
    ][
        "score_multiplier"
    ]

    base = (
        level * 1000
    )

    time_penalty = (
        elapsed_seconds * 8
    )

    move_penalty = (
        moves * 3
    )

    raw_score = (
        base
        -
        time_penalty
        -
        move_penalty
    )

    return max(
        0,
        int(
            raw_score
            *
            multiplier
        )
    )


# ============================================================
# FINAL COMPLETION SCREEN
# ============================================================

def completion_screen(
    score,
    elapsed_seconds,
    moves,
    difficulty
):
    """
    Completed all 50 levels.

    Player is then asked for a name.
    """

    play_sound(
        CHIME_SOUND
    )

    while True:

        for event in pygame.event.get():

            if event.type == pygame.QUIT:

                pygame.quit()
                sys.exit()

            if event.type == pygame.KEYDOWN:

                if event.key == pygame.K_F1:

                    result = name_entry_screen(
                        score,
                        difficulty,
                        elapsed_seconds,
                        moves,
                        "COMPLETED"
                    )

                    if result == "saved":

                        return "menu"

                elif event.key == pygame.K_ESCAPE:

                    return "menu"

                elif event.key == pygame.K_F10:

                    pygame.quit()
                    sys.exit()

        screen.fill(BLACK)

        draw_centered(
            "ALL 50 LEVELS COMPLETE!",
            LARGE_FONT,
            GREEN,
            150
        )

        draw_centered(
            f"Score: {score:,}",
            MEDIUM_FONT,
            WHITE,
            245
        )

        draw_centered(
            f"Time: {format_time(elapsed_seconds)}",
            MEDIUM_FONT,
            WHITE,
            295
        )

        draw_centered(
            f"Moves: {moves}",
            MEDIUM_FONT,
            WHITE,
            345
        )

        draw_centered(
            f"Difficulty: {difficulty}",
            MEDIUM_FONT,
            WHITE,
            395
        )

        draw_centered(
            "F1  Enter Name & Save Score",
            SMALL_FONT,
            BLUE,
            490
        )

        draw_centered(
            "ESC  Main Menu",
            SMALL_FONT,
            GREY,
            535
        )

        pygame.display.flip()

        clock.tick(60)


# ============================================================
# PLAY GAME
# ============================================================

def play_game():

    difficulty = difficulty_names[
        selected_difficulty_index
    ]

    play_sound(
        START_SOUND
    )

    level = 1

    total_moves = 0

    game_start_time = (
        pygame.time.get_ticks()
    )

    while level <= MAX_LEVELS:

        # ----------------------------------------------------
        # Maze size.
        # ----------------------------------------------------

        rows = 11 + (
            (level - 1) * 2
        )

        cols = 11 + (
            (level - 1) * 2
        )

        (
            minimum_solution,
            minimum_dead_ends,
            minimum_depth
        ) = get_level_requirements(
            level
        )

        # ----------------------------------------------------
        # Generate.
        # ----------------------------------------------------

        (
            maze,
            exit_position,
            solution_length,
            dead_end_count,
            maximum_depth
        ) = generate_maze(
            rows,
            cols,
            minimum_solution,
            minimum_dead_ends,
            minimum_depth
        )

        exit_x, exit_y = exit_position

        # ----------------------------------------------------
        # Screen layout.
        # ----------------------------------------------------

        available_width = (
            WIDTH - 40
        )

        available_height = (
            HEIGHT - 150
        )

        cell_size = min(
            available_width // cols,
            available_height // rows
        )

        cell_size = max(
            3,
            cell_size
        )

        maze_width = (
            cols * cell_size
        )

        maze_height = (
            rows * cell_size
        )

        offset_x = (
            WIDTH - maze_width
        ) // 2

        offset_y = (
            115
            +
            max(
                0,
                (
                    HEIGHT
                    -
                    115
                    -
                    maze_height
                ) // 2
            )
        )

        # ----------------------------------------------------
        # Player.
        # ----------------------------------------------------

        player_x = 1
        player_y = 0

        next_move_time = 0

        level_start_time = (
            pygame.time.get_ticks()
        )

        level_moves = 0

        # ----------------------------------------------------
        # Give Up button.
        # ----------------------------------------------------

        give_up_button = pygame.Rect(
            WIDTH - 175,
            HEIGHT - 72,
            150,
            45
        )

        running = True

        # ====================================================
        # LEVEL LOOP
        # ====================================================

        while running:

            current_time = (
                pygame.time.get_ticks()
            )

            # ------------------------------------------------
            # EVENTS
            # ------------------------------------------------

            for event in pygame.event.get():

                if event.type == pygame.QUIT:

                    pygame.quit()
                    sys.exit()

                elif event.type == pygame.KEYDOWN:

                    if event.key == pygame.K_ESCAPE:

                        return "menu"

                    if event.key == pygame.K_F10:

                        pygame.quit()
                        sys.exit()

                elif event.type == pygame.MOUSEBUTTONDOWN:

                    if event.button == 1:

                        if give_up_button.collidepoint(
                            event.pos
                        ):

                            # --------------------------------
                            # Calculate score at point of
                            # giving up.
                            # --------------------------------

                            elapsed_seconds = (
                                current_time
                                -
                                game_start_time
                            ) / 1000.0

                            score = calculate_score(
                                level,
                                elapsed_seconds,
                                total_moves,
                                difficulty
                            )

                            # --------------------------------
                            # Ask for name.
                            # --------------------------------

                            result = name_entry_screen(
                                score,
                                difficulty,
                                elapsed_seconds,
                                total_moves,
                                "GAVE UP"
                            )

                            if result == "saved":

                                return "menu"

            # ------------------------------------------------
            # Held arrow keys.
            # ------------------------------------------------

            keys = pygame.key.get_pressed()

            dx = 0
            dy = 0

            if keys[pygame.K_LEFT]:

                dx = -1

            elif keys[pygame.K_RIGHT]:

                dx = 1

            elif keys[pygame.K_UP]:

                dy = -1

            elif keys[pygame.K_DOWN]:

                dy = 1

            # ------------------------------------------------
            # Move.
            # ------------------------------------------------

            if (
                (dx != 0 or dy != 0)
                and
                current_time >= next_move_time
            ):

                new_x = (
                    player_x + dx
                )

                new_y = (
                    player_y + dy
                )

                if (
                    0 <= new_x < cols
                    and
                    0 <= new_y < rows
                    and
                    maze[new_y][new_x] == 0
                ):

                    player_x = new_x
                    player_y = new_y

                    total_moves += 1
                    level_moves += 1

                    play_sound(
                        MOVE_SOUND
                    )

                next_move_time = (
                    current_time
                    +
                    MOVE_DELAY
                )

            # ------------------------------------------------
            # Check exit.
            # ------------------------------------------------

            if (
                player_x == exit_x
                and
                player_y == exit_y
            ):

                running = False

            # ------------------------------------------------
            # Stats.
            # ------------------------------------------------

            elapsed_seconds = (
                current_time
                -
                game_start_time
            ) / 1000.0

            level_elapsed = (
                current_time
                -
                level_start_time
            ) / 1000.0

            score = calculate_score(
                level,
                elapsed_seconds,
                total_moves,
                difficulty
            )

            # ------------------------------------------------
            # Draw.
            # ------------------------------------------------

            screen.fill(
                DARK_GREY
            )

            draw_text(
                f"LEVEL {level}/{MAX_LEVELS}",
                SMALL_FONT,
                WHITE,
                20,
                18
            )

            draw_text(
                f"TIME {format_time(elapsed_seconds)}",
                SMALL_FONT,
                WHITE,
                220,
                18
            )

            draw_text(
                f"MOVES {total_moves}",
                SMALL_FONT,
                WHITE,
                435,
                18
            )

            draw_text(
                f"SCORE {score:,}",
                SMALL_FONT,
                WHITE,
                620,
                18
            )

            draw_text(
                difficulty.upper(),
                SMALL_FONT,
                BLUE,
                WIDTH - 165,
                18
            )

            # ------------------------------------------------
            # Maze.
            # ------------------------------------------------

            draw_maze(
                maze,
                cell_size,
                offset_x,
                offset_y,
                player_x,
                player_y,
                exit_x,
                exit_y
            )

            # ------------------------------------------------
            # Bottom information.
            # ------------------------------------------------

            draw_text(
                f"Target: {minimum_solution}+",
                TINY_FONT,
                GREY,
                20,
                HEIGHT - 50
            )

            draw_text(
                f"Dead ends: {dead_end_count}",
                TINY_FONT,
                GREY,
                195,
                HEIGHT - 50
            )

            draw_text(
                f"Deepest: {maximum_depth}",
                TINY_FONT,
                GREY,
                365,
                HEIGHT - 50
            )

            # ------------------------------------------------
            # Give Up button.
            # ------------------------------------------------

            mouse_position = pygame.mouse.get_pos()

            if give_up_button.collidepoint(
                mouse_position
            ):

                button_colour = HOVER_RED

            else:

                button_colour = DARK_RED

            draw_button(
                give_up_button,
                "GIVE UP",
                SMALL_FONT,
                WHITE,
                button_colour,
                RED
            )

            pygame.display.flip()

            clock.tick(60)

        # ====================================================
        # LEVEL COMPLETE
        # ====================================================

        play_sound(
            CHIME_SOUND
        )

        level_elapsed = (
            pygame.time.get_ticks()
            -
            level_start_time
        ) / 1000.0

        screen.fill(BLACK)

        draw_centered(
            f"LEVEL {level} COMPLETE",
            LARGE_FONT,
            GREEN,
            HEIGHT // 2 - 100
        )

        draw_centered(
            f"Time: {format_time(level_elapsed)}",
            MEDIUM_FONT,
            WHITE,
            HEIGHT // 2 - 30
        )

        draw_centered(
            f"Moves: {level_moves}",
            MEDIUM_FONT,
            WHITE,
            HEIGHT // 2 + 15
        )

        draw_centered(
            f"Solution: {solution_length} moves",
            SMALL_FONT,
            GREY,
            HEIGHT // 2 + 65
        )

        pygame.display.flip()

        pygame.time.delay(
            900
        )

        level += 1

    # ========================================================
    # COMPLETE GAME
    # ========================================================

    final_elapsed = (
        pygame.time.get_ticks()
        -
        game_start_time
    ) / 1000.0

    final_score = calculate_score(
        MAX_LEVELS,
        final_elapsed,
        total_moves,
        difficulty
    )

    return completion_screen(
        final_score,
        final_elapsed,
        total_moves,
        difficulty
    )


# ============================================================
# MAIN MENU LOOP
# ============================================================

def main():

    while True:

        selection = title_screen()

        if selection == "start":

            result = play_game()

            if result in (
                "menu",
                "restart"
            ):

                continue

        elif selection == "instructions":

            instructions_screen()

        elif selection == "scores":

            high_scores_screen()

        elif selection == "exit":

            break

    pygame.quit()
    sys.exit()


# ============================================================
# ENTRY POINT
# ============================================================

if __name__ == "__main__":

    main()