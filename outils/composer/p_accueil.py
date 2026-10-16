"""Page d'accueil du test de design, composée de blocs extraits mot pour mot de docs/fr/index.html.

Ordre de la trame (lot D, spec V2 § 7) : hero et bandeau des distinctions, problème, sécurité et souveraineté (juste
après le problème, décision de Fabien du 2026-10-15), situation visée (plateforme, schéma « qui fait quoi » du lot B,
chiffres, agents, piliers, niveaux, comparaison), preuves, FAQ, appel.
Toutes les sections existantes sont gardées ; seul leur ordre change."""
import re
import html as H
from source import *
from comp import *
from app import app_corrext
from commun import fichiers_demo
import vues as V
import schema_produits
import trame


def app_ecran():
    """Écran Corrext de la scène, avec l'avis et l'encart d'aide tels qu'ils figurent dans la démo publiée."""
    cx = bloc(liens(charger("corrext/traduction-texte-et-document/"), "corrext/traduction-texte-et-document/"), "div", attr='id="cx"')
    av = bloc(cx, "div", "cx-notice")
    titre = txt(bloc(av, "b"))
    texte = brut(re.sub(r"<b>.*?</b>", "", interne(av), flags=re.S))
    hi = bloc(cx, "div", "cx-hint")
    ill = brut(interne(bloc(hi, "div", "ill")))
    return app_corrext(titre, texte, ill, txt(bloc(hi, "b")), brut(bloc(hi, "p")))

P = ""
t = liens(charger(P), P)
C = "{{ROOT}}contact/"
B = {}  # blocs existants, rangés dans l'ordre de la trame en fin de script

# 1. Hero C3 et scène S1 (vraie démo Corrext)
demo = bloc(t, "section", "demo")
zone = '<div class="cx-zone">' + bloc(demo, "div", "cx-ex") + bloc(demo, "div", attr='id="cx"') + "</div>"
micro = brut(bloc(bloc(t, "section", "final-cta"), "p", "micro"))
B["hero"] = ('<section class="hero hero-a">\n<div class="wrap">\n'
           '<h1 class="h1"><span class="n">Votre solution de traduction par IA</span> <span class="s">pour le droit, la fiscalité et la finance</span></h1>\n'
           f'<p class="hero-bl">{trame.texte("accueil.baseline")}</p>\n'
           f'<div class="hero-act"><a class="btn" href="{C}" data-suivi="cta-accueil-hero">Demander une démo</a><p class="note">{micro}</p></div>\n</div>\n'
           '<div class="wrap hero-st">' + scene(1176, 680, app_ecran(), sim="app", curseur=False, label="Démonstration de l'interface Corrext").replace('data-sim="app"', 'data-sim="app" data-tenue="0" data-interactif data-une-fois', 1).replace('<span class="sim-jauge"', f'<p class="sim-main" hidden>{trame.texte("accueil.demo.libre")}</p><span class="sim-jauge"', 1) + "</div>\n</section>\n")

# 2. Distinctions (bandeau défilant du hero source)
hl = [txt(x) for x in blocs(bloc(t, "div", "hero-logos"), "span", "hl") if "aria-hidden" not in x[:60]]
items = [(x.split(" · ", 1)[0], x.split(" · ", 1)[1] if " · " in x else "") for x in hl]
B["distinctions"] = dist(txt(bloc(bloc(t, "section", "trust"), "h2")), items)

# 3. Chiffres
stats = []
for s in blocs(bloc(t, "section", "stats"), "div", "stat"):
    stats.append((txt(bloc(s, "div", "num")).replace(" M+", " M+"), None, brut(bloc(s, "div", "desc"))))
# Retour de Fabien du 2026-10-16 : aucun chiffre seul en titre (unité accolée), et la tuile « 1 · Mode Highly sensitive »
# devient « 20 000+ documents » (CHnell). Textes : H-accueil.json.
def _u(n, cle):
    return f'{n} <span class="u">{H.escape(trame.texte(f"accueil.chiffres.{cle}.unite"), quote=False)}</span>'
stats = [(_u(stats[0][0], "segments"), None, H.escape(trame.texte("accueil.chiffres.segments.texte"), quote=False)),
         (_u("30", "langues"), None, H.escape(trame.texte("accueil.chiffres.langues.texte"), quote=False)),
         (_u("4", "moteurs"), None, H.escape(trame.texte("accueil.chiffres.moteurs.texte"), quote=False)),
         (_u(trame.texte("accueil.chiffres.documents.chiffre"), "documents"), None, H.escape(trame.texte("accueil.chiffres.documents.texte"), quote=False))]
B["chiffres"] = section(tuiles(stats, "tl t4"))

# 4. Plateforme : une ligne C7 par produit, visuel = maquette du site actuel
pr = bloc(t, "section", "products")
tete = bloc(pr, "div", "sec-head")
lignes = []
for i, f in enumerate(blocs(pr, "div", "feature")):
    h3 = bloc(f, "h3")
    pill = txt(bloc(h3, "span", "pn")).rstrip(".")
    titre = brut(re.sub(r'<span class="pn">.*?</span>', "", h3, flags=re.S))
    texte = brut(bloc(bloc(f, "div", "feat-txt"), "p"))
    liste = [brut(li) for li in blocs(f, "li")]
    a = bloc(f, "a", "feat-link")
    lien = (txt(a), re.search(r'href="([^"]+)"', a).group(1))
    maq = '<div class="maq">' + bloc(f, "div", "win") + "</div>"
    vis = (scene(764, 444, V.vue_fichiers(fichiers_demo("fichier", "pdf")), sim="lot", curseur=False, label=pill)
           if "doc-body" in maq else scene(764, 515, maq, label=pill))
    lignes.append(ft(pill, titre, texte, vis, lien, inv=i % 2 == 1, liste=liste))
B["plateforme"] = (section(h2(txt(bloc(tete, "h2")), "seule plateforme") + f'<p class="intro">{brut(bloc(tete, "p"))}</p>' + "".join(lignes)))

# 5. Agents : bento, chiffres d'économies dans les petites tuiles
ag = bloc(t, "section", "agents")
tete = bloc(ag, "div", "sec-head")
petites = []
for i, s in enumerate(blocs(ag, "div", "astep")):
    pct = txt(bloc(s, "span", "pct")).replace("%", " %")
    petites.append((f'<span class="n">{pct}</span><b>{brut(bloc(s, "h3"))}</b>', brut(bloc(s, "span", "sl")), "bt-l" if i == 2 else ""))
B["agents"] = (section(bento({"titre": h2(txt(bloc(tete, "h2")), "du devis à la livraison", "h3s"), "texte": brut(bloc(tete, "p"))}, petites)
                   + f'<p class="legende">{brut(bloc(ag, "p", "agents-note"))}</p>'))

# 6. Piliers
pi = bloc(t, "section", "pillars")
tete = bloc(pi, "div", "sec-head")
B["piliers"] = (section(h2(txt(bloc(tete, "h2")), "le connaître") + f'<p class="intro">{brut(bloc(tete, "p"))}</p>'
                   + tuiles([(None, brut(bloc(x, "h3")), brut(bloc(x, "p"))) for x in blocs(pi, "div", "pillar")], "tl txt")))

# 7. Quatre niveaux
lv = bloc(t, "section", "levels")
tete = bloc(lv, "div", "sec-head")
niv = [(str(i + 1), brut(bloc(x, "h3")), brut(bloc(x, "p"))) for i, x in enumerate(blocs(lv, "div", "lev"))]
B["niveaux"] = (section(h2(txt(bloc(tete, "h2")), "Quatre niveaux") + f'<p class="intro">{brut(bloc(tete, "p"))}</p>' + tuiles(niv, "tl t4")))

# 8. Comparaison
cp = bloc(t, "section", "compare")
B["comparaison"] = (section(h2(txt(bloc(cp, "h2")), "maîtrise le droit suisse") + f'<p class="intro">{brut(bloc(cp, "p", "compare-note"))}</p>'
                   + '<div class="tb">' + sans_svg(bloc(cp, "table")) + "</div>"
                   + '<p class="legende cmp-leg">' + "".join("<span>" + interne(x) + "</span>" for x in blocs(bloc(cp, "div", "cmp-legend"), "span")[::2]) + "</p>"))

# 9. Sécurité : bento, quatre preuves
se = bloc(t, "section", "security")
tete = bloc(se, "div", "security-head")
items = [(brut(bloc(x, "h3")), brut(bloc(x, "p")), "") for x in blocs(se, "div", "sec-item")[:4]]
B["securite"] = (section(bento({"pill": "Sécurité et souveraineté", "titre": h2(txt(bloc(tete, "h2")), "restent en Suisse", "h3s"),
                          "texte": brut(bloc(tete, "p")), "lien": ("Sécurité et souveraineté", "{{ROOT}}fr/securite-souverainete/")}, items)))

# 10. FAQ
fq = bloc(t, "section", "faq")
qr = [(brut(bloc(d, "summary")), "".join(f"<p>{brut(p)}</p>" for p in blocs(d, "p"))) for d in blocs(fq, "details")]
B["faq"] = faq(txt(bloc(fq, "h2")), qr)

# 11. Appel final
B["appel"] = trame.appel(cta("Prêt à voir Neur.on", "sur vos propres documents ?", ("Demander une démo", C))
                         .replace('<a class="btn"', '<a class="btn" data-suivi="cta-accueil-fin"', 1))

# 12. Trame : hero, problème, souveraineté, situation visée, preuves, FAQ, appel (le schéma suit le bloc qui présente
# la plateforme ; la souveraineté, argument majeur, suit directement le problème : décision de Fabien du 2026-10-15)
out = [B["hero"], B["distinctions"], trame.probleme("accueil"), B["securite"],
       B["plateforme"], schema_produits.rendre(), B["chiffres"], B["agents"], B["piliers"], B["niveaux"], B["comparaison"],
       trame.preuves("accueil", bandeau=B["distinctions"], exemple=False), B["faq"], B["appel"]]
assert len(out) == len(B) + 3, "un bloc existant manque à la trame"

ecrire(P, entete_existant(P), "".join(out))
print("accueil écrite :", sum(len(x) for x in out), "caractères")
