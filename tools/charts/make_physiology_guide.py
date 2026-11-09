#!/usr/bin/env python3
"""Physiology on one page, with the oxygen dissociation curves actually drawn.

Physiology is a practice subject with 34 questions and exactly one chart
(membrane transport), while its pages carry real demand: the oxygen
dissociation curve page alone takes about 326 Bing impressions, with cardiac
output, renal clearance and osmotic pressure behind it.

The hero is the plot. Myoglobin, adult hemoglobin and fetal hemoglobin go on
one set of axes, drawn from the Hill parameters PARSED out of
oxygen-dissociation-curve-calculator.html rather than typed, and each P50 gets
a dropline off the 50% line. Every other value is read out of the page it
belongs to and asserted here, so a page edit fails this build instead of
shipping a chart that disagrees with the site.

Colour carries meaning and nothing else: one hue per curve, used in the plot,
the legend, the droplines, the parameter panel and the shift table, plus one
hue per shift direction. The direction trap is the whole reason the shift table
exists. A RIGHT shift is LOWER affinity and a HIGHER P50, which is the pair
students reverse, so the chart states it twice and quotes the page's own
wording rather than paraphrasing it. The page also keeps rising temperature and
2,3-BPG as separate modulators rather than folding them into the Bohr effect,
and the bracket tags on the table are the page's own.
"""
import os as _os, re, sys
from PIL import Image, ImageDraw

sys.path.insert(0, _os.path.dirname(_os.path.abspath(__file__)))
import chartkit
from lightmode import theme, suffix

HERE = _os.path.dirname(_os.path.abspath(__file__))
SITE = _os.path.join(HERE, "..", "..")
BUILD_DIR = _os.path.join(HERE, "build")
_os.makedirs(BUILD_DIR, exist_ok=True)

LIGHT, P = theme()
F = chartkit.fonts()
W, M = chartkit.WIDTH, chartkit.MARGIN


def page(name):
    return open(_os.path.join(SITE, name), encoding="utf-8").read()


def plain(s):
    """Strip tags and the sub/superscripts Arial cannot draw, nothing else."""
    s = re.sub(r"<[^>]+>", "", s)
    for a, b in (("₂", "2"), ("₃", "3"), ("⁺", "+"),
                 ("⁻", "-"), ("&amp;", "&"), ("&ndash;", "to")):
        s = s.replace(a, b)
    return re.sub(r"\s+", " ", s).strip()


# =========================================================================
# values pulled from the site, not typed
# =========================================================================

# --- 1. the curves ------------------------------------------------------
ox = page("oxygen-dissociation-curve-calculator.html")

blk = re.search(r"const CURVES\s*=\s*\{([\s\S]*?)\n\};", ox)
assert blk, "CURVES table not found on the oxygen page"
CURVES = {}
for key, body in re.findall(r"(\w+):\s*\{([^}]*)\}", blk.group(1)):
    p50 = float(re.search(r"p50:\s*([\d.]+)", body).group(1))
    n = float(re.search(r"\bn:\s*([\d.]+)", body).group(1))
    label = re.search(r'label:"([^"]*)"', body).group(1)
    CURVES[key] = dict(p50=p50, n=n, label=label)

assert set(CURVES) == {"myo", "adult", "fetal"}, CURVES
# The three P50 values, asserted before anything is drawn.
assert (CURVES["myo"]["p50"], CURVES["myo"]["n"]) == (2.8, 1.0), CURVES["myo"]
assert (CURVES["adult"]["p50"], CURVES["adult"]["n"]) == (26.6, 2.8), CURVES["adult"]
assert (CURVES["fetal"]["p50"], CURVES["fetal"]["n"]) == (19.0, 2.8), CURVES["fetal"]
assert [CURVES[k]["label"] for k in ("myo", "adult", "fetal")] == \
    ["Myoglobin", "Adult Hb", "Fetal Hb"], CURVES

# The Hill equation itself, so a change to the maths fails the build.
assert "100*Math.pow(pO2,n)/(Math.pow(p50,n)+Math.pow(pO2,n))" in \
    ox.replace(" ", ""), "Hill equation changed on the oxygen page"
HILL = "%Sat = 100 × pO2ⁿ / (P50ⁿ + pO2ⁿ)"


def sat(po2, p50, n):
    """The page's own Hill equation, same form, same parameters."""
    if po2 <= 0:
        return 0.0
    return 100.0 * po2 ** n / (p50 ** n + po2 ** n)


# P50 means half saturation: prove the implementation agrees with the name,
# and with what the page's own quiz says about pO2 = 19.
for _k, _c in CURVES.items():
    assert abs(sat(_c["p50"], _c["p50"], _c["n"]) - 50.0) < 1e-9, _k
assert abs(sat(19.0, CURVES["fetal"]["p50"], CURVES["fetal"]["n"]) - 50.0) < 1e-9
assert "Fetal hemoglobin, whose P50 is 19 mmHg" in ox

# --- 2. the shift block, quoted from the page ---------------------------
sh = re.search(r'<div class="work">(Right shift[\s\S]*?)</div>', ox)
assert sh, "shift block not found on the oxygen page"
SHIFT = sh.group(1)
RIGHT_HEAD = "Right shift (lower O2 affinity, easier unloading)"
LEFT_HEAD = "Left shift (higher O2 affinity, easier loading)"
assert RIGHT_HEAD in SHIFT and LEFT_HEAD in SHIFT, SHIFT
assert "tissue conditions" in SHIFT and "lung conditions" in SHIFT

lines = [l for l in SHIFT.split("\n")]
RIGHT_ROWS = []          # [(modulator, the page's own bracket tag)]
for l in lines[1:3]:
    parts = re.split(r"\s{2,}", l.strip())
    tag = parts[-1]
    assert tag.startswith("[") and tag.endswith("]"), l
    for mod in parts[:-1]:
        RIGHT_ROWS.append((mod, tag))
assert len(RIGHT_ROWS) == 4, RIGHT_ROWS
assert ("↑ CO2", "[Bohr effect]") in RIGHT_ROWS, RIGHT_ROWS
assert ("↑ 2,3-BPG", "[separate right-shifters]") in RIGHT_ROWS, RIGHT_ROWS

LEFT_ROWS = re.split(r"\s{2,}", lines[lines.index("") + 2].strip())
assert len(LEFT_ROWS) == 4 and LEFT_ROWS[0] == "↓ CO2", LEFT_ROWS

MECH = plain(SHIFT[SHIFT.index("Mechanism:"):]).replace('"', "")

# --- 3. the equations ---------------------------------------------------
co = page("cardiac-output-calculator.html")


def unit(src, field):
    m = re.search(r'label for="%s">[^<(]*\(([^)]*)\)' % field, src)
    assert m, "unit label for %s not found" % field
    return plain(m.group(1))


def named(src, field):
    """The words beside a symbol on its own input label."""
    m = re.search(r'label for="%s">([^<(]*)\(' % field, src)
    assert m, "label text for %s not found" % field
    txt = plain(m.group(1))
    txt = txt.split(", ", 1)[1] if ", " in txt else txt
    # Lower the leading capital of an ordinary word, never of O2, VO2 or GFR.
    return txt[0].lower() + txt[1:] if len(txt) > 1 and txt[1].islower() else txt


HR_U, SV_U = unit(co, "hr"), unit(co, "sv")
VO2_U, CAO2_U, CVO2_U = unit(co, "vo2"), unit(co, "cao2"), unit(co, "cvo2")
assert (HR_U, SV_U) == ("beats/min", "mL/beat"), (HR_U, SV_U)
assert (VO2_U, CAO2_U, CVO2_U) == ("mL/min", "mL/L", "mL/L"), (VO2_U, CAO2_U, CVO2_U)
assert "CO = HR × SV = ${hr} × ${sv}" in co, "CO formula changed"
assert "CO = VO₂ / (CaO₂ − CvO₂) = ${vo2} / (${cao2} − ${cvo2})" in co, \
    "Fick formula changed"
assert "giving CO ≈ 5 L/min" in co, "resting cardiac output changed"
EDV_NAME = re.search(r"its (end-diastolic volume) \(EDV\)", co)
assert EDV_NAME, "EDV expansion not found on the cardiac page"
EDV_NAME = EDV_NAME.group(1)

ef = re.search(r"EF = SV / EDV = (\d+) / (\d+) = [\d.]+ = ([\d.]+)%", co)
assert ef and ef.groups() == ("70", "120", "58.3"), ef and ef.groups()
EF_RANGE = re.search(r"A normal EF is roughly ([\d]+-[\d]+%)", co)
assert EF_RANGE, "normal EF range not found"
EF_RANGE = EF_RANGE.group(1)

rc = page("renal-clearance-calculator.html")
UX_U, V_U, PX_U = unit(rc, "ux"), unit(rc, "v"), unit(rc, "px")
assert (UX_U, V_U, PX_U) == ("mg/mL", "mL/min", "mg/mL"), (UX_U, V_U, PX_U)
GFR_NAME = re.search(r"GFR \((glomerular filtration rate)\)", rc)
RPF_NAME = re.search(r"RPF \((renal plasma flow)\)", rc)
assert GFR_NAME and RPF_NAME, "GFR/RPF expansions not found on the renal page"
GFR_NAME, RPF_NAME = GFR_NAME.group(1), RPF_NAME.group(1)
assert "Cx = (Ux × V) / Px = (${ux} × ${v}) / ${px}" in rc, "clearance formula changed"
assert "FF = GFR / RPF = ${gfr} / ${rpf}" in rc, "filtration fraction formula changed"
nv = re.search(r"Normal values: GFR ≈ ([\d]+) mL/min[^,]*, RPF ≈ ([\d-]+) mL/min, "
               r"filtration fraction ≈ ([\d]+)%", rc)
assert nv, "renal normal values not found"
GFR_N, RPF_N, FF_N = nv.groups()
assert (GFR_N, RPF_N, FF_N) == ("125", "600-700", "20"), nv.groups()

EQUATIONS = [
    ("Cardiac output", "CO = HR × SV",
     "HR %s · SV %s" % (named(co, "hr"), named(co, "sv")),
     "%s × %s = mL/min. Divide by 1000 for L/min, about 5 L/min at rest."
     % (HR_U, SV_U)),
    ("Cardiac output, Fick", "CO = VO2 / (CaO2 − CvO2)",
     "VO2 %s · CaO2 %s · CvO2 %s"
     % (named(co, "vo2"), named(co, "cao2"), named(co, "cvo2")),
     "%s divided by %s = L/min. The same quantity, through oxygen delivery."
     % (VO2_U, CAO2_U)),
    ("Ejection fraction", "EF = SV / EDV",
     "SV %s · EDV %s" % (named(co, "sv"), EDV_NAME),
     "A fraction, no units. %s / %s = %s%%, normal %s."
     % (ef.group(1), ef.group(2), ef.group(3), EF_RANGE)),
    ("Renal clearance", "Cx = (Ux × V) / Px",
     "Ux %s · V %s · Px %s"
     % (named(rc, "ux"), named(rc, "v"), named(rc, "px")),
     "(%s × %s) / %s = mL/min. Inulin clearance is GFR, about %s mL/min."
     % (UX_U, V_U, PX_U, GFR_N)),
    ("Filtration fraction", "FF = GFR / RPF",
     "GFR %s · RPF %s" % (GFR_NAME, RPF_NAME),
     "A fraction, no units. About %s%%, RPF about %s mL/min from PAH."
     % (FF_N, RPF_N)),
]

# --- 4. tonicity --------------------------------------------------------
op = page("osmotic-pressure-calculator.html")
assert "Osmolarity = i × M = ${i} × ${M}" in op, "osmolarity formula changed"
assert "π = iMRT = ${i} × ${M} × 0.08206" in op, "van't Hoff formula changed"
R_GAS = re.search(r"const R=([\d.]+);", op)
assert R_GAS and R_GAS.group(1) == "0.08206", R_GAS and R_GAS.group(1)
R_GAS = R_GAS.group(1)

BLOOD = re.search(r"bloodOsm\s*=\s*([\d.]+)", op)
assert BLOOD and BLOOD.group(1) == "0.30", BLOOD and BLOOD.group(1)
BLOOD = float(BLOOD.group(1))
hi = re.search(r'if\(osm>bloodOsm\*([\d.]+)\)\{label="([^"]+)"', op)
lo = re.search(r'else if\(osm<bloodOsm\*([\d.]+)\)\{label="([^"]+)"', op)
iso = re.search(r'else \{label="(Isotonic[^"]+)"', op)
assert hi and lo and iso, "tonicity classifier not found on the osmotic page"
HI_F, LO_F = float(hi.group(1)), float(lo.group(1))
assert (HI_F, LO_F) == (1.05, 0.95), (HI_F, LO_F)


def split_label(s):
    name, rest = s.split(", ", 1)
    return name.replace(" to blood", "").replace(" with blood", ""), rest


TONICITY = [
    (split_label(hi.group(2))[0],
     "> %.3f Osm  (more than %.2f × blood)" % (BLOOD * HI_F, HI_F),
     split_label(hi.group(2))[1]),
    (split_label(iso.group(1))[0],
     "%.3f to %.3f Osm  (within 5%% of blood)" % (BLOOD * LO_F, BLOOD * HI_F),
     split_label(iso.group(1))[1]),
    (split_label(lo.group(2))[0],
     "< %.3f Osm  (less than %.2f × blood)" % (BLOOD * LO_F, LO_F),
     split_label(lo.group(2))[1]),
]
assert [t[0] for t in TONICITY] == ["Hypertonic", "Isotonic (~0.30 Osm)",
                                    "Hypotonic"], TONICITY
assert "water leaves cells (they shrink)" in TONICITY[0][2], TONICITY[0]

sel = re.search(r'<select id="solute">([\s\S]*?)</select>', op)
assert sel, "solute list not found on the osmotic page"
SOLUTES = [(plain(t).split(" (i")[0], v) for v, t in
           re.findall(r'<option value="([^"]+)">([^<]+)</option>', sel.group(1))
           if re.match(r"^\d", v)]
assert len(SOLUTES) == 5, SOLUTES
I_LIST = " · ".join("%s %s" % (name, v[0]) for name, v in SOLUTES)
assert "NaCl 2" in I_LIST and "Glucose 1" in I_LIST and "CaCl2 3" in I_LIST, I_LIST
assert "reflection coefficient" in op and "iso-osmotic and still hypotonic" in op

# One hue per curve, carried everywhere that curve is named, plus one hue per
# shift direction. Myoglobin and adult Hb land on the site's own curve colours;
# the palette has no match for the site's fetal tan, so fetal takes PURPLE.
COL = {"myo": P["AMBER"], "adult": P["GREEN"], "fetal": P["PURPLE"]}
RIGHT_C, LEFT_C = P["RED"], P["BLUE"]

ORDER = sorted(CURVES, key=lambda k: CURVES[k]["p50"])     # left to right
NOTES = {
    "myo": "One subunit, one site, no cooperativity, so the curve is a plain "
           "hyperbola. Highest affinity of the three: it stores oxygen in "
           "muscle rather than carrying it.",
    "fetal": "Cooperative, but left of adult Hb. It binds 2,3-BPG weakly and "
             "2,3-BPG is what lowers affinity, so it holds oxygen tightly "
             "enough to pull it across the placenta.",
    "adult": "Four subunits binding cooperatively, which is where the S-shape "
             "comes from. Loads in the lung, unloads in tissue, and this is "
             "the curve that shifts.",
}


# =========================================================================
# drawing
# =========================================================================

def wrap(d, s, font, maxw):
    out, cur = [], ""
    for word in s.split():
        trial = (cur + " " + word).strip()
        if cur and d.textlength(trial, font=font) > maxw:
            out.append(cur)
            cur = word
        else:
            cur = trial
    if cur:
        out.append(cur)
    return out


def dashed(d, a, b, colour, dash=11, gap=8, width=3):
    (x0, y0), (x1, y1) = a, b
    span = max(abs(x1 - x0), abs(y1 - y0))
    if span == 0:
        return
    ux, uy = (x1 - x0) / span, (y1 - y0) / span
    t = 0.0
    while t < span:
        e = min(t + dash, span)
        d.line([x0 + ux * t, y0 + uy * t, x0 + ux * e, y0 + uy * e],
               fill=colour, width=width)
        t = e + gap


def draw():
    H = 2900
    img = Image.new("RGB", (W, H), P["BG"])
    d = ImageDraw.Draw(img)
    T = chartkit.safe_text
    y = M

    T(d, (M, y), "Physiology, one page", F["title"], P["WHITE"]); y += 70
    T(d, (M, y), "The oxygen curves drawn to scale, which way they shift, and "
                 "the equations with their units.", F["sub"], P["GRAY"]); y += 56

    def band(title):
        nonlocal y
        d.rectangle([M, y, W - M, y + 2], fill=P["LINE"]); y += 18
        T(d, (M, y), title, F["head"], P["AMBER"]); y += 42

    # ---------------- the hero: three curves on one set of axes ----------
    band("The oxygen dissociation curves")

    T(d, (M, y), "% saturation", F["small"], P["DIM"]); y += 30
    AX_L, AX_R = 150, 890
    AX_T, AX_B = y, y + 470
    PW, PH = AX_R - AX_L, AX_B - AX_T

    def sx(po2):
        return AX_L + po2 / 100.0 * PW

    def sy(s):
        return AX_B - s / 100.0 * PH

    # grid, then axes on top of it
    for s in (0, 25, 50, 75, 100):
        d.line([AX_L, sy(s), AX_R, sy(s)], fill=P["LINE"], width=1)
        lab = "%d" % s
        T(d, (AX_L - 16 - d.textlength(lab, font=F["small"]), sy(s) - 11),
          lab, F["small"], P["DIM"])
    for v in range(0, 101, 20):
        d.line([sx(v), AX_T, sx(v), AX_B], fill=P["LINE"], width=1)
    d.line([AX_L, AX_T, AX_L, AX_B], fill=P["GRAY"], width=2)
    d.line([AX_L, AX_B, AX_R, AX_B], fill=P["GRAY"], width=2)

    # the 50% line: every P50 is read off it
    dashed(d, (AX_L, sy(50)), (AX_R, sy(50)), P["GRAY"], dash=7, gap=7, width=2)
    half = "50% saturation"
    T(d, (AX_R - 8 - d.textlength(half, font=F["small"]), sy(50) - 30),
      half, F["small"], P["GRAY"])

    # droplines first, so the curves sit over them
    for k in ORDER:
        c = CURVES[k]
        dashed(d, (sx(c["p50"]), sy(50)), (sx(c["p50"]), AX_B), COL[k])

    for k in ORDER:
        c = CURVES[k]
        pts = []
        steps = 400
        for i in range(steps + 1):
            po2 = 100.0 * i / steps
            pts.append((sx(po2), sy(sat(po2, c["p50"], c["n"]))))
        d.line(pts, fill=COL[k], width=5, joint="curve")

    # a dot where each curve crosses 50%, and the P50 under the axis
    for k in ORDER:
        c = CURVES[k]
        x = sx(c["p50"])
        d.ellipse([x - 7, sy(50) - 7, x + 7, sy(50) + 7], fill=COL[k],
                  outline=P["BG"], width=2)
        d.line([x, AX_B, x, AX_B + 9], fill=COL[k], width=3)

    # which direction a shift goes, stated on the plot itself
    ax, ay = sx(55), sy(16)
    d.line([ax, ay, ax + 310, ay], fill=P["GRAY"], width=2)
    d.line([ax, ay, ax + 14, ay - 8], fill=P["GRAY"], width=2)
    d.line([ax, ay, ax + 14, ay + 8], fill=P["GRAY"], width=2)
    d.line([ax + 310, ay, ax + 296, ay - 8], fill=P["GRAY"], width=2)
    d.line([ax + 310, ay, ax + 296, ay + 8], fill=P["GRAY"], width=2)
    T(d, (ax, ay - 40), "← left shift", F["label"], LEFT_C)
    rs = "right shift →"
    T(d, (ax + 310 - d.textlength(rs, font=F["label"]), ay - 40), rs,
      F["label"], RIGHT_C)
    T(d, (ax, ay + 16), "holds oxygen", F["small"], LEFT_C)
    gl = "gives it up"
    T(d, (ax + 310 - d.textlength(gl, font=F["small"]), ay + 16), gl,
      F["small"], RIGHT_C)

    # x ticks, then the P50 values in their curve's colour, then the axis name
    for v in range(0, 101, 20):
        d.line([sx(v), AX_B, sx(v), AX_B + 7], fill=P["GRAY"], width=2)
        lab = "%d" % v
        T(d, (sx(v) - d.textlength(lab, font=F["small"]) / 2, AX_B + 12),
          lab, F["small"], P["DIM"])
    for k in ORDER:
        c = CURVES[k]
        lab = ("%g" % c["p50"])
        T(d, (sx(c["p50"]) - d.textlength(lab, font=F["label"]) / 2, AX_B + 44),
          lab, F["label"], COL[k])
    xt = "pO2 (mmHg)"
    T(d, (AX_L + PW / 2 - d.textlength(xt, font=F["body"]) / 2, AX_B + 78),
      xt, F["body"], P["GRAY"])

    # ---------------- the parameter panel, same hues ---------------------
    PX0, PW2 = 950, (W - M) - 950
    py = AX_T
    py = chartkit.legend(d, PX0, py,
                         [(CURVES[k]["label"], COL[k]) for k in ORDER], P, F,
                         gap=26)
    py += 10
    for k in ORDER:
        c = CURVES[k]
        T(d, (PX0, py), c["label"], F["label"], COL[k])
        stat = "P50 %g mmHg   n = %g" % (c["p50"], c["n"])
        T(d, (W - M - d.textlength(stat, font=F["body"]), py), stat,
          F["body"], P["WHITE"])
        py += 32
        for line in wrap(d, NOTES[k], F["small"], PW2):
            T(d, (PX0, py), line, F["small"], P["GRAY"]); py += 26
        py += 16

    d.rectangle([PX0, py, W - M, py + 136], fill=P["CARD"])
    T(d, (PX0 + 18, py + 16), "Hill equation", F["label"], P["WHITE"])
    T(d, (PX0 + 18, py + 48), HILL, F["body"], P["WHITE"])
    for i, line in enumerate(wrap(
            d, "n is cooperativity, not a count of sites: Hb has four and "
               "n is about 2.8.", F["small"], PW2 - 36)):
        T(d, (PX0 + 18, py + 84 + i * 24), line, F["small"], P["GRAY"])
    py += 160

    T(d, (AX_L, AX_B + 112), "Droplines mark each P50: the pO2 that gives "
                             "50% saturation.", F["small"], P["DIM"])
    y = max(AX_B + 112 + chartkit.SCALE["xs"], py) + 30

    # ---------------- which way it shifts --------------------------------
    band("Which way the curve shifts, and the direction students reverse")

    T(d, (M, y), CURVES["adult"]["label"], F["label"], COL["adult"])
    T(d, (M + d.textlength(CURVES["adult"]["label"], font=F["label"]) + 10, y),
      "is the curve that moves. Right is tissue, left is lung.",
      F["body"], P["GRAY"]); y += 48

    C1, C2 = M, 820
    CW = 660
    top = y
    for x, head, col, rows, where in (
            (C1, RIGHT_HEAD, RIGHT_C, RIGHT_ROWS, "tissue conditions"),
            (C2, LEFT_HEAD, LEFT_C, [(r, "") for r in LEFT_ROWS],
             "lung conditions")):
        yy = top
        d.rectangle([x, yy, x + CW, yy + 2], fill=col); yy += 14
        name, detail = head.split(" (", 1)
        T(d, (x, yy), name.upper(), F["head"], col)
        yy += 40
        for line in wrap(d, detail.rstrip(")") + "  ·  " + where,
                         F["body"], CW):
            T(d, (x, yy), line, F["body"], col); yy += 30
        yy += 10
        for mod, tag in rows:
            T(d, (x, yy), mod, F["label"], P["WHITE"])
            if tag:
                T(d, (x + 330, yy), tag, F["small"], P["DIM"])
            yy += 34
        y = max(y, yy)

    y += 10
    tie = CURVES["fetal"]["label"]
    T(d, (C2, y), tie, F["label"], COL["fetal"])
    T(d, (C2 + d.textlength(tie, font=F["label"]) + 10, y),
      "is a permanent left shift: P50 %g against %g."
      % (CURVES["fetal"]["p50"], CURVES["adult"]["p50"]), F["body"], P["GRAY"])
    myo = CURVES["myo"]["label"]
    T(d, (C1, y), myo, F["label"], COL["myo"])
    T(d, (C1 + d.textlength(myo, font=F["label"]) + 10, y),
      "sits far left of both: P50 %g." % CURVES["myo"]["p50"],
      F["body"], P["GRAY"])
    y += 46

    for line in wrap(d, MECH, F["body"], W - 2 * M):
        T(d, (M, y), line, F["body"], P["GRAY"]); y += 30
    y += 16

    trap = ("A RIGHT shift is LOWER affinity and a HIGHER P50.")
    trap2 = ("The two halves feel opposite, which is why this is the one "
             "students reverse. Lower affinity means hemoglobin needs a "
             "higher pO2 to be half full, so P50 goes up.")
    box_lines = wrap(d, trap2, F["body"], W - 2 * M - 48)
    bh = 30 + 34 + len(box_lines) * 30
    d.rectangle([M, y, W - M, y + bh], fill=P["CHIP"])
    T(d, (M + 24, y + 18), trap, F["head"], P["WHITE"])
    for i, line in enumerate(box_lines):
        T(d, (M + 24, y + 60 + i * 30), line, F["body"], P["GRAY"])
    y += bh + 42

    # ---------------- the equations --------------------------------------
    band("The equations, with their units")
    NOTE_X = M + 740
    NOTE_W = (W - M) - NOTE_X
    for name, formula, gloss, note in EQUATIONS:
        T(d, (M, y), name, F["label"], P["WHITE"])
        T(d, (M + 330, y), formula, F["body"], P["WHITE"])
        gy = y + 32
        for line in wrap(d, gloss, F["small"], NOTE_X - (M + 330) - 30):
            T(d, (M + 330, gy), line, F["small"], P["DIM"]); gy += 24
        yy = y
        for line in wrap(d, note, F["body"], NOTE_W):
            T(d, (NOTE_X, yy), line, F["body"], P["GRAY"]); yy += 30
        y = max(y + 40, yy + 10, gy + 8)
    y += 18

    # ---------------- tonicity -------------------------------------------
    band("Tonicity")
    T(d, (M, y), "osmolarity = i × M", F["body"], P["WHITE"])
    for line in wrap(d, "i = particles per formula unit:  %s" % I_LIST,
                     F["body"], (W - M) - (M + 330)):
        T(d, (M + 330, y), line, F["body"], P["GRAY"]); y += 30
    y += 8
    T(d, (M, y), "π = iMRT", F["body"], P["WHITE"])
    for line in wrap(d, "R = %s L·atm/mol·K, T in kelvin. Blood plasma is the "
                        "reference at %.2f Osm." % (R_GAS, BLOOD),
                     F["body"], (W - M) - (M + 330)):
        T(d, (M + 330, y), line, F["body"], P["GRAY"]); y += 30
    y += 16

    TON_X = M + 800
    for name, rule, effect in TONICITY:
        T(d, (M, y), name, F["label"], P["WHITE"])
        T(d, (M + 330, y), rule, F["body"], P["WHITE"])
        yy = y
        for line in wrap(d, "red cell: %s" % effect, F["body"],
                         (W - M) - TON_X):
            T(d, (TON_X, yy), line, F["body"], P["GRAY"]); yy += 30
        y = max(y + 38, yy + 8)
    y += 12
    for line in wrap(d, "Osmolarity is not tonicity. Urea raises osmolarity "
                        "but crosses the membrane about as freely as water "
                        "(reflection coefficient σ near 0), so a urea "
                        "solution can be iso-osmotic and still leave the cell "
                        "unprotected.", F["body"], W - 2 * M):
        T(d, (M, y), line, F["body"], P["GRAY"]); y += 30
    y += 46

    y = chartkit.footer(d, W, H, y, P, F,
                        note="Curves plotted from the Hill parameters in the "
                             "site's own oxygen dissociation calculator; every "
                             "value read from its page at build time.")

    img = chartkit.fit(img, y, d=d)
    out = _os.path.join(BUILD_DIR, "physiology-guide%s.png" % suffix())
    img.save(out)
    print("saved", out, img.size)
    print("verified: P50 %s, n %s; %d right-shifters, %d left-shifters; "
          "%d equations; tonicity band %.3f to %.3f Osm around %.2f"
          % ({k: CURVES[k]["p50"] for k in ORDER},
             {k: CURVES[k]["n"] for k in ORDER},
             len(RIGHT_ROWS), len(LEFT_ROWS), len(EQUATIONS),
             BLOOD * LO_F, BLOOD * HI_F, BLOOD))


draw()
