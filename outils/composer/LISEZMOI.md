# Composer les pages

Chaque `p_*.py` recompose une page de `src/pages/` à partir de la page FR publiée du site Neur.on
(`../neuron/docs/fr/`), sans changer un mot : il découpe les blocs et les habille avec les composants
de `comp.py`. Relancer un script après une mise à jour des textes du site, puis `python3 build.py`
et `python3 -m unittest` à la racine.

```
cd outils/composer && python3 p_accueil.py
```

Node est nécessaire pour lire les données de la démo Corrext.

## Pages complétées

`generique.py` compose toutes les autres pages publiées du site Neur.on, absentes de `src/pages`.

- Chaque type de bloc (hero, faits, situations, encadré, cartes, FAQ, termes, articles, glossaire, aide, etc.) a sa transposition.
- Un repli structuré traite les blocs rares.

```
cd outils/composer && python3 generique.py                 # toutes les pages manquantes
cd outils/composer && python3 generique.py aide/chnell/    # une page précise
```
