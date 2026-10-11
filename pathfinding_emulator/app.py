"""Composition root and bounded GUI/headless application orchestration."""

import argparse
import logging
import random
import time
from collections import deque
from pathlib import Path

from .agents import Agent, NoSolutionError, SearchLimitError, search_steps
from .config import Settings, validate_styles
from .environment import Env
from .maps import ChallengeDesigner

logger = logging.getLogger(__name__)


def run_headless(grid, settings, rng=None):
    """Run a simulation to completion or fail explicitly within configured limits."""
    env = Env(grid)
    agent = Agent(
        env.send_map, settings.algorithm, rng, settings.max_nodes, settings.max_depth
    )
    for step in range(settings.max_steps + 1):
        if env.goal_test():
            return env, step
        if step == settings.max_steps:
            raise SearchLimitError(
                f"Simulation reached {settings.max_steps} actions; raise --max-steps or select A_Star"
            )
        env.take_action(agent.act().return_action())
    raise AssertionError("Unreachable simulation state")


def run_gui(settings, designer, initial_map=None):
    import pygame as pg

    from .ui.main_gui import GUI
    from .ui.map_editor import MapEditor
    from .ui.solver import Solver

    def make_editor(grid, gui=None, quotas=False):
        if len(grid) > 22 or len(grid[0]) > 22:
            raise ValueError(
                "GUI supports at most 20 x 20 interior cells; use --headless for larger maps"
            )
        desktop_width, desktop_height = pg.display.get_desktop_sizes()[0]
        fit = min(
            settings.cell_size,
            max(20, (desktop_width - 368) // len(grid[0]) - 1),
            max(20, (desktop_height - 192) // len(grid) - 1),
        )
        kwargs = {}
        if quotas and gui is not None and gui.command == "design_map":
            kwargs = dict(zip(("B", "EH", "R"), gui.inputs[3][4:7]))
        return MapEditor(
            map=grid,
            cubeSize=fit,
            env_style=gui.env_style if gui else 1,
            agent_style=gui.agent_style if gui else 1,
            **kwargs,
        )

    pg.init()
    clock = pg.time.Clock()
    pg.display.set_caption("PathFinding Emulator")
    gui = GUI(map_path=str(settings.maps_dir) + "/")
    editor = None
    solver = None
    env = None
    agent = None
    planner = None
    plan = deque()
    steps = 0
    next_action = 0.0
    screen = "setup"
    try:
        if initial_map is not None:
            designer.mapArr = initial_map
            editor = make_editor(initial_map)
            screen = "editor"
        while True:
            for event in pg.event.get():
                if event.type == pg.QUIT:
                    return
                if screen == "setup":
                    if event.type == pg.MOUSEBUTTONDOWN:
                        gui.user_click(event)
                    elif event.type == pg.KEYDOWN:
                        gui.user_write(event)
                elif screen == "editor":
                    if event.type == pg.MOUSEBUTTONDOWN:
                        editor.user_click(event)
                    elif event.type == pg.KEYDOWN:
                        if event.key == pg.K_ESCAPE:
                            editor.back_to_gui = True
                        elif event.key in (pg.K_h, pg.K_s, pg.K_b):
                            editor.active_buttons = [
                                event.key == key for key in (pg.K_h, pg.K_s, pg.K_b)
                            ]
                        elif event.key == pg.K_RETURN and sum(editor.remained) == 0:
                            editor.Done = True
                elif event.type == pg.MOUSEBUTTONDOWN:
                    solver.user_click(event)
                elif event.type == pg.KEYDOWN:
                    solver.user_write(event)

            try:
                if screen == "setup":
                    if gui.Done:
                        gui.Done = False
                        validate_styles(gui.env_style, gui.agent_style)
                        if gui.command in {"create_random_map", "design_map"}:
                            dimensions = gui.inputs[
                                2 if gui.command == "create_random_map" else 3
                            ][2:4]
                            if any(
                                type(n) is not int or not 1 <= n <= 20
                                for n in dimensions
                            ):
                                raise ValueError(
                                    "GUI dimensions must be whole numbers from 1 to 20"
                                )
                        designer.run(gui.command, gui.inputs)
                        editor = make_editor(designer.mapArr, gui, quotas=True)
                        screen = "editor"
                    if screen == "setup":
                        gui.draw()
                elif screen == "editor":
                    if editor.to_change:
                        designer.update_map(*editor.to_change)
                        editor.map = designer.mapArr
                        editor.to_change = []
                    if editor.save:
                        editor.save = False
                        editor.message = (
                            "Saved: " + Path(designer.save_map(editor.map)).name
                        )
                    if editor.back_to_gui:
                        gui = GUI(
                            str(settings.maps_dir) + "/", gui.env_style, gui.agent_style
                        )
                        screen = "setup"
                    elif editor.Done:
                        editor.Done = False
                        env = Env(editor.map)
                        agent = Agent(
                            env.send_map,
                            settings.algorithm,
                            designer.rng,
                            settings.max_nodes,
                            settings.max_depth,
                        )
                        plan.clear()
                        planner = (
                            None
                            if settings.algorithm == "random"
                            else search_steps(
                                env.send_map(),
                                settings.algorithm,
                                settings.max_nodes,
                                settings.max_depth,
                            )
                        )
                        solver = Solver(
                            editor.cubeSize,
                            settings.delay,
                            env.state,
                            gui.env_style,
                            gui.agent_style,
                        )
                        screen = "solver"
                        steps = 0
                        next_action = time.monotonic()
                    else:
                        editor.redrawPage()
                else:
                    if solver.back_to_mapeditor:
                        if planner is not None:
                            planner.close()
                        planner = None
                        editor = make_editor(designer.mapArr, gui)
                        screen = "editor"
                    elif planner is not None:
                        solver.status = "Planning..."
                        solver.redrawPage(env.state)
                        # Cooperatively budget planning each frame so Back/Quit work.
                        deadline = time.monotonic() + 0.008
                        while time.monotonic() < deadline:
                            try:
                                next(planner)
                            except StopIteration as result:
                                plan.extend(result.value)
                                planner = None
                                break
                        pg.display.set_caption(
                            "PathFinding Emulator — planning; Esc to cancel"
                        )
                    elif env.goal_test():
                        solver.status = "Solved"
                        solver.redrawPage(env.state)
                        pg.display.set_caption(
                            f"Solved — cost {env.send_cost()}, {steps} actions; Esc to edit"
                        )
                    elif time.monotonic() >= next_action:
                        if steps >= settings.max_steps:
                            raise SearchLimitError(
                                "Action limit reached; edit the map or increase --max-steps"
                            )
                        if settings.algorithm != "random" and not plan:
                            raise NoSolutionError(
                                "Plan exhausted before all boxes were removed"
                            )
                        action = (
                            agent.act()
                            if settings.algorithm == "random"
                            else plan.popleft()
                        )
                        env.take_action(action.return_action())
                        steps += 1
                        solver.steps = steps
                        solver.status = "Solving..."
                        solver.redrawPage(env.state, action)
                        next_action = time.monotonic() + float(solver.delayinput.text)
                        pg.display.set_caption(
                            "PathFinding Emulator — solving; Esc to edit"
                        )
            except (
                OSError,
                ValueError,
                SearchLimitError,
                StopIteration,
            ) as error:
                logger.warning("%s", error)
                if screen == "setup":
                    gui.Done = False
                    gui.message = str(error)
                elif screen == "editor":
                    editor.message = str(error)
                else:
                    if planner is not None:
                        planner.close()
                    planner = None
                    editor = make_editor(designer.mapArr, gui)
                    editor.message = str(error)
                    screen = "editor"
            clock.tick(settings.fps)
    finally:
        if planner is not None:
            planner.close()
        pg.quit()


def parser():
    result = argparse.ArgumentParser(description="Edit and solve box-pushing puzzles")
    result.add_argument(
        "--headless", action="store_true", help="Run without importing Pygame"
    )
    result.add_argument(
        "--map", help="JSON/legacy pickle path, or sample name such as map_7"
    )
    result.add_argument(
        "--height", type=int, default=2, help="Interior rows for generated maps"
    )
    result.add_argument(
        "--width", type=int, default=2, help="Interior columns for generated maps"
    )
    result.add_argument(
        "--maps-dir",
        type=Path,
        default=Path("maps"),
        help="Directory for new JSON saves",
    )
    result.add_argument(
        "--algorithm", choices=("random", "A_Star", "IDS"), default="random"
    )
    result.add_argument("--seed", type=int)
    result.add_argument("--cell-size", type=int, default=50)
    result.add_argument(
        "--delay", type=float, default=1.0, help="Seconds between animated actions"
    )
    result.add_argument("--fps", type=int, default=60)
    result.add_argument("--max-steps", type=int, default=10000)
    result.add_argument("--max-nodes", type=int, default=50000)
    result.add_argument("--max-depth", type=int, default=100)
    return result


def main(argv=None):
    args_parser = parser()
    args = args_parser.parse_args(argv)
    logging.basicConfig(level=logging.INFO, format="%(levelname)s: %(message)s")
    try:
        settings = Settings(
            **{name: getattr(args, name) for name in Settings.__dataclass_fields__}
        )
        designer = ChallengeDesigner(settings.maps_dir, random.Random(settings.seed))
        if args.map:
            designer.load_map(args.map)
        if args.headless:
            if designer.mapArr is None:
                designer.create_random_map(1, 1, args.height, args.width)
            env, steps = run_headless(designer.mapArr, settings, designer.rng)
            print(f"Solved: {steps} actions, total cost {env.send_cost()}")
        else:
            run_gui(settings, designer, designer.mapArr)
        return 0
    except (OSError, ValueError, SearchLimitError) as error:
        logger.error("%s", error)
        return 1
    except ModuleNotFoundError as error:
        if error.name != "pygame":
            raise
        logger.error(
            "Pygame is required for the GUI. Install requirements.txt with Python 3.11–3.13"
        )
        return 1
    except KeyboardInterrupt:
        return 130
