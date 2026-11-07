# Personal academic site

Static site: plain HTML and CSS, no build step. Hosted on GitHub Pages (`.nojekyll` disables Jekyll).

## Editing
- All content is in `index.html`. Search for `TODO` to find what is left to fill in.
- Each entry (news, education, project, teaching) is an `<article>` block. To add one, copy a block and paste it in the list; a comment above each list says so.
- Replace the CV by overwriting `assets/cv.pdf`.
- Colors are CSS variables at the top of `assets/css/style.css` (light and dark).
- Photo: none for now. To add one, put it in `assets/img/` and add an `<img alt="...">` in the sidebar header.
- `assets/js/nav.js` only highlights the current section in the menu; the site works without it.

## Preview
    python3 -m http.server 8000
and open http://localhost:8000.
