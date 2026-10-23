"""Page À propos (a-propos/) : composée par generique.py, sauf cinq blocs (audit validé par Fabien le 2026-10-23),
sur la grammaire de la page Presse (fiche de référence à filets) :

- Ce que nous pouvons prouver : liste chronologique (outil_modele.chronologie), note de la V1 rétablie.
- « Technology Empowers, Not Overpowers » : la devise et ses deux paragraphes, puis les trois principes en rangées.
- Ce qui est suisse, exactement : fiche, libellé à gauche, valeur à droite (outil_modele.fiche_signaletique).
- Une équipe experte : une rangée par personne, phrase de la V1 sur iCoSys et la HEIA-FR rétablie.
- Les catégories d'organisations : les cinq catégories de la formulation validée de la marque (contenus lot U), la
  description de la V1 pour les éditeurs juridiques, la note et le lien « Parler de votre cas » rétablis.

    cd outils/composer && python3 p_apropos.py
"""
import generique
from outil_modele import *

P = "a-propos/"
CATEGORIES = ["cabinets", "finance", "autorites", "big4"]  # puis « Éditeurs juridiques », catégorie de la V1


def leitmotiv(sec, ctx):
    box = bloc(sec, "div", "gov-box")
    tete = blocs(box, "div")[0]
    texte_ = "</p><p class=\"intro\">".join(brut(p) for p in blocs(tete, "p"))
    a = blocs(tete, "a", "feat-link")[0]
    items = []
    for d in [x for x in blocs(bloc(box, "div", "gov-steps"), "div") if 'class="gov-steps"' not in x[:30]]:
        s = bloc(d, "span")
        items.append((txt(bloc(s, "b")).rstrip("."), brut(re.sub(r"<b>.*?</b>", "", interne(s), flags=re.S)).strip()))
    return section(rangees(h2(txt(bloc(tete, "h2")), "Not Overpowers »"), texte_, (txt(a), re.search(r'href="([^"]+)"', a).group(1)), items))


def equipe(sec):
    lead = bloc(sec, "div", "ab-cats-lead")
    rangs = ""
    for it in blocs(sec, "div", "ab-item"):
        b = txt(bloc(it, "b"))
        nom, role = (b.split(" · ", 1) + [""])[:2]
        rangs += (f'<div class="eq-r"><div><p class="eq-n">{nom}</p>' + (f'<p class="eq-o">{role}</p>' if role else "")
                  + f'</div><p>{brut(bloc(it, "p"))}</p></div>')
    return section(h2(txt(bloc(lead, "h2")), generique.mots_accent(sec)) + intro_lead(lead) + f'<div class="eq">{rangs}</div>')


def categories(sec):
    lead = bloc(sec, "div", "ab-cats-lead")
    items = [(esc(texte(f"apropos.cat.{c}")), "") for c in CATEGORIES]
    items += [(txt(bloc(it, "b")), brut(bloc(it, "p"))) for it in blocs(sec, "div", "ab-item")]
    lignes = "".join(f'<div class="cg-r"><p class="eq-n">{n}</p>' + (f'<p>{d}</p>' if d else "") + '</div>' for n, d in items)
    note = brut(bloc(sec, "p", "ab-note"))
    return section(h2(txt(bloc(lead, "h2")), generique.mots_accent(sec)) + intro_lead(lead) + f'<div class="eq cg">{lignes}</div>'
                   + f'<p class="cg-note">{note}</p>' + liens_lead(lead))


def ab_cats(sec, ctx):
    return equipe(sec) if 'id="equipe"' in sec[:60] else categories(sec)


print(P, generique.composer(P, remplacer={"trust": lambda sec, ctx: chronologie(sec, generique.mots_accent(sec)), "gov": leitmotiv,
                                          "facts": lambda sec, ctx: fiche_signaletique(sec, generique.mots_accent(sec)), "ab-cats": ab_cats}) or "écrite")
