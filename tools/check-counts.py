#!/usr/bin/env python3
"""Guard the numbers and files that have silently broken before.

TOOL_COUNT in streak.js caps the progress bar and the homepage repeats the count in
prose; both drifted to 46 while the site had 48 tools. streak.js must also be
referenced with its content hash, or returning visitors keep a cached copy forever.

The emptiness check exists because a script once did
    open("streak.js","w").write(open("streak.js").read())
which truncates the file before the read runs and shipped a 0-byte streak.js to
production. Run this before every push.
"""
import glob, re, sys, hashlib, os, json

os.chdir(os.path.join(os.path.dirname(__file__), ".."))
errs = []

for f in ["streak.js", "index.html", "sitemap.xml"]:
    if os.path.getsize(f) == 0:
        errs.append("%s is EMPTY" % f)
if errs:
    print("FAIL"); [print("  " + e) for e in errs]; sys.exit(1)

src = open("streak.js").read()
m = re.search(r'var TOOL_COUNT = (\d+);', src)
if not m:
    print("FAIL\n  streak.js has no TOOL_COUNT declaration"); sys.exit(1)
for fn in ["renderStreakWidget", "recordVisit", "answerStreak", "renderToolFooterRecent"]:
    if fn not in src:
        errs.append("streak.js is missing %s(), it may have been truncated" % fn)

cards = open("index.html").read().count('<a class="tool"')
declared = int(m.group(1))
ver = hashlib.md5(src.encode()).hexdigest()[:8]
if declared != cards:
    errs.append("streak.js TOOL_COUNT is %d but index.html has %d tool cards" % (declared, cards))

for f in sorted(glob.glob("*.html")):
    h = open(f).read()
    # Strip tags first and allow a few describing words between the number and
    # the noun. The old pattern only caught "46 tools" written exactly that way,
    # so it sat quiet through "<b>46</b> tools", "All 46 free biochem tools" on
    # fifty pages, and "46 free interactive ... tools" in the meta description.
    vis = re.sub(r"<[^>]+>", " ", h)
    vis = vis.replace("&amp;", "&")
    for mm in re.finditer(r"\b(\d+)((?:\s+[A-Za-z&,]+){0,6})\s+tools\b", vis):
        if int(mm.group(1)) != cards:
            errs.append('%s claims "%s%s tools", should be %d'
                        % (f, mm.group(1), mm.group(2).rstrip(), cards))
    for mm in re.finditer(r'src="/streak\.js(\?v=([0-9a-f]+))?"', h):
        if mm.group(2) != ver:
            errs.append("%s loads streak.js with a stale or missing ?v= (want %s)" % (f, ver))


# charts.html publishes each chart image's pixel dimensions in its structured data.
# Rebuilding a chart taller (adding a footer line, say) silently makes those wrong,
# and three of eleven had drifted before this check existed.
try:
    from PIL import Image
    ch = open("charts.html").read()
    mm = re.search(r'<script type="application/ld\+json">(.*?)</script>', ch, re.S)
    if mm:
        for part in json.loads(mm.group(1)).get("hasPart", []):
            rel = part.get("contentUrl", "").split("/downloads/")[-1]
            path = os.path.join("downloads", rel)
            if not os.path.exists(path):
                errs.append("charts.html lists %s but downloads/%s is missing" % (rel, rel))
                continue
            w, h_ = Image.open(path).size
            if (part.get("width"), part.get("height")) != (w, h_):
                errs.append("charts.html says %s is %sx%s, the file is %dx%d"
                            % (rel, part.get("width"), part.get("height"), w, h_))
except ImportError:
    pass

if errs:
    print("FAIL"); [print("  " + e) for e in errs]; sys.exit(1)
print("OK: %d tools, streak.js %d bytes, v%s referenced everywhere" % (cards, len(src), ver))
