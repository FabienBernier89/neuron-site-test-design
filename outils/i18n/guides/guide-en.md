# Guide de style anglais (britannique) · site neur-on.ai

Ce guide s'applique à toutes les pages EN du site : première traduction Corrext, adaptation, relecture. Il complète la base terminologique `src/i18n/termes-en.json` et la table des adresses `docs-traduction/routes-en.json` (version lisible : `docs-traduction/routes-en.md`).

Lectorat visé : un lecteur international qui travaille avec la Suisse. Avocat d'un cabinet international, juriste d'une multinationale établie en Suisse, banquier, contrepartie étrangère d'un contrat suisse. Il lit l'anglais juridique, souvent comme seconde langue.

Ordre de priorité : les règles absolues (section 1), puis ce guide, puis le brouillon LexMachina. En cas de doute sur un terme juridique, la traduction anglaise de la Confédération (Fedlex, TERMDAT) l'emporte sur l'usage du droit anglais ou américain. Elle n'a pas force de loi : seuls les textes allemand, français et italien font foi.

Références (lues le 2 octobre 2026) :
- **General Style Guide**, English Language Service, Chancellerie fédérale, 3e édition, septembre 2024 : https://www.bk.admin.ch/dam/en/sd-web/s-KLxST1P9Ke/English%20Style%20Guide.pdf (cité « GSG »). Le guide se dit contraignant pour les auteurs et traducteurs anglais de l'administration fédérale.
- **Legal Style Guide**, English Language Service de la Chancellerie fédérale et service linguistique du DFAE, août 2025 : https://www.bk.admin.ch/dam/en/sd-web/tMwxRM3uw-WI/Legal%20Style%20Guide.pdf (cité « LSG »).
- Page d'accueil des deux guides : https://www.bk.admin.ch/en/style-guides-for-english-language-translators
- Fedlex, traductions anglaises (point d'accès SPARQL https://fedlex.data.admin.ch/sparqlendpoint, expression `ENG`) et TERMDAT (https://www.termdat.bk.admin.ch). L'API publique de TERMDAT ne sert pas les titres des lois : ils ont été relevés dans Fedlex.

## 1. Règles absolues

1. **Anglais britannique.** Le GSG (« Writing in English ») prend l'usage de Grande-Bretagne et d'Irlande comme norme, sans tournures très familières, parce qu'une grande partie des lecteurs n'est pas anglophone de naissance. Orthographe :
   - **-ise** et non -ize : organisation, prioritise, recognise, authorise (GSG §1) ;
   - **-yse** seulement : analyse, paralyse (GSG §1) ;
   - licence (nom) et license (verbe), practice (nom) et practise (verbe), defence, centre, programme, behaviour, judgment au sens juridique et judgement ailleurs (GSG §1 et §2) ;
   - les noms propres gardent leur graphie d'origine : « US CLOUD Act », « International Labour Organization », et les libellés de l'application Corrext (GSG §1 : « Retain original spellings in titles »).
2. **« you » neutre**, sans « dear client » ni tutoiement marketing. Les appels à l'action sont à l'impératif : « Request a demo », « Upload your file ». Pas de contractions dans le texte courant (« do not », « it is ») ; elles sont tolérées dans les questions de FAQ formulées comme on les tape.
3. **Noms jamais traduits ni modifiés** : Neur.on, Corrext, LexMachina, CHnell, Fast lookup CHnell, Highly sensitive content, Infomaniak. Casse et orthographe intactes.
   - « the Corrext platform », « the LexMachina engine », « Corrext's editor » sont corrects en anglais. Jamais de nom modifié, coupé ou mis au pluriel (« Correxts », « Lexmachina », « the CHnells »).
   - Le mode s'écrit « Highly sensitive content mode ». Là où le FR emploie la forme courte « mode Highly sensitive », garder la forme courte : « Highly sensitive mode ». Le contrôle compte les noms de produits segment par segment.
   - La raison sociale reste **Neur.on AI Solutions SA**, jamais « Ltd » : le GSG (§13) interdit de remplacer « SA » ou « GmbH » par « Inc. » ou « Ltd », et le registre du commerce inscrit la société sous la forme SA. L'ancienne page anglaise écrivait « Ltd » : voir l'annexe A.
4. **LexMachina** est un « neural machine translation engine », un « translation engine » ou un « neural translation model ». Jamais « LLM », « language model », « AI model » ni « chatbot ». Seule exception : les actualités historiques, qui gardent leurs faits et leurs mots (par exemple les AI Days 2025).
5. **Noms interdits** : toute autre marque que celles de Neur.on, « group », « acquisition », « merger » au sens d'une opération de reprise, ou toute allusion à une telle opération. Aucun prix, aucun montant en CHF, aucun nom de client.
6. **Moteurs tiers sans numéro de version** : DeepL Pro, Azure OpenAI GPT, ChatGPT, Claude.
7. **Aucun tiret cadratin ni demi-cadratin** (U+2014, U+2013). Le GSG (§6.4, §11, §12) emploie le demi-cadratin pour les intervalles et les incises : le site s'en écarte, parce que son contrôle automatique bloque ces deux signes dans toutes les langues. À la place :
   - intervalles : « to » (« Articles 80 to 84 DEBA », « from 2020 to 2024 »), forme que le GSG §12 impose lui-même (« from … to », « between … and ») ; dans un tableau, le trait d'union simple (« 2025-2028 ») ;
   - incises : virgules, parenthèses, deux-points, point médian « · » dans les titres ;
   - en citant Fedlex, remplacer le demi-cadratin des renvois (par exemple entre deux numéros d'articles) par « to ».
8. **Aucun superlatif sans preuve** : pas de « the best », « leading », « unique », « revolutionary », « cutting-edge », « state-of-the-art », « world-class ». Un chiffre sourcé vaut mieux qu'un adjectif.
9. **Phrases courtes, une idée par phrase.** Voix active, verbe plutôt que nom (« you translate » plutôt que « the performance of the translation »). Au-delà de 25 mots, couper. Le GSG (« How to write clearly ») et le LSG (§2.4.2) demandent un anglais clair, sans jargon archaïque (« hereinafter », « witnesseth », « null and void »).
10. **Aucune tournure qui trahit un texte écrit par une IA.** À proscrire :
    - « In today's fast-paced world », « Dive into », « Unlock », « Elevate », « Discover the world of » ;
    - « seamless », « robust », « leverage », « delve », « game-changer », « harness the power of », « navigate the complexities of », « tailored » à répétition ;
    - « It is important to note that », « Not only … but also » à répétition ;
    - les séries de trois adjectifs, les questions rhétoriques en cascade, un « In conclusion » au bout de chaque section.
11. **Aucune phrase reprise d'un autre site** (contrôle par séquences de 8 mots).
12. **Langage inclusif** (GSG §17) : « they » singulier, noms neutres (« chair », « lawyer », « legal expert »). Jamais « he/she ».

## 2. Formats

| Élément | Règle | Exemple |
|---|---|---|
| Milliers | virgule dans le texte courant ; espace insécable dans les tableaux (GSG §7) | 15,000 · tableau : 15 000 |
| Décimales | point (GSG §7) | 4.5 |
| Montants (s'il en faut un) | code ISO avant le nombre, jamais « SFr. » ni « Fr. », ni « 20.-- » après le nombre (GSG §8) | CHF 15,000 |
| Pourcentages | « % » collé au chiffre ; « per cent » en deux mots si le nombre est en lettres (GSG §10). Le DE met une espace : pas l'EN | 25% · twenty per cent |
| Nombres | un à dix en lettres, au-delà en chiffres ; jamais un chiffre en tête de phrase (GSG §7) | ten items · 27 items |
| Dates | jour en chiffre, mois en toutes lettres, sans « th » ni virgule (GSG §12) ; jamais de date numérique (02/10 se lit 10 février aux États-Unis) ; dans un tableau, mois abrégé avec point (GSG §13) | 2 October 2026 · tableau : 2 Oct. 2026 |
| Heures | 12 heures avec point, ou 24 heures avec deux-points (GSG §12) | 4.30pm · 16:30 |
| Intervalles | « to » ou « from … to » (voir 1.7 : divergence assumée avec le GSG) | from 2020 to 2024 · Arts 80 to 84 DEBA |
| Guillemets | “…” pour une citation, ‘…’ pour un mot isolé ou une citation dans la citation ; jamais « » ni „“ (GSG §6.6) | the term ‘summons for payment’ |
| Ponctuation | aucune espace avant « : ; ? ! » (GSG §6) | Corrext: Take back control |
| Articles de loi | « Art. », « para. », « let. », « no », pluriels « Arts », « paras » sans point ; en toutes lettres dans le texte courant, abrégés entre parenthèses (LSG §2.4.3) | Art. 104 para. 1 CO · Article 104 paragraph 1 of the Code of Obligations · Art. 305bis SCC |
| Recueils et arrêts | SR, AS, BBl gardés ; la citation BGE n'est jamais traduite (LSG §2.4.3) | SR 220 · BGE 145 III 72 |
| Ordre des langues | les trois langues officielles, puis l'anglais | German, French, Italian and English |
| Villes et cantons | forme anglaise du GSG, annexe 1 ; « canton » minuscule pour le territoire, « Canton » majuscule pour le gouvernement (GSG §4) | Geneva, Zurich, Lucerne, Bern, St Gallen, Fribourg, Ticino · the canton of Schwyz · the Canton of Fribourg |
| Adresse postale | forme locale | Place de la Gare 15, 1700 Fribourg, Switzerland |
| Abréviations | nom complet à la première mention, puis le sigle ; jamais un sigle anglais improvisé (GSG §13) | the Swiss Financial Market Supervisory Authority (FINMA) |

Pour Fribourg : « Fribourg » partout. À la première mention sur les pages À propos et Presse, écrire « Fribourg, Switzerland » : un lecteur ou un moteur de réponse ne situe pas toujours la ville.

## 3. Terminologie suisse, pas celle du droit anglais ou américain

Principe (LSG §1) : le droit suisse a des notions sans équivalent en common law. On reprend le terme anglais de la Confédération (Fedlex, TERMDAT). Quand ce terme peut tromper un juriste anglophone, on ajoute le terme original entre parenthèses à la première mention de la page : « debt enforcement (Betreibung) », « summons for payment (Zahlungsbefehl) », « setting aside of the objection (Rechtsöffnung) », « composition moratorium (Nachlassstundung) ».

Les traductions anglaises de Fedlex portent la mention : « English is not an official language of the Swiss Confederation » (LSG §3.1). Sur les pages du glossaire et des domaines, dire une fois que l'équivalent anglais vient de cette traduction, sans force légale.

### Oui / non

| Notion suisse | Oui | Non | Pourquoi |
|---|---|---|---|
| Bundesgericht, Tribunal fédéral | Federal Supreme Court | Federal Court, Swiss Supreme Court | LSG §3.2 et GSG §21 ; Cst. art. 188 en anglais |
| Betreibung, poursuite | debt enforcement (Betreibung) | debt collection, execution | DEBA art. 38 en anglais ; « execution » a un sens étroit en droit anglais (LSG §3.4.2) |
| Konkurs, faillite | bankruptcy | insolvency, liquidation, winding-up | DEBA art. 39 et 197 en anglais : la faillite vise aussi les débiteurs inscrits au registre du commerce |
| Arrest, séquestre | attachment | sequestration, freezing order | DEBA art. 271 en anglais ; « sequestration » a un autre sens dans plusieurs droits anglophones |
| Rechtsvorschlag, opposition | objection (to the summons for payment) | opposition | DEBA art. 74 en anglais |
| Beschwerde (au Tribunal fédéral) | appeal | complaint | LSG §3.4.2 : « complaint » désigne en anglais l'acte introductif d'une action civile |
| Strafbefehl, ordonnance pénale | summary penalty order | penalty notice, fixed penalty notice | CrimPC art. 352 en anglais ; LSG §3.4.3 réserve « fixed penalty fine » à l'Ordnungsbusse |
| Geldstrafe et Busse | monetary penalty et fine | fine pour les deux | LSG §3.4.3 : la distinction compte dans presque tous les textes |
| Staatsanwaltschaft, ministère public | public prosecutor, cantonal prosecutor's office | Crown Prosecution Service, district attorney | CrimPC art. 12 en anglais ; LSG §3.4.3 |
| Aktiengesellschaft, société anonyme | company limited by shares | public limited company, plc, corporation | CO art. 620 en anglais ; « plc » et « corporation » sont des formes étrangères |
| GmbH, Sàrl | limited liability company | Ltd, private limited company | CO art. 772 en anglais ; GSG §13 |
| Statuten, statuts | articles of association | statutes, bylaws | LSG §3.1 ; CO art. 626 en anglais |
| Verwaltungsrat, conseil d'administration | board of directors | supervisory board | CO art. 707 en anglais |
| Revisionsstelle, organe de révision | external auditor | statutory auditor | CO art. 727 en anglais (« External Auditors ») |
| Handelsregister, registre du commerce | commercial register | Companies House, register of companies | CO art. 927 en anglais ; institutions britanniques |
| Treuhand, fiduciaire | fiduciary, fiduciary and audit firm | trust, trustee | LSG §3.5 : « trust » suppose un trust de common law |
| Rechtsanwalt, avocat | lawyer | solicitor, barrister, advocate | LSG §3.3 : termes au sens propre au Royaume-Uni |
| Notar, notaire | notary | notary public | LSG §3.3 : le notaire suisse est un juriste, le « notary public » n'en est pas toujours un |
| Jurist, juriste | legal expert, in-house lawyer, legal counsel | jurist | LSG §3.3 : « jurist » désigne un juge ou un savant du droit |
| Anwaltskanzlei, cabinet d'avocats | law firm | chambers | LSG §3.3 |
| Kündigung, résiliation | termination, notice of termination | cancellation, rescission | LSG §3.4.4 ; CO art. 335 en anglais |
| missbräuchliche Kündigung, résiliation abusive | wrongful termination | unfair dismissal | CO art. 336 en anglais ; « unfair dismissal » est une notion du droit anglais du travail |
| Konventionalstrafe, clause pénale | contractual penalty | liquidated damages, penalty clause | CO art. 160 en anglais ; notions de common law |
| Gewährleistung, garantie des défauts | warranty | guarantee | LSG §3.4.4 ; CO art. 197 en anglais |
| Bürgschaft, cautionnement | contract of surety | guarantee | CO art. 492 en anglais ; la « guarantee » de l'art. 111 CO est une autre figure |
| Verjährung, prescription | prescription | limitation (seul) | CO art. 127 en anglais ; « limitation period » possible en glose |
| Schaden, Schadenersatz | loss and damage, damages | damages pour le préjudice lui-même | LSG §3.5 : « damages » est la somme allouée |
| höhere Gewalt, force majeure | force majeure | act of God | LSG §3.5 : « act of God » ne couvre que les causes naturelles |
| AGB, conditions générales | General Terms and Conditions | General Conditions, General Business Conditions | LSG §3.4.4 |
| Rechtsprechung, jurisprudence | case law | jurisprudence | LSG §3.5 : « jurisprudence » est la science du droit |
| materielles Recht, droit matériel | substantive law | material law | LSG §3.5 |
| juristische Person, personne morale | legal entity | legal person | LSG §3.5 |
| Sorgfaltspflichten (GwG), obligations de diligence | due diligence obligations | duty of care | LSG §3.5 ; AMLA art. 3 à 8 en anglais |
| Berufsgeheimnis, secret professionnel | professional secrecy, professional confidentiality | attorney-client privilege, legal professional privilege | AMLA et SCC art. 321 en anglais ; le « privilege » de common law est une autre institution (à confirmer par le traducteur expert). Le libellé d'application « Attorney-Client privilege notice » reste tel quel |
| Steuerhinterziehung, soustraction d'impôt | tax evasion, avec prudence | tax fraud | LSG §3.4.3 : certains faits de « tax evasion » au Royaume-Uni ne sont pas des infractions pénales en Suisse ; le Steuerbetrug est une notion distincte |
| Verfügung, décision | ruling | order, decree | APA art. 5 en anglais |
| Prozess, procès | trial, proceedings, litigation | process | LSG §3.4.2 |
| Auftrag, mandat | agency contract, instructions, engagement | mandate | LSG §3.5 : « mandate » évoque surtout un mandat politique |
| Reglement, règlement | rules, regulations | regulation (au singulier) | LSG §3.1 |
| Verordnung (droit suisse) | Ordinance | Regulation | LSG §3.1 : « Regulation » est réservé au droit de l'UE |
| Kanton, Gemeinde | canton, commune | state, province, municipality | GSG §4 |
| vorsehen, prévoir | provide for, stipulate | foresee | LSG §3.5 |

Institutions : « Federal Council » (le gouvernement, GSG §21), « Swiss Financial Market Supervisory Authority FINMA », « Swiss Innovation Agency Innosuisse », « Swiss Federal Institute of Intellectual Property (IPI) » (GSG, annexe 2), « Federal Administrative Court », « Federal Criminal Court », « Federal Patent Court » (LSG §3.2), « Office of the Attorney General of Switzerland » (LSG §3.4.3).

### Métier de la traduction

- devis : **quote** (« Request a quote ») ; page standard : **standard page** ; délai de livraison : **delivery time** (délai légal : « time limit », comme Fedlex) ;
- relecture juridique : **legal review** ; relecture humaine : **human review** ; post-édition : **post-editing** ;
- traduction certifiée : **certified translation** ; notariée : **notarised translation** ; apostille : **apostille** ;
- le document signé par l'agence, qui atteste l'exactitude : **certificate of accuracy** (traduction maison à valider) ; « certification » et « certificate » seuls restent réservés à ISO 27001 quand il y a risque de confusion ;
- juriste-linguiste : **lawyer-linguist** (terme des institutions européennes) ; traducteur juridique : **legal translator** ;
- mémoire de traduction : **translation memory** ; concordancier : **concordancer**.

Libellés de l'application, conventions fixées pour le site :
- les libellés anglais de Corrext restent **tels quels**, avec leur casse et leur orthographe : Light review, Full review, **Double review & certified translation**, **Notarized & Apostilled Certification** (« Notarized » américain compris), File translation, Text translation, PDF to Word, Rephrasing, Attorney-Client privilege notice, Fast translation, Translation project, Open in CAT, Export docx ;
- en anglais, toutes les variantes FR du niveau 3 (« Double review et traduction certifiée », « Double review avec certificat », « Double review certifiée ») deviennent le libellé exact « Double review & certified translation ». Jamais « Double review and certified translation » (le site FR l'écrit deux fois : à corriger en FR aussi) ;
- **Highly sensitive** garde la même forme que le FR (voir 1.3) ;
- dans le texte courant, l'anglais britannique s'applique : « the document is notarised, then an apostille is added ».

Centre d'aide : l'interface de Corrext est en anglais. Reprendre chaque libellé à l'identique, relevé en lecture seule dans l'application, en gras ou entre guillemets simples. Si l'interface écrit à l'américaine (« Organization »), garder sa graphie dans le libellé et l'orthographe britannique dans la phrase.

## 4. Lois et abréviations

Toujours l'abréviation anglaise de Fedlex (`jolux:titleShort` de l'expression ENG). Liste complète dans `termes-en.json` (type « loi »). Dans le texte courant, la première mention donne le titre : « the Code of Obligations (CO) », « the Federal Act on Debt Enforcement and Bankruptcy (DEBA) ». « Act » prend toujours la majuscule, même sans le titre complet (LSG §3.1).

| FR | EN | Titre court EN | FR | EN | Titre court EN |
|---|---|---|---|---|---|
| CO | CO | Code of Obligations | LBA | AMLA | Anti-Money Laundering Act |
| CC | CC | Swiss Civil Code | LIFD | DFTA | Federal Act on Direct Federal Taxation |
| LP | DEBA | Federal Act on Debt Enforcement and Bankruptcy | LPD | FADP | Data Protection Act |
| CPC | CPC | Civil Procedure Code | LTF | (aucune) | Federal Supreme Court Act |
| CPP | CrimPC | Criminal Procedure Code | LB | BankA | Banking Act |
| CP | SCC | Swiss Criminal Code | LSFin | FinSA | Financial Services Act |
| LDIP | PILA | Federal Act on Private International Law | LFINMA | FINMASA | Financial Market Supervision Act |
| LCA | (aucune) | Federal Act on Contracts of Insurance | LFus | (aucune) | Mergers Act |
| LIA | (aucune) | Federal Act on Withholding Tax (à valider) | LTVA | VAT Act | Value Added Tax Act |
| ORC | (aucune) | Commercial Register Ordinance (à valider) | Cst. | Cst. | Federal Constitution |
| LPCC | CISA | Collective Investment Schemes Act | PA | APA | Administrative Procedure Act |
| RS | SR | Classified Compilation of Federal Legislation | FF | BBl | Federal Gazette |
| RO | AS | Official Compilation (à valider) | ATF | BGE | Decisions of the Swiss Federal Supreme Court |

Règles :
- « (aucune) » : Fedlex n'a pas d'abréviation anglaise. On écrit le titre anglais en entier, jamais un sigle improvisé (GSG §13).
- « nLPD » devient « the revised FADP » dans un texte marketing ; dans une référence juridique, écrire « FADP ». « RGPD » devient « GDPR ».
- Trois abréviations divergent entre Fedlex et l'usage : LSA (« ISA » dans la FinSA, « IOA » dans la FINMASA : retenir ISA), LEI (« FNA » dans les métadonnées, « FNIA » dans le texte en vigueur : retenir FNIA), LTVA (le LSG donne « VATA » en exemple, Fedlex « VAT Act » : retenir Fedlex).
- Pour la matière, le LSG (§3.4.1) préfère « international private law » ; le titre Fedlex de la LDIP dit « Private International Law ». Garder le titre Fedlex pour la loi et « private international law » pour la matière, l'usage de la plupart des lecteurs visés.

**Liens Fedlex des pages EN** : `/en` si la loi a une traduction anglaise, sinon `/de` (tâche 12 du plan). Vérification SPARQL du 2 octobre 2026 :
- traduction anglaise publiée (22 lois) : CC, CO, CP, CPC, CPP, EIMP, LBA, LBI, LCart, LDA, LDIP, LDes, LEI, LFINMA, LP, LPCC, LPD, LPM, LSFin, LTVA, PA, Cst. ;
- **aucune traduction anglaise** (10 lois : expressions ENG vides, sans fichier) : LB, LCA, LFus, LHID, LIA, LIFD, LSA, LTF, LTr, ORC. Le champ `url_en` de `src/data/fedlex.json` existe pour ces dix lois mais pointe vers une version qui n'existe pas : lien `/de` à la place.
- Conséquence pour le glossaire EN : six fiches ont leur loi de base sans texte anglais (bankgeheimnis : LB ; beschwerde : LTF ; verrechnungssteuer : LIA ; versicherungsvertrag : LCA ; steuerhinterziehung et quellensteuer : LIFD). Leur exemple anglais ne peut pas venir de la loi de base : à décider avec Fabien (exemple allemand seul, ou segment anglais d'une autre loi, signalé comme tel).

Écarts entre les fiches du glossaire et Fedlex (détail dans les notes de `termes-en.json`) :

| Fiche | `glossaire.json` (champ `en`) | Fedlex | Décision proposée |
|---|---|---|---|
| revisionsstelle | auditor | external auditor (CO art. 727) | aligner sur Fedlex, aussi dans les tableaux |
| nachlassstundung | debt restructuring moratorium | composition moratorium (DEBA art. 293 ss) | aligner sur Fedlex |
| bankgeheimnis | banking secrecy | aucune traduction de la LB | garder, à valider par un traducteur expert |
| quellensteuer | tax at source | aucune traduction de la LIFD | garder, à valider |
| beschwerde | appeal | aucune traduction de la LTF ; « appeal » dans DEBA art. 19 | garder |
| untersuchungshaft | remand (pre-trial detention) | remand (CrimPC art. 220) | garder, la glose aide le lecteur |

Dans les tableaux des domaines, deux autres écarts : « securities » pour les papiers-valeurs (Fedlex : « negotiable securities », CO art. 965) et « auditor » pour l'organe de révision.

## 5. Ton, titres et SEO

- **Ton** : expert, précis, sobre, ancré en Suisse. On montre (où sont les données, qui relit, quelle loi), on ne vante pas. La retenue britannique convient : pas de « amazing », pas de points d'exclamation.
- **Le mot « Swiss »** : le GSG (§4) met en garde contre son abus. Une fois par bloc suffit quand le contexte est clair.
- **Structure des accroches** : garder la forme du FR, « Name. Promise » (« Law firms. Translate a case file without it ever leaving Switzerland »).
- **title** : 30 à 62 caractères, la requête principale en tête, puis « · Neur.on ». Exemple glossaire : « Verzugszins in English: default interest · Neur.on » (50 caractères).
- **description** : 110 à 160 caractères, ce que la page apporte, sans formule creuse.
- **h1 et h2** : majuscule au premier mot seulement, comme les titres d'articles de Fedlex (LSG §3.1) et selon la règle du GSG (§3) : « the longer the name, the fewer the capitals ». Les noms propres et les titres officiels gardent leurs majuscules (« Code of Obligations »).
- **FAQ** : de vraies questions de lecteurs internationaux, formulées comme on les tape ou les pose à un assistant (« Can I translate confidential contracts with DeepL? »). Réponse directe dans la première phrase.
- **Longueur** : l'anglais est plus court que le DE ; un bouton tient en 22 caractères au plus pour passer à 375 px.
- **Traits d'union** (GSG §5) : adjectif composé avant le nom (« ISO 27001-certified hosting », « AI-powered translation », « up-to-date terminology »), pas après (« the terminology is up to date ») ; pas de trait d'union entre deux noms (« data protection law ») ; « email », « database », « cybersecurity » en un mot (GSG §5).
- **Virgule d'Oxford** : seulement si elle lève une ambiguïté (GSG §6.3).
- **Listes** (GSG §14) : deux-points après l'introduction, rien en fin d'élément simple ; point-virgule et point final si les éléments prolongent la phrase.

## 6. Vingt formulations maison, FR → EN

| # | Type | FR (site) | EN | Ce que l'exemple montre |
|---|---|---|---|---|
| 1 | Accroche, accueil | Votre solution de traduction par IA pour le droit, la fiscalité et la finance | AI translation for legal, tax and financial documents | Requête « AI legal translation » en tête, sans « solution » ni adjectif. |
| 2 | Accroche, Corrext | Corrext : reprenez le contrôle de vos traductions | Corrext: Take back control of your translations | Pas d'espace avant les deux-points ; majuscule après, car ce qui suit est une proposition complète et ce qui précède n'en est pas une (GSG §6.1). |
| 3 | Accroche, LexMachina | LexMachina. Le moteur qui connaît les lois qu'il traduit | LexMachina. The translation engine that knows the law it translates | « translation engine », jamais « LLM ». |
| 4 | Accroche, avocats | Cabinets d'avocats. Traduire un dossier sans jamais le sortir de Suisse | Law firms. Translate a case file without it ever leaving Switzerland | « law firm » (LSG §3.3), « case file » et non « dossier ». |
| 5 | Chapeau, avocats | Quatre cents pages de pièces à comprendre avant l'audience, un contrat à livrer ce soir, un mémoire à citer au mot près. | Four hundred pages of exhibits to digest before the hearing. A contract due tonight. A written submission to quote word for word. | Une énumération longue devient trois phrases ; « mémoire » se dit « written submission » (LSG §3.4.2), les pièces « exhibits » (LSG §3.4.4). |
| 6 | Accroche, fiduciaires | Fiduciaires et conseil. Documents d'entreprise traduits et certifiés | Fiduciary and advisory firms. Company documents, translated and certified | « fiduciary », jamais « trust » (LSG §3.5). |
| 7 | Accroche, sécurité | Souveraineté des données. Où va votre document, exactement, et qui peut le lire | Data sovereignty. Where exactly your document goes, and who can read it | Question indirecte, sans point d'interrogation. |
| 8 | Bouton | Demander une démo | Request a demo | Verbe en tête, 14 caractères. |
| 9 | Bouton | Essayer Corrext en direct | Try Corrext live | Court : tient sur un bouton à 375 px. |
| 10 | Bandeau | Essayez Corrext, sans inscription | Try Corrext without signing up | Impératif simple, pas de virgule superflue. |
| 11 | Sécurité | Mode Highly sensitive : stockage et traitement exclusivement en Suisse | Highly sensitive mode: stored and processed in Switzerland only | Forme courte du nom du mode, identique au FR. |
| 12 | Sécurité | Hébergement 100% suisse · Infomaniak | 100% Swiss hosting · Infomaniak | « % » collé (GSG §10), point médian conservé. |
| 13 | Sécurité | Hors CLOUD Act. Société suisse, infrastructure suisse : le stockage de vos projets ne relève pas du US CLOUD Act. | Outside the CLOUD Act. Swiss company, Swiss infrastructure: Storage of your projects is not subject to the US CLOUD Act. | Majuscule après les deux-points devant une proposition complète (GSG §6.1) ; nom de la loi américaine dans sa graphie d'origine. |
| 14 | Sécurité | Aucun entraînement sur vos contenus. LexMachina apprend de corpus juridiques et financiers suisses publics, jamais de vos dossiers. | No training on your content. LexMachina learns from public Swiss legal and financial texts, never from your files. | « content » indénombrable ; « texts » plutôt que « corpora ». |
| 15 | Sécurité | Le certificat et le périmètre sont remis sur demande, pour votre dossier fournisseur. | The certificate and its scope are available on request for your supplier assessment. | « dossier fournisseur » devient « supplier assessment » : pas de calque. |
| 16 | Sécurité | Votre politique s'applique au moment du choix, pas dans une charte oubliée | Your policy applies when the engine is chosen, not in a forgotten set of rules | « Reglement / charte » devient « rules » (LSG §3.1), jamais « regulation ». |
| 17 | Glossaire | Les lois fédérales suisses sont publiées en allemand, en français et en italien, et les trois versions font foi. L'équivalence ci-contre n'est donc pas une traduction d'usage : c'est le terme employé par le texte officiel lui-même. | Swiss federal acts are published in German, French and Italian, and all three versions are equally authoritative. The English term shown here comes from the Federal Administration's English translation, published on Fedlex for information only. | Adaptation de fond : en anglais, l'équivalent n'a pas force de loi et il faut le dire (LSG §3.1). |
| 18 | Glossaire | Source : Fedlex, Code des obligations. Dans Corrext, ce segment et ceux qui l'entourent s'affichent dans Fast lookup CHnell, chacun avec sa référence. | Source: Fedlex, Code of Obligations (English translation, no legal force). In Corrext, this segment and the ones around it appear in Fast lookup CHnell, each with its reference. | Le titre anglais de la loi, et la mention de l'absence de force légale. |
| 19 | Glossaire | L'intérêt moratoire est dû dès que le débiteur est en demeure de payer une somme d'argent, indépendamment de tout dommage prouvé. | Default interest is owed as soon as a debtor is in default on payment of a pecuniary debt, regardless of any proven loss. | Reprend les mots de l'art. 104 CO en anglais (« in default on payment of a pecuniary debt »). |
| 20 | Glossaire | Classés par terme allemand. Le glossaire s'étoffe au fil des vérifications de nos juristes-linguistes. | Sorted by German term. The glossary grows with each check by our lawyer-linguists. | « lawyer-linguist », terme des institutions européennes. |

Autres libellés récurrents (liste complète dans `termes-en.json`, type « interface ») : « En bref » devient « In brief », « Lire l'article » devient « Read the article », « Centre d'aide » devient « Help Centre », « Voir la plateforme » devient « See the platform », « Découvrir CHnell » devient « Explore CHnell », « Une question reste sans réponse ? » devient « Still have a question? », « Mentions légales et CGU » devient « Impressum and Terms of Use », « Protection des données » devient « Privacy policy ».

## 7. Carte des requêtes EN par famille de pages

Requêtes plausibles pour un lecteur international qui travaille avec la Suisse, en anglais. Elles ne sont **pas mesurées** : avant de figer les titres, les confronter aux volumes réels (Google Ads Keyword Planner, Search Console), sur deux marchés : « anglais, Suisse » et « anglais, monde » (Royaume-Uni, États-Unis, Allemagne, Luxembourg, Singapour pour les banques). La requête visée page par page figure dans `docs-traduction/routes-en.md`.

| Famille | Requêtes principales (hypothèses) | Où les placer |
|---|---|---|
| Produit (Corrext, outils, LexMachina, langues, niveaux) | « legal translation software » · « AI legal translation Switzerland » · « Swiss commercial register extract translation » · « translate PDF keep formatting » | title et h1 de l'outil concerné, FAQ produit |
| Sécurité et comparatifs | « legal translation Switzerland » · « Swiss data sovereignty » · « DeepL alternative for lawyers » · « is DeepL safe for confidential documents » · « ChatGPT professional secrecy » | page Security, trois comparatifs |
| Solutions par métier | « translation for law firms Switzerland » · « financial translation for banks » · « translation for in-house legal teams » | une requête par page métier, en title et h1 |
| Domaines du droit | « contract translation Swiss law » · « annual report translation Switzerland » · « articles of association translation » · « FINMA circular translation » | title, h1, tableau des termes, FAQ |
| Paires de langues | « German to English legal translation » · « French to English legal translation » · « Swiss German contract translation English » | title et h1 de chaque paire |
| Glossaire | « Betreibung in English » · « Zahlungsbefehl English translation » · « Swiss legal terms German English » | title « <Begriff> in English: <equivalent> · Neur.on », description avec l'équivalent anglais et la loi |
| Centre d'aide | « Corrext help » · « convert PDF to Word and translate » · « Corrext translation memory » | titres des rubriques, questions des articles |
| Blog et guides | « translate a contract under Swiss law » · « legal translation cost Switzerland » · « professional secrecy AI translation » | title et h1 des articles, bloc « In brief » |

Les actualités visent le nom de l'événement (« Swiss FinTech Awards 2024 », « EPFL Investor Day 2024 ») : pas de réécriture SEO de leurs faits.

## Annexe A. Pages légales EN : texte anglais d'origine

Les pages légales n'existaient qu'en anglais sur l'ancien site ; le FR en est la traduction. Les pages EN reprennent donc **le texte anglais d'origine**, placé dans la structure de la page FR (h1, ligne de version en tête, carte d'adresse, h2, identifiants d'ancre FR, lien « See also »). On ne retraduit pas le FR vers l'anglais.

Sources, lues le 2 octobre 2026 (curl), identiques au relevé du 1er octobre :
- https://neur-on.ai/impressum/ : « Impressum & Terms of Use », « Version of February 2024 » → `/en/impressum/` ;
- https://neur-on.ai/privacy-policy/ : « Privacy and Data Security » (titre de page « Privacy Policy »), « Version of February 2023 » → `/en/privacy-policy/` ;
- https://neur-on.ai/terms-of-use/ ne contient qu'une phrase de renvoi : les conditions d'utilisation sont dans l'Impressum.

Ce que le FR a ajouté ou changé, et ce qu'il faut faire en EN :

| Page | Écart du FR par rapport à l'original | En EN |
|---|---|---|
| Impressum | Raison sociale : l'original écrit « Neur.on AI Solutions Ltd », le FR « Neur.on AI Solutions SA » (forme inscrite au registre du commerce) | « Neur.on AI Solutions SA » (GSG §13). Seul écart de fond avec l'original : à faire valider |
| Impressum | Titre : « Mentions légales et conditions d'utilisation » | h1 d'origine : « Impressum & Terms of Use » |
| Impressum | Les intertitres de l'original (« Contact address and Data Controller », « Intellectual Property », « Links to other websites », « Changes », « Applicable law », « Contact details ») sont de simples paragraphes ; le FR en fait des h2 et met l'adresse dans une carte | mêmes intertitres anglais, en h2, dans la structure FR |
| Impressum | Ligne « Version of February 2024 » déplacée de la fin vers le haut | en haut, comme le FR |
| Impressum | Téléphone en lien `tel:` ; « E-Mail » devient « E-mail » | « Email » (GSG §5) et « Tel. » ; lien conservé |
| Impressum | La longue phrase sur la propriété intellectuelle est coupée en deux | coupe acceptable au même endroit, mots d'origine conservés |
| Impressum | « by using our contact form under the corresponding tab/webpage » devient un lien vers la page Contact, sans « tab » | « by using our contact form » avec le lien ; « tab/webpage » renvoyait à l'ancien site |
| Impressum | Ajout du lien « Voir aussi : Protection des données » | « See also: Privacy policy » |
| Privacy | Titre : « Confidentialité et sécurité des données » | h1 d'origine : « Privacy and Data Security » |
| Privacy | Ajout en tête de la carte « Adresse de contact et responsable du traitement », reprise de l'Impressum, parce que le point 1 renvoie à « the address indicated above », qui se trouvait sur l'autre onglet de l'ancien site | même carte, intitulée « Contact address and Data Controller » |
| Privacy | Ligne de version déplacée en haut | en haut |
| Privacy | Troisième droit reformulé : « the right to refuse or limit our processing » devient « le droit de vous opposer au traitement, ou d'en demander la limitation » | texte d'origine |
| Privacy | Listes en minuscules avec points-virgules | texte d'origine ; éléments simples sans ponctuation finale (GSG §14) |
| Privacy | « Web-Tracking » devient « Outils de suivi web » | « Web tracking » (GSG §5) : correction de forme |
| Privacy | « customize » (graphie américaine dans un texte par ailleurs britannique) | « customise » (GSG §1) : correction d'orthographe |
| Privacy | « U.S.A. » devient « États-Unis » ; « Do Not Track » et « Google Analytics Opt-out Browser Add-on » glosés en français ; adresses web en liens | « USA » (GSG §13, sigles sans points) ; pas de glose ; liens conservés |
| Privacy | Ajout du lien « Voir aussi : Mentions légales et conditions d'utilisation » | « See also: Impressum & Terms of Use » |

Les trois points faux connus de la politique de confidentialité (certification Privacy Shield de Google, description de Lucky Orange, « Google Inc. ») figurent dans l'original comme dans le FR. **Ne pas les corriger maintenant** : décision de Fabien du 1er octobre 2026, hors périmètre de la spécification. Ils seront corrigés en même temps dans les quatre langues.

## Annexe B. Actualités : les textes anglais d'origine

La plupart des actualités FR sont des traductions retravaillées et anonymisées de textes anglais de l'ancien site (page `/news/`). Les originaux extraits sont dans le scratchpad de la session ce992fec : `/private/tmp/claude-501/-Users-fabienbernier-Claude-project/ce992fec-3d03-4df9-a989-fe30aa564320/scratchpad/blog-source/`. Ce dossier est **temporaire** : à archiver avant la tâche 13, hors du dépôt public (par exemple dans `Bibliotheque-Claude/`).

Structure :
- `lots/articles-1.json` à `articles-4.json` : les 31 originaux devenus des articles (champs `num`, `titre`, `date`, `langue`, `corps_html`, `images`, `liens_externes`, `signalements`, `notes`) ;
- `lots/breves-1.json` et `breves-2.json` : les 80 originaux devenus des brèves ;
- `trad/*.json` : les adaptations FR, même `num`, avec les `notes` de l'adaptateur (corrections, anonymisations, points à vérifier) ;
- `articles.json` : les 112 éléments bruts extraits de `/news/`, avec leurs métadonnées ; `anciens-posts-wordpress.json` : les 33 billets WordPress de 2020 et 2021 qui avaient une adresse propre.

Correspondance : un article de `src/data/blog.json` porte `source_num`, une brève de `src/data/actualites.json` porte `num` ; ce numéro est le `num` des fichiers `lots/` et `trad/`. La langue d'origine est dans `langue` : 104 originaux en anglais, quelques-uns en français ou en allemand (pour eux, seule la version FR sert).

Comment s'en servir :
1. **Référence de formulation**, pas source : la source reste la version FR retravaillée. L'original sert pour les noms d'événements, les intitulés officiels, les citations et la tournure anglaise d'une idée.
2. **Les anonymisations du FR priment.** Les noms de clients que l'original cite et que le FR a retirés (par exemple dans l'article « LegalTech et avocats ») restent retirés. Ne jamais réintroduire un nom de l'original.
3. **Les corrections du FR priment** : graphie « Swiss FinTech Awards », « CLOUD Act » au lieu de « US Clouds Act », restes de publication LinkedIn supprimés, dates d'origine conservées (jamais la date du jour). Lire les `notes` de `trad/` pour chaque numéro avant d'écrire.
4. **« LLM » reste tel quel** dans ces actualités historiques (exception de la règle 1.4).
5. L'actualité de mars 2026 sur l'équipe Legal NLP (premier élément d'`articles.json`) n'est pas reprise : ne pas l'ajouter.
6. Les tirets demi-cadratins de l'original (par exemple entre le lieu, la date et le texte, en tête de certaines actualités) disparaissent : deux-points ou point (règle 1.7).
