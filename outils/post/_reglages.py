"""Réglages du build en cours, lus par les post-traitements du lot C (nom en « _ » : le chargeur l'ignore).

Les post-traitements ne reçoivent que (html, page) : ils lisent la configuration du module build qui tourne, celle que
les tests surchargent (tests/support.py), et à défaut src/data/config.json, en lecture seule."""
import json
import sys
from pathlib import Path

FICHIER = Path(__file__).resolve().parents[2] / "src/data/config.json"


def config():
    """Réglages du build en cours : module « build » importé (tests) ou lancé en script (« __main__ »), sinon le fichier."""
    for nom in ("build", "__main__"):
        module = sys.modules.get(nom)
        reglages = getattr(module, "CONFIG", None)
        if isinstance(reglages, dict) and callable(getattr(module, "chemin_page", None)):
            return reglages
    return json.loads(FICHIER.read_text(encoding="utf-8"))
