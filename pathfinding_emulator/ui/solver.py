import os

from ..config import asset_path

os.environ["PYGAME_HIDE_SUPPORT_PROMPT"] = "hide"

import pygame as pg

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

        self.back = pg.image.load(asset_path("back.png"))
        self.back = pg.transform.scale(
            self.back, (int(0.66 * cubeSize), int(0.66 * cubeSize))
        )

        self.increase = pg.image.load(asset_path("increase.png"))
        self.increase = pg.transform.scale(
            self.increase, (int(0.5 * cubeSize), int(0.3 * cubeSize))
        )

        self.decrease = pg.image.load(asset_path("decrease.png"))
        self.decrease = pg.transform.scale(
            self.decrease, (int(0.5 * cubeSize), int(0.3 * cubeSize))
        )

        self.back_to_mapeditor = False

        self.delay = delay
        w = len(state.map_array[0])
        h = len(state.map_array)
        self.celltype = ["stone", "hole", "empty", "box"]
        self.cubeSize = cubeSize
        self.pixelWidth, self.pixelHeight = (
            max(4, w) * (self.cubeSize + 1) - 1,
            h * self.cubeSize + h - 1,
        )
        self.page = pg.display.set_mode(
            (self.pixelWidth, self.pixelHeight + 3 * self.cubeSize)
        )

        self.delayinput = InputBox(
            0.5 * self.pixelWidth - 2 * self.cubeSize + 1.5 * self.cubeSize,
            self.pixelHeight + 1.4 * self.cubeSize,
            0.7 * self.cubeSize,
            0.6 * self.cubeSize,
            text=str(delay),
            font_size=int(0.6 * self.cubeSize),
        )

        self.redrawPage(state)

    def redrawPage(self, game, action=None):
        mapArr = game.previous_map
        self.page.fill((60, 60, 60))
        self.drawTile(mapArr)
        self.drawAction(action)
        self.drawTexts(game)
        self.drawButtons()
        self.animate(game, action)

        self.drawTile(game.map_array)
        self.drawAction(action)

        pg.display.update()

    def drawTile(self, array):
        draw_board(self.page, array, self.tiles, self.cubeSize)

    def drawAction(self, action):
        if action is not None:
            self.page.blit(
                self.direction_images[action.direction],
                (
                    self.pixelPos(action.y) - self.cubeSize / 2,
                    self.pixelPos(action.x) - self.cubeSize / 2,
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
                            (self.pixelPos(cell[1]), self.pixelPos(cell[0])),
                        )

                    for cell in cells_to_move:
                        self.page.blit(
                            self.box_img,
                            (
                                self.pixelPos(cell[1]) + state.h * k * step + state.h,
                                self.pixelPos(cell[0]) + state.v * k * step + state.v,
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
        self.page.blit(
            self.back,
            (
                0.5 * self.pixelWidth - 2 * self.cubeSize + 3.23 * self.cubeSize,
                self.pixelHeight + 2.22 * self.cubeSize,
            ),
        )
        self.page.blit(
            self.increase,
            (
                0.5 * self.pixelWidth - 2 * self.cubeSize + 1.6 * self.cubeSize,
                self.pixelHeight + 1 * self.cubeSize,
            ),
        )
        self.page.blit(
            self.decrease,
            (
                0.5 * self.pixelWidth - 2 * self.cubeSize + 1.6 * self.cubeSize,
                self.pixelHeight + 2.1 * self.cubeSize,
            ),
        )
        self.delayinput.draw(self.page)
        pg.display.update()

    def drawTexts(self, state):
        pg.font.init()
        pg.draw.rect(
            self.page,
            (60, 60, 60),
            (0, self.pixelHeight, self.pixelWidth, self.cubeSize * 3),
        )
        font = pg.font.SysFont("arial", int(0.45 * self.cubeSize))
        color = (255, 255, 255)
        message = "Total cost: " + str(state.cost)
        text = font.render(message, True, color)
        self.page.blit(
            text,
            (
                0.5 * self.pixelWidth - 2 * self.cubeSize + 0.15 * self.cubeSize,
                self.pixelHeight + 0.2 * self.cubeSize,
            ),
        )

        text = font.render("Delay :          (s)", True, color)
        self.page.blit(
            text,
            (
                0.5 * self.pixelWidth - 2 * self.cubeSize + 0.2 * self.cubeSize,
                self.pixelHeight + 1.4 * self.cubeSize,
            ),
        )

    def colorCube(self, i, j, celltype):
        self.page.blit(self.tiles[celltype], (self.pixelPos(i), self.pixelPos(j)))

    def pixelPos(self, i):
        return i * self.cubeSize + i

    def user_click(self, event=None):
        x, y = event.pos if event is not None else pg.mouse.get_pos()

        if (
            0.5 * self.pixelWidth - 2 * self.cubeSize + 1.6 * self.cubeSize
            <= x
            <= 0.5 * self.pixelWidth
            - 2 * self.cubeSize
            + 1.6 * self.cubeSize
            + 0.5 * self.cubeSize
        ):
            if (
                self.pixelHeight + 1 * self.cubeSize
                <= y
                <= self.pixelHeight + 1 * self.cubeSize + 0.3 * self.cubeSize
            ):
                if float(self.delayinput.text) < 99:
                    self.delayinput.text = str(
                        min(99, float(self.delayinput.text) + 0.25)
                    )
            elif (
                self.pixelHeight + 2.1 * self.cubeSize
                <= y
                <= self.pixelHeight + 2.1 * self.cubeSize + 0.3 * self.cubeSize
            ):
                if float(self.delayinput.text) > 0:
                    self.delayinput.text = str(
                        max(0, float(self.delayinput.text) - 0.25)
                    )

        elif (
            0.5 * self.pixelWidth - 2 * self.cubeSize + 3.23 * self.cubeSize
            <= x
            <= 0.5 * self.pixelWidth
            - 2 * self.cubeSize
            + 3.23 * self.cubeSize
            + int(0.66 * self.cubeSize)
        ):
            if (
                self.pixelHeight + 2.22 * self.cubeSize
                <= y
                <= self.pixelHeight + 2.22 * self.cubeSize + int(0.66 * self.cubeSize)
            ):
                self.back_to_mapeditor = True
        self.drawButtons()
        pg.display.update()

    def user_write(self, event):
        if event.key == pg.K_ESCAPE:
            self.back_to_mapeditor = True
