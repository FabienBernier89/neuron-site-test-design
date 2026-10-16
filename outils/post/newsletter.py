"""Insère l'encart d'inscription à la lettre d'information juste avant le pied de page (lot E).

Une seule fois par page, entre </main> et <footer class="pied"> ; le pied de page lui-même n'est pas modifié.
Pages de lecture seulement (décision de Fabien du 2026-10-16) : tout ce qui est sous ressources/ (hub, blog et ses
billets, actualités, guides, études, glossaire). Ailleurs (accueil, produits, solutions, tarifs, aide, pages légales,
contact, 404), l'appel « Demander une démo » reste seul en fin de page, sans second appel qui l'affaiblisse.
"""
import sys

from outils.composer import newsletter

MARQUE = '<footer class="pied">'
DEJA = 'class="nl-s"'


def exclue(page):
    """Vrai hors des pages de lecture."""
    return not page.startswith("ressources/")


def config_du_build():
    """Réglages du build en cours (build.CONFIG, éventuellement surchargés par un test), sinon None : l'encart lit alors
    src/data/config.json."""
    for nom in ("build", "__main__"):
        c = getattr(sys.modules.get(nom), "CONFIG", None)
        if isinstance(c, dict):
            return c
    return None


def traiter(html, page):
    i = html.find(MARQUE)
    if exclue(page) or i < 0 or DEJA in html:
        return html
    return html[:i] + newsletter.encart(config_du_build()) + html[i:]
