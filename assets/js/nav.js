// Highlights the current section in the menu. The site works without it.
(function () {
  if (!("IntersectionObserver" in window)) return;
  var links = document.querySelectorAll(".menu a[href^='#']");
  var map = {};
  links.forEach(function (a) { map[a.getAttribute("href").slice(1)] = a; });
  var io = new IntersectionObserver(function (entries) {
    entries.forEach(function (e) {
      if (e.isIntersecting && map[e.target.id]) {
        links.forEach(function (a) { a.classList.remove("active"); a.removeAttribute("aria-current"); });
        map[e.target.id].classList.add("active");
        map[e.target.id].setAttribute("aria-current", "true");
      }
    });
  }, { rootMargin: "-20% 0px -70% 0px" });
  document.querySelectorAll("main section[id]").forEach(function (s) { io.observe(s); });
})();
