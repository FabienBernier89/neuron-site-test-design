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
# Garanties : mosaïque (choix de Fabien du 2026-10-15). Les deux garanties de souveraineté en tuiles larges,
# les huit autres en tuiles simples ; tons clairs, le thème sombre suit par les variables.
S = 'fill="none" stroke="currentColor" stroke-width="1.6" stroke-linecap="round" stroke-linejoin="round"'
ICONES = {
    "Entité suisse": '<path d="M4 21V8l8-5 8 5v13"/><path d="M9 21v-6h6v6"/>',
    "Infrastructure": '<rect x="3" y="4" width="18" height="7" rx="1.5"/><rect x="3" y="13" width="18" height="7" rx="1.5"/><path d="M7 7.5h.01M7 16.5h.01"/>',
    "ISO 27001": '<circle cx="12" cy="9" r="5"/><path d="M8.5 13 7 21l5-3 5 3-1.5-8"/>',
    "nLPD et RGPD": '<path d="M12 3 4 6v6c0 5 3.5 8 8 9 4.5-1 8-4 8-9V6z"/><path d="m9 12 2 2 4-4"/>',
    "Hors CLOUD Act": '<circle cx="12" cy="12" r="9"/><path d="M5.6 5.6l12.8 12.8"/>',
    "Aucun entraînement sur vos contenus": '<rect x="4" y="4" width="16" height="16" rx="3"/><path d="M9 9h6v6H9z"/><path d="M4 4l16 16"/>',
    "Mémoire privée": '<rect x="5" y="10" width="14" height="10" rx="2"/><path d="M8 10V7a4 4 0 0 1 8 0v3"/>',
    "Droits d'accès": '<circle cx="9" cy="8" r="3.5"/><path d="M3 20c0-3.3 2.7-6 6-6s6 2.7 6 6"/><path d="M16 4.5a3.5 3.5 0 0 1 0 7M21 20c0-2.6-1.6-4.8-4-5.6"/>',
    "On-premises": '<rect x="3" y="4" width="18" height="12" rx="2"/><path d="M8 20h8M12 16v4"/>',
    "API REST": '<path d="m8 8-4 4 4 4M16 8l4 4-4 4M14 5l-4 14"/>',
}
PHARES = ("Entité suisse", "Hors CLOUD Act")
sf = bloc(t, "section", "svfacts")
lead = bloc(sf, "div", "facts-lead")
faits = [(txt(bloc(f, "b")), brut(bloc(f, "p"))) for f in blocs(sf, "div", "fact")]
assert set(ICONES) == {titre for titre, _ in faits}, "garanties : un titre de la V1 a changé, mettre ICONES à jour"
faits.sort(key=lambda x: (x[0] not in PHARES, PHARES.index(x[0]) if x[0] in PHARES else 0))
tuiles = "".join(f'<li class="gr-c{" gr-l" if titre in PHARES else ""}"><span class="gr-i"><svg viewBox="0 0 24 24" {S} aria-hidden="true">{ICONES[titre]}</svg></span>'
                 f'<h3>{titre}</h3><p>{texte}</p></li>' for titre, texte in faits)
out.append(section(h2(txt(bloc(lead, "h2")), "précisément") + f'<p class="intro">{brut(bloc(lead, "p"))}</p>'
                   + f'<ul class="gr">{tuiles}</ul>', ident="garanties"))
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
