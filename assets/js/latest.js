// "Latest": keeps the items updated in the last N months (data-months on the list), newest first.
// Each <li> carries data-date="YYYY-MM-DD" (its last update). If nothing is left, the whole section is hidden.
document.addEventListener("DOMContentLoaded", function () {
  var list = document.querySelector("ol.news"); if (!list) return;
  var months = parseInt(list.getAttribute("data-months"), 10) || 2;
  var limit = new Date(); limit.setMonth(limit.getMonth() - months);
  var items = Array.prototype.slice.call(list.children);
  items.forEach(function (li, i) { li._i = i; });
  items.sort(function (a, b) { return (b.getAttribute("data-date") || "").localeCompare(a.getAttribute("data-date") || "") || a._i - b._i; });
  var kept = 0;
  items.forEach(function (li) {
    var d = new Date(li.getAttribute("data-date"));
    if (isNaN(d) || d >= limit) { list.appendChild(li); kept++; } else { li.remove(); }
  });
  if (!kept) { var s = document.getElementById("latest"); if (s) s.hidden = true; }
});
