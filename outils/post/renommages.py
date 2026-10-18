"""Renommages et corrections de phrases appliqués à toute la page, données structurées comprises.

- Une entrée de src/data/contenus-v2/ dont la clé commence par « renommage. » porte le nouveau nom (« texte ») et
  l'ancien (« remplace ») : l'ancien nom exact est remplacé sur tout le site. Premier usage : « Corrext et les LLM
  généralistes » devient « Corrext et les IA génératives » (demande de Fabien du 2026-10-18).
- Une entrée d'une page précise qui porte « remplace » corrige cette phrase partout dans la page, y compris dans le
  JSON-LD repris de la V1 (FAQPage), pour que le texte affiché et les données structurées disent la même chose.
"""
import html as H

from outils import contenus


def _paires(page):
    return [(e["remplace"], e["texte"]) for e in contenus.toutes()
            if "remplace" in e and (e["cle"].startswith("renommage.") or e["page"] == page)]


def traiter(html, page):
    for ancien, nouveau in _paires(page):
        html = html.replace(ancien, nouveau).replace(H.escape(ancien, quote=False), H.escape(nouveau, quote=False))
    return html
