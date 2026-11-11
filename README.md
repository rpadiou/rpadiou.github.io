# Personal academic site

Static site: plain HTML and CSS, no build step. Hosted on GitHub Pages (`.nojekyll` disables Jekyll).

## Editing
- Pages: `index.html` (about, news, keywords, contact), `projects.html` and `sketches/index.html` (title-only lists), `cv.html`. Every project and every sketch is a short illustrated article (what it is for, plain words first, then the technique and the figures), in `projects/<name>/index.html` or `sketches/<name>/index.html`, and links to its paper or code. Copy an existing article to start a new one.
- Latest (home page): what was posted or updated in the last 2 months (`data-months="2"` on `<ol class="news">`; change the number to widen the window), newest first. For each new or updated project or sketch, add an `<li data-date="YYYY-MM-DD">` (date of the last update; order does not matter, `assets/js/latest.js` sorts and hides the old ones; if none is left the section disappears). Also add it to the list of `projects.html` or `sketches/index.html`, and put a `Posted … · updated …` line (`<p class="pdate">`) on the article. A project keeps a short generic name (`<span class="pname">`) next to its descriptive title.
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

## Checks
    python3 scripts/make_sitemap.py   # regenerates sitemap.xml (lastmod = last commit of each page)
    python3 scripts/site_check.py     # SEO and link checks, exit 1 on errors
Install the pre-push hook (runs both, blocks the push on errors): `git config core.hooksPath scripts/hooks`. See `CLAUDE.md` for the checklists.

## Favicon
Source: `favicon.svg` (root). `python3 scripts/make_favicons.py` regenerates `favicon.ico`, `favicon-{48,96,192}.png` and `apple-touch-icon.png` (needs Pillow and Playwright's headless Chromium).
