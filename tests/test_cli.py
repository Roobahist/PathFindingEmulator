import os
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

from pathfinding_emulator.agents import Action
from pathfinding_emulator.environment import base_map

ROOT = Path(__file__).resolve().parents[1]


class CLITests(unittest.TestCase):
    def launch(self, *args):
        return subprocess.run(
            [sys.executable, str(ROOT / "Main.py"), *args],
            capture_output=True,
            text=True,
            cwd=ROOT,
            timeout=10,
        )

    def test_launch_success_and_errors(self):
        result = self.launch("--headless", "--map", "map_10", "--algorithm", "A_Star")
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertIn("Solved: 2 actions, total cost 10", result.stdout)
        for args, code in (
            (["--delay", "nan"], 1),
            (["--map", "/missing/map.json", "--headless"], 1),
            (["--algorithm", "missing"], 2),
            (["--headless", "--height", "0"], 1),
            (
                [
                    "--headless",
                    "--height",
                    "3",
                    "--width",
                    "3",
                    "--seed",
                    "1",
                    "--max-steps",
                    "1",
                ],
                1,
            ),
        ):
            with self.subTest(args=args):
                failure = self.launch(*args)
                self.assertEqual(failure.returncode, code)
                self.assertNotIn("Traceback", failure.stderr)

    def test_core_imports_and_cli_do_not_require_site_packages(self):
        result = subprocess.run(
            [
                sys.executable,
                "-S",
                str(ROOT / "Main.py"),
                "--headless",
                "--map",
                "map_10",
                "--algorithm",
                "IDS",
            ],
            capture_output=True,
            text=True,
            cwd=ROOT,
            timeout=10,
        )
        self.assertEqual(result.returncode, 0, result.stderr)

    def test_configured_map_directory_lookup(self):
        from pathfinding_emulator.maps import ChallengeDesigner

        with tempfile.TemporaryDirectory() as directory:
            designer = ChallengeDesigner(directory)
            path = designer.save_map(base_map(2, 2))
            original = Path.cwd()
            try:
                os.chdir(directory)
                self.assertEqual(designer.load_map(Path(path).stem), base_map(2, 2))
            finally:
                os.chdir(original)

    def test_all_experimental_policies_have_explicit_exhaustion(self):
        from other_agents import AgentInspiration

        grid = base_map(2, 2)
        grid[1][1] = 1
        for name in AgentInspiration(lambda: grid).agent_type_dict:
            agent = AgentInspiration(lambda: grid)
            agent.agent_type = name
            for _ in range(3):
                self.assertIsInstance(agent.act(), Action)
        with self.assertRaises(StopIteration):
            AgentInspiration(lambda: base_map(2, 2)).act()
