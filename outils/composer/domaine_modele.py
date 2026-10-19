"""Modèle des pages de domaine du droit (traduction/<domaine>/), choisi par Fabien le 2026-10-19 sur la page Droit des
sociétés (maquettes 1-B et 2-B), à dérouler ensuite sur les autres domaines.

Ordre : hero ; CHnell en contexte sur un terme du domaine ; les équivalences (tableau des paires, sans langue mise en
avant) ; les textes de référence en registre (abréviation en grand, nom, abréviations allemande et italienne, texte) ;
« concrètement » en deux colonnes (ce que les actes demandent, ce que Corrext apporte) ; les situations (icône et
contexte de la V1) ; FAQ ; les autres domaines ; appel.

Textes : la page actuelle (V1), mot pour mot ; nouveaux libellés dans src/data/contenus-v2/P-domaines.json (à relire).
"""
from paire_modele import *


def textes_reference(t):
    """Registre des textes de loi : la fin « ; OR en allemand, CO en italien » de la V1 devient des étiquettes."""
    tl = bloc(t, "section", "tlaws")
    lead = bloc(tl, "div", "tlaws-lead")
    lignes = ""
    for x in blocs(tl, "div", "tlaw"):
        texte_ = brut(bloc(x, "p"))
        m = re.search(r" ; ([^;]*\ben (?:allemand|italien)\b[^;]*)\.$", texte_)
        langues = ""
        if m:
            texte_ = texte_[:m.start()]  # le point final est affiché par la feuille (.dm-tr) : le texte reste celui de la V1
            langues = "".join(f'<span class="dm-lg"><i>{"DE" if l == "allemand" else "IT"}</i>{a}</span>'
                              for a, l in re.findall(r"([\w-]+) en (allemand|italien)", m.group(1)))
        lignes += (f'<div><p class="dm-ab">{txt(bloc(x, "span", "ab"))}</p><div><h3>{txt(bloc(x, "b"))}</h3>'
                   + (f'<p class="dm-lgs">{langues}</p>' if langues else "") + f'</div><p{' class="dm-tr"' if m else ""}>{texte_}</p></div>')
    return section(h2(txt(bloc(lead, "h2")), mots_fin(txt(bloc(lead, "h2")))) + f'<p class="intro">{brut(bloc(lead, "p"))}</p>'
                   + f'<div class="dm-reg">{lignes}</div>')


def intertitre_actes(slug):
    """Intertitre de la colonne de gauche : propre au domaine ({slug}.actes) sinon commun (domaine.actes)."""
    try:
        return texte(f"{slug}.actes")
    except KeyError:
        return texte("domaine.actes")


def mots_fin(titre, n=2):
    m = titre.rstrip(" .?!").split(" ")
    return " ".join(m[-n:])


def concretement(t, actes, accent, slug=None):
    """Deux colonnes : les actes numérotés (besoin), les apports de Corrext en encart (réponse)."""
    fa = bloc(t, "section", "facts")
    lead = bloc(fa, "div", "facts-lead")
    faits_ = {txt(bloc(f, "b")): brut(bloc(f, "p")) for f in blocs(fa, "div", "fact")}
    assert set(actes) <= set(faits_), f"actes absents de la V1 : {set(actes) - set(faits_)}"
    apports = [k for k in faits_ if k not in actes]
    gauche = "".join(f'<li><h3>{k}</h3><p>{faits_[k]}</p></li>' for k in actes)
    droite = "".join(f'<div><span class="pa-ck">{COCHE}</span><div><h3>{k}</h3><p>{faits_[k]}</p></div></div>' for k in apports)
    return section(h2(txt(bloc(lead, "h2")), accent) + f'<p class="intro">{brut(bloc(lead, "p"))}</p>'
                   + f'<div class="dm-2c"><div><p class="pa-st">{esc(intertitre_actes(slug))}</p><ol class="dm-num">{gauche}</ol></div>'
                   + f'<div class="dm-in"><p class="pa-st">{esc(texte("domaine.apporte"))}</p><div class="dm-ck">{droite}</div></div></div>')
