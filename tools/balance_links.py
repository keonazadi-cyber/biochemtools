#!/usr/bin/env python3
"""Give the under-linked pages that actually have demand a contextual link.

Measured 2026-11-03. Every page has at least one contextual inbound link, so
there are no orphans, but the links are distributed by accident rather than by
value:

  nucleic-acid-concentration-calculator   1,000 Bing impressions, 1 inbound link
  beer-lambert-calculator                   409 impressions,      2 inbound
  serial-dilution-calculator                275 impressions,      2 inbound
  oxygen-dissociation-curve-calculator      256 impressions,      2 inbound

Contextual links, the ones inside <main>, are what a crawler weighs; the global
nav links every page to every page and therefore says nothing. On a site whose
documented binding constraint on Google is crawl budget, that matters.

The mapping below is curated by hand, not generated from text similarity. A
plausible-looking but irrelevant link is worse for a reader and for a crawler
than an imbalance, so each pair here is one a student would actually follow.

Only adds; never removes a link someone chose. Idempotent.
"""
import pathlib, re, sys

SITE = pathlib.Path(__file__).resolve().parent.parent

# target page -> pages that should link to it, and the anchor text to use
WANT = {
    "nucleic-acid-concentration-calculator.html": (
        "DNA and RNA concentration (A260)",
        ["dna-melting-temperature-calculator.html",
         "dna-to-protein-translation.html",
         "oligocalc-alternative.html"]),
    "beer-lambert-calculator.html": (
        "Beer-Lambert absorbance",
        ["nucleic-acid-concentration-calculator.html",
         "protein-molecular-weight-calculator.html",
         "enzyme-kinetics-simulator.html"]),
    "serial-dilution-calculator.html": (
        "Serial dilution",
        ["dilution-calculator.html",
         "antibody-dilution-calculator.html",
         "molarity-molar-mass-calculator.html"]),
    "oxygen-dissociation-curve-calculator.html": (
        "Oxygen-hemoglobin dissociation curve",
        ["cardiac-output-calculator.html",
         "membrane-transport-explorer.html",
         "renal-clearance-calculator.html"]),
}

# Two wordings exist on the site, "Related tools:" and "See also:". Matching
# only the first silently skipped dna-to-protein-translation.html, which has
# 3,242 Google impressions, and oligocalc-alternative.html, which has neither.
REL = re.compile(r'(<p class="note">(?:Related tools|See also):)([\s\S]*?)(</p>)')
# Where to start a line on a page that has none: just before the ask line.
ASKLINE = "<!-- askline:start -->"


def main():
    added = 0
    for target, (anchor, sources) in WANT.items():
        if not (SITE / target).exists():
            print("  FAIL target %s does not exist" % target); return 1
        for src in sources:
            path = SITE / src
            if not path.exists():
                print("  FAIL source %s does not exist" % src); return 1
            h = path.read_text()
            # Check inside <main> only. The global nav links every page to every
            # page, so scanning the whole file always matched and this script
            # silently did nothing on its first run.
            body = h
            for pat in (r'<nav id="sitenav"[\s\S]*?</nav>',
                        r'<footer[\s\S]*?</footer>',
                        r'<div class="topnav"[\s\S]*?</div>'):
                body = re.sub(pat, "", body)
            main_only = (body.split("<main", 1)[-1].split("</main>", 1)[0]
                         if "<main" in body else body)
            if 'href="/%s"' % target in main_only:
                continue                      # already linked, leave it alone
            m = REL.search(h)
            link = ' <a href="/%s">%s</a> &middot;' % (target, anchor)
            if m:
                # insert directly after the label so it reads first
                h = h[:m.end(1)] + link + h[m.end(1):m.end(3)] + h[m.end(3):]
            elif ASKLINE in h:
                fresh = ('<p class="note">Related tools: <a href="/%s">%s</a>'
                         ' &middot; <a href="/">all biochem tools</a>.</p>\n'
                         % (target, anchor))
                h = h.replace(ASKLINE, fresh + ASKLINE, 1)
                print("  %-44s -> %s  (new line)" % (src, target))
                path.write_text(h)
                added += 1
                continue
            else:
                print("  skip %s has nowhere to put a link" % src)
                continue
            path.write_text(h)
            added += 1
            print("  %-44s -> %s" % (src, target))
    print("  %d contextual link(s) added" % added)
    return 0


if __name__ == "__main__":
    sys.exit(main())
