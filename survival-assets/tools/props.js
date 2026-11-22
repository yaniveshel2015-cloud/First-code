// Props & decorations (transparent PNG)
const { OL, SW, svgDoc, P, C, E, R, L, G, limb, blob, shade, flame, star4, qpt, rng } = require('./common');
const { frond, leaf, palm, bush, grass, hibiscus } = require('./flora');

const WOOD = '#A0692F', WOOD_D = '#6B4220', WOOD_L = '#C68B4E', BAMBOO = '#D2A95A', GOLD = '#F2B632', GOLD_D = '#C98A12';
const glow = (id, c = '#FFC94A', o = 0.55) => `<radialGradient id="${id}"><stop offset="0" stop-color="${c}" stop-opacity="${o}"/><stop offset="1" stop-color="${c}" stop-opacity="0"/></radialGradient>`;
const bambooPole = (x, y1, y2, w = 26) => {
  let s = limb(`M${x},${y1} L${x},${y2}`, BAMBOO, w);
  for (let y = y1 + 80; y < y2 - 20; y += 95) s += L(`M${x - w / 2},${y} Q${x},${y + 6} ${x + w / 2},${y}`, '#8B6A35', 4);
  s += L(`M${x - w / 4},${y1 + 10} L${x - w / 4},${y2 - 10}`, '#fff', 3, { opacity: 0.35 });
  return s;
};
const basket = (x, y) => P(`M${x - 62},${y} L${x + 62},${y} L${x + 32},${y + 100} L${x - 32},${y + 100} Z`, WOOD)
  + L(`M${x - 52},${y + 30} L${x + 52},${y + 30} M${x - 42},${y + 62} L${x + 42},${y + 62} M${x - 20},${y} L${x - 10},${y + 100} M${x + 20},${y} L${x + 10},${y + 100}`, WOOD_D, 4)
  + R(x - 70, y - 12, 140, 20, 9, WOOD_L);

function torchLit() {
  const s = C(150, 130, 150, 'url(#g)', { stroke: 'none' }) + bambooPole(150, 280, 780) + flame(150, 210, 210) + basket(150, 200);
  return svgDoc(300, 800, s, glow('g'));
}
function torchSnuffed() {
  let s = bambooPole(150, 280, 780) + basket(150, 200);
  s += limb('M150,178 C116,140 186,110 150,72 C122,42 168,20 150,0', '#D9D9D9', 18, { sw: 4 });
  s += limb('M132,182 C110,160 128,140 112,118', '#E6E6E6', 12, { sw: 4 });
  s += limb('M170,182 C190,160 176,138 194,116', '#E6E6E6', 12, { sw: 4 });
  s += E(150, 190, 40, 9, '#3B2A20', { sw: 3 }) + C(138, 188, 4, '#FF7A1A', { stroke: 'none' }) + C(160, 190, 3, '#FF7A1A', { stroke: 'none' });
  return svgDoc(300, 800, s);
}
function campfire() {
  const stones = (front) => {
    let s = '';
    for (let i = 0; i < 14; i++) {
      const a = (i / 14) * Math.PI * 2, x = 350 + Math.cos(a) * 225, y = 500 + Math.sin(a) * 58;
      if ((Math.sin(a) > 0) === front) s += E(x, y, 40 - (i % 3) * 5, 26 - (i % 2) * 4, i % 2 ? '#9AA0A6' : '#828990', { sw: 4 });
    }
    return s;
  };
  const log = (x1, y1, x2, y2) => limb(`M${x1},${y1} L${x2},${y2}`, '#8B5A2B', 52, { cap: 'butt' }) + L(`M${x1 + 20},${y1 + (y2 - y1) * 0.06 - 8} L${x2 - 60},${y2 - (y2 - y1) * 0.16 - 8}`, '#6B4220', 4, { opacity: 0.6 })
    + E(x2, y2, 14, 28, '#E3B07A', { transform: `rotate(${Math.atan2(y2 - y1, x2 - x1) * 180 / Math.PI} ${x2} ${y2})` }) + C(x2, y2, 6, '#B97A45', { stroke: 'none' });
  let s = C(350, 340, 290, 'url(#g)', { stroke: 'none' }) + E(350, 510, 240, 62, '#3B2A20', { stroke: 'none', opacity: 0.35 });
  s += stones(false) + flame(350, 490, 380) + log(160, 520, 520, 430) + log(540, 520, 180, 430) + stones(true);
  [[250, 120, 7], [430, 90, 6], [300, 60, 5], [470, 180, 5], [220, 200, 5], [390, 30, 4]].forEach(([x, y, r]) => { s += C(x, y, r, '#FFD23F', { sw: 2.5 }); });
  return svgDoc(700, 600, s, glow('g', '#FFB347', 0.6));
}
function necklace() {
  let s = '';
  const L1 = [[140, 40], [130, 330], [300, 455]], R1 = [[460, 40], [470, 330], [300, 455]];
  s += L(`M140,40 Q130,330 300,455 Q470,330 460,40`, '#5C3A1A', 14) + L(`M140,40 Q130,330 300,455 Q470,330 460,40`, '#8B5A2B', 7);
  const cols = ['#F1E3C6', '#2EC4B6', '#F1E3C6', '#E4572E'];
  for (let i = 0; i < 9; i++) {
    const t = 0.22 + i * 0.085;
    [L1, R1].forEach((cv) => { const [x, y] = qpt(cv[0], cv[1], cv[2], t); s += i % 2 ? C(x, y, 15, cols[(i >> 1) % 4], { sw: 4 }) : E(x, y, 11, 20, '#F1E3C6', { sw: 4, transform: `rotate(${cv === L1 ? -30 + i * 6 : 30 - i * 6} ${x} ${y})` }); });
  }
  s += C(300, 470, 22, 'none', { sw: 14, stroke: GOLD_D }) + C(300, 470, 22, 'none', { sw: 6, stroke: GOLD });
  s += C(300, 600, 128, GOLD_D) + C(300, 600, 110, GOLD, { sw: 4 }) + C(300, 600, 84, '#E9A62A', { sw: 3, stroke: GOLD_D });
  for (let i = 0; i < 12; i++) { const a = i * Math.PI / 6; s += L(`M${300 + Math.cos(a) * 88},${600 + Math.sin(a) * 88} L${300 + Math.cos(a) * 106},${600 + Math.sin(a) * 106}`, GOLD_D, 5); }
  s += L('M300,600 m-6,0 a6,6 0 1,1 12,0 a14,14 0 1,1 -26,0 a24,24 0 1,1 46,0 a34,34 0 1,1 -66,0 a44,44 0 1,1 86,0', '#8A5A0B', 7);
  s += P('M232,540 Q260,512 300,508', 'none', { stroke: '#fff', sw: 8, opacity: 0.6 });
  [[455, 520, 20], [150, 560, 16], [440, 690, 14]].forEach(([x, y, r]) => { s += star4(x, y, r); });
  return svgDoc(600, 760, s);
}
function idol(withGlow) {
  let s = '';
  if (withGlow) {
    let rays = '';
    for (let i = 0; i < 16; i++) { const a = i * Math.PI / 8, b = a + 0.12; rays += `M250,330 L${250 + Math.cos(a) * 330},${330 + Math.sin(a) * 330} L${250 + Math.cos(b) * 330},${330 + Math.sin(b) * 330} Z `; }
    s += C(250, 330, 260, 'url(#g)', { stroke: 'none' }) + P(rays, '#FFE38A', { stroke: 'none', opacity: 0.45 });
  }
  s += E(250, 640, 150, 26, '#000', { stroke: 'none', opacity: 0.15 });
  s += R(130, 560, 240, 70, 14, WOOD_D) + R(130, 560, 240, 18, 9, WOOD);
  s += R(175, 380, 150, 190, 34, WOOD) + L('M195,440 Q250,470 305,440 M200,470 L200,540 M300,470 L300,540', WOOD_D, 6) + E(250, 505, 26, 34, WOOD_L, { sw: 4 });
  s += R(135, 120, 230, 280, 70, WOOD_L) + P('M135,250 Q250,230 365,250 L365,300 Q250,280 135,300 Z', WOOD, { sw: 0, stroke: 'none', opacity: 0.6 });
  s += P('M160,210 Q205,170 240,212 M260,212 Q295,170 340,210', 'none', { sw: 10 });
  s += C(203, 240, 32, '#FFF6DD') + C(297, 240, 32, '#FFF6DD') + C(206, 244, 15, OL, { stroke: 'none' }) + C(294, 244, 15, OL, { stroke: 'none' }) + C(200, 238, 5, '#fff', { stroke: 'none' }) + C(288, 238, 5, '#fff', { stroke: 'none' });
  s += P('M236,262 L250,300 L264,262', WOOD, { sw: 5 });
  s += R(180, 315, 140, 52, 22, '#5C2A14') + R(192, 320, 116, 16, 4, '#FFF6DD', { sw: 3 }) + L('M215,320 L215,336 M240,320 L240,336 M265,320 L265,336 M290,320 L290,336', OL, 3);
  s += P('M145,150 Q250,95 355,150 L360,120 Q250,40 140,120 Z', '#2EC4B6') + L('M170,128 L190,108 L210,128 L230,104 L250,128 L270,104 L290,128 L310,108 L330,128', '#FFE14D', 6);
  if (withGlow) s += star4(90, 160, 26) + star4(420, 110, 30) + star4(430, 450, 18) + star4(70, 420, 16);
  return svgDoc(500, 680, s, glow('g', '#FFD95A', 0.85));
}
function tikiMask() {
  let s = '';
  [[-60, 'M250,140 Q150,20 70,30'], [-20, 'M250,140 Q200,0 170,-10'], [20, 'M250,140 Q300,0 330,-10'], [60, 'M250,140 Q350,20 430,30']].forEach(([, d]) => {
    const m = d.match(/M([\d.]+),([\d.]+) Q([-\d.]+),([-\d.]+) ([-\d.]+),([-\d.]+)/).slice(1).map(Number);
    s += frond([m[0], m[1]], [m[2], m[3] + 40], [m[4], m[5] + 40], 34, '#3FA34D', { notch: 0.35 });
  });
  s += P('M250,110 C380,110 410,200 400,330 C392,470 360,600 300,690 Q250,740 200,690 C140,600 108,470 100,330 C90,200 120,110 250,110 Z', WOOD);
  s += P('M120,300 Q250,270 380,300 L384,330 Q250,302 116,330 Z', '#2EC4B6', { sw: 4 }) + P('M136,470 Q250,450 364,470 L356,500 Q250,482 144,500 Z', '#E4572E', { sw: 4 });
  s += P('M140,230 Q190,180 240,232 M260,232 Q310,180 360,230', 'none', { sw: 12 });
  s += E(190, 260, 44, 32, '#FFF6DD') + E(310, 260, 44, 32, '#FFF6DD') + C(194, 262, 17, OL, { stroke: 'none' }) + C(306, 262, 17, OL, { stroke: 'none' }) + C(188, 255, 6, '#fff', { stroke: 'none' }) + C(300, 255, 6, '#fff', { stroke: 'none' });
  s += P('M232,290 Q228,370 210,390 Q250,410 290,390 Q272,370 268,290 Z', WOOD_L, { sw: 5 });
  s += R(170, 520, 160, 90, 40, '#5C2A14') + R(186, 528, 128, 22, 6, '#FFF6DD', { sw: 3 }) + R(186, 578, 128, 22, 6, '#FFF6DD', { sw: 3 }) + L('M218,528 L218,550 M250,528 L250,550 M282,528 L282,550 M218,578 L218,600 M250,578 L250,600 M282,578 L282,600', OL, 3);
  s += L('M250,630 L250,690 M224,640 L230,680 M276,640 L270,680', WOOD_D, 5);
  s += P('M150,170 Q170,140 210,132', 'none', { stroke: '#fff', sw: 8, opacity: 0.35 });
  return svgDoc(500, 760, s);
}
function palmTree() { return svgDoc(760, 1000, palm([400, 980], [470, 600], [370, 300], { frondScale: 1.25, w0: 70, w1: 40 }) + E(400, 982, 150, 16, '#000', { stroke: 'none', opacity: 0.12 })); }
function coconut() {
  let s = E(250, 380, 150, 20, '#000', { stroke: 'none', opacity: 0.13 }) + C(250, 230, 150, '#7A4A22');
  for (let i = 0; i < 26; i++) { const a = i * 0.9, r = 40 + (i * 37) % 100; const x = 250 + Math.cos(a) * r, y = 230 + Math.sin(a) * r * 0.9; s += L(`M${x},${y} l${8 + (i % 3) * 4},${-4 + (i % 4) * 3}`, '#5A3416', 4); }
  s += C(222, 150, 14, '#3B2210', { stroke: 'none' }) + C(270, 140, 14, '#3B2210', { stroke: 'none' }) + C(250, 180, 14, '#3B2210', { stroke: 'none' });
  s += P('M160,150 Q190,110 240,100', 'none', { stroke: '#fff', sw: 10, opacity: 0.25 });
  return svgDoc(500, 410, s);
}
function coconutDrink() {
  let s = E(250, 440, 160, 20, '#000', { stroke: 'none', opacity: 0.13 });
  s += limb('M300,230 L380,40 L420,30', '#FF4F79', 12) + L('M318,190 L340,140', '#fff', 4);
  s += P('M330,90 Q400,10 470,90 Q400,70 330,90 Z', '#FFC400') + L('M400,40 L400,84 M365,60 L388,84 M435,60 L412,84', '#E09A00', 3) + limb('M400,84 L390,230', '#C68B4E', 6, { sw: 3 });
  s += P('M90,230 Q90,430 250,430 Q410,430 410,230 Z', '#7A4A22') + E(250, 230, 160, 34, '#F8F4EA') + E(250, 232, 130, 22, '#EDE3CC', { stroke: 'none' });
  s += L('M130,290 l12,-4 M180,340 l14,-2 M300,360 l12,-6 M360,300 l10,-6 M240,390 l12,0', '#5A3416', 4);
  s += hibiscus(150, 205, 60);
  return svgDoc(500, 470, s);
}
function votingUrn() {
  let s = E(300, 640, 190, 22, '#000', { stroke: 'none', opacity: 0.14 });
  s += P('M190,200 Q168,250 150,330 C112,480 180,620 300,630 C420,620 488,480 450,330 Q432,250 410,200 Z', '#C8693A');
  s += P('M150,360 Q300,392 450,360 L452,410 Q300,442 148,410 Z', '#F3DDB1', { sw: 4 });
  let z = 'M156,386'; for (let i = 1; i <= 14; i++) z += ` L${156 + i * 21},${386 + 4 + (i % 2 ? 10 : -6)}`; s += L(z, '#B4532A', 5);
  [[200, 470], [250, 486], [300, 490], [350, 486], [400, 470], [230, 540], [300, 552], [370, 540]].forEach(([x, y]) => { s += C(x, y, 7, '#F3DDB1', { stroke: 'none' }); });
  s += P('M400,240 Q450,330 438,450 Q420,560 340,610 Q420,520 410,400 Q404,300 380,232 Z', '#000', { stroke: 'none', opacity: 0.12 });
  s += P('M200,280 Q186,330 184,380', 'none', { stroke: '#fff', sw: 10, opacity: 0.3 });
  s += E(300, 190, 135, 36, '#D97B48') + E(300, 190, 108, 23, '#4A2010');
  const papers = G(P('M0,0 L150,0 L150,220 L0,220 Z', '#F3E2B8', { sw: 4 }) + L('M20,40 L120,40 M20,70 L100,70', '#C4A26A', 4), { transform: 'translate(205,40) rotate(-12)' })
    + G(P('M0,0 L140,0 L140,220 L0,220 Z', '#F8EBCB', { sw: 4 }) + L('M20,40 L110,40 M20,70 L90,70', '#C4A26A', 4), { transform: 'translate(300,22) rotate(10)' });
  s += G(papers, { 'clip-path': 'url(#uc)' });
  s += P('M165,190 A135,36 0 0 0 435,190 L408,190 A108,23 0 0 1 192,190 Z', '#D97B48');
  return svgDoc(600, 680, s, '<clipPath id="uc"><rect x="0" y="0" width="600" height="190"/><ellipse cx="300" cy="190" rx="108" ry="23"/></clipPath>');
}
function parchmentPath(w, h, seed) {
  const r = rng(seed); let d = `M30,${30 + r() * 10}`;
  for (let x = 30; x < w - 30; x += 40) d += ` L${x + 40},${24 + r() * 14}`;
  for (let y = 30; y < h - 30; y += 40) d += ` L${w - 26 - r() * 12},${y + 40}`;
  for (let x = w - 30; x > 30; x -= 40) d += ` L${x - 40},${h - 24 - r() * 14}`;
  for (let y = h - 30; y > 30; y -= 40) d += ` L${26 + r() * 12},${y - 40}`;
  return d + ' Z';
}
function voteParchment() {
  const d = parchmentPath(700, 460, 7);
  let s = G(P(d, '#000', { stroke: 'none', opacity: 0.15 }), { transform: 'translate(8,10)' }) + P(d, '#F3E2B8') + G(P(d, 'none', { stroke: '#D9B77A', sw: 18, opacity: 0.5 }), { 'clip-path': 'url(#pc)' });
  s += L('M90,380 L610,380', '#C4A26A', 4, { 'stroke-dasharray': '2 14' });
  return svgDoc(700, 460, s, `<clipPath id="pc"><path d="${d}"/></clipPath>`);
}
function treasureMap() {
  const d = parchmentPath(900, 640, 11);
  let s = G(P(d, '#000', { stroke: 'none', opacity: 0.15 }), { transform: 'translate(8,10)' }) + P(d, '#F1DDAE') + G(P(d, 'none', { stroke: '#C9A266', sw: 26, opacity: 0.45 }), { 'clip-path': 'url(#pc)' });
  for (let i = 0; i < 9; i++) { const x = 90 + (i * 97) % 700, y = 90 + (i * 151) % 460; s += L(`M${x},${y} q10,-10 20,0 q10,10 20,0`, '#6FA7B8', 4); }
  s += blob([[400, 330, 140], [520, 300, 110], [300, 360, 90], [460, 410, 100]], '#E8CC8A', { sw: 4 }) + blob([[400, 320, 110], [510, 300, 84], [320, 350, 64], [450, 390, 76]], '#7DB46C', { sw: 4 });
  s += P('M380,300 L420,250 L460,300 Z', '#8C7A5B', { sw: 4 }) + P('M405,268 L420,250 L435,268 Z', '#fff', { sw: 3 }) + P('M470,320 L500,284 L530,320 Z', '#8C7A5B', { sw: 4 });
  [[340, 330], [360, 380], [560, 330], [480, 360]].forEach(([x, y]) => { s += limb(`M${x},${y} L${x},${y - 22}`, '#6B4220', 4, { sw: 2 }) + C(x, y - 26, 10, '#3E8E41', { sw: 3 }); });
  s += L('M150,520 Q260,560 310,440 Q340,380 430,420 Q500,450 520,380', '#C0392B', 6, { 'stroke-dasharray': '4 16' });
  s += L('M500,360 L540,400 M540,360 L500,400', '#C0392B', 12);
  s += C(150, 520, 12, '#C0392B', { sw: 3 });
  const cx = 760, cy = 150; s += C(cx, cy, 70, 'none', { sw: 4, stroke: '#8B6A35' }) + P(`M${cx},${cy - 80} L${cx + 14},${cy} L${cx},${cy + 80} L${cx - 14},${cy} Z`, '#C0392B', { sw: 3 }) + P(`M${cx - 80},${cy} L${cx},${cy - 14} L${cx + 80},${cy} L${cx},${cy + 14} Z`, '#8B6A35', { sw: 3 }) + C(cx, cy, 8, '#F1DDAE', { sw: 3 });
  s += G(P('M0,0 Q20,-20 40,0 Q60,20 80,0', 'none', { sw: 4 }) + P('M30,-30 L44,-14 L58,-30', 'none', { sw: 4 }), { transform: 'translate(150,170)' });
  return svgDoc(900, 640, s, `<clipPath id="pc"><path d="${d}"/></clipPath>`);
}
function treasureChest() {
  let s = C(350, 300, 300, 'url(#g)', { stroke: 'none' }) + E(350, 560, 250, 24, '#000', { stroke: 'none', opacity: 0.15 });
  s += P('M120,300 L140,120 Q350,60 560,120 L580,300 Z', '#7A4A22') + P('M150,290 L165,140 Q350,90 535,140 L550,290 Z', '#3B2210', { sw: 3 });
  s += limb('M150,128 L132,300 M550,128 L568,300', GOLD, 14, { sw: 4 });
  s += blob([[230, 300, 50], [300, 280, 60], [380, 275, 62], [460, 295, 52], [340, 300, 60]], GOLD, { sw: 4 });
  [[250, 280], [330, 250], [410, 262], [300, 300], [450, 300], [380, 300], [220, 310]].forEach(([x, y]) => { s += E(x, y, 22, 10, '#FFD54F', { sw: 3 }) + L(`M${x - 8},${y} L${x + 8},${y}`, GOLD_D, 2); });
  s += P('M300,240 L330,200 L360,240 L330,260 Z', '#2EC4B6', { sw: 4 }) + C(420, 236, 16, '#E4572E', { sw: 4 });
  s += R(110, 300, 480, 240, 16, '#8B5A2B') + L('M120,380 L580,380 M120,460 L580,460', WOOD_D, 4);
  s += R(110, 300, 480, 34, 10, '#A0692F');
  s += R(150, 300, 36, 240, 4, GOLD, { sw: 4 }) + R(514, 300, 36, 240, 4, GOLD, { sw: 4 });
  s += R(312, 320, 76, 92, 12, GOLD, { sw: 4 }) + C(350, 356, 12, OL, { stroke: 'none' }) + P('M344,360 L356,360 L360,392 L340,392 Z', OL, { stroke: 'none' });
  s += star4(120, 110, 26) + star4(600, 90, 30) + star4(620, 260, 16) + star4(330, 40, 18);
  return svgDoc(700, 600, s, glow('g', '#FFD95A', 0.8));
}
function signpost() {
  let s = E(300, 770, 140, 18, '#000', { stroke: 'none', opacity: 0.14 }) + R(272, 120, 56, 650, 10, '#8B5A2B') + L('M290,200 L290,740', WOOD_D, 3, { opacity: 0.5 });
  const plank = (y, dir) => {
    const d = dir > 0 ? `M60,${y} L470,${y} L540,${y + 70} L470,${y + 140} L60,${y + 140} Z` : `M540,${y} L130,${y} L60,${y + 70} L130,${y + 140} L540,${y + 140} Z`;
    return P(d, WOOD_L) + L(`M80,${y + 40} Q300,${y + 30} 500,${y + 44} M90,${y + 100} Q300,${y + 110} 490,${y + 96}`, shade(WOOD_L, -0.2), 3) + C(300, y + 70, 7, WOOD_D, { sw: 3 });
  };
  s += plank(170, 1) + plank(360, -1);
  s += grass(250, 772, 60, '#4CAF50') + grass(350, 772, 50, '#3E8E41');
  return svgDoc(600, 800, s);
}
function shelter() {
  let s = E(450, 660, 360, 24, '#000', { stroke: 'none', opacity: 0.13 });
  [[170, 1], [730, 1], [260, 0], [640, 0]].forEach(([x]) => { s += bambooPole(x, 330, 660, 28); });
  s += R(120, 430, 660, 40, 8, WOOD) + L('M200,430 L200,470 M300,430 L300,470 M400,430 L400,470 M500,430 L500,470 M600,430 L600,470 M700,430 L700,470', WOOD_D, 3);
  s += P('M450,80 L840,400 L60,400 Z', '#D9B55B');
  for (let r = 0; r < 6; r++) {
    const y = 130 + r * 50, half = (y - 80) * (390 / 320);
    let d = `M${450 - half - 10},${y + 20}`;
    for (let x = 450 - half; x < 450 + half; x += 36) d += ` q18,18 36,0`;
    s += L(d, '#B08A35', 4);
  }
  s += P('M450,80 L840,400 L60,400 Z', 'none', { sw: 6 });
  s += L('M840,400 l-14,30 m-60,-30 l-10,26 m-80,-26 l-8,24 m-140,-24 l-6,22 m-150,-22 l-10,24 m-90,-24 l-12,28', '#B08A35', 5);
  s += limb('M450,60 L450,110', WOOD_D, 16);
  s += bush(110, 640, 50, '#3FA34D') + bush(800, 640, 44, '#4CAF50');
  return svgDoc(900, 700, s);
}
function flag(col, sym) {
  let s = E(150, 790, 90, 12, '#000', { stroke: 'none', opacity: 0.14 }) + bambooPole(150, 60, 790, 24);
  s += P('M162,90 C240,60 310,130 440,96 L440,330 C310,364 240,296 162,326 Z', col);
  s += P('M162,90 C240,60 310,130 440,96 L440,120 C310,154 240,86 162,114 Z', '#fff', { stroke: 'none', opacity: 0.18 });
  s += G(sym, { transform: 'translate(300,212)' });
  s += C(150, 52, 16, GOLD);
  return svgDoc(480, 800, s);
}
const SYM = {
  sun: () => { let s = C(0, 0, 40, '#fff', { sw: 4 }); for (let i = 0; i < 8; i++) { const a = i * Math.PI / 4; s += L(`M${Math.cos(a) * 54},${Math.sin(a) * 54} L${Math.cos(a) * 76},${Math.sin(a) * 76}`, '#fff', 9); } return s; },
  wave: () => L('M-80,-20 q20,-26 40,0 q20,26 40,0 q20,-26 40,0 q20,26 40,0 M-80,30 q20,-26 40,0 q20,26 40,0 q20,-26 40,0 q20,26 40,0', '#fff', 12),
  spiral: () => L('M0,0 m-8,0 a8,8 0 1,1 16,0 a20,20 0 1,1 -40,0 a32,32 0 1,1 64,0 a44,44 0 1,1 -88,0 a56,56 0 1,1 112,0', '#fff', 10),
  leaf: () => P('M-70,40 Q-60,-70 70,-50 Q60,60 -70,40 Z', '#fff', { sw: 4 }) + L('M-60,34 L60,-44', '#3E8E41', 5),
};
function buff(col) {
  const d = 'M60,120 Q300,70 540,120 L540,300 Q300,250 60,300 Z';
  let s = G(P(d, '#000', { stroke: 'none', opacity: 0.12 }), { transform: 'translate(8,12)' }) + P(d, col);
  let inner = '';
  for (let row = 0; row < 3; row++) {
    const y = 150 + row * 60; let z = `M40,${y}`;
    for (let x = 40; x < 560; x += 30) z += ` L${x + 15},${y + (x / 30 % 2 ? -12 : 12)}`;
    inner += L(z, '#fff', 5, { opacity: 0.85 });
    for (let x = 70; x < 560; x += 60) inner += C(x, y + 30, 5, shade(col, -0.35), { stroke: 'none' });
  }
  inner += P('M40,110 Q300,60 560,110 L560,140 Q300,90 40,140 Z', shade(col, -0.25), { stroke: 'none' }) + P('M40,270 Q300,220 560,270 L560,320 Q300,270 40,320 Z', shade(col, -0.25), { stroke: 'none' });
  s += G(inner, { 'clip-path': 'url(#bc)' }) + P(d, 'none');
  return svgDoc(600, 360, s, `<clipPath id="bc"><path d="${d}"/></clipPath>`);
}
function bottle() {
  let s = E(300, 330, 230, 16, '#000', { stroke: 'none', opacity: 0.12 });
  let b = P('M-170,-70 Q-200,-70 -200,-30 L-200,30 Q-200,70 -170,70 L90,70 Q130,70 150,40 L200,20 L200,-20 L150,-40 Q130,-70 90,-70 Z', '#9FE0D0', { 'fill-opacity': 0.75 });
  b += R(-150, -40, 190, 80, 30, '#F3E2B8', { sw: 4 }) + limb('M-60,-42 L-60,42', '#E4572E', 8, { sw: 3 }) + L('M-130,-10 L-80,-10 M-130,12 L-90,12', '#C4A26A', 3);
  b += R(196, -26, 50, 52, 10, '#C68B4E') + L('M-170,-48 L80,-48', '#fff', 8, { opacity: 0.6 });
  s += G(b, { transform: 'translate(290,200) rotate(-14)' });
  return svgDoc(600, 360, s);
}
function compass() {
  let s = E(250, 470, 160, 16, '#000', { stroke: 'none', opacity: 0.12 }) + C(250, 250, 200, GOLD_D) + C(250, 250, 180, GOLD, { sw: 4 }) + C(250, 250, 150, '#FFF6E0') + C(250, 40, 22, 'none', { sw: 14, stroke: GOLD_D });
  for (let i = 0; i < 16; i++) { const a = i * Math.PI / 8, r1 = i % 4 ? 128 : 112; s += L(`M${250 + Math.cos(a) * r1},${250 + Math.sin(a) * r1} L${250 + Math.cos(a) * 142},${250 + Math.sin(a) * 142}`, '#8B6A35', i % 4 ? 3 : 6); }
  s += P('M250,250 m-16,0 L250,128 L266,250 Z', '#E53935', { sw: 4 }) + P('M250,250 m-16,0 L250,372 L266,250 Z', '#3D5A80', { sw: 4 }) + C(250, 250, 14, GOLD, { sw: 4 });
  s += P('M150,150 Q190,110 240,104', 'none', { stroke: '#fff', sw: 10, opacity: 0.6 });
  return svgDoc(500, 500, s);
}
function trophy() {
  let s = C(250, 230, 220, 'url(#g)', { stroke: 'none' }) + E(250, 620, 170, 16, '#000', { stroke: 'none', opacity: 0.13 });
  s += R(110, 520, 280, 90, 12, WOOD) + R(140, 540, 220, 44, 6, GOLD, { sw: 4 });
  s += P('M215,520 L225,420 L275,420 L285,520 Z', GOLD) + R(190, 400, 120, 26, 10, GOLD_D);
  s += L('M120,140 C40,140 50,300 160,300 M380,140 C460,140 450,300 340,300', OL, 34) + L('M120,140 C40,140 50,300 160,300 M380,140 C460,140 450,300 340,300', GOLD, 22);
  s += P('M100,100 L400,100 Q400,370 250,400 Q100,370 100,100 Z', GOLD) + R(92, 88, 316, 30, 12, '#FFD54F');
  s += P('M250,170 L270,220 L322,222 L281,254 L296,306 L250,276 L204,306 L219,254 L178,222 L230,220 Z', '#fff', { sw: 4, opacity: 0.95 });
  s += P('M140,140 Q140,300 210,360', 'none', { stroke: '#fff', sw: 12, opacity: 0.45 });
  s += star4(60, 70, 24) + star4(450, 60, 28) + star4(440, 420, 16);
  return svgDoc(500, 640, s, glow('g', '#FFD95A', 0.6));
}
function parrot() {
  let s = limb('M40,520 Q250,500 470,540', '#7A4A22', 26) + leaf(420, 530, 70, 20, '#3FA34D') + leaf(80, 512, 60, 160, '#4CAF50');
  s += P('M230,440 L190,590 L220,585 L250,450 Z', '#1E88E5') + P('M250,440 L240,600 L268,592 L272,446 Z', '#FFC400') + P('M270,440 L290,585 L312,580 L290,436 Z', '#E53935');
  s += E(260, 340, 95, 130, '#E53935', { transform: 'rotate(-12 260 340)' });
  s += P('M290,260 C380,300 380,420 300,470 C320,400 300,330 260,300 Z', '#1E88E5') + P('M296,300 C350,330 350,400 310,440 C318,390 304,340 280,320 Z', '#FFC400', { sw: 4 });
  s += C(230, 200, 80, '#E53935');
  s += E(210, 196, 34, 28, '#fff') + C(204, 196, 14, OL, { stroke: 'none' }) + C(199, 191, 5, '#fff', { stroke: 'none' });
  s += P('M150,196 C110,190 100,250 140,280 C140,250 150,236 170,232 Z', '#3B3B3B') + P('M160,180 C120,170 104,210 128,236 C140,220 156,214 176,214 Z', '#F2E8D5');
  s += limb('M220,500 L214,528 M286,500 L292,528', '#9E9E9E', 10, { sw: 3 });
  s += P('M230,128 Q240,90 270,96 Q250,110 250,130 Z', '#E53935', { sw: 4 });
  return svgDoc(500, 620, s);
}
function crab() {
  let s = E(250, 350, 170, 16, '#000', { stroke: 'none', opacity: 0.12 });
  [[-1, 0], [-1, 1], [-1, 2], [1, 0], [1, 1], [1, 2]].forEach(([sd, i]) => { s += limb(`M${250 + sd * 90},${270 + i * 18} Q${250 + sd * 160},${250 + i * 30} ${250 + sd * 180},${330 + i * 6}`, '#E8553A', 14, { sw: 4 }); });
  [-1, 1].forEach((sd) => {
    s += limb(`M${250 + sd * 100},${230} Q${250 + sd * 160},${200} ${250 + sd * 170},${150}`, '#E8553A', 18, { sw: 4 });
    const cx = 250 + sd * 170, cy = 140, r = 46, a1 = (-90 + 28 * sd) * Math.PI / 180, a2 = (-90 - 6 * sd) * Math.PI / 180;
    s += P(`M${cx + Math.cos(a2) * 8},${cy + Math.sin(a2) * 8} L${cx + Math.cos(a1) * r},${cy + Math.sin(a1) * r} A${r},${r} 0 1,${sd > 0 ? 1 : 0} ${cx + Math.cos(a2) * r},${cy + Math.sin(a2) * r} Z`, '#F26B4F');
  });
  s += E(250, 260, 120, 76, '#F26B4F') + E(220, 236, 40, 18, '#fff', { stroke: 'none', opacity: 0.3 });
  s += limb('M220,200 L210,150 M280,200 L290,150', '#E8553A', 10, { sw: 4 });
  s += C(210, 140, 24, '#fff') + C(290, 140, 24, '#fff') + C(214, 144, 11, OL, { stroke: 'none' }) + C(286, 144, 11, OL, { stroke: 'none' }) + C(210, 139, 4, '#fff', { stroke: 'none' }) + C(282, 139, 4, '#fff', { stroke: 'none' });
  s += L('M226,280 Q250,302 274,280', OL, 5) + E(195, 270, 13, 7, '#FF9E9E', { stroke: 'none' }) + E(305, 270, 13, 7, '#FF9E9E', { stroke: 'none' });
  return svgDoc(500, 380, s);
}
function fish() {
  let s = P('M380,150 L470,80 Q450,150 470,220 Z', '#FFC400') + P('M80,150 C120,40 320,40 390,150 C320,260 120,260 80,150 Z', '#29B6F6');
  s += P('M200,70 Q240,30 300,64 Q250,70 230,90 Z', '#FFC400', { sw: 4 }) + P('M230,180 Q260,220 300,206 Q270,200 262,170 Z', '#FFC400', { sw: 4 });
  s += L('M250,90 Q280,150 250,210 M300,96 Q326,150 300,204', '#0288D1', 5) + E(200, 190, 70, 20, '#fff', { stroke: 'none', opacity: 0.3 });
  s += C(150, 130, 22, '#fff') + C(146, 132, 11, OL, { stroke: 'none' }) + C(142, 127, 4, '#fff', { stroke: 'none' }) + L('M92,160 Q104,170 116,164', OL, 5);
  return svgDoc(500, 300, s);
}
function hourglass() {
  let s = E(200, 590, 140, 14, '#000', { stroke: 'none', opacity: 0.12 });
  s += P('M110,80 C110,220 180,250 190,300 C180,350 110,380 110,520 L290,520 C290,380 220,350 210,300 C220,250 290,220 290,80 Z', '#DDF3F7', { 'fill-opacity': 0.85 });
  s += P('M140,140 L260,140 C250,210 215,240 200,280 C185,240 150,210 140,140 Z', '#F2C14E', { sw: 3 }) + L('M200,280 L200,470', '#F2C14E', 6) + P('M120,510 Q200,410 280,510 Z', '#F2C14E', { sw: 3 });
  s += L('M134,110 C134,200 160,230 178,260', '#fff', 8, { opacity: 0.7 });
  s += R(70, 40, 260, 44, 14, WOOD) + R(70, 516, 260, 44, 14, WOOD);
  s += limb('M92,84 L92,516 M308,84 L308,516', WOOD_D, 18);
  return svgDoc(400, 610, s);
}
function puzzle() {
  const d = 'M80,120 L170,120 C160,60 260,60 250,120 L340,120 L340,210 C400,200 400,300 340,290 L340,380 L250,380 C260,320 160,320 170,380 L80,380 L80,290 C20,300 20,200 80,210 Z';
  let s = G(P(d, '#000', { stroke: 'none', opacity: 0.15 }), { transform: 'translate(10,12)' }) + P(d, '#E8A33C') + L('M110,150 L150,150', '#fff', 8, { opacity: 0.45 });
  return svgDoc(420, 420, s);
}
function hibiscusProp() { return svgDoc(400, 400, leaf(200, 230, 150, 30, '#3FA34D', { sw: 5 }) + leaf(190, 230, 150, 150, '#4CAF50', { sw: 5 }) + hibiscus(200, 190, 150)); }
function cornerLeaves() {
  let s = '';
  const set = [[[0, 0], [260, 40], [560, 170], 70, '#2E7D32'], [[0, 0], [160, 160], [330, 440], 64, '#388E3C'], [[0, 0], [60, 260], [80, 560], 60, '#2E7D32'], [[0, 0], [300, 120], [470, 330], 70, '#43A047'], [[0, 0], [180, 30], [420, 40], 54, '#4CAF50']];
  set.forEach(([b, c, t, w, col]) => { s += frond(b, c, t, w, col, { n: 30, notch: 0.55 }); });
  s += frond([0, 0], [120, 200], [200, 330], 80, '#66BB6A', { notch: 0, veins: true, peak: 0.45 });
  s += hibiscus(150, 120, 70) + hibiscus(280, 80, 46, '#FF7043');
  return svgDoc(640, 640, s);
}
function vinesTop() {
  let s = '';
  const r = rng(5);
  for (let i = 0; i < 26; i++) { const x = i * 78 - 20; s += frond([x, -30], [x + 40, 60], [x + 30 + r() * 60, 120 + r() * 80], 40, i % 2 ? '#2E7D32' : '#43A047', { notch: 0.4, n: 20 }); }
  [[120, 330], [380, 240], [700, 380], [1010, 260], [1290, 350], [1560, 230], [1820, 320]].forEach(([x, len], k) => {
    const d = `M${x},0 C${x + 40},${len * 0.3} ${x - 40},${len * 0.6} ${x + 10},${len}`;
    s += limb(d, '#6D8B3A', 8, { sw: 3 });
    for (let j = 1; j <= 6; j++) {
      const t = j / 7, x0 = (1 - t) ** 3 * x + 3 * (1 - t) ** 2 * t * (x + 40) + 3 * (1 - t) * t * t * (x - 40) + t ** 3 * (x + 10), y0 = len * t;
      s += leaf(x0, y0, 46, j % 2 ? 20 : 160, j % 2 ? '#4CAF50' : '#66BB6A');
    }
    if (k % 2 === 0) s += hibiscus(x + 10, len + 12, 34, k % 4 ? '#FF7043' : '#FF4F79');
  });
  return svgDoc(1920, 440, s);
}
function bushesBottom() {
  let s = '';
  const r = rng(9);
  for (let i = 0; i < 14; i++) { const x = i * 150 + r() * 40; s += bush(x, 260 - r() * 30, 70 + r() * 30, i % 2 ? '#2E7D32' : '#388E3C'); }
  for (let i = 0; i < 18; i++) { const x = i * 112 + 30; s += bush(x, 300, 50 + r() * 16, i % 2 ? '#43A047' : '#4CAF50'); }
  for (let i = 0; i < 24; i++) s += grass(i * 84 + 20, 330, 50 + r() * 40, i % 2 ? '#66BB6A' : '#7CB342');
  [[200, 230], [640, 250], [1100, 220], [1500, 250], [1800, 236]].forEach(([x, y], k) => { s += hibiscus(x, y, 36, k % 2 ? '#FF7043' : '#FF4F79'); });
  return svgDoc(1920, 330, s);
}
function rock() { return svgDoc(500, 320, E(250, 290, 220, 18, '#000', { stroke: 'none', opacity: 0.13 }) + P('M40,280 Q30,180 110,140 Q160,60 260,70 Q380,60 430,150 Q480,210 460,280 Z', '#9AA0A6') + P('M90,170 Q140,110 200,110', 'none', { stroke: '#fff', sw: 10, opacity: 0.35 }) + P('M300,120 Q360,150 380,230', 'none', { stroke: '#6B7178', sw: 5 }) + bush(80, 270, 40, '#4CAF50') + grass(420, 284, 50, '#66BB6A')); }

module.exports = () => {
  const D = '04-props';
  const list = [
    ['torch-lit', 'לפיד דולק', torchLit(), 300, 800],
    ['torch-snuffed', 'לפיד כבוי (הודחת!)', torchSnuffed(), 300, 800],
    ['campfire', 'מדורה', campfire(), 700, 600],
    ['immunity-necklace', 'שרשרת חסינות', necklace(), 600, 760],
    ['hidden-idol-glowing', 'פסל חסינות נסתר (זוהר)', idol(true), 500, 680],
    ['hidden-idol', 'פסל חסינות נסתר', idol(false), 500, 680],
    ['tiki-mask', 'מסכת טיקי', tikiMask(), 500, 760],
    ['voting-urn', 'כד הצבעות', votingUrn(), 600, 680],
    ['vote-parchment', 'פתק הצבעה ריק (לכתוב שם)', voteParchment(), 700, 460],
    ['treasure-map', 'מפת אוצר', treasureMap(), 900, 640],
    ['treasure-chest', 'תיבת אוצר', treasureChest(), 700, 600],
    ['signpost', 'שלט כיוונים ריק', signpost(), 600, 800],
    ['shelter', 'מחסה / בקתה', shelter(), 900, 700],
    ['palm-tree', 'עץ דקל', palmTree(), 760, 1000],
    ['coconut', 'קוקוס', coconut(), 500, 410],
    ['coconut-drink', 'משקה קוקוס', coconutDrink(), 500, 470],
    ['flag-orange', 'דגל שבט כתום', flag('#FF7A1A', SYM.sun()), 480, 800],
    ['flag-blue', 'דגל שבט כחול', flag('#1E88E5', SYM.wave()), 480, 800],
    ['flag-purple', 'דגל שבט סגול (איחוד)', flag('#8E44AD', SYM.spiral()), 480, 800],
    ['flag-green', 'דגל שבט ירוק', flag('#2EAF5A', SYM.leaf()), 480, 800],
    ['buff-orange', 'באף כתום', buff('#FF7A1A'), 600, 360],
    ['buff-blue', 'באף כחול', buff('#1E88E5'), 600, 360],
    ['buff-purple', 'באף סגול', buff('#8E44AD'), 600, 360],
    ['buff-green', 'באף ירוק', buff('#2EAF5A'), 600, 360],
    ['message-in-bottle', 'מכתב בבקבוק', bottle(), 600, 360],
    ['compass', 'מצפן', compass(), 500, 500],
    ['trophy', 'גביע המנצח', trophy(), 500, 640],
    ['hourglass', 'שעון חול', hourglass(), 400, 610],
    ['puzzle-piece', 'חלק פאזל (משימה)', puzzle(), 420, 420],
    ['parrot', 'תוכי', parrot(), 500, 620],
    ['crab', 'סרטן', crab(), 500, 380],
    ['fish', 'דג', fish(), 500, 300],
    ['hibiscus-flower', 'פרח היביסקוס', hibiscusProp(), 400, 400],
    ['rock', 'סלע עם צמחייה', rock(), 500, 320],
    ['corner-leaves', 'עלים לפינת שקופית', cornerLeaves(), 640, 640],
    ['vines-top-border', 'גפנים תלויות – גבול עליון', vinesTop(), 1920, 440],
    ['bushes-bottom-border', 'שיחים – גבול תחתון', bushesBottom(), 1920, 330],
  ];
  return list.map(([name, he, svg, w, h]) => ({ dir: D, name, he, svg, w, h, scale: w >= 1920 ? 1 : 1.5 }));
};
module.exports.parts = { torchLit, campfire, shelter, votingUrn, flag, SYM, signpost, rock, treasureChest };
