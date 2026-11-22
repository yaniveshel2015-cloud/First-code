// Speech / thought bubbles (blank, transparent PNG). Each comes with the tail on the left and on the right.
const { OL, svgDoc, P, C, E, R, L, G, shade, rng } = require('./common');
const W = 800, H = 580, SWB = 7;

// union outline: thick dark strokes first, fills on top
const union = (ds, fill, ol = OL, sw = SWB) => ds.map((d) => P(d, ol, { stroke: ol, sw: sw * 2 })).join('') + ds.map((d) => P(d, fill, { stroke: 'none' })).join('');
const ept = (cx, cy, rx, ry, deg) => [cx + rx * Math.cos(deg * Math.PI / 180), cy + ry * Math.sin(deg * Math.PI / 180)].map((n) => n.toFixed(1));
const ovalPath = () => { const [a, b] = ept(400, 240, 350, 195, 108), [c, d] = ept(400, 240, 350, 195, 128); return `M${a},${b} A350,195 0 1,0 ${c},${d} Q170,480 110,548 Q240,510 ${a},${b} Z`; };
const shadow = (inner) => G(inner, { transform: 'translate(10,12)', opacity: 0.18 });

function oval(fill, ol = OL, dashed = false) {
  const d = ovalPath();
  return shadow(P(d, '#000', { stroke: 'none' })) + P(d, fill, { stroke: ol, sw: SWB, 'stroke-dasharray': dashed ? '28 18' : undefined })
    + P('M150,170 Q190,100 280,78', 'none', { stroke: '#fff', sw: 12, opacity: dashed ? 0 : 0.7 });
}
function rounded(fill, extra = '') {
  const ds = ['M40,40 L760,40 Q790,40 790,70 L790,390 Q790,420 760,420 L40,420 Q10,420 10,390 L10,70 Q10,40 40,40 Z', 'M170,400 L110,550 L300,410 Z'];
  return shadow(ds.map((d) => P(d, '#000', { stroke: 'none' })).join('')) + union(ds, fill) + extra;
}
function thought() {
  const cs = [];
  for (let i = 0; i < 14; i++) { const a = i / 14 * Math.PI * 2; cs.push([400 + Math.cos(a) * 300, 250 + Math.sin(a) * 138, 74 + (i % 3) * 9]); }
  let s = shadow(cs.map(([x, y, r]) => C(x, y, r, '#000', { stroke: 'none' })).join('') + E(400, 250, 310, 150, '#000', { stroke: 'none' }));
  s += cs.map(([x, y, r]) => C(x, y, r + SWB, OL, { stroke: 'none' })).join('') + cs.map(([x, y, r]) => C(x, y, r, '#fff', { stroke: 'none' })).join('') + E(400, 250, 320, 158, '#fff', { stroke: 'none' });
  s += C(175, 488, 30, '#fff', { sw: SWB }) + C(115, 532, 20, '#fff', { sw: SWB }) + C(74, 562, 12, '#fff', { sw: SWB });
  return s;
}
function shout(fill) {
  const r = rng(3); let d = '';
  const N = 22;
  for (let i = 0; i < N; i++) { const a = i / N * Math.PI * 2, rr = i % 2 ? 0.82 : 1 + r() * 0.12; d += (i ? 'L' : 'M') + (400 + Math.cos(a) * 370 * rr).toFixed(1) + ',' + (235 + Math.sin(a) * 215 * rr).toFixed(1) + ' '; }
  d += 'Z';
  const tail = 'M250,330 L70,560 L360,360 Z';
  return shadow(P(d, '#000', { stroke: 'none' }) + P(tail, '#000', { stroke: 'none' })) + union([d, tail], fill);
}
function wood() {
  const grain = L('M60,130 C260,110 520,150 740,120 M60,230 C300,250 520,210 740,240 M60,330 C260,310 520,350 740,320', shade('#C68B4E', -0.2), 4)
    + C(60, 70, 8, '#6B4220', { sw: 3 }) + C(740, 70, 8, '#6B4220', { sw: 3 }) + C(60, 390, 8, '#6B4220', { sw: 3 }) + C(740, 390, 8, '#6B4220', { sw: 3 });
  return rounded('#C68B4E', grain);
}
function caption() {
  let s = shadow(R(20, 120, 760, 300, 14, '#000', { stroke: 'none' })) + R(20, 120, 760, 300, 14, '#FFF6DD', { sw: SWB }) + R(40, 140, 720, 260, 8, 'none', { sw: 3, stroke: '#C4A26A' });
  let z = 'M40,140'; for (let x = 40; x < 760; x += 24) z += ` L${x + 12},${x / 24 % 2 ? 128 : 152} L${x + 24},140`;
  s += R(20, 120, 760, 40, 14, '#FF7A1A', { sw: SWB }) + L('M50,140 ' + Array.from({ length: 29 }, (_, i) => `L${62 + i * 24},${i % 2 ? 132 : 148}`).join(' '), '#fff', 4, { opacity: 0.85 });
  return s;
}

module.exports = () => {
  const D = '03-speech-bubbles';
  const list = [
    ['speech-oval', 'בועת דיבור אובלית', oval('#FFFFFF')],
    ['speech-rounded', 'בועת דיבור מלבנית', rounded('#FFFFFF')],
    ['thought-cloud', 'בועת מחשבה (ענן)', thought()],
    ['shout', 'בועת צעקה', shout('#FFF59D')],
    ['whisper', 'בועת לחישה (קו מקווקו)', oval('#FFFFFF', OL, true)],
    ['parchment', 'בועת קלף', oval('#F7E3B5', '#6B4220')],
    ['wood', 'בועת עץ', wood()],
    ['orange-tribe', 'בועה כתומה (שבט כתום)', oval('#FFD8B0')],
    ['blue-tribe', 'בועה כחולה (שבט כחול)', oval('#CDE6FF')],
  ];
  const out = [];
  for (const [name, he, body] of list) {
    out.push({ dir: D, name: `${name}-tail-left`, he: `${he} – זנב שמאלה`, w: W, h: H, scale: 1, svg: svgDoc(W, H, body) });
    out.push({ dir: D, name: `${name}-tail-right`, he: `${he} – זנב ימינה`, w: W, h: H, scale: 1, svg: svgDoc(W, H, G(body, { transform: `translate(${W},0) scale(-1,1)` })) });
  }
  out.push({ dir: D, name: 'caption-box', he: 'תיבת כיתוב / קריין', w: W, h: H, scale: 1, svg: svgDoc(W, H, caption()) });
  return out;
};
