"""Titres des billets et des guides orientés problème (lot E).

Les nouveaux titres vivent dans src/data/contenus-v2/E-blog.json : pour chaque page, trois entrées `<page>.h1`,
`<page>.title` et `<page>.og` (page sans la barre finale dans la clé), et le titre d'origine dans le champ « ancien »
de l'entrée `.h1`. Ce post-traitement remplace, sans toucher aux URL :

- sur la page elle-même : le H1 (pour un guide, le texte du <span class="s">, le repère « Guide. » reste), le <title>,
  l'og:title et le headline du JSON-LD Article ou BlogPosting ;
- partout ailleurs où le titre d'origine servait de titre : les cartes (<h2> et <h3>) qui renvoient vers l'article, les
  headline des JSON-LD de la liste du blog, et le nom du guide dans la page qui les liste (<b>, ou <b class="fx-t">
  d'une carte illustrée) ;
- dans les blocs « À lire ensuite », le titre de chaque carte qui renvoie vers une page retitrée (son libellé court
  d'origine devient le nouveau H1).
Les menus ne changent pas.
"""
import functools
import html as H
import json
import re
from pathlib import Path

from outils import contenus

JSON_LD = re.compile(r'<script type="application/ld\+json">(.*?)</script>', re.S)
LIRE_ENSUITE = re.compile(r"À lire ensuite</h2>.*?</section>", re.S)
ARTICLES = ("Article", "BlogPosting", "NewsArticle")
SUFFIXES = (".h1", ".title", ".og")


@functools.lru_cache(maxsize=4)
def _lire(signature):
    """Registre {page: {"h1", "title", "og", "ancien"}} des entrées du lot E (signature : fichiers et dates de modification)."""
    registre = {}
    for e in contenus.toutes():
        if e["lot"] != "E" or e["page"] == "*" or not e["cle"].endswith(SUFFIXES):
            continue
        registre.setdefault(e["page"], {})[e["cle"].rsplit(".", 1)[1]] = e["texte"]
        if e["cle"].endswith(".h1"):
            registre[e["page"]]["ancien"] = e["ancien"]
    return registre


def registre():
    fichiers = sorted(Path(contenus.DOSSIER).glob("*.json"))
    return _lire(tuple((f.name, f.stat().st_mtime_ns) for f in fichiers))


def texte_html(s):
    return H.escape(s, quote=False)


def attribut(s):
    return s.replace("&", "&amp;").replace('"', "&quot;").replace("<", "&lt;")


def remplacer_h1(html, titre):
    def sub(m):
        interne = m.group(2)
        if '<span class="s">' in interne:  # guide : « Guide. » est un repère, le titre est dans le span .s
            interne = re.sub(r'(<span class="s">).*?(</span>)', lambda s: s.group(1) + texte_html(titre) + s.group(2), interne, count=1, flags=re.S)
        else:
            interne = texte_html(titre)
        return m.group(1) + interne + "</h1>"
    return re.sub(r"(<h1\b[^>]*>)(.*?)</h1>", sub, html, count=1, flags=re.S)


def corriger_json_ld(html, titre, ancien_vers_nouveau, sur_la_page):
    """Met le headline des Article et BlogPosting : celui d'un titre d'origine devient le nouveau ; sur la page elle-même,
    tout headline d'Article devient le nouveau H1."""
    def parcourir(x):
        modifie = False
        if isinstance(x, dict):
            if x.get("@type") in ARTICLES and "headline" in x:
                nouveau = titre if sur_la_page else ancien_vers_nouveau.get(x["headline"])
                if nouveau and x["headline"] != nouveau:
                    x["headline"] = nouveau
                    modifie = True
            for v in x.values():
                modifie = parcourir(v) or modifie
        elif isinstance(x, list):
            for v in x:
                modifie = parcourir(v) or modifie
        return modifie

    def sub(m):
        try:
            d = json.loads(m.group(1))
        except ValueError:
            return m.group(0)
        if not parcourir(d):
            return m.group(0)
        return '<script type="application/ld+json">' + json.dumps(d, ensure_ascii=False).replace("</", "<\\/") + "</script>"

    return JSON_LD.sub(sub, html)


def lire_ensuite(html, reg):
    """Blocs « À lire ensuite » : la carte <a href="{{ROOT}}fr/<page>"><b>...</b> d'une page retitrée prend son H1."""
    def bloc(m):
        b = m.group(0)
        for q, x in reg.items():
            carte = re.compile(r'(<a href="\{\{ROOT\}\}(?:fr/)?' + re.escape(q) + r'"[^>]*>(?:<b>)+)(.*?)((?:</b>)+)', re.S)
            b = carte.sub(lambda c: c.group(1) + texte_html(x["h1"]) + c.group(3), b)
        return b
    return LIRE_ENSUITE.sub(bloc, html)


def traiter(html, page):
    reg = registre()
    if not reg:
        return html
    propre = reg.get(page)
    if propre:
        html = remplacer_h1(html, propre["h1"])
        html = re.sub(r"<title>.*?</title>", lambda m: f"<title>{texte_html(propre['title'])}</title>", html, count=1, flags=re.S)
        html = re.sub(r'<meta property="og:title" content="[^"]*">',
                      lambda m: f'<meta property="og:title" content="{attribut(propre["og"])}">', html, count=1)
    html = corriger_json_ld(html, propre["h1"] if propre else None, {x["ancien"]: x["h1"] for x in reg.values()}, bool(propre))
    for q, x in reg.items():
        ancien, nouveau = re.escape(texte_html(x["ancien"])), texte_html(x["h1"])
        # carte qui renvoie vers l'article : titre en <h2> ou <h3>
        html = re.sub(r"(<h[23]\b[^>]*>)" + ancien + r"(</h[23]>)", lambda m: m.group(1) + nouveau + m.group(2), html)
        if page == q.rstrip("/").rpartition("/")[0] + "/":  # liste des guides : le nom de chaque guide
            html = html.replace(f"<b>{texte_html(x['ancien'])}</b>", f"<b>{nouveau}</b>")
            # carte illustrée (outils/post/fonctionnalites.py passe avant : <b class="fx-t">)
            html = html.replace('<b class="fx-t">' + texte_html(x["ancien"]) + "</b>", f'<b class="fx-t">{nouveau}</b>')
    return lire_ensuite(html, reg)
