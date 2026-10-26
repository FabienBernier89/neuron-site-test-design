# Guide de style allemand (Suisse) · site neur-on.ai

Ce guide s'applique à toutes les pages DE du site : première traduction Corrext, adaptation, relecture. Il complète la base terminologique `src/i18n/termes-de.json` et la table des adresses `src/routes.json` (version lisible : `docs-traduction/routes-de.md`).

Ordre de priorité : les règles absolues (section 1), puis ce guide, puis le brouillon LexMachina. En cas de doute sur un terme juridique, le texte officiel suisse en allemand (Fedlex) l'emporte sur tout le reste.

## 1. Règles absolues

1. **Allemand standard suisse** (Schweizer Hochdeutsch). Ni dialecte, ni allemand d'Allemagne ou d'Autriche.
2. **ss, jamais d'eszett** : Strasse, Massnahmen, gemäss, ausschliesslich, grösser, Schweizer Recht.
3. **« Sie »**, toujours, avec la majuscule (Sie, Ihr, Ihnen). Jamais « du ». Les appels à l'action sont à l'impératif de politesse : « Testen Sie », « Laden Sie Ihre Datei hoch ».
4. **Noms jamais traduits ni modifiés** : Neur.on, Corrext, LexMachina, CHnell, Fast lookup CHnell, Highly sensitive content, Infomaniak. Casse et orthographe intactes.
   - Pas de génitif collé (« Correxts ») : « die Funktionen von Corrext ».
   - Pas de mot composé avec un nom de produit : « die Plattform Corrext », « der Übersetzungsmotor LexMachina », et non « Corrext-Plattform ».
   - Le mode s'écrit « der Modus Highly sensitive content ». Là où le FR emploie la forme courte « mode Highly sensitive », garder la forme courte : le contrôle compte les noms de produits segment par segment.
   - La raison sociale reste « Neur.on AI Solutions SA » (pas « AG »).
5. **LexMachina** est un « neuronaler Übersetzungsmotor », un « Übersetzungsmotor » ou un « neuronales Übersetzungsmodell ». Jamais « LLM », « Sprachmodell » ni « Chatbot ». Seule exception : les actualités historiques, qui gardent leurs faits et leurs mots (par exemple les AI Days 2025).
6. **Noms interdits** : toute autre marque que celles de Neur.on, « Gruppe », « Übernahme », « Zusammenschluss » ou toute allusion à une opération de reprise. Aucun prix, aucun montant en CHF, aucun nom de client.
7. **Moteurs tiers sans numéro de version** : DeepL Pro, Azure OpenAI GPT, ChatGPT, Claude.
8. **Aucun tiret cadratin ni demi-cadratin** (U+2014, U+2013), alors que l'allemand en use beaucoup. À la place : deux-points, virgule, parenthèses, point médian « · ». Les intervalles s'écrivent avec « bis » (« Art. 80 bis 84 SchKG ») ou avec le trait d'union simple (« 2025-2028 »).
9. **Aucun superlatif sans preuve** : pas de « der beste », « führend », « einzigartig », « revolutionär », « modernste ». Un chiffre sourcé vaut mieux qu'un adjectif.
10. **Phrases courtes, une idée par phrase.** L'allemand pousse aux chaînes de noms : préférer le verbe (« Sie übersetzen » plutôt que « die Durchführung der Übersetzung »). Au-delà de 20 mots, couper.
11. **Aucune tournure qui trahit un texte écrit par une IA.** À proscrire :
    - « In der heutigen schnelllebigen Welt », « Tauchen Sie ein in », « Entdecken Sie die Welt von » ;
    - « nahtlos », « ganzheitlich », « Gamechanger », « auf ein neues Level heben », « im Handumdrehen », « massgeschneidert » (on écrit « individuell ») ;
    - « Es ist wichtig zu beachten, dass », « Nicht nur …, sondern auch … » à répétition ;
    - les séries de trois adjectifs, les questions rhétoriques en cascade, un « Fazit: » au bout de chaque section.
12. **Aucune phrase reprise d'un site du groupe** (contrôle par séquences de 8 mots).

## 2. Formats suisses

| Élément | Règle | Exemple |
|---|---|---|
| Milliers | apostrophe | 15'000 · 1'500 |
| Montants (s'il en faut un) | « CHF » avant le nombre | CHF 15'000 |
| Dates | jour, point, mois en toutes lettres | 2. Oktober 2026 · format court 2.10.2026 |
| Mois | forme suisse et allemande standard | Januar (jamais « Jänner ») |
| Pourcentages | espace insécable avant % | 5 % · 100 % |
| Guillemets | guillemets suisses, sans espace intérieur | «Text», et à l'intérieur ‹Text› |
| Articles de loi | Art., Abs., lit., Ziff., abréviation allemande | Art. 104 Abs. 1 OR · Art. 305bis StGB · Art. 80 ff. SchKG |
| Recueils | SR, AS, BBl, BGE | SR 220 · BGE 145 III 72 |
| Ordre des langues | allemand en premier | Deutsch, Französisch, Italienisch und Englisch |
| Villes | nom allemand dans le texte, forme postale dans l'adresse | Freiburg, Genf, Zürich, St. Gallen, Bern, Luzern · « Place de la Gare 15, 1700 Fribourg » |

Pour Fribourg : « Freiburg » dans le texte. À la première mention sur les pages À propos et Presse, écrire « Freiburg (Schweiz) » : un lecteur ou un moteur de réponse peut confondre avec Freiburg im Breisgau.

## 3. Vocabulaire suisse et non allemand

| Suisse (à employer) | Allemagne ou Autriche (à éviter) |
|---|---|
| Bundesgericht, BGE | Bundesgerichtshof, BGH |
| Handelsregister, Handelsregisterauszug, UID | Firmenbuch, Handelsregisternummer |
| Treuhand, Treuhänder, Treuhandunternehmen | Steuerberater, Steuerkanzlei |
| Kanton, kantonal | Bundesland |
| Anwaltskanzlei, Kanzlei, Rechtsanwältin und Rechtsanwalt | Sozietät |
| Offerte | Angebot, Kostenvoranschlag |
| Verwaltungsrat | Vorstand, Aufsichtsrat |
| Generalversammlung, Traktandenliste | Hauptversammlung, Tagesordnung |
| Revisionsstelle, ordentliche und eingeschränkte Revision | Abschlussprüfer, Wirtschaftsprüfung |
| Aktienkapital, Statuten | Grundkapital, Satzung |
| Betreibung, Zahlungsbefehl, Rechtsvorschlag, Rechtsöffnung | Zwangsvollstreckung, Mahnbescheid, Widerspruch |
| Erfolgsrechnung, Jahresrechnung | Gewinn- und Verlustrechnung, Jahresabschluss |
| Mehrwertsteuer (MWST), Verrechnungssteuer | Umsatzsteuer (USt), Kapitalertragsteuer |
| Personendaten, DSG | personenbezogene Daten, BDSG |
| Gesamtarbeitsvertrag (GAV) | Tarifvertrag |
| Rechtsschrift | Schriftsatz |
| innert 30 Tagen, allfällig (usage juridique suisse, à préférer) | innerhalb von 30 Tagen, etwaig |
| Bundesrat (le gouvernement), Departement | Bundesregierung, Ministerium |

Métier de la traduction :
- devis : **Offerte** ; page standard : **Normseite** ; délai de livraison : **Lieferfrist** ;
- relecture juridique : **juristisches Lektorat** ; post-édition : **Post-Editing** ;
- traduction certifiée : **beglaubigte Übersetzung** ; notariée : **notariell beglaubigt** ; apostillée : **mit Apostille** ;
- niveau 3 de relecture (convention du site, fixée le 2 octobre 2026) :
  - le libellé exact de l'application reste en anglais : « Double review & certified translation », partout où le FR le cite ainsi (titres, tableaux, vignettes) ;
  - dans le texte courant, quand le FR écrit « Double review et traduction certifiée », « Double review avec certificat » ou « Double review certifiée » : **Double review und beglaubigte Übersetzung** (jamais « Doppeltes Lektorat », « mit Zertifikat » ni « and certified translation ») ;
  - le document signé par l'agence, qui atteste l'exactitude : **Bescheinigung** (pas « Zertifikat », réservé à la certification ISO 27001) ;
  - le niveau 4 : **Beglaubigung und Apostille**, notarielle Beglaubigung de la signature puis Apostille ;
- juriste-linguiste : **Rechtslinguistin, Rechtslinguist** ; traducteur juridique : **juristische Übersetzerin, juristischer Übersetzer** ;
- mémoire de traduction : **Translation Memory**.

Les libellés anglais de l'application (File translation, PDF to Word, Rephrasing, Light review, Full review, Attorney-Client privilege notice) restent en anglais, comme sur le site FR. Dans le centre d'aide, si Corrext existe en interface allemande, reprendre ses libellés exacts, relevés en lecture seule dans l'application.

Écriture inclusive : formes doubles (« Anwältinnen und Anwälte ») ou neutres (« Fachleute », « Mitarbeitende », « Juristinnen und Juristen »). Ni astérisque, ni deux-points, ni tiret bas de genre, comme dans les textes de la Confédération.

## 4. Lois et abréviations

Toujours l'abréviation allemande officielle, vérifiée dans Fedlex (`jolux:titleShort` de l'expression allemande). Liste complète dans `termes-de.json` (type « loi »). Les plus fréquentes sur le site :

| FR | DE | FR | DE |
|---|---|---|---|
| CO | OR | LBA | GwG |
| CC | ZGB | LIFD | DBG |
| LP | SchKG | LPD | DSG |
| CPC | ZPO | LTF | BGG |
| CPP | StPO | LB | BankG |
| CP | StGB | LSFin | FIDLEG |
| LDIP | IPRG | LFINMA | FINMAG |
| LCA | VVG | LFus | FusG |
| LIA | VStG | LTVA | MWSTG |
| ORC | HRegV | Cst. | BV |
| RS | SR | FF | BBl |
| RO | AS | ATF | BGE |

« nLPD » devient « nDSG » dans un texte marketing ; dans une référence juridique, écrire « DSG ». « RGPD » devient « DSGVO ».

Trois mots-vedettes du glossaire ne sont pas la forme du texte officiel. Les fiches gardent leur mot-vedette, mais le corps du texte cite la forme officielle quand il renvoie à la loi :

| Mot-vedette du glossaire | Texte officiel (OR) |
|---|---|
| Schuldnerverzug | Verzug des Schuldners (Art. 102) |
| Überstunden | Überstundenarbeit (Art. 321c) |
| fristlose Kündigung | fristlose Auflösung (Art. 337) |

## 5. Ton, titres et SEO

- **Ton** : expert, précis, sobre, ancré en Suisse. On montre (où sont les données, qui relit, quelle loi), on ne vante pas.
- **Structure des accroches** : garder la forme du FR, « Nom. Promesse » (« Anwaltskanzleien. Ein Dossier übersetzen, ohne dass es die Schweiz verlässt »).
- **title** : 30 à 62 caractères, la requête principale en tête, puis « · Neur.on ». Exemple glossaire : « Verzugszins: Definition und Übersetzung · Neur.on ».
- **description** : 110 à 160 caractères, ce que la page apporte, sans formule creuse.
- **h1 et h2** : naturels, porteurs de la requête, jamais une liste de mots-clés.
- **FAQ** : de vraies questions de lecteurs alémaniques, formulées comme on les tape ou les pose à un assistant (« Darf ich vertrauliche Verträge mit DeepL übersetzen? »). Réponse directe dans la première phrase.
- **Mots longs** : la page doit tenir à 375 px. Dans un h1, un bouton ou un menu, éviter les composés de plus de 20 lettres. Préférer « Übersetzung von Handelsregisterauszügen » à « Handelsregisterauszugsübersetzung ».
- **Composés** : trait d'union pour les composés avec un sigle ou un chiffre (« ISO-27001-zertifiziert », « KI-Übersetzung », « M&A-Transaktion »).

## 6. Vingt formulations maison, FR → DE

| # | Type | FR (site) | DE | Ce que l'exemple montre |
|---|---|---|---|---|
| 1 | Accroche, accueil | Votre solution de traduction par IA pour le droit, la fiscalité et la finance | Ihre KI-Übersetzungslösung für Recht, Steuern und Finanzen | Requête « KI-Übersetzung Recht » en tête, sans adjectif. |
| 2 | Accroche, Corrext | Corrext : reprenez le contrôle de vos traductions | Corrext: Holen Sie die Kontrolle über Ihre Übersetzungen zurück | Pas d'espace avant les deux-points en allemand. |
| 3 | Accroche, LexMachina | LexMachina. Le moteur qui connaît les lois qu'il traduit | LexMachina. Der Übersetzungsmotor, der die Gesetze kennt, die er übersetzt | « Übersetzungsmotor », jamais « LLM ». |
| 4 | Accroche, avocats | Cabinets d'avocats. Traduire un dossier sans jamais le sortir de Suisse | Anwaltskanzleien. Ein Dossier übersetzen, ohne dass es die Schweiz verlässt | « Anwaltskanzlei » et « Dossier », usage suisse. |
| 5 | Chapeau, avocats | Quatre cents pages de pièces à comprendre avant l'audience, un contrat à livrer ce soir, un mémoire à citer au mot près. | Vierhundert Seiten Akten vor der Verhandlung. Ein Vertrag, der heute Abend fertig sein muss. Eine Rechtsschrift, die wörtlich zu zitieren ist. | Une énumération longue devient trois phrases ; « mémoire » se dit « Rechtsschrift ». |
| 6 | Accroche, fiduciaires | Fiduciaires et conseil. Documents d'entreprise traduits et certifiés | Treuhand und Beratung. Unternehmensdokumente übersetzt und beglaubigt | « Treuhand », et « beglaubigt » pour une traduction certifiée. |
| 7 | Accroche, sécurité | Souveraineté des données. Où va votre document, exactement, et qui peut le lire | Datensouveränität. Wohin Ihr Dokument genau geht und wer es lesen kann | Question indirecte, sans point d'interrogation. |
| 8 | Bouton | Demander une démo | Demo anfragen | Verbe à l'infinitif en fin de bouton. |
| 9 | Bouton | Essayer Corrext en direct | Corrext live testen | Court : tient sur un bouton à 375 px. |
| 10 | Bandeau | Essayez Corrext, sans inscription | Testen Sie Corrext ohne Registrierung | Impératif de politesse, pas de virgule superflue. |
| 11 | Sécurité | Mode Highly sensitive : stockage et traitement exclusivement en Suisse | Modus Highly sensitive content: Speicherung und Verarbeitung ausschliesslich in der Schweiz | Forme du nom du mode identique au FR ; « ausschliesslich » avec ss. |
| 12 | Sécurité | Hébergement 100% suisse · Infomaniak | Hosting zu 100 % in der Schweiz · Infomaniak | Espace avant %, point médian conservé. |
| 13 | Sécurité | Hors CLOUD Act. Société suisse, infrastructure suisse : le stockage de vos projets ne relève pas du US CLOUD Act. | Ausserhalb des CLOUD Act. Schweizer Unternehmen, Schweizer Infrastruktur: Die Speicherung Ihrer Projekte fällt nicht unter den US CLOUD Act. | Majuscule après les deux-points devant une phrase complète. |
| 14 | Sécurité | Aucun entraînement sur vos contenus. LexMachina apprend de corpus juridiques et financiers suisses publics, jamais de vos dossiers. | Kein Training mit Ihren Inhalten. LexMachina lernt aus öffentlichen Schweizer Rechts- und Finanztexten, nie aus Ihren Dossiers. | Composé suspendu « Rechts- und Finanztexte » plutôt que « juristische und finanzielle Korpora ». |
| 15 | Sécurité | Le certificat et le périmètre sont remis sur demande, pour votre dossier fournisseur. | Zertifikat und Geltungsbereich erhalten Sie auf Anfrage für Ihr Lieferantendossier. | Tournure active, le lecteur est sujet. |
| 16 | Sécurité | Votre politique s'applique au moment du choix, pas dans une charte oubliée | Ihre Richtlinie greift im Moment der Wahl, nicht in einem vergessenen Reglement | « Reglement », mot suisse. |
| 17 | Glossaire | Les lois fédérales suisses sont publiées en allemand, en français et en italien, et les trois versions font foi. L'équivalence ci-contre n'est donc pas une traduction d'usage : c'est le terme employé par le texte officiel lui-même. | Die Bundesgesetze werden auf Deutsch, Französisch und Italienisch veröffentlicht, und alle drei Fassungen sind gleichermassen verbindlich. Die nebenstehende Entsprechung ist also keine Übersetzung aus der Praxis, sondern der Begriff des amtlichen Textes selbst. | « amtlich » pour « officiel » ; « gleichermassen » avec ss. |
| 18 | Glossaire | Source : Fedlex, Code des obligations. Dans Corrext, ce segment et ceux qui l'entourent s'affichent dans Fast lookup CHnell, chacun avec sa référence. | Quelle: Fedlex, Obligationenrecht. In Corrext erscheinen dieses Segment und die umliegenden Segmente in Fast lookup CHnell, jeweils mit Fundstelle. | « Fundstelle » pour une référence légale. |
| 19 | Glossaire | L'intérêt moratoire est dû dès que le débiteur est en demeure de payer une somme d'argent, indépendamment de tout dommage prouvé. | Der Verzugszins ist geschuldet, sobald der Schuldner mit der Zahlung einer Geldschuld in Verzug ist, unabhängig von einem nachgewiesenen Schaden. | Reprend les mots de l'Art. 104 OR (« mit der Zahlung einer Geldschuld in Verzug »). |
| 20 | Glossaire | Classés par terme allemand. Le glossaire s'étoffe au fil des vérifications de nos juristes-linguistes. | Nach deutschem Begriff geordnet. Das Glossar wächst mit jeder Prüfung durch unsere Rechtslinguistinnen und Rechtslinguisten. | Forme double inclusive, « Rechtslinguist ». |

Autres libellés récurrents (liste complète dans `termes-de.json`, type « interface ») : « En bref » devient « In Kürze », « Lire l'article » devient « Artikel lesen », « Centre d'aide » devient « Hilfe-Center », « Voir la plateforme » devient « Zur Plattform », « Découvrir CHnell » devient « CHnell entdecken », « Une question reste sans réponse ? » devient « Noch eine Frage offen? ».

## 7. Carte des requêtes DE par famille de pages

Requêtes plausibles en Suisse alémanique, du point de vue d'un avocat, d'un juriste d'entreprise ou d'un banquier zurichois. Elles ne sont **pas mesurées** : avant de figer les titres, les confronter aux volumes réels (Google Ads Keyword Planner, Search Console). La requête visée page par page figure dans `docs-traduction/routes-de.md`.

| Famille | Requêtes principales | Où les placer |
|---|---|---|
| Produit (Corrext, outils, LexMachina, langues, niveaux) | « juristische Übersetzungssoftware » · « KI-Übersetzung für Juristen » · « Handelsregisterauszug übersetzen » | title et h1 de l'outil concerné, FAQ produit |
| Sécurité et comparatifs | « Datensouveränität Schweiz » · « DeepL Alternative Schweiz » · « ChatGPT Berufsgeheimnis » | page Sicherheit, trois comparatifs |
| Solutions par métier | « Übersetzung für Anwaltskanzleien » · « Finanzübersetzung Bank Schweiz » · « Übersetzung Rechtsabteilung » | une requête par page métier, en title et h1 |
| Domaines du droit | « Vertragsübersetzung » · « Geschäftsbericht übersetzen » · « Statuten übersetzen » | title, h1, tableau des termes, FAQ |
| Paires de langues | « juristische Übersetzung Deutsch Französisch » · « Vertrag Englisch Deutsch übersetzen » · « Rechtsübersetzer Französisch » | title et h1 de chaque paire |
| Glossaire | « Verzugszins auf Französisch » · « Zahlungsbefehl französisch » · « juristisches Wörterbuch Deutsch Französisch » | title « <Begriff>: Definition und Übersetzung · Neur.on », description avec l'équivalent français |
| Centre d'aide | « Corrext Anleitung » · « PDF in Word umwandeln und übersetzen » · « Corrext Translation Memory » | titres des rubriques, questions des articles |
| Blog et guides | « Vertrag übersetzen Schweizer Recht » · « Kosten juristische Übersetzung » · « Berufsgeheimnis KI-Übersetzung » | title et h1 des articles, bloc « In Kürze » |

Les actualités visent le nom de l'événement (« Swiss FinTech Awards 2024 », « EPFL Investor Day 2024 ») : pas de réécriture SEO de leurs faits.
