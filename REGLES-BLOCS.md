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
| Encart newsletter (`.nl-s`) | Sur les pages de lecture seulement (tout `ressources/`) ; ailleurs, l'appel « Demander une démo » reste seul en fin de page | `outils/post/newsletter.py` |
| Cartes à visuel de termes (`.cd .kv`, « Autres domaines ») | Visuels de même hauteur sur une ligne, termes centrés | `site.css`, sous-grille `.cd:has(> * > .v > .kv)` |
| Scène CHnell (paires, domaines) | Trois résultats réels relevés dans CHnell (filtre fedlex.admin.ch), la fenêtre est remplie sur toute sa hauteur | `paire_modele.py`, clés `a`, `a2`, `a3` des contenus |
| Surlignage dans les scènes | Bleu pour un terme mis en avant ; rouge et vert seulement pour une comparaison juste / faux | `site.css`, composants |

## Règles de rédaction des blocs

- Titres et sous-titres sur une ligne quand la largeur le permet ; sinon une coupure nette, jamais un mot seul.
- Une légende sous une scène tient en deux lignes. Au-delà, elle devient un tableau de lecture ou une carte
  conclusion et note (modèle : page LexMachina).
- Pages qui présentent des fonctionnalités : pas de focus sur DeepL. Ce n'est pas une interdiction de le nommer
  (la comparaison de la page LexMachina affiche « IA généraliste » par choix propre à ce bloc).
- Un visuel ne montre que des libellés réels (pages du site, sorties de moteur relevées, contenus relus de
  `src/data/contenus-v2/`).

## Corrections propres à une page (exceptions assumées)

- Tarifs : titre du hero légèrement au-dessus du texte de droite (`.tf-hg`), demande de Fabien du 2026-10-16.
- Pages de paires : forme cible des exemples en vert, piège en rouge barré (`paire.css`, `.pa-ex`), validé par Fabien
  le 2026-10-19 bien qu'il ne s'agisse pas d'une comparaison juste / faux.
