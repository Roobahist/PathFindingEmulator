# Project guidance

- This is a local browser box-pushing puzzle editor and simulator, with an optional Pygame interface. Python 3.11–3.13
  is supported for installation; prefer 3.12 during development.
- `pathfinding_emulator/environment.py` owns movement/scoring. `maps.py` owns
  storage and generation. `agents.py` plans through environment transitions.
  `app.py` is the composition root; `ui/` must not be imported by core code.
  `web_server.py` adapts the same engine; `web/` contains the browser presentation.
- Keep one movement/scoring implementation. Search identity must include the
  continuation cell/direction and prior chain length, not only box locations.
- Tile values -2/-1/0/1 and `(row, column, direction)` are compatibility contracts.
  Preserve original maps and artwork. Root modules are compatibility imports.
- Use snake_case for new APIs. Preserve legacy Pygame class/member names used by
  compatibility imports unless a migration is documented.
- Operational options belong in validated `Settings`; inject perception callbacks
  and `random.Random` at application boundaries. No DI framework is needed.
- New maps use validated JSON. Never use unrestricted pickle loading. Bound map
  sizes, memo indices, search expansions, and simulation actions.
- Resolve assets relative to the package; new saves go to the configured maps
  directory. Never overwrite existing user maps or add actual credentials.
- Run `python -m unittest discover -v`, `ruff check .`, and
  `ruff format --check .`. Build with `python -m build --no-isolation`, then
  `python tools/check_wheel.py`. Audit `requirements.txt` with pip-audit.
- Tests select SDL dummy drivers for real Pygame smoke tests. Preserve event
  handling during planning/animation and ensure Pygame shuts down on errors.
- Keep requirements.txt, pyproject.toml, and requirements-dev.lock consistent.
  Update docs and compatibility notes with behavioral changes. No production
  deployment, release publication, history rewriting, or automatic merging.
- If delivering copyable text with placeholders, emphasize in bold above it
  that placeholders need correct values before use.
