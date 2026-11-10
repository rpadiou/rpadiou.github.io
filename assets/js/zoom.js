// Click (or Enter) on a figure of a post opens the enlarged image; Escape, the x or a click outside closes it.
(function () {
  var overlay = null;
  function close() { if (overlay) { overlay.remove(); overlay = null; } }
  function open(img) {
    close();
    overlay = document.createElement("div"); overlay.className = "sk-zoom";
    var box = document.createElement("div"); box.className = "sk-zoom-box"; box.setAttribute("role", "dialog"); box.setAttribute("aria-label", "Enlarged figure");
    var x = document.createElement("button"); x.type = "button"; x.className = "sk-zoom-x"; x.textContent = "×"; x.setAttribute("aria-label", "Close");
    var big = document.createElement("img"); big.src = img.currentSrc || img.src; big.alt = img.alt;
    box.appendChild(x); box.appendChild(big);
    var cap = img.parentNode.querySelector("figcaption");
    if (cap) { var p = document.createElement("p"); p.innerHTML = cap.innerHTML; box.appendChild(p); }
    overlay.appendChild(box); (document.querySelector(".sk") || document.body).appendChild(overlay);
    overlay.addEventListener("click", function (e) { if (e.target === overlay || e.target === x) close(); });
    x.focus();
  }
  document.addEventListener("DOMContentLoaded", function () {
    Array.prototype.forEach.call(document.querySelectorAll(".sk figure img"), function (img) {
      img.classList.add("zoomable"); img.tabIndex = 0;
      img.addEventListener("click", function () { open(img); });
      img.addEventListener("keydown", function (e) { if (e.key === "Enter" || e.key === " ") { e.preventDefault(); open(img); } });
    });
  });
  document.addEventListener("keydown", function (e) { if (e.key === "Escape") close(); });
})();
