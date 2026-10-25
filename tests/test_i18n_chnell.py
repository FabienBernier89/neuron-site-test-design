"""Terminologie vérifiée dans CHnell (tâche 4.2) : outils/i18n/chnell.py et commandes chnell.

Tout est synthétique : lexique, journal et termes V1 écrits ici, dossiers temporaires pour les fichiers. Aucun test ne lit
ni n'écrit le dossier réel de la terminologie (Bibliotheque-Claude, Ruling 5), aucune requête réseau, aucune capture de
CHnell (la zone de résultats et sa lecture attendent la session avec Fabien, tâche 4.2 step 1)."""
import contextlib
import io
import json
import tempfile
import unittest
from pathlib import Path
from unittest import mock

import build
from outils.i18n import __main__ as commandes
from outils.i18n import chnell, terminologie

TIRET_CADRATIN, DEMI_CADRATIN = chr(0x2014), chr(0x2013)


def lex(fr, priorite, retenu=True):
    return {"fr": fr, "origine": ["ngramme"], "priorite": priorite, "pages": [""], "occurrences": 3, "retenu": retenu}


def ligne(fr, langue="de", **champs):
    """Entrée de journal valide, champs surchargeables."""
    base = {"date": "2026-10-26", "fr": fr, "langue": langue, "url": chnell.url_chnell(fr, langue), "resultats": 12,
            "sources": ["Fedlex : CO art. 620"], "retenu": "Aktienkapital", "statut": "confirme",
            "justification": "même équivalent dans les concordances", "verifie_par": "agent"}
    return {**base, **champs}


class TestUrl(unittest.TestCase):
    def test_url_exacte(self):
        self.assertEqual(chnell.url_chnell("capital-actions", "de"),
                         "https://corrext.com/chnell/search?searchText=capital-actions&sourceLang=fr&targetLang=de&resource=1")
        self.assertTrue(chnell.url_chnell("capital-actions", "de", fedlex=True).endswith("&resource=1&sources=60"))
        self.assertIn("searchText=droit%20des%20soci%C3%A9t%C3%A9s", chnell.url_chnell("droit des sociétés", "de"))

    def test_langue_inconnue_refusee(self):
        with self.assertRaises(ValueError):
            chnell.url_chnell("capital-actions", "fr")


class TestFileAttente(unittest.TestCase):
    LEXIQUE = [lex("capital-actions", 2), lex("prescription", 3), lex("assemblée générale", 1),
               lex("procuration", 1, retenu=None), lex("mandat", 2, retenu=False), lex("commandite", 4)]

    def test_file_ignore_deja_journalises(self):
        journal = [ligne("capital-actions"), ligne("prescription", langue="en")]
        file = chnell.file_attente("de", self.LEXIQUE, journal, priorite_max=3)
        self.assertEqual([e["fr"] for e in file], ["assemblée générale", "prescription"])
        # autre langue : seul « prescription » est journalisé pour elle
        file_en = chnell.file_attente("en", self.LEXIQUE, journal, priorite_max=3)
        self.assertEqual([e["fr"] for e in file_en], ["assemblée générale", "capital-actions"])

    def test_file_garde_les_retenus_sous_le_seuil_par_priorite(self):
        # ni retenu non décidé (None), ni écarté (False), ni priorité au-dessus du seuil ; priorité puis terme
        file = chnell.file_attente("de", self.LEXIQUE, [], priorite_max=2)
        self.assertEqual([(e["fr"], e["priorite"]) for e in file], [("assemblée générale", 1), ("capital-actions", 2)])

    def test_file_porte_les_deux_adresses(self):
        e = chnell.file_attente("it", [lex("capital-actions", 2)], [], priorite_max=3)[0]
        self.assertEqual(e, {"fr": "capital-actions", "langue": "it", "priorite": 2,
                             "url": chnell.url_chnell("capital-actions", "it"),
                             "url_fedlex": chnell.url_chnell("capital-actions", "it", fedlex=True)})

    def test_priorite_par_defaut_de_la_commande_est_3(self):
        self.assertEqual(chnell.PRIORITE_MAX, 3)


class TestJournal(unittest.TestCase):
    def setUp(self):
        tmp = tempfile.TemporaryDirectory()
        self.addCleanup(tmp.cleanup)
        self.journal = Path(tmp.name) / "terminologie" / "journal.jsonl"

    def test_journal_schema(self):
        with self.assertRaises(ValueError):
            chnell.ajouter(self.journal, ligne("capital-actions", statut="valide"))
        for champ in ("justification", "retenu"):
            with self.assertRaises(ValueError, msg=champ):
                chnell.ajouter(self.journal, ligne("capital-actions", **{champ: f"avant {TIRET_CADRATIN} après"}))
        with self.assertRaises(ValueError):
            chnell.ajouter(self.journal, ligne("capital-actions", sources=[f"Fedlex {DEMI_CADRATIN} CO"]))
        self.assertFalse(self.journal.exists(), "une entrée refusée ne laisse aucune trace")

    def test_une_ligne_json_par_appel(self):
        chnell.ajouter(self.journal, ligne("capital-actions"))
        chnell.ajouter(self.journal, ligne("prescription", retenu="Verjährung", statut="corrige"))
        lignes = self.journal.read_text(encoding="utf-8").splitlines()
        self.assertEqual(len(lignes), 2)
        self.assertEqual(json.loads(lignes[0]), ligne("capital-actions"))
        self.assertEqual([e["fr"] for e in chnell.charger_journal(self.journal.parent)], ["capital-actions", "prescription"])

    def test_champs_exacts(self):
        brouillon = ligne("capital-actions")
        del brouillon["justification"]
        with self.assertRaisesRegex(ValueError, "justification"):
            chnell.ajouter(self.journal, brouillon)
        with self.assertRaisesRegex(ValueError, "extrait"):  # champ en trop : jamais d'extrait de texte
            chnell.ajouter(self.journal, {**ligne("capital-actions"), "extrait": "texte de CHnell"})

    def test_valeurs_refusees(self):
        for champs in ({"date": "26/10/2026"}, {"langue": "fr"}, {"resultats": -1}, {"resultats": "12"},
                       {"resultats": True}, {"sources": "Fedlex"}, {"sources": [3]}, {"fr": ""}, {"retenu": ""},
                       {"verifie_par": ""}, {"url": "https://exemple.org/?q=1"}, {"retenu": None},
                       {"justification": "x" * 400}, {"retenu": "Schloß"}):
            with self.subTest(champs=champs), self.assertRaises(ValueError):
                chnell.ajouter(self.journal, {**ligne("capital-actions"), **champs})

    def test_absent_sans_retenu(self):
        chnell.ajouter(self.journal, ligne("capital-actions", statut="absent", retenu=None, resultats=0, sources=[]))
        with self.assertRaises(ValueError):
            chnell.ajouter(self.journal, ligne("prescription", statut="absent", retenu="Verjährung"))

    def test_eszett_refuse_en_allemand_seulement(self):
        with self.assertRaises(ValueError):
            chnell.ajouter(self.journal, ligne("capital-actions", retenu="Schloß"))
        chnell.ajouter(self.journal, ligne("capital-actions", langue="en", retenu="share capital"))

    def test_journal_absent_ou_ligne_illisible(self):
        self.assertEqual(chnell.charger_journal(self.journal.parent), [])
        self.journal.parent.mkdir(parents=True)
        self.journal.write_text('{"fr": "a"}\nn\'importe quoi\n', encoding="utf-8")
        with self.assertRaisesRegex(ValueError, "ligne 2"):
            chnell.charger_journal(self.journal.parent)


class TestLireResultats(unittest.TestCase):
    def test_lecture_attend_la_capture_de_chnell(self):
        """Ni ZONE ni lire_resultats ne sont inventés : ils viennent de la session avec Fabien (tâche 4.2 step 1)."""
        self.assertIsNone(chnell.ZONE)
        with self.assertRaisesRegex(NotImplementedError, "capture CHnell à faire avec Fabien"):
            chnell.lire_resultats("<html></html>")


V1_DE = [{"fr": "capital-actions", "de": "Aktienkapital", "type": "glossaire", "source": "V1"},
         {"fr": "prescription", "de": "Verjährung", "type": "glossaire", "source": "V1"},
         {"fr": "prescription", "de": "Verjaehrungsfrist", "type": "metier", "source": "V1"},
         {"fr": "devis", "de": "Offerte", "type": "metier", "source": "V1"}]


class Commandes(unittest.TestCase):
    """Commandes chnell, dans un dossier de terminologie et un site V1 temporaires."""

    def setUp(self):
        tmp = tempfile.TemporaryDirectory()
        self.addCleanup(tmp.cleanup)
        self.dossier = Path(tmp.name) / "terminologie"
        self.v1 = Path(tmp.name) / "v1"
        (self.v1 / "src/i18n").mkdir(parents=True)
        (self.v1 / "src/i18n/termes-de.json").write_text(json.dumps(V1_DE), encoding="utf-8")
        for patch in (mock.patch.object(terminologie, "TERMINOLOGIE", self.dossier), mock.patch.object(build, "NEURON", self.v1)):
            patch.start()
            self.addCleanup(patch.stop)

    def lancer(self, *args):
        sortie, erreur = io.StringIO(), io.StringIO()
        with contextlib.redirect_stdout(sortie), contextlib.redirect_stderr(erreur):
            code = commandes.main(list(args))
        return code, sortie.getvalue(), erreur.getvalue()

    def ajouter(self, fr, retenu, statut="confirme", *plus):
        return self.lancer("chnell", "ajouter", "de", fr, "--resultats", "12", "--retenu", retenu, "--statut", statut,
                           "--justification", "même équivalent dans les concordances", "--source", "Fedlex : CO art. 620",
                           "--verifie-par", "agent", "--date", "2026-10-26", *plus)


class TestCommandesChnell(Commandes):
    def test_ajouter_ecrit_une_ligne_dans_le_dossier_de_la_terminologie(self):
        code, sortie, _ = self.ajouter("capital-actions", "Aktienkapital")
        self.assertEqual(code, 0, sortie)
        self.assertEqual(chnell.charger_journal(self.dossier), [ligne("capital-actions")])

    def test_ajouter_refuse_avec_un_message_en_francais(self):
        code, _, erreur = self.ajouter("capital-actions", "Aktienkapital", "valide")
        self.assertEqual(code, 1)
        self.assertIn("statut", erreur)
        self.assertEqual(chnell.charger_journal(self.dossier), [])

    def test_ajouter_absent_sans_retenu(self):
        code, _, erreur = self.lancer("chnell", "ajouter", "de", "mandat", "--resultats", "0", "--statut", "absent",
                                      "--justification", "terme introuvable", "--verifie-par", "agent",
                                      "--date", "2026-10-26")
        self.assertEqual(code, 0, erreur)
        self.assertIsNone(chnell.charger_journal(self.dossier)[0]["retenu"])

    def test_lire_dit_que_la_capture_est_a_faire(self):
        code, sortie, erreur = self.lancer("chnell", "lire", "inexistant.html", "--fr", "capital-actions", "--langue", "de")
        self.assertEqual(code, 1)
        self.assertIn("capture CHnell à faire avec Fabien (tâche 4.2 step 1)", sortie + erreur)

    def test_file_liste_les_termes_restants(self):
        terminologie.ecrire_lexique("de", [lex("capital-actions", 2), lex("prescription", 3), lex("hors seuil", 4)],
                                    self.dossier)
        self.ajouter("capital-actions", "Aktienkapital")
        code, sortie, _ = self.lancer("chnell", "file", "de")
        self.assertEqual(code, 0)
        self.assertIn("prescription", sortie)
        self.assertNotIn("capital-actions", sortie)
        self.assertNotIn("hors seuil", sortie)  # seuil par défaut : priorité 3
        self.assertIn(f"P3 prescription : {chnell.url_chnell('prescription', 'de')}", sortie)
        self.assertIn("&sources=60", sortie)
        _, sortie, _ = self.lancer("chnell", "file", "de", "--priorite-max", "4")
        self.assertIn("hors seuil", sortie)


if __name__ == "__main__":
    unittest.main()
