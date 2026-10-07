from blocs_communs import *
P = "solutions/cabinets-avocats/"
t = liens(charger(P), P)
out = []
th = bloc(t, "section", "thero")
out.append(hero("Cabinets d'avocats.", "Traduire un dossier sans jamais le sortir de Suisse", brut(bloc(th, "p", "lead")), ("Demander une démo", C)))
out.append(distinctions())
wh = bloc(t, "section", "who")
lignes = []
d = EX["ldip"]
VIS = [  # contentieux : lot de pièces ; transactions : devis et relecture complète ; arbitrage : alternatives par moteur
    (764, 444, V.vue_fichiers(fichiers_demo("pdf", "fichier")), "lot", "Traduction d'un lot de fichiers"),
    (764, 496, V.vue_devis("Darlehensvertrag_2026.docx", "DE → FR", NIVEAUX_RELECTURE, NIVEAUX_RELECTURE[1]), "devis", "Devis avec relecture complète par un traducteur juridique"),
    (764, 476, V.vue_alternatives("ldip", esc(d["src"]), esc(d["out"]["en"]["main"]), esc(d["out"]["en"]["alt"][0]["t"]), d["out"]["en"]["alt"][0]["e"], len(d["out"]["en"]["alt"])), "alts", "Alternatives attribuées à leur moteur"),
]
for i, (r, (w, h, ui, sim, lab)) in enumerate(zip(blocs(wh, "article", "sc-row"), VIS)):
    vis = scene(w, h, ui, sim=sim, curseur=False, label=lab)
    lignes.append(ft(txt(bloc(r, "span", "sc-a")), brut(bloc(r, "h3")), brut(bloc(r, "p")), vis, inv=i % 2 == 1))
out.append(section(h2(txt(bloc(wh, "h2")), "gagne des heures") + "".join(lignes)))
out.append(gov_bento(t, "outil de traduction en ligne"))
out.append(faits(t, "dans un cabinet"))
sb = bloc(t, "section", "siblings")
cs = []
for a in blocs(sb, "a", "jv-tool"):
    win = bloc(a, "div", "jv-win")
    titre_fen = txt(bloc(bloc(win, "div", "jv-bar"), "b"))
    reste = a.replace(win, "")
    cs.append((brut(bloc(reste, "b")), brut(bloc(reste, "span")), (txt(bloc(reste, "em")), re.search(r'href="([^"]+)"', a).group(1)),
               scene(355, 199, V.vignette(win), titre=titre_fen, label=titre_fen)))
out.append(section(h2(txt(bloc(sb, "h2")), "les plus utilisés") + cartes(cs)))
tm = bloc(t, "section", "temo")
lk = EX["co"]["lookup"]
r0 = lk["rows"][0]
vis = f'<div class="qt-v" data-ui><small><span>{esc(lk["q"])}</span> · <span>{esc(lk["l1"])}</span> · <span>{esc(lk["l2"])}</span></small><p>{esc(r0["a"])}</p><p class="qt-tr">{esc(r0["b"])}</p></div>'
out.append(f'<section class="sec temo temo-ex"><div class="wrap"><figure class="qt">{vis}<div><blockquote>{interne(bloc(tm, "blockquote")).strip()}</blockquote>'
           f'<figcaption><span class="temo-lab">Exemple de cas d\'usage</span></figcaption></div></figure></div></section>\n')
out.append(faq_section(t))
out.append(cta_section(t, "Voyez Corrext"))
ecrire(P, entete_existant(P), "".join(out))
print("métier écrit")
