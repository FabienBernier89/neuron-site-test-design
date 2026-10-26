#!/usr/bin/env python3
"""Site Neur.on V2 : assemble les pages de src/pages dans docs/ (docs/fr/<page>, comme les URL de production ; les
langues DE, IT et EN de CONFIG["langues"] vivent à côté, sous leur propre adresse : outils/i18n/langues.py).

Le build travaille en trois passes : (1) assembler_fr compose chaque page française, liens encore en {{ROOT}} ;
(2) TRADUIRE en tire la page de chaque autre langue (outils/i18n/traduire.py, table src/langues/<l>/segments.json) ; une
page n'est construite dans une langue que si elle y est entièrement traduite, et en production une langue ne l'est que
si toutes ses pages, sa 404 et ses llms.txt le sont (décision V3) ; (3) finaliser résout images, dimensions et liens,
puis la page est écrite à chemin_page(page, langue).

Bibliothèque standard uniquement. Lit le site Neur.on (Sites/neuron) pour le méga-menu, le pied de
page, la page 404, les redirections, les images et les données de démonstration, sans jamais y écrire. Le
référencement repris de la V1 (balises et JSON-LD de 156 pages) est figé dans src/data/referencement/ et n'est plus lu
dans la V1 (outils/figer_referencement.py).

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
import subprocess
import sys
from datetime import date
from pathlib import Path

import menu
import redirections
from outils import donnees_structurees, envoi, llms, post
from outils.i18n import langues, localiser, traduire
from outils.i18n.table import Table

ICI = Path(__file__).resolve().parent
NEURON = Path(os.environ.get("NEURON_SRC", ICI.parent / "neuron")).resolve()
SRC, ASSETS = ICI / "src", ICI / "assets"
# Référencement repris de la V1, figé dans le dépôt (outils/figer_referencement.py) : le build ne le lit plus dans la V1
REFERENCEMENT = SRC / "data/referencement"
DOSSIER_LANGUES = SRC / "langues"  # tables de traduction : <langue>/segments.json (outils/i18n/table.py)
DOCS = Path(os.environ.get("SORTIE") or ICI / "docs").resolve()  # dossier de sortie du build
# Réglages du site : apercu (noindex, robots), base, identifiants, destinataire des formulaires
CONFIG = json.loads((SRC / "data/config.json").read_text(encoding="utf-8"))

# Toutes les pages présentes dans src/pages (chemin publié ; source : src/pages/<chemin>index.html), accueil en tête
PAGES = sorted((("" if str(f.parent.relative_to(SRC / "pages")) == "." else str(f.parent.relative_to(SRC / "pages")) + "/")
                for f in (SRC / "pages").rglob("index.html")), key=lambda p: (p != "", p))
ARTICLE = "ressources/blog/traduire-contrat-droit-suisse/"
PAIRE = re.compile(r"^traduction/(allemand|francais|italien|anglais)-(francais|allemand|anglais|italien)/$")
BILLET = re.compile(r"^ressources/(blog|actualites)/[^/]+/$")
# lien de page à résoudre ; un lien déjà localisé ({{ROOT}}de/..., it/, en/) est laissé tel quel
LIEN = re.compile(r'href="\{\{ROOT\}\}(?!(?:de|it|en)/)(?:fr/)?([^"#?]*)([#?][^"]*)?"')
ENTETE = re.compile(r"\A<!--page\n(.*?)\n-->\n", re.S)
IMAGES = ["neuron-logo.png", "neuron-logo-blanc.png", "neuron-mark.png", "favicon.ico", "corrext-logo.svg", "chnell-logo.svg", "chnell-symbol.png"]

TETE = """<!DOCTYPE html>
<html lang="@LANG@" data-theme="systeme">
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


def chemin_page(page, langue="fr"):
    """Fichier écrit par le build pour une page (chemin publié, ex. « corrext/ ») dans une langue : docs/fr/<page>/index.html
    en français, docs/<adresse de la langue>/index.html sinon (langues.route : « traduction/contrats/ » donne
    de/uebersetzung/vertraege/ en allemand). KeyError si la langue ou, hors français, la page est inconnue."""
    if langue == "fr":
        return DOCS / "fr" / page / "index.html"
    return DOCS / langues.route(page, langue) / "index.html"


def relier(html, page, racine=None, langue="fr"):
    """Remplace {{ROOT}} par le chemin relatif vers la racine du site (docs/) et envoie les liens sans page vers
    leur page modèle. langue : langue de la page, qui fixe la profondeur de son dossier (de/kontakt/ est à deux niveaux
    de la racine) ; un lien déjà localisé vers de/, it/ ou en/ n'est pas modifié, hors la racine qui le précède.

    Les pages vivent sous fr/ : un lien de page s'écrit {{ROOT}}contact/ ou {{ROOT}}fr/contact/ et mène à
    fr/contact/ depuis n'importe quelle profondeur, le logo ({{ROOT}}) mène à fr/. Hors lien de page,
    {{ROOT}} désigne la racine du site : assets/, envoi.php. La page 404, servie depuis la racine, passe
    racine="" pour que ses liens partent de la base."""
    if racine is None:
        racine = "../" * ((page.count("/") + 1) if langue == "fr" else langues.route(page, langue).count("/"))

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
    """Dossiers (relatifs à la sortie, « fr/corrext/ ») des pages françaises que ce build écrit, à l'emplacement de
    chemin_page. Les autres langues n'y figurent pas : leurs alternates sont posés à la finalisation (tâche 1.3)."""
    return frozenset(chemin_page(p).parent.relative_to(docs).as_posix().rstrip("/") + "/" for p in pages)


def adresse_construite(url):
    """Vrai si une adresse de production désigne une page de la sortie : la page d'aiguillage de la racine, une page de
    ce build (PAGES) ou une page déjà écrite dans le dossier de sortie. Rien n'est écrit en dur. Ne sert qu'au filtre
    provisoire de seo() : les hreflang définitifs d'une page ne dépendent pas du dossier de sortie, ce sont ceux que
    finaliser pose (outils/i18n/localiser.poser_alternates) d'après les pages construites dans chaque langue."""
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


@functools.lru_cache(maxsize=1)
def _libelles_fil():
    f = REFERENCEMENT / "_fil.json"
    return json.loads(f.read_text(encoding="utf-8")) if f.is_file() else {}


def nom_fil(chemin):
    """Libellé d'un niveau du fil d'Ariane : celui du site Neur.on V1 (figé dans src/data/referencement/_fil.json)
    quand la page y existait, sinon son slug."""
    return _libelles_fil().get(chemin) or chemin.rstrip("/").split("/")[-1].replace("-", " ").capitalize()


LANGUE_PAR_DEFAUT = "fr"  # langue de la page désignée par hreflang x-default
X_DEFAULT = re.compile(r'<link rel="alternate" hreflang="x-default" href="[^"]*">')


def adresse_x_default(page):
    """Cible du hreflang x-default d'une page : sa version dans la langue par défaut (le français), une page réelle et
    indexable. La racine du domaine, page d'aiguillage non indexée (redirigée côté serveur), n'en est plus la cible.
    Quand les versions DE, IT et EN existeront, chacune gardera ce x-default : la version française de la même page
    (ou celle de LANGUE_PAR_DEFAUT si l'on en change)."""
    return f"{PRODUCTION}{LANGUE_PAR_DEFAUT}/{page}"


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
        f'<link rel="alternate" hreflang="x-default" href="{adresse_x_default(page)}">',
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


def referencement_fige(page):
    """Référencement de la page repris de la V1 et figé dans le dépôt (src/data/referencement/<page>index.json), ou
    None pour une page nouvelle. Format décrit dans outils/figer_referencement.py."""
    f = REFERENCEMENT / page / "index.json"
    return json.loads(f.read_text(encoding="utf-8")) if f.is_file() else None


OG_IMAGE = re.compile(r'<meta property="og:image" content="([^"]+)"')


def seo(page, meta=None):
    """Référencement de la page Neur.on V1 correspondante, figé dans le dépôt : canonique et hreflang vers les URL de
    production, Open Graph, données structurées (la version retenue se publiera à ces adresses). Une page nouvelle,
    sans équivalent dans la V1, reçoit un référencement de repli tiré de sa méta. Les hreflang ne gardent ici que
    les langues dont la page existe dans la sortie (garder_alternate) : un état provisoire, que finaliser remplace par
    les alternates des pages construites dans chaque langue (localiser.poser_alternates) ; x-default désigne la
    version française de la page (adresse_x_default)."""
    if not page.endswith("/") and page:
        return ""
    fige = referencement_fige(page)
    if fige is None:
        return seo_repli(page, meta or {})
    balises = [X_DEFAULT.sub(f'<link rel="alternate" hreflang="x-default" href="{adresse_x_default(page)}">', x)
               for x in fige["balises"] if garder_alternate(x)]
    image = next((m.group(1) for m in map(OG_IMAGE.match, fige["balises"]) if m), None)
    return "".join(x + "\n" for x in balises + [completer(d, image) for d in fige["donnees_structurees"]])


def completer(d, image):
    """Bloc JSON-LD (lu) prêt pour la page, complété des champs recommandés pour les résultats enrichis à partir des
    visuels réels du site : image de partage pour un article qui n'en a pas, logo pour une organisation."""
    d = json.loads(json.dumps(d))  # copie : le référencement figé n'est jamais modifié
    for o in (d.get("@graph") or [d]) if isinstance(d, dict) else d:
        if o.get("@type") in ("Article", "BlogPosting", "NewsArticle") and "image" not in o and image:
            o["image"] = image
        if o.get("@type") == "Organization" and "logo" not in o and o.get("url", "").startswith("https://neur-on.ai"):
            o["logo"] = "https://neur-on.ai/assets/img/neuron-logo.png"
    return '<script type="application/ld+json">' + donnees_structurees.ecrire(d) + "</script>"


DATE_BUILD = date.today().isoformat()


@functools.lru_cache(maxsize=1)
def _dates_git():
    """{fichier source relatif au dépôt : date AAAA-MM-JJ du dernier commit qui l'a modifié}, pour src/pages. Un fichier
    modifié ou nouveau, pas encore commité, en est absent (il prend la date du build). Vide si git est indisponible."""
    def git(*args):
        return subprocess.run(["git", *args], cwd=ICI, capture_output=True, text=True, check=True).stdout
    try:
        journal = git("log", "--format=@%cs", "--name-only", "--relative", "--", "src/pages")
        en_cours = set(git("diff", "--name-only", "--relative", "HEAD", "--", "src/pages").split())
        en_cours |= set(git("ls-files", "--others", "--exclude-standard", "--", "src/pages").split())
    except (OSError, subprocess.CalledProcessError):
        return {}
    dates, courante = {}, None
    for ligne in journal.splitlines():
        if ligne.startswith("@"):
            courante = ligne[1:]
        elif ligne and ligne not in dates:
            dates[ligne] = courante
    return {f: d for f, d in dates.items() if f not in en_cours}


def date_page(page):
    """Date de dernière modification d'une page (AAAA-MM-JJ), utilisée par le sitemap (lastmod) et par le JSON-LD
    (dateModified) : la date du dernier commit de son fichier source src/pages/<page>index.html (git log) ; à défaut
    (fichier modifié et pas encore commité, nouveau, ou dépôt sans git), la date du build."""
    return _dates_git().get(f"src/pages/{page}index.html", DATE_BUILD)


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


def assembler_fr(meta, corps, page, nav, pied, v):
    """Page française complète, avant résolution des liens : {{ROOT}} et @LANG@ restent à remplacer (finaliser). C'est ce
    HTML que TRADUIRE reçoit pour les autres langues."""
    cx = 'id="cx"' in corps
    sim = "data-sim" in corps or "data-ech" in corps
    feuilles = (["cx.css"] if cx else []) + (["maq.css"] if 'class="maq' in corps else []) + meta.get("styles", "").split()
    lien_cx = "".join('<link rel="stylesheet" href="{{ROOT}}assets/' + f + "?v=" + v + '">\n' for f in feuilles)
    robots = '<meta name="robots" content="noindex, nofollow">\n' if CONFIG["apercu"] else ""
    html = (TETE.replace("@ROBOTS@", robots).replace("@TITRE@", meta["title"]).replace("@DESC@", meta["description"])
            .replace("@SEO@", seo(page, meta)).replace("@V@", v).replace("@CX@", lien_cx))
    html += menu.rendre_entete(nav, meta.get("menu", ""), minimal=meta.get("gabarit") == "contact",
                              langues=tuple(l for l in langues.LANGUES if l in CONFIG["langues"]))
    html += '<main id="main">\n' + corps + "</main>\n" + menu.rendre_pied(pied)
    demo = 'id="cxSrc"' in corps
    globaux = ["global.js"] if (DOCS / "assets/global.js").exists() else []
    scripts = ["nav.js"] + globaux + (["corrext-demo.js"] if demo else []) + (["sim-data.js", "sim.js"] if sim or demo else []) + meta.get("scripts", "").split()
    html += "".join('<script src="{{ROOT}}assets/' + s + "?v=" + v + '" defer></script>\n' for s in scripts)
    html = post.appliquer(html + "</body>\n</html>\n", page)  # post-traitements des lots, avant la résolution des liens
    # données structurées : @context, entité Organization unique, dateModified (outils/donnees_structurees.py)
    html = donnees_structurees.normaliser(html, page, date_page(page) if page in PAGES else None)
    html = html.replace("@INTER@", PRECHARGE_INTER if utilise_inter(html) else "", 1)  # décidé sur le HTML final
    return html


def finaliser(html, page, langue, construites, racine=None):
    """Dernière passe d'une page assemblée dans une langue : attribut lang, hreflang de toutes les langues construites
    (poser_alternates, français compris), localisation des liens, de la tête et des données structurées (localiser,
    hors français), sélecteur de langue (menu.resoudre_selecteur), images recopiées, dimensions, puis liens relatifs
    (relier). construites : pages construites par langue (langue vers ensemble de pages). racine : voir relier (la 404 passe racine="")."""
    html = html.replace('<html lang="@LANG@"', f'<html lang="{langue}"', 1)
    html = localiser.poser_alternates(html, page, construites)
    html, _ = localiser.localiser(html, page, langue, construites)
    html = menu.resoudre_selecteur(html, page, langue, construites)  # après localiser : voir resoudre_selecteur
    copier_images(html)
    return relier(dimensionner(html), page, racine, langue)


def langues_construites(construites):
    """Langues dont au moins une page est construite, dans l'ordre de langues.LANGUES (le français d'abord)."""
    return [l for l in langues.LANGUES if construites.get(l)]


def assembler(meta, corps, page, nav, pied, v, racine=None, langue="fr", construites=None):
    """Page complète et finalisée dans une langue : assembler_fr puis finaliser (la 404 s'assemble ainsi). Sans
    construites, seul le français est construit : la page est celle d'un site à une seule langue, sans sélecteur."""
    return finaliser(assembler_fr(meta, corps, page, nav, pied, v), page, langue, construites or {"fr": set(PAGES)}, racine)


def base_pages():
    """Chemin du site pour la page 404, servie à toute profondeur : la variable BASE_PAGES si elle est donnée ; sinon
    « / » en production (site à la racine du domaine) et la clé « base » de la configuration sur l'aperçu."""
    return os.environ.get("BASE_PAGES") or ("/" if not CONFIG["apercu"] else CONFIG["base"])


def assembler_404_fr(nav, pied, v):
    """Page 404 française assemblée (passe 1), avant traduction et finalisation ; nommée 404.html pour les
    post-traitements."""
    src = (NEURON / "src/partials/404.html").read_text(encoding="utf-8")
    h1 = re.search(r'<h1 data-t="h1">(.*?)</h1>', src, re.S).group(1)
    lead = re.search(r'<p class="lead" data-t="lead">(.*?)</p>', src, re.S).group(1)
    corps = ('<section class="hero"><div class="wrap hero-g"><h1 class="h1">' + h1 + "</h1>"
             '<div class="hero-d"><p>' + lead + '</p><a class="btn" href="{{ROOT}}">Neur.on</a></div></div></section>\n')
    meta = {"title": "Page introuvable · Neur.on", "description": "Page introuvable."}
    return assembler_fr(meta, corps, "404.html", nav, pied, v)


def page_404_a_traduire(html):
    """404 française assemblée, telle que TRADUIRE la reçoit (clé de page « 404 ») : sans ses données structurées, que
    page_404 retire de toute façon (elles n'ont donc pas à être traduites)."""
    return DONNEES.sub("", html)


def page_404(nav, pied, v, langue="fr", construites=None, html=None):
    """Page 404 d'une langue : DOCS/404.html en français, DOCS/<l>/404.html sinon (main écrit aussi DOCS/<l>/.htaccess, qui
    la désigne). construites : voir assembler ; les liens et le sélecteur de langue en dépendent (aucun sélecteur tant
    que le français est seul construit). html : la 404 assemblée dans la langue (traduite par TRADUIRE hors français) ;
    par défaut, la 404 française."""
    if html is None:
        html = assembler_404_fr(nav, pied, v)
    # servie depuis la racine du site, à toute profondeur, via <base>
    html = finaliser(html, "404.html", langue, construites or {"fr": set(PAGES)}, racine="")
    html = DONNEES.sub("", SEO_TETE.sub("", html)).replace("\n\n", "\n")  # la page 404 n'a ni canonique ni données structurées
    return html.replace("<head>\n", '<head>\n<base href="' + base_pages() + '">\n', 1)


def page_racine(dispo=("fr",)):
    """Page d'aiguillage de la racine : celle du site Neur.on, réduite aux langues construites (dispo : le français et les
    langues dont la page d'accueil l'est). Elle choisit la langue côté navigateur, repli sur le français ; elle reste
    non indexée, comme dans le site actuel. Redirection par Accept-Language et bascule de x-default vers l'anglais :
    lot 10 (décision V7)."""
    h = (NEURON / "docs/index.html").read_text(encoding="utf-8")
    liste = json.dumps(list(dispo), separators=(",", ":"))
    h, n = re.subn(r'var dispo=\[[^\]]*\],def="[a-z]+"', lambda m: f'var dispo={liste},def="fr"', h)
    h = h.replace('<html lang="en">', '<html lang="fr">', 1)
    h = X_DEFAULT.sub(f'<link rel="alternate" hreflang="x-default" href="{adresse_x_default("")}">', h)
    absentes = "|".join(l for l in ("de", "it", "en") if l not in dispo)
    if absentes:
        h = re.sub(rf'<link rel="alternate" hreflang="(?:{absentes})[^"]*" href="[^"]*">\n', "", h)
        h = re.sub(rf'<a href="(?:{absentes})/" hreflang="[^"]*">[A-Z]+</a>(?: · )?', "", h)
    h = re.sub(r" · (?=</p>)", "", h)
    if n != 1 or len(re.findall(r'<a href="fr/" hreflang="fr-CH">FR</a>', h)) != 2 or "location.replace" not in h:
        sys.exit("La page d'aiguillage du site Neur.on a changé de forme : adapter page_racine() dans build.py")
    return h


def plan_du_site(langue="fr", construites=None):
    """Plan du site d'une langue : l'adresse canonique de chaque page indexable construite dans cette langue, lue dans son
    HTML, avec sa date de dernière modification (lastmod, date_page). Ni page noindex (remerciement), ni redirection,
    ni page d'aiguillage ; une page dont la canonique désigne une autre adresse n'y figure pas. Écrit dans sitemap.xml
    quand le français est seul construit, sinon dans sitemap-<l>.xml (réuni par index_sitemaps) : chaque adresse y porte
    alors ses xhtml:link (les mêmes alternates que sa tête : localiser.alternates). construites : voir assembler."""
    construites = construites or {"fr": set(PAGES)}
    multilingue = len(langues_construites(construites)) > 1
    adresses = {}
    for page in PAGES:
        if page not in construites.get(langue, ()):
            continue
        tete = chemin_page(page, langue).read_text(encoding="utf-8").split("</head>", 1)[0]
        if re.search(r'<meta name="robots" content="[^"]*noindex', tete):
            continue
        canonique = re.search(r'<link rel="canonical" href="([^"]+)">', tete)
        propre = PRODUCTION + chemin_page(page, langue).parent.relative_to(DOCS).as_posix() + "/"
        if canonique and H.unescape(canonique.group(1)) == propre and propre not in adresses:
            adresses[propre] = page

    def entree(adresse, page):
        liens = "".join(f'<xhtml:link rel="alternate" hreflang="{hl}" href="{H.escape(url)}"/>'
                        for hl, url in localiser.alternates(page, construites)) if multilingue else ""
        return f"<url><loc>{H.escape(adresse, quote=False)}</loc><lastmod>{date_page(page)}</lastmod>{liens}</url>\n"

    xhtml = ' xmlns:xhtml="http://www.w3.org/1999/xhtml"' if multilingue else ""
    return ('<?xml version="1.0" encoding="UTF-8"?>\n<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9"' + xhtml + ">\n"
            + "".join(entree(a, p) for a, p in adresses.items()) + "</urlset>\n")


def index_sitemaps(langues_presentes):
    """sitemap.xml en index des plans par langue (sitemap-<l>.xml), pour le site à plusieurs langues construites."""
    return ('<?xml version="1.0" encoding="UTF-8"?>\n<sitemapindex xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">\n'
            + "".join(f"<sitemap><loc>{PRODUCTION}sitemap-{l}.xml</loc></sitemap>\n" for l in langues_presentes)
            + "</sitemapindex>\n")


ROBOTS_APERCU = '<meta name="robots" content="noindex, nofollow">\n'
# Pages jamais indexées, quel que soit le mode : la page de remerciement des formulaires (noindex posé par
# outils/post/z_formulaires.py, MERCI ; sur l'aperçu, la balise générale le masque, d'où cette liste)
NON_INDEXEES = ("contact/merci/",)


def indexable(page, langue="fr"):
    """Vrai si la page, dans cette langue, est destinée aux moteurs en production : ni dans NON_INDEXEES (chemins
    français, valables pour toutes les langues), ni exclue par sa propre balise robots (la balise noindex que l'aperçu
    pose sur toutes les pages ne compte pas)."""
    if page in NON_INDEXEES:
        return False
    tete = chemin_page(page, langue).read_text(encoding="utf-8").split("</head>", 1)[0].replace(ROBOTS_APERCU, "", 1)
    return not re.search(r'<meta name="robots" content="[^"]*noindex', tete)


def meta_de_html(html):
    """Titre et description d'une page construite, tels que la tête les porte (la méta d'une page traduite est celle de
    sa traduction, pas celle du français)."""
    titre = re.search(r"<title>(.*?)</title>", html, re.S)
    desc = re.search(r'<meta name="description" content="([^"]*)">', html)
    return {"title": titre.group(1) if titre else "", "description": desc.group(1) if desc else ""}


def ecrire_llms(metas, construites=None, libelles=None):
    """llms.txt et llms-full.txt générés depuis les pages de la V2 (outils/llms.py), datés de la page la plus récente :
    à la racine en français, sous <l>/ pour chaque autre langue construite dont les libellés fixes sont traduits
    (libelles : langue -> fonction de traduction des libellés, Table.t ; métas lues dans ses pages). Le fichier racine
    renvoie vers les autres quand plusieurs langues en ont un. construites : voir assembler."""
    construites = construites or {"fr": set(PAGES)}
    libelles = {"fr": lambda s: s, **(libelles or {})}
    presentes = [l for l in langues_construites(construites) if l in libelles]
    for langue in presentes:
        pages = [(p, metas[p] if langue == "fr" else meta_de_html(chemin_page(p, langue).read_text(encoding="utf-8")))
                 for p in PAGES if p in construites[langue] and indexable(p, langue)]
        recente = max((date_page(p) for p, _ in pages), default=DATE_BUILD)
        dossier = DOCS if langue == "fr" else DOCS / langue
        t = libelles[langue]
        (dossier / "llms.txt").write_text(llms.llms_txt(pages, recente, langue, t, langues=presentes), encoding="utf-8")
        lire = lambda p, l=langue: chemin_page(p, l).read_text(encoding="utf-8")
        (dossier / "llms-full.txt").write_text(llms.llms_full_txt(pages, lire, recente, langue, t), encoding="utf-8")


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


def cible_v2(cible):
    """Cible d'une redirection vérifiée dans la sortie V2 : une ancre (#actu-108) absente de la page V2 construite est
    retirée, la redirection mène alors en haut de la page. Les ancres de la V1 (cartes de la page actualités) n'existent
    pas dans la V2 ; vérifié le 2026-10-23 : aucune des actualités de 2020 et 2021 visées n'a de billet dans la V2,
    la page actualités sans ancre est donc la meilleure cible existante."""
    chemin, _, ancre = cible.partition("#")
    if not ancre:
        return cible
    page = chemin_page(chemin[len("/fr/"):])
    return cible if page.is_file() and f'id="{ancre}"' in page.read_text(encoding="utf-8") else chemin


def ecrire_redirections():
    """Anciennes adresses du site Neur.on : une page de redirection par adresse (aperçu) et un .htaccess de 301.
    Appelée après l'écriture des pages : chaque ancre est vérifiée dans la page V2 (cible_v2)."""
    redirs = {ancien: cible_v2(cible) for ancien, cible in redirections.lire(NEURON).items()}
    for ancien, cible in redirs.items():
        sortie = DOCS / ancien / "index.html"
        if sortie.exists():
            sys.exit(f"Redirection {ancien} : la page existe déjà dans la sortie, elle serait écrasée")
        sortie.parent.mkdir(parents=True, exist_ok=True)
        sortie.write_text(redirections.page(ancien, cible), encoding="utf-8")
    (DOCS / ".htaccess").write_text(redirections.htaccess(redirs), encoding="utf-8")


_TABLES = {}  # tables de traduction lues pendant un build (vidé au début de main)


def table(langue):
    """Table de traduction d'une langue (DOSSIER_LANGUES/<langue>/segments.json), lue une fois par build."""
    k = (langue, str(DOSSIER_LANGUES))
    if k not in _TABLES:
        _TABLES[k] = Table(langue, DOSSIER_LANGUES)
    return _TABLES[k]


def mode_build():
    """Mode de la traduction : « apercu » (traductions adaptées acceptées, avec bandeau) ou « production »."""
    return "apercu" if CONFIG["apercu"] else "production"


def traduire_page(html, page, langue):
    """Passe 2 : page française assemblée -> (page traduite, manquants) avec la table de la langue et le mode du build
    (outils/i18n/traduire.py). Une page avec des manquants n'est pas construite dans la langue."""
    return traduire.traduire(html, page, langue, table(langue), mode_build(), NEURON)


def libelles_llms(langue):
    """Libellés fixes des llms.txt d'une langue : (Table(langue).t, manquants) ; les llms de la langue ne sont écrits que
    sans manquant."""
    return table(langue).t, traduire.verifier_libelles(table(langue), mode_build())


# Points d'injection de la traduction, remplacés par l'identité dans les tests de structure (tests/support.identite)
TRADUIRE = traduire_page
LIBELLES = libelles_llms


def assembler_pages():
    """Passe 1 : copie les assets dans DOCS puis assemble chaque page française (liens encore en {{ROOT}}). Renvoie
    (métas, pages assemblées, menu, pied, version des assets)."""
    copier_assets()
    v = version()
    nav = menu.lire_menu((NEURON / "src/partials/nav.html").read_text(encoding="utf-8"))
    pied = menu.lire_pied((NEURON / "src/partials/footer.html").read_text(encoding="utf-8"))
    menu.appliquer_ajouts(nav, pied)  # entrées de menu et de pied ajoutées par les lots (src/data/menu-ajouts.json)
    metas, assemblees = {}, {}
    for page in PAGES:
        meta, corps = lire_page(page)
        metas[page] = meta
        assemblees[page] = assembler_fr(meta, corps, page, nav, pied, v)
    return metas, assemblees, nav, pied, v


def main():
    garde_sortie()
    if DOCS.exists():
        shutil.rmtree(DOCS)
    DOCS.mkdir(parents=True)
    _TABLES.clear()
    metas, assemblees, nav, pied, v = assembler_pages()  # passe 1
    fr404 = assembler_404_fr(nav, pied, v)
    autres = [l for l in CONFIG["langues"] if l != "fr"]
    construites, traduites, pages_404, libelles = {"fr": set(PAGES)}, {}, {}, {}
    for langue in autres:  # passe 2 : une page n'est construite dans une langue que sans segment manquant
        resultats = {page: TRADUIRE(assemblees[page], page, langue) for page in PAGES}
        html_404, manquants_404 = TRADUIRE(page_404_a_traduire(fr404), "404", langue)
        t, manquants_llms = LIBELLES(langue)
        incompletes = ([p for p, (_, m) in resultats.items() if m] + (["404"] if manquants_404 else [])
                       + (["llms"] if manquants_llms else []))
        if not CONFIG["apercu"] and incompletes:  # production : la langue entière ou rien (décision V3)
            print(f"Langue {langue} non publiée : {len(incompletes)} pages incomplètes")
            construites[langue] = set()
            continue
        construites[langue] = {p for p, (_, m) in resultats.items() if not m}
        traduites.update(((langue, p), h) for p, (h, m) in resultats.items() if not m)
        if not manquants_404:
            pages_404[langue] = html_404
        if not manquants_llms:
            libelles[langue] = t
    for page in PAGES:  # passe 3 : finalisation et écriture, français d'abord
        pages_langues = [("fr", assemblees[page])] + [(l, traduites[l, page]) for l in autres if page in construites[l]]
        for langue, html in pages_langues:
            sortie = chemin_page(page, langue)
            sortie.parent.mkdir(parents=True, exist_ok=True)
            sortie.write_text(finaliser(html, page, langue, construites), encoding="utf-8")
    (DOCS / "404.html").write_text(page_404(nav, pied, v, "fr", construites, fr404), encoding="utf-8")
    for langue in autres:  # une 404 par langue construite et traduite, désignée par le .htaccess de son dossier ; sinon
        if construites[langue] and langue in pages_404:  # la 404 française de la racine sert de repli
            (DOCS / langue / "404.html").write_text(page_404(nav, pied, v, langue, construites, pages_404[langue]), encoding="utf-8")
            (DOCS / langue / ".htaccess").write_text(
                f"# Généré par build.py : ne pas modifier à la main.\nErrorDocument 404 {base_pages()}{langue}/404.html\n", encoding="utf-8")
    presentes = langues_construites(construites)
    accueils = [l for l in langues.LANGUES if l == "fr" or "" in construites.get(l, ())]  # l/ doit exister pour être proposée
    (DOCS / "index.html").write_text(page_racine(accueils), encoding="utf-8")
    # Aperçu : aucun robot, aucun plan du site. Production : tout est ouvert, robots.txt annonce sitemap.xml (un plan
    # par langue réunis en index dès que plusieurs langues sont construites)
    if CONFIG["apercu"]:
        (DOCS / "robots.txt").write_text("User-agent: *\nDisallow: /\n", encoding="utf-8")
    else:
        if len(presentes) > 1:
            for langue in presentes:
                (DOCS / f"sitemap-{langue}.xml").write_text(plan_du_site(langue, construites), encoding="utf-8")
            (DOCS / "sitemap.xml").write_text(index_sitemaps(presentes), encoding="utf-8")
        else:
            (DOCS / "sitemap.xml").write_text(plan_du_site("fr", construites), encoding="utf-8")
        (DOCS / "robots.txt").write_text(f"User-agent: *\nAllow: /\nSitemap: {PRODUCTION}sitemap.xml\n", encoding="utf-8")
    ecrire_llms(metas, construites, libelles)  # résumé et texte intégral pour les moteurs IA, un jeu par langue construite
    (DOCS / ".nojekyll").write_text("", encoding="utf-8")
    ecrire_redirections()
    # envoi des formulaires sur Hostpoint, réglé par la configuration ; sa table des pages de remerciement ne garde
    # que les langues dont cette page est construite, le français toujours (une langue absente renvoie vers lui)
    envoi.ecrire(DOCS / "envoi.php", CONFIG,
                 [l for l in langues.LANGUES if l == "fr" or envoi.PAGE_MERCI in construites.get(l, ())])
    print(f"{len(PAGES)} pages écrites dans {DOCS}")
    for langue in autres:
        print(f"{len(construites[langue])} pages {langue} écrites")


if __name__ == "__main__":
    main()
