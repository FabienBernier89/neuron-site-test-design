"""Page Éditeur de relecture : composée par generique.py, sauf trois blocs (Fabien, 2026-10-21) :
« Ce que fait l'éditeur » en tuiles, une par fonction, avec sa famille (Relire, Vérifier, Partager et suivre) et son
icône (version B revue, 2026-10-23) ;
le parcours « Du fichier déposé au document validé » en frise compacte, suivi de « Travailler dans Word » réduit à
son texte, un lien vers la page Plugin Word et l'écran Word de cette page (proposition D).

    cd outils/composer && python3 p_editeur.py
"""
import generique
from outil_modele import *
import p_plugin_word

P = "corrext/editeur-de-relecture/"
FAMILLES = [("Relire", ["Deux colonnes", "Origine de chaque phrase", "Confirmation", "Barre d'outils"]),
            ("Vérifier", ["Contrôles", "Mémoires", "Fast Lookup", "Assistant IA"]),
            ("Partager et suivre", ["Sync", "Tableau de bord"])]
ICONES = ICONES_FONCTIONS  # outil_modele ; fonctions phares en grand
GRAND = {"Deux colonnes", "Origine de chaque phrase", "Fast Lookup", "Assistant IA", "Sync", "Tableau de bord"}


def fonctions(sec, ctx):
    lead = bloc(sec, "div", "facts-lead")
    F = {}
    for f in blocs(sec, "div", "fact"):  # la note en petit de la V1 (définition) reste hors de la tuile
        p = bloc(f, "p")
        F[txt(bloc(f, "b"))] = brut(p.replace(bloc(p, "small"), "")) if "<small>" in p else brut(p)
    assert {k for _, ks in FAMILLES for k in ks} == set(F) <= set(ICONES), "fait de la V1 non rangé"
    return section(h2(txt(bloc(lead, "h2")), "relecture, exactement") + f'<p class="intro">{brut(bloc(lead, "p"))}</p>'
                   + tuiles_fonctions([(n, k, F[k], ICONES[k]) for n, ks in FAMILLES for k in ks], GRAND))


def parcours(sec, ctx):
    lead = bloc(sec, "div", "trust-lead")
    rangs = [(txt(bloc(r, "span", "ty")), txt(re.sub(r"<small>.*?</small>", "", bloc(r, "span", "tn"), flags=re.S)), brut(bloc(r, "small")),
              txt(bloc(r, "span", "tb"))) for r in blocs(sec, "div", "ledger-row")]
    # « Travailler dans Word » : rendu dans ce bloc, juste après le parcours (le bloc cxe-word de la V1 est remplacé)
    w = bloc(ctx["t"], "section", "cxe-word")
    titre_w = txt(bloc(w, "span", "pn")).rstrip(".")
    ecran = scene(1176, 640, p_plugin_word.ecran_word(), sim="word", titre="Microsoft Word", curseur=False, label="Le panneau Corrext dans Microsoft Word")
    word = (f'<div class="ow"><div><h3>{titre_w}</h3><p>{brut(bloc(w, "p"))}</p>'
            f'<a class="lien" href="{{{{ROOT}}}}fr/corrext/plugin-word/">{texte("editeur-de-relecture.word.lien")}</a></div><div>{ecran}</div></div>')
    return section(h2(txt(bloc(lead, "h2")), "document validé") + f'<p class="intro">{brut(bloc(lead, "p"))}</p>' + frise(rangs) + word)


print(P, generique.composer(P, remplacer={"who": lambda sec, ctx: situations_rangees(sec, generique.mots_accent(sec)), "facts": fonctions, "gov": lambda sec, ctx: gov_rangees(sec, generique.mots_accent(sec)), "trust": parcours, "cxe-word": lambda sec, ctx: ""}) or "écrite")
