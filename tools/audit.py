#!/usr/bin/env python3
"""Whole-site audit: metadata, links, structure, and pages that overwhelm.

check-counts.py guards the handful of numbers that have broken before. This is
the wider sweep: every page, every link, every title, looking for the things that
quietly cost traffic or make a page hard to read.
"""
import os, re, glob, json, html, collections, sys

SITE = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..")
SITE_URL = "https://biochemtools.com/"
os.chdir(SITE)
PAGES = sorted(p for p in glob.glob("*.html") if p != "404.html")

def read(p):
    return open(p, encoding="utf-8").read()

def visible(h):
    h = re.sub(r"<(script|style|nav|footer)[\s\S]*?</\1>", " ", h, flags=re.I)
    return html.unescape(re.sub(r"<[^>]+>", " ", h))

def tag(h, pat, group=1):
    m = re.search(pat, h, re.I | re.S)
    return m.group(group).strip() if m else None

findings = collections.defaultdict(list)
def add(cat, page, msg):
    findings[cat].append((page, msg))

docs = {p: read(p) for p in PAGES}

# ---------- metadata ----------
titles, descs = collections.defaultdict(list), collections.defaultdict(list)
for p, h in docs.items():
    t = tag(h, r"<title>(.*?)</title>")
    d = tag(h, r'<meta name="description" content="(.*?)"')
    c = tag(h, r'<link rel="canonical" href="(.*?)"')
    h1s = re.findall(r"<h1[^>]*>(.*?)</h1>", h, re.S | re.I)

    if not t: add("title", p, "no <title>")
    else:
        titles[t].append(p)
        n = len(html.unescape(t))
        if n > 62: add("title", p, "title is %d chars, will truncate: %s" % (n, t[:70]))
        elif n < 25: add("title", p, "title is only %d chars: %s" % (n, t))
    if not d: add("description", p, "no meta description")
    else:
        descs[d].append(p)
        n = len(html.unescape(d))
        if n > 165: add("description", p, "description is %d chars, will truncate" % n)
        elif n < 70: add("description", p, "description is only %d chars" % n)
    if not c: add("canonical", p, "no canonical")
    elif not c.rstrip("/").endswith(p.replace("index.html", "")) and not (p == "index.html" and c.rstrip("/").endswith("biochemtools.com")):
        add("canonical", p, "canonical points at %s" % c)
    if len(h1s) == 0: add("headings", p, "no <h1>")
    elif len(h1s) > 1: add("headings", p, "%d <h1> tags" % len(h1s))

for t, ps in titles.items():
    if len(ps) > 1: add("duplicate", ps[0], "title shared by %d pages: %s" % (len(ps), ", ".join(ps)))
for d, ps in descs.items():
    if len(ps) > 1: add("duplicate", ps[0], "description shared by %d pages: %s" % (len(ps), ", ".join(ps)))

# ---------- internal links ----------
for p, h in docs.items():
    for m in re.finditer(r'href="(/[^"#?]*)[^"]*"', h):
        t = m.group(1).lstrip("/")
        # hrefs built in JavaScript are not real links: daily-question.html has
        # href="/' + question.tool + '.html", which is a template, not a target
        if not t or t.endswith("/") or "'" in t or "+" in t or "${" in t: continue
        if not os.path.exists(t):
            add("broken link", p, "links to /%s which does not exist" % t)

# ---------- images ----------
for p, h in docs.items():
    for m in re.finditer(r"<img\b[^>]*>", h):
        tagtxt = m.group(0)
        if 'alt="' not in tagtxt: add("images", p, "img with no alt: %s" % tagtxt[:70])
        src = re.search(r'src="([^"]+)"', tagtxt)
        if src and src.group(1).startswith("/") and not os.path.exists(src.group(1).lstrip("/")):
            add("images", p, "missing file %s" % src.group(1))

# ---------- structured data ----------
for p, h in docs.items():
    for m in re.finditer(r'<script type="application/ld\+json">([\s\S]*?)</script>', h):
        try: json.loads(m.group(1))
        except Exception as e: add("structured data", p, "invalid JSON-LD: %s" % str(e)[:60])

# ---------- house rules ----------
for p, h in docs.items():
    v = visible(h)
    if "—" in v: add("house style", p, "em dash in visible text")
    if re.search(r"\b18[- ]year[- ]old\b|\bI am 18\b", v, re.I): add("house style", p, "mentions age")

# ---------- sitemap ----------
sm = read("sitemap.xml") if os.path.exists("sitemap.xml") else ""
listed = set(re.findall(r"<loc>https://biochemtools\.com/([^<]*)</loc>", sm))
for p in PAGES:
    key = "" if p == "index.html" else p
    if key not in listed: add("sitemap", p, "not in sitemap.xml")
for u in listed:
    if u and not os.path.exists(u): add("sitemap", "sitemap.xml", "lists /%s which does not exist" % u)

# ---------- orphans ----------
linked = set()
for h in docs.values():
    for m in re.finditer(r'href="/([^"#?]*)', h):
        linked.add(m.group(1))
for p in PAGES:
    if p == "index.html": continue
    if p not in linked: add("orphan", p, "no internal page links to it")

# ---------- thin content ----------
# A page that means to win a search needs enough substance to answer it. These
# thresholds come from the site's own distribution: median 750 words.
for p, h in docs.items():
    if p in ("404.html",): continue
    v = re.sub(r"\s+", " ", visible(h)).strip()
    words = len(v.split())
    if words < 400:
        add("thin", p, "%d words of crawlable text" % words)

# ---------- title vs h1 ----------
for p, h in docs.items():
    t = tag(h, r"<title>(.*?)</title>") or ""
    h1 = tag(h, r"<h1[^>]*>(.*?)</h1>") or ""
    h1 = re.sub(r"<[^>]+>", "", h1)
    tw = set(re.findall(r"[a-z0-9]+", html.unescape(t).lower()))
    hw = set(re.findall(r"[a-z0-9]+", html.unescape(h1).lower()))
    if hw and tw and not (hw & tw):
        add("headings", p, "h1 shares no words with the title (%r vs %r)" % (h1[:40], t[:40]))

# ---------- social preview ----------
for p, h in docs.items():
    og = tag(h, r'<meta property="og:image" content="(.*?)"')
    if not og:
        add("social", p, "no og:image, shares will render bare")
    elif og.startswith("https://biochemtools.com/"):
        f = og.replace("https://biochemtools.com/", "")
        if not os.path.exists(f):
            add("social", p, "og:image points at missing file %s" % f)

# ---------- how well linked ----------
inbound = collections.Counter()
for src, h in docs.items():
    body = h
    m = re.search(r'<nav id="sitenav"', h)
    if m:
        body = h[:m.start()]          # ignore the boilerplate footer nav
    for mm in re.finditer(r'href="/([^"#?]*)', body):
        t = mm.group(1)
        if t and t != src:
            inbound[t] += 1
for p in PAGES:
    if p == "index.html": continue
    if inbound[p] == 0:
        add("internal links", p, "only reachable from the footer nav, no contextual link anywhere")

# ---------- overwhelming ----------
for p, h in docs.items():
    v = re.sub(r"\s+", " ", visible(h)).strip()
    words = len(v.split())
    cards = len(re.findall(r'class="card"', h))
    h2 = len(re.findall(r"<h2", h, re.I))
    if words > 2600: add("overwhelming", p, "%d words of visible text" % words)
    if cards > 12: add("overwhelming", p, "%d cards on one page" % cards)
    if h2 > 14: add("overwhelming", p, "%d h2 sections" % h2)


# ---------- analytics ----------
# 22 pages shipped without the Cloudflare beacon, including charts.html, which is
# the page submitted to OER Commons and MERLOT. They were invisible in the traffic
# numbers for a month, which nearly produced a wrong conclusion about whether the
# generated pages were working.
for p, h in docs.items():
    if "cloudflareinsights" not in h:
        add("analytics", p, "no Cloudflare beacon, this page is invisible in traffic data")
    n = h.count("gtag/js?id=G-E3NEEKFCPP")
    if n == 0:
        add("analytics", p, "no Google Analytics tag, this page is invisible to Mediavine")
    elif n > 1:
        add("analytics", p, "%d Google Analytics tags, Google says never add more than one" % n)
    # charset has to land inside the first 1024 bytes or a browser may sniff the
    # encoding wrong. The gtag block sits above it, so this is worth watching.
    i = h.encode("utf-8").find(b"<meta charset")
    if i >= 1024:
        add("analytics", p, "charset is at byte %d, past the 1024 byte limit" % i)

# --- duplicate id attributes -------------------------------------------------
# An id has to be unique in a document. This is here because a generator's cleanup
# regex never matched its own output, so every run appended another copy of the
# same link block, and eleven had stacked up on amino-acid-titration-curve.html
# before anyone noticed. A duplicate id is the cheapest signal that a build step
# is appending where it means to replace.
for p, h in docs.items():
    ids = re.findall(r'\sid="([^"]+)"', h)
    for i in sorted({x for x in ids if ids.count(x) > 1}):
        add("duplicate", p, 'id="%s" appears %d times, an id must be unique' % (i, ids.count(i)))

# --- the curve pages must ship an image a crawler can actually see ------------
# The titration curves are drawn in a <canvas>, which Google Images cannot index.
# The `cysteine titration curve` result page opens with an image pack of eight
# curves and ours was not among them. Each page now ships a real PNG as well.
curve_pages = sorted(x for x in docs if x.endswith("-titration-curve.html")
                     and x != "amino-acid-titration-curve.html")
seen_og = {}
for p in curve_pages:
    h = docs[p]
    imgs = re.findall(r'<img[^>]*src="([^"]+)"[^>]*>', h)
    curve_img = [u for u in imgs if "/curves/" in u]
    if not curve_img:
        add("images", p, "draws its curve in canvas only, so Google Images cannot see it")
    for u in curve_img:
        f = os.path.join(SITE, u.lstrip("/"))
        if not os.path.exists(f):
            add("images", p, "references %s, which is not on disk" % u)
    for m in re.finditer(r'<img[^>]*>', h):
        if "/curves/" in m.group(0) and not re.search(r'alt="[^"]{30,}"', m.group(0)):
            add("images", p, "the curve image has no usable alt text")
    # The overlay canvas has to be transparent in CSS. The site's own canvas rule
    # gives it an opaque background, and an unpainted canvas then covers the image
    # completely, so with JavaScript off the curve was a blank dark rectangle. The
    # script paints its own background before drawing, so this costs nothing.
    m = re.search(r"\.curvewrap canvas\{([^}]*)\}", h)
    if not m:
        add("images", p, "no .curvewrap canvas rule, the overlay is unstyled")
    elif "background:transparent" not in m.group(1).replace(" ", ""):
        add("images", p, "the overlay canvas is not transparent, so the curve "
                         "disappears for anyone without JavaScript")

# --- every page needs its own social image -----------------------------------
# All nine curve pages shared og-images/amino-acid-titration-curve.png, so sharing
# a link to the cysteine page previewed a different amino acid's curve.
for p in curve_pages:
    m = re.search(r'<meta property="og:image" content="([^"]+)"', docs[p])
    if not m:
        add("social", p, "no og:image")
        continue
    seen_og.setdefault(m.group(1), []).append(p)
for url, pages in seen_og.items():
    if len(pages) > 1:
        n = len(pages) - 1
        add("social", pages[0], "shares og:image %s with %d other curve page%s"
            % (url.rsplit("/", 1)[-1], n, "" if n == 1 else "s"))

# --- the sitemap must not list the same url twice -----------------------------
# A generator whose cleanup regex stopped matching its own output quietly stacked
# four copies of every titration page into sitemap.xml. The generator asserts this
# itself now, but the guard belongs here too, so it holds for any source.
_sm = os.path.join(SITE, "sitemap.xml")
if os.path.exists(_sm):
    _x = open(_sm, encoding="utf-8").read()
    _locs = re.findall(r"<url><loc>([^<]+)</loc>", _x)
    for _u in sorted({u for u in _locs if _locs.count(u) > 1}):
        add("sitemap", "sitemap.xml", "%s is listed %d times" % (_u, _locs.count(_u)))

# --- a content image must be declared on the page that shows it ---------------
# Every chart was listed in the sitemap under charts.html and nowhere else, and
# charts.html has never been indexed, so the only declared route to any chart we
# own ran through a dead page. genetic-code-chart.png sat on codon-chart.html,
# 4,349 impressions, undeclared. tools/sitemap_images.py fixes this; the guard is
# here so it stays fixed.
_sm2 = os.path.join(SITE, "sitemap.xml")
if os.path.exists(_sm2):
    _x2 = open(_sm2, encoding="utf-8").read()
    for _p, _h in docs.items():
        _imgs = {m.group(1).lstrip("/") for m in
                 re.finditer(r'<img[^>]*\ssrc="(/(?:downloads|curves)/[^"]+)"', _h)}
        if not _imgs:
            continue
        _loc = "https://biochemtools.com/" + ("" if _p == "index.html" else _p)
        _m2 = re.search(r"<url><loc>%s</loc>([\s\S]*?)</url>" % re.escape(_loc), _x2)
        if not _m2:
            add("sitemap", _p, "embeds %d content image(s) but is not in the sitemap" % len(_imgs))
            continue
        _declared = set(re.findall(r"<image:loc>https://biochemtools\.com/([^<]+)</image:loc>",
                                   _m2.group(1)))
        for _u in sorted(_imgs - _declared):
            add("images", _p, "shows %s but the sitemap does not declare it here, so "
                              "Google has no route to it from this page" % _u)

# --- the suggestions page must keep working ----------------------------------
# A feedback form that silently stops posting looks identical to a site nobody has
# opinions about. These check the parts that would fail quietly.
_sg = os.path.join(SITE, "suggest.html")
if not os.path.exists(_sg):
    add("broken link", "suggest.html", "the suggestions page is missing")
else:
    _h = open(_sg, encoding="utf-8").read()
    _m = re.search(r'<form[^>]*action="([^"]+)"', _h)
    if not _m:
        add("broken link", "suggest.html", "has no form at all")
    elif "formspree.io/f/" not in _m.group(1):
        add("broken link", "suggest.html", "form posts to %s, not a Formspree endpoint" % _m.group(1))
    if 'name="message"' not in _h:
        add("broken link", "suggest.html", "the form has no message field")
    for _img in re.findall(r'<img[^>]*src="(/downloads/[^"]+)"', _h):
        if not os.path.exists(os.path.join(SITE, _img.lstrip("/"))):
            add("images", "suggest.html", "receipt image %s is not on disk" % _img)
    # every tool page should offer the ask line; policy pages deliberately do not
    _skip = {"404.html", "about.html", "contact.html", "privacy.html", "license.html",
             "suggest.html", "charts.html", "daily-question.html", "index.html"}
    for _p, _ph in docs.items():
        if _p in _skip or "</main>" not in _ph:
            continue
        if "askline:start" not in _ph:
            add("internal links", _p, "no link to the suggestions page, so feedback has to be hunted for")

# --- never link an internal page with a query string -------------------------
# The ask line shipped as /suggest.html?from=<page>, which made 73 separate
# crawlable URLs of one page. Google crawled every one, on a site whose binding
# constraint is crawl budget at roughly 18 fetches a day, so they were competing
# with the real pages still waiting to be crawled. A #fragment does the same job
# and is never a separate URL.
for p, h in docs.items():
    for m in re.finditer(r'href="(/[a-z0-9\-]+\.html)\?([^"]*)"', h):
        add("internal links", p,
            "links %s with a query string (?%s), which makes a separate crawlable URL; "
            "use a #fragment" % (m.group(1), m.group(2)[:40]))

# --- one page per image, and a licence that is actually a licence ------------
# Google shows one page per image in an image pack, and it believes the page's
# own schema about which page that is. Nine pages shipped an ImageObject whose
# isPartOf named charts.html and whose `license` was charts.html rather than a
# licence URL, so they nominated a different page and offered no licence terms.
# amino-acid-chart.html, which gets all three right, is in its image pack;
# codon-chart.html, which got all three wrong, is not. tools/normalize_image_schema.py
# fixes this at the source; these three checks stop it coming back.
_CCBY = "https://creativecommons.org/licenses/by/4.0/"


def _content_imgs(h):
    """The images on a page that Google could rank, in page order.

    /curves/ belongs here as much as /downloads/ does: the twenty titration
    pages are the ones that actually rank, and leaving them out meant the
    original defect could be reintroduced on any of them without the audit
    noticing. -light variants are suggestion-page thumbnails of a chart that
    already has a home, and /structures/ are 320px decorations.
    """
    return [u for u in re.findall(r'<img[^>]*src="(/(?:downloads|curves)/[^"]+)"', h)
            if not u.endswith("-light.png")]


_GALLERY = {"index.html", "charts.html"}
_nominated = {}
for p, h in docs.items():
    _url = SITE_URL if p == "index.html" else SITE_URL + p
    for _m in re.finditer(r'<script type="application/ld\+json">([\s\S]*?)</script>', h):
        try:
            _d = json.loads(_m.group(1))
        except Exception:
            continue                       # invalid JSON-LD is already reported
        def _walk(_x):
            """Every object anywhere in the block, however deeply nested.

            Checking only top-level nodes missed a `license` inside
            primaryImageOfPage, which is one of the two places
            normalize_image_schema.py writes one. A broken value there passed
            the audit clean.
            """
            if isinstance(_x, dict):
                yield _x
                for _v in _x.values():
                    for _y in _walk(_v):
                        yield _y
            elif isinstance(_x, list):
                for _v in _x:
                    for _y in _walk(_v):
                        yield _y
        for _n in _walk(_d):
            _lic = _n.get("license")
            if _lic and "creativecommons.org/licenses/" not in _lic:
                add("structured data", p,
                    'license is %r, which is not a licence URL, so no "Licensable" '
                    'badge can ever show' % _lic[:60])
            if _n.get("@type") == "ImageObject":
                # Only the page's own hero image is at stake. A page may also show
                # a chart that genuinely belongs to the gallery, and saying so is
                # correct, not a defect.
                _mine = _content_imgs(h)
                _hero = SITE_URL.rstrip("/") + _mine[0] if _mine else None
                _part = _n.get("isPartOf")
                _pu = _part.get("url") if isinstance(_part, dict) else None
                if (_pu and _pu != _url and p not in _GALLERY
                        and _n.get("contentUrl") == _hero):
                    add("structured data", p,
                        "its ImageObject says isPartOf %s, handing its own image to "
                        "another page" % _pu)
            if _n.get("@type") == "WebPage" and _n.get("primaryImageOfPage"):
                _pi = _n["primaryImageOfPage"]
                _cu = _pi.get("contentUrl") if isinstance(_pi, dict) else None
                if _cu:
                    _nominated.setdefault(_cu, []).append(p)
for _cu, _pages in sorted(_nominated.items()):
    if len(_pages) > 1:
        add("structured data", sorted(_pages)[0],
            "%s is nominated as the primary image of %d pages (%s), so Google has "
            "to pick one" % (_cu.rsplit("/", 1)[-1], len(_pages), ", ".join(sorted(_pages))))
# --- a page may not claim to be a different page ----------------------------
# build_titration_pages.py builds each curve page from the tool page's markup and
# carried the tool's WebPage block with it, so twenty curve pages (and five more
# built the same way) declared a second WebPage entity with another page's url,
# title and dates. tools/normalize_schema.py removes it; this stops it returning.
for p, h in docs.items():
    _canon = re.search(r'<link rel="canonical"[^>]*href="([^"]+)"', h)
    _mine = {SITE_URL + p, SITE_URL}
    if _canon:
        _mine.add(_canon.group(1))
        _mine.add(_canon.group(1).rstrip("/") + "/index.html")
    _mine.add(SITE_URL + "index.html")
    for _m in re.finditer(r'<script type="application/ld\+json">([\s\S]*?)</script>', h):
        try:
            _d = json.loads(_m.group(1))
        except Exception:
            continue
        for _n in (_d if isinstance(_d, list) else [_d]):
            if (_n.get("@type") == "WebPage" and _n.get("url")
                    and _n["url"] not in _mine):
                add("structured data", p,
                    "declares a WebPage whose url is %s, so the page tells Google "
                    "it is a different page" % _n["url"])

# a page that owns a chart has to say so, or it competes with the gallery unarmed
for p, h in docs.items():
    if p in _GALLERY or p == "suggest.html":
        continue
    _own = _content_imgs(h)
    # Several pages can legitimately show the same chart. What matters is that
    # exactly one of them claims it, so only an image no page claims is a finding.
    _orphan = [u for u in _own
               if not any(u in _c for _c in _nominated)]
    if _orphan and "primaryImageOfPage" not in h:
        add("structured data", p,
            "embeds %s and no page on the site nominates it as primaryImageOfPage, "
            "so the gallery wins the image pack slot" % _orphan[0])

ORDER = ["analytics", "broken link", "images", "structured data", "title", "description", "canonical",
         "headings", "duplicate", "sitemap", "orphan", "thin", "internal links", "social",
         "house style", "overwhelming"]
total = 0
for cat in ORDER:
    if cat not in findings: continue
    rows = findings[cat]; total += len(rows)
    print("\n=== %s (%d) ===" % (cat.upper(), len(rows)))
    for pg, msg in rows[:40]:
        print("  %-42s %s" % (pg, msg))
    if len(rows) > 40: print("  ... and %d more" % (len(rows) - 40))
print("\n%d findings across %d pages" % (total, len(PAGES)))
