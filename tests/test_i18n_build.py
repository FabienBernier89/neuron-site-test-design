"""Build en trois passes et chemins par langue (tâche 1.2) : adresses, attribut lang, liens relatifs des pages
construites hors français.

La traduction n'est pas encore branchée (build.TRADUIRE est l'identité) : une page « de » contient le texte français.
Ces tests vérifient la structure (chemin, lang, liens relatifs), jamais le texte."""
import re
import tempfile
import unittest
from unittest import mock

import build
from outils.i18n import langues
from tests import support

PAGES = ("", "contact/")


def references(html):
    """Valeurs des href et src relatifs d'une page (ni adresse absolue, ni ancre seule, ni mailto, tel ou data)."""
    return [r for r in re.findall(r'(?:href|src)="([^"]+)"', html) if not r.startswith(("http", "mailto:", "tel:", "#", "data:", "/"))]


def cible(base, ref):
    """Fichier désigné par une référence relative depuis le dossier base."""
    chemin = ref.split("#")[0].split("?")[0]
    fichier = (base / chemin).resolve()
    return fichier / "index.html" if chemin == "" or chemin.endswith("/") else fichier


class TestCheminPage(unittest.TestCase):
    def test_chemin_page_par_langue(self):
        self.assertEqual(build.chemin_page("traduction/contrats/", "de"), build.DOCS / "de/uebersetzung/vertraege/index.html")
        self.assertEqual(build.chemin_page("corrext/", "en"), build.DOCS / "en/corrext/index.html")
        self.assertEqual(build.chemin_page("", "it"), build.DOCS / "it/index.html")
        self.assertEqual(build.chemin_page(""), build.DOCS / "fr" / "index.html")

    def test_langue_ou_page_inconnue(self):
        with self.assertRaises(KeyError):
            build.chemin_page("corrext/", "es")
        with self.assertRaises(KeyError):
            build.chemin_page("page-inexistante/", "de")


class TestRelierParLangue(unittest.TestCase):
    def test_racine_relative_d_une_page_traduite(self):
        """La racine vaut « ../ » autant de fois que l'adresse de la page traduite a de niveaux."""
        self.assertEqual(build.relier('<img src="{{ROOT}}assets/img/x.png">', "contact/", langue="de"),
                         '<img src="../../assets/img/x.png">')
        self.assertEqual(build.relier('<img src="{{ROOT}}assets/img/x.png">', "traduction/contrats/", langue="de"),
                         '<img src="../../../assets/img/x.png">')
        self.assertEqual(build.relier('<a href="{{ROOT}}">', "", langue="it"), '<a href="../fr/">')

    def test_francais_inchange(self):
        self.assertEqual(build.relier('<a href="{{ROOT}}contact/">', "corrext/"),
                         build.relier('<a href="{{ROOT}}contact/">', "corrext/", langue="fr"))

    def test_lien_deja_localise_non_touche(self):
        """Un lien déjà écrit vers une langue (de/, it/, en/) n'est ni envoyé sous fr/ ni renvoyé vers une page modèle."""
        for langue in ("de", "it", "en"):
            h = build.relier(f'<a href="{{{{ROOT}}}}{langue}/kontakt/#x">', "contact/", langue="de")
            self.assertEqual(h, f'<a href="../../{langue}/kontakt/#x">')

    def test_racine_explicite(self):
        self.assertEqual(build.relier('<a href="{{ROOT}}de/kontakt/">', "", racine="", langue="de"), '<a href="de/kontakt/">')


class TestBuildDeuxLangues(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls._tmp = tempfile.TemporaryDirectory()
        cls.sortie = support.construire(cls._tmp.name, pages=PAGES, langues=("fr", "de"))

    @classmethod
    def tearDownClass(cls):
        cls._tmp.cleanup()

    def test_lang_de(self):
        for page in PAGES:
            h = support.chemin(self.sortie, page, "de").read_text(encoding="utf-8")
            self.assertIn('<html lang="de" ', h, page)
        self.assertTrue((self.sortie / "de/index.html").is_file())
        self.assertTrue((self.sortie / "de/kontakt/index.html").is_file())

    def test_lang_fr_inchange(self):
        for page in PAGES:
            h = support.chemin(self.sortie, page).read_text(encoding="utf-8")
            self.assertIn('<html lang="fr" ', h, page)
            self.assertNotIn("@LANG@", h, page)

    def test_aucune_autre_langue(self):
        self.assertFalse((self.sortie / "it").exists())
        self.assertFalse((self.sortie / "en").exists())

    def test_francais_toujours_ecrit_a_cote(self):
        self.assertTrue((self.sortie / "fr/index.html").is_file())
        self.assertTrue((self.sortie / "fr/contact/index.html").is_file())

    def test_404_en_francais_seulement(self):
        h = (self.sortie / "404.html").read_text(encoding="utf-8")
        self.assertIn('<html lang="fr" ', h)
        self.assertNotIn("@LANG@", h)

    def test_assets_resolus_depuis_de(self):
        """Les ressources (feuilles, scripts, polices) d'une page allemande existent depuis son dossier."""
        fichier = support.chemin(self.sortie, "contact/", "de")
        assets = [r for r in references(fichier.read_text(encoding="utf-8")) if "assets/" in r]
        self.assertTrue(assets)
        for ref in assets:
            self.assertTrue(cible(fichier.parent, ref).is_file(), ref)


class TestPagesNonConstruites(unittest.TestCase):
    def test_page_avec_manquant_non_ecrite(self):
        """TRADUIRE signale les segments restés sans traduction : la page n'est pas construite dans cette langue, et les
        autres pages le sont (construites[langue] = pages sans manquant)."""
        def traduire(html, page, langue):
            return html, (["segment manquant"] if page == "contact/" else [])
        with tempfile.TemporaryDirectory() as tmp, mock.patch.object(build, "TRADUIRE", traduire):
            sortie = support.construire(tmp, pages=PAGES, langues=("fr", "de"))
            self.assertTrue((sortie / "de/index.html").is_file())
            self.assertFalse((sortie / "de/kontakt/index.html").exists())
            self.assertTrue((sortie / "fr/contact/index.html").is_file())

    def test_traduire_recoit_le_html_francais_complet(self):
        """TRADUIRE reçoit la page française assemblée (liens encore en {{ROOT}}) pour chaque langue hors fr."""
        appels = []

        def traduire(html, page, langue):
            appels.append((page, langue, "{{ROOT}}" in html))
            return html, []
        with tempfile.TemporaryDirectory() as tmp, mock.patch.object(build, "TRADUIRE", traduire):
            support.construire(tmp, pages=PAGES, langues=("fr", "de"))
        self.assertEqual(sorted(appels), [("", "de", True), ("contact/", "de", True)])

    def test_traduire_jamais_appele_en_francais_seul(self):
        with tempfile.TemporaryDirectory() as tmp, mock.patch.object(build, "TRADUIRE", side_effect=AssertionError("appelé")):
            support.construire(tmp, pages=PAGES)


class TestLiensDepuisDe(unittest.TestCase):
    """Site complet construit en français et en allemand (une fois par processus de test)."""

    @classmethod
    def setUpClass(cls):
        cls.sortie = support.site_complet(langues=("fr", "de"), apercu=True)

    def test_toutes_les_pages_de(self):
        attendues = {build.chemin_page(p, "de").relative_to(build.DOCS).as_posix() for p in build.PAGES}
        ecrites = {f.relative_to(self.sortie).as_posix() for f in (self.sortie / "de").rglob("index.html")}
        self.assertEqual(ecrites, attendues)

    def test_liens_relatifs_resolus_depuis_de(self):
        fichier = support.chemin(self.sortie, "contact/", "de")
        refs = references(fichier.read_text(encoding="utf-8"))
        self.assertTrue(refs)
        for ref in refs:
            self.assertTrue(cible(fichier.parent, ref).is_file(), f"lien cassé depuis de/kontakt/ : {ref}")

    def test_liens_relatifs_resolus_depuis_toutes_les_pages_de(self):
        for page in build.PAGES:
            fichier = support.chemin(self.sortie, page, "de")
            for ref in references(fichier.read_text(encoding="utf-8")):
                self.assertTrue(cible(fichier.parent, ref).is_file(), f"{langues.route(page, 'de')} : lien cassé {ref}")


if __name__ == "__main__":
    unittest.main()
