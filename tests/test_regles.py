"""Règles d'écriture : tirets longs, référence jamais nommée, termes interdits (spec § 2, tests 5 à 7)."""
import re
import subprocess
import sys
import unittest
from pathlib import Path

ICI = Path(__file__).resolve().parent.parent
MOT = "doc" + "trine"  # composé pour ne pas l'écrire en clair
INTERDITS = [r"Legal ?230", r"\bLexa\b", r"Neur\.on LLM(?!s)", r"\brapprochement"]
# « Neur.on LLM(?!s) » : le nom du moteur retiré, pas la phrase allemande « wie Neur.on LLMs trainiert » (Neur.on entraîne
# des LLM), sujet puis complément
# dossiers de travail non publiés : .superpowers (briefs, qui citent légitimement les termes interdits), .claude (copies du dépôt)
IGNORES = {".git", "__pycache__", ".superpowers", ".claude"}
# fixture volontairement fautive (tâche 0.1) : elle contient les termes interdits pour que les contrôles les attrapent
FIXTURES_FAUTIVES = {"page-de-fautive.html"}
BINAIRES = {".png", ".jpg", ".jpeg", ".webp", ".ico", ".pyc", ".woff2"}


def fichiers():
    for f in ICI.rglob("*"):
        parties = f.relative_to(ICI).parts  # relatif : le dépôt peut lui-même vivre sous .claude/worktrees/
        if (set(parties) & IGNORES) or f.name in FIXTURES_FAUTIVES or not f.is_file() or f.suffix in BINAIRES:
            continue
        yield f


class TestRegles(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        subprocess.run([sys.executable, str(ICI / "build.py")], check=True, cwd=ICI, stdout=subprocess.DEVNULL)

    def test_pas_de_tirets_longs(self):
        for f in fichiers():
            t = f.read_text(encoding="utf-8", errors="ignore")
            self.assertNotIn("\u2014", t, str(f))
            self.assertNotIn("\u2013", t, str(f))

    def test_reference_jamais_nommee(self):
        for f in fichiers():
            self.assertNotIn(MOT, f.read_text(encoding="utf-8", errors="ignore").casefold(), str(f))
            self.assertNotIn(MOT, str(f.relative_to(ICI)).casefold())

    def test_motif_du_moteur_retire(self):
        motif = INTERDITS[2]
        self.assertIsNotNone(re.search(motif, "le moteur Neur.on LLM"))
        self.assertIsNotNone(re.search(motif, "Neur.on LLM, notre moteur"))
        self.assertIsNone(re.search(motif, "wie Neur.on LLMs trainiert"))

    def test_termes_interdits(self):
        for f in fichiers():
            if f.suffix not in (".html", ".js", ".css", ".md"):
                continue
            t = f.read_text(encoding="utf-8", errors="ignore")
            for motif in INTERDITS:
                self.assertIsNone(re.search(motif, t), f"{f} : {motif}")


if __name__ == "__main__":
    unittest.main()
