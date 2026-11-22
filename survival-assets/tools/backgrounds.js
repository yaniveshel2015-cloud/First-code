// 16:9 slide backgrounds (1920x1080, opaque)
const { OL, svgDoc, P, C, E, R, L, G, limb, blob, shade, flame, star4, rng } = require('./common');
const { frond, leaf, palm, bush, grass, hibiscus } = require('./flora');
const parts = require('./props').parts;

const W = 1920, H = 1080;
let uid = 0;
// embed another asset's svg (renaming its ids) at x,y with scale
function embed(svg, x, y, sc = 1) {
  const p = 'e' + (++uid) + '_';
  const defs = (svg.match(/<defs>([\s\S]*?)<\/defs>/) || [, ''])[1];
  const body = svg.replace(/^<svg[^>]*>/, '').replace(/<\/svg>$/, '').replace(/<defs>[\s\S]*?<\/defs>/, '');
  const fix = (t) => t.replace(/id="([^"]+)"/g, `id="${p}$1"`).replace(/url\(#([^)]+)\)/g, `url(#${p}$1)`);
  return { defs: fix(defs), body: G(fix(body), { transform: `translate(${x},${y}) scale(${sc})` }) };
}
const lin = (id, stops, x2 = 0, y2 = 1) => `<linearGradient id="${id}" x1="0" y1="0" x2="${x2}" y2="${y2}">${stops.map(([o, c, a = 1]) => `<stop offset="${o}" stop-color="${c}" stop-opacity="${a}"/>`).join('')}</linearGradient>`;
const rad = (id, c, a = 0.6) => `<radialGradient id="${id}"><stop offset="0" stop-color="${c}" stop-opacity="${a}"/><stop offset="1" stop-color="${c}" stop-opacity="0"/></radialGradient>`;
const cloud = (x, y, s, col = '#FFFFFF', o = {}) => blob([[x, y, 60 * s], [x + 70 * s, y - 30 * s, 75 * s], [x + 150 * s, y, 60 * s], [x + 60 * s, y + 20 * s, 55 * s], [x - 60 * s, y + 15 * s, 40 * s], [x + 210 * s, y + 18 * s, 38 * s]], col, { sw: o.sw ?? 0.01, ol: o.ol ?? col })
  + E(x + 70 * s, y + 40 * s, 200 * s, 14 * s, shade(col, -0.08), { stroke: 'none', opacity: o.flat === false ? 0 : 0.6 });
const waves = (y0, y1, n, seed, col = '#FFFFFF', op = 0.5) => { const r = rng(seed); let s = ''; for (let i = 0; i < n; i++) { const y = y0 + r() * (y1 - y0), x = r() * W, w = 20 + (y - y0) / (y1 - y0) * 50; s += L(`M${x},${y} q${w / 2},${-w / 5} ${w},0`, col, 3 + (y - y0) / (y1 - y0) * 3, { opacity: op }); } return s; };
const speckle = (y0, y1, n, seed, col) => { const r = rng(seed); let s = ''; for (let i = 0; i < n; i++) s += C(r() * W, y0 + r() * (y1 - y0), 2 + r() * 3, col, { stroke: 'none', opacity: 0.6 }); return s; };
const shoreline = (y, amp = 14) => { let d = `M0,${y}`; for (let x = 0; x <= W; x += 120) d += ` Q${x + 60},${y + (x / 120 % 2 ? amp : -amp)} ${x + 120},${y}`; return d; };
const starfish = (x, y, r, col = '#FF8A50', rot = 0) => { let d = ''; for (let i = 0; i < 10; i++) { const a = (i * 36 - 90) * Math.PI / 180, rr = i % 2 ? r * 0.45 : r; d += (i ? 'L' : 'M') + (x + Math.cos(a) * rr).toFixed(1) + ',' + (y + Math.sin(a) * rr).toFixed(1); } return G(P(d + 'Z', col, { sw: 4 }) + C(x, y, 3, '#fff', { stroke: 'none' }), { transform: `rotate(${rot} ${x} ${y})` }); };
const shell = (x, y, s = 1, col = '#FFD6C9') => G(P('M0,0 L-30,-10 Q-30,-46 0,-50 Q30,-46 30,-10 Z', col, { sw: 4 }) + L('M0,0 L-18,-40 M0,0 L0,-48 M0,0 L18,-40', shade(col, -0.25), 3), { transform: `translate(${x},${y}) scale(${s})` });
const silhouettePalm = (b, c, t, sc, col) => palm(b, c, t, { frondScale: sc, trunk: col, leaf: col, coconuts: false, w0: 50 * sc, w1: 28 * sc, sw: 2 });
const finish = (name, he, body, defs) => ({ dir: '02-backgrounds', name, he, w: W, h: H, opaque: true, scale: 1, svg: svgDoc(W, H, body, defs) });

function beachDay() {
  let defs = lin('sky', [[0, '#3FB7EE'], [1, '#BFEAFB']]) + lin('sea', [[0, '#22C1D6'], [1, '#0B8FAD']]) + lin('sand', [[0, '#FBE3A8'], [1, '#EDC27C']]) + rad('sun', '#FFF3B0', 0.9);
  let s = R(0, 0, W, 620, 0, 'url(#sky)', { stroke: 'none' });
  s += C(1640, 170, 260, 'url(#sun)', { stroke: 'none' }) + C(1640, 170, 86, '#FFE873', { stroke: 'none' });
  s += cloud(220, 170, 1.1) + cloud(860, 110, 0.8) + cloud(1220, 250, 0.9) + cloud(560, 330, 0.55);
  s += P('M1100,612 Q1180,520 1260,540 Q1330,440 1420,500 Q1500,470 1580,612 Z', '#5FAE84', { stroke: 'none' }) + P('M1300,612 Q1330,520 1420,500 Q1450,560 1460,612 Z', '#4E9B74', { stroke: 'none' });
  s += R(0, 600, W, 240, 0, 'url(#sea)', { stroke: 'none' }) + R(0, 600, W, 6, 0, '#9EE7F0', { stroke: 'none', opacity: 0.7 });
  s += waves(620, 800, 70, 3);
  s += P(shoreline(800, 16) + ` L${W},840 L0,840 Z`, '#7FE0E6', { stroke: 'none' });
  s += P(shoreline(830, 12) + ` L${W},${H} L0,${H} Z`, 'url(#sand)', { stroke: 'none' }) + L(shoreline(830, 12), '#FFFFFF', 10, { opacity: 0.9 });
  s += speckle(850, H, 220, 5, '#D9AE62');
  s += starfish(1420, 980, 40, '#FF8A50', 12) + shell(560, 1010, 1) + shell(1500, 900, 0.7, '#FFE3B3') + starfish(320, 900, 26, '#FFB74D', -20);
  s += palm([220, 1130], [320, 760], [190, 360], { frondScale: 1.55, w0: 84, w1: 46 });
  s += palm([1790, 1130], [1680, 800], [1790, 470], { frondScale: 1.3, w0: 74, w1: 40 });
  s += bush(70, 1040, 80, '#3FA34D') + bush(1870, 1050, 70, '#43A047') + grass(400, 1080, 60, '#66BB6A') + grass(1620, 1080, 70, '#66BB6A');
  return finish('01-beach-day', 'חוף טרופי ביום', s, defs);
}
function beachSunset() {
  let defs = lin('sky', [[0, '#2A1A4D'], [0.38, '#7A2E6E'], [0.66, '#E2546E'], [0.88, '#FF9A4D'], [1, '#FFD27A']]) + lin('sea', [[0, '#7A3470'], [1, '#2B1844']]) + rad('sun', '#FFD27A', 0.8);
  let s = R(0, 0, W, 640, 0, 'url(#sky)', { stroke: 'none' });
  const r = rng(4); for (let i = 0; i < 40; i++) s += C(r() * W, r() * 260, 1.5 + r() * 2, '#fff', { stroke: 'none', opacity: 0.4 + r() * 0.5 });
  s += C(960, 640, 420, 'url(#sun)', { stroke: 'none' }) + C(960, 640, 170, '#FFD54F', { stroke: 'none' }) + C(960, 640, 140, '#FFE38A', { stroke: 'none' });
  [[200, 300, 520], [1300, 260, 600], [700, 420, 380], [1500, 450, 320]].forEach(([x, y, w]) => { s += R(x, y, w, 16, 8, '#B9477A', { stroke: 'none', opacity: 0.55 }) + R(x + 60, y + 26, w * 0.6, 12, 6, '#D0587A', { stroke: 'none', opacity: 0.45 }); });
  [[560, 220], [610, 250], [1380, 160], [1330, 190]].forEach(([x, y]) => { s += L(`M${x - 22},${y} q11,-12 22,0 q11,-12 22,0`, '#2A1A4D', 5); });
  s += R(0, 640, W, 280, 0, 'url(#sea)', { stroke: 'none' });
  for (let i = 0; i < 12; i++) { const w = 300 - i * 20; s += R(960 - w / 2 + (i % 2) * 20, 652 + i * 20, w, 7, 4, '#FFB74D', { stroke: 'none', opacity: 0.75 - i * 0.04 }); }
  s += waves(650, 900, 50, 8, '#FFB27A', 0.35);
  s += P(shoreline(905, 12) + ` L${W},${H} L0,${H} Z`, '#3A1F45', { stroke: 'none' }) + P(shoreline(960, 10) + ` L${W},${H} L0,${H} Z`, '#2A1636', { stroke: 'none' });
  s += silhouettePalm([180, 1130], [280, 760], [150, 340], 1.5, '#1B0F26') + silhouettePalm([1760, 1130], [1680, 800], [1800, 430], 1.35, '#1B0F26');
  s += silhouettePalm([1560, 1100], [1530, 900], [1590, 680], 0.8, '#24132F');
  return finish('02-beach-sunset', 'שקיעה על החוף', s, defs);
}
function jungle() {
  let defs = lin('sky', [[0, '#D9F0B8'], [1, '#86BF6E']]) + lin('ray', [[0, '#FFFDE0', 0.55], [1, '#FFFDE0', 0]]);
  let s = R(0, 0, W, H, 0, 'url(#sky)', { stroke: 'none' });
  const r = rng(21);
  for (let i = 0; i < 12; i++) { const x = i * 170 + r() * 60; s += R(x, 0, 26 + r() * 20, 760, 0, '#9CC98A', { stroke: 'none' }); }
  s += blob(Array.from({ length: 22 }, (_, i) => [i * 92, 60 + r() * 120, 110 + r() * 50]), '#A9D494', { sw: 0.01, ol: '#A9D494' });
  s += P('M0,700 Q480,640 960,690 Q1440,640 1920,700 L1920,1080 L0,1080 Z', '#78B35F', { stroke: 'none' });
  [[260, 1], [560, 0], [1380, 1], [1660, 0]].forEach(([x, k]) => { s += R(x, 0, 60 + k * 16, 760, 6, '#7A5A3A', { sw: 4 }) + L(`M${x + 18},60 L${x + 18},740`, '#5E4329', 4, { opacity: 0.6 }); });
  s += blob(Array.from({ length: 16 }, (_, i) => [i * 130, 40 + r() * 70, 110 + r() * 40]), '#5DA453', { sw: 4 });
  s += P('M200,0 L560,0 L1100,1080 L640,1080 Z', 'url(#ray)', { stroke: 'none', opacity: 0.55 }) + P('M800,0 L980,0 L1450,1080 L1200,1080 Z', 'url(#ray)', { stroke: 'none', opacity: 0.45 }) + P('M1300,0 L1420,0 L1800,1080 L1620,1080 Z', 'url(#ray)', { stroke: 'none', opacity: 0.35 });
  s += P('M780,1080 C820,940 930,860 960,760 C990,720 1010,700 1000,690 C1060,720 1060,780 1030,840 C990,930 1120,1000 1180,1080 Z', '#D7B57A', { sw: 4 });
  [[640, 760, 70], [1290, 760, 64], [460, 820, 90], [1490, 830, 90]].forEach(([x, y, rr], i) => { s += bush(x, y, rr, i % 2 ? '#4E9A47' : '#43913F'); });
  [[300, 0], [620, 0], [1300, 0], [1620, 0], [980, 0]].forEach(([x], i) => {
    const len = 280 + (i * 97) % 200; s += limb(`M${x},0 C${x + 40},${len * 0.3} ${x - 40},${len * 0.6} ${x + 10},${len}`, '#6D8B3A', 8, { sw: 3 });
    for (let j = 1; j <= 5; j++) s += leaf(x + (j % 2 ? 6 : -6), len * j / 6, 44, j % 2 ? 20 : 160, j % 2 ? '#4CAF50' : '#66BB6A');
  });
  s += frond([-40, 1120], [120, 820], [420, 700], 110, '#2E7D32', { notch: 0, veins: true, peak: 0.45 });
  s += frond([-40, 1120], [40, 800], [100, 560], 100, '#388E3C', { notch: 0, veins: true, peak: 0.45 });
  s += frond([1960, 1120], [1800, 820], [1500, 720], 110, '#2E7D32', { notch: 0, veins: true, peak: 0.45 });
  s += frond([1960, 1120], [1880, 800], [1820, 560], 100, '#388E3C', { notch: 0, veins: true, peak: 0.45 });
  s += frond([-40, -40], [200, 80], [480, 120], 80, '#1B5E20', { notch: 0.5 }) + frond([-40, -40], [80, 200], [140, 420], 80, '#2E7D32', { notch: 0.5 });
  s += frond([1960, -40], [1720, 80], [1440, 120], 80, '#1B5E20', { notch: 0.5 }) + frond([1960, -40], [1840, 200], [1780, 420], 80, '#2E7D32', { notch: 0.5 });
  s += bush(140, 1060, 110, '#2E7D32') + bush(1780, 1060, 110, '#2E7D32') + hibiscus(330, 990, 46) + hibiscus(1600, 980, 40, '#FF7043');
  for (let i = 0; i < 10; i++) s += grass(560 + i * 90, 1085, 50 + (i % 3) * 14, i % 2 ? '#558B2F' : '#689F38');
  return finish('03-jungle', 'ג׳ונגל', s, defs);
}
function tribalCouncil() {
  let defs = lin('sky', [[0, '#0B0F2A'], [1, '#2B2258']]) + lin('floor', [[0, '#4A3448'], [1, '#22172A']]) + rad('glow', '#FF9E3D', 0.55) + rad('glow2', '#FFB347', 0.35);
  let s = R(0, 0, W, H, 0, 'url(#sky)', { stroke: 'none' });
  const r = rng(77); for (let i = 0; i < 110; i++) s += C(r() * W, r() * 420, 1 + r() * 2.4, '#FFFFFF', { stroke: 'none', opacity: 0.3 + r() * 0.7 });
  s += C(1640, 150, 64, '#FFF4C7', { stroke: 'none', mask: 'url(#moon)' }); defs += '<mask id="moon"><rect width="1920" height="1080" fill="#fff"/><circle cx="1668" cy="132" r="58" fill="#000"/></mask>';
  s += blob(Array.from({ length: 20 }, (_, i) => [i * 100, 470 + r() * 50, 90 + r() * 50]), '#141A3D', { sw: 0.01, ol: '#141A3D' });
  s += silhouettePalm([150, 700], [190, 520], [120, 300], 1.0, '#101433') + silhouettePalm([1780, 700], [1740, 520], [1810, 320], 1.0, '#101433');
  s += P('M0,620 Q960,560 1920,620 L1920,1080 L0,1080 Z', 'url(#floor)', { stroke: 'none' });
  s += C(960, 600, 900, 'url(#glow2)', { stroke: 'none' });
  // back wooden gate
  s += R(520, 250, 70, 420, 8, '#5A3A22') + R(1330, 250, 70, 420, 8, '#5A3A22') + R(470, 230, 980, 70, 12, '#6B4628') + R(490, 300, 940, 26, 8, '#4A2E1A');
  [[555, 250], [1365, 250]].forEach(([x, y]) => { s += G(P('M-48,0 L-40,-120 Q0,-150 40,-120 L48,0 Z', '#7A5230') + L('M-34,-98 Q-18,-112 -4,-98 M4,-98 Q18,-112 34,-98', OL, 6) + C(-19, -82, 13, '#FFE0A0', { sw: 3 }) + C(19, -82, 13, '#FFE0A0', { sw: 3 }) + C(-18, -81, 6, OL, { stroke: 'none' }) + C(18, -81, 6, OL, { stroke: 'none' }) + P('M-6,-70 L0,-54 L6,-70', 'none', { sw: 4 }) + R(-26, -44, 52, 24, 8, '#3A2214', { sw: 3 }) + R(-20, -40, 40, 8, 2, '#FFE0A0', { stroke: 'none' }), { transform: `translate(${x},${y})` }); });
  for (let i = 0; i < 13; i++) { const x = 640 + i * 54; s += limb(`M${x},476 L${x},600`, '#C9A15A', 9, { sw: 3 }) + flame(x, 470, 54, { sw: 3 }) + C(x, 440, 40, 'url(#glow)', { stroke: 'none' }); }
  s += R(610, 590, 700, 30, 8, '#6B4628');
  // big side torches
  [[120, 360, 1.25], [380, 430, 1.05], [1540, 430, 1.05], [1800, 360, 1.25]].forEach(([x, y, k]) => {
    s += C(x, y - 70 * k, 220 * k, 'url(#glow)', { stroke: 'none' }) + limb(`M${x},${y + 40} L${x},1080`, '#B98F4E', 24 * k, { sw: 4 }) + flame(x, y + 10 * k, 170 * k);
    s += P(`M${x - 50 * k},${y} L${x + 50 * k},${y} L${x + 26 * k},${y + 80 * k} L${x - 26 * k},${y + 80 * k} Z`, '#7A4A22') + L(`M${x - 40 * k},${y + 28 * k} L${x + 40 * k},${y + 28 * k} M${x - 32 * k},${y + 54 * k} L${x + 32 * k},${y + 54 * k}`, '#4A2E1A', 4);
  });
  // benches
  [[230, 820, 520], [170, 940, 600]].forEach(([x, y, w]) => { s += R(x, y, w, 46, 22, '#7A4A22') + L(`M${x + 30},${y + 22} L${x + w - 30},${y + 22}`, '#5A3418', 4) + E(x + w, y + 23, 16, 23, '#C68B4E', { sw: 4 }); });
  // voting stump + urn on right
  s += R(1480, 770, 210, 160, 16, '#6B4628') + E(1585, 772, 105, 26, '#C68B4E') + L('M1585,772 m-60,0 a60,14 0 1,0 120,0 a60,14 0 1,0 -120,0', '#8B5A2B', 4);
  const urn = embed(parts.votingUrn(), 1500, 560, 0.3); defs += urn.defs; s += urn.body;
  // fire pit
  s += C(960, 820, 330, 'url(#glow)', { stroke: 'none' });
  const fire = embed(parts.campfire(), 760, 640, 0.58); defs += fire.defs; s += fire.body;
  return finish('04-tribal-council', 'מועצת השבט בלילה', s, defs);
}
function camp() {
  let defs = lin('sky', [[0, '#7CC3DE'], [0.7, '#FFD9A0'], [1, '#FFC98A']]) + lin('sea', [[0, '#4DB6C8'], [1, '#2A8FA8']]) + lin('sand', [[0, '#F2D49A'], [1, '#E0B370']]) + rad('sun', '#FFE9A8', 0.8);
  let s = R(0, 0, W, 580, 0, 'url(#sky)', { stroke: 'none' }) + C(1200, 520, 320, 'url(#sun)', { stroke: 'none' }) + C(1200, 540, 80, '#FFE38A', { stroke: 'none' });
  s += cloud(260, 160, 0.9, '#FFF4E4') + cloud(1450, 120, 0.8, '#FFF4E4') + cloud(900, 260, 0.5, '#FFF4E4');
  s += R(0, 560, W, 170, 0, 'url(#sea)', { stroke: 'none' }) + waves(570, 720, 45, 9, '#E9FBFF', 0.5);
  s += P(shoreline(720, 14) + ` L${W},${H} L0,${H} Z`, 'url(#sand)', { stroke: 'none' }) + L(shoreline(720, 14), '#FFFFFF', 8, { opacity: 0.85 }) + speckle(740, H, 160, 12, '#C99B55');
  s += palm([1700, 1100], [1620, 760], [1720, 380], { frondScale: 1.3, w0: 74, w1: 40 });
  // clothesline from palm to shelter with buffs
  s += L('M560,430 Q1150,520 1690,470', '#7A5A3A', 4);
  [[820, 472, '#FF7A1A'], [1000, 492, '#1E88E5'], [1350, 494, '#FFC400']].forEach(([x, y, c]) => { s += P(`M${x - 40},${y} L${x + 40},${y + 2} L${x + 30},${y + 70} L${x - 34},${y + 66} Z`, c, { sw: 4 }) + L(`M${x - 30},${y + 24} L${x + 30},${y + 26}`, '#fff', 4, { opacity: 0.7 }); });
  const sh = embed(parts.shelter(), -60, 360, 0.85); defs += sh.defs; s += sh.body;
  s += R(1050, 900, 260, 56, 26, '#8B5A2B') + E(1310, 928, 18, 28, '#E3B07A', { sw: 4 }) + L('M1080,928 L1280,928', '#6B4220', 4);
  // tripod + pot
  s += limb('M1380,640 L1300,900 M1380,640 L1460,900 M1380,640 L1380,910', '#7A5A3A', 10, { sw: 4 });
  const fire = embed(parts.campfire(), 1240, 700, 0.42); defs += fire.defs; s += fire.body;
  s += limb('M1380,640 L1380,720', '#555', 3, { sw: 2 }) + P('M1335,720 L1425,720 Q1428,790 1380,792 Q1332,790 1335,720 Z', '#4A4A4A') + E(1380, 720, 46, 10, '#2E2E2E', { sw: 4 });
  s += starfish(620, 1000, 30, '#FF8A50', 15) + shell(900, 1040, 0.8);
  s += bush(1880, 1050, 70, '#43A047') + grass(1560, 1080, 60, '#66BB6A');
  return finish('05-camp', 'המחנה – מחסה ומדורה', s, defs);
}
function challenge() {
  let defs = lin('sky', [[0, '#3FB7EE'], [1, '#C9EEFB']]) + lin('sea', [[0, '#22C1D6'], [1, '#0F95B0']]) + lin('sand', [[0, '#FBE3A8'], [1, '#EBC07A']]);
  let s = R(0, 0, W, 560, 0, 'url(#sky)', { stroke: 'none' }) + cloud(300, 140, 0.9) + cloud(1350, 110, 1) + cloud(820, 230, 0.5);
  s += R(0, 540, W, 120, 0, 'url(#sea)', { stroke: 'none' }) + waves(550, 650, 40, 13);
  s += P(shoreline(660, 10) + ` L${W},${H} L0,${H} Z`, 'url(#sand)', { stroke: 'none' }) + L(shoreline(660, 10), '#fff', 8, { opacity: 0.9 }) + speckle(680, H, 200, 15, '#D9AE62');
  // central wooden tower
  s += R(820, 300, 30, 420, 4, '#8B5A2B') + R(1070, 300, 30, 420, 4, '#8B5A2B') + R(790, 300, 340, 40, 8, '#A0692F') + R(800, 480, 320, 28, 6, '#A0692F') + L('M850,340 L1070,480 M1070,340 L850,480', '#6B4220', 10);
  s += R(900, 200, 120, 100, 10, '#C68B4E') + C(960, 250, 36, '#F2B632', { sw: 4 }) + C(960, 250, 14, '#C98A12', { stroke: 'none' }) + L('M910,200 L960,170 L1010,200', '#6B4220', 6);
  // lanes
  [[640, 1], [960, 0], [1280, 1]].forEach(([x]) => { s += L(`M${x},700 L${x + (x - 960) * 0.9},${H}`, '#F5F5F5', 8, { 'stroke-dasharray': '30 20', opacity: 0.85 }); });
  [[600, 720], [1320, 720], [420, 900], [1500, 900]].forEach(([x, y]) => { s += limb(`M${x},${y} L${x},${y - 90}`, '#D2A95A', 16, { sw: 4 }); });
  s += L('M600,640 Q510,770 420,820 M1320,640 Q1410,770 1500,820', '#E0C89A', 5);
  // puzzle tables
  [[420, '#FF7A1A'], [1300, '#1E88E5']].forEach(([x, c]) => { s += R(x, 600, 200, 120, 10, '#A0692F') + R(x + 16, 612, 168, 96, 6, shade(c, 0.6), { sw: 3 }) + R(x + 24, 720, 16, 60, 3, '#6B4220') + R(x + 160, 720, 16, 60, 3, '#6B4220'); for (let i = 0; i < 3; i++) for (let j = 0; j < 2; j++) s += R(x + 26 + i * 52, 622 + j * 42, 44, 36, 5, (i + j) % 2 ? c : shade(c, 0.3), { sw: 2.5 }); });
  // balance beam
  s += R(760, 860, 400, 28, 8, '#C68B4E') + R(790, 888, 20, 50, 3, '#6B4220') + R(1110, 888, 20, 50, 3, '#6B4220');
  const fo = embed(parts.flag('#FF7A1A', parts.SYM.sun()), 30, 300, 0.95); const fb = embed(parts.flag('#1E88E5', parts.SYM.wave()), 1430, 300, 0.95);
  defs += fo.defs + fb.defs; s += fo.body + fb.body;
  s += palm([60, 760], [120, 560], [40, 330], { frondScale: 0.9, w0: 44, w1: 26 }) + palm([1880, 760], [1820, 560], [1880, 340], { frondScale: 0.9, w0: 44, w1: 26 });
  return finish('06-challenge-arena', 'זירת משימות', s, defs);
}
function island() {
  let defs = lin('sky', [[0, '#5CC6F2'], [1, '#D3F2FC']]) + lin('sea', [[0, '#1FB3CC'], [1, '#0A6E95']]) + rad('shallow', '#7FF0E8', 0.9);
  let s = R(0, 0, W, 470, 0, 'url(#sky)', { stroke: 'none' }) + cloud(180, 160, 1) + cloud(1450, 130, 1.1) + cloud(820, 90, 0.6);
  s += R(0, 460, W, 620, 0, 'url(#sea)', { stroke: 'none' }) + waves(480, 1080, 120, 31, '#E9FBFF', 0.5);
  s += E(960, 700, 760, 190, 'url(#shallow)', { stroke: 'none' });
  s += P('M380,720 Q420,640 600,630 Q760,560 960,580 Q1200,560 1360,630 Q1540,650 1560,720 Q1400,790 960,790 Q520,790 380,720 Z', '#F6D89A');
  s += P('M470,690 Q560,620 700,600 Q760,420 880,330 Q960,260 1040,330 Q1140,420 1200,560 Q1330,590 1450,690 Q1300,740 960,740 Q620,740 470,690 Z', '#4CAF50');
  s += P('M880,330 Q960,260 1040,330 Q1090,380 1120,450 Q1000,420 960,470 Q930,410 830,420 Q850,370 880,330 Z', '#8C7A5B', { sw: 4 }) + P('M920,300 Q960,262 1000,300 Q980,320 960,312 Q940,326 920,300 Z', '#FFFFFF', { sw: 3 });
  s += bush(650, 660, 50, '#388E3C') + bush(1260, 660, 50, '#388E3C') + bush(800, 560, 46, '#43A047') + bush(1130, 580, 46, '#43A047') + bush(960, 690, 50, '#2E7D32');
  s += palm([560, 720], [580, 640], [540, 560], { frondScale: 0.5, w0: 18, w1: 12, sw: 3 }) + palm([1400, 720], [1390, 640], [1420, 560], { frondScale: 0.5, w0: 18, w1: 12, sw: 3 }) + palm([720, 760], [700, 690], [740, 610], { frondScale: 0.45, w0: 16, w1: 10, sw: 3 });
  s += L('M380,720 Q420,770 960,800 Q1500,770 1560,720', '#fff', 8, { opacity: 0.8 });
  // boat
  s += G(P('M-90,0 L90,0 L60,40 L-60,40 Z', '#A0692F') + limb('M0,0 L0,-120', '#6B4220', 6, { sw: 3 }) + P('M6,-116 L80,-10 L6,-10 Z', '#FFFFFF', { sw: 4 }) + L('M-120,48 q30,-10 60,0 M60,48 q30,-10 60,0', '#fff', 4, { opacity: 0.8 }), { transform: 'translate(1600,930)' });
  [[400, 300], [440, 330], [1300, 340]].forEach(([x, y]) => { s += L(`M${x - 18},${y} q9,-10 18,0 q9,-10 18,0`, '#37474F', 4); });
  return finish('07-island-ocean', 'אי בודד באמצע האוקיינוס', s, defs);
}
function jungleFrame() {
  let defs = `<radialGradient id="c" cx="0.5" cy="0.5" r="0.7"><stop offset="0" stop-color="#FFF8E7"/><stop offset="0.7" stop-color="#F6E7C4"/><stop offset="1" stop-color="#D9C08B"/></radialGradient>`;
  let s = R(0, 0, W, H, 0, 'url(#c)', { stroke: 'none' });
  const corner = (tx, ty, sx, sy) => {
    let c = '';
    [[[0, 0], [300, 60], [620, 170], 80, '#2E7D32'], [[0, 0], [200, 180], [380, 460], 76, '#388E3C'], [[0, 0], [60, 280], [90, 600], 70, '#2E7D32'], [[0, 0], [330, 140], [520, 350], 84, '#43A047'], [[0, 0], [200, 30], [470, 40], 60, '#4CAF50']].forEach(([b, cc, t, w, col]) => { c += frond(b, cc, t, w, col, { n: 30, notch: 0.55 }); });
    c += frond([0, 0], [140, 220], [230, 380], 90, '#66BB6A', { notch: 0, veins: true, peak: 0.45 });
    return G(c, { transform: `translate(${tx},${ty}) scale(${sx},${sy})` });
  };
  s += corner(-20, -20, 1, 1) + corner(W + 20, -20, -1, 1) + corner(-20, H + 20, 1, -1) + corner(W + 20, H + 20, -1, -1);
  s += hibiscus(170, 140, 60) + hibiscus(W - 170, 140, 60, '#FF7043') + hibiscus(180, H - 150, 50, '#FF7043') + hibiscus(W - 180, H - 150, 50);
  [[620, 0, 170], [960, 0, 120], [1300, 0, 170]].forEach(([x, , len]) => { s += limb(`M${x},0 C${x + 30},${len * 0.3} ${x - 30},${len * 0.6} ${x},${len}`, '#6D8B3A', 7, { sw: 3 }); for (let j = 1; j <= 3; j++) s += leaf(x, len * j / 3.5, 40, j % 2 ? 20 : 160, '#4CAF50'); });
  return finish('08-jungle-frame-light', 'מסגרת ג׳ונגל עם מרכז בהיר לטקסט', s, defs);
}
function woodPlanks() {
  const r = rng(42);
  let s = R(0, 0, W, H, 0, '#7A4A22', { stroke: 'none' });
  const ph = 135;
  for (let i = 0; i < 8; i++) {
    const y = i * ph, col = ['#9C6233', '#8E5A2E', '#A86C3A', '#94602F'][i % 4];
    s += R(-10, y + 3, W + 20, ph - 6, 10, col, { sw: 4 });
    for (let k = 0; k < 5; k++) { const yy = y + 20 + r() * (ph - 40); s += L(`M0,${yy} C${480},${yy + (r() - 0.5) * 30} ${1440},${yy + (r() - 0.5) * 30} ${W},${yy + (r() - 0.5) * 16}`, shade(col, -0.18), 3, { opacity: 0.7 }); }
    const kx = 200 + r() * 1500; s += E(kx, y + ph / 2, 30, 12, shade(col, -0.25), { stroke: 'none' }) + E(kx, y + ph / 2, 16, 6, shade(col, -0.4), { stroke: 'none' });
    const off = (i % 2) * 480; for (let x = 140 + off; x < W; x += 960) { s += L(`M${x},${y + 3} L${x},${y + ph - 3}`, OL, 4); s += C(x - 30, y + 24, 6, '#5A5A5A', { sw: 2 }) + C(x - 30, y + ph - 24, 6, '#5A5A5A', { sw: 2 }) + C(x + 30, y + 24, 6, '#5A5A5A', { sw: 2 }) + C(x + 30, y + ph - 24, 6, '#5A5A5A', { sw: 2 }); }
  }
  const defs = `<radialGradient id="v" cx="0.5" cy="0.5" r="0.75"><stop offset="0.55" stop-color="#000" stop-opacity="0"/><stop offset="1" stop-color="#000" stop-opacity="0.45"/></radialGradient>`;
  s += R(0, 0, W, H, 0, 'url(#v)', { stroke: 'none' });
  return finish('09-wood-planks', 'קיר קרשי עץ', s, defs);
}
function sandLight() {
  let defs = lin('sand', [[0, '#FFF1CF'], [1, '#F4D89C']]);
  let s = R(0, 0, W, H, 0, 'url(#sand)', { stroke: 'none' }) + speckle(0, H, 380, 51, '#E0BC78');
  const r = rng(8);
  for (let i = 0; i < 7; i++) { const x = 1500 + i * 40 + (i % 2) * 40, y = 1020 - i * 120; s += G(E(0, 0, 18, 30, '#E3C084', { stroke: 'none' }) + C(-10, -38, 6, '#E3C084', { stroke: 'none' }) + C(4, -42, 6, '#E3C084', { stroke: 'none' }) + C(16, -36, 5, '#E3C084', { stroke: 'none' }), { transform: `translate(${x},${y}) rotate(${-10 + r() * 20})` }); }
  s += starfish(180, 920, 46, '#FF8A50', 10) + shell(320, 1000, 1.1) + shell(1760, 160, 0.9, '#FFE3B3') + starfish(1700, 280, 30, '#FFB74D', -18) + shell(140, 200, 0.8);
  s += P(`M0,0 L${W},0 L${W},40 ` + Array.from({ length: 17 }, (_, i) => `Q${W - i * 120 - 60},${i % 2 ? 70 : 20} ${W - (i + 1) * 120},40`).join(' ') + ' Z', '#7FE0E6', { stroke: 'none' }) + L(Array.from({ length: 17 }, (_, i) => (i ? '' : `M${W},40 `) + `Q${W - i * 120 - 60},${i % 2 ? 70 : 20} ${W - (i + 1) * 120},40`).join(' '), '#fff', 10, { opacity: 0.9 });
  return finish('10-sand-light', 'חול בהיר (לשקופיות טקסט)', s, defs);
}

module.exports = () => [beachDay(), beachSunset(), jungle(), tribalCouncil(), camp(), challenge(), island(), jungleFrame(), woodPlanks(), sandLight()];
