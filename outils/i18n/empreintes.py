"""Empreintes du build : sha256 de chaque fichier texte de la sortie, pour prouver qu'une modification du code de
traduction ne change pas un octet du site français.

Fichiers pris en compte : .html, .xml, .txt et .htaccess, hors du dossier assets/ (les images et polices ne passent pas
par le build de traduction). Le paramètre de version des ressources (« ?v=1a2b3c4d », dérivé du contenu) est neutralisé
avant le calcul : seule sa présence compte.

Commande :  python3 -m outils.i18n.empreintes <sortie> [--ecrire <fichier>]
Sans --ecrire, l'empreinte est affichée en JSON sur la sortie standard. Bibliothèque standard seulement."""
import argparse
import hashlib
import json
import re
import sys
from pathlib import Path

EXTENSIONS = {".html", ".xml", ".txt"}
NOMS = {".htaccess"}
_VERSION = re.compile(rb"\?v=[0-9a-f]{8}")


def _concerne(chemin, sortie):
    relatif = chemin.relative_to(sortie)
    if relatif.parts[0] == "assets":
        return False
    return chemin.suffix in EXTENSIONS or chemin.name in NOMS


def empreintes(sortie):
    """{chemin relatif (« fr/contact/index.html »): sha256 hexadécimal} pour chaque fichier concerné de la sortie."""
    sortie = Path(sortie)
    resultat = {}
    for f in sorted(sortie.rglob("*")):
        if f.is_file() and _concerne(f, sortie):
            contenu = _VERSION.sub(b"?v=", f.read_bytes())
            resultat[f.relative_to(sortie).as_posix()] = hashlib.sha256(contenu).hexdigest()
    return resultat


def main(argv=None):
    p = argparse.ArgumentParser(prog="python3 -m outils.i18n.empreintes", description=__doc__.split("\n")[0])
    p.add_argument("sortie", help="dossier de sortie du build (docs/ ou un dossier temporaire)")
    p.add_argument("--ecrire", metavar="FICHIER", help="écrit l'empreinte dans ce fichier JSON au lieu de l'afficher")
    args = p.parse_args(argv)
    sortie = Path(args.sortie)
    if not sortie.is_dir():
        print(f"Dossier de sortie introuvable : {sortie}", file=sys.stderr)
        return 1
    texte = json.dumps(empreintes(sortie), indent=1, sort_keys=True, ensure_ascii=False) + "\n"
    if args.ecrire:
        Path(args.ecrire).write_text(texte, encoding="utf-8")
        print(f"{len(json.loads(texte))} empreintes écrites dans {args.ecrire}")
    else:
        sys.stdout.write(texte)
    return 0


if __name__ == "__main__":
    sys.exit(main())
