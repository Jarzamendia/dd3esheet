// scene_live.js — LiveStage: renderer read-only + polling + move de jogador +
// utilidades efêmeras (régua/cone/ping/marcador/tela cheia). Depende de hex.js,
// scene_state.js, scene_canvas.js.
(function () {
  const root = document.querySelector('.sc-live');
  if (!root) return;
  const canvasEl = document.getElementById('sc-canvas');
  if (!canvasEl) return;

  const SIZE_SCALE = { sm: 0.74, md: 1, lg: 1.6, xl: 2.3 };
  const COLORS = ['#c8923a', '#8a2f28', '#3f6079', '#4f6b3a', '#5d4978', '#b58a36', '#2b2622'];

  function readJSON(id) { const el = document.getElementById(id); try { return el ? JSON.parse(el.textContent) : null; } catch (e) { return null; } }
  function csrf() { const el = root.querySelector('[name=csrfmiddlewaretoken]'); return el ? el.value : ''; }
  function elNode(tag, cls) { const e = document.createElement(tag); if (cls) e.className = cls; return e; }
  function cssUrl(u) { return 'url(' + JSON.stringify(String(u)) + ')'; }
  function factionVar(f) { return 'var(--sc-' + (f || 'enemy') + ')'; }

  let scene = readJSON('tt-scene-data');
  if (!scene || scene.empty) return;
  const terrainList = readJSON('tt-terrain-data') || [];
  const terrainPalette = {}; terrainList.forEach(t => { terrainPalette[t.id] = t; });
  const canEdit = root.dataset.canEdit === '1';
  const moveUrlTpl = root.dataset.moveUrl || '';
  const fragmentUrl = root.dataset.liveFragmentUrl;

  const stage = document.getElementById('sc-stage');
  const tokensLayer = document.getElementById('sc-tokens');
  let store = SceneState.create(scene);
  let S = store.s;

  let util = 'move';
  let utilColor = COLORS[0];
  const markers = new Map();  // hexKey -> {el, color}
  let measureStart = null;

  const canvas = SceneCanvas.create(canvasEl, store, {
    terrainPalette,
    fogOpaque: true,
    zoomMin: 0.12, zoomMax: 3.2,
    getLayers: () => ({ terrain: {}, tokens: {}, fog: {}, grid: {} }),
    onCamChange: positionAll,
    shouldPan: (ev) => util === 'move' || ev.button === 1 || ev.button === 2,
    onPointer: onStagePointer,
  });

  // --- tokens (read-only, arraste se permitido) --------------------------
  const tokenEls = new Map();
  function tokenKey(t) { return t.id != null ? t.id : t.tempId; }

  function renderTokens() {
    const present = new Set();
    S.tokens.forEach(t => {
      const k = tokenKey(t); present.add(k);
      let e = tokenEls.get(k);
      if (!e) { e = buildToken(t); tokenEls.set(k, e); tokensLayer.appendChild(e); }
      updateToken(e, t);
    });
    tokenEls.forEach((e, k) => { if (!present.has(k)) { e.remove(); tokenEls.delete(k); } });
    positionAll();
  }
  function buildToken(t) {
    const e = elNode('div', 'sc-token');
    e.appendChild(elNode('div', 'sc-token__disc'));
    const hp = elNode('div', 'sc-token__hp'); hp.appendChild(document.createElement('i')); e.appendChild(hp);
    e.appendChild(elNode('div', 'sc-token__name'));
    e.addEventListener('pointerdown', (ev) => onTokenDown(ev, t));
    return e;
  }
  function updateToken(e, t) {
    e.style.setProperty('--ring', factionVar(t.faction));
    const disc = e.querySelector('.sc-token__disc');
    if (t.spriteUrl) { disc.style.backgroundImage = cssUrl(t.spriteUrl); e.classList.remove('sc-token--placeholder'); }
    else { disc.style.backgroundImage = 'none'; e.classList.add('sc-token--placeholder'); }
    const hp = e.querySelector('.sc-token__hp');
    if (!t.maxHp || t.kind === 'object') hp.style.display = 'none';
    else {
      hp.style.display = '';
      const ratio = Math.max(0, Math.min(1, t.hp / t.maxHp));
      const bar = hp.querySelector('i');
      bar.style.width = (ratio * 100) + '%';
      bar.style.background = ratio > 0.6 ? 'var(--forest)' : ratio > 0.3 ? 'var(--muted-gold)' : 'var(--deep-red)';
    }
    e.querySelector('.sc-token__name').textContent = t.name || '';
    e.style.cursor = (canEdit || t.movable) ? 'grab' : 'default';
  }
  function positionAll() {
    const z = canvas.cam.zoom;
    S.tokens.forEach(t => {
      const e = tokenEls.get(tokenKey(t)); if (!e) return;
      const [wx, wy] = Hex.axialToPixel(t.q, t.r, S.grid.size);
      const [sx, sy] = canvas.worldToScreen(wx, wy);
      const d = S.grid.size * (SIZE_SCALE[t.size] || 1) * z;
      e.style.left = sx + 'px'; e.style.top = sy + 'px'; e.style.width = d + 'px'; e.style.height = d + 'px';
      e.querySelector('.sc-token__name').style.display = z > 0.78 ? '' : 'none';
    });
    markers.forEach((m, key) => {
      const [q, r] = key.split(',').map(Number);
      const [wx, wy] = Hex.axialToPixel(q, r, S.grid.size);
      const [sx, sy] = canvas.worldToScreen(wx, wy);
      m.el.style.left = sx + 'px'; m.el.style.top = sy + 'px';
    });
  }

  // --- move de jogador ----------------------------------------------------
  let drag = null;
  function onTokenDown(ev, t) {
    if (ev.button !== 0 || util !== 'move') return;
    if (!(canEdit || t.movable)) return;
    ev.stopPropagation();
    const e = tokenEls.get(tokenKey(t));
    drag = { t, moved: false };
    e.setPointerCapture(ev.pointerId);
    e.addEventListener('pointermove', onTokenMove);
    e.addEventListener('pointerup', onTokenUp);
  }
  function onTokenMove(ev) {
    if (!drag) return;
    const r = canvasEl.getBoundingClientRect();
    const [wx, wy] = canvas.screenToWorld(ev.clientX - r.left, ev.clientY - r.top);
    const [q, rr] = Hex.pixelToAxial(wx, wy, S.grid.size);
    if (q === drag.t.q && rr === drag.t.r) return;
    drag.moved = true; drag.t.q = q; drag.t.r = rr; positionAll();
  }
  function onTokenUp(ev) {
    const e = ev.currentTarget;
    e.removeEventListener('pointermove', onTokenMove);
    e.removeEventListener('pointerup', onTokenUp);
    try { e.releasePointerCapture(ev.pointerId); } catch (x) {}
    if (drag && drag.moved) commitMove(drag.t);
    drag = null;
  }
  function commitMove(t) {
    const [x, y] = Hex.axialToPixel(t.q, t.r, S.grid.size);
    const url = moveUrlTpl.replace('/token/0/move', '/token/' + t.id + '/move');
    fetch(url, {
      method: 'POST',
      headers: { 'X-CSRFToken': csrf(), 'Content-Type': 'application/x-www-form-urlencoded' },
      body: new URLSearchParams({ X: x, Y: y }),
    }).catch(() => {});
  }

  // --- utilidades (régua/cone/ping/marcador) -----------------------------
  function onStagePointer(phase, world, ev) {
    const [q, r] = Hex.pixelToAxial(world[0], world[1], S.grid.size);
    if (util === 'ruler' || util === 'cone') {
      if (phase === 'down') measureStart = [q, r];
      else if (phase === 'move' && measureStart) canvas.setRuler({ a: measureStart, b: [q, r], type: util === 'cone' ? 'cone' : 'ruler' });
      else if (phase === 'up') measureStart = null;  // mantém desenho até limpar/novo
    } else if (util === 'ping' && phase === 'down') {
      spawnPing(q, r);
    } else if (util === 'marker' && phase === 'down') {
      toggleMarker(q, r);
    }
  }
  function spawnPing(q, r) {
    const [wx, wy] = Hex.axialToPixel(q, r, S.grid.size);
    const [sx, sy] = canvas.worldToScreen(wx, wy);
    const ping = elNode('div', 'sc-ping');
    ping.style.left = sx + 'px'; ping.style.top = sy + 'px';
    ping.style.setProperty('--ping', utilColor);
    for (let i = 0; i < 3; i++) { const ring = document.createElement('i'); ring.style.animationDelay = (i * 0.18) + 's'; ping.appendChild(ring); }
    tokensLayer.appendChild(ping);
    setTimeout(() => ping.remove(), 1600);
  }
  function toggleMarker(q, r) {
    const key = Hex.key(q, r);
    if (markers.has(key)) { markers.get(key).el.remove(); markers.delete(key); return; }
    const pin = elNode('div', 'sc-pin'); pin.textContent = '📍'; pin.style.setProperty('--pin', utilColor);
    pin.style.color = utilColor;
    tokensLayer.appendChild(pin);
    markers.set(key, { el: pin, color: utilColor });
    positionAll();
  }
  function clearUtils() {
    canvas.setRuler(null); measureStart = null;
    markers.forEach(m => m.el.remove()); markers.clear();
    tokensLayer.querySelectorAll('.sc-ping').forEach(p => p.remove());
  }

  // dock
  root.querySelectorAll('[data-util]').forEach(b => b.addEventListener('click', () => {
    util = b.dataset.util;
    root.querySelectorAll('[data-util]').forEach(x => x.classList.toggle('is-active', x === b));
    if (util !== 'ruler' && util !== 'cone') canvas.setRuler(null);
  }));
  const colorsBox = document.getElementById('sc-live-colors');
  COLORS.forEach((c, i) => {
    const sw = document.createElement('i'); sw.style.background = c; sw.title = 'Cor';
    if (i === 0) sw.style.outline = '2px solid var(--sc-text)';
    sw.addEventListener('click', () => {
      utilColor = c;
      colorsBox.querySelectorAll('i').forEach(x => x.style.outline = 'none');
      sw.style.outline = '2px solid var(--sc-text)';
    });
    colorsBox.appendChild(sw);
  });
  const clearBtn = document.getElementById('sc-util-clear');
  if (clearBtn) clearBtn.addEventListener('click', clearUtils);

  // zoom + fullscreen
  const zoomPct = document.getElementById('sc-zoom');
  function updateZoom() { if (zoomPct) zoomPct.textContent = Math.round(canvas.cam.zoom * 100) + '%'; }
  root.querySelectorAll('[data-zoom]').forEach(b => b.addEventListener('click', () => {
    const k = b.dataset.zoom;
    if (k === 'in') canvas.zoomAt(1.2); else if (k === 'out') canvas.zoomAt(1 / 1.2); else canvas.fit();
    updateZoom();
  }));
  stage.addEventListener('wheel', () => requestAnimationFrame(updateZoom), { passive: true });
  const fs = document.getElementById('sc-fullscreen');
  if (fs) fs.addEventListener('click', () => {
    if (document.fullscreenElement) document.exitFullscreen();
    else stage.requestFullscreen && stage.requestFullscreen();
  });

  // --- polling ------------------------------------------------------------
  // Importante: o canvas guarda referência ao MESMO objeto `S`, então atualizamos
  // o conteúdo in-place (não recriamos o store) para o render refletir os dados.
  let lastJSON = JSON.stringify(scene);
  function applyData(data) {
    S.name = data.name || '';
    Object.assign(S.grid, data.grid || {});
    S.terrain.clear();
    (data.terrain || []).forEach(c => S.terrain.set(Hex.key(c.q, c.r), c.terrain));
    S.fog.clear();
    (data.fog || []).forEach(c => S.fog.add(Hex.key(c.q, c.r)));
    S.tokens = (data.tokens || []).map(t => Object.assign({}, t));
  }
  function poll() {
    fetch(fragmentUrl, { headers: { 'X-Requested-With': 'fetch' } })
      .then(r => r.json())
      .then(data => {
        if (!data || data.empty) return;
        const str = JSON.stringify(data);
        if (str === lastJSON) return;
        if (drag) return;  // não atropela um arraste em andamento
        lastJSON = str;
        applyData(data);
        canvas.draw(); renderTokens();
      }).catch(() => {});
  }

  // --- boot ---------------------------------------------------------------
  canvas.fit(); updateZoom(); renderTokens();
  setInterval(poll, 2000);
})();
