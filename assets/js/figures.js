// Click (or tap, or Enter) on a figure opens its enlarged view; Escape, the close button
// or a click outside closes it. The same behaviour on every device and browser.
(function () {
  var root = document.documentElement;
  var current = null;

  function open(fig) {
    var lens = fig.querySelector(".lens");
    if (!lens) return;
    if (!lens.querySelector(".lens-close")) {
      var b = document.createElement("button");
      b.type = "button";
      b.className = "lens-close";
      b.setAttribute("aria-label", "Close the enlarged figure");
      b.textContent = "×";
      lens.insertBefore(b, lens.firstChild);
    }
    lens.removeAttribute("aria-hidden");
    lens.setAttribute("role", "dialog");
    lens.setAttribute("aria-label", "Enlarged figure");
    fig.classList.add("open");
    root.classList.add("lens-open");
    current = fig;
    lens.querySelector(".lens-close").focus({ preventScroll: true });
  }

  function close() {
    if (!current) return;
    var lens = current.querySelector(".lens");
    current.classList.remove("open");
    lens.setAttribute("aria-hidden", "true");
    lens.removeAttribute("role");
    lens.removeAttribute("aria-label");
    root.classList.remove("lens-open");
    current.focus({ preventScroll: true });
    current = null;
  }

  document.addEventListener("click", function (e) {
    if (current) {
      if (e.target.closest(".lens-close") || !e.target.closest(".lens")) close();
      return;
    }
    var fig = e.target.closest ? e.target.closest(".hoverable") : null;
    if (fig) open(fig);
  });

  document.addEventListener("keydown", function (e) {
    if (e.key === "Escape") { close(); return; }
    if ((e.key === "Enter" || e.key === " ") && !current && e.target.classList &&
        e.target.classList.contains("hoverable")) {
      e.preventDefault();
      open(e.target);
    }
  });
})();
