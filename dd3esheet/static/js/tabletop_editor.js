/* Rich tabletop scene editor. State here is client-side view state; mutations go to Django. */
(function () {
    'use strict';

    var SQ3 = Math.sqrt(3);
    var M_PER_CELL = 1.5;
    var state = {
        tool: 'select',
        paletteTab: 'token',
        selectedTile: null,
        selectedToken: null,
        scale: 1,
        panX: 0,
        panY: 0,
        locks: { terrain: false, tokens: false }
    };

    function editor() { return document.querySelector('[data-rich-editor="1"]'); }
    function stage() { return document.getElementById('tt-stage'); }
    function world() { return document.getElementById('tt-world'); }
    function overlay() { return document.getElementById('tt-editor-canvas'); }
    function canvas() {
        var ed = editor();
        return ed ? ed.querySelector('.tt-canvas') : null;
    }
    function htmxPost(url, values) {
        if (!url || !window.htmx) return;
        window.htmx.ajax('POST', url, { target: '#tt-editor', swap: 'innerHTML', values: values || {} });
    }

    function cubeRound(q, r) {
        var x = q, z = r, y = -x - z;
        var rx = Math.round(x), ry = Math.round(y), rz = Math.round(z);
        var dx = Math.abs(rx - x), dy = Math.abs(ry - y), dz = Math.abs(rz - z);
        if (dx > dy && dx > dz) rx = -ry - rz; else if (dy > dz) ry = -rx - rz; else rz = -rx - ry;
        return [rx, rz];
    }
    function gridSize() {
        var cv = canvas();
        return cv ? (parseInt(cv.dataset.gridSize, 10) || 64) : 64;
    }
    function cellAt(p) {
        var R = gridSize() / SQ3;
        var q = (SQ3 / 3 * p.x - 1 / 3 * p.y) / R;
        var r = (2 / 3 * p.y) / R;
        var a = cubeRound(q, r);
        return { q: a[0], r: a[1] };
    }
    function axialToPixel(q, r) {
        var R = gridSize() / SQ3;
        return { x: SQ3 * R * (q + r / 2), y: 1.5 * R * r };
    }
    function snapWorld(p) {
        var c = cellAt(p);
        var px = axialToPixel(c.q, c.r);
        return { x: Math.round(px.x), y: Math.round(px.y), q: c.q, r: c.r };
    }
    function screenToWorld(ev) {
        var st = stage();
        var r = st.getBoundingClientRect();
        return {
            x: (ev.clientX - r.left - state.panX) / state.scale,
            y: (ev.clientY - r.top - state.panY) / state.scale
        };
    }
    function screenPoint(ev) {
        var st = stage();
        var r = st.getBoundingClientRect();
        return { x: ev.clientX - r.left, y: ev.clientY - r.top };
    }

    function applyTransform() {
        var w = world();
        if (!w) return;
        w.style.transform = 'translate(' + state.panX + 'px,' + state.panY + 'px) scale(' + state.scale + ')';
        w.style.transformOrigin = '0 0';
        var pct = document.getElementById('zoom-pct');
        if (pct) pct.textContent = Math.round(state.scale * 100) + '%';
    }
    function resizeOverlay() {
        var st = stage(), ov = overlay();
        if (!st || !ov) return;
        ov.width = st.clientWidth;
        ov.height = st.clientHeight;
    }
    function fitView() {
        var st = stage(), cv = canvas();
        if (!st || !cv) return;
        var w = parseInt(cv.style.width, 10) || cv.offsetWidth || 1600;
        var h = parseInt(cv.style.height, 10) || cv.offsetHeight || 1200;
        state.scale = Math.max(0.15, Math.min((st.clientWidth - 24) / w, (st.clientHeight - 24) / h));
        state.panX = Math.round((st.clientWidth - w * state.scale) / 2);
        state.panY = Math.round((st.clientHeight - h * state.scale) / 2);
        applyTransform();
    }
    function zoomBy(mult, ev) {
        var before = ev ? screenToWorld(ev) : null;
        state.scale = Math.max(0.2, Math.min(3, state.scale * mult));
        if (before && ev) {
            var st = stage().getBoundingClientRect();
            state.panX = ev.clientX - st.left - before.x * state.scale;
            state.panY = ev.clientY - st.top - before.y * state.scale;
        }
        applyTransform();
    }

    function setTool(tool) {
        state.tool = tool || 'select';
        var ed = editor();
        if (!ed) return;
        ed.classList.remove('tool-select', 'tool-place', 'tool-paint', 'tool-measure');
        ed.classList.add('tool-' + state.tool);
        document.querySelectorAll('[data-tool]').forEach(function (b) {
            b.classList.toggle('is-active', b.dataset.tool === state.tool);
        });
        var hint = document.getElementById('sb-hint');
        if (hint) hint.textContent = state.tool;
    }
    function setPaletteTab(tab) {
        state.paletteTab = tab || 'token';
        document.querySelectorAll('[data-palette-tab]').forEach(function (b) {
            b.classList.toggle('is-active', b.dataset.paletteTab === state.paletteTab);
        });
        document.querySelectorAll('.tt-ptile').forEach(function (tile) {
            tile.hidden = tile.dataset.spriteKind !== state.paletteTab;
        });
        document.querySelectorAll('.tt-empty--tokens').forEach(function (el) { el.hidden = state.paletteTab !== 'token'; });
        document.querySelectorAll('.tt-empty--tiles').forEach(function (el) { el.hidden = state.paletteTab !== 'tile'; });
    }
    function selectPalette(tile) {
        state.selectedTile = tile ? {
            spriteId: tile.dataset.spriteId || '',
            spriteKind: tile.dataset.spriteKind,
            kind: tile.dataset.kind || 'enemy',
            label: tile.dataset.label || ''
        } : null;
        document.querySelectorAll('.tt-ptile').forEach(function (t) { t.classList.toggle('is-selected', t === tile); });
        if (state.selectedTile && state.selectedTile.spriteKind === 'tile') setTool('paint');
        if (state.selectedTile && state.selectedTile.spriteKind === 'token') setTool('place');
    }
    function selectedTokenName(tok) {
        var label = tok.querySelector('.tt-token__label');
        return label ? label.textContent : (tok.dataset.kind || 'Token');
    }
    function selectToken(tok) {
        document.querySelectorAll('.tt-token.is-selected').forEach(function (t) { t.classList.remove('is-selected'); });
        state.selectedToken = tok || null;
        var empty = document.getElementById('tt-inspector-empty');
        var box = document.getElementById('tt-token-inspector');
        if (!tok) {
            if (empty) empty.hidden = false;
            if (box) box.hidden = true;
            return;
        }
        tok.classList.add('is-selected');
        if (empty) empty.hidden = true;
        if (box) box.hidden = false;
        var name = document.getElementById('tt-token-name');
        if (name) name.textContent = selectedTokenName(tok);
        setRotationControl(parseInt(tok.dataset.rotation, 10) || 0);
    }
    function setRotationControl(value) {
        var input = document.getElementById('tt-rotation');
        var out = document.getElementById('tt-rotation-value');
        if (input) input.value = value;
        if (out) out.textContent = value;
    }
    function applyTokenRotation(tok, value) {
        tok.dataset.rotation = value;
        tok.style.transform = 'translate(-50%, -50%) rotate(' + value + 'deg)';
        setRotationControl(value);
    }

    function postPlace(p, tile) {
        var ed = editor();
        var cv = canvas();
        if (!ed || !cv || !tile) return;
        var s = snapWorld(p);
        htmxPost(ed.dataset.addTokenUrl, {
            MapId: ed.dataset.mapId,
            SpriteId: tile.spriteId,
            Kind: tile.kind || 'enemy',
            Label: tile.label || '',
            X: s.x,
            Y: s.y
        });
    }
    function postPaint(cells) {
        var ed = editor();
        if (!ed || state.locks.terrain || !cells.length) return;
        var values = { cells: cells.join(';') };
        if (state.selectedTile && state.selectedTile.spriteKind === 'tile') values.SpriteId = state.selectedTile.spriteId;
        htmxPost(ed.dataset.paintTerrainUrl, values);
    }

    function startPan(ev) {
        ev.preventDefault();
        var sx = ev.clientX, sy = ev.clientY, px = state.panX, py = state.panY;
        stage().classList.add('panning');
        function move(e) {
            state.panX = px + (e.clientX - sx);
            state.panY = py + (e.clientY - sy);
            applyTransform();
        }
        function up() {
            document.removeEventListener('pointermove', move);
            document.removeEventListener('pointerup', up);
            var st = stage();
            if (st) st.classList.remove('panning');
        }
        document.addEventListener('pointermove', move);
        document.addEventListener('pointerup', up);
    }
    function startTokenMove(ev, tok) {
        if (state.locks.tokens || !tok.dataset.moveUrl) return;
        ev.preventDefault();
        selectToken(tok);
        tok.classList.add('is-dragging');
        function move(e) {
            var p = screenToWorld(e);
            tok.style.left = Math.round(p.x) + 'px';
            tok.style.top = Math.round(p.y) + 'px';
        }
        function up(e) {
            document.removeEventListener('pointermove', move);
            document.removeEventListener('pointerup', up);
            tok.classList.remove('is-dragging');
            var s = snapWorld(screenToWorld(e));
            tok.style.left = s.x + 'px';
            tok.style.top = s.y + 'px';
            htmxPost(tok.dataset.moveUrl, { X: s.x, Y: s.y });
        }
        document.addEventListener('pointermove', move);
        document.addEventListener('pointerup', up);
    }
    function startPaint(ev) {
        if (state.locks.terrain) return;
        ev.preventDefault();
        var seen = {};
        function add(e) {
            var c = cellAt(screenToWorld(e));
            seen[c.q + ',' + c.r] = true;
            updateCoord(c);
        }
        function move(e) { add(e); }
        function up() {
            document.removeEventListener('pointermove', move);
            document.removeEventListener('pointerup', up);
            postPaint(Object.keys(seen));
        }
        add(ev);
        document.addEventListener('pointermove', move);
        document.addEventListener('pointerup', up);
    }
    function startMeasure(ev) {
        ev.preventDefault();
        var start = cellAt(screenToWorld(ev));
        var ov = overlay();
        function draw(e) {
            var end = cellAt(screenToWorld(e));
            var a = axialToPixel(start.q, start.r);
            var b = axialToPixel(end.q, end.r);
            var ap = { x: a.x * state.scale + state.panX, y: a.y * state.scale + state.panY };
            var bp = { x: b.x * state.scale + state.panX, y: b.y * state.scale + state.panY };
            var g = ov.getContext('2d');
            g.clearRect(0, 0, ov.width, ov.height);
            g.strokeStyle = 'rgba(132, 31, 31, .95)';
            g.lineWidth = 2;
            g.beginPath();
            g.moveTo(ap.x, ap.y);
            g.lineTo(bp.x, bp.y);
            g.stroke();
            var dist = hexDistance(start, end);
            var meas = document.getElementById('tt-meas');
            if (meas) meas.textContent = dist + ' hex / ' + (dist * M_PER_CELL).toFixed(1) + ' m';
        }
        function up() {
            document.removeEventListener('pointermove', draw);
            document.removeEventListener('pointerup', up);
        }
        draw(ev);
        document.addEventListener('pointermove', draw);
        document.addEventListener('pointerup', up);
    }
    function hexDistance(a, b) {
        var dq = a.q - b.q, dr = a.r - b.r, ds = -a.q - a.r - (-b.q - b.r);
        return (Math.abs(dq) + Math.abs(dr) + Math.abs(ds)) / 2;
    }
    function updateCoord(c) {
        var coord = document.getElementById('sb-coord');
        if (coord) coord.textContent = 'q' + c.q + ' r' + c.r;
    }

    function updateLayerClasses() {
        var ed = editor();
        if (!ed) return;
        ['terrain', 'tokens', 'fog'].forEach(function (name) {
            var input = document.querySelector('[data-layer-visible="' + name + '"]');
            ed.classList.toggle('tt-hide-' + name, input && !input.checked);
        });
        ['terrain', 'tokens'].forEach(function (name) {
            var input = document.querySelector('[data-layer-lock="' + name + '"]');
            state.locks[name] = !!(input && input.checked);
            ed.classList.toggle('tt-lock-' + name, state.locks[name]);
        });
    }
    function filterPalette(term) {
        term = (term || '').toLowerCase();
        document.querySelectorAll('.tt-ptile').forEach(function (tile) {
            var label = (tile.dataset.label || '').toLowerCase();
            var activeTab = tile.dataset.spriteKind === state.paletteTab;
            tile.hidden = !activeTab || (term && label.indexOf(term) === -1);
        });
    }

    document.body.addEventListener('click', function (ev) {
        if (!editor()) return;
        var tool = ev.target.closest('[data-tool]');
        if (tool) { setTool(tool.dataset.tool); return; }
        var tab = ev.target.closest('[data-palette-tab]');
        if (tab) { setPaletteTab(tab.dataset.paletteTab); return; }
        var tile = ev.target.closest('.tt-ptile');
        if (tile) { selectPalette(tile); return; }
        var zoom = ev.target.closest('[data-zoom]');
        if (zoom) {
            if (zoom.dataset.zoom === 'in') zoomBy(1.2);
            else if (zoom.dataset.zoom === 'out') zoomBy(1 / 1.2);
            else fitView();
            return;
        }
        if (ev.target.closest('[data-clear-terrain]')) {
            var ed = editor();
            htmxPost(ed.dataset.clearTerrainUrl, {});
            return;
        }
        var tok = ev.target.closest('.tt-token');
        if (tok && editor().contains(tok)) selectToken(tok);
    });
    document.body.addEventListener('change', function (ev) {
        if (!editor()) return;
        if (ev.target.matches('[data-layer-visible], [data-layer-lock]')) updateLayerClasses();
        if (ev.target.id === 'tt-rotation' && state.selectedToken) {
            var v = parseInt(ev.target.value, 10) || 0;
            applyTokenRotation(state.selectedToken, v);
            htmxPost(state.selectedToken.dataset.editUrl, { Rotation: v });
        }
    });
    document.body.addEventListener('input', function (ev) {
        if (!editor()) return;
        if (ev.target.id === 'tt-palette-search') filterPalette(ev.target.value);
        if (ev.target.id === 'tt-rotation' && state.selectedToken) {
            applyTokenRotation(state.selectedToken, parseInt(ev.target.value, 10) || 0);
        }
    });
    document.body.addEventListener('dragstart', function (ev) {
        var tile = ev.target.closest('.tt-ptile');
        if (!tile) return;
        selectPalette(tile);
        ev.dataTransfer.setData('application/json', JSON.stringify(state.selectedTile));
    });
    document.body.addEventListener('dragover', function (ev) {
        if (ev.target.closest('#tt-stage')) ev.preventDefault();
    });
    document.body.addEventListener('drop', function (ev) {
        var st = ev.target.closest('#tt-stage');
        if (!st || !editor()) return;
        ev.preventDefault();
        var data = state.selectedTile;
        try {
            data = JSON.parse(ev.dataTransfer.getData('application/json')) || data;
        } catch (_) {}
        if (!data) return;
        var p = screenToWorld(ev);
        if (data.spriteKind === 'token') postPlace(p, data);
        else {
            state.selectedTile = data;
            var c = cellAt(p);
            postPaint([c.q + ',' + c.r]);
        }
    });
    document.body.addEventListener('pointerdown', function (ev) {
        var ed = editor();
        var st = stage();
        if (!ed || !st || !st.contains(ev.target)) return;
        var tok = ev.target.closest('.tt-token');
        if (tok && state.tool === 'select') { startTokenMove(ev, tok); return; }
        if (state.tool === 'paint') { startPaint(ev); return; }
        if (state.tool === 'measure') { startMeasure(ev); return; }
        if (state.tool === 'place' && state.selectedTile && state.selectedTile.spriteKind === 'token') {
            ev.preventDefault();
            postPlace(screenToWorld(ev), state.selectedTile);
            return;
        }
        if (ev.button === 1 || ev.shiftKey || !tok) startPan(ev);
    });
    document.body.addEventListener('pointermove', function (ev) {
        if (!editor() || !stage() || !stage().contains(ev.target)) return;
        updateCoord(cellAt(screenToWorld(ev)));
    });
    document.body.addEventListener('wheel', function (ev) {
        if (!editor() || !ev.target.closest('#tt-stage')) return;
        ev.preventDefault();
        zoomBy(ev.deltaY < 0 ? 1.12 : 1 / 1.12, ev);
    }, { passive: false });

    function init() {
        if (!editor()) return;
        resizeOverlay();
        setTool(state.tool);
        setPaletteTab(state.paletteTab);
        updateLayerClasses();
        applyTransform();
        if (!state._fitted) {
            state._fitted = true;
            fitView();
        }
    }
    window.addEventListener('resize', resizeOverlay);
    document.body.addEventListener('htmx:afterSwap', function (ev) {
        if (ev.target && ev.target.id === 'tt-editor') init();
    });
    if (document.readyState !== 'loading') init();
    else document.addEventListener('DOMContentLoaded', init);
})();
