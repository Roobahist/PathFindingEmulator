# Legacy imports

These small forwarding modules preserve original imports (`Env`, `ai`,
`Astarr`, `simpids`, and the Pygame screens) for installed users. Application
logic belongs in `src/pathfinding_emulator`, never here. `other_agents` forwards
to `pathfinding_emulator.experimental`.

They are included in wheels and editable installs. Install the project before
using legacy imports from source. The root `Main.py` remains a source launcher.
