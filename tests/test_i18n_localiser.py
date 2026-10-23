"""Localisation des liens, de la tête et des données structurées d'une page traduite (tâche 1.3) : liens vers la
version de la langue quand elle est construite, canonique et Open Graph, hreflang réciproques, og:locale et inLanguage.

Les unités testent localiser, alternates et poser_alternates sur de petites pages ; la construction réelle (français
et allemand, TRADUIRE identité) vérifie la réciprocité avec outils.i18n.controles.hreflang."""
import re
import tempfile
import unittest
from pathlib import Path
from unittest import mock

import build
from outils.i18n import controles, langues, localiser
from tests import support

PAGES = ("", "contact/")
U = "https://neur-on.ai/"


def tete(extra="", lang="fr"):
    """Tête d'une page française assemblée (avant finalisation) : canonique, alternates, Open Graph, JSON-LD."""
    return (f'<!DOCTYPE html>\n<html lang="{lang}" data-theme="systeme">\n<head>\n'
            f'<link rel="canonical" href="{U}fr/contact/">\n'
            f'<link rel="alternate" hreflang="fr-CH" href="{U}fr/contact/">\n'
            f'<link rel="alternate" hreflang="x-default" href="{U}fr/contact/">\n'
            f'<meta property="og:url" content="{U}fr/contact/">\n'
            '<meta property="og:image" content="https://neur-on.ai/assets/img/og-neuron.jpg">\n'
            '<meta property="og:locale" content="fr_CH">\n'
            '<script type="application/ld+json">{"@type": "ContactPage", "url": "https://neur-on.ai/fr/contact/", '
            '"inLanguage": "fr-CH"}</script>\n</head>\n<body>\n' + extra + "</body>\n</html>\n")


DE = {"fr": {"", "contact/", "tarifs/"}, "de": {"", "contact/"}}


class TestLiens(unittest.TestCase):
    def test_lien_vers_page_traduite(self):
        h, absentes = localiser.localiser('<a href="{{ROOT}}fr/contact/">C</a><a href="{{ROOT}}contact/#x">D</a>',
                                          "", "de", DE)
        self.assertEqual(h, '<a href="{{ROOT}}de/kontakt/">C</a><a href="{{ROOT}}de/kontakt/#x">D</a>')
        self.assertEqual(absentes, set())

    def test_logo_vers_accueil_de_la_langue(self):
        h, _ = localiser.localiser('<a href="{{ROOT}}">logo</a>', "contact/", "de", DE)
        self.assertEqual(h, '<a href="{{ROOT}}de/">logo</a>')

    def test_lien_vers_page_absente(self):
        """« tarifs/ » n'est pas construite en allemand : le lien reste français et la page est signalée."""
        h, absentes = localiser.localiser('<a href="{{ROOT}}tarifs/">T</a><a href="{{ROOT}}fr/contact/">C</a>',
                                          "", "de", DE)
        self.assertEqual(h, '<a href="{{ROOT}}tarifs/">T</a><a href="{{ROOT}}de/kontakt/">C</a>')
        self.assertEqual(absentes, {"tarifs/"})

    def test_ressources_et_liens_hors_page_intacts(self):
        src = ('<link rel="stylesheet" href="{{ROOT}}assets/site.css?v=1"><img src="{{ROOT}}assets/img/x.png">'
               '<a href="mailto:team@corrext.com">m</a><a href="#haut">h</a><a href="{{ROOT}}de/kontakt/">déjà</a>')
        h, absentes = localiser.localiser(src, "", "de", DE)
        self.assertEqual((h, absentes), (src, set()))

    def test_attribut_data_retour(self):
        """La page de remerciement lit son lien de retour dans data-retour : il est localisé comme un href."""
        h, _ = localiser.localiser('<a href="{{ROOT}}" data-retour="{{ROOT}}fr/contact/">R</a>', "contact/", "de", DE)
        self.assertEqual(h, '<a href="{{ROOT}}de/" data-retour="{{ROOT}}de/kontakt/">R</a>')

    def test_adresses_des_donnees_de_page(self):
        """L'index de recherche de l'aide cite ses pages en {{ROOT}}fr/<p> dans un script : localisé, ancre gardée."""
        src = '<script>[{"u": "{{ROOT}}fr/contact/#q-demo"}, {"u": "{{ROOT}}fr/tarifs/#t"}]</script>'
        h, absentes = localiser.localiser(src, "", "de", DE)
        self.assertEqual(h, '<script>[{"u": "{{ROOT}}de/kontakt/#q-demo"}, {"u": "{{ROOT}}fr/tarifs/#t"}]</script>')
        self.assertEqual(absentes, {"tarifs/"})

    def test_adresses_absolues_localisees_et_absentes_signalees(self):
        h, absentes = localiser.localiser(f'<a href="{U}fr/contact/">c</a>{{"item": "{U}fr/tarifs/"}}', "", "de", DE)
        self.assertEqual(h, f'<a href="{U}de/kontakt/">c</a>{{"item": "{U}fr/tarifs/"}}')
        self.assertEqual(absentes, {"tarifs/"})

    def test_canonique_et_og_url_localises(self):
        h, _ = localiser.localiser(tete(), "contact/", "de", DE)
        self.assertIn(f'<link rel="canonical" href="{U}de/kontakt/">', h)
        self.assertIn(f'<meta property="og:url" content="{U}de/kontakt/">', h)
        self.assertIn(f'"url": "{U}de/kontakt/"', h)

    def test_francais_sans_effet(self):
        h = tete('<a href="{{ROOT}}contact/">c</a>')
        self.assertEqual(localiser.localiser(h, "contact/", "fr", {"fr": {"", "contact/"}}), (h, set()))


class TestTete(unittest.TestCase):
    def test_alternates_intacts(self):
        """localiser ne touche à aucune balise alternate (poser_alternates les décide), même française."""
        h, _ = localiser.localiser(tete(), "contact/", "de", DE)
        self.assertEqual(re.findall(r'<link rel="alternate"[^>]*>', h), re.findall(r'<link rel="alternate"[^>]*>', tete()))

    def test_og_locale_et_inlanguage(self):
        for langue, locale, code in (("de", "de_CH", "de-CH"), ("it", "it_CH", "it-CH"), ("en", "en_GB", "en")):
            h, _ = localiser.localiser(tete(), "contact/", langue, {"fr": {"contact/"}, langue: {"contact/"}})
            self.assertIn(f'<meta property="og:locale" content="{locale}">', h, langue)
            self.assertIn(f'"inLanguage": "{code}"', h, langue)
            self.assertNotIn("fr-CH", h.split("</head>")[0].replace('hreflang="fr-CH"', ""), langue)
            self.assertIn(f'<html lang="{langue}" ', h, langue)  # code court (décision 10), jamais de-CH

    def test_inlanguage_des_termes_du_glossaire_intact(self):
        """Seul l'inLanguage de la page change : un DefinedTerm allemand reste de-CH, un jeu de langues reste une liste."""
        src = ('<script type="application/ld+json">{"@type": "DefinedTerm", "inLanguage": "de-CH"}</script>'
               '<script type="application/ld+json">{"@type": "DefinedTermSet", "inLanguage": ["de-CH", "fr-CH", "it-CH", "en"]}'
               '</script><script type="application/ld+json">{"@type": "WebPage", "inLanguage": "fr-CH"}</script>')
        h, _ = localiser.localiser(src, "", "it", {"fr": {""}, "it": {""}})
        self.assertIn('{"@type": "DefinedTerm", "inLanguage": "de-CH"}', h)
        self.assertIn('"inLanguage": ["de-CH", "fr-CH", "it-CH", "en"]', h)
        self.assertIn('{"@type": "WebPage", "inLanguage": "it-CH"}', h)

    def test_image_de_partage_par_langue_si_elle_existe(self):
        with tempfile.TemporaryDirectory() as tmp, mock.patch.object(localiser, "IMAGES", Path(tmp)):
            (Path(tmp) / "og-neuron-de.png").write_bytes(b"png")
            h, _ = localiser.localiser(tete(), "contact/", "de", DE)
            self.assertIn('content="https://neur-on.ai/assets/img/og-neuron-de.png"', h)
            h, _ = localiser.localiser(tete(), "contact/", "it", {"fr": {"contact/"}, "it": {"contact/"}})
            self.assertIn('content="https://neur-on.ai/assets/img/og-neuron.jpg"', h)  # pas de fichier italien

    def test_visuels_d_articles_gardes(self):
        src = ('<meta property="og:image" content="https://neur-on.ai/assets/img/blog/couverture.jpg">'
               '<meta property="og:image" content="https://neur-on.ai/assets/img/og-neuron.jpg.bak">')
        with tempfile.TemporaryDirectory() as tmp, mock.patch.object(localiser, "IMAGES", Path(tmp)):
            (Path(tmp) / "og-neuron-de.png").write_bytes(b"png")
            self.assertEqual(localiser.localiser(src, "", "de", DE)[0], src)

    def test_champ_langue_du_formulaire(self):
        src = '<form><input type="hidden" name="langue" value="fr"><input name="prenom" value="fr"></form>'
        h, _ = localiser.localiser(src, "contact/", "it", {"fr": {"contact/"}, "it": {"contact/"}})
        self.assertEqual(h, '<form><input type="hidden" name="langue" value="it"><input name="prenom" value="fr"></form>')


class TestAlternates(unittest.TestCase):
    def test_une_seule_langue_inchangee(self):
        u = U + "fr/corrext/"
        self.assertEqual(localiser.alternates("corrext/", {"fr": {"corrext/"}}), [("fr-CH", u), ("x-default", u)])

    def test_ordre_des_langues_et_x_default_francais(self):
        construites = {"fr": {"contact/"}, "en": {"contact/"}, "de": {"contact/"}}
        self.assertEqual(localiser.alternates("contact/", construites),
                         [("fr-CH", U + "fr/contact/"), ("de-CH", U + "de/kontakt/"), ("en", U + "en/contact/"),
                          ("x-default", U + "fr/contact/")])

    def test_page_francaise_absente_de_la_table(self):
        """Une page française sans adresse dans routes.json garde son alternate fr-CH et son x-default."""
        u = U + "fr/corrext/page-factice/"
        self.assertEqual(localiser.alternates("corrext/page-factice/", {"fr": {"corrext/page-factice/"}}),
                         [("fr-CH", u), ("x-default", u)])

    def test_page_nouvelle(self):
        """« tarifs/ » construite en allemand : la page française l'annonce aussi, et la version allemande aussi."""
        construites = {"fr": {"", "tarifs/"}, "de": {"tarifs/"}}
        attendu = [("fr-CH", U + "fr/tarifs/"), ("de-CH", U + "de/preise/"), ("x-default", U + "fr/tarifs/")]
        self.assertEqual(localiser.alternates("tarifs/", construites), attendu)
        self.assertEqual(localiser.alternates("", construites), [("fr-CH", U + "fr/"), ("x-default", U + "fr/")])
        fr = localiser.poser_alternates(tete(), "tarifs/", construites)
        self.assertIn(f'<link rel="alternate" hreflang="de-CH" href="{U}de/preise/">', fr)

    def test_poser_alternates_remplace_a_la_place_des_anciennes(self):
        ancien = tete().replace(f'<link rel="alternate" hreflang="x-default" href="{U}fr/contact/">\n',
                                f'<link rel="alternate" hreflang="it-CH" href="{U}it/contatto/">\n'
                                f'<link rel="alternate" hreflang="x-default" href="{U}fr/contact/">\n')
        h = localiser.poser_alternates(ancien, "contact/", DE)
        self.assertEqual(re.findall(r'<link rel="alternate" hreflang="([^"]+)" href="([^"]+)">', h),
                         [("fr-CH", U + "fr/contact/"), ("de-CH", U + "de/kontakt/"), ("x-default", U + "fr/contact/")])
        # même emplacement que la première ancienne balise : rien d'autre ne bouge
        self.assertEqual(h.replace("".join(f'<link rel="alternate" hreflang="{a}" href="{b}">\n' for a, b in
                                           localiser.alternates("contact/", DE)), "@A@"),
                         ancien.replace(f'<link rel="alternate" hreflang="fr-CH" href="{U}fr/contact/">\n'
                                        f'<link rel="alternate" hreflang="it-CH" href="{U}it/contatto/">\n'
                                        f'<link rel="alternate" hreflang="x-default" href="{U}fr/contact/">\n', "@A@"))

    def test_poser_alternates_sans_balise_ne_change_rien(self):
        """La page 404 n'a pas d'alternate (ni de route) : rien n'est ajouté, rien ne plante."""
        h = "<!DOCTYPE html>\n<html>\n<head>\n<title>x</title>\n</head>\n<body></body>\n</html>\n"
        self.assertEqual(localiser.poser_alternates(h, "404.html", {"fr": set()}), h)

    def test_poser_alternates_ignore_le_corps(self):
        h = tete('<link rel="alternate" hreflang="de-CH" href="x">')
        self.assertTrue(localiser.poser_alternates(h, "contact/", {"fr": {"contact/"}}).endswith(
            '<link rel="alternate" hreflang="de-CH" href="x"></body>\n</html>\n'))


class TestFinaliser(unittest.TestCase):
    """finaliser : poser_alternates (toutes langues), localiser (hors fr), images, dimensions, relier."""

    def test_alternates_decides_par_construites_et_non_par_le_dossier_de_sortie(self):
        with tempfile.TemporaryDirectory() as tmp, mock.patch.object(build, "DOCS", Path(tmp)):
            (Path(tmp) / "de/kontakt").mkdir(parents=True)
            (Path(tmp) / "de/kontakt/index.html").write_text("<!DOCTYPE html>", encoding="utf-8")
            seul = build.finaliser(tete(), "contact/", "fr", {"fr": {"contact/"}})
            self.assertEqual(re.findall(r'hreflang="([^"]+)"', seul), ["fr-CH", "x-default"])
            avec = build.finaliser(tete(), "contact/", "fr", {"fr": {"contact/"}, "de": {"contact/"}})
            self.assertEqual(re.findall(r'hreflang="([^"]+)"', avec), ["fr-CH", "de-CH", "x-default"])

    def test_page_de_repli_recoit_les_memes_alternates(self):
        """Une page sans référencement figé (seo_repli) reçoit, une fois finalisée, les mêmes alternates qu'une page figée."""
        repli = build.seo_repli("tarifs/", {"title": "Tarifs", "description": "d"})
        html = tete().replace(f'<link rel="canonical" href="{U}fr/contact/">\n', "") + ""
        html = html.replace("<head>\n", "<head>\n" + repli, 1)
        construites = {"fr": {"tarifs/"}, "de": {"tarifs/"}}
        h = build.finaliser(html, "tarifs/", "de", construites)
        self.assertEqual(re.findall(r'<link rel="alternate" hreflang="([^"]+)" href="([^"]+)">', h),
                         [("fr-CH", U + "fr/tarifs/"), ("de-CH", U + "de/preise/"), ("x-default", U + "fr/tarifs/")])
        self.assertIn(f'<link rel="canonical" href="{U}de/preise/">', h)
        self.assertIn(f'<meta property="og:url" content="{U}de/preise/">', h)
        self.assertIn('<meta property="og:locale" content="de_CH">', h)
        self.assertIn('<html lang="de" ', h)


class TestBuildFrDe(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls._tmp = tempfile.TemporaryDirectory()
        cls.sortie = support.construire(cls._tmp.name, pages=PAGES, langues=("fr", "de"))

    @classmethod
    def tearDownClass(cls):
        cls._tmp.cleanup()

    def lire(self, page, langue):
        return support.chemin(self.sortie, page, langue).read_text(encoding="utf-8")

    def test_alternates_intacts_et_reciproques(self):
        for page in PAGES:
            attendus = [("fr-CH", U + langues.route(page, "fr")), ("de-CH", U + langues.route(page, "de")),
                        ("x-default", U + langues.route(page, "fr"))]
            for langue in ("fr", "de"):
                h = self.lire(page, langue)
                self.assertEqual(re.findall(r'<link rel="alternate" hreflang="([^"]+)" href="([^"]+)">', h[:h.index("</head>")]),
                                 attendus, (page, langue))
        self.assertEqual(controles.hreflang(self.sortie), [])

    def test_canonique_en_allemand(self):
        h = self.lire("contact/", "de")
        self.assertIn(f'<link rel="canonical" href="{U}de/kontakt/">', h)
        self.assertIn(f'<meta property="og:url" content="{U}de/kontakt/">', h)
        self.assertIn('<meta property="og:locale" content="de_CH">', h)
        self.assertEqual(re.findall(r'"inLanguage": "fr-CH"', h), [])
        self.assertIn('<html lang="de" ', h)

    def test_liens_vers_pages_traduites(self):
        """Depuis l'accueil allemand, le lien vers le contact mène à la version allemande, résolue en relatif."""
        h = self.lire("", "de")
        self.assertIn('href="../de/kontakt/"', h)
        self.assertNotIn('href="../fr/contact/"', h)
        self.assertIn('href="../de/"', h)  # logo

    def test_francais_toujours_francais(self):
        h = self.lire("contact/", "fr")
        self.assertIn('<meta property="og:locale" content="fr_CH">', h)
        self.assertIn(f'<link rel="canonical" href="{U}fr/contact/">', h)
        self.assertIn('href="../../fr/contact/"', h)
        self.assertNotIn("../de/", h)


if __name__ == "__main__":
    unittest.main()
