"""Verify curated challenge maps using the production solver."""

import unittest
from pathlib import Path
from tempfile import TemporaryDirectory

from pathfinding_emulator.agents import solve
from pathfinding_emulator.config import SAMPLE_MAPS_DIR
from pathfinding_emulator.environment import Env
from pathfinding_emulator.maps import ChallengeDesigner, load_map


class CuratedChallengesTests(unittest.TestCase):
    # Cost-optimal solutions from uniform-cost search, verified by replay.
    EXPECTED = [
        (5, 13),
        (6, 19),
        (7, 28),
        (8, 29),
        (8, 19),
        (9, 28),
        (11, 30),
        (11, 56),
        (13, 38),
        (13, 45),
        (15, 57),
        (16, 65),
        (17, 62),
        (20, 67),
    ]

    def test_bundled_json_levels_are_unique_and_solvable(self):
        samples = sorted(SAMPLE_MAPS_DIR.glob("map_*.json"))
        self.assertEqual(len(samples), len(self.EXPECTED))
        fingerprints = set()
        for index, (expected_pushes, expected_cost) in enumerate(self.EXPECTED):
            with self.subTest(level=index):
                path = SAMPLE_MAPS_DIR / f"map_{index}.json"
                grid = load_map(path)
                fingerprints.add(tuple(tuple(row) for row in grid))
                self.assertLessEqual(len(grid), 22)
                self.assertLessEqual(len(grid[0]), 22)
                env = Env(grid)
                plan = solve(grid, "A_Star")
                self.assertEqual(len(plan), expected_pushes)
                for action in plan:
                    env.take_action(action.return_action())
                self.assertTrue(env.goal_test())
                self.assertEqual(env.send_cost(), expected_cost)
                self.assertEqual(ChallengeDesigner().load_map(f"map_{index}"), grid)
        self.assertEqual(len(fingerprints), len(self.EXPECTED))

    def test_new_saves_do_not_shadow_bundled_level_names(self):
        with TemporaryDirectory() as directory:
            designer = ChallengeDesigner(directory)
            path = Path(designer.save_map(load_map(SAMPLE_MAPS_DIR / "map_0.json")))
            self.assertEqual(path.name, "map_14.json")
