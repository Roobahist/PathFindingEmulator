"""Display-independent puzzle rules and the original continuation scoring."""

from copy import deepcopy

DIRECTIONS = {"up": (-1, 0), "down": (1, 0), "left": (0, -1), "right": (0, 1)}
TILES = {-2, -1, 0, 1}  # Stone, hole, floor, box; persisted map format.
START_COST = 4
MAX_SIDE = 100


def validate_map(grid):
    """Require a rectangular integer grid enclosed by holes or stones."""
    if not isinstance(grid, list) or not 3 <= len(grid) <= MAX_SIDE + 2:
        raise ValueError("Map must have 1–100 interior rows and a border")
    if not isinstance(grid[0], list) or not 3 <= len(grid[0]) <= MAX_SIDE + 2:
        raise ValueError("Map must have 1–100 interior columns and a border")
    width = len(grid[0])
    for row, cells in enumerate(grid):
        if not isinstance(cells, list) or len(cells) != width:
            raise ValueError("Map rows must have equal lengths")
        for column, tile in enumerate(cells):
            if type(tile) is not int or tile not in TILES:
                raise ValueError("Map cells must be integers -2, -1, 0, or 1")
            if row in (0, len(grid) - 1) or column in (0, width - 1):
                if tile not in {-2, -1}:
                    raise ValueError("Border cells must be holes or stones")
    return grid


def base_map(height, width):
    """Create a board with the requested interior dimensions and hole border."""
    if any(type(n) is not int or not 1 <= n <= MAX_SIDE for n in (height, width)):
        raise ValueError("Height and width must be integers between 1 and 100")
    return [
        [
            -1 if row in (0, height + 1) or col in (0, width + 1) else 0
            for col in range(width + 2)
        ]
        for row in range(height + 2)
    ]


class State:
    def __init__(self, map):
        self.map_array = deepcopy(validate_map(map))
        self.previous_map = deepcopy(self.map_array)
        self.cost = 0
        self.no_initial_cost_move = (-1, -1, "left")
        self.prev_num_box = 0
        self.last_state = None
        self.number_of_boxes = 0
        self.v = self.h = 0

    def validate_action(self, action):
        if not isinstance(action, (tuple, list)) or len(action) != 3:
            return False
        row, col, direction = action
        return (
            type(row) is int
            and type(col) is int
            and isinstance(direction, str)
            and direction in DIRECTIONS
            and 1 <= row < len(self.map_array) - 1
            and 1 <= col < len(self.map_array[0]) - 1
        )

    def inspect_action(self, row, col, direction):
        """Return the contiguous box count and first non-box tile."""
        if not self.validate_action((row, col, direction)):
            raise ValueError(
                "Action must be (interior row, interior column, valid direction)"
            )
        if self.map_array[row][col] != 1:
            return 0, "no box"
        dr, dc = DIRECTIONS[direction]
        count = 0
        while self.map_array[row][col] == 1:
            count += 1
            row, col = row + dr, col + dc
        return count, {-1: "fire", -2: "stone", 0: "empty"}[self.map_array[row][col]]

    def update(self, row, col, direction):
        self.inspect_action(
            row, col, direction
        )  # Reject invalid actions before mutation.
        self.previous_map = deepcopy(self.map_array)
        self.update_score(row, col, direction)
        self.update_map(row, col, direction)

    def update_score(self, row, col, direction):
        count, outcome = self.inspect_action(row, col, direction)
        continuation = (row, col, direction) == self.no_initial_cost_move
        previous_count = self.prev_num_box * 2 if continuation else self.prev_num_box
        penalty = 0 if continuation else START_COST
        if count > previous_count:
            penalty = START_COST
        self.v, self.h = DIRECTIONS[direction]
        self.number_of_boxes, self.last_state = count, outcome
        if outcome == "no box":
            self.no_initial_cost_move = (-1, -1, "left")
        elif outcome == "stone":
            self.no_initial_cost_move = (row, col, direction)
        else:
            self.no_initial_cost_move = (row + self.v, col + self.h, direction)
        self.prev_num_box = count
        self.cost += penalty + count

    def update_map(self, row, col, direction):
        count, outcome = self.inspect_action(row, col, direction)
        if outcome in {"empty", "fire"}:
            dr, dc = DIRECTIONS[direction]
            self.map_array[row][col] = 0
            if outcome == "empty":
                self.map_array[row + dr * count][col + dc * count] = 1

    def key(self):
        """Search identity includes history that affects the next move's cost."""
        return (
            tuple(tuple(row) for row in self.map_array),
            self.no_initial_cost_move,
            self.prev_num_box,
        )


class Env:
    def __init__(self, map):
        self.state = State(map)

    def __eq__(self, other):
        return isinstance(other, Env) and self.state.key() == other.state.key()

    def take_action(self, action):
        self.state.update(*action)

    def send_map(self):
        return deepcopy(self.state.map_array)

    def send_cost(self):
        return self.state.cost

    def copy_env(self):
        return deepcopy(self)

    def goal_test(self):
        return not any(1 in row for row in self.state.map_array)
