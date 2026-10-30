#!/usr/bin/env python3
"""Make each page's JSON-LD describe that page, and no other.

Two jobs, both "whose page is this".

Google shows one page per image in an image pack. It picks that page from the
signals on the page, and ours were pointing at the wrong one: nine pages carried
an ImageObject whose `isPartOf` named charts.html, and whose `license` was
charts.html rather than a licence. amino-acid-chart.html, which does it
correctly, is in its image pack. codon-chart.html, which does not, is not.

So, for every page that embeds a content image and is not a gallery:

  1. license         -> the CC BY 4.0 deed, which is what the field is for and
                        what makes the "Licensable" badge possible at all
  2. isPartOf        -> this page, not the gallery
  3. primaryImageOfPage + image on the WebPage block -> this page nominates it

Idempotent on purpose: run it twice and the second run must report 0 changes.
"""
import json, re, sys, pathlib

ROOT = pathlib.Path(__file__).resolve().parent.parent
SITE = "https://biochemtools.com/"
CCBY = "https://creativecommons.org/licenses/by/4.0/"
ACQUIRE = SITE + "charts.html"

# Galleries list every chart by design; they must not claim an image that has a
# dedicated page of its own.
GALLERIES = {"index.html", "charts.html"}

IMG_RE = re.compile(
    r'<img[^>]*src="(/(?:downloads|structures|curves)/[^"]+)"[^>]*>')
LD_RE = re.compile(r'(<script type="application/ld\+json">)([\s\S]*?)(</script>)')


def page_url(name):
    return SITE if name == "index.html" else SITE + name


def primary_image(html):
    """The first chart-sized content image on the page. Structures are 320px
    decorations, never the thing someone searched for."""
    for m in IMG_RE.finditer(html):
        src = m.group(1)
        # -light variants are the suggestions-page thumbnails, a UI skin of a
        # chart that already has its own home. Never nominate one.
        if src.startswith("/structures/") or src.endswith("-light.png"):
            continue
        tag = m.group(0)
        w = re.search(r'width="(\d+)"', tag)
        h = re.search(r'height="(\d+)"', tag)
        alt = re.search(r'alt="([^"]*)"', tag)
        return {
            "src": src,
            "width": int(w.group(1)) if w else None,
            "height": int(h.group(1)) if h else None,
            "alt": alt.group(1) if alt else "",
        }
    return None


def drop_foreign_webpage(name, html, report):
    """Remove a WebPage node that says it is a different page.

    build_titration_pages.py builds each curve page out of the tool page's own
    markup, and carried the tool's WebPage block along with it. All twenty curve
    pages therefore declared a second WebPage entity with the hub's url, title
    and dates, next to their own. Two WebPage entities on one page, one of them
    naming a different URL, is a page telling Google two stories about what it
    is, on the pages that rank best on the site.
    """
    # What counts as "this page" is wider than one string. index.html declared
    # its WebPage as .../index.html while its canonical is .../ , and comparing
    # on one spelling deleted the homepage's own identity. Take the page's own
    # canonical as the authority and accept every spelling of itself.
    mine = {page_url(name), SITE + name}
    if name == "index.html":
        mine.add(SITE)
    can = re.search(r'<link rel="canonical"[^>]*href="([^"]+)"', html)
    if can:
        mine.add(can.group(1))
        mine.add(can.group(1).rstrip("/") + "/index.html")
    dropped = [0]

    def fix(m):
        raw = m.group(2)
        try:
            data = json.loads(raw)
        except ValueError:
            return m.group(0)
        nodes = data if isinstance(data, list) else [data]
        keep = [n for n in nodes
                if not (n.get("@type") == "WebPage"
                        and n.get("url") and n.get("url") not in mine)]
        if len(keep) == len(nodes):
            return m.group(0)
        dropped[0] += len(nodes) - len(keep)
        if not keep:
            return ""                      # the whole block was the foreign node
        out = keep[0] if len(keep) == 1 else keep
        return m.group(1) + json.dumps(out, separators=(",", ":"),
                                       ensure_ascii=False) + m.group(3)

    out = LD_RE.sub(fix, html)
    if dropped[0]:
        report.append((name, "dropped %d WebPage node(s) naming another page"
                       % dropped[0]))
    return out


def normalize(name, html, report):
    html = drop_foreign_webpage(name, html, report)
    img = primary_image(html)
    if img is None or name in GALLERIES:
        return html          # the foreign-WebPage pass above already ran
    url = page_url(name)
    content_url = SITE.rstrip("/") + img["src"]
    changed = []

    def fix_block(raw):
        try:
            data = json.loads(raw)
        except ValueError:
            report.append((name, "UNPARSEABLE ld+json, left alone"))
            return raw
        def walk(x):
            """Every object in the block, at any depth.

            The licence also lives inside primaryImageOfPage, which this script
            writes but only when the key is absent. Walking top-level nodes only
            meant a wrong value nested there was never repaired, and the audit
            could not see it either.
            """
            if isinstance(x, dict):
                yield x
                for v in x.values():
                    for y in walk(v):
                        yield y
            elif isinstance(x, list):
                for v in x:
                    for y in walk(v):
                        yield y

        touched = False
        # Any node carrying a licence must carry a real one, however deep.
        for node in walk(data):
            if ("license" in node
                    and "creativecommons.org/licenses/" not in str(node["license"])):
                node["license"] = CCBY
                changed.append("license")
                touched = True

        nodes = data if isinstance(data, list) else [data]
        for node in nodes:
            t = node.get("@type")
            if t == "ImageObject" and node.get("contentUrl") == content_url:
                part = node.get("isPartOf")
                if not (isinstance(part, dict) and part.get("url") == url):
                    node["isPartOf"] = {"@type": "WebPage", "url": url}
                    changed.append("isPartOf")
                    touched = True
                node.setdefault("acquireLicensePage", ACQUIRE)
            if t == "WebPage" and node.get("url") == url:
                if "primaryImageOfPage" not in node:
                    node["image"] = content_url
                    node["primaryImageOfPage"] = {
                        "@type": "ImageObject",
                        "contentUrl": content_url,
                        "url": content_url,
                        **({"width": img["width"]} if img["width"] else {}),
                        **({"height": img["height"]} if img["height"] else {}),
                        "caption": img["alt"],
                        "license": CCBY,
                        "acquireLicensePage": ACQUIRE,
                        "creditText": "BiochemTools",
                        "creator": {"@type": "Organization",
                                    "name": "BiochemTools"},
                    }
                    changed.append("primaryImageOfPage")
                    touched = True
        if not touched:
            return raw
        return json.dumps(data, separators=(",", ":"), ensure_ascii=False)

    out = LD_RE.sub(lambda m: m.group(1) + fix_block(m.group(2)) + m.group(3),
                    html)
    if changed:
        report.append((name, ", ".join(sorted(set(changed)))))
    return out


def main():
    report = []
    written = 0
    for path in sorted(ROOT.glob("*.html")):
        html = path.read_text()
        out = normalize(path.name, html, report)
        if out != html:
            path.write_text(out)
            written += 1
    for name, what in report:
        print("  %-44s %s" % (name, what))
    print("%d page(s) changed" % written)
    return written


if __name__ == "__main__":
    sys.exit(0 if main() >= 0 else 1)
