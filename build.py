#!/usr/bin/env python3
"""Site de test de design Neur.on : assemble les 11 pages modèles dans docs/.

Bibliothèque standard uniquement. Lit le site Neur.on (Sites/neuron) pour le méga-menu, le pied de
page, la page 404 et les données de démonstration, sans jamais y écrire.
"""
import hashlib
import os
import re
import shutil
import sys
from pathlib import Path

import menu

ICI = Path(__file__).resolve().parent
NEURON = Path(os.environ.get("NEURON_SRC", ICI.parent / "neuron")).resolve()
SRC, DOCS, ASSETS = ICI / "src", ICI / "docs", ICI / "assets"
BASE_PAGES = "/neuron-site-test-design/"  # chemin du site sur GitHub Pages (404 servie à toute profondeur)

# Les 11 pages modèles, par chemin publié (source : src/pages/<chemin>index.html)
PAGES = [
    "",
    "corrext/",
    "corrext/traduction-texte-et-document/",
    "lexmachina/",
    "securite-souverainete/",
    "solutions/cabinets-avocats/",
    "traduction/contrats/",
    "traduction/allemand-francais/",
    "ressources/blog/",
    "ressources/blog/traduire-contrat-droit-suisse/",
    "contact/",
]
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
<meta name="robots" content="noindex, nofollow">
<title>@TITRE@</title>
<meta name="description" content="@DESC@">
<script>try{document.documentElement.dataset.theme=localStorage.getItem("theme")||"systeme"}catch(e){}</script>
<link rel="icon" href="{{ROOT}}assets/img/favicon.ico">
<link rel="preconnect" href="https://fonts.googleapis.com">
<link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
<link rel="stylesheet" href="https://fonts.googleapis.com/css2?family=Inter:wght@500&family=Source+Serif+4:ital,opsz,wght@0,8..60,300;1,8..60,300&display=swap">
<link rel="stylesheet" href="{{ROOT}}assets/site.css?v=@V@">
@CX@</head>
<body>
"""


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


def relier(html, page):
    """Remplace {{ROOT}} par le chemin relatif et envoie les liens sans page vers leur page modèle."""
    racine = "../" * page.count("/")

    def sub(m):
        chemin, suite = m.group(1), m.group(2) or ""
        if chemin.startswith("assets/"):
            return f'href="{racine}{chemin}{suite}"'
        cible, attr = modele(chemin), ""
        if cible != chemin:
            suite, attr = "", f' data-modele="{chemin}"'
        return f'href="{(racine + cible) or "./"}{suite}"{attr}'

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


def copier_assets():
    sortie = DOCS / "assets"
    shutil.copytree(ASSETS, sortie)
    (sortie / "sim-data.js").write_text(sim_data(), encoding="utf-8")
    shutil.copy2(NEURON / "assets/corrext-demo.js", sortie / "corrext-demo.js")
    (sortie / "img").mkdir(exist_ok=True)
    for nom in IMAGES:
        shutil.copy2(NEURON / "assets/img" / nom, sortie / "img" / nom)


def copier_images(html):
    """Recopie les couvertures de blog et d'actualités citées par une page."""
    for chemin in set(re.findall(r'\{\{ROOT\}\}(assets/img/(?:blog|actualites)/[^"\s?]+)', html)):
        cible = DOCS / chemin
        cible.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(NEURON / chemin, cible)


def version():
    h = hashlib.md5()
    for f in sorted((DOCS / "assets").glob("*.*")):
        h.update(f.read_bytes())
    return h.hexdigest()[:8]


def assembler(meta, corps, page, nav, pied, v):
    cx = 'id="cx"' in corps
    sim = "data-sim" in corps or "data-ech" in corps
    feuilles = (["cx.css"] if cx else []) + (["maq.css"] if 'class="maq' in corps else [])
    lien_cx = "".join('<link rel="stylesheet" href="{{ROOT}}assets/' + f + "?v=" + v + '">\n' for f in feuilles)
    html = (TETE.replace("@TITRE@", meta["title"]).replace("@DESC@", meta["description"])
            .replace("@V@", v).replace("@CX@", lien_cx))
    html += menu.rendre_entete(nav, meta.get("menu", ""), minimal=meta.get("gabarit") == "contact")
    html += '<main id="main">\n' + corps + "</main>\n" + menu.rendre_pied(pied)
    scripts = ["nav.js"] + (["corrext-demo.js"] if cx else []) + (["sim-data.js", "sim.js"] if sim or cx else [])
    html += "".join('<script src="{{ROOT}}assets/' + s + "?v=" + v + '" defer></script>\n' for s in scripts)
    return relier(html + "</body>\n</html>\n", page)


def page_404(nav, pied, v):
    src = (NEURON / "src/partials/404.html").read_text(encoding="utf-8")
    h1 = re.search(r'<h1 data-t="h1">(.*?)</h1>', src, re.S).group(1)
    lead = re.search(r'<p class="lead" data-t="lead">(.*?)</p>', src, re.S).group(1)
    corps = ('<section class="hero"><div class="wrap hero-g"><h1 class="h1">' + h1 + "</h1>"
             '<div class="hero-d"><p>' + lead + '</p><a class="btn" href="{{ROOT}}">Neur.on</a></div></div></section>\n')
    meta = {"title": "Page introuvable · Neur.on", "description": "Page introuvable."}
    html = assembler(meta, corps, "", nav, pied, v)
    return html.replace("<head>\n", '<head>\n<base href="' + BASE_PAGES + '">\n', 1)


def main():
    if DOCS.exists():
        shutil.rmtree(DOCS)
    DOCS.mkdir()
    copier_assets()
    v = version()
    nav = menu.lire_menu((NEURON / "src/partials/nav.html").read_text(encoding="utf-8"))
    pied = menu.lire_pied((NEURON / "src/partials/footer.html").read_text(encoding="utf-8"))
    for page in PAGES:
        meta, corps = lire_page(page)
        copier_images(corps)
        sortie = DOCS / page / "index.html"
        sortie.parent.mkdir(parents=True, exist_ok=True)
        sortie.write_text(assembler(meta, corps, page, nav, pied, v), encoding="utf-8")
    (DOCS / "404.html").write_text(page_404(nav, pied, v), encoding="utf-8")
    (DOCS / "robots.txt").write_text("User-agent: *\nDisallow: /\n", encoding="utf-8")
    (DOCS / ".nojekyll").write_text("", encoding="utf-8")
    print(f"{len(PAGES)} pages écrites dans {DOCS}")


if __name__ == "__main__":
    main()
