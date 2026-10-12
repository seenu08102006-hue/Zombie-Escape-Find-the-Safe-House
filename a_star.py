import heapq
from typing import List, Tuple, Optional

Position = Tuple[int, int]


def heuristic(a: Position, b: Position) -> int:
    return abs(a[0] - b[0]) + abs(a[1] - b[1])


def reconstruct_path(came_from: dict, current: Position) -> List[Position]:
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
    """
    rows = len(grid)
    cols = len(grid[0]) if rows > 0 else 0

    if not grid or not (0 <= start[0] < rows and 0 <= start[1] < cols):
        return None
    if not (0 <= goal[0] < rows and 0 <= goal[1] < cols):
        return None
    if grid[start[0]][start[1]] == 1 or grid[goal[0]][goal[1]] == 1:
        return None

    open_heap: List[Tuple[int, int, Position]] = []
    heapq.heappush(open_heap, (0, 0, start))

    came_from: dict[Position, Position] = {}
    g_score = {start: 0}
    f_score = {start: heuristic(start, goal)}

    directions = [(-1, 0), (1, 0), (0, -1), (0, 1)]

    while open_heap:
        _, _, current = heapq.heappop(open_heap)

        if current == goal:
            return reconstruct_path(came_from, current)

        row, col = current

        for dr, dc in directions:
            nr = row + dr
            nc = col + dc
            neighbor = (nr, nc)

            if nr < 0 or nr >= rows or nc < 0 or nc >= cols:
                continue
            if grid[nr][nc] == 1:
                continue

            tentative_g_score = g_score[current] + 1
            if tentative_g_score < g_score.get(neighbor, float("inf")):
                came_from[neighbor] = current
                g_score[neighbor] = tentative_g_score
                total_cost = tentative_g_score + heuristic(neighbor, goal)
                f_score[neighbor] = total_cost
                heapq.heappush(open_heap, (total_cost, tentative_g_score, neighbor))

    return None


if __name__ == "__main__":
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
