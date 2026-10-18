"""Renommages de pages appliqués à tout le site (menu, pied de page, cartes, titres, visuels).

Une entrée de src/data/contenus-v2/ dont la clé commence par « renommage. » porte le nouveau nom (« texte ») et
l'ancien (« remplace ») : l'ancien nom exact est remplacé partout. Premier usage : « Corrext et les LLM généralistes »
devient « Corrext et les IA génératives » (demande de Fabien du 2026-10-18).
"""
import html as H

from outils import contenus


def _paires():
    return [(e["remplace"], e["texte"]) for e in contenus.toutes() if e["cle"].startswith("renommage.")]


def traiter(html, page):
    for ancien, nouveau in _paires():
        html = html.replace(ancien, nouveau).replace(H.escape(ancien, quote=False), H.escape(nouveau, quote=False))
    return html
