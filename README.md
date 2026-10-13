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

- `app.py` contains the Solara interface, maze generation, zombie patrols, and turn-based game logic.
- `a_star.py` provides the A* pathfinder used by the game.
- `requirements.txt` lists the Solara dependency.

## How to play

- Use the directional buttons to move and **Wait** to let the zombies patrol without moving.
- Find the safe house (`H`) without stepping on bombs (`B`) or zombies (`Z`).
- The blue route (`+`) shows a current safe path and recalculates after every turn; patrol movement can change it.
- Zombies patrol within three tiles of their starting positions.
- Each level uses a new maze and location. More zombies appear as levels advance.
- Use **Restart level** to retry, **Pause** to freeze the game, and **Next level** after reaching the safe house.
