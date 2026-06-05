// hex.js — espelho de tabletop/calculations.py (pointy-top axial).
// Exposto em window.Hex para os outros scripts da mesa.
(function (global) {
  const SQRT3 = Math.sqrt(3);

  function cubeRound(q, r) {
    let x = q, z = r, y = -q - r;
    let rx = Math.round(x), ry = Math.round(y), rz = Math.round(z);
    const dx = Math.abs(rx - x), dy = Math.abs(ry - y), dz = Math.abs(rz - z);
    if (dx > dy && dx > dz) rx = -ry - rz;
    else if (dy > dz) ry = -rx - rz;
    else rz = -rx - ry;
    return [rx, rz];
  }
  function axialToPixel(q, r, size) {
    const radius = size / SQRT3;
    return [Math.round(SQRT3 * radius * (q + r / 2)), Math.round(1.5 * radius * r)];
  }
  function pixelToAxial(x, y, size) {
    const radius = size / SQRT3;
    const q = (SQRT3 / 3 * x - 1 / 3 * y) / radius;
    const r = (2 / 3 * y) / radius;
    return cubeRound(q, r);
  }
  function distance(q1, r1, q2, r2) {
    const dq = q1 - q2, dr = r1 - r2;
    return (Math.abs(dq) + Math.abs(dr) + Math.abs(dq + dr)) / 2;
  }
  function disk(q, r, radius) {
    const out = [];
    for (let dq = -radius; dq <= radius; dq++) {
      const lo = Math.max(-radius, -dq - radius);
      const hi = Math.min(radius, -dq + radius);
      for (let dr = lo; dr <= hi; dr++) out.push([q + dq, r + dr]);
    }
    return out;
  }
  function line(q1, r1, q2, r2) {
    const n = distance(q1, r1, q2, r2);
    if (n === 0) return [[q1, r1]];
    const out = [], seen = new Set();
    for (let i = 0; i <= n; i++) {
      const t = i / n;
      const [rq, rr] = cubeRound(q1 + (q2 - q1) * t, r1 + (r2 - r1) * t);
      const key = rq + ',' + rr;
      if (!seen.has(key)) { seen.add(key); out.push([rq, rr]); }
    }
    return out;
  }
  // corners de um hex pointy-top (em px de mundo) para desenho no canvas.
  function corners(cx, cy, size) {
    const radius = size / SQRT3;
    const pts = [];
    for (let i = 0; i < 6; i++) {
      const angle = Math.PI / 180 * (60 * i - 90);
      pts.push([cx + radius * Math.cos(angle), cy + radius * Math.sin(angle)]);
    }
    return pts;
  }
  global.Hex = { SQRT3, cubeRound, axialToPixel, pixelToAxial, distance, disk, line, corners, key: (q, r) => q + ',' + r };
})(window);
