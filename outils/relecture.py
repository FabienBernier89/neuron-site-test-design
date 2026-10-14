#!/usr/bin/env python3
"""Écrit RELECTURE-CONTENUS.md : les contenus nouveaux de la V2 par lot, puis par page, pour la relecture de Fabien.

    python3 outils/relecture.py

Le document est régénéré à chaque appel et n'est pas versionné (voir .gitignore).
"""
import sys
from itertools import groupby
from pathlib import Path

ICI = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ICI))
from outils import contenus  # noqa: E402

SORTIE = ICI / "RELECTURE-CONTENUS.md"
LIBELLES = {"a_relire": "à relire", "valide": "validé"}


def rendre(entrees):
    """Texte du document de relecture pour une liste d'entrées (clé, page, texte, statut, source, lot)."""
    md = ["# Relecture des contenus nouveaux", ""]
    if not entrees:
        return "\n".join(md + ["Aucun contenu nouveau à relire pour le moment.", ""])
    a_relire = sum(1 for e in entrees if e["statut"] == "a_relire")
    pluriel = "s" if len(entrees) > 1 else ""
    md += [f"{len(entrees)} texte{pluriel} : {a_relire} à relire, {len(entrees) - a_relire} validé{'s' if len(entrees) - a_relire > 1 else ''}.", ""]
    for lot, du_lot in groupby(sorted(entrees, key=lambda e: e["lot"]), key=lambda e: e["lot"]):
        md += [f"## Lot {lot}", ""]
        for page, de_la_page in groupby(sorted(du_lot, key=lambda e: e["page"]), key=lambda e: e["page"]):
            md += [f"### {page or 'accueil'}", ""]
            for e in de_la_page:
                md += [f"**`{e['cle']}`** · {LIBELLES.get(e['statut'], e['statut'])} · source : {e['source']}", ""]
                md += ["\n".join("> " + ligne for ligne in e["texte"].splitlines()), ""]
    return "\n".join(md)


def ecrire(sortie=None, dossier=None):
    (sortie or SORTIE).write_text(rendre(contenus.toutes(dossier)), encoding="utf-8")


if __name__ == "__main__":
    ecrire()
    print(f"{SORTIE} écrit")
