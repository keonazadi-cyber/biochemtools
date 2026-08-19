#!/usr/bin/env python3
"""Glycolysis in 10 steps, as a shareable chart.

The ATP and NADH accounting is summed from the step list itself and asserted against
the known net (2 ATP, 2 NADH per glucose), so the chart cannot contradict its own rows.
"""
import os as _os
BUILD_DIR = _os.path.join(_os.path.dirname(_os.path.abspath(__file__)), "build")
_os.makedirs(BUILD_DIR, exist_ok=True)
from PIL import Image, ImageDraw, ImageFont

# step, enzyme, ATP delta per glucose, NADH per glucose, note, irreversible?
STEPS = [
    ("Glucose to glucose-6-phosphate", "Hexokinase / glucokinase", -1, 0,
     "Traps glucose in the cell. The phosphate stops it leaving.", True),
    ("Glucose-6-P to fructose-6-P", "Phosphoglucose isomerase", 0, 0,
     "Aldose to ketose, so carbon 1 is free to be phosphorylated.", False),
    ("Fructose-6-P to fructose-1,6-bisP", "Phosphofructokinase-1", -1, 0,
     "THE control point of glycolysis. Committed step.", True),
    ("Fructose-1,6-bisP to two 3-carbons", "Aldolase", 0, 0,
     "Splits the six-carbon sugar into DHAP and G3P.", False),
    ("DHAP to G3P", "Triose phosphate isomerase", 0, 0,
     "Converts the other half, so everything below runs twice.", False),
    ("G3P to 1,3-bisphosphoglycerate", "G3P dehydrogenase", 0, 2,
     "First energy payoff. Oxidation captured as NADH.", False),
    ("1,3-BPG to 3-phosphoglycerate", "Phosphoglycerate kinase", 2, 0,
     "Substrate-level phosphorylation, no oxygen needed.", False),
    ("3-PG to 2-phosphoglycerate", "Phosphoglycerate mutase", 0, 0,
     "Moves the phosphate to set up the next step.", False),
    ("2-PG to phosphoenolpyruvate", "Enolase", 0, 0,
     "Loses water, creating a very high-energy phosphate bond.", False),
    ("PEP to pyruvate", "Pyruvate kinase", 2, 0,
     "Second substrate-level phosphorylation. Irreversible.", True),
]

INVESTED = -sum(a for _, _, a, _, _, _ in STEPS if a < 0)
MADE = sum(a for _, _, a, _, _, _ in STEPS if a > 0)
NET_ATP = MADE - INVESTED
NET_NADH = sum(n for _, _, _, n, _, _ in STEPS)
IRREV = [s[0] for s in STEPS if s[5]]
assert len(STEPS) == 10, "glycolysis has 10 steps"
assert (INVESTED, MADE, NET_ATP, NET_NADH) == (2, 4, 2, 2), \
    f"accounting wrong: invested {INVESTED}, made {MADE}, net {NET_ATP}, NADH {NET_NADH}"
assert len(IRREV) == 3, "three irreversible steps: hexokinase, PFK-1, pyruvate kinase"

from lightmode import theme, suffix
LIGHT, P = theme()
BG, CARD, LINE = P["BG"], P["CARD"], P["LINE"]
WHITE, GRAY, DIM = P["WHITE"], P["GRAY"], P["DIM"]
GREEN, AMBER, RED, BLUE = P["GREEN"], P["AMBER"], P["RED"], P["BLUE"]

B = "/System/Library/Fonts/Supplemental/Arial Bold.ttf"
R_ = "/System/Library/Fonts/Supplemental/Arial.ttf"
f = lambda p, s: ImageFont.truetype(p, s)
F_TITLE, F_SUB = f(B, 58), f(R_, 28)
F_N = f(B, 30)
F_STEP = f(B, 27)
F_ENZ = f(R_, 23)
F_NOTE = f(R_, 23)
F_CHIP = f(B, 22)
F_H = f(B, 23)
F_BIG = f(B, 40)
F_FOOT = f(R_, 24)
F_DOM = f(B, 34)

W, M = 1560, 60
CW = W - 2 * M
ROW = 116
H = 300 + len(STEPS) * ROW + 430
img = Image.new("RGB", (W, H), BG)
d = ImageDraw.Draw(img)
d.rectangle([0, 0, W, 12], fill=GREEN)

d.text((M, 60), "Glycolysis in 10 steps", font=F_TITLE, fill=WHITE)
d.text((M + 2, 142), f"One glucose to two pyruvate. Spend {INVESTED} ATP, make {MADE}, keep {NET_ATP}, plus {NET_NADH} NADH.",
       font=F_SUB, fill=GRAY)

y = 226
d.text((M + 76, y), "STEP", font=F_H, fill=DIM)
d.text((M + 960, y), "YIELD", font=F_H, fill=DIM)
y += 32
d.line([(M, y), (M + CW, y)], fill=LINE, width=2)
y += 12


def chip(x, yy, text, colour):
    tw = d.textlength(text, font=F_CHIP)
    d.rounded_rectangle([x, yy, x + tw + 26, yy + 38], radius=9, fill=P["CHIP"])
    d.text((x + 13, yy + 6), text, font=F_CHIP, fill=colour)
    return x + tw + 26 + 10


for i, (name, enz, atp, nadh, note, irrev) in enumerate(STEPS, 1):
    col = AMBER if irrev else GREEN
    d.rounded_rectangle([M, y, M + CW, y + ROW - 12], radius=12, fill=CARD)
    d.rectangle([M, y + 14, M + 5, y + ROW - 26], fill=col if irrev else LINE)
    d.text((M + 26, y + 26), str(i), font=F_N, fill=col if irrev else DIM)
    d.text((M + 76, y + 14), name, font=F_STEP, fill=WHITE)
    d.text((M + 78, y + 48), enz, font=F_ENZ, fill=col)
    assert M + 78 + d.textlength(note, font=F_NOTE) < M + 950, f"note {i} overflows"
    d.text((M + 78, y + 76), note, font=F_NOTE, fill=DIM)
    x = M + 960
    if atp:
        x = chip(x, y + 20, f"{atp:+d} ATP", RED if atp < 0 else GREEN)
    if nadh:
        x = chip(x, y + 20, f"+{nadh} NADH", BLUE)
    if not atp and not nadh:
        d.text((M + 960, y + 26), "setup only", font=F_NOTE, fill=DIM)
    if irrev:
        t = "irreversible"
        d.text((M + CW - 20 - d.textlength(t, font=F_NOTE), y + 74), t, font=F_NOTE, fill=AMBER)
    y += ROW

y += 10
d.rounded_rectangle([M, y, M + CW, y + 150], radius=14, fill=P["PANEL"])
d.text((M + 26, y + 22), "Net per glucose", font=F_STEP, fill=GREEN)
d.text((M + 26, y + 60), f"{NET_ATP} ATP  and  {NET_NADH} NADH", font=F_BIG, fill=WHITE)
side = [
    f"Spend {INVESTED} early, make {MADE} later. The payoff steps run twice,",
    "because the sugar split in half back at step 4.",
    "No oxygen is used anywhere in these ten steps.",
]
for i, t in enumerate(side):
    assert M + 620 + d.textlength(t, font=F_NOTE) < M + CW - 20, f"net note {i} overflows"
    d.text((M + 620, y + 46 + i * 30), t, font=F_NOTE, fill=GRAY if i < 2 else DIM)
y += 176

d.line([(M, y), (M + CW, y)], fill=LINE, width=2)
y += 24
foot = [
    "The three amber steps are irreversible, which is why gluconeogenesis needs different enzymes to get back.",
    "Phosphofructokinase-1 is the committed step and the main regulation point. It is inhibited by ATP and citrate.",
    "The 2 NADH still need shuttling into the mitochondrion, which costs ATP. See the ATP yield chart for that.",
]
for i, t in enumerate(foot):
    assert M + d.textlength(t, font=F_FOOT) < W - M, f"footer {i} overflows"
    d.text((M, y + 34 * i), t, font=F_FOOT, fill=GRAY if i < 2 else DIM)
y += 34 * len(foot) + 26

assert y + 46 < H, f"content overflows: needs {y + 46}, have {H}"
d.text((M, y), "biochemtools.com", font=F_DOM, fill=WHITE)
tag = "free, no signup  /  CC BY 4.0"
d.text((W - M - d.textlength(tag, font=F_FOOT), y + 10), tag, font=F_FOOT, fill=DIM)

out = BUILD_DIR + "/glycolysis-guide%s.png" % suffix()
img.save(out)
print("saved", out, img.size)
print(f"verified: {len(STEPS)} steps, spend {INVESTED}, make {MADE}, net {NET_ATP} ATP + {NET_NADH} NADH")
print("irreversible:", ", ".join(s.split(" to ")[0] for s in IRREV))
