#!/usr/bin/env python3
"""Publish the shared question bank and wire the training log into the pages.

quiz.html used to generate recall drills from the 20-row amino acid table.
Finite by construction: learn twenty codes and it is over, which is why it read
as too easy while still being the best-converting page on the site. The old
drill is kept, demoted below the new engine, because it works; it is just not
the whole quiz any more.

The bank ships as /questions.json rather than inlined, so the page stays light,
and a sample is rendered here at build time as plain <details> so the page is
not empty for a crawler or with JavaScript off.
"""
import collections, hashlib, html as H, json, pathlib, re, sys

SITE = pathlib.Path(__file__).resolve().parent.parent
BANKS = SITE / "tools" / "questions"
START, END = "<!-- quiz:start -->", "<!-- quiz:end -->"
JS_START, JS_END = "<!-- quizjs:start -->", "<!-- quizjs:end -->"

CSS = """<style>
.qwrap{border:1px solid var(--line);background:var(--card);border-radius:12px;padding:1.25rem;margin:1.5rem 0}
.q-head{display:flex;justify-content:space-between;font-size:.82rem;color:var(--muted);margin-bottom:.6rem;gap:1rem}
.q-row{display:flex;flex-wrap:wrap;gap:.4rem;align-items:center;margin-bottom:.6rem}
.q-lab{font-size:.78rem;color:var(--muted);text-transform:uppercase;letter-spacing:.06em;min-width:4.5rem}
.q-chip{padding:.5rem .8rem;min-height:44px;display:inline-flex;align-items:center;border:1px solid var(--line);border-radius:999px;background:transparent;color:var(--txt);font:inherit;font-size:.86rem;cursor:pointer}
.q-chip:hover{border-color:var(--accent)}
.q-chip.on{border-color:var(--accent);color:var(--accent)}
.q-frame{margin-left:auto;background:none;border:0;color:var(--muted);font:inherit;font-size:.78rem;text-decoration:underline;cursor:pointer}
.q-go{margin-top:.6rem;padding:.6rem 1rem;border:1px solid var(--accent);border-radius:8px;background:transparent;color:var(--accent);font:inherit;font-size:.95rem;cursor:pointer}
.q-go:disabled{opacity:.5;cursor:default}
.q-hint{color:var(--muted);font-size:.85rem;line-height:1.5;margin:.6rem 0 0}
.q-prog{height:3px;background:var(--line);border-radius:2px;overflow:hidden;margin-bottom:1rem}
.q-progfill{height:100%;background:var(--accent);transition:width .25s ease}
.q-q{margin:0 0 .9rem;font-size:1.02rem;line-height:1.45}
.q-opts{display:grid;gap:.5rem}
.q-opt{text-align:left;padding:.6rem .75rem;border:1px solid var(--line);border-radius:8px;background:transparent;color:var(--txt);font:inherit;font-size:.94rem;cursor:pointer}
.q-opt:hover:enabled{border-color:var(--accent)}
.q-opt:disabled{cursor:default;opacity:.75}
.q-opt.is-right{border-color:var(--accent2);color:var(--accent2);opacity:1}
.q-opt.is-wrong{border-color:var(--wrong);color:var(--wrong);opacity:1}
.q-why{margin-top:.8rem;font-size:.9rem;line-height:1.5;color:var(--muted);min-height:1.2em}
.q-why.is-right{color:var(--accent2)}
.q-why.is-wrong{color:var(--txt)}
.q-tool{color:var(--accent)}
.q-next{margin-top:.9rem;padding:.5rem .9rem;border:1px solid var(--accent);border-radius:8px;background:transparent;color:var(--accent);font:inherit;cursor:pointer}
.q-score{margin:.2rem 0 .3rem;font-size:1.6rem;color:var(--accent)}
.q-missed{margin-top:1rem}
.q-missed summary{cursor:pointer;padding:.45rem 0;font-size:.93rem}
.q-ans{color:var(--accent2);font-size:.9rem;margin:.1rem 0 .3rem}
.q-exp{color:var(--muted);font-size:.88rem;margin:0 0 .6rem}
.q-mastery{margin-top:1.4rem;padding-top:1rem;border-top:1px solid var(--line)}
.q-mastery h3{font-size:.95rem;margin:0 0 .7rem}
.q-mrow{display:flex;align-items:center;gap:.6rem;margin-bottom:.4rem}
.q-mname{font-size:.84rem;min-width:8.5rem;color:var(--muted)}
.q-mbar{position:relative;flex:1;height:8px;background:var(--line);border-radius:4px;overflow:hidden}
.q-mmet{position:absolute;inset:0 auto 0 0;background:var(--line);filter:brightness(1.6)}
.q-mfill{position:absolute;inset:0 auto 0 0;background:var(--accent2)}
.q-mpct{font-size:.8rem;color:var(--muted);min-width:2.6rem;text-align:right}
.q-fallback summary{cursor:pointer;padding:.45rem 0;font-size:.93rem}
@media (max-width:460px){.qwrap{padding:1rem}.q-lab{min-width:100%}.q-mname{min-width:6.5rem;font-size:.8rem}}
</style>"""


def load():
    banks, subjects = [], []
    for f in sorted(BANKS.glob("*.json")):
        d = json.loads(f.read_text())
        subj = d["subject"]
        subjects.append(subj)
        for q in d["questions"]:
            q = dict(q)
            q["subject"] = subj
            banks.append(q)
    return banks, subjects


def fallback(bank):
    """What a crawler and a no-JavaScript visitor read: real question and answer
    text, one per subject per level, so the page is never an empty box."""
    picked, seen = [], set()
    for q in bank:
        k = (q["subject"], q["type"])
        if k not in seen:
            seen.add(k); picked.append(q)
    out = ['<div class="q-fallback">']
    for q in picked[:21]:
        out.append("<details><summary>%s</summary>" % H.escape(q["q"]))
        out.append('<p class="q-ans">%s</p>' % H.escape(q["choices"][q["correct"]]))
        out.append('<p class="q-exp">%s</p>' % H.escape(q["explain"]))
        out.append("</details>")
    out.append("</div>")
    return "".join(out)


def strip(h):
    h = re.sub(r"\s*" + re.escape(START) + r"[\s\S]*?" + re.escape(END), "", h)
    h = re.sub(r"\s*" + re.escape(JS_START) + r"[\s\S]*?" + re.escape(JS_END), "", h)
    h = re.sub(r"\s*<style>\s*\.qwrap\{[\s\S]*?</style>", "", h)
    return h


PRACTICE_MAIN = """<main>
<header class="hero">
<h1>Biochem Practice Questions: Easy, Medium and Hard</h1>
<p>Pick a level and a subject, or mix every subject together. Practice mode
gives you the reason straight away; practice test mode holds it back until the
end, the way the real thing does. Anything you miss comes back first next time.
Free, no account, and your progress stays in your own browser.</p>
</header>
</main>"""


def make_practice_page():
    """Build practice.html from quiz.html's chrome, so it inherits the nav,
    the footer, the analytics and the styling without a second copy of any."""
    src = (SITE / "quiz.html").read_text()
    out = SITE / "practice.html"
    if out.exists():
        return                       # already built; the block logic updates it
    head = src.split("</head>")[0]
    head = re.sub(r"<title>[\s\S]*?</title>",
                  "<title>Biochem Practice Questions: Easy, Medium, Hard</title>",
                  head, count=1)
    head = re.sub(r'(<meta name="description" content=")[^"]*(")',
                  r"\1Free biochem practice questions at three levels across seven "
                  r"subjects, with a mixed mode and practice tests. Every answer "
                  r"explained, progress kept in your browser.\2", head, count=1)
    head = re.sub(r'(<link rel="canonical" href=")[^"]*(")',
                  r"\1https://biochemtools.com/practice.html\2", head, count=1)
    head = re.sub(r"<script type=\"application/ld\+json\">[\s\S]*?</script>", "", head)
    tail = src.split("</main>", 1)[1] if "</main>" in src else "</body></html>"
    out.write_text(head + "</head>\n<body>\n" + PRACTICE_MAIN + tail)
    print("  created practice.html from quiz.html's chrome")


def main():
    if not BANKS.exists():
        print("  no question banks yet"); return 0
    bank, subjects = load()
    if not bank:
        print("  FAIL banks are empty"); return 1

    for name in ("quiz-engine.js", "quiz-ui.js"):
        if not (SITE / name).exists():
            print("  FAIL %s is missing" % name); return 1
    ver = hashlib.sha1(
        (SITE / "quiz-engine.js").read_bytes()
        + (SITE / "quiz-ui.js").read_bytes()).hexdigest()[:8]

    slim = [{"id": q["id"], "subject": q["subject"], "type": q["type"],
             "q": q["q"], "choices": q["choices"], "correct": q["correct"],
             "explain": q["explain"], "tool": q.get("tool", "")}
            for q in bank]
    payload = json.dumps({"subjects": subjects, "questions": slim},
                         separators=(",", ":"), ensure_ascii=False)
    (SITE / "questions.json").write_text(payload)

    dist = collections.Counter(q["type"] for q in bank)
    block = (START
             + '<section class="qwrap" data-quiz>'
             + fallback(bank)
             + "</section>" + END)
    tag = ('%s<script src="/quiz-engine.js?v=%s" defer></script>'
           '<script src="/quiz-ui.js?v=%s" defer></script>%s'
           % (JS_START, ver, ver, JS_END))

    # The training log gets its OWN page. quiz.html ranks at position 5.28 for
    # "amino acid quiz" with the site's second-best CTR, and turning it into a
    # general seven-subject engine would dilute the topic that earns that. The
    # amino acid drill stays exactly where it is and links here instead.
    make_practice_page()

    # quiz.html carried this block during an earlier design. Remove any trace,
    # and give it a contextual link to the practice page instead: it keeps its
    # ranking topic and sends its traffic somewhere deeper.
    qp = SITE / "quiz.html"
    qh = before = qp.read_text()
    qh = strip(qh)
    link = ('%s<p class="note">Past the twenty codes? '
            '<a href="/practice.html">Biochem practice questions</a> go three '
            'levels deep across seven subjects, with practice tests.</p>%s'
            % (START, END))
    if START not in qh:
        m = re.search(r"</header>", qh)
        if m:
            qh = qh[:m.end()] + "\n" + link + qh[m.end():]
    if qh != before:
        qp.write_text(qh)
        print("  quiz.html: engine removed, link to practice.html added")

    wrote = 0
    for page in ("practice.html",):
        p = SITE / page
        h = original = p.read_text()
        h = strip(h)
        # After the hero, not after <main>. Injecting at the top of <main> put
        # the quiz above the h1, so the page opened with a question and no
        # explanation of what it was, with the heading buried underneath.
        m = re.search(r"</header>", h) or re.search(r"<main[^>]*>", h)
        if not m:
            print("  FAIL %s has no <header> or <main>" % page); return 1
        h = h[:m.end()] + "\n" + block + h[m.end():]
        h = h.replace("</head>", CSS + "\n</head>", 1)
        if tag not in h:
            h = h.replace("</body>", tag + "\n</body>", 1)
        if h.count(START) != 1 or h.count(JS_START) != 1:
            print("  FAIL %s ended with %d blocks" % (page, h.count(START))); return 1
        if h != original:
            p.write_text(h); wrote += 1

    print("  questions.json: %d questions, %d subjects (Easy %d, Medium %d, Hard %d)"
          % (len(bank), len(subjects), dist["recall"], dist["apply"], dist["exam"]))
    print("  training log on %d page(s), engine v%s" % (wrote, ver))
    return 0


if __name__ == "__main__":
    sys.exit(main())
