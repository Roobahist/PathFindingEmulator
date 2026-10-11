"""Shared desktop palette, typography and workspace geometry."""

import pygame as pg

BG = (250, 250, 249)
PANEL = (255, 255, 255)
FIELD = (239, 240, 241)
BORDER = (180, 184, 190)
TEXT = (30, 33, 38)
MUTED = (89, 94, 102)
ACCENT = (35, 78, 121)
INK = (255, 255, 255)


def text(screen, label, pos, size=20, color=TEXT, bold=False):
    font = pg.font.SysFont("Arial", size, bold=bold)
    image = font.render(str(label), True, color)
    screen.blit(image, pos)
    return image.get_rect(topleft=pos)


def panel(screen, rect, color=PANEL):
    pg.draw.rect(screen, color, rect, border_radius=0)


def button(screen, rect, label, primary=False, selected=False):
    hover = rect.collidepoint(pg.mouse.get_pos())
    panel(screen, rect, ACCENT if primary else FIELD if hover or selected else PANEL)
    pg.draw.rect(
        screen,
        ACCENT if selected else BORDER,
        rect,
        2 if selected else 1,
        border_radius=4,
    )
    font = pg.font.SysFont("Arial", 17)
    image = font.render(label, True, INK if primary else TEXT)
    screen.blit(image, image.get_rect(center=rect.center))


def header(screen, title, subtitle, section):
    screen.fill(BG)
    pg.draw.rect(screen, PANEL, (0, 0, screen.get_width(), 52))
    text(screen, "PathFinding", (32, 16), 17, bold=True)
    text(screen, "/  " + section.capitalize(), (146, 17), 16, MUTED)
    pg.draw.line(screen, BORDER, (0, 52), (screen.get_width(), 52))
    text(screen, title, (32, 72), 23, bold=True)
    text(screen, subtitle, (32, 104), 15, MUTED)
    pg.draw.line(
        screen,
        BORDER,
        (32, screen.get_height() - 64),
        (screen.get_width() - 32, screen.get_height() - 64),
    )


def workspace(cols, rows, size):
    width = max(960, cols * (size + 1) + 368)
    height = max(680, rows * (size + 1) + 192)
    page = pg.display.set_mode((width, height))
    area = pg.Rect(32, 128, width - 352, height - 192)
    board = pg.Rect(0, 0, cols * (size + 1) - 1, rows * (size + 1) - 1)
    board.center = area.center
    sidebar = pg.Rect(width - 296, 128, 264, height - 192)
    return page, area, board, sidebar


def notice(screen, message):
    if message:
        pg.draw.rect(
            screen, BG, (32, screen.get_height() - 63, screen.get_width() - 64, 63)
        )
        # Replace the footer hints with readable, wrapped feedback.
        words, line, lines = str(message).split(), "", []
        font = pg.font.SysFont("Arial", 17)
        for word in words:
            candidate = (line + " " + word).strip()
            if font.size(candidate)[0] > screen.get_width() - 80 and line:
                lines.append(line)
                line = word
            else:
                line = candidate
        lines.append(line)
        for index, line in enumerate(lines):
            text(screen, line, (40, screen.get_height() - 52 + index * 20), 17, ACCENT)
