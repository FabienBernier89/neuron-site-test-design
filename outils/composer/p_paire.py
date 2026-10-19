"""Page de paire Allemand vers français, sur le modèle des paires (outils/composer/paire_modele.py, validé par Fabien
le 2026-10-19)."""
from paire_modele import *

P = "traduction/allemand-francais/"
CFG = {
    "source": "Allemand", "cible": "Français",
    "lookup": EX["co"]["lookup"],  # Verzugszins, allemand vers français (démo CHnell publiée)
    "principe": "Trois versions, même valeur",
    # ce qui se convertit : fait de la V1 et son exemple, pris dans le texte du fait
    "conversions": [("Abréviations à convertir", ("OR", "CO")), ("Jurisprudence fédérale", ("BGE", "ATF")),
                    ("Orthographe suisse", ("ß", "ss")), ("Chiffres et montants", (None, "15'000"))],
    "garanties": [("Moteur entraîné sur le droit suisse", "moteur"), ("Confidentialité", "cadenas"), ("Composés allemands", "mise")],
}
t = liens(charger(P), P)
th = bloc(t, "section", "thero")
out = [hero("Allemand vers français.", "Le droit suisse d'une rive à l'autre", brut(bloc(th, "p", "lead")), ("Demander une démo", C)),
       chnell(P, CFG),
       equivalences(t, CFG, "dans les quatre langues"),
       pratique(t, CFG, "en pratique"),
       situations(t, "décide de la journée"),
       faq_section(t),
       autres_paires(t),
       cta_section(t, "Essayez cette paire")]
ecrire(P, entete_existant(P), "".join(out))
print("paire écrite")
