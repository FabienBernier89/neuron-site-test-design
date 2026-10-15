"""Page Protection des données : paragraphe Google Analytics corrigé (décisions de Fabien du 2026-10-15).

Le composeur reprend la V1 mot pour mot, qui décrit les données envoyées à Google comme « anonymisées ». Elles sont
pseudonymisées : ce post-traitement remplace les deux phrases concernées et ajoute la durée de conservation, sans rien
toucher d'autre. Il n'agit que sur la page « protection-des-donnees/ » et dans le seul paragraphe qui commence par
DEBUT ; si la V1 change et qu'une phrase attendue manque, le build s'arrête plutôt que de publier un texte faux.

Textes : src/data/contenus-v2/F-souverainete.json. Une entrée porte soit « remplace » (phrase de la V1 qu'elle
remplace), soit « insere_avant » (texte de la V1 devant lequel elle s'insère).
"""
import html as H
import re

from outils import contenus

PAGE = "protection-des-donnees/"
DEBUT = "<p>Google Analytics est un service d'analyse web"
CLES = ("protection-des-donnees.analytics.pseudonymisee", "protection-des-donnees.analytics.pseudonymisation",
        "protection-des-donnees.analytics.conservation")


def _entrees():
    par_cle = {e["cle"]: e for e in contenus.toutes()}
    return [par_cle[c] for c in CLES]


def corriger(paragraphe):
    """Paragraphe Google Analytics avec les phrases du JSON. ValueError si une phrase de la V1 attendue manque."""
    for e in _entrees():
        ancre = H.escape(e.get("remplace") or e["insere_avant"], quote=False)
        if paragraphe.count(ancre) != 1:
            raise ValueError(f"{PAGE} : texte de la V1 introuvable dans le paragraphe Google Analytics : {ancre[:60]}")
        nouveau = H.escape(e["texte"], quote=False)
        paragraphe = paragraphe.replace(ancre, nouveau if "remplace" in e else f"{nouveau} {ancre}")
    return paragraphe


def traiter(html, page):
    if page != PAGE:
        return html
    trouves = re.findall(re.escape(DEBUT) + r".*?</p>", html, re.S)
    if len(trouves) != 1:
        raise ValueError(f"{PAGE} : paragraphe Google Analytics introuvable ou en double ({len(trouves)})")
    return html.replace(trouves[0], corriger(trouves[0]), 1)
