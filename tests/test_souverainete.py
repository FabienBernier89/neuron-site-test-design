"""Souveraineté des données mise en avant (décisions de Fabien du 2026-10-15).

- Page Protection des données : dans le paragraphe Google Analytics, les données sont « pseudonymisées » et non plus
  « anonymisées », et leur durée de conservation est indiquée (post-traitement outils/post/pseudonymisation.py).
- Page Sécurité et souveraineté, sur le modèle des pages secteur (trame.py) : bloc « Le problème » juste après le hero,
  bento « Le parcours d'un document » retiré (ses quatre tuiles reprenaient les preuves), bloc « Preuves » de cinq
  faits juste avant la FAQ, sans redite de la liste « Ce que Neur.on garantit, précisément », et appels à l'action
  suivis (cta-securite-hero, cta-securite-milieu, cta-securite-fin).
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
from tests.test_trame import sections, suites, texte_brut  # noqa: E402

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


# Page Sécurité et souveraineté
SECURITE = "securite-souverainete/"
CLE = "securite-souverainete"
# Cinq faits du bloc Preuves, dans l'ordre du brief, et un repère attendu dans le nom affiché
PREUVES = {"iso": "ISO 27001", "infomaniak": "Infomaniak", "traitement": "Traitement en Suisse", "nlpd": "nLPD et RGPD",
           "cloudact": "CLOUD Act"}
GARANTIES = "Ce que Neur.on garantit, précisément"


class TestPageSecurite(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        subprocess.run([sys.executable, str(ICI / "build.py")], check=True, cwd=ICI, stdout=subprocess.DEVNULL)
        cls.h = build.chemin_page(SECURITE).read_text(encoding="utf-8")
        cls.main = cls.h[cls.h.index('<main id="main">'):cls.h.index("</main>")]
        cls.secs = sections(cls.h)
        cls.noms = [n for n, _ in cls.secs]
        cls.par_nom = dict(cls.secs)

    def test_ordre_hero_probleme_preuves_faq_appel(self):
        self.assertEqual(self.noms[:2], ["hero", "tr-pb"])
        self.assertEqual(self.noms.index("tr-pv") + 1, self.noms.index("faq"))
        self.assertEqual(self.noms[-1], "cta")
        for n in ("hero", "tr-pb", "tr-pv", "faq", "cta"):
            self.assertEqual(self.noms.count(n), 1, n)

    def test_bento_du_parcours_retire(self):
        lu = texte_brut(self.main)
        self.assertNotIn("Le parcours d'un document", lu)
        self.assertNotIn('<div class="bt"', self.main)  # plus aucune tuile qui reprendrait une preuve
        self.assertNotIn('<div class="tl', self.main)
        # Les autres sections existantes sont gardées
        for x in ("Où va votre document, selon votre choix", "Votre politique s'applique au moment du choix", GARANTIES,
                  "Trois régimes de confidentialité", "Pour aller plus loin", "Questions fréquentes sur la sécurité",
                  "Faites examiner ce document"):
            self.assertEqual(lu.count(x), 1, x)

    def test_probleme_trois_difficultes_tirees_du_json(self):
        pb = self.par_nom["tr-pb"]
        self.assertEqual(texte_brut(re.search(r"<h2[^>]*>(.*?)</h2>", pb, re.S).group(1)), contenus.texte(f"trame.pb.{CLE}.titre"))
        items = re.findall(r"<li\b.*?</li>", pb, re.S)
        self.assertEqual(len(items), 3)
        for n, li in enumerate(items, 1):
            for partie in ("label", "titre", "texte"):
                self.assertIn(contenus.texte(f"trame.pb.{CLE}.{n}.{partie}"), texte_brut(li), (n, partie))
            self.assertRegex(li, r"<h3[ >]", n)
        lu = texte_brut(pb)
        for repere in ("hors de Suisse", "CLOUD Act", "quel que soit", "secret"):
            self.assertIn(repere, lu)

    def test_probleme_sans_redite_du_hero_ni_de_la_section_suivante(self):
        i = self.noms.index("tr-pb")
        voisins = [self.par_nom["hero"], self.secs[i + 1][1]]
        self.assertEqual(suites(self.secs[i][1]) & set().union(*(suites(x) for x in voisins)), set())

    def test_preuves_cinq_faits(self):
        pv = self.par_nom["tr-pv"]
        lignes = re.findall(r"<li\b.*?</li>", pv, re.S)
        self.assertEqual(len(lignes), len(PREUVES))
        for li, (i, repere) in zip(lignes, PREUVES.items()):
            nom = contenus.texte(f"trame.pv.{i}.nom")
            self.assertIn(repere, nom, i)
            self.assertIn(f"<b>{nom}</b>", li, i)
            for x in ("detail", "type"):
                self.assertIn(contenus.texte(f"trame.pv.{i}.{x}"), texte_brut(li), (i, x))
        lu = texte_brut(pv)
        self.assertIn(contenus.texte(f"trame.pv.{CLE}.intro"), lu)
        # Ni la phrase de discrétion, ni la note sur les références clients : elles concernent les distinctions
        self.assertNotIn(contenus.texte("trame.pv.discretion"), lu)
        self.assertNotIn(contenus.texte("trame.pv.note"), lu)

    def test_preuves_sans_redite_des_garanties(self):
        """Le bloc Preuves ne reprend aucune suite de 5 mots de la liste « Ce que Neur.on garantit, précisément »."""
        garanties = next(x for _, x in self.secs if GARANTIES in texte_brut(x))
        self.assertEqual(suites(self.par_nom["tr-pv"]) & suites(garanties), set())

    def test_appels_a_l_action_suivis(self):
        boutons = re.findall(r'<a class="btn"[^>]*>', self.main)
        self.assertEqual(len(boutons), 3)  # hero, bande du milieu, appel final
        for b in boutons:
            self.assertRegex(b, r'href="(\.\./)+fr/contact/"')
        self.assertRegex(self.par_nom["hero"], r'<a class="btn"[^>]*data-suivi="cta-securite-hero"')
        bande = next(x for _, x in self.secs if "Votre politique s'applique au moment du choix" in texte_brut(x))
        self.assertRegex(bande, r'<a class="btn"[^>]*data-suivi="cta-securite-milieu"')
        self.assertRegex(self.par_nom["cta"], r'<a class="btn"[^>]*data-suivi="cta-securite-fin"')

    def test_textes_dans_le_json(self):
        e = entrees_f()
        cles = [f"trame.pb.{CLE}.titre"] + [f"trame.pb.{CLE}.{n}.{x}" for n in (1, 2, 3) for x in ("label", "titre", "texte")]
        cles += [f"trame.pv.{CLE}.intro"] + [f"trame.pv.{i}.{x}" for i in ("traitement", "nlpd", "cloudact")
                                             for x in ("nom", "detail", "type")]
        for cle in cles:
            self.assertEqual(e[cle]["page"], SECURITE, cle)
            self.assertEqual(e[cle]["statut"], "a_relire", cle)
            self.assertTrue(e[cle]["source"].strip(), cle)
        # Chaque preuve cite le site publié (V1) comme source
        for i in ("traitement", "nlpd", "cloudact"):
            self.assertIn("V1 ", e[f"trame.pv.{i}.nom"]["source"], i)
        self.assertIn("18 U.S.C. § 2713", e[f"trame.pb.{CLE}.2.texte"]["source"])


if __name__ == "__main__":
    unittest.main()
