#!/usr/bin/env python3
"""Whole-site audit: metadata, links, structure, and pages that overwhelm.

check-counts.py guards the handful of numbers that have broken before. This is
the wider sweep: every page, every link, every title, looking for the things that
quietly cost traffic or make a page hard to read.
"""
import os, re, glob, json, html, collections, sys

SITE = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..")
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

ORDER = ["broken link", "images", "structured data", "title", "description", "canonical",
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
