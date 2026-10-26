"""Traduction de la page assemblée et pages publiables (tâche 2.3) : outils/i18n/traduire.py et son branchement dans
build.py (passe 2), commande d'état.

Les tables des tests sont synthétiques : la fixture tests/fixtures/i18n/segments-de.json (traduction allemande de la
fixture de la tâche 2.1, écrite pour les tests) ou des tables « DE <texte FR> » tirées des pages assemblées."""
import contextlib
import html as H
import io
import json
import re
import tempfile
import unittest
from pathlib import Path
from unittest import mock

import build
from tests import support
from outils import llms
from outils.i18n import controles, empreintes, traduire as T
from outils.i18n import segments as S
from outils.i18n.table import Table, cle

FIXTURES = Path(__file__).resolve().parent / "fixtures" / "i18n"
PAGE = (FIXTURES / "page-fr-assemblee.html").read_text(encoding="utf-8")
ABSENT = FIXTURES / "absent"  # dossier inexistant : Table vide
BANDEAU_DE = "Arbeitsversion, Übersetzung nicht geprüft"


def table_fixture():
    """Table allemande qui traduit entièrement la fixture de la tâche 2.1 (statut relu, ou invariant si identique)."""
    t = Table("de", ABSENT)
    t.entrees = json.loads((FIXTURES / "segments-de.json").read_text(encoding="utf-8"))
    return t


def doc(corps, tete=""):
    return f'<!DOCTYPE html>\n<html lang="fr"><head><meta charset="utf-8">{tete}</head><body>\n{corps}</body></html>'


def milliers_suisses(texte):
    """15 000 devient 15'000 : la traduction factice respecte la règle des milliers (bloquante en production)."""
    return controles._MILLIERS.sub(lambda m: re.sub(r"\s", "'", m.group(0)), texte)


def pseudo(table, html, statut="relu"):
    """Pose « DE <texte FR> » pour chaque texte à traduire de la page (hors lang="fr", invariants et avis fictifs), milliers
    à l'apostrophe."""
    for u in S.extraire_page(T.retirer_avis_fictifs(html)):
        if not u["lang_fr"] and not T._invariant(u["texte"], table.langue):
            table.poser(u["texte"], "DE " + milliers_suisses(u["texte"]), statut, "test")
    return table


def libelles(table, statut="relu"):
    """Libellés fixes : llms.txt (« Quelle: » pour la source) et bandeau de l'aperçu."""
    for texte in llms.libelles_fixes():
        table.poser(texte, "Quelle:" if texte == llms.SOURCE else "DE " + texte, statut, "test")
    table.poser(T.LIBELLE_BANDEAU, BANDEAU_DE, statut, "test")
    return table


def assemblees(pages, apercu=True):
    """Pages françaises assemblées que TRADUIRE reçoit (404 comprise), pour un build fr+de des pages données."""
    vues = {}

    def enregistrer(html, page, langue):
        vues[page] = html
        return html, []
    with tempfile.TemporaryDirectory() as tmp:
        support.construire(tmp, pages=pages, config={"apercu": apercu}, langues=("fr", "de"),
                           patches=[mock.patch.object(build, "TRADUIRE", enregistrer),
                                    mock.patch.object(build, "LIBELLES", lambda langue: ((lambda s: s), []))])
    return vues


def table_complete(dossier, pages, statut="relu", apercu=True, avec_libelles=True, sauf=(), deux_modes=False):
    """Table allemande écrite dans <dossier>/de/segments.json, qui traduit les pages données et leur 404 (« DE <texte> »),
    plus les libellés fixes ; sauf : clés de page laissées sans traduction ; deux_modes : les pages des deux modes (textes
    de l'aperçu et de la production, comme la chaîne les liste : traduire.pages_union)."""
    t = Table("de", dossier)
    for mode in ((True, False) if deux_modes else (apercu,)):
        for page, html in assemblees(pages, mode).items():
            if page not in sauf:
                pseudo(t, html, statut)
    if avec_libelles:
        libelles(t, statut)
    t.enregistrer()
    return t


class TestTraduire(unittest.TestCase):
    def test_page_entierement_traduite(self):
        for mode in ("apercu", "production"):
            html, manquants = T.traduire(PAGE, "contact/", "de", table_fixture(), mode)
            self.assertEqual(manquants, [], mode)
            self.assertIn("Demo anfragen", html)
            self.assertIn("Fragen Sie eine Demo an.", html)
            self.assertEqual(controles.restes_fr(html, "de"), [])
            self.assertNotIn("bandeau-travail", html)  # tout est relu ou invariant

    def test_segment_manquant_bloque_la_page(self):
        t = table_fixture()
        del t.entrees[next(k for k, e in t.entrees.items() if e["fr"] == "Ce champ est obligatoire.")]
        html, manquants = T.traduire(PAGE, "contact/", "de", t, "apercu")
        self.assertEqual(html, "")
        self.assertEqual([(m["fr"], m["raison"], m["statut"]) for m in manquants], [("Ce champ est obligatoire.", "absent", None)])
        self.assertEqual(set(manquants[0]), {"cle", "fr", "statut", "raison"})

    def test_statut_mt_refuse_partout(self):
        t = table_fixture()
        t.poser("Ce champ est obligatoire.", "Dieses Feld ist ein Pflichtfeld.", "mt", "LexMachina")
        for mode in ("apercu", "production"):
            html, manquants = T.traduire(PAGE, "contact/", "de", t, mode)
            self.assertEqual(html, "", mode)
            self.assertEqual([(m["raison"], m["statut"]) for m in manquants], [("statut", "mt")], mode)

    def test_adapte_accepte_en_apercu_seulement(self):
        t = table_fixture()
        t.poser("Ce champ est obligatoire.", "Dieses Feld ist ein Pflichtfeld.", "adapte", "adaptation")
        t.poser(T.LIBELLE_BANDEAU, BANDEAU_DE, "relu", "test")
        html, manquants = T.traduire(PAGE, "contact/", "de", t, "apercu")
        self.assertEqual(manquants, [])
        self.assertIn('data-requis="Dieses Feld ist ein Pflichtfeld."', html)
        html, manquants = T.traduire(PAGE, "contact/", "de", t, "production")
        self.assertEqual(html, "")
        self.assertEqual([(m["raison"], m["statut"]) for m in manquants], [("statut", "adapte")])

    def test_controles_de_segment_en_production(self):
        """Vague finale, point 5 : en production, une traduction relue à défaut bloquant (milliers) rend la page non
        publiable (raison « controles ») ; la même, V1 validée passée relue sans changement (champ « v1 »), est
        exemptée (Ruling 30) ; l'aperçu ne la bloque pas."""
        t = table_fixture()
        fr = "Ce champ est obligatoire."
        t.poser(fr, "Pflichtfeld, 15 000 Zeichen", "relu", "relu par Alice")
        _, manquants = T.traduire(PAGE, "contact/", "de", t, "production")
        self.assertEqual([(m["fr"], m["raison"]) for m in manquants], [(fr, "controles")])
        t.poser(T.LIBELLE_BANDEAU, BANDEAU_DE, "relu", "test")
        self.assertEqual(T.traduire(PAGE, "contact/", "de", t, "apercu")[1], [])
        t.poser(fr, "Pflichtfeld, 15 000 Zeichen", "relu", "V1 de/ ; relu par Alice", v1=True)
        self.assertEqual(T.traduire(PAGE, "contact/", "de", t, "production")[1], [])

    def test_marqueurs_restaures(self):
        h = doc('<p><a href="{{ROOT}}contact/">Démo</a> à demander</p>\n')
        t = Table("de", ABSENT)
        t.poser("{1}Démo{/1} à demander", "{1}Demo{/1} anfragen", "relu", "test")
        html, manquants = T.traduire(h, "", "de", t, "production")
        self.assertEqual(manquants, [])
        self.assertIn('<p><a href="{{ROOT}}contact/">Demo</a> anfragen</p>', html)

    def test_marqueur_perdu(self):
        h = doc('<p><a href="{{ROOT}}contact/">Démo</a> à demander</p>\n')
        t = Table("de", ABSENT)
        t.poser("{1}Démo{/1} à demander", "{1}Demo anfragen", "relu", "test")
        html, manquants = T.traduire(h, "", "de", t, "production")
        self.assertEqual(html, "")
        self.assertEqual([(m["fr"], m["raison"]) for m in manquants], [("{1}Démo{/1} à demander", "balisage")])

    def test_texte_fr_modifie_apres_traduction(self):
        modifiee = PAGE.replace("Nous vous répondons sous 24 h.", "Nous vous répondons sous 48 h.")
        self.assertNotEqual(modifiee, PAGE)
        html, manquants = T.traduire(modifiee, "contact/", "de", table_fixture(), "apercu")
        self.assertEqual(html, "")
        self.assertEqual([(m["fr"], m["raison"]) for m in manquants], [("Nous vous répondons sous 48 h.", "absent")])

    def test_lang_fr_jamais_traduit_ni_manquant(self):
        """Ruling 14 : une unité sous lang="fr" explicite garde le français, même si la table a une entrée pour ce texte."""
        h = doc('<div lang="fr"><p>Le débiteur en demeure doit des intérêts moratoires.</p></div><p>Bonjour</p>\n')
        t = Table("de", ABSENT)
        t.poser("Bonjour", "Guten Tag", "relu", "test")
        html, manquants = T.traduire(h, "", "de", t, "production")
        self.assertEqual(manquants, [])
        self.assertIn("<p>Le débiteur en demeure doit des intérêts moratoires.</p>", html)
        t.poser("Le débiteur en demeure doit des intérêts moratoires.", "Der Schuldner schuldet Verzugszins.", "relu", "test")
        self.assertEqual(T.traduire(h, "", "de", t, "production")[0], html)

    def test_traduction_propre_a_la_page(self):
        """par_page utilise la clé de page de build.PAGES (« contact/ »)."""
        h = doc("<p>Contact</p>\n")
        t = Table("de", ABSENT)
        t.poser("Contact", "Kontakt", "relu", "test")
        t.poser("Contact", "Kontaktieren Sie uns", "relu", "test", page="contact/")
        self.assertIn("<p>Kontaktieren Sie uns</p>", T.traduire(h, "contact/", "de", t, "production")[0])
        self.assertIn("<p>Kontakt</p>", T.traduire(h, "", "de", t, "production")[0])

    def test_invariants_sans_entree(self):
        # un nombre seul n'est jamais un segment (aucune lettre) : « CHnell 15 000 » est un invariant (marque et nombre)
        h = doc("<p>Neur.on</p><p>team@corrext.com</p><p>CHnell 15 000</p>\n")
        html, manquants = T.traduire(h, "", "en", Table("en", ABSENT), "production")
        self.assertEqual(manquants, [])
        self.assertIn("<p>CHnell 15 000</p>", html)
        # en allemand, un nombre aux milliers séparés par une espace doit être traduit (15'000)
        html, manquants = T.traduire(h, "", "de", Table("de", ABSENT), "production")
        self.assertEqual([(m["fr"], m["raison"]) for m in manquants], [("CHnell 15 000", "absent")])

    def test_mode_inconnu(self):
        with self.assertRaises(ValueError):
            T.traduire(PAGE, "contact/", "de", table_fixture(), "brouillon")


class TestExhaustivite(unittest.TestCase):
    """Ruling 3 : la page traduite, ré-extraite, ne garde aucun texte français de la page d'origine sans que ce soit voulu."""
    H = doc('<p>Bonjour</p><img src="x.png" alt="Schéma du flux de traduction">\n',
            tete='<meta name="description" content="Une description de la page.">')

    def table(self, statut_alt="relu", trad_alt="Schéma du flux de traduction", statut_meta="relu", trad_meta="Seitenbeschreibung."):
        t = Table("de", ABSENT)
        t.poser("Bonjour", "Guten Tag", "relu", "test")
        t.poser("Schéma du flux de traduction", trad_alt, statut_alt, "test")
        t.poser("Une description de la page.", trad_meta, statut_meta, "test")
        return t

    def test_attribut_alt_non_traduit(self):
        html, manquants = T.traduire(self.H, "", "de", self.table(), "production")
        self.assertEqual(html, "")
        self.assertEqual([(m["fr"], m["raison"], m["statut"]) for m in manquants],
                         [("Schéma du flux de traduction", "exhaustivite", "relu")])

    def test_meta_non_traduite(self):
        t = self.table(trad_alt="Schema des Übersetzungsablaufs", trad_meta="Une description de la page.")
        html, manquants = T.traduire(self.H, "", "de", t, "production")
        self.assertEqual([(m["fr"], m["raison"]) for m in manquants], [("Une description de la page.", "exhaustivite")])

    def test_identique_voulu_invariant_ou_v1(self):
        for statut in ("invariant", "v1"):
            html, manquants = T.traduire(self.H, "", "de", self.table(statut_alt=statut), "production")
            self.assertEqual(manquants, [], statut)
            self.assertIn('alt="Schéma du flux de traduction"', html)

    def test_libelle_identique_relu_refuse(self):
        t = Table("en", ABSENT)
        t.poser("Contact", "Contact", "relu", "test")
        self.assertEqual(T.libelle(t, "Contact", "production")[1]["raison"], "exhaustivite")
        t.poser("Contact", "Contact", "invariant", "test")
        self.assertEqual(T.libelle(t, "Contact", "production"), ("Contact", None))


class TestBandeau(unittest.TestCase):
    """Ruling 2 : bandeau « Version de travail, traduction non relue » en aperçu, sur une page qui contient au moins une
    traduction hors {v1, invariant, relu} ; jamais en production, jamais sur une page entièrement relue."""

    def table(self, statut="adapte", bandeau=True):
        t = table_fixture()
        t.poser("Ce champ est obligatoire.", "Dieses Feld ist ein Pflichtfeld.", statut, "test")
        if bandeau:
            t.poser(T.LIBELLE_BANDEAU, BANDEAU_DE, "adapte", "test")
        return t

    def test_bandeau_apres_body_en_apercu(self):
        html, manquants = T.traduire(PAGE, "contact/", "de", self.table(), "apercu")
        self.assertEqual(manquants, [])
        self.assertEqual(html.count("bandeau-travail"), 1)
        self.assertIn('<body>\n<div class="bandeau-travail" role="note">' + BANDEAU_DE + "</div>\n", html)

    def test_aucun_bandeau_sur_une_page_relue(self):
        for statut in ("relu", "v1", "invariant"):
            html, _ = T.traduire(PAGE, "contact/", "de", self.table(statut), "apercu")
            self.assertTrue(html)
            self.assertNotIn("bandeau-travail", html, statut)

    def test_jamais_en_production(self):
        html, _ = T.traduire(PAGE, "contact/", "de", self.table("relu"), "production")
        self.assertTrue(html)
        self.assertNotIn("bandeau-travail", html)
        self.assertEqual(T.traduire(PAGE, "contact/", "de", self.table("adapte"), "production")[0], "")

    def test_libelle_du_bandeau_manquant(self):
        html, manquants = T.traduire(PAGE, "contact/", "de", self.table(bandeau=False), "apercu")
        self.assertEqual(html, "")
        self.assertEqual([(m["fr"], m["raison"]) for m in manquants], [(T.LIBELLE_BANDEAU, "absent")])

    def test_body_a_attributs_ou_introuvable(self):
        """Vague finale, point 8 : <body> à attributs reçoit le bandeau ; sans <body>, ValueError (jamais de page non
        relue publiée sans son bandeau)."""
        page = PAGE.replace("<body>", '<body class="x">', 1)
        html, _ = T.traduire(page, "contact/", "de", self.table(), "apercu")
        self.assertIn('<body class="x">\n<div class="bandeau-travail" role="note">' + BANDEAU_DE + "</div>\n", html)
        with self.assertRaises(ValueError) as e:
            T.traduire(re.sub(r"</?body[^>]*>", "", PAGE), "contact/", "de", self.table(), "apercu")
        self.assertIn("<body>", str(e.exception))

    def test_libelle_du_bandeau_liste_par_etat_des_le_premier_tour(self):
        """Vague finale, point 8 : etat (aperçu) a une ligne « bandeau » et met le libellé dans a_traduire, même quand
        aucune page n'est encore traduite ; la production ne le demande pas."""
        with tempfile.TemporaryDirectory() as tmp:
            dossier = Path(tmp) / "langues"
            with mock.patch.object(build, "PAGES", ["contact/"]), mock.patch.object(build, "DOSSIER_LANGUES", dossier):
                etat, a_traduire = T.etat_detaille("de", "apercu")
                production = T.etat("de", "production")
        self.assertFalse(etat["pages"][T.PAGE_BANDEAU]["publiable"])
        self.assertIn(cle(T.LIBELLE_BANDEAU), a_traduire)
        self.assertNotIn(T.PAGE_BANDEAU, production["pages"])


class TestAvisFictifs(unittest.TestCase):
    """Ruling 4 (V8) : hors FR, les avis fictifs des pages métier sont retirés avant l'extraction."""

    def test_page_metier_sans_avis(self):
        page = "solutions/cabinets-avocats/"
        fr = assemblees((page,))[page]
        self.assertIn("data-avis-fictif", fr)
        self.assertIn('class="sec mt-avis"', fr)
        t = Table("de", ABSENT)
        pseudo(t, T.retirer_avis_fictifs(fr))  # aucune traduction pour les textes des avis
        libelles(t)
        html, manquants = T.traduire(fr, page, "de", t, "apercu")
        self.assertEqual(manquants, [])
        self.assertNotIn("data-avis-fictif", html)
        self.assertNotIn("mt-avis", html)
        self.assertNotIn("Avis fictif", html)

    def test_avis_hors_section(self):
        h = doc('<div><figure class="mt-av" data-avis-fictif><blockquote>Un avis.</blockquote></figure><p>Reste</p></div>\n')
        self.assertEqual(T.retirer_avis_fictifs(h), doc("<div><p>Reste</p></div>\n"))


class TestScripts(unittest.TestCase):
    """Ruling 13 : une page dont un script inline écrit du texte français n'est publiable dans aucune langue hors FR."""
    H = doc("<p>Bonjour</p><script>el.textContent = 'Analyse en cours avec le moteur';</script>\n")

    def table(self):
        t = Table("de", ABSENT)
        t.poser("Bonjour", "Guten Tag", "relu", "test")
        return t

    def test_page_a_script_bloquee(self):
        html, manquants = T.traduire(self.H, "corrext/chnell/", "de", self.table(), "apercu")
        self.assertEqual(html, "")
        self.assertEqual([(m["cle"], m["raison"]) for m in manquants], [(None, "scripts")])
        self.assertIn("Analyse en cours avec le moteur", manquants[0]["fr"])

    def test_mot_seul_bloque(self):
        """Relecture 2.1 : un libellé d'un seul mot écrit par un script (« Retirer ») bloque aussi la page."""
        h = doc("<p>Bonjour</p><script>b.setAttribute('aria-label','Retirer '+l);</script>\n")
        html, manquants = T.traduire(h, "corrext/gestion-de-projet/", "de", self.table(), "apercu")
        self.assertEqual([(m["cle"], m["raison"]) for m in manquants], [(None, "scripts")])

    def test_page_a_script_anglais_non_bloquee(self):
        """Les libellés anglais de l'application écrits par un script (extraits du registre) ne bloquent pas la page."""
        h = doc("<p>Bonjour</p><script>el.textContent = 'No results for these filters';</script>\n")
        html, manquants = T.traduire(h, "corrext/extraits-registre-commerce/", "de", self.table(), "apercu")
        self.assertEqual(manquants, [])

    def test_inventaire_reel(self):
        """Sur le site construit, plus aucune page n'est bloquée par ses scripts (tâche 7.3 : les textes des démos sont
        sortis des scripts)."""
        sortie = support.site_complet()
        bloquees = {p for p in build.PAGES if S.scripts_a_traduire(support.chemin(sortie, p).read_text(encoding="utf-8"))}
        self.assertEqual(bloquees, set())


class TestBuild(unittest.TestCase):
    PAGES = ("", "contact/")
    PAGES_MULTI = ("", "contact/", "contact/merci/")

    def construire(self, tmp, pages, apercu=True, patches=()):
        console = mock.Mock()
        sortie = support.construire(tmp, pages=pages, config={"apercu": apercu}, langues=("fr", "de"),
                                    patches=[mock.patch.object(build, "DOSSIER_LANGUES", Path(tmp) / "langues"),
                                             mock.patch.object(build, "print", console, create=True), *patches])
        return sortie, " ".join(str(c.args[0]) for c in console.call_args_list)

    def test_build_n_ecrit_pas_de_page_incomplete(self):
        with tempfile.TemporaryDirectory() as tmp:
            table_complete(Path(tmp) / "langues", self.PAGES, sauf=("contact/", "404"))
            sortie, _ = self.construire(tmp, self.PAGES)
            self.assertTrue((sortie / "de/index.html").is_file())
            self.assertFalse((sortie / "de/kontakt").exists())
            self.assertIn("<title>DE ", (sortie / "de/index.html").read_text(encoding="utf-8"))
            # le sélecteur de la page de contact mène à l'accueil allemand, seule page allemande construite
            fr = (sortie / "fr/contact/index.html").read_text(encoding="utf-8")
            self.assertIn('<a href="../../de/" hreflang="de-CH" lang="de" translate="no">DE</a>', fr)
            # 404 sans traduction : pas de 404 allemande, la 404 française de la racine sert de repli
            self.assertFalse((sortie / "de/404.html").exists())
            self.assertFalse((sortie / "de/.htaccess").exists())

    def test_production_sans_langue_complete(self):
        """Production, fr+de configurées, allemand incomplet : la langue n'est pas publiée, le français est identique
        octet pour octet à la référence de production."""
        with tempfile.TemporaryDirectory() as tmp:
            sortie, console = self.construire(tmp, build.PAGES, apercu=False)
            self.assertFalse((sortie / "de").exists())
            obtenu = empreintes.empreintes(sortie)
        reference = json.loads((FIXTURES / "empreintes-fr-production.json").read_text(encoding="utf-8"))
        self.assertEqual(obtenu, reference)
        self.assertRegex(console, rf"Langue de non publiée : {len(build.PAGES) + 2} pages incomplètes")

    def test_production_langue_complete(self):
        with tempfile.TemporaryDirectory() as tmp:
            table_complete(Path(tmp) / "langues", self.PAGES_MULTI, apercu=False)
            sortie, console = self.construire(tmp, self.PAGES_MULTI, apercu=False)
            self.assertNotIn("non publiée", console)
            for f in ("de/index.html", "de/kontakt/index.html", "de/kontakt/danke/index.html", "de/404.html", "de/.htaccess",
                      "de/llms.txt", "de/llms-full.txt", "sitemap-de.xml"):
                self.assertTrue((sortie / f).is_file(), f)
            for f in sortie.rglob("*.html"):
                self.assertNotIn("bandeau-travail", f.read_text(encoding="utf-8"), f)
            self.assertIn("DE Page introuvable", (sortie / "de/404.html").read_text(encoding="utf-8"))
            # libellés fixes des llms.txt traduits par la table ; « Optional » n'y passe jamais
            de = (sortie / "de/llms.txt").read_text(encoding="utf-8")
            self.assertIn("## DE Contact", de)
            self.assertIn("Quelle: https://neur-on.ai/de/kontakt/", (sortie / "de/llms-full.txt").read_text(encoding="utf-8"))
            self.assertIn("## Versions linguistiques", (sortie / "llms.txt").read_text(encoding="utf-8"))

    def test_production_adapte_bloque_la_langue(self):
        with tempfile.TemporaryDirectory() as tmp:
            table_complete(Path(tmp) / "langues", self.PAGES_MULTI, statut="adapte", apercu=False)
            sortie, console = self.construire(tmp, self.PAGES_MULTI, apercu=False)
            self.assertFalse((sortie / "de").exists())
            self.assertIn(f"Langue de non publiée : {len(self.PAGES_MULTI) + 2} pages incomplètes", console)

    def test_production_bloquee_par_un_defaut_de_segment(self):
        """Vague finale, point 5 : une traduction relue au séparateur de milliers français bloque la langue en
        production (message, français seul) ; une traduction V1 validée qui cite « 15 000 » reste exemptée."""
        with tempfile.TemporaryDirectory() as tmp:
            t = table_complete(Path(tmp) / "langues", self.PAGES_MULTI, apercu=False)
            k, e = next((k, e) for k, e in t.entrees.items() if e["trad"] and e["trad"].startswith("DE ")
                        and len(e["trad"]) > 20 and "{" not in e["trad"])
            t.poser(e["fr"], e["trad"] + " (20 000 Dokumente)", "v1", "V1 de/")  # V1 validée : exemptée
            t.enregistrer()
            sortie, console = self.construire(tmp, self.PAGES_MULTI, apercu=False)
            self.assertNotIn("non publiée", console)
            t.poser(e["fr"], e["trad"] + " (20 000 Dokumente)", "relu", "relu par Alice")
            t.enregistrer()
            sortie, console = self.construire(tmp, self.PAGES_MULTI, apercu=False)
            self.assertFalse((sortie / "de").exists())
            self.assertRegex(console, r"Langue de non publiée : \d+ pages incomplètes, dont \d+ aux contrôles bloquants")

    def test_production_bloquee_par_un_controle_de_page(self):
        """Vague finale, point 5 : un problème de controles.controler_production sur une page traduite et finalisée
        retient toute la langue (message, français seul)."""
        with tempfile.TemporaryDirectory() as tmp:
            table_complete(Path(tmp) / "langues", self.PAGES_MULTI, apercu=False)
            faux = lambda html, langue, tete=True: ([controles.probleme("langue", "inLanguage « fr-CH » dans le JSON-LD", "x")]
                                         if 'lang="de"' in html and "kontakt/danke" in html else [])
            sortie, console = self.construire(tmp, self.PAGES_MULTI, apercu=False,
                                              patches=[mock.patch.object(controles, "controler_production", faux)])
            self.assertFalse((sortie / "de").exists())
            self.assertFalse(list(sortie.glob("sitemap-de.xml")))
            self.assertIn("Langue de non publiée : ", console)
            self.assertIn("problème(s) bloquant(s)", console)

    def test_controler_production(self):
        page = ('<!DOCTYPE html><html lang="de"><head><meta property="og:locale" content="de_CH">'
                '<script type="application/ld+json">{"@type":"WebPage","inLanguage":"de-CH"}</script></head>'
                "<body><p>Rund 15 000 Dokumente</p></body></html>")
        self.assertEqual(controles.controler_production(page, "de"), [])  # milliers : contrôlés par segment
        self.assertEqual([p["regle"] for p in controles.controler_production(page.replace("de-CH", "fr-CH"), "de")],
                         ["langue"])
        self.assertEqual([p["regle"] for p in controles.controler_segment("Corrext, 20 000 documents",
                                                                          "Corrext, 20 000 Dokumente", "de")], ["milliers"])
        self.assertEqual([p["regle"] for p in controles.controler_segment("Corrext", "Korrext", "de")], ["marques"])
        self.assertEqual(controles.controler_segment("Corrext, 20 000 documents", "Corrext, 20'000 Dokumente", "de"), [])

    def test_production_avertit_sans_image_de_partage(self):
        """Vague finale, point 9 : une langue publiée sans og-neuron-<l>.png est signalée ; le français garde la sienne."""
        with tempfile.TemporaryDirectory() as tmp:
            table_complete(Path(tmp) / "langues", self.PAGES, apercu=False)
            images = Path(tmp) / "img"
            images.mkdir()
            from outils.i18n import localiser
            with mock.patch.object(localiser, "IMAGES", images):
                sortie, console = self.construire(tmp, self.PAGES, apercu=False)
                self.assertIn("Avertissement : langue de sans image de partage", console)
                (images / "og-neuron-de.png").write_bytes(b"png")
                sortie, console = self.construire(tmp, self.PAGES, apercu=False)
                self.assertNotIn("sans image de partage", console)
            self.assertIn("og-neuron.jpg", (sortie / "fr/index.html").read_text(encoding="utf-8"))

    def test_apercu_signale_les_liens_vers_une_page_non_traduite(self):
        """Vague finale, point 13 : en aperçu, un lien d'une page traduite vers une page non traduite est listé dans le
        rapport du build et porte data-lien-fr ; en production, la langue est entière ou absente (V3)."""
        with tempfile.TemporaryDirectory() as tmp:
            table_complete(Path(tmp) / "langues", self.PAGES, sauf=("contact/",))
            sortie, console = self.construire(tmp, self.PAGES)
            self.assertIn("Liens vers des pages non traduites (de, data-lien-fr) : 1 page(s) : contact/", console)
            accueil = (sortie / "de/index.html").read_text(encoding="utf-8")
            self.assertRegex(accueil, r'href="(?:\.\./)*fr/contact/" data-lien-fr')
            self.assertNotIn("data-lien-fr", (sortie / "fr/index.html").read_text(encoding="utf-8"))
        with tempfile.TemporaryDirectory() as tmp:
            table_complete(Path(tmp) / "langues", self.PAGES, apercu=False, sauf=("contact/",))
            sortie, console = self.construire(tmp, self.PAGES, apercu=False)
            self.assertFalse((sortie / "de").exists())  # jamais de page allemande avec un lien vers le français
            self.assertNotIn("Liens vers des pages non traduites", console)

    def test_production_llms_incomplets_bloquent_la_langue(self):
        with tempfile.TemporaryDirectory() as tmp:
            table_complete(Path(tmp) / "langues", self.PAGES_MULTI, apercu=False, avec_libelles=False)
            sortie, console = self.construire(tmp, self.PAGES_MULTI, apercu=False)
            self.assertFalse((sortie / "de").exists())
            self.assertIn("Langue de non publiée : 1 pages incomplètes", console)

    def test_apercu_bandeau_sur_les_pages_adaptees_jamais_en_francais(self):
        with tempfile.TemporaryDirectory() as tmp:
            table_complete(Path(tmp) / "langues", self.PAGES, statut="adapte")
            sortie, _ = self.construire(tmp, self.PAGES)
            for page in self.PAGES:
                de = support.chemin(sortie, page, "de").read_text(encoding="utf-8")
                self.assertIn(f'<div class="bandeau-travail" role="note">{BANDEAU_DE}</div>', de, page)
                self.assertNotIn("bandeau-travail", support.chemin(sortie, page).read_text(encoding="utf-8"), page)
            self.assertIn("bandeau-travail", (sortie / "de/404.html").read_text(encoding="utf-8"))
            self.assertNotIn("bandeau-travail", (sortie / "404.html").read_text(encoding="utf-8"))
            self.assertIn(".bandeau-travail{", (sortie / "assets/site.css").read_text(encoding="utf-8"))

    def test_apercu_llms_sans_libelles(self):
        """Aperçu : pages allemandes construites, mais ni llms.txt allemand ni renvoi vers lui sans libellés traduits."""
        with tempfile.TemporaryDirectory() as tmp:
            table_complete(Path(tmp) / "langues", self.PAGES, avec_libelles=False)
            sortie, _ = self.construire(tmp, self.PAGES)
            self.assertTrue((sortie / "de/kontakt/index.html").is_file())
            self.assertFalse((sortie / "de/llms.txt").exists())
            self.assertNotIn("Versions linguistiques", (sortie / "llms.txt").read_text(encoding="utf-8"))


class TestEtat(unittest.TestCase):
    def test_etat_liste_le_texte_modifie(self):
        """Un mot changé dans la page FR après sa traduction : la page n'est plus publiable, etat la liste avec le texte
        à traduire ; la 404 et les llms ont leur ligne."""
        with tempfile.TemporaryDirectory() as tmp:
            dossier = Path(tmp) / "langues"
            with mock.patch.object(build, "PAGES", ["contact/"]):
                table_complete(dossier, ("contact/",), deux_modes=True)
            original = build.lire_page

            def lire_page(page):
                meta, corps = original(page)
                return meta, corps.replace("Ce n'est pas une visite guidée générique", "Ce n'est pas une visite générique")
            with mock.patch.object(build, "PAGES", ["contact/"]), mock.patch.object(build, "DOSSIER_LANGUES", dossier):
                complet = T.etat("de", "apercu")
                with mock.patch.object(build, "lire_page", lire_page):
                    etat, a_traduire = T.etat_detaille("de", "apercu")
            self.assertEqual(set(complet["pages"]), {"contact/", "404", "llms", T.PAGE_BANDEAU})
            self.assertTrue(all(e["publiable"] for e in complet["pages"].values()), complet["pages"])
            self.assertEqual(complet["mots_a_traduire"], 0)
            contact = etat["pages"]["contact/"]
            self.assertFalse(contact["publiable"])
            self.assertEqual(contact["manquants"], 1)
            [texte] = a_traduire.values()
            self.assertIn("Ce n'est pas une visite générique", texte)
            self.assertEqual(contact["mots"], T.mots(texte))
            self.assertEqual(etat["mots_a_traduire"], T.mots(texte))
            self.assertEqual(etat["segments"]["absent"], 1)
            self.assertGreater(etat["segments"]["relu"], 50)

    def test_commande_etat(self):
        from outils.i18n import __main__ as commande
        with tempfile.TemporaryDirectory() as tmp:
            dossier = Path(tmp) / "langues"
            sortie = io.StringIO()
            # contexte V1 d'un texte à traduire (commande memoire, tâche 3.2) : repris dans a_traduire.json
            contexte = {"nature": "morceau", "page_v1": "de/kontakt/", "fr_complet": "Demander une démonstration ici",
                        "trad_complete": "Hier eine Demo anfragen"}
            (dossier / "de").mkdir(parents=True)
            (dossier / "de" / T.CONTEXTES).write_text(json.dumps(
                {cle("Demander une démonstration"): {"fr": "Demander une démonstration", "contexte": contexte}}),
                encoding="utf-8")
            with mock.patch.object(build, "PAGES", ["contact/"]), mock.patch.object(build, "DOSSIER_LANGUES", dossier), \
                    contextlib.redirect_stdout(sortie):
                self.assertEqual(commande.main(["etat", "de", "--production"]), 0)
            texte = sortie.getvalue()
            self.assertIn("Traduction de (production) : 0 pages publiables sur 3", texte)
            self.assertIn("contact/ : ", texte)
            self.assertIn("Mots à traduire : ", texte)
            a_traduire = json.loads((dossier / "de/a_traduire.json").read_text(encoding="utf-8"))
            textes = [v["fr"] for v in a_traduire.values()]
            self.assertIn("Demander une démonstration", textes)
            self.assertIn(llms.SOURCE, textes)
            self.assertEqual(a_traduire[cle("Demander une démonstration")]["contexte"], contexte)
            self.assertNotIn("contexte", a_traduire[cle(llms.SOURCE)])
            self.assertNotIn(chr(0x2014), texte)


class TestUnionDesModes(unittest.TestCase):
    """Vague finale, point 1 : la chaîne (etat, export, pont, lexique, mémoire) lit l'union des pages des deux modes ; le
    bandeau de consentement (production seulement) est listé et exporté, et une langue entièrement relue par cette chaîne
    se construit en production sans intervention."""
    COOKIES = ("Cookies de mesure d'audience", "Préférences cookies", "Refuser", "Accepter")

    def test_union_et_variantes(self):
        faux = {"apercu": {"": "A", "404": "N"}, "production": {"": "P", "404": "N"}}
        with mock.patch.object(T, "pages_assemblees", lambda langue, mode: faux[mode]):
            union = T.pages_union("de")
        self.assertEqual(union, {"": {"apercu": "A", "production": "P"}, "404": {"apercu": "N", "production": "N"}})
        self.assertEqual(T.variantes(union[""]), ["A", "P"])
        self.assertEqual(T.variantes(union["404"]), ["N"])  # deux modes identiques : une seule variante
        self.assertEqual(T.variantes("seule"), ["seule"])
        self.assertEqual((T.page_du_mode(union[""], "production"), T.page_du_mode("seule", "apercu")), ("P", "seule"))

    def test_bandeau_cookies_liste_exporte_puis_production_construite(self):
        from outils.i18n import echanges
        with tempfile.TemporaryDirectory() as tmp:
            dossier = Path(tmp) / "langues"
            with mock.patch.object(build, "PAGES", ["contact/"]):
                table = table_complete(dossier, ("contact/",))  # aperçu entièrement relu, comme après un premier tour
                with mock.patch.object(build, "DOSSIER_LANGUES", dossier):
                    etat, a_traduire = T.etat_detaille("de", "apercu")
                    self.assertTrue(etat["pages"]["contact/"]["publiable"])  # jugée sur sa version de l'aperçu
                    for texte in self.COOKIES:
                        self.assertIn(texte, a_traduire.values())
                    # export : les textes de la production seule sont dans le fichier du relecteur
                    for k, fr in a_traduire.items():
                        table.poser(fr, "DE " + fr, "adapte", "test")
                    xlf = Path(tmp) / "export" / "de.xlf"
                    echanges.exporter_xliff("de", table, None, {"adapte"}, xlf, glossaire={})
                    contenu = xlf.read_text(encoding="utf-8")
                    for texte in self.COOKIES:
                        self.assertIn(H.escape(texte, quote=False), contenu)
                    # le relecteur confirme tout : la production se construit, bandeau de consentement traduit
                    for fr in a_traduire.values():
                        table.poser(fr, "DE " + fr, "relu", "test")
                    table.enregistrer()
            sortie, console = TestBuild().construire(tmp, ("contact/",), apercu=False)
            self.assertNotIn("non publiée", console)
            html = (sortie / "de/kontakt/index.html").read_text(encoding="utf-8")
            self.assertIn("DE Préférences cookies", html)
            self.assertIn('id="cc"', html)


if __name__ == "__main__":
    unittest.main()
