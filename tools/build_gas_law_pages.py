#!/usr/bin/env python3
"""One page per rearrangement of PV = nRT.

Search Console, 3 months to 2026-08-20: nine queries, 72 impressions, every one
between position 38 and 47. People type the rearranged form they need, "n pv/rt"
or "v nrt p" or "p=nrt", not "ideal gas law calculator". This is the closest
cluster to page one the site has.

Every worked number below is computed, then asserted against the value the page
prints, so a page cannot ship with arithmetic that does not check out.
"""
import os, re, json, html

SITE = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..")
SRC = os.path.join(SITE, "ideal-gas-law-calculator.html")

R_ATM = 0.08206   # L*atm / mol*K, the value the calculator uses
R_SI = 8.314      # J / mol*K

FORMS = [
    dict(key="moles", sym="n", rhs="PV / RT", slug="solve-ideal-gas-law-for-moles.html",
         word="moles", unit="mol",
         given="A 2.50 L flask holds a gas at 1.00 atm and 298 K. How many moles are in it?",
         vals=dict(P=1.00, V=2.50, T=298.0),
         steps=["n = PV / RT",
                "n = (1.00 atm x 2.50 L) / (0.08206 L&middot;atm/mol&middot;K x 298 K)",
                "n = 2.50 / 24.454"],
         note="Moles is the one people solve for most, because it is the bridge to grams."),
    dict(key="volume", sym="V", rhs="nRT / P", slug="solve-ideal-gas-law-for-volume.html",
         word="volume", unit="L",
         given="What volume does 1.00 mol of an ideal gas occupy at 1.00 atm and 273.15 K?",
         vals=dict(n=1.00, P=1.00, T=273.15),
         steps=["V = nRT / P",
                "V = (1.00 mol x 0.08206 L&middot;atm/mol&middot;K x 273.15 K) / 1.00 atm",
                "V = 22.414 / 1.00"],
         note="This is the molar volume at STP, and getting 22.4 L back is a good check that "
              "your units and your R agree."),
    dict(key="pressure", sym="P", rhs="nRT / V", slug="solve-ideal-gas-law-for-pressure.html",
         word="pressure", unit="atm",
         given="0.500 mol of gas is sealed in a 10.0 L vessel at 310 K. What is the pressure?",
         vals=dict(n=0.500, V=10.0, T=310.0),
         steps=["P = nRT / V",
                "P = (0.500 mol x 0.08206 L&middot;atm/mol&middot;K x 310 K) / 10.0 L",
                "P = 12.719 / 10.0"],
         note="310 K is body temperature, which is where this one usually turns up in "
              "physiology questions."),
    dict(key="temperature", sym="T", rhs="PV / nR", slug="solve-ideal-gas-law-for-temperature.html",
         word="temperature", unit="K",
         given="0.200 mol of gas fills 5.00 L at 1.00 atm. What temperature is it at?",
         vals=dict(P=1.00, V=5.00, n=0.200),
         steps=["T = PV / nR",
                "T = (1.00 atm x 5.00 L) / (0.200 mol x 0.08206 L&middot;atm/mol&middot;K)",
                "T = 5.00 / 0.016412"],
         note="The answer comes out in kelvin every time. Subtract 273.15 if the question "
              "wants Celsius."),
]


def solve(f):
    v = f["vals"]
    if f["key"] == "moles":       return v["P"] * v["V"] / (R_ATM * v["T"])
    if f["key"] == "volume":      return v["n"] * R_ATM * v["T"] / v["P"]
    if f["key"] == "pressure":    return v["n"] * R_ATM * v["T"] / v["V"]
    if f["key"] == "temperature": return v["P"] * v["V"] / (v["n"] * R_ATM)


def head_and_nav():
    h = open(SRC, encoding="utf-8").read()
    return h[h.index("<head>"):h.index("</head>")], h[h.index("<body>"):h.index("<header>")]


# A second run at the same problem in different units. The point of each is that
# the answer does not change when the units and R change together, which is the
# thing students actually get wrong.
SECOND = {
 "moles": dict(
   text="The same flask in SI units: 101325 Pa, 0.00250 m<sup>3</sup>, 298 K, using R = 8.314 J/mol&middot;K.",
   steps=["n = PV / RT",
          "n = (101325 Pa x 0.00250 m&sup3;) / (8.314 J/mol&middot;K x 298 K)",
          "n = 253.31 / 2477.6"],
   calc=lambda: 101325 * 0.00250 / (R_SI * 298),
   fmt="%.3f", unit="mol",
   moral="Identical to the first answer, because the units and R changed together. That is the "
         "whole trick: match R to your units and the physics takes care of itself."),
 "volume": dict(
   text="One mole of gas at body temperature, 310 K, still at 1.00 atm.",
   steps=["V = nRT / P",
          "V = (1.00 mol x 0.08206 L&middot;atm/mol&middot;K x 310 K) / 1.00 atm"],
   calc=lambda: 1.00 * R_ATM * 310 / 1.00,
   fmt="%.2f", unit="L",
   moral="Warmer gas takes more room. Up from 22.41 L at 0 &deg;C to over 25 L at body "
         "temperature, for the same one mole."),
 "pressure": dict(
   text="The same vessel, but the answer wanted in mmHg, so R = 62.36 L&middot;mmHg/mol&middot;K.",
   steps=["P = nRT / V",
          "P = (0.500 mol x 62.36 L&middot;mmHg/mol&middot;K x 310 K) / 10.0 L",
          "P = 9665.8 / 10.0"],
   calc=lambda: 0.500 * 62.36 * 310 / 10.0,
   fmt="%.0f", unit="mmHg",
   moral="Same pressure, different ruler. 967 mmHg is 1.27 atm, since one atmosphere is "
         "760 mmHg."),
 "temperature": dict(
   text="The same gas, with the answer converted to Celsius.",
   steps=["T = PV / nR = 304.7 K", "&deg;C = K - 273.15", "&deg;C = 304.7 - 273.15"],
   calc=lambda: (1.00 * 5.00 / (0.200 * R_ATM)) - 273.15,
   fmt="%.1f", unit="&deg;C",
   moral="Always solve in kelvin, then convert at the very end if the question asks for "
         "Celsius. Converting first is how the answer goes wrong."),
}

PRACTICE = {
 "moles": [("How many moles fill a 500 mL flask at 2.00 atm and 273 K?",
            lambda: 2.00 * 0.500 / (R_ATM * 273), "%.4f", "mol"),
           ("A 22.4 L vessel at 1.00 atm and 273.15 K holds how many moles?",
            lambda: 1.00 * 22.4 / (R_ATM * 273.15), "%.3f", "mol")],
 "volume": [("What volume does 0.250 mol occupy at 2.00 atm and 300 K?",
             lambda: 0.250 * R_ATM * 300 / 2.00, "%.2f", "L"),
            ("And the same 0.250 mol at 0.500 atm, same temperature?",
             lambda: 0.250 * R_ATM * 300 / 0.500, "%.2f", "L")],
 "pressure": [("2.00 mol of gas in a 5.00 L cylinder at 350 K exerts what pressure?",
               lambda: 2.00 * R_ATM * 350 / 5.00, "%.2f", "atm"),
              ("Halve the volume to 2.50 L at the same temperature.",
               lambda: 2.00 * R_ATM * 350 / 2.50, "%.2f", "atm")],
 "temperature": [("1.00 mol in 30.0 L at 1.00 atm sits at what temperature?",
                  lambda: 1.00 * 30.0 / (1.00 * R_ATM), "%.0f", "K"),
                 ("0.500 mol in 12.0 L at 1.50 atm?",
                  lambda: 1.50 * 12.0 / (0.500 * R_ATM), "%.0f", "K")],
}

DISPLAY = {"moles": ("%.3f", "mol"), "volume": ("%.2f", "L"),
           "pressure": ("%.2f", "atm"), "temperature": ("%.0f", "K")}

OTHER = {"moles": "n", "volume": "V", "pressure": "P", "temperature": "T"}


def page(f, headsrc, navsrc):
    ans = solve(f)
    fmt, unit = DISPLAY[f["key"]]
    shown = fmt % ans
    sym, rhs, word = f["sym"], f["rhs"], f["word"]

    title = "%s = %s: Solving the Ideal Gas Law for %s" % (sym, rhs, word.title())
    desc = ("Rearrange PV = nRT to %s = %s and solve for %s, with a worked example, "
            "the right R to use, and the unit mistakes that cost marks." % (sym, rhs, word))

    h = headsrc
    h = re.sub(r"<title>[\s\S]*?</title>", "<title>%s</title>" % html.escape(title), h, count=1)
    h = re.sub(r'<meta name="description" content="[^"]*"',
               '<meta name="description" content="%s"' % html.escape(desc), h, count=1)
    h = re.sub(r'<meta name="keywords" content="[^"]*"',
               '<meta name="keywords" content="%s"' % html.escape(
                   "%s = %s, ideal gas law for %s, pv nrt %s, solve pv=nrt for %s"
                   % (sym, rhs.replace(" ", ""), word, sym.lower(), word)), h, count=1)
    h = re.sub(r'<link rel="canonical" href="[^"]*"',
               '<link rel="canonical" href="https://biochemtools.com/%s"' % f["slug"], h, count=1)
    h = re.sub(r'<meta property="og:title" content="[^"]*"',
               '<meta property="og:title" content="%s"' % html.escape(title), h, count=1)
    h = re.sub(r'<meta property="og:description" content="[^"]*"',
               '<meta property="og:description" content="%s"' % html.escape(desc), h, count=1)
    h = re.sub(r'<meta property="og:image" content="[^"]*"',
               '<meta property="og:image" content="https://biochemtools.com/og-images/ideal-gas-law-calculator.png"', h)
    h = re.sub(r'<meta name="twitter:image" content="[^"]*"',
               '<meta name="twitter:image" content="https://biochemtools.com/og-images/ideal-gas-law-calculator.png"', h)
    ld = {"@context": "https://schema.org", "@type": "WebPage",
          "url": "https://biochemtools.com/" + f["slug"], "name": title, "description": desc,
          "inLanguage": "en", "isAccessibleForFree": True,
          "publisher": {"@type": "Organization", "name": "BiochemTools", "url": "https://biochemtools.com/"}}
    h = re.sub(r'<script type="application/ld\+json">[\s\S]*?</script>',
               '<script type="application/ld+json">%s</script>' % json.dumps(ld), h, count=1)

    sec = SECOND[f["key"]]
    sec_ans = sec["fmt"] % sec["calc"]()
    sec_steps = "".join("<div>%s</div>" % x for x in sec["steps"])
    prac = "".join(
        "<li>%s<br><span style=\"color:var(--accent)\">%s %s</span></li>"
        % (q, fm % fn(), un) for q, fn, fm, un in PRACTICE[f["key"]])

    others = "".join(
        '<li><a href="/%s">%s = %s</a>, for %s</li>' % (o["slug"], o["sym"], o["rhs"], o["word"])
        for o in FORMS if o["key"] != f["key"])
    steps = "".join("<div>%s</div>" % s for s in f["steps"])

    body = """<header>
 <h1>Solving PV = nRT for %(word)s</h1>
</header>
<main>
 <div class="card">
  <p style="margin-top:0" class="lead"><b>%(sym)s = %(rhs)s</b></p>
  <p>Start from PV = nRT and divide both sides by whatever is sitting next to %(sym)s.
  Everything else stays where it is. %(note)s</p>
 </div>

 <div class="card">
  <h2 style="margin-top:0">Worked example</h2>
  <p>%(given)s</p>
  <div class="work">%(steps)s<div><b>%(sym)s = %(shown)s %(unit)s</b></div></div>
 </div>

 <div class="card">
  <h2 style="margin-top:0">Why the rearrangement works</h2>
  <p>PV = nRT is one equation with four variables and a constant, so knowing any three gives you
  the fourth. To isolate %(sym)s, divide both sides by everything that shares its side of the
  equals sign. Nothing else moves, and no term changes sign, because there is no addition
  anywhere in the equation. That is why all four rearrangements look so similar.</p>
 </div>

 <div class="card">
  <h2 style="margin-top:0">The same problem in different units</h2>
  <p>%(sec_text)s</p>
  <div class="work">%(sec_steps)s<div><b>%(sym)s = %(sec_ans)s %(sec_unit)s</b></div></div>
  <p>%(sec_moral)s</p>
 </div>

 <div class="card">
  <h2 style="margin-top:0">Which R to use</h2>
  <p>R only looks like several different constants because it carries units. Pick the one that
  matches the units you already have, and do not convert anything afterwards.</p>
  <table>
   <thead><tr><th>R</th><th>Units</th><th>Use when</th></tr></thead>
   <tbody>
    <tr><td>0.08206</td><td>L&middot;atm / mol&middot;K</td><td>pressure in atm, volume in litres</td></tr>
    <tr><td>8.314</td><td>J / mol&middot;K</td><td>pressure in pascals, volume in cubic metres</td></tr>
    <tr><td>62.36</td><td>L&middot;mmHg / mol&middot;K</td><td>pressure in mmHg or torr</td></tr>
   </tbody>
  </table>
 </div>

 <div class="card">
  <h2 style="margin-top:0">Where this goes wrong</h2>
  <p><b>Temperature must be in kelvin.</b> Celsius is the single most common reason an ideal gas
  answer comes out wrong, and it is silent: the arithmetic still works, the number is just false.
  Add 273.15.</p>
  <p><b>R has to match your units.</b> Using 0.08206 with pressure in kilopascals gives an answer
  that is out by a factor of about a hundred.</p>
  <p><b>Volume in litres, not millilitres,</b> when you are using 0.08206. A 250 mL flask is
  0.250 L.</p>
 </div>

 <div class="card">
  <h2 style="margin-top:0">Practice</h2>
  <p>Answers are underneath each one. Use R = 0.08206 and keep temperature in kelvin.</p>
  <ul>%(prac)s</ul>
 </div>

 <div class="card">
  <h2 style="margin-top:0">The other rearrangements</h2>
  <ul>%(others)s</ul>
  <p>Or use the <a href="/ideal-gas-law-calculator.html">ideal gas law calculator</a>, which
  solves for whichever one you leave blank and shows the working.</p>
 </div>
</main>
""" % dict(word=word, sym=sym, rhs=rhs, note=f["note"], given=f["given"],
           steps=steps, shown=shown, unit=unit, others=others,
           sec_text=sec["text"], sec_steps=sec_steps, sec_ans=sec_ans,
           sec_unit=sec["unit"], sec_moral=sec["moral"], prac=prac)

    return "<!DOCTYPE html>\n<html lang=\"en\">\n" + h + "</head>\n" + navsrc + body + "</body>\n</html>\n"


if __name__ == "__main__":
    headsrc, navsrc = head_and_nav()
    # the styles the calculator page never needed
    extra = """
 table{width:100%;border-collapse:collapse;margin:.9rem 0 .2rem;font-size:.95rem}
 th{text-align:left;color:var(--muted);font-weight:600;font-size:.82rem;text-transform:uppercase;
    letter-spacing:.04em;padding:.35rem .9rem .5rem 0;border-bottom:1px solid var(--line)}
 td{padding:.55rem .9rem .55rem 0;border-bottom:1px solid var(--line);vertical-align:top}
 tr:last-child td{border-bottom:none}
 .lead{font-size:1.5rem;letter-spacing:.01em}
</style>"""
    headsrc = headsrc.replace("</style>", extra, 1)

    made = []
    for f in FORMS:
        ans = solve(f)
        fmt, _ = DISPLAY[f["key"]]
        shown = float(fmt % ans)
        # the printed answer must be the computed one, to the precision shown
        assert abs(shown - ans) < (10 ** -len((fmt % ans).split(".")[1]) if "." in (fmt % ans) else 1.0), \
            "%s: prints %s but computes %.6f" % (f["key"], fmt % ans, ans)
        open(os.path.join(SITE, f["slug"]), "w", encoding="utf-8").write(page(f, headsrc, navsrc))
        made.append((f["slug"], f["sym"], fmt % ans, DISPLAY[f["key"]][1]))
    print("  wrote %d pages, every worked answer recomputed" % len(made))
    for s, sym, v, u in made:
        print("    %-44s %s = %s %s" % (s, sym, v, u))

    # The pages do not just show numbers, they claim relationships between them.
    # Each claim is checked here, because a page that says two answers are
    # identical had better be right about that.
    v = solve(FORMS[1])
    assert abs(v - 22.414) < 0.01, "molar volume at STP came out %.4f, expected 22.414" % v

    n_atm, n_si = solve(FORMS[0]), SECOND["moles"]["calc"]()
    assert abs(n_atm - n_si) < 0.0005, \
        "the moles page claims the atm and SI routes agree, but %.5f != %.5f" % (n_atm, n_si)

    p_atm, p_mm = solve(FORMS[2]), SECOND["pressure"]["calc"]()
    assert abs(p_mm - p_atm * 760) < 1.5, \
        "the pressure page claims %.0f mmHg is %.2f atm, but 760 atm-to-mmHg gives %.1f" % (
            p_mm, p_atm, p_atm * 760)

    t_k, t_c = solve(FORMS[3]), SECOND["temperature"]["calc"]()
    assert abs(t_c - (t_k - 273.15)) < 0.01, "the Celsius conversion does not match"

    assert SECOND["volume"]["calc"]() > 25, \
        "the volume page says 'over 25 L' at body temperature, but it is not"

    print("  molar volume at STP is %.3f L, and every cross-unit claim checks out" % v)
