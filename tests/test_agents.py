import random
import unittest
from itertools import product

from pathfinding_emulator.agents import Agent, NoSolutionError, SearchLimitError, solve
from pathfinding_emulator.app import run_headless
from pathfinding_emulator.config import Settings
from pathfinding_emulator.environment import Env, base_map


class AgentTests(unittest.TestCase):
    def test_small_maps_search_replays_using_environment(self):
        for cells in product((-2, -1, 0, 1), repeat=4):
            grid = base_map(2, 2)
            grid[1][1:3] = cells[:2]
            grid[2][1:3] = cells[2:]
            for algorithm in ("A_Star", "IDS"):
                with self.subTest(cells=cells, algorithm=algorithm):
                    plan = solve(grid, algorithm, max_nodes=10000, max_depth=10)
                    env = Env(grid)
                    for action in plan:
                        self.assertTrue(
                            env.state.validate_action(action.return_action())
                        )
                        env.take_action(action.return_action())
                    self.assertTrue(env.goal_test())

    def test_cost_matches_original_continuation_scoring(self):
        grid = base_map(1, 3)
        grid[0] = [-2] * 5
        grid[2] = [-2] * 5
        grid[1][0] = -2
        grid[1][1] = 1
        plan = solve(grid)
        env = Env(grid)
        for action in plan:
            env.take_action(action.return_action())
        self.assertEqual(len(plan), 3)
        self.assertEqual(env.send_cost(), 7)

    def test_internal_hole_is_used(self):
        grid = base_map(3, 3)
        grid[2][2], grid[2][3] = 1, -1
        plan = solve(grid)
        self.assertEqual(len(plan), 1)

    def test_unsolvable_and_limits_are_distinct(self):
        grid = [[-2] * 3, [-2, 1, -2], [-2] * 3]
        for algorithm in ("A_Star", "IDS"):
            with self.assertRaises(NoSolutionError):
                solve(grid, algorithm)
        grid = base_map(3, 3)
        grid[2][2] = 1
        with self.assertRaises(SearchLimitError):
            solve(grid, max_nodes=1)
        with self.assertRaises(SearchLimitError):
            solve(grid, "IDS", max_depth=1)

    def test_random_actions_always_select_movable_boxes(self):
        grid = base_map(3, 3)
        grid[2][2] = 1
        grid[2][1] = -2
        env = Env(grid)
        for seed in range(20):
            action = Agent(env.send_map, rng=random.Random(seed)).act()
            copied = env.copy_env()
            copied.take_action(action.return_action())
            self.assertNotEqual(copied.send_map(), env.send_map())

    def test_headless_simulation_and_legacy_imports(self):
        from Astarr import Agent as AStarAgent
        from simpids import Agent as IDSAgent

        grid = base_map(2, 2)
        grid[1][1] = 1
        env, steps = run_headless(grid, Settings(algorithm="A_Star"))
        self.assertTrue(env.goal_test())
        self.assertEqual(steps, 1)
        for legacy in (AStarAgent, IDSAgent):
            agent = legacy(lambda: grid)
            self.assertTrue(
                Env(grid).state.validate_action(agent.act().return_action())
            )
            with self.assertRaises(StopIteration):
                agent.act()

    def test_invalid_settings(self):
        for kwargs in (
            {"delay": float("nan")},
            {"max_nodes": 0},
            {"cell_size": 1},
            {"fps": True},
            {"algorithm": "wrong"},
        ):
            with self.assertRaises(ValueError):
                Settings(**kwargs)
