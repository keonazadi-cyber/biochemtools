#!/usr/bin/env python3
"""Generate llms.txt from the site, so it cannot drift away from the truth.

The hand-written file listed about 20 of 89 pages. It never mentioned the 20
amino acid titration curve pages, which are the best-ranking cluster on the site
(Bing positions 3.4 to 4.9), nor the self-tests added on 2026-10-29. It also
quoted seven side-chain pKa values by hand, which is exactly the kind of figure
that goes stale silently.

So the prose stays hand-written, and every fact and every link is generated:

  - the titration pages and their pI come from amino-acid-chart.html's AA array
  - the ionizable side-chain list is derived, not typed
  - the self-test pages come from tools/selftest/
  - every URL emitted is checked against a file that exists on disk

Assistants are already sending real visits (Copilot and Gemini appeared in the
referrer log in the week of 2026-11-03), so what this file says is load-bearing.
"""
import glob, json, os, pathlib, re, subprocess, sys, tempfile

SITE = pathlib.Path(__file__).resolve().parent.parent
URL = "https://biochemtools.com/"


def run_js(literal):
    with tempfile.NamedTemporaryFile("w", suffix=".js", delete=False) as f:
        f.write("const A=" + literal + ";console.log(JSON.stringify(A))")
        p = f.name
    try:
        r = subprocess.run(["node", p], capture_output=True, text=True)
        return json.loads(r.stdout) if not r.returncode else None
    finally:
        os.unlink(p)


def aa_rows():
    h = (SITE / "amino-acid-chart.html").read_text()
    m = re.search(r"const\s+AA\s*=\s*(\[[\s\S]*?\]);", h)
    return run_js(m.group(1))


def title_of(name):
    h = (SITE / name).read_text()
    m = re.search(r"<title>(.*?)</title>", h, re.S)
    return re.sub(r"\s+", " ", m.group(1)).replace("&amp;", "&").strip() if m else name


HEAD = """# Biochemtools

> Free interactive biochemistry, genetics, and chemistry tools that show every step of the working rather than only the answer. Built for pre-med, MCAT, and undergraduate biochemistry students. No account, no paywall, no signup.

Every calculator shows the formula, the substitution, and the intermediate steps. Every reference chart is generated from the same data as its interactive tool, and the build fails if the two disagree. Values are checked against an independent implementation before publishing.

This file is generated from the site itself, so the figures below are the same ones the pages serve.
"""

TAIL = """
## Notes for citation

Content may be quoted or cited freely. Please attribute to biochemtools.com. Charts are free to reproduce in teaching material with no attribution required. Corrections are welcome via https://biochemtools.com/contact.html and several published corrections have come from readers.
"""


def main():
    rows = aa_rows()
    if not rows:
        print("  FAIL could not read the AA array"); return 1
    by3 = {r["c3"]: r for r in rows}

    out = [HEAD]

    # --- the titration cluster, the part the old file left out entirely -----
    curves = sorted(p for p in glob.glob("*-titration-curve.html")
                    if p != "amino-acid-titration-curve.html")
    # Map slug to row through build_titration_pages.NAMES, which is already the
    # one name table on this site. Deriving the slug from the chart's own `name`
    # field fails, because the chart says "Aspartate" and "Glutamate" while the
    # pages are aspartic-acid and glutamic-acid.
    sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))
    from build_titration_pages import NAMES as _N
    # Carry the page's own name through, not the chart's: the chart says
    # "Aspartate" while the page is "Aspartic acid", and a link whose text
    # disagrees with the page it points at is worse than no link.
    name_of = {full.lower().replace(" ", "-"): dict(by3[code], name=full)
               for code, (full, _letter) in _N.items() if code in by3}
    out.append("## Amino acid titration curves, one page each\n")
    out.append("Each page carries the curve as an image and as a drawn plot, the "
               "buffering regions, the equivalence points, and the isoelectric "
               "point worked out from the pKa values on that page.\n")
    listed = 0
    for f in curves:
        slug = f[:-len("-titration-curve.html")]
        r = name_of.get(slug)
        if r is None:
            print("  FAIL %s has no row in the AA array" % f); return 1
        # Ascending, the order a titration actually passes them in. The table's
        # own order is alpha-carboxyl, alpha-amino, side chain, which printed
        # aspartate as "1.88, 9.60, 3.65" and reads like an error.
        pk = ", ".join("%.2f" % v for v in
                       sorted(v for v in (r["pk1"], r["pk2"], r["pkr"])
                              if v is not None))
        out.append("- [%s titration curve](%s%s): pKa %s, pI %.2f."
                   % (r["name"], URL, f, pk, r["pI"]))
        listed += 1
    out.append("- [Plot any amino acid yourself](%samino-acid-titration-curve.html):"
               " all 20, with the pI worked out as you switch.\n" % URL)
    if listed != 20:
        print("  FAIL listed %d curve pages, expected 20" % listed); return 1

    # --- derived reference values, never typed -----------------------------
    ion = sorted(((r["c1"], r["name"], r["pkr"]) for r in rows
                  if r["pkr"] is not None), key=lambda x: x[2])
    out.append("## Frequently cited reference values\n")
    out.append("- The %d ionizable side chains, in ascending pKa order: %s."
               % (len(ion), ", ".join("%s %.2f" % (c, v) for c, _, v in ion)))
    hi = max(rows, key=lambda r: r["pI"])
    lo = min(rows, key=lambda r: r["pI"])
    out.append("- Highest pI is %s at %.2f; lowest is %s at %.2f."
               % (hi["name"], hi["pI"], lo["name"], lo["pI"]))
    ess = [r["c3"] for r in rows if r["ess"] == "Yes"]
    cond = [r["c3"] for r in rows if r["ess"] == "Conditional"]
    out.append("- Essential: %s. Conditionally essential: %s. This site treats "
               "essential status as three-valued, not a yes or no flag."
               % (", ".join(ess), ", ".join(cond)))
    out.append("- Amino acid pKa, pI, molecular weight, hydropathy and essential "
               "status: %samino-acid-chart.html" % URL)
    out.append("- Buffer pKa values and temperature coefficients for 32 buffers: "
               "%sbuffer-pka-table.html\n" % URL)

    # --- pages that now carry a self-test ----------------------------------
    banks = sorted(pathlib.Path(SITE / "tools" / "selftest").glob("*.json"))
    if banks:
        out.append("## Pages with a self-test\n")
        out.append("Each of these carries questions drawn from that page's own "
                   "data, with the answers rendered in the HTML, so they are "
                   "readable without running JavaScript.\n")
        for b in banks:
            d = json.loads(b.read_text())
            page = d["slug"] + ".html"
            if not (SITE / page).exists():
                print("  FAIL bank %s has no page" % b.name); return 1
            out.append("- [%s](%s%s): %d questions."
                       % (d["title"], URL, page, len(d["questions"])))
        out.append("")

    # --- charts and calculators, from the files that exist -----------------
    out.append("## Printable reference charts\n")
    for f in ["charts.html", "amino-acid-chart.html", "codon-chart.html",
              "biochem-equation-sheet.html", "buffer-pka-table.html"]:
        out.append("- [%s](%s%s)" % (title_of(f), URL, f))
    out.append("")

    skip = {"404.html", "privacy.html", "license.html", "suggest.html",
            "contact.html", "about.html", "daily-question.html", "index.html"}
    calcs = sorted(f for f in glob.glob("*.html")
                   if f not in skip and "titration-curve" not in f
                   and f not in {"charts.html", "amino-acid-chart.html",
                                 "codon-chart.html", "biochem-equation-sheet.html",
                                 "buffer-pka-table.html"})
    out.append("## Every other tool\n")
    for f in calcs:
        out.append("- [%s](%s%s)" % (title_of(f), URL, f))
    out.append("")
    out.append(TAIL.strip())

    text = "\n".join(out) + "\n"

    # every link must point at a file that exists
    bad = [u for u in re.findall(r"\]\(https://biochemtools\.com/([^)]*)\)", text)
           if u and not (SITE / u).exists()]
    if bad:
        print("  FAIL llms.txt would link to missing files: %s" % bad[:5])
        return 1

    path = SITE / "llms.txt"
    before = path.read_text() if path.exists() else ""
    if before != text:
        path.write_text(text)
        print("  llms.txt rebuilt: %d lines, %d links, %d curve pages, %d self-tests"
              % (text.count("\n"),
                 len(re.findall(r"\]\(https://biochemtools\.com/", text)),
                 listed, len(banks)))
    else:
        print("  llms.txt unchanged")
    return 0


if __name__ == "__main__":
    sys.exit(main())
