"""Pages générées, robots, 404, noindex, liens internes, h1 unique, pages modèles (spec § 6, § 8, § 9)."""
import re
import subprocess
import sys
import unittest
from pathlib import Path

ICI = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ICI))
import build  # noqa: E402


class TestBuild(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        subprocess.run([sys.executable, str(ICI / "build.py")], check=True, cwd=ICI)
        cls.pages = {p: (ICI / "docs" / p / "index.html").read_text(encoding="utf-8") for p in build.PAGES}

    def test_onze_pages_robots_404(self):
        html = sorted(str(f.relative_to(ICI / "docs")) for f in (ICI / "docs").rglob("*.html"))
        self.assertEqual(html, sorted([p + "index.html" for p in build.PAGES] + ["404.html"]))
        self.assertEqual((ICI / "docs/robots.txt").read_text(encoding="utf-8"), "User-agent: *\nDisallow: /\n")
        self.assertTrue((ICI / "docs/.nojekyll").exists())

    def test_noindex_partout(self):
        for p, h in self.pages.items():
            self.assertIn('<meta name="robots" content="noindex, nofollow">', h, p)
        self.assertIn('<meta name="robots" content="noindex, nofollow">',
                      (ICI / "docs/404.html").read_text(encoding="utf-8"))

    def test_liens_internes_resolus(self):
        for p, h in self.pages.items():
            base = ICI / "docs" / p
            for ref in re.findall(r'(?:href|src)="([^"]+)"', h):
                if ref.startswith(("http", "mailto:", "#", "data:")):
                    continue
                chemin = ref.split("#")[0].split("?")[0]
                cible = (base / chemin).resolve()
                if chemin in ("", "./") or chemin.endswith("/"):
                    cible = cible / "index.html"
                self.assertTrue(cible.exists(), f"{p or 'accueil'} : lien cassé {ref}")

    def test_un_seul_h1(self):
        for p, h in self.pages.items():
            self.assertEqual(len(re.findall(r"<h1[ >]", h)), 1, p)

    def test_balises_equilibrees(self):
        """Une balise restée ouverte (textarea, select) avale la suite de la page, scripts compris."""
        for p, h in self.pages.items():
            for tag in ("div", "section", "main", "a", "ul", "li", "select", "textarea", "form", "figure", "details", "p"):
                ouvre = len(re.findall(r"<" + tag + r"[\s>]", h))
                ferme = h.count("</" + tag + ">")
                self.assertEqual(ouvre, ferme, f"{p or 'accueil'} : <{tag}> {ouvre} ouvertes, {ferme} fermées")

    def test_pages_modeles(self):
        m = build.modele
        self.assertEqual(m("corrext/chnell/"), "corrext/traduction-texte-et-document/")
        self.assertEqual(m("niveaux-de-qualite/"), "corrext/")
        self.assertEqual(m("solutions/banques-finance/"), "solutions/cabinets-avocats/")
        self.assertEqual(m("traduction/francais-anglais/"), "traduction/allemand-francais/")
        self.assertEqual(m("traduction/fusions-acquisitions/"), "traduction/contrats/")
        self.assertEqual(m("traduction/"), "traduction/contrats/")
        self.assertEqual(m("comparatif/deepl-traduction-juridique/"), "lexmachina/")
        self.assertEqual(m("ressources/blog/legaltech-avocats-allies-ou-concurrents/"),
                         "ressources/blog/traduire-contrat-droit-suisse/")
        self.assertEqual(m("ressources/glossaire/"), "ressources/blog/")
        self.assertEqual(m("aide/decouvrir-corrext/"), "ressources/blog/")
        self.assertEqual(m("a-propos/"), "")
        self.assertEqual(m("mentions-legales/"), "")

    def test_relier(self):
        h = build.relier('<a href="{{ROOT}}fr/solutions/banques-finance/#x">', "corrext/")
        self.assertEqual(h, '<a href="../solutions/cabinets-avocats/" data-modele="solutions/banques-finance/">')
        self.assertEqual(build.relier('<a href="{{ROOT}}">', ""), '<a href="./">')
        self.assertEqual(build.relier('<img src="{{ROOT}}assets/img/x.png">', "a/b/"), '<img src="../../assets/img/x.png">')


if __name__ == "__main__":
    unittest.main()
