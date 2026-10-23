"""A* pathfinding on a grid of walkable (0) and blocked (1) cells."""

import heapq
from typing import List, Tuple, Optional

# A grid coordinate. In this module it is (row, col); app.py converts to and from (x, y).
Position = Tuple[int, int]


def heuristic(a: Position, b: Position) -> int:
    """Return the Manhattan distance between a and b, an estimate of the steps left to the goal."""
    return abs(a[0] - b[0]) + abs(a[1] - b[1])


def reconstruct_path(came_from: dict, current: Position) -> List[Position]:
    """Walk the came_from links back from the goal and return the path from start to goal."""
    path = [current]
    while current in came_from:
        current = came_from[current]
        path.append(current)
    path.reverse()
    return path


def a_star(grid: List[List[int]], start: Position, goal: Position) -> Optional[List[Position]]:
    """
    Finds a path from start to goal using the A* algorithm.

    grid: 0 = walkable cell, 1 = blocked cell
    start, goal: (row, col) tuples
    Returns the shortest path as a list of cells, or None when no path exists.
    """
    # Reject empty grids, out-of-bounds or blocked endpoints before searching.
    if not grid or not grid[0]:
        return None

    rows = len(grid)
    cols = len(grid[0])

    if not (0 <= start[0] < rows and 0 <= start[1] < cols):
        return None
    if not (0 <= goal[0] < rows and 0 <= goal[1] < cols):
        return None
    if grid[start[0]][start[1]] == 1 or grid[goal[0]][goal[1]] == 1:
        return None
    if start == goal:
        return [start]

    # The open set is a min-heap of (estimated total cost, steps so far, cell);
    # ties on total cost are broken by the smaller step count.
    open_heap: List[Tuple[int, int, Position]] = []
    heapq.heappush(open_heap, (0, 0, start))

    came_from: dict[Position, Position] = {}
    g_score = {start: 0}  # cheapest known number of steps from start to each cell
    f_score = {start: heuristic(start, goal)}  # g_score plus the heuristic estimate

    # Moves are limited to up, down, left and right.
    directions = [(-1, 0), (1, 0), (0, -1), (0, 1)]

    while open_heap:
        # Expand the cell with the lowest estimated total cost.
        _, _, current = heapq.heappop(open_heap)

        if current == goal:
            return reconstruct_path(came_from, current)

        row, col = current

        for dr, dc in directions:
            nr = row + dr
            nc = col + dc
            neighbor = (nr, nc)

            # Skip cells outside the grid or blocked by a wall.
            if nr < 0 or nr >= rows or nc < 0 or nc >= cols:
                continue
            if grid[nr][nc] == 1:
                continue

            # Record the neighbor when this route to it is shorter than any found before.
            tentative_g_score = g_score[current] + 1
            if tentative_g_score < g_score.get(neighbor, float("inf")):
                came_from[neighbor] = current
                g_score[neighbor] = tentative_g_score
                total_cost = tentative_g_score + heuristic(neighbor, goal)
                f_score[neighbor] = total_cost
                heapq.heappush(open_heap, (total_cost, tentative_g_score, neighbor))

    # The open set ran out without reaching the goal.
    return None


if __name__ == "__main__":
    # Small demo: find a path through a 5 x 5 sample maze.
    maze = [
        [0, 0, 0, 0, 0],
        [0, 1, 1, 1, 0],
        [0, 0, 0, 1, 0],
        [0, 1, 0, 0, 0],
        [0, 0, 0, 1, 0],
    ]

    start = (0, 0)
    goal = (4, 4)

    path = a_star(maze, start, goal)
    if path is None:
        print("No path found.")
    else:
        print("Path found:", path)
