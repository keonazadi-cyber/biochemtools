#!/usr/bin/env python3
"""The four enzyme inhibition patterns, as a shareable chart.

Uses the same alpha / alpha-prime formalism as michaelis-menten-vs-lineweaver-burk.html:
    Km(app)   = Km * alpha / alpha'
    Vmax(app) = Vmax / alpha'
Every arrow on the chart is computed from those two equations and asserted, so the
chart cannot claim a direction the algebra does not produce.
"""
import os as _os
BUILD_DIR = _os.path.join(_os.path.dirname(_os.path.abspath(__file__)), "build")
_os.makedirs(BUILD_DIR, exist_ok=True)
from PIL import Image, ImageDraw, ImageFont

KM, VMAX, R = 25.0, 100.0, 2.0        # baseline Km, Vmax, and [I]/Ki

# alpha applies to the free enzyme, alpha' to the ES complex
MODELS = {
    "Competitive":    (1 + R, 1.0),
    "Uncompetitive":  (1.0, 1 + R),
    "Noncompetitive": (1 + R, 1 + R),   # pure, alpha == alpha'
    # Mixed is a continuum, not a fixed signature. Whether Km rises or falls depends on
    # whether the inhibitor prefers free enzyme (alpha > alpha') or the ES complex
    # (alpha < alpha'). Corrected after u/xtalgeek pointed out on r/Biochemistry that the
    # chart was showing one arbitrary alpha pair as though it were the general rule.
    "Mixed (prefers E)":  (1 + R, 1 + R / 2),
    "Mixed (prefers ES)": (1 + R / 2, 1 + R),
}


def apparent(a, ap):
    return KM * a / ap, VMAX / ap


def arrow(new, old):
    if abs(new - old) < 1e-9:
        return "unchanged"
    return "up" if new > old else "down"


ROWS = []
for name, (a, ap) in MODELS.items():
    km, vm = apparent(a, ap)
    slope, yint, xint = km / vm, 1 / vm, -1 / km
    ROWS.append({
        "name": name, "km": arrow(km, KM), "vmax": arrow(vm, VMAX),
        "slope": arrow(slope, KM / VMAX),
        "yint": arrow(yint, 1 / VMAX), "xint": arrow(xint, -1 / KM),
        "kmv": km, "vmv": vm,
    })

by = {r["name"]: r for r in ROWS}
# the four signatures every textbook states, re-derived rather than trusted
assert by["Competitive"]["km"] == "up" and by["Competitive"]["vmax"] == "unchanged"
assert by["Uncompetitive"]["km"] == "down" and by["Uncompetitive"]["vmax"] == "down"
assert by["Uncompetitive"]["slope"] == "unchanged", "uncompetitive lines must be parallel"
assert by["Noncompetitive"]["km"] == "unchanged" and by["Noncompetitive"]["vmax"] == "down"
assert by["Noncompetitive"]["xint"] == "unchanged", "noncompetitive must meet on the x-axis"
assert by["Competitive"]["yint"] == "unchanged", "competitive must meet on the y-axis"
assert by["Mixed (prefers E)"]["km"] == "up" and by["Mixed (prefers E)"]["vmax"] == "down"
assert by["Mixed (prefers ES)"]["km"] == "down" and by["Mixed (prefers ES)"]["vmax"] == "down", \
    "mixed must be able to LOWER Km when the inhibitor prefers ES"
# noncompetitive is the special case of mixed where alpha == alpha', so Km does not move
assert MODELS["Noncompetitive"][0] == MODELS["Noncompetitive"][1], \
    "pure noncompetitive is mixed with alpha == alpha'"

from lightmode import theme, suffix
LIGHT, P = theme()
BG, CARD, LINE = P["BG"], P["CARD"], P["LINE"]
WHITE, GRAY, DIM = P["WHITE"], P["GRAY"], P["DIM"]
UP, DOWN, SAME = P["RED"], P["BLUE"], P["DIM"]
GREEN, AMBER = P["GREEN"], P["AMBER"]
COL = {"Competitive": P["RED"], "Uncompetitive": P["BLUE"],
       "Noncompetitive": P["PURPLE"], "Mixed (prefers E)": P["AMBER"],
       "Mixed (prefers ES)": P["AMBER"]}

B = "/System/Library/Fonts/Supplemental/Arial Bold.ttf"
R_ = "/System/Library/Fonts/Supplemental/Arial.ttf"
f = lambda p, s: ImageFont.truetype(p, s)
F_TITLE, F_SUB = f(B, 58), f(R_, 28)
F_H = f(B, 23)
F_NAME = f(B, 30)
F_VAL = f(B, 27)
F_BODY = f(R_, 24)
F_FOOT = f(R_, 24)
F_DOM = f(B, 34)

W, M = 1500, 60
CW = W - 2 * M
H = 1694
img = Image.new("RGB", (W, H), BG)
d = ImageDraw.Draw(img)
d.rectangle([0, 0, W, 12], fill=GREEN)

d.text((M, 60), "The enzyme inhibition patterns", font=F_TITLE, fill=WHITE)
d.text((M + 2, 142), "What each one does to Km and Vmax, and how to tell them apart on a Lineweaver-Burk plot.",
       font=F_SUB, fill=GRAY)

SYM = {"up": ("increases", UP), "down": ("decreases", DOWN), "unchanged": ("no change", SAME)}
X = {"name": M + 26, "km": M + 330, "vmax": M + 545, "lb": M + 775}

y = 232
d.text((X["name"], y), "INHIBITOR", font=F_H, fill=DIM)
d.text((X["km"], y), "Km", font=F_H, fill=DIM)
d.text((X["vmax"], y), "Vmax", font=F_H, fill=DIM)
d.text((X["lb"], y), "ON A LINEWEAVER-BURK PLOT", font=F_H, fill=DIM)
y += 34
d.line([(M, y), (M + CW, y)], fill=LINE, width=2)
y += 16

LB = {
    "Competitive":    "Meet on the y-axis. Same 1/Vmax, steeper.",
    "Uncompetitive":  "Parallel lines. Same slope, both intercepts move.",
    "Noncompetitive": "Meet on the x-axis. Same -1/Km, steeper.",
    "Mixed (prefers E)":  "Meet off both axes, above the x-axis.",
    "Mixed (prefers ES)": "Meet off both axes, below the x-axis.",
}
BIND = {
    "Competitive":    "binds free enzyme only, at the active site",
    "Uncompetitive":  "binds the ES complex only",
    "Noncompetitive": "binds both, equally well",
    "Mixed (prefers E)":  "binds both, free enzyme more tightly",
    "Mixed (prefers ES)": "binds both, the ES complex more tightly",
}

for r in ROWS:
    col = COL[r["name"]]
    d.rounded_rectangle([M, y, M + CW, y + 152], radius=14, fill=CARD)
    d.rectangle([M, y + 18, M + 5, y + 134], fill=col)
    d.text((X["name"], y + 22), r["name"], font=F_NAME, fill=col)
    d.text((X["name"] + 2, y + 64), BIND[r["name"]], font=F_BODY, fill=DIM)
    for key, xk in (("km", "km"), ("vmax", "vmax")):
        label, c = SYM[r[key]]
        d.text((X[xk], y + 30), label, font=F_VAL, fill=c)
    txt = LB[r["name"]]
    assert X["lb"] + d.textlength(txt, font=F_BODY) < M + CW - 20, f"LB text overflows: {r['name']}"
    d.text((X["lb"], y + 34), txt, font=F_BODY, fill=GRAY)
    d.text((X["lb"], y + 78), f"apparent Km {r['kmv']:.1f}, apparent Vmax {r['vmv']:.1f}",
           font=F_BODY, fill=DIM)
    y += 172

y += 8
tips = [
    "Noncompetitive and uncompetitive sound alike and behave nothing alike.",
    "Noncompetitive leaves Km alone. Uncompetitive lowers BOTH Km and Vmax.",
    "Mixed has no single signature. Km rises or falls depending on which form the inhibitor prefers,",
    "and pure noncompetitive is the special case of mixed where it binds both equally, so Km does not move.",
    "If the Lineweaver-Burk lines are parallel, it is uncompetitive. Nothing else gives parallel lines.",
]
# box height follows the tips, so adding a line can never spill outside it again
TIP_H = 78 + 34 * len(tips)
d.rounded_rectangle([M, y, M + CW, y + TIP_H], radius=14, fill=P["WARM"])
d.text((M + 26, y + 22), "The one that trips everyone up", font=F_NAME, fill=AMBER)
for i, t in enumerate(tips):
    assert M + 26 + d.textlength(t, font=F_BODY) < M + CW - 20, f"tip {i} overflows"
    d.text((M + 26, y + 66 + i * 34), t, font=F_BODY, fill=WHITE if i in (2, 3) else GRAY)
y += TIP_H + 26

d.line([(M, y), (M + CW, y)], fill=LINE, width=2)
y += 24
foot = [
    f"Worked with Km {KM:.0f}, Vmax {VMAX:.0f}, and inhibitor at {R:.0f} times its Ki.",
    "Km(app) = Km x alpha / alpha', and Vmax(app) = Vmax / alpha', where alpha acts on free enzyme and alpha' on the ES complex.",
    "Uncompetitive lowering Km looks wrong but is real: removing ES pulls the equilibrium toward binding more substrate.",
    "Mixed split into two rows after u/xtalgeek pointed out on r/Biochemistry that the old version showed one case as the rule.",
]
for i, t in enumerate(foot):
    assert M + d.textlength(t, font=F_FOOT) < W - M, f"footer {i} overflows"
    d.text((M, y + 34 * i), t, font=F_FOOT, fill=GRAY if i < 2 else DIM)
y += 34 * len(foot) + 26

assert y + 46 < H, f"content overflows: needs {y + 46}, have {H}"
d.text((M, y), "biochemtools.com", font=F_DOM, fill=WHITE)
tag = "free, no signup"
d.text((W - M - d.textlength(tag, font=F_FOOT), y + 10), tag, font=F_FOOT, fill=DIM)

out = BUILD_DIR + "/inhibition-guide%s.png" % suffix()
img.save(out)
print("saved", out, img.size)
for r in ROWS:
    print(f"  {r['name']:<15} Km {r['km']:<9} Vmax {r['vmax']:<9} slope {r['slope']}")
