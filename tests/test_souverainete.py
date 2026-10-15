"""Souveraineté des données mise en avant (décisions de Fabien du 2026-10-15).

- Page Protection des données : dans le paragraphe Google Analytics, les données sont « pseudonymisées » et non plus
  « anonymisées », et leur durée de conservation est indiquée (post-traitement outils/post/pseudonymisation.py).
- Page Sécurité et souveraineté : voir TestPageSecurite.
Textes nouveaux : src/data/contenus-v2/F-souverainete.json (statut à relire, une source par entrée)."""
import importlib
import json
import re
import subprocess
import sys
import unittest
from pathlib import Path

ICI = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ICI))
import build  # noqa: E402
from outils import contenus  # noqa: E402

JSON_F = ICI / "src/data/contenus-v2/F-souverainete.json"
DECISION = "Décision de Fabien du 2026-10-15"

# Page Protection des données : paragraphe Google Analytics de la V1 et phrases attendues (consignes du 2026-10-15)
DONNEES = "protection-des-donnees/"
DEBUT_GA = "<p>Google Analytics est un service d'analyse web"
ANCIENNE_1 = ("Les informations générées par les cookies sont envoyées sous forme anonymisée à un serveur de Google aux "
              "États-Unis, où elles sont stockées.")
NOUVELLE_1 = ANCIENNE_1.replace("sous forme anonymisée", "sous forme pseudonymisée")
ANCIENNE_2 = "Grâce à l'anonymisation, il est impossible de relier ces données à la personne concernée."
NOUVELLE_2 = "Grâce à la pseudonymisation, ces données ne permettent pas, à elles seules, d'identifier la personne concernée."
CONSERVATION = ("Les données liées aux utilisateurs et aux événements sont conservées deux mois dans Google Analytics, "
                "puis supprimées automatiquement.")
SUITE_V1 = "Google utilise ces informations pour analyser votre utilisation de notre site"


def paragraphe_ga(h):
    m = re.search(re.escape(DEBUT_GA) + r".*?</p>", h, re.S)
    if not m:
        raise AssertionError("paragraphe Google Analytics introuvable")
    return m.group(0)


def entrees_f():
    return {e["cle"]: e for e in json.loads(JSON_F.read_text(encoding="utf-8"))["entrees"]}


class TestProtectionDesDonnees(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        subprocess.run([sys.executable, str(ICI / "build.py")], check=True, cwd=ICI, stdout=subprocess.DEVNULL)
        cls.publiee = build.chemin_page(DONNEES).read_text(encoding="utf-8")
        cls.source = (build.SRC / "pages" / DONNEES / "index.html").read_text(encoding="utf-8")

    def post(self):
        return importlib.import_module("outils.post.pseudonymisation")

    def test_paragraphe_pseudonymise_avec_conservation(self):
        p = paragraphe_ga(self.publiee)
        self.assertNotIn("anonymis", p.lower())
        self.assertNotIn("impossible de relier", p)
        for phrase in (NOUVELLE_1, NOUVELLE_2, CONSERVATION):
            self.assertEqual(p.count(phrase), 1, phrase)
        # Ordre : pseudonymisation, conservation, puis la suite du texte de la V1
        self.assertLess(p.index(NOUVELLE_1), p.index(NOUVELLE_2))
        self.assertLess(p.index(NOUVELLE_2), p.index(CONSERVATION))
        self.assertLess(p.index(CONSERVATION), p.index(SUITE_V1))

    def test_reste_de_la_page_intact(self):
        apres = self.post().traiter(self.source, DONNEES)
        p_avant, p_apres = paragraphe_ga(self.source), paragraphe_ga(apres)
        # Hors du paragraphe, rien ne change ; dans le paragraphe, seules ces phrases changent
        self.assertEqual(apres.replace(p_apres, ""), self.source.replace(p_avant, ""))
        self.assertEqual(p_apres, p_avant.replace(ANCIENNE_1, NOUVELLE_1).replace(ANCIENNE_2, NOUVELLE_2 + " " + CONSERVATION))
        # Page publiée : les paragraphes voisins de la V1 sont toujours là
        for x in ("Notre site utilise Google Analytics pour mesurer sa fréquentation", "Si le droit suisse ou étranger l'exige",
                  "Google Analytics Opt-out Browser Add-on"):
            self.assertIn(x, self.publiee)

    def test_seule_cette_page_est_touchee(self):
        for p in ("", "mentions-legales/", "securite-souverainete/", "404.html"):
            self.assertEqual(self.post().traiter(self.source, p), self.source, p)

    def test_textes_dans_le_json(self):
        e = entrees_f()
        attendus = {"protection-des-donnees.analytics.pseudonymisee": (NOUVELLE_1, ANCIENNE_1),
                    "protection-des-donnees.analytics.pseudonymisation": (NOUVELLE_2, ANCIENNE_2),
                    "protection-des-donnees.analytics.conservation": (CONSERVATION, None)}
        for cle, (texte, ancien) in attendus.items():
            self.assertEqual(e[cle]["texte"], texte, cle)
            self.assertEqual(e[cle]["page"], DONNEES, cle)
            self.assertEqual(e[cle]["statut"], "a_relire", cle)
            self.assertIn(DECISION, e[cle]["source"], cle)
            self.assertEqual(e[cle].get("remplace"), ancien, cle)
        self.assertIn("formulation juridiquement exacte de la pseudonymisation", e["protection-des-donnees.analytics.pseudonymisation"]["source"])
        self.assertIn("GA4 : 2 mois", e["protection-des-donnees.analytics.conservation"]["source"])
        self.assertEqual(e["protection-des-donnees.analytics.conservation"]["insere_avant"], SUITE_V1)
        self.assertEqual(contenus.texte("protection-des-donnees.analytics.conservation"), CONSERVATION)


if __name__ == "__main__":
    unittest.main()
