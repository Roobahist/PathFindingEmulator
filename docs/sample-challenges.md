# Curated sample challenges

These 14 browser levels replace the easy historical samples with increasingly
constrained, **solver-verified** puzzles. The original `map_*.pickle` files remain
untouched for compatibility.

These are results from the project's cost-minimizing `A_Star` solver, which
implements uniform-cost search. Minimum-cost paths can use more pushes than
minimum-push paths.

| Map | Challenge | Interior | Boxes | Pushes | Total movement cost |
| --- | --- | --- | ---: | ---: | ---: |
| [map_0.json](../src/pathfinding_emulator/sample_maps/map_0.json) | Opening Moves | 4 × 4 | 2 | 5 | 13 |
| [map_1.json](../src/pathfinding_emulator/sample_maps/map_1.json) | The Long Way | 4 × 4 | 2 | 6 | 19 |
| [map_2.json](../src/pathfinding_emulator/sample_maps/map_2.json) | Stone Gates | 4 × 4 | 3 | 7 | 28 |
| [map_3.json](../src/pathfinding_emulator/sample_maps/map_3.json) | Corner Crossing | 4 × 4 | 3 | 8 | 29 |
| [map_4.json](../src/pathfinding_emulator/sample_maps/map_4.json) | Split Paths | 4 × 5 | 3 | 8 | 19 |
| [map_5.json](../src/pathfinding_emulator/sample_maps/map_5.json) | Costly Detours | 4 × 5 | 3 | 9 | 28 |
| [map_6.json](../src/pathfinding_emulator/sample_maps/map_6.json) | Bottleneck | 4 × 5 | 4 | 11 | 30 |
| [map_7.json](../src/pathfinding_emulator/sample_maps/map_7.json) | North Passage | 5 × 5 | 3 | 11 | 56 |
| [map_8.json](../src/pathfinding_emulator/sample_maps/map_8.json) | Dead-End Diversion | 5 × 5 | 3 | 13 | 38 |
| [map_9.json](../src/pathfinding_emulator/sample_maps/map_9.json) | Hidden Route | 5 × 5 | 3 | 13 | 45 |
| [map_10.json](../src/pathfinding_emulator/sample_maps/map_10.json) | Double Barrier | 5 × 6 | 3 | 15 | 57 |
| [map_11.json](../src/pathfinding_emulator/sample_maps/map_11.json) | Crossed Corridors | 6 × 6 | 3 | 16 | 65 |
| [map_12.json](../src/pathfinding_emulator/sample_maps/map_12.json) | Long Escape | 5 × 6 | 3 | 17 | 62 |
| [map_13.json](../src/pathfinding_emulator/sample_maps/map_13.json) | Final Gauntlet | 6 × 6 | 3 | 20 | 67 |

The new levels vary obstacles, exit locations, blocked borders and box placements
to require detours and longer action sequences. Levels 0–3 introduce routing,
4–9 require more planning, and 10–13 require multi-stage paths. Every level
fits the 20 × 20 browser limit and has a cost-minimizing solution within the
default 50,000-node search budget. Tests replay the returned actions through
the production environment and check goal completion, movement cost and
action counts.

Play with **A*** to find minimum-cost solutions, or **BFS** to minimize the
number of pushes. Use step controls and timeline scrubbing to explore the
effects of action choices. Other strategies can reach search limits without
implying that a level is unsolvable.

The original pickle samples are still available with explicit paths, for
example `--map map_7.pickle`. Using `--map map_7` opens the new JSON level.
