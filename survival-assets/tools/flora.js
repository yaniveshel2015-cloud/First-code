// Plant helpers shared by props + backgrounds
const { OL, SW, P, C, E, L, G, limb, blob, shade, qpt } = require('./common');

const qd = (p0, p1, p2, t) => [2 * (1 - t) * (p1[0] - p0[0]) + 2 * t * (p2[0] - p1[0]), 2 * (1 - t) * (p1[1] - p0[1]) + 2 * t * (p2[1] - p1[1])];
const f1 = (n) => n.toFixed(1);

// Palm frond / long leaf along a quadratic centreline.  notch 0 = smooth leaf
function frond(base, ctrl, tip, width, col, o = {}) {
  const N = o.n ?? 26, notch = o.notch ?? 0.5, peak = o.peak ?? 0.35;
  const left = [], right = [];
  for (let i = 0; i <= N; i++) {
    const t = i / N, p = qpt(base, ctrl, tip, t), d = qd(base, ctrl, tip, t);
    const len = Math.hypot(d[0], d[1]) || 1, n = [-d[1] / len, d[0] / len];
    let w = width * Math.pow(t < peak ? t / peak : 1 - (t - peak) / (1 - peak), 0.8);
    if (t < peak) w = Math.max(w, width * 0.12);
    if (i % 2 && i < N) w *= 1 - notch;
    left.push([p[0] + n[0] * w, p[1] + n[1] * w]);
    right.push([p[0] - n[0] * w, p[1] - n[1] * w]);
  }
  const pts = left.concat(right.reverse());
  const d = 'M' + pts.map((q) => f1(q[0]) + ',' + f1(q[1])).join(' L') + ' Z';
  let s = P(d, col, { sw: o.sw ?? SW });
  s += L(`M${base[0]},${base[1]} Q${ctrl[0]},${ctrl[1]} ${tip[0]},${tip[1]}`, o.rib ?? shade(col, -0.3), o.ribW ?? 4);
  if (o.veins) {
    for (let i = 2; i < 12; i++) {
      const t = i / 13, p = qpt(base, ctrl, tip, t), dd = qd(base, ctrl, tip, t);
      const len = Math.hypot(dd[0], dd[1]), u = [dd[0] / len, dd[1] / len], n = [-u[1], u[0]];
      const w = width * Math.pow(t < peak ? t / peak : 1 - (t - peak) / (1 - peak), 0.8) * 0.85;
      [1, -1].forEach((sg) => { s += L(`M${f1(p[0])},${f1(p[1])} L${f1(p[0] + n[0] * w * sg + u[0] * w * 0.5)},${f1(p[1] + n[1] * w * sg + u[1] * w * 0.5)}`, shade(col, -0.22), 3); });
    }
  }
  return s;
}

// simple almond leaf at x,y pointing at angle (deg)
const leaf = (x, y, len, ang, col, o = {}) => G(
  P(`M0,0 Q${len * 0.45},${-len * 0.38} ${len},0 Q${len * 0.45},${len * 0.38} 0,0 Z`, col, { sw: o.sw ?? 4 }) + L(`M2,0 L${len * 0.8},0`, shade(col, -0.3), 3),
  { transform: `translate(${f1(x)},${f1(y)}) rotate(${f1(ang)})` });

// palm tree: trunk from bottom b to top t (quadratic with control c)
function palm(b, c, t, o = {}) {
  const segs = o.segs ?? 11, w0 = o.w0 ?? 46, w1 = o.w1 ?? 30, col = o.trunk ?? '#B07A45';
  let s = '';
  for (let i = 0; i < segs; i++) {
    const ta = i / segs, tb = (i + 1) / segs;
    const pa = qpt(b, c, t, ta), pb = qpt(b, c, t, Math.min(1, tb + 0.02));
    const da = qd(b, c, t, ta), la = Math.hypot(da[0], da[1]), na = [-da[1] / la, da[0] / la];
    const wa = (w0 + (w1 - w0) * ta) / 2, wb = (w0 + (w1 - w0) * tb) / 2 * 1.18;
    s += P(`M${f1(pa[0] + na[0] * wa)},${f1(pa[1] + na[1] * wa)} L${f1(pb[0] + na[0] * wb)},${f1(pb[1] + na[1] * wb)} L${f1(pb[0] - na[0] * wb)},${f1(pb[1] - na[1] * wb)} L${f1(pa[0] - na[0] * wa)},${f1(pa[1] - na[1] * wa)} Z`, i % 2 ? col : shade(col, -0.1), { sw: o.sw ?? 4 });
  }
  const [tx, ty] = t, sc = o.frondScale ?? 1, fc = o.leaf ?? '#3FA34D';
  const fr = [[-170, 40, -120, -70], [-150, 120, -100, 10], [-70, 170, -60, 70], [170, 40, 120, -70], [150, 120, 100, 10], [70, 170, 60, 70], [10, -150, -30, -110], [-110, -110, -90, -100], [120, -100, 80, -110]];
  const order = [6, 7, 8, 0, 3, 1, 4, 2, 5];
  order.forEach((k, j) => {
    const [dx, dy, cx, cy] = fr[k];
    s += frond([tx, ty], [tx + cx * sc, ty + cy * sc], [tx + dx * 1.45 * sc, ty + dy * 1.25 * sc], 34 * sc, j < 3 ? shade(fc, -0.15) : fc, { sw: o.sw ?? 4 });
  });
  if (o.coconuts !== false) s += C(tx - 18 * sc, ty + 18 * sc, 17 * sc, '#6B4220', { sw: 4 }) + C(tx + 16 * sc, ty + 20 * sc, 17 * sc, '#5A381C', { sw: 4 }) + C(tx, ty + 34 * sc, 17 * sc, '#6B4220', { sw: 4 });
  return s;
}

const bush = (x, y, r, col, o = {}) => blob([[x - r * 0.9, y, r * 0.75], [x, y - r * 0.35, r], [x + r * 0.9, y, r * 0.8], [x - r * 0.35, y + r * 0.15, r * 0.8], [x + r * 0.4, y + r * 0.15, r * 0.8]], col, o)
  + C(x - r * 0.25, y - r * 0.6, r * 0.18, shade(col, 0.2), { stroke: 'none' });

const grass = (x, y, h, col) => P(`M${x - 22},${y} Q${x - 18},${y - h * 0.6} ${x - 30},${y - h} Q${x - 8},${y - h * 0.6} ${x - 4},${y - h * 0.3} Q${x},${y - h * 0.9} ${x + 6},${y - h * 1.15} Q${x + 8},${y - h * 0.6} ${x + 8},${y - h * 0.4} Q${x + 18},${y - h * 0.8} ${x + 32},${y - h * 0.9} Q${x + 18},${y - h * 0.5} ${x + 22},${y} Z`, col, { sw: 4 });

const hibiscus = (x, y, r, col = '#FF4F79') => {
  let s = '';
  for (let i = 0; i < 5; i++) {
    const a = (i * 72 - 90) * Math.PI / 180, px = x + Math.cos(a) * r * 0.55, py = y + Math.sin(a) * r * 0.55;
    s += G(P(`M0,${r * 0.5} C${-r * 0.75},${r * 0.2} ${-r * 0.6},${-r * 0.55} 0,${-r * 0.45} C${r * 0.6},${-r * 0.55} ${r * 0.75},${r * 0.2} 0,${r * 0.5} Z`, col, { sw: Math.max(3, r * 0.06) }), { transform: `translate(${f1(px)},${f1(py)}) rotate(${i * 72})` });
  }
  s += C(x, y, r * 0.3, shade(col, -0.35), { stroke: 'none' });
  s += limb(`M${x},${y} L${x + r * 0.45},${y - r * 0.55}`, '#FFE14D', r * 0.07, { sw: 3 }) + C(x + r * 0.45, y - r * 0.55, r * 0.09, '#FFC400', { sw: 3 });
  return s;
};

module.exports = { frond, leaf, palm, bush, grass, hibiscus };
