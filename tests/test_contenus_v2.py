"""Contenus nouveaux de la V2 (src/data/contenus-v2) : clés uniques, statut, source, règles de marque (spec V2 § 2)."""
import json
import re
import unittest
from pathlib import Path

ICI = Path(__file__).resolve().parent.parent
INTERDITS = [chr(0x2014), chr(0x2013), "doc" + "trine", "Legal 230", "Lexa ", "rapprochement"]


class TestContenusV2(unittest.TestCase):
    def setUp(self):
        self.e = [x for f in sorted((ICI / "src/data/contenus-v2").glob("*.json"))
                  for x in json.loads(f.read_text(encoding="utf-8"))["entrees"]]

    def test_dossier_et_notice(self):
        self.assertTrue((ICI / "src/data/contenus-v2").is_dir())
        self.assertTrue((ICI / "src/data/contenus-v2/README.md").is_file())

    def test_cles_uniques_textes_et_statuts(self):
        cles = [x["cle"] for x in self.e]
        self.assertEqual(len(cles), len(set(cles)))
        for x in self.e:
            self.assertTrue(x["texte"].strip(), x["cle"])
            self.assertIn(x["statut"], ("a_relire", "valide"), x["cle"])
            self.assertTrue(x.get("source"), x["cle"])

    def test_regles_de_marque(self):
        for x in self.e:
            for m in INTERDITS:
                self.assertNotIn(m, x["texte"], x["cle"])
            self.assertFalse(re.search(r"LexMachina[^.]{0,60}\bLLM\b|\bLLM\b[^.]{0,60}LexMachina", x["texte"]), x["cle"])


if __name__ == "__main__":
    unittest.main()
