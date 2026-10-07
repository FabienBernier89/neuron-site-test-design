from commun import *
P = "corrext/"
t = liens(charger(P), P)
out = []
ph = bloc(t, "section", "phero")
out.append(hero("Corrext :", "reprenez le contrôle de vos traductions", brut(bloc(ph, "p", "lead")), ("Demander une démo", C)))
dash = bloc(ph, "div", "dash")
tl = [txt(b) for b in blocs(dash, "button", "dtab")]
pans = [interne(p) for p in blocs(dash, "div", "dpanel")]
kp = interne(bloc(dash, "div", "kpis"))
ecran = A.tableau_bord(tl, pans, txt(bloc(dash, "span", "ddata")), kp)
out.append(section(scene(1176, 640, ecran, sim="tableau", curseur=False, label="Tableau de bord de Corrext, données de démonstration"), "sec sec-st"))
pt = bloc(t, "section", "ptrust")
items = []
for li in blocs(pt, "li"):
    tt = bloc(li, "span", "ptrust-t")
    items.append((None, brut(bloc(tt, "b")), brut(interne(blocs(tt, "span")[1]))))
out.append(section(tuiles(items, "tl txt")))
po = bloc(t, "section", "postes")
h, p = tete(po)
co = EX["co"]
et, nivs, soc, ide = textes_extrait()
VIS = [(V.vue_alternatives("co", esc(co["src"]), esc(co["out"]["en"]["main"]), esc(co["out"]["en"]["alt"][0]["t"]), co["out"]["en"]["alt"][0]["e"], len(co["out"]["en"]["alt"]), tabs=True), "alts", 556),
       (V.vue_analyse("Contrat_assurance.docx", "2,5", "pages standard", "Français", "Assurance privée"), "analyse", 440),
       (V.vue_chnell(co["lookup"]), None, 470),
       (V.vue_extrait(et, nivs, soc, ide, "German", 2, ("Company", "Target language", "Certification level")), "extrait", 540)]
out.append(section(h2(h, "une seule salle de contrôle") + f'<p class="intro">{p}</p>' + lignes_features(po, visuels=VIS)))
us = bloc(t, "section", "usp")
lead = bloc(us, "div", "usp-lead")
a = blocs(lead, "a", "feat-link")[0]
petites = [(brut(bloc(r, "b")), brut(bloc(r, "p")), "") for r in blocs(us, "div", "usp-row")]
out.append(section(bento({"titre": h2(txt(bloc(lead, "h2")), "agnostique et pérenne", "h3s"), "texte": brut(bloc(lead, "p")),
                          "lien": (txt(a), re.search(r'href="([^"]+)"', a).group(1))}, petites)))
qb = bloc(t, "section", "qband")
out.append(section(bande(brut(bloc(qb, "b")), ("Demander une démo", C))))
out.append(faq_section(t))
out.append(cta_section(t, "Voyez Corrext"))
ecrire(P, entete_existant(P), "".join(out))
print("hub écrit")
