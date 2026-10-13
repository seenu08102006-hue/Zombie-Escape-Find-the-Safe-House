from __future__ import annotations

import copy
import random
from collections import deque
from dataclasses import dataclass, field
from typing import Optional

import solara

from a_star import Position, a_star


LOCATIONS = (
    "Overgrown Village",
    "Pinewood Forest",
    "Frozen Outpost",
    "Ashen City",
    "Toxic Marsh",
)
DIRECTIONS: dict[str, Position] = {
    "Up": (0, -1),
    "Down": (0, 1),
    "Left": (-1, 0),
    "Right": (1, 0),
}


@dataclass
class Zombie:
    position: Position
    home: Position
    previous: Optional[Position] = None


@dataclass
class Game:
    level: int
    score: int
    seed: int
    walls: list[list[bool]]
    player: Position
    house: Position
    zombies: list[Zombie]
    traps: set[Position]
    route: list[Position]
    exact_steps: int
    steps: int = 0
    route_visible: bool = True
    paused: bool = False
    ended: Optional[str] = None
    message: str = ""
    rng: random.Random = field(default_factory=random.Random, repr=False)


def path_on(walls: list[list[bool]], start: Position, goal: Position,
            blocked: set[Position] | None = None) -> list[Position]:
    blocked = blocked or set()
    grid = [
        [int(walls[y][x] or (x, y) in blocked) for x in range(len(walls[0]))]
        for y in range(len(walls))
    ]
    path = a_star(grid, (start[1], start[0]), (goal[1], goal[0]))
    return [(x, y) for y, x in path] if path else []


def open_neighbors(walls: list[list[bool]], point: Position) -> list[Position]:
    x, y = point
    candidates = ((x, y - 1), (x, y + 1), (x - 1, y), (x + 1, y))
    return [
        tile for tile in candidates
        if 0 <= tile[1] < len(walls)
        and 0 <= tile[0] < len(walls[0])
        and not walls[tile[1]][tile[0]]
    ]


def make_maze(width: int, height: int, rng: random.Random, level: int) -> list[list[bool]]:
    walls = [[True] * width for _ in range(height)]
    start = (1, 1)
    walls[start[1]][start[0]] = False
    stack: list[Position] = [start]
    while stack:
        x, y = stack[-1]
        options = [
            (x + dx * 2, y + dy * 2, dx, dy)
            for dx, dy in DIRECTIONS.values()
            if 0 < x + dx * 2 < width - 1 and 0 < y + dy * 2 < height - 1
            and walls[y + dy * 2][x + dx * 2]
        ]
        if not options:
            stack.pop()
            continue
        nx, ny, dx, dy = rng.choice(options)
        walls[y + dy][x + dx] = False
        walls[ny][nx] = False
        stack.append((nx, ny))

    loop_chance = max(0.02, 0.08 - (level - 1) * 0.003)
    for y in range(1, height - 1):
        for x in range(1, width - 1):
            if not walls[y][x] or (x % 2 == 0) == (y % 2 == 0):
                continue
            if rng.random() > loop_chance:
                continue
            neighbors = ((x - 1, y), (x + 1, y)) if x % 2 == 0 else ((x, y - 1), (x, y + 1))
            if all(not walls[ny][nx] for nx, ny in neighbors):
                walls[y][x] = False
    return walls


def add_detours(walls: list[list[bool]], start: Position, goal: Position) -> tuple[list[Position], list[Position]]:
    main_path = path_on(walls, start, goal)
    path_tiles = set(main_path)
    detours: list[Position] = []
    for index in range(1, len(main_path) - 1):
        previous, current, following = main_path[index - 1:index + 2]
        if previous[0] == following[0] or previous[1] == following[1]:
            continue
        detour = (previous[0] + following[0] - current[0], previous[1] + following[1] - current[1])
        x, y = detour
        if walls[y][x] and detour not in path_tiles and detour not in detours:
            detours.append(detour)
    for x, y in detours:
        walls[y][x] = False
    return main_path, detours


def distances_from(walls: list[list[bool]], start: Position) -> dict[Position, int]:
    distances = {start: 0}
    queue = deque([start])
    while queue:
        current = queue.popleft()
        for neighbor in open_neighbors(walls, current):
            if neighbor not in distances:
                distances[neighbor] = distances[current] + 1
                queue.append(neighbor)
    return distances


def trap_count(level: int) -> int:
    return 3 if level < 5 else min(8, level - 1)


def start_level(level: int, score: int, seed: int) -> Game:
    size_step = min((level - 1) // 3, 2)
    width, height = min(23, 19 + 2 * size_step), min(17, 13 + 2 * size_step)
    start, house = (1, 1), (width - 2, height - 2)
    rng = random.Random((seed + level * 92821 + 47311) & 0xFFFFFFFF)
    best: tuple[list[list[bool]], list[Position], list[Position]] | None = None
    for _ in range(32):
        walls = make_maze(width, height, rng, level)
        safe_path, detours = add_detours(walls, start, house)
        if best is None or len(detours) > len(best[2]):
            best = (walls, safe_path, detours)
        if len(detours) >= trap_count(level):
            best = (walls, safe_path, detours)
            break
    if best is None or len(best[2]) < trap_count(level):
        raise RuntimeError(f"Could not generate enough alternate route tiles for level {level}.")

    walls, safe_path, detours = best
    count = min(trap_count(level), len(detours))
    traps = {
        detours[min(len(detours) - 1, int((index + 0.5) * len(detours) / count))]
        for index in range(count)
    }
    exact_path = path_on(walls, start, house, traps)
    if not exact_path:
        raise RuntimeError(f"Could not find a bomb-free route for level {level}.")

    from_start = distances_from(walls, start)
    from_house = distances_from(walls, house)
    safe_tiles = set(exact_path)
    spawn_options = [
        (x, y)
        for y in range(1, height - 1)
        for x in range(1, width - 1)
        if not walls[y][x]
        and from_start.get((x, y), 0) >= 10
        and from_house.get((x, y), 0) >= 5
        and (x, y) not in safe_tiles
        and (x, y) not in traps
    ]
    rng.shuffle(spawn_options)
    zombie_count = 0 if level == 1 else min(level, 5, len(spawn_options))
    zombies = [Zombie(tile, tile) for tile in spawn_options[:zombie_count]]

    location = LOCATIONS[(level - 1) % len(LOCATIONS)]
    return Game(
        level=level,
        score=score,
        seed=seed,
        walls=walls,
        player=start,
        house=house,
        zombies=zombies,
        traps=traps,
        route=exact_path,
        exact_steps=len(exact_path) - 1,
        message=f"Level {level} · {location}. Reach the safe house without stepping on a bomb.",
        rng=rng,
    )


def current_route(game: Game) -> list[Position]:
    occupied = {zombie.position for zombie in game.zombies}
    return path_on(game.walls, game.player, game.house, game.traps | occupied)


def move_zombies(game: Game) -> None:
    occupied = {zombie.position for zombie in game.zombies}
    for zombie in game.zombies:
        occupied.discard(zombie.position)
        options = [
            tile for tile in open_neighbors(game.walls, zombie.position)
            if abs(tile[0] - zombie.home[0]) + abs(tile[1] - zombie.home[1]) <= 3
            and tile != game.house
            and tile not in game.traps
            and tile not in occupied
        ]
        forward = [tile for tile in options if tile != zombie.previous]
        if forward:
            options = forward
        zombie.previous = zombie.position
        if options:
            zombie.position = game.rng.choice(options)
        occupied.add(zombie.position)


def end_game(game: Game, message: str, outcome: str = "lost") -> None:
    game.ended = outcome
    game.message = message


def take_turn(game: Game, direction: str | None) -> None:
    if game.ended or game.paused:
        return
    if direction is not None:
        dx, dy = DIRECTIONS[direction]
        target = (game.player[0] + dx, game.player[1] + dy)
        if game.walls[target[1]][target[0]]:
            game.message = "A wall blocks the way."
            return
        if any(zombie.position == target for zombie in game.zombies):
            end_game(game, "A zombie caught you! Retry the level to try again.")
            return
        game.player = target
        game.steps += 1
        if game.player in game.traps:
            end_game(game, "BOOM! You stepped on a bomb trap. Retry the level to try again.")
            return
        if game.steps > game.exact_steps:
            end_game(game, f"You used more than the {game.exact_steps} steps available on the exact route.")
            return
        if game.player == game.house:
            game.score += game.level * 500
            end_game(game, f"Level {game.level} complete! You found the safe house.", "won")
            return
    move_zombies(game)
    if any(zombie.position == game.player for zombie in game.zombies):
        end_game(game, "A roaming zombie caught you! Retry the level to try again.")
    else:
        game.message = "You wait as the zombies patrol." if direction is None else "The zombies patrol nearby."


def board_text(game: Game) -> str:
    route = set(current_route(game)) if game.route_visible else set()
    zombies = {zombie.position for zombie in game.zombies}
    rows = []
    for y, row in enumerate(game.walls):
        cells = []
        for x, wall in enumerate(row):
            point = (x, y)
            if point == game.player:
                cell = "P"
            elif point in zombies:
                cell = "Z"
            elif point == game.house:
                cell = "H"
            elif point in game.traps:
                cell = "B"
            elif wall:
                cell = "#"
            elif point in route:
                cell = "+"
            else:
                cell = " "
            cells.append(cell)
        rows.append("".join(cells))
    return "\n".join(rows)


@solara.component
def Page():
    initial_game = solara.use_memo(lambda: start_level(1, 0, random.randrange(2**32)), [])
    game = solara.use_reactive(initial_game)

    def change(action):
        updated = copy.deepcopy(game.value)
        action(updated)
        game.value = updated

    def move(direction: str) -> None:
        change(lambda state: take_turn(state, direction))

    def wait() -> None:
        change(lambda state: take_turn(state, None))

    def restart() -> None:
        game.value = start_level(game.value.level, game.value.score, game.value.seed)

    def next_level() -> None:
        game.value = start_level(game.value.level + 1, game.value.score, game.value.seed)

    def toggle_pause() -> None:
        def update(state: Game) -> None:
            state.paused = not state.paused
            state.message = "Game paused." if state.paused else "Back in the maze."

        change(update)

    def toggle_route() -> None:
        def update(state: Game) -> None:
            state.route_visible = not state.route_visible
            state.message = "Safe path shown." if state.route_visible else "Safe path hidden."

        change(update)

    state = game.value
    location = LOCATIONS[(state.level - 1) % len(LOCATIONS)]
    solara.Title("Zombie Escape: Find the Safe House")
    solara.Markdown("# Zombie Escape")
    solara.Markdown(f"### Level {state.level} · {location}")
    solara.Markdown(
        f"**Zombies:** {len(state.zombies)}　 **Safe house:** Open　 "
        f"**Score:** {state.score}　 **Steps:** {state.steps}/{state.exact_steps}"
    )
    solara.Markdown(f"```text\n{board_text(state)}\n```")
    solara.Markdown("`P` You　 `Z` Zombie　 `H` Safe house　 `B` Bomb　 `+` Safe route　 `#` Wall")
    solara.Markdown(state.message)

    with solara.Row():
        solara.Button("↑ Up", on_click=lambda: move("Up"), disabled=state.ended is not None or state.paused)
    with solara.Row():
        solara.Button("← Left", on_click=lambda: move("Left"), disabled=state.ended is not None or state.paused)
        solara.Button("Wait", on_click=wait, disabled=state.ended is not None or state.paused)
        solara.Button("Right →", on_click=lambda: move("Right"), disabled=state.ended is not None or state.paused)
    with solara.Row():
        solara.Button("↓ Down", on_click=lambda: move("Down"), disabled=state.ended is not None or state.paused)
    with solara.Row():
        solara.Button("Safe path", on_click=toggle_route)
        solara.Button("Resume" if state.paused else "Pause", on_click=toggle_pause, disabled=state.ended is not None)
        solara.Button("Restart level", on_click=restart)
        if state.ended == "won":
            solara.Button("Next level", on_click=next_level)
        elif state.ended == "lost":
            solara.Button("Retry level", on_click=restart)

    solara.Markdown(
        "Move with the buttons. Zombies patrol within three tiles of their starting spots "
        "after each move or wait. The blue route avoids bombs and current zombie positions, "
        "but can change as they move."
    )
