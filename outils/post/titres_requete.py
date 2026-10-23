"""H1 orientés requête et titles différenciés (lot Y, décision de Fabien du 2026-10-23, point 11 de l'audit).

Les textes vivent dans src/data/contenus-v2/Y-h1-requete.json :

- `<page>.h1-requete` : nouvelle 1re ligne du H1 d'une page Solutions ou Traduction, et la 1re ligne d'origine dans le
  champ « ancien ». Seul le <span class="n"> du <h1 class="h1"> de la page change : l'accroche (<span class="s">), les
  URL, le menu, les fils d'Ariane et les cartes qui pointent vers la page gardent leur texte. Une substitution du mot
  sur toute la page (« Contrats. ») toucherait d'autres blocs : elle est exclue.
- `<page>.title` et `<page>.og` : title et og:title différenciés de deux pages qui se cannibalisaient (pages banques,
  billets des Swiss FinTech Awards 2024), sans suppression ni redirection. Le H1 et le headline JSON-LD des billets ne
  changent pas : le headline reste aligné sur le H1. Remplacement repris d'outils/post/titres_blog.py (lot E).

Une page déclarée dont la 1re ligne d'origine a disparu fait échouer le build : la décision ne s'applique jamais à
moitié en silence.
"""
import functools
import re
from pathlib import Path

from outils import contenus
from outils.post import titres_blog

LOT = "Y"


@functools.lru_cache(maxsize=4)
def _lire(signature):
    """Registre {page: {"h1", "ancien", "title", "og"}} des entrées du lot Y (signature : fichiers et dates)."""
    registre = {}
    for e in contenus.toutes():
        if e["lot"] != LOT:
            continue
        cle = e["cle"].rsplit(".", 1)[1]
        x = registre.setdefault(e["page"], {})
        if cle == "h1-requete":
            x["h1"], x["ancien"] = e["texte"], e["ancien"]
        elif cle in ("title", "og"):
            x[cle] = e["texte"]
    return registre


def registre():
    fichiers = sorted(Path(contenus.DOSSIER).glob("*.json"))
    return _lire(tuple((f.name, f.stat().st_mtime_ns) for f in fichiers))


def remplacer_premiere_ligne(html, page, ancien, nouveau):
    """1re ligne du H1 de hero (<h1 class="h1"><span class="n">…</span>), et rien d'autre."""
    motif = re.compile(r'(<h1 class="h1"><span class="n">)' + re.escape(titres_blog.texte_html(ancien)) + r"(</span>)")
    html, n = motif.subn(lambda m: m.group(1) + titres_blog.texte_html(nouveau) + m.group(2), html, count=1)
    if n != 1:
        raise ValueError(f"{page} : 1re ligne du H1 d'origine introuvable ({ancien!r}), lot Y à revoir")
    return html


def traiter(html, page):
    x = registre().get(page)
    if not x:
        return html
    if "h1" in x:
        html = remplacer_premiere_ligne(html, page, x["ancien"], x["h1"])
    if "title" in x:
        html = titres_blog.retitrer(html, x["title"], x["og"])
    return html
