#!/usr/bin/env python3
"""The standard genetic code as a shareable image, classic first/second/third base layout.
Codon data parsed from codon-chart.html and verified against the standard code."""
import os as _os
BUILD_DIR = _os.path.join(_os.path.dirname(_os.path.abspath(__file__)), "build")
_os.makedirs(BUILD_DIR, exist_ok=True)
import chartdata
import json
from PIL import Image, ImageDraw, ImageFont

CODON = chartdata.codons()
AA = chartdata.amino_acids()
NAME = {a["c1"]: a["c3"] for a in AA}
CLASS = {a["c1"]: a["cls"] for a in AA}
NAME["*"] = "Stop"
CLASS["*"] = "Stop"

from lightmode import theme, suffix
LIGHT, P = theme()
BG, CELL, LINE = P["BG"], P["CARD"], P["LINE"]
WHITE, GRAY, DIM = P["WHITE"], P["GRAY"], P["DIM"]
COL = {"Nonpolar": P["NONPOLAR"], "Aromatic": P["AROMATIC"],
       "Polar": P["POLAR"], "Acidic": P["ACIDIC"],
       "Basic": P["BASIC"], "Stop": P["RED"]}
START = P["AMBER"]

B = "/System/Library/Fonts/Supplemental/Arial Bold.ttf"
R = "/System/Library/Fonts/Supplemental/Arial.ttf"
M = "/System/Library/Fonts/Menlo.ttc"
f = lambda p, s: ImageFont.truetype(p, s)
F_TITLE, F_SUB = f(B, 58), f(R, 29)
F_AXIS = f(B, 30)
F_BASE = f(B, 34)
F_CODON = ImageFont.truetype(M, 27)
F_AA = f(B, 26)
F_LEG = f(R, 25)
F_FOOT = f(R, 25)
F_DOM = f(B, 34)

BASES = "UCAG"
LEFT, TOPY = 96, 250
CW, RH = 322, 52
W = LEFT + CW * 4 + 96
H = TOPY + 60 + (RH * 4 + 26) * 4 + 250

img = Image.new("RGB", (W, H), BG)
d = ImageDraw.Draw(img)
d.rectangle([0, 0, W, 12], fill=(55, 138, 221))

d.text((60, 60), "The genetic code", font=F_TITLE, fill=WHITE)
d.text((62, 136), "All 64 codons, coloured by amino acid class. AUG starts, UAA UAG UGA stop.",
       font=F_SUB, fill=GRAY)

# second-base header
d.text((60, TOPY - 44), "1st", font=F_AXIS, fill=DIM)
for j, b in enumerate(BASES):
    x = LEFT + CW * j
    d.text((x + CW // 2 - 10, TOPY - 46), b, font=F_BASE, fill=DIM)
d.text((LEFT + CW * 4 + 24, TOPY - 44), "3rd", font=F_AXIS, fill=DIM)
d.text((LEFT + CW * 2 - 60, TOPY - 92), "2nd base", font=F_AXIS, fill=DIM)

y = TOPY
for i, b1 in enumerate(BASES):
    block_h = RH * 4
    d.text((52, y + block_h // 2 - 22), b1, font=F_BASE, fill=DIM)
    for k, b3 in enumerate(BASES):
        yy = y + RH * k
        d.text((LEFT + CW * 4 + 30, yy + 12), b3, font=F_BASE, fill=DIM)
        for j, b2 in enumerate(BASES):
            x = LEFT + CW * j
            if k % 2 == 0:
                d.rectangle([x, yy, x + CW - 8, yy + RH - 4], fill=CELL)
            cod = b1 + b2 + b3
            aa = CODON[cod]
            c = COL[CLASS[aa]]
            d.text((x + 16, yy + 12), cod, font=F_CODON, fill=WHITE)
            label = NAME[aa]
            if cod == "AUG":
                label += "  start"
                c = START
            elif aa == "*":
                label = "STOP"
            d.text((x + 118, yy + 13), label, font=F_AA, fill=c)
    y += block_h + 26

# legend
y += 10
d.line([(56, y), (W - 56, y)], fill=LINE, width=2)
y += 28
lx = 60
for cls in ["Nonpolar", "Aromatic", "Polar", "Acidic", "Basic", "Stop"]:
    c = COL[cls]
    d.rectangle([lx, y + 6, lx + 18, y + 24], fill=c)
    d.text((lx + 28, y + 2), cls, font=F_LEG, fill=c)
    lx += 40 + int(d.textlength(cls, font=F_LEG)) + 42
d.rectangle([lx, y + 6, lx + 18, y + 24], fill=START)
d.text((lx + 28, y + 2), "Start", font=F_LEG, fill=START)

y += 52
foot = [("64 codons but only 20 amino acids, so most are read by more than one.", GRAY),
        ("Leu, Ser and Arg have six codons each. Met and Trp have exactly one.", GRAY),
        ("Standard code (NCBI translation table 1). Some mitochondria and ciliates differ.", DIM)]
for n, (line, colr) in enumerate(foot):
    wpx = d.textlength(line, font=F_FOOT)
    assert 60 + wpx < W - 56, "footer line %d overflows: %d > %d" % (n, 60 + wpx, W - 56)
    d.text((60, y + 36 * n), line, font=F_FOOT, fill=colr)
y += 36 * (len(foot) - 2)

d.text((60, y + 96), "biochemtools.com", font=F_DOM, fill=WHITE)
tag = "free, no signup  /  CC BY 4.0"
d.text((W - 60 - d.textlength(tag, font=F_FOOT), y + 104), tag, font=F_FOOT, fill=DIM)

out = BUILD_DIR + "/codon-chart-guide%s.png" % suffix()
img.save(out)
print("saved", out, img.size)
