# Consigne d'adaptation (agents de traduction)

Tu traduis un lot de **segments** du site Neur.on du français vers la langue cible (`<langue>` : `de`, `it` ou `en`). Un segment est un texte français de la table de traduction (`src/langues/<langue>/segments.json`), repéré par sa clé : un titre, une phrase, un libellé, une réponse de FAQ. Décision de Fabien du 2026-10-27, valable pour l'allemand, l'italien et l'anglais : tu traduis directement depuis le français. LexMachina, le moteur de traduction neuronale de Neur.on, n'est pas conçu pour le rédactionnel d'un site web : aucune de ses sorties ne sert de base. Seule la terminologie validée dans CHnell (le glossaire de ton lot) est imposée. Ton travail : un texte que l'on croirait écrit directement pour le marché suisse de cette langue, sans rien perdre du sens, de l'exactitude juridique ni du référencement. Adapte les tournures de phrase d'une langue à l'autre chaque fois que c'est nécessaire : ne calque jamais la syntaxe française.

Tu ne travailles pas sur des pages ni sur des fichiers du site. Tu reçois des propositions de segments et tu rends des propositions de segments.

## Ce que contient ton lot

Le lot est un fichier JSON préparé par `python3 -m outils.i18n preparer <langue>` hors du dépôt : une liste de `{cle, fr, contexte_v1, glossaire}`. Pour chaque segment :

- `cle` : l'identifiant du segment (jamais modifié) ;
- le texte français (FR), avec ses marqueurs ;
- le contexte V1 quand la mémoire des traductions validées en a un : `nature` (morceau d'un texte V1 plus long, variante de balisage, correction V2, recomposition), `fr_complet` (le texte V1 entier) et `trad_complete` (sa traduction validée par les traducteurs). Pars de cette traduction pour le morceau concerné : c'est la formulation que les traducteurs ont déjà approuvée. Un segment sans contexte n'a pas d'équivalent V1 ;
- les lignes utiles du glossaire de projet : pour chaque terme français présent dans le segment, l'équivalent vérifié dans CHnell. Ces équivalents ne changent pas.

Rien d'autre n'est autorisé comme source : ni mémoire personnelle d'une formulation, ni texte pris sur un autre site. Aucun outil de traduction tiers, aucun accès réseau : tu travailles avec ton lot, le guide et ce brief, rien d'autre.

## À lire avant de commencer

1. Le guide de style de la langue : `outils/i18n/guides/guide-<langue>.md`. Il prime sur tout le reste, sauf sur les règles absolues ci-dessous. Ses renvois à des fichiers de la V1 (base terminologique, table des adresses, consignes) sont sans objet pour toi : ton lot porte déjà les lignes utiles du glossaire, et tu ne touches à aucune adresse.
2. Les règles absolues ci-dessous.

## Ce que tu rends

Un fichier JSON, `scratchpad/<lot>/propositions.json` (un sous-dossier par agent), liste de propositions, une par segment du lot. Les lots, le scratchpad et les lignes du glossaire restent hors du dépôt public : rien de tout cela n'est copié dans le dépôt, ni dans une note, ni dans un commit.

```json
[{"cle": "3f2a9c0d1e2b4a5f", "trad": "Demo anfragen", "note": ""}]
```

- `cle` : celle du segment ;
- `trad` : le texte complet adapté, avec ses marqueurs ;
- `note` : vide, ou une remarque courte pour le relecteur (terme incertain, choix motivé, doute sur le sens du français). Les notes ne vont jamais dans la table, elles remontent au traducteur expert.

Tu ne modifies rien d'autre : ni la table, ni les sources, ni les gabarits.

## Les marqueurs

Les balises en ligne (liens, gras, retours à la ligne, jetons) sont remplacées dans le texte par des marqueurs : `{1}…{/1}` entoure un passage, `{2}` seul remplace un élément sans contenu (retour à la ligne, jeton). Tu les gardes tels quels :

- les mêmes numéros, chacun exactement une fois (`{n}` et `{/n}` pour une paire, `{n}` seul sinon), l'ouvrant avant le fermant ;
- tu traduis le texte entre les marqueurs, jamais les marqueurs ;
- tu places chaque marqueur autour du passage qui correspond à celui du français, même si l'ordre des mots change ;
- pas d'espace ajoutée à l'intérieur d'une paire quand le français n'en a pas (`{1}Texte{/1}`, pas `{1} Texte {/1}`) ;
- tu ne touches pas à ce qui est caché dans les marqueurs : adresses, classes, jetons, valeurs techniques.

## Comment adapter

- Pars du sens du FR, pas de ses mots. Évite toute tournure calquée (exemple DE : « Konsultieren Sie die Datenschutzerklärung » devient « Lesen Sie die Datenschutzerklärung »). Un calque se repère à un lecteur suisse de la langue qui devinerait la traduction.
- Phrases courtes, une idée par phrase, ton expert et sobre de la marque. Aucun superlatif sans preuve, aucune affirmation ajoutée, aucune donnée inventée.
- Terminologie juridique : celle des textes officiels suisses de la langue (glossaire du lot, guide, Fedlex). Abréviations des lois dans la langue (CO = OR en allemand). En cas de doute sur un terme, garde l'équivalent officiel et signale-le dans `note`.
- Formats suisses : CHF 15'000 en allemand et en italien (apostrophe), 15,000 en anglais (virgule), dates selon le guide.
- SEO : quand le lot signale qu'un segment est le `title` d'une page, il fait de 30 à 62 caractères et porte la requête principale de la page dans la langue (carte des requêtes du guide) ; la `description` fait de 110 à 160 caractères et dit ce que la page apporte. Les titres h1 et h2 restent naturels et porteurs des requêtes, jamais bourrés de mots-clés.
- GEO : garde les réponses directes en tête de section, les chiffres sourcés, les FAQ, les blocs « En bref ». Une question de FAQ doit être une vraie question d'un lecteur de ce marché, dans la langue.
- Longueur : les mots composés allemands sont longs. Un titre de tuile, de bouton ou de menu doit tenir sur la même place que le français ; si ce n'est pas possible sans trahir le sens, dis-le dans `note`.
- Glossaire du site : le mot-vedette et ses équivalents ne changent pas ; seuls le résumé, le chapeau, la définition et les textes qui l'entourent se traduisent. La base légale s'écrit comme la loi dans la langue (« art. 201 CO » devient « Art. 201 OR » en allemand).
- Blog et actualités : dates d'origine, noms et anonymisations inchangés. Les actualités historiques gardent leurs faits tels quels.

## Règles absolues

Elles priment sur le guide et sur toute envie de style.

- Aucun tiret cadratin (U+2014) ni demi-cadratin (U+2013), nulle part, même dans une note. Emploie la virgule, le deux-points, la parenthèse ou le trait d'union.
- Allemand : standard suisse, ss, jamais ß (sauf si le segment FR contient lui-même « ß »), milliers avec apostrophe (15'000), registre « Sie ». Italien : milliers avec apostrophe (convention du site), registre « voi ». Anglais : britannique, milliers avec virgule (15,000), « you » sobre.
- Jamais traduits : Neur.on, Corrext, LexMachina, CHnell, Fast lookup CHnell, Highly sensitive content, Infomaniak, Neur.on AI Solutions SA (jamais « AG »). Chaque marque apparaît autant de fois que dans le français, à la même casse.
- Libellés de l'application, en anglais et inchangés : Text translation, File translation, PDF to Word, Rephrasing, Fast Lookup, Translation engine, Detect language, Show more results, Close, Download, Generate more, Alternatives, Light review, Full review, Double review & certified translation, Attorney-Client privilege, Project manager, Admin, Member, Formal legal, Financial, Simplified, Formal, Informal, Shorten.
- Neur.on et son moteur : LexMachina est le moteur de traduction neuronale de Neur.on, jamais un LLM ni un modèle de langage (sauf dans une actualité historique, à laisser telle quelle). Corrext est la plateforme. Le site ne nomme aucune autre marque que celles de Neur.on et ne fait allusion ni à une société mère, ni à un groupe, ni à une opération de reprise : la liste des termes interdits est dans `src/langues/proteges.json` et la fusion à blanc (plus bas) refuse tout segment qui en contient un. Les moteurs tiers se nomment sans numéro de version.
- Rien d'inventé : pas de texte sans équivalent dans le français du segment, pas de prix, pas de nom de client, pas de chiffre, de loi ou de jurisprudence qui n'y figurent pas. Un doute sur le sens du français va dans `note`, pas dans le texte.
- Un segment que tu rends reste une traduction non relue (statut `adapte`). Aucune traduction ne part en production sans la relecture d'un traducteur expert (statut `relu`) : ne présente jamais ta traduction comme relue, dans une note ou ailleurs.

### Décisions et rulings qui touchent les segments

- **Ruling 14 : `lang="fr"` n'est jamais traduit.** Les textes placés sous un ancêtre `lang="fr"` explicite (sources françaises des démos, équivalents français du glossaire) gardent le français dans toutes les langues. Ils ne sont pas dans ton lot : ne propose rien pour eux, et si un texte français de ton lot ressemble à l'un d'eux, signale-le dans `note`.
- **Écrans de l'application en anglais.** Les écrans de Corrext et de CHnell reproduits sur le site montrent l'interface réelle de l'application, en anglais dans toutes les langues du site (barres, menus, boutons, panneau de Word, commande d'extraits du registre), comme les sorties de démo en anglais. Ces textes portent `lang="en"` : ils ne sont pas dans ton lot. Si un segment de ton lot est pourtant un libellé d'interface en anglais, rends-le identique au français et dis-le dans `note` : le relecteur le confirmera tel quel. Les écrans en français (parcours de devis, onglets « Projets ») se traduisent comme le reste.
- **Ruling 22 : les liens Fedlex suivent la langue de la page.** Les adresses sont dans les marqueurs et tu n'y touches pas : le site les adapte à la langue de la page (en anglais, le texte allemand quand Fedlex ne publie pas l'anglais, comme la V1). Si le texte d'un lien nomme la langue du texte de loi, aligne-le sur cette règle.
- **V11 : titre anglais de l'accueil.** Le titre de la page d'accueil en anglais est la baseline de la marque, en casse de phrase britannique : « AI-powered translation software for legal, tax and finance ». Si le titre est coupé en deux marqueurs, la coupe suit le sens (« AI-powered translation software », puis « for legal, tax and finance »). En allemand et en italien, le titre garde la traduction du titre actuel, qui est déjà celle de la V1.

## Vérification avant de rendre

Lance la fusion à blanc, qui applique tes propositions à une copie de la table sans rien écrire :

```
python3 -m outils.i18n fusionner <langue> scratchpad/<lot>/propositions.json --simuler
```

Chaque proposition refusée est listée avec sa raison : clé inconnue, marqueurs faux, tirets, ß, marque modifiée, terme interdit, milliers séparés par une espace (allemand, italien : 15'000), entrée déjà relue ou validée. Corrige tous les refus. Traite aussi les avertissements de terminologie (un terme du glossaire absent de ta traduction), sauf choix motivé, que tu écris dans `note`.

Ne lance pas `build.py`, n'écris pas dans `src/`, ne commite pas. D'autres agents travaillent en même temps dans le dépôt : git en lecture seule (status, diff, log, show), jamais reset, checkout, restore, stash ni clean, qui effaceraient leur travail. L'appelant applique la fusion pour de bon, puis rejoue `controler <langue>`.

## Rapport (en français, court)

- Nombre de segments traités.
- Choix de traduction marquants (tournures adaptées, termes), par grandes catégories, avec 3 exemples.
- Termes ou formulations incertains, à soumettre à un traducteur expert (ce sont aussi tes `note`).
- Résultat de la fusion à blanc : propositions acceptées, refusées, avertissements.

## Passe d'harmonisation des textes V1

Décision de Fabien du 2026-10-27 : pour un style rédactionnel homogène sur tout le site, les textes repris de la V1 (validés par les traducteurs le 2026-10-05) sont relus avec les mêmes exigences que les textes neufs. Le lot vient de `python3 -m outils.i18n preparer <langue> --v1 [--pages ...]` : une liste de `{cle, fr, v1, glossaire}`, où `v1` est la traduction actuelle.

- Tu ne réécris un texte V1 que s'il en a besoin : tournure calquée sur le français, ton ou registre différent du reste du site (guide de la langue), terme du glossaire non respecté, erreur de sens. Jamais pour une simple préférence : un texte V1 juste et naturel reste tel quel, il garde sa validation.
- Les traducteurs ont validé la précision juridique de la V1 : ne la défais pas. Une réécriture garde les termes, les références et les nuances juridiques du texte V1, sauf erreur que tu motives dans `note`.
- Tu rends `scratchpad/<lot>/harmonisation.json`, au format des propositions, **seulement pour les textes réécrits**. Chacun repart dans la file du traducteur expert (statut `adapte`).
- Fusion à blanc : `python3 -m outils.i18n fusionner <langue> scratchpad/<lot>/harmonisation.json --harmonisation --simuler`.
- Rapport : nombre de textes réécrits sur le total du lot, par motif, avec 3 exemples avant et après.

## Relecture croisée (second agent)

Un second agent relit les propositions du premier. C'est le second regard : un relecteur juriste-linguiste exigeant, de langue maternelle `<langue>`, qui connaît le droit suisse. Il reçoit le même lot, les mêmes règles et le même guide, plus `propositions.json`.

Il vérifie, segment par segment :

1. **Fidélité** : rien d'ajouté, rien d'oublié, rien de déformé. Les chiffres, les dates, les références d'articles et les noms sont identiques. Une nuance juridique du FR est rendue.
2. **Terminologie** : termes juridiques des textes officiels suisses de la langue, abréviations des lois de la langue, équivalents du glossaire inchangés, marques intactes.
3. **Naturel** : un lecteur suisse de la langue ne devine pas une traduction. Pas de calque, pas de répétition, registre du guide (DE « Sie », IT « voi », EN britannique « you »).
4. **SEO et GEO** : `title` de 30 à 62 caractères et `description` de 110 à 160, avec la requête de la page ; réponses directes en tête de section ; FAQ crédibles pour ce marché.

Il écrit `scratchpad/<lot>/relecture.json`, au même format que les propositions et **seulement pour les segments qu'il corrige** (`trad` : le texte corrigé en entier ; `note` : la raison, avec le contrôle concerné). L'appelant applique `propositions.json` puis `relecture.json` avec `fusionner`. Son rapport donne le nombre de corrections par contrôle, les 5 plus importantes avec avant et après, ce qui reste à trancher par un traducteur expert, et le résultat de la fusion à blanc.
