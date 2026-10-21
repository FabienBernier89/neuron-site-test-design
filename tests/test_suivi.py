"""Suivi des parcours (lot C, spec V2 § 6) : formulaire de démo (secteur, champs cachés, piège), envoi.php écrit par
le build, Google Analytics avec consentement (jamais sur l'aperçu), page de remerciement, textes à relire.

Le comportement dans le navigateur (UTM gardés sur plusieurs pages, stockage bloqué, refus sans appel à Google) se
vérifie dans Chrome : voir le rapport du lot C."""
import html as H
import json
import re
import shutil
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path
from unittest import mock

ICI = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ICI))
import build  # noqa: E402
from outils import contenus, envoi  # noqa: E402
from outils.post import consentement, z_formulaires  # noqa: E402
from tests import support  # noqa: E402

GA_TEST = "G-TEST12345"
# Les 6 pages secteur de la V2 : dossier solutions/<slug>/ et libellé du pied de page (repris du site actuel)
SECTEURS = [("cabinets-avocats", "Cabinets d'avocats"), ("banques-finance", "Banques et finance"),
            ("directions-juridiques", "Directions juridiques"), ("autorites-administration", "Autorités et administration"),
            ("fiduciaires-conseil", "Fiduciaires et conseil"), ("editeurs-legaltech", "LegalTechs et éditeurs")]
CACHES = ("page_entree", "page_origine", "utm_source", "utm_medium", "utm_campaign", "utm_term", "utm_content", "t0", "duree", "type")
NEWSLETTER = ('<form class="nl-f" action="/envoi.php" method="post" data-demo><input type="hidden" name="type" value="newsletter">'
              '<input type="hidden" name="t0" value=""><div class="nl-piege" aria-hidden="true"><input type="text" name="site_url" '
              'tabindex="-1"></div><input type="email" name="email" required><input type="checkbox" name="consentement" value="oui" '
              'required><button type="submit" class="btn">OK</button></form>')


def formulaires(h):
    return re.findall(r"<form\b[^>]*>.*?</form>", h, re.S)


def demo(h):
    return next(f for f in formulaires(h) if 'name="prenom"' in f)


def page_essai(formulaire, apercu=True):
    """Page minimale qui contient un formulaire, passée dans z_formulaires avec le réglage « apercu » donné."""
    h = f"<!DOCTYPE html>\n<html><head></head><body><main>{formulaire}</main></body></html>\n"
    with mock.patch.object(build, "CONFIG", {**build.CONFIG, "apercu": apercu}):
        return z_formulaires.traiter(h, "ressources/blog/")


class TestSuivi(unittest.TestCase):
    """Tests du brief du lot C (libellés de secteur : ceux des pages secteur du site, décision du contrôleur)."""

    @classmethod
    def setUpClass(cls):
        cls.docs = support.site_complet(apercu=True)  # aperçu forcé, quel que soit le réglage du dépôt
        cls.contact = support.chemin(cls.docs, "contact/").read_text(encoding="utf-8")

    def test_formulaire_secteur_et_champs_caches(self):
        self.assertIn('name="secteur"', self.contact)
        for n in ("page_entree", "page_origine", "utm_source", "utm_medium", "utm_campaign", "utm_term", "utm_content", "site_url", "t0", "type"):
            self.assertRegex(self.contact, r'<input[^>]+name="%s"' % n)
        for _slug, libelle in SECTEURS:
            self.assertIn(libelle, self.contact)

    def test_ga_absent_de_l_apercu(self):
        for p in build.PAGES:
            h = support.chemin(self.docs, p).read_text(encoding="utf-8")
            self.assertNotIn("googletagmanager.com", h, p)
            self.assertNotIn('name="ga-id"', h, p)
            self.assertNotIn('id="cc"', h, p)
            self.assertNotIn("data-cc-ouvrir", h, p)


class TestFormulaireDemo(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.tmp = tempfile.TemporaryDirectory()
        pages = ["", "contact/", "contact/merci/"]
        cls.apercu = support.construire(Path(cls.tmp.name) / "a", pages, config={"apercu": True})
        cls.production = support.construire(Path(cls.tmp.name) / "p", pages, config={"apercu": False})
        cls.f_apercu = demo((cls.apercu / "fr/contact/index.html").read_text(encoding="utf-8"))
        cls.f_production = demo((cls.production / "fr/contact/index.html").read_text(encoding="utf-8"))

    @classmethod
    def tearDownClass(cls):
        cls.tmp.cleanup()

    def ouverture(self, f):
        return re.match(r"<form\b[^>]*>", f).group(0)

    def test_envoi_vers_envoi_php_en_post(self):
        for f in (self.f_apercu, self.f_production):
            o = self.ouverture(f)
            self.assertIn('action="/envoi.php"', o)
            self.assertIn('method="post"', o)

    def test_apercu_inactif_production_active(self):
        self.assertIn("data-demo", self.ouverture(self.f_apercu))
        self.assertIn('class="avis"', self.f_apercu)  # l'avis « aucun envoi » de l'aperçu reste
        o = self.ouverture(self.f_production)
        self.assertNotIn("data-demo", o)
        self.assertNotIn("novalidate", o)  # en production, le navigateur contrôle les champs obligatoires
        self.assertNotIn('class="avis"', self.f_production)

    def test_secteur_six_pages_plus_autre(self):
        select = re.search(r'<select id="cf-secteur" name="secteur"[^>]*>(.*?)</select>', self.f_apercu, re.S)
        self.assertTrue(select)
        options = re.findall(r'<option value="([^"]*)">([^<]*)</option>', select.group(1))
        self.assertEqual(options[0][0], "")
        self.assertEqual([(v, H.unescape(t)) for v, t in options[1:]], SECTEURS + [("autre", "Autre")])
        self.assertIn('<label for="cf-secteur">' + contenus.texte("contact.secteur.libelle") + "</label>", self.f_apercu)
        self.assertNotIn("required", select.group(0))  # facultatif : il ne freine pas la demande

    def test_secteurs_alignes_sur_les_pages_et_le_pied(self):
        pied = (self.apercu / "fr/index.html").read_text(encoding="utf-8")
        for slug, libelle in z_formulaires.SECTEURS:
            self.assertTrue((build.SRC / "pages/solutions" / slug / "index.html").is_file(), slug)
            self.assertIn(f'solutions/{slug}/">{libelle}</a></li>', pied)
        self.assertEqual(list(z_formulaires.SECTEURS), SECTEURS)

    def test_obligatoires_d_abord_puis_secteur_dans_le_groupe_facultatif(self):
        """Page contact pensée pour la conversion (2026-10-16) : les cinq champs obligatoires d'abord, puis le groupe
        facultatif, qui commence par le secteur."""
        f = self.f_apercu
        ordre = [f.index(f'name="{n}"') for n in ("prenom", "nom", "email", "organisation", "fonction")]
        self.assertEqual(ordre, sorted(ordre))
        self.assertLess(f.index('name="fonction"'), f.index('class="ct-opt"'))
        self.assertLess(f.index('class="ct-opt"'), f.index('name="secteur"'))
        self.assertEqual(f.count('name="secteur"'), 1)

    def test_champs_caches_piege_et_type(self):
        for f in (self.f_apercu, self.f_production):
            for n in CACHES:
                self.assertEqual(len(re.findall(r'<input type="hidden" name="%s" value="[^"]*">' % n, f)), 1, n)
            self.assertIn('<input type="hidden" name="type" value="demo">', f)
            piege = re.search(r'<div class="piege" aria-hidden="true">(.*?)</div>', f)
            self.assertTrue(piege)
            self.assertRegex(piege.group(1), r'<input type="text" name="site_url" tabindex="-1" autocomplete="off">')

    def test_cases_multiples_en_tableau(self):
        """PHP ne garde qu'une valeur d'un nom répété : les langues cochées partent sous langues[]."""
        self.assertEqual(len(re.findall(r'name="langues\[\]"', self.f_apercu)), 5)
        self.assertNotIn('name="langues"', self.f_apercu)

    def test_idempotent(self):
        h = (self.apercu / "fr/contact/index.html").read_text(encoding="utf-8")
        with mock.patch.object(build, "CONFIG", {**build.CONFIG, "apercu": True}):
            self.assertEqual(z_formulaires.traiter(h, "contact/"), h)
        h = (self.production / "fr/contact/index.html").read_text(encoding="utf-8")
        with mock.patch.object(build, "CONFIG", {**build.CONFIG, "apercu": False}):
            self.assertEqual(z_formulaires.traiter(h, "contact/"), h)

    def test_tout_formulaire_vers_envoi_php(self):
        """L'encart newsletter d'un autre lot reçoit les champs de suivi, sans champ secteur ni doublon."""
        f = formulaires(page_essai(NEWSLETTER))[0]
        for n in CACHES:
            self.assertEqual(len(re.findall(r'name="%s"' % n, f)), 1, n)
        self.assertIn('name="type" value="newsletter"', f)
        self.assertEqual(f.count("site_url"), 1)
        self.assertEqual(self.ouverture(f).count("data-demo"), 1)
        self.assertNotIn('name="secteur"', f)
        prod = formulaires(page_essai(NEWSLETTER, apercu=False))[0]
        self.assertNotIn("data-demo", self.ouverture(prod))
        une_fois = page_essai(NEWSLETTER)
        with mock.patch.object(build, "CONFIG", {**build.CONFIG, "apercu": True}):
            self.assertEqual(z_formulaires.traiter(une_fois, "ressources/blog/"), une_fois)

    def test_action_ramenee_au_chemin_absolu(self):
        """Quelle que soit son écriture ({{ROOT}}envoi.php, ../envoi.php), l'action devient /envoi.php : envoi.php vit à
        la racine du site et n'est pas une page."""
        for action in ("{{ROOT}}envoi.php", "../../envoi.php", "envoi.php"):
            f = formulaires(page_essai(NEWSLETTER.replace('action="/envoi.php"', f'action="{action}"')))[0]
            self.assertIn('action="/envoi.php"', self.ouverture(f), action)
            self.assertIn('name="page_entree"', f, action)

    def test_methode_post_imposee(self):
        for methode in ('method="get"', "method='GET'", "method=get"):
            f = formulaires(page_essai(NEWSLETTER.replace('method="post"', methode)))[0]
            self.assertEqual(re.findall(r"\smethod=\S+", self.ouverture(f)), [' method="post"'], methode)
        sans = formulaires(page_essai(NEWSLETTER.replace(' method="post"', "")))[0]
        self.assertIn(' method="post"', self.ouverture(sans))

    def test_autres_formulaires_intacts(self):
        autre = '<form action="https://exemple.ch/recherche" method="get"><input name="q"></form>'
        self.assertIn(autre, page_essai(autre))


class TestConsentement(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.tmp = tempfile.TemporaryDirectory()
        pages = ["", "contact/", "contact/merci/", "protection-des-donnees/"]
        chemins = ("fr/index.html", "fr/contact/index.html", "fr/contact/merci/index.html", "404.html")
        cls.sortie = support.construire(Path(cls.tmp.name) / "p", pages, config={"ga_id": GA_TEST, "apercu": False})
        cls.pages = {c: (cls.sortie / c).read_text(encoding="utf-8") for c in chemins}
        apercu = support.construire(Path(cls.tmp.name) / "a", pages, config={"ga_id": GA_TEST, "apercu": True})
        cls.apercu = {c: (apercu / c).read_text(encoding="utf-8") for c in chemins}

    @classmethod
    def tearDownClass(cls):
        cls.tmp.cleanup()

    def test_identifiant_du_site_dans_la_configuration(self):
        self.assertEqual(build.CONFIG["ga_id"], "G-H128S2PTKN")  # site existant, décision de Fabien du 2026-10-14
        self.assertRegex(build.CONFIG["ga_id"], consentement.IDENTIFIANT)

    def test_apercu_jamais_de_mesure_meme_avec_identifiant(self):
        for c, h in self.apercu.items():
            for absent in ('name="ga-id"', 'id="cc"', "data-cc-ouvrir", "googletagmanager.com"):
                self.assertNotIn(absent, h, c)

    def test_identifiant_dans_la_tete(self):
        for c, h in self.pages.items():
            tete = h[:h.index("</head>")]
            self.assertEqual(tete.count(f'<meta name="ga-id" content="{GA_TEST}">'), 1, c)

    def test_gtag_jamais_dans_le_html(self):
        """gtag.js n'est chargé que par consentement.js, après « Accepter »."""
        for c, h in self.pages.items():
            self.assertNotIn("googletagmanager.com", h, c)
            self.assertNotIn("gtag(", h, c)
        js = (self.sortie / "assets/global.js").read_text(encoding="utf-8")
        self.assertIn("googletagmanager.com/gtag/js", js)

    def test_bandeau_cache_au_depart_et_tot_dans_la_page(self):
        for c, h in self.pages.items():
            self.assertEqual(h.count('id="cc"'), 1, c)
            bandeau = re.search(r'<div class="cc" id="cc"[^>]*>.*?</div></div></div>', h, re.S).group(0)
            self.assertIn(" hidden", re.match(r"<div[^>]*>", bandeau).group(0), c)
            self.assertLess(h.index('class="skip"'), h.index('id="cc"'), c)  # juste après le lien d'évitement
            self.assertLess(h.index('id="cc"'), h.index('<header'), c)
            for cle in ("consentement.texte", "consentement.lien", "consentement.refuser", "consentement.accepter"):
                self.assertIn(H.escape(contenus.texte(cle), quote=False), bandeau, cle)
            self.assertIn(f'aria-label="{H.escape(contenus.texte("consentement.aria"))}"', bandeau)
            self.assertIn('data-cc="refuser"', bandeau)
            self.assertIn('data-cc="accepter"', bandeau)

    def test_lien_protection_des_donnees_resolu(self):
        for c, h in self.pages.items():
            bandeau = h[h.index('id="cc"'):]
            lien = re.search(r'href="([^"]+)"', bandeau).group(1)
            base = (self.sortie / c).parent if c != "404.html" else self.sortie
            self.assertEqual(((base / lien.split("#")[0]).resolve() / "index.html"),
                             (self.sortie / "fr/protection-des-donnees/index.html").resolve(), c)
            self.assertTrue(lien.endswith("#suivi"), lien)

    def test_parametres_dans_la_barre_basse_du_pied(self):
        for c, h in self.pages.items():
            barre = re.search(r'<div class="fp-b">.*?</div>\n', h, re.S).group(0)
            bouton = f'<button type="button" class="fp-ck" data-cc-ouvrir hidden>{contenus.texte("consentement.parametres")}</button>'
            self.assertIn(bouton, barre, c)
            self.assertLess(barre.index("Protection des données"), barre.index("fp-ck"), c)
            self.assertEqual(h.count("data-cc-ouvrir"), 1, c)

    def test_idempotent(self):
        h = self.pages["fr/index.html"]
        with mock.patch.object(build, "CONFIG", {**build.CONFIG, "ga_id": GA_TEST, "apercu": False}):
            self.assertEqual(consentement.traiter(h, ""), h)

    def test_identifiant_invalide_refuse(self):
        h = "<!DOCTYPE html>\n<html><head></head><body></body></html>\n"
        for mauvais in ('G-1"><script>alert(1)</script>', "UA-12345-1", "G-"):
            with mock.patch.object(build, "CONFIG", {**build.CONFIG, "ga_id": mauvais, "apercu": False}):
                with self.assertRaises(ValueError, msg=mauvais):
                    consentement.traiter(h, "")


class TestMerci(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.tmp = tempfile.TemporaryDirectory()
        cls.production = support.construire(cls.tmp.name, ["", "contact/", "contact/merci/"], config={"apercu": False})

    @classmethod
    def tearDownClass(cls):
        cls.tmp.cleanup()

    def test_page_et_gabarit(self):
        self.assertIn("contact/merci/", build.PAGES)
        src = (build.SRC / "pages/contact/merci/index.html").read_text(encoding="utf-8")
        self.assertIn("\ngabarit: contact\n", src)
        self.assertIn("\nscripts: merci.js\n", src)
        h = (self.production / "fr/contact/merci/index.html").read_text(encoding="utf-8")
        self.assertNotIn('class="hd-nav"', h)  # en-tête minimal du gabarit contact
        self.assertEqual(len(re.findall(r"<h1[ >]", h)), 1)
        self.assertRegex(h, r'<script src="\.\./\.\./\.\./assets/merci\.js\?v=[0-9a-f]{8}" defer></script>')

    def test_noindex_toujours(self):
        h = (self.production / "fr/contact/merci/index.html").read_text(encoding="utf-8")
        self.assertEqual(h.count('<meta name="robots"'), 1)
        self.assertIn('<meta name="robots" content="noindex">', h[:h.index("</head>")])
        self.assertNotIn("noindex", (self.production / "fr/contact/index.html").read_text(encoding="utf-8"))
        with tempfile.TemporaryDirectory() as tmp:
            apercu = (support.construire(tmp, ["contact/merci/"], config={"apercu": True}) / "fr/contact/merci/index.html").read_text(encoding="utf-8")
        self.assertEqual(apercu.count('<meta name="robots"'), 1)
        self.assertIn('<meta name="robots" content="noindex, nofollow">', apercu)

    def test_variantes(self):
        h = (self.production / "fr/contact/merci/index.html").read_text(encoding="utf-8")
        for v in ("demo", "newsletter", "erreur", "refus"):
            self.assertIn(f'data-seul="{v}"', h)
        self.assertEqual(len(re.findall(r'data-seul="(?:newsletter|erreur|refus)" hidden', h)), 3)  # sans script : la variante démo
        refus = re.search(r'<p data-seul="refus" hidden>(.*?)</p>', h).group(1)
        self.assertNotIn("Vérifiez les champs", refus)  # un refus anti-robot ne met pas en cause les champs
        self.assertIn('<a href="mailto:team@corrext.com">team@corrext.com</a>', refus)
        self.assertIn(H.escape(contenus.texte("merci.newsletter.h1").split(". ", 1)[1], quote=True), h)
        self.assertIn("data-v-erreur=", h)


class TestEnvoiPhp(unittest.TestCase):
    """Le script lui-même se teste avec php (tests/test_envoi.php) ; ici, ce que le build en fait et des gardes lisibles
    sans php."""

    @classmethod
    def setUpClass(cls):
        cls.source = (ICI / "envoi.php").read_text(encoding="utf-8")

    @unittest.skipUnless(shutil.which("php"), "php absent de cette machine : lancer « php tests/test_envoi.php » sur Hostpoint")
    def test_envoi_php(self):
        r = subprocess.run(["php", str(build.ICI / "tests/test_envoi.php")], capture_output=True, text=True)
        self.assertEqual(r.returncode, 0, r.stdout + r.stderr)

    def test_ecrit_a_la_racine_avec_la_configuration(self):
        with tempfile.TemporaryDirectory() as tmp:
            sortie = support.construire(tmp, ["contact/"])
            php = (sortie / "envoi.php").read_text(encoding="utf-8")
        self.assertIn("const DESTINATAIRE = '" + build.CONFIG["destinataire"] + "';", php)
        self.assertIn("const EXPEDITEUR = '" + build.CONFIG["expediteur"] + "';", php)
        self.assertNotIn("{{", php)

    def test_configuration_invalide_refusee(self):
        for mauvais in ({"destinataire": ""}, {"destinataire": "team@corrext.com\nBcc: x@y.ch"}, {"destinataire": "a'b@c.ch"},
                        {"expediteur": "noreply@corrext.com'; system('x'); '"}):
            with self.assertRaises(ValueError, msg=mauvais):
                envoi.rendre({**build.CONFIG, **mauvais})

    def test_destinataire_jamais_lu_dans_la_requete(self):
        self.assertTrue(self.source.startswith("<?php\n"))
        self.assertNotIn("?>", self.source)  # pas de balise fermante : aucun octet parasite avant les en-têtes
        for interdit in ("$_GET", "$_REQUEST", "$_COOKIE", "$_POST['destinataire']", '$_POST["destinataire"]', "eval(", "extract("):
            self.assertNotIn(interdit, self.source)
        self.assertRegex(self.source, r"mail\(DESTINATAIRE,")
        self.assertEqual(self.source.count("{{destinataire}}"), 1)

    def test_fonctions_pures_et_regles(self):
        for f in ("function nettoyer_entete(", "function valider(array $post)", "function origine_autorisee(", "function reseau_ip(",
                  "function cle_ip(", "function limiter(array $etat, string $cle, int $maintenant)", "function compter(",
                  "function preparer_dossier(string $dossier)", "function encoder_entete(", "function composer(",
                  "function adresse_retour(", "function expediteur("):
            self.assertTrue(f in self.source, f)
        for attendu in ("http_response_code(303)", "http_response_code(405)", "FILTER_VALIDATE_EMAIL",
                        "const DELAI_MINIMAL = 3000;",  # millisecondes, champ duree mesuré dans le navigateur
                        "const DOMAINE = 'neur-on.ai';", "const PLAFOND_IP = 3;", "const FENETRE_IP = 600;",
                        "const PLAFOND_IP_HEURE = 6;", "const FENETRE_IP_HEURE = 3600;",
                        "const PLAFOND_GLOBAL = 60;", "const FENETRE_GLOBALE = 3600;",
                        "const EMAIL_INTERDITS = '\"<>,;';", "strpbrk($donnees['email'], EMAIL_INTERDITS) !== false",
                        "if ($source === '') {\n        return false;", "@rename($temporaire, $htaccess)",
                        "const DOSSIER_LIMITES = __DIR__ . '/../envoi-limites';", "flock($f, LOCK_EX)", "Require all denied",
                        "hash_hmac('sha256', reseau_ip($ip), $sel)", "inet_pton(", "mb_str_split(", "const OCTETS_PAR_MOT = 39;",
                        "fwrite($f, $json) === strlen($json)", "plafond global atteint", "HTTP_ORIGIN", "HTTP_REFERER"):
            self.assertTrue(attendu in self.source, attendu)
        # Nom et objet entièrement encodés : mb_encode_mimeheader laisse en clair les mots ASCII placés avant un accent
        self.assertNotIn("mb_encode_mimeheader", self.source)
        self.assertNotIn("sys_get_temp_dir", self.source)  # aucun repli : dossier inutilisable, envoi refusé
        self.assertNotIn("SERVER_NAME", self.source)  # le domaine vient de la constante DOMAINE, jamais de la requête
        self.assertNotIn("$_POST['t0']", self.source)  # plus de comparaison entre l'horloge du visiteur et celle du serveur
        self.assertNotRegex(self.source, r"\$/[a-z]*'")  # fin de chaîne par \z dans les expressions de validation

    def test_type_documentation_api(self):
        """Demande de documentation API (page API et on-premises, 2026-10-21) : mêmes champs obligatoires que la démo,
        objet d'e-mail distinct."""
        obl = re.search(r"const OBLIGATOIRES = \[(.*?)\];", self.source, re.S).group(1)
        champs = dict(re.findall(r"'(\w+)' => (\[[^\]]*\])", obl))
        self.assertEqual(champs["documentation"], champs["demo"])
        self.assertIn("'documentation' => 'Demande de documentation API'", self.source)

    def test_une_adresse_n_epuise_pas_le_plafond_global(self):
        """Sur la fenêtre globale, une adresse obtient au plus PLAFOND_IP_HEURE envois : bien moins que PLAFOND_GLOBAL."""
        c = {n: int(v) for n, v in re.findall(r"^const (PLAFOND_\w+|FENETRE_\w+) = (\d+);", self.source, re.M)}
        self.assertEqual(sorted(c), ["FENETRE_GLOBALE", "FENETRE_IP", "FENETRE_IP_HEURE", "PLAFOND_GLOBAL", "PLAFOND_IP", "PLAFOND_IP_HEURE"])
        self.assertGreaterEqual(c["FENETRE_IP_HEURE"], c["FENETRE_GLOBALE"])
        self.assertLessEqual(c["PLAFOND_IP_HEURE"] * 5, c["PLAFOND_GLOBAL"])
        self.assertLessEqual(c["PLAFOND_IP"], c["PLAFOND_IP_HEURE"])

    def test_accolades_et_parentheses_equilibrees(self):
        """Garde minimale tant que php manque sur la machine de build : délimiteurs équilibrés hors chaînes et commentaires."""
        code = re.sub(r"/\*.*?\*/|//[^\n]*|'(?:[^'\\]|\\.)*'|\"(?:[^\"\\]|\\.)*\"", "", self.source, flags=re.S)
        for o, f in ("{}", "()", "[]"):
            self.assertEqual(code.count(o), code.count(f), o + f)

    def test_test_php_fourni(self):
        t = (ICI / "tests/test_envoi.php").read_text(encoding="utf-8")
        self.assertIn("require __DIR__ . '/../envoi.php';", t)
        for cas in ("saut de ligne dans le nom", "saut de ligne dans l'e-mail", "champ piège", "moins de 3 s", "duree absente",
                    "par IP : 3 envois en 10 minutes", "par IP : 6 envois par heure", "global : 60 envois par heure",
                    "une seule adresse n'épuise jamais le plafond global", "sans Origin ni Referer : refusé",
                    'e-mail avec " < > , ou ; refusé', ".htaccess écrit par renommage", "Origin d'un autre site refusé",
                    "compter : fichier partagé", "lignes de 75 caractères au plus", "rien en clair hors de",
                    "virgule légitime dans un nom accentué", "objet décodé", "IPv6 ramenée à son réseau /64",
                    "plafond global noté au journal", "Require all denied"):
            self.assertTrue(cas in t, cas)


class TestTextesC(unittest.TestCase):
    def setUp(self):
        self.f = json.loads((ICI / "src/data/contenus-v2/C-suivi.json").read_text(encoding="utf-8"))

    def test_lot_et_statut(self):
        self.assertEqual(self.f["lot"], "C")
        for e in self.f["entrees"]:
            self.assertEqual(e["statut"], "a_relire", e["cle"])
            self.assertTrue(e["source"], e["cle"])

    def test_paragraphe_google_analytics_a_relire_non_publie(self):
        e = next(x for x in self.f["entrees"] if x["cle"] == "confidentialite.google-analytics")
        self.assertEqual(e["page"], "protection-des-donnees/")
        for attendu in ("Google Analytics", "Google les reçoit", "accord", "retirer", "« Préférences cookies »", "cookie"):
            self.assertIn(attendu, e["texte"])
        self.assertNotRegex(e["texte"], r"\b(art\.|LPD|nLPD|RGPD|ATF|loi)\b")  # aucune référence légale
        for apercu in (True, False):  # ni sur l'aperçu, ni en production
            page = support.chemin(support.site_complet(apercu=apercu), "protection-des-donnees/").read_text(encoding="utf-8")
            self.assertNotIn(e["texte"][:80], page, apercu)


if __name__ == "__main__":
    unittest.main()
