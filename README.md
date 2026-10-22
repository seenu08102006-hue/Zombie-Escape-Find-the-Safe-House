# Zombie Escape: Find the Safe House

A Python maze game built with Solara. The game logic and interface are written in Python; it does not use Pygame or project-authored JavaScript.

## Run the game

Use Python 3.10 or newer. From this folder, install the dependencies and start the Solara development server:

```powershell
py -m pip install -r requirements.txt
solara run app.py
```

Open the local URL printed by Solara in your browser. Stop the server with **Ctrl+C**.

## Project files

- `app.py` contains the Solara interface, maze generation, zombie pursuit, and turn-based game logic.
- `a_star.py` provides the A* pathfinder used by the game.
- `requirements.txt` lists the Solara dependency.

## How to play

- Use the directional buttons to move and **Wait** to let the zombies patrol without moving.
- Find the safe house (`H`) without stepping on bombs (`B`) or zombies (`Z`).
- Before starting every level, choose A*, BFS, or DFS from the algorithm dropdown. The previous selection is preselected, but you must press **Start game** to begin each new level. The selector stays visible until your first move. If the chosen algorithm has no further safe move, or you or the AI step onto the same tile for a third time, the game stops, shows the message in red, restarts that level from its beginning, and the selector returns so you can pick another algorithm and press **Start game**. Choosing an algorithm resets that tile count. The blue route (`+`) appears once you press **Start game**, animating in along the path before your first move; it stays hidden until then. The route is calculated by that algorithm and recalculates after every turn to avoid zombies. If no safe route is available, the game hides the unsafe route, displays a warning naming the other two algorithms, and keeps the selector available so you can switch.
- Zombies appear behind you from level 1 and pursue you through the maze after each turn without passing you toward the safe house. If you step onto a zombie or it reaches your tile, the game ends.
- Each level uses a new maze and location. More zombies appear as levels advance.
- Your current level, score, and maze seed are saved in your operating system's application-data folder (`%LOCALAPPDATA%\\ZombieEscape\\progress.sqlite3` on Windows). Reopening the game restores the same level and maze from its starting position. This is a local-machine save, not an account save; users of one hosted server share its progress database.
- Use **Restart level** to retry, **Previous level** (shown from level 2 onward) to return to the prior level, **Pause** to freeze the game, and **Next level** after reaching the safe house. Returning to a previous level restarts its maze and saves it as your current progress. After winning, press **Space** to start the next level.
