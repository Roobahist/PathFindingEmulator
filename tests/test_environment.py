import json
import unittest
from copy import deepcopy
from pathlib import Path

from pathfinding_emulator.environment import Env, State, base_map, validate_map


class EnvironmentTests(unittest.TestCase):
    def test_original_scoring_fixtures(self):
        cases = json.loads(
            (Path(__file__).parent / "fixtures/legacy_scoring.json").read_text()
        )
        for case in cases:
            with self.subTest(case=case):
                grid = base_map(1, 2)
                grid[1][1:3] = case["cells"]
                env = Env(grid)
                for action in case["actions"]:
                    env.take_action(action)
                self.assertEqual(env.send_map(), case["map"])
                self.assertEqual(env.send_cost(), case["cost"])

    def test_chain_pushes_in_all_directions(self):
        for direction, dr, dc in (
            ("up", -1, 0),
            ("down", 1, 0),
            ("left", 0, -1),
            ("right", 0, 1),
        ):
            with self.subTest(direction=direction):
                grid = base_map(3, 3)
                grid[2][2] = grid[2 + dr][2 + dc] = 1
                env = Env(grid)
                env.take_action((2, 2, direction))
                self.assertEqual(sum(row.count(1) for row in env.send_map()), 1)
                self.assertEqual(env.send_cost(), 6)
                self.assertEqual(env.state.last_state, "fire")

    def test_full_copy_preserves_cost_history_and_isolation(self):
        grid = base_map(1, 3)
        grid[1][1] = 1
        env = Env(grid)
        env.take_action((1, 1, "right"))
        for copied in (env.copy_env(), deepcopy(env)):
            self.assertEqual(copied, env)
            copied.take_action((1, 2, "right"))
            self.assertEqual(copied.send_cost(), 6)
            self.assertEqual(env.send_cost(), 5)
            self.assertEqual(env.state.map_array[1][2], 1)
        grid[1][1] = 0
        perceived = env.send_map()
        perceived[1][2] = 0
        self.assertEqual(env.state.map_array[1][2], 1)

    def test_invalid_actions_do_not_change_state(self):
        state = State(base_map(2, 2))
        for action in (
            None,
            (),
            (True, 1, "up"),
            (1, 1, []),
            (0, 1, "up"),
            (1, 1, "diagonal"),
        ):
            self.assertFalse(state.validate_action(action))
        with self.assertRaises(ValueError):
            state.update(0, 1, "up")
        self.assertEqual(state.cost, 0)

    def test_invalid_maps(self):
        cyclic = []
        cyclic.append(cyclic)
        for grid in ([], [[1]], [[-1] * 3, [-1, 0], [-1] * 3], base_map(1, 1), cyclic):
            if grid == base_map(1, 1):
                grid[1][1] = True
            with self.subTest(grid=str(grid)), self.assertRaises(ValueError):
                validate_map(grid)

    def test_dimensions_and_border_validation(self):
        for dimensions in ((0, 1), (1, 101), (True, 2)):
            with self.assertRaises(ValueError):
                base_map(*dimensions)
        grid = base_map(1, 1)
        grid[0][1] = 0
        with self.assertRaises(ValueError):
            Env(grid)
