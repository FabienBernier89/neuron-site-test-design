"""Insère l'encart d'inscription à la lettre d'information juste avant le pied de page (lot E).

Une seule fois par page : la liste du blog, la fin de chaque billet et de chaque guide, puis toutes les autres pages,
l'encart se place entre </main> et <footer class="pied">. Le pied de page lui-même n'est pas modifié.
Exceptions : la page de contact (déjà un formulaire, en-tête réduit), la page de remerciement qui lui fait suite
et la 404.
"""
import sys

from outils.composer import newsletter

MARQUE = '<footer class="pied">'
DEJA = 'class="nl-s"'


def exclue(page):
    return page == "404.html" or page.startswith("contact/")


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
