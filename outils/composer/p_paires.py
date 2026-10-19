"""Pages de paires de langues (hors Allemand vers français, composée par p_paire.py), sur le modèle validé par Fabien
le 2026-10-19 (outils/composer/paire_modele.py). Une configuration par page : sens de la paire, recherche CHnell
relevée pour la paire, principe, conversions avec leur exemple (pris dans le texte du fait de la V1), garanties.

    cd outils/composer && python3 p_paires.py
"""
from paire_modele import *

PAIRES = {
    "francais-allemand": {
        "source": "Français", "cible": "Allemand", "chnell": ("société anonyme", "French", "German", "Aktiengesellschaft"),
        "principe": "Le mot existe déjà",
        "conversions": [("Abréviations à convertir", ("CO", "OR")), ("Jamais de ß", ("ß", "ss")),
                        ("Montants et dates", (None, "15'000")), ("Faux amis romands", ("for", "Gerichtsstand"))],
        "garanties": [("Deux langues natives", "moteur"), ("Cohérence sur la durée", "moteur"), ("Composés à reconstruire", "mise")],
        "situations": "est attendue", "cta": "Faites relire",
    },
    "allemand-anglais": {
        "source": "Allemand", "cible": "Anglais", "chnell": ("Aktiengesellschaft", "German", "English", "company limited by shares"),
        "principe": "Pas de version qui fasse foi",
        "conversions": [("Sociétés", ("AG", "company limited by shares")), ("Notions sans équivalent", (None, "Betreibung")),
                        ("Le piège inverse", ("trust", None)), ("Références légales", (None, "art. 104 OR"))],
        "garanties": [("Finance et conformité", "moteur"), ("Volume des due diligences", "mise"), ("Confidentialité", "cadenas")],
        "situations": "par l'anglais", "cta": "Montrez-nous",
    },
    "anglais-allemand": {
        "source": "Anglais", "cible": "Allemand", "chnell": ("arbitral tribunal", "English", "German", "Schiedsgericht"),
        "principe": "Langue et droit applicable",
        "conversions": [("Clause pénale", ("liquidated damages", "Konventionalstrafe")), ("Clauses sans équivalent", ("best efforts", None)),
                        ("Arbitrage international", (None, "IPRG")), ("Orthographe et format", ("ß", "ss"))],
        "garanties": [("Définitions du contrat", "moteur"), ("Volume et annexes", "mise"), ("Confidentialité", "cadenas")],
        "situations": "en anglais", "cta": "Soumettez-nous",
    },
    "francais-anglais": {
        "source": "Français", "cible": "Anglais", "chnell": ("tribunal arbitral", "French", "English", "arbitral tribunal"),
        "principe": "Aucune version anglaise ne fait foi",
        "conversions": [("Le Tribunal fédéral", (None, "Federal Supreme Court")), ("Citer un arrêt", (None, "ATF")),
                        ("Notions sans équivalent", (None, "séquestre")), ("Arbitrage international", ("tribunal arbitral", "arbitral tribunal"))],
        "garanties": [("Finance et reporting", "moteur"), ("Volume d'un arbitrage", "mise"), ("Confidentialité", "cadenas")],
        "situations": "en anglais", "cta": "Testez la paire",
    },
    "italien-francais": {
        "source": "Italien", "cible": "Français", "chnell": ("ricorso", "Italian", "French", "recours"),
        "principe": "Une version qui fait foi",
        "conversions": [("Abréviations propres", ("LEF", "LP")), ("Jurisprudence", ("DTF", "ATF")),
                        ("Suisse ou Italie", (None, "precetto esecutivo")), ("Les institutions", (None, "Tribunale federale"))],
        "garanties": [("Langue native", "moteur"), ("Vérification en contexte", "moteur"), ("Documents cantonaux", "mise")],
        "situations": "du Tessin", "cta": "Faites vérifier",
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
           pratique(t, cfg, "en pratique"),
           situations(t, cfg["situations"]),
           faq_section(t),
           autres_paires(t),
           cta_section(t, cfg["cta"])]
    ecrire(P, entete_existant(P), "".join(out))
    print(f"{P} écrite")


if __name__ == "__main__":
    for slug, cfg in PAIRES.items():
        composer(slug, cfg)
