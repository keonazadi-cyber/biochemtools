#!/usr/bin/env python3
"""The citric acid cycle in 8 steps, as a shareable chart.

Steps come from the STEPS array in citric-acid-cycle-explorer.html, so the chart and
the tool cannot disagree. The per-turn yield is summed from the steps themselves and
asserted against 3 NADH, 1 FADH2, 1 GTP and 2 CO2.
"""
import os as _os
BUILD_DIR = _os.path.join(_os.path.dirname(_os.path.abspath(__file__)), "build")
_os.makedirs(BUILD_DIR, exist_ok=True)
import chartdata
import json
from PIL import Image, ImageDraw, ImageFont
from lightmode import theme, suffix

LIGHT, P = theme()
S = chartdata.tca()

NADH = sum(s.get("nadh", 0) for s in S)
FADH2 = sum(s.get("fadh2", 0) for s in S)
GTP = sum(s.get("gtp", 0) for s in S)
CO2 = sum(s.get("co2", 0) for s in S)
REG = [s for s in S if s.get("reg")]
assert len(S) == 8, f"the citric acid cycle has 8 steps, got {len(S)}"
assert (NADH, FADH2, GTP, CO2) == (3, 1, 1, 2), \
    f"per-turn yield wrong: {NADH} NADH, {FADH2} FADH2, {GTP} GTP, {CO2} CO2"
assert len(REG) == 3, f"expected 3 regulated steps, got {len(REG)}"

# what one turn is worth downstream, using the modern conversion rates
ATP_EQ = NADH * 2.5 + FADH2 * 1.5 + GTP
assert ATP_EQ == 10, f"one turn should be 10 ATP-equivalents, got {ATP_EQ}"

BG, CARD, LINE = P["BG"], P["CARD"], P["LINE"]
WHITE, GRAY, DIM = P["WHITE"], P["GRAY"], P["DIM"]
GREEN, AMBER, RED, BLUE, PURPLE = P["GREEN"], P["AMBER"], P["RED"], P["BLUE"], P["PURPLE"]

B = "/System/Library/Fonts/Supplemental/Arial Bold.ttf"
R_ = "/System/Library/Fonts/Supplemental/Arial.ttf"
f = lambda p, s: ImageFont.truetype(p, s)
F_TITLE, F_SUB = f(B, 56), f(R_, 27)
F_N = f(B, 32)
F_RX = f(B, 27)
F_ENZ = f(R_, 23)
F_NOTE = f(R_, 22)
F_TAG = f(B, 21)
F_BIG = f(B, 42)
F_H = f(B, 22)
F_FOOT = f(R_, 23)
F_DOM = f(B, 33)

W, M = 1560, 60
CW = W - 2 * M
ROW = 132
H = 300 + len(S) * ROW + 420

img = Image.new("RGB", (W, H), BG)
d = ImageDraw.Draw(img)
d.rectangle([0, 0, W, 12], fill=GREEN)

d.text((M, 58), "The citric acid cycle in 8 steps", font=F_TITLE, fill=WHITE)
d.text((M + 2, 134), f"One turn yields {NADH} NADH, {FADH2} FADH2 and {GTP} GTP, which is worth about {ATP_EQ:.0f} ATP downstream.",
       font=F_SUB, fill=GRAY)

y = 216
d.text((M + 78, y), "STEP", font=F_H, fill=DIM)
d.text((M + CW - 300, y), "YIELD", font=F_H, fill=DIM)
y += 30
d.line([(M, y), (M + CW, y)], fill=LINE, width=2)
y += 12

for i, s in enumerate(S, 1):
    reg = s.get("reg", False)
    col = AMBER if reg else GREEN
    d.rounded_rectangle([M, y, M + CW, y + ROW - 14], radius=13, fill=CARD)
    d.rectangle([M, y + 14, M + 5, y + ROW - 30], fill=col if reg else LINE)
    d.text((M + 26, y + 22), str(i), font=F_N, fill=col if reg else DIM)
    d.text((M + 78, y + 14), s["rx"], font=F_RX, fill=WHITE)
    d.text((M + 80, y + 50), s["enz"], font=F_ENZ, fill=col)
    # truncate on a word boundary and mark it, never mid-word
    note = s.get("note", "")
    if d.textlength(note, font=F_NOTE) > CW - 400:
        words = note.split()
        while words and d.textlength(" ".join(words) + "...", font=F_NOTE) > CW - 400:
            words.pop()
        note = " ".join(words) + "..."
    d.text((M + 80, y + 80), note, font=F_NOTE, fill=DIM)

    x = M + CW - 20
    chips = []
    if s.get("co2"):   chips.append((f"{s['co2']} CO2", DIM))
    if s.get("gtp"):   chips.append((f"+{s['gtp']} GTP", PURPLE))
    if s.get("fadh2"): chips.append((f"+{s['fadh2']} FADH2", BLUE))
    if s.get("nadh"):  chips.append((f"+{s['nadh']} NADH", GREEN))
    for text, c in chips:
        tw = d.textlength(text, font=F_TAG)
        x -= tw + 24
        d.rounded_rectangle([x, y + 18, x + tw + 24, y + 52], radius=8, fill=P["CHIP"])
        d.text((x + 12, y + 24), text, font=F_TAG, fill=c)
        x -= 10
    if not chips:
        t = "no yield"
        d.text((M + CW - 20 - d.textlength(t, font=F_NOTE), y + 26), t, font=F_NOTE, fill=DIM)
    if reg:
        t = "regulated"
        d.text((M + CW - 20 - d.textlength(t, font=F_NOTE), y + 76), t, font=F_NOTE, fill=AMBER)
    y += ROW

y += 6
d.rounded_rectangle([M, y, M + CW, y + 176], radius=14, fill=P["PANEL"])
d.text((M + 26, y + 20), "Per turn", font=F_RX, fill=GREEN)
d.text((M + 26, y + 60), f"{NADH} NADH, {FADH2} FADH2, {GTP} GTP", font=F_BIG, fill=WHITE)
side = [
    f"Worth about {ATP_EQ:.0f} ATP once the electron transport chain cashes it in.",
    "Glucose gives two acetyl-CoA, so the cycle turns twice per glucose.",
    f"The {CO2} CO2 released per turn is the carbon you breathe out.",
]
for i, t in enumerate(side):
    assert M + 640 + d.textlength(t, font=F_NOTE) < M + CW - 20, f"side note {i} overflows"
    d.text((M + 640, y + 58 + i * 32), t, font=F_NOTE, fill=GRAY if i < 2 else AMBER)
y += 202

d.line([(M, y), (M + CW, y)], fill=LINE, width=2)
y += 24
foot = [
    "The three amber steps are the regulated ones: citrate synthase, isocitrate dehydrogenase, and alpha-ketoglutarate dehydrogenase.",
    "All three are inhibited by ATP and NADH, which is the cycle sensing that the cell already has enough energy.",
    "No oxygen appears anywhere in these eight steps, yet the cycle stops without it.",
    "In the matrix, NAD+ comes back from the electron transport chain, and that is where the oxygen is needed.",
]
for i, t in enumerate(foot):
    assert M + d.textlength(t, font=F_FOOT) < W - M, f"footer {i} overflows"
    d.text((M, y + 32 * i), t, font=F_FOOT, fill=GRAY if i < 2 else DIM)
y += 32 * len(foot) + 24

assert y + 44 < H, f"content overflows: needs {y + 44}, have {H}"
d.text((M, y), "biochemtools.com", font=F_DOM, fill=WHITE)
t = "free, no signup  /  CC BY 4.0"
d.text((W - M - d.textlength(t, font=F_FOOT), y + 10), t, font=F_FOOT, fill=DIM)

out = BUILD_DIR + "/tca-guide%s.png" % suffix()
img.save(out)
print("saved", out, img.size)
print(f"verified: {len(S)} steps, {NADH} NADH + {FADH2} FADH2 + {GTP} GTP + {CO2} CO2, "
      f"{len(REG)} regulated, {ATP_EQ:.0f} ATP-equivalents")
