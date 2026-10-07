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
import os, re, json, subprocess, tempfile, sys, datetime

TODAY = datetime.date.today().isoformat()
from decimal import Decimal, ROUND_HALF_UP

# The generators build a page from a cloned <head> plus their own body, so the
# analytics beacon that sits before </body> on the source page never came along.
# Fourteen generated pages were invisible to Cloudflare for a month because of it.
BEACON = ("<script type='module' src='https://static.cloudflareinsights.com/beacon.min.js' "
          "data-cf-beacon='{\"token\": \"101e4b9cdbae4363953f0ae30fae9a04\"}'></script>\n")


SITE = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..")
SRC = os.path.join(SITE, "amino-acid-titration-curve.html")

NAMES = {"Gly": ("Glycine", "G"), "Ala": ("Alanine", "A"), "Asp": ("Aspartic acid", "D"),
         "Glu": ("Glutamic acid", "E"), "His": ("Histidine", "H"), "Lys": ("Lysine", "K"),
         "Arg": ("Arginine", "R"), "Cys": ("Cysteine", "C"), "Tyr": ("Tyrosine", "Y"),
         "Met": ("Methionine", "M"), "Val": ("Valine", "V"), "Ile": ("Isoleucine", "I")}
# Published pI, Lehninger. Read out of amino-acid-chart.html rather than retyped,
# so the chart and these pages cannot drift apart, and checked below against the
# figures that were hand-entered when there were only nine of them.
WAS_TYPED = {"Gly": 5.97, "Ala": 6.01, "Asp": 2.77, "Glu": 3.22, "His": 7.59,
             "Lys": 9.74, "Arg": 10.76, "Cys": 5.07, "Tyr": 5.66}


# No ionizable side chain first, then acidic, basic, and the special side chains,
# which is the order the chart page teaches them in. Used for the sibling links on
# each page and for the block on the parent tool, so the two cannot disagree.
ORDER = ["Gly", "Ala", "Val", "Ile", "Met", "Asp", "Glu", "His", "Lys", "Arg", "Cys", "Tyr"]


def load_book_pi():
    """pI and pKa for every amino acid, straight from the chart page's own table."""
    h = open(os.path.join(SITE, "amino-acid-chart.html"), encoding="utf-8").read()
    m = re.search(r"const\s+AA\s*=\s*(\[[\s\S]*?\]);", h)
    if not m:
        raise RuntimeError("AA array not found in amino-acid-chart.html")
    with tempfile.NamedTemporaryFile("w", suffix=".js", delete=False) as f:
        f.write("const A=" + m.group(1) + ";console.log(JSON.stringify(A))")
        q = f.name
    try:
        r = subprocess.run(["node", q], capture_output=True, text=True)
        if r.returncode:
            raise RuntimeError(r.stderr[:300])
        rows = json.loads(r.stdout)
    finally:
        os.unlink(q)
    out = {row["c3"]: float(row["pI"]) for row in rows}
    for code, typed in WAS_TYPED.items():
        assert code in out, "%s is missing from the chart page" % code
        assert abs(out[code] - typed) < 0.005, \
            "%s: the chart says pI %.2f, this file was built on %.2f" % (code, out[code], typed)
    return out


BOOK_PI = None  # filled by load_book_pi() at build time
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
    "Met": ["alpha-carboxyl", "alpha-amino"],
    "Val": ["alpha-carboxyl", "alpha-amino"],
    "Ile": ["alpha-carboxyl", "alpha-amino"],
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


def charge_states(gs):
    """The dominant species between each pair of pKa values, with its net charge.

    At pH 0 every group is protonated: the basic groups each carry +1 and the
    acidic ones are neutral. Each pKa passed removes one proton and drops the
    net charge by one.
    """
    pks = sorted(g["pka"] for g in gs)
    start = sum(1 for g in gs if g["t"] == "b")
    out, edges = [], [None] + pks + [None]
    for i in range(len(pks) + 1):
        lo, hi = edges[i], edges[i + 1]
        if lo is None:
            rng = "below pH %.2f" % hi
        elif hi is None:
            rng = "above pH %.2f" % lo
        else:
            rng = "pH %.2f to %.2f" % (lo, hi)
        out.append((rng, start - i))
    return out


def net_charge(gs, pH):
    return sum((1 / (1 + 10 ** (pH - g["pka"]))) if g["t"] == "b"
               else -(1 / (1 + 10 ** (g["pka"] - pH))) for g in gs)


def page(code, gs, headsrc, navsrc, siblings):
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
    imgslug = "%s-titration-curve.png" % name.lower().replace(" ", "-")
    imgurl = "https://biochemtools.com/curves/" + imgslug
    # Written out rather than generic, because this is what Google Images reads and
    # it is what a screen reader hears in place of the plot.
    alt = ("Titration curve of %s: pH against equivalents of hydroxide, with buffering "
           "plateaus at pKa %s and the isoelectric point at pH %.2f"
           % (name.lower(), pk_and, pi_))

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
 /* The curve ships as a real PNG so Google Images can see it, with the canvas
    layered over the top to draw the same curve in. The canvas paints its own
    opaque background, otherwise the finished line underneath would show through
    and there would be nothing left to animate. */
 .curvewrap{position:relative;line-height:0}
 .curvewrap img{width:100%;height:auto;display:block;border-radius:6px}
 /* margin:0 matters: the site's canvas rule sets margin-top:8px, and margin still
    applies to an absolutely positioned box, so the canvas sat 8px below the image
    it is supposed to sit exactly on top of. */
 /* background:transparent matters as much as margin:0. The site's canvas rule sets
    an opaque background, so with JavaScript off the unpainted canvas sat on top of
    the image as a blank dark block and the curve was invisible. The script paints
    its own opaque fillRect before it draws, so nothing changes when JS runs. */
 .curvewrap canvas{position:absolute;left:0;top:0;width:100%;height:100%;
                   margin:0;background:transparent;border-radius:6px}
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
    # Every one of these pages used to share amino-acid-titration-curve.png, so a
    # shared link to the cysteine page previewed a different amino acid's curve.
    h = re.sub(r'<meta property="og:image" content="[^"]*"',
               '<meta property="og:image" content="%s"' % imgurl, h, count=1)
    h = re.sub(r'<meta property="og:image:width" content="[^"]*"',
               '<meta property="og:image:width" content="1400"', h, count=1)
    h = re.sub(r'<meta property="og:image:height" content="[^"]*"',
               '<meta property="og:image:height" content="640"', h, count=1)
    h = re.sub(r'<meta name="twitter:image" content="[^"]*"',
               '<meta name="twitter:image" content="%s"' % imgurl, h, count=1)
    img_ld = {"@type": "ImageObject", "contentUrl": imgurl, "url": imgurl,
              "width": 1400, "height": 640, "caption": alt,
              "license": "https://creativecommons.org/licenses/by/4.0/",
              "acquireLicensePage": "https://biochemtools.com/charts.html",
              "creditText": "BiochemTools",
              "creator": {"@type": "Organization", "name": "BiochemTools"}}
    ld = {"@context": "https://schema.org", "@type": "WebPage",
          "url": "https://biochemtools.com/" + slug, "name": title, "description": desc,
          "inLanguage": "en", "isAccessibleForFree": True,
          "license": "https://creativecommons.org/licenses/by/4.0/",
          "image": imgurl, "primaryImageOfPage": img_ld,
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
    sign = lambda q: ("%+d" % q) if q else "0"
    chg_rows = "".join("<tr><td>%s</td><td>%s</td></tr>" % (r, sign(q)) for r, q in charge_states(gs))
    q74 = net_charge(gs, 7.4)
    terms = []
    for g in sorted(gs, key=lambda g: g["pka"]):
        c = (1 / (1 + 10 ** (7.4 - g["pka"]))) if g["t"] == "b" else -(1 / (1 + 10 ** (g["pka"] - 7.4)))
        terms.append("%s (pKa %.2f) contributes %+.2f" % (
            "the base group" if g["t"] == "b" else "the acid group", g["pka"], c))
    terms_html = "".join("<li>%s</li>" % t for t in terms)
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
  <div class="curvewrap">
   <img src="/curves/%(imgslug)s" width="700" height="320" alt="%(alt)s"
    fetchpriority="high" decoding="async">
   <canvas id="plot" width="700" height="320" aria-hidden="true"></canvas>
  </div>
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
  <h2 style="margin-top:0">What charge it carries, and when</h2>
  <p>Reading the curve left to right, each pKa you pass strips off one proton and drops the
  net charge by one. Between two pKa values one species dominates:</p>
  <table><thead><tr><th>pH range</th><th>Net charge</th></tr></thead>
  <tbody>%(chg_rows)s</tbody></table>
  <p>The charge is zero at the isoelectric point, which is why %(lname)s will not move in an
  electric field at pH %(pi).2f. That is the basis of isoelectric focusing, and it is why the pI
  is the number worth remembering rather than the individual pKa values.</p>
 </div>

 <div class="card">
  <h2 style="margin-top:0">Net charge at physiological pH</h2>
  <p>At pH 7.4 no group is cleanly on or off. Each contributes a fraction, given by the
  Henderson-Hasselbalch relation, and the net charge is their sum:</p>
  <ul>%(terms_html)s</ul>
  <div class="work"><p>Net charge on %(lname)s at pH 7.4 = <b>%(q74)+.2f</b></p></div>
  <p>This is the calculation behind every peptide charge question. Do it for each residue in a
  sequence and add the results, and you have the charge on the whole peptide.</p>
 </div>

 <div class="card">
  <h2 style="margin-top:0">Working out the pI</h2>
  <div class="work"><p>%(work)s</p></div>
 </div>

 <div class="card">
  <h2 style="margin-top:0">The other amino acids</h2>
  <p>Each of these has its own curve, its own buffering regions and a worked isoelectric
  point. The three-group side chains behave quite differently from the two-group ones,
  so it is worth looking at one of each.</p>
  <p>%(siblings)s</p>
  <p style="margin-bottom:0">You can also <a href="/amino-acid-titration-curve.html">plot any
  amino acid's curve yourself</a>, see <a href="/amino-acid-chart.html">all 20 with their pKa
  values</a>, or run a whole sequence through the
  <a href="/peptide-charge-calculator.html">peptide charge and pI calculator</a>.</p>
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
(function(){
 const n=GS.length,c=document.getElementById("plot");if(!c)return;
 const ctx=c.getContext("2d"),W=c.width,H=c.height,P=40;
 ctx.fillStyle="#171310";ctx.fillRect(0,0,W,H);
 const X=e=>P+(e/n)*(W-P-14), Y=pH=>H-P-(pH/14)*(H-P-14);
 ctx.strokeStyle="#2c2620";ctx.lineWidth=1;ctx.beginPath();ctx.moveTo(P,10);ctx.lineTo(P,H-P);ctx.lineTo(W-14,H-P);ctx.stroke();
 ctx.fillStyle="#a2968a";ctx.font="12px sans-serif";
 for(let p=0;p<=14;p+=2){if(p<14)ctx.fillText(p,P-24,Y(p)+4);ctx.strokeStyle="#1a1512";ctx.beginPath();ctx.moveTo(P,Y(p));ctx.lineTo(W-14,Y(p));ctx.stroke();}
 ctx.fillStyle="#a2968a";ctx.fillText("pH",P-30,Y(14)+4);ctx.fillText("equivalents of OH\\u207B \\u2192",W-170,H-14);
 GS.forEach(g=>{ctx.strokeStyle="#e8b04b";ctx.setLineDash([5,4]);ctx.beginPath();ctx.moveTo(P,Y(g.pka));ctx.lineTo(W-14,Y(g.pka));ctx.stroke();ctx.fillStyle="#e8b04b";ctx.fillText("pKa "+g.pka.toFixed(2),W-96,Y(g.pka)-4);});
 const pi=pIv();ctx.strokeStyle="#6fb59f";ctx.beginPath();ctx.moveTo(P,Y(pi));ctx.lineTo(W-14,Y(pi));ctx.stroke();ctx.setLineDash([]);
 ctx.fillStyle="#6fb59f";ctx.fillText("pI "+pi.toFixed(2),P+6,Y(pi)-4);
 // The curve draws itself, the way the hero line on the homepage does. An SVG
 // path can be animated with stroke-dashoffset; a canvas cannot, so it is drawn
 // progressively instead: each frame extends the line a little further.
 const pts=[];
 for(let pH=0;pH<=14;pH+=0.02) pts.push([X(equiv(pH)),Y(pH)]);
 const still=(window.matchMedia&&window.matchMedia("(prefers-reduced-motion:reduce)").matches);
 function curve(upto){
  ctx.strokeStyle="#cf9366";ctx.lineWidth=2.5;ctx.beginPath();
  for(let i=0;i<upto;i++){ i?ctx.lineTo(pts[i][0],pts[i][1]):ctx.moveTo(pts[0][0],pts[0][1]); }
  ctx.stroke();
 }
 if(still||!window.requestAnimationFrame){curve(pts.length);return;}
 let t0=null;const DUR=1150;
 function frame(ts){
  if(t0===null)t0=ts;
  const k=Math.min(1,(ts-t0)/DUR);
  const eased=1-Math.pow(1-k,3);
  curve(Math.max(2,Math.round(eased*pts.length)));
  if(k<1)requestAnimationFrame(frame);
 }
 // only start once the chart is actually on screen
 if("IntersectionObserver" in window){
  const io=new IntersectionObserver(function(es){es.forEach(function(e){
   if(e.isIntersecting){io.disconnect();requestAnimationFrame(frame);}})},{threshold:.2});
  io.observe(c);
  setTimeout(function(){ if(t0===null){io.disconnect();curve(pts.length);} },3000);
 } else { requestAnimationFrame(frame); }
})();
</script>
""" % dict(name=name, lname=name.lower(), n=len(pks), pk_and=pk_and, pi=pi_,
           imgslug=imgslug, alt=esc(alt), siblings=siblings,
           neq=len(eq), eqs="" if len(eq) == 1 else "s",
           grp_rows=grp_rows, buf_rows=buf_rows, eq_rows=eq_rows, work=work,
           chg_rows=chg_rows, terms_html=terms_html, q74=q74,
           gsjson=json.dumps(gs))

    return slug, "<!DOCTYPE html>\n<html lang=\"en\">\n" + h + "</head>\n" + navsrc + body + BEACON + "</body>\n</html>\n"


def wire_up(made):
    """Internal links from the parent tool, plus sitemap entries.

    These are reference content, not tools, so they deliberately do not go into
    the homepage tool grid. Putting them there would inflate the tool count into
    something the site does not actually have.
    """
    order = ORDER
    missing = [c for c in dict(made) if c not in order]
    assert not missing, "built pages that the link block would silently drop: %s" % missing
    links = " &middot; ".join(
        '<a href="/%s">%s</a>' % (s, NAMES[c][0])
        for c, s in [(c, dict(made)[c]) for c in order if c in dict(made)])

    block = ('\n <div class="card" id="per-amino-acid">\n'
             '  <h2 style="margin-top:0">One amino acid at a time</h2>\n'
             '  <p>Each of these has its own page with that amino acid\'s pKa values, its curve, '
             'its buffering regions and a worked isoelectric point.</p>\n'
             '  <p>%s</p>\n </div>\n' % links)

    h = open(SRC, encoding="utf-8").read()
    # Remove every previous copy before adding this one. The old pattern required a
    # newline and a space in front of the div, but the insert below lstrips exactly
    # that, so it never matched its own output and each run appended another block.
    # Eleven had accumulated on the parent page before this was caught.
    h = re.sub(r'\s*<div class="card" id="per-amino-acid">[\s\S]*?</p>\s*</div>', "", h)
    assert 'id="per-amino-acid"' not in h, "a previous link block survived the cleanup"
    anchor = '<div class="card" id="sources">'
    if anchor not in h:
        raise RuntimeError("sources card not found, cannot place the link block")
    h = h.replace(anchor, block.lstrip("\n") + " " + anchor, 1)
    open(SRC, "w", encoding="utf-8").write(h)

    sm = os.path.join(SITE, "sitemap.xml")
    x = open(sm, encoding="utf-8").read()
    # Only strip the generated children. The earlier pattern also matched
    # amino-acid-titration-curve.html, the parent tool, and quietly deleted it
    # from the sitemap on every rebuild.
    ours = "|".join(re.escape(s_) for _, s_ in made)
    x = re.sub(r'\s*<url><loc>https://biochemtools\.com/(?:%s)</loc>[^<]*<lastmod>[^<]*</lastmod>'
               r'<priority>[^<]*</priority></url>' % ours, "", x)
    # Each entry carries its curve as an <image:image>, because getting into the
    # image pack on "<amino acid> titration curve" is the point of rendering a PNG
    # at all. The image namespace is already declared on <urlset>.
    rows = "".join(
        '\n  <url><loc>https://biochemtools.com/%s</loc><lastmod>%s</lastmod>'
        '<priority>0.6</priority>'
        '<image:image><image:loc>https://biochemtools.com/curves/%s</image:loc>'
        '<image:title>%s</image:title></image:image></url>'
        % (s, TODAY, s.replace(".html", ".png"),
           esc("%s titration curve" % NAMES[c][0]))
        for c, s in made)
    tail = "</urlset>"
    x = x.replace(tail, rows + "\n" + tail, 1)
    open(sm, "w", encoding="utf-8").write(x)
    return len(made)


if __name__ == "__main__":
    BOOK_PI = load_book_pi()
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
        sibs = " &middot; ".join(
            '<a href="/%s-titration-curve.html">%s</a>'
            % (NAMES[c][0].lower().replace(" ", "-"), NAMES[c][0])
            for c in ORDER if c in aa and c != code)
        slug, html = page(code, gs, headsrc, navsrc, sibs)
        open(os.path.join(SITE, slug), "w", encoding="utf-8").write(html)
        made.append((code, slug, shown))
    print("  wrote %d pages, every pI checked against the published value" % len(made))
    for c, s_, p_ in made:
        print("    %-38s pI %.2f" % (s_, p_))
    n = wire_up([(c, s_) for c, s_, _ in made])
    print("  linked %d from the parent tool and added them to the sitemap" % n)
