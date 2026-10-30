/* A flashcard that calls your bluff.
 *
 * These pages rank and nobody clicks, because a chart in a search result IS the
 * answer. The test is the one thing the result cannot contain. It is rendered at
 * build time as plain <details>, so it works, and is crawlable, with no
 * JavaScript at all; this file only upgrades it into one question at a time
 * where you have to commit before you see whether you were right.
 *
 * Motion encodes state and nothing else: the bar is how far through you are, the
 * flash is which row you should have read.
 */
(function () {
  var root = document.querySelector(".st-live[data-selftest]");
  if (!root) return;
  var bank;
  try { bank = JSON.parse(root.getAttribute("data-selftest")); }
  catch (e) { return; }                       // leave the <details> fallback alone
  if (!bank || !bank.length) return;

  var order = bank.map(function (_, i) { return i; });
  for (var i = order.length - 1; i > 0; i--) {   // shuffle, so a second go is not the same go
    var j = Math.floor(Math.random() * (i + 1));
    var t = order[i]; order[i] = order[j]; order[j] = t;
  }

  var at = 0, score = 0, answered = false;
  var el = {};
  root.innerHTML =
    '<div class="st-head"><span class="st-count"></span><span class="st-score" aria-live="polite"></span></div>' +
    '<div class="st-bar"><div class="st-fill"></div></div>' +
    '<p class="st-q" id="st-q"></p>' +
    '<div class="st-opts" role="group" aria-labelledby="st-q"></div>' +
    '<div class="st-why" role="status" aria-live="polite"></div>' +
    '<div class="st-foot"><button class="st-next" type="button"></button></div>';
  ["count", "score", "fill", "q", "opts", "why", "next"].forEach(function (k) {
    el[k] = root.querySelector(".st-" + k);
  });

  function render() {
    var item = bank[order[at]];
    answered = false;
    el.count.textContent = "Question " + (at + 1) + " of " + bank.length;
    el.score.textContent = score + " right";
    el.fill.style.width = (at / bank.length * 100) + "%";
    el.q.textContent = item.q;
    el.why.textContent = "";
    el.why.className = "st-why";
    el.next.style.display = "none";
    el.opts.innerHTML = "";
    item.options.forEach(function (text, idx) {
      var b = document.createElement("button");
      b.type = "button";
      b.className = "st-opt";
      b.textContent = text;
      b.addEventListener("click", function () { choose(idx, item, b); });
      el.opts.appendChild(b);
    });
  }

  function choose(idx, item, btn) {
    if (answered) return;
    answered = true;
    var right = idx === item.answer;
    if (right) score++;
    var buttons = el.opts.querySelectorAll(".st-opt");
    for (var k = 0; k < buttons.length; k++) {
      buttons[k].disabled = true;
      if (k === item.answer) buttons[k].classList.add("is-right");
    }
    if (!right) btn.classList.add("is-wrong");
    el.score.textContent = score + " right";
    el.fill.style.width = ((at + 1) / bank.length * 100) + "%";
    el.why.textContent = (right ? "Yes. " : "No. ") + item.why;
    el.why.className = "st-why " + (right ? "is-right" : "is-wrong");
    el.next.textContent = at + 1 < bank.length ? "Next question" : "See how you did";
    el.next.style.display = "";
    el.next.focus();
  }

  el.next.addEventListener("click", function () {
    at++;
    if (at < bank.length) { render(); return; }
    root.innerHTML =
      '<div class="st-head"><span class="st-count">Done</span>' +
      '<span class="st-score">' + score + " of " + bank.length + "</span></div>" +
      '<div class="st-bar"><div class="st-fill" style="width:100%"></div></div>' +
      '<p class="st-q">' + (score === bank.length
        ? "Every one. The table below is the part you already know."
        : "The ones you missed are all in the table below.") + "</p>" +
      '<div class="st-foot"><button class="st-next" type="button">Go again</button></div>';
    root.querySelector(".st-next").addEventListener("click", function () {
      at = 0; score = 0;
      root.innerHTML = "";
      location.reload();
    });
  });

  render();
})();
