#!/usr/bin/env python3
"""Which buffer for which pH, as a shareable chart.

Each buffer is drawn as a bar spanning pKa +/- 1, the range where it actually
buffers, positioned on a real pH axis.

Three changes came from r/Biochemistry readers on 2026-08-04:

  u/erikna10 asked for piperazine and for the charge of each buffering ion, both
  for planning ion exchange runs. The buffer ion must not stick to the resin:
  cation exchange wants an anionic or zwitterionic buffer, anion exchange wants a
  cationic or zwitterionic one.

  u/MorphingSp asked for polyprotic buffers on a single row with each pKa marked.
  Those are drawn as one row per family with a separate segment per pKa. Where the
  ranges overlap they merge into a continuous bar, as citrate does; where they do
  not, they stay as separate islands, as phosphate does. Drawing phosphate as one
  unbroken bar from pH 1 to 13 would be a lie, since it barely buffers at pH 5.

  u/RendertheFatCap pointed out that the crowd near pH 7 is a property of the list
  rather than of chemistry, which the footer now says outright.
"""
import os as _os
BUILD_DIR = _os.path.join(_os.path.dirname(_os.path.abspath(__file__)), "build")
_os.makedirs(BUILD_DIR, exist_ok=True)
import chartdata
import json
import sys
from PIL import Image, ImageDraw, ImageFont

BUF = chartdata.buffers()   # [name, pKa, dpKa/degC, isGoods, charge, family]

assert len(BUF) >= 30, f"expected the full buffer list, got {len(BUF)}"
assert all(2 <= b[1] <= 13 for b in BUF), "a pKa is outside the plausible range"
assert all(b[4] in "+-0" for b in BUF), "every buffer needs a charge"

PH_LO, PH_HI = 1.5, 13.0
LIGHT = "--light" in sys.argv        # print-friendly variant, asked for on r/Biochemistry

# collapse polyprotic buffers onto one row each, keyed by family
rows, seen = [], {}
for name, pka, dt, goods, charge, family in BUF:
    if family:
        if family in seen:
            r = seen[family]
            r["pkas"].append(pka)
            r["dts"].append(dt)
            continue
        label = family.capitalize() if family != "piperazine" else "Piperazine"
        r = dict(name=label, pkas=[pka], dts=[dt], goods=goods, charge=charge)
        seen[family] = r
    else:
        r = dict(name=name, pkas=[pka], dts=[dt], goods=goods, charge=charge)
    rows.append(r)
rows.sort(key=lambda r: min(r["pkas"]))

assert len(rows) < len(BUF), "polyprotic families should have collapsed some rows"
cit = next(r for r in rows if r["name"] == "Citrate")
assert len(cit["pkas"]) == 3, "citrate should carry all three pKa values on one row"

if LIGHT:
    # Deeper, more saturated than a straight light theme. Two readers said the bars
    # washed out on paper, so the fills carry real colour and the accents are dark
    # enough to survive a mediocre office printer.
    BG, CARD = (255, 255, 255), (246, 247, 249)
    LINE, WHITE, GRAY, DIM = (198, 204, 213), (18, 20, 24), (74, 80, 90), (116, 123, 134)
    GREEN, AMBER, BLUE, RED = (6, 105, 74), (146, 92, 4), (17, 76, 152), (170, 28, 24)
    PURPLE = (92, 56, 156)
    BAND, CHIP = (240, 242, 245), (225, 229, 236)
    BAR_G, BAR_B = (150, 214, 189), (166, 199, 238)
else:
    BG, CARD = (17, 19, 24), (25, 28, 35)
    LINE, WHITE, GRAY, DIM = (46, 50, 60), (240, 242, 245), (158, 164, 174), (120, 128, 140)
    GREEN, AMBER, BLUE, RED = (95, 204, 167), (228, 169, 59), (93, 157, 226), (226, 100, 94)
    PURPLE = (171, 144, 224)
    BAND, CHIP = (22, 24, 30), (38, 42, 52)
    BAR_G, BAR_B = (28, 52, 45), (38, 46, 56)

# charge of the buffering ion, the thing that decides whether it sticks to an IEX resin
CHG_COL = {"-": BLUE, "+": RED, "0": GREEN}
CHG_TXT = {"-": "-", "+": "+", "0": "±"}

B = "/System/Library/Fonts/Supplemental/Arial Bold.ttf"
R_ = "/System/Library/Fonts/Supplemental/Arial.ttf"
f = lambda p, s: ImageFont.truetype(p, s)
F_TITLE, F_SUB = f(B, 56), f(R_, 27)
F_NAME = f(B, 22)
F_PKA = f(B, 20)
F_CHG = f(B, 22)
F_AXIS = f(B, 22)
F_KEY = f(R_, 22)
F_FOOT = f(R_, 23)
F_DOM = f(B, 33)

W, M = 1560, 60
LABEL_W = 250
CHG_X = M + LABEL_W + 8        # charge badge
PKA_R = M + LABEL_W + 190      # pKa values, right after the name
PLOT_L = M + LABEL_W + 214
PLOT_R = W - M - 90
ROW = 40
H = 300 + len(rows) * ROW + 340

img = Image.new("RGB", (W, H), BG)
d = ImageDraw.Draw(img)
d.rectangle([0, 0, W, 12], fill=GREEN)

d.text((M, 58), "Which buffer for which pH", font=F_TITLE, fill=WHITE)
d.text((M + 2, 134), "Every bar spans pKa plus or minus 1, the range where a buffer actually works. Pick one whose bar covers your target pH.",
       font=F_SUB, fill=GRAY)

x_of = lambda ph: PLOT_L + (ph - PH_LO) / (PH_HI - PH_LO) * (PLOT_R - PLOT_L)

y = 216
for ph in range(2, 14):
    xp = x_of(ph)
    d.line([(xp, y + 6), (xp, H - 300)], fill=LINE if LIGHT else (32, 35, 43), width=1)
    d.text((xp - 8, y - 16), str(ph), font=F_AXIS, fill=DIM)
d.text((PLOT_L - 46, y - 16), "pH", font=F_AXIS, fill=DIM)
xp7 = x_of(7.4)
d.line([(xp7, y + 6), (xp7, H - 300)], fill=AMBER if LIGHT else (70, 60, 40), width=2)
d.text((xp7 + 8, y - 16), "7.4", font=F_AXIS, fill=AMBER)

y += 26
for idx, r in enumerate(rows):
    goods, charge = r["goods"], r["charge"]
    col = GREEN if goods else BLUE
    if idx % 2 == 0:
        d.rectangle([M, y + 2, W - M, y + 34], fill=BAND)

    # merge the pKa +/- 1 windows so overlapping ones read as one continuous bar,
    # while genuinely separate ones (phosphate) stay as separate islands
    spans = sorted((max(PH_LO, p - 1), min(PH_HI, p + 1)) for p in r["pkas"])
    merged = [list(spans[0])]
    for lo, hi in spans[1:]:
        if lo <= merged[-1][1]:
            merged[-1][1] = max(merged[-1][1], hi)
        else:
            merged.append([lo, hi])
    for lo, hi in merged:
        d.rounded_rectangle([x_of(lo), y + 6, x_of(hi), y + 30], radius=7,
                            fill=BAR_G if goods else BAR_B)
        d.rectangle([x_of(lo), y + 6, x_of(lo) + 3, y + 30], fill=col)
    for p in r["pkas"]:
        xp = x_of(p)
        d.ellipse([xp - 5, y + 13, xp + 5, y + 23], fill=col)

    label = r["name"] if len(r["name"]) < 26 else r["name"][:24] + "."
    assert M + d.textlength(label, font=F_NAME) < CHG_X - 10, f"label too long: {r['name']}"
    d.text((M, y + 8), label, font=F_NAME, fill=WHITE if goods else GRAY)

    # charge badge, so the chart is usable for planning an ion exchange run
    ct = CHG_TXT[charge]
    cw = d.textlength(ct, font=F_CHG)
    d.rounded_rectangle([CHG_X, y + 7, CHG_X + 34, y + 31], radius=7, fill=CHIP)
    d.text((CHG_X + (34 - cw) / 2, y + 7), ct, font=F_CHG, fill=CHG_COL[charge])

    pk = ", ".join(f"{p:.2f}" for p in sorted(r["pkas"]))
    pkw = d.textlength(pk, font=F_PKA)
    assert CHG_X + 40 + pkw < PLOT_L - 8, f"pKa list too wide: {r['name']} {pk}"
    d.text((PKA_R - pkw, y + 9), pk, font=F_PKA, fill=col)

    if any(abs(t) >= 0.02 for t in r["dts"]):
        d.text((PLOT_R + 14, y + 9), "temp!", font=F_KEY, fill=RED)
    y += ROW

y += 16
d.line([(M, y), (W - M, y)], fill=LINE, width=2)
y += 22

kx = M
for swatch, text in ((GREEN, "Good's buffer, made for biology"), (BLUE, "other common buffer"),
                     (RED, "pKa shifts more than 0.02 per degree C")):
    d.ellipse([kx, y + 6, kx + 12, y + 18], fill=swatch)
    d.text((kx + 22, y + 2), text, font=F_KEY, fill=GRAY)
    kx += 34 + int(d.textlength(text, font=F_KEY)) + 40
assert kx < W - M, "key row overflows"
y += 34

kx = M
d.text((kx, y + 2), "Charge of the buffering ion:", font=F_KEY, fill=GRAY)
kx += int(d.textlength("Charge of the buffering ion:", font=F_KEY)) + 18
for ch, text in (("-", "anionic"), ("+", "cationic"), ("0", "zwitterionic")):
    ct = CHG_TXT[ch]
    cw = d.textlength(ct, font=F_CHG)
    d.rounded_rectangle([kx, y - 2, kx + 34, y + 22], radius=7, fill=CHIP)
    d.text((kx + (34 - cw) / 2, y - 2), ct, font=F_CHG, fill=CHG_COL[ch])
    d.text((kx + 42, y + 2), text, font=F_KEY, fill=GRAY)
    kx += 42 + int(d.textlength(text, font=F_KEY)) + 34
assert kx < W - M, "charge key row overflows"

y += 44
GOODS = sum(1 for b in BUF if b[3] == 1)


def _peak(entries):
    best = (0, 0.0)
    x = 0.0
    while x <= 14.01:
        n = sum(1 for e in entries if abs(e[1] - x) <= 1.0)
        if n > best[0]:
            best = (n, x)
        x += 0.1
    return best


PEAK_ALL = _peak(BUF)[1]
PEAK_NO_GOODS = _peak([b for b in BUF if not b[3]])[1]
assert PEAK_NO_GOODS < PEAK_ALL, "removing Good's buffers should move the peak away from physiological pH"

# the gap that makes piperazine worth listing
CAT_LOW = [b[0] for b in BUF if b[4] == "+" and 4.5 <= b[1] <= 6.5]
assert len(CAT_LOW) == 2, f"expected 2 cationic buffers between pH 4.5 and 6.5, got {CAT_LOW}"

WORST = min(BUF, key=lambda b: b[2])
foot = [
    f"{len(BUF)} buffering equilibria across {len(rows)} buffers, {GOODS} of them Good's buffers, chosen to be soluble and to not chelate metals.",
    f"Temperature matters more than people expect. {WORST[0]} shifts {WORST[2]:+.3f} pH units per degree C.",
    "A buffer you set at 25 C is not the same buffer in a 4 C cold room, so set the pH at the temperature you will use it.",
    "For ion exchange, pick a buffer whose ion carries the same charge as the resin, so it does not bind and get stripped off.",
    f"Only {len(CAT_LOW)} cationic buffers cover pH 4.5 to 6.5, which is why piperazine is worth knowing for anion exchange down there.",
    f"The crowd around pH 7 is this list, not chemistry. Drop the {GOODS} Good's buffers and the busiest point falls to pH {PEAK_NO_GOODS:.1f}.",
]
for i, t in enumerate(foot):
    assert M + d.textlength(t, font=F_FOOT) < W - M, f"footer {i} overflows"
    d.text((M, y + 32 * i), t, font=F_FOOT, fill=GRAY if i < 2 else DIM)
y += 32 * len(foot) + 24

assert y + 44 < H, f"content overflows: needs {y + 44}, have {H}"
d.text((M, y), "biochemtools.com", font=F_DOM, fill=WHITE)
tag = "free, no signup  /  CC BY 4.0"
d.text((W - M - d.textlength(tag, font=F_FOOT), y + 10), tag, font=F_FOOT, fill=DIM)

out = BUILD_DIR + "/buffer-guide%s.png" % ("-light" if LIGHT else "")
img.save(out)
print("saved", out, img.size)
print(f"verified: {len(BUF)} equilibria on {len(rows)} rows, {GOODS} Good's, "
      f"citrate carries {len(cit['pkas'])} pKa values on one row")
