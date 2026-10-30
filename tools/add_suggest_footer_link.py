#!/usr/bin/env python3
"""A link to the suggestions page in every footer.

The nav carries one and every tool page carries an ask line, but the policy pages
(about, privacy, license, contact) deliberately get no ask line, and the footer is
where someone who has read to the bottom of one of those is looking. Without this
there is no route to /suggest.html from those pages at all.

Footers differ page to page, so this appends rather than rewriting them, and it
removes its own previous insertion first so repeated runs do not stack.
"""
import os, re, glob, sys

SITE = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..")
START = "<!-- suggestfoot:start -->"
END = "<!-- suggestfoot:end -->"
LINK = (' %s &middot; <a href="/suggest.html" style="color:inherit;text-decoration:underline">'
        'Suggest a tool</a>%s' % (START, END))


def transform(h):
    """Remove whatever this script put here last time, then put it back.

    The leading \\s* is the whole point. LINK starts with a space, and a cleanup
    that matched only from START to END left that space behind, so every run
    added one more: eleven of them had piled up on each page before anyone
    looked. The assert in main() is what will catch the next version of this.
    """
    h = re.sub(r"\s*" + re.escape(START) + r"[\s\S]*?" + re.escape(END), "", h)
    h = re.sub(r"\s*&middot;\s*(?=</footer>)", "", h)   # tidy a trailing separator
    m = re.search(r"</footer>", h)
    if not m:
        return h, False
    return h[:m.start()] + LINK + h[m.start():], True


def main():
    done, nofooter = [], []
    for f in sorted(glob.glob(os.path.join(SITE, "*.html"))):
        name = os.path.basename(f)
        h = open(f, encoding="utf-8").read()
        h, had_footer = transform(h)
        if not had_footer:
            nofooter.append(name)
            open(f, "w", encoding="utf-8").write(h)
            continue
        if h.count(START) != 1:
            print("  FAIL %s ended with %d footer links" % (name, h.count(START)))
            return 1
        # Byte-identical on a second pass, or this script grows the page forever.
        again, _ = transform(h)
        if again != h:
            print("  FAIL %s is not idempotent: a second pass changes %d bytes"
                  % (name, abs(len(again) - len(h))))
            return 1
        open(f, "w", encoding="utf-8").write(h)
        done.append(name)

    print("  suggestions link in %d footers" % len(done))
    if nofooter:
        print("  no <footer>, skipped: %s" % ", ".join(nofooter))
    return 0


if __name__ == "__main__":
    sys.exit(main())
