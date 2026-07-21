# Biochemtools Growth Roadmap

Living doc: rating, priorities, and a dated notes log so work never gets lost
between sessions. Update this file whenever a growth/monetization task is
worked on — add a dated entry to the Notes Log at the bottom, and move items
between Done / In Progress / Not Started as they change state.

## Rating snapshot (2026-07-20)

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
2. **[IN PROGRESS]** Content depth — add a worked numeric example + FAQ
   block to each tool page (270-390 words → 600-900 words). Highest
   remaining ROI: helps both SEO and ad real estate without hurting UX.
   Starting with the pages Google has already indexed (existing traction),
   see Notes Log for which pages are done.
3. **[BLOCKED ON KEON]** Turn on Cloudflare Web Analytics (free, cookieless,
   one click in the Cloudflare dashboard since DNS is already there). Needed
   to know which pages actually get used — currently flying blind beyond
   Search Console query data.
4. **[NOT STARTED]** Proper social preview image (og:image), 1200×630
   landscape, one per tool or one site-wide. The 20 Pinterest pins are the
   wrong aspect ratio (1000×1500 portrait) — this needs its own small image
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

18 of 20 tool pages now have deepened content. Remaining 2: quiz,
dna-to-protein-translation.
