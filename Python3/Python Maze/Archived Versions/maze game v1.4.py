import pygame
import random
import sys
from collections import deque


# ============================================================
# INITIALISE PYGAME
# ============================================================

pygame.init()

INFO = pygame.display.Info()

WIDTH = INFO.current_w
HEIGHT = INFO.current_h

screen = pygame.display.set_mode(
    (WIDTH, HEIGHT),
    pygame.FULLSCREEN
)

pygame.display.set_caption("Random Maze Game")


# ============================================================
# COLOURS
# ============================================================

WHITE = (255, 255, 255)
BLACK = (0, 0, 0)
GREEN = (0, 255, 0)
RED = (255, 0, 0)
BLUE = (0, 0, 255)


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
# GAME SETTINGS
# ============================================================

MAX_LEVELS = 50

# Maximum attempts to generate a suitable maze.
MAX_GENERATION_ATTEMPTS = 300

# Time between repeated moves when an arrow key is held.
# Lower value = faster movement.
MOVE_DELAY = 100


# ============================================================
# DISPLAY
# ============================================================

FONT = pygame.font.Font(None, 50)

clock = pygame.time.Clock()


# ============================================================
# DIFFICULTY SETTINGS
# ============================================================

def get_difficulty(level):
    """
    Return difficulty requirements for the current level.

    Returns:

        minimum_solution
        minimum_dead_ends
        minimum_dead_end_depth
    """

    if level <= 10:

        minimum_solution = 20 + ((level - 1) * 2)
        minimum_dead_ends = 3 + (level // 3)
        minimum_dead_end_depth = 5 + (level // 3)

    elif level <= 20:

        minimum_solution = 40 + ((level - 11) * 3)
        minimum_dead_ends = 6 + ((level - 11) // 2)
        minimum_dead_end_depth = 8 + ((level - 11) // 2)

    elif level <= 30:

        minimum_solution = 70 + ((level - 21) * 4)
        minimum_dead_ends = 10 + ((level - 21) // 2)
        minimum_dead_end_depth = 11 + ((level - 21) // 2)

    elif level <= 40:

        minimum_solution = 110 + ((level - 31) * 5)
        minimum_dead_ends = 15 + ((level - 31) // 2)
        minimum_dead_end_depth = 14 + ((level - 31) // 2)

    else:

        minimum_solution = 160 + ((level - 41) * 6)
        minimum_dead_ends = 20 + ((level - 41) // 2)
        minimum_dead_end_depth = 17 + ((level - 41) // 2)

    return (
        minimum_solution,
        minimum_dead_ends,
        minimum_dead_end_depth
    )


# ============================================================
# RANDOMISED PRIM MAZE GENERATOR
# ============================================================

def generate_basic_maze(rows, cols):
    """
    Generate a maze using a randomised Prim-style algorithm.

    Unlike recursive backtracking, this tends to create a more
    branchy maze with shorter corridors and more opportunities
    for misleading routes.

    The outer perimeter remains solid.
    """

    # Ensure odd dimensions.
    if rows % 2 == 0:
        rows -= 1

    if cols % 2 == 0:
        cols -= 1

    # Everything begins as a wall.
    maze = [
        [1 for _ in range(cols)]
        for _ in range(rows)
    ]

    # Start cell.
    start = (1, 1)

    maze[1][1] = 0

    # Frontier walls.

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
        start[0],
        start[1]
    )

    # --------------------------------------------------------
    # Randomised Prim algorithm
    # --------------------------------------------------------

    while frontier:

        index = random.randrange(
            len(frontier)
        )

        x, y, nx, ny = frontier.pop(
            index
        )

        # If destination has already been carved,
        # ignore this frontier entry.
        if maze[ny][nx] == 0:
            continue

        # Carve wall between cells.
        wall_x = (x + nx) // 2
        wall_y = (y + ny) // 2

        maze[wall_y][wall_x] = 0

        # Carve destination.
        maze[ny][nx] = 0

        # Add new frontier.
        add_frontier(
            nx,
            ny
        )

    return maze


# ============================================================
# CREATE ENTRANCE
# ============================================================

def create_entrance(maze):

    maze[1][1] = 0

    # Opening through top border.
    maze[0][1] = 0


# ============================================================
# GET POSSIBLE EXITS
# ============================================================

def get_possible_exits(maze):

    rows = len(maze)
    cols = len(maze[0])

    exits = []

    # --------------------------------------------------------
    # TOP
    # --------------------------------------------------------

    # Start at 3 because (1,0) is the entrance.
    for x in range(3, cols - 1, 2):

        if maze[1][x] == 0:

            exits.append(
                (x, 0)
            )

    # --------------------------------------------------------
    # RIGHT
    # --------------------------------------------------------

    for y in range(1, rows - 1, 2):

        if maze[y][cols - 2] == 0:

            exits.append(
                (cols - 1, y)
            )

    # --------------------------------------------------------
    # BOTTOM
    # --------------------------------------------------------

    for x in range(1, cols - 1, 2):

        if maze[rows - 2][x] == 0:

            exits.append(
                (x, rows - 1)
            )

    # --------------------------------------------------------
    # LEFT
    # --------------------------------------------------------

    for y in range(1, rows - 1, 2):

        if maze[y][1] == 0:

            exits.append(
                (0, y)
            )

    return exits


# ============================================================
# SHORTEST PATH DISTANCE
# ============================================================

def find_distances(maze, start):
    """
    Perform BFS from the start.

    Returns a dictionary containing the shortest distance
    from start to every reachable cell.
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

        current_distance = distances[
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
                current_distance + 1
            )

            queue.append(
                position
            )

    return distances


# ============================================================
# COUNT OPEN NEIGHBOURS
# ============================================================

def get_open_neighbours(
    maze,
    x,
    y
):
    """
    Return all open neighbouring cells.
    """

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
# FIND DEAD ENDS
# ============================================================

def analyse_dead_ends(
    maze,
    entrance,
    exit_position
):
    """
    Find dead ends in the maze.

    A dead end is an open cell with only one open neighbour.

    Returns:

        number of dead ends
        maximum dead-end depth
        list of dead-end depths
    """

    rows = len(maze)
    cols = len(maze[0])

    dead_ends = []

    # --------------------------------------------------------
    # Find all dead-end cells.
    # --------------------------------------------------------

    for y in range(1, rows - 1):

        for x in range(1, cols - 1):

            if maze[y][x] != 0:
                continue

            position = (
                x,
                y
            )

            # Don't count entrance or exit.
            if position == entrance:
                continue

            if position == exit_position:
                continue

            neighbours = get_open_neighbours(
                maze,
                x,
                y
            )

            if len(neighbours) == 1:

                dead_ends.append(
                    position
                )

    # --------------------------------------------------------
    # Calculate depth of each dead end.
    #
    # We walk backwards from the dead end until we reach a
    # junction.
    # --------------------------------------------------------

    dead_end_depths = []

    for dead_end in dead_ends:

        current = dead_end
        previous = None
        depth = 0

        while True:

            neighbours = get_open_neighbours(
                maze,
                current[0],
                current[1]
            )

            # Don't walk backwards.
            next_cells = [
                cell
                for cell in neighbours
                if cell != previous
            ]

            # We have reached a junction.
            if len(neighbours) > 2:

                break

            # We have reached the entrance or exit.
            if current == entrance:
                break

            if current == exit_position:
                break

            # No further route.
            if not next_cells:
                break

            previous = current

            current = next_cells[0]

            depth += 1

        dead_end_depths.append(
            depth
        )

    if dead_end_depths:

        maximum_depth = max(
            dead_end_depths
        )

    else:

        maximum_depth = 0

    return (
        len(dead_ends),
        maximum_depth,
        dead_end_depths
    )


# ============================================================
# GENERATE COMPLETE MAZE
# ============================================================

def generate_maze(
    rows,
    cols,
    minimum_solution,
    minimum_dead_ends,
    minimum_dead_end_depth
):
    """
    Generate and validate a maze.

    A maze is accepted only when it satisfies:

        minimum solution length
        minimum number of dead ends
        minimum dead-end depth
    """

    entrance = (1, 0)

    for attempt in range(
        MAX_GENERATION_ATTEMPTS
    ):

        # ----------------------------------------------------
        # Generate maze.
        # ----------------------------------------------------

        maze = generate_basic_maze(
            rows,
            cols
        )

        create_entrance(
            maze
        )

        # ----------------------------------------------------
        # Find possible exits.
        # ----------------------------------------------------

        possible_exits = get_possible_exits(
            maze
        )

        random.shuffle(
            possible_exits
        )

        suitable_exits = []

        # ----------------------------------------------------
        # Calculate distances once.
        # ----------------------------------------------------

        distances = find_distances(
            maze,
            entrance
        )

        # ----------------------------------------------------
        # Examine exits.
        # ----------------------------------------------------

        for exit_position in possible_exits:

            # Internal cell adjacent to exit.
            exit_x, exit_y = exit_position

            if exit_y == 0:

                inside = (
                    exit_x,
                    exit_y + 1
                )

            elif exit_y == rows - 1:

                inside = (
                    exit_x,
                    exit_y - 1
                )

            elif exit_x == 0:

                inside = (
                    exit_x + 1,
                    exit_y
                )

            else:

                inside = (
                    exit_x - 1,
                    exit_y
                )

            # Make sure the internal cell is reachable.
            if inside not in distances:
                continue

            solution_length = (
                distances[inside] + 1
            )

            # Check solution length.
            if solution_length < minimum_solution:
                continue

            # Temporarily create exit.
            maze[exit_y][exit_x] = 0

            # Analyse dead ends.
            (
                dead_end_count,
                maximum_dead_end_depth,
                dead_end_depths
            ) = analyse_dead_ends(
                maze,
                entrance,
                exit_position
            )

            # Close exit again.
            maze[exit_y][exit_x] = 1

            # Check dead-end requirements.
            if dead_end_count < minimum_dead_ends:
                continue

            if maximum_dead_end_depth < minimum_dead_end_depth:
                continue

            suitable_exits.append(
                (
                    exit_position,
                    solution_length,
                    dead_end_count,
                    maximum_dead_end_depth
                )
            )

        # ----------------------------------------------------
        # Suitable maze found.
        # ----------------------------------------------------

        if suitable_exits:

            # Prefer mazes with:
            #
            # 1. Long solution
            # 2. Deep dead ends
            # 3. More dead ends

            suitable_exits.sort(
                key=lambda item: (
                    item[1],
                    item[3],
                    item[2]
                ),
                reverse=True
            )

            # Choose randomly from the better candidates.
            candidate_count = max(
                1,
                len(suitable_exits) // 2
            )

            candidates = suitable_exits[
                :candidate_count
            ]

            (
                exit_position,
                solution_length,
                dead_end_count,
                maximum_dead_end_depth
            ) = random.choice(
                candidates
            )

            # Open exit permanently.
            exit_x, exit_y = exit_position

            maze[exit_y][exit_x] = 0

            return (
                maze,
                exit_position,
                solution_length,
                dead_end_count,
                maximum_dead_end_depth
            )

    # ========================================================
    # FALLBACK
    # ========================================================

    # If we fail to generate a sufficiently difficult maze
    # within the limit, use the best maze we can produce.

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

    best_candidate = None

    for exit_position in possible_exits:

        exit_x, exit_y = exit_position

        if exit_y == 0:

            inside = (
                exit_x,
                exit_y + 1
            )

        elif exit_y == rows - 1:

            inside = (
                exit_x,
                exit_y - 1
            )

        elif exit_x == 0:

            inside = (
                exit_x + 1,
                exit_y
            )

        else:

            inside = (
                exit_x - 1,
                exit_y
            )

        if inside not in distances:
            continue

        solution_length = (
            distances[inside] + 1
        )

        maze[exit_y][exit_x] = 0

        (
            dead_end_count,
            maximum_dead_end_depth,
            _
        ) = analyse_dead_ends(
            maze,
            entrance,
            exit_position
        )

        maze[exit_y][exit_x] = 1

        score = (
            solution_length * 10
            +
            maximum_dead_end_depth * 5
            +
            dead_end_count
        )

        if (
            best_candidate is None
            or
            score > best_candidate[0]
        ):

            best_candidate = (
                score,
                exit_position,
                solution_length,
                dead_end_count,
                maximum_dead_end_depth
            )

    if best_candidate is None:

        # Extremely unlikely safety fallback.
        exit_position = (
            cols - 1,
            rows - 2
        )

        exit_x, exit_y = exit_position

        maze[exit_y][exit_x] = 0

        solution_length = (
            distances.get(
                (exit_x - 1, exit_y),
                0
            ) + 1
        )

        dead_end_count = 0
        maximum_dead_end_depth = 0

    else:

        (
            _,
            exit_position,
            solution_length,
            dead_end_count,
            maximum_dead_end_depth
        ) = best_candidate

        exit_x, exit_y = exit_position

        maze[exit_y][exit_x] = 0

    return (
        maze,
        exit_position,
        solution_length,
        dead_end_count,
        maximum_dead_end_depth
    )


# ============================================================
# MOVE PLAYER
# ============================================================

def move_player(
    maze,
    player_x,
    player_y,
    dx,
    dy
):
    """
    Attempt to move the player one cell.
    """

    rows = len(maze)
    cols = len(maze[0])

    new_x = player_x + dx
    new_y = player_y + dy

    if not (
        0 <= new_x < cols
        and
        0 <= new_y < rows
    ):

        return (
            player_x,
            player_y
        )

    if maze[new_y][new_x] != 0:

        return (
            player_x,
            player_y
        )

    return (
        new_x,
        new_y
    )


# ============================================================
# SHOW MESSAGE
# ============================================================

def show_message(
    text,
    duration=2
):

    screen.fill(BLACK)

    message = FONT.render(
        text,
        True,
        BLUE
    )

    text_rect = message.get_rect(
        center=(
            WIDTH // 2,
            HEIGHT // 2
        )
    )

    screen.blit(
        message,
        text_rect
    )

    pygame.display.flip()

    pygame.time.delay(
        duration * 1000
    )


# ============================================================
# MAIN GAME
# ============================================================

def main():

    level = 1

    while level <= MAX_LEVELS:

        # ----------------------------------------------------
        # Maze dimensions.
        #
        # Level 1  = 11 x 11
        # Level 10 = 29 x 29
        # Level 20 = 49 x 49
        # Level 30 = 69 x 69
        # Level 40 = 89 x 89
        # Level 50 = 109 x 109
        # ----------------------------------------------------

        rows = 11 + (
            (level - 1) * 2
        )

        cols = 11 + (
            (level - 1) * 2
        )

        # ----------------------------------------------------
        # Difficulty.
        # ----------------------------------------------------

        (
            minimum_solution,
            minimum_dead_ends,
            minimum_dead_end_depth
        ) = get_difficulty(
            level
        )

        # ----------------------------------------------------
        # Generate maze.
        # ----------------------------------------------------

        (
            maze,
            exit_position,
            solution_length,
            dead_end_count,
            maximum_dead_end_depth
        ) = generate_maze(
            rows,
            cols,
            minimum_solution,
            minimum_dead_ends,
            minimum_dead_end_depth
        )

        exit_x, exit_y = exit_position

        # ----------------------------------------------------
        # Cell size.
        # ----------------------------------------------------

        cell_size = min(
            WIDTH // cols,
            HEIGHT // rows
        )

        maze_width = (
            cols * cell_size
        )

        maze_height = (
            rows * cell_size
        )

        # ----------------------------------------------------
        # Centre maze.
        # ----------------------------------------------------

        maze_offset_x = (
            WIDTH - maze_width
        ) // 2

        maze_offset_y = (
            HEIGHT - maze_height
        ) // 2

        # ----------------------------------------------------
        # Player.
        # ----------------------------------------------------

        player_x = 1
        player_y = 0

        next_move_time = 0

        running = True

        # ====================================================
        # LEVEL LOOP
        # ====================================================

        while running:

            current_time = pygame.time.get_ticks()

            # ------------------------------------------------
            # EVENTS
            # ------------------------------------------------

            for event in pygame.event.get():

                if event.type == pygame.QUIT:

                    pygame.quit()
                    sys.exit()

                elif event.type == pygame.KEYDOWN:

                    if event.key == pygame.K_ESCAPE:

                        pygame.quit()
                        sys.exit()

            # ------------------------------------------------
            # READ HELD KEYS
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
            # MOVE PLAYER
            # ------------------------------------------------

            if (
                (dx != 0 or dy != 0)
                and
                current_time >= next_move_time
            ):

                (
                    player_x,
                    player_y
                ) = move_player(
                    maze,
                    player_x,
                    player_y,
                    dx,
                    dy
                )

                next_move_time = (
                    current_time
                    +
                    MOVE_DELAY
                )

            # ------------------------------------------------
            # CHECK EXIT
            # ------------------------------------------------

            if (
                player_x == exit_x
                and
                player_y == exit_y
            ):

                running = False

            # ------------------------------------------------
            # DRAW
            # ------------------------------------------------

            screen.fill(BLACK)

            # ------------------------------------------------
            # Draw maze.
            # ------------------------------------------------

            for row in range(rows):

                for col in range(cols):

                    if maze[row][col] == 0:

                        colour = WHITE

                    else:

                        colour = BLACK

                    pygame.draw.rect(
                        screen,
                        colour,
                        (
                            maze_offset_x
                            +
                            col * cell_size,

                            maze_offset_y
                            +
                            row * cell_size,

                            cell_size,
                            cell_size
                        )
                    )

            # ------------------------------------------------
            # Draw player.
            # ------------------------------------------------

            pygame.draw.rect(
                screen,
                GREEN,
                (
                    maze_offset_x
                    +
                    player_x * cell_size,

                    maze_offset_y
                    +
                    player_y * cell_size,

                    cell_size,
                    cell_size
                )
            )

            # ------------------------------------------------
            # Draw exit.
            # ------------------------------------------------

            pygame.draw.rect(
                screen,
                RED,
                (
                    maze_offset_x
                    +
                    exit_x * cell_size,

                    maze_offset_y
                    +
                    exit_y * cell_size,

                    cell_size,
                    cell_size
                )
            )

            pygame.display.flip()

            clock.tick(60)

        # ====================================================
        # LEVEL COMPLETED
        # ====================================================

        if level == MAX_LEVELS:

            show_message(
                "Congratulations! You've completed the final level!",
                4
            )

            break

        else:

            show_message(
                f"Level {level} Complete! "
                f"Solution: {solution_length} moves",
                2
            )

        level += 1

    pygame.quit()


# ============================================================
# PROGRAM ENTRY POINT
# ============================================================

if __name__ == "__main__":
    main()