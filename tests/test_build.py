"""Pages générées sous fr/, page racine, robots, 404, noindex, liens internes, h1 unique, pages modèles
(spec § 6, § 8, § 9 du test de design ; spec V2 § 3 pour l'arborescence et la configuration)."""
import os
import posixpath
import re
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path
from unittest import mock

ICI = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ICI))
import build  # noqa: E402
import redirections  # noqa: E402
from tests import support  # noqa: E402


class TestBuild(unittest.TestCase):
    """Site complet construit en mode aperçu forcé (dossier temporaire), quel que soit le réglage du dépôt."""

    @classmethod
    def setUpClass(cls):
        cls.docs = support.site_complet(apercu=True)
        cls.pages = {p: support.chemin(cls.docs, p).read_text(encoding="utf-8") for p in build.PAGES}

    def test_arborescence_fr_et_racine(self):
        self.assertEqual(build.chemin_page("corrext/"), build.DOCS / "fr" / "corrext" / "index.html")
        self.assertEqual(build.chemin_page(""), build.DOCS / "fr" / "index.html")
        racine = (self.docs / "index.html").read_text(encoding="utf-8")
        self.assertIn("location.replace", racine)
        self.assertIn('href="fr/"', racine)
        self.assertTrue((self.docs / "fr/index.html").exists())
        self.assertTrue((self.docs / "fr/corrext/index.html").exists())

    def test_racine_reduite_au_francais(self):
        """La page d'aiguillage de la V1 ne propose plus que la langue du site : fr."""
        racine = (self.docs / "index.html").read_text(encoding="utf-8")
        self.assertIn('var dispo=["fr"],def="fr"', racine)
        self.assertEqual(re.findall(r'<a href="([^"]+)"', racine), ["fr/", "fr/"])  # corps et noscript
        for langue in ("de", "it", "en"):
            self.assertNotIn(f'href="{langue}/"', racine)
            self.assertNotIn(f'hreflang="{langue}', racine)

    def test_pages_robots_404(self):
        html = sorted(str(f.relative_to(self.docs)) for f in self.docs.rglob("*.html"))
        attendu = ["index.html", "404.html"] + [str(support.chemin(self.docs, p).relative_to(self.docs)) for p in build.PAGES]
        attendu += [ancien + "index.html" for ancien in redirections.lire(build.NEURON)]  # pages de redirection d'aperçu
        self.assertEqual(html, sorted(attendu))
        self.assertEqual((self.docs / "robots.txt").read_text(encoding="utf-8"), "User-agent: *\nDisallow: /\n")
        self.assertTrue((self.docs / ".nojekyll").exists())

    def test_noindex_et_ruban_partout(self):
        for p, h in self.pages.items():
            self.assertIn('<meta name="robots" content="noindex, nofollow">', h, p)
            self.assertIn("Aperçu du futur site Neur.on, non indexé.", h, p)
        self.assertIn('<meta name="robots" content="noindex, nofollow">',
                      (self.docs / "404.html").read_text(encoding="utf-8"))

    def test_liens_internes_resolus(self):
        for p, h in self.pages.items():
            base = support.chemin(self.docs, p).parent
            for ref in re.findall(r'(?:href|src)="([^"]+)"', h):
                if ref.startswith(("http", "mailto:", "tel:", "#", "data:")):
                    continue
                chemin = ref.split("#")[0].split("?")[0]
                cible = (base / chemin).resolve()
                if chemin in ("", "./") or chemin.endswith("/"):
                    cible = cible / "index.html"
                self.assertTrue(cible.exists(), f"{p or 'accueil'} : lien cassé {ref}")

    def test_deux_ecritures_de_lien_menent_a_fr(self):
        """{{ROOT}}contact/ et {{ROOT}}fr/contact/ désignent fr/contact/, le logo désigne fr/, depuis toute profondeur."""
        for page in ("", "corrext/", "ressources/blog/", "ressources/blog/traduire-contrat-droit-suisse/", "a/b/c/d/"):
            for ecriture in ("{{ROOT}}contact/", "{{ROOT}}fr/contact/"):
                href = re.search(r'href="([^"]+)"', build.relier(f'<a href="{ecriture}">', page)).group(1)
                self.assertEqual(posixpath.normpath(posixpath.join("fr", page, href)), "fr/contact", (page, ecriture))
            logo = re.search(r'href="([^"]+)"', build.relier('<a href="{{ROOT}}">', page)).group(1)
            self.assertEqual(posixpath.normpath(posixpath.join("fr", page, logo)), "fr", page)
            img = re.search(r'src="([^"]+)"', build.relier('<img src="{{ROOT}}assets/img/x.png">', page)).group(1)
            self.assertEqual(posixpath.normpath(posixpath.join("fr", page, img)), "assets/img/x.png", page)

    def test_logo_et_demo_dans_les_pages_construites(self):
        for p, h in self.pages.items():
            base = support.chemin(self.docs, p).parent
            logo = re.search(r'class="hd-logo" href="([^"]+)"', h).group(1)
            self.assertEqual((base / logo).resolve(), (self.docs / "fr").resolve(), p or "accueil")
            demo = re.search(r'<a class="btn btn-s" href="([^"]+)"[^>]*>Demander une démo', h)
            if demo:  # l'en-tête minimal de la page contact n'en a pas
                self.assertEqual((base / demo.group(1)).resolve(), (self.docs / "fr/contact").resolve(), p or "accueil")

    def test_404_liens_resolus_depuis_la_base(self):
        """La 404 est servie à toute profondeur : ses liens relatifs partent de la base, c'est-à-dire de la racine du site."""
        h = (self.docs / "404.html").read_text(encoding="utf-8")
        self.assertRegex(h, r'<base href="/[^"]*/">')
        liens = [r for r in re.findall(r'(?:href|src)="([^"]+)"', h) if not r.startswith(("http", "mailto:", "tel:", "#", "data:", "/"))]
        self.assertTrue(liens)
        for ref in liens:
            self.assertFalse(ref.startswith("../"), ref)
            cible = (self.docs / ref.split("#")[0].split("?")[0]).resolve()
            if ref.split("#")[0].endswith("/") or ref.split("#")[0] == "":
                cible = cible / "index.html"
            self.assertTrue(cible.exists(), f"404 : lien cassé {ref}")

    def test_sortie_et_base_configurables_par_l_environnement(self):
        with tempfile.TemporaryDirectory() as tmp:
            env = {**os.environ, "SORTIE": str(Path(tmp) / "essai"), "BASE_PAGES": "/essai/"}
            subprocess.run([sys.executable, str(ICI / "build.py")], check=True, cwd=ICI, env=env, stdout=subprocess.DEVNULL)
            self.assertTrue((Path(tmp) / "essai/fr/index.html").exists())
            self.assertIn('<base href="/essai/">', (Path(tmp) / "essai/404.html").read_text(encoding="utf-8"))
        # sans variable, sur l'aperçu : la base vient de src/data/config.json
        self.assertIn(f'<base href="{build.CONFIG["base"]}">', (self.docs / "404.html").read_text(encoding="utf-8"))

    def test_base_selon_le_mode(self):
        """Sans BASE_PAGES : « / » en production (site à la racine du domaine), la clé « base » sur l'aperçu."""
        sans = {k: v for k, v in os.environ.items() if k != "BASE_PAGES"}
        with mock.patch.dict(os.environ, sans, clear=True):
            with mock.patch.object(build, "CONFIG", {**build.CONFIG, "apercu": False, "base": "/essai/"}):
                self.assertEqual(build.base_pages(), "/")
            with mock.patch.object(build, "CONFIG", {**build.CONFIG, "apercu": True, "base": "/essai/"}):
                self.assertEqual(build.base_pages(), "/essai/")
        with mock.patch.dict(os.environ, {"BASE_PAGES": "/variable/"}):
            for apercu in (True, False):
                with mock.patch.object(build, "CONFIG", {**build.CONFIG, "apercu": apercu}):
                    self.assertEqual(build.base_pages(), "/variable/", apercu)
        production = support.site_complet(apercu=False)
        self.assertIn('<base href="/">', (production / "404.html").read_text(encoding="utf-8"))

    def test_modes_apercu_et_production(self):
        """apercu vrai : noindex, ruban, robots Disallow, pas de plan du site. apercu faux : rien de tout cela, robots
        ouvert qui annonce sitemap.xml."""
        def construire(apercu):
            return support.construire(self.enterContext(tempfile.TemporaryDirectory()), ["", "contact/", "corrext/"],
                                      config={"apercu": apercu})

        apercu = construire(True)
        production = construire(False)
        for chemin in ("fr/index.html", "fr/contact/index.html", "fr/corrext/index.html", "404.html"):
            h = (apercu / chemin).read_text(encoding="utf-8")
            self.assertIn('<meta name="robots" content="noindex, nofollow">', h, chemin)
            self.assertIn('class="ruban"', h, chemin)
            h = (production / chemin).read_text(encoding="utf-8")
            self.assertNotIn("noindex", h, chemin)
            self.assertNotIn('class="ruban"', h, chemin)
        self.assertEqual((apercu / "robots.txt").read_text(encoding="utf-8"), "User-agent: *\nDisallow: /\n")
        robots = (production / "robots.txt").read_text(encoding="utf-8")
        self.assertIn("User-agent: *", robots)
        self.assertIn("Allow: /", robots)
        self.assertNotIn("Disallow: /", robots)
        self.assertIn("Sitemap: https://neur-on.ai/sitemap.xml", robots)
        self.assertTrue((production / "sitemap.xml").is_file())
        self.assertFalse((apercu / "sitemap.xml").exists())

    def test_referencement_repris_du_site(self):
        """Chaque page garde les balises de référencement de la page Neur.on correspondante (URL de production)."""
        import json
        for p, h in self.pages.items():
            tete = h[:h.index("</head>")]
            self.assertIn(f'<link rel="canonical" href="https://neur-on.ai/fr/{p}">', tete, p or "accueil")
            self.assertIn('<meta property="og:title"', tete, p)
            self.assertIn('hreflang="x-default"', tete, p)
            lds = re.findall(r'<script type="application/ld\+json">(.*?)</script>', h, re.S)
            self.assertTrue(lds, f"{p or 'accueil'} : aucune donnée structurée")
            for ld in lds:
                json.loads(ld)

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
        """Une page présente se sert elle-même ; un chemin sans page renvoie au modèle de son type."""
        m = build.modele
        for p in build.PAGES:
            self.assertEqual(m(p), p)
        self.assertEqual(m("solutions/inexistante/"), "solutions/cabinets-avocats/")
        self.assertEqual(m("traduction/francais-italien/"), "traduction/allemand-francais/")
        self.assertEqual(m("traduction/inexistante/"), "traduction/contrats/")
        self.assertEqual(m("ressources/blog/billet-inexistant/"), "ressources/blog/traduire-contrat-droit-suisse/")
        self.assertEqual(m("chemin/inconnu/"), "")

    def test_relier(self):
        h = build.relier('<a href="{{ROOT}}fr/solutions/inexistante/#x">', "corrext/")
        self.assertEqual(h, '<a href="../../fr/solutions/cabinets-avocats/" data-modele="solutions/inexistante/">')
        self.assertEqual(build.relier('<a href="{{ROOT}}">', ""), '<a href="../fr/">')
        self.assertEqual(build.relier('<img src="{{ROOT}}assets/img/x.png">', "a/b/"), '<img src="../../../assets/img/x.png">')
        # la 404 est servie depuis la racine du site : aucun retour en arrière
        self.assertEqual(build.relier('<a href="{{ROOT}}contact/">', "", racine=""), '<a href="fr/contact/">')

    def test_menu_sans_page_modele(self):
        """Une fois le site complet, aucune entrée du méga-menu ne doit tomber sur une page modèle."""
        manquants = sorted(set(re.findall(r'data-modele="([^"]+)"', self.pages[""])))
        if len(build.PAGES) > 100:
            self.assertEqual(manquants, [])


if __name__ == "__main__":
    unittest.main()
