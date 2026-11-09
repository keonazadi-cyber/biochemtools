#!/usr/bin/env python3
"""Dilutions and solutions on one page. The first chart built on chartkit.

Solutions was the only practice subject with no chart at all, while the pages it
covers (serial dilution, antibody dilution, C1V1) carry about 1,100 Bing
impressions between them.

Every value is read out of the page it belongs to and asserted here, never
typed: the A260 factors from nucleic-acid-concentration-calculator.html and the
application ranges from antibody-dilution-calculator.html. If a page changes,
this build fails instead of shipping a chart that disagrees with the site.
"""
import os as _os, re, sys
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


def page(name):
    return open(_os.path.join(SITE, name), encoding="utf-8").read()


# --- values pulled from the site, not typed -------------------------------
m = re.search(r"FACTOR\s*=\s*\{([^}]*)\}", page("nucleic-acid-concentration-calculator.html"))
assert m, "FACTOR table not found on the A260 page"
A260 = dict(re.findall(r"(\w+)\s*:\s*(\d+)", m.group(1)))
assert A260 == {"dsDNA": "50", "ssDNA": "33", "RNA": "40"}, A260

ab = page("antibody-dilution-calculator.html")
tbl = re.search(r"<table[\s\S]*?</table>", ab)
assert tbl, "application table not found on the antibody page"
APPS = []
for row in re.findall(r"<tr>([\s\S]*?)</tr>", tbl.group(0))[1:]:
    cells = [re.sub(r"<[^>]+>", "", c).replace("&ndash;", "to").strip()
             for c in re.findall(r"<t[dh][^>]*>([\s\S]*?)</t[dh]>", row)]
    if len(cells) == 2:
        APPS.append((cells[0], re.sub(r"\s+", " ", cells[1])))
assert len(APPS) == 6, "expected 6 application rows, got %d" % len(APPS)
assert any("Western blot, primary" in a for a, _ in APPS), APPS

sd = page("serial-dilution-calculator.html")
assert "transfer=V/F" in sd.replace(" ", ""), "serial dilution formula changed"

ROWS = [
    ("C1V1 = C2V2", "What you take out times what it was, equals what you end "
                    "up with times what it becomes."),
    ("Solve for any one", "V1 = C2V2 / C1   ·   C2 = C1V1 / V2   ·   V2 = C1V1 / C2"),
    ("From a solid", "mass = molarity × volume in litres × molar mass"),
]

SERIAL = [
    ("Transfer per step", "V / F", "1000 µL at 10-fold = 100 µL moved"),
    ("Diluent per step", "V - transfer", "1000 - 100 = 900 µL"),
    ("Total after n steps", "Fⁿ", "10-fold, 4 steps = 1 in 10,000"),
]


def draw():
    H = 1980
    img = Image.new("RGB", (W, H), P["BG"])
    d = ImageDraw.Draw(img)
    T = chartkit.safe_text
    y = M

    T(d, (M, y), "Dilutions, one page", F["title"], P["WHITE"]); y += 70
    T(d, (M, y), "C1V1, serial dilutions, antibody ratios and A260 factors.",
      F["sub"], P["GRAY"]); y += 56

    def band(title):
        nonlocal y
        d.rectangle([M, y, W - M, y + 2], fill=P["LINE"]); y += 18
        T(d, (M, y), title, F["head"], P["AMBER"]); y += 42

    band("The one equation")
    for lab, txt in ROWS:
        T(d, (M, y), lab, F["label"], P["WHITE"])
        T(d, (M + 330, y), txt, F["body"], P["GRAY"]); y += 40
    y += 16

    band("Serial dilution")
    for lab, formula, eg in SERIAL:
        T(d, (M, y), lab, F["label"], P["WHITE"])
        T(d, (M + 330, y), formula, F["body"], P["GREEN"])
        T(d, (M + 700, y), eg, F["body"], P["GRAY"]); y += 40
    y += 8
    T(d, (M, y), "A 1:200 dilution is one part in 200 TOTAL, not one part plus 200.",
      F["body"], P["RED"]); y += 52

    band("Antibody starting points")
    for app, rng in APPS:
        T(d, (M, y), app, F["body"], P["WHITE"])
        T(d, (M + 700, y), rng, F["body"], P["BLUE"]); y += 38
    y += 8
    T(d, (M, y), "Titrate from the strong end of the range, then back off.",
      F["body"], P["GRAY"]); y += 52

    band("A260 to concentration")
    T(d, (M, y), "concentration = A260 × factor × dilution",
      F["body"], P["GREEN"]); y += 42
    for k, v in (("Double-stranded DNA", A260["dsDNA"]),
                 ("Single-stranded DNA", A260["ssDNA"]),
                 ("RNA", A260["RNA"])):
        T(d, (M, y), k, F["body"], P["WHITE"])
        T(d, (M + 700, y), "A260 of 1.0 = %s µg/mL" % v, F["body"], P["GRAY"])
        y += 38
    y += 8
    T(d, (M, y), "260/280 near 1.8 for DNA and 2.0 for RNA. 260/230 near 2.0 to 2.2.",
      F["body"], P["GRAY"]); y += 56

    chartkit.legend(d, M, y, [("Formula", P["GREEN"]), ("Range", P["BLUE"]),
                              ("Common mistake", P["RED"])], P, F)
    y += 54
    y = chartkit.footer(d, W, H, y, P, F,
                        note="Values read from the site's own calculators at build time.")

    img = chartkit.fit(img, y, d=d)
    out = _os.path.join(BUILD_DIR, "dilution-guide%s.png" % suffix())
    img.save(out)
    print("saved", out, img.size)
    print("verified: %d application rows, A260 factors %s, serial formula present"
          % (len(APPS), A260))


draw()
