/* The training log, on screen. Reads BCTQuiz for state, /questions.json for
 * content. Renders into [data-quiz]; the build leaves a plain <details> set
 * inside it, which is what a crawler and a no-JavaScript visitor read. */
(function () {
  "use strict";
  var root = document.querySelector("[data-quiz]");
  if (!root || !window.BCTQuiz) return;
  var Q = window.BCTQuiz, BANK = [], SUBJECTS = [];
  var sel = { type: "all", subject: "all", mode: "practice" };
  var run = null;

  fetch("/questions.json").then(function (r) { return r.json(); }).then(function (d) {
    BANK = d.questions || [];
    SUBJECTS = d.subjects || [];
    root.innerHTML = "";
    home();
  }).catch(function () { /* leave the no-JS fallback exactly as it is */ });

  function el(tag, cls, text) {
    var e = document.createElement(tag);
    if (cls) e.className = cls;
    if (text != null) e.textContent = text;
    return e;
  }
  function pool() {
    return BANK.filter(function (q) {
      return (sel.type === "all" || q.type === sel.type) &&
             (sel.subject === "all" || q.subject === sel.subject);
    });
  }
  function chip(label, on, fn) {
    var b = el("button", "q-chip" + (on ? " on" : ""), label);
    b.type = "button";
    b.addEventListener("click", fn);
    return b;
  }

  function home() {
    root.innerHTML = "";
    var F = Q.frame();

    var head = el("div", "q-head");
    var st = Q.streak();
    head.appendChild(el("span", "q-streak",
      st ? st + (st === 1 ? " day streak" : " day streak") : "No streak yet"));
    var wrong = Q.wrongCount();
    head.appendChild(el("span", "q-owed",
      wrong ? wrong + " to come back to" : "Nothing owed"));
    root.appendChild(head);

    // level, named the way this visitor chose
    var lv = el("div", "q-row");
    lv.appendChild(el("span", "q-lab", "Level"));
    lv.appendChild(chip("All", sel.type === "all", function () { sel.type = "all"; home(); }));
    Q.ORDER.forEach(function (t) {
      var n = BANK.filter(function (q) { return q.type === t; }).length;
      lv.appendChild(chip(F[t] + " (" + n + ")", sel.type === t,
        function () { sel.type = t; home(); }));
    });
    var sw = el("button", "q-frame",
      Q.frameName() === "level" ? "call them Recall, Apply, Exam"
                                : "call them Easy, Medium, Hard");
    sw.type = "button";
    sw.addEventListener("click", function () {
      Q.setFrame(Q.frameName() === "level" ? "asks" : "level"); home();
    });
    lv.appendChild(sw);
    root.appendChild(lv);

    var sb = el("div", "q-row");
    sb.appendChild(el("span", "q-lab", "Subject"));
    sb.appendChild(chip("Mixed", sel.subject === "all",
      function () { sel.subject = "all"; home(); }));
    SUBJECTS.forEach(function (s) {
      sb.appendChild(chip(s, sel.subject === s, function () { sel.subject = s; home(); }));
    });
    root.appendChild(sb);

    var md = el("div", "q-row");
    md.appendChild(el("span", "q-lab", "Mode"));
    md.appendChild(chip("Practice", sel.mode === "practice",
      function () { sel.mode = "practice"; home(); }));
    md.appendChild(chip("Practice test", sel.mode === "test",
      function () { sel.mode = "test"; home(); }));
    root.appendChild(md);

    var n = pool().length;
    var go = el("button", "q-go",
      n === 0 ? "No questions match yet"
              : (sel.mode === "test" ? "Start a " + Math.min(20, n) + " question test"
                                     : "Start, " + Math.min(10, n) + " questions"));
    go.type = "button";
    go.disabled = n === 0;
    go.addEventListener("click", start);
    root.appendChild(go);

    var hint = el("p", "q-hint", sel.mode === "test"
      ? "No feedback until the end, like the real thing."
      : "You get the answer and the reason straight away. Anything you miss comes back.");
    root.appendChild(hint);

    root.appendChild(masteryGrid());
  }

  function masteryGrid() {
    var wrap = el("div", "q-mastery");
    wrap.appendChild(el("h3", null, "What you have actually got down"));
    var m = Q.mastery(BANK);
    SUBJECTS.forEach(function (s) {
      var d = m[s] || { pct: 0, met: 0, total: 0, metPct: 0 };
      var row = el("div", "q-mrow");
      row.appendChild(el("span", "q-mname", s));
      var bar = el("div", "q-mbar");
      var met = el("div", "q-mmet"); met.style.width = d.metPct + "%";
      var fill = el("div", "q-mfill"); fill.style.width = d.pct + "%";
      bar.appendChild(met); bar.appendChild(fill);
      row.appendChild(bar);
      row.appendChild(el("span", "q-mpct", d.pct + "%"));
      wrap.appendChild(row);
    });
    wrap.appendChild(el("p", "q-hint",
      "The solid bar is what you get right without a miss on record. The faint "
      + "bar behind it is how much of the subject you have met at all. It falls "
      + "when you stop, which is the point."));
    return wrap;
  }

  function start() {
    var n = sel.mode === "test" ? 20 : 10;
    run = { qs: Q.pick(pool(), n), at: 0, right: 0, answers: [] };
    Q.markDay();
    step();
  }

  function step() {
    if (run.at >= run.qs.length) return finish();
    var q = run.qs[run.at], F = Q.frame();
    root.innerHTML = "";

    var bar = el("div", "q-prog");
    var fill = el("div", "q-progfill");
    fill.style.width = (run.at / run.qs.length * 100) + "%";
    bar.appendChild(fill);

    var head = el("div", "q-head");
    head.appendChild(el("span", "q-streak",
      "Question " + (run.at + 1) + " of " + run.qs.length));
    head.appendChild(el("span", "q-owed", q.subject + " · " + F[q.type]));
    root.appendChild(head);
    root.appendChild(bar);

    root.appendChild(el("p", "q-q", q.q));
    var opts = el("div", "q-opts");
    q.choices.forEach(function (c, i) {
      var b = el("button", "q-opt", c);
      b.type = "button";
      b.addEventListener("click", function () { answer(i, b); });
      opts.appendChild(b);
    });
    root.appendChild(opts);
    root.appendChild(el("div", "q-why"));
    var next = el("button", "q-next", "Next");
    next.type = "button";
    next.style.display = "none";
    next.addEventListener("click", function () { run.at++; step(); });
    root.appendChild(next);
  }

  function answer(i, btn) {
    var q = run.qs[run.at];
    if (btn.disabled) return;
    var right = i === q.correct;
    if (right) run.right++;
    run.answers.push({ q: q, chose: i, right: right });
    Q.record(q, right);

    var opts = root.querySelectorAll(".q-opt");
    for (var k = 0; k < opts.length; k++) opts[k].disabled = true;
    if (sel.mode === "practice") {
      opts[q.correct].classList.add("is-right");
      if (!right) btn.classList.add("is-wrong");
      var why = root.querySelector(".q-why");
      why.textContent = (right ? "Yes. " : "No. ") + q.explain;
      why.className = "q-why " + (right ? "is-right" : "is-wrong");
      if (q.tool) {
        var a = el("a", "q-tool", "Open the tool for this");
        a.href = "/" + q.tool + (q.tool.indexOf(".html") === -1 ? ".html" : "");
        why.appendChild(document.createTextNode(" "));
        why.appendChild(a);
      }
    }
    var next = root.querySelector(".q-next");
    next.textContent = run.at + 1 < run.qs.length ? "Next" : "See how you did";
    next.style.display = "";
    next.focus();
  }

  function finish() {
    root.innerHTML = "";
    var pct = Math.round(100 * run.right / run.qs.length);
    root.appendChild(el("h3", "q-score", run.right + " of " + run.qs.length));
    root.appendChild(el("p", "q-hint", pct === 100
      ? "Clean. Try a level up, or mix the subjects."
      : "The ones you missed are now first in the queue next time."));

    var missed = run.answers.filter(function (a) { return !a.right; });
    if (missed.length) {
      var list = el("div", "q-missed");
      list.appendChild(el("h3", null, "What to look at"));
      missed.forEach(function (a) {
        var d = document.createElement("details");
        var s = document.createElement("summary");
        s.textContent = a.q.q;
        d.appendChild(s);
        d.appendChild(el("p", "q-ans", a.q.choices[a.q.correct]));
        d.appendChild(el("p", "q-exp", a.q.explain));
        if (a.q.tool) {
          var p = el("p", "q-exp");
          var link = el("a", "q-tool", "Open the tool for this");
          link.href = "/" + a.q.tool + (a.q.tool.indexOf(".html") === -1 ? ".html" : "");
          p.appendChild(link); d.appendChild(p);
        }
        list.appendChild(d);
      });
      root.appendChild(list);
    }
    var again = el("button", "q-go", "Go again");
    again.type = "button";
    again.addEventListener("click", home);
    root.appendChild(again);
    root.appendChild(masteryGrid());
  }
})();

/* The daily question, drawing from the same shared bank.
 *
 * It used to carry its own inline 80-question copy, which is how the two
 * systems drifted apart: the quiz could not see these questions and this page
 * could not see a difficulty. Same bank now, with a level you pick.
 *
 * The question is seeded by the date, so everyone on a given level gets the
 * same one on a given day and it does not reshuffle when you reload. */
(function () {
  "use strict";
  var root = document.querySelector("[data-daily]");
  if (!root || !window.BCTQuiz) return;
  var Q = window.BCTQuiz, BANK = [];
  var lvl = "all", answered = false;

  fetch("/questions.json").then(function (r) { return r.json(); }).then(function (d) {
    BANK = d.questions || [];
    root.innerHTML = "";
    render();
  }).catch(function () { /* the build-time fallback stays */ });

  function el(t, c, x) {
    var e = document.createElement(t);
    if (c) e.className = c;
    if (x != null) e.textContent = x;
    return e;
  }
  function daySeed() {
    var d = new Date(), s = d.getUTCFullYear() * 1000 + d.getUTCMonth() * 40 + d.getUTCDate();
    return s;
  }
  function todaysQuestion() {
    var pool = BANK.filter(function (q) { return lvl === "all" || q.type === lvl; });
    if (!pool.length) return null;
    return pool[daySeed() % pool.length];
  }

  function render() {
    answered = false;
    root.innerHTML = "";
    var F = Q.frame(), q = todaysQuestion();

    var row = el("div", "q-row");
    row.appendChild(el("span", "q-lab", "Level"));
    ["all"].concat(Q.ORDER).forEach(function (t) {
      var b = el("button", "q-chip" + (lvl === t ? " on" : ""),
                 t === "all" ? "Any" : F[t]);
      b.type = "button";
      b.addEventListener("click", function () { lvl = t; render(); });
      row.appendChild(b);
    });
    root.appendChild(row);

    if (!q) { root.appendChild(el("p", "q-hint", "No question at that level yet.")); return; }

    var head = el("div", "q-head");
    head.appendChild(el("span", "q-streak",
      Q.streak() ? Q.streak() + " day streak" : "Start a streak today"));
    head.appendChild(el("span", "q-owed", q.subject + " · " + F[q.type]));
    root.appendChild(head);

    root.appendChild(el("p", "q-q", q.q));
    var opts = el("div", "q-opts");
    q.choices.forEach(function (c, i) {
      var b = el("button", "q-opt", c);
      b.type = "button";
      b.addEventListener("click", function () { answer(q, i, b, opts); });
      opts.appendChild(b);
    });
    root.appendChild(opts);
    root.appendChild(el("div", "q-why"));
  }

  function answer(q, i, btn, opts) {
    if (answered) return;
    answered = true;
    var right = i === q.correct;
    Q.record(q, right);
    Q.markDay();
    var bs = opts.querySelectorAll(".q-opt");
    for (var k = 0; k < bs.length; k++) bs[k].disabled = true;
    bs[q.correct].classList.add("is-right");
    if (!right) btn.classList.add("is-wrong");
    var why = root.querySelector(".q-why");
    why.textContent = (right ? "Yes. " : "No. ") + q.explain;
    why.className = "q-why " + (right ? "is-right" : "is-wrong");
    var more = el("p", "q-hint", "");
    var a = el("a", "q-tool", "Want more than one? Practice questions at three levels.");
    a.href = "/practice.html";
    more.appendChild(a);
    root.appendChild(more);
  }
})();
