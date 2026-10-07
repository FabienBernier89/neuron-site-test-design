from commun import *
P = "corrext/traduction-texte-et-document/"
t = liens(charger(P), P)
out = []
th = bloc(t, "section", "thero")
out.append(hero("Traduction texte et document.", "Traduisez, comparez et reformulez", brut(bloc(th, "p", "lead")), ("Demander une démo", C)))
td = bloc(t, "section", "tdemo")
zone = '<div class="cx-zone">' + bloc(td, "div", "cx-ex") + bloc(td, "div", attr='id="cx"') + "</div>"
out.append(section(scene(1176, 680, zone, sim="visite", label="Démonstration de Traduction texte et document"), "sec sec-st", "demo"))
fa = bloc(t, "section", "facts")
lead = bloc(fa, "div", "facts-lead")
faits = {txt(bloc(f, "b")): brut(bloc(f, "p")) for f in blocs(fa, "div", "fact")}
SC = [("Text translation", "traduire", ui_traduction([("LexMachina", "", True)]), "Corrext"),
      ("Moteurs", "sensible", ui_moteurs(), "Translation engine"),
      ("Alternatives", "moteurs", ui_traduction([("LexMachina", ' data-i="0"', True), ("DeepL Pro", ' data-i="1"', False), ("Azure OpenAI - GPT", ' data-i="2"', False)]), "Corrext"),
      ("Langues", "langues", ui_traduction([("English", ' data-l="en"', True), ("Italian", ' data-l="it"', False)], lg_src="French"), "Corrext")]
lignes = []
for i, (cle, sim, ui, titre) in enumerate(SC):
    lignes.append(ft(None, cle, faits.pop(cle), scene(764, 515, ui, sim=sim, titre=titre, label=cle), inv=i % 2 == 1))
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
