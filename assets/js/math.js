// Renders the formulas written as \( ... \) (inline) and \[ ... \] (display) with the self-hosted KaTeX.
document.addEventListener("DOMContentLoaded", function () {
  if (!window.renderMathInElement) return;
  renderMathInElement(document.body, {
    delimiters: [{ left: "\\[", right: "\\]", display: true }, { left: "\\(", right: "\\)", display: false }],
    ignoredTags: ["script", "noscript", "style", "textarea", "pre", "code", "canvas"],
    throwOnError: false
  });
});
