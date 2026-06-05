// scene_canvas.js — renderer 2D da cena (terreno/grade/névoa/régua) + câmera.
// window.SceneCanvas.create(canvas, store, opts) -> controlador.
//
// opts: {
//   terrainPalette: { id: {kind, color, url} },
//   fogOpaque: bool,                  // live: névoa opaca
//   getLayers: () => ({terrain:{visible}, tokens, fog, grid}),
//   onCamChange: fn,                  // reposicionar overlay DOM
//   onPointer: (phase, world, ev) => {}, // phase: 'down'|'move'|'up'
//   shouldPan: (ev) => bool,
//   zoomMin, zoomMax,
// }
(function (global) {
  function create(canvas, store, opts) {
    opts = opts || {};
    const ctx = canvas.getContext('2d');
    const s = store.s;
    const cam = { x: 0, y: 0, zoom: 1 };
    const ZMIN = opts.zoomMin || 0.18, ZMAX = opts.zoomMax || 3;
    const palette = opts.terrainPalette || {};
    const patterns = {};   // id -> CanvasPattern | 'loading'
    let brushPreview = [];
    let ruler = null;      // {a:[q,r], b:[q,r], type:'ruler'|'cone'}
    let dpr = global.devicePixelRatio || 1;

    function size() { return s.grid.size; }
    function layers() { return opts.getLayers ? opts.getLayers() : { terrain: {}, tokens: {}, fog: {}, grid: {} }; }

    function setDims() {
      dpr = global.devicePixelRatio || 1;
      const r = canvas.getBoundingClientRect();
      canvas.width = Math.max(1, Math.round(r.width * dpr));
      canvas.height = Math.max(1, Math.round(r.height * dpr));
    }
    function resize() { setDims(); draw(); }

    function worldToScreen(wx, wy) { return [wx * cam.zoom + cam.x, wy * cam.zoom + cam.y]; }
    function screenToWorld(sx, sy) { return [(sx - cam.x) / cam.zoom, (sy - cam.y) / cam.zoom]; }

    function viewBoundsWorld() {
      const r = canvas.getBoundingClientRect();
      const [x0, y0] = screenToWorld(0, 0);
      const [x1, y1] = screenToWorld(r.width, r.height);
      return { x0, y0, x1, y1 };
    }

    // bloco retangular de hexes (offset odd-r) -> lista de [q,r]
    function gridCells() {
      const cells = [];
      const cols = s.grid.cols, rows = s.grid.rows;
      for (let row = 0; row < rows; row++) {
        const qStart = -Math.floor(row / 2);
        for (let col = 0; col < cols; col++) cells.push([qStart + col, row]);
      }
      return cells;
    }

    function hexPath(cx, cy) {
      const pts = Hex.corners(cx, cy, size());
      ctx.beginPath();
      pts.forEach((p, i) => { if (i === 0) ctx.moveTo(p[0], p[1]); else ctx.lineTo(p[0], p[1]); });
      ctx.closePath();
    }

    function ensurePattern(id, url) {
      if (!url) return null;
      if (patterns[id] && patterns[id] !== 'loading') return patterns[id];
      if (patterns[id] === 'loading') return null;
      patterns[id] = 'loading';
      const img = new Image();
      img.onload = function () {
        try { patterns[id] = ctx.createPattern(img, 'repeat'); } catch (e) { patterns[id] = null; }
        draw();
      };
      img.onerror = function () { patterns[id] = null; };
      img.src = url;
      return null;
    }

    function fillTerrain(cx, cy, terrainId) {
      const def = palette[terrainId];
      hexPath(cx, cy);
      if (def && def.kind === 'texture' && def.url) {
        const pat = ensurePattern(terrainId, def.url);
        ctx.fillStyle = pat || (def.color || '#888');
      } else {
        ctx.fillStyle = (def && def.color) || '#d8d4ca';
      }
      ctx.fill();
    }

    function draw() {
      const L = layers();
      ctx.setTransform(1, 0, 0, 1, 0, 0);
      ctx.clearRect(0, 0, canvas.width, canvas.height);
      ctx.setTransform(dpr * cam.zoom, 0, 0, dpr * cam.zoom, dpr * cam.x, dpr * cam.y);

      const vb = viewBoundsWorld();
      const inView = (cx, cy) => cx > vb.x0 - size() && cx < vb.x1 + size() && cy > vb.y0 - size() && cy < vb.y1 + size();

      // terreno
      if (!L.terrain || L.terrain.visible !== false) {
        s.terrain.forEach((terrainId, key) => {
          const [q, r] = key.split(',').map(Number);
          const [cx, cy] = Hex.axialToPixel(q, r, size());
          if (inView(cx, cy)) fillTerrain(cx, cy, terrainId);
        });
      }

      // grade
      if ((!L.grid || L.grid.visible !== false) && s.grid.showGrid) {
        ctx.lineWidth = 1 / cam.zoom;
        ctx.strokeStyle = 'rgba(43,38,34,.18)';
        gridCells().forEach(([q, r]) => {
          const [cx, cy] = Hex.axialToPixel(q, r, size());
          if (inView(cx, cy)) { hexPath(cx, cy); ctx.stroke(); }
        });
      }

      // névoa
      if (!L.fog || L.fog.visible !== false) {
        ctx.fillStyle = opts.fogOpaque ? 'rgba(20,18,16,.96)' : 'rgba(20,18,16,.42)';
        s.fog.forEach(key => {
          const [q, r] = key.split(',').map(Number);
          const [cx, cy] = Hex.axialToPixel(q, r, size());
          if (inView(cx, cy)) { hexPath(cx, cy); ctx.fill(); }
        });
      }

      // prévia de pincel
      if (brushPreview.length) {
        ctx.lineWidth = 2 / cam.zoom;
        ctx.strokeStyle = '#c8923a';
        brushPreview.forEach(([q, r]) => {
          const [cx, cy] = Hex.axialToPixel(q, r, size());
          hexPath(cx, cy); ctx.stroke();
        });
      }

      // régua / cone
      if (ruler) drawRuler();

      if (opts.onCamChange) opts.onCamChange();
    }

    function drawRuler() {
      const [ax, ay] = Hex.axialToPixel(ruler.a[0], ruler.a[1], size());
      const [bx, by] = Hex.axialToPixel(ruler.b[0], ruler.b[1], size());
      const n = Hex.distance(ruler.a[0], ruler.a[1], ruler.b[0], ruler.b[1]);
      ctx.lineWidth = 2 / cam.zoom;
      ctx.strokeStyle = '#c8923a';
      ctx.fillStyle = 'rgba(200,146,58,.18)';
      if (ruler.type === 'cone') {
        const CONE_HALF = Math.PI / 6;
        const ang = Math.atan2(by - ay, bx - ax);
        const len = Math.hypot(bx - ax, by - ay);
        ctx.beginPath();
        ctx.moveTo(ax, ay);
        ctx.lineTo(ax + Math.cos(ang - CONE_HALF) * len, ay + Math.sin(ang - CONE_HALF) * len);
        ctx.lineTo(ax + Math.cos(ang + CONE_HALF) * len, ay + Math.sin(ang + CONE_HALF) * len);
        ctx.closePath(); ctx.fill(); ctx.stroke();
      } else {
        ctx.beginPath(); ctx.moveTo(ax, ay); ctx.lineTo(bx, by); ctx.stroke();
      }
      // label
      const label = n + ' hex · ' + (n * 1.5).toFixed(1).replace('.', ',') + ' m';
      ctx.setTransform(dpr, 0, 0, dpr, 0, 0);
      const [lsx, lsy] = worldToScreen((ax + bx) / 2, (ay + by) / 2);
      ctx.font = '12px sans-serif'; ctx.fillStyle = '#2b2622';
      ctx.fillStyle = 'rgba(244,236,217,.9)';
      const w = ctx.measureText(label).width + 10;
      ctx.fillRect(lsx, lsy - 18, w, 16);
      ctx.fillStyle = '#2b2622';
      ctx.fillText(label, lsx + 5, lsy - 6);
      // restaura transform de mundo
      ctx.setTransform(dpr * cam.zoom, 0, 0, dpr * cam.zoom, dpr * cam.x, dpr * cam.y);
    }

    function fit() {
      const cells = gridCells();
      if (!cells.length) return;
      let minX = Infinity, minY = Infinity, maxX = -Infinity, maxY = -Infinity;
      const half = size();
      cells.forEach(([q, r]) => {
        const [cx, cy] = Hex.axialToPixel(q, r, size());
        minX = Math.min(minX, cx - half); maxX = Math.max(maxX, cx + half);
        minY = Math.min(minY, cy - half); maxY = Math.max(maxY, cy + half);
      });
      const rect = canvas.getBoundingClientRect();
      const pad = 40;
      const zx = (rect.width - pad * 2) / (maxX - minX);
      const zy = (rect.height - pad * 2) / (maxY - minY);
      cam.zoom = Math.max(ZMIN, Math.min(ZMAX, Math.min(zx, zy)));
      cam.x = rect.width / 2 - ((minX + maxX) / 2) * cam.zoom;
      cam.y = rect.height / 2 - ((minY + maxY) / 2) * cam.zoom;
      draw();
    }

    function zoomAt(sx, sy, factor) {
      const [wx, wy] = screenToWorld(sx, sy);
      cam.zoom = Math.max(ZMIN, Math.min(ZMAX, cam.zoom * factor));
      cam.x = sx - wx * cam.zoom;
      cam.y = sy - wy * cam.zoom;
      draw();
    }

    // --- eventos ----------------------------------------------------------
    let panning = false, panLast = null, panStart = null, panMoved = 0;

    canvas.addEventListener('wheel', function (ev) {
      ev.preventDefault();
      const r = canvas.getBoundingClientRect();
      zoomAt(ev.clientX - r.left, ev.clientY - r.top, ev.deltaY < 0 ? 1.1 : 1 / 1.1);
    }, { passive: false });

    function localPoint(ev) {
      const r = canvas.getBoundingClientRect();
      return [ev.clientX - r.left, ev.clientY - r.top];
    }

    canvas.addEventListener('pointerdown', function (ev) {
      const [sx, sy] = localPoint(ev);
      if (opts.shouldPan && opts.shouldPan(ev)) {
        panning = true; panLast = [ev.clientX, ev.clientY]; panStart = [ev.clientX, ev.clientY]; panMoved = 0;
        canvas.setPointerCapture(ev.pointerId);
        ev.preventDefault();
        return;
      }
      if (opts.onPointer) opts.onPointer('down', screenToWorld(sx, sy), ev);
    });
    canvas.addEventListener('pointermove', function (ev) {
      if (panning) {
        cam.x += ev.clientX - panLast[0];
        cam.y += ev.clientY - panLast[1];
        panMoved += Math.abs(ev.clientX - panLast[0]) + Math.abs(ev.clientY - panLast[1]);
        panLast = [ev.clientX, ev.clientY];
        draw();
        return;
      }
      const [sx, sy] = localPoint(ev);
      if (opts.onPointer) opts.onPointer('move', screenToWorld(sx, sy), ev);
    });
    function endPan(ev) {
      if (panning) {
        panning = false;
        try { canvas.releasePointerCapture(ev.pointerId); } catch (e) {}
        if (panMoved < 4 && opts.onBackgroundTap) {
          const [sx, sy] = localPoint(ev);
          opts.onBackgroundTap(screenToWorld(sx, sy), ev);
        }
        return true;
      }
      return false;
    }
    canvas.addEventListener('pointerup', function (ev) {
      if (endPan(ev)) return;
      const [sx, sy] = localPoint(ev);
      if (opts.onPointer) opts.onPointer('up', screenToWorld(sx, sy), ev);
    });
    canvas.addEventListener('contextmenu', function (ev) { ev.preventDefault(); });
    global.addEventListener('resize', resize);

    // só dimensiona; o primeiro desenho fica para o consumidor (fit() no boot),
    // evitando TDZ de estado declarado após a criação do canvas.
    setDims();

    return {
      cam, draw, fit, resize, worldToScreen, screenToWorld,
      zoomAt: (factor) => { const r = canvas.getBoundingClientRect(); zoomAt(r.width / 2, r.height / 2, factor); },
      setBrushPreview(cells) { brushPreview = cells || []; draw(); },
      setRuler(r) { ruler = r; draw(); },
      gridCells,
    };
  }

  global.SceneCanvas = { create };
})(window);
