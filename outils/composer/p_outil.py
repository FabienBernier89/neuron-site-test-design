from outil_modele import *
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
# « Ce que fait… » : onglets compacts groupés, un écran animé de même taille par fonction, les faits chiffrables en
# tuiles (proposition A retenue par Fabien le 2026-10-20, outils/composer/outil_modele.py)
d = EX["ldip"]
def sc(ui, sim, label):
    return scene(764, 500, ui, sim=sim, titre="Corrext", curseur=False, label=label)
groupes = [
    (texte("outil.groupe.onglets"), [
        ("Text translation", faits["Text translation"], sc(A.fragment_travail(), "traduire", "Text translation")),
        ("File translation", faits["File translation"], sc(V.vue_fichiers(fichiers_demo("pdf", "fichier")), "lot", "File translation")),
        ("PDF to Word", faits["PDF to Word"], sc(V.vue_fichiers(fichiers_demo("pdf")), "lot", "PDF to Word")),
        ("Rephrasing", faits["Rephrasing"], sc(A.fragment_reph(T["reph"], EX["co"]["src"], EX["co"]["reph"]["def"], EX["co"]["reph"]["simp"], "Simplified"), "reph", "Rephrasing")),
    ]),
    (texte("outil.groupe.partout"), [
        ("Alternatives", faits["Alternatives"], sc(V.vue_alternatives("ldip", esc(d["src"]), esc(d["out"]["en"]["main"]), esc(d["out"]["en"]["alt"][0]["t"]),
                                                                       d["out"]["en"]["alt"][0]["e"], len(d["out"]["en"]["alt"])), "alts", "Alternatives")),
        ("Fast Lookup", faits["Fast Lookup"], sc(V.vue_chnell(EX["co"]["lookup"]), "chnell", "Fast Lookup")),
    ]),
]
k = lambda c: texte(f"traduction-texte-et-document.chiffre.{c}")
ch = chiffres([(k("langues"), faits["Langues"]), (k("moteurs"), faits["Moteurs"]), (k("suisse"), faits["Confidentialité"])])
assert {n for _, it in groupes for n, *_ in it} | {"Langues", "Moteurs", "Confidentialité"} == set(faits), "fait de la V1 non rangé"
out.append(section(h2(txt(bloc(lead, "h2")), "exactement") + f'<p class="intro">{brut(bloc(lead, "p"))}</p>' + onglets_groupes(groupes)
                   + f'<div class="ot-ch">{ch}</div>'))
wh = bloc(t, "section", "who")
out.append(section(h2(txt(bloc(wh, "h2")), "change la journée") + cartes([(brut(bloc(r, "h3")), brut(bloc(r, "p")), None, "") for r in blocs(wh, "article", "sc-row")])))
out.append(gov_rangees(t, "hébergé à l'étranger"))  # rangées au lieu du bento (audit des pages outils)
sb = bloc(t, "section", "siblings")
cs = [(brut(bloc(x, "b")), brut(bloc(x, "span")), (None, re.search(r'href="([^"]+)"', x).group(1)), "") for x in blocs(sb, "a")]
out.append(section(h2(txt(bloc(sb, "h2")), "outils de Corrext") + cartes(cs)))
out.append(faq_section(t))
out.append(cta_section(t, "Voyez Traduction texte et document"))
ecrire(P, entete_existant(P), "".join(out))
print("outil écrit")
