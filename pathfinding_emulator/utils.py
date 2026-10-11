"""Small shared board helpers, independent of Pygame."""

from .environment import base_map

__all__ = ["base_map", "possible_locs", "show"]


def possible_locs(location, map):
    row, col = location
    return [
        [r, c]
        for r, c in ((row + 1, col), (row - 1, col), (row, col + 1), (row, col - 1))
        if 0 <= r < len(map) and 0 <= c < len(map[0]) and map[r][c] == 0
    ]


def show(array):
    for row in array:
        print(" , ".join(str(tile).zfill(2) for tile in row))
