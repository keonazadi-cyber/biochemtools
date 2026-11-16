#!/usr/bin/env python3
"""Homepage card pictures: each tool, photographed with an answer already on screen.

Keon was shown the same cards twice (the chart shown whole, and the tool with a
result visible) and picked the tool. See Vault/Biochemtools/Homepage Design Brief
2026-11-09.md and the site-polish skill.

How a picture is chosen, per page, with no hand-picked rectangles:

1. Find the page's LOUDEST RESULT: the largest-font number below the title. Tools
   open prefilled, so there always is one. This is the "one loudest element" rule
   applied by code.
2. Take the whole card that contains it.
3. Fit that card into the frame WITHOUT cropping it. A crop through the middle of a
   word reads as a broken image ("ross a membrane"), so the card is scaled to fit
   and padded with the page background instead.

Fallbacks, in order, when a page has no big number: the largest drawn chart
(canvas or svg), then the first real table (a Punnett square), then the first card
after the inputs. OVERRIDE names a selector for a page the rules get wrong.
Pages whose product IS a chart keep the chart (CHART_PAGES).

Needs the preview server (bct-preview, port 8911) serving a synced copy, because
the preview launcher cannot read ~/Desktop. Drives agent-browser, one page at a time.

    python3 tools/make_card_shots.py                 # every tool
    python3 tools/make_card_shots.py --only ph-calculator.html punnett-square-calculator.html
"""
import json
import os
import subprocess
import sys
import tempfile

from PIL import Image

HERE = os.path.dirname(os.path.abspath(__file__))
SITE = os.path.join(HERE, "..")
OUT = os.path.join(SITE, "previews")
BASE = "http://localhost:8911/"
TOOLS = os.path.join(HERE, "charts", "preview_tools.json")

CARD_W, CARD_H = 760, 440
PAD = 22                           # page background around the fitted card, px
BG = (14, 12, 10)                  # --bg

# The product IS the chart on these, so the card shows the chart, whole.
CHART_PAGES = {
    "amino-acid-chart.html": "amino-acid-chart",
    "codon-chart.html": "genetic-code-chart",
    "biochem-equation-sheet.html": "biochem-equation-chart",
}

# Pages the rules cannot read, set after looking at the full contact sheet.
#   loud:  the element that IS the answer, when it is not a number
#   click: buttons to press first, for explorers that open at step 0
OVERRIDE = {
    "quiz.html": {"loud": "#ask"},
    "blood-type-calculator.html": {"loud": "div.bt"},
    "empirical-formula-calculator.html": {"loud": "#empOut"},
    "x-linked-inheritance-calculator.html": {"loud": "#dOut"},
    "dna-to-protein-translation.html": {"loud": "#protein"},
    "limiting-reagent-calculator.html": {"loud": "#outBox"},
    "buffer-pka-table.html": {"loud": "#best"},
    # the whole result card (square plus both ratio tables) shrank the square;
    # it is the second-busiest tool, so show the square alone, large
    "punnett-square-calculator.html": {"loud": "table", "grow": False},
    # The glycolysis and citric acid explorers open at step 0 with every tally at
    # zero, which breaks the tools-open-prefilled rule (flagged, not changed).
    "glycolysis-pathway-explorer.html": {"click": ["#all"]},
    # "Show all" here expands the steps without running the tallies, unlike the
    # glycolysis page, so step through all eight instead.
    "citric-acid-cycle-explorer.html": {"click": ["#next"] * 8, "loud": "#tNADH", "grow": False},
    # explorers shown in their most telling state rather than the default
    "gene-expression-regulation-explorer.html": {"text": ["Glucose absent", "Lactose present"],
                                                 "loud": "#lacWork"},
    "membrane-transport-explorer.html": {"text": ["Primary active"], "loud": "#modes"},
    "amino-acid-catabolism-explorer.html": {"click": ["#aaGrid button:nth-of-type(10)"],
                                            "loud": "#aaGrid"},
    # the practice worksheet is blank by design; show the answered version
    "punnett-square-practice-problems.html": {"click": ["#toggle"]},
}

FIND_JS = r"""
(() => {
  const CFG = %s;
  const st = document.createElement('style');
  st.textContent = '#bct-share-btn,#tool-streak-badge,.topnav,#recommended-slot,' +
                   '.tools-tried,[class*=streak]{display:none!important}';
  document.head.appendChild(st);
  // A sticky bar (the citric explorer's tally) overlaps whatever scrolls under it
  // in a full-page capture. Put every sticky element back in normal flow.
  for (const el of document.querySelectorAll('body *'))
    if (getComputedStyle(el).position === 'sticky') el.style.position = 'static';
  const vis = el => { const r = el.getBoundingClientRect(), cs = getComputedStyle(el);
    return r.width > 0 && r.height > 0 && cs.display !== 'none' &&
           cs.visibility !== 'hidden' && +cs.opacity > 0.05; };
  const doc = el => { const r = el.getBoundingClientRect();
    return {x: r.left + scrollX, y: r.top + scrollY, w: r.width, h: r.height}; };
  const h1 = document.querySelector('h1');
  const floor = h1 ? doc(h1).y + doc(h1).h : 0;
  const bodyBg = getComputedStyle(document.body).backgroundColor;
  const isCard = el => { const cs = getComputedStyle(el), r = el.getBoundingClientRect();
    const bg = cs.backgroundColor;
    const filled = bg && bg !== 'rgba(0, 0, 0, 0)' && bg !== 'transparent' && bg !== bodyBg;
    const edged = parseFloat(cs.borderTopWidth) > 0 && cs.borderTopStyle !== 'none';
    return (filled || edged) && r.width >= 320 && r.height >= 110; };
  const cardOf = el => { let e = el.parentElement, best = null;
    while (e && e !== document.body) {
      if (isCard(e)) { best = e; if (e.getBoundingClientRect().height >= 150) break; }
      e = e.parentElement; }
    return best; };
  // the row of answer tiles around a result: widest ancestor still under 340px tall
  const groupOf = el => { let e = el, best = el;
    while (e && e !== document.body) { const r = e.getBoundingClientRect();
      if (r.height > 340) break; if (r.width >= 380) best = e; e = e.parentElement; }
    return best; };

  // the largest drawn chart below the title
  let chart = null, area = 0;
  for (const el of document.querySelectorAll('canvas, svg')) {
    if (!vis(el) || doc(el).y < floor || el.closest('a,button,nav,header')) continue;
    const r = el.getBoundingClientRect(), a = r.width * r.height;
    if (r.width >= 240 && a > area) { area = a; chart = el; }
  }

  // the loudest answer: named by OVERRIDE, else the largest-font number. A short
  // label in front ("pH 2.87") and scientific notation ("1.000e-4 M") both count.
  let loud = CFG.loud ? document.querySelector(CFG.loud) : null, size = loud ? 99 : 0;
  const NUM = /^(?:[A-Za-z]{1,4}\s*=?\s*)?[+\-−]?\d[\d.,]*(?:e[+\-−]?\d+)?\s*(%%|mM|µM|uM|nM|M|kDa|Da|g\/mol|g|mg|mL|µL|L|ATP|mmHg|°C|K|min|s|bp|atm|V|Osm|mmol|kJ\/mol|ng\/µL)?$/i;
  if (!loud) for (const el of document.querySelectorAll('body *')) {
    if (/^(H1|H2|SCRIPT|STYLE|OPTION|BUTTON|INPUT|TEXTAREA|LABEL|A|TH|TD)$/.test(el.tagName)) continue;
    const own = [...el.childNodes].filter(n => n.nodeType === 3).map(n => n.textContent.trim()).join('');
    if (!own || !NUM.test(own) || !vis(el) || doc(el).y < floor) continue;
    const fs = parseFloat(getComputedStyle(el).fontSize);
    if (fs > size) { size = fs; loud = el; }
  }

  if (loud && size >= 22) {
    const card = cardOf(loud);
    // a compact result card is the best picture: big answer plus its working
    if (card && card.getBoundingClientRect().height <= 560)
      return JSON.stringify({kind: 'result ' + Math.round(size) + 'px', ...doc(card)});
    // too tall to read once shrunk: take the result band instead, the answer
    // tiles joined with the plot when one sits nearby, at full card width so
    // nothing is clipped at the sides and no edge cuts through a line
    const g = groupOf(loud), gd = doc(g), frame = doc(card || g);
    let top = gd.y, bot = gd.y + gd.h;
    if (chart) { const c = doc(chart);
      if (Math.abs(c.y - gd.y) < 800 && Math.max(bot, c.y + c.h) - Math.min(top, c.y) <= 900) {
        top = Math.min(top, c.y); bot = Math.max(bot, c.y + c.h); } }
    // A lone answer box in empty space reads as thin: the best cards are the
    // answer PLUS its working. So grow the band down through whole following
    // blocks (the worked steps) while it stays compact, never splitting one.
    let nxt = g.nextElementSibling;
    while (CFG.grow && nxt && bot - top < 300) {
      if (!vis(nxt)) { nxt = nxt.nextElementSibling; continue; }
      const nd = doc(nxt);
      if (nd.y + nd.h - top > 470) break;
      bot = nd.y + nd.h; nxt = nxt.nextElementSibling;
    }
    // Never start the picture partway through an element. A margin alone was not
    // enough: on the equilibrium page the inputs sit flush against the answer, so
    // the band sliced their bottom edge. Move the top below anything it would cut.
    // Only a SLIVER moves the edge: an element mostly above it, poking in. The
    // first version moved the edge past the wrapper around the enzyme plots and
    // deleted both charts, so anything holding the chart or the answer is exempt.
    top -= 5;
    for (const el of document.querySelectorAll('body *')) {
      if (!vis(el) || el.contains(g) || g.contains(el) || (chart && el.contains(chart))) continue;
      const d = doc(el);
      if (d.x + d.w < frame.x || d.x > frame.x + frame.w) continue;
      const poke = d.y + d.h - top;
      if (d.y < top && poke > 0 && poke < d.h * 0.5 && d.y + d.h <= gd.y + 1) top = d.y + d.h + 2;
    }
    return JSON.stringify({kind: 'band ' + Math.round(size) + 'px',
      x: frame.x, y: top, w: frame.w, h: bot - top + 16});
  }

  if (chart) { const c = cardOf(chart), cd = doc(chart);
    if (c && c.getBoundingClientRect().height <= 900) return JSON.stringify({kind: 'chart', ...doc(c)});
    const f = c ? doc(c) : cd;
    return JSON.stringify({kind: 'chart band', x: f.x, y: cd.y - 14, w: f.w, h: cd.h + 28}); }

  for (const t of document.querySelectorAll('table')) {
    if (!vis(t) || doc(t).y < floor || t.querySelectorAll('td').length < 6) continue;
    const c = cardOf(t) || t;
    if (c.getBoundingClientRect().height <= 900) return JSON.stringify({kind: 'table', ...doc(c)});
  }
  const cards = [...document.querySelectorAll('main *, body > *')].filter(e => isCard(e) &&
    doc(e).y >= floor && !isCard(e.parentElement || document.body));
  const pick = cards[1] || cards[0];
  if (pick) return JSON.stringify({kind: 'card', ...doc(pick)});
  return JSON.stringify({kind: 'none'});
})()
"""


def ab(*args, timeout=60):
    r = subprocess.run(["agent-browser", *args], capture_output=True, text=True, timeout=timeout)
    return r.stdout.strip()


def find_box(href):
    cfg = OVERRIDE.get(href, {})
    js = FIND_JS % json.dumps({"loud": cfg.get("loud"), "grow": cfg.get("grow", True)})
    raw = ab("eval", js).splitlines()[-1]
    val = json.loads(raw)
    return json.loads(val) if isinstance(val, str) else val


def trim_slivers(img):
    """Cut off a sliced element at the top or bottom edge, judged from pixels.

    Predicting slices from page structure failed three times on the equilibrium
    page. The picture itself is the reliable witness: a sliver is content that
    TOUCHES the edge and is followed by a blank gap. A real title has a margin
    above it, so it never touches the edge and is never trimmed.
    """
    g = img.convert("L")
    w, h = g.size
    px = g.load()

    def blank(y):
        vals = [px[x, y] for x in range(0, w, 4)]
        m = sum(vals) / len(vals)
        return (sum((v - m) ** 2 for v in vals) / len(vals)) ** .5 < 5

    top, reach = 0, int(h * .2)
    if not all(blank(y) for y in range(0, 3)):
        for y in range(3, reach):
            if all(blank(y + k) for k in range(4)):
                top = y
                break
    else:
        # a lone thin line (a neighbouring card's border) with margin above it
        first = next((y for y in range(reach) if not blank(y)), None)
        if first is not None:
            run = 0
            while first + run < reach and not blank(first + run):
                run += 1
            if run <= 4 and all(blank(first + run + k) for k in range(4)):
                top = first + run
    # Top only. Every real sliver has been at the top edge, and the answer box
    # usually sits at the bottom of a band: a bottom trim removed the oxygen
    # page's 93.5% answer as if it were a sliver.
    bot = h
    return img.crop((0, top, w, bot)) if (top or bot != h) else img


def fit(region):
    """Scale the whole card into the frame. Never crop it."""
    canvas = Image.new("RGB", (CARD_W, CARD_H), BG)
    room_w, room_h = CARD_W - 2 * PAD, CARD_H - 2 * PAD
    s = min(room_w / region.width, room_h / region.height)
    img = region.resize((max(1, int(region.width * s)), max(1, int(region.height * s))),
                        Image.LANCZOS)
    canvas.paste(img, ((CARD_W - img.width) // 2, (CARD_H - img.height) // 2))
    return canvas, s


def chart_card(plate):
    im = Image.open(os.path.join(SITE, "downloads", plate + ".png")).convert("RGB")
    h = int(im.width * (CARD_H - 2 * PAD) / (CARD_W - 2 * PAD))
    return fit(im.crop((0, 0, im.width, min(h, im.height))))[0]


def save(img, path):
    img.convert("P", palette=Image.ADAPTIVE, colors=128).save(path, optimize=True)
    return os.path.getsize(path)


def main(argv):
    tools = json.load(open(TOOLS))
    hrefs = [h for sec in tools.values() for h, _ in sec]
    if "--only" in argv:
        hrefs = argv[argv.index("--only") + 1:]
    os.makedirs(OUT, exist_ok=True)
    ab("set", "viewport", "1100", "900", "2")
    report, tmp = [], tempfile.mkdtemp()
    for href in hrefs:
        dest = os.path.join(OUT, href.replace(".html", ".png"))
        if href in CHART_PAGES:
            n = save(chart_card(CHART_PAGES[href]), dest)
            report.append((href, "chart page", "-", n))
            continue
        ab("open", BASE + href, timeout=90)
        ab("wait", "--load", "networkidle", timeout=60)
        ab("wait", "700")
        # Direct element clicks: agent-browser's click silently missed the citric
        # explorer's Next button (five clicks, still step 0), while el.click()
        # advanced it every time.
        for sel in OVERRIDE.get(href, {}).get("click", []):
            ab("eval", "document.querySelector(%s).click()" % json.dumps(sel))
            ab("wait", "250")
        for label in OVERRIDE.get(href, {}).get("text", []):
            ab("find", "text", label, "click")
            ab("wait", "500")
        box = find_box(href)
        if box.get("kind") == "none":
            report.append((href, "NOTHING FOUND", "-", 0))
            continue
        shot = os.path.join(tmp, "full.png")
        ab("screenshot", "--full", shot, timeout=90)
        full = Image.open(shot).convert("RGB")
        k = full.width / 1100.0                       # css px to image px (2 at retina)
        m = 10
        x0, y0 = max(0, (box["x"] - m) * k), max(0, (box["y"] - m) * k)
        x1 = min(full.width, (box["x"] + box["w"] + m) * k)
        y1 = min(full.height, (box["y"] + box["h"] + m) * k)
        card, s = fit(trim_slivers(full.crop((int(x0), int(y0), int(x1), int(y1)))))
        n = save(card, dest)
        report.append((href, box["kind"], "%.2f" % s, n))
    print("  %-48s %-16s %-6s %s" % ("page", "picked", "scale", "KB"))
    for href, kind, s, n in report:
        print("  %-48s %-16s %-6s %.0f" % (href, kind, s, n / 1000.0))
    bad = [r for r in report if r[1] == "NOTHING FOUND"]
    print("\n  %d pictures, %d with nothing found" % (len(report) - len(bad), len(bad)))
    return 1 if bad else 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
