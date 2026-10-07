#!/usr/bin/env python3
"""Declare each content image on the page that actually embeds it.

Every downloadable chart was listed in sitemap.xml under charts.html, and only
there. charts.html has had zero Google impressions since it was published on
2026-08-03, despite 79 inbound links, so the only declared route to any chart we
own ran through a page Google has never indexed.

Meanwhile genetic-code-chart.png is embedded on codon-chart.html, which IS indexed
and carries 4,349 impressions, and the sitemap never mentioned it there.

This walks every page, finds the images it genuinely embeds as <img>, and writes an
<image:image> entry on that page's own sitemap url. charts.html keeps its own,
because it does embed them.

Only images under downloads/ and curves/ count. Structure SVGs and icons are
page furniture, not content worth surfacing in an image pack.
"""
import os, re, glob, sys, html as _html

SITE = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..")
SM = os.path.join(SITE, "sitemap.xml")
CONTENT = re.compile(r'<img[^>]*\ssrc="(/(?:downloads|curves)/[^"]+)"[^>]*>')


def embedded(h):
    """(url, alt) for every content image the page really shows."""
    out = []
    for m in re.finditer(r"<img[^>]*>", h):
        tag = m.group(0)
        src = re.search(r'\ssrc="(/(?:downloads|curves)/[^"]+)"', tag)
        if not src:
            continue
        alt = re.search(r'\salt="([^"]*)"', tag)
        out.append((src.group(1).lstrip("/"), alt.group(1) if alt else ""))
    seen, uniq = set(), []
    for u, a in out:
        if u not in seen:
            seen.add(u)
            uniq.append((u, a))
    return uniq


def main():
    x = open(SM, encoding="utf-8").read()
    pages = {os.path.basename(p): open(p, encoding="utf-8").read()
             for p in glob.glob(os.path.join(SITE, "*.html"))}

    total, touched, missing_alt = 0, [], []
    for name, h in sorted(pages.items()):
        imgs = embedded(h)
        loc = "https://biochemtools.com/" + ("" if name == "index.html" else name)
        m = re.search(r"(<url><loc>%s</loc>)([\s\S]*?)(</url>)" % re.escape(loc), x)
        if not m:
            continue
        body = re.sub(r"<image:image>[\s\S]*?</image:image>", "", m.group(2))
        for u, a in imgs:
            if not os.path.exists(os.path.join(SITE, u)):
                print("  FAIL %s embeds %s, which is not on disk" % (name, u))
                return 1
            if len(a) < 20:
                missing_alt.append((name, u))
            body += ('<image:image><image:loc>https://biochemtools.com/%s</image:loc>'
                     '<image:title>%s</image:title></image:image>'
                     % (u, _html.escape(a[:160], quote=True)))
        if imgs:
            touched.append((name, len(imgs)))
            total += len(imgs)
        x = x[:m.start()] + m.group(1) + body + m.group(3) + x[m.end():]

    if missing_alt:
        for n, u in missing_alt:
            print("  FAIL %s: %s has no usable alt text to use as an image title" % (n, u))
        return 1

    locs = re.findall(r"<url><loc>([^<]+)</loc>", x)
    dupes = sorted({u for u in locs if locs.count(u) > 1})
    if dupes:
        print("  FAIL sitemap would have duplicate urls: %s" % dupes[:5])
        return 1

    open(SM, "w", encoding="utf-8").write(x)
    print("  %d content images declared across %d pages" % (total, len(touched)))
    for n, c in sorted(touched, key=lambda t: -t[1]):
        print("    %-44s %d" % (n, c))
    return 0


if __name__ == "__main__":
    sys.exit(main())
