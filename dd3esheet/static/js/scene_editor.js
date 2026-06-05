// scene_editor.js — orquestra o Editor de Cena: tokens DOM, ferramentas, rails,
// autosave, atalhos e menu de contexto. Depende de hex.js, scene_state.js, scene_canvas.js.
(function () {
  const root = document.querySelector('[data-rich-editor="2"]');
  if (!root) return;

  const SIZE_SCALE = { sm: 0.74, md: 1, lg: 1.6, xl: 2.3 };
  const FACTIONS = [
    { id: 'party', label: 'Grupo' }, { id: 'ally', label: 'Aliado' },
    { id: 'neutral', label: 'Neutro' }, { id: 'enemy', label: 'Inimigo' },
  ];
  const CONDITIONS = [
    { id: 'poisoned', label: 'Envenenado', color: '#4f6b3a', icon: '☣' },
    { id: 'stunned', label: 'Atordoado', color: '#b58a36', icon: '✦' },
    { id: 'prone', label: 'Caído', color: '#6b6f73', icon: '↓' },
    { id: 'blessed', label: 'Abençoado', color: '#c8923a', icon: '☀' },
    { id: 'frightened', label: 'Amedrontado', color: '#5d4978', icon: '!' },
    { id: 'shielded', label: 'Protegido', color: '#3f6079', icon: '⛉' },
  ];
  const BRUSH_LABELS = ['1', '7', '19', '37'];

  function readJSON(id) {
    const el = document.getElementById(id);
    if (!el) return null;
    try { return JSON.parse(el.textContent); } catch (e) { return null; }
  }
  function csrf() {
    const el = root.querySelector('[name=csrfmiddlewaretoken]');
    return el ? el.value : '';
  }
  // html aqui é SEMPRE markup estático/confiável (ícones, rótulos fixos).
  // Dados do usuário (nomes de token/asset) usam txt() para evitar XSS.
  function el(tag, cls, html) {
    const e = document.createElement(tag);
    if (cls) e.className = cls;
    if (html != null) e.innerHTML = html;
    return e;
  }
  function txt(tag, cls, text) {
    const e = document.createElement(tag);
    if (cls) e.className = cls;
    e.textContent = text == null ? '' : text;
    return e;
  }
  function cssUrl(url) { return 'url(' + JSON.stringify(String(url)) + ')'; }
  function factionVar(f) { return 'var(--sc-' + (f || 'enemy') + ')'; }

  // --- estado -------------------------------------------------------------
  const sceneData = readJSON('tt-scene-data') || {};
  const tileLib = readJSON('tt-tile-data') || [];
  const tokenLib = readJSON('tt-tokenlib-data') || [];
  const tileUrls = new Map();
  tileLib.forEach(t => tileUrls.set(t.id, t.url));

  const store = SceneState.create(sceneData, onChange);
  const S = store.s;

  let tool = 'select';
  let terrainActive = tileLib.length ? tileLib[0].id : null;
  let terrainMode = 'brush';
  let fogMode = 'hide';
  let brushSize = 0;
  let selectedId = null;
  let armedAssetId = null;
  let spaceHeld = false;
  const layers = {
    terrain: { visible: true, locked: false },
    tokens: { visible: true, locked: false },
    fog: { visible: true, locked: false },
    grid: { visible: true, locked: false },
  };

  const stage = document.getElementById('sc-stage');
  const canvasEl = document.getElementById('sc-canvas');
  const tokensLayer = document.getElementById('sc-tokens');
  const saveUrl = root.dataset.sceneSaveUrl;

  const canvas = SceneCanvas.create(canvasEl, store, {
    tileUrl: (id) => tileUrls.get(id),
    getLayers: () => layers,
    onCamChange: positionAll,
    onPointer: onStagePointer,
    shouldPan: (ev) => ev.button === 1 || ev.button === 2 || spaceHeld || tool === 'select',
    onBackgroundTap: () => { if (tool === 'select') { selectToken(null); } },
  });

  // --- token overlay ------------------------------------------------------
  const tokenEls = new Map();   // key (id|tempId) -> element

  function tokenKey(t) { return t.id != null ? t.id : t.tempId; }

  function renderTokens() {
    const present = new Set();
    if (layers.tokens.visible !== false) {
      S.tokens.forEach(t => {
        const k = tokenKey(t);
        present.add(k);
        let e = tokenEls.get(k);
        if (!e) { e = buildToken(t); tokenEls.set(k, e); tokensLayer.appendChild(e); }
        updateToken(e, t);
      });
    }
    // remove ausentes
    tokenEls.forEach((e, k) => { if (!present.has(k)) { e.remove(); tokenEls.delete(k); } });
    positionAll();
    renderQuickbar();
  }

  function buildToken(t) {
    const e = el('div', 'sc-token');
    e.innerHTML = '<div class="sc-token__disc"></div>' +
      '<div class="sc-token__conds"></div>' +
      '<div class="sc-token__hp"><i></i></div>' +
      '<div class="sc-token__name"></div>';
    e.addEventListener('pointerdown', (ev) => onTokenPointerDown(ev, t));
    e.addEventListener('contextmenu', (ev) => { ev.preventDefault(); ev.stopPropagation(); openContextMenu(ev, tokenKey(t)); });
    return e;
  }

  function updateToken(e, t) {
    e.dataset.key = tokenKey(t);
    e.style.setProperty('--ring', factionVar(t.faction));
    const isProp = t.kind === 'object';
    const disc = e.querySelector('.sc-token__disc');
    if (t.spriteUrl) { disc.style.backgroundImage = cssUrl(t.spriteUrl); e.classList.remove('sc-token--placeholder'); }
    else { disc.style.backgroundImage = 'none'; e.classList.add('sc-token--placeholder'); }
    // hp
    const hp = e.querySelector('.sc-token__hp');
    if (isProp || !t.maxHp) { hp.style.display = 'none'; }
    else {
      hp.style.display = '';
      const ratio = Math.max(0, Math.min(1, t.hp / t.maxHp));
      const bar = hp.querySelector('i');
      bar.style.width = (ratio * 100) + '%';
      bar.style.background = ratio > 0.6 ? 'var(--forest)' : ratio > 0.3 ? 'var(--muted-gold)' : 'var(--deep-red)';
    }
    // conditions (até 3)
    const conds = e.querySelector('.sc-token__conds');
    conds.innerHTML = '';
    (t.conditions || []).slice(0, 3).forEach(cid => {
      const def = CONDITIONS.find(c => c.id === cid);
      if (!def) return;
      const i = el('i', '', def.icon); i.style.background = def.color; i.title = def.label;
      conds.appendChild(i);
    });
    e.querySelector('.sc-token__name').textContent = t.name || '';
    e.classList.toggle('is-selected', tokenKey(t) === selectedId);
  }

  function positionAll() {
    const z = canvas.cam.zoom;
    S.tokens.forEach(t => {
      const e = tokenEls.get(tokenKey(t));
      if (!e) return;
      const [wx, wy] = Hex.axialToPixel(t.q, t.r, S.grid.size);
      const [sx, sy] = canvas.worldToScreen(wx, wy);
      const d = S.grid.size * (SIZE_SCALE[t.size] || 1) * z;
      e.style.left = sx + 'px'; e.style.top = sy + 'px';
      e.style.width = d + 'px'; e.style.height = d + 'px';
      const nameEl = e.querySelector('.sc-token__name');
      nameEl.style.display = (tokenKey(t) === selectedId || z > 0.78) ? '' : 'none';
    });
    positionQuickbar();
  }

  // --- seleção + arraste de token ----------------------------------------
  let dragInfo = null;

  function onTokenPointerDown(ev, t) {
    if (ev.button !== 0) return;
    ev.stopPropagation();
    if (tool !== 'select') return;
    if (layers.tokens.locked) { selectToken(tokenKey(t)); return; }
    selectToken(tokenKey(t));
    const e = tokenEls.get(tokenKey(t));
    dragInfo = { token: t, moved: false, startedUndo: false };
    e.setPointerCapture(ev.pointerId);
    e.addEventListener('pointermove', onTokenDragMove);
    e.addEventListener('pointerup', onTokenDragUp);
  }
  function onTokenDragMove(ev) {
    if (!dragInfo) return;
    const r = canvasEl.getBoundingClientRect();
    const [wx, wy] = canvas.screenToWorld(ev.clientX - r.left, ev.clientY - r.top);
    const [q, rr] = Hex.pixelToAxial(wx, wy, S.grid.size);
    if (q === dragInfo.token.q && rr === dragInfo.token.r) return;
    if (!dragInfo.startedUndo) { store.pushUndo(); dragInfo.startedUndo = true; }
    dragInfo.moved = true;
    dragInfo.token.q = q; dragInfo.token.r = rr;
    positionAll();
  }
  function onTokenDragUp(ev) {
    const e = ev.currentTarget;
    e.removeEventListener('pointermove', onTokenDragMove);
    e.removeEventListener('pointerup', onTokenDragUp);
    try { e.releasePointerCapture(ev.pointerId); } catch (x) {}
    if (dragInfo && dragInfo.moved) onChange('move');
    dragInfo = null;
  }

  function selectToken(key) {
    selectedId = key;
    tokenEls.forEach((e, k) => e.classList.toggle('is-selected', k === key));
    renderQuickbar();
    renderInspector();
    renderTokenList();
    positionQuickbar();
  }

  // --- quickbar -----------------------------------------------------------
  let quickbar = null;
  function renderQuickbar() {
    if (quickbar) { quickbar.remove(); quickbar = null; }
    const t = selectedToken();
    if (!t || tool !== 'select') return;
    quickbar = el('div', 'sc-quickbar');
    quickbar.innerHTML =
      '<button data-q="dmg">−</button><span class="hp"></span><button data-q="heal">+</button>' +
      '<button data-q="dup" title="Duplicar">⧉</button><button data-q="del" title="Remover">🗑</button>';
    quickbar.querySelector('.hp').textContent = t.maxHp ? (t.hp + '/' + t.maxHp) : '—';
    quickbar.addEventListener('pointerdown', e => e.stopPropagation());
    quickbar.addEventListener('click', (ev) => {
      const q = ev.target.dataset.q; if (!q) return;
      if (q === 'dmg') { adjustHp(t, -1); }
      else if (q === 'heal') { adjustHp(t, +1); }
      else if (q === 'dup') { duplicateToken(t); }
      else if (q === 'del') { removeToken(t); }
    });
    tokensLayer.appendChild(quickbar);
    positionQuickbar();
  }
  function positionQuickbar() {
    const t = selectedToken();
    if (!quickbar || !t) return;
    const [wx, wy] = Hex.axialToPixel(t.q, t.r, S.grid.size);
    const [sx, sy] = canvas.worldToScreen(wx, wy);
    const d = S.grid.size * (SIZE_SCALE[t.size] || 1) * canvas.cam.zoom;
    quickbar.style.left = sx + 'px'; quickbar.style.top = (sy - d / 2) + 'px';
  }

  // --- mutações de token --------------------------------------------------
  function selectedToken() { return selectedId == null ? null : store.tokenById(selectedId); }
  function adjustHp(t, delta) {
    t.hp = Math.max(0, (t.hp || 0) + delta);
    onChange('hp'); renderQuickbar();
  }
  function duplicateToken(t) {
    store.pushUndo();
    const copy = Object.assign({}, t);
    delete copy.id; copy.tempId = 'n' + Date.now() + Math.floor(Math.random() * 1000);
    copy.q = t.q + 1;
    S.tokens.push(copy);
    selectedId = copy.tempId;
    onChange('dup');
  }
  function removeToken(t) {
    store.pushUndo();
    const k = tokenKey(t);
    S.tokens = S.tokens.filter(x => tokenKey(x) !== k);
    if (selectedId === k) selectedId = null;
    onChange('del');
  }
  function placeTokenAt(assetId, q, r) {
    store.pushUndo();
    const lib = tokenLib.find(a => a.id === assetId);
    const t = {
      tempId: 'n' + Date.now() + Math.floor(Math.random() * 1000),
      assetId: assetId || null, spriteUrl: lib ? lib.url : '',
      name: lib ? lib.name : '', kind: 'enemy', faction: 'enemy',
      q, r, hp: 0, maxHp: 0, size: 'md', conditions: [], rotation: 0,
      hidden: false, movable: false,
    };
    S.tokens.push(t);
    selectedId = t.tempId;
    onChange('place');
  }

  // --- interação no palco (terreno/névoa/régua/colocar) ------------------
  let paintingActive = false, lastPaintHex = null, measureStart = null;

  function brushCells(q, r) { return Hex.disk(q, r, brushSize); }

  function cellValue(k) { return S.terrain.has(k) ? S.terrain.get(k) : null; }

  function paintTerrainAt(q, r, eraser) {
    if (eraser) { brushCells(q, r).forEach(([cq, cr]) => S.terrain.delete(Hex.key(cq, cr))); return; }
    if (terrainActive == null) return;
    if (terrainMode === 'fill') { floodFill(q, r, terrainActive); return; }
    brushCells(q, r).forEach(([cq, cr]) => S.terrain.set(Hex.key(cq, cr), terrainActive));
  }
  function floodFill(q, r, value) {
    const target = cellValue(Hex.key(q, r));
    if (target === value) return;
    const seen = new Set(), queue = [[q, r]]; let n = 0;
    const NB = [[1, 0], [1, -1], [0, -1], [-1, 0], [-1, 1], [0, 1]];
    while (queue.length && n < 6000) {
      const [cq, cr] = queue.pop();
      const k = Hex.key(cq, cr);
      if (seen.has(k)) continue;
      seen.add(k); n++;
      if (cellValue(k) !== target) continue;
      S.terrain.set(k, value);
      NB.forEach(([dq, dr]) => queue.push([cq + dq, cr + dr]));
    }
  }
  function fogAt(q, r) {
    brushCells(q, r).forEach(([cq, cr]) => {
      const k = Hex.key(cq, cr);
      if (fogMode === 'reveal') S.fog.delete(k); else S.fog.add(k);
    });
  }

  function onStagePointer(phase, world, ev) {
    const [q, r] = Hex.pixelToAxial(world[0], world[1], S.grid.size);
    document.getElementById('sc-status-coord').textContent = 'q' + q + ' r' + r;

    if (tool === 'terrain' || tool === 'erase') {
      if (layers.terrain.locked) return;
      if (phase === 'down') {
        if (ev.altKey && tool === 'terrain') { eyedrop(q, r); return; }
        store.pushUndo(); paintingActive = true; lastPaintHex = [q, r];
        paintTerrainAt(q, r, tool === 'erase'); onChange('paint');
      } else if (phase === 'move' && paintingActive) {
        Hex.line(lastPaintHex[0], lastPaintHex[1], q, r).forEach(([lq, lr]) => paintTerrainAt(lq, lr, tool === 'erase'));
        lastPaintHex = [q, r]; onChange('paint');
      } else if (phase === 'up') { paintingActive = false; }
      return;
    }
    if (tool === 'fog') {
      if (layers.fog.locked) return;
      if (phase === 'down') { store.pushUndo(); paintingActive = true; lastPaintHex = [q, r]; fogAt(q, r); onChange('fog'); }
      else if (phase === 'move' && paintingActive) { Hex.line(lastPaintHex[0], lastPaintHex[1], q, r).forEach(([lq, lr]) => fogAt(lq, lr)); lastPaintHex = [q, r]; onChange('fog'); }
      else if (phase === 'up') { paintingActive = false; }
      return;
    }
    if (tool === 'measure') {
      if (phase === 'down') { measureStart = [q, r]; }
      else if (phase === 'move' && measureStart) {
        canvas.setRuler({ a: measureStart, b: [q, r], type: 'ruler' });
        const n = Hex.distance(measureStart[0], measureStart[1], q, r);
        document.getElementById('sc-status-meas').textContent = n + ' hex · ' + (n * 1.5).toFixed(1).replace('.', ',') + ' m';
      } else if (phase === 'up') { measureStart = null; }
      return;
    }
    if (tool === 'token' && armedAssetId != null && phase === 'down') {
      placeTokenAt(armedAssetId, q, r);
      return;
    }
  }
  function eyedrop(q, r) {
    const k = Hex.key(q, r);
    if (S.terrain.has(k)) { terrainActive = S.terrain.get(k); renderPanel(); }
  }

  // --- ferramentas + painéis ---------------------------------------------
  function setTool(next) {
    tool = next;
    document.querySelectorAll('.sc-tool').forEach(b => b.classList.toggle('is-active', b.dataset.tool === next));
    document.getElementById('sc-status-tool').textContent = root.querySelector('.sc-tool.is-active span').textContent;
    canvas.setRuler(null);
    canvas.setBrushPreview([]);
    renderPanel();
    renderQuickbar();
  }

  function renderPanel() {
    const p = document.getElementById('sc-panel');
    p.innerHTML = '';
    if (tool === 'terrain' || tool === 'erase') p.appendChild(terrainPanel());
    else if (tool === 'token') p.appendChild(tokenPanel());
    else if (tool === 'fog') p.appendChild(fogPanel());
    else p.appendChild(simplePanel());
  }

  function brushChips(value, onPick) {
    const row = el('div', 'sc-brushrow');
    BRUSH_LABELS.forEach((lbl, i) => {
      const c = el('button', 'sc-chip' + (i === value ? ' is-active' : ''), lbl);
      c.addEventListener('click', () => { onPick(i); });
      row.appendChild(c);
    });
    return row;
  }

  function terrainPanel() {
    const wrap = el('div');
    wrap.appendChild(el('h2', 'sc-panel__title', tool === 'erase' ? 'Apagar terreno' : 'Terreno'));
    if (tool === 'terrain') {
      const seg = el('div', 'sc-seg');
      ['brush', 'fill'].forEach(m => {
        const b = el('button', terrainMode === m ? 'is-active' : '', m === 'brush' ? 'Pincel' : 'Balde');
        b.addEventListener('click', () => { terrainMode = m; renderPanel(); });
        seg.appendChild(b);
      });
      wrap.appendChild(seg);
      const search = el('input', 'sc-search'); search.type = 'search'; search.placeholder = 'Buscar terreno na biblioteca';
      wrap.appendChild(search);
      const grid = el('div', 'sc-terrains');
      const CAP = 80;
      function fill(term) {
        grid.innerHTML = '';
        const matches = tileLib.filter(t => !term || (t.name || '').toLowerCase().includes(term));
        matches.slice(0, CAP).forEach(t => {
          const sw = el('button', 'sc-swatch' + (t.id === terrainActive ? ' is-active' : ''));
          sw.title = t.name || '';
          const chip = el('span', 'chip');
          if (t.url) chip.style.backgroundImage = cssUrl(t.url);
          sw.appendChild(chip); sw.appendChild(txt('span', '', t.name || ''));
          sw.addEventListener('click', () => { terrainActive = t.id; fill(search.value.toLowerCase()); });
          grid.appendChild(sw);
        });
        if (matches.length > CAP) grid.appendChild(el('p', 'sc-hint', '+' + (matches.length - CAP) + ' — refine a busca.'));
        else if (!matches.length) grid.appendChild(el('p', 'sc-empty', 'Nenhum tile encontrado.'));
      }
      fill('');
      search.addEventListener('input', () => fill(search.value.toLowerCase()));
      wrap.appendChild(grid);
      wrap.appendChild(el('p', 'sc-hint', 'Alt+clique no mapa = conta-gotas.'));
    }
    wrap.appendChild(brushChips(brushSize, (i) => { brushSize = i; renderPanel(); }));
    return wrap;
  }

  function tokenPanel() {
    const wrap = el('div');
    wrap.appendChild(el('h2', 'sc-panel__title', 'Tokens'));
    const search = el('input', 'sc-search'); search.type = 'search'; search.placeholder = 'Buscar asset';
    wrap.appendChild(search);
    const grid = el('div', 'sc-assets');
    function fill(term) {
      grid.innerHTML = '';
      tokenLib.filter(a => !term || (a.name || '').toLowerCase().includes(term)).forEach(a => {
        const b = el('button', 'sc-asset' + (a.id === armedAssetId ? ' is-armed' : ''));
        b.draggable = true;
        const th = el('span', 'sc-asset__thumb');
        if (a.url) { const img = new Image(); img.src = a.url; img.alt = ''; th.appendChild(img); }
        else { th.textContent = '☻'; }
        b.appendChild(th); b.appendChild(txt('span', '', a.name || ''));
        b.addEventListener('click', () => { armedAssetId = (armedAssetId === a.id ? null : a.id); fill(search.value.toLowerCase()); });
        b.addEventListener('dragstart', (ev) => { ev.dataTransfer.setData('text/plain', String(a.id)); });
        grid.appendChild(b);
      });
    }
    fill('');
    search.addEventListener('input', () => fill(search.value.toLowerCase()));
    wrap.appendChild(grid);
    wrap.appendChild(el('p', 'sc-hint', 'Arraste para o mapa, ou clique para pegar e clicar num hex.'));
    return wrap;
  }

  function fogPanel() {
    const wrap = el('div');
    wrap.appendChild(el('h2', 'sc-panel__title', 'Névoa'));
    const seg = el('div', 'sc-seg');
    [['hide', 'Ocultar'], ['reveal', 'Revelar']].forEach(([m, lbl]) => {
      const b = el('button', fogMode === m ? 'is-active' : '', lbl);
      b.addEventListener('click', () => { fogMode = m; renderPanel(); });
      seg.appendChild(b);
    });
    wrap.appendChild(seg);
    wrap.appendChild(brushChips(brushSize, (i) => { brushSize = i; renderPanel(); }));
    const actions = el('div', 'sc-actions');
    const reveal = el('button', 'sc-btn', 'Revelar tudo');
    reveal.addEventListener('click', () => { store.pushUndo(); S.fog.clear(); onChange('fog'); });
    const cover = el('button', 'sc-btn', 'Cobrir tudo');
    cover.addEventListener('click', () => { store.pushUndo(); canvas.gridCells().forEach(([q, r]) => S.fog.add(Hex.key(q, r))); onChange('fog'); });
    actions.appendChild(reveal); actions.appendChild(cover);
    wrap.appendChild(actions);
    return wrap;
  }

  function simplePanel() {
    const titles = {
      select: ['Selecionar', 'Clique para selecionar; arraste para mover. Arraste o fundo para deslocar.'],
      measure: ['Régua', 'Arraste de um hex a outro para medir (1 hex = 1,5 m).'],
      erase: ['Apagar', 'Pinte para remover o tile de terreno do hex.'],
    };
    const t = titles[tool] || ['Ferramenta', ''];
    const wrap = el('div');
    wrap.appendChild(el('h2', 'sc-panel__title', t[0]));
    wrap.appendChild(el('p', 'sc-hint', t[1]));
    return wrap;
  }

  // --- rail direito -------------------------------------------------------
  function renderRightRails() { renderSceneSize(); renderLayers(); renderInspector(); renderTokenList(); }

  function renderSceneSize() {
    const box = document.getElementById('sc-scenesize');
    box.innerHTML = '';
    box.appendChild(el('h2', 'sc-box__title', 'Tamanho da cena'));
    const presets = [['Pequena', 16, 12], ['Média', 30, 22], ['Grande', 44, 32], ['Enorme', 60, 44]];
    const row = el('div', 'sc-actions');
    presets.forEach(([lbl, c, r]) => {
      const b = el('button', 'sc-btn', lbl);
      b.addEventListener('click', () => { S.grid.cols = c; S.grid.rows = r; canvas.fit(); onChange('grid'); renderSceneSize(); });
      row.appendChild(b);
    });
    box.appendChild(row);
    box.appendChild(stepper('Largura', S.grid.cols, 8, 80, v => { S.grid.cols = v; canvas.fit(); onChange('grid'); renderSceneSize(); }));
    box.appendChild(stepper('Altura', S.grid.rows, 6, 60, v => { S.grid.rows = v; canvas.fit(); onChange('grid'); renderSceneSize(); }));
  }
  function stepper(label, value, lo, hi, onSet) {
    const w = el('div', 'sc-insp__row');
    w.appendChild(el('span', 'sc-layer__name', label));
    const s = el('div', 'sc-stepper');
    const minus = el('button', 'sc-iconbtn', '−');
    const inp = el('input'); inp.type = 'number'; inp.value = value; inp.min = lo; inp.max = hi;
    const plus = el('button', 'sc-iconbtn', '+');
    const clamp = v => Math.max(lo, Math.min(hi, v | 0));
    minus.addEventListener('click', () => onSet(clamp(parseInt(inp.value, 10) - 1)));
    plus.addEventListener('click', () => onSet(clamp(parseInt(inp.value, 10) + 1)));
    inp.addEventListener('change', () => onSet(clamp(parseInt(inp.value, 10) || lo)));
    s.appendChild(minus); s.appendChild(inp); s.appendChild(plus);
    w.appendChild(s);
    return w;
  }

  function renderLayers() {
    const box = document.getElementById('sc-layers');
    box.innerHTML = '';
    box.appendChild(el('h2', 'sc-box__title', 'Camadas'));
    const defs = [['terrain', 'Terreno', true], ['tokens', 'Tokens', true], ['fog', 'Névoa', false], ['grid', 'Grade', false]];
    defs.forEach(([id, lbl, lockable]) => {
      const row = el('div', 'sc-layer');
      const eye = el('button', '', layers[id].visible ? '👁' : '🚫');
      eye.title = 'Visibilidade';
      eye.addEventListener('click', () => { layers[id].visible = !layers[id].visible; renderLayers(); canvas.draw(); renderTokens(); });
      row.appendChild(eye);
      row.appendChild(el('span', 'sc-layer__name', lbl));
      if (lockable) {
        const lock = el('button', '', layers[id].locked ? '🔒' : '🔓');
        lock.title = 'Travar';
        lock.addEventListener('click', () => { layers[id].locked = !layers[id].locked; renderLayers(); });
        row.appendChild(lock);
      }
      box.appendChild(row);
    });
    const clr = el('button', 'sc-btn sc-btn--danger', 'Limpar terreno');
    clr.style.marginTop = '8px';
    clr.addEventListener('click', () => { store.pushUndo(); S.terrain.clear(); onChange('clear'); });
    box.appendChild(clr);
  }

  function renderInspector() {
    const box = document.getElementById('sc-inspector');
    box.innerHTML = '';
    box.appendChild(el('h2', 'sc-box__title', 'Inspector'));
    const t = selectedToken();
    if (!t) { box.appendChild(el('p', 'sc-empty', 'Nada selecionado.')); return; }
    const isProp = t.kind === 'object';
    const name = el('input', 'sc-insp__name'); name.value = t.name || ''; name.placeholder = 'Nome';
    name.addEventListener('input', () => { t.name = name.value; updateTokenEl(t); scheduleSave(); });
    box.appendChild(name);

    // facção
    const facRow = el('div', 'sc-insp__faction');
    FACTIONS.forEach(f => {
      const b = el('button', 'sc-fac sc-fac--' + f.id + (t.faction === f.id ? ' is-active' : '')); b.title = f.label;
      b.addEventListener('click', () => { store.pushUndo(); t.faction = f.id; onChange('faction'); });
      facRow.appendChild(b);
    });
    box.appendChild(facRow);

    if (!isProp) {
      // HP
      const hpRow = el('div', 'sc-insp__row');
      hpRow.appendChild(el('span', 'sc-layer__name', 'PV'));
      const sp = el('div', 'sc-stepper');
      const minus = el('button', 'sc-iconbtn', '−');
      const hpIn = el('input'); hpIn.type = 'number'; hpIn.value = t.hp || 0; hpIn.style.width = '48px';
      const slash = el('span', '', '/'); const maxIn = el('input'); maxIn.type = 'number'; maxIn.value = t.maxHp || 0; maxIn.style.width = '48px';
      const plus = el('button', 'sc-iconbtn', '+');
      minus.addEventListener('click', () => { adjustHp(t, -1); hpIn.value = t.hp; });
      plus.addEventListener('click', () => { adjustHp(t, +1); hpIn.value = t.hp; });
      hpIn.addEventListener('input', () => { t.hp = Math.max(0, parseInt(hpIn.value, 10) || 0); updateTokenEl(t); scheduleSave(); });
      maxIn.addEventListener('input', () => { t.maxHp = Math.max(0, parseInt(maxIn.value, 10) || 0); updateTokenEl(t); scheduleSave(); });
      sp.appendChild(minus); sp.appendChild(hpIn); sp.appendChild(slash); sp.appendChild(maxIn); sp.appendChild(plus);
      hpRow.appendChild(sp);
      box.appendChild(hpRow);
    }

    // tamanho
    const sizeRow = el('div', 'sc-sizes');
    [['sm', 'P'], ['md', 'M'], ['lg', 'G'], ['xl', 'GG']].forEach(([id, lbl]) => {
      const b = el('button', 'sc-size' + (t.size === id ? ' is-active' : ''), lbl);
      b.addEventListener('click', () => { store.pushUndo(); t.size = id; onChange('size'); });
      sizeRow.appendChild(b);
    });
    box.appendChild(el('p', 'sc-hint', 'Tamanho'));
    box.appendChild(sizeRow);

    if (!isProp) {
      const condRow = el('div', 'sc-conds');
      CONDITIONS.forEach(c => {
        const on = (t.conditions || []).includes(c.id);
        const b = el('button', 'sc-cond' + (on ? ' is-active' : ''), c.icon + ' ' + c.label);
        if (on) b.style.background = c.color;
        b.addEventListener('click', () => {
          store.pushUndo();
          t.conditions = t.conditions || [];
          if (on) t.conditions = t.conditions.filter(x => x !== c.id); else t.conditions.push(c.id);
          onChange('cond');
        });
        condRow.appendChild(b);
      });
      box.appendChild(el('p', 'sc-hint', 'Condições'));
      box.appendChild(condRow);
    }
  }

  function renderTokenList() {
    const box = document.getElementById('sc-tokenlist');
    box.innerHTML = '';
    box.appendChild(el('h2', 'sc-box__title', 'Tokens nesta cena'));
    if (!S.tokens.length) { box.appendChild(el('p', 'sc-empty', 'Nenhum token ainda.')); return; }
    S.tokens.forEach(t => {
      const row = el('div', 'sc-tokrow' + (tokenKey(t) === selectedId ? ' is-active' : ''));
      const dot = el('span', 'sc-tokrow__dot'); dot.style.background = factionVar(t.faction);
      row.appendChild(dot);
      row.appendChild(txt('span', 'sc-tokrow__name', t.name || '(sem nome)'));
      if (t.maxHp) {
        const hp = el('span', 'sc-tokrow__hp', '<i></i>');
        hp.querySelector('i').style.width = Math.max(0, Math.min(1, t.hp / t.maxHp)) * 100 + '%';
        row.appendChild(hp);
      }
      row.addEventListener('click', () => selectToken(tokenKey(t)));
      box.appendChild(row);
    });
  }

  function updateTokenEl(t) { const e = tokenEls.get(tokenKey(t)); if (e) updateToken(e, t); }

  // --- menu de contexto ---------------------------------------------------
  let ctxMenu = null;
  function closeContextMenu() { if (ctxMenu) { ctxMenu.remove(); ctxMenu = null; } }
  function openContextMenu(ev, key) {
    closeContextMenu();
    selectToken(key);
    const t = selectedToken(); if (!t) return;
    ctxMenu = el('div', 'sc-ctx');
    const dup = el('button', '', 'Duplicar <kbd>Ctrl+D</kbd>');
    dup.addEventListener('click', () => { duplicateToken(t); closeContextMenu(); });
    ctxMenu.appendChild(dup);
    ctxMenu.appendChild(el('div', 'sc-ctx__sep'));
    const facLabel = el('div', '', '<span style="font-size:12px;color:var(--sc-faint)">Facção</span>');
    const sw = el('div', 'sc-ctx__swatches');
    FACTIONS.forEach(f => {
      const i = el('i'); i.style.background = factionVar(f.id); i.title = f.label;
      i.addEventListener('click', () => { store.pushUndo(); t.faction = f.id; onChange('faction'); closeContextMenu(); });
      sw.appendChild(i);
    });
    ctxMenu.appendChild(facLabel); ctxMenu.appendChild(sw);
    ctxMenu.appendChild(el('div', 'sc-ctx__sep'));
    const del = el('button', 'danger', 'Remover <kbd>Del</kbd>');
    del.addEventListener('click', () => { removeToken(t); closeContextMenu(); });
    ctxMenu.appendChild(del);
    document.body.appendChild(ctxMenu);
    ctxMenu.style.left = ev.clientX + 'px'; ctxMenu.style.top = ev.clientY + 'px';
  }
  document.addEventListener('pointerdown', (ev) => { if (ctxMenu && !ctxMenu.contains(ev.target)) closeContextMenu(); });

  // --- autosave -----------------------------------------------------------
  let saveTimer = null;
  function scheduleSave() { if (saveTimer) clearTimeout(saveTimer); saveTimer = setTimeout(doSave, 800); }
  const savestate = document.getElementById('sc-savestate');
  function doSave() {
    savestate.textContent = 'salvando…';
    fetch(saveUrl, {
      method: 'POST',
      headers: { 'X-CSRFToken': csrf(), 'Content-Type': 'application/x-www-form-urlencoded' },
      body: new URLSearchParams({ scene: JSON.stringify(store.toPayload()) }),
    }).then(r => r.json()).then(data => {
      if (!data.ok) throw new Error('save');
      // reconciliar tempId -> id real
      if (data.idMap) {
        Object.keys(data.idMap).forEach(tempId => {
          const t = S.tokens.find(x => x.tempId === tempId);
          if (t) { t.id = data.idMap[tempId]; if (selectedId === tempId) selectedId = t.id; delete t.tempId; }
        });
        rekeyTokenEls();
      }
      const d = new Date();
      savestate.textContent = 'salvo ' + String(d.getHours()).padStart(2, '0') + ':' + String(d.getMinutes()).padStart(2, '0');
    }).catch(() => { savestate.textContent = 'falha ao salvar'; setTimeout(scheduleSave, 3000); });
  }
  function rekeyTokenEls() {
    tokenEls.clear();
    tokensLayer.querySelectorAll('.sc-token').forEach(e => e.remove());
    renderTokens();
  }

  // --- onChange central ---------------------------------------------------
  function onChange(source) {
    canvas.draw();
    renderTokens();
    updateUndoButtons();
    renderTokenList();
    if (source !== 'select') scheduleSave();
  }
  function updateUndoButtons() {
    document.getElementById('sc-undo').disabled = !store.canUndo();
    document.getElementById('sc-redo').disabled = !store.canRedo();
  }

  // --- header controls ----------------------------------------------------
  document.getElementById('sc-undo').addEventListener('click', () => { if (store.undo()) afterUndoRedo(); });
  document.getElementById('sc-redo').addEventListener('click', () => { if (store.redo()) afterUndoRedo(); });
  function afterUndoRedo() { selectedId = null; rekeyTokenEls(); canvas.draw(); updateUndoButtons(); renderRightRails(); scheduleSave(); }

  document.getElementById('sc-rename').addEventListener('click', () => {
    const v = prompt('Nome da cena', S.name);
    if (v != null && v.trim()) { S.name = v.trim(); document.getElementById('sc-scene-name').textContent = S.name; scheduleSave(); }
  });
  const zoomPct = document.getElementById('sc-zoom');
  root.querySelectorAll('[data-zoom]').forEach(b => b.addEventListener('click', () => {
    const k = b.dataset.zoom;
    if (k === 'in') canvas.zoomAt(1.2); else if (k === 'out') canvas.zoomAt(1 / 1.2); else canvas.fit();
    updateZoomLabel();
  }));
  function updateZoomLabel() { zoomPct.textContent = Math.round(canvas.cam.zoom * 100) + '%'; }

  // tooldock
  document.querySelectorAll('.sc-tool').forEach(b => b.addEventListener('click', () => setTool(b.dataset.tool)));

  // drag-drop de asset no palco
  stage.addEventListener('dragover', (ev) => ev.preventDefault());
  stage.addEventListener('drop', (ev) => {
    ev.preventDefault();
    const id = parseInt(ev.dataTransfer.getData('text/plain'), 10);
    if (isNaN(id)) return;
    const r = canvasEl.getBoundingClientRect();
    const [wx, wy] = canvas.screenToWorld(ev.clientX - r.left, ev.clientY - r.top);
    const [q, rr] = Hex.pixelToAxial(wx, wy, S.grid.size);
    placeTokenAt(id, q, rr);
  });

  // --- atalhos ------------------------------------------------------------
  function typing(ev) {
    const el = ev.target;
    return el && (el.tagName === 'INPUT' || el.tagName === 'TEXTAREA' || el.isContentEditable);
  }
  document.addEventListener('keydown', (ev) => {
    if (typing(ev)) return;
    if (ev.code === 'Space') { spaceHeld = true; return; }
    const key = ev.key.toLowerCase();
    const tools = { v: 'select', b: 'terrain', t: 'token', f: 'fog', r: 'measure', e: 'erase' };
    if ((ev.ctrlKey || ev.metaKey) && key === 'z') { ev.preventDefault(); if (ev.shiftKey ? store.redo() : store.undo()) afterUndoRedo(); return; }
    if ((ev.ctrlKey || ev.metaKey) && key === 'y') { ev.preventDefault(); if (store.redo()) afterUndoRedo(); return; }
    if ((ev.ctrlKey || ev.metaKey) && key === 'd') { ev.preventDefault(); const t = selectedToken(); if (t) duplicateToken(t); return; }
    if (ev.ctrlKey || ev.metaKey) return;
    if (tools[key]) { setTool(tools[key]); return; }
    if (key === '0') { canvas.fit(); updateZoomLabel(); return; }
    if (key === 'escape') { selectToken(null); canvas.setRuler(null); closeContextMenu(); return; }
    const t = selectedToken();
    if (!t) return;
    if (key === 'delete' || key === 'backspace') { ev.preventDefault(); removeToken(t); return; }
    const nudges = { arrowup: [0, -1], arrowdown: [0, 1], arrowleft: [-1, 0], arrowright: [1, 0] };
    if (nudges[key]) { ev.preventDefault(); store.pushUndo(); t.q += nudges[key][0]; t.r += nudges[key][1]; onChange('move'); }
  });
  document.addEventListener('keyup', (ev) => { if (ev.code === 'Space') spaceHeld = false; });

  // --- boot ---------------------------------------------------------------
  function boot() {
    renderPanel();
    renderRightRails();
    renderTokens();
    canvas.fit();
    updateZoomLabel();
    updateUndoButtons();
    // % de zoom acompanha a roda do mouse (botões/atalhos atualizam direto)
    stage.addEventListener('wheel', () => requestAnimationFrame(updateZoomLabel), { passive: true });
  }
  boot();
})();
