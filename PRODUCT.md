# Product

<!-- impeccable:product-schema 1 -->

## Platform
Local browser workspace on macOS, Windows and Linux. Python 3.11–3.13 runs the
puzzle engine and a loopback HTTP server. The earlier Pygame interface remains
available through `--desktop`; it is no longer the default launch experience.

## Stack
Vanilla HTML, CSS and JavaScript, Python standard-library HTTP server, existing
Python rules and search. No frontend framework, build tool or runtime package.
Pygame 2.6.1 is needed only for the optional desktop interface.

## Product Purpose
Design, open and generate box-pushing puzzles, then watch an agent push boxes
into holes while tracking movement cost. Users edit and inspect solutions locally.

## Users and Operating Context
Someone creating, editing and solving puzzles with a mouse or keyboard in a
local browser. On narrow screens the board comes first and tools follow it.
No narrower demographic or reference application was supplied.

## Capabilities and Constraints
- Floor, hole, stone and box tiles; chain pushes and continuation scoring.
- Random, uniform-cost and iterative-deepening agents with bounded search.
- Preserve original artwork, sample maps, rules, stored data and legacy imports.
- Exclusive JSON saves in the configured maps directory; never overwrite maps.
- Browser boards support 20 × 20 interior cells; headless supports 100 × 100.
- The browser connects only to the local Python server; no cloud service.

## Brand Commitments
The name is PathFinding Emulator. The user explicitly rejected washed-out colors,
flat replacement tiles and a boring older-looking interface. Their original
textures must be prominent, including the vivid grass, water and lava sets.
They explicitly authorized changing the presentation stack, including HTML.
They asked for Impeccable and modern, sleek design, with no reference app in mind.

## Evidence and Principles
All four original texture sets, directional sprites and 14 original maps are
available. README images must show the running application. The board leads;
controls make editing, saving, solving and inspecting playback easy to find.
Preserve the puzzle's character through its actual artwork and saturated color.
