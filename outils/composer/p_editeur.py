"""Page Éditeur de relecture : composée par generique.py, sauf trois blocs (Fabien, 2026-10-21) :
« Ce que fait l'éditeur » en trois familles d'onglets (proposition B : Relire, Vérifier, Partager et suivre) ;
le parcours « Du fichier déposé au document validé » en frise compacte, suivi de « Travailler dans Word » réduit à
son texte, un lien vers la page Plugin Word et l'écran Word de cette page (proposition D).

    cd outils/composer && python3 p_editeur.py
"""
import generique
from outil_modele import *
import p_plugin_word

P = "corrext/editeur-de-relecture/"
FAMILLES = [("Relire", "relire", ["Deux colonnes", "Origine de chaque phrase", "Confirmation", "Barre d'outils"]),
            ("Vérifier", "verifier", ["Contrôles", "Mémoires", "Fast Lookup", "Assistant IA"]),
            ("Partager et suivre", "partager", ["Sync", "Tableau de bord"])]


def fonctions(sec, ctx):
    lead = bloc(sec, "div", "facts-lead")
    F = {txt(bloc(f, "b")): brut(bloc(f, "p")) for f in blocs(sec, "div", "fact")}
    assert {k for *_, ks in FAMILLES for k in ks} == set(F), "fait de la V1 non rangé"
    return section(h2(txt(bloc(lead, "h2")), "relecture, exactement") + f'<p class="intro">{brut(bloc(lead, "p"))}</p>'
                   + familles([(n, c, [(k, F[k]) for k in ks]) for n, c, ks in FAMILLES]))


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


print(P, generique.composer(P, remplacer={"facts": fonctions, "trust": parcours, "cxe-word": lambda sec, ctx: ""}) or "écrite")
