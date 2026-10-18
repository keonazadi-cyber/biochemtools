#!/usr/bin/env python3
"""One quiet line at the bottom of every tool page, pointing at /suggest.html.

Most feedback comes from someone mid-task who just hit the thing the site does not
do, not from someone who went hunting for a contact page. So the ask has to be where
the work happens.

It carries ?from=<page> so a suggestion arrives already knowing which tool prompted
it, which is the difference between "add a converter" and a fixable report.

Excluded: policy and meta pages (privacy, license, about, contact, 404, and the
suggestions page itself), where it would be noise rather than an invitation.
"""
import os, re, glob, sys

SITE = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..")
SKIP = {"404.html", "about.html", "contact.html", "privacy.html", "license.html",
        "suggest.html", "charts.html", "daily-question.html", "index.html"}
START = "<!-- askline:start -->"
END = "<!-- askline:end -->"


def block(page):
    return ('%s\n <p class="askline" style="margin:2.5rem 0 0;padding-top:1.4rem;'
            'border-top:1px solid var(--line);color:var(--muted);font-size:.92rem">'
            'Something missing from this tool, or a number that looks wrong? '
            '<a href="/suggest.html?from=%s">Tell me</a> and it gets read.</p>\n%s'
            % (START, page, END))


def main():
    pages = sorted(os.path.basename(p) for p in glob.glob(os.path.join(SITE, "*.html")))
    targets = [p for p in pages if p not in SKIP]
    done, missing = [], []
    for p in targets:
        f = os.path.join(SITE, p)
        h = open(f, encoding="utf-8").read()
        h = re.sub(re.escape(START) + r"[\s\S]*?" + re.escape(END), "", h)
        if "</main>" not in h:
            missing.append(p)
            continue
        h = h.replace("</main>", block(p) + "</main>", 1)
        if h.count(START) != 1:
            print("  FAIL %s ended with %d ask lines" % (p, h.count(START)))
            return 1
        open(f, "w", encoding="utf-8").write(h)
        done.append(p)

    # the excluded pages must not carry it
    for p in SKIP:
        f = os.path.join(SITE, p)
        if os.path.exists(f) and START in open(f, encoding="utf-8").read():
            print("  FAIL %s is excluded but carries an ask line" % p)
            return 1

    print("  ask line on %d tool pages, %d pages deliberately skipped" % (len(done), len(SKIP)))
    if missing:
        print("  no <main>, left alone: %s" % ", ".join(missing))
    return 0


if __name__ == "__main__":
    sys.exit(main())
