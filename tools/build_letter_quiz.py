#!/usr/bin/env python3
"""The amino acid one-letter code quiz, as its own page.

Search Console: "amino acid quiz one letter code" 22.0, "amino acid letter quiz"
22.3, "single letter amino acid quiz" 19.5. Those rank noticeably better than the
plain "amino acid quiz" at 35.6, which is the same pattern seen everywhere else
on this site: the specific query wins and the generic one does not.

quiz.html has a one-letter mode, but it is a JavaScript button, so there is no URL
for Google to rank. This gives the topic an address.

Data comes from amino-acid-chart.html, and the exceptions are derived rather than
listed, so the page cannot claim an exception that is not one.
"""
import os, re, json, subprocess, tempfile, html

SITE = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..")
CHART = os.path.join(SITE, "amino-acid-chart.html")
SRC = os.path.join(SITE, "quiz.html")
SLUG = "amino-acid-one-letter-code-quiz.html"

# why each non-obvious letter was chosen, for the ones the data flags
WHY = {
    "F": ("P was taken by proline", "Fenylalanine"),
    "W": ("T was taken by threonine", "tWyptophan, or the two rings of the indole drawn as a W"),
    "Y": ("T was taken by threonine", "tYrosine"),
    "N": ("A was taken by alanine", "asparagiNe"),
    "Q": ("G was taken by glycine", "Q-tamine"),
    "K": ("L was taken by leucine", "K sits next to L in the alphabet"),
    "R": ("A was taken by alanine", "aRginine"),
    "D": ("A was taken by alanine", "asparDic acid, or D for aciDic"),
    "E": ("G was taken by glycine", "gluEtamic acid, and E follows D just as Glu is one carbon longer than Asp"),
}


def load():
    h = open(CHART, encoding="utf-8").read()
    m = re.search(r"\bAA\s*=\s*(\[[\s\S]*?\n\s*\]);", h)
    if not m:
        raise RuntimeError("AA array not found in amino-acid-chart.html")
    with tempfile.NamedTemporaryFile("w", suffix=".js", delete=False) as f:
        f.write("const A=" + m.group(1) + ";console.log(JSON.stringify(A))")
        p = f.name
    try:
        r = subprocess.run(["node", p], capture_output=True, text=True)
        if r.returncode:
            raise RuntimeError(r.stderr[:300])
        return json.loads(r.stdout)
    finally:
        os.unlink(p)


def build(AA, exc, matches):
    h = open(SRC, encoding="utf-8").read()
    head = h[h.index("<head>"):h.index("</head>")]
    nav = h[h.index("<body>"):h.index("<header>")]

    title = "Amino Acid One-Letter Code Quiz: All 20, Free"
    desc = ("Quiz yourself on all 20 amino acid one-letter codes, plus the nine that do not match "
            "the first letter and why. Free, no signup, instant feedback.")
    head = re.sub(r"<title>[\s\S]*?</title>", "<title>%s</title>" % title, head, count=1)
    head = re.sub(r'<meta name="description" content="[^"]*"',
                  '<meta name="description" content="%s"' % desc, head, count=1)
    head = re.sub(r'<meta name="keywords" content="[^"]*"',
                  '<meta name="keywords" content="amino acid one letter code quiz, single letter '
                  'amino acid quiz, amino acid letter quiz, one letter amino acid codes"', head, count=1)
    head = re.sub(r'<link rel="canonical" href="[^"]*"',
                  '<link rel="canonical" href="https://biochemtools.com/%s"' % SLUG, head, count=1)
    head = re.sub(r'<meta property="og:title" content="[^"]*"',
                  '<meta property="og:title" content="%s"' % title, head, count=1)
    head = re.sub(r'<meta property="og:description" content="[^"]*"',
                  '<meta property="og:description" content="%s"' % desc, head, count=1)
    ld = {"@context": "https://schema.org", "@type": "Quiz",
          "url": "https://biochemtools.com/" + SLUG, "name": title, "description": desc,
          "inLanguage": "en", "isAccessibleForFree": True,
          "about": {"@type": "Thing", "name": "Amino acid one-letter codes"},
          "publisher": {"@type": "Organization", "name": "BiochemTools", "url": "https://biochemtools.com/"}}
    head = re.sub(r'<script type="application/ld\+json">[\s\S]*?</script>',
                  '<script type="application/ld+json">%s</script>' % json.dumps(ld), head, count=1)
    head = head.replace("</style>", """
 table{width:100%;border-collapse:collapse;margin:.9rem 0 .2rem;font-size:.95rem}
 th{text-align:left;color:var(--muted);font-weight:600;font-size:.82rem;text-transform:uppercase;
    letter-spacing:.04em;padding:.35rem .9rem .5rem 0;border-bottom:1px solid var(--line)}
 td{padding:.5rem .9rem .5rem 0;border-bottom:1px solid var(--line);vertical-align:top}
 tr:last-child td{border-bottom:none}
 .code{font-family:ui-monospace,Menlo,monospace;font-weight:700;color:var(--accent);font-size:1.05rem}
 #qname{font-size:2rem;font-weight:700;margin:.4rem 0 1rem}
 .opts{display:grid;grid-template-columns:repeat(auto-fit,minmax(88px,1fr));gap:.6rem}
 .opts button{font-size:1.3rem;font-weight:700;padding:.85rem 0;border-radius:10px;
   border:1px solid var(--line);background:var(--card);color:var(--txt);cursor:pointer}
 .opts button:hover{border-color:var(--accent)}
 .opts button.right{border-color:#6fb59f;color:#6fb59f}
 .opts button.wrong{border-color:#e2645e;color:#e2645e}
 #fb{min-height:1.6rem;margin-top:.9rem;color:var(--muted)}
</style>""", 1)

    exc_rows = "".join(
        '<tr><td>%s</td><td class="code">%s</td><td>%s. Think <b>%s</b></td></tr>'
        % (a["name"], a["c1"], WHY[a["c1"]][0], WHY[a["c1"]][1]) for a in exc)
    all_rows = "".join(
        '<tr><td>%s</td><td class="code">%s</td><td>%s</td><td>%s</td></tr>'
        % (a["name"], a["c1"], a["c3"], a["cls"]) for a in sorted(AA, key=lambda a: a["name"]))
    easy = ", ".join(a["name"] for a in sorted(matches, key=lambda a: a["name"]))

    body = """<header>
 <h1>Amino acid one-letter code quiz</h1>
</header>
<main>
 <div class="card">
  <div style="color:var(--muted);font-size:.85rem">What is the one-letter code for</div>
  <div id="qname">&nbsp;</div>
  <div class="opts" id="opts"></div>
  <div id="fb"></div>
  <div style="margin-top:1rem;color:var(--muted);font-size:.9rem">
   Score <span id="score">0</span> of <span id="asked">0</span>
  </div>
 </div>

 <div class="card">
  <h2 style="margin-top:0">Eleven of them are just the first letter</h2>
  <p>%(easy)s. If the name starts with the letter, that is the code. Learn the other nine and you
  have all twenty.</p>
 </div>

 <div class="card">
  <h2 style="margin-top:0">The nine that do not match, and why</h2>
  <p>These are not arbitrary. In every case the obvious letter had already been claimed by another
  amino acid, so a nearby or phonetic letter was used instead.</p>
  <table><thead><tr><th>Amino acid</th><th>Code</th><th>Why</th></tr></thead>
  <tbody>%(exc_rows)s</tbody></table>
 </div>

 <div class="card">
  <h2 style="margin-top:0">All twenty, for reference</h2>
  <table><thead><tr><th>Name</th><th>1-letter</th><th>3-letter</th><th>Class</th></tr></thead>
  <tbody>%(all_rows)s</tbody></table>
 </div>

 <div class="card">
  <h2 style="margin-top:0">Where you actually meet these</h2>
  <p>One-letter codes are not a memory exercise for their own sake. They are how sequences get
  written down anywhere space matters.</p>
  <p><b>FASTA files and sequence alignments</b> use them exclusively, because a 300-residue protein
  written in three-letter codes is unreadable. A BLAST result is a wall of single letters.</p>
  <p><b>Mutation notation</b> uses them constantly. Sickle cell anaemia is written E6V: glutamate at
  position 6 replaced by valine. If you cannot read E and V on sight, the notation tells you
  nothing, and that is the form it appears in throughout the literature and on exams.</p>
  <p><b>Restriction and cloning tools</b> return translated sequences in one-letter code by default,
  including the <a href="/dna-to-protein-translation.html">DNA to protein translator</a> here.</p>
 </div>

 <div class="card">
  <h2 style="margin-top:0">Other ways to drill these</h2>
  <p>The <a href="/quiz.html">full amino acid quiz</a> also tests three-letter codes and side-chain
  class. There is a <a href="/amino-acid-chart.html">sortable chart of all 20</a> with pKa values
  and molecular weights, and a
  <a href="/downloads/amino-acid-structures-chart.png">printable structures chart</a> if you prefer
  paper.</p>
 </div>
</main>
<script>
const AA=%(aajson)s;
let score=0,asked=0,cur=null,locked=false;
const $=i=>document.getElementById(i);
function pick(){
 locked=false;
 cur=AA[Math.floor(Math.random()*AA.length)];
 $("qname").textContent=cur.name;
 const wrong=AA.filter(a=>a.c1!==cur.c1);
 const opts=[cur.c1];
 while(opts.length<4){const c=wrong[Math.floor(Math.random()*wrong.length)].c1;if(!opts.includes(c))opts.push(c);}
 for(let i=opts.length-1;i>0;i--){const j=Math.floor(Math.random()*(i+1));[opts[i],opts[j]]=[opts[j],opts[i]];}
 const box=$("opts");box.innerHTML="";
 opts.forEach(c=>{const b=document.createElement("button");b.textContent=c;b.onclick=()=>answer(b,c);box.appendChild(b);});
 $("fb").textContent="";
}
function answer(btn,c){
 if(locked)return;locked=true;asked++;
 const right=c===cur.c1;
 if(right){score++;btn.classList.add("right");$("fb").textContent="Correct.";}
 else{btn.classList.add("wrong");
  [...$("opts").children].forEach(b=>{if(b.textContent===cur.c1)b.classList.add("right");});
  $("fb").textContent=cur.name+" is "+cur.c1+".";}
 $("score").textContent=score;$("asked").textContent=asked;
 if(window.answerStreak){try{window.answerStreak(right);}catch(e){}}
 setTimeout(pick,right?700:1900);
}
pick();
</script>
""" % dict(easy=easy, exc_rows=exc_rows, all_rows=all_rows,
           aajson=json.dumps([{"name": a["name"], "c1": a["c1"]} for a in AA]))

    return "<!DOCTYPE html>\n<html lang=\"en\">\n" + head + "</head>\n" + nav + body + "</body>\n</html>\n"


if __name__ == "__main__":
    AA = load()
    assert len(AA) == 20, "expected 20 amino acids, got %d" % len(AA)
    matches = [a for a in AA if a["name"][0].upper() == a["c1"].upper()]
    exc = [a for a in AA if a["name"][0].upper() != a["c1"].upper()]
    assert len(exc) == 9, "expected 9 codes that do not match the first letter, found %d" % len(exc)
    for a in exc:
        assert a["c1"] in WHY, "no explanation written for %s (%s)" % (a["name"], a["c1"])
    print("  %d codes match the first letter, %d do not" % (len(matches), len(exc)))
    for a in exc:
        taken, mnem = WHY[a["c1"]]
        print("    %-14s %s   %s. %s" % (a["name"], a["c1"], taken, mnem))
    open(os.path.join(SITE, SLUG), "w", encoding="utf-8").write(build(AA, exc, matches))
    print("  wrote " + SLUG)
