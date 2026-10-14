"""Production simulée : le site complet construit avec « apercu » faux, dans un dossier temporaire, comme il partira sur
Hostpoint (neur-on.ai, à la racine du domaine). Rien ne dépend du réglage du dépôt."""
import re
import sys
import unittest
from pathlib import Path
from urllib.parse import unquote

ICI = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ICI))
import build  # noqa: E402
from tests import support  # noqa: E402


IMAGE = r"[^\"'\s()<>\\]+\.(?:png|jpe?g|webp|gif|svg|ico|avif)"
ABSOLUE = re.compile(r"https://neur-on\.ai/(" + IMAGE + r")", re.I)
ATTRIBUT = re.compile(r'\s(?:src|href|content|poster)="(' + IMAGE + r')(?:[?#][^"]*)?"', re.I)
SRCSET = re.compile(r'\ssrcset="([^"]+)"', re.I)
URL_CSS = re.compile(r"url\(\s*['\"]?(" + IMAGE + r")(?:[?#][^)'\"]*)?['\"]?\s*\)", re.I)


def images_manquantes(sortie):
    """Images citées par la sortie (HTML et CSS) absentes de la sortie : chemin relatif résolu depuis le fichier (depuis
    la racine pour une page à <base>), adresse absolue https://neur-on.ai/... ramenée à la racine du site."""
    manquantes = set()
    for f in list(sortie.rglob("*.html")) + list(sortie.rglob("*.css")):
        texte = f.read_text(encoding="utf-8")
        depart = sortie if "<base href=" in texte else f.parent
        refs = [u for u in ATTRIBUT.findall(texte) + URL_CSS.findall(texte)]
        for jeu in SRCSET.findall(texte):
            refs += [m.split()[0] for m in jeu.split(",") if m.strip()]
        for chemin in ABSOLUE.findall(texte):
            if not (sortie / unquote(chemin)).is_file():
                manquantes.add((str(f.relative_to(sortie)), "https://neur-on.ai/" + chemin))
        for ref in refs:
            if ref.startswith(("http:", "https:", "data:", "//")) or not re.search(IMAGE + "$", ref):
                continue
            cible = (sortie / ref.lstrip("/")) if ref.startswith("/") else (depart / ref)
            if not cible.resolve().is_file():
                manquantes.add((str(f.relative_to(sortie)), ref))
    return sorted(manquantes)


class TestImages(unittest.TestCase):
    def test_toute_image_de_la_sortie_existe(self):
        """Production et aperçu : chaque image citée, relative ou absolue (og:image, JSON-LD), est dans la sortie."""
        for apercu in (False, True):
            manquantes = images_manquantes(support.site_complet(apercu=apercu))
            self.assertEqual(manquantes[:10], [], f"apercu={apercu} : {len(manquantes)} images manquantes")

    def test_og_neuron_copiee(self):
        self.assertTrue((support.site_complet(apercu=False) / "assets/img/og-neuron.jpg").is_file())

    def test_copier_images_absolues(self):
        """copier_images recopie depuis le site Neur.on une image citée par https://neur-on.ai/assets/img/..."""
        import tempfile
        from unittest import mock
        with tempfile.TemporaryDirectory() as tmp, mock.patch.object(build, "DOCS", Path(tmp)):
            build.copier_images('<meta property="og:image" content="https://neur-on.ai/assets/img/og-neuron.jpg">'
                                '<script type="application/ld+json">{"image": "https://neur-on.ai/assets/img/neuron-logo.png"}</script>'
                                '<img src="https://neur-on.ai/assets/img/absente-du-site.png">')
            self.assertEqual((Path(tmp) / "assets/img/og-neuron.jpg").read_bytes(),
                             (build.NEURON / "assets/img/og-neuron.jpg").read_bytes())
            self.assertTrue((Path(tmp) / "assets/img/neuron-logo.png").is_file())
            self.assertFalse((Path(tmp) / "assets/img/absente-du-site.png").exists())  # absente de la V1 : ignorée


ALTERNATE = re.compile(r'<link rel="alternate" hreflang="([^"]+)" href="([^"]+)">')


class TestHreflang(unittest.TestCase):
    def test_seulement_les_langues_construites(self):
        """Tant que seule la version fr est construite : hreflang fr-CH (la page elle-même) et x-default (la racine)."""
        for apercu in (False, True):
            docs = support.site_complet(apercu=apercu)
            for p in build.PAGES:
                h = support.chemin(docs, p).read_text(encoding="utf-8")
                alternates = ALTERNATE.findall(h[:h.index("</head>")])
                self.assertEqual(alternates, [("fr-CH", "https://neur-on.ai/fr/" + p), ("x-default", "https://neur-on.ai/")], p)

    def test_detection_d_une_langue_presente_dans_la_sortie(self):
        """Une variante revient d'elle-même dès que sa page existe dans la sortie (lot F) : rien n'est écrit en dur."""
        import tempfile
        from unittest import mock
        with tempfile.TemporaryDirectory() as tmp, mock.patch.object(build, "DOCS", Path(tmp)):
            seule = dict(ALTERNATE.findall(build.seo("corrext/")))
            self.assertEqual(sorted(seule), ["fr-CH", "x-default"])
            (Path(tmp) / "de/corrext").mkdir(parents=True)
            (Path(tmp) / "de/corrext/index.html").write_text("<!DOCTYPE html>", encoding="utf-8")
            avec = dict(ALTERNATE.findall(build.seo("corrext/")))
            self.assertEqual(sorted(avec), ["de-CH", "fr-CH", "x-default"])
            self.assertEqual(avec["de-CH"], "https://neur-on.ai/de/corrext/")
        with mock.patch.object(build, "PAGES", build.PAGES + ["essai-de/"]), \
                mock.patch.object(build, "chemin_page", lambda p: build.DOCS / ("de/corrext" if p == "essai-de/" else "fr/" + p) / "index.html"):
            self.assertIn("de-CH", dict(ALTERNATE.findall(build.seo("corrext/"))))  # page de ce build, pas encore écrite

    def test_adresse_construite(self):
        self.assertTrue(build.adresse_construite("https://neur-on.ai/"))
        self.assertTrue(build.adresse_construite("https://neur-on.ai/fr/corrext/"))
        self.assertFalse(build.adresse_construite("https://neur-on.ai/de/corrext/"))
        self.assertFalse(build.adresse_construite("https://exemple.ch/fr/corrext/"))


LIEN_LLMS = re.compile(r"\]\((https://neur-on\.ai/[^)\s]*)\)")


class TestLlmsTxt(unittest.TestCase):
    def test_aucun_lien_vers_une_langue_absente(self):
        """llms.txt (production et aperçu) : plus de lien ni de section vers /de/, /it/ ou /en/ ; chaque lien restant
        mène à une page de la sortie ; les sections françaises restent entières."""
        v1 = (build.NEURON / "docs/llms.txt").read_text(encoding="utf-8")
        for apercu in (False, True):
            docs = support.site_complet(apercu=apercu)
            t = (docs / "llms.txt").read_text(encoding="utf-8")
            self.assertIsNone(re.search(r"neur-on\.ai/(?:de|it|en)/", t), apercu)
            for section in ("## Deutsch", "## Italiano", "## English"):
                self.assertNotIn(section, t, apercu)
            for url in LIEN_LLMS.findall(t):
                self.assertTrue((docs / url[len("https://neur-on.ai/"):] / "index.html").is_file(), url)
            francais = v1[:v1.index("## Deutsch")]
            self.assertTrue(t.rstrip("\n") == francais.rstrip("\n"), apercu)  # la partie française, mot pour mot

    def test_detection_et_sections_vides(self):
        import tempfile
        from unittest import mock
        texte = ("# Neur.on\n\n> Résumé.\n\n## Produit\n\n- [Corrext](https://neur-on.ai/fr/corrext/)\n"
                 "- [Corrext DE](https://neur-on.ai/de/corrext/)\n\n## Deutsch\n\n- [Start](https://neur-on.ai/de/)\n"
                 "- [Corrext](https://neur-on.ai/de/corrext/)\n\n## English\n\n- [Home](https://neur-on.ai/en/)\n")
        with tempfile.TemporaryDirectory() as tmp, mock.patch.object(build, "DOCS", Path(tmp)):
            self.assertEqual(build.llms_txt(texte), "# Neur.on\n\n> Résumé.\n\n## Produit\n\n- [Corrext](https://neur-on.ai/fr/corrext/)\n")
            (Path(tmp) / "de/corrext").mkdir(parents=True)
            (Path(tmp) / "de/corrext/index.html").write_text("<!DOCTYPE html>", encoding="utf-8")
            garde = build.llms_txt(texte)
            self.assertIn("## Deutsch\n\n- [Corrext](https://neur-on.ai/de/corrext/)\n", garde)
            self.assertIn("- [Corrext DE](https://neur-on.ai/de/corrext/)", garde)
            self.assertNotIn("https://neur-on.ai/de/)", garde)
            self.assertNotIn("## English", garde)


class TestPlanDuSite(unittest.TestCase):
    def test_sitemap_des_pages_indexables(self):
        import xml.etree.ElementTree as ET
        import redirections
        docs = support.site_complet(apercu=False)
        racine = ET.parse(docs / "sitemap.xml").getroot()
        ns = "{http://www.sitemaps.org/schemas/sitemap/0.9}"
        self.assertEqual(racine.tag, ns + "urlset")
        locs = [u.find(ns + "loc").text for u in racine.findall(ns + "url")]
        self.assertEqual(len(locs), len(set(locs)))
        attendues = {"https://neur-on.ai/fr/" + p for p in build.PAGES if p != "contact/merci/"}
        self.assertEqual(set(locs), attendues)
        self.assertNotIn("https://neur-on.ai/fr/contact/merci/", locs)  # noindex
        for ancien in redirections.lire(build.NEURON):  # redirections : jamais dans le plan
            self.assertNotIn("https://neur-on.ai/" + ancien, locs)
        self.assertNotIn("https://neur-on.ai/", locs)  # page d'aiguillage, non indexée
        for loc in locs:  # chaque adresse est la canonique de sa page
            h = (docs / loc[len("https://neur-on.ai/"):] / "index.html").read_text(encoding="utf-8")
            self.assertIn(f'<link rel="canonical" href="{loc}">', h)

    def test_robots_annonce_le_plan_en_production_seulement(self):
        robots = (support.site_complet(apercu=False) / "robots.txt").read_text(encoding="utf-8")
        self.assertEqual(robots, "User-agent: *\nAllow: /\nSitemap: https://neur-on.ai/sitemap.xml\n")
        apercu = support.site_complet(apercu=True)
        self.assertFalse((apercu / "sitemap.xml").exists())
        self.assertEqual((apercu / "robots.txt").read_text(encoding="utf-8"), "User-agent: *\nDisallow: /\n")


class TestGardeSortie(unittest.TestCase):
    def verdict(self, sortie):
        """None si garde_sortie accepte le dossier, sinon le message de refus."""
        from unittest import mock
        with mock.patch.object(build, "DOCS", Path(sortie).resolve()):
            try:
                build.garde_sortie()
            except SystemExit as e:
                return str(e)
        return None

    def test_seul_docs_dans_le_depot(self):
        self.assertIsNone(self.verdict(build.ICI / "docs"))
        for refuse in (build.ICI, build.ICI / "src", build.ICI / "essai", build.ICI / "docs/sous-dossier",
                       build.ICI / "assets/img", build.ICI.parent, build.NEURON, build.NEURON / "docs", Path.home()):
            self.assertIsNotNone(self.verdict(refuse), refuse)

    def test_hors_du_depot_accepte(self):
        import tempfile
        with tempfile.TemporaryDirectory() as tmp:
            self.assertIsNone(self.verdict(Path(tmp) / "docs"))


class TestProductionSimulee(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.docs = support.site_complet(apercu=False)
        cls.pages = {p: support.chemin(cls.docs, p).read_text(encoding="utf-8") for p in build.PAGES}

    def test_toutes_les_pages_construites(self):
        for p in build.PAGES:
            self.assertTrue(support.chemin(self.docs, p).is_file(), p)
        for f in ("index.html", "404.html", "robots.txt", "envoi.php", ".htaccess"):
            self.assertTrue((self.docs / f).is_file(), f)

    def test_indexable_sans_ruban_sauf_la_page_merci(self):
        for p, h in self.pages.items():
            tete = h[:h.index("</head>")]
            if p == "contact/merci/":
                self.assertIn('<meta name="robots" content="noindex">', tete)
            else:
                self.assertNotIn('name="robots"', tete, p)
            self.assertNotIn('class="ruban"', h, p)

    def test_404_servie_depuis_la_racine_du_domaine(self):
        h = (self.docs / "404.html").read_text(encoding="utf-8")
        self.assertIn('<base href="/">', h)
        self.assertNotIn("noindex", h)

    def test_robots_ouvert(self):
        robots = (self.docs / "robots.txt").read_text(encoding="utf-8")
        self.assertIn("User-agent: *\nAllow: /\n", robots)
        self.assertNotIn("Disallow", robots)

    def test_og_image_sur_chaque_page(self):
        for p, h in self.pages.items():
            self.assertRegex(h[:h.index("</head>")], r'<meta property="og:image" content="https://neur-on\.ai/assets/img/[^"]+">', p)


if __name__ == "__main__":
    unittest.main()
