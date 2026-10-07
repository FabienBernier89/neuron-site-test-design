from commun import *
P = "securite-souverainete/"
t = liens(charger(P), P)
out = []
th = bloc(t, "section", "thero")
out.append(hero("Souveraineté des données.", "Où va votre document, exactement, et qui peut le lire", brut(bloc(th, "p", "lead")), ("Demander une démo", C)))
# Bento : le parcours d'un document
spec = bloc(th, "div", "law-spec")
rangs = {txt(bloc(r, "i")): txt(bloc(r, "b")) for r in blocs(spec, "div", "sr")}
petites = [(rangs[k], k, "") for k in ("Stockage", "Traitement", "Norme", "Cadre")]
out.append(section(bento({"titre": f'<h2 class="h3s">{txt(bloc(bloc(spec, "div", "sh"), "b"))}</h2>',
                          "texte": txt(bloc(spec, "div", "sf")),
                          "lien": ("Voir le tableau", "{{ROOT}}fr/securite-souverainete/#ou-va-mon-document")}, petites)))
# Où va votre document : scène S5 (avis réel), puis le tableau
cp = bloc(t, "section", "compare")
sq = bloc(t, "section", "svq")
carte = bloc(sq, "figure", "svq-card")
avis = f'<b>{txt(bloc(carte, "div", "h"))}</b><p lang="en">{brut(bloc(carte, "blockquote"))}</p>'
leg = "".join("<span>" + interne(x) + "</span>" for x in blocs(bloc(cp, "div", "cmp-legend"), "span")[::2])
out.append(section(h2(txt(bloc(cp, "h2")), "selon votre choix") + f'<p class="intro">{brut(bloc(cp, "p", "compare-note"))}</p>'
                   + scene(1176, 520, A.ecran_securite(*textes_demo()["notice"], esc(EX["co"]["src"]), esc(EX["co"]["out"]["en"]["main"])), sim="avis", curseur=False, titre="Corrext", label="Choix du moteur et avis Attorney-Client privilege")
                   + f'<p class="legende">{brut(bloc(carte, "figcaption"))}</p>'
                   + '<div class="tb tb-m">' + sans_svg(bloc(cp, "table")) + "</div>"
                   + f'<p class="legende cmp-leg">{leg}</p><p class="legende">{brut(bloc(cp, "p", "cmp-note"))}</p>', ident="ou-va-mon-document"))
# Politique au moment du choix : bande
out.append(section(bande(txt(bloc(sq, "h2")), ("Demander une démo", C))))
# Garanties : liste
sf = bloc(t, "section", "svfacts")
lead = bloc(sf, "div", "facts-lead")
items = "".join(f'<li><span><b>{txt(bloc(f, "b"))}</b> {brut(bloc(f, "p"))}</span></li>' for f in blocs(sf, "div", "fact"))
out.append(section(h2(txt(bloc(lead, "h2")), "précisément") + f'<p class="intro">{brut(bloc(lead, "p"))}</p>'
                   + f'<div class="duo seul"><div class="oui"><ul>{items}</ul></div></div>'))
wh = bloc(t, "section", "who")
out.append(section(h2(txt(bloc(wh, "h2")), "trois manières") + cartes([(brut(bloc(r, "h3")), brut(bloc(r, "p")), None, "") for r in blocs(wh, "article", "sc-row")])))
sb = bloc(t, "section", "siblings")
out.append(section(h2(txt(bloc(sb, "h2"))) + cartes([(brut(bloc(x, "b")), brut(bloc(x, "span")), (None, re.search(r'href="([^"]+)"', x).group(1)), "") for x in blocs(sb, "a")])))
out.append(faq_section(t))
out.append(cta_section(t, "Faites examiner ce document"))
ecrire(P, entete_existant(P), "".join(out))
print("sécurité écrite")
