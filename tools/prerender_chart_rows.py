#!/usr/bin/env python3
"""Put the amino acid chart's 20 rows into the HTML, instead of only into JavaScript.

The table body was `<tbody id="rows"></tbody>` and every row was written by
`$("rows").innerHTML = ...` at runtime. So the site's strongest page, 5,526
impressions over three months, shipped no table content in its HTML at all, and
the per-amino-acid links added to that template would only exist after Google
chose to render the page's JavaScript.

That is the same crawl problem the titration pages already have: eight of them
rank #1 on DuckDuckGo and have zero Google impressions, on one inbound link each.
Links a crawler has to execute JavaScript to find are not the fix for it.

So the default view is rendered here at build time, by running the page's own
template in node rather than reimplementing it, and written into the tbody. The
script then takes over on load exactly as before and replaces it on the first
filter, sort or search.
"""
import os, re, json, subprocess, tempfile, sys, glob

SITE = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..")
PAGE = os.path.join(SITE, "amino-acid-chart.html")


def has_curve():
    """Three-letter code -> page, for the titration pages that exist on disk."""
    out = {}
    for f in glob.glob(os.path.join(SITE, "*-titration-curve.html")):
        b = os.path.basename(f)
        name = b[: -len("-titration-curve.html")].replace("-", " ")
        out[name] = b
    # chart page spelling -> file spelling
    byname = {"Alanine": "alanine", "Arginine": "arginine", "Aspartate": "aspartic acid",
              "Cysteine": "cysteine", "Glutamate": "glutamic acid", "Glycine": "glycine",
              "Histidine": "histidine", "Isoleucine": "isoleucine", "Lysine": "lysine",
              "Methionine": "methionine", "Tyrosine": "tyrosine", "Valine": "valine"}
    return out, byname


def grab(h, pat, what):
    m = re.search(pat, h)
    if not m:
        raise RuntimeError("could not find %s in amino-acid-chart.html" % what)
    return m


def build_rows(h):
    aa = grab(h, r"const\s+AA\s*=\s*(\[[\s\S]*?\]);", "the AA array").group(1)
    tpl = grab(h, r'\$\("rows"\)\.innerHTML=(list\.map\([\s\S]*?\)\.join\(""\));',
               "the row template").group(1)
    files, byname = has_curve()
    hc = {}
    for row in json.loads(subprocess.run(
            ["node", "-e", "console.log(JSON.stringify(%s))" % aa],
            capture_output=True, text=True, check=True).stdout):
        slug = byname.get(row["name"])
        if slug and slug in files:
            hc[row["c3"]] = files[slug]

    js = """
const AA=%s;
const HAS_CURVE=%s;
let filter="all", sortKey="c1", sortDir=1, query="";
function matches(a){ return true; }
const list=AA.filter(matches).sort((x,y)=>{
 let a=x[sortKey],b=y[sortKey];
 if(a===null)a=Infinity; if(b===null)b=Infinity;
 if(typeof a==="string") return sortDir*a.localeCompare(b);
 return sortDir*(a-b);
});
console.log(%s);
""" % (aa, json.dumps(hc), tpl)
    with tempfile.NamedTemporaryFile("w", suffix=".js", delete=False) as f:
        f.write(js)
        q = f.name
    try:
        r = subprocess.run(["node", q], capture_output=True, text=True)
        if r.returncode:
            raise RuntimeError(r.stderr[:400])
        return r.stdout.strip(), hc
    finally:
        os.unlink(q)


if __name__ == "__main__":
    h = open(PAGE, encoding="utf-8").read()

    # the page's own HAS_CURVE must match what is on disk, or the static rows and
    # the runtime rows would link different things
    rows, hc = build_rows(h)
    decl = "const HAS_CURVE=%s;" % json.dumps(hc, sort_keys=True)
    if re.search(r"const HAS_CURVE=\{[^;]*\};", h):
        h = re.sub(r"const HAS_CURVE=\{[^;]*\};", decl, h, count=1)
    else:
        anchor = "const $=id=>document.getElementById(id);"
        if anchor not in h:
            anchor = grab(h, r"let filter=\"all\"[^;]*;", "the state line").group(0)
        h = h.replace(anchor, decl + "\n" + anchor, 1)

    n = rows.count("<tr>")
    links = rows.count("-titration-curve.html")
    if n != 20:
        print("  FAIL rendered %d rows, the chart has 20" % n)
        sys.exit(1)
    if links != len(hc):
        print("  FAIL rendered %d links, expected %d" % (links, len(hc)))
        sys.exit(1)

    # Check the anchor exists, not that the file changed. Re-running on an
    # unchanged chart produces byte-identical rows, which is correct, and an
    # equality test called that a failure.
    if not re.search(r'<tbody id="rows">[\s\S]*?</tbody>', h):
        print("  FAIL tbody#rows not found")
        sys.exit(1)
    h2 = re.sub(r'<tbody id="rows">[\s\S]*?</tbody>',
                lambda m: '<tbody id="rows">' + rows + "</tbody>", h, count=1)
    open(PAGE, "w", encoding="utf-8").write(h2)
    print("  pre-rendered %d rows into the HTML, %d of them linking a titration page" % (n, links))
    for c3 in sorted(hc):
        print("    %-5s -> %s" % (c3, hc[c3]))
