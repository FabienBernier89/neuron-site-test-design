"""Page secteur Cabinets d'avocats, composée de blocs extraits mot pour mot de la page publiée.

Ordre de la trame (lot D, spec V2 § 7) : hero et bandeau des distinctions, problème, situation visée (trois moments,
« Ce que Corrext change », outils, question de gouvernance), preuves, exemple de cas d'usage, FAQ, appel. Les boutons
« Demander une démo » mènent au formulaire avec le secteur prérempli (lot C)."""
from blocs_communs import *
import trame
P = "solutions/cabinets-avocats/"
SLUG = P.split("/")[1]
t = liens(charger(P), P)
B = {}  # blocs existants, rangés dans l'ordre de la trame en fin de script
th = bloc(t, "section", "thero")
B["hero"] = trame.boutons_secteur(hero("Cabinets d'avocats.", "Traduire un dossier sans jamais le sortir de Suisse", brut(bloc(th, "p", "lead")), ("Demander une démo", C)), SLUG, "hero")
B["distinctions"] = distinctions()
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
B["moments"] = section(h2(txt(bloc(wh, "h2")), "gagne des heures") + "".join(lignes))
B["gouvernance"] = gov_bento(t, "outil de traduction en ligne")
B["visee"] = faits(t, "dans un cabinet")
sb = bloc(t, "section", "siblings")
cs = []
for a in blocs(sb, "a", "jv-tool"):
    win = bloc(a, "div", "jv-win")
    titre_fen = txt(bloc(bloc(win, "div", "jv-bar"), "b"))
    reste = a.replace(win, "")
    cs.append((brut(bloc(reste, "b")), brut(bloc(reste, "span")), (txt(bloc(reste, "em")), re.search(r'href="([^"]+)"', a).group(1)),
               scene(355, 199, V.vignette(win), titre=titre_fen, label=titre_fen)))
B["outils"] = section(h2(txt(bloc(sb, "h2")), "les plus utilisés") + cartes(cs))
tm = bloc(t, "section", "temo")
lk = EX["co"]["lookup"]
r0 = lk["rows"][0]
vis = f'<div class="qt-v" data-ui><small><span>{esc(lk["q"])}</span> · <span>{esc(lk["l1"])}</span> · <span>{esc(lk["l2"])}</span></small><p>{esc(r0["a"])}</p><p class="qt-tr">{esc(r0["b"])}</p></div>'
B["exemple"] = (f'<section class="sec temo temo-ex"><div class="wrap"><figure class="qt">{vis}<div><blockquote>{interne(bloc(tm, "blockquote")).strip()}</blockquote>'
           f'<figcaption><span class="temo-lab">Exemple de cas d\'usage</span></figcaption></div></figure></div></section>\n')
B["faq"] = faq_section(t)
B["appel"] = trame.appel(cta_section(t, "Voyez Corrext"), SLUG)

# Trame : hero, problème, situation visée, preuves, exemple de cas d'usage, FAQ, appel
out = [B["hero"], B["distinctions"], trame.probleme(SLUG), B["moments"], B["visee"], B["outils"], B["gouvernance"],
       trame.preuves(SLUG, bandeau=B["distinctions"], exemple=True), B["exemple"], B["faq"], B["appel"]]
assert len(out) == len(B) + 2, "un bloc existant manque à la trame"
ecrire(P, entete_existant(P), "".join(out))
print("métier écrit")
