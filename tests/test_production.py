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
        """Tant que seule la version fr est construite : hreflang fr-CH et x-default, tous deux vers la page elle-même
        (x-default désigne la version française, page indexable, et non plus la racine d'aiguillage non indexée)."""
        for apercu in (False, True):
            docs = support.site_complet(apercu=apercu)
            for p in build.PAGES:
                h = support.chemin(docs, p).read_text(encoding="utf-8")
                alternates = ALTERNATE.findall(h[:h.index("</head>")])
                self.assertEqual(alternates, [("fr-CH", "https://neur-on.ai/fr/" + p), ("x-default", "https://neur-on.ai/fr/" + p)], p)

    def test_alternates_poses_par_les_pages_construites(self):
        """Les hreflang d'une page finalisée viennent des pages construites dans chaque langue (localiser.poser_alternates),
        jamais du contenu du dossier de sortie : une page de cette langue construite les fait apparaître, rien d'écrit en dur."""
        tete = build.seo("corrext/")
        seule = build.finaliser(tete, "corrext/", "fr", {"fr": {"corrext/"}})
        self.assertEqual(sorted(dict(ALTERNATE.findall(seule))), ["fr-CH", "x-default"])
        avec = dict(ALTERNATE.findall(build.finaliser(tete, "corrext/", "fr", {"fr": {"corrext/"}, "de": {"corrext/"}})))
        self.assertEqual(sorted(avec), ["de-CH", "fr-CH", "x-default"])
        self.assertEqual(avec["de-CH"], "https://neur-on.ai/de/corrext/")
        self.assertEqual(avec["x-default"], "https://neur-on.ai/fr/corrext/")

    def test_adresse_construite(self):
        self.assertTrue(build.adresse_construite("https://neur-on.ai/"))
        self.assertTrue(build.adresse_construite("https://neur-on.ai/fr/corrext/"))
        self.assertFalse(build.adresse_construite("https://neur-on.ai/de/corrext/"))
        self.assertFalse(build.adresse_construite("https://exemple.ch/fr/corrext/"))


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


PAGES_MULTI = ("", "contact/", "contact/merci/")
NS_SITEMAP = "{http://www.sitemaps.org/schemas/sitemap/0.9}"
NS_XHTML = "{http://www.w3.org/1999/xhtml}"


class TestProductionMultilingue(unittest.TestCase):
    """Production simulée en français et en allemand (tâche 1.5) : racine, 404, sitemaps, robots et llms.txt par langue.
    La traduction n'est pas branchée : les pages « de » portent le texte français, seuls les adresses et le balisage comptent."""

    @classmethod
    def setUpClass(cls):
        import tempfile
        cls._tmp = tempfile.TemporaryDirectory()
        cls.docs = support.construire(cls._tmp.name, pages=PAGES_MULTI, config={"apercu": False}, langues=("fr", "de"))

    @classmethod
    def tearDownClass(cls):
        cls._tmp.cleanup()

    def lire(self, fichier):
        return (self.docs / fichier).read_text(encoding="utf-8")

    def urls(self, fichier):
        import xml.etree.ElementTree as ET
        racine = ET.parse(self.docs / fichier).getroot()
        return racine, {u.find(NS_SITEMAP + "loc").text: u for u in racine.findall(NS_SITEMAP + "url")}

    def test_racine_dispo(self):
        h = self.lire("index.html")
        self.assertIn('var dispo=["fr","de"],def="fr"', h)
        self.assertIn('<link rel="alternate" hreflang="de-CH" href="https://neur-on.ai/de/">', h)
        self.assertIn('<link rel="alternate" hreflang="fr-CH" href="https://neur-on.ai/fr/">', h)
        self.assertNotIn("hreflang=\"it-CH\"", h)
        self.assertNotIn("hreflang=\"en\"", h)
        self.assertIn('<link rel="alternate" hreflang="x-default" href="https://neur-on.ai/fr/">', h)
        self.assertIn('<a href="de/" hreflang="de-CH">DE</a> · <a href="fr/" hreflang="fr-CH">FR</a>', h)
        self.assertNotIn('href="it/"', h)
        self.assertNotIn(" · </p>", h)

    def test_racine_sans_langue_construite_hors_fr(self):
        """Une langue configurée dont la page d'accueil n'est pas construite n'est ni dans la liste, ni dans les liens."""
        import tempfile
        from unittest import mock
        absente = mock.patch.object(build, "TRADUIRE", lambda html, page, langue: (html, ["segment manquant"]))
        with tempfile.TemporaryDirectory() as tmp:
            docs = support.construire(tmp, pages=PAGES_MULTI, config={"apercu": False}, langues=("fr", "de"), patches=[absente])
            h = (docs / "index.html").read_text(encoding="utf-8")
            self.assertIn('var dispo=["fr"],def="fr"', h)
            self.assertNotIn("de-CH", h)
            # ni sitemap par langue, ni index, ni 404 allemande, ni llms.txt allemand : le français seul, comme avant
            self.assertFalse((docs / "de").exists())
            self.assertIn("<urlset", (docs / "sitemap.xml").read_text(encoding="utf-8"))
            self.assertNotIn("sitemap-", " ".join(f.name for f in docs.iterdir()))
            self.assertNotIn("Versions linguistiques", (docs / "llms.txt").read_text(encoding="utf-8"))

    def test_404_par_langue(self):
        h = self.lire("de/404.html")
        self.assertIn('<html lang="de" ', h)
        self.assertIn('<base href="/">', h)
        self.assertNotIn("noindex", h)
        self.assertNotIn("{{", h)
        self.assertNotIn("@LANG@", h)
        self.assertIn("ErrorDocument 404 /de/404.html", self.lire("de/.htaccess"))
        # la 404 française reste à la racine, en français
        fr = self.lire("404.html")
        self.assertIn('<html lang="fr" ', fr)
        self.assertIn("ErrorDocument 404 /404.html", self.lire(".htaccess"))

    def test_404_liens_dans_la_langue_et_selecteur(self):
        """Les liens de la 404 allemande mènent aux pages allemandes construites ; le sélecteur renvoie vers les accueils."""
        de = self.lire("de/404.html")
        self.assertIn('href="de/kontakt/"', de)
        self.assertIn('<a href="fr/" hreflang="fr-CH" lang="fr" translate="no">FR</a>', de)
        self.assertIn('<a href="de/" hreflang="de-CH" lang="de" translate="no" aria-current="true">DE</a>', de)
        self.assertIn('hreflang="de-CH" lang="de" translate="no">DE</a>', self.lire("404.html"))

    def test_sitemap_index_et_par_langue(self):
        import xml.etree.ElementTree as ET
        index = ET.parse(self.docs / "sitemap.xml").getroot()
        self.assertEqual(index.tag, NS_SITEMAP + "sitemapindex")
        self.assertEqual([s.find(NS_SITEMAP + "loc").text for s in index.findall(NS_SITEMAP + "sitemap")],
                         ["https://neur-on.ai/sitemap-fr.xml", "https://neur-on.ai/sitemap-de.xml"])
        racine, urls = self.urls("sitemap-de.xml")
        self.assertEqual(set(urls), {"https://neur-on.ai/de/", "https://neur-on.ai/de/kontakt/"})
        liens = {l.get("hreflang"): l.get("href") for l in urls["https://neur-on.ai/de/kontakt/"].findall(NS_XHTML + "link")}
        self.assertEqual(liens, {"fr-CH": "https://neur-on.ai/fr/contact/", "de-CH": "https://neur-on.ai/de/kontakt/",
                                 "x-default": "https://neur-on.ai/fr/contact/"})
        for l in urls["https://neur-on.ai/de/kontakt/"].findall(NS_XHTML + "link"):
            self.assertEqual(l.get("rel"), "alternate")
        _, fr = self.urls("sitemap-fr.xml")
        self.assertEqual(set(fr), {"https://neur-on.ai/fr/", "https://neur-on.ai/fr/contact/"})
        liens_fr = {l.get("hreflang") for l in fr["https://neur-on.ai/fr/"].findall(NS_XHTML + "link")}
        self.assertEqual(liens_fr, {"fr-CH", "de-CH", "x-default"})
        self.assertIn("lastmod", ET.tostring(urls["https://neur-on.ai/de/"], encoding="unicode"))

    def test_merci_non_indexee_par_langue(self):
        for fichier in ("sitemap-de.xml", "sitemap-fr.xml"):
            self.assertNotIn("danke", self.lire(fichier))
            self.assertNotIn("merci", self.lire(fichier))
        self.assertTrue((self.docs / "de/kontakt/danke/index.html").is_file())

    def test_robots_annonce_l_index(self):
        self.assertEqual(self.lire("robots.txt"), "User-agent: *\nAllow: /\nSitemap: https://neur-on.ai/sitemap.xml\n")

    def test_llms_par_langue(self):
        de = self.lire("de/llms.txt")
        adresses = re.findall(r"\]\((https://[^)]+)\)", de)
        self.assertTrue(adresses)
        for a in adresses:
            self.assertTrue(a.startswith("https://neur-on.ai/de/"), a)
        self.assertIn("(https://neur-on.ai/de/kontakt/)", de)
        self.assertNotIn("danke", de)
        self.assertIn("https://neur-on.ai/de/llms-full.txt", de)
        full = self.lire("de/llms-full.txt")
        self.assertIn("Source : https://neur-on.ai/de/kontakt/", full)
        self.assertIn("https://neur-on.ai/de/llms.txt", full)
        racine = self.lire("llms.txt")
        self.assertIn("## Versions linguistiques", racine)
        self.assertIn("https://neur-on.ai/de/llms.txt", racine)
        self.assertIn("(https://neur-on.ai/fr/contact/)", racine)
        self.assertLess(racine.index("## Versions linguistiques"), racine.index("## Optional") if "## Optional" in racine else len(racine))


class TestLlmsParLangue(unittest.TestCase):
    PAGES = [("", {"title": "Accueil · Neur.on", "description": "Résumé."}),
             ("contact/", {"title": "Contact · Neur.on", "description": ""})]

    def test_adresse(self):
        from outils import llms
        self.assertEqual(llms.adresse("contact/"), "https://neur-on.ai/fr/contact/")
        self.assertEqual(llms.adresse("contact/", "de"), "https://neur-on.ai/de/kontakt/")
        self.assertEqual(llms.adresse("", "en"), "https://neur-on.ai/en/")

    def test_francais_par_defaut_inchange(self):
        from outils import llms
        self.assertEqual(llms.llms_txt(self.PAGES, "2026-10-23"), llms.llms_txt(self.PAGES, "2026-10-23", "fr", lambda s: s))
        self.assertNotIn("Versions linguistiques", llms.llms_txt(self.PAGES, "2026-10-23"))
        self.assertIn("Texte intégral des pages principales : https://neur-on.ai/llms-full.txt", llms.llms_txt(self.PAGES, "2026-10-23"))

    def test_libelles_passent_par_t(self):
        """t reçoit chaque libellé fixe (sections, phrase d'introduction) ; l'identité les laisse tels quels."""
        from outils import llms
        vus = []
        llms.llms_txt(self.PAGES, "2026-10-23", "de", lambda s: vus.append(s) or s)
        self.assertIn("Accueil", vus)
        self.assertIn("Contact", vus)
        self.assertTrue(any("Texte intégral" in s for s in vus))
        txt = llms.llms_txt(self.PAGES, "2026-10-23", "de", lambda s: {"Contact": "Kontakt"}.get(s, s))
        self.assertIn("## Kontakt", txt)
        self.assertIn("(https://neur-on.ai/de/kontakt/)", txt)
        self.assertIn("https://neur-on.ai/de/llms-full.txt", txt)


class TestPageRacine(unittest.TestCase):
    def test_liste_et_liens_des_seules_langues_donnees(self):
        for dispo in (["fr"], ["fr", "de"], ["fr", "it", "en"], ["fr", "de", "it", "en"]):
            h = build.page_racine(dispo)
            self.assertIn("var dispo=" + str(dispo).replace("'", '"').replace(" ", "") + ',def="fr"', h)
            codes = {"fr": "fr-CH", "de": "de-CH", "it": "it-CH", "en": "en"}
            for langue, hreflang in codes.items():
                presente = langue in dispo
                self.assertEqual(f'hreflang="{hreflang}" href="https://neur-on.ai/{langue}/"' in h, presente, (dispo, langue))
                self.assertEqual(f'<a href="{langue}/" hreflang="{hreflang}">' in h, presente, (dispo, langue))
            self.assertNotIn(" · </p>", h)
            self.assertIn('hreflang="x-default" href="https://neur-on.ai/fr/"', h)

    def test_defaut_francais_seul(self):
        self.assertEqual(build.page_racine(), build.page_racine(["fr"]))


if __name__ == "__main__":
    unittest.main()
