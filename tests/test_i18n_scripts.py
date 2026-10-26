"""Scripts et données embarquées par langue (tâche 7.2) : phrase préremplie de la demande de documentation API
(data-prerempli, lue par suivi.js), case de la visite de la gestion de projet (value stable, libellé traduit), adresses de
l'index de recherche du centre d'aide, et un contrôle de fond : aucun script externe n'écrit de texte français.

Inventaire des scripts externes (relecture 2.1, confirmée ici) : seul suivi.js écrivait du français affiché (la phrase
préremplie, traitée ici). sim.js, merci.js, nav.js, aide.js, formulaires.js, consentement.js, animations.js, metier.js,
sommaire.js, schema-produits.js et visite-*.js lisent leurs textes dans le HTML (data-*) ou visent des libellés anglais
de l'application ; corrext-demo.js suit <html lang> (TX par langue) ; sim-data.js porte les données des démos (tâche 7.3)."""
import html as H
import json
import re
import shutil
import subprocess
import tempfile
import unittest
from pathlib import Path
from unittest import mock

import build
from outils.i18n import langues, segments as S, traduire as T
from outils.post import z_formulaires
from tests import support
from tests.test_i18n_traduire import ABSENT, assemblees, pseudo
from outils.i18n.table import Table

ICI = Path(__file__).resolve().parent.parent
PHRASE = "Je souhaite recevoir la documentation technique de l'API."
CONTACT = "contact/"
GESTION = "corrext/gestion-de-projet/"
NODE = shutil.which("node")


def formulaire_demo(h):
    """Formulaire de démonstration d'une page : celui qui a un champ message."""
    return next(f for f in re.findall(r"<form\b[^>]*>.*?</form>", h, re.S) if 'name="message"' in f)


def ouverture(f):
    return re.match(r"<form\b[^>]*>", f).group(0)


class TestPrerempli(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.fr = assemblees([CONTACT], apercu=False)[CONTACT]
        cls.table = pseudo(Table("de", ABSENT), cls.fr)
        cls.de, cls.manquants = T.traduire(cls.fr, CONTACT, "de", cls.table, "production")

    def test_prerempli_traduit(self):
        """La phrase est posée sur le formulaire (data-prerempli) en français, extraite comme texte, puis traduite."""
        ouvre = ouverture(formulaire_demo(self.fr))
        valeur = re.search(r'\sdata-prerempli="([^"]*)"', ouvre).group(1)
        self.assertEqual(H.unescape(valeur), PHRASE)
        unites = [u for u in S.extraire_page(self.fr) if u["genre"] == "attr" and u["attr"] == "data-prerempli"]
        self.assertEqual([u["texte"] for u in unites], [PHRASE])
        self.assertEqual(self.manquants, [])
        ouvre_de = ouverture(formulaire_demo(self.de))
        traduit = H.unescape(re.search(r'\sdata-prerempli="([^"]*)"', ouvre_de).group(1))
        self.assertEqual(traduit, "DE " + PHRASE)

    def test_une_seule_phrase_sur_les_pages_du_site(self):
        """Seul un formulaire qui a un champ message porte la phrase : pas le formulaire de la lettre d'information."""
        for f in re.findall(r"<form\b[^>]*>.*?</form>", self.fr, re.S):
            self.assertEqual('data-prerempli=' in ouverture(f), 'name="message"' in f)

    def test_idempotent(self):
        with mock.patch.object(build, "CONFIG", {**build.CONFIG, "apercu": False}):  # réglage de assemblees(apercu=False)
            self.assertEqual(z_formulaires.traiter(self.fr, CONTACT), self.fr)

    def test_suivi_js_n_ecrit_plus_de_francais(self):
        js = (ICI / "assets/global/suivi.js").read_text(encoding="utf-8")
        self.assertNotIn("Je souhaite", js)
        self.assertIn('getAttribute("data-prerempli")', js)

    def lancer(self, phrase):
        """Exécute suivi.js sur la page de contact (?demande=documentation-api) dans un navigateur factice ; renvoie le
        message du formulaire de démonstration."""
        script = r"""
        const fs = require("fs"), vm = require("vm");
        const [phrase, deja] = JSON.parse(process.argv[2]);
        const champ = { value: deja };
        const type = { value: "demo" };
        const f = {
          getAttribute: (n) => (n === "action" ? "/envoi.php" : n === "data-prerempli" ? phrase : null),
          querySelector: (s) => (s === 'input[type="hidden"][name="type"]' ? type : s === 'textarea[name="message"]' ? champ : null),
          addEventListener: () => {},
        };
        const doc = {
          referrer: "", querySelector: () => null, querySelectorAll: (s) => (s === "form[action]" ? [f] : []),
          addEventListener: () => {},
        };
        const fenetre = { performance: { now: () => 5000, getEntriesByType: () => [] } };
        const memoire = {};
        const contexte = {
          window: fenetre, document: doc, performance: fenetre.performance,
          location: { pathname: "/de/kontakt/", search: "?demande=documentation-api", origin: "https://neur-on.ai", href: "https://neur-on.ai/de/kontakt/" },
          sessionStorage: { getItem: (k) => memoire[k] || null, setItem: (k, v) => { memoire[k] = v; } },
          URL, URLSearchParams, JSON, String, Math, Date, Number,
        };
        vm.createContext(contexte);
        vm.runInContext(fs.readFileSync(process.argv[1], "utf8"), contexte);
        process.stdout.write(JSON.stringify({ message: champ.value, type: type.value }));
        """
        r = subprocess.run([NODE, "-e", script, str(ICI / "assets/global/suivi.js"), json.dumps(phrase)], capture_output=True, text=True)
        self.assertEqual(r.returncode, 0, r.stderr)
        return json.loads(r.stdout)

    @unittest.skipUnless(NODE, "node absent de cette machine")
    def test_message_prerempli_dans_la_langue_de_la_page(self):
        """La demande de documentation API devient le type « documentation » ; le message reprend le data-prerempli de la
        page (ici une phrase allemande), jamais une phrase écrite dans le script."""
        r = self.lancer(["Ich möchte die technische Dokumentation der API erhalten.", ""])
        self.assertEqual(r, {"message": "Ich möchte die technische Dokumentation der API erhalten.", "type": "documentation"})

    @unittest.skipUnless(NODE, "node absent de cette machine")
    def test_message_deja_saisi_jamais_ecrase(self):
        r = self.lancer([PHRASE, "Mon texte"])
        self.assertEqual(r["message"], "Mon texte")

    @unittest.skipUnless(NODE, "node absent de cette machine")
    def test_sans_data_prerempli_aucun_texte(self):
        """Un formulaire sans l'attribut (page non reconstruite) n'est pas prérempli : jamais de français de repli."""
        r = self.lancer([None, ""])
        self.assertEqual(r, {"message": "", "type": "documentation"})


class TestVisiteGestionDeProjet(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.fr = assemblees([GESTION], apercu=False)[GESTION]
        unites = S.extraire_page(T.retirer_avis_fictifs(cls.fr))
        # libellés du français « Allemand » traduits en allemand ; tout le reste de la page inchangé
        cls.de = S.reinjecter_page(cls.fr, {u["id"]: "Deutsch" for u in unites if u["texte"] == "Allemand"})
        cls.visite = (ICI / "assets/visite-gestion-de-projet.js").read_text(encoding="utf-8")

    @staticmethod
    def ligne(h):
        liste = h[h.index('id="cxpLangList"'):]
        liste = liste[:liste.index("</ul>")]
        return re.search(r'<li><label><input type="checkbox" value="Allemand">([^<]*)</label></li>', liste)

    def test_visite_gestion_case_presente(self):
        """La visite vise la case par sa valeur (value n'est jamais traduit) : présente dans la page allemande, dont le
        libellé visible est traduit. La valeur sert de clé à l'état de la démo : elle reste « Allemand »."""
        self.assertIn('input[value="Allemand"]', self.visite)
        fr, de = self.ligne(self.fr), self.ligne(self.de)
        self.assertIsNotNone(fr)
        self.assertIsNotNone(de, "la case value=\"Allemand\" a disparu de #cxpLangList dans la page allemande")
        self.assertEqual(fr.group(1).strip(), "Allemand")
        self.assertEqual(de.group(1).strip(), "Deutsch")

    def test_la_recherche_de_la_visite_suit_le_libelle_affiche(self):
        """La démo filtre sur le texte affiché de chaque ligne : la visite y tape le début du libellé visible (pas celui
        de la valeur), sinon rien ne correspondrait en allemand et la ligne serait masquée."""
        self.assertIn("ligneLangue.textContent", self.visite)
        self.assertNotIn("langue.slice(0, 4)", self.visite)
        self.assertNotIn("var langue = caseLangue.value", self.visite)


class TestIndexAide(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls._tmp = tempfile.TemporaryDirectory()
        cls.pages = [p for p in build.PAGES if p.startswith("aide/")]
        cls.sortie = support.construire(cls._tmp.name, pages=cls.pages, langues=("fr", "de"), patches=support.identite())

    @classmethod
    def tearDownClass(cls):
        cls._tmp.cleanup()

    def index(self, langue):
        f = support.chemin(self.sortie, "aide/", langue)
        return f, json.loads(re.search(r'id="aide-index">(.*?)</script>', f.read_text(encoding="utf-8"), re.S).group(1))

    def test_aide_index_adresses_de(self):
        """Chaque entrée de l'index de recherche de la page d'aide allemande mène à la page allemande de sa rubrique, dont
        l'ancre existe : les adresses suivent localiser, les ancres (identifiants) restent celles du français."""
        page, entrees = self.index("de")
        self.assertGreater(len(entrees), 50)
        for e in entrees:
            chemin, _, ancre = e["u"].partition("#")
            self.assertNotIn("/fr/", "/" + chemin, e["u"])
            cible = (page.parent / chemin / "index.html").resolve()
            self.assertTrue(cible.is_file(), e["u"])
            self.assertTrue(str(cible).startswith(str((self.sortie / "de").resolve())), e["u"])
            self.assertTrue(ancre and f'id="{ancre}"' in cible.read_text(encoding="utf-8"), e["u"])

    def test_adresses_du_francais_inchangees(self):
        page, entrees = self.index("fr")
        for e in entrees:
            chemin, _, ancre = e["u"].partition("#")
            cible = (page.parent / chemin / "index.html").resolve()
            self.assertTrue(cible.is_file() and str(cible).startswith(str((self.sortie / "fr").resolve())), e["u"])

    def test_une_entree_par_question_dans_les_deux_langues(self):
        self.assertEqual([e["u"].partition("#")[2] for e in self.index("fr")[1]],
                         [e["u"].partition("#")[2] for e in self.index("de")[1]])

    def test_rubrique_absente_reste_francaise(self):
        """Une rubrique dont la page n'est pas construite dans la langue garde l'adresse française (la page existe)."""
        with tempfile.TemporaryDirectory() as tmp:
            sortie = support.construire(tmp, pages=["aide/", "aide/depannage/"], langues=("fr", "de"), patches=support.identite())
            f = support.chemin(sortie, "aide/", "de")
            entrees = json.loads(re.search(r'id="aide-index">(.*?)</script>', f.read_text(encoding="utf-8"), re.S).group(1))
        cibles = {e["u"].partition("#")[0] for e in entrees}
        self.assertTrue(any("/de/" in c for c in cibles), cibles)
        self.assertTrue(any("/fr/" in c for c in cibles), cibles)


class TestScriptsExternesSansFrancais(unittest.TestCase):
    """Invariant : aucun script externe du site n'écrit de texte français (il le lirait dans le HTML traduit)."""

    SCRIPTS = ("assets/sim.js", "assets/merci.js", "assets/nav.js", "assets/visite-chnell.js",
               "assets/visite-editeur-de-relecture.js", "assets/visite-extraits-registre-commerce.js",
               "assets/visite-gestion-de-projet.js", "assets/visite-word.js")
    # Chaînes françaises voulues : « Français » est une clé de CODES (sim.js), comparée au nom de langue affiché par
    # l'interface, jamais affichée.
    ADMIS = {"Français"}
    LITTERAL = re.compile(r"""(['"`])((?:\\.|(?!\1)[^\\\n])*)\1""")
    MOTS = re.compile(r"\b(le|la|les|des|du|une?|vous|votre|vos|je|nous|pour|est|sont|avec|dans|sur|cette?|ce)\b", re.I)

    def francais(self, chemin):
        t = (ICI / chemin).read_text(encoding="utf-8")
        t = re.sub(r"/\*.*?\*/", "", t, flags=re.S)
        t = re.sub(r"(?m)(^|\s)//[^\n]*", "", t)
        trouves = []
        for m in self.LITTERAL.finditer(t):
            s = m.group(2)
            if s in self.ADMIS or not re.search(r"[A-Za-zÀ-ÿ]{3}", s):
                continue
            if re.search(r"[À-ÿ]", s) or (" " in s and self.MOTS.search(s)):
                trouves.append(s)
        return trouves

    def test_scripts_externes_sans_texte_francais(self):
        scripts = list(self.SCRIPTS) + sorted(p.relative_to(ICI).as_posix() for p in (ICI / "assets/global").glob("*.js"))
        for chemin in scripts:
            self.assertEqual(self.francais(chemin), [], chemin)

    def test_le_controle_voit_une_phrase_francaise(self):
        """Garde du contrôle lui-même : l'ancienne phrase de suivi.js serait relevée."""
        t = 'm.value = "Je souhaite recevoir la documentation technique de l\'API.";'
        trouves = [m.group(2) for m in self.LITTERAL.finditer(t) if self.MOTS.search(m.group(2))]
        self.assertEqual(len(trouves), 1)


if __name__ == "__main__":
    unittest.main()
