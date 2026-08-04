#!/usr/bin/env python3
"""Guard the two numbers that have silently gone stale before.

TOOL_COUNT in streak.js caps the progress bar, and the homepage hero repeats the
count in prose. Both drifted to 46 while the site had 48 tools. Run before a push.
Also verifies streak.js is referenced with a content hash, so returning visitors
actually receive updates instead of a cached copy.
"""
import glob, re, sys, hashlib, os

os.chdir(os.path.join(os.path.dirname(__file__), ".."))
cards = open("index.html").read().count('<a class="tool"')
declared = int(re.search(r'var TOOL_COUNT = (\d+);', open("streak.js").read()).group(1))
ver = hashlib.md5(open("streak.js", "rb").read()).hexdigest()[:8]

errs = []
if declared != cards:
    errs.append("streak.js TOOL_COUNT is %d but index.html has %d tool cards" % (declared, cards))

for f in sorted(glob.glob("*.html")):
    h = open(f).read()
    for m in re.finditer(r'\b(\d+)\s+(?:free\s+)?tools\b', h):
        if int(m.group(1)) != cards:
            errs.append('%s claims "%s tools", should be %d' % (f, m.group(1), cards))
    for m in re.finditer(r'src="/streak\.js(\?v=([0-9a-f]+))?"', h):
        if m.group(2) != ver:
            errs.append("%s loads streak.js with a stale or missing ?v= (want %s)" % (f, ver))

if errs:
    print("FAIL"); [print("  " + e) for e in errs]; sys.exit(1)
print("OK: %d tools, streak.js v%s referenced correctly everywhere" % (cards, ver))
