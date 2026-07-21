# Biochemtools Growth Roadmap

Living doc: rating, priorities, and a dated notes log so work never gets lost
between sessions. Update this file whenever a growth/monetization task is
worked on — add a dated entry to the Notes Log at the bottom, and move items
between Done / In Progress / Not Started as they change state.

## Rating snapshot (2026-07-21, re-audit)

**8.5/10 as an ad-revenue-ready asset** (up from 6.5/10 on 2026-07-20 —
original punch list fully closed). Verified fresh: all 20 tool pages
600-900 words, zero broken internal links, zero invalid JSON-LD, every
page has exactly one H1, all canonicals correct, favicon/og:image/
analytics on every page that needs them. New finding this pass (fixed
same day): title tags and meta descriptions were running long (titles
68-100 chars vs. Google's ~50-60 display limit, descriptions 162-268
chars vs. ~155-160) — rewrote all 21 to fit, keeping og:title/
og:description (used for the social preview images) untouched. What's
keeping this from 9-10: no real traffic yet to prove any of it converts.

## Rating snapshot (2026-07-20, original)

**6.5/10 as an ad-revenue-ready asset → target 8.5/10.**

Strengths: zero-dependency single-file pages (fast, great Core Web Vitals),
real differentiation ("shows the work" vs. bare calculators), schema markup
on most pages, clean cross-linking between all tools.

Weaknesses at time of rating: no Privacy/About/Contact pages (blocks AdSense
outright), no favicon, thin per-page content (270-390 words), no analytics,
no social preview image, no ads.txt (not urgent yet).

## Priority list

1. **[DONE 2026-07-20]** Privacy Policy, About, Contact pages + favicon +
   footer links site-wide. Unblocks ad-network application.
2. **[DONE 2026-07-21]** Content depth — worked numeric example + FAQ block
   on all 20/20 tool pages (270-390 words → 600-900 words each).
3. **[DONE 2026-07-21]** Cloudflare Web Analytics — manual JS snippet on
   all 24 pages (the auto-inject "Enable Globally" option doesn't work
   since DNS is unproxied; used "Enable with JS Snippet installation").
4. **[DONE 2026-07-21]** Proper social preview image (og:image), 1200×630
   landscape, one per tool + homepage (21 total), generated from each
   page's own og:title/og:description so there's one source of truth.
   og:image/twitter:card meta wired into all 21 pages. See commit 426c287.
   pipeline, not a reuse of the pin assets.
5. **[NOT STARTED, LOW URGENCY]** ads.txt — add the day an ad network
   (e.g. AdSense) is actually signed up for. Five-minute task, don't do it
   before there's a publisher ID to put in it.

## Which pages are indexed right now (as of 2026-07-20 check)

Google was showing 7 of 21 pages in search results (up from 2 on
2026-07-04): index, peptide-charge-calculator, osmotic-pressure-calculator,
serial-dilution-calculator, michaelis-menten-fitter,
hardy-weinberg-calculator, beer-lambert-calculator. These are the pages
prioritized first for the content-depth pass, since they already have some
visibility to reinforce.

## Notes Log

### 2026-07-20 — Canonical tag bug fix
Found and fixed 4 tool pages (peptide-charge-calculator, enzyme-kinetics-
simulator, henderson-hasselbalch-buffer-calculator, glycolysis-pathway-
explorer) with leftover `example.com` placeholder canonical tags and
internal "related tool" links, left over from an unedited template. Fixed
and pushed (commit 742043f). This was suppressing indexing on those 4 pages
independent of the Search Console "page with redirect" issue that prompted
the check.

### 2026-07-20 — Trust/policy pages + full site audit
Full site audit against real ad-revenue-site criteria (see rating above).
Added about.html, privacy.html, contact.html, site-wide favicon (was
missing entirely), and footer links to all three on every page. Pushed
(commit 8108ce0). Sitemap updated to include the 3 new pages.

### 2026-07-20 — Content depth pass, batch 1 (3 of 6 done)
Added a "worked example" section + FAQ block (with FAQPage schema) to 3
pages. Method: computed every number in Python first using the exact same
formula as the page's own JS, then wrote it into the page, then loaded the
page in a local browser and confirmed the live tool output matched the
written example word-for-word before moving on. Word counts went from
~270-390 to 717-760 per page — solidly in the 600-900 target range.
Pushed (commit — see git log after this entry). Progress:
- [x] peptide-charge-calculator.html — worked pI of DKHEYR (pI≈7.49, net
      charge +0.08 at pH 7), 4 FAQs. 343→753 words.
- [x] michaelis-menten-fitter.html — worked Lineweaver-Burk regression on
      the default 6-point dataset (Vmax=96.3, Km=1.81, R²=0.9992), 4 FAQs.
      365→717 words.
- [x] hardy-weinberg-calculator.html — two contrasting worked examples
      (one population in equilibrium, χ²=0; one that fails, χ²=20.0 vs
      critical 3.84), 4 FAQs. 325→760 words.
- [x] beer-lambert-calculator.html — unknown-concentration example (default
      values, c=1.00e-4 M) + a real NADH-at-340nm assay example (A=0.311,
      the classic LDH-assay wavelength) + absorbance/%T round-trip,
      4 FAQs. 277→683 words.
- [x] osmotic-pressure-calculator.html — 0.15 M NaCl at 37°C (default,
      π=7.635 atm, exactly isotonic — that's why it's the default) + 0.05 M
      CaCl₂ at 25°C (hypotonic contrast, π=3.670 atm), 4 FAQs. 328→705 words.
- [x] serial-dilution-calculator.html — the default 6-tube 10-fold series
      table + a real microbiology use case (diluting 1e9 CFU/mL down to a
      countable 30-300 colony plate), 4 FAQs. 289→696 words.

**Batch 1 complete: all 6 of the currently-indexed pages now have deepened
content.** Every number in every example was computed independently in
Python, then cross-checked against the live tool in a local browser before
publishing — zero unverified numbers went out.

### 2026-07-20 — Content depth pass, batch 2 (3 more done, not-yet-indexed)
Moved on to 3 of the remaining 14 not-yet-indexed pages, same verified
method throughout:
- [x] ph-calculator.html — strong acid default (pH 1.00) + weak acid
      (acetic acid, pKa 4.76, pH 2.88) + a third example specifically
      chosen to show where the √(Ka·C) approximation breaks down (0.21 pH
      unit error at 61.8% dissociation), 4 FAQs. 284→737 words.
- [x] gibbs-free-energy-calculator.html — default ΔH/ΔS/T example
      (ΔG=−10.19 kJ/mol, crossover 400 K) + ATP hydrolysis in a cell
      (ΔG°′=−30.5 kJ/mol default, actual ΔG=−42.37 kJ/mol via RT ln Q, a
      real illustration of why "unfavorable" ΔG°′ reactions still run in
      vivo), 4 FAQs. 321→792 words.
- [x] dilution-calculator.html — default C1V1=C2V2 example (V1=10 mL) + a
      real NaOH titration-prep example (V1=40 mL from 5 M stock), 4 FAQs
      including the common misconception about mixing two solutions vs.
      diluting with pure solvent. 288→649 words.

9 of 20 tool pages now have deepened content.

### 2026-07-20 — Content depth pass, batch 3 (3 more done)
- [x] enzyme-kinetics-simulator.html — side-by-side competitive vs.
      noncompetitive worked example at identical inhibitor concentration
      (r=1), showing why they diverge (Km(app) 50 vs 25, Vmax(app) 100 vs
      50, v 33.33 vs 25.00), 4 FAQs (already had HowTo schema; added new
      FAQPage schema). 390→754 words.
- [x] henderson-hasselbalch-buffer-calculator.html — default phosphate
      buffer at pH 7.40 (30.4/19.6 mmol) + a contrasting "bad pKa match"
      example (acetate at the same target pH, 99.77%/0.23% split,
      demonstrating numerically why it fails), 4 FAQs. 319→789 words.
- [x] glycolysis-pathway-explorer.html — cumulative step-by-step ATP/NADH
      tally table (verified against the page's own STEPS array), reaching
      the same +2 ATP/2 NADH/2 pyruvate the live tool shows on "Show all".
      This page already had a 2-question FAQPage schema with no matching
      visible content — expanded to 4 questions AND added a visible FAQ
      section so the schema now matches on-page content. 279→629 words.

12 of 20 tool pages now have deepened content.

### 2026-07-20 — Content depth pass, batch 4 (3 more done)
- [x] nernst-equation-calculator.html — default Daniell cell example
      (E=1.1887V, verified full RT/nF form against the 0.0592/n shortcut)
      + a concentration-cell example (E°=0 but E=+0.0887V from
      concentration difference alone, tied to resting membrane potential),
      4 FAQs. 277→734 words.
- [x] ideal-gas-law-calculator.html — STP sanity check (1 mol, 22.4 L →
      1.0007 atm, confirms the textbook number) + a body-temperature
      volume example (0.5 mol at 37°C → 12.725 L, explicitly contrasted
      against the common "just halve 22.4 L" mistake), 4 FAQs. 272→652
      words.
- [x] molarity-molar-mass-calculator.html — default glucose example
      (180.16 g/mol, 22.520 g) + a Ca(OH)2 example exercising the
      parenthesis/multiplier parser (74.09 g/mol, 1.482 g), 4 FAQs
      including a hydration-vs-anhydrous gotcha. 278→666 words.

15 of 20 tool pages now have deepened content.

### 2026-07-21 — Content depth pass, batch 5 (3 more done)
- [x] punnett-square-calculator.html — default AaBb×AaBb dihybrid cross
      (verified 9 genotype classes summing to 16, 9:3:3:1 phenotype) + a
      test-cross example (Aa×aa, 1:1 split, tied to why test crosses are
      used to reveal unknown genotypes), 4 FAQs. 287→690 words.
- [x] amino-acid-titration-curve.html — glycine's simple 2-pKa average
      (pI=5.97) + histidine's 3-pKa case showing you can't average all
      three pKas, only the two that flank the neutral species (pI=7.59,
      not the naive 3-pKa average of 5.66), 4 FAQs. 349→770 words.
- [x] dna-melting-temperature-calculator.html — default 20-mer primer
      (long-sequence formula, Tm=55.9°C) + a short palindromic primer
      example (ATGCAT, Wallace rule, Tm=16°C) that's also the real NsiI
      restriction site, tying reverse-complement-equals-self to why
      restriction enzymes recognize palindromes, 4 FAQs. 341→692 words.

18 of 20 tool pages now have deepened content.

### 2026-07-21 — Content depth pass COMPLETE (final 2 pages)
- [x] dna-to-protein-translation.html — default sequence (frame 1, Met-
      Ala-Leu-His-Stop) + a "find the ORF" example that explicitly
      contrasts the tool's full-frame display against the real biological
      protein (only from the highlighted AUG onward), 4 FAQs. 349→777
      words.
- [x] quiz.html — not a calculator, so instead of a numeric worked
      example: a verified class-breakdown table (7 nonpolar/3 aromatic/5
      polar/3 basic/2 acidic = 20, counted directly from the quiz's own
      AA array) + a table of the 9 one-letter codes that don't match the
      first letter of the name, with the reason for each (letter already
      taken by another amino acid), 4 FAQs. Also added FAQPage schema —
      this page had none before. 282→704 words.

**ALL 20 of 20 tool pages now have deepened content.** The content-depth
pass (priority #2 in the list above) is done. Every single number/example
added across all 20 pages, in every batch, was independently computed
(mostly in Python, matched against each page's own JS logic) and then
verified against the live tool in a browser before publishing — nothing
went out unchecked.

## What's left overall (as of 2026-07-21)

1. Content-depth pass: **DONE** (20/20 pages).
2. **[DONE 2026-07-21]** Cloudflare Web Analytics. The zone's "Enable
   Globally" auto-inject option doesn't work here since DNS is
   intentionally unproxied (DNS-only, for GitHub Pages cert reasons) —
   Cloudflare's edge never sees the traffic to auto-inject a beacon.
   Used "Enable with JS Snippet installation" instead to get a manual
   token, added the beacon script to all 24 pages (commit 0e7edd9). Give
   it a few days of traffic, then check Cloudflare dashboard → Web
   Analytics for real page-view/visit data per URL.
3. og:image: **DONE** (see above, commit 426c287).
4. ads.txt: still correctly deferred until an ad network is actually
   signed up for.
5. Pinterest: pins 04-06 due for posting, keep the ~2-3/week cadence.
6. Once there's real traffic (via Search Console/Analytics), the next
   growth lever is applying for AdSense/an ad network — the site is
   trust-page-ready for that now (privacy policy, about, contact all
   exist).

### 2026-07-21 — og:image project complete
Built a small PIL-based generator (script not checked into the repo,
lived in scratchpad) producing a branded 1200×630 dark-theme image per
tool page + homepage, with a category-colored accent pill, title, and
description pulled directly from each page's own og:title/og:description
meta tags (no separately-authored copy to drift out of sync). Images live
in `og-images/` in the repo (~1MB total, 21 files, 40-55KB each). Wired
og:image, og:image:width/height, and twitter:card (summary_large_image)
into all 21 pages. About/privacy/contact were skipped (no og:title to
source from, low share-likelihood).

**With this, every item on the original growth-rating punch list is
either done or intentionally deferred (ads.txt, until there's an ad
network to put in it).** Remaining work going forward is Keon's Pinterest
cadence, watching Analytics once traffic accumulates, and eventually the
AdSense application once there's enough traffic to make it worthwhile.

### 2026-07-21 — "how do I actually get to $10k/mo" 3-part plan

Reality check first: display-ad RPM in the study/edu niche runs roughly
$5-15. To hit $10k/mo on ads alone requires ~700k-2M monthly pageviews —
not realistic off 20 calculator pages even ranking well. Real leverage
is (1) a reason to come back daily, (2) higher-yield monetization than
banner ads, (3) an ad-ready layout for whenever there is enough traffic
to apply. Did all three:

**1. Landing page redesign (commit bfcb1a5).** Restructured index.html
from a single centered column to content+sidebar (the sidebar has a
reserved ad slot div, `#sidebar-ad-slot`, ready for whenever AdSense is
live). Added live client-side search/filter, a jump-to-category nav,
category-colored left borders on every tool card, and a homepage
ItemList schema. No URLs changed.

**2. Repeat-visit engagement system (commit 40b3ae8).** Added
`streak.js` — a small localStorage-based tracker (no accounts, no
server, no cookies) included on every page. Tracks daily visits, current
streak, and which tools have been tried; renders into the homepage
sidebar. Quiz page now shows best score + current streak on completion.
This is the actual growth lever: MCAT/pre-med prep spans months, so
turning one-time visitors into daily habit users multiplies
pageviews-per-user far more than any SEO or layout change could.
**[DONE 2026-07-21, commit 89788ef]** Extended the streak badge to every
tool page (small top bar, not just the homepage sidebar) — this was the
real gap, since most traffic lands directly on a tool page from search
and never touches the homepage. Verified no conflict with pages that
have their own sticky elements (glycolysis's sticky ATP/NADH tally).

**3. Affiliate research (this entry, no site changes).** Real programs
found, worth pursuing once there's real traffic:
- **Gold Standard MCAT** — 10% commission on all sales, 60-day cookie,
  paid out once $1000 in accrued sales. Most transparent terms found.
  https://www.mcat-prep.com/goldstandard-affiliate/
- **MCAT Self Prep** — affiliate program exists, $50 minimum payout,
  30-day tracking window, commission % not fixed/disclosed publicly.
- **Prep101** — affiliate program exists (info.prep101.com), commission
  rate not publicly disclosed, worth applying directly to see terms.
- **Blueprint MCAT / UWorld MCAT** — big, well-known brands; couldn't
  find their affiliate terms via search (likely run through a network
  like Impact or ShareASale rather than a public page) — worth emailing
  them directly or checking those networks once there's traffic to show.
- **Amazon Associates** — lowest friction to set up (just needs a live
  site), covers MCAT prep books (Kaplan, Princeton Review, Examkrackers)
  and general biochem textbooks. Commission on books is low (~4.5%) and
  the cookie window is short (24 hrs), but zero relationship-building
  required and instant approval process. Good "day one" option while
  bigger affiliate deals get sorted out.

**Recommended sequencing once there's traffic:** start with Amazon
Associates (fastest to set up, matches the "textbook/study resource"
intent students already have) + Gold Standard (best disclosed terms),
add a tasteful "Recommended MCAT resources" section — NOT ads plastered
everywhere, a few honest, contextual recommendations near relevant tools
(e.g. an MCAT-prep-course mention near the quiz/study tools). Chase the
bigger brand deals (Blueprint, UWorld) once there's a traffic number
worth showing them.

### 2026-07-21 — more real fixes found on a fresh pass
Keon asked to keep improving in parallel with the distribution/waiting
phase rather than stop. Found two more genuine (not manufactured) gaps:
- **[DONE, commit ca62617]** No custom 404 page — GitHub Pages was
  serving its generic error page for any broken/mistyped link. Added
  404.html (auto-served by GitHub Pages for any unmatched path) with
  links back into popular tools, `noindex` meta so it never competes in
  search. Also fixed a bug caught before shipping: streak.js's
  tools-tried tracking would have miscounted 404 visits as a "tool
  tried" — excluded it.
- **[DONE, commit ca62617]** sitemap.xml lastmod dates were stuck at the
  original 2026-06-30 launch date on 21 of 24 pages, even after those
  pages got 2-3x more content this week. Refreshed to 2026-07-21 —
  matters because lastmod is a real signal Google uses for crawl
  prioritization; a page that claims "unchanged since June" gets
  recrawled less urgently than one that's honestly marked as updated.

**[DONE, commit 6217b13]** Added `aria-live="polite"` to each tool
page's single headline result element (20/20 pages) — pH, pI, Tm,
Km/Vmax, ΔG, cell potential, etc. Screen readers now announce the answer
as sliders/inputs change instead of giving zero feedback. Deliberately
marked only the one primary metric per page, not every sub-value, to
avoid over-announcing on every keystroke.

**Checked and passed (no fix needed):** color contrast. Muted gray text
on the dark background is 7.18:1 — well above the 4.5:1 WCAG AA minimum
for normal text. Worth knowing this was actually verified, not assumed.

**[DONE, commit 0a4f009]** The 5 canvas-drawn charts (peptide titration
curve, enzyme kinetics x2 plots, Michaelis-Menten fit, amino acid
titration curve) had zero accessible fallback — a screen reader user
would get total silence where a chart is. Added `role="img"` +
descriptive `aria-label` to each, noting the exact values are also
available in accessible text/tables on the same page.

### 2026-07-21 — another "keep digging" round, all real findings
Ran a full HTML well-formedness sweep (Python's html.parser, checking
every open/close tag matches across all 24 pages) plus a mobile
home-screen audit. All genuine, none manufactured:
- **[DONE, commit 888246b]** `michaelis-menten-fitter.html` was missing
  its closing `</main>` tag — the footer nav and analytics scripts were
  nesting inside `<main>` instead of after it. Browsers silently
  recover from this, but it's invalid HTML that could confuse crawler
  DOM parsing and assistive tech. Only page on the whole site with a
  structural tag mismatch (verified via the same script against all 24).
- **[DONE, commit cb2104a]** Favicon was SVG-only (data URI) — Safari
  has spotty support for that — and there was no apple-touch-icon at
  all. That matters specifically for this site: MCAT prep runs for
  months, so a student adding the site to their iPhone home screen is
  exactly the kind of repeat-visit habit we're trying to build, and
  without an apple-touch-icon that shortcut would show a generic
  screenshot instead of a branded icon. Generated real favicon.png (32)
  and apple-touch-icon.png (180) matching the existing brand mark.
- **[DONE, commit 4a27a43]** Same gap on Android — no manifest.json, no
  192/512 icons, no theme-color. Added all three so "Add to Home
  Screen" on Android creates a real standalone-feeling icon instead of
  a bare bookmark, and Chrome's address bar tints to match the site.

**Also checked and passed, for the record:** no duplicate element IDs
anywhere, no `target="_blank"` link missing `rel="noopener"`, no
duplicate titles/descriptions across pages, sitemap XML valid.

### 2026-07-21 — growth features, round 2 (Keon: "we can do them all")
Four growth ideas approved. Sequencing: daily question → practice
problem banks → fill Physiology gap → cheat-sheet PDF.

**1. [DONE, commit 442d67a] Daily Question feature.** New
`daily-question.html`: one multiple-choice question a day, same for
everyone (deterministic by calendar date via a day-index formula, no
server needed), 30-question bank spanning every category on the site.
Answer once/day, get an explanation either way. Tracked via a new
`recordDailyQuestion` in streak.js, linked from the homepage (featured
callout card) and every tool page's footer nav, own og-image, added to
sitemap. This is meant to be a stronger retention lever than the streak
alone — the streak only rewards not breaking a habit, this gives a new
reason to open the site each day. Caught and fixed a real bug before
shipping: the page's own script ran before deferred streak.js had
executed, so the streak line rendered blank on load — fixed by
deferring that specific render call to DOMContentLoaded.

**2. [DONE, commits be19ddd/644d6f6/e0b9837] Practice problem banks.**
2 additional solved practice problems added to all 19 tool pages (quiz
excluded — it's already inherently practice-based), using native
`<details>/<summary>` disclosure widgets (accessible by default, zero
JS needed). Every number verified in Python before writing, several
spot-checked directly against the live tools.

**Bonus finds while doing this:** caught 4 pages
(peptide-charge-calculator, dna-to-protein-translation,
punnett-square-calculator, serial-dilution-calculator) using
`class="work"` for monospace calculation blocks without ever defining
a `.work{}` CSS rule — meaning those sections had been rendering with
no background/padding/monospace font since they were first added
earlier in the project. Also glycolysis-pathway-explorer was missing
both `.card` and `.work`. Fixed all 5 by adding the standard rule to
each page's stylesheet, verified via computed styles in-browser.

**3. [DONE, commit 559b624] Filled the thin Physiology category.**
Added cardiac-output-calculator.html (HR×SV or Fick's principle, both
methods verified to agree at the textbook 5 L/min resting value) and
renal-clearance-calculator.html (Cx=UxV/Px + filtration fraction,
verified against the standard 125 mL/min GFR / 20% FF). Site is now 22
tools, not 20 — updated everywhere: all 20 original pages' sitenav,
homepage (cards + hero + meta + ItemList schema), sitemap, streak.js
TOOL_COUNT, daily-question.html and 404.html's "browse all tools" copy,
new og-images generated, index.png regenerated since its baked-in text
said "20". Full verification passed, both tools' math confirmed live.

**4. [DONE, commit 1779767] Printable/shareable cheat-sheet PDF.** One
clean "Biochemtools MCAT Formula Sheet" (`downloads/biochemtools-mcat-
formula-sheet.pdf`), built with reportlab as a true 2-column layout,
light/print-friendly theme (deliberately not the site's dark theme,
since this is meant to be printed), condensed formulas from all 22
tools across all 6 categories, category-colored header bars matching
the site's palette, footer with the file's own URL on every page.
Linked from the homepage sidebar (new card, above "Study tip") and the
About page. Verified: page count, text extraction, and a rendered PNG
of the actual page — the PDF text-extraction pass initially looked
alarming (Greek letters and arrows showed as garbled Latin characters
like "S" for Σ and "fl" for ↓) but that's a red herring specific to how
reportlab uses the Symbol font for those glyphs; naive text extractors
don't know that encoding. The rendered image confirmed every symbol
(α, χ, Σ, π, →, √, °, ±) displays correctly. Fits on one page, no
overflow, no black-box glyphs.

All 4 growth features from the "we can do them all" batch are now done.
