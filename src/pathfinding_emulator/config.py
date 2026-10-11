"""Validated application settings and paths, assembled at the entry point."""

import math
from dataclasses import dataclass
from pathlib import Path

from .agents import ALGORITHMS

PACKAGE_DIR = Path(__file__).resolve().parent
ASSETS_DIR = PACKAGE_DIR / "assets"
SAMPLE_MAPS_DIR = PACKAGE_DIR / "sample_maps"
ARTWORK_THEMES = ("classic", "wood_stone", "lava", "grass_water")


@dataclass(frozen=True)
class Settings:
    maps_dir: Path = Path("maps")
    cell_size: int = 50
    delay: float = 1.0
    fps: int = 60
    max_steps: int = 10000
    max_nodes: int = 50000
    max_depth: int = 100
    seed: int | None = None
    algorithm: str = "random"

    def __post_init__(self):
        for name in ("cell_size", "fps", "max_steps", "max_nodes", "max_depth"):
            value = getattr(self, name)
            if type(value) is not int or value <= 0:
                raise ValueError(f"{name} must be a positive integer")
        if not 20 <= self.cell_size <= 100:
            raise ValueError("cell_size must be between 20 and 100 pixels")
        if not math.isfinite(self.delay) or not 0 <= self.delay <= 99:
            raise ValueError("delay must be between 0 and 99 seconds")
        if self.algorithm not in ALGORITHMS:
            raise ValueError(
                "algorithm must be random, A_Star, IDS, BFS, DFS, or Greedy"
            )
        object.__setattr__(self, "maps_dir", Path(self.maps_dir).expanduser().resolve())


def asset_path(*parts):
    """Resolve bundled artwork independently of the process working directory."""
    return str(ASSETS_DIR.joinpath(*(str(part) for part in parts)))


def validate_styles(env_style, agent_style):
    for name, value in (("Environment", env_style), ("Agent", agent_style)):
        if type(value) is not int or value not in range(4):
            raise ValueError(f"{name} style must be 0, 1, 2, or 3")
