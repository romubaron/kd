"""Site check run by CI and by Gravity (workflow.verify.quick).

Fails if a page lacks lang/title, has not exactly one <h1> or skips a heading level,
has an <img> without alt/width/height, a target="_blank" link without rel="noopener",
or links to a local file or #anchor that doesn't exist.
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
        self.headings, self.problems = [], []

    def handle_starttag(self, tag, attrs):
        a = dict(attrs)
        if "id" in a:
            self.ids.add(a["id"])
        if tag == "html" and a.get("lang"):
            self.lang = True
        if tag == "title":
            self.title = True
        if len(tag) == 2 and tag[0] == "h" and tag[1] in "123456":
            self.headings.append(int(tag[1]))
        if tag == "img":
            for k in ("alt", "width", "height"):
                if k not in a:
                    self.problems.append(f"<img src={a.get('src')!r}> sans {k}")
        if tag == "a" and a.get("target") == "_blank" and "noopener" not in (a.get("rel") or "").split():
            self.problems.append(f"lien target=_blank sans rel=noopener : {a.get('href')}")
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
        if p.headings.count(1) != 1:
            errors.append(f"{rel}: {p.headings.count(1)} <h1> (un seul attendu)")
        prev = 0
        for h in p.headings:
            if prev and h > prev + 1:
                errors.append(f"{rel}: saut de titre h{prev} -> h{h}")
            prev = h
        errors += [f"{rel}: {m}" for m in p.problems]
        for ref in p.refs:
            u = urlparse(ref)
            if u.scheme or u.netloc:
                continue  # externe (https:, mailto:, tel:)
            if u.path.startswith("/kd/"):
                target = (root / u.path[len("/kd/"):]).resolve()  # racine GitHub Pages
            else:
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
        (d / "index.html").write_text('<html lang="fr"><title>t</title><h1>t</h1><a href="#x"></a><a href="nope.css"></a><a href="mailto:a@b">m</a>')
        assert check(d) == ["index.html: ancre introuvable #x", "index.html: lien cassé nope.css"], check(d)
    with tempfile.TemporaryDirectory() as d:
        d = Path(d)
        (d / "style.css").write_text("")
        (d / "index.html").write_text('<html lang="fr"><title>t</title><h1>t</h1>')
        (d / "404.html").write_text('<html lang="fr"><title>t</title><h1>t</h1><a href="/kd/style.css"></a><a href="/kd/"></a><a href="/kd/absent.css"></a>')
        assert check(d) == ["404.html: lien cassé /kd/absent.css"], check(d)
    ok = '<html lang="fr"><title>t</title>'
    ext = '<a href="https://e.com" target="_blank"'
    cases = {
        "<h1>a</h1><h1>b</h1>": "index.html: 2 <h1> (un seul attendu)",
        "<p>x</p>": "index.html: 0 <h1> (un seul attendu)",
        "<h1>a</h1><h2>b</h2><h4>c</h4>": "index.html: saut de titre h2 -> h4",
        '<h1>a</h1><img src="x.png" width="1" height="1">': "index.html: <img src='x.png'> sans alt",
        '<h1>a</h1><img src="x.png" alt="" height="1">': "index.html: <img src='x.png'> sans width",
        '<h1>a</h1><img src="x.png" alt="" width="1">': "index.html: <img src='x.png'> sans height",
        f"<h1>a</h1>{ext}>e</a>": "index.html: lien target=_blank sans rel=noopener : https://e.com",
        f'<h1>a</h1>{ext} rel="nofollow">e</a>': "index.html: lien target=_blank sans rel=noopener : https://e.com",
    }
    for body, expected in cases.items():
        with tempfile.TemporaryDirectory() as d:
            d = Path(d)
            (d / "x.png").write_bytes(b"")
            (d / "index.html").write_text(ok + body)
            assert check(d) == [expected], (body, check(d))
    with tempfile.TemporaryDirectory() as d:
        d = Path(d)
        (d / "x.png").write_bytes(b"")
        (d / "index.html").write_text(ok + f'<h1>a</h1><h2>b</h2><h3>c</h3><h2>d</h2><img src="x.png" alt="" width="1" height="1">{ext} rel="noopener noreferrer">e</a>')
        assert check(d) == [], check(d)


if __name__ == "__main__":
    demo()
    errors = check(ROOT)
    print("\n".join(errors) or "OK")
    sys.exit(1 if errors else 0)
