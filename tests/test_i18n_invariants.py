"""Contrôles d'invariants de la traduction (outils/i18n/controles.py) : chaque contrôle attrape sa faute sur la page
fautive, aucun ne se déclenche sur la page conforme ni sur la sortie FR actuelle."""
import tempfile
import unittest
from pathlib import Path

from tests import support
from outils.i18n import controles

FIXTURES = Path(__file__).resolve().parent / "fixtures" / "i18n"
CONFORME = (FIXTURES / "page-de-conforme.html").read_text(encoding="utf-8")
FAUTIVE = (FIXTURES / "page-de-fautive.html").read_text(encoding="utf-8")
PROD = "https://neur-on.ai/"


def ecrire(racine, chemin, html):
    f = Path(racine) / chemin / "index.html"
    f.parent.mkdir(parents=True, exist_ok=True)
    f.write_text(html, encoding="utf-8")


def page_alternates(*alternates):
    """Page minimale dont la tête déclare les hreflang donnés : couples (hreflang, chemin de la page)."""
    liens = "".join(f'<link rel="alternate" hreflang="{hl}" href="{PROD}{chemin}">' for hl, chemin in alternates)
    return f"<!doctype html><html><head>{liens}</head><body></body></html>"


class TestProteges(unittest.TestCase):
    def test_quatre_cles(self):
        self.assertEqual(set(controles.proteges()), {"marques", "libelles_application", "invariants_exacts", "interdits"})

    def test_valeurs_du_plan(self):
        p = controles.proteges()
        self.assertEqual(p["invariants_exacts"], ["Place de la Gare 15, 1700 Fribourg", "team@corrext.com"])
        self.assertEqual(p["interdits"], ["Neur.on LLM", "Exoscale", "Legal 230", "Legal230", "Lexa", "Silex"])
        self.assertIn("Neur.on AI Solutions SA", p["marques"])
        self.assertIn("Double review & certified translation", p["libelles_application"])


class TestTexteVisible(unittest.TestCase):
    def test_exclusions(self):
        textes = " | ".join(controles.texte_visible(CONFORME, "de"))
        self.assertIn("Präzision", textes)
        self.assertIn("Bildschirm von Corrext", textes)       # alt lisible
        self.assertIn("Beispielseite im JSON-LD", textes)     # valeurs du JSON-LD lues
        self.assertNotIn("inLanguage", textes)                # ... mais pas ses clés
        self.assertNotIn("Le moteur traduit", textes)         # lang="fr"
        self.assertNotIn("Ce nom reste", textes)              # translate="no"
        self.assertNotIn("dividende", textes)                 # data-html
        self.assertNotIn("script ne compte pas", textes)      # script hors JSON-LD

    def test_entites_desechappees(self):
        textes = controles.texte_visible("<p>a &amp; b &#8212; c</p>", "de")
        self.assertEqual(textes, ["a & b " + chr(0x2014) + " c"])

    def test_page_en_francais_lue_en_langue_fr(self):
        # le lang de <html> ne masque jamais la page : c'est le contrôle langue_page qui le juge
        self.assertTrue(any("resté en français" in t for t in controles.texte_visible(FAUTIVE, "de")))


class TestControles(unittest.TestCase):
    def test_tirets(self):
        self.assertEqual(len(controles.tirets("a " + chr(0x2014) + " b " + chr(0x2013) + " c")), 2)

    def test_tirets_entite(self):
        self.assertEqual(len(controles.tirets("a &#8212; b &#x2013; c")), 2)

    def test_tirets_extrait_sans_le_caractere(self):
        p = controles.tirets("a " + chr(0x2014) + " b")[0]
        self.assertNotIn(chr(0x2014), p["extrait"])
        self.assertEqual(set(p), {"regle", "detail", "extrait"})

    def test_interdits(self):
        self.assertTrue(controles.interdits("Le moteur Neur.on LLM"))
        self.assertFalse(controles.interdits("Ein Lexikon"))

    def test_interdits_mots_entiers(self):
        self.assertTrue(controles.interdits("Wir nutzen Lexa."))
        self.assertTrue(controles.interdits("Partenaire : Legal 230"))
        self.assertFalse(controles.interdits("Lexical, Silexit et Exoscaleur"))

    def test_marques_jamais_traduites(self):
        self.assertTrue(controles.marques("Corrext et LexMachina", "Korrext und LexMachina"))
        self.assertFalse(controles.marques("Corrext et LexMachina", "Corrext und LexMachina"))

    def test_marques_nombre_et_casse(self):
        self.assertTrue(controles.marques("Corrext, Corrext", "Corrext"))
        self.assertTrue(controles.marques("Corrext", "corrext"))
        self.assertTrue(controles.marques("Neur.on AI Solutions SA", "Neur.on AI Solutions AG"))
        self.assertFalse(controles.marques("Fast lookup CHnell et CHnell", "Fast lookup CHnell und CHnell"))

    def test_libelles_application(self):
        self.assertTrue(controles.marques("Cliquez sur Show more results", "Klicken Sie auf Weitere Ergebnisse", ui=True))
        self.assertFalse(controles.marques("Cliquez sur Show more results", "Klicken Sie auf Show more results", ui=True))
        # hors contexte d'application, les libellés ne sont pas des marques
        self.assertFalse(controles.marques("Cliquez sur Show more results", "Klicken Sie auf Weitere Ergebnisse"))

    def test_eszett(self):
        self.assertTrue(controles.eszett("la rue", "die Straße"))
        self.assertFalse(controles.eszett("« Straße » s'écrit ainsi", "« Straße » schreibt man so"))

    def test_milliers(self):
        self.assertTrue(controles.milliers("20 000 Dokumente", "de"))
        self.assertFalse(controles.milliers("20'000 Dokumente", "de"))
        self.assertFalse(controles.milliers("15,000 documents", "en"))

    def test_milliers_espace_insecable_et_italien(self):
        self.assertTrue(controles.milliers("20" + chr(0xA0) + "000 documenti", "it"))
        self.assertTrue(controles.milliers("20" + chr(0x202F) + "000 documenti", "de"))
        self.assertFalse(controles.milliers("20 000 documents", "fr"))
        self.assertFalse(controles.milliers("20 000 documents", "en"))
        self.assertFalse(controles.milliers("Tel. 026 300 00 00 und 2024 Dokumente", "de"))

    def test_langue_page(self):
        regles = [p["regle"] for p in controles.langue_page(FAUTIVE, "de")]
        self.assertEqual(regles, ["langue", "langue"])
        self.assertEqual(controles.langue_page(CONFORME, "de"), [])

    def test_langue_page_json_ld(self):
        html = CONFORME.replace('"inLanguage":"de-CH"', '"inLanguage":"fr-CH"')
        self.assertEqual(len(controles.langue_page(html, "de")), 1)

    def test_page_fautive(self):
        regles = {p["regle"] for p in controles.controler_page(FAUTIVE, "de")}
        self.assertEqual(regles, {"tirets", "interdits", "langue", "restes_fr", "milliers"})

    def test_page_conforme(self):
        self.assertEqual(controles.controler_page(CONFORME, "de"), [])

    def test_citation_francaise_exclue(self):   # <blockquote lang="fr"> de 20 mots dans CONFORME
        self.assertEqual(controles.restes_fr(CONFORME, "de"), [])

    def test_restes_fr_page_fautive(self):
        self.assertEqual(len(controles.restes_fr(FAUTIVE, "de")), 1)

    def test_restes_fr_en_francais_sans_objet(self):
        self.assertEqual(controles.restes_fr(FAUTIVE, "fr"), [])

    def test_hreflang_reciproque(self):         # sortie temporaire : fr/x/ annonce de/x/, de/x/ n'annonce pas fr/x/
        with tempfile.TemporaryDirectory() as tmp:
            ecrire(tmp, "fr/x", page_alternates(("fr-CH", "fr/x/"), ("de-CH", "de/x/"), ("x-default", "fr/x/")))
            ecrire(tmp, "de/x", page_alternates(("de-CH", "de/x/"), ("x-default", "fr/x/")))
            self.assertEqual([p["regle"] for p in controles.hreflang(Path(tmp))], ["hreflang"])

    def test_hreflang_conforme(self):
        with tempfile.TemporaryDirectory() as tmp:
            tout = (("fr-CH", "fr/x/"), ("de-CH", "de/x/"), ("x-default", "fr/x/"))
            ecrire(tmp, "fr/x", page_alternates(*tout))
            ecrire(tmp, "de/x", page_alternates(*tout))
            self.assertEqual(controles.hreflang(Path(tmp)), [])

    def test_hreflang_fautes(self):
        with tempfile.TemporaryDirectory() as tmp:
            # pas d'auto-référence ; x-default vers une autre langue que le français ; cible absente
            ecrire(tmp, "fr/x", page_alternates(("de-CH", "de/x/"), ("it-CH", "it/x/"), ("x-default", "de/x/")))
            ecrire(tmp, "de/x", page_alternates(("de-CH", "de/x/"), ("fr-CH", "fr/x/"), ("x-default", "fr/x/")))
            details = " ".join(p["detail"] for p in controles.hreflang(Path(tmp)))
            self.assertIn("auto-référence", details)
            self.assertIn("x-default", details)
            self.assertIn("absente", details)

    def test_liens_langue(self):                # page DE qui lie ../../fr/contact/
        page = '<a href="../../fr/contact/">Kontakt</a>'
        with tempfile.TemporaryDirectory() as tmp:
            ecrire(tmp, "fr/contact", "")
            ecrire(tmp, "de/kontakt", page)
            sortie = Path(tmp)
            self.assertTrue(controles.liens_langue(page, "de/kontakt/", "de", sortie, tolere_fr=False))
            self.assertFalse(controles.liens_langue(page, "de/kontakt/", "de", sortie, tolere_fr=True))

    def test_liens_langue_sans_cible_ni_autre_langue(self):
        with tempfile.TemporaryDirectory() as tmp:
            ecrire(tmp, "fr/contact", "")
            ecrire(tmp, "de/kontakt", "")
            ecrire(tmp, "it/contatto", "")
            sortie = Path(tmp)
            absent = '<a href="../preise/">Preise</a>'
            self.assertEqual(len(controles.liens_langue(absent, "de/kontakt/", "de", sortie, tolere_fr=True)), 1)
            autre = '<a href="../../it/contatto/">Contatto</a>'
            self.assertEqual(len(controles.liens_langue(autre, "de/kontakt/", "de", sortie, tolere_fr=True)), 1)
            fr_absent = '<a href="../../fr/tarifs/">Tarifs</a>'
            self.assertEqual(len(controles.liens_langue(fr_absent, "de/kontakt/", "de", sortie, tolere_fr=True)), 1)

    def test_liens_langue_ignore_selecteur_externes_et_ancres(self):
        page = ('<a href="../../fr/contact/" hreflang="fr-CH">FR</a><a href="https://example.com/fr/">x</a>'
                '<a href="mailto:team@corrext.com">m</a><a href="#haut">h</a><a href="../../assets/doc.pdf">d</a>')
        with tempfile.TemporaryDirectory() as tmp:
            self.assertEqual(controles.liens_langue(page, "de/kontakt/", "de", Path(tmp), tolere_fr=False), [])

    def test_sortie_fr_sans_tiret_ni_terme_interdit(self):
        for f in (support.site_complet() / "fr").rglob("index.html"):
            t = f.read_text(encoding="utf-8")
            self.assertEqual(controles.tirets(t) + controles.interdits(t), [], f)


if __name__ == "__main__":
    unittest.main()
