"""Compose l'accueil du centre d'aide (aide/), sur le modèle d'un centre d'aide de référence adapté à Neur.on
(retour de Fabien du 2026-10-17 : « il n'y a que des blocs de texte, c'est trop compliqué en l'état »).

Hero centré avec une recherche dans toutes les questions des rubriques, rubriques en cartes compactes (icône, titre,
nombre de questions) sur deux colonnes, liste « Pour bien démarrer », appel final. Textes et icônes : page actuelle
(V1) ; questions : pages des rubriques ; nouveaux libellés : src/data/contenus-v2/M-aide.json (à relire).
La recherche (assets/global/aide.js) lit l'index des questions écrit dans la page ; chaque résultat ouvre sa question
(ancres posées par outils/post/aide_ancres.py).

    cd outils/composer && python3 p_aide.py
"""
import html as H
import json
import re
import sys

from source import *
from comp import cta

sys.path.insert(0, str(RACINE))
from outils.contenus import texte  # noqa: E402
from outils.post.aide_ancres import ancre  # noqa: E402

P = "aide/"
t = liens(charger(P), P)


def k(cle):
    return H.escape(texte(f"aide.{cle}"), quote=False)


def questions(rub):
    """(titre de la rubrique, [(question, ancre)]) lus dans la page de la rubrique."""
    page = (RACINE / "src/pages" / rub / "index.html").read_text(encoding="utf-8")
    titre = txt(bloc(page, "h1"))
    qs = [brut(q) for q in re.findall(r"<summary>(.*?)</summary>", page, re.S)]
    return titre, [(q, ancre(q)) for q in qs]


hero = bloc(t, "section", "hc-hero")
form = bloc(hero, "form", "hc-search")
place = re.search(r'placeholder="([^"]+)"', form).group(1)
etiquette = txt(bloc(form, "label"))
LOUPE = re.search(r"<svg.*?</svg>", form, re.S).group(0)

espaces, index, rubriques = [], [], {}
for sp in blocs(t, "section", "hc-space"):
    tete = bloc(sp, "div", "hc-space-head")
    cartes = []
    for c in blocs(sp, "a", "hc-card"):
        lien = re.search(r'href="\{\{ROOT\}\}([^"]+)"', c).group(1)
        rub = lien[3:] if lien.startswith("fr/") else lien
        icone = bloc(c, "span", "ws-ic")
        nb = txt(re.sub(r"<svg.*?</svg>", "", bloc(c, "em"), flags=re.S))
        titre, qs = questions(rub)
        rubriques[rub] = qs
        index += [{"q": H.unescape(re.sub(r"<[^>]+>", "", q)), "r": txt(bloc(c, "b")), "u": f"{{{{ROOT}}}}fr/{rub}#{a}"} for q, a in qs]
        cartes.append(f'<a class="hc-c" href="{{{{ROOT}}}}fr/{rub}">{icone.replace("ws-ic", "hc-ic", 1)}'
                      f'<span><b>{brut(bloc(c, "b"))}</b><em>{nb}</em></span></a>')
    espaces.append(f'<section class="sec hc-sp"><div class="wrap"><h2 class="h2">{txt(bloc(tete, "h2"))}</h2>'
                   f'<p class="intro">{brut(bloc(tete, "p"))}</p><div class="hc-g2">{"".join(cartes)}</div></div></section>\n')

# Pour bien démarrer : les premières questions qu'un nouvel utilisateur se pose (rubriques Premiers pas et Traduction)
CHOIX = [("aide/premiers-pas/", 0), ("aide/premiers-pas/", 2), ("aide/premiers-pas/", 3),
         ("aide/traduction-texte-et-document/", 0), ("aide/gestion-de-projet/", 0)]
FLECHE = ('<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" '
          'stroke-linejoin="round" aria-hidden="true"><path d="m9 6 6 6-6 6"/></svg>')
lignes = "".join(f'<li><a href="{{{{ROOT}}}}fr/{r}#{rubriques[r][i][1]}"><span>{rubriques[r][i][0]}</span>{FLECHE}</a></li>'
                 for r, i in CHOIX)
demarrer = (f'<section class="sec hc-sp"><div class="wrap"><h2 class="h2">{k("demarrer.titre")}</h2>'
            f'<ul class="hc-top">{lignes}</ul></div></section>\n')

entree = (f'<section class="hc-h"><div class="wrap">'
          f'<h1 class="h1"><span class="n">{txt(bloc(hero, "h1"))}</span></h1><p class="hc-lead">{brut(bloc(hero, "p", "lead"))}</p>'
          f'<form class="hc-f" role="search" data-aide-recherche data-vide="{H.escape(texte("aide.recherche.vide"))}">'
          f'<label class="sr-only" for="hc-q">{etiquette}</label>{LOUPE}'
          f'<input id="hc-q" type="search" autocomplete="off" placeholder="{place}">'
          f'<div class="hc-res" id="hc-res" role="listbox" aria-label="{H.escape(texte("aide.recherche.resultats"))}" hidden></div></form>'
          f'</div></section>\n'
          '<script type="application/json" id="aide-index">' + json.dumps(index, ensure_ascii=False).replace("</", "<\\/") + "</script>\n")

fc = bloc(t, "section", "final-cta")
h = txt(bloc(fc, "h2"))
appel = cta("Une question", h[len("Une question"):].strip(), ("Demander une démo", "{{ROOT}}fr/contact/"))

ecrire(P, entete_existant(P), entree + "".join(espaces) + demarrer + appel)
print(f"centre d'aide écrit : {len(index)} questions indexées")
