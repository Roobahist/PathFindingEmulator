"""Legacy A* entry point; now uses bounded, cost-correct uniform-cost search."""

from pathfinding_emulator.agents import Action, SearchAgent

__all__ = ["Action", "Agent"]


class Agent(SearchAgent):
    def __init__(self, env_perception, **kwargs):
        super().__init__(env_perception, algorithm="A_Star", **kwargs)
