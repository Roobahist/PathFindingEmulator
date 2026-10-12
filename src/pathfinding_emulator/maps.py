"""Validated JSON persistence, restricted legacy import, and bounded generation."""

import io
import json
import pickle
import pickletools
import random
from pathlib import Path

from .config import SAMPLE_MAPS_DIR, validate_styles
from .environment import base_map, validate_map
from .utils import possible_locs

MAX_MAP_BYTES = 1024 * 1024
# Legacy maps only need lists, integers, and memo references. Reject executable
# opcodes before unpickling; find_class adds a second boundary against globals.
LEGACY_OPCODES = {
    "PROTO",
    "FRAME",
    "STOP",
    "MARK",
    "EMPTY_LIST",
    "LIST",
    "APPEND",
    "APPENDS",
    "INT",
    "BININT",
    "BININT1",
    "BININT2",
    "LONG",
    "LONG1",
    "LONG4",
    "PUT",
    "BINPUT",
    "LONG_BINPUT",
    "GET",
    "BINGET",
    "LONG_BINGET",
    "MEMOIZE",
}


class MapUnpickler(pickle.Unpickler):
    def find_class(self, module, name):
        raise pickle.UnpicklingError("Legacy maps cannot reference Python objects")


def load_map(path):
    """Load JSON or a legacy list-of-integers pickle without executable opcodes."""
    path = Path(path)
    with path.open("rb") as source:
        data = source.read(MAX_MAP_BYTES + 1)
    if len(data) > MAX_MAP_BYTES:
        raise ValueError("Map exceeds the 1 MiB file limit")
    try:
        if path.suffix == ".pickle":
            for operation, argument, _ in pickletools.genops(data):
                if operation.name not in LEGACY_OPCODES:
                    raise ValueError(
                        "Legacy map contains unsupported or unsafe pickle operations"
                    )
                if operation.name in {
                    "PUT",
                    "BINPUT",
                    "LONG_BINPUT",
                    "GET",
                    "BINGET",
                    "LONG_BINGET",
                }:
                    if not 0 <= int(argument) <= 20000:
                        raise ValueError(
                            "Legacy map memo reference exceeds the resource limit"
                        )
            grid = MapUnpickler(io.BytesIO(data)).load()
        elif path.suffix == ".json":
            grid = json.loads(data)
        else:
            raise ValueError("Map extension must be .json or .pickle")
        return validate_map(grid)
    except (
        pickle.UnpicklingError,
        EOFError,
        RecursionError,
        UnicodeError,
        json.JSONDecodeError,
        OverflowError,
    ) as error:
        raise ValueError(f"Invalid map file: {error}") from error


class ChallengeDesigner:
    def __init__(self, maps_dir="maps", rng=None):
        self.mapArr = None
        self.maps_dir = Path(maps_dir).expanduser().resolve()
        self.rng = rng if rng is not None else random.Random()

    def run(self, command, inputs):
        if command == "load_map":
            self.load_map(*inputs[1])
        elif command == "create_random_map":
            self.create_random_map(*inputs[2])
        elif command == "design_map":
            validate_styles(*inputs[3][:2])
            self.base_map(inputs[3][2], inputs[3][3])
        else:
            raise ValueError("Choose load_map, create_random_map, or design_map")
        return self.mapArr

    def base_map(self, height, width):
        self.mapArr = base_map(height, width)

    def update_map(self, row, column, value):
        candidate = [cells[:] for cells in self.mapArr]
        candidate[row][column] = value
        validate_map(candidate)
        self.mapArr = candidate

    def create_random_map(self, env_style, agent_style, height, width):
        """Generate using interior dimensions consistently with the design screen.

        Reverse walks from holes place distinct boxes. Generation is bounded;
        obstacle arrangements are not guaranteed to be solvable.
        """
        validate_styles(env_style, agent_style)
        grid = base_map(height, width)
        locations = [(r, c) for r in range(1, height + 1) for c in range(1, width + 1)]
        for row, col in self.rng.sample(locations, int(0.05 * height * width)):
            grid[row][col] = -2
        holes = [
            (r, c)
            for r, cells in enumerate(grid)
            for c, value in enumerate(cells)
            if value == -1
        ]
        target = int(0.5 * height * width)
        for _ in range(target):
            starts = [hole for hole in holes if possible_locs(hole, grid)]
            if not starts:
                raise ValueError(
                    "Cannot place more boxes; retry with a different seed or board size"
                )
            current = self.rng.choice(starts)
            for _ in range(self.rng.randint(1, max(1, height * width // 2))):
                available = possible_locs(current, grid)
                if not available:
                    break
                current = self.rng.choice(available)
            grid[current[0]][current[1]] = 1
        self.mapArr = validate_map(grid)

    def load_map(self, path):
        # Accept historical Windows-style paths and extensionless map names.
        path = Path(str(path).replace("\\", "/")).expanduser()
        candidates = (
            [path]
            if path.suffix
            else [path.with_suffix(s) for s in (".json", ".pickle")]
        )
        for candidate in candidates:
            if candidate.is_file():
                self.mapArr = load_map(candidate)
                return self.mapArr
        # An explicit custom directory must never silently select a sample.
        if not path.is_absolute() and (
            path.parent == Path(".") or path.parent == Path("maps")
        ):
            for directory in (self.maps_dir, SAMPLE_MAPS_DIR):
                for candidate in candidates:
                    resolved = directory / candidate.name
                    if resolved.is_file():
                        self.mapArr = load_map(resolved)
                        return self.mapArr
        raise FileNotFoundError(f"Map not found: {path}. Use a .json or .pickle file")

    def save_map(self, map_array):
        """Create a new JSON file exclusively, never replacing an existing map."""
        payload = json.dumps(validate_map(map_array), indent=2) + "\n"
        self.maps_dir.mkdir(parents=True, exist_ok=True)
        index = 0
        while True:
            path = self.maps_dir / f"map_{index}.json"
            # Avoid reusing names of the bundled/legacy pickle maps.
            if (
                path.with_suffix(".pickle").exists()
                or (SAMPLE_MAPS_DIR / path.name).exists()
            ):
                index += 1
                continue
            try:
                with path.open("x", encoding="utf-8") as destination:
                    destination.write(payload)
                return str(path)
            except FileExistsError:
                index += 1
