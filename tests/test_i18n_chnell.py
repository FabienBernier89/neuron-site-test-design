"""Terminologie vérifiée dans CHnell (tâches 4.2 et 4.3) : outils/i18n/chnell.py et commandes chnell, glossaire.

Tout est synthétique : lexique, journal et termes V1 écrits ici, dossiers temporaires pour les fichiers. Aucun test ne lit
ni n'écrit le dossier réel de la terminologie (Bibliotheque-Claude, Ruling 5), aucune requête réseau, aucune capture de
CHnell : la lecture des résultats s'appuie sur une fixture JSON synthétique (textes de remplissage), qui reprend la
structure relevée avec Fabien le 2026-10-26 sans aucun texte réel de CHnell (le dépôt est public)."""
import contextlib
import io
import json
import re
import tempfile
import unittest
from pathlib import Path
from unittest import mock

import build
from outils.i18n import __main__ as commandes
from outils.i18n import chnell, terminologie

TIRET_CADRATIN, DEMI_CADRATIN = chr(0x2014), chr(0x2013)
FIXTURE = Path(__file__).resolve().parent / "fixtures" / "i18n" / "chnell-resultats.json"


def page(etat="resultats", resultats=(), total=""):
    """Sortie JSON du script d'extraction, telle que la renvoie l'outil JavaScript."""
    return json.dumps({"etat": etat, "total": total, "resultats": list(resultats)})


def resultat(source, cible, reference="Référence de remplissage"):
    return {"domaine": "DOMAINE", "reference": reference, "source": source, "surlignes_source": [],
            "surlignes_cible": cible}


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
                       {"justification": "x" * 400}, {"retenu": "Schloß"},
                       # vague finale, point 14 : date AAAA-MM-JJ stricte, verifie_par en liste fermée
                       {"date": "20261026"}, {"date": "2026-W43-1"}, {"date": "2026-10-26T10:00"},
                       {"verifie_par": "quelqu'un"}, {"verifie_par": "fabien"}, {"verifie_par": None}):
            with self.subTest(champs=champs), self.assertRaises(ValueError):
                chnell.ajouter(self.journal, {**ligne("capital-actions"), **champs})

    def test_verificateurs_admis(self):
        for qui in chnell.VERIFICATEURS:
            chnell.ajouter(self.journal, ligne("capital-actions", verifie_par=qui))
        self.assertEqual([e["verifie_par"] for e in chnell.charger_journal(self.journal.parent)], ["agent", "Fabien"])

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
    def test_lire_resultats_fixture(self):
        resultats = chnell.lire_resultats(FIXTURE.read_text(encoding="utf-8"))
        self.assertEqual(len(resultats), 5)
        for r in resultats[:4]:
            for champ in ("domaine", "reference", "source"):
                self.assertTrue(r[champ], champ)
            self.assertTrue(r["surlignes_source"] and r["surlignes_cible"])
        self.assertEqual(resultats[0]["source"], "fedlex.admin.ch")
        self.assertEqual(resultats[0]["surlignes_cible"], ["Zielwort Alpha", "Nebenwort", "Zielwort Alpha"])
        self.assertEqual(chnell.lire_page(FIXTURE.read_text(encoding="utf-8"))["total"], "42 results")

    def test_page_de_connexion_refusee(self):
        with self.assertRaisesRegex(ValueError, "page de connexion : prévenir Fabien"):
            chnell.lire_resultats(page("connexion"))

    def test_page_en_chargement_refusee(self):
        with self.assertRaisesRegex(ValueError, "chargement"):
            chnell.lire_resultats(page("chargement"))

    def test_aucun_resultat_rend_une_liste_vide(self):
        self.assertEqual(chnell.lire_resultats(page("aucun")), [])

    def test_sortie_doublement_encodee_acceptee(self):
        """L'outil JavaScript peut renvoyer la chaîne JSON elle-même encodée en JSON."""
        brut = FIXTURE.read_text(encoding="utf-8")
        self.assertEqual(chnell.lire_resultats(json.dumps(brut)), chnell.lire_resultats(brut))

    def test_schema_refuse(self):
        bon = resultat("fedlex.admin.ch", ["Zielwort"])
        for texte in ("", "pas du json", "[]", json.dumps({"etat": "inconnu", "total": "", "resultats": []}),
                      json.dumps({"etat": "resultats", "total": "", "resultats": [{"source": "x"}]}),
                      json.dumps({"etat": "resultats", "total": "", "resultats": "aucun"}),
                      json.dumps({"etat": "resultats", "total": 3, "resultats": [bon]}),
                      page("resultats", [{**bon, "surlignes_cible": "Zielwort"}]),
                      page("resultats", [{**bon, "surlignes_cible": [3]}]),
                      page("resultats", [{**bon, "source": None}]),
                      # jamais de texte complet : un champ en trop est refusé
                      page("resultats", [{**bon, "phrase": "texte complet d'un résultat"}])):
            with self.subTest(texte=texte[:50]), self.assertRaises(ValueError):
                chnell.lire_resultats(texte)


class TestEquivalents(unittest.TestCase):
    def test_equivalents_fedlex_dabord(self):
        """Le plan : Fedlex d'abord, même si un autre terme est plus fréquent hors Fedlex."""
        resultats = chnell.lire_resultats(FIXTURE.read_text(encoding="utf-8"))
        eq = chnell.equivalents(resultats)
        self.assertEqual([e[0] for e in eq], ["Zielwort Alpha", "Nebenwort", "Zielwort Beta", "Zielwort Gamma"])
        # Zielwort Beta compte 4 occurrences (casse fusionnée), plus que Zielwort Alpha (3), mais hors Fedlex
        self.assertEqual([e[1] for e in eq], [3, 2, 4, 1])
        self.assertEqual(eq[0][2], ["fedlex.admin.ch"])
        self.assertEqual(eq[2][2], ["autorite-exemple.example"])

    def test_classement_par_frequence_puis_ordre_d_apparition(self):
        eq = chnell.equivalents([resultat("exemple.example", ["Bb", "Aa", "Cc", "Aa", "Cc", "Dd"])])
        self.assertEqual([(e[0], e[1]) for e in eq], [("Aa", 2), ("Cc", 2), ("Bb", 1), ("Dd", 1)])

    def test_casse_normalisee_flexions_non_fusionnees(self):
        eq = chnell.equivalents([resultat("exemple.example", ["Kapital", "kapital", " Kapital. ", "Kapitals"])])
        self.assertEqual([(e[0], e[1]) for e in eq], [("Kapital", 3), ("Kapitals", 1)])

    def test_sources_distinctes_fedlex_en_premier(self):
        eq = chnell.equivalents([resultat("exemple.example", ["Terme"]), resultat("fedlex.admin.ch", ["Terme", "Terme"]),
                                 resultat("exemple.example", ["Terme"])])
        self.assertEqual(eq, [("Terme", 4, ["fedlex.admin.ch", "exemple.example"])])

    def test_sans_resultat(self):
        self.assertEqual(chnell.equivalents([]), [])
        self.assertEqual(chnell.equivalents([resultat("fedlex.admin.ch", [])]), [])


class TestExtractionJs(unittest.TestCase):
    """Le script d'extraction ne dépend pas du suffixe haché des classes CSS Modules (il change à chaque déploiement)."""

    def test_selecteurs_par_prefixe_seulement(self):
        for script in (chnell.EXTRACTION_JS, chnell.EXTRACTION_JS_PLUS):
            attributs = re.findall(r"\[class([^\]=]*)=\"([^\"]*)\"\]", script)
            self.assertGreaterEqual(len(attributs), 7)
            for operateur, valeur in attributs:
                self.assertEqual(operateur, "^", f"[class{operateur}={valeur}] : sélecteur par préfixe attendu")
                self.assertNotIn("__", valeur, "suffixe haché dans un sélecteur")
            self.assertFalse(re.findall(r"\.[A-Za-z]+_[A-Za-z]+__", script), "classe hachée écrite en entier")

    def test_selecteurs_releves_avec_fabien(self):
        self.assertEqual(chnell.ZONE, '[class^="SearchResults_container"]')
        for script in (chnell.EXTRACTION_JS, chnell.EXTRACTION_JS_PLUS):
            for selecteur in (chnell.ZONE, '[class^="AlignmentResult_container"]', '[class^="AlignmentResult_domain"]',
                              '[class^="AlignmentResult_rest"]',
                              '[class^="AlignmentResult_alignment"] > div:nth-child(1) span.bg-highlight',
                              '[class^="AlignmentResult_alignment"] > div:nth-child(2) span.bg-highlight'):
                self.assertIn(selecteur, script)
        self.assertIn('[class^="SearchResults_showMore"] button', chnell.EXTRACTION_JS_PLUS)
        self.assertNotIn("showMore", chnell.EXTRACTION_JS)

    def test_aucun_texte_complet_dans_la_sortie(self):
        """Seuls les surlignés, la référence, la source et le domaine sortent : pas de HTML, pas de phrase."""
        for script in (chnell.EXTRACTION_JS, chnell.EXTRACTION_JS_PLUS):
            self.assertNotIn("innerHTML", script)
            self.assertNotIn("outerHTML", script)
            self.assertIn("JSON.stringify", script)
            for champ in ("etat", "total", "resultats", "domaine", "reference", "source", "surlignes_source",
                          "surlignes_cible"):
                self.assertIn(champ, script)

    def test_sans_tiret_long(self):
        for script in (chnell.EXTRACTION_JS, chnell.EXTRACTION_JS_PLUS):
            self.assertNotIn(TIRET_CADRATIN, script)
            self.assertNotIn(DEMI_CADRATIN, script)


V1_DE = [{"fr": "capital-actions", "de": "Aktienkapital", "type": "glossaire", "source": "V1"},
         {"fr": "prescription", "de": "Verjährung", "type": "glossaire", "source": "V1"},
         {"fr": "prescription", "de": "Verjaehrungsfrist", "type": "metier", "source": "V1"},
         {"fr": "devis", "de": "Offerte", "type": "metier", "source": "V1"}]


class TestGlossaire(unittest.TestCase):
    def construire(self, journal, termes=None):
        return chnell.construire_glossaire(journal, {"de": V1_DE if termes is None else termes})

    def test_glossaire_ignore_a_arbitrer(self):
        journal = [ligne("capital-actions", retenu="Grundkapital", statut="a_arbitrer"),
                   ligne("assemblée générale", retenu="Generalversammlung", statut="confirme"),
                   ligne("mandat", statut="absent", retenu=None, resultats=0, sources=[])]
        self.assertEqual(list(self.construire(journal)), ["assemblée générale"])

    def test_glossaire_garde_la_source(self):
        journal = [ligne("capital-actions", sources=["Fedlex : CO art. 620", "Fedlex : CC art. 2"]),
                   ligne("assemblée générale", retenu="Generalversammlung", statut="corrige", sources=[])]
        g = self.construire(journal)
        self.assertEqual(g["capital-actions"]["de"],
                         {"terme": "Aktienkapital", "source": "Fedlex : CO art. 620 ; Fedlex : CC art. 2",
                          "statut": "confirme"})
        self.assertEqual(g["assemblée générale"]["de"],
                         {"terme": "Generalversammlung", "source": "CHnell", "statut": "corrige"})

    def test_conflit_v1_signale(self):
        journal = [ligne("capital-actions", retenu="Grundkapital", statut="confirme"),
                   ligne("devis", retenu="Offerte", statut="confirme"),
                   ligne("prescription", retenu="verjährung", statut="confirme")]  # casse seule : pas un conflit
        g = self.construire(journal)
        self.assertNotIn("capital-actions", g, "divergence avec la V1 : à Fabien, pas dans le glossaire")
        self.assertEqual(sorted(g), ["devis", "prescription"])
        a = chnell.arbitrages(journal, {"de": V1_DE})
        self.assertEqual([(x["fr"], x["langue"], x["retenu"], x["v1"]) for x in a],
                         [("capital-actions", "de", "Grundkapital", ["Aktienkapital"])])
        self.assertIn("V1", a[0]["raison"])

    def test_a_arbitrer_du_journal_est_liste(self):
        journal = [ligne("assemblée générale", retenu="Generalversammlung", statut="a_arbitrer",
                         justification="deux équivalents à égalité")]
        a = chnell.arbitrages(journal, {"de": V1_DE})
        self.assertEqual([(x["fr"], x["v1"], x["justification"]) for x in a],
                         [("assemblée générale", [], "deux équivalents à égalité")])

    def test_arbitrage_tranche_par_fabien(self):
        """La dernière ligne d'un terme l'emporte ; celle de Fabien n'est plus un conflit avec la V1."""
        journal = [ligne("capital-actions", retenu="Grundkapital", statut="a_arbitrer"),
                   ligne("capital-actions", retenu="Grundkapital", statut="corrige", verifie_par="Fabien",
                         justification="arbitrage de Fabien")]
        g = self.construire(journal)
        self.assertEqual(g["capital-actions"]["de"]["terme"], "Grundkapital")
        self.assertEqual(chnell.arbitrages(journal, {"de": V1_DE}), [])

    def test_derniere_ligne_l_emporte(self):
        journal = [ligne("devis", retenu="Offerte", statut="confirme"),
                   ligne("devis", retenu="Offerte", statut="absent", resultats=0, sources=[])]
        # le dernier avis est « absent » : plus d'entrée au glossaire
        self.assertNotIn("devis", self.construire(journal))

    def test_langue_sans_termes_v1_pas_de_conflit(self):
        journal = [ligne("capital-actions", langue="en", retenu="share capital")]
        g = chnell.construire_glossaire(journal, {})
        self.assertEqual(g["capital-actions"]["en"]["terme"], "share capital")

    def test_trois_langues_dans_un_meme_glossaire(self):
        journal = [ligne("capital-actions"), ligne("capital-actions", langue="en", retenu="share capital")]
        g = chnell.construire_glossaire(journal, {"de": V1_DE})
        self.assertEqual(sorted(g["capital-actions"]), ["de", "en"])


class TestFichiersTerminologie(unittest.TestCase):
    def setUp(self):
        tmp = tempfile.TemporaryDirectory()
        self.addCleanup(tmp.cleanup)
        self.dossier = Path(tmp.name)

    def test_ecrire_remplace_la_langue_et_garde_les_autres(self):
        de = {"capital-actions": {"de": {"terme": "Aktienkapital", "source": "CHnell", "statut": "confirme"}}}
        en = {"capital-actions": {"en": {"terme": "share capital", "source": "CHnell", "statut": "confirme"}}}
        chnell.ecrire_glossaire(de, "de", self.dossier)
        chnell.ecrire_glossaire(en, "en", self.dossier)
        self.assertEqual(sorted(chnell.charger_glossaire(self.dossier)["capital-actions"]), ["de", "en"])
        chnell.ecrire_glossaire({}, "de", self.dossier)  # relancer : le terme DE disparu est retiré, l'anglais reste
        self.assertEqual(list(chnell.charger_glossaire(self.dossier)["capital-actions"]), ["en"])
        chnell.ecrire_glossaire({}, "en", self.dossier)
        self.assertEqual(chnell.charger_glossaire(self.dossier), {})

    def test_glossaire_absent(self):
        self.assertEqual(chnell.charger_glossaire(self.dossier), {})

    def test_fichiers_dans_le_dossier_de_la_terminologie_par_defaut(self):
        with mock.patch.object(terminologie, "TERMINOLOGIE", self.dossier):
            chnell.ecrire_glossaire({}, "de")
            self.assertEqual(chnell.fichier_journal(), self.dossier / "journal.jsonl")
            self.assertTrue((self.dossier / "glossaire.json").is_file())


class Commandes(unittest.TestCase):
    """Commandes chnell et glossaire, dans un dossier de terminologie et un site V1 temporaires."""

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

    def test_lire_affiche_les_equivalents_classes_et_leurs_sources(self):
        code, sortie, erreur = self.lancer("chnell", "lire", str(FIXTURE), "--fr", "terme de test", "--langue", "de")
        self.assertEqual(code, 0, erreur)
        self.assertIn("« terme de test »", sortie)
        self.assertIn("5 résultat(s) lu(s) sur 42 results", sortie)
        self.assertIn("1. Zielwort Alpha : 3 occurrence(s), sources : fedlex.admin.ch", sortie)
        self.assertIn("3. Zielwort Beta : 4 occurrence(s), sources : autorite-exemple.example", sortie)
        self.assertLess(sortie.index("Zielwort Alpha"), sortie.index("Zielwort Beta"))
        self.assertIn(chnell.url_chnell("terme de test", "de"), sortie)
        self.assertEqual(chnell.charger_journal(self.dossier), [], "lire n'écrit rien dans le journal")

    def test_lire_refuse_la_page_de_connexion_avec_un_message_en_francais(self):
        fichier = self.dossier.parent / "connexion.json"
        fichier.write_text(page("connexion"), encoding="utf-8")
        code, sortie, erreur = self.lancer("chnell", "lire", str(fichier), "--fr", "capital-actions", "--langue", "de")
        self.assertEqual(code, 1)
        self.assertIn("page de connexion : prévenir Fabien", erreur)
        self.assertEqual(sortie, "")

    def test_lire_aucun_resultat(self):
        fichier = self.dossier.parent / "aucun.json"
        fichier.write_text(page("aucun"), encoding="utf-8")
        code, sortie, _ = self.lancer("chnell", "lire", str(fichier), "--fr", "capital-actions", "--langue", "de")
        self.assertEqual(code, 0)
        self.assertIn("aucun résultat", sortie)

    def test_lire_fichier_introuvable(self):
        code, _, erreur = self.lancer("chnell", "lire", "inexistant.json", "--fr", "capital-actions", "--langue", "de")
        self.assertEqual(code, 1)
        self.assertIn("introuvable", erreur)

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


class TestCommandeGlossaire(Commandes):
    def test_glossaire_ecrit_le_fichier_et_liste_les_arbitrages(self):
        terminologie.ecrire_lexique("de", [lex("capital-actions", 2), lex("devis", 3), lex("assemblée générale", 1),
                                           lex("procuration", 2)], self.dossier)
        self.ajouter("capital-actions", "Grundkapital")           # diverge de la V1 : arbitrage
        self.ajouter("devis", "Offerte")                          # confirme la V1
        self.ajouter("assemblée générale", "Generalversammlung", "a_arbitrer")
        code, sortie, erreur = self.lancer("glossaire", "--langue", "de", "--arbitrages")
        self.assertEqual(code, 0, erreur)
        g = chnell.charger_glossaire(self.dossier)
        self.assertEqual(list(g), ["devis"])
        self.assertEqual(g["devis"]["de"]["terme"], "Offerte")
        self.assertIn("Arbitrages pour Fabien : 2", sortie)
        self.assertIn("capital-actions", sortie)
        self.assertIn("Grundkapital", sortie)
        self.assertIn("Aktienkapital", sortie)          # l'équivalent de la V1 en regard
        self.assertIn("assemblée générale", sortie)
        # critère V5 : « procuration » est retenu, de priorité 2, et n'a pas de ligne de journal
        self.assertIn("1 terme(s) retenu(s)", sortie)
        self.assertIn("procuration", sortie)

    def test_glossaire_sans_l_option_ne_detaille_pas_les_arbitrages(self):
        self.ajouter("capital-actions", "Grundkapital")
        code, sortie, _ = self.lancer("glossaire", "--langue", "de")
        self.assertEqual(code, 0)
        self.assertIn("Arbitrages pour Fabien : 1", sortie)
        self.assertNotIn("Grundkapital", sortie)

    def test_glossaire_garde_les_autres_langues(self):
        chnell.ecrire_glossaire({"capital-actions": {"en": {"terme": "share capital", "source": "CHnell",
                                                            "statut": "confirme"}}}, "en", self.dossier)
        self.ajouter("devis", "Offerte")
        self.lancer("glossaire", "--langue", "de")
        self.assertEqual(sorted(chnell.charger_glossaire(self.dossier)), ["capital-actions", "devis"])

    def test_termes_v1_introuvables(self):
        (self.v1 / "src/i18n/termes-de.json").unlink()
        code, _, erreur = self.lancer("glossaire", "--langue", "de")
        self.assertEqual(code, 1)
        self.assertIn("Termes V1 introuvables", erreur)


if __name__ == "__main__":
    unittest.main()
