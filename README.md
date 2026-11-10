# Personal academic site

Static site: plain HTML and CSS, no build step. Hosted on GitHub Pages (`.nojekyll` disables Jekyll).

## Editing
- Pages: `index.html` (about, keywords, contact), `projects.html`, `cv.html`, `sketches/` (a listing page plus one folder per sketch, with its own code). Search for `TODO` to find what is left to fill in.
- News (home page): a dated list, newest first. For each new project or sketch, paste a `<li>` at the top of `<ol class="news">` in `index.html`, and add a `Posted … · updated …` line (`<p class="pdate">`) on the project card or the sketch page. When something is updated, change its "updated" date in both places (home and the item itself).
- Each project is an `<article>` block in `projects.html`: copy one and paste it in the list (a comment says so). Papers go in `assets/papers/`, with a first-page image in `assets/img/`.
- Education, teaching and experience live in the CV only. To update it, overwrite `assets/cv.pdf`, then regenerate the preview and re-check the clickable zones in `cv.html`:
      pdftoppm -jpeg -r 130 -f 1 -l 1 -singlefile assets/cv.pdf assets/img/cv-preview
  (zone positions are percentages of the page; `PyMuPDF`'s `page.get_links()` lists the link rectangles).
- Colors and font are at the top of `assets/css/style.css`. The font (STIX Two Text, OFL) is self-hosted in `assets/fonts/`: no external request.
- Two small scripts, no library: `assets/js/figures.js` (only on `projects.html`) opens and closes the enlarged figures (click, tap or Enter to open; Escape, the close button or a click outside to close); `sketches/mwu-rps/anim.js` runs the animation of the sketch and enlarges its figures the same way.

## Preview
    python3 -m http.server 8000
and open http://localhost:8000.

## Cache
GitHub Pages serves CSS with a 10-minute cache. After changing `assets/css/style.css`, bump the `?v=` number in the `<link>` of every page (`grep -rl 'style.css?v=' --include='*.html' .`) so visitors get the new styles at once.
