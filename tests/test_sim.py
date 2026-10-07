"""Données de démonstration copiées sans modification, sim.js sans texte affiché (spec § 7, test 8)."""
import re
import subprocess
import sys
import unittest
from pathlib import Path

ICI = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ICI))
import build  # noqa: E402


class TestSim(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        subprocess.run([sys.executable, str(ICI / "build.py")], check=True, cwd=ICI)

    def test_donnees_identiques(self):
        js = (build.NEURON / "assets/corrext-demo.js").read_text(encoding="utf-8")
        sim = (build.DOCS / "assets/sim-data.js").read_text(encoding="utf-8")
        objet = sim.split("window.SIM_EX=", 1)[1].rstrip().rstrip(";")
        self.assertIn("var EX=" + objet, js)

    def test_demo_copiee_a_l_identique(self):
        self.assertEqual((build.DOCS / "assets/corrext-demo.js").read_bytes(),
                         (build.NEURON / "assets/corrext-demo.js").read_bytes())

    def test_sim_sans_texte_affiche(self):
        js = (ICI / "assets/sim.js").read_text(encoding="utf-8")
        for c in re.findall(r'"([^"\\]*)"', js):
            self.assertIsNone(re.search(r"[a-zà-ÿ]{3,} [a-zà-ÿ]{3,} [a-zà-ÿ]{3,}", c, re.I), c)


if __name__ == "__main__":
    unittest.main()
