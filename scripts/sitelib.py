"""Shared helpers for make_sitemap.py and site_check.py (standard library only)."""
import datetime
import pathlib
import subprocess

ROOT = pathlib.Path(__file__).resolve().parent.parent
BASE = "https://rpadiou.github.io/"
SKIP_DIRS = {".git", "assets", "code", "scripts", "node_modules"}


def public_pages():
    """Public HTML pages (paths relative to ROOT), without the Google verification file and technical dirs."""
    pages = []
    for p in sorted(ROOT.rglob("*.html")):
        rel = p.relative_to(ROOT)
        if SKIP_DIRS & set(rel.parts[:-1]) or (len(rel.parts) == 1 and rel.name.startswith("google")):
            continue
        pages.append(rel)
    return pages


def page_url(rel):
    """Canonical public URL of a page: dir/index.html -> dir/, other.html -> other.html."""
    s = rel.as_posix()
    if s == "index.html":
        return BASE
    if s.endswith("/index.html"):
        return BASE + s[: -len("index.html")]
    return BASE + s


def last_commit_date(rel):
    """Date (YYYY-MM-DD) of the last commit that touched the file; today if it is not committed yet."""
    out = subprocess.run(["git", "log", "-1", "--format=%cs", "--", rel.as_posix()],
                         cwd=ROOT, capture_output=True, text=True).stdout.strip()
    return out or datetime.date.today().isoformat()
