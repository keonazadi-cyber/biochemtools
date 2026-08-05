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
import glob, re, sys, hashlib, os

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
    for mm in re.finditer(r'\b(\d+)\s+(?:free\s+)?tools\b', h):
        if int(mm.group(1)) != cards:
            errs.append('%s claims "%s tools", should be %d' % (f, mm.group(1), cards))
    for mm in re.finditer(r'src="/streak\.js(\?v=([0-9a-f]+))?"', h):
        if mm.group(2) != ver:
            errs.append("%s loads streak.js with a stale or missing ?v= (want %s)" % (f, ver))

if errs:
    print("FAIL"); [print("  " + e) for e in errs]; sys.exit(1)
print("OK: %d tools, streak.js %d bytes, v%s referenced everywhere" % (cards, len(src), ver))
