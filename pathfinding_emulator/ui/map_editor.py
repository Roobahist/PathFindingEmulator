"""Map editing and tile quotas; persistence belongs to the application."""

from copy import deepcopy

import pygame as pg

from ..config import validate_styles
from ..environment import base_map, validate_map
from . import theme as ui
from .tiles import TILE_NAMES, draw_board, load_tiles


def tile_count(value, default=0):
    if value is None or value == "":
        return default
    if isinstance(value, str) and value.isdecimal():
        value = int(value)
    if type(value) is not int or value < 0:
        raise ValueError("Tile counts must be nonnegative integers")
    return value


class MapEditor:
    def __init__(
        self,
        y=None,
        x=None,
        map=None,
        B=None,
        R=None,
        EH=None,
        delay=250,
        debug=True,
        cubeSize=50,
        env_style=1,
        agent_style=1,
    ):
        validate_styles(env_style, agent_style)
        pg.init()
        creating = map is None or map == []
        self.map = base_map(y, x) if creating else deepcopy(validate_map(map))
        self.x, self.y = len(self.map[0]), len(self.map)
        self.N = (self.x - 2) * (self.y - 2)
        self.initial_map = self.make_initial_map()
        self.cubeSize = cubeSize
        self.delay, self.debug = delay, debug
        self.celltype = list(TILE_NAMES)
        self.active_buttons = [False, False, False]
        self.to_fill = ["hole", "stone", "box"]
        self.remained = [
            tile_count(EH),
            tile_count(R, int(0.05 * self.N) if creating else 0),
            tile_count(B, int(0.5 * self.N) if creating else 0),
        ]
        interior = [tile for row in self.map[1:-1] for tile in row[1:-1]]
        occupied = sum(tile != 0 for tile in interior)
        if sum(self.remained) > self.N - occupied:
            raise ValueError("Tile counts must fit in the empty interior cells")
        self.EH = interior.count(-1) + self.remained[0]
        self.R = interior.count(-2) + self.remained[1]
        self.B = interior.count(1) + self.remained[2]
        self.font = pg.font.Font(None, max(16, int(0.45 * cubeSize)))
        self.colors = [
            (255, 255, 255),
            (60, 60, 60),
            (0, 0, 64),
            (255, 201, 14),
            (255, 127, 39),
            (0, 128, 64),
            (180, 230, 30),
            (128, 0, 0),
            (237, 38, 36),
        ]
        self.tiles = load_tiles(env_style, cubeSize)
        self.box_img, self.hole_img = self.tiles["box"], self.tiles["hole"]
        self.floor_img, self.stone_img = self.tiles["empty"], self.tiles["stone"]
        self.small_box, self.small_hole, self.small_stone = [
            pg.transform.scale(self.tiles[name], (int(0.52 * cubeSize),) * 2)
            for name in ("box", "hole", "stone")
        ]
        self.page, self.board_area, self.board_rect, self.sidebar = ui.workspace(
            self.x, self.y, cubeSize
        )
        self.pixelWidth, self.pixelHeight = self.board_rect.size
        left = self.sidebar.x + 20
        self.tile_buttons = [pg.Rect(left, 200 + i * 64, 224, 52) for i in range(3)]
        self.control_buttons = [pg.Rect(left, yy, 224, 48) for yy in (430, 490, 550)]
        self.last_mouse_click = [None, None]
        self.Done = self.save = self.back_to_gui = False
        self.saved_path = self.message = self.last_message = None
        self.message_until = 0
        self.to_change = []
        self.redrawPage()

    def check_legal_map(self, map):
        try:
            validate_map(map)
            return True
        except ValueError:
            return False

    def make_initial_map(self):
        return base_map(self.y - 2, self.x - 2)

    def redrawPage(self):
        ui.header(
            self.page,
            "Shape the challenge.",
            "Select a tile, then click the board. Click a placed tile to remove it.",
            "editor",
        )
        ui.panel(self.page, self.board_area)
        ui.panel(self.page, self.sidebar)
        self.drawTile(self.map)
        self.drawButtons()
        self.drawMessage()
        pg.display.update()

    def drawButtons(self):
        ui.text(
            self.page, "TILE PALETTE", (self.sidebar.x + 20, 154), 14, ui.ACCENT, True
        )
        for index, (rect, name, key) in enumerate(
            zip(self.tile_buttons, ("Hole", "Stone", "Box"), ("H", "S", "B"))
        ):
            ui.button(
                self.page,
                rect,
                f"{name}  [{key}]       {self.remained[index]} left",
                selected=self.active_buttons[index],
            )
        ui.text(
            self.page,
            f"{self.y - 2} rows × {self.x - 2} columns",
            (self.sidebar.x + 20, 396),
            17,
            ui.MUTED,
        )
        for rect, label in zip(
            self.control_buttons,
            ("Solve board / Enter", "Save JSON", "New board / Esc"),
        ):
            ui.button(self.page, rect, label, primary=rect == self.control_buttons[0])

    def drawLines(self):
        pass  # Board spacing is rendered by the shared tile renderer.

    def drawTile(self, array):
        draw_board(self.page, array, self.tiles, self.cubeSize, self.board_rect.topleft)

    def drawMessage(self):
        if self.message != self.last_message:
            self.last_message = self.message
            self.message_until = pg.time.get_ticks() + 5000
        if pg.time.get_ticks() >= self.message_until:
            self.message = self.last_message = None
        ui.notice(self.page, self.message)

    def colorCube(self, i, j, celltype):
        self.page.blit(
            self.tiles[celltype],
            (
                self.board_rect.x + self.pixelPos(i),
                self.board_rect.y + self.pixelPos(j),
            ),
        )

    def user_click(self, event=None):
        x, y = event.pos if event is not None else pg.mouse.get_pos()
        if self.board_rect.collidepoint(x, y):
            row, column = (
                self.whichTile(y - self.board_rect.y),
                self.whichTile(x - self.board_rect.x),
            )
            self.last_mouse_click = [row, column]
            self.update_map(row, column)
        else:
            self.update_buttons(x, y)

    def update_buttons(self, x, y):
        for index, rect in enumerate(self.tile_buttons):
            if rect.collidepoint(x, y):
                self.active_buttons = [i == index for i in range(3)]
                return
        if self.control_buttons[0].collidepoint(x, y):
            if sum(self.remained) == 0:
                self.Done = True
            else:
                self.message = "Place the remaining tiles before solving"
        elif self.control_buttons[1].collidepoint(x, y):
            self.save = True
        elif self.control_buttons[2].collidepoint(x, y):
            self.back_to_gui = True

    def update_map(self, row, column):
        value = self.map[row][column]
        changed = value != self.initial_map[row][column]
        if changed:
            self.remained[{-1: 0, -2: 1, 1: 2}[value]] += 1
            self.to_change = [row, column, self.initial_map[row][column]]
            return
        if not any(self.active_buttons):
            self.message = "Choose a tile: H hole, S stone, B box"
            return
        index = self.active_buttons.index(True)
        tile = (-1, -2, 1)[index]
        if self.remained[index] > 0 and (value == 0 or (tile == -2 and value == -1)):
            self.to_change = [row, column, tile]
            self.remained[index] -= 1
        else:
            self.message = "No tiles remaining, or this cell cannot hold that tile"

    def pixelPos(self, i):
        return i * (self.cubeSize + 1)

    def whichTile(self, pixel):
        return pixel // (self.cubeSize + 1)
