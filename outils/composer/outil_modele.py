"""Modèle des pages outils (corrext/<outil>/), refonte validée par Fabien le 2026-10-20 sur Traduction texte et
document (proposition A) : la description de l'outil passe en onglets compacts groupés, chacun avec son écran animé
de même taille, et les faits chiffrables en tuiles chiffrées. Onglets : assets/global/metier.js ([data-onglets])."""
from paire_modele import *


def onglets_groupes(groupes):
    """groupes : [(intertitre, [(nom, texte, écran)])]. Liste compacte à gauche (seul l'onglet ouvert montre son texte),
    écran animé à droite ; la liste garde à peu près la hauteur de l'écran (Fabien, 2026-10-20)."""
    tabs, panneaux, i = "", "", 0
    for titre, items in groupes:
        tabs += f'<p class="ot-gh" role="presentation">{esc(titre)}</p>'
        for nom, texte_, ecran in items:
            i += 1
            on = i == 1
            tabs += (f'<div class="mt-o{" on" if on else ""}"><button type="button" role="tab" id="ot-t{i}" aria-controls="ot-p{i}" '
                     f'aria-selected="{"true" if on else "false"}"><span class="mt-ot">{nom}</span></button>'
                     f'<div class="mt-od"><p>{texte_}</p></div></div>')
            panneaux += f'<div class="mt-p" role="tabpanel" id="ot-p{i}" aria-labelledby="ot-t{i}"{"" if on else " hidden"}>{ecran}</div>'
    return f'<div class="mt-ou ot-cp" data-onglets><div class="mt-os" role="tablist">{tabs}</div><div class="mt-ps">{panneaux}</div></div>'


def chiffres(items, cls="tl"):
    """items : [(chiffre tel que « 30 Langues », texte)]. Unité accolée en petit, comme les chiffres de l'accueil."""
    def chiffre(n):
        m = re.fullmatch(r"([\d'.,]+(?: M\+)?) ([A-Za-zÀ-ÿ]+)", n)
        return f'{m.group(1)} <span class="u">{m.group(2)}</span>' if m else n
    return tuiles([(chiffre(esc(n)), None, t_) for n, t_ in items], cls)


def etapes(liste, note=""):
    """Parcours en étapes (proposition B retenue par Fabien le 2026-10-21 pour Gestion de projet) : barre des étapes
    comme l'indicateur de l'application ; l'étape ouverte montre tous ses faits à gauche et son écran à droite.
    liste : [(nom de l'étape, [(titre, texte)], écran)] ; note : paragraphe sous le parcours (HTML)."""
    barre, panneaux = "", ""
    for i, (nom, faits_, ecran) in enumerate(liste, 1):
        on = i == 1
        barre += (f'<span class="et-o{" on" if on else ""}"><button type="button" role="tab" id="et-t{i}" aria-controls="et-p{i}" '
                  f'aria-selected="{"true" if on else "false"}"><i>{i}</i>{nom}</button></span>')
        gauche = "".join(f'<div><h3>{t_}</h3><p>{p}</p></div>' for t_, p in faits_)
        panneaux += (f'<div class="et-p" role="tabpanel" id="et-p{i}" aria-labelledby="et-t{i}"{"" if on else " hidden"}>'
                     f'<div class="et-l">{gauche}</div><div>{ecran}</div></div>')
    return (f'<div class="et" data-onglets><div class="et-bar" role="tablist">{barre}</div>{panneaux}</div>'
            + (f'<p class="et-note">{note}</p>' if note else ""))
