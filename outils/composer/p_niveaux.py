"""Page Niveaux de qualité, refonte validée par Fabien le 2026-10-20 (audit du même jour) :
hero ; les quatre niveaux en escalier (usage, qui intervient, où il se commande et ce qui est livré : les tuiles et les
neuf faits « où / qui » de la V1 réunis) ; dans l'application (écran de devis animé et les trois libellés exacts de
l'étape Quotes) ; le tableau « quel niveau pour quel document » réparé ; devis, délai et confidentialité en bandeau ;
pour aller plus loin ; FAQ ; appel. Textes de la V1 mot pour mot ; nouveau libellé dans contenus-v2/R-niveaux.json.

    cd outils/composer && python3 p_niveaux.py
"""
from paire_modele import *
import generique

P = "niveaux-de-qualite/"
t = liens(charger(P), P)


def escalier():
    lv = bloc(t, "section", "levels")
    niv = [(brut(bloc(x, "h3")), brut(bloc(x, "p"))) for x in blocs(lv, "div", "lev")]
    fa = bloc(t, "section", "facts")
    F = {txt(bloc(f, "b")): brut(bloc(f, "p")) for f in blocs(fa, "div", "fact")}
    # (libellé de la V1, colonne de départ, nombre de colonnes, ligne de la grille)
    cellules = [("Niveau 1 · qui", 1, 1, 3), ("Niveau 2 · qui", 2, 1, 3), ("Niveau 3 · qui", 3, 1, 3), ("Niveau 4 · qui", 4, 1, 3),
                ("Niveau 1 · où", 1, 1, 4), ("Niveaux 2 et 3 · où", 2, 2, 4), ("Niveau 4 · où", 4, 1, 4)]
    utilises = {c for c, *_ in cellules} | {"Devis et délai", "Confidentialité"}
    assert utilises == set(F), f"faits de la V1 non rangés : {set(F) ^ utilises}"
    g = ""
    for i, (titre, texte_) in enumerate(niv, 1):
        g += (f'<div class="nq-h" style="grid-column:{i};grid-row:1"><span class="nq-bar" style="--n:{i}"></span>'
              f'<p class="nq-n">Niveau {i}</p><h3>{titre}</h3></div>'
              f'<p class="nq-u" style="grid-column:{i};grid-row:2">{texte_}</p>')
        for lib, col, span, row in cellules:
            if col == i:
                g += f'<div class="nq-c" style="grid-column:{col} / span {span};grid-row:{row}"><p class="nq-l">{lib}</p><p>{F[lib]}</p></div>'
    gr = "".join(f'<div><span class="pa-ck">{COCHE}</span><div><h3>{k}</h3><p>{F[k]}</p></div></div>' for k in ("Devis et délai", "Confidentialité"))
    return section(h2(txt(bloc(lv, "h2")), "une autorité") + f'<p class="intro">{brut(bloc(bloc(lv, "div", "sec-head"), "p"))}</p>'
                   + f'<p class="nq-prog">{esc(texte("niveaux.progression"))}</p><div class="nq-esc">{g}</div>'
                   + f'<div class="pa-gr nq-gr">{gr}</div>')


def application():
    nd = bloc(t, "section", "nq-defs")
    defs = "".join(f'<div class="nq-d"><p class="nq-dl">{txt(bloc(d, "h3"))}</p><blockquote lang="en">{brut(bloc(d, "blockquote"))}</blockquote>'
                   f'<p>{brut(bloc(d, "p"))}</p></div>' for d in blocs(nd, "div", "nq-def"))
    ecran = scene(764, 500, V.vue_devis("Darlehensvertrag_2026.docx", "DE → FR", NIVEAUX_RELECTURE, NIVEAUX_RELECTURE[1]), sim="devis", curseur=False,
                  label="Devis avec relecture complète par un traducteur juridique")
    return section(h2(txt(bloc(nd, "h2")), "de l'application") + f'<p class="intro">{brut(bloc(bloc(nd, "div", "sec-head"), "p"))}</p>'
                   + f'<div class="nq-app"><div class="nq-sc">{ecran}</div><div class="nq-ds">{defs}</div></div>')


def tableau():
    cp = bloc(t, "section", "compare")
    tab = bloc(cp, "table")
    entetes = [txt(x) for x in re.findall(r"<th[^>]*>(.*?)</th>", bloc(tab, "thead"), re.S)]
    lignes = ""
    for tr in blocs(bloc(tab, "tbody"), "tr"):
        cel = re.findall(r"<t([hd])[^>]*>(.*?)</t[hd]>", tr, re.S)
        out = ""
        for j, ((_, v), e) in enumerate(zip(cel, entetes)):
            if j == 0:
                out += f'<th scope="row" class="pa-s" data-m="{e}">{brut(v)}</th>'
            elif j == 1:  # pastille du niveau, puis son libellé
                n = re.search(r'<span class="cmp-[a-z]">(.*?)</span>', v, re.S)
                out += f'<td data-m="{e}"><span class="nq-pill">{txt(n.group(1))}</span>{txt(v.replace(n.group(0), ""))}</td>'
            else:  # mention principale, puis précision sur sa propre ligne
                out += f'<td class="nq-x" data-m="{e}"><b>{brut(bloc(v, "b"))}</b><span>{brut(bloc(v, "span"))}</span></td>'
        lignes += f"<tr>{out}</tr>"
    tete = "".join(f'<th scope="col" class="{"pa-s" if j == 0 else "pa-n"}">{e}</th>' for j, e in enumerate(entetes))
    note = bloc(cp, "p", "compare-note")  # la règle générale : le destinataire fixe l'exigence
    return section(h2(txt(bloc(cp, "h2")), "quel document") + f'<p class="intro">{brut(note)}</p>'
                   + f'<div class="pa-tw"><table class="pa-t nq-t"><thead><tr>{tete}</tr></thead><tbody>{lignes}</tbody></table></div>')


th = bloc(t, "section", "thero")
h1 = bloc(th, "h1")
out = [hero(txt(bloc(h1, "em")), txt(re.sub(r"<em>.*?</em>", "", h1, flags=re.S)), brut(bloc(th, "p", "lead")), ("Demander une démo", C)),
       escalier(), application(), tableau(), generique.h_siblings(bloc(t, "section", "siblings"), {}), faq_section(t), cta_section(t, "Hésitez sur le niveau ?")]
ecrire(P, entete_existant(P), "".join(out))
print(f"{P} écrite")
