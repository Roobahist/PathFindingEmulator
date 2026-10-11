import math
import os
import sys

os.environ["PYGAME_HIDE_SUPPORT_PROMPT"] = "hide"
import pygame as pg

from ..config import SAMPLE_MAPS_DIR
from ..maps import load_map
from . import theme as ui
from .tiles import draw_board, load_tiles


class InputBox:
    def __init__(self, x, y, w, h, font_size=24, text="", maximum_lengh=sys.maxsize):
        self.w, self.h, self.ml = w, h, maximum_lengh
        self.font = pg.font.SysFont("Arial", font_size)
        self.COLOR_INACTIVE, self.COLOR_ACTIVE = ui.BORDER, ui.ACCENT
        self.rect = pg.Rect(x, y, w, h)
        self.color, self.fillcolor = ui.TEXT, ui.FIELD
        self.text, self.active, self.changed = text, False, True
        self.txt_surface = self.font.render(text, True, self.color)

    def draw(self, screen):
        ui.panel(screen, self.rect, self.fillcolor)
        pg.draw.rect(
            screen,
            ui.ACCENT if self.active else ui.BORDER,
            self.rect,
            2 if self.active else 1,
            border_radius=4,
        )
        self.txt_surface = self.font.render(self.text, True, ui.TEXT)
        old_clip = screen.get_clip()
        screen.set_clip(self.rect.inflate(-20, -4))
        x = min(self.rect.x + 10, self.rect.right - 10 - self.txt_surface.get_width())
        screen.blit(
            self.txt_surface,
            (x, self.rect.centery - self.txt_surface.get_height() // 2),
        )
        screen.set_clip(old_clip)


class GUI:
    titles = (
        "Boards",
        "Open a saved board",
        "Random board",
        "New board",
    )
    descriptions = (
        "Open an existing puzzle or create a new one.",
        "Load a JSON file or a bundled sample such as map_10.",
        "Set the dimensions for a generated puzzle.",
        "Set the dimensions and number of tiles to place.",
    )
    labels = (
        (),
        ("Map path or sample name",),
        ("Board artwork (0–3)", "Agent artwork (0–3)", "Rows (1–20)", "Columns (1–20)"),
        (
            "Board artwork (0–3)",
            "Agent artwork (0–3)",
            "Rows (1–20)",
            "Columns (1–20)",
            "Boxes",
            "Extra holes",
            "Stones",
        ),
    )

    def __init__(self, map_path="maps/", env_style=1, agent_style=1):
        pg.init()
        self.pixelWidth, self.pixelHeight = 960, 680
        self.page = pg.display.set_mode((960, 680))
        self.which_page = 0
        self.map_path = map_path
        self.default_env_style, self.default_agent_style = env_style, agent_style
        self.env_style, self.agent_style = env_style, agent_style
        self.navigation_buttons = [
            pg.Rect(48, 220 + i * 100, 384, 88) for i in range(3)
        ]
        self.preview_grid = load_map(SAMPLE_MAPS_DIR / "map_1.pickle")
        self.preview_tiles = load_tiles(env_style, 48)
        self.back_button = pg.Rect(56, 550, 150, 48)
        self.submit_button = pg.Rect(692, 550, 212, 48)
        self.page_buttons = self.make_input_boxes()
        self.inputs = [[], [], [], []]
        self.Done, self.command = False, ""
        self.message = self.last_message = None
        self.message_until = 0
        self.draw()

    def make_input_boxes(self):
        result = [[], [InputBox(56, 260, 848, 52, text=self.map_path)], [], []]
        for page in (2, 3):
            values = [
                str(self.default_env_style),
                str(self.default_agent_style),
                "2",
                "2",
            ]
            if page == 3:
                values += ["", "", ""]
            result[page] = [
                InputBox(
                    56 + (i % 4) * 216,
                    242 + (i // 4) * 100,
                    200,
                    48,
                    text=value,
                    maximum_lengh=3,
                )
                for i, value in enumerate(values)
            ]
        return result

    def draw(self):
        page = self.which_page
        ui.header(self.page, self.titles[page], self.descriptions[page], "workspace")
        if page == 0:
            self.main_page()
        else:
            ui.text(
                self.page,
                ("File", "Board settings", "Board settings")[page - 1],
                (56, 185),
                17,
                ui.TEXT,
                True,
            )
            if page == 3:
                self.default_text_calculator()
            self.draw_fields(page, self.labels[page])
            ui.text(
                self.page,
                "Interior dimensions exclude the border. Artwork styles: 0, 1, 2, 3.",
                (56, 490),
                17,
                ui.MUTED,
            )
            ui.button(self.page, self.back_button, "Back")
            ui.button(
                self.page,
                self.submit_button,
                "Open board" if page == 1 else "Create board",
                primary=True,
            )
        self.drawMessage()
        pg.display.update()

    def main_page(self):
        ui.text(self.page, "Open or create", (48, 172), 17, bold=True)
        titles = ("Open board", "Random board", "New board")
        details = (
            "Load a saved file or a sample map.",
            "Generate a board with random tiles.",
            "Set the size and place tiles yourself.",
        )
        for index, rect in enumerate(self.navigation_buttons):
            if rect.collidepoint(pg.mouse.get_pos()):
                ui.panel(self.page, rect, ui.FIELD)
            ui.text(self.page, titles[index], (rect.x + 16, rect.y + 15), 19, bold=True)
            ui.text(self.page, details[index], (rect.x + 16, rect.y + 46), 15, ui.MUTED)
            ui.text(
                self.page, str(index + 1), (rect.right - 32, rect.y + 18), 16, ui.MUTED
            )
            pg.draw.line(
                self.page,
                ui.BORDER,
                (rect.x + 16, rect.bottom),
                (rect.right - 16, rect.bottom),
            )
        pg.draw.line(self.page, ui.BORDER, (480, 172), (480, 560))
        ui.text(self.page, "Sample board", (532, 172), 17, bold=True)
        draw_board(self.page, self.preview_grid, self.preview_tiles, 48, (532, 218))
        ui.text(self.page, "map_1 · 5 × 5 interior", (532, 573), 15, ui.MUTED)
        ui.text(
            self.page,
            "1–3  Choose a workflow     Tab  Next field     Enter  Continue",
            (32, 636),
            15,
            ui.MUTED,
        )

    def load_map_page(self):
        self.draw_fields(1, self.labels[1])

    def create_map_page(self):
        self.draw_fields(2, self.labels[2])

    def design_map_page(self):
        self.default_text_calculator()
        self.draw_fields(3, self.labels[3])

    def draw_fields(self, page, labels):
        for box, label in zip(self.page_buttons[page], labels):
            ui.text(self.page, label, (box.rect.x, box.rect.y - 28), 17, ui.MUTED)
            box.draw(self.page)

    def drawMessage(self):
        if self.message:
            self.expire_message()
            ui.notice(self.page, self.message)

    def default_text_calculator(self):
        if (
            self.page_buttons[3][2].text.isdigit()
            and self.page_buttons[3][3].text.isdigit()
        ):
            if self.page_buttons[3][2].changed or self.page_buttons[3][3].changed:
                self.page_buttons[3][2].changed = False
                self.page_buttons[3][3].changed = False

                N = int(self.page_buttons[3][2].text) * int(
                    self.page_buttons[3][3].text
                )
                self.page_buttons[3][4].text = str(math.floor(0.5 * N))
                self.page_buttons[3][5].text = str(0)
                self.page_buttons[3][6].text = str(math.floor(0.05 * N))

    def user_click(self, event=None):
        x, y = event.pos if event is not None else pg.mouse.get_pos()
        page = self.which_page

        if page == 0:
            for index, rect in enumerate(self.navigation_buttons, 1):
                if rect.collidepoint(x, y):
                    self.which_page = index

        if page in [1, 2, 3]:
            # Back button
            if self.back_button.collidepoint(x, y):
                self.which_page = 0

            # text boxes
            for button in self.page_buttons[page]:
                if button.rect.collidepoint(x, y):
                    button.active = not button.active

                else:
                    button.active = False
                button.color = (
                    button.COLOR_ACTIVE if button.active else button.COLOR_INACTIVE
                )

            # OK button
            if self.submit_button.collidepoint(x, y):
                page_inputs = []
                buttons = self.page_buttons[page]
                for index, button in enumerate(buttons):
                    if page == 1:
                        page_inputs.append(button.text)

                    elif button.text.isdecimal():
                        page_inputs.append(int(button.text))

                    elif page == 3 and index >= 4 and not button.text:
                        page_inputs.append(0)
                    else:
                        self.message = (
                            "Use whole numbers for styles, dimensions and tile counts"
                        )
                        self.Done = False
                        return

                self.inputs[page] = page_inputs
                self.Done = True

                if page == 1:
                    self.command = "load_map"

                elif page == 2:
                    self.command = "create_random_map"
                    self.env_style = page_inputs[0]
                    self.agent_style = page_inputs[1]

                elif page == 3:
                    self.command = "design_map"
                    self.env_style = page_inputs[0]
                    self.agent_style = page_inputs[1]

    def user_write(self, event=None):
        page = self.which_page
        if event.key == pg.K_ESCAPE:
            self.which_page = 0
            return
        if page and event.key == pg.K_TAB:
            boxes = self.page_buttons[page]
            active = next((i for i, box in enumerate(boxes) if box.active), -1)
            next_index = (active + 1) % len(boxes)
            for i, box in enumerate(boxes):
                box.active = i == next_index
                box.color = box.COLOR_ACTIVE if box.active else box.COLOR_INACTIVE
            return
        if page and event.key == pg.K_RETURN:
            self.user_click(
                pg.event.Event(pg.MOUSEBUTTONDOWN, pos=self.submit_button.center)
            )
            return
        if page == 0 and event.key in (pg.K_1, pg.K_2, pg.K_3):
            self.which_page = event.key - pg.K_1 + 1

        if page in [1, 2, 3]:
            for button in self.page_buttons[page]:
                if button.active:
                    if event.key == pg.K_BACKSPACE:
                        button.text = button.text[:-1]
                    else:
                        if len(button.text) + 1 <= button.ml:
                            if event.unicode.isprintable():
                                button.text += event.unicode

                    button.changed = True
                    button.txt_surface = button.font.render(
                        button.text, True, button.color
                    )

            pg.display.flip()

    def expire_message(self):
        if self.message != self.last_message:
            self.last_message = self.message
            self.message_until = pg.time.get_ticks() + 3000
        elif pg.time.get_ticks() >= self.message_until:
            self.message = None
            self.last_message = None
