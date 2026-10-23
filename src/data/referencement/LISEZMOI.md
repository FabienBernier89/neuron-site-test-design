# Référencement figé des pages reprises de la V1

Ces fichiers remplacent la lecture, à chaque build, des pages du site Neur.on V1 (`Sites/neuron/docs/fr/…`).
Ils en sont la copie exacte, faite le 23 octobre 2026 par `outils/figer_referencement.py`. Le build ne dépend plus de la V1 pour le référencement.

## Format

- `<chemin de la page>/index.json` : une page reprise de la V1. L'accueil est `index.json` à la racine de ce dossier.
  - `source` : la page V1 d'origine.
  - `balises` : les balises de l'en-tête, telles quelles (canonique, hreflang de toutes les langues, Open Graph, Twitter, theme-color).
  - `donnees_structurees` : les blocs JSON-LD de la page V1, dans l'ordre.
- `_fil.json` : le libellé du fil d'Ariane de chaque niveau de chemin présent dans la V1.

Une page sans fichier ici est une page nouvelle : son référencement est tiré de sa méta (`build.seo_repli`).

## Ce que le build ajoute à la volée

Les fichiers ne sont jamais modifiés par le build. Il applique ses règles au moment d'assembler la page :

- hreflang : seules les langues construites restent, et `x-default` désigne la version française de la page (`build.adresse_x_default`) ;
- JSON-LD (`outils/donnees_structurees.py`) : `@context` sur chaque bloc, entité Organization unique (`src/data/organisation.json`), `dateModified`.

## Modifier le référencement d'une page

Modifier directement son `index.json`, puis ajouter la page à `MODIFIEES_DEPUIS_LE_GEL` dans `tests/test_referencement.py` (le test vérifie que les autres restent la copie exacte de la V1). Ne relancer `outils/figer_referencement.py` que pour reprendre une page de la V1 : il remplace les fichiers existants.
