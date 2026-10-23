"""Schéma « qui fait quoi » (lot B, spec V2 § 5) : une section par page Corrext, LexMachina et CHnell, définitions
dans un <dl> lisible sans CSS, liens vers les trois pages, hébergement suisse, moteurs tiers au choix, animation en
transform et opacity seulement, déclenchée à la visibilité, mouvement réduit respecté."""
import html as H
import json
import re
import subprocess
import sys
import unittest
from pathlib import Path

ICI = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ICI))
sys.path.insert(0, str(ICI / "outils/composer"))
import build  # noqa: E402
import schema_produits  # noqa: E402
from outils import contenus  # noqa: E402
from outils.post import schema_produits as schema_post  # noqa: E402

PAGES = ("corrext/", "corrext/chnell/")  # plus sur la page LexMachina (Fabien, 2026-10-16)
LIENS = {"LexMachina": "lexmachina/", "Corrext": "corrext/", "CHnell": "corrext/chnell/"}
JSON_B = ICI / "src/data/contenus-v2/B-schema.json"
CSS = ICI / "assets/composants/schema-produits.css"
JS = ICI / "assets/global/schema-produits.js"
MOUVEMENT = {"transform", "opacity"}


def texte_brut(h):
    """Texte d'un fragment HTML tel qu'un lecteur sans CSS le voit (éléments « hidden » retirés)."""
    h = re.sub(r"<(dd|div|span)\b[^>]*\bhidden\b[^>]*>.*?</\1>", " ", h, flags=re.S)
    return re.sub(r"\s+", " ", H.unescape(re.sub(r"<[^>]+>", " ", h))).replace(" ,", ",").replace(" .", ".").strip()


def section_de(h):
    return re.search(r'<section class="sec sp".*?</section>', h, re.S).group(0)


def _brut(cle):
    """Texte de contenus-v2 tel que texte_brut() le lit : espaces insécables normalisées."""
    return contenus.texte(cle).replace("\xa0", " ")


class TestSchema(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        subprocess.run([sys.executable, str(ICI / "build.py")], check=True, cwd=ICI, stdout=subprocess.DEVNULL)
        cls.pages = {p: build.chemin_page(p).read_text(encoding="utf-8") for p in build.PAGES}
        cls.section = schema_produits.rendre()

    def test_trois_pages_et_definitions(self):
        for p in PAGES:
            h = build.chemin_page(p).read_text(encoding="utf-8")
            self.assertEqual(h.count('class="sec sp"'), 1, p)
            for nom in ("Corrext", "LexMachina", "CHnell"):
                self.assertRegex(h, r'<dt[^>]*>' + nom, p)

    def test_absent_des_autres_pages(self):
        for p, h in self.pages.items():
            if p not in PAGES and p != "":  # l'accueil l'intègre par son composeur (lot D, tests/test_trame.py)
                self.assertNotIn('class="sec sp"', h, p or "accueil")

    def test_section_complete_sans_h1(self):
        s = self.section.strip()
        self.assertTrue(s.startswith('<section class="sec sp"'), s[:60])
        self.assertTrue(s.endswith("</section>"))
        self.assertEqual(s.count("<section"), 1)
        self.assertEqual(len(re.findall(r"<h2[ >]", s)), 1)
        self.assertNotRegex(s, r"<h1[ >]")

    def test_place_apres_la_premiere_scene_sinon_apres_le_hero(self):
        """Sauf la page CHnell, où il suit « Trois situations » (outils/post/schema_produits.APRES)."""
        for p in PAGES:
            h = self.pages[p]
            sections = re.findall(r"<section\b[^>]*>.*?</section>", h[h.index("<main"):], re.S)
            i = next(k for k, s in enumerate(sections) if s.startswith('<section class="sec sp"'))
            autres = sections[:i] + sections[i + 1:]
            scenes = [k for k, s in enumerate(autres) if "data-sim" in s or 'class="ech"' in s]
            attendu = scenes[0] if scenes else 0  # sinon le hero, première section de la page
            if p in schema_post.APRES:  # CHnell : après « Trois situations »
                attendu = next(k for k, s in enumerate(autres) if schema_post.APRES[p] in s)
            self.assertEqual(i - 1, attendu, p)
            if not scenes:
                self.assertIn('class="hero"', sections[i - 1], p)

    def test_definitions_lisibles_sans_css(self):
        dl = re.search(r"<dl\b.*?</dl>", self.section, re.S).group(0)
        self.assertEqual(re.findall(r"<dt[^>]*>([^<]*)</dt>", dl), ["LexMachina", "Corrext", "CHnell"])
        # Les illustrations sont masquées sans CSS et pour les aides techniques
        illustrations = re.findall(r'<dd\b[^>]*\bsp-ui\b[^>]*>', dl)
        self.assertEqual(len(illustrations), 3)
        for dd in illustrations:
            self.assertRegex(dd, r"\shidden[\s>]")
            self.assertIn('aria-hidden="true"', dd)
            self.assertIn("data-ui", dd)
        lu = texte_brut(dl)
        for cle in ("schema.lexmachina.def", "schema.corrext.def", "schema.chnell.def"):
            self.assertIn(_brut(cle), lu, cle)
        # Ordre de lecture : chaque nom suivi de sa définition
        positions = [lu.index(x) for x in ("LexMachina", _brut("schema.lexmachina.def"), "Corrext",
                                           _brut("schema.corrext.def"), "CHnell", _brut("schema.chnell.def"))]
        self.assertEqual(positions, sorted(positions))

    def test_liens_vers_les_trois_pages(self):
        for chemin in LIENS.values():
            self.assertIn(f'href="{{{{ROOT}}}}{chemin}"', self.section)
        for p in PAGES:
            s = section_de(self.pages[p])
            courants = re.findall(r'<a\b[^>]*aria-current="page"[^>]*>', s)
            self.assertEqual(len(courants), 1, p)
            self.assertIn(f'href="{"../" * (p.count("/") + 1)}fr/{p}"', courants[0], p)

    def test_moteurs_tiers_au_choix_sans_legende_d_hebergement(self):
        lu = texte_brut(self.section)
        # légende d'hébergement retirée sous l'animation (demande de Fabien du 2026-10-15)
        self.assertNotIn(contenus.texte("schema.hebergement"), lu)
        self.assertNotIn('class="sp-h"', self.section)
        tiers = contenus.texte("schema.lexmachina.tiers")
        self.assertIn(tiers, lu)
        self.assertIn("au choix", tiers)
        for moteur in ("DeepL Pro", "Azure OpenAI GPT", "Claude"):
            self.assertIn(moteur, tiers)
        self.assertNotRegex(lu, r"(DeepL( Pro)?|GPT|Claude)[\s-]*\d")  # jamais de numéro de version

    def test_textes_nouveaux_dans_le_json_du_lot(self):
        f = json.loads(JSON_B.read_text(encoding="utf-8"))
        self.assertEqual(f["lot"], "B")
        cles = {e["cle"] for e in f["entrees"]}
        for cle in ("schema.titre", "schema.intro", "schema.lexmachina.def", "schema.lexmachina.tiers",
                    "schema.corrext.def", "schema.corrext.role", "schema.chnell.def", "schema.chnell.lookup",
                    "schema.hebergement"):
            self.assertIn(cle, cles)
        for e in f["entrees"]:
            self.assertIn(e["statut"], ("a_relire", "valide"), e["cle"])  # validés par Fabien le 2026-10-23
            self.assertEqual(e["page"], "*", e["cle"])  # commun aux pages qui affichent le schéma
            self.assertTrue(e["source"].strip(), e["cle"])
        titre = re.search(r"<h2[^>]*>(.*?)</h2>", self.section, re.S).group(1)
        self.assertEqual(texte_brut(titre), contenus.texte("schema.titre"))


class TestAnimation(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.css = CSS.read_text(encoding="utf-8")
        cls.js = JS.read_text(encoding="utf-8")

    def test_transitions_et_images_cles_en_transform_et_opacity(self):
        for decl in re.findall(r"transition:([^;}]+)", self.css):
            for partie in decl.split(","):
                self.assertIn(partie.split()[0], MOUVEMENT | {"none"}, decl)
        for corps in re.findall(r"@keyframes\s+[\w-]+\s*\{((?:[^{}]*\{[^}]*\})*)\s*\}", self.css):
            for prop in re.findall(r"([\w-]+)\s*:", corps):
                self.assertIn(prop, MOUVEMENT, corps)
        for images in re.findall(r"\.animate\(\s*\[(.*?)\]", self.js, re.S):
            for prop in re.findall(r"(\w+)\s*:", images):
                self.assertIn(prop, MOUVEMENT | {"offset", "easing"}, images)  # offset et easing ne sont pas animés

    def test_declenchee_a_la_visibilite_et_mouvement_reduit(self):
        self.assertIn("IntersectionObserver", self.js)
        self.assertIn("prefers-reduced-motion: reduce", self.js)
        # Rejouée tant que le schéma est à l'écran (proposition A, 2026-10-15) : le cycle suivant attend la visibilité,
        # aucune animation CSS sans fin
        self.assertIn("sc.__visible", self.js)
        self.assertIn("__enAttente", self.js)
        self.assertNotIn("infinite", self.css)
        # En mouvement réduit, le script s'arrête avant de poser l'état de départ
        sortie = re.search(r'matchMedia\("\(prefers-reduced-motion: reduce\)"\)\.matches\)\s*return;', self.js)
        self.assertIsNotNone(sortie, "sortie du script en mouvement réduit introuvable")
        self.assertLess(sortie.end(), self.js.index('classList.add("sp-pret")'))
        # L'état de départ de l'animation n'existe que sous la classe posée par le script : sans script ou en
        # mouvement réduit, le schéma s'affiche dans son état final
        sans_images_cles = re.sub(r"@keyframes\s+[\w-]+\s*\{(?:[^{}]*\{[^}]*\})*\s*\}", "", self.css)
        for regle in re.findall(r"([^{}]+)\{[^}]*opacity:0[;}]", sans_images_cles):
            self.assertIn(".sp-pret", regle, regle)

    def test_textes_d_au_moins_11_px(self):
        for taille in re.findall(r"font:[^;}]*?([\d.]+)px", self.css) + re.findall(r"font-size:([\d.]+)px", self.css):
            self.assertGreaterEqual(float(taille), 11, taille)

    def test_empilement_en_colonne_sur_mobile(self):
        self.assertRegex(self.css, r"@media \(max-width:1023px\)\{[^@]*\.sp-dl\{[^}]*grid-template-columns:minmax\(0,1fr\)")

    def test_script_sans_texte_affiche(self):
        for c in re.findall(r'"([^"\\]*)"', self.js):
            self.assertIsNone(re.search(r"[a-zà-ÿ]{3,} [a-zà-ÿ]{3,} [a-zà-ÿ]{3,}", c, re.I), c)


if __name__ == "__main__":
    unittest.main()
