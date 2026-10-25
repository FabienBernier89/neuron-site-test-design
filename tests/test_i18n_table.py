"""Table de segments par langue (outils/i18n/table.py) : clé stable, priorité du texte propre à une page, statuts,
refus des tirets et du ß, reconnaissance des invariants, enregistrement. Le dernier test lit la sortie FR complète
pour s'assurer que les libellés de langues et de moteurs ajoutés à proteges.json existent vraiment."""
import hashlib
import html as H
import json
import re
import tempfile
import unittest
from pathlib import Path

from tests import support
from outils.i18n import controles
from outils.i18n import segments as S
from outils.i18n import table
from outils.i18n.table import Table

TIRET_CADRATIN, DEMI_CADRATIN = chr(0x2014), chr(0x2013)


class TestTable(unittest.TestCase):
    def setUp(self):
        tmp = tempfile.TemporaryDirectory()
        self.addCleanup(tmp.cleanup)
        self.dossier = Path(tmp.name)
        self.de = Table("de", self.dossier)

    def test_cle_stable_aux_espaces(self):
        self.assertEqual(table.cle("a  b\n c"), table.cle("a b c"))
        self.assertNotEqual(table.cle("a b c"), table.cle("a b d"))

    def test_cle_est_le_sha1_tronque(self):
        self.assertEqual(table.cle("Demander une démo"),
                         hashlib.sha1("Demander une démo".encode()).hexdigest()[:16])
        self.assertRegex(table.cle("x"), r"^[0-9a-f]{16}$")

    def test_par_page_prioritaire(self):
        self.de.poser("Allemand", "Deutsch", "v1", "V1 de/")
        self.de.poser("Allemand", "Deutsche Version", "relu", "relecteur DE", page="traduction/allemand-francais/")
        self.assertEqual(self.de.chercher("Allemand", "traduction/allemand-francais/")["trad"], "Deutsche Version")
        self.assertEqual(self.de.chercher("Allemand", "traduction/allemand-francais/")["statut"], "relu")
        self.assertEqual(self.de.chercher("Allemand", "contact/")["trad"], "Deutsch")
        self.assertEqual(self.de.chercher("Allemand", "contact/")["statut"], "v1")
        self.assertEqual(self.de.t("Allemand"), "Deutsch")

    def test_page_sans_defaut_refusee(self):
        with self.assertRaises(ValueError):
            self.de.poser("Allemand", "Deutsch", "v1", "V1", page="contact/")

    def test_chercher_absent(self):
        self.assertIsNone(self.de.chercher("Inconnu", "contact/"))

    def test_chercher_ignore_les_espaces(self):
        self.de.poser("Demander   une démo", "Demo anfragen", "v1", "V1 de/kontakt/")
        self.assertEqual(self.de.chercher("Demander une\ndémo", "")["trad"], "Demo anfragen")

    def test_statut_inconnu_refuse(self):
        with self.assertRaises(ValueError):
            self.de.poser("Demander une démo", "Demo anfragen", "brouillon", "x")

    def test_statuts_et_acceptes(self):
        self.assertEqual(table.STATUTS, ("mt", "adapte", "v1", "invariant", "relu"))
        self.assertEqual(table.ACCEPTES["apercu"], {"adapte", "v1", "invariant", "relu"})
        self.assertEqual(table.ACCEPTES["production"], {"v1", "invariant", "relu"})
        for statut in table.STATUTS:
            self.de.poser("Texte " + statut, "Text", statut, "x")

    def test_langue_inconnue_refusee(self):
        for langue in ("fr", "es", ""):
            with self.assertRaises(ValueError):
                Table(langue, self.dossier)

    def test_tirets_refuses(self):
        for tiret in (TIRET_CADRATIN, DEMI_CADRATIN):
            for langue in ("de", "en", "it"):
                with self.assertRaises(ValueError, msg=langue):
                    Table(langue, self.dossier).poser("Demander une démo", f"Demo {tiret} anfragen", "v1", "x")

    def test_tiret_en_entite_refuse(self):
        with self.assertRaises(ValueError):
            self.de.poser("Demander une démo", "Demo &#8212; anfragen", "v1", "x")

    def test_eszett_refuse_en_de(self):
        with self.assertRaises(ValueError):
            self.de.poser("la rue", "die Straße", "v1", "x")
        self.assertIsNone(self.de.chercher("la rue", ""))  # refus : rien n'est enregistré

    def test_eszett_permis_si_le_francais_le_contient(self):
        self.de.poser("la « Straße » citée", "die zitierte « Straße »", "v1", "x")
        self.assertEqual(self.de.t("la « Straße » citée"), "die zitierte « Straße »")

    def test_eszett_ne_concerne_que_l_allemand(self):
        Table("en", self.dossier).poser("la rue", "the Straße", "v1", "x")
        Table("it", self.dossier).poser("la rue", "la Straße", "v1", "x")

    def test_t_traduit_ou_leve_keyerror(self):
        self.de.poser("Demander une démo", "Demo anfragen", "v1", "V1 de/kontakt/")
        self.assertEqual(self.de.t("Demander une démo"), "Demo anfragen")
        with self.assertRaises(KeyError):
            self.de.t("Texte absent")

    def test_chercher_rend_une_copie(self):
        self.de.poser("Demander une démo", "Demo anfragen", "v1", "x")
        self.de.chercher("Demander une démo", "")["trad"] = "modifié"
        self.assertEqual(self.de.t("Demander une démo"), "Demo anfragen")

    def test_enregistrer_format_et_relecture(self):
        self.de.poser("Demander une démo", "Demo anfragen", "v1", "V1 de/kontakt/")
        self.de.poser("Allemand", "Deutsch", "v1", "V1 de/")
        self.de.poser("Allemand", "Deutsche Version", "relu", "relecteur DE", page="b/")
        self.de.poser("Allemand", "Version", "relu", "relecteur DE", page="a/")
        self.de.enregistrer()
        brut = (self.dossier / "de" / "segments.json").read_text(encoding="utf-8")
        données = json.loads(brut)
        self.assertEqual(list(données), sorted(données))
        self.assertEqual(brut, json.dumps(données, indent=1, ensure_ascii=False) + "\n")
        self.assertIn("démo", brut)  # ensure_ascii=False
        entree = données[table.cle("Demander une démo")]
        self.assertEqual(entree, {"fr": "Demander une démo", "trad": "Demo anfragen", "statut": "v1",
                                  "source": "V1 de/kontakt/", "par_page": {}})
        self.assertEqual(list(données[table.cle("Allemand")]["par_page"]), ["a/", "b/"])
        relue = Table("de", self.dossier)
        self.assertEqual(relue.chercher("Allemand", "b/")["trad"], "Deutsche Version")
        self.assertEqual(relue.t("Demander une démo"), "Demo anfragen")

    def test_poser_conserve_les_textes_par_page(self):
        self.de.poser("Allemand", "Deutsch", "v1", "V1")
        self.de.poser("Allemand", "Deutsche Version", "relu", "r", page="a/")
        self.de.poser("Allemand", "Deutsch (corrigé)", "relu", "r")
        self.assertEqual(self.de.chercher("Allemand", "a/")["trad"], "Deutsche Version")
        self.assertEqual(self.de.t("Allemand"), "Deutsch (corrigé)")

    def test_fichiers_de_langue_du_depot(self):
        for langue in ("de", "en", "it"):
            f = table.SRC / "langues" / langue / "segments.json"
            self.assertIsInstance(json.loads(f.read_text(encoding="utf-8")), dict, langue)
            Table(langue)  # lit le dossier par défaut sans erreur


class TestInvariant(unittest.TestCase):
    def test_marques(self):
        for t in ("Corrext", "Neur.on", "LexMachina", "CHnell", "Fast lookup CHnell", "Highly sensitive content",
                  "Infomaniak", "Neur.on AI Solutions SA"):
            self.assertTrue(Table.est_invariant(t), t)

    def test_marques_associees(self):
        self.assertTrue(Table.est_invariant("Corrext · LexMachina"))
        self.assertTrue(Table.est_invariant("Corrext, CHnell"))
        self.assertTrue(Table.est_invariant("{1}Neur.on{/1}"))

    def test_libelles_d_application(self):
        for t in ("Text translation", "Double review & certified translation", "Attorney-Client privilege",
                  "German", "English", "Italian", "French", "DeepL Pro", "Azure OpenAI - GPT"):
            self.assertTrue(Table.est_invariant(t), t)
        self.assertTrue(Table.est_invariant("Double review &amp; certified translation"))

    def test_passage_a_marqueurs_de_libelles(self):
        self.assertTrue(Table.est_invariant("{1}{/1}{2}Text translation{/2}{3}File translation{/3}{4}PDF to Word{/4}"))
        self.assertTrue(Table.est_invariant("{1}{2}German{/2}{3}English{/3}{4}Italian{/4}{/1}"))
        self.assertFalse(Table.est_invariant("{1}{2}German{/2}{3}Créer un projet{/3}{/1}"))

    def test_invariants_exacts(self):
        self.assertTrue(Table.est_invariant("Place de la Gare 15, 1700 Fribourg"))
        self.assertTrue(Table.est_invariant("team@corrext.com"))

    def test_nombres_adresses_et_ponctuation(self):
        for t in ("15'000", "2,5", "100%", "+41 26 000 00 00", "2026", "12.10.2026", "…", "·", "→", "(1)", "",
                  "jean.dupont@example.org", "https://neur-on.ai/fr/", "www.neur-on.ai/fr/", "mailto:team@corrext.com"):
            self.assertTrue(Table.est_invariant(t), t)

    def test_textes_a_traduire(self):
        for t in ("Demander une démo", "Allemand", "Corrext Premium", "corrext", "CORREXT", "German Law",
                  "50 Mo", "Fast Lookup rapide", "Lexa"):
            self.assertFalse(Table.est_invariant(t), t)

    def test_marque_dans_un_domaine(self):
        self.assertFalse(Table.est_invariant("écrire à info@corrext.com"))

    def test_libelles_de_langues_et_moteurs_existent_dans_la_sortie_fr(self):
        """Ruling 15 : chaque libellé de langue ou de moteur ajouté à proteges.json figure vraiment dans la sortie FR
        (attribut data-v ou unité d'écran), jamais inventé."""
        ajoutes = ("German", "English", "Italian", "French", "Spanish", "DeepL Pro", "Azure OpenAI - GPT")
        for nom in ajoutes:
            self.assertIn(nom, controles.proteges()["libelles_application"], nom)
        vus = set()
        for f in sorted(support.site_complet().rglob("*.html")):
            h = f.read_text(encoding="utf-8")
            vus.update(H.unescape(m.group(1)) for m in re.finditer(r'data-v="([^"]*)"', h))
            vus.update(u["texte"] for u in S.extraire_page(h) if u["ui"] and not u["lang_fr"])
        autonomes = {v for v in vus if "{" not in v}
        for nom in ajoutes:
            self.assertTrue(nom in autonomes or any(nom in v for v in vus), f"« {nom} » absent de la sortie FR")


if __name__ == "__main__":
    unittest.main()
