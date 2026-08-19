#!/usr/bin/env python3
"""Blood type inheritance, as a shareable chart.

A 4x4 grid of every parent pairing and the child types it can produce, derived from
the ABO model rather than typed in. The two cells that matter are asserted: AB x O
can never make AB or O, and A x B can make all four.
"""
import os as _os
BUILD_DIR = _os.path.join(_os.path.dirname(_os.path.abspath(__file__)), "build")
_os.makedirs(BUILD_DIR, exist_ok=True)
import chartdata
import json
from PIL import Image, ImageDraw, ImageFont
from lightmode import theme, suffix

LIGHT, P = theme()
G = chartdata.blood_grid()
ORDER = ["A", "B", "AB", "O"]

assert G["ABxO"] == ["A", "B"], "AB x O must exclude AB and O"
assert G["AxB"] == ORDER, "A x B must be able to give all four"
assert G["AxA"] == ["A", "O"], "two type A parents can have a type O child"
assert G["OxO"] == ["O"]

BG, CARD, LINE = P["BG"], P["CARD"], P["LINE"]
WHITE, GRAY, DIM = P["WHITE"], P["GRAY"], P["DIM"]
GREEN, AMBER, RED, BLUE, PURPLE = P["GREEN"], P["AMBER"], P["RED"], P["BLUE"], P["PURPLE"]
TCOL = {"A": BLUE, "B": AMBER, "AB": PURPLE, "O": GRAY}

B = "/System/Library/Fonts/Supplemental/Arial Bold.ttf"
R_ = "/System/Library/Fonts/Supplemental/Arial.ttf"
f = lambda p, s: ImageFont.truetype(p, s)
F_TITLE, F_SUB = f(B, 56), f(R_, 27)
F_HDR = f(B, 34)
F_CELL = f(B, 27)
F_LBL = f(B, 20)
F_NOTE = f(R_, 23)
F_BIG = f(B, 32)
F_FOOT = f(R_, 23)
F_DOM = f(B, 33)

W, M = 1560, 60
CW = W - 2 * M
CELL, HDR = 300, 150
GRID_W = HDR + CELL * 4
H = 1800

img = Image.new("RGB", (W, H), BG)
d = ImageDraw.Draw(img)
d.rectangle([0, 0, W, 12], fill=GREEN)
d.text((M, 54), "What blood type can a child be?", font=F_TITLE, fill=WHITE)
SUB = "Every parent pairing and what a child can be. A blood type does not fix a genotype."
assert M + 2 + d.textlength(SUB, font=F_SUB) < W - M, "subtitle overflows the canvas"
d.text((M + 2, 128), SUB, font=F_SUB, fill=GRAY)

ox, oy = M + (CW - GRID_W) // 2, 210
d.text((ox + 14, oy + 46), "PARENT 1", font=F_LBL, fill=DIM)
for j, p2 in enumerate(ORDER):
    x = ox + HDR + j * CELL
    d.text((x + (CELL - d.textlength(p2, font=F_HDR)) / 2, oy + 34), p2, font=F_HDR, fill=TCOL[p2])
d.text((ox + HDR + (CELL * 4 - d.textlength("PARENT 2", font=F_LBL)) / 2, oy + 4), "PARENT 2", font=F_LBL, fill=DIM)

y = oy + 96
for i, p1 in enumerate(ORDER):
    d.text((ox + (HDR - d.textlength(p1, font=F_HDR)) / 2, y + (CELL * 0.42) - 20), p1, font=F_HDR, fill=TCOL[p1])
    for j, p2 in enumerate(ORDER):
        x = ox + HDR + j * CELL
        poss = G[p1 + "x" + p2]
        # the pairings that surprise people get the accent border
        notable = len(poss) == 4 or (p1 == "AB" and p2 == "O") or (p2 == "AB" and p1 == "O")
        d.rounded_rectangle([x + 4, y + 4, x + CELL - 4, y + int(CELL * 0.84)], radius=12,
                            fill=P["CHIP"] if notable else CARD,
                            outline=AMBER if notable else LINE, width=2 if notable else 1)
        txt = "  ".join(poss)
        tw = d.textlength(txt, font=F_CELL)
        cx = x + (CELL - tw) / 2
        for t in poss:
            wpart = d.textlength(t, font=F_CELL)
            d.text((cx, y + int(CELL * 0.30)), t, font=F_CELL, fill=TCOL[t])
            cx += wpart + d.textlength("  ", font=F_CELL)
        miss = [t for t in ORDER if t not in poss]
        if miss:
            m = "never " + ", ".join(miss)
            d.text((x + (CELL - d.textlength(m, font=F_NOTE)) / 2, y + int(CELL * 0.52)), m, font=F_NOTE, fill=DIM)
    y += int(CELL * 0.86)

y += 18
d.rounded_rectangle([M, y, M + CW, y + 128], radius=14, fill=P["WARM"])
d.text((M + 26, y + 18), "The two worth memorising", font=F_BIG, fill=AMBER)
LINE1 = "AB x O gives A or B, not AB or O. A x B can give all four, and is the only pairing that can."
assert M + 26 + d.textlength(LINE1, font=F_NOTE) < M + CW - 20, "panel line 1 overflows"
d.text((M + 26, y + 60), LINE1, font=F_NOTE, fill=WHITE)
# "a blood test cannot tell you which" was incomplete: a blood TYPE test cannot,
# but genotyping can. Raised by u/nautilist on r/genetics, who has two type A
# parents and a type O sibling, all confirmed AO by retail DNA testing.
LINE2 = "Two type A parents can have a type O child. Type A is AA or AO, and a blood type test cannot separate them. A DNA test can."
assert M + 26 + d.textlength(LINE2, font=F_NOTE) < M + CW - 20, "panel line 2 overflows"
d.text((M + 26, y + 90), LINE2, font=F_NOTE, fill=GRAY)
y += 152

d.line([(M, y), (M + CW, y)], fill=LINE, width=2)
y += 22
# The cis-AB exception was raised by u/Dorudol on r/genetics, who is themselves an O
# child of a cis-AB father. A single allele encodes a transferase making both antigens,
# so the genotype is cisAB/O rather than A/B and that parent can pass an O.
foot = [
    "Three alleles, not two. A and B are codominant so carrying both shows both antigens, and O is recessive to each.",
    "One real exception to the AB row: a cis-AB parent carries both antigens on one allele and an O on the other,",
    "so cis-AB crossed with O can give a type O child. It is rare, and most often seen in Korean and Japanese families.",
    "Rh is a separate gene. Two Rh positive parents who both carry a hidden d have a 1 in 4 chance of an Rh negative child.",
    "This can exclude a parent but never confirm one. Millions of people share any given type, so a match proves nothing.",
]
for i, t in enumerate(foot):
    assert M + d.textlength(t, font=F_FOOT) < W - M, f"footer {i} overflows"
    d.text((M, y + 31 * i), t, font=F_FOOT, fill=GRAY if i < 2 else DIM)
y += 31 * len(foot) + 20

assert y + 44 < H, f"content overflows: needs {y+44}, have {H}"
d.text((M, y), "biochemtools.com", font=F_DOM, fill=WHITE)
t = "free, no signup  /  CC BY 4.0"
d.text((W - M - d.textlength(t, font=F_FOOT), y + 10), t, font=F_FOOT, fill=DIM)

out = BUILD_DIR + "/bloodtype-guide%s.png" % suffix()
img.save(out)
print("saved", out, img.size)
print("verified: AB x O ->", G["ABxO"], "| A x B ->", G["AxB"], "| A x A ->", G["AxA"])
