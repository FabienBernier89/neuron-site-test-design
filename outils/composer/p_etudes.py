"""Page Études : le bloc de texte « Ce que nous nous interdisons » en trois tuiles titrées (retour de Fabien du 2026-10-16).

Les trois paragraphes de la page actuelle restent mot pour mot ; seuls les titres sont nouveaux
(src/data/contenus-v2/L-ressources.json, à relire). La publication et « Pour aller plus loin » sont mis en forme par
outils/post/fonctionnalites.py (cartes illustrées). Rejouable.

    cd outils/composer && python3 p_etudes.py
"""
import html as H
import re
import sys
from pathlib import Path

RACINE = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(RACINE))
from outils.contenus import texte  # noqa: E402
from comp import tuiles  # noqa: E402

fichier = RACINE / "src/pages/ressources/etudes/index.html"
page = fichier.read_text(encoding="utf-8")
paras = re.findall(r'<p class="para">(.*?)</p>', page, re.S)
if paras:
    assert len(paras) == 3, len(paras)
    titres = [H.escape(texte(f"etudes.regle{i}.titre"), quote=False) for i in (1, 2, 3)]
    bloc = tuiles([(None, t, p) for t, p in zip(titres, paras)], "tl txt")
    debut = page.index('<p class="para">')
    fin = page.index("</p>", page.rindex('<p class="para">')) + len("</p>")
    page = page[:debut] + bloc + page[fin:]
    fichier.write_text(page, encoding="utf-8")
print("études écrites")
