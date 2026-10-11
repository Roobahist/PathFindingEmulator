"""Shared desktop palette, typography and workspace geometry."""

import pygame as pg

BG = (15, 21, 32)
PANEL = (24, 33, 47)
FIELD = (34, 45, 62)
BORDER = (65, 83, 104)
TEXT = (239, 245, 250)
MUTED = (169, 186, 205)
ACCENT = (91, 226, 191)
INK = (12, 38, 34)


def text(screen, label, pos, size=20, color=TEXT, bold=False):
    font = pg.font.SysFont("Arial", size, bold=bold)
    image = font.render(str(label), True, color)
    screen.blit(image, pos)
    return image.get_rect(topleft=pos)


def panel(screen, rect, color=PANEL):
    pg.draw.rect(screen, color, rect, border_radius=16)


def button(screen, rect, label, primary=False, selected=False):
    hover = rect.collidepoint(pg.mouse.get_pos())
    panel(screen, rect, ACCENT if primary else FIELD if hover or selected else PANEL)
    pg.draw.rect(
        screen,
        ACCENT if selected else BORDER,
        rect,
        2 if selected else 1,
        border_radius=12,
    )
    font = pg.font.SysFont("Arial", 18, bold=True)
    image = font.render(label, True, INK if primary else TEXT)
    screen.blit(image, image.get_rect(center=rect.center))


def header(screen, title, subtitle, section):
    screen.fill(BG)
    text(screen, "PATHFINDING / " + section.upper(), (32, 22), 14, ACCENT, True)
    text(screen, title, (32, 48), 30, bold=True)
    text(screen, subtitle, (32, 88), 17, MUTED)


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
        # Wrap instead of shrinking text, preserving readable error messages.
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
