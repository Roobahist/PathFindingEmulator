"""Exercise real Pygame screens using SDL's display-independent test driver."""

import os

os.environ.setdefault("SDL_VIDEODRIVER", "dummy")
os.environ.setdefault("SDL_AUDIODRIVER", "dummy")
os.environ.setdefault("PYGAME_HIDE_SUPPORT_PROMPT", "hide")

import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

try:
    import pygame as pg
except ModuleNotFoundError:
    pg = None

from pathfinding_emulator.app import run_gui
from pathfinding_emulator.config import Settings
from pathfinding_emulator.environment import Env, base_map
from pathfinding_emulator.maps import ChallengeDesigner


@unittest.skipIf(pg is None, "Pygame is not installed")
class UITests(unittest.TestCase):
    def setUp(self):
        pg.init()

    def tearDown(self):
        pg.quit()

    def test_all_themes_and_screens_load_from_any_directory(self):
        from pathfinding_emulator.ui.main_gui import GUI
        from pathfinding_emulator.ui.map_editor import MapEditor
        from pathfinding_emulator.ui.solver import Solver

        original = Path.cwd()
        try:
            with tempfile.TemporaryDirectory() as directory:
                os.chdir(directory)
                gui = GUI()
                for page in range(4):
                    gui.which_page = page
                    gui.draw()
                for style in range(4):
                    grid = base_map(2, 2)
                    editor = MapEditor(map=grid, env_style=style, agent_style=style)
                    editor.redrawPage()
                    solver = Solver(50, 0.5, Env(grid).state, style, style)
                    self.assertEqual(float(solver.delayinput.text), 0.5)
        finally:
            os.chdir(original)

    def test_keyboard_navigation_and_path_input(self):
        from pathfinding_emulator.ui.main_gui import GUI

        gui = GUI()
        gui.user_click(pg.event.Event(pg.MOUSEBUTTONDOWN, pos=(200, 100)))
        self.assertEqual(gui.which_page, 1)
        gui.user_write(pg.event.Event(pg.KEYDOWN, key=pg.K_TAB, unicode="\t"))
        self.assertTrue(gui.page_buttons[1][0].active)
        gui.user_write(pg.event.Event(pg.KEYDOWN, key=pg.K_a, unicode="a"))
        self.assertTrue(gui.page_buttons[1][0].text.endswith("a"))
        gui.user_write(pg.event.Event(pg.KEYDOWN, key=pg.K_RETURN, unicode="\r"))
        self.assertTrue(gui.Done)
        gui.user_write(pg.event.Event(pg.KEYDOWN, key=pg.K_ESCAPE, unicode=""))
        self.assertEqual(gui.which_page, 0)

    def test_solver_can_render_an_already_updated_state(self):
        from pathfinding_emulator.ui.solver import Solver

        grid = base_map(2, 2)
        grid[1][1] = 1
        env = Env(grid)
        env.take_action((1, 1, "left"))
        solver = Solver(50, 0, env.state)
        solver.redrawPage(env.state)

    def test_delay_cannot_go_negative(self):
        from pathfinding_emulator.ui.solver import Solver

        solver = Solver(50, 0, Env(base_map(2, 2)).state)
        x = int(0.5 * solver.pixelWidth - 2 * solver.cubeSize + 1.8 * solver.cubeSize)
        y = int(solver.pixelHeight + 2.2 * solver.cubeSize)
        solver.user_click(pg.event.Event(pg.MOUSEBUTTONDOWN, pos=(x, y)))
        self.assertEqual(float(solver.delayinput.text), 0)

    def test_design_edit_save_solve_back_and_quit(self):
        from pathfinding_emulator.ui.main_gui import GUI

        class DesignGUI(GUI):
            def __init__(self, *args, **kwargs):
                super().__init__(*args, **kwargs)
                self.command = "design_map"
                self.inputs[3] = [1, 1, 2, 2, 1, 0, 0]
                self.Done = True

        calls = 0
        completed = False
        returned = False

        def events():
            nonlocal calls, completed, returned
            calls += 1
            if calls > 150:
                self.fail("GUI did not finish within 150 event cycles")
            caption = pg.display.get_caption()[0]
            if calls == 2:
                return [
                    pg.event.Event(pg.KEYDOWN, key=pg.K_b, unicode="b"),
                    pg.event.Event(pg.MOUSEBUTTONDOWN, pos=(75, 75)),
                ]
            if calls == 3:
                return [pg.event.Event(pg.MOUSEBUTTONDOWN, pos=(170, 295))]
            if calls == 4:
                return [pg.event.Event(pg.KEYDOWN, key=pg.K_RETURN, unicode="\r")]
            if caption.startswith("Solved") and not completed:
                completed = True
                return [pg.event.Event(pg.KEYDOWN, key=pg.K_ESCAPE, unicode="")]
            if completed:
                returned = True
                return [pg.event.Event(pg.QUIT)]
            return []

        with tempfile.TemporaryDirectory() as directory:
            settings = Settings(maps_dir=Path(directory), algorithm="A_Star", delay=0)
            designer = ChallengeDesigner(directory)
            with (
                patch("pathfinding_emulator.ui.main_gui.GUI", DesignGUI),
                patch.object(pg.event, "get", events),
            ):
                run_gui(settings, designer)
            self.assertTrue(completed)
            self.assertTrue(returned)
            self.assertEqual(len(list(Path(directory).glob("*.json"))), 1)
            self.assertFalse(pg.get_init())
