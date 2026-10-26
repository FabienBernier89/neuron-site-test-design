"""Scripts et données embarquées par langue (tâches 7.2 et 7.3) : phrase préremplie de la demande de documentation API
(data-prerempli, lue par suivi.js), cases de langues de la gestion de projet (data-code, libellé traduit), adresses de
l'index de recherche du centre d'aide, et deux contrôles de fond : aucun script externe n'écrit de texte français, aucun
script inline non plus (tâche 7.3 : les démos CHnell, Éditeur de relecture et Gestion de projet lisent leurs textes dans
un bloc JSON extrait, <script type="application/json" data-textes>, et leurs données dans un bloc translate="no" ; les
phrases autour d'une valeur sont des gabarits à variables nommées, « Segment {n} confirmé. », contrôlés à la traduction,
à la fusion et à l'import).

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
from outils.i18n import controles, echanges as E, langues, segments as S, traduire as T
from outils.composer import demos
from outils.post import z_formulaires
from tests import support
from tests.test_i18n_traduire import ABSENT, assemblees, doc, pseudo
from outils.i18n.table import Table, cle

ICI = Path(__file__).resolve().parent.parent
PHRASE = "Je souhaite recevoir la documentation technique de l'API."
CONTACT = "contact/"
GESTION = "corrext/gestion-de-projet/"
CHNELL = "corrext/chnell/"
EDITEUR = "corrext/editeur-de-relecture/"
DEMOS = (CHNELL, EDITEUR, GESTION)
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
    def cases(h):
        """(value, data-code, libellé) de chaque case de #cxpLangList."""
        liste = h[h.index('id="cxpLangList"'):]
        liste = liste[:liste.index("</ul>")]
        return re.findall(r'<li><label><input type="checkbox" value="([^"]*)" data-code="([a-z]{2})">([^<]*)</label></li>',
                          liste)

    def test_cases_de_langues_avec_code(self):
        """Chaque case porte le code de sa langue (data-code, relecture 7.2) ; value reste la clé de l'état de la démo,
        égale au libellé français."""
        fr = self.cases(self.fr)
        self.assertEqual([(v, c) for v, c, _ in fr],
                         [("Allemand", "de"), ("Français", "fr"), ("Italien", "it"), ("Anglais", "en"), ("Tchèque", "cs"),
                          ("Hongrois", "hu"), ("Arabe", "ar"), ("Bulgare", "bg"), ("Danois", "da"), ("Grec", "el"),
                          ("Espagnol", "es"), ("Néerlandais", "nl")])
        self.assertEqual([l.strip() for _, _, l in fr], [v for v, _, _ in fr])

    def test_visite_gestion_case_presente(self):
        """La visite vise la case par son code (data-code n'est jamais traduit) : présente dans la page allemande, dont le
        libellé visible est traduit, et dont la valeur (clé de l'état) reste « Allemand »."""
        self.assertIn('input[data-code="de"]', self.visite)
        self.assertNotIn('input[value=', self.visite)
        de = {c: (v, l.strip()) for v, c, l in self.cases(self.de)}
        self.assertEqual(de["de"], ("Allemand", "Deutsch"))

    def test_la_recherche_de_la_visite_suit_le_libelle_affiche(self):
        """La démo filtre sur le texte affiché de chaque ligne : la visite y tape le début du libellé visible (pas celui
        de la valeur), sinon rien ne correspondrait en allemand et la ligne serait masquée."""
        self.assertIn("ligneLangue.textContent", self.visite)
        self.assertNotIn("langue.slice(0, 4)", self.visite)
        self.assertNotIn("var langue = caseLangue.value", self.visite)

    def test_pastilles_lisent_le_libelle_affiche(self):
        """Les pastilles et leur nom accessible (« Retirer {langue} ») prennent le libellé de la case, traduit avec la
        page, jamais sa valeur (relecture 7.2 : « Allemand » restait écrit sur la page allemande)."""
        script = re.findall(r"<script>(.*?)</script>", self.fr, re.S)[-1]
        self.assertIn('closest("label")', script)
        self.assertNotIn("createTextNode(l+", script)
        self.assertNotIn("'Retirer '", script)


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


# ---------- tâche 7.3 : textes des scripts inline des démos ----------

def textes_de(h):
    """Bloc des textes d'une démo (<script type="application/json" data-textes>) : {clé: texte français}."""
    m = re.search(r'<script type="application/json" data-textes>(.*?)</script>', h, re.S)
    return json.loads(m.group(1)) if m else None


def scripts_inline(h):
    """Corps des scripts inline (hors JSON) d'une page."""
    return [m.group(2) for m in re.finditer(r"<script\b([^>]*)>(.*?)</script>", h, re.S)
            if "json" not in m.group(1) and "src=" not in m.group(1)]


class TestDetectionDuFrancais(unittest.TestCase):
    """segments.scripts_a_traduire : un texte français écrit par un script, même d'un seul mot (relecture 2.1 :
    « Retirer » n'était pas vu) ; jamais l'anglais de l'application, le code ni les données dans leur langue."""

    def test_mot_seul_et_phrase_coupee(self):
        for js in ("b.setAttribute('aria-label','Retirer '+l);", "setEst({prep:'1 jour'});", "x.textContent='à calculer';",
                   "say('Segment '+i+' confirmé.');", "n.textContent=\"l'application\";", "t=`Aucun segment`;"):
            with self.subTest(js=js):
                self.assertTrue(S.scripts_a_traduire(f"<script>{js}</script>"))

    def test_anglais_code_et_donnees_ignores(self):
        for js in ("h='<p class=\"cxe-h\">Translation memories</p>'+'No result';", "if(e.key==='Escape'){}",
                   "lang='de';x.classList.toggle('on')", "s.style.transform='scaleX(0)'", "u='../fr/protection-des-donnees/';",
                   "t='From this project\\'s TM';", "var RX={src:/int[ée]r[êe]ts?\\s+moratoires?/gi};",
                   "/* Démo : commentaire en français */ var a=1; // la suite", "a='Kann die Zahlstelle des fehlenden Betrages';",
                   "x='Keep all My Edits'+' · LM';"):
            with self.subTest(js=js):
                self.assertFalse(S.scripts_a_traduire(f"<script>{js}</script>"), S.francais_des_scripts(f"<script>{js}</script>"))

    def test_blocs_json_ignores(self):
        self.assertFalse(S.scripts_a_traduire('<script type="application/json" data-textes>{"a": "Aucun résultat."}</script>'))

    def test_litteraux_js(self):
        self.assertEqual(S.litteraux_js("a='l\\'un'+\"b\"+`c`;r=/x'y/g;d=a/2/3;// 'non'\n/* 'non' */e='fin'"),
                         ["l'un", "b", "c", "fin"])


class TestVariables(unittest.TestCase):
    """Gabarits à variables nommées : chaque variable du français survit à la traduction, sinon la traduction est
    refusée (controles.variables) par traduire, par la fusion des adaptations et par l'import des relectures."""
    FR = "Segment {n} confirmé."

    def test_controle(self):
        self.assertEqual(S.variables("Démo : {affiches} des {total} résultats ; {n} et {n}"), ["affiches", "n", "n", "total"])
        self.assertEqual(S.variables("{1}Fichier{/1} {{ROOT}}fr/ {Ab}"), [])  # marqueurs, jetons et majuscules : pas des variables
        self.assertEqual(controles.variables(self.FR, "Segment {n} bestätigt."), [])
        for faux in ("Segment bestätigt.", "Segment {nummer} bestätigt.", "Segment {n} {n} bestätigt.", "{n} {m} bestätigt."):
            with self.subTest(faux=faux):
                self.assertEqual([p["regle"] for p in controles.variables(self.FR, faux)], ["variables"])
        self.assertIn("variables", controles.BLOQUANTS)

    def page(self):
        return doc('<p>Bonjour</p><script type="application/json" data-textes>{"confirme": "Segment {n} confirmé."}</script>\n')

    def table(self, trad):
        t = Table("de", ABSENT)
        t.poser("Bonjour", "Guten Tag", "relu", "test")
        t.poser(self.FR, trad, "relu", "test")
        return t

    def test_gabarit_variables_conservees(self):
        html, manquants = T.traduire(self.page(), "corrext/editeur-de-relecture/", "de", self.table("Segment {n} bestätigt."),
                                     "production")
        self.assertEqual(manquants, [])
        self.assertEqual(textes_de(html), {"confirme": "Segment {n} bestätigt."})
        html, manquants = T.traduire(self.page(), "corrext/editeur-de-relecture/", "de", self.table("Segment bestätigt."),
                                     "production")
        self.assertEqual(html, "")
        self.assertEqual([(m["cle"], m["raison"]) for m in manquants], [(cle(self.FR), "variables")])

    def test_controler_traductions_bloque(self):
        n, problemes = controles.controler_traductions("de", self.table("Segment {nummer} bestätigt.").entrees, {})
        self.assertEqual([(p["regle"], p["gravite"]) for p in problemes], [("variables", "bloquant")])

    def test_fusion_refuse_une_variable_perdue(self):
        with tempfile.TemporaryDirectory() as tmp:
            t = Table("de", Path(tmp))
            t.poser(self.FR, "Segment {n} bestätigt.", "mt", "LexMachina")
            f = Path(tmp) / "propositions.json"
            f.write_text(json.dumps([{"cle": cle(self.FR), "trad": "Segment {nummer} bestätigt.", "note": ""}]), encoding="utf-8")
            r = E.fusionner(f, t, glossaire={}, jour="2026-10-26")
        self.assertEqual([x["raison"] for x in r["refuses"]], ["variables"])
        self.assertEqual(t.entrees[cle(self.FR)]["trad"], "Segment {n} bestätigt.")

    def test_import_refuse_une_variable_perdue(self):
        with tempfile.TemporaryDirectory() as tmp:
            t = Table("de", Path(tmp))
            t.poser(self.FR, "Segment {n} bestätigt.", "adapte", "adapté")
            f = Path(tmp) / "corrections.csv"
            f.write_text(f'cle;fr;trad\n{cle(self.FR)};"{self.FR}";"Segment bestätigt."\n', encoding="utf-8-sig")
            r = E.importer_csv(f, t, "Alice", glossaire={}, jour="2026-10-26")
        self.assertEqual([x["raison"] for x in r["rejetes"]], ["variables"])
        self.assertEqual(t.entrees[cle(self.FR)]["statut"], "adapte")


class TestDemos(unittest.TestCase):
    """Les trois démos sur la sortie FR : plus aucun texte français dans les scripts, textes extraits, données exclues."""

    @classmethod
    def setUpClass(cls):
        cls.sortie = support.site_complet()
        cls.pages = {p: support.chemin(cls.sortie, p).read_text(encoding="utf-8") for p in DEMOS}

    def test_aucune_chaine_fr_dans_les_scripts_inline(self):
        """Sur toutes les pages construites, aucun script inline n'écrit de français (gabarit, mot seul ou phrase)."""
        trouves = {}
        for f in sorted(self.sortie.rglob("*.html")):
            ecrits = S.francais_des_scripts(f.read_text(encoding="utf-8"))
            if ecrits:
                trouves[f.relative_to(self.sortie).as_posix()] = ecrits[:3]
        self.assertEqual(trouves, {})

    # Textes des scripts des démos qui restent dans le code : libellés anglais de l'application, noms de touches et de
    # langues de l'interface, comparés ou affichés tels quels. Toute autre chaîne lisible fait échouer : un texte nouveau
    # va dans le bloc data-textes (s'il est français) ou ici (s'il est un libellé de l'application).
    LIBELLES = {
        CHNELL: {"German", "French", "No results", "No results for these filters", "Show in context", "Enter"},
        EDITEUR: {"From this project's TM", "Apply", "Source", "Target", "Translation memories", "CHnell", "No result",
                  "Conflicting changes", "Segment ", "My Edit · AM", "Last Edit · LM", "Keep all My Edits",
                  "Apply all Last Edits", "No conflicting change to resolve.", "Incoming changes", " · LM",
                  "No incoming change to apply.", "Propagation decisions", "Keep as is", " Segment ",
                  "No propagation decision required.",
                  "Enter", "ArrowDown", "ArrowRight", "ArrowUp", "ArrowLeft", "Home", "End", "Escape"},
        GESTION: {"Escape", "ArrowRight", "ArrowLeft", "×"},
    }

    @staticmethod
    def textes_lisibles(chaine):
        """Morceaux de texte d'une chaîne du script, hors balises (entières ou coupées en bord de chaîne) et hors code :
        un morceau sans majuscule ni lettre accentuée (clé, classe, sélecteur, style, événement) n'est pas lu."""
        chaine = re.sub(r"<[^<>]*$", "", re.sub(r'^[^<>]*">', "", chaine))
        for morceau in re.split(r"<[^>]*>", chaine):
            lisible = H.unescape(morceau)
            code = not re.search(r"\s", lisible) and (lisible[:1].islower() or re.search(r"[()\[\]:.=#\"]", lisible)
                                                     or lisible.isupper())
            if re.search(r"[A-ZÀ-ÿ]", lisible) and not code:  # identifiant (cxlL2X), sélecteur, style, sigle (NFD)
                yield lisible

    def test_litteraux_des_demos_inventories(self):
        for page, h in self.pages.items():
            vus = {t for js in scripts_inline(h) for c in S.litteraux_js(js) for t in self.textes_lisibles(c)}
            with self.subTest(page=page):
                self.assertEqual(vus - self.LIBELLES[page], set())
                self.assertEqual(self.LIBELLES[page] - vus, set())  # liste tenue à jour

    def test_textes_extraits(self):
        """Chaque texte du bloc data-textes est une unité de extraire_page (genre json) ; le bloc des données
        (translate="no") n'en donne aucune ; chaque clé lue par le script existe, et chaque clé du bloc est lue."""
        for page, h in self.pages.items():
            with self.subTest(page=page):
                textes = textes_de(h)
                self.assertTrue(textes)
                unites = [u for u in S.extraire_page(h) if u["genre"] == "json"]
                self.assertEqual(sorted(u["texte"] for u in unites), sorted(textes.values()))
                debut = h.find('data-donnees')
                if debut >= 0:
                    fin = h.index("</script>", debut)
                    self.assertFalse([u for u in S.extraire_page(h) if debut < u["debut"] < fin])
                js = "".join(scripts_inline(h))
                lues = set(re.findall(r"""\bt\(\s*['"]([\w-]+)['"]""", js))
                # clés écrites en toutes lettres, jamais calculées (sauf le choix entre deux clés écrites)
                self.assertNotRegex(js, r"""(?<!function )\bt\(\s*(?!['"]|pend>1\?'attente_plusieurs':'attente_un')""")
                lues |= set(re.findall(r"""pend>1\?'(\w+)':'(\w+)'""", js)[0]) if page == EDITEUR else set()
                self.assertEqual(lues - set(textes), set())
                self.assertEqual(set(textes) - lues, set())

    def test_textes_repris_de_la_v1(self):
        """Aucun texte inventé : chaque texte français, coupé à ses variables, se lit dans le script de la page V1."""
        for page, h in self.pages.items():
            v1 = (build.NEURON / "docs/fr" / page / "index.html").read_text(encoding="utf-8")
            fragments = demos.fragments_v1("".join(re.findall(r"<script>(.*?)</script>", v1, re.S)))
            for k, t in textes_de(h).items():
                for morceau in S.VARIABLE.split(t)[::2]:
                    with self.subTest(page=page, cle=k, morceau=morceau):
                        self.assertTrue(demos.repris(morceau, fragments))
            # la garde elle-même : un mot ajouté ou changé n'est pas repris
            self.assertFalse(demos.repris("Démo : texte inventé.", fragments))

    def test_pages_publiables_une_fois_traduites(self):
        """Ruling 13 levé : une table complète publie les trois pages (plus aucune raison « scripts »)."""
        fr = assemblees(list(DEMOS), apercu=False)
        for page in DEMOS:
            with self.subTest(page=page):
                t = pseudo(Table("de", ABSENT), fr[page])
                html, manquants = T.traduire(fr[page], page, "de", t, "production")
                self.assertEqual(manquants, [])
                self.assertTrue(all(v.startswith("DE ") for v in textes_de(html).values()))


if __name__ == "__main__":
    unittest.main()
