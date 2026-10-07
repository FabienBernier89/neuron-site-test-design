from commun import *
P = "corrext/traduction-texte-et-document/"
t = liens(charger(P), P)
out = []
th = bloc(t, "section", "thero")
out.append(hero("Traduction texte et document.", "Traduisez, comparez et reformulez", brut(bloc(th, "p", "lead")), ("Demander une démo", C)))
td = bloc(t, "section", "tdemo")
zone = '<div class="cx-zone">' + bloc(td, "div", "cx-ex") + bloc(td, "div", attr='id="cx"') + "</div>"
T = textes_demo()
ecran = A.ecran_outil(*T["notice"], *T["hint"], T["fichier"], T["pdf"], T["reph"])
out.append(section(scene(1176, 680, ecran, sim="outil", curseur=False, label="Démonstration de Traduction texte et document").replace('data-sim="outil"', 'data-sim="outil" data-tenue="0"', 1), "sec sec-st", "demo"))
fa = bloc(t, "section", "facts")
lead = bloc(fa, "div", "facts-lead")
faits = {txt(bloc(f, "b")): brut(bloc(f, "p")) for f in blocs(fa, "div", "fact")}
SC = [("Text translation", "traduire", A.fragment_travail(), "Corrext"),
      ("Moteurs", "sensible", A.fragment_moteurs(esc(EX["co"]["src"]), esc(EX["co"]["out"]["en"]["main"])), "Corrext"),
      ("Alternatives", "moteurs", A.fragment_travail(esc(EX["ldip"]["src"]), esc(EX["ldip"]["out"]["en"]["main"])), "Corrext"),
      ("Langues", "langues", A.fragment_travail(esc(EX["lb"]["src"]), esc(EX["lb"]["out"]["en"]["main"])), "Corrext")]
lignes = []
for i, (cle, sim, ui, titre) in enumerate(SC):
    lignes.append(ft(None, cle, faits.pop(cle), scene(764, 400, ui, sim=sim, titre=titre, curseur=False, label=cle), inv=i % 2 == 1))
liens_lead = "".join(f'<a class="lien" href="{re.search(r"href=\"([^\"]+)\"", a).group(1)}">{txt(a)}</a> ' for a in blocs(lead, "a", "feat-link"))
out.append(section(h2(txt(bloc(lead, "h2")), "exactement") + f'<p class="intro">{brut(bloc(lead, "p"))}</p>' + "".join(lignes)))
out.append(section(tuiles([(None, k, v) for k, v in faits.items()], "tl txt t2")))
wh = bloc(t, "section", "who")
out.append(section(h2(txt(bloc(wh, "h2")), "change la journée") + cartes([(brut(bloc(r, "h3")), brut(bloc(r, "p")), None, "") for r in blocs(wh, "article", "sc-row")])))
gv = bloc(t, "section", "gov")
box = bloc(gv, "div", "gov-box")
a = blocs(box, "a", "feat-link")[0]
pas = []
for i, s in enumerate(blocs(bloc(gv, "div", "gov-steps"), "span")):
    if 'class=' in s[:20]:
        continue
    b = brut(bloc(s, "b")); reste = brut(re.sub(r"<b>.*?</b>", "", interne(s), flags=re.S))
    pas.append((b, reste, ""))
pas[-1] = (pas[-1][0], pas[-1][1], "bt-l")
out.append(section(bento({"titre": h2(txt(bloc(box, "h2")), "hébergé à l'étranger", "h3s"), "texte": brut(bloc(box, "p")),
                          "lien": (txt(a), re.search(r'href="([^"]+)"', a).group(1))}, pas)))
sb = bloc(t, "section", "siblings")
cs = [(brut(bloc(x, "b")), brut(bloc(x, "span")), (None, re.search(r'href="([^"]+)"', x).group(1)), "") for x in blocs(sb, "a")]
out.append(section(h2(txt(bloc(sb, "h2")), "outils de Corrext") + cartes(cs)))
out.append(faq_section(t))
out.append(cta_section(t, "Voyez Traduction texte et document"))
ecrire(P, entete_existant(P), "".join(out))
print("outil écrit")
