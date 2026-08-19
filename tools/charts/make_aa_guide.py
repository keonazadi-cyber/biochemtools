#!/usr/bin/env python3
"""Full 20-amino-acid reference chart as a shareable image.
Data pulled straight from the live amino-acid-chart.html so the two cannot disagree."""
import os as _os
BUILD_DIR = _os.path.join(_os.path.dirname(_os.path.abspath(__file__)), "build")
_os.makedirs(BUILD_DIR, exist_ok=True)
import chartdata
import json
from PIL import Image, ImageDraw, ImageFont

AA = chartdata.amino_acids()

from lightmode import theme, suffix
LIGHT, P = theme()
BG, CARD, LINE = P["BG"], P["CARD"], P["LINE"]
WHITE, GRAY, DIM = P["WHITE"], P["GRAY"], P["DIM"]
CLS = {"Nonpolar": P["NONPOLAR"], "Aromatic": P["AROMATIC"],
       "Polar": P["POLAR"], "Acidic": P["ACIDIC"], "Basic": P["BASIC"]}
ORDER = ["Nonpolar", "Aromatic", "Polar", "Acidic", "Basic"]

B = "/System/Library/Fonts/Supplemental/Arial Bold.ttf"
R = "/System/Library/Fonts/Supplemental/Arial.ttf"
f = lambda p, s: ImageFont.truetype(p, s)
F_TITLE, F_SUB = f(B, 60), f(R, 30)
F_GRP = f(B, 26)
F_HD = f(B, 22)
F_C1 = f(B, 40)
F_C3, F_NAME = f(B, 27), f(R, 27)
F_NUM = f(R, 27)
F_NUMB = f(B, 27)
F_FOOT = f(R, 26)
F_DOM = f(B, 34)

W = 1500
ROW, GRP_H = 60, 58
H = 250 + sum(GRP_H + ROW * len([a for a in AA if a["cls"] == c]) for c in ORDER) + 460

img = Image.new("RGB", (W, H), BG)
d = ImageDraw.Draw(img)
d.rectangle([0, 0, W, 12], fill=(95, 204, 167))

d.text((60, 62), "The 20 amino acids", font=F_TITLE, fill=WHITE)
d.text((62, 140), "pKa, isoelectric point, molecular weight, hydropathy, and which are essential",
       font=F_SUB, fill=GRAY)

# columns
X = {"c1": 62, "c3": 118, "name": 205, "pk1": 470, "pk2": 625,
     "pkr": 775, "pI": 910, "mw": 1030, "hyd": 1185, "ess": 1320}

y = 215
hdrs = [("c1", "AA"), ("name", "NAME"), ("pk1", "pKa COOH"),
        ("pk2", "pKa NH3"), ("pkr", "pKa R"), ("pI", "pI"), ("mw", "MW"),
        ("hyd", "HYDRO"), ("ess", "ESSENTIAL")]
for k, label in hdrs:
    d.text((X[k], y), label, font=F_HD, fill=DIM)
y += 34
d.line([(56, y), (W - 56, y)], fill=LINE, width=2)
y += 14

for cls in ORDER:
    rows = [a for a in AA if a["cls"] == cls]
    col = CLS[cls]
    d.rectangle([56, y + 8, 60, y + 40], fill=col)
    d.text((78, y + 10), cls.upper(), font=F_GRP, fill=col)
    y += GRP_H
    for a in rows:
        d.text((X["c1"], y - 6), a["c1"], font=F_C1, fill=col)
        d.text((X["c3"], y + 4), a["c3"], font=F_C3, fill=WHITE)
        d.text((X["name"], y + 4), a["name"], font=F_NAME, fill=GRAY)
        d.text((X["pk1"], y + 4), f'{a["pk1"]:.2f}', font=F_NUM, fill=GRAY)
        d.text((X["pk2"], y + 4), f'{a["pk2"]:.2f}', font=F_NUM, fill=GRAY)
        d.text((X["pkr"], y + 4), "-" if a["pkr"] is None else f'{a["pkr"]:.2f}',
               font=F_NUMB if a["pkr"] is not None else F_NUM,
               fill=col if a["pkr"] is not None else DIM)
        d.text((X["pI"], y + 4), f'{a["pI"]:.2f}', font=F_NUMB, fill=WHITE)
        d.text((X["mw"], y + 4), f'{a["mw"]:.2f}', font=F_NUM, fill=GRAY)
        hv = a["hyd"]
        d.text((X["hyd"], y + 4), f'{hv:+.1f}', font=F_NUM,
               fill=(228, 160, 90) if hv > 0 else (110, 170, 220))
        e = a["ess"]
        d.text((X["ess"], y + 4), "yes" if e == "Yes" else ("cond." if e == "Conditional" else "no"),
               font=F_NUM, fill=WHITE if e == "Yes" else DIM)
        y += ROW
    y += 6

# the 21st and 22nd, which are not in the standard code
y += 14
d.line([(56, y), (W - 56, y)], fill=LINE, width=2)
y += 24
EXTRA = P["AMBER"]
d.rectangle([56, y + 6, 60, y + 34], fill=EXTRA)
d.text((78, y + 6), "THE 21ST AND 22ND, NOT IN THE STANDARD CODE", font=F_GRP, fill=EXTRA)
y += GRP_H
for c1, c3, name, note in [
    ("U", "Sec", "Selenocysteine",
     "UGA stop codon recoded via a SECIS element. 25 human selenoproteins."),
    ("O", "Pyl", "Pyrrolysine",
     "UAG stop codon recoded. Some methanogenic archaea, a few bacteria."),
]:
    d.text((X["c1"], y - 6), c1, font=F_C1, fill=EXTRA)
    d.text((X["c3"], y + 4), c3, font=F_C3, fill=WHITE)
    d.text((X["name"], y + 4), name, font=F_NAME, fill=GRAY)
    assert X["pk1"] + d.textlength(note, font=F_NAME) < W - 56, "note overflows: " + name
    d.text((X["pk1"], y + 4), note, font=F_NAME, fill=DIM)
    y += ROW

y += 20
d.line([(56, y), (W - 56, y)], fill=LINE, width=2)
y += 26
d.text((60, y), "Only 7 side chains ionize (D, E, H, C, Y, K, R). The N and C termini ionize too, and rule short peptides.",
       font=F_FOOT, fill=GRAY)
d.text((60, y + 38), "Hydropathy is Kyte-Doolittle: positive is hydrophobic, negative is hydrophilic. pKa values are the Lehninger set.",
       font=F_FOOT, fill=DIM)
assert y + 92 + 46 < H, "content overflows canvas: needs %d, have %d" % (y + 92 + 46, H)
d.text((60, y + 92), "biochemtools.com", font=F_DOM, fill=WHITE)
tag = "free, no signup  /  CC BY 4.0"
d.text((W - 60 - d.textlength(tag, font=F_FOOT), y + 100), tag, font=F_FOOT, fill=DIM)

out = BUILD_DIR + "/amino-acid-guide%s.png" % suffix()
img.save(out)
print("saved", out, img.size)
