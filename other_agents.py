"""Historical educational policies; the supported launcher uses ai.Agent.

These stochastic policies intentionally include ineffective pushes. They do
not guarantee completion; perception and randomness can be supplied for study.
"""

import random
from math import exp

from ai import Action


class AgentInspiration:
    def __init__(self, env_percption, rng=None):
        self.rng = rng if rng is not None else random.Random()
        self.agent_type = "NErSimAnealAgent"
        self.agent_type_dict = {
            name: getattr(self, name)
            for name in (
                "BruteRandomAgent",
                "WiseRandomAgent",
                "EdgeOrientedAgent",
                "NearestEdgeAgent",
                "NErandAgent",
                "NErSimAnealAgent",
                "NE1memAgent",
            )
        }
        self.push_on = self.push_dir = self.last_push_on = None
        self.perceive = env_percption
        self.sequence = []
        self.t = 0

    def act(self):
        if self.sequence:
            return self.sequence.pop(0)
        if not any(1 in row for row in self.perceive()):
            raise StopIteration("All boxes have been removed")
        result = self.agent_type_dict[self.agent_type]()
        if isinstance(result, list) and all(
            isinstance(action, Action) for action in result
        ):
            if not result:
                raise StopIteration("Plan exhausted")
            self.sequence = result
            return self.sequence.pop(0)
        if not isinstance(result, Action):
            raise TypeError("Agent must return an Action or list of Actions")
        self.push_on = (result.x, result.y)
        self.push_dir = result.direction
        return result

    def choose_box(self, grid):
        boxes = [
            (r, c)
            for r, row in enumerate(grid)
            for c, tile in enumerate(row)
            if tile == 1
        ]
        if not boxes:
            raise StopIteration("All boxes have been removed")
        return self.rng.choice(boxes)

    def choose_again(self, grid):
        return (
            not self.push_dir
            or grid[self.push_on[0]][self.push_on[1]] != 1
            or self.rng.random() > 0.75
        )

    def random_direction(self):
        return self.rng.choice(["right", "left", "up", "down"])

    def edge_direction(self, grid, row, col, vertical=None):
        height, width = len(grid), len(grid[0])
        if vertical is None:
            vertical = min(row, height - 1 - row) < min(col, width - 1 - col)
        if vertical:
            return "up" if 2 * row < height else "down"
        return "left" if 2 * col < width else "right"

    def BruteRandomAgent(self):
        grid = self.perceive()
        if self.choose_again(grid):
            return Action(
                self.rng.randint(1, len(grid) - 2),
                self.rng.randint(1, len(grid[0]) - 2),
                self.random_direction(),
            )
        return Action(*self.push_on, self.push_dir)

    def WiseRandomAgent(self):
        grid = self.perceive()
        if self.choose_again(grid):
            return Action(*self.choose_box(grid), self.random_direction())
        return Action(*self.push_on, self.push_dir)

    def EdgeOrientedAgent(self):
        grid = self.perceive()
        if self.choose_again(grid):
            row, col = self.choose_box(grid)
            return Action(
                row, col, self.edge_direction(grid, row, col, self.rng.random() < 0.5)
            )
        return Action(*self.push_on, self.push_dir)

    def NearestEdgeAgent(self):
        return self.edge_action(0)

    def NErandAgent(self):
        return self.edge_action(0.2)

    def NErSimAnealAgent(self):
        action = self.edge_action(1 - exp(-self.t / 10))
        self.t += 1
        return action

    def edge_action(self, random_probability):
        grid = self.perceive()
        if self.choose_again(grid):
            row, col = self.choose_box(grid)
            direction = (
                self.random_direction()
                if self.rng.random() < random_probability
                else self.edge_direction(grid, row, col)
            )
            return Action(row, col, direction)
        return Action(*self.push_on, self.push_dir)

    def NE1memAgent(self):
        grid = self.perceive()
        if not self.push_dir or grid[self.push_on[0]][self.push_on[1]] != 1:
            row, col = self.choose_box(grid)
            direction = (
                self.random_direction()
                if self.rng.random() < 0.2
                else self.edge_direction(grid, row, col)
            )
            self.last_push_on = (row, col)
            return Action(row, col, direction)
        if self.push_on == self.last_push_on:
            return Action(*self.push_on, self.random_direction())
        self.last_push_on = self.push_on
        return Action(*self.push_on, self.push_dir)
