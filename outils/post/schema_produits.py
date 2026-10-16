"""Lot B : insère le schéma « qui fait quoi » (outils/composer/schema_produits.py) sur les pages Corrext et CHnell
(plus sur la page LexMachina depuis le 2026-10-16), après la première section qui porte une scène (sinon après le hero). Le lien du schéma vers la page affichée
reçoit aria-current="page". Les autres pages ne changent pas ; l'accueil intègre le schéma par son composeur (lot D)."""
import importlib.util
import re
from pathlib import Path

PAGES = ("corrext/", "corrext/chnell/")  # retiré de la page LexMachina, qui parle du moteur (Fabien, 2026-10-16)
COMPOSEUR = Path(__file__).resolve().parents[1] / "composer/schema_produits.py"
SECTION = re.compile(r"<section\b[^>]*>.*?</section>\n?", re.S)
_section = []


def section():
    """Section rendue une fois par build (le composeur est chargé par son chemin, sous un nom distinct)."""
    if not _section:
        spec = importlib.util.spec_from_file_location("composeur_schema_produits", COMPOSEUR)
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)
        _section.append(module.rendre())
    return _section[0]


def traiter(html, page):
    if page not in PAGES or 'class="sec sp"' in html:
        return html
    debut = html.find('<main id="main">')
    sections = list(SECTION.finditer(html, debut)) if debut >= 0 else []
    cible = next((m for m in sections if "data-sim" in m.group(0) or 'class="ech"' in m.group(0)), None)
    cible = cible or next((m for m in sections if m.group(0).startswith('<section class="hero"')), None)
    if cible is None:
        raise ValueError(f"{page} : ni scène ni hero où placer le schéma « qui fait quoi »")
    s = section().replace(f'<a class="lien" href="{{{{ROOT}}}}{page}">', f'<a class="lien" href="{{{{ROOT}}}}{page}" aria-current="page">', 1)
    return html[:cible.end()] + s + html[cible.end():]
