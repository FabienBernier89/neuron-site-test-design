"""Contenus nouveaux de la V2 : lecture de src/data/contenus-v2/*.json (format dans le README de ce dossier)."""
import json
from pathlib import Path

ICI = Path(__file__).resolve().parent.parent
DOSSIER = ICI / "src/data/contenus-v2"


def toutes(dossier=None):
    """Toutes les entrées des fichiers du dossier, dans l'ordre alphabétique des fichiers, chacune avec son lot.
    Lève ValueError si une clé apparaît deux fois."""
    entrees, vues = [], {}
    for f in sorted(Path(dossier or DOSSIER).glob("*.json")):
        fichier = json.loads(f.read_text(encoding="utf-8"))
        for e in fichier["entrees"]:
            if e["cle"] in vues:
                raise ValueError(f"clé en double « {e['cle']} » : {vues[e['cle']]} et {f.name}")
            vues[e["cle"]] = f.name
            entrees.append({"lot": fichier.get("lot", f.stem), **e})
    return entrees


def texte(cle, dossier=None):
    """Texte d'une entrée. KeyError si la clé n'existe pas."""
    for e in toutes(dossier):
        if e["cle"] == cle:
            return e["texte"]
    raise KeyError(cle)
