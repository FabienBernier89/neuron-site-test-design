from blocs_communs import *
P = "traduction/contrats/"
t = liens(charger(P), P)
out = []
th = bloc(t, "section", "thero")
out.append(hero("Contrats.", "Le Code des obligations, d'une langue à l'autre", brut(bloc(th, "p", "lead")), ("Demander une démo", C)))
T = textes_demo()
out.append(section(scene(1176, 452, V.vue_fichiers(fichiers_demo("fichier"), depot=T["fichier"]), sim="lot", curseur=False, label="Traduction d'un contrat dans son format d'origine"), "sec sec-st"))
out.append(termes(t, "dans les quatre langues"))
out.append(faits(t, "concrètement"))
tl = bloc(t, "section", "tlaws")
lead = bloc(tl, "div", "tlaws-lead")
cs = [(txt(bloc(x, "b")), brut(bloc(x, "p")), None, f'<span class="kv kv-ab"><b>{txt(bloc(x, "span", "ab"))}</b></span>') for x in blocs(tl, "div", "tlaw")]
out.append(section(h2(txt(bloc(lead, "h2")), "tous les jours") + f'<p class="intro">{brut(bloc(lead, "p"))}</p>' + cartes(cs).replace('class="cd"', 'class="cd c4"', 1)))
out.append(situations_cartes(t, "se complique"))
out.append(faq_section(t))
out.append(voisins(t))
out.append(cta_section(t, "Voyez Corrext"))
ecrire(P, entete_existant(P), "".join(out))
print("contrats écrit")
