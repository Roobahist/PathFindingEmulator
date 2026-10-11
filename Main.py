"""Backward-compatible launch command: python Main.py."""

from pathfinding_emulator.app import main

if __name__ == "__main__":
    raise SystemExit(main())
