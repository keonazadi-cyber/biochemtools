#!/usr/bin/env python3
"""All 20 amino acid titration curves on one sheet.

The 20 per-amino-acid curve pages are the best cluster on the site: Google
positions 3.3 to 5.2 against a site average of 20.8, and CTR 2 to 6.5%. They
work because a curve is not something a search result can hand you. This sheet
is the printable form of that cluster, and it is the one chart on the site whose
subject is already proven.

Curves are computed from the tool page's own AA table with the same
Henderson-Hasselbalch model the pages use, so a sheet and a page can never
disagree. The pI is solved numerically and checked against the published value.
"""
import os as _os, re, json, subprocess, sys, tempfile
from PIL import Image, ImageDraw

sys.path.insert(0, _os.path.dirname(_os.path.abspath(__file__)))
import chartkit
from lightmode import theme, suffix

HERE = _os.path.dirname(_os.path.abspath(__file__))
SITE = _os.path.join(HERE, "..", "..")
BUILD_DIR = _os.path.join(HERE, "build")
_os.makedirs(BUILD_DIR, exist_ok=True)

LIGHT, P = theme()
F = chartkit.fonts()
W, M = chartkit.WIDTH, chartkit.MARGIN

sys.path.insert(0, _os.path.join(SITE, "tools"))
from build_titration_pages import NAMES, ORDER          # the one name table


def run_js(lit):
    with tempfile.NamedTemporaryFile("w", suffix=".js", delete=False) as f:
        f.write("const A=" + lit + ";console.log(JSON.stringify(A))")
        p = f.name
    try:
        r = subprocess.run(["node", p], capture_output=True, text=True)
        assert not r.returncode, r.stderr[:300]
        return json.loads(r.stdout)
    finally:
        _os.unlink(p)


tool = open(_os.path.join(SITE, "amino-acid-titration-curve.html"), encoding="utf-8").read()
m = re.search(r"const AA=(\{[\s\S]*?\});", tool)
assert m, "AA table not found on the titration tool"
AA = run_js(m.group(1))
assert len(AA) == 20, "expected all 20 amino acids, got %d" % len(AA)

chart = open(_os.path.join(SITE, "amino-acid-chart.html"), encoding="utf-8").read()
m2 = re.search(r"const\s+AA\s*=\s*(\[[\s\S]*?\]);", chart)
BOOK = {r["c3"]: float(r["pI"]) for r in run_js(m2.group(1))}


def charge(gs, pH):
    t = 0.0
    for g in gs:
        t += (1 / (1 + 10 ** (pH - g["pka"])) if g["t"] == "b"
              else -1 / (1 + 10 ** (g["pka"] - pH)))
    return t


def equivalents(gs, pH):
    return sum(1 / (1 + 10 ** (g["pka"] - pH)) for g in gs)


def solve_pi(gs):
    lo, hi = 0.0, 14.0
    for _ in range(60):
        mid = (lo + hi) / 2
        if charge(gs, mid) > 0:
            lo = mid
        else:
            hi = mid
    return (lo + hi) / 2


# every pI checked against the published figure before anything is drawn
for code, gs in AA.items():
    got, want = solve_pi(gs), BOOK[code]
    assert abs(got - want) < 0.04, "%s: solved pI %.2f, chart says %.2f" % (code, got, want)

COLS, CELL_W, CELL_H = 4, 348, 252
GRID_W = COLS * CELL_W
LEFT = (W - GRID_W) // 2


def draw():
    rows = (len(ORDER) + COLS - 1) // COLS
    # Generous on purpose: fit() crops to the real content, so over-allocating
    # costs nothing and under-allocating fails the build, which is the right way
    # round. The first attempt here was 43px short and the guard caught it.
    H = M + 150 + rows * CELL_H + 400
    img = Image.new("RGB", (W, H), P["BG"])
    d = ImageDraw.Draw(img)
    T = chartkit.safe_text
    y = M

    T(d, (M, y), "Every amino acid, titrated", F["title"], P["WHITE"]); y += 70
    T(d, (M, y), "All 20 curves, with each pKa and the isoelectric point solved "
                 "from them.", F["sub"], P["GRAY"]); y += 56

    top = y
    for i, code in enumerate(ORDER):
        gs = sorted(AA[code], key=lambda g: g["pka"])
        cx = LEFT + (i % COLS) * CELL_W
        cy = top + (i // COLS) * CELL_H
        name, _letter = NAMES[code]

        T(d, (cx + 8, cy), name, F["label"], P["WHITE"])
        pk = ", ".join("%.2f" % g["pka"] for g in gs)
        T(d, (cx + 8, cy + 26), "pKa %s" % pk, F["small"], P["GRAY"])
        T(d, (cx + 8, cy + 50), "pI %.2f" % BOOK[code], F["small"], P["AMBER"])

        # the plot box
        px, py = cx + 8, cy + 78
        pw, ph = CELL_W - 46, CELL_H - 112
        d.rectangle([px, py, px + pw, py + ph], fill=P["BAND"], outline=P["LINE"])

        n = len(gs)
        X = lambda e: px + (e / n) * pw
        Y = lambda pH: py + ph - (pH / 14) * ph

        for g in gs:                                   # a dashed line per pKa
            yy = Y(g["pka"])
            for xx in range(int(px), int(px + pw), 10):
                d.line([xx, yy, xx + 5, yy], fill=P["LINE"])
        yy = Y(BOOK[code])                             # the pI
        for xx in range(int(px), int(px + pw), 6):
            d.line([xx, yy, xx + 3, yy], fill=P["AMBER"])

        # The 20 cells share one y-mapping and sit on aligned rows, so a scale
        # on the leftmost column reads across its whole row. Labelling all 20
        # would be 60 numbers of ink for the same information.
        if i % COLS == 0:
            for mark in (0, 7, 14):
                yy = Y(mark)
                d.line([px - 7, yy, px - 2, yy], fill=P["GRAY"])
                t = str(mark)
                tw = d.textlength(t, font=F["small"])
                T(d, (px - 12 - tw, yy - 11), t, F["small"], P["GRAY"])

        pts = []
        pH = 0.0
        while pH <= 14.0001:
            pts.append((X(equivalents(gs, pH)), Y(pH)))
            pH += 0.05
        d.line(pts, fill=P["GREEN"], width=3)

    y = top + rows * CELL_H + 18
    y = chartkit.legend(d, M, y, [("Curve", P["GREEN"]), ("pI", P["AMBER"]),
                                  ("pKa", P["LINE"])], P, F)
    y += 10
    T(d, (M, y), "Each curve is pH against equivalents of base added, pH 0 to 14 "
                 "on every cell. Flat means buffering, steep means an equivalence "
                 "point.", F["body"], P["GRAY"]); y += 34
    T(d, (M, y), "The pI is where net charge is zero: between the two pKa values "
                 "either side of the neutral species.", F["body"], P["GRAY"])
    y += 48

    y = chartkit.footer(d, W, H, y, P, F,
                        note="Curves and pI solved from the site's own pKa table "
                             "at build time, then checked against the published pI.")
    img = chartkit.fit(img, y, d=d)
    out = _os.path.join(BUILD_DIR, "curves-guide%s.png" % suffix())
    img.save(out)
    print("saved", out, img.size)
    print("verified: %d curves, every pI within 0.04 of the published value" % len(ORDER))


draw()
