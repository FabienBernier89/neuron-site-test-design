"""Adresses des pages par langue (DE, IT, EN) et conversion dans les deux sens.

La table est src/data/routes.json : les 156 entrées de la V1 (Sites/neuron/src/routes.json, slugs inchangés) plus les
trois pages nouvelles de la V2 (tarifs, plugin Word, remerciement du formulaire), dont les adresses sont validées par
Fabien (décision V1 du 2026-10-23). Format : {"fr/<page>": {"de": "...", "it": "...", "en": "..."}}, la page d'accueil
étant "fr/". Les adresses françaises se déduisent de la page : "fr/" + page.

Bibliothèque standard seulement."""
import json
from pathlib import Path

ICI = Path(__file__).resolve().parent.parent.parent
ROUTES = ICI / "src/data/routes.json"
LANGUES = ("fr", "de", "it", "en")
HREFLANG = {"fr": "fr-CH", "de": "de-CH", "it": "it-CH", "en": "en"}
OG_LOCALE = {"fr": "fr_CH", "de": "de_CH", "it": "it_CH", "en": "en_GB"}

TABLE = json.loads(ROUTES.read_text(encoding="utf-8"))
# adresse (avec son préfixe de langue) vers (page, langue), pour toutes les langues
_INVERSE = {"fr/" + cle[3:]: (cle[3:], "fr") for cle in TABLE}
for _cle, _adresses in TABLE.items():
    for _langue, _adresse in _adresses.items():
        _INVERSE[_adresse] = (_cle[3:], _langue)


def route(page, langue):
    """Adresse de la page dans la langue, préfixe de langue compris : ("traduction/contrats/", "de") donne
    "de/uebersetzung/vertraege/". KeyError si la langue ou la page est inconnue."""
    if langue not in LANGUES:
        raise KeyError(f"langue inconnue : {langue}")
    cle = "fr/" + page
    if cle not in TABLE:
        raise KeyError(f"page absente de la table des adresses : {page!r}")
    return cle if langue == "fr" else TABLE[cle][langue]


def page_de(chemin):
    """Inverse de route : "de/uebersetzung/vertraege/" donne ("traduction/contrats/", "de"), None si l'adresse est
    inconnue."""
    return _INVERSE.get(chemin)
