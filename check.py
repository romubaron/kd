"""Site check run by CI and by Gravity (workflow.verify.quick).

Fails if a page lacks lang/title, or links to a local file or #anchor that doesn't exist.
"""
import sys
from html.parser import HTMLParser
from pathlib import Path
from urllib.parse import urlparse

ROOT = Path(__file__).parent


class Page(HTMLParser):
    def __init__(self):
        super().__init__()
        self.ids, self.refs, self.lang, self.title = set(), [], False, False

    def handle_starttag(self, tag, attrs):
        a = dict(attrs)
        if "id" in a:
            self.ids.add(a["id"])
        if tag == "html" and a.get("lang"):
            self.lang = True
        if tag == "title":
            self.title = True
        for k in ("href", "src"):
            if a.get(k):
                self.refs.append(a[k])


def check(root):
    errors = []
    pages = {}
    for f in root.rglob("*.html"):
        p = Page()
        p.feed(f.read_text(encoding="utf-8"))
        pages[f.resolve()] = p
    for f, p in pages.items():
        rel = f.relative_to(root.resolve())
        if not p.lang:
            errors.append(f"{rel}: <html> sans lang")
        if not p.title:
            errors.append(f"{rel}: pas de <title>")
        for ref in p.refs:
            u = urlparse(ref)
            if u.scheme or u.netloc:
                continue  # externe (https:, mailto:, tel:)
            target = (f.parent / u.path).resolve() if u.path else f
            if target.is_dir():
                target = target / "index.html"
            if not target.exists():
                errors.append(f"{rel}: lien cassé {ref}")
            elif u.fragment and target in pages and u.fragment not in pages[target].ids:
                errors.append(f"{rel}: ancre introuvable {ref}")
    return errors


def demo():
    import tempfile
    with tempfile.TemporaryDirectory() as d:
        d = Path(d)
        (d / "index.html").write_text('<html lang="fr"><title>t</title><a href="#x"></a><a href="nope.css"></a><a href="mailto:a@b">m</a>')
        assert check(d) == ["index.html: ancre introuvable #x", "index.html: lien cassé nope.css"], check(d)


if __name__ == "__main__":
    demo()
    errors = check(ROOT)
    print("\n".join(errors) or "OK")
    sys.exit(1 if errors else 0)
