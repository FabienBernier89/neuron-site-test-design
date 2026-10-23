#!/usr/bin/env python3
"""Fige dans le dépôt le référencement repris du site Neur.on V1, pour que le build n'aille plus le lire dans la V1.

Avant ce script, build.py relisait à chaque build, dans Sites/neuron/docs/fr/<page>/index.html, les balises de
référencement (canonique, hreflang, Open Graph, Twitter, theme-color) et les données structurées (JSON-LD) de 156
pages, ainsi que les libellés du fil d'Ariane. Toute modification de la V1 changeait donc le référencement de la V2.

Ce script copie ces données une fois, SANS rien y changer, dans src/data/referencement/ :
- <chemin de la page>/index.json, un fichier par page reprise de la V1 (accueil : index.json à la racine du
  dossier). Clés : « source » (fichier V1 d'origine), « balises » (les balises de l'en-tête, telles quelles, y
  compris les hreflang des langues pas encore construites), « donnees_structurees » (les blocs JSON-LD de la page V1,
  dans l'ordre, lus en JSON) ;
- _fil.json : libellé du fil d'Ariane de chaque niveau de chemin qui existe dans la V1 (dernier élément de son
  BreadcrumbList).

Le build lit ces fichiers (build.seo, build.nom_fil) et applique ensuite ses propres règles (hreflang des seules
langues construites, x-default, entité Organization unique, @context, dateModified) : les fichiers restent la copie
exacte de la V1. Une page sans fichier reçoit le référencement de repli tiré de sa méta (build.seo_repli).

Usage (rarement : seulement pour reprendre une nouvelle page de la V1) :
    NEURON_SRC=<dossier de la V1> python3 outils/figer_referencement.py [page/ ...]
Sans argument, toutes les pages de build.PAGES qui existent dans la V1 sont figées (fichiers existants remplacés).
"""
import json
import sys
from pathlib import Path

ICI = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ICI))
import build  # noqa: E402

DOSSIER = build.REFERENCEMENT


def lire_v1(page):
    """(balises, blocs JSON-LD) de la page V1, lus comme le faisait build.seo avant le gel ; None si la page n'existe pas."""
    s = build.NEURON / "docs/fr" / page / "index.html"
    if not s.is_file():
        return None
    h = s.read_text(encoding="utf-8")
    balises = build.SEO_TETE.findall(h[:h.find("</head>")])
    return balises, build.blocs_json(h)


def libelle_v1(chemin):
    """Libellé du fil d'Ariane d'un niveau de chemin dans la V1 (None si la page n'y existe pas)."""
    f = build.NEURON / "docs/fr" / chemin / "index.html"
    if f.is_file():
        for d in build.blocs_json(f.read_text(encoding="utf-8")):
            if isinstance(d, dict) and d.get("@type") == "BreadcrumbList":
                return d["itemListElement"][-1]["name"]
    return None


def ecrire(chemin, donnees):
    chemin.parent.mkdir(parents=True, exist_ok=True)
    chemin.write_text(json.dumps(donnees, ensure_ascii=False, indent=1) + "\n", encoding="utf-8")


def main(pages):
    if not (build.NEURON / "docs/fr").is_dir():
        sys.exit(f"Site Neur.on V1 introuvable : {build.NEURON} (variable NEURON_SRC)")
    figees = 0
    for page in pages:
        lu = lire_v1(page)
        if lu is None:
            continue
        balises, blocs = lu
        ecrire(DOSSIER / page / "index.json", {"source": f"Sites/neuron/docs/fr/{page}index.html",
                                              "balises": balises, "donnees_structurees": blocs})
        figees += 1
    fil = {}
    for page in build.PAGES:
        segments = [s for s in page.split("/") if s]
        for i in range(len(segments)):
            chemin = "/".join(segments[:i + 1]) + "/"
            nom = libelle_v1(chemin)
            if nom is not None:
                fil[chemin] = nom
    ecrire(DOSSIER / "_fil.json", dict(sorted(fil.items())))
    print(f"{figees} pages figées, {len(fil)} libellés de fil d'Ariane, dans {DOSSIER}")


if __name__ == "__main__":
    main(sys.argv[1:] or build.PAGES)
