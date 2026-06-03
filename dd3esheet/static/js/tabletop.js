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

    function snap(x, y, mode, size) {
        if (mode !== 'square' || !size) return [Math.round(x), Math.round(y)];
        return [Math.floor(x / size) * size + (size >> 1), Math.floor(y / size) * size + (size >> 1)];
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
})();
