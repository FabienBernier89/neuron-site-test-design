"""Fusion des adaptations (tâche 6.2) : echanges.fusionner et la commande « fusionner », le brief d'adaptation et les guides.

Tout est synthétique : mini table allemande dans un dossier temporaire, propositions écrites ici. Aucun test ne lit ni
n'écrit le dossier réel de la terminologie (Bibliotheque-Claude, Ruling 5)."""
import contextlib
import io
import json
import re
import tempfile
import unittest
from pathlib import Path
from unittest import mock

import build
from outils.i18n import __main__ as cli
from outils.i18n import echanges
from outils.i18n.table import Table, cle

ICI = Path(__file__).resolve().parent.parent
TIRET_CADRATIN = chr(0x2014)
TIRET_COURT = chr(0x2013)
JOUR = "2026-10-26"
INTERDIT = "Le" + "xa"  # terme interdit de proteges.json, composé : tests/test_regles.py refuse le terme en clair dans le dépôt

DEMO = "Demander une démo"
CAPITAL = "Le {1}capital-actions{/1} de la société"
ADRESSE = "Adresse{1}Fribourg"
NEURON = "Neur.on traduit vos contrats"
RUE = "La rue du Tilleul"
GLOSSAIRE = {"capital-actions": {"de": {"terme": "Aktienkapital", "source": "Fedlex : CO art. 620", "statut": "confirme"}}}


class Base(unittest.TestCase):
    def setUp(self):
        self._tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self._tmp.cleanup)
        self.dossier = Path(self._tmp.name)
        self.table = Table("de", self.dossier)
        self.table.poser(DEMO, "Demo anfragen", "mt", "LexMachina 2026-10-25")
        self.table.poser(CAPITAL, "Das {1}Aktienkapital{/1} der Gesellschaft", "mt", "LexMachina 2026-10-25")
        self.table.poser(ADRESSE, "Adresse{1}Freiburg", "mt", "LexMachina 2026-10-25")
        self.table.poser(NEURON, "Neur.on übersetzt Ihre Verträge", "mt", "LexMachina 2026-10-25")
        self.table.poser(RUE, "Die Lindenstrasse", "mt", "LexMachina 2026-10-25")
        self.table.poser("Contact", "Kontakt", "v1", "V1 de/kontakt/")
        self.table.poser("Notre équipe", "Unser Team", "relu", "relu par Béatrice le 2026-09-01", v1=True)
        self.table.poser("Prix", "Preis", "mt", "LexMachina 2026-10-25")
        self.table.poser("Prix", "Preise", "v1", "V1 de/preise/", page="preise/")

    def propositions(self, *propositions):
        fichier = self.dossier / "propositions.json"
        fichier.write_text(json.dumps(list(propositions), ensure_ascii=False), encoding="utf-8")
        return fichier

    def fusionner(self, *propositions, **options):
        options.setdefault("glossaire", GLOSSAIRE)
        options.setdefault("jour", JOUR)
        return echanges.fusionner(self.propositions(*propositions), self.table, **options)

    def entree(self, texte, page=""):
        return self.table.chercher(texte, page)

    def raisons(self, rapport):
        return {r["cle"]: r["raison"] for r in rapport["refuses"]}


class TestFusion(Base):
    def test_fusion_pose_adapte(self):
        rapport = self.fusionner({"cle": cle(DEMO), "trad": "Demo vereinbaren", "note": "plus naturel pour un cabinet"},
                                 {"cle": cle(CAPITAL), "trad": "Das {1}Aktienkapital{/1} der Gesellschaft", "note": ""})
        self.assertEqual(rapport["poses"], 2)
        self.assertEqual(rapport["refuses"], [])
        e = self.entree(DEMO)
        self.assertEqual((e["trad"], e["statut"]), ("Demo vereinbaren", "adapte"))
        self.assertEqual(e["source"], f"LexMachina 2026-10-25 ; adapté le {JOUR}")
        # la même traduction confirmée passe aussi au statut adapte
        self.assertEqual(self.entree(CAPITAL)["statut"], "adapte")
        # la note de l'agent remonte pour la relecture, jamais dans la table
        self.assertEqual(rapport["notes"], [{"cle": cle(DEMO), "fr": DEMO, "note": "plus naturel pour un cabinet"}])
        self.assertNotIn("plus naturel", json.dumps(self.table.entrees, ensure_ascii=False))

    def test_fusion_ne_touche_que_les_entrees_proposees(self):
        avant = json.dumps(self.table.entrees, sort_keys=True)
        self.fusionner({"cle": cle(DEMO), "trad": "Demo vereinbaren"})
        apres = json.loads(json.dumps(self.table.entrees))
        autres = json.loads(avant)
        autres[cle(DEMO)] = apres[cle(DEMO)]
        self.assertEqual(apres, autres)

    def test_fusion_conserve_les_traductions_de_page(self):
        self.fusionner({"cle": cle("Prix"), "trad": "Preise und Angebote"})
        self.assertEqual(self.entree("Prix")["trad"], "Preise und Angebote")
        self.assertEqual(self.entree("Prix", "preise/")["statut"], "v1")

    def test_fusion_source_deja_adaptee_pas_doublee(self):
        self.fusionner({"cle": cle(DEMO), "trad": "Demo vereinbaren"})
        self.fusionner({"cle": cle(DEMO), "trad": "Demo buchen"})
        self.assertEqual(self.entree(DEMO)["source"], f"LexMachina 2026-10-25 ; adapté le {JOUR}")

    def test_fusion_refuse_cle_inconnue(self):
        rapport = self.fusionner({"cle": "0123456789abcdef", "trad": "Unbekannt"}, {"cle": cle(DEMO), "trad": "Demo vereinbaren"})
        self.assertEqual(rapport["poses"], 1)
        self.assertEqual(self.raisons(rapport), {"0123456789abcdef": "clé inconnue"})
        self.assertIsNone(self.table.entrees.get("0123456789abcdef"))

    def test_fusion_refuse_controle_bloquant(self):
        rapport = self.fusionner(
            {"cle": cle(DEMO), "trad": f"Demo {TIRET_CADRATIN} anfragen"},
            {"cle": cle(CAPITAL), "trad": f"Das {{1}}Aktienkapital{{/1}} {TIRET_COURT} der Gesellschaft"},
            {"cle": cle(RUE), "trad": "Die Lindenstraße"},
            {"cle": cle(NEURON), "trad": "Neuron übersetzt Ihre Verträge"},
            {"cle": cle("Prix"), "trad": "Preis von " + INTERDIT})
        self.assertEqual(rapport["poses"], 0)
        self.assertEqual(self.raisons(rapport), {cle(DEMO): "tirets", cle(CAPITAL): "tirets", cle(RUE): "eszett",
                                                 cle(NEURON): "marques", cle("Prix"): "interdits"})
        # rien n'a changé dans la table
        self.assertEqual(self.entree(DEMO)["trad"], "Demo anfragen")
        self.assertEqual(self.entree(DEMO)["statut"], "mt")
        self.assertEqual(self.entree(RUE)["trad"], "Die Lindenstrasse")
        # le détail dit quoi corriger, sans reproduire le tiret interdit
        detail = next(r["detail"] for r in rapport["refuses"] if r["cle"] == cle(DEMO))
        self.assertIn("tiret", detail)

    def test_fusion_eszett_permis_si_le_francais_le_contient(self):
        self.table.poser("Citation « Straße »", "Zitat « Strasse »", "mt", "LexMachina")
        rapport = self.fusionner({"cle": cle("Citation « Straße »"), "trad": "Zitat « Straße »"})
        self.assertEqual((rapport["poses"], rapport["refuses"]), (1, []))

    def test_fusion_eszett_seulement_en_allemand(self):
        t = Table("it", self.dossier)
        t.poser(DEMO, "Richiedi una demo", "mt", "LexMachina")
        fichier = self.propositions({"cle": cle(DEMO), "trad": "Richiedi una Straße"})
        self.assertEqual(echanges.fusionner(fichier, t, glossaire={}, jour=JOUR)["poses"], 1)

    def test_fusion_refuse_marqueurs_faux(self):
        rapport = self.fusionner(
            {"cle": cle(CAPITAL), "trad": "Das Aktienkapital der Gesellschaft"},                  # marqueurs perdus
            {"cle": cle(ADRESSE), "trad": "Adresse{1}Freiburg{1}"},                                # marqueur seul en double
            {"cle": cle(DEMO), "trad": "Demo {1}anfragen{/1}"})                                    # marqueur inconnu
        self.assertEqual(rapport["poses"], 0)
        self.assertEqual(self.raisons(rapport), {cle(CAPITAL): "marqueurs", cle(ADRESSE): "marqueurs", cle(DEMO): "marqueurs"})
        self.assertEqual(self.entree(CAPITAL)["statut"], "mt")

    def test_fusion_refuse_une_entree_relue(self):
        """Une traduction relue par un traducteur expert n'est jamais réécrite, et son champ v1 reste."""
        rapport = self.fusionner({"cle": cle("Notre équipe"), "trad": "Unser Expertenteam"})
        self.assertEqual(rapport["poses"], 0)
        self.assertEqual(self.raisons(rapport), {cle("Notre équipe"): "déjà relu"})
        e = self.table.entrees[cle("Notre équipe")]
        self.assertEqual((e["trad"], e["statut"], e["v1"]), ("Unser Team", "relu", True))

    def test_fusion_refuse_une_entree_validee_v1_ou_invariante(self):
        self.table.poser("Neur.on", "Neur.on", "invariant", "traduction V1 identique au français")
        rapport = self.fusionner({"cle": cle("Contact"), "trad": "Kontaktieren"}, {"cle": cle("Neur.on"), "trad": "Neuron"})
        self.assertEqual(rapport["poses"], 0)
        self.assertEqual(self.raisons(rapport), {cle("Contact"): "déjà validé", cle("Neur.on"): "déjà validé"})
        self.assertEqual(self.entree("Contact")["trad"], "Kontakt")

    def test_fusion_refait_une_entree_adaptee(self):
        """L'agent de relecture corrige une adaptation de l'autre agent : même commande, même statut."""
        self.fusionner({"cle": cle(DEMO), "trad": "Demo vereinbaren"})
        rapport = self.fusionner({"cle": cle(DEMO), "trad": "Demo buchen"})
        self.assertEqual(rapport["poses"], 1)
        self.assertEqual(self.entree(DEMO)["trad"], "Demo buchen")

    def test_fusion_traduction_vide_refusee(self):
        rapport = self.fusionner({"cle": cle(DEMO), "trad": "  "})
        self.assertEqual(rapport["poses"], 0)
        self.assertEqual(self.raisons(rapport), {cle(DEMO): "traduction vide"})

    def test_fusion_doublon_refuse(self):
        rapport = self.fusionner({"cle": cle(DEMO), "trad": "Demo vereinbaren"}, {"cle": cle(DEMO), "trad": "Demo buchen"})
        self.assertEqual(rapport["poses"], 1)
        self.assertEqual(self.raisons(rapport), {cle(DEMO): "doublon"})
        self.assertEqual(self.entree(DEMO)["trad"], "Demo vereinbaren")

    def test_fusion_proposition_mal_formee(self):
        rapport = self.fusionner("texte", {"trad": "sans clé"}, {"cle": cle(DEMO), "trad": 3}, {"cle": cle(CAPITAL)})
        self.assertEqual(rapport["poses"], 0)
        self.assertEqual([r["raison"] for r in rapport["refuses"]], ["format"] * 4)

    def test_fusion_terminologie_en_avertissement(self):
        rapport = self.fusionner({"cle": cle(CAPITAL), "trad": "Das {1}Grundkapital{/1} der Gesellschaft"})
        self.assertEqual(rapport["poses"], 1)  # posée : la terminologie n'est qu'une alerte
        self.assertEqual(rapport["refuses"], [])
        self.assertEqual([a["cle"] for a in rapport["avertissements"]], [cle(CAPITAL)])
        self.assertIn("capital-actions", rapport["avertissements"][0]["detail"])
        self.assertEqual(self.entree(CAPITAL)["statut"], "adapte")

    def test_fusion_sans_avertissement_si_terme_respecte(self):
        rapport = self.fusionner({"cle": cle(CAPITAL), "trad": "Das {1}Aktienkapital{/1} der Gesellschaft"})
        self.assertEqual(rapport["avertissements"], [])

    def test_fusion_lit_le_glossaire_du_projet_par_defaut(self):
        with mock.patch.object(echanges.chnell, "charger_glossaire", lambda *a, **k: GLOSSAIRE):
            rapport = echanges.fusionner(self.propositions({"cle": cle(CAPITAL), "trad": "Das {1}Grundkapital{/1} der Gesellschaft"}),
                                         self.table, jour=JOUR)
        self.assertEqual(len(rapport["avertissements"]), 1)

    def test_fusion_ne_pose_que_le_statut_adapte(self):
        for statut in ("mt", "relu", "v1", "invariant", "inconnu"):
            with self.assertRaises(ValueError):
                self.fusionner({"cle": cle(DEMO), "trad": "Demo vereinbaren"}, statut=statut)
        self.assertEqual(self.entree(DEMO)["statut"], "mt")
        self.assertEqual(self.entree(DEMO)["trad"], "Demo anfragen")

    def test_fusion_fichier_illisible_ou_pas_une_liste(self):
        f = self.dossier / "mauvais.json"
        f.write_text("pas du json", encoding="utf-8")
        with self.assertRaises(ValueError):
            echanges.fusionner(f, self.table, glossaire={})
        f.write_text('{"cle": "x"}', encoding="utf-8")
        with self.assertRaises(ValueError):
            echanges.fusionner(f, self.table, glossaire={})
        with self.assertRaises(ValueError):
            echanges.fusionner(self.dossier / "absent.json", self.table, glossaire={})

    def test_fusion_ecrit_en_memoire_seulement(self):
        self.fusionner({"cle": cle(DEMO), "trad": "Demo vereinbaren"})
        self.assertFalse(self.table.fichier.exists())  # enregistrer() est l'affaire de l'appelant


class TestCommande(Base):
    def lancer(self, *argv):
        sortie, erreur = io.StringIO(), io.StringIO()
        with contextlib.redirect_stdout(sortie), contextlib.redirect_stderr(erreur), \
                mock.patch.object(build, "DOSSIER_LANGUES", self.dossier), \
                mock.patch.object(cli.chnell, "charger_glossaire", lambda *a, **k: GLOSSAIRE):
            code = cli.main(list(argv))
        return code, sortie.getvalue(), erreur.getvalue()

    def test_commande_fusionner(self):
        self.table.enregistrer()
        fichier = self.propositions({"cle": cle(DEMO), "trad": "Demo vereinbaren", "note": "à faire vérifier"},
                                    {"cle": cle(CAPITAL), "trad": "Das {1}Grundkapital{/1} der Gesellschaft"})
        code, sortie, _ = self.lancer("fusionner", "de", str(fichier))
        self.assertEqual(code, 0)
        self.assertIn("2 proposition(s) posée(s) au statut adapte", sortie)
        self.assertIn("1 avertissement(s) de terminologie", sortie)
        self.assertIn("à faire vérifier", sortie)
        relue = Table("de", self.dossier)
        self.assertEqual(relue.chercher(DEMO, "")["statut"], "adapte")
        self.assertEqual(relue.chercher(DEMO, "")["trad"], "Demo vereinbaren")

    def test_commande_fusionner_refus_donne_code_1_et_ecrit_le_reste(self):
        self.table.enregistrer()
        fichier = self.propositions({"cle": cle(DEMO), "trad": "Demo vereinbaren"},
                                    {"cle": cle("Notre équipe"), "trad": "Unser Expertenteam"})
        code, sortie, _ = self.lancer("fusionner", "de", str(fichier))
        self.assertEqual(code, 1)
        self.assertIn("1 proposition(s) posée(s)", sortie)
        self.assertIn("déjà relu", sortie)
        relue = Table("de", self.dossier)
        self.assertEqual(relue.chercher(DEMO, "")["statut"], "adapte")
        self.assertEqual(relue.chercher("Notre équipe", "")["trad"], "Unser Team")

    def test_commande_fusionner_simuler_n_ecrit_rien(self):
        self.table.enregistrer()
        avant = self.table.fichier.read_bytes()
        fichier = self.propositions({"cle": cle(DEMO), "trad": "Demo vereinbaren"},
                                    {"cle": cle(RUE), "trad": "Die Lindenstraße"})
        code, sortie, _ = self.lancer("fusionner", "de", str(fichier), "--simuler")
        self.assertEqual(code, 1)  # le refus eszett est rapporté
        self.assertIn("1 proposition(s) posée(s)", sortie)
        self.assertIn("eszett", sortie)
        self.assertIn("table non écrite", sortie)
        self.assertEqual(self.table.fichier.read_bytes(), avant)

    def test_commande_fusionner_fichier_introuvable(self):
        code, _, erreur = self.lancer("fusionner", "de", str(self.dossier / "absent.json"))
        self.assertEqual(code, 1)
        self.assertIn("introuvable", erreur)

    def test_commande_fusionner_statut(self):
        self.table.enregistrer()
        fichier = self.propositions({"cle": cle(DEMO), "trad": "Demo vereinbaren"})
        code, _, erreur = self.lancer("fusionner", "de", str(fichier), "--statut", "relu")
        self.assertEqual(code, 1)
        self.assertIn("relu", erreur)
        self.assertEqual(Table("de", self.dossier).chercher(DEMO, "")["statut"], "mt")


GUIDES = ICI / "outils/i18n/guides"
BRIEF = ICI / "outils/i18n/BRIEF-ADAPTATION.md"
V1 = Path(build.NEURON) / "docs-traduction"
REFORMULATIONS = {  # (texte V1, texte du guide du dépôt)
    "de": (("« Zusammenschluss » ou toute allusion au rapprochement.",
            "« Zusammenschluss » ou toute allusion à une opération de reprise."),),
    "en": (("« merger » au sens du rapprochement, ou toute allusion au rapprochement.",
            "« merger » au sens d'une opération de reprise, ou toute allusion à une telle opération."),
           # vague finale, point 10 : le chemin d'un dossier de travail temporaire n'a rien à faire dans le dépôt public
           ("Les originaux extraits sont dans le scratchpad de la session ce992fec : "
            "`/private/tmp/claude-501/-Users-fabienbernier-Claude-project/ce992fec-3d03-4df9-a989-fe30aa564320/scratchpad/"
            "blog-source/`. Ce dossier est **temporaire** : à archiver avant la tâche 13, hors du dépôt public (par exemple "
            "dans `Bibliotheque-Claude/`).",
            "Les originaux extraits ont été rassemblés hors du dépôt public, dans un dossier de travail temporaire de la V1 "
            "(à archiver dans `Bibliotheque-Claude/`).")),
    "it": (("« fusione » au sens du rapprochement, ou toute allusion à celui-ci.",
            "« fusione » au sens d'une opération de reprise, ou toute allusion à celle-ci."),)}


class TestDocuments(unittest.TestCase):
    def test_guides_copies_figees_des_guides_v1(self):
        """Copies des guides V1, à une réserve près : tests/test_regles.py interdit le mot « rapprochement » dans le dépôt,
        et les trois guides l'écrivaient dans la règle sur les marques ; ces trois phrases sont reformulées (REFORMULATIONS)."""
        if not V1.is_dir():
            self.skipTest("site V1 absent (NEURON_SRC)")
        for langue in ("de", "en", "it"):
            attendu = (V1 / f"guide-{langue}.md").read_text(encoding="utf-8")
            for avant, apres in REFORMULATIONS.get(langue, ()):
                self.assertEqual(attendu.count(avant), 1, avant)
                attendu = attendu.replace(avant, apres)
            self.assertEqual((GUIDES / f"guide-{langue}.md").read_text(encoding="utf-8"), attendu, langue)

    def test_brief_contient_les_regles_absolues(self):
        t = BRIEF.read_text(encoding="utf-8")
        for attendu in (
                # format d'échange
                '[{"cle"', "propositions.json", "relecture.json", "fusionner",
                # règles reprises du plan
                "ss, jamais ß", "Sie", "voi", "15'000", "15,000", "britannique",
                "Neur.on, Corrext, LexMachina, CHnell", "Neur.on AI Solutions SA", "jamais « AG »",
                "Text translation", "Double review & certified translation", "Fast lookup CHnell", "Highly sensitive content",
                "Infomaniak", "moteur de traduction neuronale", "jamais un LLM", "proteges.json", "numéro de version",
                "Rien d'inventé", "relu",
                # décisions et rulings
                'lang="fr"', "Ruling 14", "Fedlex", "Ruling 22", "V11", "AI-powered translation software for legal, tax and finance",
                "guide-<langue>.md",
                # vague finale, points 7 et 10
                "aucun accès réseau", "Aucun outil de traduction tiers", "restent hors du dépôt public",
                "preparer <langue>", "contexte_v1"):
            self.assertIn(attendu, t, attendu)

    def test_brief_sans_tiret_long_ni_reference_aux_pages_v1(self):
        t = BRIEF.read_text(encoding="utf-8")
        self.assertNotIn(TIRET_CADRATIN, t)
        self.assertNotIn(TIRET_COURT, t)
        # l'agent travaille sur des propositions de segments : plus de brouillons de pages ni de contrôle V1
        for ancien in ("controle_traductions.py", "src/langues/<lang>/", "front-matter", "--seulement"):
            self.assertNotIn(ancien, t, ancien)

    def test_brief_ne_nomme_aucun_terme_interdit(self):
        """Règle du dépôt (tests/test_regles.py) : le brief renvoie à proteges.json au lieu d'écrire les termes interdits."""
        t = BRIEF.read_text(encoding="utf-8")
        for terme in json.loads((ICI / "src/langues/proteges.json").read_text(encoding="utf-8"))["interdits"]:
            self.assertIsNone(re.search(r"(?<!\w)" + re.escape(terme) + r"(?!\w)", t, re.I), terme)

    def test_brief_sans_nom_de_modele_ni_prix(self):
        t = BRIEF.read_text(encoding="utf-8").lower()
        for interdit in ("gpt", "gemini", "claude", "exoscale", "deepl"):
            self.assertNotIn(interdit, t, interdit)

    def test_brief_adapte_les_regles_de_la_v1(self):
        """Le brief V1 parle de pages et de fichiers ; celui-ci de segments : chaque règle de fond de la V1 y est encore."""
        t = BRIEF.read_text(encoding="utf-8")
        for attendu in ("title", "62", "description", "160", "une idée par phrase", "calque"):
            self.assertIn(attendu, t, attendu)

    def test_guides_sans_chemin_de_travail_temporaire(self):
        for langue in ("de", "en", "it"):
            t = (GUIDES / f"guide-{langue}.md").read_text(encoding="utf-8")
            self.assertNotIn("/private/tmp", t, langue)
            self.assertNotIn("scratchpad/blog-source", t, langue)

    def test_guides_sans_tiret_long(self):
        for langue in ("de", "en", "it"):
            t = (GUIDES / f"guide-{langue}.md").read_text(encoding="utf-8")
            self.assertEqual(len(re.findall("[" + TIRET_CADRATIN + TIRET_COURT + "]", t)), 0, langue)


if __name__ == "__main__":
    unittest.main()
