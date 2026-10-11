"""Loopback browser workspace; all puzzle transitions stay in the Python engine."""

import json
import random
import webbrowser
from http import HTTPStatus
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from urllib.parse import parse_qs, urlsplit

from .agents import ALGORITHMS, Agent, SearchLimitError
from .config import ASSETS_DIR, PACKAGE_DIR, SAMPLE_MAPS_DIR
from .environment import Env, base_map, validate_map
from .maps import ChallengeDesigner

WEB_DIR = PACKAGE_DIR / "web"
MAX_REQUEST = 1024 * 1024
MAX_REPLAY = 8 * 1024 * 1024


def browser_grid(grid):
    grid = validate_map(grid)
    if len(grid) > 22 or len(grid[0]) > 22:
        raise ValueError("Browser boards support up to 20 × 20 interior cells")
    return grid


def replay(grid, algorithm, settings, seed=None):
    if algorithm not in ALGORITHMS:
        raise ValueError("Choose a supported solver")
    env = Env(browser_grid(grid))
    agent = Agent(
        env.send_map,
        algorithm,
        random.Random(seed),
        settings.max_nodes,
        settings.max_depth,
    )
    frames = [{"grid": env.send_map(), "cost": 0, "action": None}]
    for _ in range(settings.max_steps):
        if env.goal_test():
            return frames
        action = agent.act()
        env.take_action(action.return_action())
        frames.append(
            {
                "grid": env.send_map(),
                "cost": env.send_cost(),
                "action": {
                    "row": action.x,
                    "col": action.y,
                    "direction": action.direction,
                },
            }
        )
        # Bound replay memory independently of the search budget.
        if len(frames) * len(grid) * len(grid[0]) * 5 > MAX_REPLAY:
            raise SearchLimitError(
                "Replay is too large. Use a smaller board or the headless CLI"
            )
    if env.goal_test():
        return frames
    raise SearchLimitError(
        "Action limit reached. Try another algorithm or a smaller board"
    )


def make_server(settings, designer, initial_map=None, port=0):
    initial = (
        browser_grid(initial_map)
        if initial_map is not None
        else ChallengeDesigner().load_map(SAMPLE_MAPS_DIR / "map_13.pickle")
    )

    class Handler(BaseHTTPRequestHandler):
        def log_message(self, *_args):
            pass

        def send_json(self, value, status=200):
            payload = json.dumps(value).encode()
            self.send_response(status)
            self.send_header("Content-Type", "application/json; charset=utf-8")
            self.send_header("Content-Length", str(len(payload)))
            self.send_header("Cache-Control", "no-store")
            self.end_headers()
            self.wfile.write(payload)

        def do_GET(self):
            parsed = urlsplit(self.path)
            try:
                if parsed.path == "/api/bootstrap":
                    self.send_json(
                        {
                            "grid": initial,
                            "title": "Loaded board"
                            if initial_map is not None
                            else "Map 13",
                            "algorithm": settings.algorithm,
                            "delay": settings.delay,
                            "seed": settings.seed,
                            "maxNodes": settings.max_nodes,
                        }
                    )
                elif parsed.path == "/api/maps":
                    names = {p.name for p in SAMPLE_MAPS_DIR.glob("*.pickle")}
                    names.update(p.name for p in settings.maps_dir.glob("*.json"))
                    self.send_json({"maps": sorted(names)})
                elif parsed.path == "/api/map":
                    name = parse_qs(parsed.query).get("name", [""])[0]
                    if (
                        not name
                        or Path(name).name != name
                        or "/" in name
                        or "\\" in name
                        or ".." in name
                    ):
                        raise ValueError("Select a map from the library")
                    loader = ChallengeDesigner(settings.maps_dir)
                    self.send_json({"grid": browser_grid(loader.load_map(name))})
                else:
                    self.serve_file(parsed.path)
            except (ValueError, OSError) as error:
                self.send_json({"error": str(error)}, 400)

        def serve_file(self, path):
            if path.startswith("/assets/"):
                root, relative = ASSETS_DIR, path.removeprefix("/assets/")
            else:
                root, relative = WEB_DIR, path.lstrip("/") or "index.html"
            target = (root / relative).resolve()
            if not target.is_relative_to(root.resolve()) or not target.is_file():
                self.send_error(HTTPStatus.NOT_FOUND)
                return
            types = {
                ".svg": "image/svg+xml",
                ".html": "text/html; charset=utf-8",
                ".css": "text/css",
                ".js": "text/javascript",
                ".jpg": "image/jpeg",
                ".png": "image/png",
                ".ttf": "font/ttf",
            }
            payload = target.read_bytes()
            self.send_response(200)
            self.send_header("Content-Type", types.get(target.suffix, "text/plain"))
            self.send_header("Content-Length", str(len(payload)))
            self.send_header("X-Content-Type-Options", "nosniff")
            self.send_header(
                "Content-Security-Policy",
                "default-src 'self'; img-src 'self' blob:; style-src 'self'; script-src 'self'; font-src 'self'; connect-src 'self'; frame-ancestors 'none'",
            )
            self.end_headers()
            self.wfile.write(payload)

        def do_POST(self):
            origin = self.headers.get("Origin")
            allowed_origin = f"http://127.0.0.1:{self.server.server_port}"
            if origin and origin != allowed_origin:
                self.send_json({"error": "Use the local app window"}, 403)
                return
            try:
                length = int(self.headers.get("Content-Length", "0"))
                if not 0 < length <= MAX_REQUEST:
                    raise ValueError("Request must be between 1 byte and 1 MiB")
                if self.headers.get_content_type() != "application/json":
                    raise ValueError("Requests must use JSON")
                data = json.loads(self.rfile.read(length))
                if not isinstance(data, dict):
                    raise ValueError("Request must be an object")
                path = urlsplit(self.path).path
                if path == "/api/validate":
                    self.send_json({"grid": browser_grid(data.get("grid"))})
                elif path == "/api/new":
                    rows, cols = data.get("rows"), data.get("cols")
                    if (
                        type(rows) is not int
                        or type(cols) is not int
                        or not 1 <= rows <= 20
                        or not 1 <= cols <= 20
                    ):
                        raise ValueError(
                            "Rows and columns must be whole numbers from 1 to 20"
                        )
                    if data.get("random"):
                        loader = ChallengeDesigner(
                            settings.maps_dir,
                            random.Random(data.get("seed", settings.seed)),
                        )
                        loader.create_random_map(1, 1, rows, cols)
                        grid = loader.mapArr
                    else:
                        grid = base_map(rows, cols)
                    self.send_json({"grid": grid})
                elif path == "/api/save":
                    saved = designer.save_map(browser_grid(data.get("grid")))
                    self.send_json({"name": Path(saved).name})
                elif path == "/api/solve":
                    frames = replay(
                        data.get("grid"),
                        data.get("algorithm", "A_Star"),
                        settings,
                        data.get("seed", settings.seed),
                    )
                    self.send_json({"frames": frames})
                else:
                    self.send_json({"error": "Unknown action"}, 404)
            except (ValueError, TypeError, OSError, SearchLimitError) as error:
                self.send_json({"error": str(error)}, 400)

    return ThreadingHTTPServer(("127.0.0.1", port), Handler)


def run_web(settings, designer, initial_map=None, port=8765, open_browser=True):
    with make_server(settings, designer, initial_map, port) as server:
        url = f"http://127.0.0.1:{server.server_port}"
        print(f"PathFinding Emulator: {url}", flush=True)
        if open_browser:
            webbrowser.open(url)
        try:
            server.serve_forever(poll_interval=0.25)
        finally:
            server.server_close()
