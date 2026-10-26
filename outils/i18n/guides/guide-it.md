# Guide de style italien (Suisse) · site neur-on.ai

Ce guide s'applique à toutes les pages IT du site : première traduction Corrext, adaptation, relecture. Il complète la base terminologique `src/i18n/termes-it.json` et la table des adresses `docs-traduction/routes-it.json` (version lisible : `docs-traduction/routes-it.md`).

Ordre de priorité : les règles absolues (section 1), puis ce guide, puis le brouillon LexMachina. En cas de doute sur un terme juridique, le texte officiel suisse en italien (Fedlex) l'emporte sur tout le reste. Pour la forme (dates, nombres, guillemets, abréviations), la référence est le document de la Chancellerie fédérale : *Istruzioni della Cancelleria federale per la redazione dei testi ufficiali in italiano* du 8 mai 2023, état au 15 décembre 2025 (bk.admin.ch, « Documentazione per la redazione di testi ufficiali »), cité ci-dessous « Istruzioni, n. X ».

## 1. Règles absolues

1. **Italien de Suisse**, celui des textes fédéraux, du Tessin et des Grisons italophones. Ni l'italien juridique ou administratif de l'Italie, ni ses institutions (section 3).
2. **« voi »**, le vouvoiement au pluriel du B2B suisse, toujours, en minuscules (voi, vostro, vi). Décision de Fabien du 2 octobre 2026, après vérification : UBS Svizzera (« Siamo al vostro fianco », « Fissate un appuntamento ») et Swisscom Business (« Gestite online le vostre soluzioni ») l'emploient. Jamais « tu », trop familier ; pas de « Lei », que la Chancellerie réserve à la correspondance officielle (Istruzioni, n. 124 à 126).
   - Texte courant et bandeaux : impératif pluriel. « Caricate il documento », « Provate Corrext senza registrazione ».
   - Boutons : infinitif, comme UBS (« Fissare un appuntamento ») : « Richiedere una demo ». Liens de navigation : forme « Alla … » (« Alla piattaforma »), comme UBS (« Alle opportunità di investimento »).
3. **Noms jamais traduits ni modifiés** : Neur.on, Corrext, LexMachina, CHnell, Fast lookup CHnell, Highly sensitive content, Infomaniak. Casse et orthographe intactes.
   - On écrit « la piattaforma Corrext », « il motore di traduzione LexMachina » ; le nom seul se passe d'article (« con Corrext », « LexMachina traduce »).
   - Le mode s'écrit « la modalità Highly sensitive content ». Là où le FR emploie la forme courte « mode Highly sensitive », garder la forme courte : « modalità Highly sensitive ». Le contrôle compte les noms de produits segment par segment.
   - La raison sociale reste « Neur.on AI Solutions SA ».
   - Les libellés anglais de l'application restent en anglais, comme sur le site FR : Light review, Full review, « Double review & certified translation », File translation, Text translation, PDF to Word, Rephrasing, Highly sensitive content, Attorney-Client privilege notice.
4. **LexMachina** est un « motore di traduzione neurale », un « motore di traduzione » ou un « modello di traduzione neurale ». Jamais « LLM », « modello linguistico » ni « chatbot ». Seule exception : les actualités historiques, qui gardent leurs faits et leurs mots (par exemple les AI Days 2025).
5. **Noms interdits** : toute autre marque que celles de Neur.on, « gruppo », « acquisizione », « fusione » au sens d'une opération de reprise, ou toute allusion à celle-ci. Aucun prix, aucun montant en franchi ou en CHF, aucun nom de client.
6. **Moteurs tiers sans numéro de version** : DeepL Pro, Azure OpenAI GPT, ChatGPT, Claude.
7. **Aucun tiret cadratin ni demi-cadratin** (U+2014, U+2013). Attention : les Istruzioni prescrivent la « lineetta » (le demi-cadratin) entre les bornes d'un intervalle d'années ou d'articles (n. 5, 6 et 99) ; le site la remplace par le trait d'union simple (« 2025-2028 », « articoli 80-84 LEF ») ou par une tournure (« dal 2025 al 2028 », « dall'articolo 80 all'articolo 84 »). Pour une incise : virgule, deux-points, parenthèses, point médian « · ».
8. **Aucun superlatif sans preuve** : pas de « il migliore », « leader », « unico », « rivoluzionario », « all'avanguardia ». Un chiffre sourcé vaut mieux qu'un adjectif.
9. **Phrases courtes, une idée par phrase.** L'italien juridique pousse aux subordonnées en cascade et aux nominalisations : préférer le verbe (« traducete » plutôt que « l'effettuazione della traduzione »). Au-delà de 25 mots, couper.
10. **Aucune tournure qui trahit un texte écrit par une IA.** À proscrire :
    - « Nel mondo frenetico di oggi », « Immergetevi nel mondo di », « Scoprite il mondo di » ;
    - « senza soluzione di continuità » au sens de « seamless », « a 360 gradi », « game changer », « portare al livello successivo », « in un batter d'occhio », « su misura » à répétition (on écrit « personalizzato ») ;
    - « È importante notare che », « Non solo …, ma anche … » à répétition ;
    - les séries de trois adjectifs, les questions rhétoriques en cascade, un « In conclusione » au bout de chaque section.
11. **Anglicismes** : la Chancellerie demande de les éviter quand un équivalent italien existe (Istruzioni, n. 50 à 53). Écrire « intelligenza artificiale » ou « IA » (jamais « AI » seul), « traduzione automatica », « archiviazione », « flusso di lavoro », « in linea ». On garde les termes du métier sans équivalent courant : post-editing, hosting, on-premises, API, benchmark, LegalTech, Legal Ops, et les libellés de l'application (point 3). En italien, l'anglicisme s'écrit en minuscule (n. 52).
12. **Aucune phrase reprise d'un site du groupe** (contrôle par séquences de 8 mots).

## 2. Formats suisses

| Élément | Règle | Exemple | Source |
|---|---|---|---|
| Dates | jour en chiffres, mois en lettres, année | 2 ottobre 2026 · 4 giugno 2024 | Istruzioni, n. 1 |
| Premier du mois | ordinal avec circoletto | 1° ottobre 2026 | Istruzioni, n. 1 ; Fedlex (« in vigore dal 1° gen. 2023 ») |
| Dates en tableau | chiffres séparés par un point, sans zéro initial | 2.10.2026 (et non 02.10.2026) | Istruzioni, n. 2 |
| Heure | point entre heures et minutes | ore 9.30 | Istruzioni, n. 7 |
| Nombres de 0 à 10 | en lettres dans le texte courant ; en chiffres dans les séries, tableaux, chiffres clés et avec une unité | quattro livelli di qualità · 30 lingue · 50 MB | Istruzioni, n. 15 et 16 |
| Milliers | **convention du site** : apostrophe, comme les versions FR et DE et l'usage commercial suisse (Swisscom Business : « Oltre 200'000 clienti commerciali »). Les textes officiels utilisent l'espace protégé : dans une citation de loi, garder la forme Fedlex | 10'000 caratteri · citation : « 100 000 franchi » | Istruzioni, n. 19 et 20 (espace protégé, pas de séparateur de 1000 à 9999) |
| Décimales | virgule ; les centimes après un point | 3,5 milioni · 12.50 franchi | Istruzioni, n. 17 et 18 |
| Montants (s'il en faut un) | dans le texte : nombre puis « franchi » ; en tableau ou entre parenthèses : « CHF » ou « fr. » avant | 15'000 franchi · (CHF 15'000) | Istruzioni, n. 47 et 48 |
| Pourcentages | texte courant : « per cento » en toutes lettres ; badges, chiffres clés, tableaux : symbole précédé d'un espace insécable | il 20 per cento · 100 % | Istruzioni, n. 49 |
| Guillemets | « basses » sans espace intérieur ; à l'intérieur, guillemets anglais | «testo», «la cosiddetta “soft law”» | Istruzioni, n. 22 ; Fedlex (art. 69 LEF : «fare opposizione») |
| Apostrophe | les textes officiels emploient le signe typographique ’ ; le site FR emploie surtout l'apostrophe droite : suivre le segment FR. Dans les champs « source » (« Fedlex, legge … »), écrire le nom de la loi exactement comme dans `termes-it.json` (apostrophe droite) : le build le relie à Fedlex par égalité stricte | l’articolo · Fedlex, legge sul diritto d'autore | Istruzioni, n. 36 |
| Après deux-points | minuscule, sauf nom propre ou citation | Corrext: riprendete il controllo | usage italien |
| Articles de loi | « art. », « cpv. », « lett. », « n. », « segg. », sans virgule entre eux ; abréviation italienne de la loi | art. 104 cpv. 1 CO · art. 305bis CP · art. 80 segg. LEF · art. 4 cpv. 2 lett. a LRD | Istruzioni, n. 72 à 74 et tabella 2 |
| Dans le texte suivi | unités en toutes lettres et en minuscules | secondo l'articolo 1 capoverso 1 lettera c LAVS | Istruzioni, n. 73 |
| Recueils | RS, RU, FF, DTF | RS 220 · DTF + volume + partie en chiffres romains + page · FF 2017 3245 | LPubb, art. 1 ; Istruzioni, n. 76 |
| Ordre des langues | ordre de la Constitution, puis l'anglais | tedesco, francese, italiano e inglese | art. 70 cpv. 1 Cost. ; Istruzioni, n. 151 |
| Villes | nom italien dans le texte quand il existe ; sinon le nom français ; adresse postale inchangée | Friburgo, Ginevra, Zurigo, Berna, Lucerna, Losanna, San Gallo, Svitto, Lugano · Neuchâtel, Bienne, Sion · « Place de la Gare 15, 1700 Fribourg » | art. 1 Cost. ; art. 4 LTF ; Istruzioni, n. 58 |
| Cantons | « Cantone » avec majuscule ; « Cantone di Friburgo », mais « Cantone Ticino », « Cantone dei Grigioni » | il Cantone di Friburgo | Istruzioni, n. 110 et 111 |

Pour Fribourg : « Friburgo » dans le texte (Istruzioni, n. 58 : « Fribourg = Friburgo »). À la première mention sur les pages Chi siamo et Stampa, écrire « Friburgo (Svizzera) » : un lecteur ou un moteur de réponse peut confondre avec Freiburg im Breisgau, en italien « Friburgo in Brisgovia ». « L'État de Fribourg » se dit « il Cantone di Friburgo » (traduction italienne de la Constitution fribourgeoise, RS 131.219, art. 1).

## 3. Vocabulaire suisse et non italien

Chaque ligne est justifiée par le texte fédéral italien en vigueur (Fedlex, relevé le 2 octobre 2026) ou par une institution suisse. Les formes de la colonne de droite n'apparaissent pas dans les textes cités.

| Suisse (à employer) | Italie (à éviter) | Justification |
|---|---|---|
| registro di commercio, estratto del registro di commercio | registro delle imprese, visura camerale | art. 927 CO ; art. 11 ORC (« estratti autenticati ») |
| numero d'identificazione delle imprese (IDI) | partita IVA, codice fiscale comme identifiant de l'entreprise | art. 1 LIDI (RS 431.03) |
| Foglio ufficiale svizzero di commercio | Gazzetta Ufficiale | art. 9 et 11 ORC ; art. 591 CO |
| Raccolta sistematica (RS), Raccolta ufficiale delle leggi federali (RU), Foglio federale (FF) | Gazzetta Ufficiale, Normattiva | art. 1 LPubb (RS 170.512) |
| Tribunale federale, DTF | Corte di cassazione, Corte suprema | art. 188 Cost. ; Istruzioni, n. 76 |
| Consiglio federale, Confederazione, dipartimento | Governo federale, Stato centrale, ministero | art. 174 et 178 Cost. |
| Cantone, cantonale | Regione, Provincia | art. 1 Cost. ; Istruzioni, n. 110 |
| Amministrazione federale delle contribuzioni (AFC) | Agenzia delle Entrate | art. 5 LIP ; art. 7 LIVA |
| Autorità federale di vigilanza sui mercati finanziari (FINMA) | Consob, Banca d'Italia | art. 5 LFINMA |
| Incaricato federale della protezione dei dati e della trasparenza (IFPDT), protezione dei dati | Garante della privacy, « privacy » | art. 4 LPD ; titre de la LPD |
| società anonima (SA) | società per azioni (SpA) | art. 620 CO ; ORC, allegato 2 |
| società a garanzia limitata (Sagl) | società a responsabilità limitata (Srl) | art. 772 CO ; ORC, allegato 2 |
| capitale azionario (SA) ; capitale sociale (Sagl) | capitale sociale pour une SA | art. 621 et 772 CO |
| assemblea generale, consiglio d'amministrazione | assemblea dei soci | art. 698 et 707 CO |
| ufficio di revisione, revisione ordinaria, revisione limitata | collegio sindacale, revisore legale | art. 727 et 727a CO |
| conto annuale, conto di gruppo, relazione sulla gestione | bilancio d'esercizio, bilancio consolidato | art. 958 et 963 CO |
| esecuzione, precetto esecutivo, opposizione, rigetto dell'opposizione | decreto ingiuntivo, atto di precetto | art. 38, 69, 74 et 80 LEF |
| atto scritto (le mémoire d'une partie) | comparsa, memoria | CPC, sezione « Atti scritti delle parti » (art. 130 segg.) ; art. 42 LTF |
| decreto d'accusa | decreto penale di condanna | art. 352 CPP |
| avente economicamente diritto | titolare effettivo | art. 4 LRD |
| imposta preventiva | ritenuta d'acconto sui dividendi | art. 1 LIP |
| registro fondiario | catasto, conservatoria dei registri immobiliari | art. 942 CC |
| porzione legittima | quota di legittima | art. 470 CC |
| disdetta (contrat de travail, bail) ; licenziamento collettivo | licenziamento, dimissioni au sens général | art. 335 et 335d CO |
| contratto collettivo di lavoro | CCNL | art. 356 CO |
| studio legale, avvocato | (même mot qu'en Italie, à conserver) | art. 5 LLCA (RS 935.61) |
| fiduciaria, fiduciario commercialista | commercialista, dottore commercialista | loi tessinoise sur les professions de fiduciaire (LFid, RL 953.100) |

Métier de la traduction (vocabulaire maison, à valider par un traducteur expert, voir `termes-it.json`, type « metier ») :
- devis : **offerta** (décision du 2 octobre 2026) : usage commercial suisse (Swisscom Business), parallèle à « Offerte » en DE, et mot de l'étape « Quotes » de Corrext ; « preventivo » (mot du CO, art. 375) reste un synonyme admis dans le title, la description et le h1 de l'article sur les devis, pour la requête « preventivo traduzione giuridica » ;
- page standard : **pagina standard** ; délai de livraison : **termine di consegna** (délai légal : « termine ») ;
- relecture juridique : **revisione giuridica** ; post-édition : **post-editing**. « revisione » désigne aussi l'audit (« ufficio di revisione ») : écrire « revisione della traduzione » quand le contexte touche aux fiduciaires ou à la comptabilité ;
- traduction certifiée : **traduzione certificata** ; notariée : **traduzione autenticata da un notaio** ; apostillée : **con apostille** (la Cancelleria dello Stato tessinoise emploie « apostille » ; la traduction italienne de la Convention de La Haye, RS 0.172.030.4, dit « postilla ») ;
- niveau 3 de relecture (convention du site, fixée le 2 octobre 2026 pour le DE, reprise ici) :
  - le libellé exact de l'application reste en anglais : « Double review & certified translation », partout où le FR le cite ainsi (titres, tableaux, vignettes) ;
  - dans le texte courant, quand le FR écrit « Double review et traduction certifiée », « Double review avec certificat » ou « Double review certifiée » : **Double review e traduzione certificata** (jamais « doppia revisione », « con certificato » ni « and certified translation ») ;
  - le document signé par l'agence, qui atteste l'exactitude : **attestazione** (pas « certificato », réservé à la certification ISO 27001) ;
  - le niveau 4 : **autenticazione e apostille**, authentification notariale de la signature puis apostille ;
- juriste-linguiste : **giurista linguista** (variante rencontrée : « giurilinguista ») ; traducteur juridique : **traduttore giuridico** ;
- mémoire de traduction : **memoria di traduzione** ; concordancier : **concordanziere** ;
- cabinet ou étude d'avocats : **studio legale** ; direction juridique : **ufficio legale** (dans l'administration : « servizio giuridico »).

Les libellés anglais de l'application restent en anglais (section 1, point 3). Dans le centre d'aide, si Corrext existe en interface italienne, reprendre ses libellés exacts, relevés en lecture seule dans l'application.

Écriture inclusive : la Chancellerie recommande le **masculin inclusif** dans les textes descriptifs, y compris les pages Internet, et les noms collectifs quand ils ne changent pas le sens (« la clientela », « il personale ») (Istruzioni, n. 143 à 147). Pas de doublets systématiques (« avvocate e avvocati »), à la différence du guide DE ; ni astérisque, ni schwa (ə), ni barre oblique.

## 4. Lois et abréviations

Toujours l'abréviation italienne officielle, vérifiée dans Fedlex (`jolux:titleShort` de l'expression ITA, le 2 octobre 2026). Liste complète, avec les titres, dans `termes-it.json` (type « loi »). Les plus fréquentes sur le site :

| FR | IT | FR | IT |
|---|---|---|---|
| CO | CO | LBA | **LRD** |
| CC | CC | LIFD | LIFD |
| LP | **LEF** | LPD | LPD |
| CPC | CPC | LTF | LTF |
| CPP | CPP | LB | **LBCR** |
| CP | CP | LSFin | **LSerFi** |
| LDIP | LDIP | LFINMA | LFINMA |
| LCA | LCA | LFus | LFus |
| LIA | **LIP** | LTVA | **LIVA** |
| ORC | ORC | Cst. | **Cost.** |
| LHID | **LAID** | LPCC | **LICol** |
| LEI | **LStrI** | LTr | **LL** |
| EIMP | **AIMP** | PA | PA |
| RS | RS | FF | FF |
| RO | **RU** | ATF | **DTF** |

En gras : les abréviations qui changent par rapport au FR. « nLPD » reste « nLPD » dans un texte marketing (les Istruzioni la citent en exemple, tabella 1) ; dans une référence juridique, écrire « LPD ». « RGPD » devient « GDPR » (forme courante, non vérifiée dans un texte fédéral).

Noms usuels : « Codice delle obbligazioni » (les textes fédéraux citent ainsi le CO, par exemple l'art. 321 CP), « Codice civile », « Codice penale svizzero », « Codice di procedura civile », « Codice di procedura penale », « legge federale sull'esecuzione e sul fallimento » (le titre officiel garde la forme ancienne « sulla esecuzione »), « Costituzione federale ».

Les mots-vedettes du glossaire restent allemands. Leurs équivalents italiens sont presque tous la forme du texte officiel ; trois demandent de la prudence dans le corps du texte :

| Fiche | Équivalent affiché | Texte officiel italien |
|---|---|---|
| Bankgeheimnis | segreto bancario | l'art. 47 LBCR parle de « segreto professionale » ; « segreto bancario » est l'usage |
| Vollmacht | procura | les art. 32 à 34 CO parlent de « facoltà » (di rappresentanza) ; « procura » est le document des pouvoirs (art. 68 cpv. 3 CPC), mais aussi, dans le CO, la procura commerciale (art. 458, DE « Prokura ») |
| Gewährleistung | garanzia | art. 197 CO, titre marginal « Garanzia pei difetti della cosa » (« pei », forme ancienne de « per i ») |

## 5. Ton, titres et SEO

- **Ton** : expert, précis, sobre, ancré en Suisse. On montre (où sont les données, qui relit, quelle loi), on ne vante pas. Le lecteur est une avocate tessinoise, un banquier de Lugano, un giurista d'impresa : il lit le droit fédéral en italien tous les jours et repère une tournure de l'Italie.
- **Structure des accroches** : garder la forme du FR, « Nom. Promesse » (« Studi legali. Tradurre un dossier senza che lasci mai la Svizzera »).
- **title** : 30 à 62 caractères, la requête principale en tête, puis « · Neur.on ». Exemple glossaire : « Verzugszins: interesse moratorio in tedesco · Neur.on » (53) ; si le titre dépasse 62 caractères : « <Begriff>: definizione · Neur.on ».
- **description** : 110 à 160 caractères, ce que la page apporte, sans formule creuse.
- **h1 et h2** : naturels, porteurs de la requête, jamais une liste de mots-clés.
- **FAQ** : de vraies questions de lecteurs de Suisse italienne, formulées comme on les tape ou les pose à un assistant (« Si possono tradurre contratti riservati con DeepL? »). Réponse directe dans la première phrase.
- **Longueur** : l'italien s'allonge vite (articles, prépositions articulées). La page doit tenir à 375 px : boutons de 25 caractères au plus, menus d'un ou deux mots.
- **Sigles** : article selon le nom complet (« la FINMA », « l'AFC », « il CO ») ; les noms de sociétés et de produits sans article (« Swisscom », « Corrext ») (Istruzioni, n. 101 et 102).

## 6. Vingt formulations maison, FR → IT

| # | Type | FR (site) | IT | Ce que l'exemple montre |
|---|---|---|---|---|
| 1 | Accroche, accueil | Votre solution de traduction par IA pour le droit, la fiscalité et la finance | La vostra soluzione di traduzione con l'IA per il diritto, il fisco e la finanza | « IA » et non « AI » ; requête « traduzione IA diritto » en tête. |
| 2 | Accroche, Corrext | Corrext : reprenez le contrôle de vos traductions | Corrext: riprendete il controllo delle vostre traduzioni | Pas d'espace avant les deux-points, minuscule après. |
| 3 | Accroche, LexMachina | LexMachina. Le moteur qui connaît les lois qu'il traduit | LexMachina. Il motore di traduzione che conosce le leggi che traduce | « motore di traduzione », jamais « LLM ». |
| 4 | Accroche, avocats | Cabinets d'avocats. Traduire un dossier sans jamais le sortir de Suisse | Studi legali. Tradurre un dossier senza che lasci mai la Svizzera | « studio legale » (art. 5 LLCA) ; « dossier » est lemmatisé, sans guillemets. |
| 5 | Chapeau, avocats | Quatre cents pages de pièces à comprendre avant l'audience, un contrat à livrer ce soir, un mémoire à citer au mot près. | Quattrocento pagine di atti da capire prima dell'udienza. Un contratto da consegnare stasera. Un atto scritto da citare alla lettera. | Une énumération longue devient trois phrases ; « mémoire » se dit « atto scritto » (CPC, art. 130 segg.). |
| 6 | Accroche, fiduciaires | Fiduciaires et conseil. Documents d'entreprise traduits et certifiés | Fiduciarie e consulenza. Documenti aziendali tradotti e certificati | « fiduciaria », mot suisse ; « certificati » pour une traduction certifiée. |
| 7 | Accroche, sécurité | Souveraineté des données. Où va votre document, exactement, et qui peut le lire | Sovranità dei dati. Dove va esattamente il vostro documento e chi può leggerlo | Question indirecte, sans point d'interrogation. |
| 8 | Bouton | Demander une démo | Richiedere una demo | Infinitif, comme les boutons d'UBS ; 19 caractères. |
| 9 | Bouton | Essayer Corrext en direct | Provare Corrext dal vivo | Court : tient sur un bouton à 375 px (24 caractères). |
| 10 | Bandeau | Essayez Corrext, sans inscription | Provate Corrext senza registrazione | Impératif pluriel « voi » dans le texte suivi. |
| 11 | Sécurité | Mode Highly sensitive : stockage et traitement exclusivement en Suisse | Modalità Highly sensitive: archiviazione e trattamento esclusivamente in Svizzera | Forme du nom du mode identique au FR ; « trattamento » est le mot de la LPD (art. 5 lett. d). |
| 12 | Sécurité | Hébergement 100% suisse · Infomaniak | Hosting al 100 % in Svizzera · Infomaniak | Espace insécable avant % (Istruzioni, n. 49), point médian conservé. |
| 13 | Sécurité | Hors CLOUD Act. Société suisse, infrastructure suisse : le stockage de vos projets ne relève pas du US CLOUD Act. | Fuori dal CLOUD Act. Società svizzera, infrastruttura svizzera: l'archiviazione dei vostri progetti non rientra nel CLOUD Act statunitense. | Minuscule après les deux-points ; « statunitense » plutôt que « US ». |
| 14 | Sécurité | Aucun entraînement sur vos contenus. LexMachina apprend de corpus juridiques et financiers suisses publics, jamais de vos dossiers. | Nessun addestramento sui vostri contenuti. LexMachina impara da testi giuridici e finanziari svizzeri pubblici, mai dai vostri dossier. | « testi » plutôt que « corpora » ; « dossier » invariable au pluriel. |
| 15 | Sécurité | Le certificat et le périmètre sont remis sur demande, pour votre dossier fournisseur. | Su richiesta vi forniamo il certificato e il campo di applicazione per la vostra documentazione fornitori. | Tournure active à la première personne du pluriel, comme la Chancellerie (Istruzioni, n. 124) ; « campo di applicazione », mot de l'ISO. |
| 16 | Sécurité | Votre politique s'applique au moment du choix, pas dans une charte oubliée | Le vostre regole valgono al momento della scelta, non in un regolamento dimenticato | « regolamento », usage suisse ; pas de « policy ». |
| 17 | Glossaire | Les lois fédérales suisses sont publiées en allemand, en français et en italien, et les trois versions font foi. L'équivalence ci-contre n'est donc pas une traduction d'usage : c'est le terme employé par le texte officiel lui-même. | Le leggi federali sono pubblicate in tedesco, francese e italiano, e ciascuna delle tre versioni è vincolante. L'equivalenza qui accanto non è quindi una traduzione d'uso: è il termine del testo ufficiale stesso. | Reprend les mots de l'art. 14 cpv. 1 LPubb (« ciascuna delle tre versioni è vincolante »). |
| 18 | Glossaire | Source : Fedlex, Code des obligations. Dans Corrext, ce segment et ceux qui l'entourent s'affichent dans Fast lookup CHnell, chacun avec sa référence. | Fonte: Fedlex, Codice delle obbligazioni. In Corrext questo segmento e quelli vicini compaiono in Fast lookup CHnell, ciascuno con il suo riferimento. | Nom de la loi exactement comme dans `termes-it.json` : le build en fait un lien Fedlex. |
| 19 | Glossaire | L'intérêt moratoire est dû dès que le débiteur est en demeure de payer une somme d'argent, indépendamment de tout dommage prouvé. | Gli interessi moratori sono dovuti non appena il debitore è in mora al pagamento di una somma di danaro, indipendentemente da un danno provato. | Reprend les mots de l'art. 104 CO (« in mora al pagamento di una somma di danaro », avec la graphie « danaro » du CO). |
| 20 | Glossaire | Classés par terme allemand. Le glossaire s'étoffe au fil des vérifications de nos juristes-linguistes. | In ordine alfabetico del termine tedesco. Il glossario si arricchisce a ogni verifica dei nostri giuristi linguisti. | Masculin inclusif (Istruzioni, n. 146), « giurista linguista ». |

Autres libellés récurrents (liste complète dans `termes-it.json`, type « interface ») : « En bref » devient « In breve », « Lire l'article » devient « Leggere l'articolo », « Centre d'aide » devient « Centro assistenza », « Voir la plateforme » devient « Alla piattaforma », « Découvrir CHnell » devient « Scoprire CHnell », « Une question reste sans réponse ? » devient « Avete ancora una domanda? », « Accueil » devient « Pagina iniziale » (libellé d'admin.ch).

## 7. Carte des requêtes IT par famille de pages

Requêtes plausibles en Suisse italienne, du point de vue d'une avocate tessinoise, d'un giurista d'impresa ou d'une banque de Lugano. Ce sont des **hypothèses non mesurées** : le marché italophone suisse est petit et les volumes de recherche y sont faibles, souvent mêlés à ceux de l'Italie. Avant de figer les titres, les confronter aux volumes réels (Google Ads Keyword Planner, ciblage Tessin et Grisons italophones ; Search Console après publication). La requête visée page par page figure dans `docs-traduction/routes-it.md`.

| Famille | Requêtes principales | Où les placer |
|---|---|---|
| Produit (Corrext, outils, LexMachina, langues, niveaux) | « software di traduzione giuridica » · « traduzione IA per giuristi » · « traduzione estratto registro di commercio » | title et h1 de l'outil concerné, FAQ produit |
| Sécurité et comparatifs | « sovranità dei dati Svizzera » · « alternativa a DeepL Svizzera » · « ChatGPT segreto professionale » | page Sicurezza, trois comparatifs |
| Solutions par métier | « traduzione per studi legali » · « traduzione finanziaria banca Svizzera » · « traduzione ufficio legale » | une requête par page métier, en title et h1 |
| Domaines du droit | « traduzione contratti » · « traduzione rapporto annuale » · « traduzione statuto società » | title, h1, tableau des termes, FAQ |
| Paires de langues | « traduzione giuridica tedesco francese » · « tradurre contratto inglese tedesco » · « traduttore giuridico francese » | title et h1 de chaque paire |
| Glossaire | « interesse moratorio in tedesco » · « precetto esecutivo tedesco » · « dizionario giuridico tedesco italiano » | title « <Begriff>: <termine italiano> in tedesco · Neur.on », description avec l'équivalent allemand |
| Centre d'aide | « Corrext guida » · « convertire PDF in Word e tradurre » · « Corrext memoria di traduzione » | titres des rubriques, questions des articles |
| Blog et guides | « tradurre un contratto di diritto svizzero » · « costi traduzione giuridica » · « segreto professionale traduzione IA » | title et h1 des articles, bloc « In breve » |

Les actualités visent le nom de l'événement (« Swiss FinTech Awards 2024 », « EPFL Investor Day 2024 ») : pas de réécriture SEO de leurs faits.
