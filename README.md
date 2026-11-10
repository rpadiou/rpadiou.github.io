# Personal academic site

Static site: plain HTML and CSS, no build step. Hosted on GitHub Pages (`.nojekyll` disables Jekyll).

## Editing
- Pages: `index.html` (about, news, keywords, contact), `projects.html` and `sketches/index.html` (title-only lists), `cv.html`. Every project and every sketch is a short illustrated article (what it is for, plain words first, then the technique and the figures), in `projects/<name>/index.html` or `sketches/<name>/index.html`, and links to its paper or code. Copy an existing article to start a new one.
- News (home page): a dated list, newest first. For each new project or sketch, paste an `<li>` at the top of `<ol class="news">` in `index.html`, add the same entry at the top of the list of `projects.html` or `sketches/index.html`, and put a `Posted … · updated …` line (`<p class="pdate">`) on the article. When something is updated, change its "updated" date in all three places.
- Formulas: write `\(...\)` (inline) or `\[...\]` (display) in the HTML; KaTeX renders them (`assets/katex/`, self-hosted, MIT; `assets/js/math.js` starts it). Add the KaTeX stylesheet and the three scripts as in `projects/sos-portfolio/index.html`.
- Papers go in `assets/papers/`. Education, teaching and experience live in the CV only. To update it, overwrite `assets/cv.pdf`, then regenerate the preview and re-check the clickable zones in `cv.html`:
      pdftoppm -jpeg -r 130 -f 1 -l 1 -singlefile assets/cv.pdf assets/img/cv-preview
  (zone positions are percentages of the page; `PyMuPDF`'s `page.get_links()` lists the link rectangles).
- Colors and font are at the top of `assets/css/style.css`. The font (STIX Two Text, OFL) is self-hosted in `assets/fonts/`: no external request.
- JavaScript, no library besides KaTeX: `assets/js/math.js` (formulas), `assets/js/zoom.js` (click a figure of an article to enlarge it; Escape, the x or a click outside closes it), and `sketches/mwu-rps/anim.js` (the animation of that sketch).

## Preview
    python3 -m http.server 8000
and open http://localhost:8000.

## Cache
GitHub Pages serves CSS with a 10-minute cache. After changing `assets/css/style.css`, bump the `?v=` number in the `<link>` of every page (`grep -rl 'style.css?v=' --include='*.html' .`) so visitors get the new styles at once.
