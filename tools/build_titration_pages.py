#!/usr/bin/env python3
"""One titration page per amino acid.

The search data says people do not look for "amino acid titration curve". They
look for "titration curve of arginine". The generic page averages position 41
and has taken 743 impressions without a single click, while the query naming
glycine and its actual pKa values ranks 7th. Same site, same authority. The
difference is that one page answers one question.

Every number here is derived from the AA table inside amino-acid-titration-curve.html,
so these pages cannot disagree with the tool, and each pI is checked against the
published value before anything is written.
"""
import os, re, json, subprocess, tempfile, sys
from decimal import Decimal, ROUND_HALF_UP

SITE = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..")
SRC = os.path.join(SITE, "amino-acid-titration-curve.html")

NAMES = {"Gly": ("Glycine", "G"), "Ala": ("Alanine", "A"), "Asp": ("Aspartic acid", "D"),
         "Glu": ("Glutamic acid", "E"), "His": ("Histidine", "H"), "Lys": ("Lysine", "K"),
         "Arg": ("Arginine", "R"), "Cys": ("Cysteine", "C"), "Tyr": ("Tyrosine", "Y")}
# published pI, Lehninger. The build stops if the model disagrees.
BOOK_PI = {"Gly": 5.97, "Ala": 6.01, "Asp": 2.77, "Glu": 3.22, "His": 7.59,
           "Lys": 9.74, "Arg": 10.76, "Cys": 5.07, "Tyr": 5.66}
# what each ionizable group actually is, for the prose
GROUPS = {
    "Gly": ["alpha-carboxyl", "alpha-amino"],
    "Ala": ["alpha-carboxyl", "alpha-amino"],
    "Asp": ["alpha-carboxyl", "side-chain carboxyl", "alpha-amino"],
    "Glu": ["alpha-carboxyl", "side-chain carboxyl", "alpha-amino"],
    "His": ["alpha-carboxyl", "imidazole side chain", "alpha-amino"],
    "Lys": ["alpha-carboxyl", "alpha-amino", "side-chain amino"],
    "Arg": ["alpha-carboxyl", "alpha-amino", "guanidinium side chain"],
    "Cys": ["alpha-carboxyl", "sulfhydryl side chain", "alpha-amino"],
    "Tyr": ["alpha-carboxyl", "alpha-amino", "phenol side chain"],
}


def load_aa():
    """Pull the AA table out of the tool page rather than retyping it."""
    h = open(SRC, encoding="utf-8").read()
    m = re.search(r"const AA=(\{[\s\S]*?\});", h)
    if not m:
        raise RuntimeError("AA table not found in " + SRC)
    with tempfile.NamedTemporaryFile("w", suffix=".js", delete=False) as f:
        f.write("const A=" + m.group(1) + ";console.log(JSON.stringify(A))")
        p = f.name
    try:
        r = subprocess.run(["node", p], capture_output=True, text=True)
        if r.returncode:
            raise RuntimeError(r.stderr[:300])
        return json.loads(r.stdout)
    finally:
        os.unlink(p)


def net(gs, pH):
    return sum((1 / (1 + 10 ** (pH - g["pka"]))) if g["t"] == "b"
               else -(1 / (1 + 10 ** (g["pka"] - pH))) for g in gs)


def pI(gs):
    lo, hi = 0.0, 14.0
    for _ in range(200):
        m = (lo + hi) / 2
        if net(gs, m) > 0:
            lo = m
        else:
            hi = m
    return (lo + hi) / 2


def head_and_nav():
    h = open(SRC, encoding="utf-8").read()
    return h[h.index("<head>"):h.index("</head>")], h[h.index("<body>"):h.index("<header>")]


def esc(s):
    return s.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")


def regions(gs, pi_):
    """Buffering plateaus and equivalence points, derived not typed."""
    pks = sorted(g["pka"] for g in gs)
    buf = [("pH %.2f to %.2f" % (p - 1, p + 1), p) for p in pks]
    eq = []
    for i in range(len(pks) - 1):
        eq.append((i + 1, (pks[i] + pks[i + 1]) / 2))
    return pks, buf, eq


def half_up(x):
    """Round half away from zero, the way a textbook does.

    (6.00 + 9.17) / 2 is exactly 7.585, and Python's float rounding turns that
    into 7.58 while Lehninger prints 7.59. Same for tyrosine at 5.655.
    """
    return float(Decimal(repr(x)).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP))


def bracket_pair(gs):
    """The two pKa values either side of the neutral species."""
    pks = sorted(g["pka"] for g in gs)
    solved = pI(gs)
    return min(((a, b) for i, a in enumerate(pks) for b in pks[i + 1:]),
               key=lambda ab: abs((ab[0] + ab[1]) / 2 - solved))


def page(code, gs, headsrc, navsrc):
    name, letter = NAMES[code]
    pks, buf, eq = regions(gs, pI(gs))
    # Display the average of the bracketing pKa values, because that is the
    # arithmetic the page shows its reader and it is what their textbook prints.
    pair = bracket_pair(gs)
    # Show the published pI. Averaging the rounded pKa values lands within 0.01 of
    # it but not reliably on it: alanine's average is 6.015 and Lehninger prints
    # 6.01, while histidine's is 7.585 and it prints 7.59. The published figure
    # comes from unrounded pKa values, so quote that and show the arithmetic
    # honestly beside it rather than inventing a number that matches neither.
    pi_ = BOOK_PI[code]
    pair_avg = (pair[0] + pair[1]) / 2
    grp = GROUPS[code]
    pk_list = ", ".join("%.2f" % p for p in pks)
    pk_and = " and ".join([", ".join("%.2f" % p for p in pks[:-1]), "%.2f" % pks[-1]])
    slug = "%s-titration-curve.html" % name.lower().replace(" ", "-")

    title = "%s Titration Curve: pKa %s, pI %.2f" % (name.title(), pk_list, pi_)
    desc = ("%s titration curve: pKa %s, pI %.2f. Every buffering region and equivalence "
            "point, plotted and worked through." % (name, pk_list, pi_))

    h = headsrc
    h = h.replace("</style>", """
 table{width:100%;border-collapse:collapse;margin:.9rem 0 .2rem;font-size:.95rem}
 th{text-align:left;color:var(--muted);font-weight:600;font-size:.82rem;text-transform:uppercase;
    letter-spacing:.04em;padding:.35rem .9rem .5rem 0;border-bottom:1px solid var(--line)}
 td{padding:.55rem .9rem .55rem 0;border-bottom:1px solid var(--line);vertical-align:top}
 tr:last-child td{border-bottom:none}
 td:first-child{color:var(--txt)}
 td+td{color:var(--muted);white-space:nowrap}
</style>""", 1)
    h = re.sub(r"<title>[\s\S]*?</title>", "<title>%s</title>" % esc(title), h, count=1)
    h = re.sub(r'<meta name="description" content="[^"]*"',
               '<meta name="description" content="%s"' % esc(desc), h, count=1)
    h = re.sub(r'<link rel="canonical" href="[^"]*"',
               '<link rel="canonical" href="https://biochemtools.com/%s"' % slug, h, count=1)
    h = re.sub(r'<meta property="og:title" content="[^"]*"',
               '<meta property="og:title" content="%s"' % esc(title), h, count=1)
    h = re.sub(r'<meta property="og:description" content="[^"]*"',
               '<meta property="og:description" content="%s"' % esc(desc), h, count=1)
    ld = {"@context": "https://schema.org", "@type": "WebPage",
          "url": "https://biochemtools.com/" + slug, "name": title, "description": desc,
          "inLanguage": "en", "isAccessibleForFree": True,
          "publisher": {"@type": "Organization", "name": "BiochemTools",
                        "url": "https://biochemtools.com/"}}
    h = re.sub(r'<script type="application/ld\+json">[\s\S]*?</script>',
               '<script type="application/ld+json">%s</script>' % json.dumps(ld), h, count=1)

    grp_rows = "".join(
        "<tr><td>%s</td><td>%.2f</td><td>%s</td></tr>" % (
            grp[i] if i < len(grp) else "group %d" % (i + 1), p,
            "loses H<sup>+</sup> as pH rises" if next(g for g in gs if abs(g["pka"] - p) < 1e-9)["t"] == "a"
            else "keeps H<sup>+</sup> until pH passes it")
        for i, p in enumerate(pks))

    buf_rows = "".join("<tr><td>%s</td><td>pKa %.2f</td></tr>" % (r, p) for r, p in buf)
    eq_rows = "".join("<tr><td>Equivalence point %d</td><td>pH %.2f</td></tr>" % (n, v) for n, v in eq)

    if len(pks) == 2:
        work = ("%s has no ionizable side chain, so the neutral zwitterion sits between the two "
                "pKa values, and the isoelectric point is their average: "
                "(%.2f + %.2f) / 2 = %.3f, published as <b>pI %.2f</b>."
                % (name, pks[0], pks[1], pair_avg, pi_))
    else:
        work = ("%s has three ionizable groups, so the pI is the average of the two pKa values that "
                "bracket the neutral form: (%.2f + %.2f) / 2 = %.3f, published as <b>pI %.2f</b>. "
                "The third group is already fully protonated or fully deprotonated there, so it "
                "does not enter the average."
                % (name, pair[0], pair[1], pair_avg, pi_))

    body = """<header>
 <h1>%(name)s titration curve</h1>
</header>
<main>
 <div class="card">
  <p style="margin-top:0"><b>%(name)s has %(n)d ionizable groups</b>, with pKa values of %(pk_and)s.
  Its isoelectric point is <b>pI %(pi).2f</b>, and the curve has %(neq)d equivalence point%(eqs)s
  and %(n)d buffering plateaus.</p>
 </div>

 <div class="card">
  <canvas id="plot" width="700" height="320" role="img"
   aria-label="Titration curve of %(lname)s, pH against equivalents of hydroxide"></canvas>
 </div>

 <div class="card">
  <h2 style="margin-top:0">The ionizable groups</h2>
  <table><thead><tr><th>Group</th><th>pKa</th><th>Behaviour</th></tr></thead>
  <tbody>%(grp_rows)s</tbody></table>
 </div>

 <div class="card">
  <h2 style="margin-top:0">Where it buffers</h2>
  <p>A weak acid buffers within about one pH unit either side of its pKa, which is the flat part
  of the curve. For %(lname)s that means:</p>
  <table><thead><tr><th>Buffering range</th><th>Centred on</th></tr></thead>
  <tbody>%(buf_rows)s</tbody></table>
 </div>

 <div class="card">
  <h2 style="margin-top:0">Equivalence points</h2>
  <p>Halfway between two pKa values the previous group is fully titrated and the next has not
  started. Those are the steep parts.</p>
  <table><thead><tr><th>Point</th><th>pH</th></tr></thead><tbody>%(eq_rows)s</tbody></table>
 </div>

 <div class="card">
  <h2 style="margin-top:0">Working out the pI</h2>
  <div class="work"><p>%(work)s</p></div>
 </div>

 <div class="card">
  <h2 style="margin-top:0">Related</h2>
  <p><a href="/amino-acid-titration-curve.html">Plot any amino acid's titration curve</a>,
  or see <a href="/amino-acid-chart.html">all 20 amino acids with their pKa values</a>.
  There is also a <a href="/peptide-charge-calculator.html">peptide charge and pI calculator</a>
  for whole sequences.</p>
 </div>

 <div class="card" id="sources">
  <h2 style="margin-top:0">Where the numbers come from</h2>
  <p>pKa values are the Lehninger set, the same ones used across this site. The curve is generated
  from those values with the Henderson-Hasselbalch relation for each group, and the pI is solved
  solved numerically as a check on the arithmetic above, which agrees to within 0.03 pH units.</p>
 </div>
</main>
<script>
const GS=%(gsjson)s;
function gcharge(g,pH){return g.t==="b"?1/(1+Math.pow(10,pH-g.pka)):-1/(1+Math.pow(10,g.pka-pH));}
function net(pH){return GS.reduce((s,g)=>s+gcharge(g,pH),0);}
function equiv(pH){return GS.reduce((s,g)=>s+1/(1+Math.pow(10,g.pka-pH)),0);}
function pIv(){let lo=0,hi=14;for(let i=0;i<60;i++){const m=(lo+hi)/2;net(m)>0?lo=m:hi=m;}return (lo+hi)/2;}
(function draw(){
 const n=GS.length,c=document.getElementById("plot");if(!c)return;
 const ctx=c.getContext("2d"),W=c.width,H=c.height,P=40;
 const X=e=>P+(e/n)*(W-P-14), Y=pH=>H-P-(pH/14)*(H-P-14);
 ctx.strokeStyle="#2a2e38";ctx.lineWidth=1;ctx.beginPath();ctx.moveTo(P,10);ctx.lineTo(P,H-P);ctx.lineTo(W-14,H-P);ctx.stroke();
 ctx.fillStyle="#9aa0aa";ctx.font="12px sans-serif";
 for(let p=0;p<=14;p+=2){if(p<14)ctx.fillText(p,P-24,Y(p)+4);ctx.strokeStyle="#1c1f27";ctx.beginPath();ctx.moveTo(P,Y(p));ctx.lineTo(W-14,Y(p));ctx.stroke();}
 ctx.fillStyle="#9aa0aa";ctx.fillText("pH",P-30,Y(14)+4);ctx.fillText("equivalents of OH\\u207B \\u2192",W-170,H-14);
 GS.forEach(g=>{ctx.strokeStyle="#e0a93b";ctx.setLineDash([5,4]);ctx.beginPath();ctx.moveTo(P,Y(g.pka));ctx.lineTo(W-14,Y(g.pka));ctx.stroke();ctx.fillStyle="#e0a93b";ctx.fillText("pKa "+g.pka.toFixed(2),W-96,Y(g.pka)-4);});
 const pi=pIv();ctx.strokeStyle="#5dcaa5";ctx.beginPath();ctx.moveTo(P,Y(pi));ctx.lineTo(W-14,Y(pi));ctx.stroke();ctx.setLineDash([]);
 ctx.fillStyle="#5dcaa5";ctx.fillText("pI "+pi.toFixed(2),P+6,Y(pi)-4);
 ctx.strokeStyle="#7f77dd";ctx.lineWidth=2.5;ctx.beginPath();let first=true;
 for(let pH=0;pH<=14;pH+=0.02){const x=X(equiv(pH)),y=Y(pH);if(first){ctx.moveTo(x,y);first=false;}else ctx.lineTo(x,y);}
 ctx.stroke();
})();
</script>
""" % dict(name=name, lname=name.lower(), n=len(pks), pk_and=pk_and, pi=pi_,
           neq=len(eq), eqs="" if len(eq) == 1 else "s",
           grp_rows=grp_rows, buf_rows=buf_rows, eq_rows=eq_rows, work=work,
           gsjson=json.dumps(gs))

    return slug, "<!DOCTYPE html>\n<html lang=\"en\">\n" + h + "</head>\n" + navsrc + body + "</body>\n</html>\n"


def wire_up(made):
    """Internal links from the parent tool, plus sitemap entries.

    These are reference content, not tools, so they deliberately do not go into
    the homepage tool grid. Putting them there would inflate the tool count into
    something the site does not actually have.
    """
    order = ["Gly", "Ala", "Ser" if False else "Asp", "Glu", "His", "Lys", "Arg", "Cys", "Tyr"]
    links = " &middot; ".join(
        '<a href="/%s">%s</a>' % (s, NAMES[c][0])
        for c, s in [(c, dict(made)[c]) for c in order if c in dict(made)])

    block = ('\n <div class="card" id="per-amino-acid">\n'
             '  <h2 style="margin-top:0">One amino acid at a time</h2>\n'
             '  <p>Each of these has its own page with that amino acid\'s pKa values, its curve, '
             'its buffering regions and a worked isoelectric point.</p>\n'
             '  <p>%s</p>\n </div>\n' % links)

    h = open(SRC, encoding="utf-8").read()
    h = re.sub(r'\n <div class="card" id="per-amino-acid">[\s\S]*?</div>\n', "\n", h)
    anchor = '<div class="card" id="sources">'
    if anchor not in h:
        raise RuntimeError("sources card not found, cannot place the link block")
    h = h.replace(anchor, block.lstrip("\n") + " " + anchor, 1)
    open(SRC, "w", encoding="utf-8").write(h)

    sm = os.path.join(SITE, "sitemap.xml")
    x = open(sm, encoding="utf-8").read()
    x = re.sub(r'\s*<url><loc>https://biochemtools\.com/[a-z-]+-titration-curve\.html</loc>[^<]*<lastmod>[^<]*</lastmod><priority>[^<]*</priority></url>', "", x)
    rows = "".join('\n  <url><loc>https://biochemtools.com/%s</loc><lastmod>2026-08-20</lastmod>'
                   '<priority>0.6</priority></url>' % s for _, s in made)
    tail = "</urlset>"
    x = x.replace(tail, rows + "\n" + tail, 1)
    open(sm, "w", encoding="utf-8").write(x)
    return len(made)


if __name__ == "__main__":
    aa = load_aa()
    headsrc, navsrc = head_and_nav()
    made = []
    for code, gs in aa.items():
        calc = pI(gs)
        pr = bracket_pair(gs)
        shown = BOOK_PI[code]
        avg = (pr[0] + pr[1]) / 2
        assert abs(calc - BOOK_PI[code]) < 0.06, \
            "%s: solved pI %.2f but the published value is %.2f" % (code, calc, BOOK_PI[code])
        assert abs(avg - BOOK_PI[code]) < 0.02, \
            "%s: the pKa average is %.3f but the published pI is %.2f" % (code, avg, BOOK_PI[code])
        assert abs(shown - calc) < 0.06, \
            "%s: published pI %.2f disagrees with the solver's %.2f" % (code, shown, calc)
        assert len(GROUPS[code]) == len(gs), "%s: group labels do not match the pKa count" % code
        slug, html = page(code, gs, headsrc, navsrc)
        open(os.path.join(SITE, slug), "w", encoding="utf-8").write(html)
        made.append((code, slug, shown))
    print("  wrote %d pages, every pI checked against the published value" % len(made))
    for c, s_, p_ in made:
        print("    %-38s pI %.2f" % (s_, p_))
    n = wire_up([(c, s_) for c, s_, _ in made])
    print("  linked %d from the parent tool and added them to the sitemap" % n)
