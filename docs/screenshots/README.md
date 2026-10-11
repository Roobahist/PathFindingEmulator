# Browser screenshot evidence

The web-editor, web-lava and web-playback JPEG files were captured from the actual
local app with browser automation. They are not generated mockups. Start the app
with `python Main.py --algorithm A_Star --delay 0.5 --no-browser`, open the printed
local URL, and use a desktop viewport for the editor and lava artwork screenshots.
For playback, open map_10, choose Wood & stone, solve, reset and step once; the
frame shows one remaining box, one push and movement cost 5.

The review also covers narrow-screen layouts, keyboard painting, undo, save,
creation, theme switching, playback and returning to the original board. Asset
origins and capture conditions are recorded in provenance.json. Original artwork
bytes are preserved; its source is the repository's original images directory.
`python -m tools.capture_screenshots` captures only the optional Pygame screens.
