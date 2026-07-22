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

## Which pages are indexed right now

**2026-07-21 Search Console check (data dated 7/9/26, via Page indexing
report):** 21 of ~24 known pages indexed — a real jump from the earlier
2026-07-20 spot-check (7/21 pages showing in search results). The 3
"not indexed" are all flagged "Page with redirect" and are all the same
homepage under non-canonical URLs: `http://biochemtools.com/`,
`http://www.biochemtools.com/`, `https://www.biochemtools.com/`.
Verified via curl: each does one clean 301 straight to the canonical
`https://biochemtools.com/`, no chains, no loops. This is correct,
intended behavior, not a bug — and is almost certainly what the
original "pages not indexed due to redirect" Search Console email (the
thing that kicked off this whole project) was actually about. Nothing
to fix. GSC data lags ~1-2 weeks behind the live site, so it doesn't
yet reflect the newest work (2 physiology tools, daily question, cheat
sheet, share buttons, related-link fixes) — worth another check in a
couple weeks once the crawler catches up.

**Prior 2026-07-20 spot-check (superseded by the above):** Google was
showing 7 of 21 pages in manual search results (up from 2 on
2026-07-04): index, peptide-charge-calculator, osmotic-pressure-calculator,
serial-dilution-calculator, michaelis-menten-fitter,
hardy-weinberg-calculator, beer-lambert-calculator. This was a
different, narrower metric (visible in search results for specific
queries) than the GSC "indexed" count above, so the two aren't directly
comparable — but the trend is the same direction.

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

### 2026-07-21 — Share button + related-tool link cleanup (commits 25073f7, 942ffff)
Keon asked "what else can we improve" — proposed 5 options (share
buttons, contextual related-tool links, a fresh Search Console check,
AdSense timing, affiliate pick), he approved the two that were pure
code with no decision needed from him.

**Share button [DONE, commit 25073f7].** Floating "Share" button added
via streak.js on every tool page + homepage + daily question (skips
about/privacy/contact/404). Native Web Share sheet on mobile, clipboard
copy + toast on desktop, execCommand fallback for older browsers.
Verified: renders with correct fixed positioning and brand color
(9.68:1 text contrast, computed in Python before shipping), correctly
absent on excluded pages, click-triggered copy actually resolves
(confirmed via the toast firing "Link copied!").

**Related-tool links [DONE, commit 942ffff].** Assumed this was a
built-from-scratch task, but checking first found 18 of 21 pages
already had a curated "Related tools" line (not just the generic
footer sitenav) from earlier work. Real gaps found instead:
peptide-charge-calculator.html and quiz.html had none;
enzyme-kinetics-simulator.html, glycolysis-pathway-explorer.html, and
henderson-hasselbalch-buffer-calculator.html used absolute
https://biochemtools.com/... URLs instead of the site's relative-path
convention; enzyme-kinetics-simulator.html linked to the unrelated
peptide-charge-calculator (fixed to point to the actually-related
michaelis-menten-fitter.html). All 21 tool pages now have a working,
relevant related-tools line. Full site HTML well-formedness re-check
passed (0 issues across all files) after the edits.

**Still open, waiting on Keon:** fresh Search Console indexing check
(baseline was 7/21 pages on 2026-07-20, a lot has shipped since),
AdSense application timing, and the affiliate program pick (3
candidates already researched, no decision made).

### 2026-07-21 — Search Console checked live, affiliate pick made and scaffolded

**Search Console [DONE].** Logged into Keon's real GSC via his Chrome
session (claude-in-chrome, already authenticated) and pulled the
actual Page indexing report: 21 of ~24 known pages indexed, up from
7/21 on 2026-07-20 — real progress. The 3 "not indexed" are flagged
"Page with redirect," drilled into the report and got the exact URLs:
`http://biochemtools.com/`, `http://www.biochemtools.com/`,
`https://www.biochemtools.com/` — all non-canonical variants of the
homepage. Verified via curl: each does one clean 301 straight to
`https://biochemtools.com/`, no loops. This is correct, intended
behavior, not a bug, and is almost certainly what the original
"pages not indexed due to redirect" email (the thing that started
this whole project) was actually about. Nothing to fix. GSC data was
dated 7/9/26, so it doesn't yet reflect this session's newest work —
worth another look in a couple weeks.

**Affiliate pick [DECIDED].** Amazon Associates (instant approval,
zero relationship-building, fits "textbook/study resource" intent)
+ Gold Standard MCAT (best disclosed terms of the MCAT-prep options:
10% commission, 60-day cookie, clear $1000 payout threshold). Skipped
MCAT Self Prep, Prep101, and Blueprint/UWorld — all either
undisclosed terms or require a direct-contact application, not worth
the effort pre-traffic.

**Scaffold built [DONE, commit 2f4bc66].** Added a "Study resources we
recommend" card, rendered via streak.js into any page with a
`#recommended-slot` div — currently the homepage sidebar and the quiz
page (matching the earlier "contextual, near quiz/study tools, not
ads everywhere" plan). Ships OFF by default (`AFFILIATE_LIVE = false`
at the top of streak.js) — verified via computed styles that the slot
is `display:none` / 0-height on both pages in this state, i.e. zero
visible change went live. Temporarily live-injected the real markup in
a browser console (never touched the files) to confirm it renders
correctly when on: right background/padding, correct disclosure copy,
both links resolve with `rel="noopener sponsored"`.

**What Keon needs to do:**
1. Sign up for [Amazon Associates](https://affiliate-program.amazon.com/) and [Gold Standard MCAT's affiliate program](https://www.mcat-prep.com/goldstandard-affiliate/) — account creation and payout/tax info has to be done by him, not Claude.
2. Once approved, open `streak.js`, replace `AMAZON_TAG` with the real Associates tag (looks like `something-20`) and `GOLDSTANDARD_URL` with the real tracked referral link from the Gold Standard dashboard.
3. Flip `AFFILIATE_LIVE` to `true`.
4. Commit and push — the card goes live on the homepage and quiz page automatically, no other changes needed.

### 2026-07-21 — Amazon Associates live (commit 3b7d0a1)
Keon signed up for Amazon Associates same day (Store ID `biochemtools20`
— note the signup form rejected the hyphenated `biochemtools-20`,
alphanumeric only). Refactored the single `AFFILIATE_LIVE` flag into
per-program flags (`AMAZON_LIVE`, `GOLDSTANDARD_LIVE`) so Amazon could
go live on its own without the disclosure line implying Gold Standard
was tracked when it isn't yet — Gold Standard signup still pending.
`AMAZON_LIVE = true`, `AMAZON_TAG = "biochemtools20"`. Verified live on
homepage sidebar + quiz page: exactly one link renders, correct tag
encoded in the URL, `rel="noopener sponsored"`, no Gold Standard
placeholder shown. When Gold Standard is signed up: fill in the real
`GOLDSTANDARD_URL` from their dashboard and flip `GOLDSTANDARD_LIVE`
to `true` — same pattern, independent of Amazon.

### 2026-07-21 — visual polish pass + affiliate card rolled out sitewide (commits 83cd28b, 4b8811d)
Keon asked to make the landing page and other pages "prettier and more
appealing," and to get the affiliate link more visible across the
site.

**Homepage redesign [DONE, commit 83cd28b].** Added a subtle radial
gradient glow behind the hero, bolder H1, real shadows on every tool
card and sidebar card (was flat border-only before) with a stronger
lift-and-glow on hover, category-colored dot markers on each section
heading (matching each section's existing card accent color), restyled
"Why these are different" as a proper card instead of bare text, and
matching shadow/hover treatment on the search bar and daily-question
callout. Moved the affiliate recommendations card up in the sidebar —
now second, right after the streak widget, above the fold — per Keon's
explicit ask to make it more visible.

**Sitewide polish + affiliate rollout [DONE, commit 4b8811d].** The
`.card{}` rule was byte-identical across all 21 tool pages + daily
question (confirmed via grep before touching anything), so scripted
the same shadow/hover treatment onto all of them in one pass rather
than hand-editing each file. Also added `#recommended-slot` to all 21
tool pages + daily-question.html (previously only the homepage + quiz
page had it) — since `AMAZON_LIVE` is already true, the Amazon
Associates card now shows on every page site-wide automatically, no
separate activation step.

Verified: HTML well-formedness across all files (0 issues), exactly
one `#recommended-slot` per page, spot-checked rendering + zero
console errors on ph-calculator and glycolysis-pathway-explorer (most
complex interactive layout on the site). Confirmed live on production
(biochemtools.com) via direct curl + a hard-reloaded browser check on
cardiac-output-calculator.html — card shadow and affiliate link both
present with the correct tag.

### 2026-07-21 — full premium homepage redesign (commit bff2ddc)
Keon asked for a genuinely premium homepage, not just the incremental
polish from earlier the same day. Real structural rebuild:
- Sticky glass top nav (backdrop-blur), wordmark, Daily question/About
  links, Browse-tools CTA
- Multi-gradient mesh hero glow (was a single flat blob), bolder 2.6rem
  headline
- New stat row (22 tools · 6 subjects · 100% free · no account) + two
  real CTA buttons, replacing the old standalone daily-question callout
  card (its message folded into a caption line instead)
- Hand-built inline SVG icon per category (flask/DNA helix/chromosome/
  atom/droplet/EKG pulse), colored via the existing --cat variable —
  zero external icon library or extra requests
- Tool cards: switched from left-border accent to top accent bar +
  icon chip (22 cards, injected via a scripted regex pass keyed off
  each section's id, not hand-edited)
- "Why these are different" rebuilt as a real 3-column feature grid
  with icons instead of one paragraph in a box
- Footer restructured: wordmark + tagline + organized link row

Verified: HTML well-formedness, icon color/background correctness per
category, 3-column why-grid confirmed via computed grid-template-
columns, mobile check (nav collapses correctly, zero horizontal
overflow), search filter + streak widget + affiliate slot + share
button all still functional post-restructure, zero console errors,
confirmed live on production after a hard reload (GitHub Pages took
~15s to propagate this time).

**Honest note for the next session:** the site itself is now in very
good shape — the actual blocker on real revenue is traffic/backlinks,
not more on-site polish. See the rating + growth-plan conversation
logged the same day for the prioritized next-steps list (content/SEO,
community distribution, retention deepening, monetization diversity)
instead of more visual iteration.

### 2026-07-21 — content strategy pivot: long-form guides + SEO audit (commits 0d8ca57, 5c9c96a, 4baadc1)
Keon rejected Reddit/community outreach ("I've done enough of that").
Real signal from Cloudflare Analytics: essentially zero external
traffic so far, only Keon checking the site himself. Pivoted the
"what's next" plan to something executable without any outreach from
him: long-form guide content, since the site was 100% tool pages
before this with nothing genuinely link-worthy or built for long-tail
"how do I..." queries, which are far more winnable for a brand-new
domain than competing for "X calculator" head terms.

**Guide 1 [DONE, commit 0d8ca57]:** how-to-calculate-pi-without-a-
calculator.html. 4 worked examples (2/3/4/8 ionizable groups) plus 2
practice problems, every number independently verified in Python
against the exact same charge/pI functions the peptide charge
calculator uses. HowTo + FAQPage schema. Linked from the calculator,
added to sitemap.

**Guide 2 [DONE, commit 5c9c96a]:** mcat-buffer-questions-explained.html.
Covers the 3 real buffer question archetypes (selection, ratio, strong
acid/base addition) — the third type genuinely extends the buffer
calculator rather than restating it, since the tool doesn't walk
through the "add acid, find new pH" stoichiometry problem. All worked
examples Python-verified. Caught a malformed JSON-LD block (missing
closing brace) via the standard validation pass before shipping —
exactly why that check runs on every page.

**Site-wide SEO audit [DONE, commit 4baadc1].** Full pass across all
30 pages: title/description length (with proper HTML-entity decoding
this time — the naive raw-length check was flagging false positives
on any title with `&amp;`), canonical correctness, duplicate title/
description check, JSON-LD validity, broken internal link crawl (29
unique targets, 0 broken). Real findings fixed:
- renal-clearance-calculator.html meta description was 1 char over
  the 160 limit
- 25 decorative category icon SVGs on the homepage had no
  aria-hidden, so screen readers would announce them as meaningless
  unlabeled graphics
- Both new guides were invisible from the homepage (only reachable
  via their tool page or the sitemap) — added a "Study guides"
  sidebar card
- Added BreadcrumbList schema to both guides for rich-snippet
  breadcrumbs

**Guide 3 [DONE, commit 7b8339d]:** michaelis-menten-vs-lineweaver-
burk.html. Ties both enzyme kinetics tools together — the fitter
(uses LB regression to extract Km/Vmax from data) and the simulator
(uses LB to diagnose inhibition type). Reused exact numbers from both
live tools (the fitter's 6-point dataset regression, the simulator's
r=1 competitive/noncompetitive example) rather than inventing new
ones, so the guide and the tools always agree. Caught the same
missing-closing-brace JSON-LD bug as guide 2, in all 3 FAQ entries
this time — the json.loads validation pass is now clearly worth
running on every single guide, not just spot-checking.

**All 3 planned guides now done.** Linked from their respective tool
pages, from each other where relevant, from the homepage's "Study
guides" sidebar card, and in sitemap.xml. Site-wide sweep after
shipping guide 3: 0 HTML errors, 0 invalid JSON-LD, 0 broken internal
links across 31 pages / 30 unique link targets.

**Next real decision point:** the guides are built and internally
solid, but there's still no organic traffic (per Keon's Cloudflare
check earlier this session). The content is in place for long-tail
SEO to eventually work, but that takes weeks-to-months to show up in
search even in the best case, and only works at all if these pages get
crawled/indexed — worth a Search Console check in a couple weeks to
see if they're indexed and whether any of the 3 pick up impressions.
No further content is queued; the honest next move is to wait for that
signal rather than write a 4th guide speculatively.

### 2026-07-21 — guide polish pass (commit a6188e6)
Keon asked for more things to improve rather than more speculative
content. Found and fixed real gaps:

- **Dedicated OG images for all 3 guides.** They'd been reusing their
  linked tool's social preview image, so a shared guide link showed a
  different title in the image than in the actual link preview text.
  Generated 3 new ones with the same PIL pipeline as the rest of the
  site.
- **More cross-links.** Guide 1 (pI) added to amino-acid-titration-
  curve.html and quiz.html; guide 2 (buffers) added to ph-calculator.html
  — topically relevant pages that weren't linking to the guides yet.
- **WebSite + SearchAction schema on the homepage**, for a possible
  Google sitelinks searchbox. Caught before shipping that the
  SearchAction claimed a `?q=` URL parameter worked when the site never
  actually read it — would have been non-functional structured data.
  Implemented it for real instead: the homepage search box now reads
  `?q=` on load and filters immediately, so this also means shareable
  pre-filtered links to the tools now work (e.g. biochemtools.com/?q=glycolysis).
- **Two real mobile overflow bugs**, found via actual browser testing
  at 375px width (a static column-count heuristic threw several false
  positives that turned out fine when tested for real): the 6-column
  inhibition-comparison table on the new MM-vs-LB guide, and the
  pre-existing 5-column amino acid reference table on quiz.html. Both
  wrapped in `overflow-x:auto`, verified zero horizontal overflow after.

**Investigated and deliberately left alone:** "pI" renders visually as
"pl" in every system font tested (SF Pro Bold/Regular, Helvetica Neue,
even italic) — confirmed via direct font rendering tests, not
guessed. This is a universal sans-serif limitation, present site-wide
everywhere "pI" appears, not something introduced this session.
Resolved by context for anyone who knows the term; not worth a
site-wide font change over a cosmetic edge case.

Verified: HTML well-formedness + JSON-LD validity across all 31 pages,
0 broken internal links across 30 unique targets, 0 mobile horizontal
overflow on all 3 guides + quiz.html, confirmed live on production.

### 2026-07-21 — ATP Yield Calculator, tool #23 (commit 35dfea6)
Keon: "keep improving... I'm not stopping until this is genuinely a
necessity for premed students." Read that as a mandate to fill real
content gaps, not just keep polishing/guide-writing on material
already covered. Biggest gap identified: the site had glycolysis but
nothing on total ATP yield — arguably the single most commonly tested
AND most commonly confused intro-biochem fact (textbooks disagree
between 36/38 and 30/32 ATP per glucose depending on convention, and
most students memorize one number without knowing why it varies).

Built atp-yield-calculator.html: two toggles (P/O ratio convention,
cytosolic NADH shuttle), live breakdown table, full worked math for
all 4 possible totals. Verified twice — independently in Python before
writing anything, then again by driving the actual UI through all 4
toggle combinations in-browser. Exact match both times (30/32/36/38).

Full 22->23 ripple: streak.js TOOL_COUNT, homepage (hero tag, stats,
meta description, og:description, new tool card, ItemList schema),
sitemap.xml, dedicated og-image, sitenav + "All X tools" copy across
all 25 other pages that reference it — done via a targeted script
rather than 25 hand-edits. Caught and fixed a position-renumbering bug
in the ItemList schema script before shipping (duplicate position 10)
by regenerating the block from parsed JSON instead of patching by
regex.

Also hit and correctly diagnosed a false alarm: after deploying,
localhost showed "9/22 tools tried" instead of "9/23" — traced to
browser HTTP caching of streak.js in a tab reused across many earlier
reloads this session, not a real bug. Confirmed via cache-busted
fetch() that the server was serving TOOL_COUNT=23 correctly the whole
time, then confirmed a fresh page load on production showed the
correct "2/23" immediately. Worth remembering for future sessions:
when a local test shows stale data right after a shared-JS-file edit,
check via fetch()+cache-bust before assuming the fix didn't take.

Verified: HTML well-formedness + JSON-LD validity across all 32 pages,
0 broken internal links across 31 unique targets, 0 mobile overflow on
new tool + homepage, confirmed live on production with fresh load.

**Natural next step, not yet started:** a Citric Acid Cycle explorer
(same step-through UX as the glycolysis tool) would directly complete
the cellular respiration story this ATP calculator's math depends on —
right now the calculator states TCA cycle yields without a dedicated
tool teaching them the way glycolysis has one.

### 2026-07-21 — Citric Acid Cycle Explorer, tool #24 (commit 01c7ec5)
Built the natural next step flagged above. Same step-through UX as
glycolysis-pathway-explorer.html: 8 reactions, live NADH/FADH2/GTP/CO2
tally, every enzyme named, three regulated steps flagged (citrate
synthase, isocitrate dehydrogenase — the rate-limiting step — and
alpha-ketoglutarate dehydrogenase). This closes the gap the ATP yield
calculator left open: that tool already cited "6 NADH, 2 FADH2, 2 GTP"
from the TCA cycle without the site having anything that taught where
those numbers come from.

Per-turn yield (3 NADH, 1 FADH2, 1 GTP, 2 CO2) verified in Python
before writing anything — matches exactly what atp-yield-calculator.html
already states for one turn ×2. Added a cross-tool practice problem:
using the ATP calculator's own default (modern P/O ratio) settings,
one turn contributes exactly 10 ATP (3×2.5 + 1×1.5 oxidative + 1 GTP
substrate-level) — a clean number, verified, and it directly ties the
two tools together for anyone using both.

Interactive step-through logic verified live in-browser, not just in
Python: full run matches the computed final tally (3/1/1/2), reset
zeroes correctly, and the partial-progress state after 3 steps (1
NADH, 1 CO2) matches hand-tracing since only isocitrate dehydrogenase
among the first 3 steps produces either.

Full 23->24 ripple done the same way as the previous tool addition:
streak.js TOOL_COUNT, homepage (hero tag, stats, meta description,
og:description, new tool card with a cycle-arrow icon, ItemList schema
regenerated from parsed JSON — sequential 1-24 positions verified, no
repeat of the earlier renumbering bug), sitemap.xml, dedicated
og-image, sitenav + "All 23/24 tools" copy across all 26 other pages.

Verified: HTML well-formedness + JSON-LD validity across all 33 pages,
0 broken internal links across 32 unique targets, 0 mobile overflow on
both new tool + homepage, zero console errors, confirmed live on
production (GitHub Pages took ~30s to propagate this time).

**The cellular respiration story is now complete as real interactive
tools:** glycolysis → citric acid cycle → ATP yield, each with its own
dedicated, verified tool rather than numbers cited from an uncovered
pathway. No further tool gap identified yet — next content decision
should probably wait for a fresh look at what's actually getting
traffic/engagement before picking the next build.

### 2026-07-22 — first real Search Console Performance check, 3 data-driven fixes
New day, Keon asked what's next. Instead of guessing at another tool,
went and checked Search Console's actual Performance report (not just
the Page Indexing report used previously, which lags ~2 weeks) via his
authenticated Chrome session.

**Real numbers, first time seeing them:** 2.7K impressions across 638
distinct queries over the last 3 weeks (climbing since ~7/9), but
average position 54.6 (~page 5-6 of results) and only 4 total clicks
(0.1% CTR). This reframes the whole traffic problem: it's not "nobody
finds the site," it's "found but ranked too low to click." The actual
queries showing up (molarity to grams, c1v1 calculator, absorbance
formula, punnett square calculator, etc.) are excellent matches for
the site's real content — confirming targeting is right and the
remaining gap is domain authority/ranking strength, which mostly just
needs time + backlinks (the thing Keon has ruled out doing manually).

Per-page breakdown: only 3 of ~24 pages have any clicks yet (quiz.html
2, osmotic-pressure-calculator.html 1, michaelis-menten-fitter.html 1).
The highest-impression pages (molarity-molar-mass: 444, amino-acid-
titration-curve: 297, beer-lambert: 230, dilution: 219, peptide-
charge: 212) all still have zero clicks — pure ranking-position
problem, not a content problem.

**3 concrete fixes pulled directly from the query data itself, not
guessed:**
1. henderson-hasselbalch-buffer-calculator.html — "histidine buffer
   calculator" (17 impressions) wasn't captured at all; added Histidine
   (pKa 6.0, matching the value already used site-wide for this side
   chain) as a 7th preset, plus a FAQ entry.
2. dilution-calculator.html — "antibody dilution calculator" (33
   impressions, 0 clicks) is a real, common wet-lab need the generic
   C1V1 framing didn't speak to. Added a worked example (1:1000
   primary antibody dilution for Western blot, verified: 10 µL stock +
   9.99 mL diluent) and a FAQ entry mapping ratio dilutions onto the
   same formula.
3. molarity-molar-mass-calculator.html — "molarity to grams" (80) and
   "g/mL to molarity" (61) together are 141 of this page's 444
   impressions, but the tool only ever computed grams-for-a-target-
   molarity, never the reverse. Added a second mode, "Concentration →
   molarity," with a g/L / g/mL / mg/mL unit selector. Verified in
   Python first (1 mg/mL caffeine = 1 g/L = 0.00515 M), then verified
   live by driving all three unit options to the same answer, then
   confirmed the original mode's default output was unchanged after
   the refactor.

All 3 verified: HTML well-formedness + JSON-LD validity, 0 mobile
overflow, 0 console errors, new interactive logic tested live in
addition to Python.

**Standing recommendation:** keep checking Search Console's Performance
report (not just Page Indexing) periodically — it updates much faster
(hours, not weeks) and is now the best source of real, specific,
actionable next-fixes, far better than guessing at new content.

**Same-day follow-up: sorted the query list by position instead of
impressions, and found something more interesting.** A handful of
ultra-specific queries — exact formulas (`π = iMRT`, `a=εbc`, `RT/nF`)
and even literal homework-question text (`glycine titration curve pka
2.34 9.60 pi 5.97 source`) — rank on **page 1** (position 6.8-10),
despite the domain's zero backlinks and terrible average position
(54.6) on broad terms. Checked why: osmotic-pressure-calculator,
beer-lambert-calculator, and nernst-equation-calculator all already
have their exact formula baked into title/meta/schema — that's what's
winning the exact-match. Checked the other formula-based tools for the
same treatment and found gibbs-free-energy-calculator.html's title was
completely generic (no formula at all) — added ΔG=ΔH−TΔS to its
title/description/keywords to match. ph-calculator, henderson-
hasselbalch, and hardy-weinberg were left as-is since their tool names
themselves already function as the "exact match" term.

**Real strategic takeaway:** for a brand-new, zero-backlink domain,
literal formula strings and literal worked-example numbers are
currently a stronger ranking lever than broad head-terms — exact-match
relevance is apparently strong enough to fully outweigh weak domain
authority for these ultra-specific queries. Worth keeping in mind for
any future tool or guide: put the literal formula in the title, not
just the concept name.

Stopping the query-mining here for today — the remaining 620+ queries
are mostly 1-2 impression long-tail with fast-diminishing signal.
Next real checkpoint: revisit Search Console Performance in a few days
to see whether today's 4 fixes (histidine, antibody dilution, g/mL-to-
molarity, Gibbs title) show up as new impressions/clicks, and whether
the two new guides + two new tools from yesterday have started
accumulating impressions yet (they had none as of this morning's data,
too new to expect otherwise).
