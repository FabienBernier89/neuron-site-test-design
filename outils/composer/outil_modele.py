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
                     f'<div class="mt-od"><div><p>{texte_}</p></div></div></div>')
            panneaux += f'<div class="mt-p" role="tabpanel" id="ot-p{i}" aria-labelledby="ot-t{i}"{"" if on else " hidden"}>{ecran}</div>'
    return f'<div class="mt-ou ot-cp" data-onglets><div class="mt-os" role="tablist">{tabs}</div><div class="mt-ps">{panneaux}</div></div>'


def chiffres(items, cls="tl"):
    """items : [(chiffre tel que « 30 Langues », texte)]. Unité accolée en petit, comme les chiffres de l'accueil."""
    def chiffre(n):
        m = re.fullmatch(r"([\d'.,]+(?: M\+)?) ([A-Za-zÀ-ÿ]+)", n)
        return f'{m.group(1)} <span class="u">{m.group(2)}</span>' if m else n
    return tuiles([(chiffre(esc(n)), None, t_) for n, t_ in items], cls)


def etapes_empilees(liste):
    """Parcours en étapes empilées (Gestion de projet, demande de Fabien du 2026-10-22) : un bloc par étape, l'un sous
    l'autre, le numéro, le nom de l'étape et ses faits d'un côté, son écran animé de l'autre (côtés alternés).
    liste : [(nom de l'étape, [(titre, texte)], écran)]."""
    blocs_ = ""
    for i, (nom, faits_, ecran) in enumerate(liste, 1):
        # un fait qui porte le nom de l'étape n'en répète pas le titre
        faits_html = "".join(f'<div>{"" if t_ == nom else f"<h4>{t_}</h4>"}<p>{p}</p></div>' for t_, p in faits_)
        blocs_ += (f'<div class="ee-b{" ee-inv" if i % 2 == 0 else ""}"><div class="ee-t"><h3 class="ee-n"><i>{i}</i>{nom}</h3>'
                   f'<div class="ee-f">{faits_html}</div></div><div class="ee-e">{ecran}</div></div>')
    return f'<div class="ee">{blocs_}</div>'


def bandeau(titre, texte_):
    """Encart centré, à la manière des bandeaux d'appel (Gestion de projet : la mémoire de traduction)."""
    return section(f'<div class="enc"><h2>{titre}</h2><p>{texte_}</p></div>')


ICONES_FAMILLE = {"relire": '<path d="M4 5h7v14H4zM13 5h7v14h-7z"/>', "verifier": '<circle cx="11" cy="11" r="7"/><path d="m20 20-3.5-3.5"/>',
                  "partager": '<circle cx="8" cy="9" r="3"/><circle cx="17" cy="9" r="3"/><path d="M3 19a5 5 0 0 1 10 0M12 19a5 5 0 0 1 10 0"/>'}


def familles(liste):
    """Fonctions rangées par famille, en onglets (proposition B retenue par Fabien le 2026-10-21 pour l'Éditeur de
    relecture) : même barre que le parcours en étapes ; la famille ouverte montre ses fonctions sur deux colonnes.
    liste : [(nom, clé d'icône, [(titre, texte)])]."""
    barre, panneaux = "", ""
    for i, (nom, cle, faits_) in enumerate(liste, 1):
        on = i == 1
        ic = (f'<span class="pa-ic"><svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" '
              f'stroke-linejoin="round" aria-hidden="true">{ICONES_FAMILLE[cle]}</svg></span>')
        barre += (f'<span class="et-o{" on" if on else ""}"><button type="button" role="tab" id="fa-t{i}" aria-controls="fa-p{i}" '
                  f'aria-selected="{"true" if on else "false"}">{ic}{nom}</button></span>')
        panneaux += (f'<div class="fa-p" role="tabpanel" id="fa-p{i}" aria-labelledby="fa-t{i}"{"" if on else " hidden"}>'
                     + "".join(f'<div><h3>{t_}</h3><p>{p}</p></div>' for t_, p in faits_) + '</div>')
    return f'<div class="et" data-onglets><div class="et-bar" role="tablist">{barre}</div>{panneaux}</div>'


def frise(rangs):
    """Parcours en frise compacte (Éditeur de relecture, proposition D) : rangs = [(numéro, titre, texte, étiquette)] ;
    les étapes faites à la création du projet sont soulignées en bleu ; sans étiquette, toutes les étapes le sont."""
    def etape(n, ti, tx, ph):
        tag = f'<span class="fr-ph">{ph}</span>' if ph else ""
        return f'<li class="{"fr-p" if ph in ("Projet", "") else ""}"><span class="fr-n">{n}</span>{tag}<h3>{ti}</h3><p>{tx}</p></li>'
    return '<ol class="fr">' + "".join(etape(*r) for r in rangs) + '</ol>'


def rangees(titre_h2, texte_, lien, items):
    """Garanties en rangées lisibles, à la place d'un bento à texte centré (pages outils, audit du 2026-10-20) :
    titre, texte et lien, puis une rangée de faits (titre, texte) soulignés d'un filet bleu. lien : (libellé, href)."""
    return (titre_h2 + f'<p class="intro">{texte_}</p>' + '<div class="rg">' + "".join(f'<div><h3>{t_}</h3><p>{p}</p></div>' for t_, p in items)
            + f'</div><p class="rg-lien"><a class="lien" href="{lien[1]}">{lien[0]}</a></p>')


def gov_rangees(t, accent):
    """Le bloc de gouvernance de la V1 (titre, texte, lien, petites étapes) rendu en rangées au lieu du bento."""
    gv = bloc(t, "section", "gov")  # t : la page ou la section elle-même
    box = bloc(gv, "div", "gov-box")
    a = blocs(box, "a", "feat-link")
    items = []
    for x in blocs(bloc(gv, "div", "gov-steps"), "span"):
        if "<b>" not in x[:12]:
            continue
        items.append((txt(bloc(x, "b")).strip().rstrip("."), brut(re.sub(r"<b>.*?</b>", "", interne(x), flags=re.S))))
    lien = (txt(a[0]), re.search(r'href="([^"]+)"', a[0]).group(1)) if a else None
    corps = h2(txt(bloc(box, "h2")), accent) + f'<p class="intro">{brut(bloc(box, "p"))}</p>' + '<div class="rg">' \
        + "".join(f'<div><h3>{t_}</h3><p>{p}</p></div>' for t_, p in items) + '</div>'
    return section(corps + (f'<p class="rg-lien"><a class="lien" href="{lien[1]}">{lien[0]}</a></p>' if lien else ""))


def deux_colonnes(groupes):
    """Faits en deux colonnes titrées (proposition A retenue par Fabien le 2026-10-21 pour CHnell) :
    groupes = [(intertitre, [(titre, texte)])]."""
    return '<div class="dc">' + "".join(f'<div><p class="pa-st">{esc(g)}</p>' + "".join(f'<div class="dc-i"><h3>{t_}</h3><p>{p}</p></div>' for t_, p in items) + '</div>'
                                        for g, items in groupes) + '</div>'


def pastilles(titre, items):
    """Liste en pastilles dans un encart (les domaines de CHnell)."""
    return f'<div class="pst"><p class="pst-t">{esc(titre)}</p><div class="pst-l">' + "".join(f'<span>{esc(x)}</span>' for x in items) + '</div></div>'


def situations_rangees(wh, accent):
    """« Trois situations » en rangées éditoriales (proposition A retenue par Fabien le 2026-10-22) : le métier et son
    icône (V1), le titre en serif, le texte ; filets entre les rangées, sans fond, pour ne pas redoubler les tuiles."""
    rangs = "".join(f'<div class="sr-r"><p class="sr-p">{bloc(r, "span", "ws-ic").replace("ws-ic", "sr-ic", 1)}{txt(bloc(r, "span", "sc-a"))}</p>'
                    f'<h3>{brut(bloc(r, "h3"))}</h3><p class="sr-t">{brut(bloc(r, "p"))}</p></div>' for r in blocs(wh, "article", "sc-row"))
    return section(h2(txt(bloc(wh, "h2")), accent) + f'<div class="sr">{rangs}</div>')
