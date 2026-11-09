/* The training log.
 *
 * One engine over one shared bank, used by the quiz and the daily question.
 * Before this, quiz.html generated recall drills from the 20-row amino acid
 * table: finite, and exhausted the moment you learned twenty codes. That is
 * why it read as too easy.
 *
 * The label a person sees is DERIVED from what the question asks, never stored
 * alongside it, so the two cannot drift apart as the bank grows:
 *     recall -> Easy, apply -> Medium, exam -> Hard
 *
 * Retention lives in localStorage and nowhere else. No account, no server,
 * nothing leaves the device. What it remembers is what you got wrong, so it
 * can bring it back.
 */
(function () {
  "use strict";

  var LABEL = { recall: "Easy", apply: "Medium", exam: "Hard" };
  var ASKS  = { recall: "Recall", apply: "Apply", exam: "Exam" };
  var ORDER = ["recall", "apply", "exam"];
  var KEY_SEEN = "bct_q_seen";       // {id: {n, wrong, last}}
  var KEY_FRAME = "bct_q_frame";     // "level" | "asks"
  var KEY_STREAK = "bct_q_days";     // [yyyy-mm-dd]

  function store(k, fallback) {
    try { return JSON.parse(localStorage.getItem(k)) || fallback; }
    catch (e) { return fallback; }
  }
  function save(k, v) {
    try { localStorage.setItem(k, JSON.stringify(v)); } catch (e) {}
  }
  function today() { return new Date().toISOString().slice(0, 10); }

  function markDay() {
    var d = store(KEY_STREAK, []);
    if (d[d.length - 1] !== today()) { d.push(today()); save(KEY_STREAK, d.slice(-400)); }
  }
  function streakLength() {
    var d = store(KEY_STREAK, []), n = 0, cur = new Date();
    for (;;) {
      var s = cur.toISOString().slice(0, 10);
      if (d.indexOf(s) === -1) break;
      n++; cur.setDate(cur.getDate() - 1);
    }
    return n;
  }

  /* Pick questions. Never-seen first, then ones you got wrong, then the rest
   * oldest-first. This is the whole retention mechanic: a miss comes back. */
  function pick(pool, n) {
    var seen = store(KEY_SEEN, {});
    var scored = pool.map(function (q) {
      var s = seen[q.id] || { n: 0, wrong: 0, last: "" };
      var rank = s.n === 0 ? 0 : (s.wrong > 0 ? 1 : 2);
      return { q: q, rank: rank, wrong: s.wrong, last: s.last, r: Math.random() };
    });
    scored.sort(function (a, b) {
      if (a.rank !== b.rank) return a.rank - b.rank;
      if (a.rank === 1 && a.wrong !== b.wrong) return b.wrong - a.wrong;
      if (a.last !== b.last) return a.last < b.last ? -1 : 1;
      return a.r - b.r;
    });
    return scored.slice(0, n).map(function (x) { return x.q; });
  }

  function record(q, right) {
    var seen = store(KEY_SEEN, {});
    var s = seen[q.id] || { n: 0, wrong: 0, last: "" };
    s.n++; if (!right) s.wrong++; else if (s.wrong > 0) s.wrong--;  // a right answer pays down the debt
    s.last = today();
    seen[q.id] = s; save(KEY_SEEN, seen);
  }

  /* Mastery: of the questions you have met in a subject, the share you are not
   * currently getting wrong, scaled by how much of the subject you have met.
   * Deliberately falls when you stop, because that is what retention means. */
  function mastery(bank) {
    var seen = store(KEY_SEEN, {}), out = {};
    bank.forEach(function (q) {
      var m = out[q.subject] || (out[q.subject] = { total: 0, met: 0, solid: 0 });
      m.total++;
      var s = seen[q.id];
      if (s && s.n) { m.met++; if (!s.wrong) m.solid++; }
    });
    Object.keys(out).forEach(function (k) {
      var m = out[k];
      m.pct = m.total ? Math.round(100 * m.solid / m.total) : 0;
      m.metPct = m.total ? Math.round(100 * m.met / m.total) : 0;
    });
    return out;
  }

  window.BCTQuiz = {
    LABEL: LABEL, ASKS: ASKS, ORDER: ORDER,
    frame: function () { return store(KEY_FRAME, "level") === "asks" ? ASKS : LABEL; },
    setFrame: function (f) { save(KEY_FRAME, f); },
    frameName: function () { return store(KEY_FRAME, "level"); },
    pick: pick, record: record, mastery: mastery,
    markDay: markDay, streak: streakLength,
    wrongCount: function () {
      var seen = store(KEY_SEEN, {}), n = 0;
      Object.keys(seen).forEach(function (k) { if (seen[k].wrong > 0) n++; });
      return n;
    },
    reset: function () { save(KEY_SEEN, {}); }
  };
})();
