// Signs, frames, scrolls & banners for titles and text (transparent PNG)
const { OL, svgDoc, P, C, E, R, L, G, limb, shade, rng } = require('./common');
const { frond, leaf, hibiscus } = require('./flora');
const BAMBOO = '#D2A95A';
const sh = (inner, dx = 10, dy = 14) => G(inner, { transform: `translate(${dx},${dy})`, opacity: 0.2 });

function plank(x, y, w, h, col, seed) {
  const r = rng(seed); let s = R(x, y, w, h, 14, col);
  for (let k = 0; k < 3; k++) { const yy = y + h * (0.25 + k * 0.25) + (r() - 0.5) * 10; s += L(`M${x + 20},${yy} C${x + w * 0.3},${yy + (r() - 0.5) * 20} ${x + w * 0.7},${yy + (r() - 0.5) * 20} ${x + w - 20},${yy}`, shade(col, -0.18), 3.5, { opacity: 0.8 }); }
  const kx = x + 80 + r() * (w - 160); s += E(kx, y + h / 2, 22, 9, shade(col, -0.25), { stroke: 'none' });
  return s;
}
function titleSign(w, h, cols = ['#B97A45', '#C68B4E', '#A86C3A']) {
  const W = w + 80, H = h + 140, x = 40, y0 = 110, ph = h / 3;
  let s = limb(`M${x + 90},${y0 + 20} L${x + 160},0`, '#C9A66B', 10, { sw: 3 }) + limb(`M${x + w - 90},${y0 + 20} L${x + w - 160},0`, '#C9A66B', 10, { sw: 3 });
  s += sh(R(x, y0, w, h, 16, '#000', { stroke: 'none' }));
  for (let i = 0; i < 3; i++) s += plank(x, y0 + i * ph, w, ph, cols[i % cols.length], i + 3);
  s += R(x + 40, y0 - 14, 26, h + 28, 8, '#6B4220') + R(x + w - 66, y0 - 14, 26, h + 28, 8, '#6B4220');
  for (let i = 0; i < 3; i++) { s += C(x + 53, y0 + ph * (i + 0.5), 6, '#9E9E9E', { sw: 2.5 }) + C(x + w - 53, y0 + ph * (i + 0.5), 6, '#9E9E9E', { sw: 2.5 }); }
  s += C(x + 90, y0 + 20, 10, '#9E9E9E', { sw: 3 }) + C(x + w - 90, y0 + 20, 10, '#9E9E9E', { sw: 3 });
  return [W, H, s];
}
function namePlank(col) {
  let s = sh(R(20, 20, 660, 170, 22, '#000', { stroke: 'none' })) + plank(20, 20, 660, 170, col, 9) + R(36, 36, 628, 138, 14, 'none', { stroke: shade(col, -0.3), sw: 3 });
  [[50, 50], [650, 50], [50, 160], [650, 160]].forEach(([x, y]) => { s += C(x, y, 6, '#9E9E9E', { sw: 2.5 }); });
  return svgDoc(720, 220, s);
}
function bambooPole(x1, y1, x2, y2, w = 34) {
  let s = limb(`M${x1},${y1} L${x2},${y2}`, BAMBOO, w);
  const len = Math.hypot(x2 - x1, y2 - y1), ux = (x2 - x1) / len, uy = (y2 - y1) / len, nx = -uy, ny = ux;
  for (let d = 110; d < len - 60; d += 160) { const px = x1 + ux * d, py = y1 + uy * d; s += L(`M${px + nx * w / 2},${py + ny * w / 2} L${px - nx * w / 2},${py - ny * w / 2}`, '#8B6A35', 5); }
  s += L(`M${x1 + nx * w / 4 + ux * 20},${y1 + ny * w / 4 + uy * 20} L${x2 + nx * w / 4 - ux * 20},${y2 + ny * w / 4 - uy * 20}`, '#fff', 4, { opacity: 0.35 });
  return s;
}
function rope(x, y) { return G(limb('M-30,-30 L30,30', '#C9A66B', 12, { sw: 3 }) + limb('M30,-30 L-30,30', '#D9BA80', 12, { sw: 3 }) + limb('M-34,-10 L34,-10 M-34,10 L34,10', '#C9A66B', 9, { sw: 3 }), { transform: `translate(${x},${y})` }); }
function bambooFrame(w, h) {
  const m = 40, W = w + 2 * m, H = h + 2 * m;
  let s = bambooPole(m - 30, m + 20, W - m + 30, m + 20) + bambooPole(m - 30, H - m - 20, W - m + 30, H - m - 20) + bambooPole(m + 20, m - 30, m + 20, H - m + 30) + bambooPole(W - m - 20, m - 30, W - m - 20, H - m + 30);
  [[m + 20, m + 20], [W - m - 20, m + 20], [m + 20, H - m - 20], [W - m - 20, H - m - 20]].forEach(([x, y]) => { s += rope(x, y); });
  s += leaf(m + 50, m + 60, 70, 40, '#4CAF50') + leaf(m + 60, m + 40, 60, -10, '#66BB6A') + hibiscus(m + 30, m + 30, 34);
  return svgDoc(W, H, s);
}
function scrollH() {
  const W = 1600, H = 560;
  const d = 'M150,90 Q800,60 1450,90 L1450,470 Q800,440 150,470 Z';
  let s = sh(P(d, '#000', { stroke: 'none' })) + P(d, '#F3E2B8') + G(P(d, 'none', { stroke: '#D9B77A', sw: 30, opacity: 0.45 }), { 'clip-path': 'url(#sc)' });
  [[150, -1], [1450, 1]].forEach(([x, sd]) => {
    s += R(x - 45, 50, 90, 460, 45, '#E9CF98') + L(`M${x - 20},70 L${x - 20},490`, '#fff', 6, { opacity: 0.4 }) + L(`M${x + 25},70 L${x + 25},490`, '#C4A26A', 5);
    s += R(x - 25, 26, 50, 36, 10, '#8B5A2B') + R(x - 25, 498, 50, 36, 10, '#8B5A2B');
  });
  return svgDoc(W, H, s, `<clipPath id="sc"><path d="${d}"/></clipPath>`);
}
function scrollV() {
  const W = 760, H = 1040;
  const d = 'M100,130 Q380,110 660,130 L660,910 Q380,890 100,910 Z';
  let s = sh(P(d, '#000', { stroke: 'none' })) + P(d, '#F3E2B8') + G(P(d, 'none', { stroke: '#D9B77A', sw: 30, opacity: 0.45 }), { 'clip-path': 'url(#sc)' });
  [[120], [920]].forEach(([y]) => {
    s += R(60, y - 45, 640, 90, 45, '#E9CF98') + L(`M80,${y - 20} L680,${y - 20}`, '#fff', 6, { opacity: 0.4 }) + L(`M80,${y + 25} L680,${y + 25}`, '#C4A26A', 5);
    s += R(30, y - 25, 40, 50, 10, '#8B5A2B') + R(690, y - 25, 40, 50, 10, '#8B5A2B');
  });
  return svgDoc(W, H, s, `<clipPath id="sc"><path d="${d}"/></clipPath>`);
}
function stoneTablet() {
  const d = 'M120,90 L320,60 L560,80 L820,56 L1080,90 L1130,300 L1110,560 L1140,700 L880,740 L600,722 L330,744 L80,710 L100,480 L70,260 Z';
  let s = sh(P(d, '#000', { stroke: 'none' })) + P(d, '#A7ADB3', { sw: 6 }) + P('M150,120 L1060,120 L1090,320 L1070,560 L1090,670 L130,680 L140,480 L110,270 Z', '#B9BEC3', { sw: 3, stroke: '#8E959B' });
  s += L('M320,60 L340,110 L310,140 M880,740 L860,690 M1130,300 L1080,320', '#7E858B', 4);
  s += frond([60, 720], [160, 640], [300, 640], 34, '#4CAF50', { notch: 0.5 }) + frond([60, 720], [100, 600], [180, 520], 30, '#388E3C', { notch: 0.5 }) + frond([1150, 80], [1060, 60], [940, 30], 30, '#4CAF50', { notch: 0.5 });
  return svgDoc(1200, 800, s);
}
function ribbon(col) {
  const dk = shade(col, -0.3);
  let s = sh(P('M140,120 Q800,60 1460,120 L1460,280 Q800,220 140,280 Z', '#000', { stroke: 'none' }));
  s += P('M20,170 L190,170 L190,330 L20,330 L80,250 Z', dk) + P('M1580,170 L1410,170 L1410,330 L1580,330 L1520,250 Z', dk);
  s += P('M140,280 L190,330 L190,270 Z', shade(col, -0.5)) + P('M1460,280 L1410,330 L1410,270 Z', shade(col, -0.5));
  s += P('M140,120 Q800,60 1460,120 L1460,280 Q800,220 140,280 Z', col) + L('M170,140 Q800,82 1430,140 M170,262 Q800,204 1430,262', '#fff', 4, { opacity: 0.6, 'stroke-dasharray': '18 12' });
  return svgDoc(1600, 400, s);
}
function badge(col) {
  let s = sh(C(200, 200, 170, '#000', { stroke: 'none' })) + C(200, 200, 170, col, { sw: 6 }) + C(200, 200, 140, shade(col, 0.15), { sw: 3, stroke: shade(col, -0.3) });
  for (let i = 0; i < 4; i++) s += L(`M${110 + i * 10},${150 + i * 30} Q200,${140 + i * 30} ${290 - i * 10},${150 + i * 30}`, shade(col, -0.15), 3, { opacity: 0.6 });
  s += P('M110,120 Q150,80 200,72', 'none', { stroke: '#fff', sw: 10, opacity: 0.4 });
  return svgDoc(400, 400, s);
}
function leafWreath() {
  let s = '';
  for (let i = 0; i < 28; i++) { const a = i / 28 * 360, rad = a * Math.PI / 180; s += leaf(300 + Math.cos(rad) * 250, 300 + Math.sin(rad) * 250, 70, a + 100, i % 2 ? '#43A047' : '#66BB6A'); }
  s += C(300, 300, 240, 'none', { stroke: '#6D8B3A', sw: 8 });
  s += hibiscus(300, 60, 40) + hibiscus(110, 450, 34, '#FF7043') + hibiscus(490, 450, 34);
  return svgDoc(600, 600, s);
}

module.exports = () => {
  const D = '05-frames-and-signs';
  const [w1, h1, t1] = titleSign(1520, 380);
  const [w2, h2, t2] = titleSign(900, 330, ['#C68B4E', '#B97A45', '#C68B4E']);
  const list = [
    ['wooden-title-sign', 'שלט עץ גדול לכותרת', svgDoc(w1, h1, t1), w1, h1],
    ['wooden-sign-medium', 'שלט עץ בינוני', svgDoc(w2, h2, t2), w2, h2],
    ['name-plank-natural', 'לוח שם – עץ טבעי', namePlank('#C68B4E'), 720, 220],
    ['name-plank-orange', 'לוח שם – כתום', namePlank('#F08A3C'), 720, 220],
    ['name-plank-blue', 'לוח שם – כחול', namePlank('#4C93D9'), 720, 220],
    ['name-plank-purple', 'לוח שם – סגול', namePlank('#9A63C4'), 720, 220],
    ['bamboo-frame-wide', 'מסגרת במבוק רחבה (לתמונה/טקסט)', bambooFrame(1520, 860), 1600, 940],
    ['bamboo-frame-square', 'מסגרת במבוק מרובעת', bambooFrame(920, 920), 1000, 1000],
    ['scroll-horizontal', 'מגילה אופקית', scrollH(), 1600, 560],
    ['scroll-vertical', 'מגילה אנכית (לרשימות)', scrollV(), 760, 1040],
    ['stone-tablet', 'לוח אבן', stoneTablet(), 1200, 800],
    ['ribbon-orange', 'סרט כותרת כתום', ribbon('#FF7A1A'), 1600, 400],
    ['ribbon-blue', 'סרט כותרת כחול', ribbon('#1E88E5'), 1600, 400],
    ['ribbon-purple', 'סרט כותרת סגול', ribbon('#8E44AD'), 1600, 400],
    ['round-badge-wood', 'עיגול עץ (למספרים)', badge('#C68B4E'), 400, 400],
    ['round-badge-orange', 'עיגול כתום', badge('#F08A3C'), 400, 400],
    ['round-badge-blue', 'עיגול כחול', badge('#4C93D9'), 400, 400],
    ['leaf-wreath-frame', 'מסגרת עלים עגולה', leafWreath(), 600, 600],
  ];
  return list.map(([name, he, svg, w, h]) => ({ dir: D, name, he, svg, w, h, scale: w >= 1500 ? 1 : 1.5 }));
};
