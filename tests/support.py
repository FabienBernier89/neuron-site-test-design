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


def construire(tmp, pages=("", "contact/"), config=None, patches=(), langues=None):
    """Construit le site dans <tmp>/docs (en mémoire, sans sous-processus) avec les pages données et des réglages
    surchargés. langues : langues construites, par exemple ("fr", "de") ; équivaut à config={"langues": [...]}.
    patches : liste de mock.patch.object supplémentaires (ASSETS, SRC, menu.AJOUTS, post.DOSSIER...).
    Renvoie le dossier de sortie."""
    config = {**(config or {}), **({"langues": list(langues)} if langues else {})}
    sortie = Path(tmp) / "docs"
    with contextlib.ExitStack() as pile:
        pile.enter_context(mock.patch.object(build, "DOCS", sortie))
        pile.enter_context(mock.patch.object(build, "CONFIG", {**build.CONFIG, **config}))
        pile.enter_context(mock.patch.object(build, "PAGES", list(pages)))
        for p in patches:
            pile.enter_context(p)
        pile.enter_context(contextlib.redirect_stdout(io.StringIO()))
        build.main()
    return sortie


_SITES = {}


def site_complet(langues=None, **config):
    """Site complet (toutes les pages de src/pages), construit une seule fois par jeu de réglages et par processus de
    test, dans un dossier temporaire supprimé à la fin. Exemple : site_complet(apercu=False) pour la production
    simulée, site_complet(langues=("fr", "de")) pour construire aussi l'allemand. Renvoie le dossier de sortie."""
    cle = (tuple(langues) if langues else None, tuple(sorted(config.items())))
    if cle not in _SITES:
        tmp = tempfile.mkdtemp(prefix="neuron-site-")
        atexit.register(shutil.rmtree, tmp, True)
        _SITES[cle] = construire(tmp, build.PAGES, config=config, langues=langues)
    return _SITES[cle]


def chemin(sortie, page, langue="fr"):
    """Fichier d'une page dans un site construit ailleurs que docs/ (même règle que build.chemin_page)."""
    return sortie / build.chemin_page(page, langue).relative_to(build.DOCS)
