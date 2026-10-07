from blocs_communs import *
P = "traduction/allemand-francais/"
t = liens(charger(P), P)
out = []
th = bloc(t, "section", "thero")
out.append(hero("Allemand vers français.", "Le droit suisse d'une rive à l'autre", brut(bloc(th, "p", "lead")), ("Demander une démo", C)))
out.append(scene_statique(ui_chnell(2), "CHnell", 470))
out.append(termes(t, "dans les quatre langues"))
out.append(faits(t, "en pratique"))
out.append(situations_cartes(t, "décide de la journée"))
out.append(faq_section(t))
out.append(voisins(t))
out.append(cta_section(t, "Essayez cette paire"))
ecrire(P, entete_existant(P), "".join(out))
print("paire écrite")
