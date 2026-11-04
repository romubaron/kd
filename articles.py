"""Remplace les cartes « Article » de index.html par les derniers articles de Klervi sur France 3.

Lancé par la CI juste avant chaque mise en ligne (et une fois par jour) : le site publié est
à jour sans commit. Ne touche que ce qui est entre les marqueurs START et END de index.html.
Usage : python3 articles.py [index.html]
"""
import html
import re
import sys
import urllib.request
from pathlib import Path

SOURCE = "https://france3-regions.franceinfo.fr/redaction/klervi-dalibot"
COUNT = 6
START, END = "<!-- articles:début (généré par articles.py) -->", "<!-- articles:fin -->"

# Une carte de la page d'autrice : lien, titre, puis « le JJ/MM/AAAA ».
CARD = re.compile(
    r'<a href="(https://france3-regions\.franceinfo\.fr/[^"]+\.html)"[^>]*class="main-card[^"]*"'
    r'.*?main-card__title[^>]*>(.*?)</h3>'
    r'.*?main-card__publication-date[^>]*>\s*le (\d{2}/\d{2}/\d{4})',
    re.S,
)


def parse(page):
    seen, articles = set(), []
    for url, title, date in CARD.findall(page):
        if url in seen:
            continue
        seen.add(url)
        title = html.unescape(re.sub(r"<[^>]+>", "", title)).strip()
        title = re.sub(r'"([^"]+)"', r"« \1 »", title)
        articles.append((url, title, date))
    return articles[:COUNT]


def render(articles):
    return "".join(
        f'''
        <li class="card work-card" data-cat="articles">
          <span class="tag">Article</span>
          <p class="work-title"><a href="{html.escape(url)}">{html.escape(title, quote=False)}</a></p>
          <p class="meta">{date}</p>
        </li>'''
        for url, title, date in articles
    ) + "\n        "


def update(text, articles):
    if text.count(START) != 1 or text.count(END) != 1:
        raise SystemExit("marqueurs articles:début / articles:fin absents ou en double dans index.html")
    head, rest = text.split(START)
    _, tail = rest.split(END)
    return head + START + render(articles) + END + tail


def demo():
    card = ('<a href="https://france3-regions.franceinfo.fr/x/y-1.html" class="main-card main-card--h" target="_self">'
            '<h3 class="main-card__title t">&quot;Titre&quot; : test</h3>'
            '<span class="main-card__publication-date text-grey-light">le 03/11/2026</span></a>')
    arts = parse(card + card)  # doublon ignoré
    assert arts == [("https://france3-regions.franceinfo.fr/x/y-1.html", "« Titre » : test", "03/11/2026")], arts
    page = f"<ul>\n{START}\n<li>vieux</li>\n{END}\n</ul>"
    out = update(page, arts)
    assert "vieux" not in out and "« Titre » : test" in out and out.count(START) == 1, out


if __name__ == "__main__":
    demo()
    path = Path(sys.argv[1] if len(sys.argv) > 1 else Path(__file__).parent / "index.html")
    req = urllib.request.Request(SOURCE, headers={"User-Agent": "Mozilla/5.0 (site de Klervi Dalibot)"})
    page = urllib.request.urlopen(req, timeout=30).read().decode("utf-8")
    articles = parse(page)
    if len(articles) < 3:  # la page a changé de structure : on garde la liste existante
        raise SystemExit(f"seulement {len(articles)} article(s) lu(s) sur {SOURCE}, liste inchangée")
    path.write_text(update(path.read_text(encoding="utf-8"), articles), encoding="utf-8")
    print(f"{len(articles)} articles, le plus récent du {articles[0][2]} : {articles[0][1]}")
