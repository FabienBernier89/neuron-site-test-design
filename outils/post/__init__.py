"""Post-traitements des pages : un module par besoin, sans toucher au cœur du build.

Chaque module outils/post/<nom>.py expose `traiter(html: str, page: str) -> str`. Le build les applique à
chaque page (404 comprise, sous le nom « 404.html »), dans l'ordre alphabétique des noms de fichier : pour
passer en dernier, préfixer le nom par « z_ ». Un fichier dont le nom commence par « _ » est ignoré.

Le module reçoit la page complète, de <!DOCTYPE> à </html>, avant la résolution des liens : les liens s'y
écrivent {{ROOT}}contact/ ou {{ROOT}}fr/contact/, les ressources {{ROOT}}assets/... ; les images du site Neur.on
qu'il cite sont copiées dans la sortie. `page` est le chemin publié de la page (« corrext/plugin-word/ », « » pour
l'accueil). Un module qui ne change rien à une page renvoie `html` tel quel.
"""
import importlib.util
import sys
from pathlib import Path

DOSSIER = Path(__file__).resolve().parent
_modules = {}


def _charger(fichier):
    nom = f"{__name__}.{fichier.stem}"
    spec = importlib.util.spec_from_file_location(nom, fichier)
    module = importlib.util.module_from_spec(spec)
    sys.modules[nom] = module
    try:
        spec.loader.exec_module(module)
    except BaseException:
        sys.modules.pop(nom, None)  # un module à moitié chargé ne doit pas rester importable
        raise
    if not callable(getattr(module, "traiter", None)):
        raise TypeError(f"{fichier} : le post-traitement doit définir traiter(html, page)")
    return module


def modules(dossier=None):
    """Modules de post-traitement du dossier, dans l'ordre alphabétique (chargés une fois par état du dossier)."""
    fichiers = [f for f in sorted(Path(dossier or DOSSIER).glob("*.py")) if not f.name.startswith("_")]
    cle = tuple((str(f), f.stat().st_mtime_ns) for f in fichiers)
    if cle not in _modules:
        _modules[cle] = [_charger(f) for f in fichiers]
    return _modules[cle]


def appliquer(html, page, dossier=None):
    """Passe la page dans chaque post-traitement, du premier au dernier."""
    for module in modules(dossier):
        html = module.traiter(html, page)
    return html
