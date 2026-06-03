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
        return [ev.clientX - r.left, ev.clientY - r.top];
    }

    // Enquanto arrasta/desenha, ignora o swap do polling para não reverter a peça.
    document.body.addEventListener('htmx:beforeSwap', function (evt) {
        if (dragging && evt.target && evt.target.id === 'tt-live') {
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

    document.body.addEventListener('pointerdown', function (e) {
        if (fogMode) { startFog(e); return; }
        startTokenDrag(e);
    });

    function startTokenDrag(e) {
        var tok = e.target.closest('.tt-token[data-movable="1"]');
        if (!tok) return;
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
    document.body.addEventListener('htmx:afterSwap', drawAllHexGrids);
    if (document.readyState !== 'loading') drawAllHexGrids();
    else document.addEventListener('DOMContentLoaded', drawAllHexGrids);
})();
