#!/usr/bin/env python3
"""The urea cycle in 5 steps, as a shareable chart.

Steps, compartments, nitrogen sources and ATP costs are taken from the urea cycle
section of amino-acid-catabolism-explorer.html. The accounting is summed from the
step list and asserted against the known net: 2 nitrogen atoms disposed of per turn
for 4 ATP-equivalents.
"""
import os as _os
BUILD_DIR = _os.path.join(_os.path.dirname(_os.path.abspath(__file__)), "build")
_os.makedirs(BUILD_DIR, exist_ok=True)
from PIL import Image, ImageDraw, ImageFont
from lightmode import theme, suffix

LIGHT, P = theme()

# step, enzyme, reaction, compartment, ATP-equivalents, nitrogen atoms in, note
STEPS = [
    (1, "CPS1", "NH4+ + HCO3- + 2 ATP  ->  carbamoyl phosphate", "Mitochondria", 2, 1,
     "The committed, rate-limiting step. Needs N-acetylglutamate as an obligate activator."),
    (2, "OTC", "Carbamoyl phosphate + ornithine  ->  citrulline", "Mitochondria", 0, 0,
     "Citrulline is exported to the cytosol for the rest of the cycle."),
    (3, "Argininosuccinate synthetase", "Citrulline + aspartate + ATP  ->  argininosuccinate", "Cytosol", 2, 1,
     "ATP goes to AMP + PPi, which costs 2 ATP-equivalents, not 1."),
    (4, "Argininosuccinase", "Argininosuccinate  ->  arginine + fumarate", "Cytosol", 0, 0,
     "The fumarate released here feeds straight into the citric acid cycle."),
    (5, "Arginase", "Arginine + H2O  ->  urea + ornithine", "Cytosol", 0, 0,
     "Urea is excreted. Ornithine returns to the mitochondria to start the next turn."),
]

ATP = sum(s[4] for s in STEPS)
NITROGEN = sum(s[5] for s in STEPS)
assert len(STEPS) == 5, "the urea cycle has 5 steps"
assert (ATP, NITROGEN) == (4, 2), f"accounting wrong: {ATP} ATP, {NITROGEN} N"
MITO = [s for s in STEPS if s[3] == "Mitochondria"]
assert len(MITO) == 2, "steps 1 and 2 are mitochondrial"

BG, CARD, LINE = P["BG"], P["CARD"], P["LINE"]
WHITE, GRAY, DIM = P["WHITE"], P["GRAY"], P["DIM"]
GREEN, AMBER, RED, BLUE, PURPLE = P["GREEN"], P["AMBER"], P["RED"], P["BLUE"], P["PURPLE"]
COMPART = {"Mitochondria": PURPLE, "Cytosol": BLUE}

B = "/System/Library/Fonts/Supplemental/Arial Bold.ttf"
R_ = "/System/Library/Fonts/Supplemental/Arial.ttf"
f = lambda p, s: ImageFont.truetype(p, s)
F_TITLE, F_SUB = f(B, 56), f(R_, 27)
F_N = f(B, 34)
F_ENZ = f(B, 28)
F_RXN = f(R_, 25)
F_NOTE = f(R_, 22)
F_TAG = f(B, 20)
F_BIG = f(B, 42)
F_H = f(B, 22)
F_FOOT = f(R_, 23)
F_DOM = f(B, 33)

W, M = 1560, 60
CW = W - 2 * M
ROW = 150
H = 300 + len(STEPS) * ROW + 380

img = Image.new("RGB", (W, H), BG)
d = ImageDraw.Draw(img)
d.rectangle([0, 0, W, 12], fill=GREEN)

d.text((M, 58), "The urea cycle in 5 steps", font=F_TITLE, fill=WHITE)
d.text((M + 2, 134), f"Two nitrogen atoms disposed of per turn, for {ATP} ATP-equivalents. They arrive from two different places.",
       font=F_SUB, fill=GRAY)


def tag(x, y, text, colour):
    tw = d.textlength(text, font=F_TAG)
    d.rounded_rectangle([x, y, x + tw + 24, y + 32], radius=8, fill=P["CHIP"])
    d.text((x + 12, y + 5), text, font=F_TAG, fill=colour)
    return x + tw + 24 + 10


y = 216
for n, enz, rxn, comp, atp, nitro, note in STEPS:
    col = COMPART[comp]
    d.rounded_rectangle([M, y, M + CW, y + ROW - 14], radius=14, fill=CARD)
    d.rectangle([M, y + 16, M + 5, y + ROW - 32], fill=col)
    d.text((M + 26, y + 20), str(n), font=F_N, fill=col)
    d.text((M + 76, y + 18), enz, font=F_ENZ, fill=WHITE)
    assert M + 78 + d.textlength(rxn, font=F_RXN) < M + CW - 20, f"reaction {n} overflows"
    d.text((M + 78, y + 56), rxn, font=F_RXN, fill=GRAY)
    assert M + 78 + d.textlength(note, font=F_NOTE) < M + CW - 20, f"note {n} overflows"
    d.text((M + 78, y + 92), note, font=F_NOTE, fill=DIM)
    x = M + CW - 20
    chips = [(comp, col)]
    if nitro:
        chips.insert(0, (f"+{nitro} N", GREEN))
    if atp:
        chips.insert(0, (f"-{atp} ATP", RED))
    for text, c in chips:
        tw = d.textlength(text, font=F_TAG)
        x -= tw + 24
        d.rounded_rectangle([x, y + 20, x + tw + 24, y + 52], radius=8, fill=P["CHIP"])
        d.text((x + 12, y + 25), text, font=F_TAG, fill=c)
        x -= 10
    y += ROW

y += 4
d.rounded_rectangle([M, y, M + CW, y + 176], radius=14, fill=P["PANEL"])
d.text((M + 26, y + 20), "Per turn", font=F_ENZ, fill=GREEN)
d.text((M + 26, y + 62), f"{NITROGEN} N out, {ATP} ATP in", font=F_BIG, fill=WHITE)
side = [
    "The first nitrogen comes from free ammonia at step 1.",
    "The second comes from aspartate at step 3, not from ammonia.",
    "That second one is the detail most people miss.",
]
for i, t in enumerate(side):
    assert M + 620 + d.textlength(t, font=F_NOTE) < M + CW - 20, f"side {i} overflows"
    d.text((M + 620, y + 56 + i * 32), t, font=F_NOTE, fill=GRAY if i < 2 else AMBER)
y += 202

d.line([(M, y), (M + CW, y)], fill=LINE, width=2)
y += 24
foot = [
    "Steps 1 and 2 happen in the mitochondrion, steps 3 to 5 in the cytosol. Citrulline and ornithine cross between them.",
    "Step 3 costs 2 ATP-equivalents rather than 1, because ATP goes to AMP plus pyrophosphate rather than to ADP.",
    "The fumarate from step 4 links the urea cycle to the citric acid cycle, which is why the two are sometimes drawn together.",
]
for i, t in enumerate(foot):
    assert M + d.textlength(t, font=F_FOOT) < W - M, f"footer {i} overflows"
    d.text((M, y + 32 * i), t, font=F_FOOT, fill=GRAY if i < 2 else DIM)
y += 32 * len(foot) + 24

assert y + 44 < H, f"content overflows: needs {y + 44}, have {H}"
d.text((M, y), "biochemtools.com", font=F_DOM, fill=WHITE)
t = "free, no signup"
d.text((W - M - d.textlength(t, font=F_FOOT), y + 10), t, font=F_FOOT, fill=DIM)

out = BUILD_DIR + "/urea-guide%s.png" % suffix()
img.save(out)
print("saved", out, img.size)
print(f"verified: {len(STEPS)} steps, {NITROGEN} N per turn, {ATP} ATP-equivalents, "
      f"{len(MITO)} mitochondrial")
