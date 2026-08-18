#!/usr/bin/env python3
"""The six ways things cross a membrane, as a shareable chart.

Data comes from the MODES object in membrane-transport-explorer.html, so the chart and
the tool cannot disagree. Each row carries the fields the tool already tracks: energy
source, gradient direction, whether a protein is involved, and whether it saturates.
"""
import os as _os
BUILD_DIR = _os.path.join(_os.path.dirname(_os.path.abspath(__file__)), "build")
_os.makedirs(BUILD_DIR, exist_ok=True)
import chartdata
import json
from PIL import Image, ImageDraw, ImageFont
from lightmode import theme, suffix

LIGHT, P = theme()
M_ = chartdata.transport()

ORDER = ["simple", "channel", "carrier", "primary", "symport", "antiport"]
assert set(ORDER) == set(M_), f"modes changed: {sorted(M_)}"
ROWS = [(k, M_[k]) for k in ORDER]
assert all(len(v) >= 7 for _, v in ROWS), "each mode needs all 7 fields"

PASSIVE = [k for k, v in ROWS if "passive" in v[1].lower()]
ACTIVE = [k for k, v in ROWS if "passive" not in v[1].lower()]
SATURATES = [k for k, v in ROWS if v[4].lower().startswith("yes")]
assert len(PASSIVE) == 3 and len(ACTIVE) == 3, f"expected 3 passive and 3 active, got {len(PASSIVE)}/{len(ACTIVE)}"
assert "simple" not in SATURATES and "channel" not in SATURATES, \
    "only carrier-mediated transport should saturate"
assert len(SATURATES) == 4, f"expected 4 saturating modes, got {SATURATES}"

BG, CARD, LINE = P["BG"], P["CARD"], P["LINE"]
WHITE, GRAY, DIM = P["WHITE"], P["GRAY"], P["DIM"]
GREEN, AMBER, RED, BLUE, PURPLE = P["GREEN"], P["AMBER"], P["RED"], P["BLUE"], P["PURPLE"]

B = "/System/Library/Fonts/Supplemental/Arial Bold.ttf"
R_ = "/System/Library/Fonts/Supplemental/Arial.ttf"
f = lambda p, s: ImageFont.truetype(p, s)
F_TITLE, F_SUB = f(B, 54), f(R_, 26)
F_NAME = f(B, 27)
F_LBL = f(B, 18)
F_VAL = f(R_, 22)
F_EX = f(R_, 21)
F_H = f(B, 21)
F_FOOT = f(R_, 22)
F_DOM = f(B, 32)

W, MG = 1560, 60
CW = W - 2 * MG
ROW = 176
H = 300 + len(ROWS) * ROW + 300

img = Image.new("RGB", (W, H), BG)
d = ImageDraw.Draw(img)
d.rectangle([0, 0, W, 12], fill=GREEN)
d.text((MG, 56), "How things cross a membrane", font=F_TITLE, fill=WHITE)
d.text((MG + 2, 130), f"{len(ROWS)} mechanisms. The dividing line is not the protein, it is whether the cell spends energy.",
       font=F_SUB, fill=GRAY)

y = 210
for key, v in ROWS:
    name, energy, direction, protein, sat, ex, note = v[0], v[1], v[2], v[3], v[4], v[5], v[6]
    passive = "passive" in energy.lower()
    col = BLUE if passive else AMBER
    d.rounded_rectangle([MG, y, MG + CW, y + ROW - 16], radius=14, fill=CARD)
    d.rectangle([MG, y + 16, MG + 5, y + ROW - 44], fill=col)
    d.text((MG + 26, y + 16), name, font=F_NAME, fill=WHITE)

    tag = "PASSIVE" if passive else "ACTIVE"
    tw = d.textlength(tag, font=F_LBL)
    d.rounded_rectangle([MG + CW - 26 - tw - 24, y + 18, MG + CW - 26, y + 48], radius=8, fill=P["CHIP"])
    d.text((MG + CW - 26 - tw - 12, y + 22), tag, font=F_LBL, fill=col)

    cols = [("ENERGY", energy), ("DIRECTION", direction), ("PROTEIN", protein), ("SATURATES", sat)]
    cw = (CW - 52) / len(cols)
    for i, (lbl, val) in enumerate(cols):
        x = MG + 26 + i * cw
        d.text((x, y + 58), lbl, font=F_LBL, fill=DIM)
        # If it will not fit, drop the parenthetical rather than slicing through it,
        # which produced things like "Electrochemical gradient (usually."
        t = val
        if d.textlength(t, font=F_VAL) > cw - 18 and "(" in t:
            t = t.split("(")[0].strip()
        while d.textlength(t, font=F_VAL) > cw - 18 and " " in t:
            t = t.rsplit(" ", 1)[0]
        assert "(" not in t or ")" in t, "unbalanced parenthesis after truncation: " + t
        vcol = GREEN if val.lower().startswith("yes") else (DIM if val.lower().startswith("no") else GRAY)
        d.text((x, y + 82), t, font=F_VAL, fill=vcol)

    e = ex.replace("Examples: ", "").replace("Example: ", "")
    while d.textlength(e, font=F_EX) > CW - 60 and len(e) > 20:
        e = e[:-2]
    d.text((MG + 26, y + 118), e, font=F_EX, fill=GRAY)
    y += ROW

y += 4
d.line([(MG, y), (MG + CW, y)], fill=LINE, width=2)
y += 22
foot = [
    f"{len(PASSIVE)} passive, {len(ACTIVE)} active. Passive means down the gradient at no cost, active means uphill and the cell pays.",
    "Secondary active transport uses no ATP directly. It spends a gradient that a primary pump already built with ATP.",
    f"{len(SATURATES)} of the {len(ROWS)} saturate, and the exception is the giveaway: anything using a carrier has a finite cycle time,",
    "so flux plateaus like an enzyme. Simple diffusion and channels have no such cycle, so over any physiological range their flux keeps climbing.",
]
for i, t in enumerate(foot):
    assert MG + d.textlength(t, font=F_FOOT) < W - MG, f"footer {i} overflows"
    d.text((MG, y + 31 * i), t, font=F_FOOT, fill=GRAY if i < 2 else DIM)
y += 31 * len(foot) + 22

assert y + 44 < H, f"content overflows: needs {y + 44}, have {H}"
d.text((MG, y), "biochemtools.com", font=F_DOM, fill=WHITE)
t = "free, no signup"
d.text((W - MG - d.textlength(t, font=F_FOOT), y + 10), t, font=F_FOOT, fill=DIM)

out = BUILD_DIR + "/transport-guide%s.png" % suffix()
img.save(out)
print("saved", out, img.size)
print(f"verified: {len(ROWS)} modes, {len(PASSIVE)} passive / {len(ACTIVE)} active, {len(SATURATES)} saturate")
