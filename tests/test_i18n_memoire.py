"""Mémoire de traduction tirée de la V1 (tâche 3.1) : outils/i18n/memoire_v1.py, alignement des pages V1 et
pré-remplissage des tables DE, EN et IT au statut v1.

Les tests unitaires n'utilisent que des fixtures synthétiques (mini pages FR et DE écrites ici, mini dossier V1 dans un
dossier temporaire). Le test sur la V1 réelle est sauté si la source V1 (NEURON_SRC) est absente."""
import json
import tempfile
import unittest
from pathlib import Path

import build
from outils.i18n import memoire_v1 as M
from outils.i18n import segments as S
from outils.i18n import traduire as T
from outils.i18n.table import LANGUES, STATUTS, Table, cle


def doc(corps, titre="Titre", ld=None, lang="fr"):
    """Page complète minimale : tête (titre, description, JSON-LD facultatif), menu, main, pied."""
    script = f'<script type="application/ld+json">{json.dumps(ld, ensure_ascii=False)}</script>' if ld else ""
    return (f'<!DOCTYPE html>\n<html lang="{lang}"><head><meta charset="utf-8"><title>{titre}</title>'
            f'<meta name="description" content="Description {titre}">{script}</head><body>\n'
            f'<header class="nav"><a class="logo" href="/" aria-label="Accueil Neur.on">Neur.on</a></header>\n'
            f'<main id="main">{corps}</main>\n<footer class="footer"><p>Pied</p></footer>\n</body></html>')


FR = doc('<section class="hero"><h1>Traduction juridique</h1>'
         '<p>Lisez notre <a href="/fr/aide/">centre d\'aide</a> avant la démo.</p>'
         '<img src="a.png" alt="Capture de Corrext"></section>',
         titre="Accueil", ld={"@type": "WebPage", "name": "Accueil", "description": "Le site de Neur.on",
                              "inLanguage": "fr-CH"})
DE = doc('<section class="hero"><h1>Juristische Übersetzung</h1>'
         '<p>Lesen Sie vor der Demo unser <a href="/de/hilfe/">Hilfe-Center</a>.</p>'
         '<img src="a.png" alt="Bildschirm von Corrext"></section>',
         titre="Startseite", lang="de",
         ld={"@type": "WebPage", "name": "Startseite", "description": "Die Website von Neur.on", "inLanguage": "de-CH"})


def v1(dossier, pages, routes=None):
    """Mini dossier V1 : pages {chemin publié (fr/a/, de/a-de/…): HTML} et src/routes.json."""
    for chemin, html in pages.items():
        f = Path(dossier) / "docs" / chemin / "index.html"
        f.parent.mkdir(parents=True, exist_ok=True)
        f.write_text(html, encoding="utf-8")
    (Path(dossier) / "src").mkdir(exist_ok=True)
    (Path(dossier) / "src/routes.json").write_text(json.dumps(routes, ensure_ascii=False), encoding="utf-8")
    return Path(dossier)


class TestAlignement(unittest.TestCase):

    def test_aligne_structures_identiques(self):
        paires = M.aligner_page(FR, DE)
        self.assertIsNotNone(paires)
        self.assertIn(("Accueil", "Startseite"), paires)                                   # <title>
        self.assertIn(("Description Accueil", "Description Startseite"), paires)           # méta
        self.assertIn(("Le site de Neur.on", "Die Website von Neur.on"), paires)          # JSON-LD
        # name d'une WebPage de-CH : apparié par son chemin JSON, bien que l'extraction allemande ne le livre pas
        self.assertIn(("Traduction juridique", "Juristische Übersetzung"), paires)
        self.assertIn(("Lisez notre {1}centre d'aide{/1} avant la démo.",
                       "Lesen Sie vor der Demo unser {1}Hilfe-Center{/1}."), paires)       # marqueurs
        self.assertIn(("Capture de Corrext", "Bildschirm von Corrext"), paires)            # attribut
        self.assertIn(("Pied", "Pied"), paires)
        self.assertEqual(len(paires), 10)

    def test_refuse_structure_differente(self):
        # autre gabarit (ni menu, ni pied, ni méta) : moins de la moitié des unités FR trouvent leur place
        autre = ('<!DOCTYPE html>\n<html lang="de"><head><meta charset="utf-8"><title>Titel</title></head><body>\n'
                 "<main><h2>Eins</h2><ul><li>Zwei</li><li>Drei</li></ul><table><tr><td>Vier</td></tr></table></main>"
                 "</body></html>")
        self.assertIsNone(M.aligner_page(FR, autre))

    def test_marqueurs_differents_jamais_apparies(self):
        de = DE.replace('<a href="/de/hilfe/">Hilfe-Center</a>', "<strong>Hilfe-Center</strong>")
        detail = M.aligner_detail(FR, de)
        textes = [fr for fr, _, _ in detail["paires"]]
        self.assertNotIn("Lisez notre {1}centre d'aide{/1} avant la démo.", textes)
        self.assertIn("Traduction juridique", textes)

    def test_ecart_local_refuse_le_voisinage(self):
        # la V1 allemande a un élément de liste en moins : on ne sait pas lequel, aucun élément de la liste n'est apparié
        fr = doc("<h2>Liste</h2><ul><li>Un</li><li>Deux</li><li>Trois</li></ul><p>Fin</p>"
                 "<p class='x'>A</p><p class='x'>B</p><p class='x'>C</p><p class='x'>D</p>")
        de = doc("<h2>Liste DE</h2><ul><li>Eins</li><li>Drei</li></ul><p>Ende</p>"
                 "<p class='x'>A DE</p><p class='x'>B DE</p><p class='x'>C DE</p><p class='x'>D DE</p>", lang="de")
        detail = M.aligner_detail(fr, de)
        paires = {fr: tr for fr, tr, _ in detail["paires"]}
        self.assertEqual(paires["Liste"], "Liste DE")
        self.assertEqual(paires["Fin"], "Ende")
        for texte in ("Un", "Deux", "Trois"):
            self.assertNotIn(texte, paires)
        self.assertEqual(sorted(r["fr"] for r in detail["refus"]), ["Deux", "Trois", "Un"])

    def test_libelle_d_un_passage_fr_remplace(self):
        # glossaire de la V1 anglaise : l'exemple français (lang="fr") est remplacé par l'exemple anglais ; le libellé
        # « Français » face à « English » ne vaut pas pour la V2, qui garde l'exemple français
        fr = doc('<h2>Exemples</h2><div><i>Allemand</i><p lang="de">Der Gläubiger kann</p></div>'
                 '<div><i>Français</i><p lang="fr">Le créancier peut</p></div><p>Suite</p>')
        en = doc('<h2>Examples</h2><div><i>German</i><p lang="de">Der Gläubiger kann</p></div>'
                 '<div><i>English</i><p lang="en">A creditor may</p></div><p>Next</p>', lang="en")
        detail = M.aligner_detail(fr, en)
        paires = {f: t for f, t, _ in detail["paires"]}
        self.assertEqual(paires["{1}Allemand{/1}"], "{1}German{/1}")
        self.assertEqual(paires["Suite"], "Next")
        self.assertNotIn("{1}Français{/1}", paires)
        self.assertIn({"fr": "{1}Français{/1}", "cause": M.CAUSES["libelle"]}, detail["refus"])

    def test_cible_de_lien_differente_refusee(self):
        # glossaire EN de la V1 : la source citée a changé (Constitution au lieu de la LTF) ; la V2 garde la LTF
        fr = doc('<p>Source : Fedlex, <a href="https://www.fedlex.admin.ch/eli/cc/2006/218/fr">loi sur le Tribunal '
                 'fédéral</a></p><p>Voir <a href="https://www.fedlex.admin.ch/eli/cc/1999/404/fr">la Constitution</a></p>'
                 '<div class="sf">art. 1 LTF · source : Fedlex, loi sur le Tribunal fédéral</div>')
        en = doc('<p>Source: Fedlex, <a href="https://www.fedlex.admin.ch/eli/cc/1999/404/en">Federal Constitution</a>'
                 '</p><p>See <a href="https://www.fedlex.admin.ch/eli/cc/1999/404/en">the Constitution</a></p>'
                 '<div class="sf">Art. 1 Federal Supreme Court Act · source: Fedlex, Federal Constitution</div>', lang="en")
        detail = M.aligner_detail(fr, en)
        paires = {f: t for f, t, _ in detail["paires"]}
        self.assertNotIn("Source : Fedlex, {1}loi sur le Tribunal fédéral{/1}", paires)
        self.assertIn({"fr": "Source : Fedlex, {1}loi sur le Tribunal fédéral{/1}", "cause": M.CAUSES["cible"]},
                      detail["refus"])
        # sans lien, le même nom de source sur la page est refusé aussi
        self.assertNotIn("art. 1 LTF · source : Fedlex, loi sur le Tribunal fédéral", paires)
        self.assertIn({"fr": "art. 1 LTF · source : Fedlex, loi sur le Tribunal fédéral",
                       "cause": M.CAUSES["meme_source"]}, detail["refus"])
        # même adresse au segment de langue près (/fr ↔ /en) : appariée
        self.assertEqual(paires["Voir {1}la Constitution{/1}"], "See {1}the Constitution{/1}")

    def test_json_traduit_illisible_refuse(self):
        fr = doc("<p>Texte</p>", ld={"@type": "WebPage", "description": "Une description"})
        tr = fr.replace('{"@type": "WebPage", "description": "Une description"}', '{"@type": "WebPage", "description": ')
        unites = [u for u in S.extraire_page(fr) if u["genre"] == "ld"]
        paires, refus = M._apparier_donnees(fr, tr, unites)
        self.assertEqual(paires, [])
        self.assertEqual([c for _, c in refus], ["ld_illisible"])

    def test_passage_lang_fr_jamais_apparie(self):
        fr = doc('<p>Exemple :</p><p lang="fr">Le contrat est résilié.</p>')
        de = doc('<p>Beispiel:</p><p lang="fr">Le contrat est résilié.</p>', lang="de")
        paires = dict(M.aligner_page(fr, de))
        self.assertEqual(paires["Exemple :"], "Beispiel:")
        self.assertNotIn("Le contrat est résilié.", paires)


class TestPrefill(unittest.TestCase):

    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.dossier = Path(self.tmp.name)

    def table(self):
        return Table("de", self.dossier / "tables")

    def test_pose_v1_avec_source(self):
        neuron = v1(self.dossier / "v1", {"fr/a/": FR, "de/a-de/": DE},
                    {"fr/a/": {"de": "de/a-de/", "en": "en/a/", "it": "it/a/"}})
        t = self.table()
        r = M.prefill("de", neuron, t, pages={})
        self.assertEqual(r["pages_alignees"], 1)
        self.assertEqual(t.chercher("Traduction juridique", "a/"),
                         {"fr": "Traduction juridique", "trad": "Juristische Übersetzung", "statut": "v1",
                          "source": "V1 de/a-de/"})
        # traduction identique au français : statut v1 aussi (validée par les traducteurs), pour sa page seulement
        self.assertEqual(t.chercher("Pied", "a/")["statut"], "v1")
        self.assertIsNone(t.chercher("Pied", "autre/"))
        self.assertEqual(r["segments_v1"] + r["par_page_seulement"], len(t.entrees))

    def test_doublons_divergents_en_par_page(self):
        pa = doc("<p>Allemand</p><p>Contrat</p>")
        pb = doc("<p>Allemand</p><p>Contrat</p>")
        neuron = v1(self.dossier / "v1",
                    {"fr/a/": pa, "de/a-de/": pa.replace("Allemand", "Deutsch").replace("Contrat", "Vertrag"),
                     "fr/b/": pb, "de/b-de/": pb.replace("Allemand", "Deutsch (Sprache)").replace("Contrat", "Vertrag")},
                    {"fr/a/": {"de": "de/a-de/"}, "fr/b/": {"de": "de/b-de/"}})
        t = self.table()
        r = M.prefill("de", neuron, t, pages={})
        self.assertEqual(t.chercher("Allemand", "a/"),
                         {"fr": "Allemand", "trad": "Deutsch", "statut": "v1", "source": "V1 de/a-de/"})
        self.assertEqual(t.chercher("Allemand", "b/"),
                         {"fr": "Allemand", "trad": "Deutsch (Sprache)", "statut": "v1", "source": "V1 de/b-de/"})
        # Ruling 21 : aucune traduction par défaut pour un doublon divergent ; ailleurs, circuit normal
        self.assertIsNone(t.chercher("Allemand", "autre/"))
        self.assertIsNone(t.entrees[cle("Allemand")]["trad"])
        self.assertEqual(r["doublons_divergents"],
                         [{"fr": "Allemand", "trads": ["Deutsch", "Deutsch (Sprache)"], "pages": ["a/", "b/"]}])
        self.assertEqual(t.chercher("Contrat", "b/")["source"], "V1 de/a-de/")  # même traduction : pas de par_page

    def test_divergence_dans_une_meme_page_jamais_posee(self):
        # même texte FR, deux traductions sur la même page (libellé et valeur) : impossible de dire laquelle va où
        fr = doc("<p>Allemand</p><p>Texte</p><p class='v'>Allemand</p>")
        de = doc("<p>Deutsch</p><p>Text</p><p class='v'>Deutsch (Sprache)</p>", lang="de")
        neuron = v1(self.dossier / "v1", {"fr/a/": fr, "de/a-de/": de}, {"fr/a/": {"de": "de/a-de/"}})
        t = self.table()
        r = M.prefill("de", neuron, t, pages={})
        self.assertIsNone(t.chercher("Allemand", "a/"))
        self.assertEqual(t.chercher("Texte", "a/")["trad"], "Text")
        self.assertIn("divergence dans une même page", r["refus"])

    def test_ne_remplace_jamais_invariant(self):
        neuron = v1(self.dossier / "v1", {"fr/a/": FR, "de/a-de/": DE}, {"fr/a/": {"de": "de/a-de/"}})
        t = self.table()
        t.poser("Traduction juridique", "Traduction juridique", "invariant", "relu par X, identique au français")
        t.poser("Pied", "Fusszeile", "relu", "relecteur", page="a/", sans_defaut=True)
        r = M.prefill("de", neuron, t, pages={})
        self.assertEqual(t.chercher("Traduction juridique", "a/")["statut"], "invariant")
        self.assertEqual(t.chercher("Pied", "a/")["trad"], "Fusszeile")  # traduction de page relue gardée
        self.assertIn(M.CAUSES["relu"], r["refus"])

    def test_ne_remplace_jamais_relu(self):
        neuron = v1(self.dossier / "v1", {"fr/a/": FR, "de/a-de/": DE}, {"fr/a/": {"de": "de/a-de/"}})
        t = self.table()
        t.poser("Traduction juridique", "Rechtsübersetzung", "relu", "relu par un traducteur")
        t.poser("Accueil", "Startseite", "mt", "LexMachina")
        M.prefill("de", neuron, t, pages={})
        self.assertEqual(t.chercher("Traduction juridique", "a/"),
                         {"fr": "Traduction juridique", "trad": "Rechtsübersetzung", "statut": "relu",
                          "source": "relu par un traducteur"})
        self.assertEqual(t.chercher("Accueil", "a/")["statut"], "v1")  # une sortie brute est remplacée

    def test_relance_sans_paire_perimee(self):
        # une paire posée par une mémoire précédente et que l'alignement ne donne plus disparaît ; le reste est gardé
        neuron = v1(self.dossier / "v1", {"fr/a/": FR, "de/a-de/": DE}, {"fr/a/": {"de": "de/a-de/"}})
        t = self.table()
        t.poser("Ancien texte", "Alter Text", "v1", "V1 de/ancien/")
        t.poser("Allemand", "Deutsch", "v1", "V1 de/a-de/")
        t.poser("Allemand", "Französisch", "v1", "V1 de/b-de/", page="b/")
        t.poser("Texte relu", "Geprüfter Text", "relu", "relu par un traducteur")
        M.prefill("de", neuron, t, pages={})
        self.assertIsNone(t.chercher("Ancien texte", "a/"))
        self.assertIsNone(t.chercher("Allemand", "b/"))
        self.assertEqual(t.chercher("Texte relu", "a/")["statut"], "relu")
        self.assertEqual(t.chercher("Traduction juridique", "a/")["statut"], "v1")

    def test_relance_retire_le_defaut_perime_garde_la_page_relue(self):
        neuron = v1(self.dossier / "v1", {"fr/a/": FR, "de/a-de/": DE}, {"fr/a/": {"de": "de/a-de/"}})
        t = self.table()
        t.poser("Ancien texte", "Alter Text", "v1", "V1 de/ancien/")
        t.poser("Ancien texte", "Geprüft", "relu", "relecteur", page="b/")
        M.prefill("de", neuron, t, pages={})
        self.assertIsNone(t.chercher("Ancien texte", "a/"))          # défaut v1 périmé retiré
        self.assertEqual(t.chercher("Ancien texte", "b/")["trad"], "Geprüft")

    def test_permutation_jamais_posee(self):
        # la V1 allemande met la colonne allemande en premier : chaque cellule fait face à celle d'une autre langue
        tableau = "<table><tr><th>Texte</th><th>{}</th><th>{}</th></tr><tr><td>Code</td><td>{}</td><td>{}</td></tr></table>"
        pa = doc("<p>Allemand</p><p>Français</p><p>OR</p><p>CO</p>")
        fr_b = doc(tableau.format("Français", "Allemand", "CO", "OR"))
        de_b = doc(tableau.format("Deutsch", "Französisch", "OR", "CO").replace("Texte", "Erlass").replace(
            "<td>Code</td>", "<td>Gesetz</td>"), lang="de")
        de_a = doc("<p>Deutsch</p><p>Französisch</p><p>OR</p><p>CO</p>", lang="de")
        # deux pages normales (a, c) : avec une seule, on ne saurait pas laquelle des deux pages est permutée
        neuron = v1(self.dossier / "v1",
                    {"fr/a/": pa, "de/a-de/": de_a, "fr/c/": pa, "de/c-de/": de_a, "fr/b/": fr_b, "de/b-de/": de_b},
                    {"fr/a/": {"de": "de/a-de/"}, "fr/b/": {"de": "de/b-de/"}, "fr/c/": {"de": "de/c-de/"}})
        t = self.table()
        r = M.prefill("de", neuron, t, pages={})
        for texte, attendu in (("Allemand", "Deutsch"), ("Français", "Französisch")):
            with self.subTest(texte=texte):
                self.assertEqual(t.chercher(texte, "b/")["trad"], attendu)
        # « OR » et « CO » gardés tels quels : posés pour les pages a et c seulement (Ruling 19), pas pour la page permutée
        for texte in ("OR", "CO"):
            with self.subTest(texte=texte):
                self.assertEqual(t.chercher(texte, "a/")["trad"], texte)
                self.assertIsNone(t.chercher(texte, "b/"))
        self.assertEqual(t.chercher("Texte", "b/")["trad"], "Erlass")
        self.assertEqual(r["refus"]["permutation probable dans la page"]["unites"], 4)
        self.assertEqual(r["doublons_divergents"], [])

    def test_identique_dans_les_donnees_structurees_refuse(self):
        # les données structurées n'ont pas été relues : un texte resté en français n'y vaut pas validation ; une marque
        # (invariant) reste posée
        ld_fr = {"@type": "SoftwareApplication", "name": "Corrext", "featureList": ["Gestion de projet"]}
        fr = doc("<p>Texte</p>", ld=ld_fr)
        de = doc("<p>Text</p>", ld=ld_fr, lang="de")
        neuron = v1(self.dossier / "v1", {"fr/a/": fr, "de/a-de/": de}, {"fr/a/": {"de": "de/a-de/"}})
        t = self.table()
        r = M.prefill("de", neuron, t, pages={})
        self.assertIsNone(t.chercher("Gestion de projet", "a/"))
        self.assertEqual(t.chercher("Corrext", "a/")["trad"], "Corrext")
        self.assertEqual(r["refus"][M.CAUSES["ld_identique"]]["unites"], 1)

    def test_identique_traduit_ailleurs_refuse(self):
        # resté en français sur la page a, traduit sur la page b : la page a prend la traduction, jamais le français
        neuron = v1(self.dossier / "v1",
                    {"fr/a/": doc("<p>Projets</p>"), "de/a-de/": doc("<p>Projets</p>", lang="de"),
                     "fr/b/": doc("<p>Projets</p>"), "de/b-de/": doc("<p>Projekte</p>", lang="de")},
                    {"fr/a/": {"de": "de/a-de/"}, "fr/b/": {"de": "de/b-de/"}})
        t = self.table()
        r = M.prefill("de", neuron, t, pages={})
        self.assertEqual(t.chercher("Projets", "a/"),
                         {"fr": "Projets", "trad": "Projekte", "statut": "v1", "source": "V1 de/b-de/"})
        self.assertEqual(r["doublons_divergents"], [])
        self.assertIn(M.CAUSES["identique_traduit"], r["refus"])

    def test_identique_pose_pour_sa_page_seulement(self):
        # Ruling 19 : un terme FR gardé tel quel par la V1 (colonne française d'un tableau) n'est accepté en français
        # que sur sa page ; une marque (invariant) reste globale
        fr = doc("<table><tr><td>Handelsregister</td><td>registre du commerce</td></tr></table><p>Corrext</p>")
        neuron = v1(self.dossier / "v1", {"fr/a/": fr, "de/a-de/": fr.replace('lang="fr"', 'lang="de"')},
                    {"fr/a/": {"de": "de/a-de/"}})
        t = self.table()
        r = M.prefill("de", neuron, t, pages={})
        v2 = doc("<p>registre du commerce</p><p>Corrext</p>")
        # (a) accepté sur sa page d'origine
        self.assertEqual(t.chercher("registre du commerce", "a/")["statut"], "v1")
        manquants_a = T.analyser(v2, "a/", "de", t, "apercu")["manquants"]
        self.assertNotIn("registre du commerce", [m["fr"] for m in manquants_a])
        # (b) manquant sur une autre page qui le contient comme texte à traduire
        self.assertIsNone(t.chercher("registre du commerce", "b/"))
        manquants_b = T.analyser(v2, "b/", "de", t, "apercu")["manquants"]
        self.assertIn({"cle": cle("registre du commerce"), "fr": "registre du commerce", "statut": None,
                       "raison": "absent"}, manquants_b)
        # (c) un invariant identique reste global
        self.assertEqual(t.chercher("Corrext", "b/")["trad"], "Corrext")
        self.assertNotIn("Corrext", [m["fr"] for m in manquants_b])
        for texte in ("registre du commerce", "Handelsregister", "Pied"):  # identiques, non invariants
            self.assertIsNone(t.entrees[cle(texte)]["trad"], texte)
        self.assertEqual(r["par_page_seulement"], sum(1 for e in t.entrees.values() if e["trad"] is None))

    def test_controles_refus_signales(self):
        # « ß » sans ß en français : refusé par Table.poser, compté dans le rapport, jamais contourné
        fr = doc("<p>Rue principale</p><p>Texte</p>")
        de = doc("<p>Hauptstraße</p><p>Text</p>", lang="de")
        neuron = v1(self.dossier / "v1", {"fr/a/": fr, "de/a-de/": de}, {"fr/a/": {"de": "de/a-de/"}})
        t = self.table()
        r = M.prefill("de", neuron, t, pages={})
        self.assertIsNone(t.chercher("Rue principale", "a/"))
        self.assertEqual(t.chercher("Texte", "a/")["trad"], "Text")
        self.assertTrue(any(c.startswith("contrôle") for c in r["refus"]))

    def test_page_traduite_illisible_signalee(self):
        de = DE.replace('"inLanguage": "de-CH"}', '"inLanguage": ')
        neuron = v1(self.dossier / "v1", {"fr/a/": FR, "de/a-de/": de}, {"fr/a/": {"de": "de/a-de/"}})
        r = M.prefill("de", neuron, self.table(), pages={})
        self.assertEqual(r["pages_alignees"], 0)
        self.assertEqual(r["pages_non_alignees"][0]["page"], "a/")
        self.assertIn("illisible", r["pages_non_alignees"][0]["cause"])

    def test_page_absente_signalee(self):
        neuron = v1(self.dossier / "v1", {"fr/a/": FR}, {"fr/a/": {"de": "de/a-de/"}})
        r = M.prefill("de", neuron, self.table(), pages={})
        self.assertEqual(r["pages_alignees"], 0)
        self.assertEqual(r["pages_non_alignees"], [{"page": "a/", "cause": "page V1 absente"}])

    def test_couverture_des_mots_du_main(self):
        neuron = v1(self.dossier / "v1", {"fr/a/": FR, "de/a-de/": DE}, {"fr/a/": {"de": "de/a-de/"}})
        v2 = doc("<h1>Traduction juridique</h1><p>Un texte nouveau ici</p>")
        r = M.prefill("de", neuron, self.table(), pages={"a/": v2})
        # main : « Traduction juridique » (2 mots, couvert) et « Un texte nouveau ici » (4 mots)
        self.assertAlmostEqual(r["couverture_mots"], round(100 * 2 / 6, 1))

    def test_couverture_texte_ignore_les_balises(self):
        # définition de l'audit : un passage dont seul le balisage a changé compte comme retrouvé, pas pour traduire
        neuron = v1(self.dossier / "v1", {"fr/a/": FR, "de/a-de/": DE}, {"fr/a/": {"de": "de/a-de/"}})
        v2 = doc("<h1><em>Traduction juridique</em></h1><p>Un texte nouveau ici</p>")
        r = M.prefill("de", neuron, self.table(), pages={"a/": v2})
        self.assertEqual(r["couverture_mots"], 0.0)
        self.assertAlmostEqual(r["couverture_texte"], round(100 * 2 / 6, 1))


class TestTablesProduites(unittest.TestCase):
    """Tables commitées (src/langues/<l>/segments.json, produites par « python3 -m outils.i18n memoire <l> ») : aucun
    tiret cadratin ni demi-cadratin, aucun « ß » qui ne soit déjà dans le français, statuts connus."""

    def test_tables_propres(self):
        for langue in LANGUES:
            fichier = build.DOSSIER_LANGUES / langue / "segments.json"
            if not fichier.is_file():
                continue
            texte = fichier.read_text(encoding="utf-8")
            with self.subTest(langue=langue):
                self.assertNotIn(chr(0x2014), texte)
                self.assertNotIn(chr(0x2013), texte)
                for e in json.loads(texte).values():
                    if e["trad"] is None:  # entrée par page seulement (Ruling 19)
                        self.assertEqual((e["statut"], e["source"]), (None, None))
                        self.assertTrue(e["par_page"])
                    for v in ([e] if e["trad"] is not None else []) + list(e["par_page"].values()):
                        self.assertIn(v["statut"], STATUTS)
                        if v["trad"] == e["fr"]:
                            # Ruling 19 : traduction identique par défaut seulement pour un invariant
                            self.assertTrue(v is not e or Table.est_invariant(e["fr"]), e["fr"])
                        if "ß" in v["trad"]:
                            self.assertIn("ß", e["fr"], v["trad"])


@unittest.skipUnless((build.NEURON / "src/routes.json").is_file(), "source V1 absente (NEURON_SRC)")
class TestV1Reelle(unittest.TestCase):

    def test_v1_reelle(self):
        for langue in ("de", "en", "it"):
            with self.subTest(langue=langue), tempfile.TemporaryDirectory() as tmp:
                t = Table(langue, tmp)
                # pages V2 assemblées pour la langue mesurée (comme la commande memoire)
                r = M.prefill(langue, build.NEURON, t, pages=T.pages_assemblees(langue, "apercu"))
                self.assertEqual(r["pages_alignees"], 156, r["pages_non_alignees"])
                self.assertEqual(r["pages_non_alignees"], [])
                # même ordre que l'audit (84,6 % des mots retrouvés dans la V1, § 1, balises ignorées), à 5 points près
                self.assertLess(abs(r["couverture_texte"] - 84.6), 5, r["couverture_texte"])
                # couverture utilisable (marqueurs compris) : au plus celle de l'audit
                self.assertLessEqual(r["couverture_mots"], r["couverture_texte"])
                for e in t.entrees.values():
                    self.assertTrue(all(v["statut"] == "v1" for v in e["par_page"].values()))
                    if e["trad"] is None:  # par page seulement (Ruling 19)
                        self.assertTrue(e["par_page"])
                    else:
                        self.assertEqual(e["statut"], "v1")
                        if " ".join(e["trad"].split()) == e["fr"]:
                            self.assertTrue(Table.est_invariant(e["fr"]), e["fr"])


if __name__ == "__main__":
    unittest.main()
