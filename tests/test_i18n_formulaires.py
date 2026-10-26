"""Formulaires et page de remerciement par langue (tâche 7.1) : champ caché « langue » de chaque formulaire, table des
pages de remerciement de envoi.php (réécrite par le build pour les seules langues construites), pages de remerciement
traduites et jamais indexées, langue notée dans le courriel.

php est absent du poste de build : tests/test_envoi.php (redirections par langue) se lance sur une machine qui a PHP 8,
ou sur Hostpoint (php tests/test_envoi.php). Ici, le côté Python : la table du script généré, les formulaires et les
pages."""
import json
import re
import shutil
import subprocess
import tempfile
import unittest
from pathlib import Path
from unittest import mock

import build
from outils import envoi
from outils.i18n import langues, traduire as T
from outils.i18n.table import Table
from outils.post import z_formulaires
from tests import support
from tests.test_i18n_traduire import ABSENT, assemblees, pseudo

ICI = Path(__file__).resolve().parent.parent
SOURCE = (ICI / "envoi.php").read_text(encoding="utf-8")
MERCI = "contact/merci/"
CHAMP_LANGUE = re.compile(r'<input\b[^>]*\bname="langue"[^>]*>')
NEWSLETTER = ('<form class="nl-f" action="/envoi.php" method="post" data-demo><input type="hidden" name="type" value="newsletter">'
              '<input type="email" name="email" required><button type="submit" class="btn">OK</button></form>')


def formulaires(h):
    """Formulaires de la page qui partent vers envoi.php."""
    return [f for f in re.findall(r"<form\b[^>]*>.*?</form>", h, re.S) if re.search(r'action="[^"]*envoi\.php"', f)]


def table_php(php):
    """{langue: adresse} de la constante MERCI d'un envoi.php."""
    bloc = re.search(r"const MERCI = \[(.*?)\];", php, re.S).group(1)
    return dict(re.findall(r"'([a-z]{2})' => '([^']*)'", bloc))


def attendue(codes):
    """Table que doit porter envoi.php : une adresse absolue par langue, déduite de routes.json."""
    return {l: "/" + langues.route(MERCI, l) for l in codes}


class TestChampLangue(unittest.TestCase):
    """Chaque formulaire envoyé à envoi.php porte la langue de la page dans un champ caché."""

    def traiter(self, html):
        h = f"<!DOCTYPE html>\n<html><head></head><body><main>{html}</main></body></html>\n"
        with mock.patch.object(build, "CONFIG", {**build.CONFIG, "apercu": True}):
            return z_formulaires.traiter(h, "ressources/blog/")

    def test_formulaire_francais_champ_cache_langue_fr(self):
        f = formulaires(self.traiter(NEWSLETTER))[0]
        champs = CHAMP_LANGUE.findall(f)
        self.assertEqual(champs, ['<input type="hidden" name="langue" value="fr">'])

    def test_idempotent_et_un_seul_champ(self):
        une = self.traiter(NEWSLETTER)
        with mock.patch.object(build, "CONFIG", {**build.CONFIG, "apercu": True}):
            deux = z_formulaires.traiter(une, "ressources/blog/")
        self.assertEqual(deux.count('name="langue"'), 1)
        self.assertEqual(une, deux)

    def test_les_cases_a_cocher_langues_ne_sont_pas_le_champ_langue(self):
        """« langues[] » (cases du formulaire de démo) et « langue » (page) sont deux champs distincts."""
        f = ('<form action="{{ROOT}}envoi.php"><input type="checkbox" name="langues" value="allemand">'
             '<input type="checkbox" name="langues" value="francais"></form>')
        h = formulaires(self.traiter(f))[0]
        self.assertEqual(h.count('name="langue"'), 1)
        self.assertEqual(h.count('name="langues[]"'), 2)

    def test_formulaires_sans_envoi_php_inchanges(self):
        autre = '<form action="/recherche/"><input name="q"></form>'
        self.assertNotIn('name="langue"', self.traiter(autre))


class TestTableDuScript(unittest.TestCase):
    """envoi.php : la table MERCI de la source et du script généré."""

    def test_source_table_conforme_a_routes_json(self):
        """La source porte les quatre langues, aux adresses de routes.json : le test PHP les exerce telles quelles."""
        self.assertEqual(table_php(SOURCE), attendue(langues.LANGUES))

    def test_source_adresses_validees_par_fabien(self):
        """Adresses de remerciement validées (décision V1 du 2026-10-23)."""
        t = table_php(SOURCE)
        self.assertEqual(t["fr"], "/fr/contact/merci/")
        self.assertEqual(t["de"], "/de/kontakt/danke/")
        self.assertEqual(t["en"], "/en/contact/thank-you/")
        self.assertEqual(t["it"], "/it/contatto/grazie/")

    def test_rendu_seules_les_langues_construites(self):
        for codes in (("fr",), ("fr", "de"), ("fr", "de", "it", "en"), ("fr", "en")):
            php = envoi.rendre(build.CONFIG, codes)
            self.assertEqual(table_php(php), attendue(codes), codes)

    def test_rendu_sans_langues_donne_le_francais_seul(self):
        self.assertEqual(table_php(envoi.rendre(build.CONFIG)), attendue(("fr",)))

    def test_francais_toujours_present(self):
        """Une langue inconnue renvoie au français : sans « fr », le script n'aurait aucun repli."""
        with self.assertRaises(ValueError):
            envoi.rendre(build.CONFIG, ("de",))

    def test_langue_inconnue_refusee(self):
        with self.assertRaises(ValueError):
            envoi.rendre(build.CONFIG, ("fr", "es"))

    def test_rien_d_autre_ne_change(self):
        """Hors la table, le script généré est celui d'avant : destinataire, expéditeur, et le reste du code."""
        avant = envoi.rendre(build.CONFIG, ("fr",))
        apres = envoi.rendre(build.CONFIG, ("fr", "de", "it", "en"))
        sans = lambda php: re.sub(r"const MERCI = \[.*?\];", "", php, flags=re.S)
        self.assertEqual(sans(avant), sans(apres))
        self.assertIn("const DESTINATAIRE = '" + build.CONFIG["destinataire"] + "';", apres)
        self.assertNotIn("{{", apres)

    def test_destinataire_inchange(self):
        self.assertEqual(build.CONFIG["destinataire"], "team@corrext.com")
        self.assertEqual(SOURCE.count("mail(DESTINATAIRE,"), 1)


class TestLangueDansLeCourriel(unittest.TestCase):
    """La langue de la page figure dans le courriel ; la liste des destinataires et le reste du contenu ne changent pas."""

    def test_champ_langue_declare_et_reporte_au_parcours(self):
        champs = re.search(r"const CHAMPS = \[(.*?)\n\];", SOURCE, re.S).group(1)
        self.assertRegex(champs, r"'langue' => \[\d+, 'Langue de la page'\]")
        parcours = re.search(r"const PARCOURS = \[(.*?)\];", SOURCE, re.S).group(1)
        self.assertIn("'langue'", parcours)

    def test_langue_validee_contre_la_table(self):
        """Seul un code de la table MERCI entre dans le courriel ; le reste est ignoré (français par défaut)."""
        self.assertIn("function langue_demandee(", SOURCE)
        self.assertIn("array_key_exists", re.search(r"function langue_demandee\(.*?\n}\n", SOURCE, re.S).group(0))

    def test_adresse_retour_prend_la_langue(self):
        self.assertRegex(SOURCE, r"function adresse_retour\(string \$type, string \$statut, string \$langue = 'fr'\)")
        # tout appel de repondre(adresse_retour(...)) reçoit la langue
        for a in re.findall(r"repondre\(adresse_retour\([^;]*\)\);", SOURCE):
            self.assertIn("$langue", a, a)

    def test_pas_de_lecture_directe_de_post_hors_validation(self):
        """La langue se lit par langue_demandee($_POST), jamais en clair dans une redirection."""
        self.assertNotIn("$_POST['langue']", SOURCE)
        self.assertNotIn("$_GET", SOURCE)


class TestTestPhp(unittest.TestCase):
    """tests/test_envoi.php couvre les redirections par langue (non exécutable ici : php absent)."""

    @classmethod
    def setUpClass(cls):
        cls.t = (ICI / "tests/test_envoi.php").read_text(encoding="utf-8")

    def test_cas_par_langue(self):
        for attendu in ("/de/kontakt/danke/", "/en/contact/thank-you/", "/it/contatto/grazie/", "/fr/contact/merci/"):
            self.assertIn(attendu, self.t)
        for cas in ("retour démo en allemand", "langue inconnue : page de remerciement française",
                    "erreur champs en allemand", "erreur refus en allemand", "langue absente : français",
                    "langue en tableau : français", "langue_demandee", "langue dans le courriel"):
            self.assertIn(cas, self.t, cas)

    def test_table_du_test_et_de_la_source_d_accord(self):
        """Le test PHP n'écrit pas de seconde table : il lit MERCI du script (la source porte les quatre langues)."""
        self.assertNotIn("const MERCI", self.t)


class TestBuild(unittest.TestCase):
    """Le build : formulaires, pages de remerciement et envoi.php dans chaque langue construite."""

    @classmethod
    def setUpClass(cls):
        cls._tmp = tempfile.TemporaryDirectory()
        cls.pages = ["", "contact/", MERCI, "ressources/blog/"]
        cls.sortie = support.construire(cls._tmp.name, pages=cls.pages, config={"apercu": False},
                                        langues=langues.LANGUES, patches=support.identite())

    @classmethod
    def tearDownClass(cls):
        cls._tmp.cleanup()

    def page(self, page, langue):
        return support.chemin(self.sortie, page, langue).read_text(encoding="utf-8")

    def test_formulaires_portent_la_langue_de_leur_page(self):
        total = 0
        for l in langues.LANGUES:
            for page in ("contact/", "ressources/blog/"):
                fs = formulaires(self.page(page, l))
                self.assertTrue(fs, f"{l} {page} : aucun formulaire vers envoi.php")
                for f in fs:
                    total += 1
                    self.assertEqual(re.findall(r'<input\b[^>]*\bname="langue"[^>]*>', f),
                                     [f'<input type="hidden" name="langue" value="{l}">'], f"{l} {page}")
        self.assertGreaterEqual(total, 8)

    def test_pages_de_remerciement_construites_a_l_adresse_de_chaque_langue(self):
        for l, adresse in (("de", "de/kontakt/danke/"), ("en", "en/contact/thank-you/"), ("it", "it/contatto/grazie/"),
                           ("fr", "fr/contact/merci/")):
            self.assertTrue((self.sortie / adresse / "index.html").is_file(), adresse)

    def test_pages_de_remerciement_noindex_dans_chaque_langue(self):
        for l in langues.LANGUES:
            h = self.page(MERCI, l)
            tete = h[:h.index("</head>")]
            self.assertEqual(tete.count('<meta name="robots"'), 1, l)
            self.assertIn('<meta name="robots" content="noindex">', tete, l)

    def test_pages_de_remerciement_hors_plans_et_llms(self):
        for l in langues.LANGUES:
            adresse = "https://neur-on.ai/" + langues.route(MERCI, l)
            self.assertNotIn(adresse, (self.sortie / f"sitemap-{l}.xml").read_text(encoding="utf-8"), l)
            dossier = self.sortie if l == "fr" else self.sortie / l
            self.assertNotIn(adresse, (dossier / "llms.txt").read_text(encoding="utf-8"), l)
            self.assertNotIn(adresse, (dossier / "llms-full.txt").read_text(encoding="utf-8"), l)

    def test_indexable_ne_retient_pas_la_page_de_remerciement(self):
        with mock.patch.object(build, "DOCS", self.sortie):
            for l in langues.LANGUES:
                self.assertFalse(build.indexable(MERCI, l), l)
                self.assertTrue(build.indexable("contact/", l), l)

    def test_envoi_php_porte_les_quatre_langues(self):
        php = (self.sortie / "envoi.php").read_text(encoding="utf-8")
        self.assertEqual(table_php(php), attendue(langues.LANGUES))

    def test_envoi_php_des_seules_langues_construites(self):
        with tempfile.TemporaryDirectory() as tmp:
            sortie = support.construire(tmp, pages=["", "contact/", MERCI], langues=("fr", "de"), patches=support.identite())
            php = (sortie / "envoi.php").read_text(encoding="utf-8")
        self.assertEqual(table_php(php), attendue(("fr", "de")))
        self.assertNotIn("/it/contatto/grazie/", php)
        self.assertNotIn("/en/contact/thank-you/", php)

    def test_langue_sans_page_de_remerciement_absente_de_la_table(self):
        """Une langue construite dont la page de remerciement manque n'a pas d'entrée : le visiteur reçoit le français."""
        with tempfile.TemporaryDirectory() as tmp:
            sortie = support.construire(tmp, pages=["", "contact/"], langues=("fr", "de"), patches=support.identite())
            php = (sortie / "envoi.php").read_text(encoding="utf-8")
        self.assertEqual(table_php(php), attendue(("fr",)))

    def test_francais_seul_table_francaise(self):
        with tempfile.TemporaryDirectory() as tmp:
            sortie = support.construire(tmp, pages=["", "contact/", MERCI], langues=("fr",))
            php = (sortie / "envoi.php").read_text(encoding="utf-8")
        self.assertEqual(table_php(php), attendue(("fr",)))

    def test_la_page_de_remerciement_allemande_renvoie_vers_le_contact_allemand(self):
        """data-retour (bouton « revenir au formulaire ») est localisé comme un lien."""
        h = self.page(MERCI, "de")
        self.assertIn('data-retour="../../../de/kontakt/"', h)


class TestMerciTraduite(unittest.TestCase):
    """La page de remerciement passe par la traduction comme les autres pages : texte, variantes lues par merci.js
    (data-v-erreur, data-v-refus, data-v-newsletter), puis balise noindex gardée."""

    @classmethod
    def setUpClass(cls):
        cls.fr = assemblees([MERCI], apercu=False)[MERCI]
        cls.table = pseudo(Table("de", ABSENT), cls.fr)
        cls.html, cls.manquants = T.traduire(cls.fr, MERCI, "de", cls.table, "production")

    def test_aucun_manquant_et_page_rendue(self):
        self.assertEqual(self.manquants, [])
        self.assertTrue(self.html)

    def test_variantes_de_merci_js_traduites(self):
        for variante in ("erreur", "refus", "newsletter"):
            valeurs = re.findall(rf'data-v-{variante}="([^"]*)"', self.html)
            self.assertTrue(valeurs, variante)
            self.assertTrue(all(v.startswith("DE ") for v in valeurs), (variante, valeurs))
        self.assertRegex(self.html, r"<h1[^>]*>DE ")
        self.assertIn('data-v-erreur="DE Revenir au formulaire"', self.html)

    def test_noindex_et_script_gardes(self):
        tete = self.html[:self.html.index("</head>")]
        self.assertEqual(tete.count('<meta name="robots"'), 1)
        self.assertIn('<meta name="robots" content="noindex">', tete)
        self.assertIn("assets/merci.js", self.html)

    def test_variantes_sans_script_toujours_en_place(self):
        """Sans JavaScript la variante « demo » reste visible, les trois autres cachées (comme en français)."""
        self.assertEqual(len(re.findall(r'data-seul="(?:newsletter|erreur|refus)" hidden', self.html)), 3)


class TestScriptsAssets(unittest.TestCase):
    """La page de remerciement reconnue par suivi.js, quelle que soit la langue (Node, ignoré s'il manque)."""

    NODE = shutil.which("node")

    def lancer(self, chemin, alternate):
        """Exécute assets/global/suivi.js dans un navigateur factice ; renvoie les événements GA envoyés."""
        script = r"""
        const fs = require("fs"), vm = require("vm");
        const [chemin, alternate] = JSON.parse(process.argv[2]);
        const evenements = [];
        const liens = alternate ? [{ href: alternate, getAttribute: (n) => (n === "href" ? alternate : null) }] : [];
        const memoire = {};
        const fenetre = {
          performance: { now: () => 5000, getEntriesByType: () => [{ type: "navigate" }] },
          NeuronConsentement: { mesure: () => true },
          gtag: (...a) => evenements.push(a),
        };
        const doc = {
          referrer: "https://neur-on.ai/",
          querySelector: (s) => (/alternate/.test(s) ? liens[0] || null : null),
          querySelectorAll: () => [],
          addEventListener: () => {},
        };
        const contexte = {
          window: fenetre, document: doc, performance: fenetre.performance, location: { pathname: chemin, search: "", origin: "https://neur-on.ai" },
          sessionStorage: { getItem: (k) => memoire[k] || null, setItem: (k, v) => { memoire[k] = v; } },
          URL, URLSearchParams, JSON, String, Math, Date, Number,
        };
        fenetre.document = doc;
        vm.createContext(contexte);
        vm.runInContext(fs.readFileSync(process.argv[1], "utf8"), contexte);
        process.stdout.write(JSON.stringify(evenements));
        """
        r = subprocess.run([self.NODE, "-e", script, str(ICI / "assets/global/suivi.js"), json.dumps([chemin, alternate])],
                           capture_output=True, text=True)
        self.assertEqual(r.returncode, 0, r.stderr)
        return json.loads(r.stdout)

    @unittest.skipUnless(NODE, "node absent de cette machine")
    def test_generate_lead_sur_chaque_page_de_remerciement(self):
        francais = "https://neur-on.ai/fr/contact/merci/"
        for chemin in ("/fr/contact/merci/", "/neuron-site-test-design/fr/contact/merci/"):
            self.assertEqual(self.lancer(chemin, francais)[0][1], "generate_lead", chemin)
        for l in ("de", "en", "it"):
            chemin = "/" + langues.route(MERCI, l)
            evenements = self.lancer(chemin, francais)
            self.assertEqual([e[1] for e in evenements], ["generate_lead"], chemin)

    @unittest.skipUnless(NODE, "node absent de cette machine")
    def test_aucun_evenement_hors_page_de_remerciement(self):
        francais = "https://neur-on.ai/fr/contact/"
        self.assertEqual(self.lancer("/de/kontakt/", francais), [])
        self.assertEqual(self.lancer("/fr/contact/", francais), [])

    @unittest.skipUnless(NODE, "node absent de cette machine")
    def test_sans_alternate_le_chemin_affiche_sert_de_repli(self):
        self.assertEqual([e[1] for e in self.lancer("/fr/contact/merci/", None)], ["generate_lead"])


if __name__ == "__main__":
    unittest.main()
