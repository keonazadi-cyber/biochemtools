#!/usr/bin/env python3
"""Where the ATP from one glucose actually comes from, as a shareable chart.

Hook: most textbooks still say 36-38 ATP. The modern figure is 30-32, because
NADH and FADH2 are worth 2.5 and 1.5 ATP rather than 3 and 2. Every number here
is re-derived and asserted at build time, so the chart cannot drift from the
arithmetic or from atp-yield-calculator.html.
"""
import os as _os
BUILD_DIR = _os.path.join(_os.path.dirname(_os.path.abspath(__file__)), "build")
_os.makedirs(BUILD_DIR, exist_ok=True)
from PIL import Image, ImageDraw, ImageFont

from lightmode import theme, suffix
LIGHT, P = theme()
BG, CARD, LINE = P["BG"], P["CARD"], P["LINE"]
WHITE, GRAY, DIM = P["WHITE"], P["GRAY"], P["DIM"]
GREEN, AMBER, RED = P["GREEN"], P["AMBER"], P["RED"]
BLUE, PURPLE = P["BLUE"], P["PURPLE"]

B = "/System/Library/Fonts/Supplemental/Arial Bold.ttf"
R = "/System/Library/Fonts/Supplemental/Arial.ttf"
f = lambda p, s: ImageFont.truetype(p, s)
F_TITLE = f(B, 60)
F_SUB = f(R, 29)
F_STAGE = f(B, 33)
F_LOC = f(R, 23)
F_BIG = f(B, 42)
F_LBL = f(R, 23)
F_NUM = f(B, 30)
F_BODY = f(R, 26)
F_FOOT = f(R, 24)
F_DOM = f(B, 34)

# ---- the arithmetic, re-derived here so the chart is never hand-typed ----
STAGES = [
    ("Glycolysis",             "in the cytosol",            2, 2, 0, GREEN),
    ("Pyruvate oxidation",     "x2, mitochondrial matrix",  0, 2, 0, BLUE),
    ("Citric acid cycle",      "x2, mitochondrial matrix",  2, 6, 2, PURPLE),
]
DIRECT = sum(s[2] for s in STAGES)
NADH = sum(s[3] for s in STAGES)
FADH2 = sum(s[4] for s in STAGES)
CYTO = 2                      # glycolytic NADH, cannot cross the inner membrane
assert (DIRECT, NADH, FADH2) == (4, 10, 2), "stage totals changed"

def total(n_atp, f_atp, shuttle_costs):
    n = NADH - (CYTO if shuttle_costs else 0)
    fd = FADH2 + (CYTO if shuttle_costs else 0)
    return DIRECT + n * n_atp + fd * f_atp

LOW, HIGH = int(total(2.5, 1.5, True)), int(total(2.5, 1.5, False))
OLD_LOW, OLD_HIGH = int(total(3, 2, True)), int(total(3, 2, False))
assert (LOW, HIGH) == (30, 32) and (OLD_LOW, OLD_HIGH) == (36, 38), "totals changed"

W = 1500
H = 1780
img = Image.new("RGB", (W, H), BG)
d = ImageDraw.Draw(img)
d.rectangle([0, 0, W, 12], fill=GREEN)

d.text((60, 62), "Where the ATP actually comes from", font=F_TITLE, fill=WHITE)
d.text((62, 146), f"One glucose, aerobic. Your textbook probably says {OLD_HIGH}. The real answer is {LOW} to {HIGH}.",
       font=F_SUB, fill=GRAY)

y = 232
M, CW = 60, W - 120


def chip(x, y, text, colour, font=F_NUM):
    tw = d.textlength(text, font=font)
    d.rounded_rectangle([x, y, x + tw + 34, y + 46], radius=10, fill=P["CHIP"])
    d.text((x + 17, y + 6), text, font=font, fill=colour)
    return x + tw + 34 + 14


for name, loc, atp, nadh, fadh2, col in STAGES:
    d.rounded_rectangle([M, y, M + CW, y + 148], radius=14, fill=CARD)
    d.rectangle([M, y + 16, M + 5, y + 132], fill=col)
    d.text((M + 30, y + 22), name, font=F_STAGE, fill=col)
    d.text((M + 32, y + 66), loc, font=F_LOC, fill=DIM)
    x = M + 30
    for label, n in (("ATP", atp), ("NADH", nadh), ("FADH2", fadh2)):
        if n:
            x = chip(x, y + 92, f"{n} {label}", WHITE)
    if name == "Glycolysis":
        note = "this NADH is stuck outside the mitochondrion"
        d.text((M + CW - 30 - d.textlength(note, font=F_LBL), y + 104), note, font=F_LBL, fill=AMBER)
    y += 168

# running total
d.rounded_rectangle([M, y, M + CW, y + 118], radius=14, fill=P["PANEL"])
d.text((M + 30, y + 20), "Add it up", font=F_STAGE, fill=GREEN)
x = M + 30
for label, n in (("ATP directly", DIRECT), ("NADH", NADH), ("FADH2", FADH2)):
    x = chip(x, y + 62, f"{n} {label}", GREEN)
y += 142

# the conversion, which is the part textbooks get wrong
d.rounded_rectangle([M, y, M + CW, y + 236], radius=14, fill=CARD)
d.text((M + 30, y + 22), "The electron transport chain cashes them in", font=F_STAGE, fill=AMBER)
rows = [("1 NADH", "2.5 ATP", "3 ATP"), ("1 FADH2", "1.5 ATP", "2 ATP")]
d.text((M + 30, y + 76), "", font=F_LBL, fill=DIM)
d.text((M + 430, y + 76), "modern", font=F_LBL, fill=GREEN)
d.text((M + 700, y + 76), "old textbooks", font=F_LBL, fill=RED)
yy = y + 110
for a, new, old in rows:
    d.text((M + 30, yy), a, font=F_NUM, fill=WHITE)
    d.text((M + 430, yy), new, font=F_NUM, fill=GREEN)
    d.text((M + 700, yy), old, font=F_NUM, fill=RED)
    yy += 52
note = "Pumping protons does not divide evenly into whole ATP, so the ratios are not integers."
assert M + 30 + d.textlength(note, font=F_LBL) < M + CW - 20, "conversion note overflows"
d.text((M + 30, y + 196), note, font=F_LBL, fill=DIM)
y += 260

# the answer
d.rounded_rectangle([M, y, M + CW, y + 210], radius=14, fill=P["PANEL"])
d.text((M + 30, y + 22), "So, per glucose", font=F_STAGE, fill=GREEN)
d.text((M + 30, y + 74), f"{LOW} to {HIGH} ATP", font=F_TITLE, fill=WHITE)
expl = [
    f"{LOW} with the glycerol-3-phosphate shuttle: the glycolytic",
    "NADH arrives as FADH2 and loses a whole ATP.",
    "",
    f"{HIGH} with the malate-aspartate shuttle: it arrives as NADH.",
]
for i, line in enumerate(expl):
    if not line:
        continue
    assert M + 560 + d.textlength(line, font=F_LBL) < M + CW - 20, f"shuttle line {i} overflows"
    d.text((M + 560, y + 76 + i * 32), line, font=F_LBL, fill=GRAY)
y += 234

# old vs new
d.rounded_rectangle([M, y, M + CW, y + 130], radius=14, fill=CARD)
d.text((M + 30, y + 20), "Why you may have learned 36 to 38", font=F_STAGE, fill=RED)
lines = [
    f"Older books used 3 ATP per NADH and 2 per FADH2, which gives {OLD_LOW} to {OLD_HIGH}.",
    "Same pathway, same molecules. Only the conversion rate is out of date.",
]
for i, line in enumerate(lines):
    assert M + 30 + d.textlength(line, font=F_BODY) < M + CW - 20, f"old-vs-new line {i} overflows"
    d.text((M + 30, y + 64 + i * 34), line, font=F_BODY, fill=GRAY)
y += 158

d.line([(M, y), (M + CW, y)], fill=LINE, width=2)
y += 26
foot = [
    "Glycolysis nets 2 ATP because 4 are made and 2 are spent priming the sugar.",
    "The citric acid cycle makes GTP, counted as ATP here since the cell converts one to the other freely.",
    "Real yield is lower still: mitochondria leak protons, so treat 30 to 32 as a ceiling, not a measurement.",
]
for i, line in enumerate(foot):
    assert M + d.textlength(line, font=F_FOOT) < W - M, f"footer line {i} overflows"
    d.text((M, y + 34 * i), line, font=F_FOOT, fill=GRAY if i < 2 else DIM)
y += 34 * len(foot) + 26

assert y + 46 < H, f"content overflows canvas: needs {y + 46}, have {H}"
d.text((M, y), "biochemtools.com", font=F_DOM, fill=WHITE)
tag = "free, no signup  /  CC BY 4.0"
d.text((W - M - d.textlength(tag, font=F_FOOT), y + 10), tag, font=F_FOOT, fill=DIM)

out = BUILD_DIR + "/atp-yield-guide%s.png" % suffix()
img.save(out)
print("saved", out, img.size)
print(f"verified: {DIRECT} ATP + {NADH} NADH + {FADH2} FADH2 -> {LOW}-{HIGH} modern, {OLD_LOW}-{OLD_HIGH} old")
