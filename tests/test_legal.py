"""Pages légales : sommaire collant à gauche, corps en 16 px, espace sous l'en-tête (retour de Fabien du 2026-10-15)."""
import re
import unittest
from pathlib import Path

import build

ICI = Path(__file__).resolve().parent.parent
PAGES_LEGALES = ["protection-des-donnees/", "mentions-legales/"]


class TestPagesLegales(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.html = {p: build.chemin_page(p).read_text(encoding="utf-8") for p in PAGES_LEGALES}

    def test_sommaire_relie_a_chaque_intertitre(self):
        for p, h in self.html.items():
            self.assertIn('class="sec lg-s"', h, p)
            sommaire = re.search(r'<nav class="lg-toc"[^>]*aria-label="Sommaire"[^>]*>(.*?)</nav>', h, re.S)
            self.assertIsNotNone(sommaire, p)
            ancres = re.findall(r'href="#([^"]+)"', sommaire.group(1))
            ids = re.findall(r'<h2[^>]*\bid="([^"]+)"', h)
            self.assertTrue(ids, p)
            self.assertEqual(ancres, ids, p)
            self.assertEqual(len(re.findall(r"<h1[ >]", h)), 1, p)

    def test_mise_en_page(self):
        css = (ICI / "assets/composants/legal.css").read_text(encoding="utf-8")
        self.assertIn("position:sticky", css.replace(" ", ""))
        self.assertIn("scroll-margin-top", css)
        self.assertRegex(css, r"\.lg-c p[^{]*\{[^}]*16px/26px")
        js = (ICI / "assets/global/sommaire.js").read_text(encoding="utf-8")
        self.assertIn("IntersectionObserver", js)
        self.assertIn('aria-current', js)


if __name__ == "__main__":
    unittest.main()
