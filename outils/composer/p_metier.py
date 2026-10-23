"""Pages métier (solutions/<métier>/), sur le modèle choisi par Fabien le 2026-10-19 sur Cabinets d'avocats et déroulé
sur les autres métiers le 2026-10-20 (outils/composer/metier_modele.py) : gains, avis, sans / avec Corrext, outils du
métier en onglets, niveaux de relecture, sécurité, déploiement, FAQ, appel. Les boutons « Demander une démo » mènent
au formulaire avec le secteur prérempli (lot C).

    cd outils/composer && python3 p_metier.py [métier]
"""
import sys

from metier_modele import *
from lexmachina_ecran import ecran_corrige, k as k_lm
import trame

DEMO = "{{ROOT}}fr/corrext/traduction-texte-et-document/#demo"


def ecrans():
    """Écrans animés de l'application, un par outil (même taille pour tous : Fabien, 2026-10-19)."""
    et, nivs, soc, ide = textes_extrait()
    d = EX["ldip"]
    return {
        "lot": scene(764, 500, V.vue_fichiers(fichiers_demo("pdf", "fichier")), sim="lot", curseur=False, label="Traduction d'un lot de fichiers"),
        "devis": scene(764, 500, V.vue_devis("Darlehensvertrag_2026.docx", "DE → FR", NIVEAUX_RELECTURE, NIVEAUX_RELECTURE[1]), sim="devis", curseur=False,
                       label="Devis avec relecture complète par un traducteur juridique"),
        "extrait": scene(764, 500, V.vue_extrait(et, nivs, soc, ide, "German", 2, ("Company", "Target language", "Certification level")), sim="extrait",
                         curseur=False, label="Commande d'un extrait du registre du commerce certifié"),
        "alts": scene(764, 500, V.vue_alternatives("ldip", esc(d["src"]), esc(d["out"]["en"]["main"]), esc(d["out"]["en"]["alt"][0]["t"]), d["out"]["en"]["alt"][0]["e"],
                                                   len(d["out"]["en"]["alt"])), sim="alts", curseur=False, label="Alternatives attribuées à leur moteur"),
        "api": scene(764, 500, ecran_api(), sim="api", titre="Microsoft Word", curseur=False, label="Traduction d'un paragraphe Word par appel d'API"),
        "lexmachina": scene(764, 500, ecran_corrige(), sim="corrige", titre=k_lm("compare.fenetre"), curseur=False, label=k_lm("compare.fenetre")),
    }


def chnell_(domaine, q, marque):
    """CHnell sur une recherche relevée pour une page de domaine (contenus-v2/P-domaines.json)."""
    return scene(764, 500, V.vue_chnell(lookup(domaine, q, "French", "German", marque)), sim="chnell", curseur=False, titre="CHnell", label="Fast lookup CHnell")


# Outil absent du bloc « outils les plus utilisés » de la V1 d'une page : texte et lien repris d'une autre page du site
HORS_V1 = {
    "Fast lookup CHnell": ("L'usage officiel d'un terme, sourcé, dans les quatre langues.", "{{ROOT}}fr/corrext/chnell/", "Découvrir l'outil"),
    "Traduction texte et document": ("Pièces, contrats, correspondance : texte et fichiers, en quelques secondes.", "{{ROOT}}fr/corrext/traduction-texte-et-document/", "Découvrir l'outil"),
}

# Par métier : outils (nom tel que dans la V1, écran), accents des titres, place des blocs propres à la page.
# « securite » : la V1 de la page n'a pas de bloc sécurité ; bloc construit (titre de la page, texte d'un fait de la V1)
# et le bloc de gouvernance de la V1 prend la place des niveaux de relecture.
METIERS = {
    "cabinets-avocats": {
        "outils": [("Traduction texte et document", "lot"), ("Gestion de projet", "devis"), ("Fast lookup CHnell", ("contentieux-arbitrage", "sentence arbitrale", "Schiedsspruch"))],
        "accent_outils": "du cabinet", "gov": "outil de traduction en ligne", "cta": "Voyez Corrext",
    },
    "banques-finance": {
        "outils": [("Gestion de projet", "devis"), ("Fast lookup CHnell", ("banque-finance", "secret bancaire", "Bankgeheimnis")), ("Traduction texte et document", "lot")],
        "accent_outils": "de l'établissement", "gov": "traduction automatique", "cta": "Voyez Corrext",
    },
    "directions-juridiques": {
        "outils": [("Gestion de projet", "devis"), ("Traduction texte et document", "lot"), ("Fast lookup CHnell", ("contrats", "clause pénale", "Konventionalstrafe"))],
        "accent_outils": "direction juridique", "gov": "les équipes", "cta": "Reprenez le",
    },
    "fiduciaires-conseil": {
        "outils": [("Extraits du registre", "extrait"), ("Traduction texte et document", "lot"), ("Gestion de projet", "devis")],
        "accent_outils": "de la fiduciaire", "gov": "niveau de certification", "cta": "Voyez Corrext",
        "commander": "Extraits du registre",  # lien « Commander un extrait » vers auszug-hr.ch (audit CRO du 2026-10-23)
        "securite": ("restent en Suisse", "Confidentialité client"),
    },
    "autorites-administration": {
        "outils": [("Gestion de projet", "devis"), ("Fast lookup CHnell", ("droit-penal", "ministère public", "Staatsanwaltschaft")), ("Extraits certifiés", "extrait")],
        "accent_outils": "de l'administration", "gov": "traduction en ligne", "cta": "Voyez Corrext",
    },
    "editeurs-legaltech": {
        "outils": [("LexMachina", "lexmachina"), ("Fast lookup CHnell", ("contrats", "clause pénale", "Konventionalstrafe")), ("API et on-premises", "api")],
        "accent_outils": "vous intégrez", "gov": "moteur généraliste", "cta": "Cadrons",
        "securite": ("rester en Suisse", "Traitement en Suisse"),
        # onglet de l'intégration par API (Fabien, 2026-10-20) : le texte du fait « API REST » de la V1 de la page
        "textes": {"API et on-premises": "API REST"},
    },
}

DEPLOIEMENT = [  # libellés et sous-titres du méga-menu
    ("Essayez sans inscription", "L'interface de Corrext, reproduite à l'identique sur trois extraits de droit suisse.", "Ouvrir la démo en direct", DEMO),
    ("Centre d'aide", texte("metier.deploiement.aide"), "Voir la page", "{{ROOT}}fr/aide/"),
    ("API et on-premises", "Intégration à vos DMS, intranets et workflows", "Voir la page", "{{ROOT}}fr/corrext/api-on-premises/"),
]


def composer(slug, cfg, E):
    P = f"solutions/{slug}/"
    t = liens(charger(P), P)
    th = bloc(t, "section", "thero")
    h1 = bloc(th, "h1")
    hero_ = trame.boutons_secteur(hero(txt(bloc(h1, "em")), txt(re.sub(r"<em>.*?</em>", "", h1, flags=re.S)), brut(bloc(th, "p", "lead")),
                                       ("Demander une démo", C)), slug, "hero")
    hero_ = lien_demo(hero_, DEMO)

    # Outils : textes et liens du bloc « outils les plus utilisés » de la V1 de la page
    v1 = {}
    for a in blocs(bloc(t, "section", "siblings"), "a", "jv-tool"):
        r = a.replace(bloc(a, "div", "jv-win"), "")
        v1[txt(bloc(r, "b"))] = (brut(bloc(r, "span")), re.search(r'href="([^"]+)"', a).group(1), txt(bloc(r, "em")))
    faits_ = {txt(bloc(f, "b")): brut(bloc(f, "p")) for f in blocs(bloc(t, "section", "facts"), "div", "fact")}
    items = []
    for nom, ecran in cfg["outils"]:
        texte_, href, lien_ = v1.get(nom) or HORS_V1[nom]
        if nom in cfg.get("textes", {}):
            texte_ = faits_[cfg["textes"][nom]]
        items.append((nom, texte_, href, chnell_(*ecran) if isinstance(ecran, tuple) else E[ecran], lien_))

    gov = gov_bento(t, cfg["gov"])
    if "securite" in cfg:  # gouvernance propre au métier à la place des niveaux, puis bloc sécurité construit
        accent, fait = cfg["securite"]
        milieu = [gov, securite(slug, accent, faits_[fait])]
    else:
        milieu = [niveaux(), gov]
    out = ([hero_, distinctions(), gains(slug), avis(slug), sans_avec(slug), outils(slug, items, cfg["accent_outils"], cfg.get("commander"))] + milieu
           + [deploiement(DEPLOIEMENT), faq_section(t), trame.appel(cta_section(t, cfg["cta"]), slug)])
    ecrire(P, entete_existant(P), "".join(out))
    print(f"{P} écrite")


if __name__ == "__main__":
    E = ecrans()
    for slug in sys.argv[1:] or METIERS:
        composer(slug, METIERS[slug], E)
