from __future__ import annotations

import copy
import html
import random
from collections import deque
from dataclasses import dataclass, field
from threading import Event
from typing import Optional

import reacton.ipyvuetify as v
import solara

from a_star import Position, a_star

ALGORITHMS = ("A*", "BFS", "DFS")


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
PLAYER_ICON = (
    '<svg class="game-icon player-icon" viewBox="0 0 24 24" aria-hidden="true">'
    '<path d="M7 10h3v7H7z" fill="#c77c42"/>'
    '<circle cx="12" cy="5.5" r="3.2" fill="#f2bd8d"/>'
    '<path d="M8.8 5a3.25 3.25 0 0 1 6.4 0v1H8.8z" fill="#423632"/>'
    '<path d="M8 9.5h8l1.5 7H6.5z" fill="#63c6a7"/>'
    '<path d="M9 16h2v5H8.5zM13 16h2l.5 5h-2.5z" fill="#d9e5dc"/>'
    '<path d="M9 11.5h6" stroke="#ffe29a" stroke-width="1.2"/>'
    '</svg>'
)
HOUSE_ICON = (
    '<svg class="game-icon house-icon" viewBox="0 0 24 24" aria-hidden="true">'
    '<path d="M2.5 11 12 3l9.5 8v2H2.5z" fill="#f1a65b"/>'
    '<path d="M5 11h14v10H5z" fill="#e8d1a4"/>'
    '<path d="M10 14h4v7h-4z" fill="#76503a"/>'
    '<path d="M6.5 13h2v2h-2zM15.5 13h2v2h-2z" fill="#6c9c96"/>'
    '<path d="M17 4h2v5l-2-1z" fill="#bac9c2"/>'
    '</svg>'
)


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
    algorithm: str = "A*"
    started: bool = False
    has_moved: bool = False
    route_visible: bool = True
    paused: bool = False
    ended: Optional[str] = None
    message: str = ""
    rng: random.Random = field(default_factory=random.Random, repr=False)


def path_on(walls: list[list[bool]], start: Position, goal: Position,
            blocked: set[Position] | None = None, algorithm: str = "A*") -> list[Position]:
    blocked = blocked or set()
    grid = [
        [int(walls[y][x] or (x, y) in blocked) for x in range(len(walls[0]))]
        for y in range(len(walls))
    ]
    if algorithm == "A*":
        path = a_star(grid, (start[1], start[0]), (goal[1], goal[0]))
        return [(x, y) for y, x in path] if path else []
    if algorithm not in ("BFS", "DFS"):
        raise ValueError(f"Unknown pathfinding algorithm: {algorithm}")

    if walls[start[1]][start[0]] or walls[goal[1]][goal[0]]:
        return []
    pending = deque([start])
    previous: dict[Position, Position | None] = {start: None}
    while pending:
        current = pending.popleft() if algorithm == "BFS" else pending.pop()
        if current == goal:
            break
        neighbors = open_neighbors(walls, current)
        if algorithm == "DFS":
            neighbors.reverse()
        for neighbor in neighbors:
            if neighbor in blocked or neighbor in previous:
                continue
            previous[neighbor] = current
            pending.append(neighbor)

    if goal not in previous:
        return []
    path: list[Position] = []
    current: Position | None = goal
    while current is not None:
        path.append(current)
        current = previous[current]
    path.reverse()
    return path


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


def distances_from(
    walls: list[list[bool]],
    start: Position,
    blocked: set[Position] | None = None,
) -> dict[Position, int]:
    blocked = blocked or set()
    distances = {start: 0}
    queue = deque([start])
    while queue:
        current = queue.popleft()
        for neighbor in open_neighbors(walls, current):
            if neighbor not in blocked and neighbor not in distances:
                distances[neighbor] = distances[current] + 1
                queue.append(neighbor)
    return distances


def ensure_alternate_route(
    walls: list[list[bool]],
    start: Position,
    goal: Position,
    blocked: set[Position],
) -> bool:
    route = path_on(walls, start, goal, blocked)
    if len(route) < 5:
        return False

    height, width = len(walls), len(walls[0])
    for index in range(1, len(route) - 3):
        first, middle, last = route[index:index + 3]
        if first[1] == middle[1] == last[1]:
            offsets = ((0, -1), (0, 1))
        elif first[0] == middle[0] == last[0]:
            offsets = ((-1, 0), (1, 0))
        else:
            continue

        for dx, dy in offsets:
            bypass = [
                (x + dx, y + dy)
                for x, y in (first, middle, last)
            ]
            if any(
                not (0 < x < width - 1 and 0 < y < height - 1)
                or (x, y) in blocked
                for x, y in bypass
            ):
                continue

            walls_before = [walls[y][x] for x, y in bypass]
            for x, y in bypass:
                walls[y][x] = False
            alternate = path_on(walls, start, goal, blocked | {middle})
            if alternate:
                return True
            for (x, y), was_wall in zip(bypass, walls_before):
                walls[y][x] = was_wall

    return False


def trap_count(level: int) -> int:
    if level <= 0:
        raise ValueError("Level must be a positive integer.")
    return 3 if level < 5 else min(8, level - 1)


def start_level(level: int, score: int, seed: int) -> Game:
    if level <= 0:
        raise ValueError("Level must be a positive integer.")
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
    if not ensure_alternate_route(walls, start, house, traps):
        raise RuntimeError(f"Could not create two safe routes for level {level}.")
    exact_path = path_on(walls, start, house, traps)
    if not exact_path:
        raise RuntimeError(f"Could not find a bomb-free route for level {level}.")

    from_start = distances_from(walls, start)
    from_house = distances_from(walls, house, traps)
    player_house_distance = from_house[start]
    safe_tiles = set(exact_path)
    trailing_options = [
        (x, y)
        for y in range(1, height - 1)
        for x in range(1, width - 1)
        if not walls[y][x]
        and from_house.get((x, y), 0) > player_house_distance
        and (x, y) not in safe_tiles
        and (x, y) not in traps
    ]

    if not trailing_options:
        start_x, start_y = start
        adjacent_tiles = (
            (start_x, start_y - 1),
            (start_x, start_y + 1),
            (start_x - 1, start_y),
            (start_x + 1, start_y),
        )
        for tile in adjacent_tiles:
            x, y = tile
            if (
                not (0 < x < width - 1 and 0 < y < height - 1)
                or not walls[y][x]
                or tile in traps
            ):
                continue
            walls[y][x] = False
            updated_from_house = distances_from(walls, house, traps)
            if updated_from_house.get(tile, -1) > updated_from_house[start]:
                from_house = updated_from_house
                from_start = distances_from(walls, start)
                exact_path = path_on(walls, start, house, traps)
                safe_tiles = set(exact_path)
                trailing_options = [tile]
                break
            walls[y][x] = True

    if not trailing_options:
        for tile in ((0, 1), (1, 0)):
            x, y = tile
            if tile in traps:
                continue
            walls[y][x] = False
            updated_from_house = distances_from(walls, house, traps)
            if updated_from_house.get(tile, -1) > updated_from_house[start]:
                from_house = updated_from_house
                from_start = distances_from(walls, start)
                exact_path = path_on(walls, start, house, traps)
                safe_tiles = set(exact_path)
                trailing_options = [tile]
                break
            walls[y][x] = True

    if not trailing_options:
        raise RuntimeError(f"Could not create a trailing zombie spawn for level {level}.")

    closest_distance = min(from_start[tile] for tile in trailing_options)
    nearby_spawn_options = [
        tile for tile in trailing_options
        if from_start[tile] <= closest_distance + 4
    ]
    rng.shuffle(nearby_spawn_options)
    zombie_count = min(max(1, level), 5, len(nearby_spawn_options))
    zombies = [Zombie(tile, tile) for tile in nearby_spawn_options[:zombie_count]]

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
        message="Choose a pathfinding algorithm and press Start game.",
        rng=rng,
    )


def current_route(game: Game) -> list[Position]:
    occupied = {zombie.position for zombie in game.zombies}
    safe_route = path_on(
        game.walls, game.player, game.house, game.traps | occupied, game.algorithm
    )
    if safe_route:
        return safe_route

    return path_on(game.walls, game.player, game.house, game.traps, game.algorithm)


def no_path_message(algorithm: str) -> str:
    alternatives = [name for name in ALGORITHMS if name != algorithm]
    return (
        f"{algorithm} cannot find a safe path. Choose one of the other algorithms: "
        f"{alternatives[0]} or {alternatives[1]}."
    )


def move_zombies(game: Game) -> None:
    occupied = {zombie.position for zombie in game.zombies}
    distance_to_house = distances_from(game.walls, game.house, game.traps)
    player_house_distance = distance_to_house.get(game.player)
    if player_house_distance is None:
        raise RuntimeError("Player has no safe path to the house.")

    for zombie in game.zombies:
        occupied.discard(zombie.position)
        options = [
            tile for tile in open_neighbors(game.walls, zombie.position)
            if tile != game.house
            and tile not in game.traps
            and tile not in occupied
        ]
        zombie.previous = zombie.position
        if options:
            zombie_house_distance = distance_to_house.get(zombie.position)
            if zombie_house_distance is None:
                raise RuntimeError("Zombie has no safe path through the maze.")

            distances_to_player = distances_from(
                game.walls,
                game.player,
                game.traps | occupied,
            )
            if zombie_house_distance <= player_house_distance:
                retreat_options = [
                    tile for tile in options
                    if distance_to_house.get(tile, -1) > zombie_house_distance
                ]
                if retreat_options:
                    best_distance = min(
                        distances_to_player.get(tile, float("inf"))
                        for tile in retreat_options
                    )
                    best_options = [
                        tile for tile in retreat_options
                        if distances_to_player.get(tile, float("inf")) == best_distance
                    ]
                    zombie.position = game.rng.choice(best_options)
                occupied.add(zombie.position)
                continue

            chase_path = path_on(
                game.walls,
                zombie.position,
                game.player,
                game.traps | occupied | {game.house},
            )
            trailing_options = [
                tile for tile in options
                if tile == game.player
                or distance_to_house.get(tile, -1) > player_house_distance
            ]
            if len(chase_path) > 1 and chase_path[1] in trailing_options:
                zombie.position = chase_path[1]
            elif trailing_options:
                best_distance = min(
                    distances_to_player.get(tile, float("inf"))
                    for tile in trailing_options
                )
                best_options = [
                    tile for tile in trailing_options
                    if distances_to_player.get(tile, float("inf")) == best_distance
                ]
                zombie.position = game.rng.choice(best_options)
        occupied.add(zombie.position)


def end_game(game: Game, message: str, outcome: str = "lost") -> None:
    game.ended = outcome
    game.message = message


def take_turn(game: Game, direction: str | None) -> None:
    if not game.started or game.ended or game.paused:
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
        game.has_moved = True
        if game.player in game.traps:
            end_game(game, "You stepped on a bomb. Game over. Try again.")
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


def board_markup(game: Game) -> str:
    route = set(current_route(game)) if game.route_visible else set()
    zombies = {zombie.position for zombie in game.zombies}
    tiles = []
    for y, row in enumerate(game.walls):
        for x, wall in enumerate(row):
            point = (x, y)
            if point == game.player:
                cell, kind = PLAYER_ICON, "player"
            elif point in zombies:
                cell, kind = "🧟", "zombie"
            elif point == game.house:
                cell, kind = HOUSE_ICON, "house"
            elif point in game.traps:
                cell, kind = "💣", "bomb"
            elif wall:
                cell, kind = "", "wall"
            elif point in route:
                cell, kind = "", "route"
            else:
                cell, kind = "", "floor"
            tiles.append(
                f'<div class="maze-tile {kind}" role="gridcell">{cell}</div>'
            )
    return (
        f'<div class="maze-board" role="grid" aria-label="Maze, level {game.level}" '
        f'style="grid-template-columns:repeat({len(game.walls[0])}, minmax(0, 1fr));">'
        f'{"".join(tiles)}</div>'
    )


GAME_STYLES = """
html, body, #root, .solara-app, .v-application, .v-application__wrap,
.v-main, .v-main__wrap {
    background: #0b1110 !important;
    color: #e8efeb;
}
.v-application__wrap div[style*="position: absolute"][style*="bottom: 0px"] {
    display: none !important;
}
body { margin: 0; }
.zombie-game {
    box-sizing: border-box;
    width: min(100%, 1120px);
    min-height: 100vh;
    margin: 0 auto;
    padding: 30px 32px 40px;
    background: #0b1110;
    color: #e8efeb;
    font-family: Inter, Arial, sans-serif;
    outline: none;
}
.zombie-game * { box-sizing: border-box; }
.zombie-game:focus-visible { outline: 2px solid #7cae42; outline-offset: -2px; }
.game-heading {
    display: flex; align-items: center; justify-content: space-between;
    flex-wrap: wrap; gap: 18px 24px; margin-bottom: 22px;
}
.game-eyebrow {
    color: #b7f34a; font: 800 13px/1.3 Inter, sans-serif;
    letter-spacing: .2em; text-transform: uppercase; margin-bottom: 8px;
}
.game-title {
    color: #f4f7f3; font: 800 clamp(30px, 4vw, 44px)/1 'Barlow Condensed', Inter, sans-serif;
    letter-spacing: -.025em; margin: 0 0 8px;
}
.game-subtitle { color: #9aa9a2; font-size: 14px; margin: 0; }
.game-heading-actions {
    display: flex; align-items: center; flex-wrap: wrap; gap: 8px;
    min-width: 0; max-width: 100%;
}
.zombie-game .game-heading-actions { background: transparent !important; }
.game-stats {
    display: grid; grid-template-columns: repeat(5, minmax(90px, 1fr));
    gap: 10px; margin: 0 0 18px;
}
.game-stat {
    min-height: 68px; padding: 12px 14px; border: 1px solid #293731;
    border-radius: 12px; background: #111a17;
}
.game-stat-label {
    display: block; color: #94a59c; font: 700 10px/1.3 Inter, sans-serif;
    letter-spacing: .15em; text-transform: uppercase; margin-bottom: 7px;
}
.game-stat-value { color: #f0f4ef; font: 800 18px/1 'Barlow Condensed', Inter, sans-serif; }
.maze-frame {
    padding: 10px; border: 1px solid #31443d; border-radius: 15px;
    background: #131d1a; box-shadow: 0 14px 42px #0005;
}
.maze-board {
    display: grid; width: 100%; overflow: hidden;
    border: 1px solid #435a60; border-radius: 9px;
    background: #293b40; gap: 2px; padding: 2px;
}
.maze-tile {
    position: relative; display: flex; align-items: center; justify-content: center;
    min-width: 0; aspect-ratio: 1; overflow: hidden;
    color: white; font: 700 clamp(10px, 1.5vw, 18px)/1 Arial, sans-serif;
}
.maze-tile.wall {
    border: 1px solid #6d8992; border-radius: 2px;
    background: linear-gradient(180deg, #506770 0 43%, #33494f 44% 54%, #49616a 55% 100%);
    box-shadow: inset 0 1px #a0b1b5, inset 0 -1px #25383d;
}
.maze-tile.floor { background: #26383d; }
.maze-tile.route {
    background: #075185; box-shadow: inset 0 0 0 2px #078cf4;
}
.maze-tile.player, .maze-tile.zombie, .maze-tile.house, .maze-tile.bomb {
    z-index: 1; filter: drop-shadow(0 2px 2px #0009);
}
.maze-tile.player { background: #174b50; }
.maze-tile.zombie { background: #3b4c35; }
.maze-tile.house { background: #65513b; }
.maze-tile.bomb { color: #ff9751; background: #4c342b; }
.game-icon { display: block; width: 90%; height: 90%; }
.game-below {
    display: grid; grid-template-columns: minmax(0, 1fr) auto;
    align-items: center; gap: 20px; margin-top: 14px;
}
.game-legend { display: flex; flex-wrap: wrap; gap: 8px 16px; color: #a7b5af; font-size: 12px; }
.legend-item { display: inline-flex; align-items: center; gap: 6px; }
.legend-icon {
    display: inline-flex; width: 22px; height: 22px; align-items: center; justify-content: center;
    border: 1px solid #354740; border-radius: 5px; background: #17221e; font-size: 13px;
}
.legend-icon .game-icon { width: 18px; height: 18px; }
.game-controls {
    display: flex; align-items: center; justify-content: space-between;
    flex-wrap: wrap; gap: 12px; max-width: 100%; margin-top: 20px;
}
.game-controls > * { min-width: 0; max-width: 100%; }
.game-move-controls { display: grid; grid-template-columns: repeat(3, 48px); gap: 6px; }
.game-move-controls .v-btn:first-child { grid-column: 2; }
.game-move-controls .v-btn:nth-child(2) { grid-column: 1; grid-row: 2; }
.game-move-controls .v-btn:nth-child(3) { grid-column: 3; grid-row: 2; }
.game-move-controls .v-btn:nth-child(4) { grid-column: 2; grid-row: 3; }
.game-message {
    margin-top: 14px; padding: 12px 15px; border: 1px solid #30423a;
    border-radius: 9px; background: #111a17; color: #c5d1ca; font-size: 13px;
}
.game-help { margin-top: 16px; color: #8d9e95; font-size: 12px; line-height: 1.6; }
.algorithm-picker {
    width: 100%; max-width: 100%; min-width: 0; flex-wrap: wrap;
    align-items: center; gap: 10px; margin-top: 10px;
    padding: 10px; border: 1px solid #7cae42; border-radius: 12px;
    background: linear-gradient(135deg, #1b2b20, #111a17);
    box-shadow: 0 0 24px #7cae4222;
}
.algorithm-picker .v-input {
    flex: 0 1 210px; width: 210px; min-width: 0; max-width: 100%;
}
.algorithm-picker .v-field {
    min-height: 42px; border: 1px solid #718a5e; border-radius: 9px;
    background: #0d1511; color: #f0f4ef;
}
.algorithm-picker .v-label,
.algorithm-picker .v-field__input,
.algorithm-picker .v-icon { color: #d7f5ae !important; opacity: 1; }
.algorithm-picker .v-label { font-weight: 700; }
.zombie-game .start-game-button,
.zombie-game .start-game-button .v-btn {
    min-height: 42px; max-width: 100%; padding: 0 16px;
    border: 2px solid #d5ff83 !important; border-radius: 9px !important;
    background: #b7f34a !important; color: #15200e !important;
    font: 800 13px Inter, sans-serif !important; letter-spacing: .04em !important;
    box-shadow: 0 3px 12px #9de83e44 !important;
}
.zombie-game .start-game-button:hover,
.zombie-game .start-game-button .v-btn:hover { filter: brightness(1.12); }
.zombie-game .game-button, .zombie-game .game-button .v-btn {
    min-height: 42px; border: 1px solid #34483e !important; border-radius: 9px !important;
    background: #17221d !important; color: #e8efeb !important;
    font: 700 12px Inter, sans-serif !important; letter-spacing: .02em !important;
    box-shadow: none !important;
}
.zombie-game .game-button.primary, .zombie-game .game-button.primary .v-btn {
    border-color: #7cae42 !important; background: #b7f34a !important; color: #15200e !important;
}
.zombie-game .game-button:hover, .zombie-game .game-button .v-btn:hover { filter: brightness(1.12); }
@media (max-width: 700px) {
    .zombie-game { padding: 20px 12px 28px; }
    .game-heading { align-items: flex-start; flex-direction: column; gap: 14px; }
    .game-heading-actions { width: 100%; }
    .game-heading-actions > * { flex: 0 1 auto; min-width: 0; }
    .algorithm-picker { align-items: stretch; }
    .algorithm-picker > * { min-width: 0; max-width: 100%; }
    .algorithm-picker .v-input { flex: 0 1 210px; width: min(210px, 100%); }
    .zombie-game .start-game-button, .zombie-game .start-game-button .v-btn {
        width: auto; max-width: 100%; justify-content: center;
    }
    .game-stats { grid-template-columns: repeat(3, minmax(0, 1fr)); gap: 7px; }
    .game-stat { min-height: 60px; padding: 10px; }
    .game-stat-value { font-size: 16px; }
    .game-controls { align-items: flex-start; flex-direction: column-reverse; }
    .game-below { grid-template-columns: 1fr; }
}
"""


@solara.component
def Page():
    initial_game = solara.use_memo(lambda: start_level(1, 0, random.randrange(2**32)), [])
    game = solara.use_reactive(initial_game)
    ai_running, set_ai_running = solara.use_state(False)

    def change(action):
        updated = copy.deepcopy(game.value)
        action(updated)
        game.value = updated

    def move(direction: str) -> None:
        set_ai_running(False)
        change(lambda state: take_turn(state, direction))

    def wait() -> None:
        set_ai_running(False)
        change(lambda state: take_turn(state, None))

    def restart() -> None:
        set_ai_running(False)
        current = game.value
        restarted = start_level(current.level, current.score, current.seed)
        restarted.algorithm = current.algorithm
        restarted.started = current.started
        restarted.message = (
            f"Level {restarted.level} restarted with {restarted.algorithm}. Find the safe house!"
            if restarted.started
            else f"{restarted.algorithm} selected. Start the game when you are ready."
        )
        game.value = restarted

    def next_level() -> None:
        set_ai_running(False)
        current = game.value
        next_game = start_level(current.level + 1, current.score, current.seed)
        next_game.algorithm = current.algorithm
        next_game.message = (
            f"Level {next_game.level}: choose a pathfinding algorithm and press Start game."
        )
        game.value = next_game

    def select_algorithm(algorithm: str) -> None:
        def update(state: Game) -> None:
            state.algorithm = algorithm
            if not path_on(state.walls, state.player, state.house, state.traps, algorithm):
                state.message = no_path_message(algorithm)
            else:
                state.message = f"{algorithm} selected. Start the game when you are ready."

        change(update)

    def start_game() -> None:
        def update(state: Game) -> None:
            if not path_on(
                state.walls, state.player, state.house, state.traps, state.algorithm
            ):
                state.message = no_path_message(state.algorithm)
                return
            state.started = True
            state.message = f"Game started with {state.algorithm}. Find the safe house!"

        change(update)

    def handle_keydown(_widget, _event, data) -> None:
        key = data.get("key", data.get("code")) if isinstance(data, dict) else None
        if key in (" ", "Space", "Spacebar"):
            if game.value.ended == "won" and not data.get("repeat", False):
                next_level()
            return

        direction = {
            "ArrowUp": "Up",
            "ArrowDown": "Down",
            "ArrowLeft": "Left",
            "ArrowRight": "Right",
            "Up": "Up",
            "Down": "Down",
            "Left": "Left",
            "Right": "Right",
        }.get(key)
        if direction is not None:
            move(direction)

    def run_ai(cancel: Event) -> None:
        if not ai_running:
            return
        while not cancel.is_set():
            state = game.value
            if state.ended:
                set_ai_running(False)
                return
            if not state.started or state.paused:
                cancel.wait(0.1)
                continue

            route = current_route(state)
            if len(route) < 2:
                change(lambda current: setattr(
                    current, "message", no_path_message(current.algorithm)
                ))
                set_ai_running(False)
                return

            current, following = route[:2]
            delta = (following[0] - current[0], following[1] - current[1])
            direction = next(
                (name for name, step in DIRECTIONS.items() if step == delta),
                None,
            )
            if direction is None:
                raise RuntimeError(f"AI route contains a non-adjacent step: {current} to {following}.")

            change(lambda current_state: take_turn(current_state, direction))
            if game.value.ended:
                set_ai_running(False)
                return
            cancel.wait(0.4)

    solara.use_thread(run_ai, dependencies=[ai_running])

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
    solara.Style(GAME_STYLES)
    status = "Escaped!" if state.ended == "won" else "Game Over" if state.ended == "lost" else "Open"
    can_move = state.started and state.ended is None and not state.paused
    game_root = solara.Div(
        classes=["zombie-game"],
        attributes={"tabindex": "0"},
    )
    with game_root:
        with solara.Div(classes=["game-heading"]):
            solara.HTML(
                unsafe_innerHTML=(
                    f'<div class="game-eyebrow">Level {state.level} · '
                    f'{html.escape(location)}</div><h1 class="game-title">Zombie Escape</h1>'
                    '<p class="game-subtitle">Scout the maze. Find the safe house. '
                    'Don’t let the horde catch you.</p>'
                )
            )
            if not state.has_moved and state.ended is None:
                solara.HTML(
                    unsafe_innerHTML=(
                        '<div class="game-eyebrow" style="margin:18px 0 0">'
                        'CHOOSE YOUR PATHFINDING ALGORITHM</div>'
                    )
                )
                with solara.Row(classes=["algorithm-picker"], gap="10px"):
                    solara.Select(
                        label="Choose algorithm",
                        value=state.algorithm,
                        values=list(ALGORITHMS),
                        on_value=select_algorithm,
                    )
                    solara.Button(
                        "Start game",
                        on_click=start_game,
                        classes=["start-game-button"],
                    )
            with solara.Row(classes=["game-heading-actions"], gap="10px"):
                solara.Button(
                    "Stop AI" if ai_running else "Start AI",
                    on_click=lambda: set_ai_running(not ai_running),
                    disabled=not state.started or state.ended is not None,
                    classes=["game-button", "primary"],
                )
                solara.Button(
                    "Safe path" if not state.route_visible else "Hide path",
                    on_click=toggle_route,
                    classes=["game-button"],
                )
                solara.Button(
                    "Resume" if state.paused else "Pause",
                    on_click=toggle_pause,
                    disabled=not state.started or state.ended is not None,
                    classes=["game-button"],
                )
                solara.Button("Restart", on_click=restart, classes=["game-button"])
        solara.HTML(
            unsafe_innerHTML=(
                '<div class="game-stats">'
                f'<div class="game-stat"><span class="game-stat-label">Level</span>'
                f'<span class="game-stat-value">{state.level}</span></div>'
                f'<div class="game-stat"><span class="game-stat-label">Zombies</span>'
                f'<span class="game-stat-value">{len(state.zombies)}</span></div>'
                f'<div class="game-stat"><span class="game-stat-label">Safe house</span>'
                f'<span class="game-stat-value">{status}</span></div>'
                f'<div class="game-stat"><span class="game-stat-label">Algorithm</span>'
                f'<span class="game-stat-value">{html.escape(state.algorithm)}</span></div>'
                f'<div class="game-stat"><span class="game-stat-label">Score</span>'
                f'<span class="game-stat-value">{state.score}</span></div>'
                '</div>'
            )
        )
        with solara.Div(classes=["maze-frame"]):
            solara.HTML(unsafe_innerHTML=board_markup(state))
        with solara.Div(classes=["game-below"]):
            solara.HTML(
                unsafe_innerHTML=(
                    '<div class="game-legend">'
                    f'<span class="legend-item"><span class="legend-icon">{PLAYER_ICON}</span>You</span>'
                    '<span class="legend-item"><span class="legend-icon">🧟</span>Zombie</span>'
                    f'<span class="legend-item"><span class="legend-icon">{HOUSE_ICON}</span>Safe house</span>'
                    '<span class="legend-item"><span class="legend-icon">💣</span>Bomb</span>'
                    '<span class="legend-item"><span class="legend-icon" style="color:#078cf4">+</span>Safe route</span>'
                    '</div>'
                )
            )
            if state.ended == "won":
                solara.Button("Next level", on_click=next_level, classes=["game-button", "primary"])
            elif state.ended == "lost":
                solara.Button("Try again", on_click=restart, classes=["game-button", "primary"])
        with solara.Div(classes=["game-controls"]):
            with solara.Row(classes=["game-heading-actions"], gap="8px"):
                solara.Button("Wait", on_click=wait, disabled=not can_move, classes=["game-button"])
                solara.Button("Restart level", on_click=restart, classes=["game-button"])
            with solara.Div(classes=["game-move-controls"]):
                solara.Button("↑", on_click=lambda: move("Up"), disabled=not can_move, classes=["game-button"])
                solara.Button("←", on_click=lambda: move("Left"), disabled=not can_move, classes=["game-button"])
                solara.Button("→", on_click=lambda: move("Right"), disabled=not can_move, classes=["game-button"])
                solara.Button("↓", on_click=lambda: move("Down"), disabled=not can_move, classes=["game-button"])
        solara.HTML(
            unsafe_innerHTML=(
                f'<div class="game-message">{html.escape(state.message)}</div>'
                '<div class="game-help"><strong>How to play:</strong> Click inside or Tab to focus the game, '
                'choose A*, BFS, or DFS and press Start game, then use the keyboard '
                'arrow keys or direction buttons. Select Start AI to have the computer follow the '
                f'current {html.escape(state.algorithm)} safe route automatically. Zombies patrol after each move or wait. The blue path avoids '
                'bombs and current zombie positions; it can change as they move.</div>'
            )
        )
    v.use_event(game_root, "keydown", handle_keydown)
