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
import app as A
from commun import fichiers_demo, EX
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
# Retours de Fabien du 2026-10-16 : titres sur une seule ligne (« 30 langues », « 4 moteurs »), « segments » passe dans le
# texte, et la 4e tuile devient « 100 % » suisse (le nombre de documents de CHnell était jugé trop faible). H-accueil.json.
def _u(n, cle):
    return f'{n} <span class="u">{H.escape(trame.texte(f"accueil.chiffres.{cle}.unite"), quote=False)}</span>'
stats = [(stats[0][0], None, H.escape(trame.texte("accueil.chiffres.segments.texte"), quote=False)),
         (_u("30", "langues"), None, H.escape(trame.texte("accueil.chiffres.langues.texte"), quote=False)),
         (_u("4", "moteurs"), None, H.escape(trame.texte("accueil.chiffres.moteurs.texte"), quote=False)),
         (H.escape(trame.texte("accueil.chiffres.suisse.chiffre"), quote=False), None, H.escape(trame.texte("accueil.chiffres.suisse.texte"), quote=False))]
B["chiffres"] = section(tuiles(stats, "tl t4 tl-haut"))  # petits textes alignés à la même hauteur

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

# 4 bis. Les trois axes (restructuration validée par Fabien le 2026-10-16) : LexMachina, Corrext, CHnell, en rangées au
# composant des fonctionnalités (visuel animé, texte, points forts, lien). Remplace la section plateforme et les piliers,
# dont le contenu est repris ici ; les fonctionnalités détaillées restent sur les pages outils.
def _a(cle):
    return H.escape(trame.texte(f"accueil.axes.{cle}"), quote=False)
co = EX["co"]
# Visuel LexMachina (retours de Fabien du 2026-10-16) : une seule traduction, sans alternatives, d'un texte financier
# anglais vers le français. Sortie RÉELLE de LexMachina relevée dans Corrext ; les termes surlignés sont ceux du droit
# suisse, vérifiés dans CHnell (impôt anticipé, Administration fédérale des contributions, droit de timbre d'émission,
# assujetti : art. 3 LFINMA). Source et notes : H-accueil.json.
TERMES_SUISSES = ("impôt anticipé", "Administration fédérale des contributions", "droit de timbre d’émission", "assujetti")
_sortie = H.escape(trame.texte("accueil.axes.lexmachina.demo.out"), quote=False)
for _t in TERMES_SUISSES:
    assert _t in _sortie, f"terme suisse absent de la sortie LexMachina : {_t}"
    _sortie = _sortie.replace(_t, f"<mark>{_t}</mark>", 1)
_ecran = ('<div class="cr cr-frag cr-q4 cr-q4-fr">' + A.travail(detecte=True, cible="French", src=_a("lexmachina.demo.src"), out="")
          .replace("Detected language (French)", _a("lexmachina.demo.langue"), 1)
          .replace('<p class="cr-out">', f'<p class="cr-out" data-html="{H.escape(_sortie)}">', 1) + "</div>")
AXES = [("lexmachina", "LexMachina", "{{ROOT}}lexmachina/",
         scene(764, 420, _ecran, sim="suisse", curseur=False, label="LexMachina traduit un texte fiscal suisse de l’anglais vers le français")),
        ("corrext", "Corrext", "{{ROOT}}corrext/",
         scene(764, 444, V.vue_fichiers(fichiers_demo("fichier", "pdf")), sim="lot", curseur=False, label="Corrext")),
        ("chnell", "CHnell", "{{ROOT}}corrext/chnell/",
         scene(764, 470, V.vue_chnell(co["lookup"]), curseur=False, label="CHnell"))]
axes = "".join(ft(pill, _a(f"{k}.titre"), _a(f"{k}.texte"), vis, (_a(f"{k}.lien"), lien), inv=i % 2 == 1,
                  liste=[_a(f"{k}.l{n}") for n in (1, 2, 3)]) for i, (k, pill, lien, vis) in enumerate(AXES))
B["axes"] = section(h2(_a("titre"), "un concordancier") + f'<p class="intro">{_a("intro")}</p>' + axes)

# 5. Usage de Corrext et de LexMachina (retour de Fabien du 2026-10-16) : Corrext n'a pas d'agents IA ; les chiffres
# d'économies du discours « agentique » sont remplacés par des chiffres d'usage publiés sur les pages produit
def _x(cle):
    return H.escape(trame.texte(f"accueil.usage.{cle}"), quote=False)
petites = [(f'<span class="n">{_x(k + ".chiffre")} <span class="u">{_x(k + ".unite")}</span></span><b>{_x(k + ".titre")}</b>', _x(k + ".texte"), "bt-l" if k == "alternatives" else "")
           for k in ("caracteres", "fichiers", "alternatives")]
# Ce que le juriste décide, et quand (retour de Fabien du 2026-10-16 : remplir le grand bloc sans redondance)
S = 'viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true"'
PICTOS = {"moteur": f'<svg {S}><rect x="5" y="5" width="14" height="14" rx="2"/><path d="M9 9h6v6H9zM9 2v3M15 2v3M9 19v3M15 19v3M2 9h3M2 15h3M19 9h3M19 15h3"/></svg>',
          "mode": f'<svg {S}><rect x="5" y="11" width="14" height="10" rx="2"/><path d="M8 11V7a4 4 0 0 1 8 0v4"/></svg>',
          "relecture": f'<svg {S}><path d="M4 20h4l10-10-4-4L4 16z"/><path d="m13 7 4 4"/></svg>',
          "terminologie": f'<svg {S}><path d="M4 19.5A2.5 2.5 0 0 1 6.5 17H20V3H6.5A2.5 2.5 0 0 0 4 5.5z"/><path d="M9 8h7M9 12h5"/></svg>'}
decide = (f'<div class="bt-dec"><p class="bt-dt">{_x("decide.titre")}</p><ul>'
          + "".join(f'<li><span class="bt-ic">{PICTOS[k]}</span><span><b>{_x(f"decide.{k}.titre")}</b> {_x(f"decide.{k}.texte")}</span></li>'
                    for k in ("moteur", "mode", "relecture", "terminologie")) + "</ul></div>")
grand = bento({"titre": h2(_x("titre"), "pilotée par vos juristes", "h3s"), "texte": _x("texte")}, petites).replace('<div class="bt">', '<div class="bt bt-us">', 1)
grand = grand.replace(f'<p>{_x("texte")}</p></div>', f'<p>{_x("texte")}</p>{decide}</div>', 1)
B["agents"] = (section(grand
                   + f'<p class="legende"><a href="{{{{ROOT}}}}langues-et-formats/">{_x("legende")}</a></p>'))

# 6. Piliers
pi = bloc(t, "section", "pillars")
tete = bloc(pi, "div", "sec-head")
B["piliers"] = (section(h2(txt(bloc(tete, "h2")), "le connaître") + f'<p class="intro">{brut(bloc(tete, "p"))}</p>'
                   + tuiles([(None, brut(bloc(x, "h3")), brut(bloc(x, "p"))) for x in blocs(pi, "div", "pillar")], "tl txt tl-pil")))  # titres plus grands, textes plus petits (2026-10-16)

# 7. Quatre niveaux
lv = bloc(t, "section", "levels")
tete = bloc(lv, "div", "sec-head")
niv = [(str(i + 1), brut(bloc(x, "h3")), brut(bloc(x, "p"))) for i, x in enumerate(blocs(lv, "div", "lev"))]
# Retour de Fabien du 2026-10-16 : introduction sur une ligne, titres des quatre tuiles alignés
B["niveaux"] = (section(h2(txt(bloc(tete, "h2")), "Quatre niveaux") + f'<p class="intro intro-l">{brut(bloc(tete, "p"))}</p>' + tuiles(niv, "tl t4 tl-haut")))

# 8. Comparaison
cp = bloc(t, "section", "compare")
B["comparaison"] = (section(h2(txt(bloc(cp, "h2")), "maîtrise le droit suisse") + f'<p class="intro">{brut(bloc(cp, "p", "compare-note"))}</p>'
                   + '<div class="tb">' + sans_svg(bloc(cp, "table")) + "</div>"
                   + '<p class="legende cmp-leg">' + "".join("<span>" + interne(x) + "</span>" for x in blocs(bloc(cp, "div", "cmp-legend"), "span")[::2]) + "</p>"))

# 9. Sécurité : bento, quatre preuves
se = bloc(t, "section", "security")
tete = bloc(se, "div", "security-head")
items = [(brut(bloc(x, "h3")), brut(bloc(x, "p")), "") for x in blocs(se, "div", "sec-item")[:4]]
# Titre et sous-titre de section au-dessus du bloc (retour de Fabien du 2026-10-16)
B["securite"] = (section(h2(H.escape(trame.texte("accueil.securite.titre"), quote=False), "entièrement suisse")
                         + f'<p class="intro">{H.escape(trame.texte("accueil.securite.intro"), quote=False)}</p>' + bento({"pill": "Sécurité et souveraineté", "titre": h2(txt(bloc(tete, "h2")), "restent en Suisse", "h3s"),
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
# Restructuration du 2026-10-16 : les trois axes répondent au problème, le schéma montre comment ils s'enchaînent, puis la
# souveraineté ; « plateforme » et « piliers » sont remplacés par les axes (contenu repris, détail sur les pages outils)
out = [B["hero"], B["distinctions"], trame.probleme("accueil"), B["axes"], schema_produits.rendre(), B["securite"],
       B["chiffres"], B["agents"], B["niveaux"], B["comparaison"],
       trame.preuves("accueil", bandeau=B["distinctions"], exemple=False), B["faq"], B["appel"]]
assert len(out) == len(B) + 3 - 2, "un bloc existant manque à la trame (plateforme et piliers remplacés par les axes)"

ecrire(P, entete_existant(P), "".join(out))
print("accueil écrite :", sum(len(x) for x in out), "caractères")
