#!/usr/bin/env python3
"""Ketogenic vs glucogenic amino acids, as a shareable chart.

Data comes from the AA array in amino-acid-catabolism-explorer.html, so the chart and
the tool cannot disagree. Counts and the two purely ketogenic amino acids are derived
from the data and asserted rather than typed.
"""
import os as _os
BUILD_DIR = _os.path.join(_os.path.dirname(_os.path.abspath(__file__)), "build")
_os.makedirs(BUILD_DIR, exist_ok=True)
import chartdata
import json
from PIL import Image, ImageDraw, ImageFont
from lightmode import theme, suffix

LIGHT, P = theme()
AA = chartdata.catabolism()   # [name, 3-letter, class, entry point, note]

assert len(AA) == 20, f"expected 20 amino acids, got {len(AA)}"
KETO  = [a for a in AA if a[2] == "keto"]
BOTH  = [a for a in AA if a[2] == "both"]
GLUCO = [a for a in AA if a[2] == "gluco"]
assert len(KETO) + len(BOTH) + len(GLUCO) == 20, "class split lost an amino acid"
assert len(KETO) == 2, f"expected 2 purely ketogenic, got {len(KETO)}"
assert {a[1] for a in KETO} == {"Leu", "Lys"}, f"purely ketogenic changed: {[a[1] for a in KETO]}"

BG, CARD, LINE = P["BG"], P["CARD"], P["LINE"]
WHITE, GRAY, DIM = P["WHITE"], P["GRAY"], P["DIM"]
GREEN, AMBER, RED, BLUE, PURPLE = P["GREEN"], P["AMBER"], P["RED"], P["BLUE"], P["PURPLE"]

B = "/System/Library/Fonts/Supplemental/Arial Bold.ttf"
R_ = "/System/Library/Fonts/Supplemental/Arial.ttf"
f = lambda p, s: ImageFont.truetype(p, s)
F_TITLE, F_SUB = f(B, 56), f(R_, 27)
F_GRP = f(B, 30)
F_GRPN = f(R_, 23)
F_NAME = f(B, 27)
F_C3 = f(R_, 22)
F_ENTRY = f(R_, 23)
F_BIG = f(B, 44)
F_FOOT = f(R_, 23)
F_DOM = f(B, 33)

W, M = 1560, 60
CW = W - 2 * M
ROW = 54

GROUPS = [
    ("Ketogenic only", KETO, RED,
     "Cannot make glucose. Their carbons end up as acetyl-CoA or acetoacetate, and animals cannot turn those back into sugar."),
    ("Both ketogenic and glucogenic", BOTH, AMBER,
     "Split down two routes. Part of the skeleton can make glucose, part cannot."),
    ("Glucogenic only", GLUCO, GREEN,
     "Enter as pyruvate or a citric acid cycle intermediate, both of which can run back up to glucose."),
]

H = 300 + sum(96 + len(g[1]) * ROW + 26 for g in GROUPS) + 300
img = Image.new("RGB", (W, H), BG)
d = ImageDraw.Draw(img)
d.rectangle([0, 0, W, 12], fill=GREEN)

d.text((M, 58), "Ketogenic vs glucogenic amino acids", font=F_TITLE, fill=WHITE)
d.text((M + 2, 134), f"Only {len(KETO)} of the 20 cannot make glucose at all. Here is where each one enters metabolism.",
       font=F_SUB, fill=GRAY)

y = 216
for title, members, col, blurb in GROUPS:
    d.rounded_rectangle([M, y, M + CW, y + 84 + len(members) * ROW], radius=14, fill=CARD)
    d.rectangle([M, y + 18, M + 5, y + 62], fill=col)
    d.text((M + 26, y + 16), title, font=F_GRP, fill=col)
    cnt = f"{len(members)} of 20"
    d.text((M + CW - 26 - d.textlength(cnt, font=F_GRPN), y + 24), cnt, font=F_GRPN, fill=DIM)
    assert M + 28 + d.textlength(blurb, font=F_ENTRY) < M + CW - 20, f"blurb overflows: {title}"
    d.text((M + 28, y + 54), blurb, font=F_ENTRY, fill=DIM)
    yy = y + 90
    for name, c3, cls, entry, note in members:
        d.text((M + 28, yy), name, font=F_NAME, fill=WHITE)
        d.text((M + 250, yy + 4), c3, font=F_C3, fill=DIM)
        assert M + 330 + d.textlength(entry, font=F_ENTRY) < M + CW - 20, f"entry overflows: {name}"
        d.text((M + 330, yy + 3), entry, font=F_ENTRY, fill=col)
        yy += ROW
    y += 84 + len(members) * ROW + 26

y += 6
d.rounded_rectangle([M, y, M + CW, y + 168], radius=14, fill=P["WARM"])
d.text((M + 26, y + 20), "The only two you have to memorise", font=F_GRP, fill=AMBER)
d.text((M + 26, y + 64), " and ".join(a[0] for a in KETO), font=F_BIG, fill=WHITE)
side = [
    "Both begin with L, which is the whole mnemonic.",
    "Every other amino acid can contribute to glucose,",
    "either wholly or in part.",
]
for i, t in enumerate(side):
    assert M + 620 + d.textlength(t, font=F_ENTRY) < M + CW - 20, f"side note {i} overflows"
    d.text((M + 620, y + 60 + i * 30), t, font=F_ENTRY, fill=GRAY if i < 2 else DIM)
y += 194

d.line([(M, y), (M + CW, y)], fill=LINE, width=2)
y += 24
foot = [
    "Glucogenic means the carbon skeleton becomes pyruvate or a citric acid cycle intermediate, which can run back up to glucose.",
    "Ketogenic means it becomes acetyl-CoA or acetoacetate. Animals have no way to turn acetyl-CoA back into glucose.",
    "A few classifications vary by textbook where a minor branch produces some acetyl-CoA. This follows the standard teaching set.",
]
for i, t in enumerate(foot):
    assert M + d.textlength(t, font=F_FOOT) < W - M, f"footer {i} overflows"
    d.text((M, y + 32 * i), t, font=F_FOOT, fill=GRAY if i < 2 else DIM)
y += 32 * len(foot) + 24

assert y + 44 < H, f"content overflows: needs {y + 44}, have {H}"
d.text((M, y), "biochemtools.com", font=F_DOM, fill=WHITE)
tag = "free, no signup  /  CC BY 4.0"
d.text((W - M - d.textlength(tag, font=F_FOOT), y + 10), tag, font=F_FOOT, fill=DIM)

out = BUILD_DIR + "/catabolism-guide%s.png" % suffix()
img.save(out)
print("saved", out, img.size)
print(f"verified: {len(KETO)} keto ({', '.join(a[1] for a in KETO)}), "
      f"{len(BOTH)} both, {len(GLUCO)} gluco")
