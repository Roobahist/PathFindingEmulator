"""Verify an installed wheel independently of the repository working directory."""

import os
import subprocess
import sysconfig
import tempfile
import venv
import zipfile
from pathlib import Path

root = Path(__file__).resolve().parents[1]
wheels = list((root / "dist").glob("*.whl"))
if len(wheels) != 1:
    raise SystemExit("Build exactly one wheel in dist/ before running this check")
with zipfile.ZipFile(wheels[0]) as archive:
    names = archive.namelist()
    assert sum(name.endswith(".pickle") for name in names) == 14
    for index in range(14):
        assert f"pathfinding_emulator/sample_maps/map_{index}.json" in names
    assert sum(name.endswith((".png", ".jpg")) for name in names) == 37
    for module in (
        "pathfinding_emulator/browser/server.py",
        "pathfinding_emulator/desktop/launcher.py",
        "pathfinding_emulator/desktop/editor.py",
        "pathfinding_emulator/experimental.py",
        "Env.py",
        "MapLoader.py",
        "Utils.py",
        "ai.py",
        "Astarr.py",
        "simpids.py",
        "Main.py",
        "MainGui.py",
        "MapEditor.py",
        "GuiSolver.py",
        "other_agents.py",
    ):
        assert module in names
    assert not any(
        name.startswith(
            (
                "pathfinding_emulator/ui/",
                "pathfinding_emulator/web/",
                "pathfinding_emulator/assets/env/",
            )
        )
        for name in names
    )
    for asset in (
        "browser/static/index.html",
        "browser/static/chevron.svg",
        "browser/static/styles.css",
        "browser/static/app.js",
        "assets/fonts/IBMPlexSans-Regular.ttf",
        "assets/fonts/LICENSE.txt",
    ):
        assert "pathfinding_emulator/" + asset in names
with tempfile.TemporaryDirectory() as directory:
    check_dir = Path(directory)
    venv.EnvBuilder(with_pip=True).create(check_dir / "venv")
    python = (
        check_dir / "venv" / ("Scripts/python.exe" if os.name == "nt" else "bin/python")
    )
    subprocess.run(
        [str(python), "-m", "pip", "install", "--no-deps", str(wheels[0])],
        check=True,
        cwd=directory,
    )
    env = dict(
        os.environ,
        SDL_VIDEODRIVER="dummy",
        SDL_AUDIODRIVER="dummy",
        PYGAME_HIDE_SUPPORT_PROMPT="hide",
    )
    env.pop("PYTHONPATH", None)
    subprocess.run(
        [
            str(python),
            "-m",
            "pathfinding_emulator",
            "--headless",
            "--map",
            "map_10",
            "--algorithm",
            "A_Star",
        ],
        check=True,
        cwd=directory,
        env=env,
    )
    browser_check = """
import json
import threading
from pathlib import Path
from urllib.request import urlopen
from pathfinding_emulator.config import Settings, SAMPLE_MAPS_DIR
from pathfinding_emulator.maps import ChallengeDesigner, load_map
from pathfinding_emulator.browser.server import make_server
server = make_server(Settings(maps_dir=Path('saved')), ChallengeDesigner(Path('saved')))
thread = threading.Thread(target=server.serve_forever, daemon=True)
thread.start()
try:
    url = f'http://127.0.0.1:{server.server_port}'
    for asset in ('/', '/app.js', '/chevron.svg', '/styles.css', '/assets/tiles/grass_water/box.jpg', '/assets/fonts/IBMPlexSans-Regular.ttf'):
        with urlopen(url + asset) as response:
            assert response.status == 200 and response.read()
    with urlopen(url + '/api/bootstrap') as response:
        assert json.load(response)['grid'] == load_map(SAMPLE_MAPS_DIR / 'map_0.json')
finally:
    server.shutdown()
    server.server_close()
    thread.join()
"""
    subprocess.run(
        [str(python), "-c", browser_check], check=True, cwd=directory, env=env
    )
    subprocess.run(
        [
            str(python),
            "-c",
            f"import sys; sys.path.append({sysconfig.get_path('platlib')!r}); from pathlib import Path; import pygame as pg; import pathfinding_emulator as package; from MainGui import GUI; from MapEditor import MapEditor; from Env import Env; from GuiSolver import Solver; from Utils import base_map; assert Path(package.__file__).resolve().is_relative_to(Path('venv').resolve()); pg.init(); GUI(); grid=base_map(2,2); MapEditor(map=grid); Solver(50,0,Env(grid).state); pg.quit()",
        ],
        check=True,
        cwd=directory,
        env=env,
    )
print(
    "Installed-wheel CLI, compatibility imports, samples, artwork, browser server, and GUI smoke checks passed"
)
