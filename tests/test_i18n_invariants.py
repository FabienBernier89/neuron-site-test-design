"""Contrôles d'invariants de la traduction (outils/i18n/controles.py) : chaque contrôle attrape sa faute sur la page
fautive, aucun ne se déclenche sur la page conforme ni sur la sortie FR actuelle."""
import contextlib
import io
import json
import tempfile
import unittest
from pathlib import Path
from unittest import mock

from tests import support
import build
from outils.i18n import __main__ as commandes
from outils.i18n import chnell, controles, terminologie
from outils.i18n.table import Table, cle

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

    def test_bloc_de_code_exclu(self):
        """Point 9 de la tâche 2.3 : le bloc de code de l'exemple d'API (classe u-code) n'est pas du texte de langue."""
        textes = controles.texte_visible('<p>Avant</p><pre class="u-code"><span>"source_language": "de"</span></pre>', "de")
        self.assertEqual(textes, ["Avant"])

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

    def test_milliers_ponctuation_apres_le_nombre(self):
        # une ponctuation après le dernier groupe ne dispense pas du séparateur : seule une suite de chiffres l'écarte
        for langue, mot in (("de", "Dokumente"), ("it", "documenti")):
            with self.subTest(langue=langue):
                self.assertEqual(len(controles.milliers("Wir haben 20 000.", langue)), 1)
                self.assertEqual(len(controles.milliers("Kosten: CHF 15 000.-", langue)), 1)
                self.assertEqual(len(controles.milliers(f"Mehr als 20 000, davon 30 000 {mot}", langue)), 2)
                self.assertEqual(len(controles.milliers("CHF 20 000,50 netto", langue)), 1)
                self.assertEqual(controles.milliers("CHF 20'000.- und 15'000, davon 3,5 %", langue), [])

    def test_langue_page(self):
        regles = [p["regle"] for p in controles.langue_page(FAUTIVE, "de")]
        self.assertEqual(regles, ["langue", "langue"])
        self.assertEqual(controles.langue_page(CONFORME, "de"), [])

    def test_langue_page_json_ld(self):
        html = CONFORME.replace('"inLanguage":"de-CH"', '"inLanguage":"fr-CH"')
        self.assertEqual(len(controles.langue_page(html, "de")), 1)

    def test_langue_page_terme_du_glossaire(self):
        """Ruling 11 : sur une page de glossaire italienne, un DefinedTerm de-CH (et son DefinedTermSet) garde sa langue
        sans être signalé ; le inLanguage de la page (WebPage) reste contrôlé."""
        ld = {"@context": "https://schema.org", "@graph": [
            {"@type": "WebPage", "name": "Prescrizione", "inLanguage": "it-CH"},
            {"@type": "DefinedTerm", "name": "Verjährung", "inLanguage": "de-CH",
             "inDefinedTermSet": {"@type": "DefinedTermSet", "name": "Glossar", "inLanguage": "de-CH"}},
            {"@type": ["DefinedTerm"], "name": "prescription", "inLanguage": "fr-CH"}]}
        html = ('<!DOCTYPE html><html lang="it"><head><meta property="og:locale" content="it_CH">'
                '<script type="application/ld+json">' + json.dumps(ld) + "</script></head><body></body></html>")
        self.assertEqual(controles.langue_page(html, "it"), [])
        fautive = html.replace('"it-CH"', '"fr-CH"')
        self.assertEqual([p["detail"] for p in controles.langue_page(fautive, "it")],
                         ["inLanguage « fr-CH » dans le JSON-LD : « it » attendu"])

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

    def test_hreflang_ignore_les_pages_de_redirection(self):
        """Une ancienne adresse (meta refresh, sans alternate) n'est pas une page du site : ni auto-référence exigée,
        ni réciprocité."""
        with tempfile.TemporaryDirectory() as tmp:
            tout = (("fr-CH", "fr/x/"), ("de-CH", "de/x/"), ("x-default", "fr/x/"))
            ecrire(tmp, "fr/x", page_alternates(*tout))
            ecrire(tmp, "de/x", page_alternates(*tout))
            ecrire(tmp, "fr/ancien", '<!DOCTYPE html>\n<html lang="fr"><head><meta http-equiv="refresh" content="0; url=../x/">'
                                     "</head><body></body></html>")
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


GLOSSAIRE = {"capital-actions": {"de": {"terme": "Aktienkapital", "source": "CHnell", "statut": "confirme"},
                                 "en": {"terme": "share capital", "source": "CHnell", "statut": "confirme"}},
             "CO": {"de": {"terme": "OR", "source": "Fedlex", "statut": "confirme"}}}


class TestTerminologie(unittest.TestCase):
    """Tâche 4.4 : un terme du glossaire de projet présent dans le texte FR doit y être traduit par son équivalent retenu."""

    def test_terme_du_glossaire_absent_signale(self):
        p = controles.terminologie("Le capital-actions est libéré.", "Das Grundkapital ist einbezahlt.", "de", GLOSSAIRE)
        self.assertEqual(len(p), 1)
        self.assertEqual(p[0]["regle"], "terminologie")
        self.assertIn("« capital-actions » sans « Aktienkapital »", p[0]["detail"])
        self.assertIn("Grundkapital", p[0]["extrait"])

    def test_terme_present_accepte(self):
        self.assertEqual(controles.terminologie("Le capital-actions est libéré.",
                                                "Das Aktienkapital ist einbezahlt.", "de", GLOSSAIRE), [])
        # flexion et casse : la V1 compare le début de chaque mot de l'équivalent
        self.assertEqual(controles.terminologie("Le Capital-actions est libéré.",
                                                "Des Aktienkapitals Libierung.", "de", GLOSSAIRE), [])

    def test_terme_absent_du_texte_fr_sans_objet(self):
        self.assertEqual(controles.terminologie("Une société anonyme.", "Eine Aktiengesellschaft.", "de", GLOSSAIRE), [])

    def test_equivalent_a_plusieurs_mots(self):
        g = {"droit des sociétés": {"de": {"terme": "Gesellschaftsrecht"}}, "capital social": {"en": {"terme": "share capital"}}}
        self.assertEqual(len(controles.terminologie("Le droit des sociétés.", "Das Handelsrecht.", "de", g)), 1)
        self.assertEqual(controles.terminologie("Le capital social.", "The share capital.", "en", g), [])
        self.assertEqual(len(controles.terminologie("Le capital social.", "The capital.", "en", g)), 1)

    def test_sigle_en_mot_entier_a_la_casse_exacte(self):
        self.assertEqual(len(controles.terminologie("Selon le CO.", "Gemäss Gesetz.", "de", GLOSSAIRE)), 1)
        self.assertEqual(controles.terminologie("Selon le CO.", "Gemäss OR.", "de", GLOSSAIRE), [])
        self.assertEqual(controles.terminologie("Le coco et la COTE.", "Gesetz.", "de", GLOSSAIRE), [])

    def test_seule_la_langue_du_texte_compte(self):
        self.assertEqual(controles.terminologie("Le capital-actions.", "Das Grundkapital.", "it", GLOSSAIRE), [])
        self.assertEqual(len(controles.terminologie("Le capital-actions.", "The capital.", "en", GLOSSAIRE)), 1)

    def test_marqueurs_et_entites_ignores(self):
        self.assertEqual(controles.terminologie("Le {1}capital-actions{/1} &amp; le reste.",
                                                "Das {1}Aktienkapital{/1} &amp; der Rest.", "de", GLOSSAIRE), [])

    def test_glossaire_vide(self):
        self.assertEqual(controles.terminologie("Le capital-actions.", "Das Kapital.", "de", {}), [])


class TestControlerTraductions(unittest.TestCase):
    def entrees(self, **versions):
        """Table de test : un texte par clé de versions, {fr, trad, statut}."""
        return {f"cle{i}": {"fr": fr, "trad": trad, "statut": statut, "source": "test", "par_page": {}}
                for i, (fr, trad, statut) in enumerate(versions.values())}

    def test_v1_et_invariant_hors_controle(self):
        entrees = self.entrees(a=("Le capital-actions", "Das Grundkapital", "v1"), b=("Corrext", "Corrext", "invariant"),
                               c=("Le capital-actions", "Das Grundkapital", "adapte"))
        controlees, problemes = controles.controler_traductions("de", entrees, GLOSSAIRE)
        self.assertEqual(controlees, 1)
        self.assertEqual([p["regle"] for p in problemes], ["terminologie"])
        self.assertEqual(problemes[0]["gravite"], "avertissement")

    def test_gravites(self):
        entrees = self.entrees(a=("Un texte", f"Ein Text {chr(0x2014)} ohne Sinn", "mt"), b=("Une loi", "Eine Straße", "relu"),
                               c=("Neur.on aide", "Neuron hilft", "adapte"), d=("Un pays", "Ein Land von Lexa", "mt"))
        controlees, problemes = controles.controler_traductions("de", entrees, {})
        self.assertEqual(controlees, 4)
        self.assertEqual(sorted(p["regle"] for p in problemes), ["eszett", "interdits", "marques", "tirets"])
        self.assertTrue(all(p["gravite"] == "bloquant" for p in problemes))
        self.assertTrue(all("cle" in p["lieu"] for p in problemes))

    def test_eszett_en_allemand_seulement(self):
        entrees = {"k": {"fr": "Une rue", "trad": "Eine Straße", "statut": "mt", "source": "test", "par_page": {}}}
        self.assertEqual(controles.controler_traductions("en", entrees, {}), (1, []))

    def test_traductions_par_page_controlees(self):
        entrees = {"k": {"fr": "Le capital-actions", "trad": "Das Aktienkapital", "statut": "v1", "source": "V1",
                         "par_page": {"a/": {"trad": "Das Grundkapital", "statut": "adapte", "source": "test"},
                                      "b/": {"trad": "Das Grundkapital", "statut": "v1", "source": "V1"}}}}
        controlees, problemes = controles.controler_traductions("de", entrees, GLOSSAIRE)
        self.assertEqual(controlees, 1)
        self.assertIn("page a/", problemes[0]["lieu"])

    def test_entree_par_page_seulement_sans_defaut(self):
        entrees = {"k": {"fr": "Le capital-actions", "trad": None, "statut": None, "source": None,
                         "par_page": {"": {"trad": "Das Grundkapital", "statut": "mt", "source": "test"}}}}
        controlees, problemes = controles.controler_traductions("de", entrees, GLOSSAIRE)
        self.assertEqual(controlees, 1)
        self.assertIn("page accueil", problemes[0]["lieu"])


class TestCommandeControler(unittest.TestCase):
    def setUp(self):
        tmp = tempfile.TemporaryDirectory()
        self.addCleanup(tmp.cleanup)
        self.dossier = Path(tmp.name) / "terminologie"
        self.langues = Path(tmp.name) / "langues"
        for patch in (mock.patch.object(terminologie, "TERMINOLOGIE", self.dossier),
                      mock.patch.object(build, "DOSSIER_LANGUES", self.langues)):
            patch.start()
            self.addCleanup(patch.stop)
        self.table = Table("de", self.langues)

    def poser(self, fr, trad, statut):
        self.table.poser(fr, trad, statut, "test")

    def lancer(self):
        self.table.enregistrer()
        sortie, erreur = io.StringIO(), io.StringIO()
        with contextlib.redirect_stdout(sortie), contextlib.redirect_stderr(erreur):
            code = commandes.main(["controler", "de"])
        return code, sortie.getvalue()

    def test_sans_glossaire_le_dit_et_controle_le_reste(self):
        self.poser("Un texte", "Ein Text", "adapte")
        self.table.entrees[cle("Autre")] = {  # Table.poser refuse un tiret : l'entrée fautive est écrite directement
            "fr": "Autre", "trad": f"Ein {chr(0x2014)} Text", "statut": "mt", "source": "test", "par_page": {}}
        code, sortie = self.lancer()
        self.assertEqual(code, 1)
        self.assertIn("2 traduction(s) hors statuts v1 et invariant, 1 problème(s) bloquant(s)", sortie)
        self.assertIn("Glossaire absent ou vide pour cette langue", sortie)
        self.assertIn("tirets", sortie)
        self.assertNotIn(chr(0x2014), sortie)

    def test_terminologie_en_avertissement_sans_echec(self):
        chnell.ecrire_glossaire({"capital-actions": GLOSSAIRE["capital-actions"]}, "de", self.dossier)
        self.poser("Le capital-actions est libéré.", "Das Grundkapital ist einbezahlt.", "adapte")
        self.poser("Le capital-actions est libéré.", "Das Aktienkapital ist einbezahlt.", "v1")  # remplace : v1, hors contrôle
        self.poser("Le capital-actions augmente.", "Das Grundkapital steigt.", "relu")
        code, sortie = self.lancer()
        self.assertEqual(code, 0)
        self.assertIn("0 problème(s) bloquant(s), 1 avertissement(s) de terminologie", sortie)
        self.assertIn("« capital-actions » sans « Aktienkapital »", sortie)
        self.assertNotIn("Glossaire absent", sortie)

    def test_table_conforme(self):
        chnell.ecrire_glossaire({"capital-actions": GLOSSAIRE["capital-actions"]}, "de", self.dossier)
        self.poser("Le capital-actions augmente.", "Das Aktienkapital steigt.", "relu")
        code, sortie = self.lancer()
        self.assertEqual(code, 0)
        self.assertIn("1 traduction(s)", sortie)
        self.assertIn("0 problème(s) bloquant(s), 0 avertissement(s)", sortie)


if __name__ == "__main__":
    unittest.main()
