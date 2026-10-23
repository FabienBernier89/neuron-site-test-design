"""Page Presse (a-propos/presse/) : composée par generique.py, sauf quatre blocs (audit validé par Fabien le
2026-10-23) : une seule grammaire « fiche de référence », à filets et sans cartes, pour ce qu'un journaliste consulte
et copie ; seules les ressources pour la rédaction, le bloc d'action, restent en cartes.

- Neur.on en bref : fiche signalétique, libellé à gauche, valeur à droite.
- Distinctions et certification : liste chronologique, l'année une seule fois en marge.
- Comment nous nommer : une rangée par nom, avec ce qu'il désigne et son orthographe (bloc pr-spell de la V1).
- Ressources pour la rédaction : deux cartes à icône et un lien qui ouvre l'e-mail, sans l'intro en double.

    cd outils/composer && python3 p_presse.py
"""
import generique
from outil_modele import *

P = "a-propos/presse/"
MAIL = "team@corrext.com"
k = lambda c: texte(f"presse.{c}")


def liens_v1(bloc_):
    """Liens de la V1 (feat-link) en liens fléchés."""
    out = ""
    for a in blocs(bloc_, "a", "feat-link"):
        href = re.search(r'href="([^"]+)"', a).group(1)
        out += f'<a class="lien" href="{href}">{txt(a)}</a>'
    return out


def fiche(sec, ctx):
    lead = bloc(sec, "div", "facts-lead")
    lignes = "".join(f'<div><dt>{txt(bloc(f, "b"))}</dt><dd>{brut(bloc(f, "p"))}</dd></div>' for f in blocs(sec, "div", "fact"))
    return section(h2(txt(bloc(lead, "h2"))) + f'<p class="intro">{brut(bloc(lead, "p"))}</p><dl class="fs">{lignes}</dl>'
                   + f'<p class="fs-l">{liens_v1(lead)}</p>')


def distinctions(sec, ctx):
    lead = bloc(sec, "div", "trust-lead")
    annees = {}
    for r in blocs(sec, "div", "ledger-row"):
        nom = txt(re.sub(r"<small>.*?</small>", "", bloc(r, "span", "tn"), flags=re.S))
        annees.setdefault(txt(bloc(r, "span", "ty")), []).append(
            f'<li><b>{nom}</b><span>{brut(bloc(r, "small"))}</span><em>{txt(bloc(r, "span", "tb"))}</em></li>')
    corps = "".join(f'<div class="ch-a"><p class="ch-y">{a}</p><ul>{"".join(li)}</ul></div>' for a, li in annees.items())
    return section(h2(txt(bloc(lead, "h2"))) + f'<p class="intro">{brut(bloc(lead, "p"))}</p><div class="ch">{corps}</div>')


def nommer(sec, ctx):
    box = bloc(sec, "div", "gov-box")
    tete = blocs(box, "div")[0]
    ecrit = {txt(bloc(s, "b")): brut(re.sub(r"<b>.*?</b>", "", interne(s), flags=re.S)).lstrip(" :") for s in blocs(bloc(box, "div", "pr-spell"), "span")}
    rangs = ""
    for d in [x for x in blocs(bloc(box, "div", "gov-steps"), "div") if 'class="gov-steps"' not in x[:30]]:  # sans le conteneur
        s = bloc(d, "span")
        nom = txt(bloc(s, "b"))
        designe = brut(re.sub(r"<b>.*?</b>", "", interne(s), flags=re.S)).strip()
        # phrases de la V1 mot pour mot, qui se lisent à la suite du nom (« Neur.on · désigne… », « s'écrit… »)
        rangs += f'<div class="nm-r"><p class="nm-n">{nom}</p><p>{designe}</p><p>{ecrit[nom]}</p></div>'
    assert rangs.count('class="nm-r"') == 4 == len(ecrit), "noms de la V1 changés"
    return section(h2(txt(bloc(tete, "h2"))) + f'<p class="intro">{brut(bloc(tete, "p"))}</p><div class="nm">{rangs}</div>')


def ressources(sec, ctx):
    cartes_ = ""
    for it in blocs(sec, "div", "pr-res-item"):
        ic = re.search(r"<svg.*?</svg>", it, re.S).group(0).replace("<svg ", '<svg aria-hidden="true" ', 1)
        cartes_ += (f'<div class="gq-c"><span class="gq-i">{ic}</span><div><h3>{txt(bloc(it, "b"))}</h3><p>{brut(bloc(it, "p"))}</p>'
                    f'<p class="pr-m"><a class="lien" href="mailto:{MAIL}">{esc(k("res.lien"))}</a></p></div></div>')
    return section(h2(txt(bloc(sec, "h2"))) + f'<div class="gq">{cartes_}</div>')


print(P, generique.composer(P, remplacer={"facts": fiche, "trust": distinctions, "gov": nommer, "pr-res": ressources}) or "écrite")
