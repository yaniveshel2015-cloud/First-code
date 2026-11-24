"""One-off layout fixes for the SketchUp dimension sheets (four sheets, tighter plan) and the screenshot script."""
B = "/tmp/claude-0/-home-user-First-code/bd5e9e04-ec04-58b0-88a8-01d35cd61986/scratchpad/villa84/"

s = open(B + "shoot_a3.js", encoding="utf-8").read()
a = """  await page.pdf({ path: path.join(outDir, base + '.pdf'), width: '420mm', height: '297mm', printBackground: true, preferCSSPageSize: true });
  const sheets = await page.$$('.sheet');
  for (let i = 0; i < sheets.length; i++) {
    await sheets[i].screenshot({ path: path.join(outDir, `${base}-${i + 1}.png`) });
  }
"""
assert s.count(a) == 1
s = s.replace(a, """  const sheets = await page.$$('.sheet');
  for (let i = 0; i < sheets.length; i++) {
    await sheets[i].screenshot({ path: path.join(outDir, `${base}-${i + 1}.png`) });
  }
  const p2 = await browser.newPage();
  await p2.goto('file://' + path.resolve(htmlPath));
  await p2.waitForLoadState('networkidle');
  await p2.pdf({ path: path.join(outDir, base + '.pdf'), width: '420mm', height: '297mm', printBackground: true, preferCSSPageSize: true });
""")
open(B + "shoot_a3.js", "w", encoding="utf-8").write(s)

s = open(B + "sk_sheet.py", encoding="utf-8").read()


def rep(a, b, n=1):
    global s
    assert s.count(a) == n, (a[:60], s.count(a))
    s = s.replace(a, b)


rep('            c.dim((a, -0.30), (b, -0.30), "H", -1.05, h=0.14)\n    c.dim((0, -0.30), (W, -0.30), "H", -1.5, h=0.15)',
    '            c.dim((a, -0.30), (b, -0.30), "H", -0.85, h=0.14)\n    c.dim((0, -0.30), (W, -0.30), "H", -1.25, h=0.15)')
rep('        c.dim((W + 0.30, a), (W + 0.30, b), "V", W + 1.15, h=0.14)\n    c.dim((W + 0.30, 0), (W + 0.30, D), "V", W + 1.6, h=0.15)',
    '        c.dim((W + 0.30, a), (W + 0.30, b), "V", W + 0.95, h=0.14)\n    c.dim((W + 0.30, 0), (W + 0.30, D), "V", W + 1.4, h=0.15)')
rep('        c.dim((a, D + 0.30), (b, D + 0.30), "H", D + 0.95, h=0.14)', '        c.dim((a, D + 0.30), (b, D + 0.30), "H", D + 0.85, h=0.14)')
rep('    c.text((4.15, -0.62), "קיר זכוכית אל מרפסת הגג והגינה", TS, h=0.12)', '    c.text((4.15, -0.52), "קיר זכוכית אל מרפסת הגג והגינה", TS, h=0.12)')
rep('    c.text((W + 0.72, 5.65), "קיר זכוכית אל הבריכה", TS, h=0.12, rot=90)', '    c.text((W + 0.6, 5.65), "קיר זכוכית אל הבריכה", TS, h=0.12, rot=90)')
rep('v = SH.View(-1.75, -1.8, W + 1.95, D + 1.25, 50, 12, 11)', 'v = SH.View(-1.45, -1.5, W + 1.75, D + 1.15, 50, 10, 9.5)')
rep('pages.append(sheet(svg, panel(196, "הסלון והרהיט · תוכנית"', 'pages.append(sheet(svg, panel(172, "הסלון והרהיט · תוכנית"')
rep('"1/3", "1:50", body)))', '"1/4", "1:50", body)))')

i0 = s.index("# ---- 2: section + elevation 1:50")
i1 = s.index("body = ('<h2>מפלסים (Z מהרצפה)</h2><table>'")
s = s[:i0] + '''# ---- 2: long section 1:50
vs = SH.View(-1.9, -1.6, D + 1.9, 6.2, 50, 10, 60)
svg = SH.render(section(), vs, clip_id="p2a")
svg += title(10 + vs.w, 54, "חתך לאורך הסלון, דרך המקרן והמסך · 1:50")
''' + s[i1:]
rep('''pages.append(sheet(svg, panel(132, "חתך וחזית", "גבהים, מיקום המקרן והמסך, קיר המדיה", "2/3", "1:50", body)))''',
    '''pages.append(sheet(svg, panel(98, "חתך לאורך", "גבהים, מיקום המקרן והמסך", "2/4", "1:50", body)))

# ---- 3: media wall elevation 1:50
ve = SH.View(-1.3, -1.6, W + 1.75, 5.85, 50, 14, 62)
svg = SH.render(elevation(), ve, clip_id="p3e")
svg += title(14 + ve.w, 56, "חזית קיר המדיה, מבט מתוך הסלון · 1:50")
body = ('<h2>הספרייה</h2><table>'
        + "".join(f'<tr><td>{a}</td><td class="n">{b}</td></tr>' for a, b in (
            ("רוחב כולל", "390"), ("עומק", "40"), ("גובה, עד התקרה הצפה", "500"), ("4 תאים, רוחב כל תא", "97.5"),
            ("ארון תחתון, גובה", "92"), ("בסיס שחור מתחת לארון", "6"), ("9 שורות מדפים, מרווח", "45.3"),
            ("עובי מדף", "3.5"), ("עובי מחיצה אנכית", "3.6"), ("גב הספרייה", "עץ אגוז")))
        + '</table><h2>לוחות השיש</h2><table>'
        + "".join(f'<tr><td>{a}</td><td class="n">{b}</td></tr>' for a, b in (
            ("לוח שמאלי", "165 × 30 × 500"), ("לוח ימני", "170 × 30 × 500"), ("רווח מהקירות הצדדיים", "55"),
            ("פוגה אנכית באמצע כל לוח", "כן")))
        + '</table><h2>המסך מול הספרייה</h2><ul>'
        '<li>המסך הפתוח: 420 רוחב, מ־Z=92 עד התקרה. הוא מכסה את כל המדפים.</li>'
        '<li>הארון התחתון, בגובה 92, נשאר גלוי מתחת למסך.</li>'
        '<li>כשהמסך סגור רואים את הספרייה כולה.</li></ul>'
        '<h2>הקיר</h2><ul><li>קיר המדיה אטום, בלי חלונות, כדי שלא ייכנס אור ליד המסך.</li>'
        '<li>רוחב הקיר 835, גובה עד התקרה הצפה 500.</li></ul>')
pages.append(sheet(svg, panel(170, "חזית קיר המדיה", "ספרייה, לוחות שיש ומיקום המסך", "3/4", "1:50", body)))''')
rep('"3/3", "1:10 · 1:20 · 1:50", body)))', '"4/4", "1:10 · 1:20 · 1:50", body)))')
rep("# ---- 3: details", "# ---- 4: details")
open(B + "sk_sheet.py", "w", encoding="utf-8").write(s)
print("patched")
