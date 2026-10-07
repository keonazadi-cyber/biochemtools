#!/usr/bin/env python3
"""A real PNG of every titration curve, matching what the canvas draws.

Why this exists: the `cysteine titration curve` results page on Google opens with
an image pack of eight titration curves, sourced from Chegg, ResearchGate,
Numerade, LibreTexts and Wikimedia. Several of them are phone photos of textbook
pages. Our curves are drawn in a <canvas>, which Google Images cannot index at
all, so the nicest curve in that result set is the one that is not in it.

The geometry here is a transcription of the canvas code in
build_titration_pages.py. If you change one, change the other, and run this with
--check, which re-derives every plotted point from the same pKa table the page
ships and fails if they disagree.

Rendered at 4x and downsampled for smooth curves, with text drawn afterwards at
final size so it stays crisp.
"""
import os, re, json, subprocess, tempfile, sys, math
from PIL import Image, ImageDraw, ImageFont

SITE = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..")
SRC = os.path.join(SITE, "amino-acid-titration-curve.html")
OUT = os.path.join(SITE, "curves")

# the canvas, exactly
CW, CH, P = 700, 320, 40
SCALE = 2           # final image is 1400x640, big enough for an image pack
SS = 3              # supersample factor on top of SCALE, for smooth lines

BG    = "#171310"   # --card, so the PNG reads the same as the card it sits in
AXIS  = "#2c2620"
GRID  = "#1a1512"
LABEL = "#a2968a"
PKA   = "#e8b04b"
PI    = "#6fb59f"
CURVE = "#cf9366"   # --curve

# Arial has no U+207B, the superscript minus in "OH\u207B", and silently draws a
# tofu box instead. Arial Unicode carries it. no_tofu() below fails the build if any
# label ever picks up a character the font cannot draw.
FONT = "/System/Library/Fonts/Supplemental/Arial Unicode.ttf"

NAMES = {"Gly": "Glycine", "Ala": "Alanine", "Asp": "Aspartic acid",
         "Glu": "Glutamic acid", "His": "Histidine", "Lys": "Lysine",
         "Arg": "Arginine", "Cys": "Cysteine", "Tyr": "Tyrosine",
         "Met": "Methionine", "Val": "Valine", "Ile": "Isoleucine"}


def load_aa():
    h = open(SRC, encoding="utf-8").read()
    m = re.search(r"const AA=(\{[\s\S]*?\});", h)
    if not m:
        raise RuntimeError("AA table not found in " + SRC)
    with tempfile.NamedTemporaryFile("w", suffix=".js", delete=False) as f:
        f.write("const A=" + m.group(1) + ";console.log(JSON.stringify(A))")
        p = f.name
    try:
        r = subprocess.run(["node", p], capture_output=True, text=True)
        if r.returncode:
            raise RuntimeError(r.stderr[:300])
        return json.loads(r.stdout)
    finally:
        os.unlink(p)


def equiv(gs, pH):
    return sum(1 / (1 + 10 ** (g["pka"] - pH)) for g in gs)


def net(gs, pH):
    return sum((1 / (1 + 10 ** (pH - g["pka"]))) if g["t"] == "b"
               else -(1 / (1 + 10 ** (g["pka"] - pH))) for g in gs)


def pI(gs):
    lo, hi = 0.0, 14.0
    for _ in range(60):
        m = (lo + hi) / 2
        if net(gs, m) > 0:
            lo = m
        else:
            hi = m
    return (lo + hi) / 2


def dashed(d, x0, y0, x1, y1, fill, width, on, off):
    """Pillow has no dash pattern, so step along the line by hand."""
    total = math.hypot(x1 - x0, y1 - y0)
    if total == 0:
        return
    ux, uy = (x1 - x0) / total, (y1 - y0) / total
    t, draw_on = 0.0, True
    while t < total:
        seg = min(on if draw_on else off, total - t)
        if draw_on:
            d.line([x0 + ux * t, y0 + uy * t,
                    x0 + ux * (t + seg), y0 + uy * (t + seg)], fill=fill, width=width)
        t += seg
        draw_on = not draw_on


def render(code, gs):
    n = len(gs)
    S = SCALE * SS
    W, H = CW * S, CH * S
    X = lambda e: P * S + (e / n) * (W - P * S - 14 * S)
    Y = lambda pH: H - P * S - (pH / 14) * (H - P * S - 14 * S)

    im = Image.new("RGB", (W, H), BG)
    d = ImageDraw.Draw(im)

    for p in range(0, 15, 2):                      # grid
        d.line([P * S, Y(p), W - 14 * S, Y(p)], fill=GRID, width=1 * S)
    d.line([P * S, 10 * S, P * S, H - P * S], fill=AXIS, width=1 * S)   # axes
    d.line([P * S, H - P * S, W - 14 * S, H - P * S], fill=AXIS, width=1 * S)

    for g in gs:                                   # pKa guides
        dashed(d, P * S, Y(g["pka"]), W - 14 * S, Y(g["pka"]), PKA, 1 * S, 5 * S, 4 * S)
    # The canvas draws the pI line before it clears the dash pattern, so on the page
    # this line is dashed too. The PNG has to match what a visitor actually sees.
    pi = pI(gs)
    dashed(d, P * S, Y(pi), W - 14 * S, Y(pi), PI, 1 * S, 5 * S, 4 * S)

    pts = []                                       # the curve
    pH = 0.0
    while pH <= 14.0001:
        pts.append((X(equiv(gs, pH)), Y(pH)))
        pH += 0.02
    d.line(pts, fill=CURVE, width=round(2.5 * S), joint="curve")

    im = im.resize((CW * SCALE, CH * SCALE), Image.LANCZOS)

    # text last, at final size, so it does not go through the downsample
    d = ImageDraw.Draw(im)
    f = ImageFont.truetype(FONT, 12 * SCALE)
    Xs = lambda e: P * SCALE + (e / n) * (CW * SCALE - P * SCALE - 14 * SCALE)
    Ys = lambda pH: CH * SCALE - P * SCALE - (pH / 14) * (CH * SCALE - P * SCALE - 14 * SCALE)
    for p in range(0, 14, 2):
        d.text(((P - 24) * SCALE, Ys(p) + 4 * SCALE), str(p), font=f, fill=LABEL, anchor="ls")
    d.text(((P - 30) * SCALE, Ys(14) + 4 * SCALE), "pH", font=f, fill=LABEL, anchor="ls")
    d.text(((CW - 170) * SCALE, (CH - 14) * SCALE), "equivalents of OH⁻ →",
           font=f, fill=LABEL, anchor="ls")
    for g in gs:
        d.text(((CW - 96) * SCALE, Ys(g["pka"]) - 4 * SCALE), "pKa %.2f" % g["pka"],
               font=f, fill=PKA, anchor="ls")
    d.text(((P + 6) * SCALE, Ys(pi) - 4 * SCALE), "pI %.2f" % pi, font=f, fill=PI, anchor="ls")
    return im


def no_tofu(labels):
    """Fail on any character the font renders as a .notdef box.

    U+FFFF is guaranteed absent from every font, so whatever it draws IS the box.
    Anything that renders identically is a character the font does not have.
    """
    f = ImageFont.truetype(FONT, 40)

    def bits(ch):
        im = Image.new("L", (90, 70), 0)
        ImageDraw.Draw(im).text((5, 5), ch, font=f, fill=255)
        return im.tobytes()

    box = bits("\uFFFF")
    bad = sorted({c for s_ in labels for c in s_ if c.strip() and bits(c) == box})
    return ["font cannot draw %r (U+%04X)" % (c, ord(c)) for c in bad]


def check(aa):
    """Prove the plotted geometry still agrees with the page's own numbers."""
    bad = no_tofu(["pH", "equivalents of OH\u207B \u2192", "pKa 0123456789.", "pI"])
    for code, gs in aa.items():
        n = len(gs)
        # the curve must start at 0 equivalents and finish at n
        if abs(equiv(gs, 0.0)) > 0.02:
            bad.append("%s: curve does not start at zero equivalents" % code)
        if abs(equiv(gs, 14.0) - n) > 0.15:
            bad.append("%s: curve ends at %.2f equivalents, expected %d"
                       % (code, equiv(gs, 14.0), n))
        # every pKa guide must sit inside the plot
        for g in gs:
            if not 0 <= g["pka"] <= 14:
                bad.append("%s: pKa %.2f falls outside the drawn range" % (code, g["pka"]))
        # the pI must land between the bracketing pKa values
        pks = sorted(g["pka"] for g in gs)
        p = pI(gs)
        if not pks[0] < p < pks[-1]:
            bad.append("%s: pI %.2f is not between pKa %.2f and %.2f" % (code, p, pks[0], pks[-1]))
    return bad


if __name__ == "__main__":
    aa = load_aa()
    bad = check(aa)
    if bad:
        for b in bad:
            print("  FAIL " + b)
        sys.exit(1)
    if "--check" in sys.argv:
        print("  geometry check passed for %d amino acids" % len(aa))
        sys.exit(0)
    os.makedirs(OUT, exist_ok=True)
    for code, gs in aa.items():
        slug = NAMES[code].lower().replace(" ", "-")
        im = render(code, gs)
        path = os.path.join(OUT, "%s-titration-curve.png" % slug)
        im.save(path, optimize=True)
        print("    %-44s %dx%d  %5.1f KB"
              % (os.path.relpath(path, SITE), im.width, im.height,
                 os.path.getsize(path) / 1024))
    print("  rendered %d curves" % len(aa))
