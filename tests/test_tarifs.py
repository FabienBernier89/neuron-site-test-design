"""Page Tarifs (outils/composer/p_tarifs.py) : page d'information, sans aucun prix (demande de Fabien du 2026-10-16)."""
import json
import re
import sys
import unittest
from pathlib import Path

ICI = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ICI))
from tests import support  # noqa: E402


class TestTarifs(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.sortie = support.site_complet(apercu=True)
        cls.h = (cls.sortie / "fr/tarifs/index.html").read_text(encoding="utf-8")
        cls.main = cls.h[cls.h.index('<main id="main">'):cls.h.index("</main>")]

    def test_aucun_prix(self):
        texte = re.sub(r"<[^>]+>", " ", self.main)
        self.assertIsNone(re.search(r"(CHF|EUR|€|\$|Fr\.)\s*\d|\d[\d'\u00a0 .,]*\s*(CHF|EUR|€|francs)", texte), "montant affiché")
        self.assertNotRegex(texte, r"/\s*(mois|an|utilisateur|page)\b")

    def test_tarifs_avant_ressources_dans_le_menu(self):
        nav = re.search(r'<nav class="hd-nav".*?</nav>', self.h, re.S).group(0)
        libelles = [re.sub(r"<[^>]+>", "", x).strip() for x in re.findall(r'class="hd-i[^"]*"[^>]*>(.*?)</(?:a|button)>', nav, re.S)]
        self.assertEqual(libelles, ["Corrext", "Solutions", "LexMachina", "Tarifs", "Ressources"])
        self.assertIn('class="hd-i actif" href="../../fr/tarifs/">Tarifs</a>', self.h)
        mobile = self.h[self.h.index('id="mm"'):]
        self.assertLess(mobile.index(">Tarifs</a>"), mobile.index(">Ressources"))

    def test_structure_et_appel(self):
        for attendu in ('<span class="n">Tarifs.</span>', 'data-suivi="cta-tarifs-hero"', 'class="btn btn-2" href="../../fr/corrext/traduction-texte-et-document/#demo"',
                        'class="tf-pg"', 'class="fx-g"', 'data-suivi="cta-tarifs-fin"', "Prêt à essayer ?"):
            self.assertIn(attendu, self.h)
        self.assertEqual(self.main.count('class="tf-p"'), 3)

    def test_faq_structuree(self):
        ld = [json.loads(x) for x in re.findall(r'<script type="application/ld\+json">(.*?)</script>', self.h, re.S)]
        faq = [d for d in ld if d.get("@type") == "FAQPage"]
        self.assertEqual(len(faq), 1)
        self.assertEqual(len(faq[0]["mainEntity"]), 6)


if __name__ == "__main__":
    unittest.main()
