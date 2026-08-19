#!/usr/bin/env python3
"""Every biochem equation on one page, as a shareable chart.

Equations are pulled from the EQ array in biochem-equation-sheet.html and rendered
with real superscripts, so the chart and the tool cannot drift apart. Categories and
counts are derived from the data rather than typed.
"""
import os as _os
BUILD_DIR = _os.path.join(_os.path.dirname(_os.path.abspath(__file__)), "build")
_os.makedirs(BUILD_DIR, exist_ok=True)
import chartdata
import json
from PIL import Image, ImageDraw, ImageFont

EQ = chartdata.equations()   # [category, formula, what it is, note, link, linkText]

assert len(EQ) >= 30, f"expected the full equation list, got {len(EQ)}"
assert all(len(r) >= 3 and r[1] for r in EQ), "an equation row is malformed"

CATS = []
for r in EQ:
    if r[0] not in CATS:
        CATS.append(r[0])
BY = {c: [r for r in EQ if r[0] == c] for c in CATS}
assert sum(len(v) for v in BY.values()) == len(EQ), "category split lost rows"

from lightmode import theme, suffix
LIGHT, P = theme()
BG, CARD, LINE = P["BG"], P["CARD"], P["LINE"]
WHITE, GRAY, DIM = P["WHITE"], P["GRAY"], P["DIM"]
GREEN = P["GREEN"]
PALETTE = ([P["GREEN"], P["BLUE"], P["PURPLE"], P["AMBER"], P["RED"],
            (18, 120, 132), (150, 108, 30), (60, 120, 60)] if LIGHT else
           [(95, 204, 167), (93, 157, 226), (171, 144, 224), (228, 169, 59),
            (226, 100, 94), (110, 200, 210), (200, 170, 120), (150, 190, 130)])
COL = {c: PALETTE[i % len(PALETTE)] for i, c in enumerate(CATS)}

B = "/System/Library/Fonts/Supplemental/Arial Bold.ttf"
R_ = "/System/Library/Fonts/Supplemental/Arial.ttf"
# a font with good coverage of superscripts and Greek
M_ = "/System/Library/Fonts/Supplemental/Arial Unicode.ttf"
import os
if not os.path.exists(M_):
    M_ = R_
f = lambda p, s: ImageFont.truetype(p, s)
F_TITLE, F_SUB = f(B, 56), f(R_, 27)
F_CAT = f(B, 27)
F_EQ = f(M_, 27)
F_WHAT = f(R_, 22)
F_FOOT = f(R_, 23)
F_DOM = f(B, 33)

W, M = 1560, 60
COLS = 2
COLW = (W - 2 * M - 40) // COLS
ROW = 74
CAT_H = 54

# lay out into two columns, keeping categories intact
def plan():
    seq = []
    for c in CATS:
        seq.append(("cat", c))
        for r in BY[c]:
            seq.append(("eq", r))
    return seq

SEQ = plan()
units = sum(CAT_H if k == "cat" else ROW for k, _ in SEQ)
col_target = units / COLS

# worst case: one column takes the larger half of the sequence
_left = 0
_acc = 0
for _k, _i in SEQ:
    _h = CAT_H if _k == "cat" else ROW
    if _acc + _h > col_target and _k == "cat" and _left == 0:
        _left = _acc
        _acc = 0
    _acc += _h
_tallest = max(_left, _acc)
H_ = 300 + _tallest + 250
img = Image.new("RGB", (W, H_), BG)
d = ImageDraw.Draw(img)
d.rectangle([0, 0, W, 12], fill=GREEN)

d.text((M, 58), "Every biochem equation on one page", font=F_TITLE, fill=WHITE)
d.text((M + 2, 134), f"{len(EQ)} formulas across {len(CATS)} topics, each with what it is actually for.",
       font=F_SUB, fill=GRAY)

x = M
y = top = 216
used = 0
bottom = top
for kind, item in SEQ:
    h = CAT_H if kind == "cat" else ROW
    if used + h > col_target and kind == "cat" and x == M:
        x = M + COLW + 40
        y = top
        used = 0
    if kind == "cat":
        col = COL[item]
        d.rectangle([x, y + 12, x + 4, y + 38], fill=col)
        d.text((x + 18, y + 10), item.upper(), font=F_CAT, fill=col)
        cnt = f"{len(BY[item])}"
        d.text((x + COLW - 20 - d.textlength(cnt, font=F_WHAT), y + 18), cnt, font=F_WHAT, fill=DIM)
    else:
        col = COL[item[0]]
        eq, what = item[1], item[2]
        while d.textlength(eq, font=F_EQ) > COLW - 24 and len(eq) > 8:
            eq = eq[:-2]
        d.text((x + 16, y + 4), eq, font=F_EQ, fill=WHITE)
        w2 = what
        while d.textlength(w2, font=F_WHAT) > COLW - 24 and len(w2) > 8:
            w2 = w2[:-2]
        d.text((x + 16, y + 40), w2, font=F_WHAT, fill=DIM)
    y += h
    used += h
    bottom = max(bottom, y)

# the footer goes under whichever column actually ended lowest, not the estimate
y = bottom + 30
d.line([(M, y), (W - M, y)], fill=LINE, width=2)
y += 24
biggest = max(CATS, key=lambda c: len(BY[c]))
# Counted, not claimed. This line used to read "every one of these has a working
# calculator" and it was not true: the Ka x Kb = Kw row has no calculator behind it.
linked = sum(1 for e in EQ if len(e) > 4 and e[4])
assert linked <= len(EQ)
calc_line = ("Every one of these has a working calculator on the site, so you can check an answer."
             if linked == len(EQ) else
             f"{linked} of the {len(EQ)} link to a working calculator on the site, so you can check an answer.")
foot = [
    f"{len(EQ)} equations, grouped into {len(CATS)} topics. The largest group is {biggest.lower()} with {len(BY[biggest])}.",
    calc_line,
    "Knowing which equation applies is most of the exam. The algebra is the easy part.",
]
for i, t in enumerate(foot):
    assert M + d.textlength(t, font=F_FOOT) < W - M, f"footer {i} overflows"
    d.text((M, y + 32 * i), t, font=F_FOOT, fill=GRAY if i < 2 else DIM)
y += 32 * len(foot) + 24

assert y + 44 < H_, f"content overflows: needs {y + 44}, have {H_}"
d.text((M, y), "biochemtools.com", font=F_DOM, fill=WHITE)
tag = "free, no signup  /  CC BY 4.0"
d.text((W - M - d.textlength(tag, font=F_FOOT), y + 10), tag, font=F_FOOT, fill=DIM)

out = BUILD_DIR + "/equation-guide%s.png" % suffix()
img.save(out)
print("saved", out, img.size)
print(f"verified: {len(EQ)} equations across {len(CATS)} categories")
for c in CATS:
    print(f"   {len(BY[c]):>2}  {c}")
