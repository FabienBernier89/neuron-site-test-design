"""Page Fast lookup CHnell : composée par generique.py, sauf « Ce que fait Fast lookup CHnell » (proposition A retenue
par Fabien le 2026-10-21 : chercher / lire les résultats en deux colonnes, puis les domaines en pastilles) et
« D'où viennent les segments » en rangées (audit des pages outils).

    cd outils/composer && python3 p_chnell.py
"""
import generique
from outil_modele import *

P = "corrext/chnell/"
CHERCHER = ["Recherche", "Paires de langues", "Opérateurs", "Fast Lookup contextuel"]
LIRE = ["Résultats", "Types de ressource", "Sources"]


def fonctions(sec, ctx):
    lead = bloc(sec, "div", "facts-lead")
    faits = blocs(sec, "div", "fact")
    F = {txt(bloc(f, "b")): brut(bloc(f, "p")) for f in faits}
    assert set(CHERCHER + LIRE + ["Domaines"]) == set(F), "fait de la V1 non rangé"
    pd = bloc([f for f in faits if txt(bloc(f, "b")) == "Domaines"][0], "p")
    doms = [d.strip() for d in txt(pd.replace(bloc(pd, "small"), "")).split(":", 1)[1].strip().rstrip(".").split(", ")]
    doms = [d for d in doms if d != "Other"] + ["Other"]  # « Other » en dernier, comme dans le sélecteur
    k = lambda c: texte(f"chnell.groupe.{c}")
    return section(h2(txt(bloc(lead, "h2")), "CHnell, exactement") + f'<p class="intro">{brut(bloc(lead, "p"))}</p>'
                   + deux_colonnes([(k("chercher"), [(x, F[x]) for x in CHERCHER]), (k("lire"), [(x, F[x]) for x in LIRE])])
                   + pastilles(k("domaines"), doms))


print(P, generique.composer(P, remplacer={"who": lambda sec, ctx: situations_rangees(sec, generique.mots_accent(sec)), "facts": fonctions, "gov": lambda sec, ctx: gov_rangees(sec, generique.mots_accent(sec))}) or "écrite")
