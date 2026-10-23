"""Page Fast lookup CHnell : composée par generique.py, sauf « Ce que fait Fast lookup CHnell » en trois étapes
empilées, texte et écran animé (Chercher, Lire les résultats, Depuis une traduction ; audit validé par Fabien le
2026-10-23), puis les domaines en pastilles, et « D'où viennent les segments » en rangées. Le schéma « qui fait quoi »
suit « Trois situations » (outils/post/schema_produits.APRES).

    cd outils/composer && python3 p_chnell.py
"""
import generique
from outil_modele import *

P = "corrext/chnell/"
import app as A

CHERCHER = ["Recherche", "Paires de langues", "Opérateurs"]
LIRE = ["Résultats"]
DEJA = ["Types de ressource", "Sources"]  # repris par « D'où viennent les segments », plus bas : pas de doublon
TRADUCTION = ["Fast Lookup contextuel"]


def fonctions(sec, ctx):
    lead = bloc(sec, "div", "facts-lead")
    faits = blocs(sec, "div", "fact")
    F = {txt(bloc(f, "b")): brut(bloc(f, "p")) for f in faits}
    assert set(CHERCHER + LIRE + DEJA + TRADUCTION + ["Domaines"]) == set(F), "fait de la V1 non rangé"
    pd = bloc([f for f in faits if txt(bloc(f, "b")) == "Domaines"][0], "p")
    doms = [d.strip() for d in txt(pd.replace(bloc(pd, "small"), "")).split(":", 1)[1].strip().rstrip(".").split(", ")]
    doms = [d for d in doms if d != "Other"] + ["Other"]  # « Other » en dernier, comme dans le sélecteur
    k = lambda c: texte(f"chnell.groupe.{c}")
    # Écrans au format des autres pages outils (764 × 520, Fabien, 2026-10-23) ; résultats relevés dans CHnell (Fedlex)
    def sc(ui, sim, label):
        return scene(764, 520, ui, sim=sim, titre="Corrext", curseur=False, label=label)
    bancaire = lookup("banque-finance", "secret bancaire", "French", "German", ["Bankgeheimnis", "Bankgeheimnisses"])
    bancaire["rows"] = bancaire["rows"][:2]  # deux lignes tiennent dans l'écran
    moratoires = lookup("chnell-fl", "intérêts moratoires", "French", "German", ["Verzugszinsen"])
    liste = [(k("chercher"), [(x, F[x]) for x in CHERCHER], sc(V.vue_chnell(EX["co"]["lookup"]), "chnell", "Recherche d'un terme dans CHnell")),
             (k("lire"), [(x, F[x]) for x in LIRE], sc(V.vue_chnell(bancaire), "resultats", "Résultats alignés et sources dans CHnell")),
             (texte("chnell.etape.traduction"), [(x, F[x]) for x in TRADUCTION],
              sc(A.fragment_lookup(moratoires, "intérêts moratoires"), "fastlookup", "Fast Lookup depuis Text translation"))]
    return section(h2(txt(bloc(lead, "h2")), "CHnell, exactement") + f'<p class="intro">{brut(bloc(lead, "p"))}</p>'
                   + etapes_empilees(liste) + pastilles(k("domaines"), doms))


print(P, generique.composer(P, remplacer={"who": lambda sec, ctx: situations_rangees(sec, generique.mots_accent(sec)), "facts": fonctions, "gov": lambda sec, ctx: gov_rangees(sec, generique.mots_accent(sec))}) or "écrite")
