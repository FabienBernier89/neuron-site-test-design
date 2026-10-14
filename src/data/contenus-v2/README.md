# Contenus nouveaux de la V2

Ce dossier reçoit les textes écrits pour la V2 du site. Tout texte repris du site Neur.on actuel reste mot pour
mot dans les pages sources. Tout texte nouveau vit ici, jamais dans un composeur ni dans une page, pour que
Fabien puisse le relire.

## Format

Un fichier par lot : `A-plugin-word.json`, `B-schema.json`, etc.

```json
{"lot": "A", "entrees": [
  {"cle": "plugin-word.hero.s", "page": "corrext/plugin-word/", "texte": "...", "statut": "a_relire", "source": "Fabien, 2026-10-14"}
]}
```

- `cle` : unique dans tout le dossier, sous la forme `<page>.<bloc>.<n>`.
- `page` : chemin publié de la page, avec la barre finale (« » pour l'accueil).
- `texte` : le texte exact affiché, sans balise.
- `statut` : `a_relire` à l'écriture, `valide` quand Fabien a relu.
- `source` : d'où vient le fait ou la formulation (demande de Fabien et date, page du site actuel, base de connaissances).

## Règles

- Aucun chiffre, prix, nom de client ou libellé d'interface inventé : une source pour chaque fait.
- Jamais de tiret cadratin ni demi-cadratin.
- LexMachina est un « moteur de traduction neuronale ». Les moteurs tiers sont nommés sans numéro de version.
- Le test `tests/test_contenus_v2.py` contrôle ces règles. `tests/test_contenu.py` accepte ces textes dans les pages
  concernées.

## Utilisation

```python
import sys
sys.path.insert(0, "<racine du dépôt>")
from outils.contenus import texte, toutes

texte("plugin-word.hero.s")   # le texte, KeyError si la clé n'existe pas
toutes()                      # toutes les entrées, chacune avec son lot
```

`python3 outils/relecture.py` écrit `RELECTURE-CONTENUS.md` : les textes par lot, puis par page, avec leur statut
et leur source. Ce document est régénéré à la demande et n'est pas versionné.
