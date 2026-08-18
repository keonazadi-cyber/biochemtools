#!/usr/bin/env python3
"""MCAT-focused amino acid chart: structures first, only the numbers the MCAT asks for.

Built after r/Mcat feedback on the biochem chart (2026-08-02): "all this info and no
structures", "way too much detail". So MW and hydropathy are gone and every amino acid
is drawn. Structures come from RDKit, aligned on a shared backbone template.
Data is parsed from the live amino-acid-chart.html so the two cannot disagree.
"""
import os as _os
BUILD_DIR = _os.path.join(_os.path.dirname(_os.path.abspath(__file__)), "build")
_os.makedirs(BUILD_DIR, exist_ok=True)
import chartdata
import json, os
from PIL import Image, ImageDraw, ImageFont

AA = chartdata.amino_acids()
from lightmode import theme, suffix
LIGHT, P = theme()
PNG = os.path.join(os.path.dirname(os.path.abspath(__file__)), "aa_struct", "png_light" if LIGHT else "png")
BY3 = {a["c3"]: a for a in AA}

BG, CARD, LINE = P["BG"], P["CARD"], P["LINE"]
WHITE, GRAY, DIM = P["WHITE"], P["GRAY"], P["DIM"]
CLS = {"Nonpolar": P["NONPOLAR"], "Aromatic": P["AROMATIC"],
       "Polar": P["POLAR"], "Acidic": P["ACIDIC"], "Basic": P["BASIC"]}
ORDER = ["Nonpolar", "Aromatic", "Polar", "Acidic", "Basic"]
GOLD = P["AMBER"]

B = "/System/Library/Fonts/Supplemental/Arial Bold.ttf"
R = "/System/Library/Fonts/Supplemental/Arial.ttf"
f = lambda p, s: ImageFont.truetype(p, s)
F_TITLE, F_SUB = f(B, 62), f(R, 30)
F_GRP = f(B, 27)
F_C1 = f(B, 46)
F_C3 = f(B, 28)
F_NAME = f(R, 25)
F_PKA_L = f(R, 21)
F_PKA_V = f(B, 27)
F_CHG = f(B, 24)
F_MN_H = f(B, 30)
F_MN = f(R, 26)
F_MN_L = f(B, 33)
F_FOOT = f(R, 25)
F_DOM = f(B, 36)

COLS = 4
CW, CH = 380, 452          # card pitch, including the gap to the next card
GAP = 22                   # visible space between cards
HEAD_H = 96                # letter codes + name band at the top of a card
STRUCT_H = 250             # matches the rendered PNG height
MARGIN = 60
W = MARGIN * 2 + CW * COLS

# charge carried at pH 7.4 (the four that are not neutral)
CHARGE = {"Asp": "-1", "Glu": "-1", "Lys": "+1", "Arg": "+1"}

rows_needed = sum(-(-len([a for a in AA if a["cls"] == c]) // COLS) for c in ORDER)
H = 300 + len(ORDER) * 64 + rows_needed * CH + 300 + 206

img = Image.new("RGB", (W, H), BG)
d = ImageDraw.Draw(img)
d.rectangle([0, 0, W, 12], fill=(95, 204, 167))

d.text((MARGIN, 66), "The 20 amino acids, drawn", font=F_TITLE, fill=WHITE)
d.text((MARGIN + 2, 152), "Every structure at physiological pH, plus the only 7 pKa values that matter",
       font=F_SUB, fill=GRAY)

y = 244


def cell(cx, cy, a):
    """One amino acid: letter codes, name, structure, and pKa only if it ionizes.

    Vertical budget is explicit so the structure can never land under the pKa badge:
    head band, then the structure, then the footer strip.
    """
    col = CLS[a["cls"]]
    cwv, chv = CW - GAP, CH - GAP          # visible card box
    d.rounded_rectangle([cx, cy, cx + cwv, cy + chv], radius=14, fill=CARD)
    d.text((cx + 22, cy + 14), a["c1"], font=F_C1, fill=col)
    d.text((cx + 74, cy + 26), a["c3"], font=F_C3, fill=WHITE)
    d.text((cx + 74, cy + 60), a["name"], font=F_NAME, fill=GRAY)

    p = Image.open(f"{PNG}/{a['c3']}.png")
    assert p.height == STRUCT_H, f"{a['c3']}: structure is {p.height}px, expected {STRUCT_H}"
    sy = cy + HEAD_H
    img.paste(p, (cx + int((cwv - p.width) / 2), sy))

    # net charge sits top-right, in the empty space beside the name
    q = CHARGE.get(a["c3"])
    if q:
        lbl = "at pH 7.4"
        qw = d.textlength(q, font=F_CHG)
        lw = d.textlength(lbl, font=F_PKA_L)
        chip_w = max(qw, lw) + 28
        chx = cx + cwv - 20 - chip_w
        assert chx > cx + 74 + d.textlength(a["name"], font=F_NAME) + 12, \
            f"{a['c3']}: charge chip would overlap the name"
        d.rounded_rectangle([chx, cy + 18, chx + chip_w, cy + 78], radius=10, fill=P["CHIP"])
        d.text((chx + (chip_w - qw) / 2, cy + 22), q, font=F_CHG, fill=col)
        d.text((chx + (chip_w - lw) / 2, cy + 52), lbl, font=F_PKA_L, fill=DIM)

    foot_y = sy + STRUCT_H + 12
    assert foot_y + 48 <= cy + chv, \
        f"{a['c3']}: footer strip would spill past the card bottom"

    # only the 7 ionizable side chains carry a pKa, which is the whole point
    if a["pkr"] is not None:
        lbl, val = "side chain pKa", f'{a["pkr"]:.2f}'
        lw = d.textlength(lbl, font=F_PKA_L)
        vw = d.textlength(val, font=F_PKA_V)
        bw = 12 + lw + 16 + vw + 12
        assert 22 + bw <= cwv - 20, f"{a['c3']}: pKa badge is wider than the card"
        d.rounded_rectangle([cx + 22, foot_y, cx + 22 + bw, foot_y + 44],
                            radius=10, fill=P["CHIP"])
        d.text((cx + 34, foot_y + 13), lbl, font=F_PKA_L, fill=DIM)
        d.text((cx + 22 + bw - 12 - vw, foot_y + 8), val, font=F_PKA_V, fill=col)


for cls in ORDER:
    rows = [a for a in AA if a["cls"] == cls]
    col = CLS[cls]
    d.rectangle([MARGIN - 4, y + 8, MARGIN, y + 40], fill=col)
    d.text((MARGIN + 18, y + 8), cls.upper(), font=F_GRP, fill=col)
    y += 64
    for i, a in enumerate(rows):
        if i and i % COLS == 0:
            y += CH
        cell(MARGIN + (i % COLS) * CW, y, a)
    y += CH

# the mnemonic, credited to the r/Mcat commenter who supplied it
ion = sorted([a for a in AA if a["pkr"] is not None], key=lambda a: a["pkr"])
letters = "".join(a["c1"] for a in ion)
assert letters == "DEHCYKR", "mnemonic no longer matches the data: " + letters

y += 14
d.rounded_rectangle([MARGIN - 4, y, W - MARGIN + 4, y + 232], radius=16, fill=P["WARM"])
d.text((MARGIN + 24, y + 22), "THE ONLY 7 THAT IONIZE, IN pKa ORDER", font=F_MN_H, fill=GOLD)
d.text((MARGIN + 24, y + 66), "Don't Express Hate, Create Your Kindness Right",
       font=F_MN, fill=WHITE)

lx = MARGIN + 24
for a in ion:
    box = 116
    d.rounded_rectangle([lx, y + 110, lx + box - 12, y + 190], radius=10, fill=P["CHIP"])
    cw_ = d.textlength(a["c1"], font=F_MN_L)
    d.text((lx + (box - 12 - cw_) / 2, y + 118), a["c1"], font=F_MN_L, fill=GOLD)
    vs = f'{a["pkr"]:.2f}'
    vw = d.textlength(vs, font=F_PKA_L)
    d.text((lx + (box - 12 - vw) / 2, y + 158), vs, font=F_PKA_L, fill=GRAY)
    lx += box
assert lx < W - MARGIN, "mnemonic row overflows"

d.text((MARGIN + 24, y + 198), "Ascending the whole way, 3.65 to 12.48. Mnemonic from u/The_528_Express on r/Mcat.",
       font=F_PKA_L, fill=DIM)

y += 232 + 34
d.line([(MARGIN - 4, y), (W - MARGIN + 4, y)], fill=LINE, width=2)
y += 26
foot = [
    ("Structures are the L-isomer at pH 7.4: backbone NH3+ and COO-, side chains in their dominant state.", GRAY),
    ("Proline is the exception. Its nitrogen sits inside a ring as a secondary amine, not an NH3+.", GRAY),
    ("Only these 7 side chains ionize. The N and C termini ionize as well, and dominate the charge on short peptides.", GRAY),
    ("pKa values are the Lehninger set. Molecular weight and hydropathy left out on purpose, the MCAT does not ask.", DIM),
]
for n, (line, colr) in enumerate(foot):
    assert MARGIN + d.textlength(line, font=F_FOOT) < W - MARGIN, "footer line %d overflows" % n
    d.text((MARGIN, y + 36 * n), line, font=F_FOOT, fill=colr)
y += 36 * len(foot) + 22

assert y + 50 < H, "content overflows canvas: needs %d, have %d" % (y + 50, H)
d.text((MARGIN, y), "biochemtools.com", font=F_DOM, fill=WHITE)
tag = "free, no signup"
d.text((W - MARGIN - d.textlength(tag, font=F_FOOT), y + 10), tag, font=F_FOOT, fill=DIM)

out = BUILD_DIR + "/mcat-amino-acid-guide%s.png" % suffix()
img.save(out)
print("saved", out, img.size)
