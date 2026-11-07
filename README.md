# Personal academic site

Static site: plain HTML and CSS, no build step. Hosted on GitHub Pages (`.nojekyll` disables Jekyll).

## Editing
- All content is in `index.html`. Search for `TODO` to find what is left to fill in.
- Each project is an `<article>` block: copy one and paste it in the list (a comment says so).
- Replace the CV by overwriting `assets/cv.pdf`. Education, teaching and experience live there, not on the page.
- Colors and font are at the top of `assets/css/style.css`. The font (STIX Two Text, OFL) is self-hosted in `assets/fonts/`: no external request.
- `assets/js/nav.js` only highlights the current section in the menu; the site works without it.

## Preview
    python3 -m http.server 8000
and open http://localhost:8000.
