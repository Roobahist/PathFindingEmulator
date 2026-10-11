import os

from ..config import asset_path

os.environ["PYGAME_HIDE_SUPPORT_PROMPT"] = "hide"
import math
import sys

import pygame as pg


class InputBox:
    def __init__(self, x, y, w, h, font_size=32, text="", maximum_lengh=sys.maxsize):
        self.w = w
        self.h = h
        self.ml = maximum_lengh
        self.font = pg.font.Font(None, font_size)
        self.COLOR_INACTIVE = pg.Color("red")
        self.COLOR_ACTIVE = pg.Color("green")
        self.rect = pg.Rect(x, y, w, h)
        self.color = (255, 255, 255)
        self.fillcolor = (90, 90, 90)
        self.text = text
        self.txt_surface = self.font.render(text, True, self.color)
        self.active = False
        self.changed = True

    def draw(self, screen):
        pg.draw.rect(screen, self.fillcolor, self.rect)
        pg.draw.rect(screen, self.color, self.rect, 3 if self.active else 2)
        self.txt_surface = self.font.render(self.text, True, (255, 255, 255))
        old_clip = screen.get_clip()
        screen.set_clip(self.rect.inflate(-8, -4))
        x = min(self.rect.x + 5, self.rect.right - 5 - self.txt_surface.get_width())
        screen.blit(self.txt_surface, (x, self.rect.y + 5))
        screen.set_clip(old_clip)


class GUI:
    def __init__(self, map_path="maps/", env_style=1, agent_style=1):
        pg.init()
        pg.font.init()

        self.pixelHeight = 400
        self.pixelWidth = 400

        self.colors = [(180, 180, 180), (0, 66, 94), (255, 255, 255)]

        self.bg = pg.image.load(asset_path("bg.png"))
        self.bg = pg.transform.scale(self.bg, (self.pixelHeight, self.pixelWidth))
        self.back = pg.image.load(asset_path("back.png"))
        self.back = pg.transform.scale(self.back, (45, 45))

        self.font = pg.font.SysFont("arial", 25)

        self.which_page = 0
        self.pages = [
            self.main_page,
            self.load_map_page,
            self.create_map_page,
            self.design_map_page,
        ]

        self.page = pg.display.set_mode((self.pixelWidth, self.pixelHeight))

        self.map_path = map_path
        self.default_env_style = env_style
        self.default_agent_style = agent_style
        self.page_buttons = self.make_input_boxes()
        self.inputs = [[], [], [], []]
        self.env_style = env_style
        self.agent_style = agent_style

        self.Done = False
        self.command = ""
        self.message = None
        self.message_until = 0
        self.last_message = None

        self.draw()

    def make_input_boxes(self):
        path_1 = InputBox(50, 110, 300, 31, text=self.map_path)

        env_style_2 = InputBox(
            260, 71, 45, 31, text=str(self.default_env_style), maximum_lengh=2
        )
        agent_style_2 = InputBox(
            260, 121, 45, 31, text=str(self.default_agent_style), maximum_lengh=2
        )
        height_2 = InputBox(260, 171, 45, 31, text="2", maximum_lengh=2)
        width_2 = InputBox(260, 221, 45, 31, text="2", maximum_lengh=2)

        env_style_3 = InputBox(
            265, 35, 45, 31, text=str(self.default_env_style), maximum_lengh=2
        )
        agent_style_3 = InputBox(
            145, 101, 45, 31, text=str(self.default_agent_style), maximum_lengh=2
        )
        height_3 = InputBox(145, 151, 45, 31, text="2", maximum_lengh=2)
        width_3 = InputBox(145, 201, 45, 31, text="2", maximum_lengh=2)
        boxes_3 = InputBox(346, 101, 45, 31, maximum_lengh=3)
        extra_holes_3 = InputBox(346, 151, 45, 31, maximum_lengh=3)
        obstacles_3 = InputBox(346, 201, 45, 31, maximum_lengh=3)

        return [
            [],
            [path_1],
            [env_style_2, agent_style_2, height_2, width_2],
            [
                env_style_3,
                agent_style_3,
                height_3,
                width_3,
                boxes_3,
                extra_holes_3,
                obstacles_3,
            ],
        ]

    def draw(self):
        self.page.fill(self.colors[0])
        self.page.blit(self.bg, (0, 0))
        if self.which_page != 0:
            self.page.blit(self.back, (50, 300))
            pg.draw.rect(self.page, self.colors[1], (150, 300, 100, 45))
            pg.draw.rect(self.page, self.colors[2], (150, 300, 100, 45), 2)
            message = "OK"
            text = self.font.render(message, True, self.colors[2])
            self.page.blit(text, (185, 308))

        self.pages[self.which_page]()
        self.drawMessage()

    def drawMessage(self):
        if self.message is not None and type(self.message) is str:
            pg.font.init()
            text = pg.font.Font(None, 22).render(self.message, True, pg.Color("white"))
            if text.get_width() > 380:
                text = pg.transform.smoothscale(text, (380, text.get_height()))
            self.page.blit(text, (10, 265))
            pg.display.update()
            self.expire_message()

    def main_page(self):
        # (x_start , y_start , +x , +y)
        pg.draw.rect(self.page, self.colors[1], (60, 80, 280, 60))
        pg.draw.rect(self.page, self.colors[2], (60, 80, 280, 60), 2)
        message = "Load Map"
        text = self.font.render(message, True, self.colors[2])
        self.page.blit(text, (150, 95))

        pg.draw.rect(self.page, self.colors[1], (60, 170, 280, 60))
        pg.draw.rect(self.page, self.colors[2], (60, 170, 280, 60), 2)
        message = "Create Random Map"
        text = self.font.render(message, True, self.colors[2])
        self.page.blit(text, (110, 185))

        pg.draw.rect(self.page, self.colors[1], (60, 260, 280, 60))
        pg.draw.rect(self.page, self.colors[2], (60, 260, 280, 60), 2)
        message = "Design Map"
        text = self.font.render(message, True, self.colors[2])
        self.page.blit(text, (147, 275))

        pg.display.update()

    def load_map_page(self):
        message = "Path :"
        text = self.font.render(message, True, self.colors[2])
        self.page.blit(text, (50, 70))

        text_boxes = self.page_buttons[1]

        for text_box in text_boxes:
            text_box.draw(self.page)

        pg.display.update()

    def create_map_page(self):
        self.draw_fields(2, ("Environment style", "Agent style", "Height", "Width"))

    def design_map_page(self):
        self.default_text_calculator()
        self.draw_fields(
            3,
            (
                "Environment style",
                "Agent style",
                "Height",
                "Width",
                "Boxes",
                "Extra holes",
                "Obstacles",
            ),
        )

    def draw_fields(self, page, labels):
        font = pg.font.Font(None, 26)
        for box, label in zip(self.page_buttons[page], labels):
            text = font.render(label, True, self.colors[2])
            self.page.blit(
                text, text.get_rect(midright=(box.rect.x - 10, box.rect.centery))
            )
            box.draw(self.page)
        pg.display.update()

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
            if 60 <= x <= 340:
                if 80 <= y <= 140:
                    self.which_page = 1

                elif 170 <= y <= 230:
                    self.which_page = 2

                elif 260 <= y <= 320:
                    self.which_page = 3

        if page in [1, 2, 3]:
            # Back button
            if 50 <= x <= 95 and 300 <= y <= 345:
                self.which_page = 0

            # text boxes
            for button in self.page_buttons[page]:
                if button.rect.collidepoint(event.pos):
                    button.active = not button.active

                else:
                    button.active = False
                button.color = (
                    button.COLOR_ACTIVE if button.active else button.COLOR_INACTIVE
                )

            # OK button
            if 150 <= x <= 250 and 300 <= y <= 345:
                page_inputs = []
                buttons = self.page_buttons[page]
                for index, button in enumerate(buttons):
                    if button.text.isdecimal():
                        page_inputs.append(int(button.text))

                    elif page == 1:
                        page_inputs.append(button.text)

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
            self.user_click(pg.event.Event(pg.MOUSEBUTTONDOWN, pos=(200, 320)))
            return
        if page == 0:
            pass

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
