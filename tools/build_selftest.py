#!/usr/bin/env python3
"""Put a self-test on the pages that rank but do not get clicked.

Measured 2026-10-29 on Bing, where the whole site sits at position 5 to 7 so
ranking is near enough held constant:

    quiz.html                              6.66% CTR
    nucleic-acid-concentration-calculator  2.05%
    amino-acid-chart                       0.73%
    codon-chart                            0.06%

The variable is whether you have to come to the page to get the thing. A chart in
a search result IS the answer; a test is not. So each of these pages gets a short
test built from its own data, and a title that promises the testing.

The test is rendered here, at build time, as plain <details> elements: it works
with no JavaScript, and a crawler reads real question and answer text rather than
an empty div. selftest.js only upgrades it into one-at-a-time with a commit.

Idempotent: everything this writes sits between markers and is removed before
being rewritten, including the whitespace in front of it.
"""
import hashlib, html as H, json, pathlib, re, sys

SITE = pathlib.Path(__file__).resolve().parent.parent
BANKS = SITE / "tools" / "selftest"
START, END = "<!-- selftest:start -->", "<!-- selftest:end -->"
JS_START, JS_END = "<!-- selftestjs:start -->", "<!-- selftestjs:end -->"

CSS = """<style>
.selftest{border:1px solid var(--line);background:var(--card);border-radius:12px;
  padding:1.25rem;margin:1.5rem 0}
.selftest>h2{margin:0 0 .35rem;font-size:1.05rem}
.selftest>p.st-intro{margin:0 0 1rem;color:var(--muted);font-size:.92rem}
.st-head{display:flex;justify-content:space-between;font-size:.82rem;
  color:var(--muted);margin-bottom:.5rem}
.st-bar{height:3px;background:var(--line);border-radius:2px;overflow:hidden;
  margin-bottom:1rem}
.st-fill{height:100%;width:0;background:var(--accent);transition:width .25s ease}
.st-q{margin:0 0 .9rem;font-size:1.02rem;line-height:1.45}
.st-opts{display:grid;gap:.5rem}
.st-opt{text-align:left;padding:.6rem .75rem;border:1px solid var(--line);
  border-radius:8px;background:transparent;color:var(--txt);font:inherit;
  font-size:.94rem;cursor:pointer}
.st-opt:hover:enabled{border-color:var(--accent)}
.st-opt:disabled{cursor:default;opacity:.75}
.st-opt.is-right{border-color:var(--accent2);color:var(--accent2);opacity:1}
.st-opt.is-wrong{border-color:var(--wrong);color:var(--wrong);opacity:1}
.st-why{margin-top:.8rem;font-size:.9rem;line-height:1.5;color:var(--muted);
  min-height:1.2em}
.st-why.is-right{color:var(--accent2)}
.st-why.is-wrong{color:var(--txt)}
.st-foot{margin-top:.9rem}
.st-next{padding:.5rem .9rem;border:1px solid var(--accent);border-radius:8px;
  background:transparent;color:var(--accent);font:inherit;font-size:.9rem;
  cursor:pointer}
.st-fallback summary{cursor:pointer;padding:.45rem 0;font-size:.94rem}
.st-fallback .st-ans{color:var(--accent2);font-size:.9rem;margin:.1rem 0 .6rem}
.st-fallback .st-exp{color:var(--muted);font-size:.88rem;margin:0 0 .8rem}
@media (max-width:420px){.selftest{padding:1rem}.st-q{font-size:.98rem}}
</style>"""


def fallback(bank):
    """The no-JavaScript version, and what a crawler reads."""
    out = ['<div class="st-fallback">']
    for item in bank["questions"]:
        out.append("<details><summary>%s</summary>" % H.escape(item["q"]))
        out.append('<p class="st-ans">%s</p>'
                   % H.escape(item["options"][item["answer"]]))
        out.append('<p class="st-exp">%s</p>' % H.escape(item["why"]))
        out.append("</details>")
    out.append("</div>")
    return "".join(out)


def block(bank, js_version):
    payload = H.escape(json.dumps(
        [{"q": q["q"], "options": q["options"], "answer": q["answer"],
          "why": q["why"]} for q in bank["questions"]],
        separators=(",", ":"), ensure_ascii=False), quote=True)
    return (
        START
        + '<section class="selftest">'
        + "<h2>%s</h2>" % H.escape(bank.get("heading", "Before you scroll"))
        + '<p class="st-intro">%s</p>' % H.escape(bank["intro"])
        # Only this inner region is replaced when the script runs, so the heading
        # and the sentence explaining what this is survive the upgrade. The first
        # version put data-selftest on the <section> and the script wiped both,
        # which left a quiz appearing out of nowhere with no explanation.
        + '<div class="st-live" data-selftest="%s">' % payload
        + fallback(bank)
        + "</div></section>"
        + END
    )


def strip(h):
    h = re.sub(r"\s*" + re.escape(START) + r"[\s\S]*?" + re.escape(END), "", h)
    h = re.sub(r"\s*" + re.escape(JS_START) + r"[\s\S]*?" + re.escape(JS_END), "", h)
    h = re.sub(r"\s*<style>\s*\.selftest\{[\s\S]*?</style>", "", h)
    return h


def set_meta(h, title, desc, report, name):
    t = re.search(r"<title>([\s\S]*?)</title>", h)
    if t and t.group(1).strip() != title:
        h = h[:t.start(1)] + H.escape(title, quote=False) + h[t.end(1):]
        report.append((name, "title"))
    d = re.search(r'(<meta name="description" content=")([^"]*)(")', h)
    if d and d.group(2) != desc:
        h = h[:d.start(2)] + H.escape(desc, quote=True) + h[d.end(2):]
        report.append((name, "description"))
    return h


def main():
    if not BANKS.exists():
        print("  no tools/selftest/ yet, nothing to build")
        return 0
    js = SITE / "selftest.js"
    if not js.exists():
        print("  FAIL selftest.js is missing")
        return 1
    ver = hashlib.sha1(js.read_bytes()).hexdigest()[:8]
    tag = ('%s<script src="/selftest.js?v=%s" defer></script>%s'
           % (JS_START, ver, JS_END))

    report, wrote = [], 0
    for bank_file in sorted(BANKS.glob("*.json")):
        bank = json.loads(bank_file.read_text())
        page = SITE / (bank["slug"] + ".html")
        if not page.exists():
            print("  FAIL %s has no page %s" % (bank_file.name, page.name))
            return 1
        for key in ("title", "description", "intro", "questions"):
            if not bank.get(key):
                print("  FAIL %s is missing %r" % (bank_file.name, key))
                return 1
        if len(bank["title"]) > 60:
            print("  FAIL %s title is %d chars, over 60"
                  % (bank_file.name, len(bank["title"])))
            return 1
        for field in (bank["title"], bank["description"], bank["intro"]):
            if "—" in field or "–" in field:
                print("  FAIL %s uses a dash that is banned on this site"
                      % bank_file.name)
                return 1

        h = original = page.read_text()
        h = strip(h)
        h = set_meta(h, bank["title"], bank["description"], report, page.name)

        # the test goes directly after the page's opening <main>, above the chart
        m = re.search(r"<main[^>]*>", h)
        if not m:
            print("  FAIL %s has no <main>" % page.name)
            return 1
        h = h[:m.end()] + "\n" + block(bank, ver) + h[m.end():]
        h = h.replace("</head>", CSS + "\n</head>", 1)
        if tag not in h:
            h = h.replace("</body>", tag + "\n</body>", 1)

        if h.count(START) != 1 or h.count(JS_START) != 1:
            print("  FAIL %s ended with %d tests and %d script tags"
                  % (page.name, h.count(START), h.count(JS_START)))
            return 1
        if h != original:
            page.write_text(h)
            wrote += 1
            report.append((page.name, "%d questions" % len(bank["questions"])))

    seen = {}
    for name, what in report:
        seen.setdefault(name, []).append(what)
    for name in sorted(seen):
        print("  %-46s %s" % (name, ", ".join(seen[name])))
    print("  self-test on %d page(s), selftest.js v%s" % (wrote, ver))
    return 0


if __name__ == "__main__":
    sys.exit(main())
