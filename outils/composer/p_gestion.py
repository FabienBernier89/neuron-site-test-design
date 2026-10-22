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


def court(cle, gras):
    """Texte concis d'un fait (contenus-v2), les mots clés en gras comme dans la V1."""
    def f(_):
        t_ = esc(texte(f"gestion-de-projet.quotes.{cle}"))
        for g in gras:
            assert g in t_, g
            t_ = t_.replace(g, f'<strong class="kf">{g}</strong>', 1)
        return t_
    return f


# Étape Quotes en textes concis (Fabien, 2026-10-22 : trop de texte) ; les faits complets restent dans la V1
COURT = {"Internal review": court("internal", ["Votre équipe relit", "valorisé dans le devis"]),
         "Custom workflow": court("custom", ["relecture interne ou externe"]),
         "Les trois niveaux": court("niveaux", ["Light review", "Full review", "Double review et traduction certifiée"]),
         "Devis et délai": court("devis", ["Calculés instantanément, avant toute commande"])}


def parcours(sec, ctx):
    lead = bloc(sec, "div", "facts-lead")
    F = {txt(bloc(f, "b")): brut(bloc(f, "p")) for f in blocs(sec, "div", "fact")}
    assert {k for _, ks in ETAPES for k in ks} | {"Mémoire de traduction"} == set(F), "fait de la V1 non rangé"
    def sc(ui, sim, label):
        return scene(764, 520, ui, sim=sim, titre="Corrext", curseur=False, label=label)
    ecrans = [sc(V.vue_setup(textes_setup()), "setup", "Set-up : nom du projet, confidentialité, langues cibles"),
              sc(V.vue_analyse("Contrat_assurance.docx", "2,5", "pages standard", "Français", "Assurance privée"), "analyse", "File overview : analyse du fichier"),
              sc(V.vue_devis("Darlehensvertrag_2026.docx", "DE → FR", NIVEAUX_RELECTURE, NIVEAUX_RELECTURE[1]), "devis", "Quotes : relecture et devis")]
    liste = [(nom, [(k, COURT[k](k) if k in COURT else F[k]) for k in ks], ecrans[i]) for i, (nom, ks) in enumerate(ETAPES)]
    return (section(h2(txt(bloc(lead, "h2")), "projet, exactement") + f'<p class="intro">{brut(bloc(lead, "p"))}</p>' + etapes_empilees(liste))
            + bandeau("Mémoire de traduction", F["Mémoire de traduction"]))


print(P, generique.composer(P, remplacer={"who": lambda sec, ctx: situations_rangees(sec, generique.mots_accent(sec)), "facts": parcours, "gov": lambda sec, ctx: gov_rangees(sec, generique.mots_accent(sec))}) or "écrite")
