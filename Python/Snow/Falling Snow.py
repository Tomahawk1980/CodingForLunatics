import pygame
import random
import math

# Initialize Pygame
pygame.init()

# Screen settings
fullscreen = True  # Set to True for fullscreen mode

# Hide the mouse cursor
pygame.mouse.set_visible(False)

# Get the screen dimensions
screen_info = pygame.display.Info()
screen_width = screen_info.current_w
screen_height = screen_info.current_h

# Snowflake settings
snowflake_count = 1200  # Increased the number of snowflakes
snowflakes = []

# Snowfall settings
blizzard_factor = 2  # Higher value results in stronger blizzards
snow_accumulation = [[0] * screen_width for _ in range(8)]  # Snow accumulation grid

# Colors
WHITE = (255, 255, 255)
GREY_SHADES = [(200, 200, 200), (180, 180, 180), (160, 160, 160), (140, 140, 140), (120, 120, 120)]
DARK_GREY = (100, 100, 100)

# Initialize the screen in fullscreen mode
screen = pygame.display.set_mode((screen_width, screen_height), pygame.FULLSCREEN)

pygame.display.set_caption("Falling Snow Simulation")

# Create snowflakes with random starting positions and improved downward motion
for _ in range(snowflake_count):
    x = random.randint(0, screen_width)
    y = random.randint(0, screen_height)
    speed = random.uniform(1, 3)  # Vary the speed
    angle = random.uniform(math.pi / 6, 5 * math.pi / 6)  # Improved downward motion
    color = random.choice(GREY_SHADES)  # Random color from the shades of grey
    thickness = random.randint(1, 3)  # Random thickness
    snowflakes.append([x, y, speed, angle, color, thickness])

def draw_snowflakes():
    for flake in snowflakes:
        x, y, color, thickness = flake[0], flake[1], flake[4], flake[5]
        
        # Draw a small cross for texture
        pygame.draw.line(screen, color, (x, y - thickness), (x, y + thickness), thickness)
        pygame.draw.line(screen, color, (x - thickness, y), (x + thickness, y), thickness)

def accumulate_snow():
    for flake in snowflakes:
        x, y, _, _, _ = flake
        if y >= screen_height:
            # Add to snow accumulation at the corresponding column
            if len(snow_accumulation[0]) < 8:
                for row in range(8):
                    snow_accumulation[row][x] += 1
        flake[0] = random.randint(0, screen_width)
        flake[1] = random.randint(0, 8)

def clear_snow():
    for row in range(8):
        for x in range(screen_width):
            snow_accumulation[row][x] = max(0, snow_accumulation[row][x] - 1)

# Main loop
running = True
clock = pygame.time.Clock()

while running:
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            running = False

    # Handle wind and blizzards
    wind = random.randint(-blizzard_factor, blizzard_factor)
    for flake in snowflakes:
        x, y, speed, angle, color, thickness = flake

        # Update the position based on speed and direction
        x += math.cos(angle) * speed
        y += math.sin(angle) * speed

        # Add wind effect
        x += wind

        if y >= screen_height or x >= screen_width or x < 0:
            x = random.randint(0, screen_width)
            y = 0
            speed = random.uniform(1, 3)
            angle = random.uniform(math.pi / 6, 5 * math.pi / 6)
            thickness = random.randint(1, 3)

        flake[0] = x
        flake[1] = y
        flake[2] = speed
        flake[3] = angle
        flake[5] = thickness

    # Clear the screen
    screen.fill((0, 0, 0))

    # Draw accumulated snow
    for row, y_values in enumerate(snow_accumulation):
        for x, depth in enumerate(y_values):
            for _ in range(depth):
                pygame.draw.circle(screen, WHITE, (x, screen_height - 1 - depth), 2)

    # Draw snowflakes
    draw_snowflakes()

    pygame.display.flip()
    clock.tick(60)
    clear_snow()

pygame.quit()
