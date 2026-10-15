"""Page Sécurité et souveraineté, sur le modèle des pages secteur (trame.py, décisions de Fabien du 2026-10-15).

Ordre : hero, problème (tr-pb), où va votre document, bande, garanties, trois régimes, pour aller plus loin, preuves
(tr-pv), FAQ, appel. Le bento « Le parcours d'un document » du hero de la V1 est retiré : ses quatre tuiles (stockage,
traitement, norme, cadre) sont les faits du bloc Preuves, qu'elles auraient répétés. Boutons suivis :
cta-securite-hero, cta-securite-milieu (bande), cta-securite-fin. Textes nouveaux : F-souverainete.json."""
from commun import *
import trame

P = "securite-souverainete/"
CLE = "securite-souverainete"
t = liens(charger(P), P)
out = []
th = bloc(t, "section", "thero")
out.append(trame.bouton_suivi(hero("Souveraineté des données.", "Où va votre document, exactement, et qui peut le lire",
                                   brut(bloc(th, "p", "lead")), ("Demander une démo", C)), "securite", "hero"))
# Le problème, juste après le hero
out.append(trame.probleme(CLE))
# Où va votre document : scène S5 (avis réel), puis le tableau
cp = bloc(t, "section", "compare")
sq = bloc(t, "section", "svq")
carte = bloc(sq, "figure", "svq-card")
avis = f'<b>{txt(bloc(carte, "div", "h"))}</b><p lang="en">{brut(bloc(carte, "blockquote"))}</p>'
out.append(section(h2(txt(bloc(cp, "h2")), "selon votre choix") + f'<p class="intro">{brut(bloc(cp, "p", "compare-note"))}</p>'
                   + scene(1176, 520, A.ecran_securite(*textes_demo()["notice"], esc(EX["co"]["src"]), esc(EX["co"]["out"]["en"]["main"])), sim="avis", curseur=False, titre="Corrext", label="Choix du moteur et avis Attorney-Client privilege")
                   + f'<p class="legende">{brut(bloc(carte, "figcaption"))}</p>'
                   # Tableau des trois modes : titre propre, à distance du bloc animé ; légende des pastilles et
                   # note sur l'interrupteur retirées (retour de Fabien du 2026-10-15)
                   + f'<h3 class="sv-tb-t" id="trois-modes">{trame.texte("securite.tableau.titre")}</h3>'
                   + '<div class="tb tb-m">' + sans_svg(bloc(cp, "table")).replace("<table", '<table aria-labelledby="trois-modes"', 1) + "</div>",
                   ident="ou-va-mon-document"))
# Politique au moment du choix : bande
out.append(trame.bouton_suivi(section(bande(txt(bloc(sq, "h2")), ("Demander une démo", C))), "securite", "milieu"))
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
# Preuves, juste avant la FAQ
out.append(trame.preuves(CLE, exemple=False))
out.append(faq_section(t))
out.append(trame.bouton_suivi(trame.appel(cta_section(t, "Faites examiner ce document")), "securite", "fin"))
ecrire(P, entete_existant(P), "".join(out))
print("sécurité écrite")
