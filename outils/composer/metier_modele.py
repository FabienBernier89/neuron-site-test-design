"""Modèle des pages métier (solutions/<métier>/), choisi par Fabien le 2026-10-19 sur la page Cabinets d'avocats
(maquettes A1, B1, C1, D2), à dérouler ensuite sur les autres métiers.

Ordre : hero (et lien vers la démo en direct) ; bandeau des distinctions ; gains chiffrés ; avis client ; sans Corrext,
avec Corrext ; les outils du métier en onglets avec un grand écran ; les niveaux de relecture ; sécurité (bloc de
gouvernance de la V1) ; déploiement ; FAQ ; appel.

Textes : la V1, mot pour mot ; nouveaux libellés dans src/data/contenus-v2/Q-metiers.json. L'avis client est un
emplacement fictif (statut « a_remplacer »), toujours affiché avec la mention « Avis fictif · à remplacer ».
"""
from paire_modele import *

CROIX = ('<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.6" stroke-linecap="round" '
         'aria-hidden="true"><path d="M6 6l12 12M18 6 6 18"/></svg>')


def lien_demo(hero_html, href):
    """Second lien du hero, discret, vers la démo en direct (libellé du méga-menu)."""
    return hero_html.replace("</a></div>", f'</a><a class="lien mt-demo" href="{href}">Ouvrir la démo en direct</a></div>', 1)


def gains(slug):
    """Trois tuiles chiffrées, même composant que les chiffres de l'accueil (.tl, .n) ; la note des maxima dessous."""
    k = lambda c: esc(texte(f"{slug}.gains.{c}"))
    titre = texte("metier.gains.titre")
    return section(h2(titre, " ".join(titre.split()[-3:])) + tuiles([(k(f"{i}.n"), None, k(f"{i}.t")) for i in (1, 2, 3)], "tl")
                   + f'<p class="mt-note">{esc(texte("metier.gains.note"))}</p>')


def avis(slug):
    """B1 : citation centrée ; emplacement fictif tant que l'avis réel n'est pas fourni."""
    k = lambda c: esc(texte(f"{slug}.avis.{c}"))
    return section(f'<figure class="mt-av" data-avis-fictif><span class="mt-fict">{esc(texte("metier.avis.fictif"))}</span>'
                   f'<blockquote>{k("texte")}</blockquote><figcaption><span class="mt-ph" aria-hidden="true"></span>'
                   f'<span><b>{k("nom")}</b>{k("fonction")}</span></figcaption></figure>', "sec mt-avis")


def sans_avec(slug, n=5):
    """C1 : tableau face à face, colonne « Avec » teintée."""
    lignes = "".join(f'<div role="row"><p role="cell" class="mt-sans"><i>{CROIX}</i>{esc(texte(f"{slug}.sa.{i}.sans"))}</p>'
                     f'<p role="cell" class="mt-avec"><i>{COCHE}</i>{esc(texte(f"{slug}.sa.{i}.avec"))}</p></div>' for i in range(1, n + 1))
    titre = texte("metier.sa.titre")
    return section(h2(titre, titre.split(", ", 1)[1]) + f'<div class="mt-sa" role="table"><div role="row" class="mt-sah">'
                   f'<span role="columnheader">{esc(texte("metier.sa.sans"))}</span><span role="columnheader">{esc(texte("metier.sa.avec"))}</span></div>{lignes}</div>')


def outils(slug, items, accent):
    """D2 : onglets à gauche (usage, outil, texte, lien), grand écran animé à droite. items : (titre, texte, href, scène)."""
    titre = texte(f"{slug}.outils.titre")
    onglets, panneaux = "", ""
    for i, (nom, txt_, href, sc) in enumerate(items, 1):
        actif = i == 1
        onglets += (f'<div class="mt-o{" on" if actif else ""}"><button type="button" role="tab" id="mt-t{i}" aria-controls="mt-p{i}" '
                    f'aria-selected="{"true" if actif else "false"}"><span class="mt-l">{esc(texte(f"{slug}.outils.{i}.usage"))}</span>'
                    f'<span class="mt-ot">{nom}</span></button><div class="mt-od"><p>{txt_}</p>'
                    f'<a class="lien" href="{href}">Découvrir l\'outil</a></div></div>')
        panneaux += f'<div class="mt-p" role="tabpanel" id="mt-p{i}" aria-labelledby="mt-t{i}"{"" if actif else " hidden"}>{sc}</div>'
    return section(h2(titre, accent) + f'<div class="mt-ou" data-onglets><div class="mt-os" role="tablist">{onglets}</div>'
                   f'<div class="mt-ps">{panneaux}</div></div>')


def niveaux():
    """Les quatre niveaux de la page Niveaux de qualité, en tuiles chiffrées (même rendu que cette page)."""
    P = "niveaux-de-qualite/"
    lv = bloc(liens(charger(P), P), "section", "levels")
    niv = [(str(i + 1), brut(bloc(x, "h3")), brut(bloc(x, "p"))) for i, x in enumerate(blocs(lv, "div", "lev"))]
    t = texte("metier.niveaux.titre")  # titre de la page Niveaux de qualité, déclaré pour les pages métier
    assert t == txt(bloc(lv, "h2")), "le titre des niveaux a changé dans la V1"
    return section(h2(t, "devant une autorité") + f'<p class="intro">{brut(bloc(bloc(lv, "div", "sec-head"), "p"))}</p>' + tuiles(niv, "tl t4"))


def deploiement(items):
    """Cartes reliées : démo, centre d'aide, API (libellés et sous-titres du méga-menu)."""
    titre = texte("metier.deploiement.titre")
    return section(h2(titre, "sans complexité") + cartes([(b, p, (lien_, href), "") for b, p, lien_, href in items]))
