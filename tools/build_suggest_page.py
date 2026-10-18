#!/usr/bin/env python3
"""The suggestions page: a request slip, and the receipts from everyone who sent one.

The form on its own is a void. What makes someone actually write something is seeing
that the last person who did got their name on the thing they changed. So the page
carries both: the slip at the top, and underneath, the real record.

Every entry below is traceable. The usernames come from this repo's own commit
messages and from the credit lines printed in the chart footers, which are already
public. Nothing here is invented, and nothing is attributed to anyone who did not
actually say it.

The shell (head, nav, footer, analytics) is cloned from contact.html so this page
cannot drift from the rest of the site.
"""
import os, re, json, sys, html

SITE = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..")
SRC = os.path.join(SITE, "contact.html")
OUT = os.path.join(SITE, "suggest.html")

FORMSPREE = "https://formspree.io/f/mvkzyvge"
FORM_RE = re.compile(r"^https://formspree\.io/f/[A-Za-z0-9]+$")

TITLE = "Suggest a Tool: Tell Me What to Build Next | BiochemTools"
DESC = ("Tell me what to build next, or what is wrong. Every suggestion is read, and the "
        "people whose asks changed this site are credited on the charts they changed.")

# (image, alt, what changed, [(who, where, what they said)])
RECEIPTS = [
    ("buffer-selection-chart-light.png",
     "The buffer selection chart, 32 buffers positioned on a pH axis",
     "The buffer chart was rebuilt four times, by four different people",
     [("u/erikna10", "r/Biochemistry",
       "asked for piperazine and the charge of each buffering ion, so the table could be "
       "used to plan ion exchange runs. The buffer ion must not stick to the resin."),
      ("u/MorphingSp", "r/Biochemistry",
       "asked for polyprotic buffers on a single row with each pKa marked. Citrate's "
       "ranges overlap into one bar, phosphate's stay separate islands, because drawing "
       "phosphate as unbroken from pH 1 to 13 would be a lie."),
      ("u/RendertheFatCap", "r/Biochemistry",
       "pointed out that the crowd of buffers near pH 7 is a property of the list rather "
       "than of chemistry. The footer now says so outright."),
      ("u/orchidguy", "r/Biochemistry",
       "said the pKa was stranded on the far side of the chart, so your eye had to cross "
       "the whole width to connect a buffer to its number. It sits next to the name now.")]),
    ("enzyme-inhibition-chart-light.png",
     "The enzyme inhibition chart, four inhibition patterns and their Lineweaver-Burk signatures",
     "Mixed inhibition was wrong, and a reader said so",
     [("u/xtalgeek", "r/Biochemistry",
       "pointed out the chart showed one case of mixed inhibition as though it were the "
       "rule. Mixed inhibition is a continuum. It is drawn as two rows now, and the "
       "correction is credited in the chart's own footer.")]),
    ("amino-acid-structures-chart-light.png",
     "The MCAT amino acid chart, every amino acid drawn at physiological pH",
     "A whole chart exists because two comments said the old one was wrong for studying",
     [("r/Mcat", "on the original biochem chart",
       "\"all this info and no structures\" and \"way too much detail\". So molecular "
       "weight and hydropathy came out, every amino acid got drawn, and the DEHCYKR "
       "mnemonic came from a commenter there too.")]),
]

STYLE = """
 main{max-width:760px}
 .eyebrow{font-size:.78rem;letter-spacing:.14em;text-transform:uppercase;color:var(--muted);
   margin:0 0 .6rem}
 h1{margin:0 0 .5rem;line-height:1.1}
 h1 em{font-style:normal;color:var(--accent)}
 .lede{color:var(--muted);font-size:1.05rem;margin:0 0 2rem;max-width:58ch}
 .slip{background:var(--card);border:1px solid var(--line);border-radius:14px;padding:1.6rem}
 .slip h2{margin:0 0 .25rem;font-size:1.05rem}
 .slip .hint{color:var(--muted);font-size:.9rem;margin:0 0 1.2rem}
 .kinds{display:flex;flex-wrap:wrap;gap:.5rem;margin:0 0 1.1rem;padding:0;border:0}
 .kinds legend{position:absolute;width:1px;height:1px;overflow:hidden;clip:rect(0 0 0 0)}
 .kinds label{cursor:pointer}
 .kinds input{position:absolute;opacity:0;width:0;height:0}
 .kinds span{display:inline-block;padding:.45rem .9rem;border:1px solid var(--line);
   border-radius:999px;font-size:.9rem;color:var(--muted);transition:border-color .12s,color .12s}
 .kinds input:checked+span{border-color:var(--accent);color:var(--accent)}
 .kinds input:focus-visible+span{outline:2px solid var(--accent);outline-offset:2px}
 .slip label.fl{display:block;font-size:.85rem;color:var(--muted);margin:0 0 .35rem}
 .slip textarea,.slip input[type=email]{width:100%;box-sizing:border-box;background:var(--bg);
   color:var(--txt);border:1px solid var(--line);border-radius:10px;padding:.7rem .85rem;
   font:inherit;font-size:.98rem}
 .slip textarea{min-height:130px;resize:vertical;line-height:1.5}
 .slip textarea:focus,.slip input[type=email]:focus{outline:none;border-color:var(--accent)}
 .slip .row{margin:0 0 1.1rem}
 .send{background:var(--accent);color:#17120c;border:0;border-radius:999px;
   padding:.7rem 1.5rem;font:inherit;font-weight:600;cursor:pointer}
 .send:hover{transform:translateY(-1px)}
 .send[disabled]{opacity:.55;cursor:default;transform:none}
 .slipnote{color:var(--muted);font-size:.82rem;margin:.9rem 0 0}
 .formmsg{margin:1rem 0 0;padding:.8rem 1rem;border-radius:10px;border:1px solid var(--line);
   background:var(--bg);font-size:.95rem}
 .formmsg.ok{border-color:var(--accent);color:var(--txt)}
 .formmsg.bad{border-color:var(--bad);color:var(--txt)}
 .gotcha{position:absolute;left:-9999px}
 .receipts{margin:3.2rem 0 0}
 .receipts > p{color:var(--muted);max-width:60ch}
 .receipt{display:grid;grid-template-columns:132px 1fr;gap:1.3rem;align-items:start;
   background:var(--card);border:1px solid var(--line);border-radius:14px;
   padding:1.3rem;margin:1rem 0}
 /* object-fit, because the structures chart is 1640x4290 and scaling it whole makes
    a thin unreadable strip. Showing its top crop keeps it legible. */
 .receipt img{width:132px;height:168px;object-fit:cover;object-position:top center;
   border:1px solid var(--line);border-radius:8px;display:block;background:#fff}
 .receipt h3{margin:0 0 .8rem;font-size:1rem;line-height:1.35}
 .ask{margin:0 0 .85rem;font-size:.93rem;line-height:1.55;color:var(--muted)}
 .ask:last-child{margin-bottom:0}
 .ask b{color:var(--txt);font-weight:600}
 .ask .where{color:var(--muted);opacity:.75}
 @media(max-width:560px){
  .receipt{grid-template-columns:1fr}
  .receipt img{width:100%;max-width:100%;height:150px}
 }
"""


def build():
    if not FORM_RE.match(FORMSPREE):
        print("  FAIL FORMSPREE is %r, which is not a formspree endpoint. The page would "
              "post to itself and tell people it worked." % FORMSPREE)
        return 1
    h = open(SRC, encoding="utf-8").read()
    head = h[h.index("<head>"):h.index("</head>")]
    nav = h[h.index("<body>"):h.index("<main>")]
    foot = h[h.index("</main>") + len("</main>"):]

    head = re.sub(r"<title>[\s\S]*?</title>", "<title>%s</title>" % html.escape(TITLE), head, 1)
    head = re.sub(r'<meta name="description" content="[^"]*"',
                  '<meta name="description" content="%s"' % html.escape(DESC, quote=True), head, 1)
    head = re.sub(r'<link rel="canonical" href="[^"]*"',
                  '<link rel="canonical" href="https://biochemtools.com/suggest.html"', head, 1)
    head = re.sub(r'<meta property="og:title" content="[^"]*"',
                  '<meta property="og:title" content="%s"' % html.escape(TITLE, quote=True), head, 1)
    head = re.sub(r'<meta property="og:description" content="[^"]*"',
                  '<meta property="og:description" content="%s"' % html.escape(DESC, quote=True), head, 1)
    head = re.sub(r'<meta property="og:url" content="[^"]*"',
                  '<meta property="og:url" content="https://biochemtools.com/suggest.html"', head, 1)
    ld = {"@context": "https://schema.org", "@type": "WebPage",
          "url": "https://biochemtools.com/suggest.html", "name": TITLE, "description": DESC,
          "inLanguage": "en", "isAccessibleForFree": True,
          "publisher": {"@type": "Organization", "name": "BiochemTools",
                        "url": "https://biochemtools.com/"}}
    if re.search(r'<script type="application/ld\+json">', head):
        head = re.sub(r'<script type="application/ld\+json">[\s\S]*?</script>',
                      '<script type="application/ld+json">%s</script>' % json.dumps(ld), head, 1)
    else:
        head += '\n<script type="application/ld+json">%s</script>\n' % json.dumps(ld)
    head = head.replace("</style>", STYLE + "</style>", 1)

    kinds = [("tool", "A tool I want"), ("wrong", "Something is wrong"), ("other", "Something else")]
    kind_html = "".join(
        '<label><input type="radio" name="kind" value="%s"%s><span>%s</span></label>'
        % (v, ' checked' if i == 0 else '', html.escape(t)) for i, (v, t) in enumerate(kinds))

    receipts = ""
    for img, alt, headline, asks in RECEIPTS:
        f = os.path.join(SITE, "downloads", img)
        if not os.path.exists(f):
            print("  FAIL receipt image missing: downloads/%s" % img)
            return 1
        rows = "".join(
            '<p class="ask"><b>%s</b> <span class="where">on %s</span> %s</p>'
            % (html.escape(who), html.escape(where), html.escape(what))
            for who, where, what in asks)
        receipts += (
            '\n  <div class="receipt">\n'
            '   <img src="/downloads/%s" alt="%s" loading="lazy" decoding="async" width="132" height="168">\n'
            '   <div>\n    <h3>%s</h3>\n%s\n   </div>\n'
            '  </div>' % (img, html.escape(alt, quote=True), html.escape(headline), rows))

    body = """<main>
 <p class="eyebrow">Suggestions</p>
 <h1>Tell me what to <em>build next</em></h1>
 <p class="lede">This site has 52 tools and most of the recent changes to it came from people
 who wrote in. If something is missing, or something here is wrong, this is where to say so.</p>

 <form class="slip" id="slip" action="%(action)s" method="POST">
  <h2>Your slip</h2>
  <p class="hint">No account, no newsletter. It goes straight to my inbox.</p>

  <fieldset class="kinds">
   <legend>What kind of thing is this</legend>
   %(kinds)s
  </fieldset>

  <div class="row">
   <label class="fl" for="msg">What would you like?</label>
   <textarea id="msg" name="message" required
    placeholder="What were you trying to work out, and where did this site fall short? That is more useful than a feature name, because it often turns out an existing page needs fixing rather than a new one being built."></textarea>
  </div>

  <div class="row">
   <label class="fl" for="email">Email, only if you want a reply</label>
   <input id="email" type="email" name="email" autocomplete="email" placeholder="optional">
  </div>

  <input type="text" name="_gotcha" class="gotcha" tabindex="-1" autocomplete="off" aria-hidden="true">
  <input type="hidden" name="_subject" value="biochemtools suggestion">
  <input type="hidden" name="page" id="fromPage" value="">

  <button class="send" type="submit">Send it</button>
  <p class="slipnote">If you are reporting something wrong, the page it is on and the exact
  number you think is off is the most useful thing you can give me. A source is welcome but
  not required, and disagreeing with a textbook is fine as long as you say which one.</p>
  <div class="formmsg" id="formmsg" hidden></div>
 </form>

 <section class="receipts">
  <h2>What other people asked for, and what happened</h2>
  <p>Every name here is someone who sent a note and changed the site. Several of them are
  credited in the footers of the charts they fixed.</p>
%(receipts)s
 </section>
</main>
<script>
(function(){
 var f=document.getElementById("slip"), box=document.getElementById("formmsg");
 var from=new URLSearchParams(location.search).get("from");
 if(from && /^[a-z0-9\\-]+\\.html$/.test(from)) document.getElementById("fromPage").value=from;
 // If the action is not a real Formspree endpoint, posting would hit this page
 // itself, return 200, and we would cheerfully tell someone it sent. Hand them a
 // prefilled email instead, which is the honest failure.
 if(!/^https:\/\/formspree\.io\/f\/[A-Za-z0-9]+$/.test(f.getAttribute("action")||"")){
  f.addEventListener("submit", function(e){
   e.preventDefault();
   var kind=(f.querySelector("input[name=kind]:checked")||{}).value||"other";
   var body=f.querySelector("#msg").value+"\\n\\n--\\nkind: "+kind
     +"\\npage: "+(document.getElementById("fromPage").value||"(not given)");
   box.hidden=false; box.className="formmsg bad";
   box.innerHTML='The form is not connected right now. <a id="mailout">Send it as an email instead</a> and it still reaches me.';
   var a=document.getElementById("mailout");
   a.href="mailto:keonazadi1@gmail.com?subject="+encodeURIComponent("biochemtools suggestion")
     +"&body="+encodeURIComponent(body);
   a.click();
  });
  return;
 }
 if(!window.fetch) return;            // no JS fetch: the plain POST still works
 f.addEventListener("submit", function(e){
  e.preventDefault();
  var btn=f.querySelector(".send");
  btn.disabled=true; btn.textContent="Sending";
  fetch(f.action,{method:"POST",body:new FormData(f),headers:{Accept:"application/json"}})
   .then(function(r){ return r.ok ? r.json().then(function(){return true}) : false; })
   .then(function(ok){
    box.hidden=false;
    if(ok){
     f.querySelector(".kinds").style.display="none";
     f.querySelectorAll(".row").forEach(function(r){r.style.display="none"});
     btn.style.display="none";
     box.className="formmsg ok";
     box.textContent="Got it, thank you. I read every one of these, and if it changes something here you get credited on the thing you changed.";
    } else {
     box.className="formmsg bad";
     box.innerHTML='That did not send. You can email it instead: <a href="mailto:keonazadi1@gmail.com">keonazadi1@gmail.com</a>';
     btn.disabled=false; btn.textContent="Send it";
    }
   })
   .catch(function(){
    box.hidden=false; box.className="formmsg bad";
    box.innerHTML='That did not send. You can email it instead: <a href="mailto:keonazadi1@gmail.com">keonazadi1@gmail.com</a>';
    btn.disabled=false; btn.textContent="Send it";
   });
 });
})();
</script>
""" % dict(action=FORMSPREE, kinds=kind_html, receipts=receipts)

    out = "<!DOCTYPE html>\n<html lang=\"en\">\n" + head + "</head>\n" + nav + body + foot
    open(OUT, "w", encoding="utf-8").write(out)

    names = sum(len(a) for _, _, _, a in RECEIPTS)
    print("  suggest.html written: %d receipts, %d named contributors" % (len(RECEIPTS), names))
    return 0


if __name__ == "__main__":
    sys.exit(build())
