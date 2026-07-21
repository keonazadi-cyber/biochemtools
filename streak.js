(function(){
"use strict";
var TOOL_COUNT = 20;
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

function isToolPage(){
 var p = location.pathname.replace(/^\//,"").replace(/\.html$/,"");
 return p && p !== "index" && p !== "about" && p !== "privacy" && p !== "contact";
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
 if (document.body.firstChild){
  document.body.insertBefore(bar, document.body.firstChild);
 } else {
  document.body.appendChild(bar);
 }
}

function renderAll(){
 renderStreakWidget();
 renderToolBadge();
}

recordVisit();
if (document.readyState === "loading"){
 document.addEventListener("DOMContentLoaded", renderAll);
} else {
 renderAll();
}

window.BCT = { recordQuizCompletion: recordQuizCompletion, quizBest: quizBest, currentStreak: currentStreak, toolsTried: toolsTried };
})();
