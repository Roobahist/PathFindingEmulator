'use strict';
const $ = id => document.getElementById(id);
const tileNames = ['Stone', 'Hole', 'Floor', 'Box'];
const tileFiles = ['stone', 'hole', 'floor', 'box'];
const themes = ['Classic', 'Wood & stone', 'Lava', 'Grass & water'];
const shortcuts = ['S', 'H', 'E', 'B'];
const state = {grid: [], original: [], theme: 3, tile: 1, undo: [], frames: [], frame: 0, playing: false, timer: null, mode: 'edit', request: null, focused: 0, seed: null};
const copy = value => JSON.parse(JSON.stringify(value));
const art = (value, theme = state.theme) => `/assets/env/${theme}/${tileFiles[value + 2]}.jpg`;
async function api(path, data) {
  const response = await fetch(path, data === undefined ? {} : {method: 'POST', headers: {'Content-Type': 'application/json'}, body: JSON.stringify(data)});
  const result = await response.json();
  if (!response.ok) throw new Error(result.error || 'The action could not be completed. Try again.');
  return result;
}
function feedback(message, error = false) { $('feedback').textContent = message; $('feedback').classList.toggle('error', error); }
function stop() { state.playing = false; clearTimeout(state.timer); $('pause-button').innerHTML = '<svg><use href="#i-play"/></svg>'; $('pause-button').setAttribute('aria-label', 'Play solution'); }
function setMode(mode) {
  stop(); state.mode = mode; feedback('');
  if (mode === 'edit') { state.grid = copy(state.original); state.frame = 0; }
  $('edit-mode').classList.toggle('active', mode === 'edit'); $('play-mode').classList.toggle('active', mode === 'play');
  $('edit-mode').setAttribute('aria-pressed', String(mode === 'edit')); $('play-mode').setAttribute('aria-pressed', String(mode === 'play'));
  $('edit-tools').hidden = mode === 'play'; $('undo-button').hidden = mode === 'play';
  $('board-hint').textContent = mode === 'edit' ? 'Click to place · Right-click to erase' : 'Use the timeline to inspect every push';
  render();
}
function invalidate() { feedback(''); $('solver-message').textContent = 'Solve, then pause or step through each push.'; stop(); state.frames = []; state.frame = 0; state.request = null; $('solve-button').disabled = false; $('solve-button').querySelector('span').textContent = 'Solve & play'; $('stage').classList.remove('planning'); }
function loadGrid(grid, title = 'Untitled board') {
  invalidate(); state.grid = copy(grid); state.original = copy(grid); state.undo = []; state.focused = 0;
  $('board-title').textContent = title; setMode('edit'); feedback('');
}
function palette() {
  $('palette').replaceChildren();
  [1, -2, -1, 0].forEach(value => {
    const button = document.createElement('button'); button.className = 'tile-tool'; button.dataset.tile = value;
    button.setAttribute('aria-pressed', String(state.tile === value));
    button.innerHTML = `<img src="${art(value)}" alt=""><span>${tileNames[value + 2]}<small>${shortcuts[value + 2]}</small></span>`;
    button.onclick = () => { state.tile = value; palette(); };
    $('palette').append(button);
  });
}
function themePicker() {
  $('themes').replaceChildren();
  themes.forEach((name, theme) => {
    const button = document.createElement('button'); button.className = 'theme-button' + (theme === state.theme ? ' active' : '');
    button.title = name; button.setAttribute('aria-label', name); button.setAttribute('aria-pressed', String(theme === state.theme));
    button.innerHTML = '<span class="theme-preview">' + [0, 1, -2, -1].map(tile => `<img src="${art(tile, theme)}" alt="">`).join('') + '</span>';
    button.onclick = () => { state.theme = theme; themePicker(); palette(); render(); };
    $('themes').append(button);
  });
  $('artwork-name').textContent = themes[state.theme];
}
function render() {
  if (!state.grid.length) return;
  const grid = state.grid, rows = grid.length, cols = grid[0].length;
  requestAnimationFrame(fitBoard);
  const previous = state.frames[state.frame - 1]?.grid;
  $('board').style.setProperty('--cols', cols); $('board').style.setProperty('--rows', rows);
  $('board').style.gridTemplateColumns = `repeat(${cols},1fr)`;
  $('board').classList.toggle('pixel-art', state.theme >= 2);
  const focused = document.activeElement?.dataset?.cell;
  $('board').replaceChildren();
  grid.forEach((row, r) => {
    const gridRow = document.createElement('div'); gridRow.setAttribute('role', 'row'); gridRow.className = 'grid-row';
    row.forEach((value, c) => {
    const cell = document.createElement('button'); const index = r * cols + c;
    cell.className = 'cell' + (state.mode === 'play' && previous && value !== previous[r][c] ? ' changed' : '');
    cell.dataset.cell = index; cell.setAttribute('role', 'gridcell'); cell.setAttribute('aria-label', `Row ${r + 1}, column ${c + 1}, ${tileNames[value + 2]}`);
    cell.tabIndex = index === state.focused ? 0 : -1;
    const image = document.createElement('img'); image.src = art(value); image.alt = ''; image.draggable = false; cell.append(image);
    cell.onpointerdown = event => { if (event.button === 0 || event.button === 2) { event.preventDefault(); state.focused = index; cell.focus(); paint(r, c, event.button === 2 ? 0 : state.tile); } };
    cell.onpointerenter = event => { if (event.buttons === 1) paint(r, c, state.tile); };
    cell.oncontextmenu = event => event.preventDefault();
    cell.onfocus = () => { state.focused = index; $('board').querySelectorAll('[data-cell]').forEach(item => item.tabIndex = item === cell ? 0 : -1); };
    cell.onkeydown = event => {
      const delta = {ArrowLeft: -1, ArrowRight: 1, ArrowUp: -cols, ArrowDown: cols}[event.key];
      if (delta !== undefined) { event.preventDefault(); state.focused = Math.min(rows * cols - 1, Math.max(0, index + delta)); $('board').querySelector(`[data-cell="${state.focused}"]`).focus(); }
      if (event.key === ' ' || event.key === 'Enter') { event.preventDefault(); paint(r, c, state.tile); }
      if (event.key === 'Delete' || event.key === 'Backspace') { event.preventDefault(); paint(r, c, 0); }
    };
    const action = state.mode === 'play' ? state.frames[state.frame]?.action : null;
    if (action && action.row === r && action.col === c) { const arrow = document.createElementNS('http://www.w3.org/2000/svg', 'svg'); arrow.setAttribute('viewBox', '0 0 100 100'); arrow.setAttribute('class', `push-marker ${action.direction}`); arrow.setAttribute('role', 'img'); arrow.setAttribute('aria-label', `Pushed ${action.direction}`); arrow.innerHTML = '<path d="M18 50H79M54 25L79 50L54 75"/>'; cell.append(arrow); }
    gridRow.append(cell);
    }); $('board').append(gridRow);
  });
  if (focused !== undefined) $('board').querySelector(`[data-cell="${state.focused}"]`)?.focus({preventScroll: true});
  const boxes = grid.flat().filter(value => value === 1).length;
  $('box-count').textContent = boxes;
  $('cost-count').textContent = state.mode === 'play' ? state.frames[state.frame]?.cost || 0 : 0;
  $('action-count').textContent = state.mode === 'play' ? state.frame : 0;
  $('board-dimensions').textContent = `${rows - 2} × ${cols - 2} interior`;
  $('board-description').textContent = `${boxes} ${boxes === 1 ? 'box' : 'boxes'} · ${grid.flat().filter(v => v === -2).length} ${grid.flat().filter(v => v === -2).length === 1 ? 'stone' : 'stones'} · ${themes[state.theme]}`;
  $('stage-status').textContent = state.request ? 'Finding a solution' : state.mode === 'edit' ? 'Editing' : boxes === 0 ? 'Board cleared' : state.playing ? 'Playing' : 'Paused';
  $('scrubber').max = Math.max(0, state.frames.length - 1); $('scrubber').value = state.frame;
  $('frame-label').textContent = `${state.frame} / ${Math.max(0, state.frames.length - 1)}`;
  $('scrubber').disabled = $('pause-button').disabled = $('step-button').disabled = !state.frames.length;
  $('undo-button').disabled = !state.undo.length;
}
function paint(row, col, value) {
  if (state.mode !== 'edit') return;
  const boundary = row === 0 || col === 0 || row === state.grid.length - 1 || col === state.grid[0].length - 1;
  if (boundary && value !== -1 && value !== -2) { feedback('The border must stay holes or stones.', true); return; }
  if (state.grid[row][col] === value) return;
  state.undo.push(copy(state.grid)); if (state.undo.length > 100) state.undo.shift();
  invalidate(); state.grid[row][col] = value; state.original = copy(state.grid); feedback(''); render();
}
function showFrame(index) {
  feedback('');
  state.frame = Math.min(Math.max(index, 0), state.frames.length - 1);
  state.grid = copy(state.frames[state.frame].grid); render();
}
function play() {
  if (!state.frames.length) return;
  if (state.mode !== 'play') setMode('play');
  if (state.frame === state.frames.length - 1) showFrame(0);
  state.playing = true; $('pause-button').innerHTML = '<svg><use href="#i-pause"/></svg>'; $('pause-button').setAttribute('aria-label', 'Pause solution'); render();
  const advance = () => {
    if (!state.playing) return;
    showFrame(state.frame + 1);
    if (state.frame === state.frames.length - 1) { stop(); render(); feedback(`Board cleared in ${state.frame} pushes. Total cost: ${state.frames[state.frame].cost}.`); }
    else state.timer = setTimeout(advance, Number($('speed').value));
  };
  state.timer = setTimeout(advance, Number($('speed').value));
}
async function solve() {
  stop(); const request = {}; state.request = request;
  $('solve-button').disabled = true; $('solve-button').querySelector('span').textContent = 'Finding a solution…'; $('stage').classList.add('planning');
  $('solver-message').textContent = 'Searching the board. You can keep editing to cancel this result.'; render(); feedback('');
  try {
    const result = await api('/api/solve', {grid: state.original, algorithm: $('algorithm').value, seed: state.seed});
    if (state.request !== request) return;
    state.frames = result.frames; state.request = null; setMode('play'); showFrame(0); play();
    $('solver-message').textContent = `${result.frames.length - 1} pushes found. Pause, step, or scrub to inspect the solution.`;
  } catch (error) { if (state.request === request) { state.request = null; feedback(error.message, true); $('solver-message').textContent = 'Try another algorithm or edit the board.'; } }
  finally { if (!state.request) { $('solve-button').disabled = false; $('solve-button').querySelector('span').textContent = 'Solve & play'; $('stage').classList.remove('planning'); render(); } }
}
async function library() {
  const result = await api('/api/maps'); $('map-library').replaceChildren(new Option('Open a map…', ''));
  result.maps.forEach(name => $('map-library').append(new Option(name.replace(/\.(pickle|json)$/, ''), name)));
}
$('new-button').onclick = () => { $('board-config').hidden = !$('board-config').hidden; if (!$('board-config').hidden) $('new-rows').focus(); };
$('cancel-new').onclick = () => $('board-config').hidden = true;
$('create-button').onclick = async () => { try { const result = await api('/api/new', {rows: Number($('new-rows').value), cols: Number($('new-cols').value), random: $('new-layout').value === 'random'}); loadGrid(result.grid); $('board-config').hidden = true; } catch (error) { feedback(error.message, true); } };
$('map-library').onchange = async event => { if (!event.target.value) return; try { const name = event.target.value; const result = await api('/api/map?name=' + encodeURIComponent(name)); loadGrid(result.grid, name.replace(/\.(pickle|json)$/, '').replace('map_', 'Map ')); } catch (error) { feedback(error.message, true); } event.target.value = ''; };
$('import-button').onclick = () => $('import-file').click();
$('import-file').onchange = async event => { const file = event.target.files[0]; if (!file) return; try { if (file.size > 1024 * 1024) throw new Error('Maps must be smaller than 1 MiB.'); const result = await api('/api/validate', {grid: JSON.parse(await file.text())}); loadGrid(result.grid, file.name); } catch (error) { feedback(error.message, true); } event.target.value = ''; };
$('save-button').onclick = async () => { try { const result = await api('/api/save', {grid: state.original}); feedback(`Saved ${result.name}.`); await library(); } catch (error) { feedback(error.message, true); } };
$('solve-button').onclick = solve;
$('edit-mode').onclick = () => setMode('edit'); $('play-mode').onclick = () => { if (!state.frames.length) { feedback('Solve the board first to open playback.'); return; } setMode('play'); showFrame(state.frame); };
$('pause-button').onclick = () => { if (state.playing) { stop(); render(); } else play(); };
$('step-button').onclick = () => { stop(); if (state.mode !== 'play') setMode('play'); showFrame(state.frame + 1); };
$('reset-button').onclick = () => { stop(); if (state.frames.length) { setMode('play'); showFrame(0); } else { state.grid = copy(state.original); render(); } };
$('scrubber').oninput = event => { stop(); if (state.mode !== 'play') setMode('play'); showFrame(Number(event.target.value)); };
$('undo-button').onclick = () => { if (state.mode !== 'edit' || !state.undo.length) return; invalidate(); state.grid = state.undo.pop(); state.original = copy(state.grid); render(); };
document.addEventListener('keydown', event => {
  if (['INPUT', 'SELECT', 'TEXTAREA'].includes(event.target.tagName)) return;
  if ((event.ctrlKey || event.metaKey) && event.key.toLowerCase() === 'z') { event.preventDefault(); $('undo-button').click(); return; }
  const tile = {h: -1, s: -2, b: 1, e: 0}[event.key.toLowerCase()];
  if (tile !== undefined && state.mode === 'edit') { state.tile = tile; palette(); }
  if (event.key === 'Escape') { $('board-config').hidden = true; if (state.mode === 'play') setMode('edit'); }
});
(async () => { try { const initial = await api('/api/bootstrap'); state.seed = initial.seed; loadGrid(initial.grid, initial.title); $('algorithm').value = initial.algorithm; $('speed').value = String(initial.delay * 1000); if (!$('speed').value) { const pace = new Option(`${initial.delay}s`, String(initial.delay * 1000)); $('speed').append(pace); $('speed').value = pace.value; }; palette(); themePicker(); await library(); } catch (error) { feedback(error.message, true); } })();

function fitBoard() {
  const board = $('board'), arena = document.querySelector('.arena');
  if (!state.grid.length || !matchMedia('(min-width: 1000px) and (min-height: 700px)').matches) { board.style.width = ''; board.style.height = ''; return; }
  const padding = getComputedStyle(arena);
  const width = arena.clientWidth - parseFloat(padding.paddingLeft) - parseFloat(padding.paddingRight);
  const height = arena.clientHeight - parseFloat(padding.paddingTop) - parseFloat(padding.paddingBottom);
  const rows = state.grid.length, cols = state.grid[0].length;
  const cell = Math.max(1, Math.min((width - 14 - 2 * (cols - 1)) / cols, (height - 14 - 2 * (rows - 1)) / rows, (650 - 14 - 2 * (cols - 1)) / cols));
  board.style.width = `${cell * cols + 2 * (cols - 1) + 14}px`;
  board.style.height = `${cell * rows + 2 * (rows - 1) + 14}px`;
}
new ResizeObserver(fitBoard).observe(document.querySelector('.arena'));
