"""Cartes de fonctionnalités (outils/post/fonctionnalites.py, retour de Fabien du 2026-10-15)."""
import re
import sys
import unittest
from pathlib import Path

ICI = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ICI))
from tests import support  # noqa: E402
from outils.post import fonctionnalites as F  # noqa: E402

# Tous les libellés des mini-interfaces existent déjà dans les sources (V1 ou pages V2) : rien d'inventé
SOURCES = [ICI.parent / "neuron/src/generators.py"] + sorted((ICI / "src/pages").rglob("index.html"))


class TestCartesFonctionnalites(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.sortie = support.site_complet(apercu=True)
        cls.pages = {str(f.relative_to(cls.sortie)): f.read_text(encoding="utf-8") for f in cls.sortie.rglob("index.html")}

    def test_toujours_trois_cartes(self):
        for c, h in self.pages.items():
            for bloc in re.findall(r'<div class="fx-g">(.*?)</div>\s*</div></section>', h, re.S):
                self.assertEqual(bloc.count('<a class="fx"'), 3, c)
        self.assertNotIn("fx-n", (self.sortie / "assets/site.css").read_text(encoding="utf-8"))

    def test_blocs_convertis(self):
        n = sum(h.count('<div class="fx-g') for h in self.pages.values())
        self.assertGreaterEqual(n, 15)  # 9 blocs « autres outils / pour aller plus loin » + 6 pages Solutions

    def test_plus_aucun_bloc_de_fonctionnalites_en_cartes_simples(self):
        for c, h in self.pages.items():
            for m in re.finditer(r'<div class="cd">((?:<a href="[^"]+">.*?</a>)+)</div>', h, re.S):
                cibles = re.findall(r'<a href="([^"]+)"', m.group(1))
                fonctions = [x for x in cibles if any(x.rstrip("/").endswith(k[3:].rstrip("/")) for k in F.VISUELS)]
                self.assertNotEqual(len(fonctions), len(cibles), (c, cibles))

    def test_chaque_carte_complete(self):
        for c, h in self.pages.items():
            for carte in re.findall(r'<a class="fx" .*?</a>', h, re.S):
                for partie in ('class="fx-v" aria-hidden="true"', 'class="fx-w"', 'class="fx-t"', 'class="fx-l"'):
                    self.assertIn(partie, carte, c)
                self.assertNotIn("<b>", re.search(r'<b class="fx-t">(.*?)</b>', carte, re.S).group(1), c)

    def test_libelles_issus_des_sources(self):
        corpus = " ".join(p.read_text(encoding="utf-8") for p in SOURCES if p.exists()).replace("&amp;", "&")
        for href, html in F.VISUELS.items():
            for t in re.findall(r">([^<>]{3,})<", html):
                t = t.strip().replace("&amp;", "&")
                if t and not t.startswith(("{", "}", "/")):
                    self.assertIn(t.strip(' ",:'), corpus, (href, t))

    def test_etat_final_sans_animation(self):
        css = (self.sortie / "assets/site.css").read_text(encoding="utf-8")
        # l'interrupteur est allumé et LexMachina sélectionné hors animation
        self.assertIn(".u-sw{position:relative;flex:0 0 auto;width:28px;height:16px;border-radius:999px;background:var(--u-ind)}", css)
        self.assertIn(".u-lm{background:var(--u-soft)}", css)


if __name__ == "__main__":
    unittest.main()
