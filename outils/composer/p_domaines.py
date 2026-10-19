"""Pages de domaine du droit (traduction/<domaine>/), sur le modèle choisi par Fabien le 2026-10-19
(outils/composer/domaine_modele.py). Une configuration par page : recherche CHnell relevée pour le domaine, actes
(colonne de gauche du bloc « concrètement » ; les autres faits de la V1 vont dans l'encart Corrext), accents.

    cd outils/composer && python3 p_domaines.py [domaine]
"""
import sys

from domaine_modele import *

DOMAINES = {
    "droit-des-societes": {
        "chnell": ("assemblée générale", "French", "German", "Generalversammlung"),
        "actes": ["Statuts", "Procès-verbaux", "Inscription au registre"],
        "concret": "société, concrètement", "situations": "la traduction", "cta": "Vos statuts",
    },
}


def composer(slug, cfg):
    P = f"traduction/{slug}/"
    q, l1, l2, marque = cfg["chnell"]
    cfg = dict(cfg, lookup=lookup(slug, q, l1, l2, marque))
    t = liens(charger(P), P)
    th = bloc(t, "section", "thero")
    h1 = bloc(th, "h1")
    out = [hero(txt(bloc(h1, "em")), txt(re.sub(r"<em>.*?</em>", "", h1, flags=re.S)), brut(bloc(th, "p", "lead")), ("Demander une démo", C)),
           chnell(P, cfg),
           equivalences(t, cfg, "dans les quatre langues"),
           textes_reference(t),
           concretement(t, cfg["actes"], cfg["concret"]),
           situations(t, cfg["situations"]),
           faq_section(t),
           voisins(t),
           cta_section(t, cfg["cta"])]
    ecrire(P, entete_existant(P), "".join(out))
    print(f"{P} écrite")


if __name__ == "__main__":
    for slug in sys.argv[1:] or DOMAINES:
        composer(slug, DOMAINES[slug])
