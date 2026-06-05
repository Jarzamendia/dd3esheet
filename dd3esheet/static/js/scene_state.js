// scene_state.js — estado da cena + undo/redo. window.SceneState.
// Terreno: Map<"q,r", terrainId>; névoa: Set<"q,r">; tokens: array de objetos.
(function (global) {
  const MAX_UNDO = 80;

  function fromJSON(data) {
    data = data || {};
    const terrain = new Map();   // hexKey -> assetId (tile MAP_TILE)
    (data.terrain || []).forEach(c => terrain.set(Hex.key(c.q, c.r), c.assetId));
    const fog = new Set((data.fog || []).map(c => Hex.key(c.q, c.r)));
    const tokens = (data.tokens || []).map(t => Object.assign({}, t));
    return {
      name: data.name || '',
      grid: Object.assign({ size: 64, cols: 30, rows: 22, showGrid: true }, data.grid || {}),
      terrain, fog, tokens,
      background: data.background || '',
    };
  }

  function snapshot(s) {
    return {
      terrain: new Map(s.terrain),
      fog: new Set(s.fog),
      tokens: s.tokens.map(t => Object.assign({}, t)),
    };
  }

  function create(data, onChange) {
    const s = fromJSON(data);
    const undo = [], redo = [];
    onChange = onChange || function () {};

    function pushUndo() {
      undo.push(snapshot(s));
      if (undo.length > MAX_UNDO) undo.shift();
      redo.length = 0;
    }
    function restore(snap) {
      s.terrain = new Map(snap.terrain);
      s.fog = new Set(snap.fog);
      s.tokens = snap.tokens.map(t => Object.assign({}, t));
    }
    return {
      s,
      pushUndo,
      undo() { if (!undo.length) return false; redo.push(snapshot(s)); restore(undo.pop()); onChange('undo'); return true; },
      redo() { if (!redo.length) return false; undo.push(snapshot(s)); restore(redo.pop()); onChange('redo'); return true; },
      canUndo: () => undo.length > 0,
      canRedo: () => redo.length > 0,
      tokenById(id) { return s.tokens.find(t => (t.id != null && t.id === id) || t.tempId === id) || null; },
      toPayload() {
        return {
          name: s.name,
          grid: { cols: s.grid.cols, rows: s.grid.rows, showGrid: s.grid.showGrid },
          terrain: [...s.terrain].map(([k, v]) => { const [q, r] = k.split(',').map(Number); return { q, r, assetId: v }; }),
          fog: [...s.fog].map(k => { const [q, r] = k.split(',').map(Number); return { q, r }; }),
          tokens: s.tokens.map(t => ({
            id: t.id, tempId: t.tempId, assetId: t.assetId, name: t.name, kind: t.kind,
            faction: t.faction, q: t.q, r: t.r, hp: t.hp, maxHp: t.maxHp, size: t.size,
            conditions: t.conditions, rotation: t.rotation, hidden: t.hidden, movable: t.movable,
          })),
        };
      },
    };
  }

  global.SceneState = { create, fromJSON, snapshot };
})(window);
