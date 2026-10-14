#!/usr/bin/env python3
"""Site Neur.on V2 : assemble les pages de src/pages dans docs/ (docs/fr/<page>, comme les URL de production).

Bibliothèque standard uniquement. Lit le site Neur.on (Sites/neuron) pour le méga-menu, le pied de
page, la page 404 et les données de démonstration, sans jamais y écrire.

Variables d'environnement :
- SORTIE : dossier de sortie (par défaut docs/), pour construire sans écraser le site publié ;
- NEURON_SRC : dossier du site Neur.on lu en lecture seule ;
- BASE_PAGES : chemin de base de la page 404 (par défaut « / » en production, la clé « base » de
  src/data/config.json sur l'aperçu).
"""
import functools
import hashlib
import html as H
import json
import os
import re
import shutil
import struct
import sys
from pathlib import Path

import menu
import redirections
from outils import envoi, post

ICI = Path(__file__).resolve().parent
NEURON = Path(os.environ.get("NEURON_SRC", ICI.parent / "neuron")).resolve()
SRC, ASSETS = ICI / "src", ICI / "assets"
DOCS = Path(os.environ.get("SORTIE") or ICI / "docs").resolve()  # dossier de sortie du build
# Réglages du site : apercu (noindex, robots, ruban), base, identifiants, destinataire des formulaires
CONFIG = json.loads((SRC / "data/config.json").read_text(encoding="utf-8"))

# Toutes les pages présentes dans src/pages (chemin publié ; source : src/pages/<chemin>index.html), accueil en tête
PAGES = sorted((("" if str(f.parent.relative_to(SRC / "pages")) == "." else str(f.parent.relative_to(SRC / "pages")) + "/")
                for f in (SRC / "pages").rglob("index.html")), key=lambda p: (p != "", p))
ARTICLE = "ressources/blog/traduire-contrat-droit-suisse/"
PAIRE = re.compile(r"^traduction/(allemand|francais|italien|anglais)-(francais|allemand|anglais|italien)/$")
BILLET = re.compile(r"^ressources/(blog|actualites)/[^/]+/$")
LIEN = re.compile(r'href="\{\{ROOT\}\}(?:fr/)?([^"#?]*)([#?][^"]*)?"')
ENTETE = re.compile(r"\A<!--page\n(.*?)\n-->\n", re.S)
IMAGES = ["neuron-logo.png", "neuron-logo-blanc.png", "neuron-mark.png", "favicon.ico", "corrext-logo.svg", "chnell-logo.svg", "chnell-symbol.png"]

TETE = """<!DOCTYPE html>
<html lang="fr" data-theme="systeme">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
@ROBOTS@<title>@TITRE@</title>
<meta name="description" content="@DESC@">
@SEO@<script>try{document.documentElement.dataset.theme=localStorage.getItem("theme")||"systeme"}catch(e){}</script>
<link rel="icon" href="{{ROOT}}assets/img/favicon.ico">
<link rel="preload" as="font" type="font/woff2" href="{{ROOT}}assets/fonts/source-serif-4-latin.woff2" crossorigin>
@INTER@<link rel="stylesheet" href="{{ROOT}}assets/site.css?v=@V@">
@CX@</head>
<body>
"""

# Inter 400 latin n'est préchargée que sur les pages qui s'en servent (@INTER@ dans TETE, rempli par assembler)
PRECHARGE_INTER = '<link rel="preload" as="font" type="font/woff2" href="{{ROOT}}assets/fonts/inter-latin.woff2" crossorigin>\n'
ECRAN_CORREXT = re.compile(r'class="(?:[^"]*\s)?c[rx](?:\s|")')  # jeton de classe exact « cr » ou « cx »
CLASSES = re.compile(r'class="([^"]*)"')


def modele(chemin):
    """Page construite qui sert de modèle à un chemin du site actuel (sans « fr/ » ni ancre)."""
    if chemin in PAGES:
        return chemin
    if chemin in ("niveaux-de-qualite/", "langues-et-formats/"):
        return "corrext/"
    if chemin.startswith("corrext/"):
        return "corrext/traduction-texte-et-document/"
    if chemin.startswith("solutions/"):
        return "solutions/cabinets-avocats/"
    if PAIRE.match(chemin):
        return "traduction/allemand-francais/"
    if chemin.startswith("traduction/"):
        return "traduction/contrats/"
    if chemin.startswith("comparatif/"):
        return "lexmachina/"
    if BILLET.match(chemin):
        return ARTICLE
    if chemin.startswith(("ressources/", "aide/")):
        return "ressources/blog/"
    return ""


def chemin_page(page):
    """Fichier écrit par le build pour une page (chemin publié, ex. « corrext/ ») : docs/fr/<page>/index.html."""
    return DOCS / "fr" / page / "index.html"


def relier(html, page, racine=None):
    """Remplace {{ROOT}} par le chemin relatif vers la racine du site (docs/) et envoie les liens sans page vers
    leur page modèle.

    Les pages vivent sous fr/ : un lien de page s'écrit {{ROOT}}contact/ ou {{ROOT}}fr/contact/ et mène à
    fr/contact/ depuis n'importe quelle profondeur, le logo ({{ROOT}}) mène à fr/. Hors lien de page,
    {{ROOT}} désigne la racine du site : assets/, envoi.php. La page 404, servie depuis la racine, passe
    racine="" pour que ses liens partent de la base."""
    if racine is None:
        racine = "../" * (page.count("/") + 1)

    def sub(m):
        chemin, suite = m.group(1), m.group(2) or ""
        if chemin.startswith("assets/"):
            return f'href="{racine}{chemin}{suite}"'
        cible, attr = modele(chemin), ""
        if cible != chemin:
            suite, attr = "", f' data-modele="{chemin}"'
        return f'href="{racine}fr/{cible}{suite}"{attr}'

    return LIEN.sub(sub, html).replace("{{ROOT}}", racine)


def lire_page(page):
    brut = (SRC / "pages" / page / "index.html").read_text(encoding="utf-8")
    m = ENTETE.match(brut)
    if not m:
        sys.exit(f"Front-matter manquant : src/pages/{page}index.html")
    meta = dict(ligne.split(": ", 1) for ligne in m.group(1).splitlines() if ": " in ligne)
    return meta, brut[m.end():]


def sim_data():
    """Objet EX de la démo Corrext du site Neur.on, copié sans modification."""
    js = (NEURON / "assets/corrext-demo.js").read_text(encoding="utf-8")
    debut = js.index("var EX=") + len("var EX=")
    fin = js.index("};\n", debut) + 1
    return ("/* Données réelles de la démo Corrext, copiées telles quelles depuis le site Neur.on par build.py. */\n"
            "window.SIM_EX=" + js[debut:fin] + ";\n")


def etendre_assets(sortie):
    """Points d'extension des assets : les feuilles assets/composants/*.css sont ajoutées à la fin de site.css, les
    scripts assets/global/*.js réunis dans global.js (un « ; » les sépare), chacun dans l'ordre alphabétique."""
    css = sorted((ASSETS / "composants").glob("*.css"))
    if css:
        with (sortie / "site.css").open("a", encoding="utf-8") as s:
            for f in css:
                s.write(f"\n/* composants/{f.name} */\n{f.read_text(encoding='utf-8').rstrip()}\n")
    js = sorted((ASSETS / "global").glob("*.js"))
    if js:
        (sortie / "global.js").write_text(
            "".join(f"/* global/{f.name} */\n{f.read_text(encoding='utf-8').rstrip()}\n;\n" for f in js), encoding="utf-8")


def copier_assets():
    sortie = DOCS / "assets"
    shutil.copytree(ASSETS, sortie, ignore=shutil.ignore_patterns("composants", "global"))
    etendre_assets(sortie)
    (sortie / "sim-data.js").write_text(sim_data(), encoding="utf-8")
    shutil.copy2(NEURON / "assets/corrext-demo.js", sortie / "corrext-demo.js")
    (sortie / "img").mkdir(exist_ok=True)
    for nom in IMAGES:
        shutil.copy2(NEURON / "assets/img" / nom, sortie / "img" / nom)


def copier_images(html):
    """Recopie les images et documents du site Neur.on cités par une page (couvertures, illustrations, PDF) : en chemin
    {{ROOT}}assets/..., et les images citées par leur adresse de production https://neur-on.ai/assets/img/... (og:image,
    données structurées), qui doivent exister une fois le site publié à cette adresse."""
    relatifs = re.findall(r'\{\{ROOT\}\}(assets/(?:img|docs)/[^"\s?)#]+)', html)
    absolus = re.findall(r'https://neur-on\.ai/(assets/img/[^"\'\s?)#<>\\]+)', html)
    for chemin in set(relatifs + absolus):
        cible = DOCS / chemin
        if cible.exists() or not (NEURON / chemin).is_file():
            continue
        cible.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(NEURON / chemin, cible)


def version():
    h = hashlib.md5()
    for f in sorted((DOCS / "assets").glob("*.*")):
        h.update(f.read_bytes())
    return h.hexdigest()[:8]


SEO_TETE = re.compile(r'<link rel="(?:canonical|alternate)"[^>]*>|<meta (?:property="og:[^"]+"|name="twitter:[^"]+"|name="theme-color")[^>]*>')
DONNEES = re.compile(r'<script type="application/ld\+json">.*?</script>', re.S)
PRODUCTION = "https://neur-on.ai/"  # adresse du site publié
ALTERNATE = re.compile(r'<link rel="alternate" hreflang="[^"]+" href="([^"]+)">')


@functools.lru_cache(maxsize=8)
def _chemins_construits(docs, pages):
    """Dossiers (relatifs à la sortie, « fr/corrext/ ») des pages que ce build écrit, à l'emplacement de chemin_page."""
    return frozenset(chemin_page(p).parent.relative_to(docs).as_posix().rstrip("/") + "/" for p in pages)


def adresse_construite(url):
    """Vrai si une adresse de production désigne une page de la sortie : la page d'aiguillage de la racine, une page de
    ce build (PAGES) ou une page déjà écrite dans le dossier de sortie. Rien n'est écrit en dur : un hreflang vers une
    langue absente de la sortie est retiré, et revient de lui-même dès que les pages de cette langue sont construites."""
    if not url.startswith(PRODUCTION):
        return False
    chemin = url[len(PRODUCTION):].split("#")[0].split("?")[0]
    if chemin == "":
        return True
    return chemin in _chemins_construits(DOCS, tuple(PAGES)) or (DOCS / chemin / "index.html").is_file()


def garder_alternate(balise):
    """Faux pour un hreflang qui mène à une page absente de la sortie ; vrai pour toute autre balise."""
    m = ALTERNATE.match(balise)
    return not m or adresse_construite(m.group(1))


def blocs_json(html):
    """Données structurées (JSON-LD) d'une page, lues."""
    return [json.loads(b[b.index(">") + 1:b.rindex("<")]) for b in DONNEES.findall(html)]


def nom_fil(chemin):
    """Libellé d'un niveau du fil d'Ariane : celui du site Neur.on actuel quand la page y existe, sinon son slug."""
    f = NEURON / "docs/fr" / chemin / "index.html"
    if f.is_file():
        for d in blocs_json(f.read_text(encoding="utf-8")):
            if isinstance(d, dict) and d.get("@type") == "BreadcrumbList":
                return d["itemListElement"][-1]["name"]
    return chemin.rstrip("/").split("/")[-1].replace("-", " ").capitalize()


def seo_repli(page, meta):
    """Référencement d'une page nouvelle, sans équivalent dans le site Neur.on actuel : canonique et hreflang fr-CH
    vers son adresse de production, Open Graph tiré de sa méta, fil d'Ariane (BreadcrumbList) : Accueil, puis chaque
    niveau du chemin, la page elle-même portant le début de son titre (avant « · »)."""
    url = "https://neur-on.ai/fr/" + page
    echappe = lambda s: H.escape(H.unescape(s), quote=True)
    titre = meta.get("title", "")
    segments = [s for s in page.split("/") if s]
    fil = [{"@type": "ListItem", "position": 1, "name": "Accueil", "item": "https://neur-on.ai/fr/"}]
    for i in range(len(segments)):
        chemin = "/".join(segments[:i + 1]) + "/"
        nom = H.unescape(titre).split(" · ")[0] if i == len(segments) - 1 else nom_fil(chemin)
        fil.append({"@type": "ListItem", "position": i + 2, "name": nom, "item": "https://neur-on.ai/fr/" + chemin})
    lignes = [x for x in [
        f'<link rel="canonical" href="{url}">',
        f'<link rel="alternate" hreflang="fr-CH" href="{url}">',
        '<link rel="alternate" hreflang="x-default" href="https://neur-on.ai/">',
        f'<meta property="og:title" content="{echappe(titre)}">',
        f'<meta property="og:description" content="{echappe(meta.get("description", ""))}">',
        f'<meta property="og:url" content="{url}">',
        '<meta property="og:type" content="website">',
        '<meta property="og:image" content="https://neur-on.ai/assets/img/og-neuron.jpg">',
        '<meta property="og:image:alt" content="Neur.on, traduction par IA pour le droit, la fiscalité et la finance">',
        '<meta property="og:site_name" content="Neur.on">',
        '<meta property="og:locale" content="fr_CH">',
        '<meta name="twitter:card" content="summary_large_image">',
        '<script type="application/ld+json">' + json.dumps({"@context": "https://schema.org", "@type": "BreadcrumbList",
                                                           "itemListElement": fil}, ensure_ascii=False).replace("</", "<\\/") + "</script>"]
        if garder_alternate(x)]
    return "".join(x + "\n" for x in lignes)


def seo(page, meta=None):
    """Référencement de la page Neur.on correspondante, repris tel quel : canonique et hreflang vers les URL de
    production, Open Graph, données structurées (la version retenue se publiera à ces adresses). Une page nouvelle,
    sans équivalent dans le site actuel, reçoit un référencement de repli tiré de sa méta. Les hreflang ne gardent que
    les langues dont la page existe dans la sortie (garder_alternate) : aujourd'hui fr-CH et x-default."""
    s = NEURON / "docs/fr" / page / "index.html"
    if not page.endswith("/") and page:
        return ""
    if not s.exists():
        return seo_repli(page, meta or {})
    h = s.read_text(encoding="utf-8")
    tete = [x for x in SEO_TETE.findall(h[:h.find("</head>")]) if garder_alternate(x)]
    image = re.search(r'<meta property="og:image" content="([^"]+)"', h)
    return "".join(x + "\n" for x in tete + [completer(d, image.group(1) if image else None) for d in DONNEES.findall(h)])


def completer(bloc, image):
    """Complète les entités principales des champs recommandés pour les résultats enrichis, à partir des visuels
    réels du site : image de partage pour un article qui n'en a pas, logo pour une organisation."""
    d = json.loads(bloc[bloc.index(">") + 1:bloc.rindex("<")])
    modifie = False
    for o in (d.get("@graph") or [d]) if isinstance(d, dict) else d:
        if o.get("@type") in ("Article", "BlogPosting", "NewsArticle") and "image" not in o and image:
            o["image"] = image
            modifie = True
        if o.get("@type") == "Organization" and "logo" not in o and o.get("url", "").startswith("https://neur-on.ai"):
            o["logo"] = "https://neur-on.ai/assets/img/neuron-logo.png"
            modifie = True
    if not modifie:
        return bloc
    return '<script type="application/ld+json">' + json.dumps(d, ensure_ascii=False) + "</script>"


_TAILLES = {}


def taille_image(f):
    """Largeur et hauteur intrinsèques d'une image PNG, JPEG, WebP ou SVG (None si illisible)."""
    if f in _TAILLES:
        return _TAILLES[f]
    r = None
    try:
        b = f.read_bytes()
        if b[:8] == b"\x89PNG\r\n\x1a\n":
            r = struct.unpack(">II", b[16:24])
        elif b[:2] == b"\xff\xd8":
            i = 2
            while i < len(b) - 9:
                if b[i] != 0xFF:
                    i += 1
                    continue
                m, n = b[i + 1], struct.unpack(">H", b[i + 2:i + 4])[0]
                if m in (0xC0, 0xC1, 0xC2):
                    h, w = struct.unpack(">HH", b[i + 5:i + 9])
                    r = (w, h)
                    break
                i += 2 + n
        elif b[:4] == b"RIFF" and b[8:12] == b"WEBP":
            if b[12:16] == b"VP8X":
                r = (1 + int.from_bytes(b[24:27], "little"), 1 + int.from_bytes(b[27:30], "little"))
            elif b[12:16] == b"VP8L":
                x = int.from_bytes(b[21:25], "little")
                r = ((x & 0x3FFF) + 1, ((x >> 14) & 0x3FFF) + 1)
            elif b[12:16] == b"VP8 ":
                w, h = struct.unpack("<HH", b[26:30])
                r = (w & 0x3FFF, h & 0x3FFF)
        elif f.suffix == ".svg":
            s = b[:2000].decode("utf-8", "ignore")
            vb = re.search(r'viewBox="[\d.\s-]*?([\d.]+)\s+([\d.]+)"', s)
            if vb:
                r = (round(float(vb.group(1))), round(float(vb.group(2))))
    except OSError:
        pass
    _TAILLES[f] = r
    return r


def dimensionner(html):
    """Ajoute largeur et hauteur aux images qui n'en ont pas (pas de décalage de mise en page) et le chargement
    différé aux images du contenu situées après la première section."""
    def poser(m):
        img = m.group(0)
        if "width=" in img and "height=" in img:
            return img
        src = re.search(r'src="\{\{ROOT\}\}([^"?]+)', img)
        r = taille_image(NEURON / src.group(1)) if src else None
        if not r:
            src2 = re.search(r'src="\{\{ROOT\}\}(assets/[^"?]+)', img)
            r = taille_image(ASSETS.parent / src2.group(1)) if src2 else None
        return img[:-1].rstrip("/").rstrip() + f' width="{r[0]}" height="{r[1]}">' if r else img
    html = re.sub(r"<img\b[^>]*>", poser, html)
    debut = html.find("<main")
    premiere = html.find("</section>", debut)
    if debut < 0 or premiere < 0:
        return html
    suite = re.sub(r'<img\b(?![^>]*\bloading=)', '<img loading="lazy" decoding="async"', html[premiere:])
    return html[:premiere] + suite


@functools.lru_cache(maxsize=8)
def classes_num(css):
    """Classes des sélecteurs de la feuille qui utilisent var(--num), la police des chiffres (Inter) : un tuple de
    frozenset, un par sélecteur (toutes ses classes, hors :not). Un sélecteur sans classe donne un ensemble vide."""
    css = re.sub(r"/\*.*?\*/", "", css, flags=re.S)
    selecteurs = []
    for liste, declarations in re.findall(r"([^{}]+)\{([^{}]*)\}", css):
        if "var(--num)" in declarations:
            for s in liste.split(","):
                s = re.sub(r"\[[^\]]*\]", "", re.sub(r":not\([^)]*\)", "", s))
                selecteurs.append(frozenset(re.findall(r"\.([A-Za-z_-][\w-]*)", s)))
    return tuple(dict.fromkeys(selecteurs))


def utilise_inter(html, css=None):
    """Vrai si la page, dans son HTML final, montre un écran Corrext (classe « cr » ou « cx ») ou un élément dont un
    sélecteur de la feuille pose var(--num). Pour un sélecteur, toutes ses classes doivent figurer dans la page :
    c'est une condition nécessaire pour qu'il s'applique (jamais de faux négatif). css : feuille du site construit."""
    if ECRAN_CORREXT.search(html):
        return True
    if css is None:
        css = (DOCS / "assets/site.css").read_text(encoding="utf-8")
    jetons = {j for valeur in CLASSES.findall(html) for j in valeur.split()}
    return any(classes <= jetons for classes in classes_num(css))


def assembler(meta, corps, page, nav, pied, v, racine=None):
    cx = 'id="cx"' in corps
    sim = "data-sim" in corps or "data-ech" in corps
    feuilles = (["cx.css"] if cx else []) + (["maq.css"] if 'class="maq' in corps else []) + meta.get("styles", "").split()
    lien_cx = "".join('<link rel="stylesheet" href="{{ROOT}}assets/' + f + "?v=" + v + '">\n' for f in feuilles)
    robots = '<meta name="robots" content="noindex, nofollow">\n' if CONFIG["apercu"] else ""
    html = (TETE.replace("@ROBOTS@", robots).replace("@TITRE@", meta["title"]).replace("@DESC@", meta["description"])
            .replace("@SEO@", seo(page, meta)).replace("@V@", v).replace("@CX@", lien_cx))
    html += menu.rendre_entete(nav, meta.get("menu", ""), minimal=meta.get("gabarit") == "contact", ruban=CONFIG["apercu"])
    html += '<main id="main">\n' + corps + "</main>\n" + menu.rendre_pied(pied)
    demo = 'id="cxSrc"' in corps
    globaux = ["global.js"] if (DOCS / "assets/global.js").exists() else []
    scripts = ["nav.js"] + globaux + (["corrext-demo.js"] if demo else []) + (["sim-data.js", "sim.js"] if sim or demo else []) + meta.get("scripts", "").split()
    html += "".join('<script src="{{ROOT}}assets/' + s + "?v=" + v + '" defer></script>\n' for s in scripts)
    html = post.appliquer(html + "</body>\n</html>\n", page)  # post-traitements des lots, avant la résolution des liens
    html = html.replace("@INTER@", PRECHARGE_INTER if utilise_inter(html) else "", 1)  # décidé sur le HTML final
    copier_images(html)
    return relier(dimensionner(html), page, racine)


def base_pages():
    """Chemin du site pour la page 404, servie à toute profondeur : la variable BASE_PAGES si elle est donnée ; sinon
    « / » en production (site à la racine du domaine) et la clé « base » de la configuration sur l'aperçu."""
    return os.environ.get("BASE_PAGES") or ("/" if not CONFIG["apercu"] else CONFIG["base"])


def page_404(nav, pied, v):
    src = (NEURON / "src/partials/404.html").read_text(encoding="utf-8")
    h1 = re.search(r'<h1 data-t="h1">(.*?)</h1>', src, re.S).group(1)
    lead = re.search(r'<p class="lead" data-t="lead">(.*?)</p>', src, re.S).group(1)
    corps = ('<section class="hero"><div class="wrap hero-g"><h1 class="h1">' + h1 + "</h1>"
             '<div class="hero-d"><p>' + lead + '</p><a class="btn" href="{{ROOT}}">Neur.on</a></div></div></section>\n')
    meta = {"title": "Page introuvable · Neur.on", "description": "Page introuvable."}
    # servie depuis la racine du site, à toute profondeur, via <base> ; nommée 404.html pour les post-traitements
    html = assembler(meta, corps, "404.html", nav, pied, v, racine="")
    html = DONNEES.sub("", SEO_TETE.sub("", html)).replace("\n\n", "\n")  # la page 404 n'a ni canonique ni données structurées
    return html.replace("<head>\n", '<head>\n<base href="' + base_pages() + '">\n', 1)


def page_racine():
    """Page d'aiguillage de la racine : celle du site Neur.on, réduite à la seule langue du site, le français.
    Elle choisit la langue côté navigateur ; elle reste non indexée, comme dans le site actuel."""
    h = (NEURON / "docs/index.html").read_text(encoding="utf-8")
    h, n = re.subn(r'var dispo=\[[^\]]*\],def="[a-z]+"', 'var dispo=["fr"],def="fr"', h)
    h = h.replace('<html lang="en">', '<html lang="fr">', 1)
    h = re.sub(r'<link rel="alternate" hreflang="(?:de|it|en)[^"]*" href="[^"]*">\n', "", h)
    h = re.sub(r'<a href="(?:de|it|en)/" hreflang="[^"]*">[A-Z]+</a>(?: · )?', "", h)
    h = re.sub(r" · (?=</p>)", "", h)
    if n != 1 or len(re.findall(r'<a href="fr/" hreflang="fr-CH">FR</a>', h)) != 2 or "location.replace" not in h:
        sys.exit("La page d'aiguillage du site Neur.on a changé de forme : adapter page_racine() dans build.py")
    return h


def plan_du_site():
    """sitemap.xml de la production : l'adresse canonique de chaque page indexable écrite par ce build, lue dans son
    HTML. Ni page noindex (remerciement), ni redirection, ni page d'aiguillage ; une page dont la canonique désigne une
    autre adresse n'y figure pas."""
    adresses = []
    for page in PAGES:
        tete = chemin_page(page).read_text(encoding="utf-8").split("</head>", 1)[0]
        if re.search(r'<meta name="robots" content="[^"]*noindex', tete):
            continue
        canonique = re.search(r'<link rel="canonical" href="([^"]+)">', tete)
        propre = PRODUCTION + chemin_page(page).parent.relative_to(DOCS).as_posix() + "/"
        if canonique and H.unescape(canonique.group(1)) == propre and propre not in adresses:
            adresses.append(propre)
    return ('<?xml version="1.0" encoding="UTF-8"?>\n<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">\n'
            + "".join(f"<url><loc>{H.escape(a, quote=False)}</loc></url>\n" for a in adresses) + "</urlset>\n")


LIEN_LANGUE = re.compile(r"https://neur-on\.ai/(?:de|it|en)/[^)\s]*")


def llms_txt(texte):
    """llms.txt du site Neur.on réduit à la sortie : chaque ligne qui mène à une page /de/, /it/ ou /en/ absente de la
    sortie est retirée (adresse_construite), et une section (« ## ») qui perd ainsi tous ses liens disparaît avec son
    titre. Le reste est gardé mot pour mot ; une langue dont les pages sont construites revient d'elle-même."""
    def gardee(ligne):
        return all(adresse_construite(u) for u in LIEN_LANGUE.findall(ligne))

    blocs = re.split(r"(?m)^(?=## )", texte)
    sortie = [blocs[0]]
    for bloc in blocs[1:]:
        lignes = bloc.splitlines(keepends=True)
        restantes = [l for l in lignes if gardee(l)]
        avait = any("](https://" in l for l in lignes)
        if avait and not any("](https://" in l for l in restantes):
            continue
        sortie.append("".join(restantes))
    return re.sub(r"\n{3,}", "\n\n", "".join(sortie)).rstrip("\n") + "\n"


def garde_sortie():
    """Le build vide son dossier de sortie : refuse un dossier qui contient le dépôt, le site Neur.on ou le
    dossier personnel, tout dossier situé à l'intérieur du site Neur.on (lu en lecture seule) et tout dossier situé à
    l'intérieur du dépôt, sauf docs/ lui-même."""
    for sensible in (ICI, NEURON, Path.home()):
        if DOCS == sensible or DOCS in sensible.parents:
            sys.exit(f"Dossier de sortie refusé (il contiendrait {sensible}) : {DOCS}")
    if NEURON in DOCS.parents:
        sys.exit(f"Dossier de sortie refusé (dans le site Neur.on, en lecture seule) : {DOCS}")
    if ICI in DOCS.parents and DOCS != ICI / "docs":
        sys.exit(f"Dossier de sortie refusé (dans le dépôt, où seul docs/ est une sortie) : {DOCS}")


def ecrire_redirections():
    """Anciennes adresses du site Neur.on : une page de redirection par adresse (aperçu) et un .htaccess de 301."""
    redirs = redirections.lire(NEURON)
    for ancien, cible in redirs.items():
        sortie = DOCS / ancien / "index.html"
        if sortie.exists():
            sys.exit(f"Redirection {ancien} : la page existe déjà dans la sortie, elle serait écrasée")
        sortie.parent.mkdir(parents=True, exist_ok=True)
        sortie.write_text(redirections.page(ancien, cible), encoding="utf-8")
    (DOCS / ".htaccess").write_text(redirections.htaccess(redirs), encoding="utf-8")


def main():
    garde_sortie()
    if DOCS.exists():
        shutil.rmtree(DOCS)
    DOCS.mkdir(parents=True)
    copier_assets()
    v = version()
    nav = menu.lire_menu((NEURON / "src/partials/nav.html").read_text(encoding="utf-8"))
    pied = menu.lire_pied((NEURON / "src/partials/footer.html").read_text(encoding="utf-8"))
    menu.appliquer_ajouts(nav, pied)  # entrées de menu et de pied ajoutées par les lots (src/data/menu-ajouts.json)
    for page in PAGES:
        meta, corps = lire_page(page)
        sortie = chemin_page(page)
        sortie.parent.mkdir(parents=True, exist_ok=True)
        sortie.write_text(assembler(meta, corps, page, nav, pied, v), encoding="utf-8")
    (DOCS / "404.html").write_text(page_404(nav, pied, v), encoding="utf-8")
    (DOCS / "index.html").write_text(page_racine(), encoding="utf-8")
    # Aperçu : aucun robot, aucun plan du site. Production : tout est ouvert, robots.txt annonce sitemap.xml
    if CONFIG["apercu"]:
        (DOCS / "robots.txt").write_text("User-agent: *\nDisallow: /\n", encoding="utf-8")
    else:
        (DOCS / "sitemap.xml").write_text(plan_du_site(), encoding="utf-8")
        (DOCS / "robots.txt").write_text(f"User-agent: *\nAllow: /\nSitemap: {PRODUCTION}sitemap.xml\n", encoding="utf-8")
    if (NEURON / "docs/llms.txt").exists():  # résumé pour les moteurs IA du site Neur.on, réduit aux pages de la sortie
        (DOCS / "llms.txt").write_text(llms_txt((NEURON / "docs/llms.txt").read_text(encoding="utf-8")), encoding="utf-8")
    (DOCS / ".nojekyll").write_text("", encoding="utf-8")
    ecrire_redirections()
    envoi.ecrire(DOCS / "envoi.php", CONFIG)  # envoi des formulaires sur Hostpoint, réglé par la configuration
    print(f"{len(PAGES)} pages écrites dans {DOCS}")


if __name__ == "__main__":
    main()
