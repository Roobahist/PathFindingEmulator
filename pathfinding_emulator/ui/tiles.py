"""Shared theme loading and board rendering for editor and solver."""

import pygame as pg

from ..config import asset_path

TILE_NAMES = ("stone", "hole", "empty", "box")


def load_tiles(style, size):
    return {
        name: pg.transform.scale(
            pg.image.load(asset_path("env", style, filename + ".jpg")), (size, size)
        )
        for name, filename in (
            ("stone", "stone"),
            ("hole", "hole"),
            ("empty", "floor"),
            ("box", "box"),
        )
    }


def draw_board(screen, grid, tiles, size, origin=(0, 0)):
    for row, cells in enumerate(grid):
        for col, tile in enumerate(cells):
            screen.blit(
                tiles[TILE_NAMES[tile + 2]],
                (origin[0] + col * (size + 1), origin[1] + row * (size + 1)),
            )
