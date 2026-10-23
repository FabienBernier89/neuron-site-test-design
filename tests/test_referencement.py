"""Référencement de production (audit SEO et GEO du 2026-10-23) : llms.txt généré, .htaccess (HTTPS, hôte canonique,
compression, cache), JSON-LD (@context, Organization unique, dateModified), sitemap daté, redirections sans ancre
absente, x-default indexable, référencement figé hors de la V1."""
import html as H
import json
import re
import sys
import tempfile
import unittest
import xml.etree.ElementTree as ET
from pathlib import Path
from unittest import mock

ICI = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ICI))
import build  # noqa: E402
import redirections  # noqa: E402
from outils import donnees_structurees as DS  # noqa: E402
from outils import llms  # noqa: E402
from tests import support  # noqa: E402

PROD = "https://neur-on.ai/"
LD = re.compile(r'<script type="application/ld\+json">(.*?)</script>', re.S)
DATE = re.compile(r"^\d{4}-\d{2}-\d{2}$")


def pages_html(sortie):
    return {p: support.chemin(sortie, p).read_text(encoding="utf-8") for p in build.PAGES}


class TestLlmsTxt(unittest.TestCase):
    """1. llms.txt et llms-full.txt générés depuis les pages de la V2, plus copiés de la V1."""

    @classmethod
    def setUpClass(cls):
        cls.sortie = support.site_complet(apercu=False)
        cls.texte = (cls.sortie / "llms.txt").read_text(encoding="utf-8")
        cls.complet = (cls.sortie / "llms-full.txt").read_text(encoding="utf-8")
        cls.liens = re.findall(r"^- \[([^\]]+)\]\((https://neur-on\.ai/[^)]*)\)(?:: (.*))?$", cls.texte, re.M)

    def test_pages_de_la_v2(self):
        urls = [u for _, u, _ in self.liens]
        for page in ("", "corrext/", "corrext/plugin-word/", "tarifs/", "lexmachina/", "solutions/", "traduction/",
                     "ressources/", "securite-souverainete/", "a-propos/", "a-propos/presse/", "contact/",
                     "protection-des-donnees/"):
            self.assertIn(PROD + "fr/" + page, urls, page)

    def test_chaque_page_indexable_une_fois_et_rien_d_autre(self):
        urls = [u for _, u, _ in self.liens]
        attendues = [PROD + "fr/" + p for p in build.PAGES if p not in build.NON_INDEXEES]
        self.assertEqual(sorted(urls), sorted(attendues))
        self.assertNotIn(PROD + "fr/contact/merci/", urls)
        for url in urls:
            self.assertTrue((self.sortie / url[len(PROD):] / "index.html").is_file(), url)

    def test_titres_et_descriptions_tires_de_la_meta(self):
        """Rien d'inventé : chaque titre et chaque description sont ceux de la méta de la page."""
        for titre, url, desc in self.liens:
            meta, _ = build.lire_page(url[len(PROD + "fr/"):])
            self.assertEqual(titre, llms.titre(meta), url)
            self.assertEqual(desc, H.unescape(meta["description"]).strip(), url)
        accueil, _ = build.lire_page("")
        self.assertIn("> " + H.unescape(accueil["description"]), self.texte)

    def test_plus_de_copie_de_la_v1(self):
        v1 = build.NEURON / "docs/llms.txt"
        if v1.is_file():
            self.assertNotEqual(self.texte, v1.read_text(encoding="utf-8"))
        self.assertTrue(self.texte.startswith("# Neur.on\n\n> "))
        self.assertIn("\n## Optional\n", self.texte)
        self.assertIsNone(re.search(r"neur-on\.ai/(?:de|it|en)/", self.texte))

    def test_llms_full_sans_scenes(self):
        for page in llms.PAGES_COMPLETES:
            self.assertIn(f"Source : {PROD}fr/{page}\n", self.complet, page)
        self.assertIn("# Corrext : reprenez le contrôle de vos traductions", self.complet)
        # texte des scènes d'interface (écran Corrext de l'accueil, tableau de bord) : absent
        for scene in ("You have chosen to use third-party", "Corrext Home", "échéance jeudi"):
            self.assertNotIn(scene, self.complet, scene)

    def test_identique_en_apercu(self):
        apercu = support.site_complet(apercu=True)
        self.assertEqual((apercu / "llms.txt").read_text(encoding="utf-8"), self.texte)


class TestHtaccessProduction(unittest.TestCase):
    """2. HTTPS, hôte sans www, sans chaîne, compression et cache sous garde IfModule."""

    @classmethod
    def setUpClass(cls):
        cls.sortie = support.site_complet(apercu=False)
        cls.lignes = (cls.sortie / ".htaccess").read_text(encoding="utf-8").splitlines()

    def index(self, ligne):
        self.assertIn(ligne, self.lignes)
        return self.lignes.index(ligne)

    def test_https_et_www(self):
        hote = self.index(r"RewriteCond %{HTTP_HOST} ^(www\.)?neur-on\.ai$ [NC]")
        https = self.index("RewriteCond %{HTTPS} !=on")
        www = self.index(r"RewriteCond %{HTTP_HOST} ^www\.neur-on\.ai$ [NC]")
        regle = "RewriteRule ^ https://neur-on.ai%{REQUEST_URI} [R=301,L,NE]"
        self.assertEqual([i for i, l in enumerate(self.lignes) if l == regle], [https + 2, www + 1])
        self.assertLess(hote, https)
        self.assertEqual(self.lignes[https + 1], "RewriteCond %{HTTP:X-Forwarded-Proto} !=https")

    def test_sans_chaine(self):
        """Toute redirection va directement à https://neur-on.ai/ vers une page réelle, et les règles d'anciennes
        adresses passent avant la règle d'adresse canonique (http://www.../about/ arrive en un saut)."""
        regles = [(i, l.split()) for i, l in enumerate(self.lignes) if l.startswith("RewriteRule ")]
        canonique = min(i for i, l in regles if l[1] == "^")
        for i, (_, modele, cible, options) in regles:
            self.assertTrue(cible.startswith("https://neur-on.ai/") or cible.startswith("https://neur-on.ai%"), cible)
            if modele != "^":
                self.assertLess(i, canonique, modele)
                page = cible[len(PROD):].split("#")[0]
                self.assertTrue((self.sortie / page / "index.html").is_file(), cible)
                self.assertNotIn('http-equiv="refresh"', (self.sortie / page / "index.html").read_text(encoding="utf-8"))

    def test_compression_et_cache_sous_garde(self):
        texte = "\n".join(self.lignes)
        self.assertRegex(texte, r"<IfModule mod_deflate\.c>\n  <IfModule mod_filter\.c>\n    AddOutputFilterByType DEFLATE text/html[^\n]*text/css[^\n]*application/javascript")
        ouverts = []
        for l in (x.strip() for x in self.lignes):
            if l.startswith("<IfModule"):
                ouverts.append(l)
            elif l == "</IfModule>":
                ouverts.pop()
            elif l.startswith(("AddOutputFilterByType", "Header ")):
                self.assertTrue(ouverts, l)  # jamais hors d'un garde IfModule
        self.assertEqual(ouverts, [])
        self.assertIn('Header set Cache-Control "public, max-age=2592000"', texte)  # images (sans empreinte) : un mois


class TestDonneesStructurees(unittest.TestCase):
    """3 et 8. JSON-LD de toutes les pages : JSON valide, @context partout, une seule définition de Neur.on, datée."""

    @classmethod
    def setUpClass(cls):
        cls.pages = {mode: pages_html(support.site_complet(apercu=mode)) for mode in (False, True)}

    def noeuds(self, o):
        if isinstance(o, dict):
            yield o
            for v in o.values():
                yield from self.noeuds(v)
        elif isinstance(o, list):
            for v in o:
                yield from self.noeuds(v)

    def test_json_et_contexte(self):
        for mode, pages in self.pages.items():
            for p, h in pages.items():
                blocs = [json.loads(b) for b in LD.findall(h)]
                self.assertTrue(blocs, p)
                for b in blocs:
                    for o in (b if isinstance(b, list) else [b]):
                        self.assertIsInstance(o, dict, p)
                        self.assertEqual(o.get("@context"), "https://schema.org", (mode, p or "accueil"))

    def test_une_seule_definition_par_id(self):
        definitions_neuron = []
        for p, h in self.pages[False].items():
            par_id = {}
            for b in (json.loads(x) for x in LD.findall(h)):
                for n in self.noeuds(b):
                    if "@id" in n and len(n) > 1 and "Organization" in DS.types(n):  # définition (une référence n'a que son @id)
                        par_id.setdefault(n["@id"], []).append(n)
                    if DS.est_neuron(n):
                        self.assertEqual(n.get("@id"), DS.ID_ORGANISATION, p)  # plus d'objet éclaté sans @id
            for i, defs in par_id.items():
                self.assertEqual(len(defs), 1, (p or "accueil", i))
            if DS.ID_ORGANISATION in par_id:
                definitions_neuron.append(par_id[DS.ID_ORGANISATION][0])
        self.assertGreater(len(definitions_neuron), 30)
        for d in definitions_neuron:  # même entité partout, telle que src/data/organisation.json
            self.assertEqual({k: d[k] for k in DS.ORGANISATION}, DS.ORGANISATION)

    def test_organisation_sans_fait_invente(self):
        o = DS.ORGANISATION
        self.assertEqual(o["@id"], "https://neur-on.ai/#organisation")
        self.assertEqual(o["legalName"], "Neur.on AI Solutions SA")
        self.assertEqual((o["address"]["streetAddress"], o["address"]["postalCode"], o["address"]["addressLocality"],
                          o["address"]["addressCountry"]), ("Place de la Gare 15", "1700", "Fribourg", "CH"))
        for absent in ("foundingDate", "identifier", "taxID", "vatID", "founder", "numberOfEmployees"):
            self.assertNotIn(absent, o)
        mentions = (ICI / "src/pages/mentions-legales/index.html").read_text(encoding="utf-8")
        for fait in ("Place de la Gare 15", "1700 Fribourg"):
            self.assertIn(fait, mentions)
        for lien in o["sameAs"]:
            self.assertIn(lien, (support.site_complet(apercu=False) / "fr/index.html").read_text(encoding="utf-8"))

    def test_date_de_modification(self):
        for p, h in self.pages[False].items():
            dates = []
            for b in (json.loads(x) for x in LD.findall(h)):
                for n in DS.premier_niveau(b):
                    if DS.types(n) & (DS.TYPES_PAGE | DS.TYPES_ARTICLE):
                        self.assertIn("dateModified", n, p or "accueil")
                        self.assertRegex(n["dateModified"][:10], DATE)
                        dates.append(n["dateModified"])
            self.assertTrue(dates, p or "accueil")
            if not any(t in h for t in ('"BlogPosting"', '"Article"', '"NewsArticle"')):
                self.assertIn(build.date_page(p), dates, p or "accueil")  # même source que le sitemap


class TestPlanDuSiteDate(unittest.TestCase):
    """4. Chaque <url> du sitemap porte un <lastmod>, la date de la page (date_page)."""

    def test_lastmod(self):
        racine = ET.parse(support.site_complet(apercu=False) / "sitemap.xml").getroot()
        ns = "{http://www.sitemaps.org/schemas/sitemap/0.9}"
        urls = racine.findall(ns + "url")
        self.assertGreater(len(urls), 150)
        for u in urls:
            loc, lastmod = u.find(ns + "loc").text, u.find(ns + "lastmod")
            self.assertIsNotNone(lastmod, loc)
            self.assertRegex(lastmod.text, DATE)
            self.assertEqual(lastmod.text, build.date_page(loc[len(PROD + "fr/"):]), loc)

    def test_date_git_ou_date_du_build(self):
        self.assertRegex(build.date_page("corrext/"), DATE)
        self.assertEqual(build.date_page("page-sans-source/"), build.DATE_BUILD)
        with mock.patch.object(build, "_dates_git", lambda: {}):  # sans git : la date du build
            self.assertEqual(build.date_page("corrext/"), build.DATE_BUILD)


class TestRedirectionsAncres(unittest.TestCase):
    """5. Aucune redirection vers une ancre absente de la page V2."""

    def test_aucune_ancre_absente(self):
        for mode in (False, True):
            sortie = support.site_complet(apercu=mode)
            cibles = re.findall(r"^RewriteRule \^\S+ https://neur-on\.ai(/fr/\S*) \[R=30[12]", (sortie / ".htaccess").read_text(encoding="utf-8"), re.M)
            for ancien in redirections.lire(build.NEURON):
                url = re.search(r'url=([^"]+)"', (sortie / ancien / "index.html").read_text(encoding="utf-8")).group(1)
                cibles.append("/" + url.replace("../", ""))
            self.assertGreater(len(cibles), 100)
            for cible in cibles:
                chemin, _, ancre = cible.partition("#")
                page = (sortie / chemin.strip("/") / "index.html").read_text(encoding="utf-8")
                if ancre:
                    self.assertIn(f'id="{ancre}"', page, cible)

    def test_ancre_absente_retiree_ancre_presente_gardee(self):
        sortie = support.site_complet(apercu=False)
        with mock.patch.object(build, "DOCS", sortie):
            self.assertEqual(build.cible_v2("/fr/ressources/blog/actualites/#actu-108"), "/fr/ressources/blog/actualites/")
            self.assertEqual(build.cible_v2("/fr/mentions-legales/#conditions-d-utilisation"),
                             "/fr/mentions-legales/#conditions-d-utilisation")


class TestXDefault(unittest.TestCase):
    """6. x-default vers une page indexable : la version française de chaque page, jamais la racine d'aiguillage."""

    def test_x_default_indexable(self):
        sortie = support.site_complet(apercu=False)
        for p, h in pages_html(sortie).items():
            x = re.findall(r'<link rel="alternate" hreflang="x-default" href="([^"]+)">', h)
            self.assertEqual(x, [PROD + "fr/" + p], p)
            cible = (sortie / x[0][len(PROD):] / "index.html").read_text(encoding="utf-8")
            if p not in build.NON_INDEXEES:
                self.assertNotIn("noindex", cible.split("</head>")[0], p)
        racine = (sortie / "index.html").read_text(encoding="utf-8")
        self.assertIn('<link rel="alternate" hreflang="x-default" href="https://neur-on.ai/fr/">', racine)

    def test_non_indexees_suit_les_post_traitements(self):
        from outils.post import z_formulaires
        self.assertIn(z_formulaires.MERCI, build.NON_INDEXEES)


# Pages dont le référencement figé a été modifié à dessein après le gel du 2026-10-23 (elles ne sont plus la copie de la V1)
MODIFIEES_DEPUIS_LE_GEL = ()


class TestReferencementFige(unittest.TestCase):
    """7. Le référencement des pages reprises de la V1 est lu dans src/data/referencement/, plus dans la V1."""

    def test_seo_sans_la_v1(self):
        avec = {p: build.seo(p, build.lire_page(p)[0]) for p in build.PAGES}
        with mock.patch.object(build, "NEURON", Path(tempfile.gettempdir()) / "v1-absente-pour-le-test"):
            sans = {p: build.seo(p, build.lire_page(p)[0]) for p in build.PAGES}
            self.assertEqual(build.nom_fil("corrext/"), "Corrext")
        self.assertEqual(sans, avec)
        figees = [p for p in build.PAGES if build.referencement_fige(p)]
        self.assertGreaterEqual(len(figees), 150)
        for p in figees:
            self.assertIn(f'<link rel="canonical" href="{PROD}fr/{p}">', sans[p], p)

    def test_aucune_lecture_de_la_v1_pour_le_referencement(self):
        lus = []
        lire = Path.read_text

        def espion(chemin, *a, **k):
            lus.append(str(chemin))
            return lire(chemin, *a, **k)

        with mock.patch.object(Path, "read_text", espion):
            for p in build.PAGES:
                build.seo(p, {"title": "t", "description": "d"})
        v1 = str(build.NEURON) + "/"  # avec la barre : « Sites/neuron-test-design » n'est pas la V1
        self.assertTrue(lus)
        self.assertEqual([f for f in lus if f.startswith(v1)], [])

    def test_copie_exacte_de_la_v1(self):
        """Les fichiers figés reprennent la V1 sans rien changer (vérifiable tant que la V1 est là)."""
        if not (build.NEURON / "docs/fr").is_dir():
            self.skipTest("site V1 absent")
        from outils import figer_referencement as F
        for p in build.PAGES:
            if p in MODIFIEES_DEPUIS_LE_GEL:
                continue
            fige = build.referencement_fige(p)
            v1 = F.lire_v1(p)
            if fige is None:
                self.assertIsNone(v1, p)
                continue
            self.assertEqual((fige["balises"], fige["donnees_structurees"]), (list(v1[0]), v1[1]), p)


if __name__ == "__main__":
    unittest.main()
