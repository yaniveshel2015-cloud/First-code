"""Dimension text offsets proportional to the text size (so they also work at 1:10 and 1:25), and small label fixes."""
B = "/tmp/claude-0/-home-user-First-code/bd5e9e04-ec04-58b0-88a8-01d35cd61986/scratchpad/villa84/"


def patch(path, reps):
    s = open(path, encoding="utf-8").read()
    for a, b in reps:
        assert s.count(a) == 1, (path, a[:70], s.count(a))
        s = s.replace(a, b)
    open(path, "w", encoding="utf-8").write(s)


patch(B + "sheets.py", [
    ('''            (xa, ya), (xb, yb), at = it["a"], it["b"], it["at"]
            if it["axis"] == "H":
                p, q = (xa, at), (xb, at)
                e1 = ((xa, ya + (0.25 if at > ya else -0.25)), (xa, at + (0.18 if at > ya else -0.18)))
                e2 = ((xb, yb + (0.25 if at > yb else -0.25)), (xb, at + (0.18 if at > yb else -0.18)))''',
     '''            (xa, ya), (xb, yb), at = it["a"], it["b"], it["at"]
            he = it.get("h", 0.2) * text_k                      # effective text height in model metres
            g1, g2 = 1.0 * he, 0.72 * he                        # gap from the measured point, overshoot past the line
            if it["axis"] == "H":
                p, q = (xa, at), (xb, at)
                e1 = ((xa, ya + (g1 if at > ya else -g1)), (xa, at + (g2 if at > ya else -g2)))
                e2 = ((xb, yb + (g1 if at > yb else -g1)), (xb, at + (g2 if at > yb else -g2)))'''),
    ('''                val, tp, rot = abs(xb - xa), ((xa + xb) / 2, at + it.get("side", 1) * (it.get("h", 0.2) * 0.75 + 0.07)), 0''',
     '''                val, tp, rot = abs(xb - xa), ((xa + xb) / 2, at + (0.9 * he if it.get("side", 1) > 0 else -1.45 * he)), 0'''),
    ('''                e1 = ((xa + (0.25 if at > xa else -0.25), ya), (at + (0.18 if at > xa else -0.18), ya))
                e2 = ((xb + (0.25 if at > xb else -0.25), yb), (at + (0.18 if at > xb else -0.18), yb))''',
     '''                e1 = ((xa + (g1 if at > xa else -g1), ya), (at + (g2 if at > xa else -g2), ya))
                e2 = ((xb + (g1 if at > xb else -g1), yb), (at + (g2 if at > xb else -g2), yb))'''),
    ('''                val, tp, rot = abs(yb - ya), (at - it.get("side", 1) * (it.get("h", 0.2) * 0.75 + 0.07), (ya + yb) / 2), 90''',
     '''                val, tp, rot = abs(yb - ya), (at - (0.9 * he if it.get("side", 1) > 0 else -1.45 * he), (ya + yb) / 2), 90'''),
])

patch(B + "sk_sheet.py", [
    ('''    c.dim((0.0, 0.0), (d, 0.0), "H", -0.2, h=0.05)
    c.dim((0.0, 0.0), (0.26, 0.0), "H", -0.1, h=0.045)
    c.dim((0.26, 0.0), (d, 0.0), "H", -0.1, h=0.045)''',
     '''    c.dim((0.0, 0.0), (d, 0.0), "H", -0.27, h=0.05)
    c.dim((0.0, 0.0), (0.26, 0.0), "H", -0.15, h=0.045)
    c.dim((0.26, 0.0), (d, 0.0), "H", -0.15, h=0.045)'''),
    ('''    c.text((d + 0.45, 0.31), "משענת יד 62", TS, h=0.04, rot=90)''', '''    c.text((d + 0.42, 0.31), "משענת יד", TS, h=0.04, rot=90)'''),
    ('''    zs = (0.0, 0.03, 0.08, 0.08 + IMG_H, DROP)
    for a, b in zip(zs, zs[1:]):
        c.dim((x1, a), (x1, b), "V", x1 + 0.5, h=0.11, txt=cm(b - a))''',
     '''    zs = (0.0, 0.08, 0.08 + IMG_H, DROP)
    for a, b in zip(zs, zs[1:]):
        c.dim((x1, a), (x1, b), "V", x1 + 0.5, h=0.11, txt=cm(b - a))
    c.text((x1 + 0.62, -0.28), "8 = מוט 3 + שוליים 5", TS, h=0.1)'''),
])
print("patched")
