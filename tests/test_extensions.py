"""Points d'extension du build (spec V2 § 3) : composants CSS, scripts globaux, post-traitements, repli SEO d'une
page nouvelle, API des contenus nouveaux et document de relecture."""
import contextlib
import io
import json
import re
import shutil
import sys
import tempfile
import unittest
from pathlib import Path
from unittest import mock

ICI = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ICI))
import build  # noqa: E402
from outils import contenus, post, relecture  # noqa: E402
from tests import support  # noqa: E402

IMAGE_V1_NON_UTILISEE = "assets/img/neuron-symbol.png"  # présente dans le site Neur.on, citée par aucune page V2


def assets_de_test(tmp, composants=None, globaux=None):
    """Copie des assets du dépôt, sans composants ni scripts globaux, plus ceux qu'on donne : {nom: contenu}."""
    assets = Path(tmp) / "assets"
    shutil.copytree(build.ASSETS, assets, ignore=shutil.ignore_patterns("composants", "global"))
    for dossier, fichiers in (("composants", composants or {}), ("global", globaux or {})):
        for nom, code in fichiers.items():
            (assets / dossier).mkdir(exist_ok=True)
            (assets / dossier / nom).write_text(code, encoding="utf-8")
    return assets


class TestComposantsEtScriptsGlobaux(unittest.TestCase):
    def test_dossiers_d_extension_presents(self):
        for dossier in ("assets/composants", "assets/global", "outils/post"):
            self.assertTrue((ICI / dossier).is_dir(), dossier)

    def test_css_concatene_a_la_fin_de_site_css_dans_l_ordre(self):
        with tempfile.TemporaryDirectory() as tmp:
            assets = assets_de_test(tmp, composants={"b.css": ".b-essai{color:red}\n", "a.css": ".a-essai{color:blue}", "x.txt": "EXCLU-TXT"})
            sortie = Path(tmp) / "docs"
            sortie.mkdir()
            with mock.patch.object(build, "DOCS", sortie), mock.patch.object(build, "ASSETS", assets):
                build.copier_assets()
            css = (sortie / "assets/site.css").read_text(encoding="utf-8")
            self.assertTrue(css.startswith((assets / "site.css").read_text(encoding="utf-8")))
            self.assertLess(css.index(".a-essai"), css.index(".b-essai"))
            self.assertTrue(css.rstrip().endswith(".b-essai{color:red}"))
            self.assertNotIn("EXCLU-TXT", css)  # seuls les fichiers .css sont repris
            self.assertFalse((sortie / "assets/composants").exists())  # recopiés dans site.css, pas en double

    def test_js_global_reuni_dans_l_ordre_et_charge_en_defer_partout(self):
        with tempfile.TemporaryDirectory() as tmp:
            assets = assets_de_test(tmp, globaux={"b.js": "window.b=1", "a.js": "(function(){window.a=1})()"})
            sortie = support.construire(tmp, ["", "contact/"], patches=[mock.patch.object(build, "ASSETS", assets)])
            js = (sortie / "assets/global.js").read_text(encoding="utf-8")
            self.assertLess(js.index("window.a=1"), js.index("window.b=1"))
            self.assertIn("})()\n;\n", js)  # un ; sépare les fichiers : pas de fusion de deux expressions voisines
            self.assertFalse((sortie / "assets/global").exists())
            for chemin, racine in (("fr/index.html", "../"), ("fr/contact/index.html", "../../"), ("404.html", "")):
                h = (sortie / chemin).read_text(encoding="utf-8")
                balise = re.findall(r'<script src="' + re.escape(racine) + r'assets/global\.js\?v=[0-9a-f]{8}" defer></script>', h)
                self.assertEqual(len(balise), 1, chemin)
                self.assertLess(h.index("assets/nav.js"), h.index("assets/global.js"), chemin)

    def test_sans_fichier_ni_global_js_ni_balise(self):
        with tempfile.TemporaryDirectory() as tmp:
            assets = assets_de_test(tmp)
            sortie = support.construire(tmp, ["", "contact/"], patches=[mock.patch.object(build, "ASSETS", assets)])
            self.assertFalse((sortie / "assets/global.js").exists())
            self.assertEqual((sortie / "assets/site.css").read_bytes(), (assets / "site.css").read_bytes())
            for chemin in ("fr/index.html", "404.html"):
                self.assertNotIn("global.js", (sortie / chemin).read_text(encoding="utf-8"))

    def test_la_version_des_assets_suit_les_composants(self):
        with tempfile.TemporaryDirectory() as tmp:
            sans = support.construire(Path(tmp) / "1", ["contact/"], patches=[mock.patch.object(build, "ASSETS", assets_de_test(Path(tmp) / "1"))])
            avec = support.construire(Path(tmp) / "2", ["contact/"], patches=[
                mock.patch.object(build, "ASSETS", assets_de_test(Path(tmp) / "2", composants={"a.css": ".a{}"}))])
            v = lambda d: re.search(r"site\.css\?v=([0-9a-f]{8})", (d / "fr/contact/index.html").read_text(encoding="utf-8")).group(1)
            self.assertNotEqual(v(sans), v(avec))


def module_post(dossier, nom, corps):
    (Path(dossier) / nom).write_text(corps, encoding="utf-8")


class TestPostTraitements(unittest.TestCase):
    def test_ordre_alphabetique_et_signature(self):
        with tempfile.TemporaryDirectory() as tmp:
            module_post(tmp, "z_dernier.py", 'def traiter(html, page):\n    return html + "[z:" + page + "]"\n')
            module_post(tmp, "a_premier.py", 'def traiter(html, page):\n    return html + "[a:" + page + "]"\n')
            module_post(tmp, "_prive.py", 'def traiter(html, page):\n    raise AssertionError("jamais appelé")\n')
            module_post(tmp, "m_milieu.py", 'def traiter(html, page):\n    return html + "[m:" + page + "]"\n')
            self.assertEqual(post.appliquer("<p>", "corrext/", dossier=tmp), "<p>[a:corrext/][m:corrext/][z:corrext/]")

    def test_dossier_sans_module_ne_change_rien(self):
        with tempfile.TemporaryDirectory() as tmp:
            self.assertEqual(post.appliquer("<p>", "x/", dossier=tmp), "<p>")

    def test_module_sans_traiter_refuse(self):
        with tempfile.TemporaryDirectory() as tmp:
            module_post(tmp, "a_mal_fait.py", "x = 1\n")
            with self.assertRaises(TypeError):
                post.appliquer("<p>", "x/", dossier=tmp)

    def test_appliques_dans_le_build_avant_relier_sur_toutes_les_pages(self):
        """Le post-traitement voit la page complète avec ses {{ROOT}} : les liens qu'il ajoute sont résolus ensuite, et les
        images V1 qu'il cite sont copiées. La 404 est traitée sous le nom 404.html (jamais sous celui de l'accueil)."""
        with tempfile.TemporaryDirectory() as tmp:
            dossier = Path(tmp) / "post"
            dossier.mkdir()
            module_post(dossier, "a_essai.py", (
                'def traiter(html, page):\n'
                '    assert html.rstrip().endswith("</html>") and "{{ROOT}}" in html\n'
                '    ajout = \'<a id="essai" href="{{ROOT}}contact/">contact</a><img src="{{ROOT}}' + IMAGE_V1_NON_UTILISEE + '" alt="">\'\n'
                '    return html.replace("</body>", "<!--page:" + page + "-->" + ajout + "</body>")\n'))
            sortie = support.construire(tmp, ["", "corrext/", "contact/"], patches=[mock.patch.object(post, "DOSSIER", dossier)])
            h = (sortie / "fr/corrext/index.html").read_text(encoding="utf-8")
            self.assertIn('<!--page:corrext/--><a id="essai" href="../../fr/contact/">contact</a>', h)
            self.assertIn('src="../../' + IMAGE_V1_NON_UTILISEE + '"', h)
            self.assertTrue((sortie / IMAGE_V1_NON_UTILISEE).is_file())
            self.assertIn("<!--page:-->", (sortie / "fr/index.html").read_text(encoding="utf-8"))
            h404 = (sortie / "404.html").read_text(encoding="utf-8")
            self.assertIn("<!--page:404.html--><a id=\"essai\" href=\"fr/contact/\">", h404)

    def test_les_modules_du_depot_sont_valides(self):
        post.modules()  # ne lève rien : chaque module du dépôt expose traiter(html, page)


PAGE_FACTICE = "corrext/page-factice/"


class TestRepliSeo(unittest.TestCase):
    """Une page sans équivalent dans le site Neur.on actuel (page nouvelle) reçoit tout de même canonique, Open Graph
    et fil d'Ariane."""

    def construire(self, tmp, titre="Page factice pour Corrext · Neur.on", description='Description "factice" & prête.'):
        src = Path(tmp) / "src"
        for p, t, d in (("", "Neur.on", "Accueil factice."), (PAGE_FACTICE, titre, description)):
            f = src / "pages" / p / "index.html"
            f.parent.mkdir(parents=True, exist_ok=True)
            f.write_text(f"<!--page\ntitle: {t}\ndescription: {d}\nmenu: corrext\n-->\n"
                         '<section class="hero"><div class="wrap"><h1 class="h1">Titre factice</h1></div></section>\n', encoding="utf-8")
        return support.construire(tmp, ["", PAGE_FACTICE], patches=[mock.patch.object(build, "SRC", src)])

    def test_page_sans_source_v1(self):
        with tempfile.TemporaryDirectory() as tmp:
            self.assertFalse((build.NEURON / "docs/fr" / PAGE_FACTICE).exists())
            h = (self.construire(tmp) / "fr" / PAGE_FACTICE / "index.html").read_text(encoding="utf-8")
        tete = h[:h.index("</head>")]
        url = "https://neur-on.ai/fr/" + PAGE_FACTICE
        for attendu in (
            f'<link rel="canonical" href="{url}">',
            f'<link rel="alternate" hreflang="fr-CH" href="{url}">',
            '<link rel="alternate" hreflang="x-default" href="https://neur-on.ai/">',
            '<meta property="og:title" content="Page factice pour Corrext · Neur.on">',
            '<meta property="og:description" content="Description &quot;factice&quot; &amp; prête.">',
            f'<meta property="og:url" content="{url}">',
            '<meta property="og:type" content="website">',
            '<meta property="og:image" content="https://neur-on.ai/assets/img/og-neuron.jpg">',
            '<meta property="og:locale" content="fr_CH">',
            '<meta property="og:site_name" content="Neur.on">',
            '<meta name="twitter:card" content="summary_large_image">',
        ):
            self.assertIn(attendu, tete)
        blocs = re.findall(r'<script type="application/ld\+json">(.*?)</script>', tete, re.S)
        self.assertEqual(len(blocs), 1)
        fil = json.loads(blocs[0])
        self.assertEqual(fil["@type"], "BreadcrumbList")
        self.assertEqual([(i["position"], i["name"], i["item"]) for i in fil["itemListElement"]], [
            (1, "Accueil", "https://neur-on.ai/fr/"),
            (2, "Corrext", "https://neur-on.ai/fr/corrext/"),  # libellé repris de la page Corrext du site actuel
            (3, "Page factice pour Corrext", url),
        ])

    def test_page_avec_source_v1_garde_son_referencement_repris(self):
        with tempfile.TemporaryDirectory() as tmp:
            h = (self.construire(tmp) / "fr/index.html").read_text(encoding="utf-8")
        # le référencement de la page d'accueil actuelle est repris (données structurées comprises), sauf les hreflang
        # des langues absentes de la sortie : seuls fr-CH et x-default restent tant que fr est la seule langue construite
        self.assertIn('<link rel="alternate" hreflang="fr-CH" href="https://neur-on.ai/fr/">', h)
        self.assertIn('<link rel="alternate" hreflang="x-default" href="https://neur-on.ai/">', h)
        self.assertNotIn('hreflang="de-CH"', h)
        self.assertRegex(h, r'"@type": ?"WebSite"')

    def test_404_sans_balises_de_referencement(self):
        with tempfile.TemporaryDirectory() as tmp:
            h = (self.construire(tmp) / "404.html").read_text(encoding="utf-8")
        self.assertNotIn("canonical", h)
        self.assertNotIn("application/ld+json", h)


class TestContenusNouveaux(unittest.TestCase):
    def dossier(self, tmp):
        d = Path(tmp)
        (d / "A-essai.json").write_text(json.dumps({"lot": "A", "entrees": [
            {"cle": "essai.hero.s", "page": "corrext/plugin-word/", "texte": "Un texte.", "statut": "a_relire", "source": "Fabien, 2026-10-14"},
            {"cle": "essai.faq.1", "page": "corrext/plugin-word/", "texte": "Deux phrases.\nSur deux lignes.", "statut": "valide", "source": "Fabien"},
        ]}), encoding="utf-8")
        (d / "B-essai.json").write_text(json.dumps({"lot": "B", "entrees": [
            {"cle": "schema.titre", "page": "corrext/", "texte": "Un schéma.", "statut": "a_relire", "source": "base de connaissances"}]}),
            encoding="utf-8")
        return d

    def test_texte_et_toutes(self):
        with tempfile.TemporaryDirectory() as tmp:
            d = self.dossier(tmp)
            self.assertEqual(contenus.texte("essai.hero.s", dossier=d), "Un texte.")
            self.assertEqual(contenus.texte("schema.titre", dossier=d), "Un schéma.")
            with self.assertRaises(KeyError):
                contenus.texte("absente", dossier=d)
            self.assertEqual([(e["lot"], e["cle"]) for e in contenus.toutes(dossier=d)],
                             [("A", "essai.hero.s"), ("A", "essai.faq.1"), ("B", "schema.titre")])

    def test_cle_en_double_refusee(self):
        with tempfile.TemporaryDirectory() as tmp:
            d = self.dossier(tmp)
            (d / "C-doublon.json").write_text(json.dumps({"lot": "C", "entrees": [
                {"cle": "schema.titre", "page": "x/", "texte": "t", "statut": "a_relire", "source": "s"}]}), encoding="utf-8")
            with self.assertRaises(ValueError):
                contenus.toutes(dossier=d)

    def test_dossier_du_depot(self):
        self.assertIsInstance(contenus.toutes(), list)

    def test_document_de_relecture(self):
        with tempfile.TemporaryDirectory() as tmp:
            sortie = Path(tmp) / "RELECTURE.md"
            relecture.ecrire(sortie=sortie, dossier=self.dossier(tmp))
            md = sortie.read_text(encoding="utf-8")
        # par lot, puis par page, puis par clé ; chaque entrée donne sa clé, son texte, son statut et sa source
        self.assertLess(md.index("## Lot A"), md.index("### corrext/plugin-word/"))
        self.assertLess(md.index("### corrext/plugin-word/"), md.index("## Lot B"))
        self.assertLess(md.index("## Lot B"), md.index("### corrext/\n"))
        for attendu in ("`essai.hero.s`** · à relire · source : Fabien, 2026-10-14", "> Un texte.", "> Deux phrases.\n> Sur deux lignes.", "· validé ·",
                        "base de connaissances", "3 textes : 2 à relire, 1 validé"):
            self.assertIn(attendu, md)

    def test_document_vide_mais_valide(self):
        with tempfile.TemporaryDirectory() as tmp:
            sortie = Path(tmp) / "RELECTURE.md"
            vide = Path(tmp) / "vide"
            vide.mkdir()
            relecture.ecrire(sortie=sortie, dossier=vide)
            md = sortie.read_text(encoding="utf-8")
        self.assertTrue(md.startswith("# Relecture des contenus nouveaux"))
        self.assertIn("Aucun contenu nouveau", md)

    def test_sortie_par_defaut_a_la_racine_du_depot(self):
        self.assertEqual(relecture.SORTIE, ICI / "RELECTURE-CONTENUS.md")


if __name__ == "__main__":
    unittest.main()
