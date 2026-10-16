"""Règles des blocs communs (REGLES-BLOCS.md) : une seule mise en page par type de bloc, dans la feuille partagée."""
import re
import sys
import unittest
from pathlib import Path

ICI = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ICI))
from tests import support  # noqa: E402

# Anciennes classes propres à une page, remplacées par les règles communes le 2026-10-16
CLASSES_RETIREES = ("hero-haut", "lm-hg", "tl-lm", "tl-haut")


class TestReglesBlocs(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.sortie = support.site_complet(apercu=True)
        cls.css = (cls.sortie / "assets/site.css").read_text(encoding="utf-8")
        cls.pages = {str(f.relative_to(cls.sortie)): f.read_text(encoding="utf-8") for f in cls.sortie.rglob("index.html")}

    def regle(self, selecteur):
        m = re.search(r"(?:^|\})" + re.escape(selecteur) + r"\{([^}]*)\}", self.css, re.M)
        self.assertIsNotNone(m, selecteur)
        return m.group(1)

    def test_hero_titre_cale_en_haut(self):
        self.assertIn("align-items:start", self.regle(".hero-g"))

    def test_tuiles_de_texte(self):
        r = self.regle(".tl.txt p")
        for d in ("margin-top:8px", "font-size:14px"):
            self.assertIn(d, r)

    def test_tuiles_chiffrees_alignees(self):
        r = self.regle(".tl .n")
        for d in ("height:60px", "white-space:nowrap"):
            self.assertIn(d, r)
        self.assertIn("justify-content:flex-start", self.regle(".tl > *:has(> .n)"))

    def test_aucune_classe_de_page_pour_un_bloc_commun(self):
        for c, h in self.pages.items():
            for classe in CLASSES_RETIREES:
                self.assertIsNone(re.search(r'class="[^"]*\b' + classe + r'\b', h), (c, classe))


if __name__ == "__main__":
    unittest.main()
