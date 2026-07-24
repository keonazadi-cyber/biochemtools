(function(){
"use strict";
var TOOL_COUNT = 32;

// --- Affiliate links: each program activates independently once you have a real tracked link/tag. ---
var AMAZON_LIVE = true;
var AMAZON_TAG = "biochemtools20";
var GOLDSTANDARD_LIVE = false;
var GOLDSTANDARD_URL = "https://www.mcat-prep.com/goldstandard-affiliate/";
var VISITS_KEY = "bct_visits";
var QUIZ_KEY = "bct_quiz_dates";

function todayStr(){
 var d = new Date();
 return d.getFullYear() + "-" + String(d.getMonth()+1).padStart(2,"0") + "-" + String(d.getDate()).padStart(2,"0");
}
function daysAgoStr(n){
 var d = new Date();
 d.setDate(d.getDate() - n);
 return d.getFullYear() + "-" + String(d.getMonth()+1).padStart(2,"0") + "-" + String(d.getDate()).padStart(2,"0");
}
function load(key){
 try { return JSON.parse(localStorage.getItem(key) || "[]"); } catch(e){ return []; }
}
function save(key, arr){
 try { localStorage.setItem(key, JSON.stringify(arr.slice(-90))); } catch(e){}
}

var NON_TOOL_PAGES = ["index","about","privacy","contact","404","daily-question",
 "how-to-calculate-pi-without-a-calculator","mcat-buffer-questions-explained","michaelis-menten-vs-lineweaver-burk"];
function isToolPage(){
 var p = location.pathname.replace(/^\//,"").replace(/\.html$/,"");
 return !!p && NON_TOOL_PAGES.indexOf(p) === -1;
}

function recordVisit(){
 var visits = load(VISITS_KEY);
 var today = todayStr();
 if (visits.indexOf(today) === -1) visits.push(today);
 save(VISITS_KEY, visits);

 if (isToolPage()){
  var slug = location.pathname.replace(/^\//,"").replace(/\.html$/,"");
  var toolsKey = "bct_tools_seen";
  var seen = load(toolsKey);
  if (seen.indexOf(slug) === -1) seen.push(slug);
  save(toolsKey, seen);
 }
}

function currentStreak(){
 var visits = load(VISITS_KEY);
 var set = {};
 visits.forEach(function(d){ set[d] = true; });
 var today = todayStr();
 var streak = 0;
 var startIdx = set[today] ? 0 : (set[daysAgoStr(1)] ? 1 : null);
 if (startIdx === null) return 0;
 var i = startIdx;
 while (set[daysAgoStr(i)]) { streak++; i++; }
 return streak;
}

function toolsTried(){
 return load("bct_tools_seen").length;
}

function recordQuizCompletion(score, total){
 var dates = load(QUIZ_KEY);
 dates.push(todayStr());
 save(QUIZ_KEY, dates);
 try {
  var best = parseInt(localStorage.getItem("bct_quiz_best") || "0", 10);
  if (score > best) localStorage.setItem("bct_quiz_best", String(score));
 } catch(e){}
}
function quizBest(){
 try { return parseInt(localStorage.getItem("bct_quiz_best") || "0", 10); } catch(e){ return 0; }
}

function recordDailyQuestion(correct){
 var dates = load("bct_dq_dates");
 var today = todayStr();
 if (dates.indexOf(today) === -1) dates.push(today);
 save("bct_dq_dates", dates);
 if (correct){
  var right = load("bct_dq_correct");
  if (right.indexOf(today) === -1) right.push(today);
  save("bct_dq_correct", right);
 }
}

function renderStreakWidget(){
 var el = document.getElementById("streak-widget");
 if (!el) return;
 var streak = currentStreak();
 var tried = Math.min(toolsTried(), TOOL_COUNT);
 if (streak === 0 && tried === 0){
  el.innerHTML = "";
  return;
 }
 var streakLine = streak > 0
  ? "<div style=\"font-size:1.6rem;font-weight:600;color:var(--accent)\">" + streak + " day" + (streak===1?"":"s") + " 🔥</div><div style=\"color:var(--muted);font-size:.82rem;margin-top:.15rem\">current study streak</div>"
  : "<div style=\"color:var(--muted);font-size:.88rem\">Visit again tomorrow to start a streak.</div>";
 el.innerHTML =
  "<h4>Your progress</h4>" +
  streakLine +
  "<div style=\"margin-top:.9rem;padding-top:.9rem;border-top:1px solid var(--line);color:var(--muted);font-size:.85rem\">" +
   tried + " / " + TOOL_COUNT + " tools tried" +
  "</div>";
}

function renderToolBadge(){
 if (!isToolPage()) return;
 if (document.getElementById("streak-widget")) return;
 if (document.getElementById("tool-streak-badge")) return;
 var streak = currentStreak();
 var tried = Math.min(toolsTried(), TOOL_COUNT);
 if (streak === 0 && tried === 0) return;
 var bar = document.createElement("div");
 bar.id = "tool-streak-badge";
 bar.style.cssText = "text-align:center;padding:.5rem 1rem;font-size:.82rem;color:var(--muted,#9aa0aa);background:var(--card,#1a1d24);border-bottom:1px solid var(--line,#2a2e38)";
 var parts = [];
 if (streak > 0) parts.push("🔥 " + streak + "-day streak");
 parts.push(tried + "/" + TOOL_COUNT + " tools tried");
 bar.innerHTML = parts.join(" &nbsp;&middot;&nbsp; ");
 var topnav = document.querySelector(".topnav");
 if (topnav){
  document.body.insertBefore(bar, topnav.nextSibling);
 } else if (document.body.firstChild){
  document.body.insertBefore(bar, document.body.firstChild);
 } else {
  document.body.appendChild(bar);
 }
}

function adjustStickyOffsets(){
 var nav = document.querySelector(".topnav");
 var badge = document.getElementById("tool-streak-badge");
 var h = (nav ? nav.getBoundingClientRect().height : 0) + (badge ? badge.getBoundingClientRect().height : 0);
 if (h > 0) document.documentElement.style.setProperty("--sticky-offset", h + "px");
}

var SHARE_EXCLUDE = ["about","privacy","contact","404"];
function shouldShowShare(){
 var p = location.pathname.replace(/^\//,"").replace(/\.html$/,"") || "index";
 return SHARE_EXCLUDE.indexOf(p) === -1;
}

function showToast(msg){
 var t = document.getElementById("bct-toast");
 if (!t){
  t = document.createElement("div");
  t.id = "bct-toast";
  t.style.cssText = "position:fixed;bottom:5rem;right:1.25rem;background:var(--card,#1a1d24);color:var(--txt,#e8eaed);border:1px solid var(--line,#2a2e38);padding:.6rem 1rem;border-radius:8px;font-size:.85rem;z-index:41;box-shadow:0 2px 10px rgba(0,0,0,.35);opacity:0;transition:opacity .2s;pointer-events:none";
  document.body.appendChild(t);
 }
 t.textContent = msg;
 t.style.opacity = "1";
 clearTimeout(t._hideTimer);
 t._hideTimer = setTimeout(function(){ t.style.opacity = "0"; }, 1800);
}

function fallbackCopy(text){
 var ta = document.createElement("textarea");
 ta.value = text;
 ta.style.cssText = "position:fixed;opacity:0;top:0;left:0";
 document.body.appendChild(ta);
 ta.focus(); ta.select();
 try { document.execCommand("copy"); showToast("Link copied!"); }
 catch(e){ showToast("Couldn't copy — grab the URL from the address bar."); }
 document.body.removeChild(ta);
}

function doShare(){
 var url = location.href, title = document.title;
 if (navigator.share){
  navigator.share({title: title, url: url}).catch(function(){});
  return;
 }
 if (navigator.clipboard && navigator.clipboard.writeText){
  navigator.clipboard.writeText(url).then(function(){ showToast("Link copied!"); }).catch(function(){ fallbackCopy(url); });
 } else {
  fallbackCopy(url);
 }
}

function renderShareButton(){
 if (!shouldShowShare()) return;
 if (document.getElementById("bct-share-btn")) return;
 var btn = document.createElement("button");
 btn.id = "bct-share-btn";
 btn.type = "button";
 btn.setAttribute("aria-label", "Share this page");
 btn.title = "Share this page";
 btn.style.cssText = "position:fixed;bottom:1.25rem;right:1.25rem;z-index:40;display:flex;align-items:center;gap:.4rem;background:#5dcaa5;color:#0b0d11;border:none;border-radius:99px;padding:.65rem 1.1rem;font-size:.85rem;font-weight:600;cursor:pointer;box-shadow:0 4px 14px rgba(0,0,0,.35);font-family:inherit";
 btn.innerHTML = "<span aria-hidden=\"true\">&#8599;</span> Share";
 btn.addEventListener("click", doShare);
 document.body.appendChild(btn);
}

function renderRecommended(){
 var el = document.getElementById("recommended-slot");
 if (!el || (!AMAZON_LIVE && !GOLDSTANDARD_LIVE)) return;
 var links = "";
 if (AMAZON_LIVE){
  var mcatBooks = [
   ["1506297544", "Kaplan MCAT Complete 7-Book Subject Review"],
   ["0593518918", "Princeton Review MCAT Subject Review Box Set"],
   ["1577541731", "AAMC Official Guide to the MCAT Exam"]
  ];
  for (var bi = 0; bi < mcatBooks.length; bi++){
   var bookHref = "https://www.amazon.com/dp/" + mcatBooks[bi][0] + "?tag=" + encodeURIComponent(AMAZON_TAG);
   links += "<a href=\"" + bookHref + "\" target=\"_blank\" rel=\"noopener sponsored\" style=\"display:block;color:var(--accent,#5dcaa5);text-decoration:none;font-size:.88rem;margin-bottom:.4rem\">" + mcatBooks[bi][1] + " &rarr;</a>";
  }
 }
 if (GOLDSTANDARD_LIVE){
  links += "<a href=\"" + GOLDSTANDARD_URL + "\" target=\"_blank\" rel=\"noopener sponsored\" style=\"display:block;color:var(--accent,#5dcaa5);text-decoration:none;font-size:.88rem;margin-bottom:.4rem\">Gold Standard MCAT prep course &rarr;</a>";
 }
 el.style.cssText = "background:var(--card,#1a1d24);border:1px solid var(--line,#2a2e38);border-radius:14px;padding:1.25rem";
 el.innerHTML =
  "<h4 style=\"margin:0 0 .5rem;font-size:.8rem;color:var(--muted,#9aa0aa);text-transform:uppercase;letter-spacing:.06em;font-weight:500\">Study resources we recommend</h4>" +
  links +
  "<p style=\"color:var(--muted,#9aa0aa);font-size:.72rem;margin:.7rem 0 0\">As an affiliate, we may earn a commission on qualifying purchases through these links, at no extra cost to you. We only recommend resources we'd actually tell a friend to use.</p>";
}

// Expose single-select toggle-group state (the ".on"/".active" button) to
// assistive tech via aria-pressed, syncing after each page's own click handler.
// Covers .modes / .aa-grid / .frames groups on every page in one place.
function isSelectedToggle(b){ return b.classList.contains("on") || b.classList.contains("active"); }
function syncToggleA11y(){
 var groups = document.querySelectorAll(".modes, .aa-grid, .frames");
 for (var g = 0; g < groups.length; g++){
  (function(group){
   var btns = group.querySelectorAll("button");
   if (!btns.length) return;
   function resync(){ for (var i = 0; i < btns.length; i++){ btns[i].setAttribute("aria-pressed", isSelectedToggle(btns[i]) ? "true" : "false"); } }
   resync();
   for (var j = 0; j < btns.length; j++){ btns[j].addEventListener("click", function(){ setTimeout(resync, 0); }); }
  })(groups[g]);
 }
}

function renderAll(){
 renderStreakWidget();
 renderToolBadge();
 renderShareButton();
 renderRecommended();
 syncToggleA11y();
 requestAnimationFrame(function(){ requestAnimationFrame(adjustStickyOffsets); });
 window.addEventListener("load", adjustStickyOffsets);
}

recordVisit();
if (document.readyState === "loading"){
 document.addEventListener("DOMContentLoaded", renderAll);
} else {
 renderAll();
}

window.BCT = { recordQuizCompletion: recordQuizCompletion, quizBest: quizBest, currentStreak: currentStreak, toolsTried: toolsTried, recordDailyQuestion: recordDailyQuestion };
})();
