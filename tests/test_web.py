"""Real HTTP checks for the browser/engine boundary and packaged static files."""

import json
import tempfile
import threading
import unittest
from http.client import HTTPConnection
from pathlib import Path

from pathfinding_emulator.config import Settings
from pathfinding_emulator.environment import Env, base_map
from pathfinding_emulator.maps import ChallengeDesigner, load_map
from pathfinding_emulator.web_server import make_server


class BrowserServerTests(unittest.TestCase):
    def setUp(self):
        self.directory = tempfile.TemporaryDirectory()
        self.settings = Settings(maps_dir=Path(self.directory.name), max_steps=20)
        self.server = make_server(
            self.settings, ChallengeDesigner(self.settings.maps_dir)
        )
        self.thread = threading.Thread(target=self.server.serve_forever, daemon=True)
        self.thread.start()

    def tearDown(self):
        self.server.shutdown()
        self.server.server_close()
        self.thread.join()
        self.directory.cleanup()

    def request(self, path, data=None, headers=None):
        connection = HTTPConnection("127.0.0.1", self.server.server_port)
        body = None if data is None else json.dumps(data)
        connection.request(
            "GET" if data is None else "POST",
            path,
            body,
            headers or {"Content-Type": "application/json"},
        )
        response = connection.getresponse()
        result = response.status, response.read(), dict(response.getheaders())
        connection.close()
        return result

    def test_frontend_and_original_artwork_are_served(self):
        for path, content_type in [
            ("/", "text/html"),
            ("/app.js", "text/javascript"),
            ("/chevron.svg", "image/svg+xml"),
            ("/styles.css", "text/css"),
            ("/assets/env/3/box.jpg", "image/jpeg"),
            ("/assets/fonts/IBMPlexSans-Regular.ttf", "font/ttf"),
        ]:
            with self.subTest(path=path):
                status, body, headers = self.request(path)
                self.assertEqual(status, 200)
                self.assertTrue(body)
                self.assertIn(content_type, headers["Content-Type"])
                self.assertIn("default-src 'self'", headers["Content-Security-Policy"])
        self.assertEqual(self.request("/assets/../../config.py")[0], 404)

    def test_sample_library_and_bootstrap(self):
        status, body, _ = self.request("/api/bootstrap")
        self.assertEqual(status, 200)
        self.assertEqual(json.loads(body)["title"], "Map 13")
        _, body, _ = self.request("/api/maps")
        self.assertEqual(len(json.loads(body)["maps"]), 14)
        _, body, _ = self.request("/api/map?name=map_10.pickle")
        self.assertEqual(len(json.loads(body)["grid"]), 4)
        self.assertEqual(self.request("/api/map?name=../secret.json")[0], 400)

    def test_replay_matches_engine_scoring_and_preserves_input(self):
        grid = base_map(2, 2)
        grid[1][1] = grid[1][2] = 1
        for algorithm in ("A_Star", "IDS", "BFS", "DFS", "Greedy", "random"):
            with self.subTest(algorithm=algorithm):
                status, body, _ = self.request(
                    "/api/solve", {"grid": grid, "algorithm": algorithm, "seed": 42}
                )
                self.assertEqual(status, 200, body)
                frames = json.loads(body)["frames"]
                self.assertEqual(frames[0]["grid"], grid)
                env = Env(grid)
                for frame in frames[1:]:
                    action = frame["action"]
                    env.take_action((action["row"], action["col"], action["direction"]))
                    self.assertEqual(env.send_map(), frame["grid"])
                    self.assertEqual(env.send_cost(), frame["cost"])
                self.assertTrue(env.goal_test())
        self.assertEqual(grid[1][1], 1)

    def test_save_is_exclusive_and_can_reopen(self):
        grid = base_map(2, 2)
        saved = []
        for _ in range(2):
            status, body, _ = self.request("/api/save", {"grid": grid})
            self.assertEqual(status, 200)
            saved.append(json.loads(body)["name"])
        self.assertNotEqual(*saved)
        self.assertEqual(load_map(self.settings.maps_dir / saved[0]), grid)
        status, body, _ = self.request("/api/map?name=" + saved[0])
        self.assertEqual(status, 200)
        self.assertEqual(json.loads(body)["grid"], grid)

    def test_invalid_inputs_do_not_write_maps(self):
        for path, data in [
            ("/api/new", {"rows": 0, "cols": 2}),
            ("/api/new", {"rows": True, "cols": 2}),
            ("/api/new", {"rows": 21, "cols": 2}),
            ("/api/save", {"grid": [[1]]}),
            ("/api/solve", {"grid": base_map(2, 2), "algorithm": "unknown"}),
        ]:
            with self.subTest(path=path, data=data):
                self.assertEqual(self.request(path, data)[0], 400)
        self.assertEqual(list(self.settings.maps_dir.glob("*.json")), [])
        self.assertEqual(
            self.request(
                "/api/save",
                {"grid": base_map(2, 2)},
                {"Content-Type": "application/json", "Origin": "https://example.com"},
            )[0],
            403,
        )

    def test_empty_board_and_unsolvable_board(self):
        status, body, _ = self.request(
            "/api/solve", {"grid": base_map(1, 1), "algorithm": "A_Star"}
        )
        self.assertEqual(status, 200)
        self.assertEqual(len(json.loads(body)["frames"]), 1)
        grid = [[-2, -2, -2], [-2, 1, -2], [-2, -2, -2]]
        self.assertEqual(
            self.request("/api/solve", {"grid": grid, "algorithm": "A_Star"})[0], 400
        )

    def test_creation_keeps_valid_border_and_dimensions(self):
        for random_layout in (False, True):
            status, body, _ = self.request(
                "/api/new", {"rows": 3, "cols": 5, "random": random_layout, "seed": 42}
            )
            self.assertEqual(status, 200)
            grid = json.loads(body)["grid"]
            self.assertEqual((len(grid), len(grid[0])), (5, 7))
            Env(grid)
