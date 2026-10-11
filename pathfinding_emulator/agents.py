"""Bounded agents using the same transitions as the simulator."""

import random
from collections import deque
from dataclasses import dataclass
from functools import partial
from heapq import heappop, heappush
from itertools import count

from .environment import DIRECTIONS, Env, State

SEARCH_ALGORITHMS = ("A_Star", "IDS", "BFS", "DFS", "Greedy")
ALGORITHMS = ("random", *SEARCH_ALGORITHMS)


class NoSolutionError(ValueError):
    """The reachable search space was exhausted without a solution."""


class SearchLimitError(RuntimeError):
    """A configured resource limit was reached; solvability is unknown."""


@dataclass
class Action:
    x: int  # Historical API: x is row and y is column.
    y: int
    direction: str

    def __post_init__(self):
        self.update(self.x, self.y, self.direction)

    def update(self, i, j, direction):
        if (
            type(i) is not int
            or type(j) is not int
            or not isinstance(direction, str)
            or direction not in DIRECTIONS
        ):
            raise ValueError("Action requires integer row/column and a valid direction")
        self.x, self.y, self.direction = i, j, direction

    def return_action(self):
        return self.x, self.y, self.direction


def legal_moves(state):
    """Enumerate box pushes that actually change the board."""
    for row, cells in enumerate(state.map_array[1:-1], 1):
        for col, tile in enumerate(cells[1:-1], 1):
            if tile == 1:
                for direction in DIRECTIONS:
                    if state.inspect_action(row, col, direction)[1] in {
                        "empty",
                        "fire",
                    }:
                        yield Action(row, col, direction)


def children(env):
    for action in legal_moves(env.state):
        child = env.copy_env()
        child.take_action(action.return_action())
        yield child, action


def search_steps(grid, algorithm="A_Star", max_nodes=50000, max_depth=100):
    """Yield after each expansion for responsive GUI planning; return the plan.

    A_Star uses a zero heuristic (uniform-cost search), since the historical
    edge-distance heuristic overestimated costs and ignored internal holes.
    IDS and BFS return a shortest action sequence within the depth limit.
    DFS explores deeply; greedy favors boxes near holes. Neither is optimal.
    """
    if algorithm not in SEARCH_ALGORITHMS:
        raise ValueError("Unknown search algorithm")
    if any(type(n) is not int or n <= 0 for n in (max_nodes, max_depth)):
        raise ValueError("Search limits must be positive integers")
    root = Env(grid)
    expanded = 0
    if algorithm in {"BFS", "DFS"}:
        frontier = deque([(root, [])])
        reached = {root.state.key()[0]: 0}
        cutoff = False
        while frontier:
            env, plan = frontier.popleft() if algorithm == "BFS" else frontier.pop()
            if env.goal_test():
                return plan
            if expanded >= max_nodes:
                raise SearchLimitError(f"Search reached {max_nodes} expanded nodes")
            expanded += 1
            successors = list(children(env))
            if algorithm == "DFS":
                successors.reverse()
            for child, action in successors:
                key = child.state.key()[0]
                depth = len(plan) + 1
                if depth >= reached.get(key, float("inf")):
                    continue
                if depth > max_depth:
                    cutoff = True
                    continue
                reached[key] = depth
                frontier.append((child, plan + [action]))
            yield None
        if cutoff:
            raise SearchLimitError(f"Search reached depth {max_depth}")
        raise NoSolutionError("No solution: all reachable states were exhausted")

    if algorithm in {"A_Star", "Greedy"}:
        holes = [
            (r, c)
            for r, row in enumerate(grid)
            for c, tile in enumerate(row)
            if tile == -1
        ]

        def priority(env):
            if algorithm == "A_Star":
                return env.send_cost()
            # Greedy best-first follows proximity to holes; it makes no
            # cost/length optimality promise, particularly for chain pushes.
            return sum(
                min((abs(r - hr) + abs(c - hc) for hr, hc in holes), default=0)
                for r, row in enumerate(env.send_map())
                for c, tile in enumerate(row)
                if tile == 1
            )

        order = count()
        frontier = [(priority(root), next(order), 0, root, [])]
        reached = {root.state.key(): 0}
        while frontier:
            _, _, cost, env, plan = heappop(frontier)
            if cost != reached[env.state.key()]:
                continue
            if env.goal_test():
                return plan
            if expanded >= max_nodes:
                raise SearchLimitError(
                    f"Search reached {max_nodes} expanded nodes; raise --max-nodes or use a smaller map"
                )
            expanded += 1
            for child, action in children(env):
                key = child.state.key()
                if child.send_cost() < reached.get(key, float("inf")):
                    reached[key] = child.send_cost()
                    heappush(
                        frontier,
                        (
                            priority(child),
                            next(order),
                            child.send_cost(),
                            child,
                            plan + [action],
                        ),
                    )
            yield None
        raise NoSolutionError("No solution: all reachable states were exhausted")

    for limit in range(max_depth + 1):
        root_key = root.state.key()[0]
        stack = [(root, [], frozenset({root_key}))]
        cutoff = False
        while stack:
            env, plan, ancestors = stack.pop()
            if env.goal_test():
                return plan
            if expanded >= max_nodes:
                raise SearchLimitError(
                    f"Search reached {max_nodes} expanded nodes; raise --max-nodes or use a smaller map"
                )
            expanded += 1
            successors = [
                (child, action)
                for child, action in children(env)
                if child.state.key()[0] not in ancestors
            ]
            if len(plan) == limit:
                cutoff |= bool(successors)
            else:
                for child, action in reversed(successors):
                    stack.append(
                        (child, plan + [action], ancestors | {child.state.key()[0]})
                    )
            yield None
        if not cutoff:
            raise NoSolutionError("No solution: all reachable states were exhausted")
    raise SearchLimitError(
        f"Search reached depth {max_depth}; raise --max-depth or use a smaller map"
    )


def solve(grid, algorithm="A_Star", max_nodes=50000, max_depth=100):
    steps = search_steps(grid, algorithm, max_nodes, max_depth)
    while True:
        try:
            next(steps)
        except StopIteration as result:
            return result.value


class Agent:
    """Perception and randomness are supplied by the caller, without global state."""

    def __init__(
        self,
        env_perception,
        agent_type="random",
        rng=None,
        max_nodes=50000,
        max_depth=100,
    ):
        if agent_type not in ALGORITHMS:
            raise ValueError("Unknown agent type")
        self.perceive = env_perception
        self.agent_type = agent_type
        self.rng = rng if rng is not None else random.Random()
        self.max_nodes, self.max_depth = max_nodes, max_depth
        self.sequence = deque()
        self.done = False
        self.agent_type_dict = {
            name: partial(self.search_agent, name) for name in SEARCH_ALGORITHMS
        }
        self.agent_type_dict["random"] = self.random_agent

    def search_agent(self, algorithm):
        return solve(self.perceive(), algorithm, self.max_nodes, self.max_depth)

    def find_loc(self, gamemap, value):
        return [
            [r, c]
            for r, row in enumerate(gamemap)
            for c, tile in enumerate(row)
            if tile == value
        ]

    def random_agent(self):
        state = State(self.perceive())
        moves = list(legal_moves(state))
        if not moves:
            if not any(1 in row for row in state.map_array):
                raise StopIteration("All boxes have been removed")
            raise NoSolutionError(
                "No movable boxes; edit the map or try a search agent"
            )
        # Preserve the default edge-oriented policy, falling back to a legal
        # push when a stone blocks the preferred direction.
        boxes = sorted({(move.x, move.y) for move in moves})
        row, col = self.rng.choice(boxes)
        height, width = len(state.map_array), len(state.map_array[0])
        preferred = (
            ("up" if 2 * row < height else "down")
            if min(row, height - 1 - row) < min(col, width - 1 - col)
            else ("left" if 2 * col < width else "right")
        )
        options = [move for move in moves if (move.x, move.y) == (row, col)]
        return next(
            (move for move in options if move.direction == preferred),
            self.rng.choice(options),
        )

    def A_Star_agent(self):
        return solve(self.perceive(), "A_Star", self.max_nodes, self.max_depth)

    def IDS_agent(self):
        return solve(self.perceive(), "IDS", self.max_nodes, self.max_depth)

    def update_map(self, gamemap, i, j, direction):
        state = State(gamemap)
        state.update_map(i, j, direction)
        return state.map_array

    def act(self):
        if self.sequence:
            return self.sequence.popleft()
        if self.done:
            raise StopIteration("Plan exhausted")
        result = self.agent_type_dict[self.agent_type]()
        if isinstance(result, list):
            self.sequence.extend(result)
            self.done = True
            if not self.sequence:
                raise StopIteration("All boxes have been removed")
            return self.sequence.popleft()
        return result


class SearchAgent(Agent):
    def __init__(self, env_perception, algorithm="A_Star", **kwargs):
        super().__init__(env_perception, agent_type=algorithm, **kwargs)
        self.action_list = solve(
            self.perceive(), algorithm, self.max_nodes, self.max_depth
        )
        self.sequence.extend(self.action_list)
        self.done = True
