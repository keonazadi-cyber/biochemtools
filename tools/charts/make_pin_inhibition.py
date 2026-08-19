#!/usr/bin/env python3
"""Pin 39: enzyme inhibition. Table-preview style, 1000x1500 for Pinterest.

The four signatures are re-derived from the same alpha model the full chart uses,
so the pin cannot drift from the chart or from the site. Nothing here is typed in
by hand except the wording.
"""
import os
from PIL import Image, ImageDraw, ImageFont

OUT = os.path.join(os.path.dirname(os.path.abspath(__file__)), "build")
os.makedirs(OUT, exist_ok=True)
W, H = 1000, 1500

BG, CARD, BORDER = (15, 17, 21), (23, 26, 33), (42, 46, 56)
WHITE, GRAY, LABEL, TEAL = (232, 234, 237), (154, 160, 170), (120, 128, 140), (93, 202, 165)
UP, DOWN, SAME = (226, 104, 95), (91, 155, 224), (154, 160, 170)

KM, VMAX, R = 25.0, 100.0, 2.0
MODELS = {
    "Competitive": (1 + R, 1.0),
    "Uncompetitive": (1.0, 1 + R),
    "Noncompetitive": (1 + R, 1 + R),
    "Mixed": None,
}
TELL = {
    "Competitive": "lines meet on the y-axis",
    "Uncompetitive": "lines stay parallel",
    "Noncompetitive": "lines meet on the x-axis",
    "Mixed": "meet off both axes",
}


def sig(a, ap):
    km, vm = KM * a / ap, VMAX / ap
    f = lambda new, old: "same" if abs(new - old) < 1e-9 else ("up" if new > old else "down")
    return f(km, KM), f(vm, VMAX)


ROWS = []
for name, m in MODELS.items():
    if m is None:
        ROWS.append((name, "either", "down", TELL[name]))
    else:
        km, vm = sig(*m)
        ROWS.append((name, km, vm, TELL[name]))

# the same guards the full chart runs, so a wrong pin cannot render
d_ = dict((r[0], r) for r in ROWS)
assert d_["Competitive"][1:3] == ("up", "same")
assert d_["Uncompetitive"][1:3] == ("down", "down")
assert d_["Noncompetitive"][1:3] == ("same", "down")

BOLD = "/System/Library/Fonts/Supplemental/Arial Bold.ttf"
REG = "/System/Library/Fonts/Supplemental/Arial.ttf"
f = lambda p, s: ImageFont.truetype(p, s)
F_PILL, F_TITLE, F_SUB = f(BOLD, 23), f(BOLD, 70), f(REG, 30)
F_HEAD, F_NAME, F_VAL, F_TELL = f(BOLD, 24), f(BOLD, 33), f(BOLD, 31), f(REG, 26)
F_FOOT, F_URL = f(REG, 27), f(BOLD, 36)

img = Image.new("RGB", (W, H), BG)
d = ImageDraw.Draw(img)
M = 64

y = 92
d.rounded_rectangle([M, y, M + 250, y + 46], radius=23, fill=(30, 34, 43))
d.text((M + 26, y + 12), "BIOCHEMISTRY", font=F_PILL, fill=TEAL)

y += 92
for line in ["Enzyme inhibition,", "all four types"]:
    d.text((M, y), line, font=F_TITLE, fill=WHITE)
    y += 84
y += 12
d.text((M, y), "What each one does to Km and Vmax,", font=F_SUB, fill=GRAY)
d.text((M, y + 40), "and how to tell them apart on a plot.", font=F_SUB, fill=GRAY)

y += 128
CARD_H = 620
d.rounded_rectangle([M, y, W - M, y + CARD_H], radius=20, fill=CARD, outline=BORDER, width=2)

cx = M + 34
d.text((cx, y + 30), "TYPE", font=F_HEAD, fill=LABEL)
d.text((cx + 330, y + 30), "Km", font=F_HEAD, fill=LABEL)
d.text((cx + 450, y + 30), "Vmax", font=F_HEAD, fill=LABEL)

ARROW = {"up": ("up", UP), "down": ("down", DOWN), "same": ("same", SAME), "either": ("either", SAME)}
ry = y + 82
for name, km, vm, tell in ROWS:
    d.line([(cx, ry), (W - M - 34, ry)], fill=BORDER, width=1)
    d.text((cx, ry + 22), name, font=F_NAME, fill=WHITE)
    for dx, v in ((330, km), (450, vm)):
        txt, col = ARROW[v]
        d.text((cx + dx, ry + 24), txt, font=F_VAL, fill=col)
    d.text((cx, ry + 66), tell, font=F_TELL, fill=GRAY)
    ry += 134

y += CARD_H + 46
d.rounded_rectangle([M, y, W - M, y + 132], radius=18, fill=(24, 32, 30), outline=(38, 62, 55), width=2)
d.text((M + 30, y + 26), "The one that trips people", font=F_HEAD, fill=TEAL)
d.text((M + 30, y + 62), "Uncompetitive lowers BOTH Km and Vmax.", font=F_TELL, fill=WHITE)
d.text((M + 30, y + 94), "That is why its lines stay parallel.", font=F_TELL, fill=WHITE)

y = H - 150
d.text((M, y), "Free chart, no signup", font=F_FOOT, fill=GRAY)
d.text((M, y + 42), "biochemtools.com", font=F_URL, fill=TEAL)

for name, km, vm, tell in ROWS:
    assert M + 34 + d.textlength(tell, font=F_TELL) < W - M - 34, name + " tell overflows"

p = os.path.join(OUT, "pin-39-enzyme-inhibition.png")
img.save(p)
print("saved " + p)
print("  verified: competitive Km up / Vmax same, uncompetitive both down, noncompetitive Km same")
