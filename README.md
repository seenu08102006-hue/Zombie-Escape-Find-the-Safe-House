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
- **A\*** shows a blue route from your current position to the safe house on every level. It avoids bombs and stationary zombie tiles, favors paths that keep distance from zombies, and recalculates as you move. Click **Safe path** or press **H** to hide or show it.
- The entire maze, safe house, and all zombies are visible from the start.
- Do not fight the zombies. Dodge them and avoid stepping onto their tiles.
- Zombies stay in the same position during each level. Avoid stepping onto their tiles.
- The safe house is open from the start. Reach it whenever you want to complete the level.
- The HUD shows steps already taken and the level's fixed exact step target, calculated from the shortest bomb-free route at the start of the level. The exact step target does not count down while you move. Going over it before reaching the safe house ends the level; retry to try again.
- Earn points for completing levels. The HUD tracks score and steps.
- The game has unlimited levels. The location changes every level, cycling through Overgrown Village, Pinewood Forest, Frozen Outpost, Ashen City, and Toxic Marsh. Each location has its own maze terrain and ambient background colors.
- Level 1 is a zombie-free tutorial. Zombies begin at Level 2 with two and increase to a maximum of five.
- Zombies appear from Level 2 and remain stationary for the whole level.
- Every level has two complete routes to the safe house: a winding bomb-free route and an alternate route with marked bomb detours. The first four levels have three traps; from Level 5, the number increases by one per level, up to eight. A warning lists their map coordinates; stepping on a bomb immediately ends the game.
- Levels use winding maze routes instead of clear perimeter shortcuts. The bomb-free route still requires navigating the maze, so plan carefully around the stationary zombies.
- Every level entry has a short animated location title card; completing a level plays a brief visual celebration before the next location transition.
- The maze grows through the first three stages, then stays at a playable size. Open shortcuts become rarer as levels advance, making routes harder to read and navigate. Zombie locations are randomized each run and level.
- Pause or resume with **P**, **Esc**, or the pause button.
- Reach the safe house to finish the level. Each new level has a new maze and additional zombies.
- After completing a level, click **Next level** or press **Space** to continue. After game over, click **Try this level again** or press **Space** to retry the current level without losing your progress.
- Press **R** or use **Restart** to begin again.