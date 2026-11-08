// Touch screens have no hover: a tap opens the enlarged figure, another tap anywhere (or Escape) closes it.
// On devices with a mouse, the CSS :hover rule does everything and this script does nothing.
(function () {
  var touch = window.matchMedia && window.matchMedia("(hover: none)").matches;
  function closeAll() {
    var open = document.querySelectorAll(".hoverable.open");
    for (var i = 0; i < open.length; i++) open[i].classList.remove("open");
    return open.length > 0;
  }
  document.addEventListener("click", function (e) {
    if (!touch) return;
    var fig = e.target.closest ? e.target.closest(".hoverable") : null;
    if (closeAll()) return;           // an enlarged figure was open: this tap closes it
    if (fig) fig.classList.add("open");
  });
  document.addEventListener("keydown", function (e) {
    if (e.key === "Escape") closeAll();
  });
})();
