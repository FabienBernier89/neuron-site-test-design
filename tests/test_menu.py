"""Le méga-menu reprend une à une les entrées du site actuel (spec § 6, test 3)."""
import re
import subprocess
import sys
import unittest
from pathlib import Path

ICI = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ICI))
import build  # noqa: E402
import menu  # noqa: E402


class TestMenu(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        subprocess.run([sys.executable, str(ICI / "build.py")], check=True, cwd=ICI)
        cls.nav = (build.NEURON / "src/partials/nav.html").read_text(encoding="utf-8")
        cls.m = menu.lire_menu(cls.nav)

    def test_meme_nombre_de_liens(self):
        bureau = self.nav.split("<!-- MENU MOBILE -->")[0]
        attendu = len(re.findall(r"<a ", bureau[bureau.index('<div class="mega"'):]))
        lu = sum(len(c["liens"]) for p in self.m["panneaux"].values() for c in p["colonnes"])
        lu += sum(1 for p in self.m["panneaux"].values() if p["promo"])
        self.assertEqual(lu, attendu)
        html = (build.DOCS / "index.html").read_text(encoding="utf-8")
        self.assertEqual(html.count('class="mg-a"') + html.count('class="mg-card"'), attendu)

    def test_memes_libelles_dans_le_meme_ordre(self):
        titres = [l["titre"] for p in self.m["panneaux"].values() for c in p["colonnes"] for l in c["liens"]]
        self.assertEqual(titres[0], "Corrext, le poste de commande")
        self.assertEqual(titres[-1], "Agence de traduction ou plateforme")
        self.assertEqual([e["libelle"] for e in self.m["entrees"]], ["Corrext", "Solutions", "LexMachina", "Ressources"])

    def test_pied_six_colonnes(self):
        html = (build.DOCS / "index.html").read_text(encoding="utf-8")
        pied = html[html.index('<footer class="pied">'):]
        self.assertEqual(pied.count("<div><p>"), 6)


if __name__ == "__main__":
    unittest.main()
