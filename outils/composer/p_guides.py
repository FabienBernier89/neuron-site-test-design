"""Hub des guides : relie les guides du site actuel.

La composition générique de la page remplaçait les deux fiches de guide (titre, résumé, lien « Lire le guide ») par des
tuiles sans lien : aucun guide n'était atteignable depuis le hub. Ce script remplace ces tuiles par des cartes reliées,
avec les textes de la page actuelle, sans changer le reste de la page. Rejouable.
"""
import re
from pathlib import Path

from source import *
from comp import cartes

P = "ressources/guides/"
t = liens(charger(P), P)
fiches = blocs(bloc(t, "div", "rl-grid"), "article", "rl-card")
assert len(fiches) == 2, len(fiches)
items = []
for f in fiches:
    lien = bloc(f, "a", "feat-link")
    items.append((brut(bloc(f, "h3")), brut(bloc(f, "p")), (txt(lien), re.search(r'href="([^"]+)"', lien).group(1)), ""))
cartes_guides = cartes(items).replace('<div class="cd">', '<div class="cd cd-guides">', 1)

fichier = RACINE / "src/pages" / P / "index.html"
page = fichier.read_text(encoding="utf-8")
try:
    ancien = bloc(page, "div", "cd-guides")  # déjà reliée : on remplace les cartes
except ValueError:
    ancien = bloc(page, "div", "tl")  # tuiles de la composition générique
page = page.replace(ancien, cartes_guides, 1)
fichier.write_text(page, encoding="utf-8")
print("hub des guides écrit")
