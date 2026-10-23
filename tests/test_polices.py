"""Polices hébergées sur le site (décision de Fabien du 2026-10-14) : plus aucun appel à Google Fonts avant tout
consentement, fichiers woff2 et licences OFL sous assets/fonts/, @font-face dans assets/composants/polices.css
(concaténé à site.css au build), préchargement de Source Serif 4 partout et d'Inter seulement là où la page s'en
sert, cache long des polices, feuilles et scripts dans le .htaccess."""
import posixpath
import re
import sys
import tempfile
import unittest
from pathlib import Path
from unittest import mock

ICI = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ICI))
import build  # noqa: E402
from outils import post  # noqa: E402
from tests import support  # noqa: E402

DOMAINES_GOOGLE = (b"fonts.googleapis.com", b"fonts.gstatic.com")
BINAIRES = {".woff2", ".png", ".jpg", ".jpeg", ".webp", ".ico", ".pdf", ".gif"}
POLICES_CSS = ICI / "assets/composants/polices.css"
LICENCES = {"OFL-Inter.txt": "The Inter Project Authors", "OFL-SourceSerif4.txt": "Adobe"}
# Les deux polices critiques : Source Serif 4 300 latin sur toutes les pages, Inter 400 latin quand la page s'en sert
SERIF_CRITIQUE = "assets/fonts/source-serif-4-latin.woff2"
INTER_CRITIQUE = "assets/fonts/inter-latin.woff2"
# Plages unicode-range de la CSS de Google Fonts (relevées le 2026-10-14), identiques pour Inter et Source Serif 4
LATIN = ("U+0000-00FF, U+0131, U+0152-0153, U+02BB-02BC, U+02C6, U+02DA, U+02DC, U+0304, U+0308, U+0329, U+2000-206F, "
         "U+20AC, U+2122, U+2191, U+2193, U+2212, U+2215, U+FEFF, U+FFFD")
LATIN_EXT = ("U+0100-02BA, U+02BD-02C5, U+02C7-02CC, U+02CE-02D7, U+02DD-02FF, U+0304, U+0308, U+0329, U+1D00-1DBF, "
             "U+1E00-1E9F, U+1EF2-1EFF, U+2020, U+20A0-20AB, U+20AD-20C4, U+2113, U+2C60-2C7F, U+A720-A7FF")
PLAGES = {
    "fonts/inter-latin.woff2": LATIN, "fonts/inter-latin-ext.woff2": LATIN_EXT,
    "fonts/source-serif-4-latin.woff2": LATIN, "fonts/source-serif-4-latin-ext.woff2": LATIN_EXT,
    "fonts/source-serif-4-italic-latin.woff2": LATIN, "fonts/source-serif-4-italic-latin-ext.woff2": LATIN_EXT,
}
UN_AN = "public, max-age=31536000, immutable"
# Écran Corrext : jeton de classe exact « cr » ou « cx » (« crit », « cr-home », « sp-app-cx » ne comptent pas)
ECRAN_CORREXT = re.compile(r'class="(?:[^"]*\s)?c[rx](?:\s|")')


def blocs_font_face(css):
    """Les @font-face d'une feuille, lus en dictionnaires : famille, style, graisses (bas, haut), url, plage."""
    blocs = []
    for corps in re.findall(r"@font-face\s*\{(.*?)\}", css, re.S):
        def prop(nom):
            m = re.search(r"(?<![\w-])" + nom + r"\s*:\s*([^;]+);", corps)
            return m.group(1).strip() if m else None
        graisses = [int(g) for g in (prop("font-weight") or "0").split()]
        blocs.append({
            "famille": (prop("font-family") or "").strip("\"'"),
            "style": prop("font-style"),
            "graisses": (graisses[0], graisses[-1]),
            "affichage": prop("font-display"),
            "plage": prop("unicode-range"),
            "src": prop("src") or "",
            "url": (re.search(r"url\(\s*[\"']?([^)\"']+)", corps) or [None, None])[1],
        })
    return blocs


class TestPolices(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.tmp = tempfile.TemporaryDirectory()
        cls.addClassCleanup(cls.tmp.cleanup)
        cls.sortie = support.construire(cls.tmp.name, pages=tuple(build.PAGES))
        cls.css = POLICES_CSS.read_text(encoding="utf-8") if POLICES_CSS.exists() else ""
        cls.blocs = blocs_font_face(cls.css)

    def test_aucun_appel_a_google_dans_le_site_construit(self):
        """Pages, 404, racine, redirections, feuilles et scripts : ni fonts.googleapis.com ni fonts.gstatic.com."""
        fichiers = [f for f in self.sortie.rglob("*") if f.is_file() and f.suffix not in BINAIRES]
        self.assertGreater(len(fichiers), 150)  # le site entier a bien été parcouru
        fautifs = [str(f.relative_to(self.sortie)) for f in fichiers
                   if any(d in f.read_bytes() for d in DOMAINES_GOOGLE)]
        self.assertEqual(fautifs, [])

    def test_chaque_url_de_polices_css_pointe_vers_un_fichier_du_site_construit(self):
        """Les URL sont relatives à assets/site.css (« fonts/... ») et chacune existe sous docs/assets/fonts/."""
        urls = re.findall(r"url\(\s*[\"']?([^)\"']+)", self.css)
        self.assertTrue(urls, "polices.css doit déclarer des polices")
        site_css = self.sortie / "assets/site.css"
        self.assertIn("/* composants/polices.css */", site_css.read_text(encoding="utf-8"))
        for url in urls:
            self.assertRegex(url, r"^fonts/[\w.-]+\.woff2$", "URL relative à assets/site.css attendue")
            self.assertTrue((site_css.parent / url).is_file(), url)

    def test_aucun_fichier_de_police_orphelin(self):
        """Chaque woff2 du dépôt est déclaré, et les seuls sous-ensembles livrés sont latin et latin-ext."""
        deposes = {f.name for f in (ICI / "assets/fonts").glob("*.woff2")}
        declares = {posixpath.basename(b["url"]) for b in self.blocs}
        self.assertEqual(deposes, declares)
        for nom in deposes:
            self.assertRegex(nom, r"-latin(-ext)?\.woff2$", nom)

    def test_licences_ofl_presentes_dans_le_depot_et_le_site_construit(self):
        for nom, titulaire in LICENCES.items():
            for dossier in (ICI / "assets/fonts", self.sortie / "assets/fonts"):
                texte = (dossier / nom).read_text(encoding="utf-8")
                self.assertIn("SIL OPEN FONT LICENSE Version 1.1", texte, f"{dossier}/{nom}")
                self.assertIn(titulaire, texte, f"{dossier}/{nom}")

    def test_font_face_inter_et_source_serif(self):
        """Mêmes familles que dans le CSS du site, mêmes graisses que l'ancien appel à Google, swap, plages latin."""
        self.assertEqual({b["famille"] for b in self.blocs}, {"Inter", "Source Serif 4"})
        for b in self.blocs:
            self.assertEqual(b["affichage"], "swap", b["url"])
            self.assertTrue(b["plage"] and b["plage"].startswith("U+"), b["url"])
            self.assertIn('format("woff2")', b["src"].replace("'", '"'), b["url"])
        inter = [b for b in self.blocs if b["famille"] == "Inter"]
        self.assertEqual({b["style"] for b in inter}, {"normal"})
        for graisse in (400, 500, 600):
            self.assertTrue(all(b["graisses"][0] <= graisse <= b["graisses"][1] for b in inter), graisse)
        serif = [b for b in self.blocs if b["famille"] == "Source Serif 4"]
        self.assertEqual({(b["style"], b["graisses"]) for b in serif}, {("normal", (300, 300)), ("italic", (300, 300))})
        for groupe in {(b["famille"], b["style"]) for b in self.blocs}:  # latin et latin étendu, par police et style
            fichiers = [b["url"] for b in self.blocs if (b["famille"], b["style"]) == groupe]
            self.assertEqual(sorted(f.endswith("-latin-ext.woff2") for f in fichiers), [False, True], groupe)
        site = (self.sortie / "assets/site.css").read_text(encoding="utf-8")
        self.assertIn('"Source Serif 4"', site)
        self.assertIn('"Inter"', site)

    def test_plage_unicode_exacte_de_chaque_fichier(self):
        """Chaque woff2, romain et italique compris, porte la plage de la CSS de Google, sans ajout ni oubli."""
        plages = {b["url"]: [r.strip() for r in b["plage"].split(",")] for b in self.blocs}
        self.assertEqual(set(plages), set(PLAGES))
        for fichier, attendue in PLAGES.items():
            self.assertEqual(plages[fichier], attendue.split(", "), fichier)

    def test_commentaire_remplacer_une_police_impose_un_nouveau_nom(self):
        self.assertIn("changer son nom de fichier", self.css)
        self.assertIn("changer son nom de fichier", (self.sortie / ".htaccess").read_text(encoding="utf-8"))

    def pages_construites(self):
        """Toutes les pages du site construit, 404 comprise : (page, fichier, HTML). La page de l'accueil est « »."""
        fichiers = [(p, self.sortie / "fr" / p / "index.html") for p in build.PAGES] + [("404.html", self.sortie / "404.html")]
        return [(page, f, f.read_text(encoding="utf-8")) for page, f in fichiers]

    def test_source_serif_partout_inter_selon_la_regle_sur_toutes_les_pages(self):
        """Source Serif 4 300 latin est préchargée sur chaque page. Inter 400 latin l'est seulement si la page contient
        un écran Corrext (classe « cr » ou « cx ») ou une classe qui pose var(--num). Chaque href existe."""
        num = build.classes_num((self.sortie / "assets/site.css").read_text(encoding="utf-8"))
        pages = self.pages_construites()
        self.assertEqual(len(pages), len(build.PAGES) + 1)
        avec_inter = sans_inter = 0
        for page, fichier, html in pages:
            nom = page or "accueil"
            self.assertNotIn("@INTER@", html, nom)
            jetons = {j for v in re.findall(r'class="([^"]*)"', html) for j in v.split()}
            attend_inter = bool(ECRAN_CORREXT.search(html)) or any(classes <= jetons for classes in num)
            racine = "" if page == "404.html" else "../" * (page.count("/") + 1)  # la 404 est servie depuis sa <base>
            liens = re.findall(r'<link rel="preload"[^>]*as="font"[^>]*>', html)
            hrefs = [re.search(r'href="([^"]+)"', lien).group(1) for lien in liens]
            self.assertEqual(hrefs, [racine + SERIF_CRITIQUE] + ([racine + INTER_CRITIQUE] if attend_inter else []), nom)
            for lien, href in zip(liens, hrefs):
                self.assertIn('type="font/woff2"', lien, nom)
                self.assertRegex(lien, r"\scrossorigin(>|\s|=)", nom)
                self.assertTrue((fichier.parent / href).resolve().is_file(), f"{nom} : {href}")
            avec_inter, sans_inter = avec_inter + attend_inter, sans_inter + (not attend_inter)
        self.assertGreater(avec_inter, 20)  # la règle n'est ni toujours vraie ...
        self.assertGreater(sans_inter, 20)  # ... ni toujours fausse

    def test_htaccess_cache_d_un_an_pour_les_polices_les_feuilles_et_les_scripts(self):
        """Le .htaccess généré pose Cache-Control public, un an, immutable, sous <IfModule mod_headers.c>."""
        lignes = (self.sortie / ".htaccess").read_text(encoding="utf-8").splitlines()
        blocs, ouverts, filtre = {}, [], None
        for ligne in (l.strip() for l in lignes):
            if ligne.startswith("<IfModule"):
                ouverts.append(ligne)
            elif ligne == "</IfModule>":
                ouverts.pop()
            elif ligne.startswith("<FilesMatch"):
                filtre = re.search(r'<FilesMatch "([^"]+)">', ligne).group(1)
            elif ligne == "</FilesMatch>":
                filtre = None
            elif ligne.startswith("Header "):
                self.assertEqual(ouverts, ["<IfModule mod_headers.c>"], ligne)  # jamais hors du garde-fou
                self.assertIsNotNone(filtre, ligne)
                blocs.setdefault(filtre, []).append(ligne)
        self.assertEqual(ouverts, [])
        selon = {fichier: [f for f in blocs if re.search(f, fichier)]
                 for fichier in ("inter-latin.woff2", "source-serif-4-italic-latin-ext.woff2", "site.css", "nav.js", "sim.js")}
        for fichier, filtres in selon.items():
            self.assertEqual(len(filtres), 1, fichier)
            self.assertEqual(blocs[filtres[0]], [f'Header set Cache-Control "{UN_AN}"'], fichier)
        for fichier in ("index.html", "OFL-Inter.txt", "robots.txt", "neuron-logo.png"):  # ni pages ni images : pas de cache d'un an
            for f in blocs:
                if re.search(f, fichier):
                    self.assertNotIn(UN_AN, " ".join(blocs[f]), fichier)

    def test_toute_feuille_et_tout_script_local_porte_une_version(self):
        """Invariant du cache d'un an : une feuille ou un script change d'URL (?v=empreinte) quand son contenu change."""
        references = 0
        for page in sorted(self.sortie.rglob("*.html")):
            html = page.read_text(encoding="utf-8")
            liens = re.findall(r'<link\b[^>]*\b(?:rel="stylesheet"|as="(?:style|script)")[^>]*>', html)
            urls = [re.search(r'href="([^"]+)"', l).group(1) for l in liens] + re.findall(r'<script\b[^>]*\bsrc="([^"]+)"', html)
            for url in urls:
                if url.startswith(("http:", "https:", "//")):
                    continue  # ressource tierce : hors du cache du site
                references += 1
                self.assertRegex(url, r"\?v=[0-9a-f]{8}$", f"{page.relative_to(self.sortie)} : {url}")
        self.assertGreater(references, 300)  # le site entier a bien été parcouru


class TestRegleInter(unittest.TestCase):
    """La règle qui décide du préchargement d'Inter, sur des HTML écrits à la main."""

    def test_ecran_corrext_jeton_exact_cr_ou_cx(self):
        for classe in ("cr", "cx", "app cr", "cr app", "a cx b", "st cr cr-home"):
            self.assertTrue(build.utilise_inter(f'<div class="{classe}">', css=""), classe)
        for classe in ("crit", "cr-home", "xcr", "a-cr b", "cxx", "cx-zone", "sp-app-cx", "ccr", "criteria cr-x"):
            self.assertFalse(build.utilise_inter(f'<div class="{classe}">', css=""), classe)
        self.assertFalse(build.utilise_inter("<p>cr cx</p>", css=""))  # le texte n'est pas une classe

    def test_classes_des_selecteurs_qui_utilisent_var_num(self):
        css = """
        :root{--num:"Inter",sans-serif}
        /* .commentaire{font:var(--num)} */
        .bt-p .n{font:500 40px/48px var(--num)}
        .a,.b .c:not(.d){font-family:var(--num);margin:0}
        .autre{font:400 16px sans-serif}
        @media (max-width:800px){
          .m .n{font:500 20px var(--num)}
        }
        h1{font:var(--num)}
        """
        self.assertEqual(sorted(map(sorted, build.classes_num(css))),
                         [[], ["a"], ["b", "c"], ["bt-p", "n"], ["m", "n"]])

    def test_les_selecteurs_reels_de_site_css(self):
        css = (ICI / "assets/site.css").read_text(encoding="utf-8")
        reels = build.classes_num(css)
        for attendu in ({"bt-p", "n"}, {"cd", "kv"}, {"cd", "kv-ab"}, {"tl", "n"}, {"couv"}):
            self.assertIn(frozenset(attendu), reels)

    def test_chiffre_en_num_demande_toutes_les_classes_du_selecteur(self):
        css = ".bt-p .n{font:500 40px var(--num)} .couv{font:500 40px var(--num)}"
        self.assertTrue(build.utilise_inter('<div class="bt-p"><b class="n">', css=css))
        self.assertTrue(build.utilise_inter('<i class="couv x">', css=css))
        self.assertFalse(build.utilise_inter('<b class="n">', css=css))  # « n » seul : le sélecteur ne s'applique pas
        self.assertFalse(build.utilise_inter('<div class="bt-p">', css=css))
        self.assertFalse(build.utilise_inter('<i class="couverture">', css=css))
        self.assertTrue(build.utilise_inter('<h1 class="x">', css="h1{font:var(--num)}"))  # sans classe : toujours vrai


class TestPrechargementApresPostTraitement(unittest.TestCase):
    def test_inter_decide_sur_le_html_final(self):
        """Un post-traitement qui ajoute un écran Corrext fait précharger Inter : la décision suit post.appliquer."""
        page = "mentions-legales/"  # page de texte : sans post-traitement, Inter n'y est pas préchargée
        with tempfile.TemporaryDirectory() as tmp:
            dossier = Path(tmp) / "post"
            dossier.mkdir()
            (dossier / "a_ecran.py").write_text(
                'def traiter(html, page):\n'
                f'    if page != "{page}":\n'
                '        return html\n'
                '    return html.replace("</body>", \'<div class="app cr"></div></body>\')\n', encoding="utf-8")
            avec = support.construire(Path(tmp) / "a", ["", page], patches=[mock.patch.object(post, "DOSSIER", dossier)])
            sans = support.construire(Path(tmp) / "b", ["", page])
            lien = 'href="../../assets/fonts/inter-latin.woff2"'
            texte = (avec / "fr" / page / "index.html").read_text(encoding="utf-8")
            self.assertIn(lien, texte)
            self.assertNotIn("@INTER@", texte)
            self.assertNotIn("inter-latin", (sans / "fr" / page / "index.html").read_text(encoding="utf-8"))
            self.assertIn("inter-latin", (avec / "fr/index.html").read_text(encoding="utf-8"))  # l'accueil a un écran Corrext


if __name__ == "__main__":
    unittest.main()
