---
name: PathFinding Emulator
description: Vivid original puzzle textures in a sleek local browser workspace
colors:
  bg: "#0c0e13"
  surface: "#161920"
  raised: "#21252e"
  border: "#343945"
  text: "#f7f8fb"
  muted: "#aeb7c8"
  accent: "#ff794d"
  on-accent: "#19100c"
  good: "#b8ec79"
  primary-hover: "#ff956f"
  secondary-hover: "#2d3340"
  selected-text: "#ffd1bd"
  selected-tile: "#362820"
  stage: "#12151e"
  error: "#ffada1"
typography:
  headline:
    fontFamily: "Plex, system-ui, sans-serif"
    fontSize: "28px"
    fontWeight: 600
    letterSpacing: "-.025em"
  title:
    fontFamily: "Plex, system-ui, sans-serif"
    fontSize: "17px"
    fontWeight: 600
    letterSpacing: "-.015em"
  body:
    fontFamily: "Plex, system-ui, sans-serif"
    fontSize: "16px"
    fontWeight: 400
  label:
    fontFamily: "Plex, system-ui, sans-serif"
    fontSize: "14px"
    fontWeight: 400
  supporting:
    fontFamily: "Plex, system-ui, sans-serif"
    fontSize: "12px"
    fontWeight: 400
    lineHeight: 1.5
rounded:
  cell: "2px"
  preview: "4px"
  control: "8px"
  mode-switch: "9px"
  surface: "12px"
spacing:
  xs: "4px"
  sm: "8px"
  md: "16px"
  lg: "24px"
  page: "32px"
components:
  button-primary:
    backgroundColor: "{colors.accent}"
    textColor: "{colors.on-accent}"
    rounded: "{rounded.control}"
    padding: "0 16px"
  button-primary-hover:
    backgroundColor: "{colors.primary-hover}"
  button-secondary:
    backgroundColor: "{colors.raised}"
    textColor: "{colors.text}"
    rounded: "{rounded.control}"
    padding: "0 16px"
  button-secondary-hover:
    backgroundColor: "{colors.secondary-hover}"
  button-quiet:
    textColor: "{colors.muted}"
    rounded: "{rounded.control}"
    padding: "0 16px"
  field:
    backgroundColor: "{colors.raised}"
    textColor: "{colors.text}"
    rounded: "{rounded.control}"
    padding: "0 12px"
  inspector:
    backgroundColor: "{colors.surface}"
    rounded: "{rounded.surface}"
    padding: "22px 20px"
  button-play:
    backgroundColor: "{colors.text}"
    textColor: "{colors.bg}"
    rounded: "{rounded.control}"
    width: "44px"
---

# Design System: PathFinding Emulator

## Overview

**Creative North Star: "The Textured Puzzle Workspace"**

The Textured Puzzle Workspace places the original saturated puzzle artwork inside a dark, sleek control surface. Grass, water, lava, wood and stone supply the visual character; the interface uses quiet charcoal layers, readable labels and warm orange actions to make the artwork easy to inspect.

This records the shipped local browser interface. It replaces the rejected washed-out geometric presentation. Original raster textures and directional sprites remain the source of identity; the optional desktop interface is a separate retained presentation, not the source of these browser tokens.

**Key Characteristics:**
- Original texture artwork remains prominent and unchanged.
- Compact charcoal controls frame vivid puzzle imagery.
- IBM Plex Sans labels and tabular metrics support inspection.
- Orange identifies actions, selections and keyboard focus.

## Colors

The palette is a dark charcoal frame around saturated artwork, with a warm action accent and restrained status colors. Frontmatter holds the normative CSS values; raster artwork has its own original colors and is not recolored to match interface tokens.

### Primary
- **Warm Orange** (`accent`): solve and create actions, selected artwork/tool borders, timeline accent and focus outlines; the lighter hover token signals interaction.
- **Dark Warm Ink** (`on-accent`): text and icons over orange buttons.

### Secondary
- **Fresh Green** (`good`): status dot and positive feedback.
- **Pale Coral** (`error`): error feedback.
- **Peach Highlight / Warm Tile Selection** (`selected-text`, `selected-tile`): selected tile text and surface; peach also appears on playback hover.

### Neutral
- **Near Black / Charcoal Surface / Raised Charcoal** (`bg`, `surface`, `raised`): page, inspector and control layers.
- **Cool Border** (`border`): field edges and section separators.
- **Bright Text / Blue Gray Text** (`text`, `muted`): readable primary and supporting text.
- **Stage Charcoal** (`stage`): the board surround; the transport uses the nearby source value `#12151d`.

**The The Original Artwork Rule.** Use the supplied raster textures for puzzle tiles and artwork previews; preserve their bytes and their saturated character.

**The The State Accent Rule.** Orange marks primary actions, selected tools and keyboard focus; green reports positive status and pale coral reports errors.

## Typography

**Body and Control Font:** IBM Plex Sans, bundled as `Plex`, with `system-ui, sans-serif` fallbacks. Regular and semibold faces ship locally.

The face is compact and clear without adding decorative display typography. The title and brand use slight negative tracking; numeric playback and summary values use tabular figures.

### Hierarchy
- **Headline:** map title; reduces to (24px) at the narrow breakpoint.
- **Title:** inspector section headings.
- **Body:** inherited control text.
- **Label:** common header buttons, tile names, map description and board status.
- **Supporting:** solver guidance with its established line height. Other footer and artwork labels also use (12px); solver fields and timeline labels use (13px).

**The The Readable Control Rule.** Use the bundled Plex face for browser controls; retain visible focus and text labels beside artwork choices.

## Layout

The browser workspace is a centered container with a (1600px) maximum width. Desktop page gutters use the `page` spacing token. A two-column grid gives the board the flexible column and the inspector (304px); the gap uses `lg`. Playback transport occupies the next grid row beneath the board, while the inspector spans both rows. Board size preserves the grid’s actual row/column aspect ratio and caps its width at (570px).

At (1450px) and above, the arena minimum height is (565px) and board cap is (650px). At (1100px) and below, page gutters become (20px), the inspector becomes (280px), gaps become (16px), and header actions wrap onto another row. At (760px) and below, the workspace becomes a single column in DOM order: board, playback transport, inspector. The inspector uses two columns for editing and artwork, with solver and statistics spanning both; the transport timeline wraps below its buttons and pace selector. The board continues to fit its available width.

## Elevation & Depth

Depth combines dark tonal layers and a single diffuse board shadow. Borders separate controls and tool sections; the artwork itself supplies material texture. The board shadow is `0 18px 38px #0008`. Avoid adding unrelated card shadows to every group.

Changed playback cells use a brief brightness-and-scale animation (230ms, `cubic-bezier(.16,1,.3,1)`), while control transitions last (160ms). The reduced-motion media query removes animation and transitions. The board’s hover and focus treatments remain immediate inspection cues.

## Shapes

Controls and board frame use the `control` radius; inspector, stage and transport use `surface`. Texture cells have the much smaller `cell` radius so neighboring tiles read as a continuous grid. Artwork previews use `preview`; the mode switch uses its own slightly softer radius. Thin borders provide definition, and the board’s (2px) tile gaps and (7px) dark frame keep textures legible.

## Components

### Buttons

Compact, clear controls with a (44px) minimum height. Primary actions use warm orange and dark ink, with semibold text; secondary actions use raised charcoal and a cool border; quiet actions use muted text until hover. Buttons move down (1px) on active press and disabled controls use (0.4) opacity. Focus is an orange (2px) outline offset by (4px). The solver action fills its column and has a (46px) minimum height.

### Inputs / Fields

Raised charcoal fields, cool borders and the control radius. Number inputs and selects use a (44px) minimum height. The playback range is a native range control accented orange, with a visible position label and an accessible name. Fields share the orange keyboard focus outline.

### Navigation

Editor and Playback sit in a compact segmented control. Muted inactive labels become bright over a lighter charcoal selected surface (`#343b49`); selected state is exposed with `aria-pressed`. Playback requires an available result; returning to Editor restores the original editable grid.

### Cards / Containers

The inspector uses tonal depth and internal padding from its component token. Desktop tool sections use separators with (24px) top margin and (22px) top padding. When editing tools are hidden for Playback, the first remaining Artwork section loses the preceding divider and spacing. Stage header and footer use (18px 22px) padding, reducing to (14px 12px) on narrow screens.

### Texture Tools and Artwork

Tile controls combine original texture thumbnails, tile names and shortcut labels. Selected tiles use warm surface, peach text and an orange border. Artwork choices show a four-tile raster collage and expose their name and pressed state. Changing artwork reskins the same grid immediately; the Grass & water set is the default, and lava and grass/water textures use pixelated image rendering.

### Puzzle Board and Playback

The board is an accessible grid with one keyboard tab stop, arrow-key movement, Enter/Space placement and Delete/Backspace erase. The original directional sprite marks the pushed cell. Undo is present only in Editor and becomes disabled when history is empty. Playback controls and the timeline sit directly after the board on narrow screens. Solver status, board state, feedback, remaining boxes, movement cost and pushes are distinct information roles: completion must agree with remaining boxes, and editing invalidates the prior solver result.

## Do's and Don'ts

### Do:
- **Do** preserve original tile and directional sprite files byte-for-byte.
- **Do** pair artwork previews with accessible names and pressed states.
- **Do** maintain the visible orange focus outline and the board’s keyboard navigation.
- **Do** use truthful solver and playback messages based on the current engine result.
- **Do** disable motion under the user’s reduced-motion preference.

### Don't:
- **Don't** replace the original textures with washed-out geometric tiles.
- **Don't** use texture thumbnails as the only accessible label for a control.
- **Don't** report a board as cleared while boxes remain.
- **Don't** carry stale completion or solver results into an edited board.
