# Zombie Escape: Find the Safe House

A dependency-free browser maze game with separate HTML, CSS, and JavaScript files. The project does not use Python.

## Run the game

Keep `index.html`, `style.css`, and `game.js` together in the same folder, then open `index.html` in a modern web browser. No installation or build step is needed.

## Project files

- `index.html` contains the game page and interface.
- `style.css` contains the responsive layout and visual styling.
- `game.js` contains the maze generation, rendering, controls, and game algorithms.

## How to play

- Move with **WASD**, the **arrow keys**, or the on-screen direction buttons.
- The complete maze automatically scales to fit the available screen width and height, including on later, larger levels.
- **A\*** shows a blue route from your current position to the safe house on every level. It avoids bombs and zombie-occupied tiles, favors paths that keep distance from zombies, and recalculates as you and they move. Zombies spawn off the safe route and choose moves that preserve an open route whenever possible. If no safe route exists, **Space** lets zombies move to make room. Click **Safe path** or press **H** to hide or show it. Zombies still use **A\*** to chase you.
- The entire maze, safe house, and all zombies are visible from the start.
- Do not fight the zombies. Dodge them and avoid stepping onto their tiles.
- Press **Space** to wait for a turn and let zombies move; they try to keep your route open.
- Zombies use **A\*** pathfinding to chase you while avoiding moves that block your only safe route.
- The safe house is open from the start. Reach it whenever you want to complete the level.
- Earn points for completing levels. The HUD tracks score and steps.
- The game has unlimited levels. The location changes every level, cycling through Overgrown Village, Pinewood Forest, Frozen Outpost, Ashen City, and Toxic Marsh. Each location has its own maze terrain and ambient background colors.
- Level 1 is a zombie-free tutorial. Zombies begin at Level 2 with two and increase to a maximum of five.
- In Levels 2–3, zombies move on alternating turns to give new players time to learn the maze.
- Every level has two complete routes to the safe house: a winding bomb-free route and an alternate route with marked bomb detours. From Level 5, bombs on the alternate route increase by one per level, up to six. A warning lists their map coordinates; stepping on a bomb immediately ends the game.
- Levels use winding maze routes instead of clear perimeter shortcuts. The bomb-free route still requires navigating the maze, and zombies can threaten either route, so plan carefully.
- Every level entry has a short animated location title card; completing a level plays a brief visual celebration before the next location transition.
- The maze grows through the first three stages, then stays at a playable size. Open shortcuts become rarer as levels advance, making routes harder to read and navigate. Zombie locations are randomized each run and level.
- Pause or resume with **P**, **Esc**, or the pause button.
- Reach the safe house to finish the level. Each new level has a new maze and additional zombies.
- After completing a level, click **Next level** or press **Space** to continue. After game over, click **Try this level again** or press **Space** to retry the current level without losing your progress.
- Press **R** or use **Restart** to begin again.