"""Règles d'écriture : tirets longs, référence jamais nommée, termes interdits (spec § 2, tests 5 à 7)."""
import re
import subprocess
import sys
import unittest
from pathlib import Path

ICI = Path(__file__).resolve().parent.parent
MOT = "doc" + "trine"  # composé pour ne pas l'écrire en clair
INTERDITS = [r"Legal ?230", r"\bLexa\b", r"Neur\.on LLM", r"\brapprochement"]
BINAIRES = {".png", ".jpg", ".jpeg", ".webp", ".ico", ".pyc", ".woff2"}


def fichiers():
    for f in ICI.rglob("*"):
        if ".git" in f.parts or "__pycache__" in f.parts or not f.is_file() or f.suffix in BINAIRES:
            continue
        yield f


class TestRegles(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        subprocess.run([sys.executable, str(ICI / "build.py")], check=True, cwd=ICI)

    def test_pas_de_tirets_longs(self):
        for f in fichiers():
            t = f.read_text(encoding="utf-8", errors="ignore")
            self.assertNotIn("\u2014", t, str(f))
            self.assertNotIn("\u2013", t, str(f))

    def test_reference_jamais_nommee(self):
        for f in fichiers():
            self.assertNotIn(MOT, f.read_text(encoding="utf-8", errors="ignore").casefold(), str(f))
            self.assertNotIn(MOT, str(f.relative_to(ICI)).casefold())

    def test_termes_interdits(self):
        for f in fichiers():
            if f.suffix not in (".html", ".js", ".css", ".md"):
                continue
            t = f.read_text(encoding="utf-8", errors="ignore")
            for motif in INTERDITS:
                self.assertIsNone(re.search(motif, t), f"{f} : {motif}")


if __name__ == "__main__":
    unittest.main()
