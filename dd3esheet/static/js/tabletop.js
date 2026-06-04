/* Mesa virtual — arrastar tokens e desenhar névoa (vanilla, sem framework).
 *
 * Carregado depois do htmx (main.html). Usa htmx.ajax para persistir e deixa o
 * servidor devolver o canvas autoritativo. Tudo é delegado em document.body para
 * sobreviver às trocas de #tt-live / #tt-editor feitas pelo HTMX.
 */
(function () {
    'use strict';

    var dragging = false;   // arrasto de token OU desenho de névoa em andamento
    var fogMode = false;    // modo "desenhar névoa" (botão do editor)
    var panning = false;    // arrasto do fundo (pan) na cena
    var fitted = false;     // já enquadrou a cena uma vez no carregamento
    var view = { scale: 1, panX: 0, panY: 0 };  // zoom/pan da cena (só cliente, por espectador)

    var SQ3 = Math.sqrt(3);
    function cubeRound(q, r) {
        var x = q, z = r, y = -x - z;
        var rx = Math.round(x), ry = Math.round(y), rz = Math.round(z);
        var dx = Math.abs(rx - x), dy = Math.abs(ry - y), dz = Math.abs(rz - z);
        if (dx > dy && dx > dz) rx = -ry - rz; else if (dy > dz) ry = -rx - rz; else rz = -rx - ry;
        return [rx, rz];
    }
    function snap(x, y, mode, size) {
        if (mode !== 'hex' || !size) return [Math.round(x), Math.round(y)];
        var R = size / SQ3;
        var a = cubeRound((SQ3 / 3 * x - 1 / 3 * y) / R, (2 / 3 * y) / R);
        var cx = SQ3 * R * (a[0] + a[1] / 2), cy = 1.5 * R * a[1];
        return [Math.round(cx), Math.round(cy)];
    }

    function canvasPoint(canvas, ev) {
        var r = canvas.getBoundingClientRect();
        var sc = view.scale || 1;   // o canvas da cena pode estar escalado pelo zoom
        return [(ev.clientX - r.left) / sc, (ev.clientY - r.top) / sc];
    }

    // --- zoom/pan da cena ao vivo (o editor usa tabletop_editor.js) -------------
    function liveStage() { return document.getElementById('tt-live'); }
    function liveCanvas() {
        var s = liveStage();
        var c = s ? s.querySelector('.tt-canvas') : null;
        return (c && !c.classList.contains('tt-canvas--empty')) ? c : null;
    }
    function applyView() {
        var c = liveCanvas();
        if (c) {
            c.style.transformOrigin = '0 0';
            c.style.transform = 'translate(' + view.panX + 'px,' + view.panY + 'px) scale(' + view.scale + ')';
        }
        var pct = document.getElementById('tt-zoom-pct');
        if (pct) pct.textContent = Math.round(view.scale * 100) + '%';
    }
    function stageToWorld(ev) {
        var r = liveStage().getBoundingClientRect();
        return { x: (ev.clientX - r.left - view.panX) / view.scale, y: (ev.clientY - r.top - view.panY) / view.scale };
    }
    function zoomBy(mult, ev) {
        var s = liveStage();
        if (!s) return;
        var before = ev ? stageToWorld(ev) : null;
        view.scale = Math.max(0.2, Math.min(3, view.scale * mult));
        if (before) {
            var r = s.getBoundingClientRect();
            view.panX = ev.clientX - r.left - before.x * view.scale;
            view.panY = ev.clientY - r.top - before.y * view.scale;
        }
        applyView();
    }
    function fitView() {
        var s = liveStage(), c = liveCanvas();
        if (!s || !c) return;
        var w = parseInt(c.style.width, 10) || c.offsetWidth || 1;
        var h = parseInt(c.style.height, 10) || c.offsetHeight || 1;
        view.scale = Math.max(0.2, Math.min(3, Math.min((s.clientWidth - 24) / w, (s.clientHeight - 24) / h)));
        view.panX = Math.round((s.clientWidth - w * view.scale) / 2);
        view.panY = Math.round((s.clientHeight - h * view.scale) / 2);
        applyView();
    }
    function startPan(e) {
        var s = liveStage();
        if (!s) return;
        e.preventDefault();
        panning = true;
        s.classList.add('panning');
        var sx = e.clientX, sy = e.clientY, px = view.panX, py = view.panY;
        function move(ev) {
            view.panX = px + (ev.clientX - sx);
            view.panY = py + (ev.clientY - sy);
            applyView();
        }
        function up() {
            document.removeEventListener('pointermove', move);
            document.removeEventListener('pointerup', up);
            panning = false;
            s.classList.remove('panning');
        }
        document.addEventListener('pointermove', move);
        document.addEventListener('pointerup', up);
    }

    // Enquanto arrasta/desenha, ignora o swap do polling para não reverter a peça.
    document.body.addEventListener('htmx:beforeSwap', function (evt) {
        if ((dragging || panning) && evt.target && evt.target.id === 'tt-live') {
            evt.detail.shouldSwap = false;
        }
    });

    // Liga/desliga o modo de névoa.
    document.body.addEventListener('click', function (e) {
        var btn = e.target.closest('[data-fog-toggle]');
        if (!btn) return;
        fogMode = !fogMode;
        btn.classList.toggle('is-active', fogMode);
        document.querySelectorAll('.tt-canvas[data-can-edit="1"]').forEach(function (c) {
            c.classList.toggle('tt-canvas--fogging', fogMode);
        });
    });

    // Botões de zoom da cena (− / + / Ajustar), convenção data-zoom como no editor.
    document.body.addEventListener('click', function (e) {
        var z = e.target.closest('[data-zoom]');
        if (!z || !liveStage()) return;
        if (z.dataset.zoom === 'in') zoomBy(1.2);
        else if (z.dataset.zoom === 'out') zoomBy(1 / 1.2);
        else fitView();
    });

    // Roda do mouse = zoom no ponto do cursor.
    document.body.addEventListener('wheel', function (e) {
        var s = liveStage();
        if (!s || !s.contains(e.target)) return;
        e.preventDefault();
        zoomBy(e.deltaY < 0 ? 1.12 : 1 / 1.12, e);
    }, { passive: false });

    document.body.addEventListener('pointerdown', function (e) {
        if (fogMode) { startFog(e); return; }
        var s = liveStage();
        if (!s || !s.contains(e.target)) return;            // só na cena ao vivo
        if (e.target.closest('.tt-token[data-movable="1"]')) { startTokenDrag(e); return; }
        startPan(e);                                          // arrastar o fundo = pan
    });

    function startTokenDrag(e) {
        var tok = e.target.closest('.tt-token[data-movable="1"]');
        if (!tok) return;
        if (tok.closest('[data-rich-editor="1"]')) return;
        var canvas = tok.closest('.tt-canvas');
        if (!canvas) return;
        e.preventDefault();
        var url = tok.dataset.moveUrl;
        var mode = canvas.dataset.gridMode;
        var size = parseInt(canvas.dataset.gridSize, 10) || 0;
        dragging = true;
        tok.classList.add('is-dragging');
        try { tok.setPointerCapture(e.pointerId); } catch (_) {}

        function move(ev) {
            var p = canvasPoint(canvas, ev);
            tok.style.left = p[0] + 'px';
            tok.style.top = p[1] + 'px';
        }
        function up(ev) {
            tok.removeEventListener('pointermove', move);
            tok.removeEventListener('pointerup', up);
            var p = canvasPoint(canvas, ev);
            var s = snap(p[0], p[1], mode, size);
            tok.style.left = s[0] + 'px';
            tok.style.top = s[1] + 'px';
            tok.classList.remove('is-dragging');
            dragging = false;
            if (url && window.htmx) {
                window.htmx.ajax('POST', url, { target: '#tt-live', swap: 'innerHTML', values: { X: s[0], Y: s[1] } });
            }
        }
        tok.addEventListener('pointermove', move);
        tok.addEventListener('pointerup', up);
    }

    function startFog(e) {
        var canvas = e.target.closest('.tt-canvas[data-can-edit="1"]');
        if (!canvas || !canvas.dataset.fogUrl) return;
        e.preventDefault();
        var start = canvasPoint(canvas, e);
        var box = document.createElement('div');
        box.className = 'tt-fog--drawing';
        box.style.left = start[0] + 'px';
        box.style.top = start[1] + 'px';
        canvas.appendChild(box);
        dragging = true;

        function move(ev) {
            var p = canvasPoint(canvas, ev);
            box.style.left = Math.min(start[0], p[0]) + 'px';
            box.style.top = Math.min(start[1], p[1]) + 'px';
            box.style.width = Math.abs(p[0] - start[0]) + 'px';
            box.style.height = Math.abs(p[1] - start[1]) + 'px';
        }
        function up(ev) {
            document.removeEventListener('pointermove', move);
            document.removeEventListener('pointerup', up);
            var p = canvasPoint(canvas, ev);
            var x = Math.round(Math.min(start[0], p[0]));
            var y = Math.round(Math.min(start[1], p[1]));
            var w = Math.round(Math.abs(p[0] - start[0]));
            var h = Math.round(Math.abs(p[1] - start[1]));
            box.remove();
            dragging = false;
            if (w >= 6 && h >= 6 && window.htmx) {
                window.htmx.ajax('POST', canvas.dataset.fogUrl, {
                    target: '#tt-live', swap: 'innerHTML',
                    values: { X: x, Y: y, Width: w, Height: h }
                });
            }
        }
        document.addEventListener('pointermove', move);
        document.addEventListener('pointerup', up);
    }
    function drawHexGrid(cv) {
        var size = parseInt(cv.parentElement.dataset.gridSize, 10) || 64;
        var R = size / SQ3, w = cv.width, h = cv.height;
        var g = cv.getContext('2d');
        g.clearRect(0, 0, w, h);
        g.strokeStyle = 'rgba(43,38,34,0.28)';
        g.lineWidth = 1;
        var rTop = -1, rBot = Math.ceil(h / (1.5 * R)) + 1;
        for (var r = rTop; r <= rBot; r++) {
            var qLeft = Math.floor((-(R * SQ3)) / (R * SQ3) - r / 2) - 1;
            var qRight = Math.ceil((w / (R * SQ3)) - r / 2) + 1;
            for (var q = qLeft; q <= qRight; q++) {
                var cx = SQ3 * R * (q + r / 2), cy = 1.5 * R * r;
                g.beginPath();
                for (var i = 0; i < 6; i++) {
                    var a = Math.PI / 180 * (60 * i - 30);
                    var px = cx + R * Math.cos(a), py = cy + R * Math.sin(a);
                    if (i === 0) g.moveTo(px, py); else g.lineTo(px, py);
                }
                g.closePath();
                g.stroke();
            }
        }
    }
    function drawAllHexGrids() {
        document.querySelectorAll('canvas[data-hexgrid]').forEach(drawHexGrid);
    }
    // Após cada swap (polling) redesenha a grade e reaplica o zoom/pan da cena;
    // na primeira vez que há cena, enquadra-a (fit). O editor não tem #tt-live.
    function refreshScene() {
        drawAllHexGrids();
        if (!liveCanvas()) return;
        if (!fitted) { fitted = true; fitView(); } else { applyView(); }
    }
    document.body.addEventListener('htmx:afterSwap', refreshScene);
    if (document.readyState !== 'loading') refreshScene();
    else document.addEventListener('DOMContentLoaded', refreshScene);
})();
