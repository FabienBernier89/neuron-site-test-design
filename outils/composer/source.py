"""Extraction de blocs de la page FR publiée de Neur.on, pour composer les pages du test de design.

Les textes sont repris tels quels : on ne fait que découper et réhabiller.
"""
import html as H
import re
from pathlib import Path
from urllib.parse import urljoin, urlparse

RACINE = Path(__file__).resolve().parents[2]
NEURON = RACINE.parent / "neuron"


def charger(p):
    """HTML de <main> de la page publiée fr/<p>."""
    t = (NEURON / "docs/fr" / p / "index.html").read_text(encoding="utf-8")
    m = re.search(r"<main[^>]*>(.*)</main>", t, re.S)
    return m.group(1) if m else t


def _fin(t, debut, tag):
    """Position de fin de l'élément <tag> ouvert à `debut` (balises équilibrées)."""
    prof, i = 0, debut
    motif = re.compile(r"<(/?)" + tag + r"\b[^>]*?(/?)>", re.S)
    for m in motif.finditer(t, debut):
        if m.group(2):
            continue
        prof += -1 if m.group(1) else 1
        if prof == 0:
            return m.end()
    raise ValueError("balise non fermée : " + tag)


def blocs(t, tag, cls=None, attr=None):
    """Tous les éléments <tag> (HTML externe), filtrés par classe ou par attribut."""
    res = []
    for m in re.finditer(r"<" + tag + r"\b([^>]*)>", t):
        a = m.group(1)
        if cls and not re.search(r'class="[^"]*(?<![\w-])' + re.escape(cls) + r'(?![\w-])', a):
            continue
        if attr and attr not in a:
            continue
        res.append(t[m.start():_fin(t, m.start(), tag)])
    return res


def bloc(t, tag, cls=None, attr=None):
    r = blocs(t, tag, cls, attr)
    if not r:
        raise ValueError(f"introuvable : <{tag} class={cls} {attr or ''}>")
    return r[0]


def interne(el):
    """Contenu d'un élément, sans sa balise ouvrante ni fermante."""
    return el[el.index(">") + 1:el.rindex("<")]


def sans_svg(t):
    return re.sub(r"<svg\b.*?</svg>", "", t, flags=re.S)


def txt(t):
    t = sans_svg(t)
    return re.sub(r"\s+", " ", H.unescape(re.sub(r"<[^>]+>", "", t))).strip()


def brut(t):
    """Texte interne en gardant les entités telles quelles (pour réinjection HTML)."""
    t = re.sub(r"<small\b[^>]*>", " ", sans_svg(t))
    return re.sub(r"\s+", " ", re.sub(r"<(?!/?(b|em|strong|i|q|mark|br|abbr|a)\b)[^>]+>", "", t)).strip()


def liens(t, p):
    """Liens et images relatifs de la page fr/<p> réécrits en {{ROOT}}chemin."""
    base = "https://x/fr/" + p

    def sub(m):
        attr, val = m.group(1), m.group(2)
        if val.startswith(("http", "mailto:", "#", "data:", "{{ROOT}}", "tel:")):
            return m.group(0)
        chemin = urlparse(urljoin(base, val))
        cible = chemin.path.lstrip("/") + (("#" + chemin.fragment) if chemin.fragment else "")
        return f'{attr}="{{{{ROOT}}}}{cible}"'

    return re.sub(r'\b(href|src)="([^"]*)"', sub, t)


def ecrire(p, entete, corps):
    f = RACINE / "src/pages" / p / "index.html"
    f.parent.mkdir(parents=True, exist_ok=True)
    f.write_text(entete + corps, encoding="utf-8")


def entete_existant(p):
    f = RACINE / "src/pages" / p / "index.html"
    t = f.read_text(encoding="utf-8")
    return t[:t.index("-->\n") + 4]
