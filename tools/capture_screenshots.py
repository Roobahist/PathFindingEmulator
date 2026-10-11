"""Capture real Pygame screens for the README, without a desktop display."""

import os
from pathlib import Path

os.environ.setdefault("SDL_VIDEODRIVER", "dummy")
os.environ.setdefault("SDL_AUDIODRIVER", "dummy")
os.environ.setdefault("PYGAME_HIDE_SUPPORT_PROMPT", "hide")

import pygame as pg

from pathfinding_emulator.environment import Env, base_map
from pathfinding_emulator.ui.main_gui import GUI
from pathfinding_emulator.ui.map_editor import MapEditor
from pathfinding_emulator.ui.solver import Solver


def main():
    destination = Path(__file__).resolve().parents[1] / "docs" / "screenshots"
    destination.mkdir(parents=True, exist_ok=True)
    pg.init()
    try:
        gui = GUI()
        pg.image.save(gui.page, destination / "launcher.png")
        gui.which_page = 3
        gui.page_buttons[3][2].text = "6"
        gui.page_buttons[3][3].text = "6"
        gui.draw()
        pg.image.save(gui.page, destination / "setup.png")
        grid = base_map(6, 6)
        for row, col in ((2, 2), (2, 5), (4, 3), (5, 5)):
            grid[row][col] = 1
        grid[3][3] = grid[3][4] = -2
        grid[5][2] = -1
        editor = MapEditor(map=grid, cubeSize=50, B=2, R=1, EH=1)
        editor.active_buttons[2] = True
        editor.redrawPage()
        pg.image.save(editor.page, destination / "editor.png")
        env = Env(grid)
        env.take_action((2, 2, "left"))
        solver = Solver(50, 0.5, env.state)
        solver.status = "Solving..."
        solver.steps = 1
        solver.redrawPage(env.state)
        pg.image.save(solver.page, destination / "solver.png")
    finally:
        pg.quit()


if __name__ == "__main__":
    main()
