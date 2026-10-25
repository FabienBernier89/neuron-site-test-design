"""Commandes de la traduction du site, à lancer depuis la racine du dépôt (NEURON_SRC réglé comme pour build.py).

    python3 -m outils.i18n etat de [--production]
    python3 -m outils.i18n memoire de

etat : état de la traduction d'une langue, page par page (outils/i18n/traduire.py, etat), en aperçu par défaut ou selon
les règles de la production ; écrit la liste des textes français à traduire dans src/langues/<langue>/a_traduire.json
({clé: {"fr": texte FR, "contexte": contexte V1 s'il y en a un}}, traduire.fichier_a_traduire), fichier régénéré à
chaque appel.

memoire : pré-remplit la table de la langue (src/langues/<langue>/segments.json) avec les traductions validées de la V1
(outils/i18n/memoire_v1.py, prefill), au statut v1, puis la complète des blocs recomposés et des variantes de balisage
au statut adapte (memoire_v1.recomposer, tâche 3.2) ; écrit le rapport src/langues/<langue>/memoire-rapport.json et
les contextes V1 des textes à traduire, src/langues/<langue>/contextes.json."""
import argparse
import json
import sys

from outils.i18n import memoire_v1, traduire
from outils.i18n.table import LANGUES, Table


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


def main(argv=None):
    parser = argparse.ArgumentParser(prog="python3 -m outils.i18n", description="Outils de la traduction du site.")
    sous = parser.add_subparsers(dest="commande", required=True)
    p = sous.add_parser("etat", help="état de la traduction d'une langue")
    p.add_argument("langue", choices=LANGUES)
    p.add_argument("--production", action="store_true", help="règles de la production (statuts relus seulement)")
    p = sous.add_parser("memoire", help="pré-remplir la table d'une langue avec la mémoire validée de la V1")
    p.add_argument("langue", choices=LANGUES)
    args = parser.parse_args(argv)
    import build  # import tardif : les dossiers de build.py (DOSSIER_LANGUES, NEURON) servent d'emplacement
    if args.commande == "memoire":
        table = Table(args.langue, build.DOSSIER_LANGUES)
        pages = traduire.pages_assemblees(args.langue, "apercu")
        rapport = memoire_v1.prefill(args.langue, build.NEURON, table, pages=pages)
        recomposition = memoire_v1.recomposer(args.langue, build.NEURON, table, pages=pages)
        contextes = recomposition.pop("contextes")
        rapport["recomposition"] = {**recomposition, "contextes": len(contextes)}
        table.enregistrer()
        dossier = build.DOSSIER_LANGUES / args.langue
        fichier = dossier / "memoire-rapport.json"
        fichier.write_text(json.dumps(rapport, indent=1, ensure_ascii=False) + "\n", encoding="utf-8")
        (dossier / traduire.CONTEXTES).write_text(json.dumps(contextes, indent=1, ensure_ascii=False) + "\n",
                                                  encoding="utf-8")
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
