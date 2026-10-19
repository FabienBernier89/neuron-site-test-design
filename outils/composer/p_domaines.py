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
    # Déroulé sur les autres domaines le 2026-10-19 : à gauche les documents propres au domaine, à droite les apports
    # transverses de Corrext (confidentialité, terminologie, formats, moteurs). Recherches CHnell filtrées sur fedlex.
    "assurance": {
        "chnell": ("preneur d'assurance", "French", "German", "Versicherungsnehmer"),
        "actes": ["Conditions générales", "Police et avenants", "Déclaration de sinistre", "Rapports d'expertise", "Correspondance de règlement"],
        "concret": "assurance, concrètement", "situations": "une traduction", "cta": "Vos dossiers d'assurance,",
    },
    "banque-finance": {
        "chnell": ("secret bancaire", "French", "German", "Bankgeheimnis"),
        "actes": ["Contrat de crédit", "Conditions générales", "Documentation de fonds", "Communications aux clients"],
        "concret": "bancaires, concrètement", "situations": "passage obligé", "cta": "Vos documents bancaires,",
    },
    "compliance-finma": {
        "chnell": ("intermédiaire financier", "French", "German", "Finanzintermediär"),
        "actes": ["Directives internes", "Dossiers de diligence", "Rapports à l'autorité", "Procédures écrites"],
        "concret": "conformité, concrètement", "situations": "la traduction", "cta": "Votre documentation de conformité,",
    },
    "contentieux-arbitrage": {
        "chnell": ("sentence arbitrale", "French", "German", "Schiedsspruch"),
        "actes": ["Bordereau de pièces", "Mémoire et conclusions", "Sentence arbitrale", "Exécution en Suisse"],
        "concret": "procédure, concrètement", "situations": "traduction pèse", "cta": "Voyez Corrext sur",
    },
    "contrats": {
        "chnell": ("clause pénale", "French", "German", "Konventionalstrafe"),
        "actes": ["Bail et annexes", "Conditions générales", "Contrat cadre et avenants", "Clauses chiffrées"],
        "concret": "contrat, concrètement", "situations": "se complique", "cta": "Voyez Corrext",
    },
    "droit-du-travail": {
        "chnell": ("résiliation immédiate", "French", "German", ["Fristlose Auflösung", "fristlosen Kündigung"]),
        "actes": ["Règlement d'entreprise", "Lettre de résiliation", "Clause de non-concurrence", "Collaborateurs étrangers"],
        "concret": "RH, concrètement", "situations": "plusieurs langues", "cta": "Vos documents RH,",
    },
    "droit-penal": {
        "chnell": ("ministère public", "French", "German", "Staatsanwaltschaft"),
        "actes": ["Dossier d'instruction", "Procès-verbaux d'audition", "Ordonnance pénale", "Acte d'accusation", "Entraide internationale"],
        "concret": "pénale, concrètement", "situations": "une traduction", "cta": "Vos dossiers pénaux,",
    },
    "fiscalite": {
        "chnell": ("impôt anticipé", "French", "German", "Verrechnungssteuer"),
        "actes": ["Décision de taxation", "Réclamation et recours", "Contexte international"],
        "concret": "fiscal, concrètement", "situations": "est décisive", "cta": "Vos dossiers fiscaux,",
    },
    "fusions-acquisitions": {
        "chnell": ("contrat de fusion", "French", "German", "Fusionsvertrag"),
        "actes": ["Data room", "Rapport de due diligence", "Contrat de fusion", "Décisions sociales", "Notification à la concurrence"],
        "concret": "transaction, concrètement", "situations": "se gagne", "cta": "Testez Corrext sur",
    },
    "propriete-intellectuelle": {
        "chnell": ("indication de provenance", "French", "German", "Herkunftsangabe"),
        "actes": ["Demande de brevet", "Dépôt de marque", "Contrat de licence", "Opposition et action"],
        "concret": "marque, concrètement", "situations": "du droit", "cta": "Vos dépôts et vos contrats de licence,",
    },
    "rapports-annuels-financiers": {
        "chnell": ("comptes annuels", "French", "German", "Jahresrechnung"),
        "actes": ["Rapport de gestion", "Comptes annuels", "Rapport de révision", "Annexe et notes"],
        "concret": "annuel, concrètement", "situations": "de clôture", "cta": "Préparez votre",
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
           concretement(t, cfg["actes"], cfg["concret"], slug),
           situations(t, cfg["situations"]),
           faq_section(t),
           voisins(t),
           cta_section(t, cfg["cta"])]
    ecrire(P, entete_existant(P), "".join(out))
    print(f"{P} écrite")


if __name__ == "__main__":
    for slug in sys.argv[1:] or DOMAINES:
        composer(slug, DOMAINES[slug])
