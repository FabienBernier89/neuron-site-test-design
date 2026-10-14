"""Aide commune aux tests : construire le site dans un dossier temporaire, sans toucher à docs/.

Les tests qui dépendent du mode (aperçu ou production) construisent avec une configuration forcée : la suite passe
quelle que soit la valeur de « apercu » dans src/data/config.json."""
import atexit
import contextlib
import io
import shutil
import sys
import tempfile
from pathlib import Path
from unittest import mock

ICI = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ICI))
import build  # noqa: E402


def construire(tmp, pages=("", "contact/"), config=None, patches=()):
    """Construit le site dans <tmp>/docs (en mémoire, sans sous-processus) avec les pages données et des réglages
    surchargés. patches : liste de mock.patch.object supplémentaires (ASSETS, SRC, menu.AJOUTS, post.DOSSIER...).
    Renvoie le dossier de sortie."""
    sortie = Path(tmp) / "docs"
    with contextlib.ExitStack() as pile:
        pile.enter_context(mock.patch.object(build, "DOCS", sortie))
        pile.enter_context(mock.patch.object(build, "CONFIG", {**build.CONFIG, **(config or {})}))
        pile.enter_context(mock.patch.object(build, "PAGES", list(pages)))
        for p in patches:
            pile.enter_context(p)
        pile.enter_context(contextlib.redirect_stdout(io.StringIO()))
        build.main()
    return sortie


_SITES = {}


def site_complet(**config):
    """Site complet (toutes les pages de src/pages), construit une seule fois par jeu de réglages et par processus de
    test, dans un dossier temporaire supprimé à la fin. Exemple : site_complet(apercu=False) pour la production
    simulée. Renvoie le dossier de sortie."""
    cle = tuple(sorted(config.items()))
    if cle not in _SITES:
        tmp = tempfile.mkdtemp(prefix="neuron-site-")
        atexit.register(shutil.rmtree, tmp, True)
        _SITES[cle] = construire(tmp, build.PAGES, config=config)
    return _SITES[cle]


def chemin(sortie, page):
    """Fichier d'une page dans un site construit ailleurs que docs/ (même règle que build.chemin_page)."""
    return sortie / build.chemin_page(page).relative_to(build.DOCS)
