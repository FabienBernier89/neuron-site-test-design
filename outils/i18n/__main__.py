"""Commandes de la traduction du site, à lancer depuis la racine du dépôt (NEURON_SRC réglé comme pour build.py).

    python3 -m outils.i18n etat de [--production]

etat : état de la traduction d'une langue, page par page (outils/i18n/traduire.py, etat), en aperçu par défaut ou selon
les règles de la production ; écrit la liste des textes français à traduire dans src/langues/<langue>/a_traduire.json
({clé: texte FR}), fichier régénéré à chaque appel."""
import argparse
import json
import sys

from outils.i18n import traduire
from outils.i18n.table import LANGUES


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


def main(argv=None):
    parser = argparse.ArgumentParser(prog="python3 -m outils.i18n", description="Outils de la traduction du site.")
    sous = parser.add_subparsers(dest="commande", required=True)
    p = sous.add_parser("etat", help="état de la traduction d'une langue")
    p.add_argument("langue", choices=LANGUES)
    p.add_argument("--production", action="store_true", help="règles de la production (statuts relus seulement)")
    args = parser.parse_args(argv)
    import build  # import tardif : les dossiers de build.py (DOSSIER_LANGUES) servent d'emplacement
    mode = "production" if args.production else "apercu"
    etat, a_traduire = traduire.etat_detaille(args.langue, mode)
    fichier = build.DOSSIER_LANGUES / args.langue / "a_traduire.json"
    fichier.parent.mkdir(parents=True, exist_ok=True)
    fichier.write_text(json.dumps(dict(sorted(a_traduire.items())), indent=1, ensure_ascii=False) + "\n", encoding="utf-8")
    print(afficher_etat(args.langue, mode, etat, a_traduire))
    print(f"Liste des segments à traduire : {fichier}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
