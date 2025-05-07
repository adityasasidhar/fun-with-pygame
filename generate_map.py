import random
from collections import deque

WIDTH, HEIGHT = 50, 50
TERRAINS = {
    "G": "Grass",     # walkable
    "B": "Bush",      # walkable
    "S": "Stone",     # obstacle
    "R": "River",     # not walkable
}
WALKABLE = {"G", "B"}
NON_WALKABLE = {"S", "R"}

def empty_map():
    return [["G" for _ in range(WIDTH)] for _ in range(HEIGHT)]

def add_river(grid, bends=6, width=2):
    x = random.randint(0, WIDTH - 1)
    y = 0
    direction = (0, 1)  # downward flow

    for _ in range(bends):
        dx = random.choice([-1, 0, 1])
        dy = random.choice([1, 1, 1])  # bias downward
        for _ in range(random.randint(5, 10)):
            x = max(1, min(WIDTH - 2, x + dx))
            y = max(1, min(HEIGHT - 2, y + dy))
            for i in range(-width, width + 1):
                if 0 <= x + i < WIDTH and 0 <= y < HEIGHT:
                    grid[y][x + i] = "R"

def add_lake(grid, cx, cy, radius=3):
    for y in range(-radius, radius + 1):
        for x in range(-radius, radius + 1):
            if 0 <= cx + x < WIDTH and 0 <= cy + y < HEIGHT:
                if x*x + y*y <= radius * radius:
                    grid[cy + y][cx + x] = "R"

def add_lakes(grid, count=3):
    for _ in range(count):
        x = random.randint(5, WIDTH - 6)
        y = random.randint(5, HEIGHT - 6)
        r = random.randint(2, 4)
        add_lake(grid, x, y, r)

def scatter_terrain(grid, tile, density):
    for y in range(HEIGHT):
        for x in range(WIDTH):
            if grid[y][x] == "G" and random.random() < density:
                grid[y][x] = tile

def flood_fill(grid, start):
    visited = set()
    queue = deque([start])
    while queue:
        x, y = queue.popleft()
        if (x, y) in visited: continue
        visited.add((x, y))
        for dx, dy in [(-1,0),(1,0),(0,-1),(0,1)]:
            nx, ny = x + dx, y + dy
            if 0 <= nx < WIDTH and 0 <= ny < HEIGHT:
                if grid[ny][nx] in WALKABLE:
                    queue.append((nx, ny))
    return visited

def is_walkable_map(grid, start=(0,0), min_coverage=0.85):
    if grid[start[1]][start[0]] not in WALKABLE:
        return False
    visited = flood_fill(grid, start)
    total_walkable = sum(row.count("G") + row.count("B") for row in grid)
    return len(visited) >= int(total_walkable * min_coverage)

def generate_good_map():
    attempts = 0
    while True:
        attempts += 1
        grid = empty_map()
        add_river(grid)
        add_lakes(grid)
        scatter_terrain(grid, "B", 0.08)
        scatter_terrain(grid, "S", 0.06)

        if is_walkable_map(grid):
            print(f"[✓] Map generated after {attempts} attempt(s)")
            return grid

def save_map(grid, filename="properties/map.txt"):
    with open(filename, "w") as f:
        for row in grid:
            f.write("".join(row) + "\n")

