"""Table des adresses par langue (src/data/routes.json) et fonctions de lecture (outils/i18n/langues.py)."""
import json
import re
import unittest

import build
from outils.i18n import langues

AUTRES = ("de", "it", "en")
V1 = build.NEURON / "src/routes.json"
# adresses nouvelles de la V2, absentes de la V1, validées par Fabien (décision V1 du 2026-10-23)
NOUVELLES = {
    "tarifs/": {"de": "de/preise/", "it": "it/prezzi/", "en": "en/pricing/"},
    "corrext/plugin-word/": {"de": "de/corrext/word-plugin/", "it": "it/corrext/plugin-word/",
                             "en": "en/corrext/word-plugin/"},
    "contact/merci/": {"de": "de/kontakt/danke/", "it": "it/contatto/grazie/", "en": "en/contact/thank-you/"},
}


class TestLangues(unittest.TestCase):
    def test_constantes(self):
        self.assertEqual(langues.LANGUES, ("fr", "de", "it", "en"))
        self.assertEqual(langues.HREFLANG, {"fr": "fr-CH", "de": "de-CH", "it": "it-CH", "en": "en"})
        self.assertEqual(langues.OG_LOCALE, {"fr": "fr_CH", "de": "de_CH", "it": "it_CH", "en": "en_GB"})

    def test_toutes_les_pages_ont_une_route(self):
        self.assertEqual(len(build.PAGES), 159)
        for p in build.PAGES:
            for l in AUTRES:
                with self.subTest(page=p, langue=l):
                    self.assertTrue(langues.route(p, l).startswith(l + "/"))

    def test_aucune_entree_orpheline(self):
        """La table ne décrit que des pages qui existent dans le build FR."""
        self.assertEqual({k[3:] for k in langues.TABLE}, set(build.PAGES))

    def test_francais_et_accueil(self):
        self.assertEqual(langues.route("traduction/contrats/", "fr"), "fr/traduction/contrats/")
        self.assertEqual(langues.route("", "fr"), "fr/")
        for l in AUTRES:
            self.assertEqual(langues.route("", l), l + "/")

    def test_exemple_du_plan(self):
        self.assertEqual(langues.route("traduction/contrats/", "de"), "de/uebersetzung/vertraege/")
        self.assertEqual(langues.page_de("de/uebersetzung/vertraege/"), ("traduction/contrats/", "de"))

    def test_page_absente(self):
        with self.assertRaises(KeyError):
            langues.route("page/inexistante/", "de")
        with self.assertRaises(KeyError):
            langues.route("corrext/", "es")
        self.assertIsNone(langues.page_de("de/page/inexistante/"))
        self.assertIsNone(langues.page_de("es/"))

    def test_slugs(self):
        forme = re.compile(r"^(de|it|en)/([a-z0-9-]+/)*$")
        for l in AUTRES:
            vus = {}
            for p in build.PAGES:
                r = langues.route(p, l)
                with self.subTest(page=p, langue=l):
                    self.assertRegex(r, forme)
                    self.assertTrue(r.startswith(l + "/"))
                    self.assertNotIn("ß", r)
                    self.assertNotIn(r, vus, f"adresse en double avec {vus.get(r)}")
                vus[r] = p

    def test_noms_de_produits_non_traduits(self):
        for l in AUTRES:
            self.assertEqual(langues.route("corrext/", l), f"{l}/corrext/")
            self.assertEqual(langues.route("lexmachina/", l), f"{l}/lexmachina/")
            self.assertTrue(langues.route("corrext/chnell/", l).endswith("chnell/"))

    def test_aller_retour(self):
        for p in build.PAGES:
            for l in AUTRES:
                with self.subTest(page=p, langue=l):
                    self.assertEqual(langues.page_de(langues.route(p, l)), (p, l))
        for p in build.PAGES:
            self.assertEqual(langues.page_de("fr/" + p), (p, "fr"))

    def test_nouvelles_adresses_validees(self):
        for p, attendu in NOUVELLES.items():
            for l, adresse in attendu.items():
                self.assertEqual(langues.route(p, l), adresse)
        with open(langues.ROUTES, encoding="utf-8") as f:
            for entree in json.load(f).values():
                self.assertNotIn("a_valider", entree)

    def test_aucun_tiret_long(self):
        texte = langues.ROUTES.read_text(encoding="utf-8")
        self.assertNotIn(chr(0x2014), texte)
        self.assertNotIn(chr(0x2013), texte)

    def test_reprise_v1(self):
        if not V1.is_file():
            self.skipTest("source V1 absente (NEURON_SRC)")
        v1 = json.loads(V1.read_text(encoding="utf-8"))
        self.assertEqual(len(v1), 156)
        for cle, entree in v1.items():
            with self.subTest(cle=cle):
                self.assertEqual(langues.TABLE[cle], entree)
        self.assertEqual(len(langues.TABLE), 156 + len(NOUVELLES))
