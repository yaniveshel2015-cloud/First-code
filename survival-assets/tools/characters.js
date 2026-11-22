// Cartoon castaway characters: 8 contestants + host, 10 poses/expressions each, + round avatars.
const { OL, SW, svgDoc, P, C, E, R, L, G, limb, blob, shade, flame, star4, qpt } = require('./common');

const SKIN = { light: '#F8D5B8', fair: '#EDBE96', medium: '#D69C6A', tan: '#B97A4A', brown: '#8C5331', dark: '#5C3420' };
const HAIR = { black: '#2B2120', brown: '#6B4226', blond: '#EDBB4C', ginger: '#C8562E', gray: '#BDB7B0', darkbrown: '#46291A' };
const TRIBE = { orange: '#FF7A1A', blue: '#1E88E5', purple: '#8E44AD' };

const W = 600, H = 900;
const HX = 300, HY = 258, HRX = 120, HRY = 114; // head ellipse

// ---------- hair ----------
function hair(style, col) {
  const dk = shade(col, -0.25);
  const front = (d) => P(d, col);
  const capShort = 'M182,262 C170,170 232,128 302,128 C374,128 432,172 418,262 C410,232 394,208 366,198 C350,214 318,214 296,203 C270,214 242,212 226,205 C204,220 188,240 182,262 Z';
  switch (style) {
    case 'short': return { back: '', front: front(capShort) + L('M296,150 Q286,175 296,203', dk, 4) };
    case 'spiky': return { back: '', front: front('M182,262 L168,196 L200,204 L196,144 L240,170 L258,112 L294,156 L326,104 L348,158 L392,122 L392,186 L432,180 L418,262 C406,226 382,208 352,200 C330,212 280,212 250,202 C220,210 194,232 182,262 Z') };
    case 'long': return {
      back: P('M176,250 C168,150 236,116 300,116 C364,116 432,150 424,250 C430,330 440,400 448,452 Q372,482 300,472 Q228,482 152,452 C160,400 170,330 176,250 Z', col),
      front: front('M182,264 C176,168 240,126 300,126 C362,126 424,168 418,264 C406,226 384,204 354,195 C330,224 282,234 238,228 C212,234 194,248 182,264 Z') + L('M354,196 C340,170 320,150 300,140', dk, 4),
    };
    case 'bob': return {
      back: P('M172,250 C164,150 236,118 300,118 C364,118 436,150 428,250 C432,300 438,340 440,372 Q420,388 396,380 L204,380 Q180,388 160,372 C162,340 168,300 172,250 Z', col),
      front: front('M182,262 C176,166 240,126 300,126 C360,126 424,166 418,262 C414,236 410,214 404,206 L196,206 C190,214 186,236 182,262 Z') + L('M240,206 L242,184 M300,206 L300,180 M360,206 L358,184', dk, 4),
    };
    case 'ponytail': return {
      back: P('M394,176 C470,156 520,240 494,334 C482,384 454,404 440,392 C458,342 450,292 410,250 Z', col) + C(410, 196, 14, '#E84A5F'),
      front: front('M182,264 C176,168 240,126 300,126 C362,126 424,168 418,264 C406,226 384,204 354,195 C330,224 282,234 238,228 C212,234 194,248 182,264 Z'),
    };
    case 'bun': return {
      back: C(300, 128, 48, col) + L('M268,118 Q300,100 332,118', dk, 4),
      front: front('M182,262 C176,170 236,134 300,134 C364,134 424,170 418,262 C402,214 352,190 300,194 C248,190 198,214 182,262 Z') + L('M300,142 Q296,168 300,193', dk, 4),
    };
    case 'curly': return {
      back: blob([[300, 150, 72], [222, 166, 60], [378, 166, 60], [176, 226, 52], [424, 226, 52], [168, 290, 44], [432, 290, 44], [248, 118, 52], [352, 118, 52], [170, 340, 36], [430, 340, 36]], col),
      front: blob([[208, 222, 30], [246, 196, 32], [292, 184, 33], [338, 188, 33], [380, 206, 31], [408, 236, 26], [196, 252, 24]], col)
        + C(262, 160, 10, shade(col, 0.15), { stroke: 'none' }) + C(330, 150, 8, shade(col, 0.15), { stroke: 'none' }),
    };
    case 'hat': return { back: '', front: front('M186,262 C182,226 190,200 206,190 L394,190 C410,200 418,226 414,262 C404,236 394,222 380,214 L220,214 C206,222 196,236 186,262 Z') };
    case 'bald': default: return { back: '', front: E(250, 178, 28, 12, '#FFFFFF', { stroke: 'none', opacity: 0.35, transform: 'rotate(-20 250 178)' }) };
  }
}

// ---------- face ----------
const EYE_L = [258, 270], EYE_R = [342, 270];
function eyes(kind, lashes) {
  const out = [];
  const std = (rx, ry, hl) => [EYE_L, EYE_R].map(([x, y]) => E(x, y, rx, ry, OL, { stroke: 'none' }) + C(x - 4, y - 6, hl, '#fff', { stroke: 'none' }) + C(x + 4, y + 5, hl * 0.45, '#fff', { stroke: 'none' })).join('');
  switch (kind) {
    case 'big': out.push(std(15, 20, 6)); break;
    case 'closed': out.push(L('M244,276 Q258,258 272,276', OL, 7) + L('M328,276 Q342,258 356,276', OL, 7)); break;
    case 'sly': out.push([EYE_L, EYE_R].map(([x, y]) => P(`M${x - 13},${y - 2} A13,13 0 0 0 ${x + 13},${y - 2} Z`, OL, { stroke: 'none' }) + C(x - 3, y + 3, 3.5, '#fff', { stroke: 'none' })).join('')
      + L('M240,266 L276,264', OL, 6) + L('M324,264 L360,266', OL, 6)); break;
    case 'up': out.push([EYE_L, EYE_R].map(([x, y]) => E(x + 4, y - 4, 12, 16, OL, { stroke: 'none' }) + C(x + 1, y - 10, 4.5, '#fff', { stroke: 'none' })).join('')); break;
    case 'narrow': out.push(std(12, 13, 4)); break;
    default: out.push(std(12, 16, 4.5));
  }
  if (lashes && kind !== 'closed') out.push(L('M246,262 L236,253 M249,257 L242,247', OL, 4) + L('M354,262 L364,253 M351,257 L358,247', OL, 4));
  return out.join('');
}
const BROWS = {
  normal: 'M240,238 Q257,228 274,236 M326,236 Q343,228 360,238',
  raised: 'M238,222 Q257,208 276,220 M324,220 Q343,208 362,222',
  angry: 'M238,230 L276,247 M362,230 L324,247',
  sad: 'M240,246 L274,232 M360,246 L326,232',
  think: 'M238,224 Q257,212 276,222 M326,242 L362,238',
  sly: 'M240,238 L274,246 M326,232 Q344,222 362,230',
};
function mouth(kind) {
  const DK = '#7A1F1F';
  switch (kind) {
    case 'open': return G(P('M264,312 Q300,316 336,312 Q334,360 300,362 Q266,360 264,312 Z', DK)
      + P('M270,316 Q300,320 330,316 L328,328 Q300,333 272,328 Z', '#fff', { sw: 0, stroke: 'none' })
      + E(300, 350, 17, 8, '#E86A6A', { stroke: 'none' }) + P('M264,312 Q300,316 336,312 Q334,360 300,362 Q266,360 264,312 Z', 'none'));
    case 'talk': return P('M276,318 Q300,322 324,318 Q320,346 300,347 Q280,346 276,318 Z', DK) + E(300, 338, 10, 5, '#E86A6A', { stroke: 'none' });
    case 'o': return E(300, 332, 13, 17, DK);
    case 'frown': return L('M274,340 Q300,318 326,340', OL, 6);
    case 'grit': return R(272, 318, 56, 22, 9, '#fff') + L('M274,329 L326,329 M286,320 L286,338 M300,320 L300,338 M314,320 L314,338', OL, 3);
    case 'smirk': return L('M276,326 Q302,334 330,312', OL, 6) + L('M326,318 L336,314', OL, 4);
    case 'flat': return L('M284,330 Q300,325 318,331', OL, 6);
    case 'smile': default: return L('M270,318 Q300,344 330,318', OL, 6);
  }
}
const EXPR = {
  happy: { eyes: 'normal', brows: 'normal', mouth: 'smile' },
  excited: { eyes: 'closed', brows: 'raised', mouth: 'open' },
  surprised: { eyes: 'big', brows: 'raised', mouth: 'o' },
  angry: { eyes: 'narrow', brows: 'angry', mouth: 'grit' },
  sad: { eyes: 'normal', brows: 'sad', mouth: 'frown' },
  thinking: { eyes: 'up', brows: 'think', mouth: 'flat' },
  sly: { eyes: 'sly', brows: 'sly', mouth: 'smirk' },
  talking: { eyes: 'normal', brows: 'normal', mouth: 'talk' },
};

// ---------- hands ----------
function hand(x, y, ang, type, skin, thumbSide = 1) {
  const r = (a, len) => [x + Math.cos((a * Math.PI) / 180) * len, y + Math.sin((a * Math.PI) / 180) * len];
  let s = '';
  if (type === 'point') {
    const [fx, fy] = r(ang, 44);
    s += limb(`M${x},${y} L${fx},${fy}`, skin, 13);
    const [tx, ty] = r(ang - 80 * thumbSide, 22);
    s += limb(`M${x},${y} L${tx},${ty}`, skin, 12);
  } else if (type === 'open') {
    [-38, -13, 12, 36].forEach((d, i) => { const [fx, fy] = r(ang + d, i === 0 || i === 3 ? 33 : 38); s += limb(`M${x},${y} L${fx},${fy}`, skin, 12); });
    const [tx, ty] = r(ang + 78 * thumbSide, 28); s += limb(`M${x},${y} L${tx},${ty}`, skin, 12);
  }
  s += C(x, y, type === 'open' ? 22 : 21, skin);
  if (type === 'fist') { const [kx, ky] = r(ang, 10); s += L(`M${kx - 8},${ky - 4} Q${kx},${ky + 4} ${kx + 8},${ky - 4}`, shade(skin, -0.3), 3); }
  return s;
}

// ---------- poses ----------
// each arm: d (path), hand [x,y,angle,type,thumbSide], layer back|front|top
const SL = [222, 415], SR = [378, 415];
const POSES = {
  neutral: { L: { d: 'M222,415 Q178,500 186,590', h: [186, 590, 95, 'fist'], layer: 'back' }, R: { d: 'M378,415 Q422,500 414,590', h: [414, 590, 85, 'fist'], layer: 'back' } },
  wave: { L: { d: 'M222,415 Q178,500 186,590', h: [186, 590, 95, 'fist'], layer: 'back' }, R: { d: 'M378,415 Q478,420 470,272', h: [470, 272, -92, 'open', 1], layer: 'back' }, fx: 'wave' },
  celebrate: { L: { d: 'M222,415 Q128,400 140,228', h: [140, 228, -95, 'fist'], layer: 'back' }, R: { d: 'M378,415 Q472,400 460,228', h: [460, 228, -85, 'fist'], layer: 'back' }, fx: 'sparkle' },
  shocked: { L: { d: 'M222,415 Q140,500 210,334', h: [210, 334, -60, 'open', -1], layer: 'top' }, R: { d: 'M378,415 Q460,500 390,334', h: [390, 334, -120, 'open', 1], layer: 'top' }, fx: 'shock' },
  hips: { L: { d: 'M222,415 Q140,470 214,562', h: [214, 562, 30, 'fist'], layer: 'back' }, R: { d: 'M378,415 Q460,470 386,562', h: [386, 562, 150, 'fist'], layer: 'back' } },
  sad: { L: { d: 'M222,415 Q196,505 202,594', h: [202, 594, 92, 'fist'], layer: 'back' }, R: { d: 'M378,415 Q404,505 398,594', h: [398, 594, 88, 'fist'], layer: 'back' } },
  think: { L: { d: 'M222,415 L208,512 L346,514', h: [346, 514, 0, 'fist'], layer: 'front' }, R: { d: 'M378,415 L396,514 L330,384', h: [330, 384, -115, 'fist'], layer: 'top' }, fx: 'question' },
  scheme: { L: { d: 'M222,415 Q184,504 280,490', h: [280, 490, -10, 'fist'], layer: 'front' }, R: { d: 'M378,415 Q416,504 320,490', h: [320, 490, 190, 'fist'], layer: 'front' }, fx: 'rub' },
  point: { L: { d: 'M222,415 Q178,500 186,590', h: [186, 590, 95, 'fist'], layer: 'back' }, R: { d: 'M378,415 Q456,446 528,404', h: [528, 404, -28, 'point', 1], layer: 'back' } },
  torch: { L: { d: 'M222,415 Q178,500 186,590', h: [186, 590, 95, 'fist'], layer: 'back' }, R: { d: 'M378,415 Q466,486 470,548', h: [470, 548, 90, 'fist'], layer: 'front' }, torch: true },
};

function fx(kind) {
  switch (kind) {
    case 'wave': return L('M512,236 Q530,272 512,308 M534,216 Q560,272 534,328', OL, 5);
    case 'sparkle': return star4(92, 180, 26) + star4(512, 166, 30) + star4(480, 300, 16) + star4(118, 310, 16) + star4(300, 70, 20);
    case 'shock': return L('M196,122 L174,96 M248,98 L238,66 M300,92 L300,58 M352,98 L362,66 M404,122 L426,96', OL, 6)
      + P('M152,196 Q166,222 152,236 Q138,222 152,196 Z', '#8FD3FF', { sw: 4 });
    case 'question': return G(L('M-16,-22 Q-16,-44 4,-44 Q24,-44 24,-26 Q24,-12 6,-6 L6,8', OL, 22) + L('M-16,-22 Q-16,-44 4,-44 Q24,-44 24,-26 Q24,-12 6,-6 L6,8', '#FFE14D', 12) + C(6, 30, 11, '#FFE14D'), { transform: 'translate(462,150) rotate(12)' });
    case 'rub': return L('M246,462 L232,450 M244,512 L228,520 M354,462 L368,450 M356,512 L372,520', OL, 5);
    case 'anger': return G(['M-6,-20 Q-6,-6 -20,-6', 'M6,-20 Q6,-6 20,-6', 'M-6,20 Q-6,6 -20,6', 'M6,20 Q6,6 20,6'].map((d) => L(d, '#E53935', 7)).join(''), { transform: 'translate(176,150)' });
    case 'tear': return P('M256,292 Q268,316 256,326 Q244,316 256,292 Z', '#8FD3FF', { sw: 4 }) + P('M160,196 Q172,218 160,230 Q148,218 160,196 Z', '#8FD3FF', { sw: 4 });
    default: return '';
  }
}

function torchProp(x, top) {
  // pole + basket + flame held at (x, ~548)
  let s = limb(`M${x},${top + 70} L${x},${top + 470}`, '#C9A15A', 18);
  for (let y = top + 140; y < top + 470; y += 90) s += L(`M${x - 9},${y} L${x + 9},${y}`, '#8B6A35', 4);
  s += flame(x, top + 22, 150);
  s += P(`M${x - 42},${top} L${x + 42},${top} L${x + 22},${top + 72} L${x - 22},${top + 72} Z`, '#A0692F');
  s += L(`M${x - 34},${top + 22} L${x + 34},${top + 22} M${x - 28},${top + 46} L${x + 28},${top + 46} M${x - 12},${top} L${x - 6},${top + 72} M${x + 12},${top} L${x + 6},${top + 72}`, '#6B4220', 4);
  return s;
}

function buffHead(col) {
  const band = 'M181,250 Q300,194 419,250 L417,214 Q300,156 183,214 Z';
  let zig = '';
  for (let i = 0; i <= 16; i++) { const [x, y] = qpt([182, 232], [300, 175], [418, 232], i / 16); zig += (i ? ' L' : 'M') + `${x.toFixed(1)},${(y + (i % 2 ? -6 : 6)).toFixed(1)}`; }
  return P('M412,226 Q452,206 474,236 Q448,236 430,248 Z', shade(col, -0.12)) + P('M412,238 Q448,262 452,296 Q432,280 414,260 Z', shade(col, -0.12))
    + P(band, col) + L(zig, '#FFFFFF', 4, { opacity: 0.85 }) + C(414, 234, 13, shade(col, -0.12));
}
function buffNeck(col) {
  let dots = '';
  [[280, 398], [300, 404], [320, 398], [300, 424], [292, 412], [308, 412]].forEach(([x, y]) => { dots += C(x, y, 3.5, '#fff', { stroke: 'none', opacity: 0.85 }); });
  return P('M266,372 Q300,390 334,372 L342,398 Q300,420 258,398 Z', col) + P('M272,400 Q300,414 328,400 L300,446 Z', col) + dots;
}
function hat() {
  return P('M118,196 Q300,140 482,196 Q470,226 300,222 Q130,226 118,196 Z', '#C9B07A')
    + P('M206,196 C204,120 246,88 300,88 C354,88 396,120 394,196 Q300,180 206,196 Z', '#D8C08A')
    + P('M206,196 C205,180 205,170 207,160 Q300,146 393,160 C395,170 395,180 394,196 Q300,180 206,196 Z', '#6B4220')
    + L('M300,96 Q292,130 300,170', shade('#D8C08A', -0.2), 4);
}

function character(spec, poseKey, exprKey, opts = {}) {
  const pose = POSES[poseKey], ex = EXPR[exprKey];
  const skin = spec.skin, top = spec.top, hr = hair(spec.hair, spec.hairColor);
  const defs = `<clipPath id="hc"><ellipse cx="${HX}" cy="${HY}" rx="${HRX}" ry="${HRY}"/></clipPath>`;
  const arm = (a) => {
    let s = limb(a.d, skin, 38);
    if (top.type !== 'tank') {
      const m = a.d.match(/^M([\d.]+),([\d.]+)\s*[QL]\s*([\d.]+),([\d.]+)/);
      const sx = +m[1], sy = +m[2], ex2 = +m[3], ey = +m[4];
      const len = top.type === 'shirt' ? 0.5 : 0.32;
      s += limb(`M${sx},${sy} L${sx + (ex2 - sx) * len},${sy + (ey - sy) * len}`, top.color, 54);
    }
    const [x, y, ang, t, ts] = a.h; s += hand(x, y, ang, t, skin, ts);
    if (spec.buff.place === 'arm' && a === pose.L) s += '';
    return s;
  };
  const arms = (layer) => ['L', 'R'].filter((k) => pose[k].layer === layer).map((k) => arm(pose[k])).join('');
  let s = E(300, 864, 150, 18, '#000', { stroke: 'none', opacity: 0.13 });
  s += hr.back;
  s += arms('back');
  // legs + feet
  const legCol = spec.pants ? spec.pants : skin;
  s += limb('M262,670 L256,838', legCol, 46) + limb('M338,670 L344,838', legCol, 46);
  if (spec.pants) {
    s += E(246, 852, 44, 18, '#4A3222') + E(354, 852, 44, 18, '#4A3222');
  } else {
    s += E(246, 858, 42, 13, '#5A4636', { sw: 4 }) + E(354, 858, 42, 13, '#5A4636', { sw: 4 });
    s += E(248, 848, 36, 16, skin) + E(352, 848, 36, 16, skin);
    s += L('M226,846 Q248,830 270,846 M330,846 Q352,830 374,846', spec.strap || '#E84A5F', 6);
  }
  // shorts / hips
  s += P(spec.pants ? 'M218,584 L382,584 L390,690 L310,690 L300,640 L290,690 L210,690 Z' : 'M218,584 L382,584 L394,700 Q350,708 310,700 L300,646 L290,700 Q250,708 206,700 Z', spec.shorts);
  s += L('M222,604 L378,604', shade(spec.shorts, -0.25), 4);
  // neck
  s += R(278, 330, 44, 80, 12, skin);
  // torso
  const torso = 'M228,392 Q300,378 372,392 Q398,402 396,435 L384,598 Q300,612 216,598 L204,435 Q202,402 228,392 Z';
  if (top.type === 'tank') {
    s += P(torso, skin);
    s += P('M246,390 L264,390 Q300,432 336,390 L354,390 Q390,412 394,470 L384,598 Q300,612 216,598 L206,470 Q210,412 246,390 Z', top.color);
  } else {
    s += P(torso, top.color);
    s += P('M266,390 Q300,424 334,390 Z', skin, { stroke: 'none' }) + L('M266,390 Q300,424 334,390', OL, SW);
  }
  if (top.stripe) s += P('M207,470 Q300,486 393,470 L391,500 Q300,516 209,500 Z', top.stripe, { sw: 4 });
  if (top.type === 'shirt') {
    s += P('M262,388 L300,424 L282,448 Z', shade(top.color, 0.25)) + P('M338,388 L300,424 L318,448 Z', shade(top.color, 0.25));
    [460, 500, 540, 578].forEach((y) => { s += C(300, y, 5, shade(top.color, -0.35), { stroke: 'none' }); });
    s += L('M300,424 L300,604', shade(top.color, -0.3), 3);
    s += R(330, 450, 36, 32, 4, 'none', { sw: 3, stroke: shade(top.color, -0.3) });
  }
  s += P('M368,400 Q392,410 392,440 L382,596 Q360,602 352,600 Z', '#000', { stroke: 'none', opacity: 0.08 });
  if (spec.buff.place === 'neck') s += buffNeck(spec.buff.color);
  if (pose.torch) s += torchProp(470, 290);
  s += arms('front');
  // head
  s += C(182, 276, 22, skin) + C(418, 276, 22, skin) + L('M178,268 Q188,276 180,286', shade(skin, -0.3), 3.5) + L('M422,268 Q412,276 420,286', shade(skin, -0.3), 3.5);
  s += E(HX, HY, HRX, HRY, skin);
  s += G(E(HX + 34, HY + 38, HRX, HRY, '#000', { stroke: 'none', opacity: 0.0 }), { 'clip-path': 'url(#hc)' });
  if (spec.facial === 'beard') s += P('M184,272 C186,352 240,394 300,394 C360,394 414,352 416,272 C404,318 380,340 352,336 C340,316 260,316 248,336 C220,340 196,318 184,272 Z', spec.facialColor || spec.hairColor);
  s += E(226, 304, 19, 10, '#FF6F6F', { stroke: 'none', opacity: 0.32 }) + E(374, 304, 19, 10, '#FF6F6F', { stroke: 'none', opacity: 0.32 });
  s += eyes(ex.eyes, spec.lashes);
  s += L(BROWS[ex.brows], spec.browColor || shade(spec.hairColor === HAIR.blond ? HAIR.brown : spec.hairColor, -0.2), 7);
  s += L('M293,292 Q300,301 307,292', shade(skin, -0.45), 4.5);
  s += mouth(ex.mouth);
  if (spec.facial === 'mustache' || spec.facial === 'beard') s += P('M266,310 Q282,296 300,306 Q318,296 334,310 Q318,320 300,313 Q282,320 266,310 Z', spec.facialColor || spec.hairColor, { sw: 4 });
  s += hr.front;
  if (spec.buff.place === 'head') s += buffHead(spec.buff.color);
  if (spec.hat) s += hat();
  if (spec.earring) s += C(184, 304, 6, '#FFD23F', { sw: 3 });
  s += arms('top');
  s += fx(pose.fx);
  if (exprKey === 'angry') s += fx('anger');
  if (exprKey === 'sad') s += fx('tear');
  return svgDoc(W, H, s, defs);
}

// round portrait (re-uses the happy standing character, cropped to the head)
function avatar(spec) {
  const full = character(spec, 'neutral', 'happy');
  const inner = full.replace(/^<svg[^>]*>/, '').replace(/<\/svg>$/, '');
  const c = spec.buff.color;
  return `<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 400 400" width="400" height="400"><defs><clipPath id="av"><circle cx="200" cy="200" r="182"/></clipPath></defs>`
    + C(200, 200, 186, c, { sw: 12 })
    + `<g clip-path="url(#av)">` + C(200, 200, 182, shade(c, 0.55), { stroke: 'none' }) + `<g transform="translate(200,206) scale(0.9) translate(-300,-270)">${inner}</g></g>`
    + C(200, 200, 186, 'none', { sw: 12 }) + C(200, 200, 176, 'none', { sw: 4, stroke: '#fff', opacity: 0.8 }) + `</svg>`;
}

const CAST = [
  { id: '01-orange-tom', he: 'טום (שבט כתום)', skin: SKIN.medium, hair: 'short', hairColor: HAIR.black, top: { type: 'tank', color: '#FFFFFF' }, shorts: '#C8A165', buff: { color: TRIBE.orange, place: 'head' } },
  { id: '02-blue-maya', he: 'מאיה (שבט כחול)', skin: SKIN.light, hair: 'long', hairColor: HAIR.blond, lashes: true, top: { type: 'tank', color: '#FF8A7A' }, shorts: '#4A6FA5', buff: { color: TRIBE.blue, place: 'head' } },
  { id: '03-blue-dan', he: 'דן (שבט כחול)', skin: SKIN.dark, hair: 'bald', hairColor: HAIR.black, facial: 'beard', top: { type: 'tank', color: '#3FA34D' }, shorts: '#7D7D7D', buff: { color: TRIBE.blue, place: 'neck' } },
  { id: '04-orange-noa', he: 'נועה (שבט כתום)', skin: SKIN.brown, hair: 'curly', hairColor: HAIR.black, lashes: true, earring: true, top: { type: 'tank', color: '#FFC93C' }, shorts: '#6B7A3A', buff: { color: TRIBE.orange, place: 'head' } },
  { id: '05-blue-ori', he: 'אורי (שבט כחול)', skin: SKIN.light, hair: 'spiky', hairColor: HAIR.ginger, top: { type: 'tee', color: '#9AA5B1', stripe: '#1E88E5' }, shorts: '#2F3E5C', buff: { color: TRIBE.blue, place: 'head' } },
  { id: '06-orange-shira', he: 'שירה (שבט כתום)', skin: SKIN.tan, hair: 'ponytail', hairColor: HAIR.brown, lashes: true, top: { type: 'tank', color: '#8E5BD6' }, shorts: '#C8A165', buff: { color: TRIBE.orange, place: 'neck' } },
  { id: '07-orange-moshe', he: 'משה (שבט כתום)', skin: SKIN.fair, hair: 'short', hairColor: HAIR.gray, facial: 'mustache', top: { type: 'tee', color: '#2BB3A3' }, shorts: '#5B4636', buff: { color: TRIBE.orange, place: 'head' } },
  { id: '08-blue-lea', he: 'לאה (שבט כחול)', skin: SKIN.medium, hair: 'bun', hairColor: HAIR.darkbrown, lashes: true, earring: true, top: { type: 'tee', color: '#FFFFFF', stripe: '#FF7A1A' }, shorts: '#6B7A3A', buff: { color: TRIBE.blue, place: 'neck' } },
  { id: '09-host', he: 'המנחה', skin: SKIN.fair, hair: 'hat', hairColor: HAIR.darkbrown, hat: true, top: { type: 'shirt', color: '#7FA7C9' }, shorts: '#C8B48A', pants: '#C8B48A', buff: { color: '#C9B07A', place: 'none' } },
];

const VARIANTS = [
  ['00-standing', 'neutral', 'happy', 'עומד/ת ומחייך/ת'],
  ['01-wave', 'wave', 'happy', 'מנופף/ת לשלום'],
  ['02-celebrate', 'celebrate', 'excited', 'חוגג/ת ניצחון'],
  ['03-shocked', 'shocked', 'surprised', 'בהלם'],
  ['04-angry', 'hips', 'angry', 'כועס/ת ונחוש/ה'],
  ['05-sad', 'sad', 'sad', 'עצוב/ה'],
  ['06-thinking', 'think', 'thinking', 'חושב/ת'],
  ['07-scheming', 'scheme', 'sly', 'זומם/ת תוכנית'],
  ['08-presenting', 'point', 'talking', 'מצביע/ה ומציג/ה'],
  ['09-torch', 'torch', 'happy', 'מחזיק/ה לפיד'],
];

module.exports = () => {
  const out = [];
  for (const c of CAST) {
    for (const [vid, pose, ex, vhe] of VARIANTS) {
      out.push({ dir: `01-characters/${c.id}`, name: vid, w: W, h: H, scale: 1.5, he: `${c.he} – ${vhe}`, svg: character(c, pose, ex) });
    }
    out.push({ dir: '01-characters/avatars', name: c.id, w: 400, h: 400, scale: 1.5, he: `${c.he} – תמונת פרופיל עגולה`, svg: avatar(c) });
  }
  return out;
};
module.exports.CAST = CAST;
