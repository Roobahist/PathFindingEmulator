"""Legacy source launcher; installed users can use pathfinding-emulator."""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent / "src"))

from pathfinding_emulator.app import main  # noqa: E402

if __name__ == "__main__":
    raise SystemExit(main())
