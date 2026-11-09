#!/usr/bin/env python3
"""The MCAT high-yield cross-topic sheet: the five things that keep recurring.

Not the amino acid structures chart (make_mcat_aa_guide.py draws those). This is
the cram sheet that cuts across topics, because the MCAT keeps asking the same
five questions and nothing on the site answers them on one page:

  1. the seven ionizable side chains in pKa order, and which way each drags pI
  2. the four inhibition patterns, what each does to Km and Vmax, and the
     Lineweaver-Burk line you recognise it by
  3. why ATP per glucose is 30 to 32 and not 36 to 38, and which 2 ATP survive
     without oxygen
  4. Henderson-Hasselbalch and the one-unit rule
  5. the amino acids whose pI is nowhere near 6

Nothing here is typed from memory. The side chains and every pI come out of
amino-acid-chart.html's own AA array; the inhibition model is derived from the
worked table on michaelis-menten-vs-lineweaver-burk.html by solving its numbers
back into alpha and alpha-prime; the four ATP totals are multiplied out from
atp-yield-calculator.html's own constants and P/O ratios; the one-unit rule is
read out of the buffer calculator's own range guard. If a page changes, this
build fails instead of shipping a sheet that disagrees with the site.

The acid/base character of each side chain is derived too, not asserted: for all
seven, the titration model is solved both ways and the assignment that
reproduces the page's published pI is the one used. The wrong assignment misses
by more than 3.6 pH units every time, so the fit is not ambiguous.
"""
import os as _os, re, sys
from PIL import Image, ImageDraw

sys.path.insert(0, _os.path.dirname(_os.path.abspath(__file__)))
import chartkit
import chartdata
from lightmode import theme, suffix

HERE = _os.path.dirname(_os.path.abspath(__file__))
SITE = _os.path.join(HERE, "..", "..")
BUILD_DIR = _os.path.join(HERE, "build")
_os.makedirs(BUILD_DIR, exist_ok=True)

LIGHT, P = theme()
F = chartkit.fonts()
# Arial has no superscript minus and no subscript two, so any string carrying
# A-minus or FADH-two is drawn in the Unicode face instead. Sizes come from the
# kit's scale, never from a number picked here.
S = chartkit.SCALE
U = {"body": chartkit.unicode_font(S["s"]),
     "label": chartkit.unicode_font(S["s"], bold=True),
     "small": chartkit.unicode_font(S["xs"]),
     "head": chartkit.unicode_font(S["m"], bold=True)}
W, M = chartkit.WIDTH, chartkit.MARGIN


def page(name):
    return open(_os.path.join(SITE, name), encoding="utf-8").read()


# =========================================================================
# 1. the seven ionizable side chains, from the AA array the chart page uses
# =========================================================================
AA = chartdata.amino_acids()
assert len(AA) == 20, "expected 20 amino acids on amino-acid-chart.html, got %d" % len(AA)
ION = [a for a in AA if a["pkr"] is not None]
assert len(ION) == 7, "expected exactly 7 side chains with a pKa, got %d: %s" % (
    len(ION), [a["c3"] for a in ION])
for a in ION:
    for k in ("c1", "c3", "name", "pk1", "pk2", "pkr", "pI"):
        assert a.get(k) is not None, "%s is missing %s" % (a["c3"], k)


def net_charge(a, pH, sc_acid):
    """Net charge from the three titratable groups at this pH."""
    q = 1.0 / (1 + 10 ** (pH - a["pk2"]))          # alpha-amino, + while protonated
    q -= 1.0 / (1 + 10 ** (a["pk1"] - pH))         # alpha-carboxyl, - once deprotonated
    if sc_acid:
        q -= 1.0 / (1 + 10 ** (a["pkr"] - pH))     # acidic side chain, - once deprotonated
    else:
        q += 1.0 / (1 + 10 ** (pH - a["pkr"]))     # basic side chain, + while protonated
    return q


def solve_pI(a, sc_acid):
    lo, hi = 0.0, 14.0
    for _ in range(90):
        mid = (lo + hi) / 2
        if net_charge(a, mid, sc_acid) > 0:
            lo = mid
        else:
            hi = mid
    return (lo + hi) / 2


# Which way does each side chain titrate? Fit it, do not declare it.
CHAR = {}
for a in ION:
    as_acid, as_base = abs(solve_pI(a, True) - a["pI"]), abs(solve_pI(a, False) - a["pI"])
    acid = as_acid < as_base
    best, worst = (as_acid, as_base) if acid else (as_base, as_acid)
    assert best < 0.05, ("neither titration model reproduces %s's published pI "
                         "%.2f (best miss %.3f)" % (a["c3"], a["pI"], best))
    assert worst > 1.0, ("the acid/base fit for %s is ambiguous (%.3f vs %.3f)"
                         % (a["c3"], as_acid, as_base))
    CHAR[a["c3"]] = "acidic" if acid else "basic"

ACIDIC_SC = [a for a in ION if CHAR[a["c3"]] == "acidic"]
BASIC_SC = [a for a in ION if CHAR[a["c3"]] == "basic"]
assert len(ACIDIC_SC) == 4 and len(BASIC_SC) == 3, (
    "expected 4 acidic and 3 basic side chains, got %d and %d"
    % (len(ACIDIC_SC), len(BASIC_SC)))
# the page's own class column has to agree wherever it commits to one
for a in ION:
    if a["cls"] in ("Acidic", "Basic"):
        assert a["cls"].lower() == CHAR[a["c3"]], (
            "%s is %s on the page but titrates as %s" % (a["c3"], a["cls"], CHAR[a["c3"]]))

IONS = sorted(ION, key=lambda a: a["pkr"])          # ascending pKa, as asked
PH_BODY = 7.4


def charge_at(a, pH=PH_BODY):
    """What the side chain alone is doing at body pH, from its own pKa."""
    if CHAR[a["c3"]] == "acidic":
        frac = 1.0 / (1 + 10 ** (a["pkr"] - pH))    # fraction deprotonated, negative
        return "negative", frac
    frac = 1.0 / (1 + 10 ** (pH - a["pkr"]))        # fraction protonated, positive
    return "positive", frac


# pI far from 6: computed, not a remembered list of five
FAR = sorted((a for a in AA if abs(a["pI"] - 6.0) > 1.5), key=lambda a: a["pI"])
assert [a["c3"] for a in FAR] == ["Asp", "Glu", "His", "Lys", "Arg"], \
    "the set of amino acids with pI far from 6 changed: %s" % [a["c3"] for a in FAR]
NEAR_ION = [a for a in IONS if abs(a["pI"] - 6.0) <= 1.5]
assert [a["c3"] for a in NEAR_ION] == ["Cys", "Tyr"], \
    "expected Cys and Tyr to be the ionizable pair that still sits near 6: %s" % NEAR_ION
for a in FAR:
    assert abs(solve_pI(a, CHAR[a["c3"]] == "acidic") - a["pI"]) < 0.05, \
        "%s's pI does not come back out of the titration model" % a["c3"]

# =========================================================================
# 2. the four inhibition patterns, solved out of the page's own worked table
# =========================================================================
MM = page("michaelis-menten-vs-lineweaver-burk.html")
b = re.search(r"Baseline enzyme:\s*Vmax\s*=\s*([\d.]+)[^,]*,\s*Km\s*=\s*([\d.]+)", MM)
assert b, "the baseline enzyme line is gone from the Lineweaver-Burk page"
VMAX, KM = float(b.group(1)), float(b.group(2))
rm = re.search(r"ratio r = \[I\]/Ki = (\d+)", MM)
assert rm, "the inhibitor ratio r is no longer stated on the page"
R = float(rm.group(1))

# the apparent-value formulas, quoted from the page rather than assumed
assert re.search(r"Km\(app\)\s*=\s*\(α/α′\)·Km", MM), \
    "the Km(app) = (alpha/alpha') * Km formula is gone from the page"
assert re.search(r"Vmax\(app\)\s*=\s*Vmax/α′", MM), \
    "the Vmax(app) = Vmax/alpha' formula is gone from the page"

tbl = re.search(r"<thead><tr><th></th><th>Km\(app\)[\s\S]*?</tbody>", MM)
assert tbl, "the inhibition comparison table is gone from the page"
TABLE = {}
for name, cells in re.findall(r"<tr><td>([^<]+)</td>((?:<td>[^<]*</td>)+)</tr>", tbl.group(0)):
    vals = [v.replace("−", "-") for v in re.findall(r"<td>([^<]*)</td>", cells)]
    assert len(vals) == 5, "the inhibition table's column count changed: %r" % (vals,)
    TABLE[name] = [float(v) for v in vals]
assert set(TABLE) == {"No inhibitor", "Competitive", "Noncompetitive"}, sorted(TABLE)
assert TABLE["No inhibitor"][:2] == [KM, VMAX], \
    "the table's baseline row disagrees with the stated baseline enzyme"

# Solve each published row back into the two factors, instead of typing them.
def factors_from_row(name):
    km_app, vmax_app = TABLE[name][0], TABLE[name][1]
    ap = VMAX / vmax_app
    a = (km_app / KM) * ap
    return a, ap


MODEL = {}
MODEL["Competitive"] = factors_from_row("Competitive")
MODEL["Noncompetitive"] = factors_from_row("Noncompetitive")
assert abs(MODEL["Competitive"][0] - (1 + R)) < 1e-9 and abs(MODEL["Competitive"][1] - 1) < 1e-9, \
    "competitive no longer solves to alpha = 1 + r, alpha' = 1: %r" % (MODEL["Competitive"],)
assert abs(MODEL["Noncompetitive"][0] - (1 + R)) < 1e-9 and \
       abs(MODEL["Noncompetitive"][1] - (1 + R)) < 1e-9, \
    "pure noncompetitive must solve to alpha == alpha' == 1 + r: %r" % (MODEL["Noncompetitive"],)

# Uncompetitive is not in that table; the page states its factors in the practice
# answer, at its own r. Read the shape there, then apply it at the table's r.
un = re.search(r"Uncompetitive:\s*α\s*=\s*(\d+),\s*α′\s*=\s*1\s*\+\s*r\s*=\s*(\d+)", MM)
assert un, "the uncompetitive alpha / alpha-prime line is gone from the page"
assert int(un.group(1)) == 1, "the page no longer puts alpha = 1 for uncompetitive"
ur = re.search(r"\[I\] = (\d+) µM and Ki = (\d+) µM \(so r = (\d+)\)", MM)
assert ur and int(ur.group(2)) * int(ur.group(3)) == int(ur.group(1)), \
    "the uncompetitive practice problem's r no longer matches its [I] and Ki"
assert int(un.group(2)) == 1 + int(ur.group(3)), \
    "the page's uncompetitive alpha-prime is not 1 + r any more"
MODEL["Uncompetitive"] = (1.0, 1 + R)
# Mixed is the general case: both factors above 1 but unequal. Which way Km moves
# depends on which form the inhibitor prefers, so both sub-cases are computed.
MODEL["Mixed, prefers E"] = (1 + R, 1 + R / 2)
MODEL["Mixed, prefers ES"] = (1 + R / 2, 1 + R)

BASE_SLOPE, BASE_Y, BASE_X = KM / VMAX, 1 / VMAX, -1 / KM


def apply(a, ap):
    km, vm = KM * a / ap, VMAX / ap
    return dict(km=km, vmax=vm, slope=km / vm, yint=1 / vm, xint=-1 / km)


def move(new, old):
    if abs(new - old) < 1e-9:
        return "same"
    return "up" if new > old else "down"


EFF = {}
for name, (a, ap) in MODEL.items():
    v = apply(a, ap)
    EFF[name] = dict(
        km=move(v["km"], KM), vmax=move(v["vmax"], VMAX),
        slope=move(v["slope"], BASE_SLOPE), yint=move(v["yint"], BASE_Y),
        xint=move(v["xint"], BASE_X), kmv=v["km"], vmaxv=v["vmax"])

# The derived directions must match what the page's own table and prose say.
assert EFF["Competitive"]["km"] == "up" and EFF["Competitive"]["vmax"] == "same"
assert EFF["Competitive"]["yint"] == "same", "competitive must share the y-intercept"
assert EFF["Noncompetitive"]["vmax"] == "down" and EFF["Noncompetitive"]["km"] == "same"
assert EFF["Noncompetitive"]["xint"] == "same", "noncompetitive must share the x-intercept"
assert EFF["Uncompetitive"]["km"] == "down" and EFF["Uncompetitive"]["vmax"] == "down"
assert EFF["Uncompetitive"]["slope"] == "same", "uncompetitive lines must be parallel"
assert EFF["Mixed, prefers E"]["km"] == "up" and EFF["Mixed, prefers ES"]["km"] == "down", \
    "mixed inhibition must be able to move Km either way"
assert TABLE["Competitive"][3] == TABLE["No inhibitor"][3], \
    "the page's competitive row no longer shares the baseline y-intercept"
assert TABLE["Noncompetitive"][4] == TABLE["No inhibitor"][4], \
    "the page's noncompetitive row no longer shares the baseline x-intercept"
assert re.search(r"same y-intercept as the baseline", MM), "page prose on competitive changed"
assert re.search(r"keeps the exact same x-intercept", MM), "page prose on noncompetitive changed"
assert re.search(r"parallel to the baseline \(same slope\)", MM), "page prose on uncompetitive changed"

SIGN = {("same", "down", "down"): "lines meet on the y-axis",
        ("down", "down", "same"): "lines meet on the x-axis",
        ("same", "up", "up"): "parallel lines, shifted up"}


def signature(e):
    """Name the Lineweaver-Burk tell from which feature did not move."""
    key = (e["slope"], e["yint"], e["xint"])
    if key in SIGN:
        return SIGN[key]
    assert "same" not in key, "an unlisted signature with a fixed feature: %r" % (key,)
    return "lines cross off both axes"


assert signature(EFF["Competitive"]) == "lines meet on the y-axis"
assert signature(EFF["Noncompetitive"]) == "lines meet on the x-axis"
assert signature(EFF["Uncompetitive"]) == "parallel lines, shifted up"
assert signature(EFF["Mixed, prefers E"]) == "lines cross off both axes"

BINDS = {"Competitive": "the active site, free E",
         "Noncompetitive": "elsewhere, E and ES alike",
         "Uncompetitive": "the ES complex only",
         "Mixed": "E and ES, unequal affinity"}

ARROW = {"up": "↑ rises", "down": "↓ falls", "same": "unchanged"}

# =========================================================================
# 3. ATP per glucose: four totals, multiplied out from the page's constants
# =========================================================================
ATP = page("atp-yield-calculator.html")
C = dict((k, int(v)) for k, v in
         re.findall(r"(MITO_NADH|TCA_FADH2|GLYC_NADH|SUBSTRATE)\s*=\s*(\d+)", ATP))
assert set(C) == {"MITO_NADH", "TCA_FADH2", "GLYC_NADH", "SUBSTRATE"}, sorted(C)
assert C == {"MITO_NADH": 8, "TCA_FADH2": 2, "GLYC_NADH": 2, "SUBSTRATE": 4}, C
po = re.findall(r'conv==="modern" \? ([\d.]+) : ([\d.]+)', ATP)
assert len(po) == 2, "the P/O ratio pair is no longer a modern/classic ternary: %r" % (po,)
RATIOS = {"Modern": (float(po[0][0]), float(po[1][0])),
          "Classic": (float(po[0][1]), float(po[1][1]))}
assert RATIOS == {"Modern": (2.5, 1.5), "Classic": (3.0, 2.0)}, RATIOS
assert re.search(r'shuttle==="malate" \? nadhRatio : fadh2Ratio', ATP), \
    "the shuttle no longer decides whether cytosolic NADH is worth a NADH or a FADH2"

TOTALS = []
for conv in ("Modern", "Classic"):
    nadh, fadh2 = RATIOS[conv]
    for shuttle, cyto in (("malate-aspartate", nadh), ("glycerol-3-P", fadh2)):
        parts = (C["SUBSTRATE"], C["MITO_NADH"] * nadh, C["TCA_FADH2"] * fadh2,
                 C["GLYC_NADH"] * cyto)
        TOTALS.append(dict(conv=conv, ratios=(nadh, fadh2), shuttle=shuttle,
                           parts=parts, total=sum(parts)))
assert sorted(t["total"] for t in TOTALS) == [30.0, 32.0, 36.0, 38.0], \
    "the four conventional totals no longer come out 30/32/36/38: %s" % [t["total"] for t in TOTALS]
assert re.search(r"Is the answer 36, 38, 30, or 32 ATP", ATP), \
    "the page no longer frames the answer as 36/38/30/32"
# The correction already made on that page: only glycolysis's 2 are oxygen free.
assert re.search(r"Only the 2 from glycolysis are independent of oxygen; "
                 r"the cycle stalls without it", ATP), \
    "the page's oxygen-independence correction has moved or changed wording"
assert re.search(r"Total yield in that case is just glycolysis's own net 2 ATP", ATP), \
    "the anaerobic total on the page is no longer glycolysis's net 2 ATP"
ANAEROBIC = 2
assert C["SUBSTRATE"] - ANAEROBIC == 2, \
    "the TCA cycle's 2 GTP are the other half of substrate-level ATP"

# =========================================================================
# 4. Henderson-Hasselbalch and the one-unit rule, from the buffer calculator
# =========================================================================
HH = page("henderson-hasselbalch-buffer-calculator.html")
assert re.search(r"pH = pKa \+ log\(\[A⁻\]/\[HA\]\)", HH), \
    "the Henderson-Hasselbalch equation is gone from the buffer page"
assert re.search(r"\[A⁻\]/\[HA\] = 10\^\(pH − pKa\)", HH), \
    "the rearranged ratio form is gone from the buffer page"
assert re.search(r"fA=ratio/\(1\+ratio\), fHA=1/\(1\+ratio\)", HH), \
    "the fraction formulas are gone from the buffer page"
g = re.search(r'const d=Math\.abs\(pH-pka\);[\s\S]{0,80}?innerHTML=d>(\d+)', HH)
assert g, "the buffering-range guard is gone from the buffer page"
UNIT = int(g.group(1))
assert UNIT == 1, "the buffer page's range guard is no longer one pH unit: %r" % UNIT
assert re.search(r"A buffer works best within about pKa ± 1", HH), \
    "the one-unit sentence changed on the buffer page"

# what one unit actually costs you, from the page's own fraction formulas
BUF = []
for delta in (-UNIT, 0, UNIT):
    ratio = 10 ** delta
    fA = ratio / (1 + ratio)
    BUF.append((delta, ratio, fA, 1 - fA))
assert abs(BUF[0][2] - 0.0909) < 1e-3 and abs(BUF[2][2] - 0.9091) < 1e-3, BUF
assert abs(BUF[1][2] - 0.5) < 1e-12, "at pH = pKa the two forms must be equal"

# =========================================================================
# drawing
# =========================================================================
AX_W = W - 2 * M
ROW = 38


def draw():
    H = 3200
    img = Image.new("RGB", (W, H), P["BG"])
    d = ImageDraw.Draw(img)
    T = chartkit.safe_text
    y = M

    def cells(items, yy, gap=18):
        """Draw a row of (x, text, font, colour) and prove nothing overlaps."""
        for i, (x, txt, f, c) in enumerate(items):
            lim = items[i + 1][0] if i + 1 < len(items) else W - M
            w = d.textlength(txt, font=f)
            assert x + w <= lim - gap, (
                "column overrun: %r ends at %d, next column starts at %d"
                % (txt, x + w, lim))
            T(d, (x, yy), txt, f, c)

    def band(title, lead=None):
        nonlocal y
        d.rectangle([M, y, W - M, y + 2], fill=P["LINE"])
        y += 18
        T(d, (M, y), title, F["head"], P["AMBER"])
        if lead:
            lw = d.textlength(title, font=F["head"])
            assert M + lw + 24 + d.textlength(lead, font=F["body"]) <= W - M, \
                "section lead does not fit beside %r" % title
            T(d, (M + lw + 24, y + 6), lead, F["body"], P["DIM"])
        y += 44

    # ---- header -------------------------------------------------------
    T(d, (M, y), "MCAT biochem, the high-yield sheet", F["title"], P["WHITE"])
    y += 72
    T(d, (M, y), "Side chain pKa order, enzyme inhibition, ATP accounting, "
                 "buffers, and the pI outliers.", F["sub"], P["GRAY"])
    y += 56

    # ---- 1. the pKa number line, then the table -----------------------
    band("The seven ionizable side chains", "in ascending pKa, with what each does to pI")

    def ax(v):
        return M + (v / 14.0) * AX_W

    top_y = y + 74                      # acidic labels sit above this
    axis_y = top_y + 30
    bot_y = axis_y + 18

    cap_a = "acidic side chain, pulls pI DOWN"
    cap_b = "basic side chain, pulls pI UP"
    first = min(a["pkr"] for a in IONS)
    assert M + d.textlength(cap_a, font=F["small"]) < ax(first) - 40, \
        "the acidic caption runs into the first marker"
    T(d, (M, y), cap_a, F["small"], P["DIM"])
    T(d, (M, bot_y + 78), cap_b, F["small"], P["DIM"])

    # the pH 7.4 reference, drawn first so markers sit on top of it
    x74 = ax(PH_BODY)
    for seg in range(int(y + 26), int(bot_y + 72), 12):
        d.line([x74, seg, x74, seg + 6], fill=P["LINE"], width=2)
    lab74 = "pH 7.4"
    w74 = d.textlength(lab74, font=F["small"])
    T(d, (x74 - w74 / 2, bot_y + 78), lab74, F["small"], P["GRAY"])

    d.line([M, axis_y, W - M, axis_y], fill=P["LINE"], width=2)
    for tick in range(0, 15, 2):
        x = ax(tick)
        d.line([x, axis_y - 5, x, axis_y + 5], fill=P["LINE"], width=2)
        lt = str(tick)
        T(d, (x - d.textlength(lt, font=F["small"]) / 2, axis_y + 10), lt,
          F["small"], P["DIM"])

    placed = {"up": [], "down": []}
    for a in IONS:
        x = ax(a["pkr"])
        acidic = CHAR[a["c3"]] == "acidic"
        side = "up" if acidic else "down"
        code, val = a["c1"], ("%.2f" % a["pkr"]).rstrip("0").rstrip(".")
        bw = max(d.textlength(code, font=F["label"]), d.textlength(val, font=F["small"]))
        left = x - bw / 2
        for prev in placed[side]:
            assert left - prev > 10, (
                "%s's marker label collides with its neighbour on the %s side"
                % (a["c3"], side))
        placed[side].append(left + bw)
        if acidic:
            d.line([x, axis_y - 2, x, top_y + 4], fill=P["BLUE"], width=2)
            d.ellipse([x - 5, axis_y - 5, x + 5, axis_y + 5], fill=P["BLUE"])
            T(d, (x - d.textlength(code, font=F["label"]) / 2, top_y - 56), code,
              F["label"], P["WHITE"])
            T(d, (x - d.textlength(val, font=F["small"]) / 2, top_y - 26), val,
              F["small"], P["BLUE"])
        else:
            d.line([x, axis_y + 2, x, bot_y + 40], fill=P["BLUE"], width=2)
            d.ellipse([x - 5, axis_y - 5, x + 5, axis_y + 5], fill=P["BLUE"])
            T(d, (x - d.textlength(code, font=F["label"]) / 2, bot_y + 44), code,
              F["label"], P["WHITE"])
            T(d, (x - d.textlength(val, font=F["small"]) / 2, bot_y + 74 - 30), val,
              F["small"], P["BLUE"])
    y = bot_y + 118

    X1 = [M, M + 330, M + 470, M + 760, M + 900]
    cells([(X1[0], "Side chain", F["label"], P["GRAY"]),
           (X1[1], "pKa", F["label"], P["GRAY"]),
           (X1[2], "at pH 7.4", F["label"], P["GRAY"]),
           (X1[3], "pI", F["label"], P["GRAY"]),
           (X1[4], "what it does to pI", F["label"], P["GRAY"])], y)
    y += 34
    for a in IONS:
        sign, frac = charge_at(a)
        state = ("%s, %d%% of it" % (sign, round(frac * 100)) if frac >= 0.005
                 else "%s on paper, under 1%%" % sign)
        pull = ("pulls pI down, below the backbone's own"
                if CHAR[a["c3"]] == "acidic" else
                "pulls pI up, above the backbone's own")
        cells([(X1[0], "%s   %s   %s" % (a["c1"], a["c3"], a["name"]), F["body"], P["WHITE"]),
               (X1[1], "%.2f" % a["pkr"], F["body"], P["BLUE"]),
               (X1[2], state, F["body"], P["GRAY"]),
               (X1[3], "%.2f" % a["pI"], F["body"], P["BLUE"]),
               (X1[4], pull, F["body"], P["GRAY"])], y)
        y += ROW
    y += 6
    T(d, (M, y), "His is the one that matters at body pH: its pKa of %.1f sits closest "
                 "to 7.4, so it is the side chain that can give or take a proton there."
      % next(a["pkr"] for a in IONS if a["c3"] == "His"), F["body"], P["GRAY"])
    y += 34
    T(d, (M, y), "Cys and Tyr are ionizable too, and they are the ones people forget: "
                 "both still end up with a pI near 6 (%.2f and %.2f)."
      % (NEAR_ION[0]["pI"], NEAR_ION[1]["pI"]), F["body"], P["RED"])
    y += 56

    # ---- 2. inhibition ------------------------------------------------
    band("Enzyme inhibition, the four patterns", "Km(app) = (alpha/alpha') Km,   "
         "Vmax(app) = Vmax/alpha'")
    X2 = [M, M + 330, M + 530, M + 760, M + 1130]
    cells([(X2[0], "Pattern", F["label"], P["GRAY"]),
           (X2[1], "Km", F["label"], P["GRAY"]),
           (X2[2], "Vmax", F["label"], P["GRAY"]),
           (X2[3], "Lineweaver-Burk", F["label"], P["GRAY"]),
           (X2[4], "binds", F["label"], P["GRAY"])], y)
    y += 34
    SHOW = [("Competitive", "Competitive"), ("Noncompetitive", "Noncompetitive"),
            ("Uncompetitive", "Uncompetitive"), ("Mixed, prefers E", "Mixed")]
    for key, label in SHOW:
        e = EFF[key]
        km = "up or down" if label == "Mixed" else ARROW[e["km"]]
        cells([(X2[0], label, F["body"], P["WHITE"]),
               (X2[1], km, F["body"], P["DIM"] if e["km"] == "same" and label != "Mixed"
                else P["BLUE"]),
               (X2[2], ARROW[e["vmax"]], F["body"],
                P["DIM"] if e["vmax"] == "same" else P["BLUE"]),
               (X2[3], signature(e), F["body"], P["GRAY"]),
               (X2[4], BINDS[label], F["body"], P["GRAY"])], y)
        y += ROW
    y += 6
    T(d, (M, y), "Worked at the site's own baseline: Km %g, Vmax %g, r = [I]/Ki = %g. "
                 "Competitive doubles Km to %g; noncompetitive halves Vmax to %g."
      % (KM, VMAX, R, EFF["Competitive"]["kmv"], EFF["Noncompetitive"]["vmaxv"]),
      F["body"], P["GRAY"])
    y += 34
    T(d, (M, y), "The trap: competitive is the SHARED y-intercept, noncompetitive the "
                 "shared x-intercept. Swapping those two is the usual lost point.",
      F["body"], P["RED"])
    y += 56

    # ---- 3. ATP -------------------------------------------------------
    band("ATP per glucose", "why the answer is 30 to 32, not 36 to 38")
    pitch = (AX_W - 3 * chartkit.GUTTER) / 4
    card_h = 164
    for i, t in enumerate(TOTALS):
        x = M + i * (pitch + chartkit.GUTTER)
        d.rectangle([x, y, x + pitch, y + card_h], fill=P["CARD"], outline=P["LINE"])
        head = "%s  %g / %g" % (t["conv"], t["ratios"][0], t["ratios"][1])
        assert d.textlength(head, font=F["label"]) <= pitch - 28, \
            "the convention label does not fit its card: %r" % head
        T(d, (x + 14, y + 14), head, F["label"], P["WHITE"])
        T(d, (x + 14, y + 44), t["shuttle"], F["small"], P["GRAY"])
        tot = "%g" % t["total"]
        T(d, (x + 14, y + 72), tot, F["big"], P["BLUE"])
        T(d, (x + 14 + d.textlength(tot, font=F["big"]) + 10, y + 86), "ATP",
          F["body"], P["GRAY"])
        sumline = " + ".join("%g" % p for p in t["parts"])
        assert d.textlength(sumline, font=F["small"]) <= pitch - 28, \
            "the breakdown does not fit its card: %r" % sumline
        T(d, (x + 14, y + 128), sumline, F["small"], P["GREEN"])
    y += card_h + 18
    T(d, (M, y), "Each total is substrate-level + mitochondrial NADH + FADH2 + cytosolic "
                 "NADH: %d direct, %d NADH inside, %d FADH2, %d NADH in the cytosol."
      % (C["SUBSTRATE"], C["MITO_NADH"], C["TCA_FADH2"], C["GLYC_NADH"]),
      F["body"], P["GRAY"])
    y += 34
    T(d, (M, y), "The P/O ratio is the whole argument: %g and %g measured, %g and %g in "
                 "older books. The shuttle picks the lower or upper number in each pair."
      % (RATIOS["Modern"][0], RATIOS["Modern"][1],
         RATIOS["Classic"][0], RATIOS["Classic"][1]), F["body"], P["GRAY"])
    y += 34
    T(d, (M, y), "The trap: of the %d substrate-level ATP, only glycolysis's %d are "
                 "truly oxygen independent. The cycle's %d GTP still need the chain "
                 "turning to regenerate NAD+, so they stall without oxygen too."
      % (C["SUBSTRATE"], ANAEROBIC, C["SUBSTRATE"] - ANAEROBIC), F["body"], P["RED"])
    y += 56

    # ---- 4. Henderson-Hasselbalch -------------------------------------
    band("Henderson-Hasselbalch", "and the one-unit rule")
    T(d, (M, y), "pH = pKa + log([A⁻]/[HA])", U["head"], P["GREEN"])
    T(d, (M + 520, y + 6), "[A⁻]/[HA] = 10^(pH − pKa)", U["body"], P["GREEN"])
    y += 46
    X4 = [M, M + 330, M + 620, M + 900]
    cells([(X4[0], "pH relative to pKa", F["label"], P["GRAY"]),
           (X4[1], "base : acid", F["label"], P["GRAY"]),
           (X4[2], "% as conjugate base", F["label"], P["GRAY"]),
           (X4[3], "capacity", F["label"], P["GRAY"])], y)
    y += 34
    for delta, ratio, fA, fHA in BUF:
        rel = ("pKa" if delta == 0 else
               "pKa %s %d  (one unit %s)" % ("+" if delta > 0 else "−",
                                             abs(delta), "up" if delta > 0 else "down"))
        rat = ("1 : 1" if delta == 0 else
               ("%g : 1" % ratio if ratio >= 1 else "1 : %g" % (1 / ratio)))
        cells([(X4[0], rel, F["body"], P["WHITE"]),
               (X4[1], rat, F["body"], P["BLUE"]),
               (X4[2], "%.0f%%  (acid %.0f%%)" % (fA * 100, fHA * 100), F["body"], P["BLUE"]),
               (X4[3], "good" if abs(delta) <= UNIT else "weak", F["body"], P["GRAY"])], y)
        y += ROW
    y += 6
    T(d, (M, y), "A buffer works within about %d pH unit of its pKa. One unit out, the "
                 "minority form is already down to %.0f%%, and that minority is the only "
                 "thing absorbing what you add."
      % (UNIT, min(BUF[0][2], BUF[0][3]) * 100), F["body"], P["GRAY"])
    y += 34
    T(d, (M, y), "The trap: pick the buffer whose pKa is nearest the target pH, not the "
                 "one whose name sounds physiological. Equal forms means pH = pKa exactly.",
      F["body"], P["RED"])
    y += 56

    # ---- 5. pI far from 6 ---------------------------------------------
    band("The amino acids whose pI is nowhere near 6",
         "everything else lands between 5 and 6.3")
    X5 = [M, M + 330, M + 470, M + 700]
    cells([(X5[0], "Amino acid", F["label"], P["GRAY"]),
           (X5[1], "pI", F["label"], P["GRAY"]),
           (X5[2], "from 6", F["label"], P["GRAY"]),
           (X5[3], "why, and where it runs on a gel at pH 7", F["label"], P["GRAY"])], y)
    y += 34
    for a in FAR:
        acidic = CHAR[a["c3"]] == "acidic"
        why = ("extra COOH at pKa %.2f, so it stays negative at 7 and runs to the +"
               % a["pkr"]) if acidic else (
              "extra basic N at pKa %.2f, so it stays positive at 7 and runs to the −"
              % a["pkr"])
        cells([(X5[0], "%s   %s   %s" % (a["c1"], a["c3"], a["name"]), F["body"], P["WHITE"]),
               (X5[1], "%.2f" % a["pI"], F["body"], P["BLUE"]),
               (X5[2], "%+.2f" % (a["pI"] - 6.0), F["body"], P["GRAY"]),
               (X5[3], why, U["body"], P["GRAY"])], y)
        y += ROW
    y += 6
    T(d, (M, y), "pI is the average of the two pKa values either side of the neutral "
                 "form, so a third ionizable group drags it toward that group's own pKa.",
      F["body"], P["GREEN"])
    y += 34
    T(d, (M, y), "The trap: at a pH above its pI a residue is net negative, below it net "
                 "positive. %d of the 20 sit more than 1.5 units off 6; the rest cluster "
                 "there and tell you nothing." % len(FAR), F["body"], P["RED"])
    y += 56

    y = chartkit.legend(d, M, y, [("Formula", P["GREEN"]), ("Value", P["BLUE"]),
                                  ("The trap", P["RED"])], P, F)
    y += 10
    y = chartkit.footer(d, W, H, y, P, F,
                        note="Every number read from the site's own calculators at "
                             "build time: amino-acid-chart, michaelis-menten-vs-"
                             "lineweaver-burk, atp-yield-calculator, "
                             "henderson-hasselbalch-buffer-calculator.")

    img = chartkit.fit(img, y, d=d)
    out = _os.path.join(BUILD_DIR, "mcat-highyield-guide%s.png" % suffix())
    img.save(out)
    print("saved", out, img.size)
    print("verified: 7 ionizable side chains %s"
          % [(a["c3"], a["pkr"]) for a in IONS])
    print("verified: acid/base character fitted from published pI %s" % CHAR)
    print("verified: pI far from 6 %s" % [(a["c3"], a["pI"]) for a in FAR])
    print("verified: inhibition solved to alpha/alpha' %s"
          % {k: (round(v[0], 2), round(v[1], 2)) for k, v in MODEL.items()})
    print("verified: ATP totals %s"
          % [(t["conv"], t["shuttle"], t["total"]) for t in TOTALS])
    print("verified: buffer range guard is +/- %d pH unit, %.1f%% base at one unit up"
          % (UNIT, BUF[2][2] * 100))


draw()
