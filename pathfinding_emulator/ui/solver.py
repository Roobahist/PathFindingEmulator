import os

from ..config import asset_path

os.environ["PYGAME_HIDE_SUPPORT_PROMPT"] = "hide"

import pygame as pg

from . import theme as ui
from .main_gui import InputBox
from .tiles import draw_board, load_tiles


class Solver:
    def __init__(self, cubeSize, delay, state, env_style=1, agent_style=1):

        self.tiles = load_tiles(env_style, cubeSize)
        self.box_img, self.hole_img = self.tiles["box"], self.tiles["hole"]
        self.floor_img, self.stone_img = self.tiles["empty"], self.tiles["stone"]

        self.direction_images = {
            direction: pg.transform.scale(
                pg.image.load(asset_path("agent", agent_style, direction + ".png")),
                (2 * cubeSize, 2 * cubeSize),
            )
            for direction in ("left", "right", "up", "down")
        }
        self.left_img, self.right_img = (
            self.direction_images["left"],
            self.direction_images["right"],
        )
        self.up_img, self.down_img = (
            self.direction_images["up"],
            self.direction_images["down"],
        )

        self.back_to_mapeditor = False
        self.delay = delay
        self.cubeSize = cubeSize
        self.page, self.board_area, self.board_rect, self.sidebar = ui.workspace(
            len(state.map_array[0]), len(state.map_array), cubeSize
        )
        self.pixelWidth, self.pixelHeight = self.board_rect.size
        left = self.sidebar.x + 20
        self.decrease_button = pg.Rect(left, 426, 52, 48)
        self.increase_button = pg.Rect(left + 172, 426, 52, 48)
        self.back_button = pg.Rect(left, 550, 224, 48)
        self.delayinput = InputBox(
            left + 64, 426, 96, 48, text=str(delay), font_size=22
        )
        self.steps = 0
        self.status = "Ready"
        self.redrawPage(state)

    def redrawPage(self, game, action=None):
        mapArr = game.previous_map
        ui.header(
            self.page,
            "Watch the solution unfold.",
            "Follow each push. Adjust the pace or return to edit your board.",
            "simulation",
        )
        ui.panel(self.page, self.board_area)
        ui.panel(self.page, self.sidebar)
        self.drawTile(mapArr)
        self.drawAction(action)
        self.drawTexts(game)
        self.drawButtons()
        self.animate(game, action)

        self.drawTile(game.map_array)
        self.drawAction(action)

        pg.display.update()

    def drawTile(self, array):
        draw_board(self.page, array, self.tiles, self.cubeSize, self.board_rect.topleft)

    def drawAction(self, action):
        if action is not None:
            self.page.blit(
                self.direction_images[action.direction],
                (
                    self.board_rect.x + self.pixelPos(action.y) - self.cubeSize / 2,
                    self.board_rect.y + self.pixelPos(action.x) - self.cubeSize / 2,
                ),
            )

    def animate(self, state, action, fps=30, duration=1):
        if action is None:
            return

        if state.previous_map is not None:
            cells_to_move = []
            clock = pg.time.Clock()
            if state.last_state in ["empty", "fire"]:
                for k in range(state.number_of_boxes):
                    cells_to_move.append(
                        [action.x + k * state.v, action.y + k * state.h]
                    )

            if len(cells_to_move) > 0:
                step = self.cubeSize / fps

                for k in range(1, fps + 1):
                    if self.back_to_mapeditor:
                        break

                    for cell in cells_to_move:
                        self.page.blit(
                            self.floor_img,
                            (
                                self.board_rect.x + self.pixelPos(cell[1]),
                                self.board_rect.y + self.pixelPos(cell[0]),
                            ),
                        )

                    for cell in cells_to_move:
                        self.page.blit(
                            self.box_img,
                            (
                                self.board_rect.x
                                + self.pixelPos(cell[1])
                                + state.h * k * step
                                + state.h,
                                self.board_rect.y
                                + self.pixelPos(cell[0])
                                + state.v * k * step
                                + state.v,
                            ),
                        )

                    self.drawAction(action)

                    self.drawTexts(state)
                    self.drawButtons()

                    pg.display.update()
                    clock.tick(fps / max(duration * 0.2, 0.001))

                    for event in pg.event.get():
                        if event.type == pg.QUIT:
                            raise SystemExit

                        if event.type == pg.MOUSEBUTTONDOWN:
                            self.user_click(event)

                        if event.type == pg.KEYDOWN:
                            self.user_write(event)

    def drawButtons(self):
        ui.button(self.page, self.decrease_button, "−")
        ui.button(self.page, self.increase_button, "+")
        self.delayinput.draw(self.page)
        ui.button(self.page, self.back_button, "Return to editor / Esc")

    def drawTexts(self, state):
        ui.panel(self.page, self.sidebar)
        x = self.sidebar.x + 20
        ui.text(self.page, "RUN OVERVIEW", (x, 154), 14, ui.ACCENT, True)
        ui.text(self.page, self.status, (x, 192), 25, ui.ACCENT, True)
        ui.text(self.page, "TOTAL MOVEMENT COST", (x, 244), 14, ui.MUTED)
        ui.text(self.page, state.cost, (x, 268), 40, bold=True)
        boxes = sum(row.count(1) for row in state.map_array)
        ui.text(
            self.page,
            f"{self.steps} actions  /  {boxes} boxes left",
            (x, 338),
            17,
            ui.MUTED,
        )
        ui.text(self.page, "SECONDS BETWEEN PUSHES", (x, 392), 14, ui.MUTED)
        ui.text(self.page, "− faster     + slower", (x, 492), 17, ui.MUTED)

    def colorCube(self, i, j, celltype):
        self.page.blit(
            self.tiles[celltype],
            (
                self.board_rect.x + self.pixelPos(i),
                self.board_rect.y + self.pixelPos(j),
            ),
        )

    def pixelPos(self, i):
        return i * (self.cubeSize + 1)

    def user_click(self, event=None):
        pos = event.pos if event is not None else pg.mouse.get_pos()
        if self.increase_button.collidepoint(pos):
            self.delayinput.text = str(min(99, float(self.delayinput.text) + 0.25))
        elif self.decrease_button.collidepoint(pos):
            self.delayinput.text = str(max(0, float(self.delayinput.text) - 0.25))
        elif self.back_button.collidepoint(pos):
            self.back_to_mapeditor = True
        self.drawButtons()
        pg.display.update()

    def user_write(self, event):
        if event.key == pg.K_ESCAPE:
            self.back_to_mapeditor = True
        elif event.key in (pg.K_PLUS, pg.K_EQUALS, pg.K_KP_PLUS):
            self.user_click(
                pg.event.Event(pg.MOUSEBUTTONDOWN, pos=self.increase_button.center)
            )
        elif event.key in (pg.K_MINUS, pg.K_KP_MINUS):
            self.user_click(
                pg.event.Event(pg.MOUSEBUTTONDOWN, pos=self.decrease_button.center)
            )
