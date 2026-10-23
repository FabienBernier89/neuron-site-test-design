"""Avis Attorney-Client privilege (décision de Fabien du 2026-10-23, point 3, option A).

Quand un utilisateur choisit un moteur hébergé à l'étranger (DeepL Pro, Azure OpenAI GPT, Claude), l'avis rappelle la
politique de son organisation : le site ne dit plus que Corrext ou l'avis « impose », « exige » ou « interdit » la
pseudonymisation, et il nomme l'avis « avis Attorney-Client privilege » au lieu d'« avis de pseudonymisation ».
Les phrases de la V1 sont corrigées par les entrées « remplace » de src/data/contenus-v2/W-avis-attorney-client.json
(outils/post/renommages.py). Les variantes restantes (« avertissement avant tout envoi », « avis de confidentialité »,
« règle d'organisation ») sont corrigées par src/data/contenus-v2/X-avis-variantes.json (même décision, variantes).
La citation du bandeau de l'application, en anglais, reste inchangée."""
import html as H
import json
import sys
import unittest
from pathlib import Path

ICI = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ICI))
import build  # noqa: E402
from tests import support  # noqa: E402

JSON_W = ICI / "src/data/contenus-v2/W-avis-attorney-client.json"
JSON_X = ICI / "src/data/contenus-v2/X-avis-variantes.json"
INTERDITES = ("exige une pseudonymisation", "impose de pseudonymiser", "avis de pseudonymisation",
              "avertissement de pseudonymisation", "rappel sur la pseudonymisation", "exigent une pseudonymisation")
CITATION = "Attorney-Client privilege notice"
BLOG = "ressources/blog/secret-professionnel-outils-traduction/"
# Variantes alignées par le lot X : formules interdites sur tout le site construit, et dans llms.txt et llms-full.txt
INTERDITES_X = ("avertissement avant tout envoi", "avertissement explicite avant tout envoi", "avis de confidentialité",
                "règle d'organisation")


class TestAvisAttorney(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        sortie = support.site_complet()
        cls.pages = {p: H.unescape(support.chemin(sortie, p).read_text(encoding="utf-8")) for p in build.PAGES}
        cls.entrees = json.loads(JSON_W.read_text(encoding="utf-8"))["entrees"]
        cls.entrees_x = json.loads(JSON_X.read_text(encoding="utf-8"))["entrees"]
        cls.llms = [(sortie / f).read_text(encoding="utf-8") for f in ("llms.txt", "llms-full.txt")]

    def test_aucune_formulation_d_obligation_ni_ancien_nom(self):
        for p, h in self.pages.items():
            for f in INTERDITES:
                self.assertNotIn(f.lower(), h.lower(), f"{p or 'accueil'} : « {f} »")

    def test_corrections_appliquees_et_limitees_a_leur_page(self):
        for e in self.entrees:
            self.assertEqual(e["statut"], "valide", e["cle"])
            self.assertIn("Décision de Fabien du 2026-10-23 (point 3, option A)", e["source"], e["cle"])
            self.assertIn(e["page"], self.pages, e["cle"])
            self.assertIn(e["texte"], self.pages[e["page"]], e["cle"])
            self.assertNotIn(e["remplace"], self.pages[e["page"]], e["cle"])
            self.assertNotIn(chr(0x2014), e["texte"], e["cle"])

    def test_variantes_alignees_sur_tout_le_site(self):
        for p, h in self.pages.items():
            for f in INTERDITES_X:
                self.assertNotIn(f.lower(), h.lower(), f"{p or 'accueil'} : « {f} »")
        for t in self.llms:
            for f in INTERDITES_X:
                self.assertNotIn(f.lower(), t.lower(), f"llms : « {f} »")

    def test_variantes_appliquees_et_limitees_a_leur_page(self):
        self.assertEqual(len(self.entrees_x), 13)
        for e in self.entrees_x:
            self.assertEqual(e["statut"], "valide", e["cle"])
            self.assertIn("Décision de Fabien du 2026-10-23 (point 3, option A, variantes)", e["source"], e["cle"])
            self.assertIn(e["page"], self.pages, e["cle"])
            self.assertIn(e["texte"], self.pages[e["page"]], e["cle"])
            self.assertNotIn(e["remplace"], self.pages[e["page"]], e["cle"])
            for c in (chr(0x2014), chr(0x2013)):
                self.assertNotIn(c, e["texte"], e["cle"])
            # l'avis rappelle la politique de l'organisation, il n'impose, n'exige ni n'interdit rien
            for v in ("impose", "exige", "interdit"):
                self.assertNotIn(v, e["texte"], e["cle"])

    def test_citation_de_l_application_inchangee(self):
        self.assertIn(CITATION, self.pages[BLOG])
        self.assertIn("« You have chosen to use third-party translation engines hosted abroad.", self.pages[BLOG])
        self.assertIn("your organization requires you to remove any references", self.pages[BLOG])


if __name__ == "__main__":
    unittest.main()
