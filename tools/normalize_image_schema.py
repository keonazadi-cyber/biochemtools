#!/usr/bin/env python3
"""Give every content image exactly one page that claims it.

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


def normalize(name, html, report):
    img = primary_image(html)
    if img is None or name in GALLERIES:
        return html
    url = page_url(name)
    content_url = SITE.rstrip("/") + img["src"]
    changed = []

    def fix_block(raw):
        try:
            data = json.loads(raw)
        except ValueError:
            report.append((name, "UNPARSEABLE ld+json, left alone"))
            return raw
        nodes = data if isinstance(data, list) else [data]
        touched = False
        for node in nodes:
            t = node.get("@type")
            # Every chart on the site is CC BY. A `license` that is not a licence
            # URL is wrong wherever it appears, including on a secondary chart the
            # page shows but does not own.
            if t == "ImageObject" and "creativecommons.org/licenses/" not in str(
                    node.get("license", "")):
                node["license"] = CCBY
                changed.append("license")
                touched = True
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
