#!/usr/bin/env python3
"""SEO and quality checks for the site. Exit code 1 if there is any ERROR (warnings do not fail)."""
import datetime
import json
import re
import struct
import sys
import urllib.parse
import xml.etree.ElementTree as ET
from html.parser import HTMLParser

from sitelib import BASE, ROOT, page_url, public_pages

NAME = "Raphaël Padiou"
errors, warnings = [], []


def err(page, msg): errors.append((page, msg))
def warn(page, msg): warnings.append((page, msg))


class Page(HTMLParser):
    def __init__(self):
        super().__init__(convert_charrefs=True)
        self.title = None; self._in_title = False
        self.meta = {}; self.canonical = []; self.h1 = 0
        self.imgs = []; self.refs = []; self.ids = set(); self.jsonld = []; self.icons = []; self._in_ld = False; self._ld = ""

    def handle_starttag(self, tag, attrs):
        a = dict(attrs)
        if "id" in a: self.ids.add(a["id"])
        if tag == "title": self._in_title = True; self.title = ""
        elif tag == "meta":
            key = a.get("name") or a.get("property")
            if key: self.meta.setdefault(key, []).append(a.get("content", ""))
        elif tag == "link":
            if a.get("rel") == "canonical": self.canonical.append(a.get("href", ""))
            if a.get("rel") in ("icon", "apple-touch-icon"): self.icons.append(a)
            if a.get("href"): self.refs.append(a["href"])
        elif tag == "h1": self.h1 += 1
        elif tag == "img":
            self.imgs.append(a)
            if a.get("src"): self.refs.append(a["src"])
        elif tag in ("a", "script", "source", "iframe", "video", "audio"):
            ref = a.get("href") if tag == "a" else a.get("src")
            if ref: self.refs.append(ref)
        if tag == "script" and a.get("type") == "application/ld+json": self._in_ld = True; self._ld = ""

    def handle_endtag(self, tag):
        if tag == "title": self._in_title = False
        if tag == "script" and self._in_ld: self._in_ld = False; self.jsonld.append(self._ld)

    def handle_data(self, data):
        if self._in_title: self.title += data
        if self._in_ld: self._ld += data


def local_target(ref, page_rel):
    """Map a reference to a local path (or None if external / not checkable). Returns (path, fragment)."""
    ref = ref.strip()
    if ref.startswith(BASE): ref = "/" + ref[len(BASE):]
    u = urllib.parse.urlsplit(ref)
    if u.scheme or u.netloc or ref.startswith(("mailto:", "tel:", "data:", "javascript:")): return None
    path = urllib.parse.unquote(u.path)
    if path == "": target = ROOT / page_rel
    elif path.startswith("/"): target = ROOT / path.lstrip("/")
    else: target = (ROOT / page_rel).parent / path
    return target.resolve(), u.fragment


def one(page, p, key, what):
    v = p.meta.get(key, [])
    if len(v) != 1 or not v[0].strip():
        err(page, f"{what}: {'absent ou vide' if not v or not v[0].strip() else 'présent plusieurs fois'}")
        return None
    return v[0].strip()


pages = public_pages()
parsed = {}
for rel in pages:
    p = Page(); p.feed((ROOT / rel).read_text(encoding="utf-8")); parsed[rel] = p

# --- sitemap
sm = ROOT / "sitemap.xml"
expected = {page_url(r) for r in pages}
if not sm.exists():
    err("sitemap.xml", "absent (lancer scripts/make_sitemap.py)")
else:
    try:
        ns = {"s": "http://www.sitemaps.org/schemas/sitemap/0.9"}
        urls = {}
        for u in ET.parse(sm).getroot().findall("s:url", ns):
            loc = (u.findtext("s:loc", "", ns) or "").strip(); last = (u.findtext("s:lastmod", "", ns) or "").strip()
            urls[loc] = last
            try: datetime.date.fromisoformat(last)
            except ValueError: err("sitemap.xml", f"lastmod absent ou invalide pour {loc}")
        for m in sorted(expected - set(urls)): err("sitemap.xml", f"page manquante : {m}")
        for x in sorted(set(urls) - expected): err("sitemap.xml", f"URL qui ne correspond à aucune page : {x}")
    except ET.ParseError as e:
        err("sitemap.xml", f"XML invalide : {e}")

# --- robots
rb = ROOT / "robots.txt"
if not rb.exists(): err("robots.txt", "absent")
elif not re.search(rf"^Sitemap:\s*{re.escape(BASE)}sitemap\.xml\s*$", rb.read_text(), re.M | re.I):
    err("robots.txt", f"ne pointe pas vers {BASE}sitemap.xml")

# --- Google Search Console file
if not list(ROOT.glob("google*.html")): err("racine", "fichier de validation Google Search Console (google*.html) absent")

# --- pages
titles, descs = {}, {}
for rel, p in parsed.items():
    pg = rel.as_posix(); url = page_url(rel); home = pg == "index.html"
    title = (p.title or "").strip()
    if not title: err(pg, "<title> absent ou vide")
    elif home and title != NAME: err(pg, f"<title> de l'accueil doit être « {NAME} » (trouvé : « {title} »)")
    elif not home and not (title.endswith(f" — {NAME}") and len(title) > len(f" — {NAME}")):
        err(pg, f"<title> doit avoir la forme « <Titre> — {NAME} » (trouvé : « {title} »)")
    if title: titles.setdefault(title, []).append(pg)

    desc = one(pg, p, "description", "meta description")
    if desc:
        maxd = 170 if home else 160
        if len(desc) > maxd: err(pg, f"meta description trop longue ({len(desc)} > {maxd})")
        descs.setdefault(desc, []).append(pg)

    if p.canonical != [url]: err(pg, f"canonical doit être {url} (trouvé : {p.canonical or 'absent'})")
    ogt = one(pg, p, "og:title", "og:title"); twt = one(pg, p, "twitter:title", "twitter:title")
    ogd = one(pg, p, "og:description", "og:description")
    for name, v in (("og:title", ogt), ("twitter:title", twt)):
        if v and v != title: err(pg, f"{name} ≠ <title> (« {v} »)")
    if ogd and desc and ogd != desc: err(pg, "og:description ≠ meta description")
    twd = p.meta.get("twitter:description", [None])[0]
    if twd is not None and desc and twd != desc: warn(pg, "twitter:description ≠ meta description")
    ogu = p.meta.get("og:url", [None])[0]
    if ogu != url: warn(pg, f"og:url devrait être {url} (trouvé : {ogu})")
    if not p.meta.get("twitter:card"): warn(pg, "twitter:card absent")
    for key in ("og:image", "twitter:image"):
        v = one(pg, p, key, key) if key == "og:image" else (p.meta.get(key) or [None])[0]
        if v is None:
            if key == "twitter:image": warn(pg, "twitter:image absent")
            continue
        if not v.startswith(BASE): err(pg, f"{key} doit être une URL absolue sous {BASE} (trouvé : {v})"); continue
        if not local_target(v, rel)[0].is_file(): err(pg, f"{key} : fichier introuvable ({v})")

    if p.h1 != 1: err(pg, f"{p.h1} balises <h1> (il en faut exactement 1)")
    for im in p.imgs:
        if not (im.get("alt") or "").strip(): err(pg, f"image sans alt : {im.get('src')}")

    for ref in p.refs:
        t = local_target(ref, rel)
        if t is None: continue
        path, frag = t
        if path.is_dir(): path = path / "index.html"
        if not path.exists(): err(pg, f"lien ou fichier cassé : {ref}"); continue
        if frag and path.suffix == ".html":
            ids = p.ids if path == (ROOT / rel).resolve() else (parsed[path.relative_to(ROOT)].ids if path.relative_to(ROOT) in parsed else None)
            if ids is not None and frag not in ids: err(pg, f"ancre introuvable : {ref}")

    # favicons: SVG + PNG (sizes multiple of 48 px, Google) + ICO + apple-touch-icon, files present
    def icon(rel_, typ=None, ext=None):
        return [i for i in p.icons if i.get("rel") == rel_ and (typ is None or i.get("type") == typ) and (ext is None or i.get("href", "").endswith(ext))]
    if not icon("icon", "image/svg+xml"): err(pg, "favicon SVG non déclarée")
    if not icon("icon", None, ".ico"): err(pg, "favicon.ico non déclarée")
    if not icon("apple-touch-icon"): err(pg, "apple-touch-icon non déclarée")
    pngs = icon("icon", "image/png")
    if not pngs: err(pg, "favicon PNG non déclarée")
    for i in p.icons:
        href = i.get("href", ""); f = local_target(href, rel)[0]
        if not f.is_file(): err(pg, f"favicon introuvable ({href})"); continue
        if f.suffix == ".png":
            head = f.read_bytes()[:24]
            w, h = struct.unpack(">II", head[16:24]) if head[:8] == b"\x89PNG\r\n\x1a\n" else (0, 0)
            if not i.get("sizes"): err(pg, f"favicon sans attribut sizes ({href})")
            elif i["sizes"] != f"{w}x{h}": err(pg, f"favicon {href} : sizes={i['sizes']} ≠ dimensions réelles {w}x{h}")
            if i.get("type") == "image/png" and (w != h or w % 48): err(pg, f"favicon PNG {href} : {w}x{h}, doit être carré et multiple de 48 px")
    if home:
        if not p.jsonld: err(pg, "JSON-LD absent")
        for raw in p.jsonld:
            try: d = json.loads(raw)
            except json.JSONDecodeError as e: err(pg, f"JSON-LD invalide : {e}"); continue
            if d.get("@type") == "WebSite":
                if d.get("name") != NAME: err(pg, f"JSON-LD WebSite : name doit être « {NAME} »")
                if d.get("url") != BASE: err(pg, f"JSON-LD WebSite : url doit être {BASE}")
                continue
            if d.get("@type") != "Person": err(pg, f"JSON-LD : @type doit être Person (trouvé : {d.get('@type')})")
            for k in ("name", "alternateName", "url"):
                if not isinstance(d.get(k), str) or not d[k].strip(): err(pg, f"JSON-LD : « {k} » manquant")
            if not (isinstance(d.get("sameAs"), list) and d["sameAs"] and all(isinstance(x, str) and x.startswith("http") for x in d["sameAs"])):
                err(pg, "JSON-LD : « sameAs » doit être une liste non vide d'URL")
            if d.get("url") != BASE: warn(pg, f"JSON-LD : url ≠ {BASE}")
    elif p.jsonld: warn(pg, "JSON-LD présent hors accueil")

for t, pgs in titles.items():
    if len(pgs) > 1: err(", ".join(pgs), f"<title> en double : « {t} »")
for d, pgs in descs.items():
    if len(pgs) > 1: err(", ".join(pgs), "meta description en double")

# --- report
print(f"Pages vérifiées : {len(pages)}")
bad = {pg for pg, _ in errors}
for rel in parsed:
    pg = rel.as_posix()
    if pg not in bad: print(f"  OK       {pg}")
for pg, m in errors: print(f"  ERREUR   {pg} : {m}")
for pg, m in warnings: print(f"  AVERT.   {pg} : {m}")
print(f"\n{len(errors)} erreur(s), {len(warnings)} avertissement(s)")
sys.exit(1 if errors else 0)
