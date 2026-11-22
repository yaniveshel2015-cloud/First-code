// Shared helpers + palette for the survival-island asset pack.
const OL = '#2B1B10'; // cartoon outline colour
const SW = 5; // default outline width

const svgDoc = (w, h, body, defs = '') =>
  `<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 ${w} ${h}" width="${w}" height="${h}">` +
  (defs ? `<defs>${defs}</defs>` : '') + body + `</svg>`;

const attrs = (o) => Object.entries(o)
  .filter(([, v]) => v !== undefined && v !== null && v !== false)
  .map(([k, v]) => `${k}="${v}"`).join(' ');
const tag = (t, a, inner) => inner === undefined ? `<${t} ${attrs(a)}/>` : `<${t} ${attrs(a)}>${inner}</${t}>`;

const base = (o) => {
  const { sw = SW, stroke = OL, ...rest } = o;
  return { stroke: stroke, 'stroke-width': stroke === 'none' ? undefined : sw, 'stroke-linejoin': 'round', 'stroke-linecap': 'round', ...rest };
};
const P = (d, fill, o = {}) => tag('path', { d, fill, ...base(o) });
const C = (cx, cy, r, fill, o = {}) => tag('circle', { cx, cy, r, fill, ...base(o) });
const E = (cx, cy, rx, ry, fill, o = {}) => tag('ellipse', { cx, cy, rx, ry, fill, ...base(o) });
const R = (x, y, w, h, rx, fill, o = {}) => tag('rect', { x, y, width: w, height: h, rx, fill, ...base(o) });
const L = (d, stroke, w, o = {}) => tag('path', { d, fill: 'none', stroke, 'stroke-width': w, 'stroke-linecap': 'round', 'stroke-linejoin': 'round', ...o });
const G = (inner, o = {}) => tag('g', o, inner);

// A thick stroked path with a cartoon outline (limbs, poles, ropes...)
const limb = (d, color, w, o = {}) => {
  const ol = o.ol ?? OL, sw = o.sw ?? SW, cap = o.cap ?? 'round';
  return L(d, ol, w + 2 * sw, { 'stroke-linecap': cap }) + L(d, color, w, { 'stroke-linecap': cap });
};

// Several circles merged into one outlined blob (clouds, curls, bushes)
const blob = (circles, fill, o = {}) => {
  const sw = o.sw ?? SW, ol = o.ol ?? OL;
  return circles.map(([x, y, r]) => C(x, y, r + sw / 2, ol, { stroke: 'none' })).join('') +
    circles.map(([x, y, r]) => C(x, y, r - sw / 2, fill, { stroke: 'none' })).join('');
};

// colour utils
const hex2rgb = (h) => { const n = parseInt(h.slice(1), 16); return [(n >> 16) & 255, (n >> 8) & 255, n & 255]; };
const rgb2hex = (r, g, b) => '#' + [r, g, b].map((v) => Math.max(0, Math.min(255, Math.round(v))).toString(16).padStart(2, '0')).join('');
const shade = (h, amt) => { // amt <0 darker, >0 lighter (-1..1)
  const [r, g, b] = hex2rgb(h);
  return amt < 0 ? rgb2hex(r * (1 + amt), g * (1 + amt), b * (1 + amt)) : rgb2hex(r + (255 - r) * amt, g + (255 - g) * amt, b + (255 - b) * amt);
};

// Flame (bottom centre at cx,by, height h)
const FLAME = 'M0,-100 C8,-72 36,-60 37,-30 C38,-8 20,4 0,4 C-20,4 -38,-8 -37,-30 C-36,-50 -22,-58 -17,-76 C-9,-60 -3,-58 -4,-70 C-5,-82 -7,-90 0,-100 Z';
const flame = (cx, by, h, o = {}) => {
  const s = h / 100;
  const layer = (sc, fill, dy, stroke) => G(P(FLAME, fill, { sw: (o.sw ?? SW) / (s * sc), stroke: stroke ? OL : 'none' }),
    { transform: `translate(${cx},${by - dy}) scale(${s * sc})` });
  return layer(1, o.c1 ?? '#F2541B', 0, true) + layer(0.74, o.c2 ?? '#FF9F1C', h * 0.03) + layer(0.46, o.c3 ?? '#FFE14D', h * 0.05);
};

// 4 point sparkle
const star4 = (cx, cy, r, fill = '#FFE14D', o = {}) =>
  P(`M${cx},${cy - r} Q${cx},${cy} ${cx + r},${cy} Q${cx},${cy} ${cx},${cy + r} Q${cx},${cy} ${cx - r},${cy} Q${cx},${cy} ${cx},${cy - r} Z`, fill, { sw: o.sw ?? 4 });

// quadratic point helper
const qpt = (p0, p1, p2, t) => [
  (1 - t) * (1 - t) * p0[0] + 2 * (1 - t) * t * p1[0] + t * t * p2[0],
  (1 - t) * (1 - t) * p0[1] + 2 * (1 - t) * t * p1[1] + t * t * p2[1]];

// deterministic random
const rng = (seed) => () => { seed = (seed * 16807) % 2147483647; return (seed - 1) / 2147483646; };

module.exports = { OL, SW, svgDoc, tag, P, C, E, R, L, G, limb, blob, shade, flame, star4, qpt, rng };
