# Règles des blocs communs

Chaque type de bloc a une seule mise en page, la même sur tout le site. Une correction validée par Fabien sur un
bloc s'applique à tous les blocs du même type : elle vit dans la feuille partagée (`assets/site.css`,
`assets/composants/*.css`) ou dans un post-traitement (`outils/post/`), jamais dans une classe propre à une page.
Le test `tests/test_regles_blocs.py` vérifie les règles ci-dessous.

| Bloc | Règle | Où elle vit |
|---|---|---|
| Hero à deux colonnes (`.hero-g`) | Titre calé en haut, à la hauteur du texte de droite | `site.css`, `.hero-g` |
| Tuiles de texte (`.tl.txt`) | Espace de 8 px sous le titre, texte en 14 px, plus petit que le titre | `site.css`, `.tl.txt p` |
| Tuiles chiffrées (`.tl` avec `.n`) | Chiffre sur une ligne de hauteur fixe, unité accolée (« 30 Langues »), textes alignés d'une tuile à l'autre | `site.css`, `.tl .n` |
| Cartes de liens vers une page outil ou ressource | Grand visuel animé, titre, texte, lien ; trois cartes au plus sur une ligne, jamais de 2 x 2 ; deux cartes : deux grandes colonnes | `outils/post/fonctionnalites.py` |
| Cartes de texte seul (`.cd`) | Aérées, sans trait d'accent en tête de bloc | `site.css`, `.cd` |
| Scènes animées | Aucune pause au survol, jauge de déroulé discrète en bas | `assets/sim.js` |
| Surlignage dans les scènes | Bleu pour un terme mis en avant ; rouge et vert seulement pour une comparaison juste / faux | `site.css`, composants |

## Règles de rédaction des blocs

- Titres et sous-titres sur une ligne quand la largeur le permet ; sinon une coupure nette, jamais un mot seul.
- Une légende sous une scène tient en deux lignes. Au-delà, elle devient un tableau de lecture ou une carte
  conclusion et note (modèle : page LexMachina).
- Une comparaison de qualité ne nomme pas le moteur tiers : « IA généraliste ».
- Un visuel ne montre que des libellés réels (pages du site, sorties de moteur relevées, contenus relus de
  `src/data/contenus-v2/`).

## Corrections propres à une page (exceptions assumées)

- Tarifs : titre du hero légèrement au-dessus du texte de droite (`.tf-hg`), demande de Fabien du 2026-10-16.
