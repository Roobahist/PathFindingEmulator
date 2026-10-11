---
version: 1
slug: "pathfinding-emulator-ui"
primary_target: "pathfinding_emulator/web/index.html"
related_targets: ["pathfinding_emulator/web/styles.css", "pathfinding_emulator/web/app.js"]
---

# Textured browser puzzle workspace

Mode: Operate. Build path: code-led. Scope: browser editor and solver playback.
User-pinned replacement direction supersedes rejected seed 3bae40cc and its
geometric exhibit. The user delegated autonomous implementation and explicitly
permitted moving from Pygame to HTML. No approved comp exists.

## Direction contract

THESIS: A modern game workspace whose actual colorful puzzle artwork dominates.
Original textures are the visual identity, not optional substitutes for flat tiles.

OWN-WORLD: Saturated pixel-art grass, deep blue water, lava and wooden crates
inside a dark, quiet workspace. IBM Plex Sans labels, warm orange primary action,
bright readable text, consistent compact controls and actual artwork previews.

STORY: Open or create a board, paint tiles, undo, save, solve, inspect the pushes,
and return to the original editable board. Every transition uses the Python rules.

FIRST VIEWPORT: Compact horizontal navigation and file actions. The textured
board occupies the largest region, with palette, artwork and solver in a right
inspector. Playback transport sits directly below the board. Narrow screens put
the board above tools; controls remain available without horizontal scrolling.

FORM: User-pinned original textures. Signature interaction: painting changes the
actual texture under the cursor; changing artwork immediately reskins the same
board. Playback scrubs real engine frames, flashes changed cells briefly, and
shows the original directional sprite on the last pushed cell. Reduced-motion
preferences remove the flash. No washed-out geometric replacement tiles.

FINISH: Real browser captures at desktop, narrow and user viewport; fresh finish
review against user feedback; DESIGN.md and design.json document shipped tokens.
Original raster assets stay byte-identical; screenshot origin is recorded separately.
