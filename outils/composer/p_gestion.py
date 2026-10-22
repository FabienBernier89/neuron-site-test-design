"""Page Gestion de projet : composée par generique.py, sauf « Ce que fait Gestion de projet, exactement », qui devient
le parcours en trois étapes de l'application : un bloc par étape, l'un sous l'autre, faits de la V1 et écran animé
(Fabien, 2026-10-22) ; la mémoire de traduction passe dans un encart centré à la suite.

    cd outils/composer && python3 p_gestion.py
"""
import generique
from outil_modele import *

P = "corrext/gestion-de-projet/"
ETAPES = [("Set-up", ["Set-up", "Confidentialité", "Langues cibles"]), ("File overview", ["File overview"]),
          ("Quotes", ["Internal review", "Custom workflow", "Les trois niveaux", "Devis et délai"])]


def parcours(sec, ctx):
    lead = bloc(sec, "div", "facts-lead")
    F = {txt(bloc(f, "b")): brut(bloc(f, "p")) for f in blocs(sec, "div", "fact")}
    assert {k for _, ks in ETAPES for k in ks} | {"Mémoire de traduction"} == set(F), "fait de la V1 non rangé"
    def sc(ui, sim, label):
        return scene(764, 520, ui, sim=sim, titre="Corrext", curseur=False, label=label)
    ecrans = [sc(V.vue_setup(textes_setup()), "setup", "Set-up : nom du projet, confidentialité, langues cibles"),
              sc(V.vue_analyse("Contrat_assurance.docx", "2,5", "pages standard", "Français", "Assurance privée"), "analyse", "File overview : analyse du fichier"),
              sc(V.vue_devis("Darlehensvertrag_2026.docx", "DE → FR", NIVEAUX_RELECTURE, NIVEAUX_RELECTURE[1]), "devis", "Quotes : relecture et devis")]
    liste = [(nom, [(k, F[k]) for k in ks], ecrans[i]) for i, (nom, ks) in enumerate(ETAPES)]
    return (section(h2(txt(bloc(lead, "h2")), "projet, exactement") + f'<p class="intro">{brut(bloc(lead, "p"))}</p>' + etapes_empilees(liste))
            + bandeau("Mémoire de traduction", F["Mémoire de traduction"]))


print(P, generique.composer(P, remplacer={"who": lambda sec, ctx: situations_rangees(sec, generique.mots_accent(sec)), "facts": parcours, "gov": lambda sec, ctx: gov_rangees(sec, generique.mots_accent(sec))}) or "écrite")
