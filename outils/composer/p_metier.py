"""Page métier Cabinets d'avocats, sur le modèle choisi par Fabien le 2026-10-19 (outils/composer/metier_modele.py) :
la page ne raconte plus des cas pas à pas, elle présente les gains, un avis, le face à face sans / avec Corrext, les
outils du cabinet, les niveaux de relecture, la sécurité et le déploiement. Les boutons « Demander une démo » mènent
au formulaire avec le secteur prérempli (lot C)."""
from metier_modele import *
import trame

P = "solutions/cabinets-avocats/"
SLUG = P.split("/")[1]
t = liens(charger(P), P)
th = bloc(t, "section", "thero")
hero_ = trame.boutons_secteur(hero("Cabinets d'avocats.", "Traduire un dossier sans jamais le sortir de Suisse", brut(bloc(th, "p", "lead")), ("Demander une démo", C)), SLUG, "hero")
hero_ = lien_demo(hero_, "{{ROOT}}fr/corrext/traduction-texte-et-document/#demo")

# Outils : les trois outils de la V1 (« Les outils les plus utilisés par les avocats »), chacun avec son écran animé
sb = bloc(t, "section", "siblings")
v1 = {txt(bloc(a.replace(bloc(a, "div", "jv-win"), ""), "b")): (brut(bloc(a.replace(bloc(a, "div", "jv-win"), ""), "span")), re.search(r'href="([^"]+)"', a).group(1))
      for a in blocs(sb, "a", "jv-tool")}
ECRANS = {  # même taille pour les trois écrans (Fabien, 2026-10-19)
    "Traduction texte et document": scene(764, 500, V.vue_fichiers(fichiers_demo("pdf", "fichier")), sim="lot", curseur=False, label="Traduction d'un lot de fichiers"),
    "Gestion de projet": scene(764, 500, V.vue_devis("Darlehensvertrag_2026.docx", "DE → FR", NIVEAUX_RELECTURE, NIVEAUX_RELECTURE[1]), sim="devis", curseur=False,
                               label="Devis avec relecture complète par un traducteur juridique"),
    "Fast lookup CHnell": scene(764, 500, V.vue_chnell(lookup("contentieux-arbitrage", "sentence arbitrale", "French", "German", "Schiedsspruch")), sim="chnell",
                                curseur=False, titre="CHnell", label="Fast lookup CHnell"),
}
assert set(ECRANS) == set(v1), f"outils de la V1 : {set(v1)}"
items = [(nom, v1[nom][0], v1[nom][1], ECRANS[nom]) for nom in ECRANS]

DEPLOIEMENT = [  # libellés et sous-titres du méga-menu
    ("Essayez sans inscription", "L'interface de Corrext, reproduite à l'identique sur trois extraits de droit suisse.", "Ouvrir la démo en direct", "{{ROOT}}fr/corrext/traduction-texte-et-document/#demo"),
    ("Centre d'aide", texte("metier.deploiement.aide"), "Voir la page", "{{ROOT}}fr/aide/"),
    ("API et on-premises", "Intégration à vos DMS, intranets et workflows", "Voir la page", "{{ROOT}}fr/corrext/api-on-premises/"),
]

out = [hero_, distinctions(), gains(SLUG), avis(SLUG), sans_avec(SLUG), outils(SLUG, items, "du cabinet"), niveaux(),
       gov_bento(t, "outil de traduction en ligne"), deploiement(DEPLOIEMENT), faq_section(t),
       trame.appel(cta_section(t, "Voyez Corrext"), SLUG)]
ecrire(P, entete_existant(P), "".join(out))
print("métier écrit")
