"""Commandes de la traduction du site, à lancer depuis la racine du dépôt (NEURON_SRC réglé comme pour build.py).

    python3 -m outils.i18n etat de [--production]
    python3 -m outils.i18n memoire de
    python3 -m outils.i18n lexique de
    python3 -m outils.i18n chnell file de [--priorite-max 3]
    python3 -m outils.i18n chnell ajouter de capital-actions --retenu Aktienkapital --statut confirme ...
    python3 -m outils.i18n chnell lire resultats.json --fr capital-actions --langue de
    python3 -m outils.i18n glossaire --langue de [--arbitrages]
    python3 -m outils.i18n exporter de [--pages accueil contact/] [--statuts mt adapte v1 invariant] [--sortie DOSSIER]
    python3 -m outils.i18n importer de fichier.xlf --relecteur "Prénom Nom" [--sortie DOSSIER] [--sans-etat]
    python3 -m outils.i18n preparer de [--pages accueil corrext/plugin-word/] [--sortie DOSSIER]
    python3 -m outils.i18n fusionner de propositions.json [--simuler]

etat : état de la traduction d'une langue, page par page (outils/i18n/traduire.py, etat), en aperçu par défaut ou selon
les règles de la production ; écrit la liste des textes français à traduire dans src/langues/<langue>/a_traduire.json
({clé: {"fr": texte FR, "contexte": contexte V1 s'il y en a un}}, traduire.fichier_a_traduire), fichier régénéré à
chaque appel. Comme exporter, importer, lexique et memoire, etat lit les pages des deux modes (traduire.pages_union) :
le bandeau de consentement de la production et, en aperçu, le libellé du bandeau de travail sont listés dès le premier
tour.

memoire : pré-remplit la table de la langue (src/langues/<langue>/segments.json) avec les traductions validées de la V1
(outils/i18n/memoire_v1.py, prefill), au statut v1, puis la complète des blocs recomposés et des variantes de balisage
au statut adapte (outils/i18n/recomposition.py, recomposer, tâche 3.2) ; écrit le rapport src/langues/<langue>/memoire-rapport.json et
les contextes V1 des textes à traduire, src/langues/<langue>/contextes.json.

lexique : lexique des termes à vérifier dans CHnell pour une langue (outils/i18n/terminologie.py, candidats, tâche 4.1) :
termes V1, références légales et n-grammes des segments sans traduction V1, avec leur priorité (1, 2 ou 3) et leur
origine. Écrit dans lexique.json du dossier de la terminologie (hors dépôt : Bibliotheque-Claude, variable
NEURON_TERMINOLOGIE), en gardant les décisions « retenu » déjà prises.

chnell : session de vérification dans CHnell (outils/i18n/chnell.py, tâches 4.2 et 4.3). « chnell file » liste les termes
retenus du lexique qui n'ont pas encore de ligne de journal, avec leurs adresses CHnell (priorité 3 au plus par défaut,
décision V5) ; « chnell ajouter » ajoute une ligne au journal.jsonl du dossier de la terminologie (schéma validé, aucun
extrait de texte) ; « chnell lire <fichier.json> --fr <terme> --langue <l> » lit la sortie JSON du script d'extraction
(chnell.EXTRACTION_JS, exécuté dans l'onglet CHnell par l'outil JavaScript de Claude in Chrome) et affiche les équivalents
classés (Fedlex d'abord) avec leurs sources ; elle n'écrit rien dans le journal.

glossaire : construit le glossaire de projet d'une langue d'après le journal (glossaire.json du dossier de la terminologie,
les autres langues sont gardées) : seules les lignes confirme et corrige y entrent, toute divergence avec les termes V1 et
toute ligne a_arbitrer sont des arbitrages pour Fabien (--arbitrages : la liste détaillée). Signale aussi les termes
retenus du lexique sans ligne de journal (critère de la décision V5).

controler : contrôle les traductions de la table d'une langue hors statuts v1 et invariant (outils/i18n/controles.py,
controler_traductions, tâche 4.4) : tirets longs, ß en allemand, marques, termes interdits (bloquants) et terminologie du
glossaire (avertissement). Code de sortie 1 s'il y a un problème bloquant. Sans glossaire, le dit et contrôle le reste.

exporter : fichiers pour les traducteurs experts (outils/i18n/echanges.py, tâche 5.1) : XLIFF 1.2 de la langue
(neur-on-<langue>.xlf, statuts mt, adapte, v1 et invariant par défaut, éventuellement limité à des pages), TMX 1.4 des segments
v1 (neur-on-<langue>-v1.tmx) et glossaire CSV (neur-on-<langue>-glossaire.csv). Dossier par défaut :
Bibliotheque-Claude/07-Ressources-traduction/Neuron/site-v2/<date>-<langue>/ ; un dossier du dépôt est refusé. Produit des
fichiers, n'envoie rien.

preparer : lot d'adaptation d'une langue (Ruling 32, echanges.preparer_lot) : lot-<langue>.json, liste de {cle, fr, mt,
contexte_v1, glossaire} des textes à traduire (a_traduire.json, ou les pages données par --pages, relevées à l'instant) qui
ont une sortie brute de LexMachina dans la table, avec leur contexte (contextes.json) et les lignes utiles du glossaire de
projet. Le fichier va hors du dépôt public (verifier_hors_depot ; par défaut <dossier d'export du jour>/adaptation/) ; les
textes sans sortie brute sont signalés (à passer d'abord par le pont).

fusionner : fusionne dans la table de la langue les propositions d'un agent d'adaptation ou de relecture croisée (fichier JSON
[{"cle", "trad", "note"}], echanges.fusionner, tâche 6.2) au statut adapte (outils/i18n/BRIEF-ADAPTATION.md). Refusés, avec leur
raison, et sans toucher à la table : clé inconnue, marqueurs faux, entrée déjà relue ou validée, tirets, ß en allemand, marques,
termes interdits ; la terminologie n'avertit que. Écrit la table (les propositions acceptées), liste les refus, les
avertissements et les notes de l'agent. Code de sortie 1 s'il y a un refus. --simuler : tout contrôler et rapporter sans écrire la table (vérification avant de rendre
d'un agent). Rejouer ensuite « controler <langue> » et « etat ».

importer : réimporte les corrections d'un relecteur (XLIFF, ou CSV cle;fr;trad) dans la table (tâche 5.2) : segments acceptés
au statut relu (invariant s'ils sont identiques au français), rejets listés avec leur raison, traduction précédente conservée.
Un segment relu doit être confirmé par le relecteur (state translated, final ou signed-off, ou approved="yes", Ruling 31) ; les
autres restent tels quels et sont listés « non confirmé par le relecteur ». --sans-etat : tout segment valide vaut confirmation
(à n'utiliser que pour un outil qui n'écrit pas les états, à décider au pilote). Un segment dont le texte FR a changé sur le
site depuis l'export est rejeté ; sa traduction rendue devient le contexte du nouveau texte (contextes.json) quand il est
identifiable. --export : l'XLIFF d'origine (par défaut neur-on-<langue>.xlf à côté du fichier rendu), pour lister les unités
que le fichier rendu a perdues. Écrit la table, affiche le rapport en français et l'enregistre dans le dossier d'export (rapport-import-<date>-<relecteur>.txt)."""
import argparse
import json
import sys
from datetime import date
from pathlib import Path

from outils.i18n import chnell, controles, echanges, memoire_v1, recomposition, terminologie, traduire
from outils.i18n.table import LANGUES, STATUTS, Table


def afficher_etat(langue, mode, etat, a_traduire):
    """Résumé lisible de l'état d'une langue."""
    pages = etat["pages"]
    publiables = [p for p, e in pages.items() if e["publiable"]]
    lignes = [f"Traduction {langue} ({'production' if mode == 'production' else 'aperçu'}) : "
              f"{len(publiables)} pages publiables sur {len(pages)}"]
    for page, e in pages.items():
        if not e["publiable"]:
            nom = page or "accueil"
            lignes.append(f"  {nom} : {e['manquants']} segment(s) manquant(s), {e['mots']} mot(s) à traduire")
    lignes.append("Segments du site par statut : " + ", ".join(f"{s} {n}" for s, n in etat["segments"].items()))
    lignes.append(f"Mots à traduire : {etat['mots_a_traduire']} ({len(a_traduire)} segments distincts)")
    return "\n".join(lignes)


def afficher_memoire(rapport):
    """Résumé lisible du rapport de la mémoire V1."""
    lignes = [f"Mémoire V1 {rapport['langue']} : {rapport['pages_alignees']} pages alignées, "
              f"{len(rapport['pages_non_alignees'])} non alignées",
              f"Textes posés au statut v1 : {rapport['segments_v1']} (dont {rapport['par_page_v1']} traductions propres à "
              f"une page), {rapport['par_page_seulement']} textes posés pour leurs pages seulement (identiques au français ou doublons divergents), "
              f"{len(rapport['doublons_divergents'])} doublons divergents",
              f"Couverture des mots : {rapport['couverture_mots']} % du contenu (main), "
              f"{rapport['couverture_page']} % de la page entière ; {rapport['couverture_texte']} % du contenu balises "
              f"ignorées (définition de l'audit)"]
    for p in rapport["pages_non_alignees"]:
        lignes.append(f"  non alignée : {p['page'] or 'accueil'} ({p['cause']})")
    for cause, n in rapport["refus"].items():
        lignes.append(f"  refus, {cause} : {n['unites']} unité(s), {n['textes']} texte(s), {n['mots']} mot(s)")
    r = rapport["refus_non_rattrapes"]
    lignes.append(f"Textes refusés jamais posés ailleurs : {r['textes']} ({r['mots']} mots)")
    lignes.append(f"Non posés (traduction V1 non validée) : {rapport['404_non_posee']} textes de la 404, "
                  f"{rapport['i18n_hors_pages']} textes de src/i18n hors des 156 pages")
    r = rapport.get("recomposition")
    if r:
        lignes.append(f"Statut adapte : {r['recomposes']} blocs recomposés, {r['variantes_recalees']} variantes de "
                      f"balisage recalées ({r['variantes_refusees']} refusées)")
        lignes.append(f"Contextes V1 pour l'adaptation : {r['contextes']} textes, dont {r['morceaux']} morceaux et "
                      f"{r['corrections']} corrections V2")
        for cause, n in r["refus"].items():
            lignes.append(f"  refus, {cause} : {n} texte(s)")
    return "\n".join(lignes)


def afficher_lexique(langue, entrees, fichier):
    """Résumé lisible du lexique : comptes par priorité et par origine."""
    c = terminologie.compter(entrees)
    lignes = [f"Lexique {langue} : {c['total']} termes à vérifier"]
    lignes += [f"  priorité {p} : {n}" for p, n in c["priorites"].items()]
    lignes += [f"  origine {o} : {n}" for o, n in c["origines"].items()]
    lignes.append(f"  à valider par Fabien (retenu non décidé) : {sum(1 for e in entrees if e['retenu'] is None)}")
    lignes.append(f"Lexique : {fichier}")
    return "\n".join(lignes)


def afficher_file(langue, file, priorite_max):
    """Termes à vérifier dans CHnell : une ligne par terme, l'adresse Fedlex s'obtient en ajoutant « &sources=60 »."""
    lignes = [f"File CHnell {langue} : {len(file)} terme(s) retenu(s) de priorité 1 à {priorite_max} sans ligne de journal",
              "Concordances de Fedlex seules : ajouter « &sources=60 » à l'adresse (url_fedlex de chnell.file_attente)"]
    lignes += [f"  P{e['priorite']} {e['fr']} : {e['url']}" for e in file]
    return "\n".join(lignes)


def afficher_lecture(fr, langue, page):
    """Équivalents classés d'une page de résultats CHnell (chnell.lire_page) : une ligne par équivalent, avec ses sources,
    puis les références des résultats lus. Le résumé n'est pas écrit dans le journal (« chnell ajouter »)."""
    resultats = page["resultats"]
    lignes = [f"CHnell fr vers {langue}, « {fr} » : "
              + (f"{len(resultats)} résultat(s) lu(s) sur {page['total'] or 'total inconnu'}" if resultats else "aucun résultat"),
              f"Adresse : {chnell.url_chnell(fr, langue)}"]
    if resultats:
        lignes.append("Équivalents surlignés, Fedlex d'abord puis par fréquence :")
        lignes += [f"  {i}. {terme} : {n} occurrence(s), sources : {', '.join(sources) or 'inconnues'}"
                   for i, (terme, n, sources) in enumerate(chnell.equivalents(resultats), 1)]
        lignes.append("Références lues :")
        lignes += [f"  {i}. {r['source'] or 'source inconnue'} : {r['reference']} ({r['domaine']})"
                   for i, r in enumerate(resultats, 1)]
        lignes.append("Rien n'est écrit dans le journal : « chnell ajouter » enregistre la décision (statut, équivalent retenu).")
    return "\n".join(lignes)


def afficher_arbitrages(langue, arbitrages, detail):
    """Nombre d'arbitrages pour Fabien, et leur liste si detail."""
    lignes = [f"Arbitrages pour Fabien : {len(arbitrages)}"]
    if detail:
        for a in arbitrages:
            retenu = f"CHnell « {a['retenu']} »" if a["retenu"] else "aucun équivalent retenu"
            v1 = "V1 " + " ou ".join(f"« {v} »" for v in a["v1"]) if a["v1"] else "pas de terme V1"
            lignes.append(f"  « {a['fr']} » : {retenu} ; {v1} ; {a['raison']}. {a['justification']}")
    return "\n".join(lignes)


def afficher_glossaire(langue, glossaire, arbitrages, detail, restants, fichier):
    """Résumé lisible du glossaire d'une langue : comptes, arbitrages, termes retenus sans ligne de journal."""
    entrees = [langues[langue] for langues in glossaire.values()]
    statuts = {s: sum(1 for e in entrees if e["statut"] == s) for s in chnell.STATUTS_GLOSSAIRE}
    lignes = [f"Glossaire {langue} : {len(entrees)} terme(s) (" + ", ".join(f"{s} {n}" for s, n in statuts.items()) + ")",
              afficher_arbitrages(langue, arbitrages, detail),
              f"{len(restants)} terme(s) retenu(s) de priorité 1 à {chnell.PRIORITE_MAX} sans ligne de journal"
              + (f" (commande : chnell file {langue})" if restants else "")]
    lignes += [f"  P{e['priorite']} {e['fr']}" for e in restants[:20]]
    if len(restants) > 20:
        lignes.append(f"  et {len(restants) - 20} autre(s)")
    lignes.append(f"Glossaire : {fichier}")
    return "\n".join(lignes)


def afficher_controle(langue, controlees, problemes, glossaire):
    """Rapport du contrôle d'une table : bloquants d'abord, puis avertissements de terminologie."""
    bloquants = [p for p in problemes if p["gravite"] == "bloquant"]
    avertissements = [p for p in problemes if p["gravite"] == "avertissement"]
    lignes = [f"Contrôle {langue} : {controlees} traduction(s) hors statuts v1 et invariant, "
              f"{len(bloquants)} problème(s) bloquant(s), {len(avertissements)} avertissement(s) de terminologie"]
    if not glossaire:
        lignes.append("Glossaire absent ou vide pour cette langue : terminologie non contrôlée (commande glossaire, "
                      "après la session CHnell)")
    for titre, groupe in (("Bloquants", bloquants), ("Avertissements de terminologie", avertissements)):
        if groupe:
            lignes.append(f"{titre} :")
            lignes += [f"  {p['lieu']} : {p['regle']}, {p['detail']} : {p['extrait']}" for p in groupe]
    return "\n".join(lignes)


def afficher_export(langue, dossier, resultats, pages, absents=None):
    """Résumé lisible d'un export : fichiers écrits, nombre d'unités, et textes sans traduction non exportés (absents :
    echanges.sans_traduction) avec leurs pages."""
    lignes = [f"Export {langue} : {len(resultats)} fichier(s) dans {dossier}"]
    lignes += [f"  {nom} : {n} {unite}" for nom, n, unite in resultats]
    lignes.append("Périmètre : " + (", ".join(p or echanges.ACCUEIL for p in pages) if pages else "tout le site"))
    absents = absents or {}
    par_page = {}
    for m in absents.values():
        for p in m["pages"]:
            par_page[p] = par_page.get(p, 0) + 1
    lignes.append(f"{len(absents)} texte(s) sans traduction, non exportés, sur {len(par_page)} page(s)"
                  + (" : " + ", ".join(f"{p or echanges.ACCUEIL} ({n})" for p, n in
                                       sorted(par_page.items(), key=lambda x: -x[1])[:10])
                     + (f" et {len(par_page) - 10} autre(s)" if len(par_page) > 10 else "") if absents else ""))
    return "\n".join(lignes)


def afficher_import(langue, rapport, fichier, relecteur):
    """Rapport de réimport en français : comptes, corrections, rejets (traduction précédente conservée), avertissements."""
    lignes = [f"Réimport {langue}, relecteur {relecteur} : {rapport['relus']} segment(s) relu(s) "
              f"(dont {rapport['invariants']} posé(s) invariant, identique au français), {len(rapport['modifies'])} modifié(s), "
              f"{len(rapport['rejetes'])} rejeté(s), {len(rapport['non_confirmes'])} non confirmé(s) par le relecteur, "
              f"{len(rapport['avertissements'])} avertissement(s) de terminologie",
              f"Dont {rapport['mt_adapte_intacts']} segment(s) mt ou adapte confirmé(s) sans aucune modification",
              f"Dont {rapport['v1_intacts']} traduction(s) V1 confirmée(s) sans modification (provenance V1 gardée)",
              f"Fichier lu : {fichier}"]
    absents = rapport.get("absents")
    if absents is None:
        lignes.append("Export d'origine non fourni (--export) : unités exportées absentes du fichier rendu non contrôlées")
    elif absents:
        lignes.append(f"Unités de l'export absentes du fichier rendu ({len(absents)}), laissées telles quelles :")
        lignes += [f"  {a['cle']} « {a['fr'][:60]} »" for a in absents]
    else:
        lignes.append("Toutes les unités de l'export sont dans le fichier rendu")
    if rapport.get("reorientes"):
        lignes.append("Textes modifiés sur le site depuis l'export : traduction rendue gardée en contexte du nouveau texte "
                      "(contextes.json), à adapter puis à relire :")
        lignes += [f"  {r['cle']} -> {r['nouvelle_cle']} « {r['fr'][:60]} »" for r in rapport["reorientes"]]
    if rapport["modifies"]:
        lignes.append("Corrections appliquées :")
        for m in rapport["modifies"]:
            pages = ", ".join(m["pages"]) + (f" et {m['autres_pages']} autre(s)" if m["autres_pages"] else "")
            lignes.append(f"  {m['cle']} [{pages or 'pages inconnues'}] « {m['fr'][:60]} »")
            lignes.append(f"    avant : {m['avant']}")
            lignes.append(f"    après : {m['apres']}")
    if rapport["rejetes"]:
        lignes.append("Rejetés (traduction et statut précédents conservés) :")
        for r in rapport["rejetes"]:
            lignes.append(f"  {r['cle']} « {r['fr'][:60]} » : {r['raison']}" + (f", {r['detail']}" if r["detail"] else ""))
    if rapport["non_confirmes"]:
        lignes.append("Non confirmés par le relecteur (segments laissés tels quels, jamais relus) :")
        for r in rapport["non_confirmes"]:
            lignes.append(f"  {r['cle']} « {r['fr'][:60]} »" + (" : texte modifié dans le fichier, non appliqué"
                                                                  if r["modifie"] else ""))
    if rapport["avertissements"]:
        lignes.append("Avertissements de terminologie (à revoir par un humain, rien n'est rejeté) :")
        lignes += [f"  {a['cle']} : {a['detail']}" for a in rapport["avertissements"]]
    return "\n".join(lignes)


def afficher_fusion(langue, rapport, fichier):
    """Rapport de fusion en français : posées, refus avec leur raison, avertissements de terminologie, notes de l'agent."""
    lignes = [f"Fusion {langue} : {rapport['poses']} proposition(s) posée(s) au statut adapte, {len(rapport['refuses'])} refusée(s), "
              f"{len(rapport['avertissements'])} avertissement(s) de terminologie, {len(rapport['notes'])} note(s) de l'agent",
              f"Fichier lu : {fichier}"]
    if rapport["refuses"]:
        lignes.append("Refusées (table inchangée pour ces propositions) :")
        for r in rapport["refuses"]:
            lignes.append(f"  {r['cle']} « {r['fr'][:60]} » : {r['raison']}" + (f", {r['detail']}" if r["detail"] else ""))
    if rapport["avertissements"]:
        lignes.append("Avertissements de terminologie (à revoir par un humain, rien n'est refusé) :")
        lignes += [f"  {a['cle']} : {a['detail']}" for a in rapport["avertissements"]]
    if rapport["notes"]:
        lignes.append("Notes de l'agent (à faire trancher par un traducteur expert) :")
        lignes += [f"  {n['cle']} « {n['fr'][:60]} » : {n['note']}" for n in rapport["notes"]]
    return "\n".join(lignes)


def commande_preparer(args, build):
    """preparer : lot d'adaptation (FR, sortie brute, contexte V1, glossaire) hors du dépôt public."""
    from outils.i18n import pont_corrext
    table = Table(args.langue, build.DOSSIER_LANGUES)
    dossier = Path(args.sortie) if args.sortie else echanges.dossier_export(args.langue) / "adaptation"
    fichier = dossier / f"lot-{args.langue}.json"
    langue = build.DOSSIER_LANGUES / args.langue
    try:
        echanges.verifier_hors_depot(fichier)
        a_traduire = json.loads((langue / "a_traduire.json").read_text(encoding="utf-8")) \
            if (langue / "a_traduire.json").is_file() else {}
        if not a_traduire and not args.pages:
            raise ValueError(f"{langue / 'a_traduire.json'} introuvable ou vide : lancer d'abord « etat {args.langue} »")
        contextes = json.loads((langue / traduire.CONTEXTES).read_text(encoding="utf-8")) \
            if (langue / traduire.CONTEXTES).is_file() else {}
        textes = pont_corrext.textes_des_pages(args.langue, args.pages, table) if args.pages else None
        glossaire = {fr: l for fr, l in chnell.charger_glossaire().items() if args.langue in l}
        lot, sans_mt = echanges.preparer_lot(table, a_traduire, contextes, glossaire, textes)
    except ValueError as e:
        print(f"Lot non préparé : {e}", file=sys.stderr)
        return 1
    dossier.mkdir(parents=True, exist_ok=True)
    fichier.write_text(json.dumps(lot, indent=1, ensure_ascii=False) + "\n", encoding="utf-8")
    print(f"Lot d'adaptation {args.langue} : {len(lot)} segment(s), dont {sum(1 for x in lot if x['contexte_v1'])} avec un "
          f"contexte et {sum(1 for x in lot if x['glossaire'])} avec des termes du glossaire : {fichier}")
    if not glossaire:
        print("Glossaire vide pour cette langue : aucune ligne de glossaire dans le lot (commande glossaire, après la "
              "session CHnell)")
    if sans_mt:
        print(f"{len(sans_mt)} texte(s) sans sortie brute de LexMachina, hors du lot (passer d'abord par le pont) : "
              + ", ".join(sorted(sans_mt)[:10]) + (" ..." if len(sans_mt) > 10 else ""))
    return 0


def commande_fusionner(args, build):
    """fusionner : propositions d'un agent dans la table, au statut adapte."""
    table = Table(args.langue, build.DOSSIER_LANGUES)
    try:
        rapport = echanges.fusionner(Path(args.fichier), table, args.statut)
    except ValueError as e:
        print(f"Fusion refusée, table inchangée : {e}", file=sys.stderr)
        return 1
    if not args.simuler:
        table.enregistrer()
    print(afficher_fusion(args.langue, rapport, args.fichier))
    print("Simulation : table non écrite." if args.simuler else f"Table : {table.fichier}")
    return 1 if rapport["refuses"] else 0


def commande_exporter(args, build):
    """exporter : XLIFF, TMX et glossaire CSV dans un dossier hors du dépôt."""
    table = Table(args.langue, build.DOSSIER_LANGUES)
    dossier = Path(args.sortie) if args.sortie else echanges.dossier_export(args.langue)
    try:
        echanges.verifier_hors_depot(dossier)
        assemblees = traduire.pages_union(args.langue)
        pages = [("" if p == echanges.ACCUEIL else p) for p in args.pages] if args.pages else None
        inconnues = [p for p in pages or [] if p not in assemblees and p not in echanges.PSEUDO_PAGES]
        if inconnues:
            raise ValueError("page(s) inconnue(s) : " + ", ".join(inconnues) + " (clés de page : accueil, contact/, ...)")
        glossaire = {fr: l for fr, l in chnell.charger_glossaire().items() if args.langue in l}
        absents = echanges.sans_traduction(args.langue, table, None if pages is None else set(pages), assemblees)
        statuts = set(args.statuts or echanges.STATUTS_XLIFF_PAR_DEFAUT)
        nom = f"neur-on-{args.langue}"
        resultats = [(f"{nom}.xlf", echanges.exporter_xliff(args.langue, table, pages, statuts, dossier / f"{nom}.xlf",
                                                         assemblees=assemblees, glossaire=glossaire), "unité(s) XLIFF"),
                     (f"{nom}-v1.tmx", echanges.exporter_tmx(args.langue, table, {"v1"}, dossier / f"{nom}-v1.tmx"),
                      "unité(s) de traduction TMX"),
                     (f"{nom}-glossaire.csv", echanges.exporter_glossaire_csv(args.langue, glossaire,
                                                                              dossier / f"{nom}-glossaire.csv"), "terme(s)")]
    except ValueError as e:
        print(f"Export refusé : {e}", file=sys.stderr)
        return 1
    print(afficher_export(args.langue, dossier, resultats, pages, absents))
    if not glossaire:
        print("Glossaire vide pour cette langue : le CSV ne contient que son en-tête (commande glossaire, après la "
              "session CHnell)")
    return 0


def commande_importer(args, build):
    """importer : corrections d'un relecteur dans la table, rapport en français enregistré dans le dossier d'export."""
    fichier = Path(args.fichier)
    if not fichier.is_file():
        print(f"Fichier introuvable : {fichier}", file=sys.stderr)
        return 1
    table = Table(args.langue, build.DOSSIER_LANGUES)
    dossier = Path(args.sortie) if args.sortie else echanges.dossier_export(args.langue)
    try:
        echanges.verifier_hors_depot(dossier)  # avant tout : un échec ne laisse rien d'écrit
        glossaire = {fr: l for fr, l in chnell.charger_glossaire().items() if args.langue in l}
        importer = echanges.importer_csv if fichier.suffix.lower() == ".csv" else echanges.importer_xliff
        options = {}
        if importer is echanges.importer_xliff:
            export = Path(args.export) if args.export else fichier.parent / f"neur-on-{args.langue}.xlf"
            options = {"sans_etat": args.sans_etat,
                       "export": export if export.is_file() and export.resolve() != fichier.resolve() else None}
            if args.export and options["export"] is None:
                raise ValueError(f"export d'origine introuvable : {export}")
        rapport = importer(fichier, table, args.relecteur, glossaire=glossaire,
                           assemblees=traduire.pages_union(args.langue), **options)
    except ValueError as e:
        print(f"Import refusé, table inchangée : {e}", file=sys.stderr)
        return 1
    table.enregistrer()
    if rapport["reorientes"]:
        f_contextes = table.fichier.parent / traduire.CONTEXTES
        contextes = json.loads(f_contextes.read_text(encoding="utf-8")) if f_contextes.is_file() else {}
        f_contextes.write_text(json.dumps(echanges.contextes_reorientes(contextes, rapport), indent=1,
                                          ensure_ascii=False) + "\n", encoding="utf-8")
    texte = afficher_import(args.langue, rapport, fichier, args.relecteur)
    jour = date.today().isoformat()
    base = f"rapport-import-{jour}-{echanges.nom_pour_fichier(args.relecteur)}"
    rapport_fichier, n = dossier / f"{base}.txt", 1
    while rapport_fichier.exists():
        n += 1
        rapport_fichier = dossier / f"{base}-{n}.txt"
    dossier.mkdir(parents=True, exist_ok=True)
    rapport_fichier.write_text(texte + "\n", encoding="utf-8")
    print(texte)
    print(f"Table : {table.fichier}\nRapport : {rapport_fichier}")
    return 0


def commande_chnell(args):
    """chnell file, ajouter et lire : n'ont besoin ni du site V1 ni de build.py."""
    if args.action == "lire":
        fichier = Path(args.fichier)
        if not fichier.is_file():
            print(f"Fichier introuvable : {fichier} (sortie JSON du script d'extraction, chnell.EXTRACTION_JS)", file=sys.stderr)
            return 1
        try:
            page = chnell.lire_page(fichier.read_text(encoding="utf-8"))
        except ValueError as e:
            print(f"Lecture impossible : {e}", file=sys.stderr)
            return 1
        print(afficher_lecture(args.fr, args.langue, page))
        return 0
    if args.action == "file":
        lexique = terminologie.charger_lexique(args.langue)
        if not lexique:
            print(f"Lexique {args.langue} introuvable ou vide : lancer d'abord « lexique {args.langue} »", file=sys.stderr)
            return 1
        file = chnell.file_attente(args.langue, lexique, chnell.charger_journal(), args.priorite_max)
        print(afficher_file(args.langue, file, args.priorite_max))
        return 0
    entree = {"date": args.date, "fr": args.fr, "langue": args.langue,
              "url": args.url or chnell.url_chnell(args.fr, args.langue), "resultats": args.resultats,
              "sources": args.source, "retenu": args.retenu, "statut": args.statut,
              "justification": args.justification, "verifie_par": args.verifie_par}
    try:
        chnell.ajouter(chnell.fichier_journal(), entree)
    except ValueError as e:
        print(f"Ligne refusée, journal inchangé : {e}", file=sys.stderr)
        return 1
    print(f"Journal : « {args.fr} » ({args.langue}) ajouté au statut {args.statut} : {chnell.fichier_journal()}")
    return 0


def main(argv=None):
    parser = argparse.ArgumentParser(prog="python3 -m outils.i18n", description="Outils de la traduction du site.")
    sous = parser.add_subparsers(dest="commande", required=True)
    p = sous.add_parser("etat", help="état de la traduction d'une langue")
    p.add_argument("langue", choices=LANGUES)
    p.add_argument("--production", action="store_true", help="règles de la production (statuts relus seulement)")
    p = sous.add_parser("memoire", help="pré-remplir la table d'une langue avec la mémoire validée de la V1")
    p.add_argument("langue", choices=LANGUES)
    p = sous.add_parser("lexique", help="lexique des termes à vérifier dans CHnell pour une langue")
    p.add_argument("langue", choices=LANGUES)
    p = sous.add_parser("chnell", help="session de vérification dans CHnell : file d'attente, journal")
    actions = p.add_subparsers(dest="action", required=True)
    a = actions.add_parser("file", help="termes retenus du lexique sans ligne de journal, avec leurs adresses CHnell")
    a.add_argument("langue", choices=LANGUES)
    a.add_argument("--priorite-max", type=int, default=chnell.PRIORITE_MAX, help="priorité la plus basse vérifiée (3)")
    a = actions.add_parser("ajouter", help="ajouter une ligne au journal (schéma validé, aucun extrait de texte)")
    a.add_argument("langue", choices=LANGUES)
    a.add_argument("fr", help="terme français vérifié")
    a.add_argument("--statut", required=True, help="confirme, corrige, absent ou a_arbitrer")
    a.add_argument("--retenu", help="équivalent retenu (absent pour le statut absent)")
    a.add_argument("--resultats", type=int, default=0, help="nombre de résultats CHnell")
    a.add_argument("--source", action="append", default=[], help="source des concordances, répétable (« Fedlex : CO art. 620 »)")
    a.add_argument("--justification", required=True, help="une phrase, jamais un extrait de texte")
    a.add_argument("--verifie-par", default="agent", help="agent ou Fabien (un arbitrage de Fabien)")
    a.add_argument("--date", default=date.today().isoformat(), help="AAAA-MM-JJ (aujourd'hui par défaut)")
    a.add_argument("--url", help="adresse CHnell consultée (url_chnell par défaut)")
    a = actions.add_parser("lire", help="lire la sortie JSON du script d'extraction CHnell et classer les équivalents")
    a.add_argument("fichier", help="fichier JSON écrit à partir de la sortie de chnell.EXTRACTION_JS")
    a.add_argument("--fr", required=True)
    a.add_argument("--langue", required=True, choices=LANGUES)
    p = sous.add_parser("glossaire", help="construire le glossaire de projet d'une langue d'après le journal")
    p.add_argument("--langue", required=True, choices=LANGUES)
    p.add_argument("--arbitrages", action="store_true", help="liste détaillée des arbitrages pour Fabien")
    p = sous.add_parser("controler", help="contrôler les traductions de la table d'une langue (hors v1 et invariant)")
    p.add_argument("langue", choices=LANGUES)
    p = sous.add_parser("exporter", help="XLIFF 1.2, TMX 1.4 et glossaire CSV pour les traducteurs experts")
    p.add_argument("langue", choices=LANGUES)
    p.add_argument("--pages", nargs="+", help="limiter l'XLIFF à ces pages (accueil, contact/, ...) ; tout le site par défaut")
    p.add_argument("--statuts", nargs="+", choices=STATUTS,
                   help="statuts exportés dans l'XLIFF (" + ", ".join(echanges.STATUTS_XLIFF_PAR_DEFAUT) + " par défaut)")
    p.add_argument("--sortie", help="dossier de sortie (Bibliotheque-Claude/07-Ressources-traduction/Neuron/site-v2/<date>-<langue>/)")
    p = sous.add_parser("importer", help="réimporter les corrections d'un relecteur (XLIFF ou CSV cle;fr;trad)")
    p.add_argument("langue", choices=LANGUES)
    p.add_argument("fichier")
    p.add_argument("--relecteur", required=True, help="nom du relecteur (écrit dans la source des segments relus)")
    p.add_argument("--sortie", help="dossier du rapport (le dossier d'export du jour par défaut)")
    p.add_argument("--sans-etat", action="store_true",
                   help="tout segment valide vaut confirmation, sans lire state ni approved (outil qui n'écrit pas les états)")
    p.add_argument("--export", help="XLIFF d'origine, pour lister ses unités absentes du fichier rendu "
                                    "(par défaut neur-on-<langue>.xlf à côté du fichier rendu, s'il existe)")
    p = sous.add_parser("preparer", help="lot d'adaptation d'une langue (FR, sortie brute, contexte V1, glossaire)")
    p.add_argument("langue", choices=LANGUES)
    p.add_argument("--pages", nargs="+", help="ne prendre que les textes de ces pages (accueil, contact/, ...)")
    p.add_argument("--sortie", help="dossier du lot, hors du dépôt (<dossier d'export du jour>/adaptation/ par défaut)")
    p = sous.add_parser("fusionner", help="fusionner les propositions d'un agent d'adaptation (JSON [{cle, trad, note}])")
    p.add_argument("langue", choices=LANGUES)
    p.add_argument("fichier", help="propositions.json ou relecture.json")
    p.add_argument("--statut", default=echanges.STATUT_FUSION, help="statut posé (adapte, le seul permis)")
    p.add_argument("--simuler", action="store_true", help="contrôler et rapporter sans écrire la table")
    args = parser.parse_args(argv)
    if args.commande == "chnell":
        return commande_chnell(args)
    import build  # import tardif : les dossiers de build.py (DOSSIER_LANGUES, NEURON) servent d'emplacement
    if args.commande == "exporter":
        return commande_exporter(args, build)
    if args.commande == "importer":
        return commande_importer(args, build)
    if args.commande == "fusionner":
        return commande_fusionner(args, build)
    if args.commande == "preparer":
        return commande_preparer(args, build)
    if args.commande == "glossaire":
        fichier_v1 = build.NEURON / "src/i18n" / f"termes-{args.langue}.json"
        if not fichier_v1.is_file():
            print(f"Termes V1 introuvables : {fichier_v1} (NEURON_SRC ?)", file=sys.stderr)
            return 1
        termes = {args.langue: json.loads(fichier_v1.read_text(encoding="utf-8"))}
        journal = [e for e in chnell.charger_journal() if e["langue"] == args.langue]
        glossaire = chnell.construire_glossaire(journal, termes)
        fichier = chnell.ecrire_glossaire(glossaire, args.langue)
        restants = chnell.file_attente(args.langue, terminologie.charger_lexique(args.langue), journal, chnell.PRIORITE_MAX)
        print(afficher_glossaire(args.langue, glossaire, chnell.arbitrages(journal, termes), args.arbitrages, restants,
                                 fichier))
        return 0
    if args.commande == "controler":
        table = Table(args.langue, build.DOSSIER_LANGUES)
        glossaire = {fr: l for fr, l in chnell.charger_glossaire().items() if args.langue in l}
        controlees, problemes = controles.controler_traductions(args.langue, table.entrees, glossaire)
        print(afficher_controle(args.langue, controlees, problemes, glossaire))
        return 1 if any(p["gravite"] == "bloquant" for p in problemes) else 0
    if args.commande == "lexique":
        fichier_v1 = build.NEURON / "src/i18n" / f"termes-{args.langue}.json"
        if not fichier_v1.is_file():
            print(f"Termes V1 introuvables : {fichier_v1} (NEURON_SRC ?)", file=sys.stderr)
            return 1
        termes = json.loads(fichier_v1.read_text(encoding="utf-8"))
        table = Table(args.langue, build.DOSSIER_LANGUES)
        if not table.entrees:
            print(f"Avertissement : table {args.langue} vide ({table.fichier}) : aucun texte n'a de traduction V1, tous "
                  f"comptent comme nouveaux (lancer d'abord « memoire {args.langue} »)", file=sys.stderr)
        entrees = terminologie.candidats(args.langue, table, termes)
        entrees = terminologie.conserver_decisions(entrees, terminologie.charger_lexique(args.langue))
        fichier = terminologie.ecrire_lexique(args.langue, entrees)
        print(afficher_lexique(args.langue, entrees, fichier))
        return 0
    if args.commande == "memoire":
        table = Table(args.langue, build.DOSSIER_LANGUES)
        pages = traduire.pages_union(args.langue)
        recomposition.retirer_recompositions(table)  # passe précédente retirée avant prefill : commande idempotente
        rapport = memoire_v1.prefill(args.langue, build.NEURON, table, pages=pages)
        resultat = recomposition.recomposer(args.langue, build.NEURON, table, pages=pages)
        contextes = resultat.pop("contextes")
        rapport["recomposition"] = {**resultat, "contextes": len(contextes)}
        table.enregistrer()
        dossier = build.DOSSIER_LANGUES / args.langue
        fichier = dossier / "memoire-rapport.json"
        fichier.write_text(json.dumps(rapport, indent=1, ensure_ascii=False) + "\n", encoding="utf-8")
        f_contextes = dossier / traduire.CONTEXTES
        anciens = json.loads(f_contextes.read_text(encoding="utf-8")) if f_contextes.is_file() else {}
        # les contextes posés par un réimport (texte FR modifié depuis l'export) survivent au recalcul de la mémoire
        contextes = echanges.garder_contextes_relecture(anciens, contextes)
        f_contextes.write_text(json.dumps(contextes, indent=1, ensure_ascii=False) + "\n", encoding="utf-8")
        print(afficher_memoire(rapport))
        print(f"Table : {table.fichier}\nRapport : {fichier}\nContextes : {dossier / traduire.CONTEXTES}")
        return 0
    mode = "production" if args.production else "apercu"
    etat, a_traduire = traduire.etat_detaille(args.langue, mode)
    fichier = build.DOSSIER_LANGUES / args.langue / "a_traduire.json"
    fichier.parent.mkdir(parents=True, exist_ok=True)
    f_contextes = fichier.parent / traduire.CONTEXTES
    contextes = json.loads(f_contextes.read_text(encoding="utf-8")) if f_contextes.is_file() else {}
    fichier.write_text(json.dumps(traduire.fichier_a_traduire(a_traduire, contextes), indent=1, ensure_ascii=False)
                       + "\n", encoding="utf-8")
    print(afficher_etat(args.langue, mode, etat, a_traduire))
    print(f"Liste des segments à traduire : {fichier}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
