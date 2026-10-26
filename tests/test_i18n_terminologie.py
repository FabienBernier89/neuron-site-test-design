"""Lexique des termes à vérifier dans CHnell (tâche 4.1) : outils/i18n/terminologie.py.

Tout est synthétique : mini tables et mini pages écrites ici, dossiers temporaires pour les fichiers du lexique. Aucun
test ne lit ni n'écrit le dossier réel de la terminologie (Bibliotheque-Claude, Ruling 5)."""
import os
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

from outils.i18n import terminologie as TM
from outils.i18n.table import Table

ICI = Path(__file__).resolve().parent.parent
TIRET_CADRATIN, DEMI_CADRATIN = chr(0x2014), chr(0x2013)


def page(*paragraphes):
    """Page FR assemblée minimale : un <p> par texte."""
    corps = "".join(f"<p>{p}</p>" for p in paragraphes)
    return ('<!DOCTYPE html>\n<html lang="fr"><head><meta charset="utf-8"><title>Titre</title></head><body>\n'
            f'<main id="main">{corps}</main>\n</body></html>')


def terme(fr, de, type_, source="V1"):
    return {"fr": fr, "de": de, "type": type_, "source": source}


V1 = [terme("capital-actions", "Aktienkapital", "glossaire"),
      terme("prescription", "Verjährung", "glossaire"),
      terme("devis", "Offerte", "metier"),
      terme("LB", "BankG", "loi"),
      terme("CO", "OR", "loi"),
      terme("Code des obligations", "Obligationenrecht", "loi"),
      terme("RS", "SR", "publication"),
      terme("Corrext", "Corrext", "produit"),
      terme("Enregistrer", "Speichern", "interface"),
      terme("Fribourg", "Freiburg", "lieu")]


class Base(unittest.TestCase):
    def setUp(self):
        tmp = tempfile.TemporaryDirectory()
        self.addCleanup(tmp.cleanup)
        self.dossier = Path(tmp.name)
        self.table = Table("de", self.dossier)

    def candidats(self, pages, termes=V1):
        return TM.candidats("de", self.table, termes, pages)

    @staticmethod
    def deux(texte):
        """Deux segments distincts qui répètent le texte : un même texte sur deux pages ne compte qu'une fois."""
        return {"a/": page(texte), "b/": page(texte + " Voir plus.")}

    def trouver(self, resultat, fr):
        return next((e for e in resultat if e["fr"] == fr), None)


class TestTermesV1(Base):
    def test_terme_v1_present_retenu(self):
        r = self.candidats({"ressources/glossaire/capital-actions/": page("Le capital-actions de la société reste libre.")})
        e = self.trouver(r, "capital-actions")
        self.assertEqual(e, {"fr": "capital-actions", "origine": ["v1:termes-de", "segments-nouveaux"], "priorite": 2,
                             "pages": ["ressources/glossaire/capital-actions/"], "occurrences": 1, "retenu": True})

    def test_terme_dans_un_segment_v1_est_une_confirmation(self):
        self.table.poser("Une prescription de dix ans s'applique.", "Eine zehnjährige Verjährung gilt.", "v1", "V1")
        r = self.candidats({"a/": page("Une prescription de dix ans s'applique.")})
        e = self.trouver(r, "prescription")
        self.assertEqual((e["priorite"], e["origine"], e["retenu"]), (3, ["v1:termes-de"], True))

    def test_segment_adapte_compte_comme_nouveau(self):
        self.table.poser("Un devis gratuit.", "Eine kostenlose Offerte.", "adapte", "recomposé")
        e = self.trouver(self.candidats({"a/": page("Un devis gratuit.")}), "devis")
        self.assertEqual(e["priorite"], 2)

    def test_une_page_nouvelle_suffit_a_la_priorite_2(self):
        self.table.poser("Un devis gratuit.", "Eine kostenlose Offerte.", "v1", "V1")
        r = self.candidats({"a/": page("Un devis gratuit."), "b/": page("Votre devis arrive vite.")})
        e = self.trouver(r, "devis")
        self.assertEqual((e["priorite"], e["pages"], e["occurrences"]), (2, ["b/"], 1))

    def test_terme_absent_du_site_ou_de_type_exclu_pas_candidat(self):
        r = self.candidats({"a/": page("Enregistrer puis aller à Fribourg avec Corrext.")})
        self.assertEqual(r, [])  # interface, lieu, produit : jamais candidats ; prescription etc. absents des segments

    def test_abreviation_en_majuscules_sensible_a_la_casse(self):
        r = self.candidats({"a/": page("Le co-fondateur signe.", "Le RS fait foi.")})
        self.assertIsNone(self.trouver(r, "CO"))
        self.assertIsNotNone(self.trouver(r, "RS"))

    def test_mot_entier(self):
        r = self.candidats({"a/": page("Les devises restent stables.")})
        self.assertIsNone(self.trouver(r, "devis"))


class TestReferencesLegales(Base):
    def test_reference_legale_detectee(self):
        r = self.candidats({"a/": page("Le secret bancaire découle de l'art. 47 LB et protège le client.")})
        e = self.trouver(r, "art. 47 LB")
        self.assertEqual(e, {"fr": "art. 47 LB", "origine": ["reference-legale"], "priorite": 1,
                             "pages": ["a/"], "occurrences": 1, "retenu": True})

    def test_reference_avec_alinea_et_lettre(self):
        r = self.candidats({"a/": page("Voir l'art. 104 al. 1 CO, puis l'art. 37a LB.")})
        self.assertIsNotNone(self.trouver(r, "art. 104 al. 1 CO"))
        self.assertIsNotNone(self.trouver(r, "art. 37a LB"))

    def test_reference_avec_chiffre_virgules_et_majuscule(self):
        """Vague finale, point 14 : « ch. », virgules et « Art. » en début de phrase."""
        r = self.candidats({"a/": page("Voir l'art. 6, al. 1, ch. 2 LB.", "Art. 24 CO : le principe.",
                                       "Selon l'art. 3 al. 1 ch. 4 LB, rien.")})
        for attendu in ("art. 6, al. 1, ch. 2 LB", "Art. 24 CO", "art. 3 al. 1 ch. 4 LB"):
            self.assertIsNotNone(self.trouver(r, attendu), attendu)

    def test_reference_sous_balise_en_ligne(self):
        r = self.candidats({"a/": page("Selon l'art. 47 <abbr>LB</abbr>, le secret est protégé.")})
        self.assertIsNotNone(self.trouver(r, "art. 47 LB"))

    def test_abreviation_seule_devient_priorite_1(self):
        e = self.trouver(self.candidats({"a/": page("La LB prévoit le secret.")}), "LB")
        self.assertEqual((e["priorite"], e["origine"]), (1, ["v1:termes-de", "segments-nouveaux", "reference-legale"]))

    def test_segment_deja_traduit_en_v1_ne_donne_pas_de_reference(self):
        self.table.poser("Voir l'art. 47 LB.", "Siehe Art. 47 BankG.", "v1", "V1")
        r = self.candidats({"a/": page("Voir l'art. 47 LB.")})
        self.assertIsNone(self.trouver(r, "art. 47 LB"))
        self.assertEqual(self.trouver(r, "LB")["priorite"], 3)

    def test_abreviation_inconnue_de_la_v1_ignoree(self):
        r = self.candidats({"a/": page("Voir l'art. 5 LXY.")}, termes=[terme("LB", "BankG", "loi")])
        self.assertEqual([e["fr"] for e in r if e["origine"] == ["reference-legale"]], [])


class TestNgrammes(Base):
    def test_ngramme_repete(self):
        r = self.candidats({"a/": page("Le droit des sociétés évolue."), "b/": page("Notre droit des sociétés s'adapte.")})
        e = self.trouver(r, "droit des sociétés")
        self.assertEqual(e, {"fr": "droit des sociétés", "origine": ["ngramme"], "priorite": 1,
                             "pages": ["a/", "b/"], "occurrences": 2, "retenu": None})

    def test_meme_texte_sur_deux_pages_compte_une_fois(self):
        r = self.candidats({"a/": page("Le droit des sociétés évolue."), "b/": page("Le droit des sociétés évolue.")})
        self.assertIsNone(self.trouver(r, "droit des sociétés"))

    def test_ngramme_unique_ignore(self):
        r = self.candidats({"a/": page("Le droit des sociétés évolue.")})
        self.assertIsNone(self.trouver(r, "droit des sociétés"))

    def test_mot_outil_en_bord_exclu(self):
        r = self.candidats({"a/": page("Le droit des sociétés évolue."), "b/": page("Notre droit des sociétés s'adapte.")})
        fr = {e["fr"] for e in r}
        self.assertNotIn("des sociétés", fr)
        self.assertNotIn("droit des", fr)
        self.assertNotIn("sociétés s'", fr)
        self.assertTrue(all(e["fr"].split()[0] not in ("le", "des", "notre") for e in r if e["origine"] == ["ngramme"]))

    def test_ponctuation_et_nombres_coupent_le_ngramme(self):
        r = self.candidats(self.deux("Registre foncier, cadastre suisse."))
        fr = {e["fr"] for e in r}
        self.assertIn("registre foncier", fr)
        self.assertIn("cadastre suisse", fr)
        self.assertNotIn("foncier cadastre", fr)
        r = self.candidats(self.deux("Taux 5 % maximal."))
        self.assertNotIn("taux maximal", {e["fr"] for e in r})

    def test_taille_de_2_a_4_mots(self):
        phrase = "Nous gérons les contrats internationaux de grande valeur."
        r = self.candidats(self.deux(phrase))
        tailles = {len(e["fr"].split()) for e in r}
        self.assertTrue(tailles <= {2, 3, 4}, tailles)
        self.assertNotIn("contrats", {e["fr"] for e in r})

    def test_segment_traduit_en_v1_hors_ngrammes(self):
        self.table.poser("Registre foncier ouvert.", "Offenes Grundbuch.", "v1", "V1")
        r = self.candidats({"a/": page("Registre foncier ouvert."), "b/": page("Registre foncier ouvert.")})
        self.assertIsNone(self.trouver(r, "registre foncier"))

    def test_ngramme_deja_terme_v1_non_double(self):
        termes = [terme("registre foncier", "Grundbuch", "glossaire")]
        r = self.candidats({"a/": page("Registre foncier ouvert."), "b/": page("Registre foncier clos.")}, termes)
        e = self.trouver(r, "registre foncier")
        self.assertEqual((e["priorite"], e["origine"]), (2, ["v1:termes-de", "segments-nouveaux"]))

    def test_ngramme_contenu_dans_un_plus_long_de_meme_frequence_retire(self):
        phrase = "La traduction neuronale juridique avance."
        r = self.candidats({"a/": page(phrase), "b/": page(phrase.replace("avance", "progresse"))})
        fr = {e["fr"] for e in r}
        self.assertIn("traduction neuronale juridique", fr)
        self.assertNotIn("traduction neuronale", fr)


    def test_passage_etranger_ignore(self):
        r = self.candidats(self.deux("The debtor in default shall pay the interest."))
        self.assertEqual([e for e in r if e["origine"] == ["ngramme"]], [])
        r = self.candidats(self.deux("Il debitore in mora paga gli interessi."))
        self.assertEqual([e for e in r if e["origine"] == ["ngramme"]], [])

    def test_majuscule_de_debut_de_phrase_retiree_pas_celle_du_milieu(self):
        r = self.candidats({"a/": page("Registre foncier ouvert.", "Voir le Code civil suisse."),
                            "b/": page("Registre foncier clos.", "Lire le Code civil suisse.")})
        fr = {e["fr"] for e in r}
        self.assertIn("registre foncier", fr)
        self.assertIn("Code civil suisse", fr)

    def test_apostrophe_typographique_et_elision(self):
        r = self.candidats(self.deux("Le droit d\u2019auteur."))
        self.assertIn("droit d'auteur", {e["fr"] for e in r})


class TestMarquesExclues(Base):
    def test_marques_exclues(self):
        texte = "Corrext et LexMachina traduisent avec Fast Lookup CHnell le droit fiscal."
        r = self.candidats(self.deux(texte))
        for e in r:
            for nom in ("corrext", "lexmachina", "chnell", "fast lookup"):
                self.assertNotIn(nom, e["fr"].lower())
        self.assertIn("droit fiscal", {e["fr"] for e in r})

    def test_libelle_d_application_exclu(self):
        texte = "Choisissez Text translation puis Light review pour le droit fiscal."
        r = self.candidats(self.deux(texte))
        for e in r:
            self.assertNotIn("text translation", e["fr"].lower())
            self.assertNotIn("light review", e["fr"].lower())

    def test_libelle_de_plusieurs_mots_exclu_quelle_que_soit_la_casse(self):
        r = self.candidats(self.deux("Le choix du translation engine reste libre dans le droit fiscal."))
        self.assertNotIn("translation engine", " ".join(e["fr"].lower() for e in r))

    def test_libelle_d_un_mot_exclu_en_casse_exacte_seulement(self):
        r = self.candidats(self.deux("Des alternatives fiables. Alternatives Corrext."))
        fr = {e["fr"] for e in r}
        self.assertIn("alternatives fiables", fr)  # mot français ordinaire
        r = self.candidats(self.deux("Cliquez sur Alternatives fiables."))
        self.assertNotIn("Alternatives fiables", {e["fr"] for e in r})  # libellé de l'application, casse exacte

    def test_variante_partielle_d_un_libelle_protege_exclue(self):
        """Vague finale, point 14 : « Highly sensitive » (marque « Highly sensitive content ») et « Double review »
        (libellé « Double review & certified translation ») ne sont jamais candidats."""
        r = self.candidats(self.deux("Activez Highly sensitive pour vos actes. Optez pour Double review ensuite."))
        fr = {e["fr"].lower() for e in r}
        self.assertNotIn("highly sensitive", fr)
        self.assertNotIn("double review", fr)
        self.assertTrue(TM._partie_protegee("Certified translation"))
        self.assertFalse(TM._partie_protegee("review"))  # un mot seul : jamais une variante partielle
        self.assertFalse(TM._partie_protegee("droit des sociétés"))

    def test_ngramme_ne_traverse_pas_une_marque(self):
        texte = "Le moteur LexMachina neuronal rapide."
        r = self.candidats(self.deux(texte))
        self.assertNotIn("moteur neuronal", {e["fr"] for e in r})

    def test_terme_v1_protege_jamais_candidat(self):
        termes = [terme("CHnell", "CHnell", "glossaire"), terme("Fast Lookup", "Fast Lookup", "metier")]
        self.assertEqual(self.candidats({"a/": page("CHnell et Fast Lookup aident.")}, termes), [])


class TestDeterminisme(Base):
    def test_deterministe(self):
        pages = {"b/": page("Le droit des sociétés évolue.", "Un devis pour l'art. 47 LB."),
                 "a/": page("Notre droit des sociétés s'adapte.", "Le capital-actions est libre.")}
        inverse = dict(reversed(list(pages.items())))
        r1 = self.candidats(pages)
        r2 = self.candidats(inverse, termes=list(reversed(V1)))
        self.assertEqual(r1, r2)
        self.assertEqual(r1, sorted(r1, key=lambda e: (e["priorite"], e["fr"])))
        self.assertTrue(r1)

    def test_champs_et_pas_de_tiret(self):
        r = self.candidats({"a/": page("Le droit des sociétés évolue."), "b/": page("Le droit des sociétés évolue encore.")})
        for e in r:
            self.assertEqual(set(e), {"fr", "origine", "priorite", "pages", "occurrences", "retenu"})
            self.assertIn(e["priorite"], (1, 2, 3))
            self.assertNotIn(TIRET_CADRATIN, e["fr"])
            self.assertNotIn(DEMI_CADRATIN, e["fr"])


class TestFichier(unittest.TestCase):
    def setUp(self):
        tmp = tempfile.TemporaryDirectory()
        self.addCleanup(tmp.cleanup)
        self.dossier = Path(tmp.name) / "terminologie"

    def entree(self, fr, priorite=1, retenu=None):
        return {"fr": fr, "origine": ["ngramme"], "priorite": priorite, "pages": ["a/"], "occurrences": 2,
                "retenu": retenu}

    def test_ecrire_et_relire_par_langue(self):
        TM.ecrire_lexique("de", [self.entree("droit fiscal")], self.dossier)
        TM.ecrire_lexique("en", [self.entree("tax law")], self.dossier)
        self.assertEqual([e["fr"] for e in TM.charger_lexique("de", self.dossier)], ["droit fiscal"])
        self.assertEqual([e["fr"] for e in TM.charger_lexique("en", self.dossier)], ["tax law"])
        self.assertEqual(TM.charger_lexique("it", self.dossier), [])
        self.assertTrue((self.dossier / "lexique.json").is_file())

    def test_lexique_absent_donne_une_liste_vide(self):
        self.assertEqual(TM.charger_lexique("de", self.dossier), [])

    def test_decisions_de_fabien_conservees(self):
        ancien = [self.entree("droit fiscal", retenu=True), self.entree("taux maximal", retenu=False),
                  self.entree("autre", retenu=None)]
        nouveau = [self.entree("droit fiscal"), self.entree("taux maximal"), self.entree("autre"),
                   self.entree("inédit")]
        r = TM.conserver_decisions(nouveau, ancien)
        self.assertEqual({e["fr"]: e["retenu"] for e in r},
                         {"droit fiscal": True, "taux maximal": False, "autre": None, "inédit": None})

    def test_compter(self):
        entrees = [{**self.entree("a", 1), "origine": ["ngramme"]},
                   {**self.entree("b", 2), "origine": ["v1:termes-de", "segments-nouveaux"]},
                   {**self.entree("c", 3), "origine": ["v1:termes-de"]},
                   {**self.entree("d", 1), "origine": ["ngramme"]}]
        c = TM.compter(entrees)
        self.assertEqual(c["priorites"], {1: 2, 2: 1, 3: 1})
        self.assertEqual(c["origines"], {"ngramme": 2, "segments-nouveaux": 1, "v1:termes-de": 2})
        self.assertEqual(c["total"], 4)


class TestCommandeLexique(unittest.TestCase):
    def test_table_vide_avertit(self):
        """Vague finale, point 14 : lancer lexique sur une table vide le dit (tous les textes passeraient pour nouveaux)."""
        import contextlib
        import io
        from unittest import mock
        import build
        from outils.i18n import __main__ as cli
        if not (build.NEURON / "src/i18n/termes-de.json").is_file():
            self.skipTest("site V1 absent (NEURON_SRC)")
        with tempfile.TemporaryDirectory() as tmp:
            erreur, sortie = io.StringIO(), io.StringIO()
            with mock.patch.object(build, "DOSSIER_LANGUES", Path(tmp) / "langues"), \
                    mock.patch.object(TM, "candidats", lambda *a, **k: []), \
                    mock.patch.object(TM, "TERMINOLOGIE", Path(tmp) / "terminologie"), \
                    contextlib.redirect_stderr(erreur), contextlib.redirect_stdout(sortie):
                self.assertEqual(cli.main(["lexique", "de"]), 0)
            self.assertIn("table de vide", erreur.getvalue())
            self.assertIn("memoire de", erreur.getvalue())


class TestHorsDepot(unittest.TestCase):
    """Ruling 5 (décision V6) : rien de la terminologie dans le dépôt public."""

    def test_aucun_fichier_de_terminologie_suivi_par_git(self):
        r = subprocess.run(["git", "ls-files"], cwd=ICI, capture_output=True, text=True)
        if r.returncode != 0:
            self.skipTest("pas de dépôt git")
        suivis = [f for f in r.stdout.splitlines() if Path(f).name in ("lexique.json", "journal.jsonl", "glossaire.json")]
        self.assertEqual(suivis, [], "terminologie suivie par git : elle doit vivre dans la Bibliotheque")

    def test_dossier_par_defaut_hors_du_depot(self):
        env = {k: v for k, v in os.environ.items() if k != "NEURON_TERMINOLOGIE"}
        r = subprocess.run([sys.executable, "-c", "from outils.i18n import terminologie as t; print(t.TERMINOLOGIE)"],
                           cwd=ICI, env=env, capture_output=True, text=True)
        defaut = Path(r.stdout.strip())
        self.assertEqual(defaut.parts[-4:], ("07-Ressources-traduction", "Neuron", "site-v2", "terminologie"))
        self.assertIn("Bibliotheque-Claude", defaut.parts)
        self.assertNotIn(ICI, (defaut, *defaut.parents))

    def test_variable_d_environnement_surcharge(self):
        with tempfile.TemporaryDirectory() as tmp:
            r = subprocess.run([sys.executable, "-c", "from outils.i18n import terminologie as t; print(t.TERMINOLOGIE)"],
                               cwd=ICI, env={**os.environ, "NEURON_TERMINOLOGIE": tmp}, capture_output=True, text=True)
            self.assertEqual(Path(r.stdout.strip()), Path(tmp))


if __name__ == "__main__":
    unittest.main()
