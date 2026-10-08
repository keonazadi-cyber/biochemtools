#!/usr/bin/env python3
"""Send near-miss URLs to the page they meant, instead of a dead end.

Cloudflare shows real weekly traffic arriving at URLs that do not exist:
/dna, /genetic-code-codon-chart/, /buffer-pKa-table, /amino-acid-chart/ and
/michaelis-Menten-vs-lineweaver-burk.html, which Google has indexed at position 1.

GitHub Pages serves static files and cannot do server-side redirects, and the
obvious fix of adding a file at the miscased path is impossible here anyway:
macOS is case-insensitive, so michaelis-Menten-... and michaelis-menten-... are
the same file on disk.

So the rescue runs on 404.html itself, which GitHub Pages already serves for any
unknown path. It normalises the requested path and, when that lands on exactly one
real page, goes there. When it is ambiguous it lists the candidates rather than
guessing, because sending someone to the wrong page is worse than asking.

The page list is written in at build time from the files on disk, so it cannot go
stale the way a hand-kept redirect table does.

Note this does not make Google see a 200. The URL still returns 404 and Google
will eventually drop it, which for a miscased duplicate is the right outcome. What
it fixes is the person who followed the link.
"""
import os, re, glob, json, sys

SITE = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..")
P404 = os.path.join(SITE, "404.html")

# Slugs seen in the wild that do not normalise onto a page by themselves.
# Keep this short; the normaliser handles case, slashes and the .html suffix.
ALIASES = {
    "genetic-code-codon-chart": "codon-chart.html",
    "genetic-code": "codon-chart.html",
    "codon-table": "codon-chart.html",
    "amino-acids": "amino-acid-chart.html",
    "amino-acid-table": "amino-acid-chart.html",
    "titration-curves": "amino-acid-titration-curve.html",
    "equations": "biochem-equation-sheet.html",
    "formula-sheet": "biochem-equation-sheet.html",
    "buffers": "buffer-pka-table.html",
}

START = "<!-- rescue:start -->"
END = "<!-- rescue:end -->"


def main():
    pages = sorted(os.path.basename(p) for p in glob.glob(os.path.join(SITE, "*.html"))
                   if os.path.basename(p) != "404.html")
    for slug, target in ALIASES.items():
        if target not in pages:
            print("  FAIL alias %s points at %s, which does not exist" % (slug, target))
            return 1

    # The decision is a pure function on window so it can be tested directly,
    # rather than only by navigating and seeing where you land.
    script = """%s
<script>
(function(){
 var PAGES=%s;
 var ALIAS=%s;
 window.__rescue=function(pathname){
  var raw=String(pathname||"").replace(/^\\/+/,"").replace(/\\/+$/,"");
  if(!raw) return {action:"none", why:"empty path"};
  var slug;
  try{ slug=decodeURIComponent(raw); }catch(e){ slug=raw; }
  slug=slug.toLowerCase().replace(/\\.html$/,"");
  if(ALIAS[slug]) return {action:"go", to:ALIAS[slug], why:"alias"};
  var exact=slug+".html";
  for(var i=0;i<PAGES.length;i++){
   if(PAGES[i].toLowerCase()===exact) return {action:"go", to:PAGES[i], why:"case or suffix"};
  }
  var hits=PAGES.filter(function(p){ return p.toLowerCase().indexOf(slug)===0; });
  if(hits.length===1) return {action:"go", to:hits[0], why:"only one page starts with it"};
  if(hits.length>1) return {action:"suggest", hits:hits.slice(0,6), why:"ambiguous"};
  return {action:"none", why:"no match"};
 };
 var r=window.__rescue(location.pathname);
 if(r.action==="go"){ location.replace("/"+r.to+location.search+location.hash); return; }
 if(r.action==="suggest"){
  var box=document.getElementById("rescue-suggestions");
  if(box){
   var ACR=/^(dna|rna|atp|adp|nad|fad|ph|pi|pka|mcat|hiv|uv|tca|gdp|gtp)$/i;
   box.innerHTML="<h2>Did you mean</h2>"+r.hits.map(function(p){
    var n=p.replace(/\\.html$/,"").replace(/-/g," ").split(" ").map(function(w,i){
     if(ACR.test(w)) return w.toUpperCase();
     return i===0 ? w.charAt(0).toUpperCase()+w.slice(1) : w;
    }).join(" ");
    return '<a href="/'+p+'">'+n+"</a>";
   }).join("");
   box.style.display="";
  }
 }
})();
</script>
%s""" % (START, json.dumps(pages), json.dumps(ALIASES), END)

    h = open(P404, encoding="utf-8").read()
    h = re.sub(re.escape(START) + r"[\s\S]*?" + re.escape(END), "", h)
    # .card does nothing on this page; .popular is its panel style. Placed before
    # the generic tool list, because a specific guess beats a generic list.
    if 'id="rescue-suggestions"' not in h:
        anchor = '<div class="popular">'
        if anchor not in h:
            print("  FAIL no .popular block in 404.html to anchor the suggestion box")
            return 1
        h = h.replace(anchor,
                      '<div class="popular" id="rescue-suggestions" style="display:none"></div>\n'
                      ' ' + anchor, 1)
    h = h.replace("</body>", script + "\n</body>", 1)

    if h.count(START) != 1:
        print("  FAIL rescue block appears %d times" % h.count(START))
        return 1
    open(P404, "w", encoding="utf-8").write(h)
    print("  404 rescue rebuilt: %d pages known, %d aliases" % (len(pages), len(ALIASES)))
    return 0


if __name__ == "__main__":
    sys.exit(main())
