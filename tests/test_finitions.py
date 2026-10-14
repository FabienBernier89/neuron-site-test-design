"""Finitions de la relecture finale (vague de correction avant publication) : rôle des scènes animées, cibles
tactiles, encart newsletter, titres du blog, suivi des appels à l'action."""
import re
import sys
import unittest
from pathlib import Path

ICI = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ICI))
sys.path.insert(0, str(ICI / "outils/composer"))
import build  # noqa: E402
from tests import support  # noqa: E402

SCENE = re.compile(r'<div class="st"[^>]*>')


class TestRoleDesScenes(unittest.TestCase):
    def test_gabarit_scene_animee_role_group(self):
        import comp
        anime = SCENE.search(comp.scene(100, 100, "", sim="essai", label="Démonstration")).group(0)
        self.assertIn('role="group" aria-label="Démonstration"', anime)
        fixe = SCENE.search(comp.scene(100, 100, "", label="Capture")).group(0)
        self.assertIn('role="img" aria-label="Capture"', fixe)
        sans = SCENE.search(comp.scene(100, 100, "", sim="essai")).group(0)
        self.assertNotIn("role=", sans)
        self.assertNotIn("aria-label", sans)

    def test_aucune_scene_nommee_sans_role(self):
        docs = support.site_complet(apercu=True)
        animees = 0
        for p in build.PAGES:
            for balise in SCENE.findall(support.chemin(docs, p).read_text(encoding="utf-8")):
                if "aria-label=" in balise:
                    self.assertRegex(balise, r'\srole="(?:group|img)"', p)
                    animees += "data-sim=" in balise
        self.assertGreaterEqual(animees, 20)


def regles(css, selecteur):
    """Déclarations des règles dont la liste de sélecteurs contient exactement `selecteur` (hors @media)."""
    sans_media = re.sub(r"@media[^{]*\{(?:[^{}]*\{[^{}]*\})*[^{}]*\}", "", re.sub(r"/\*.*?\*/", "", css, flags=re.S))
    return [d for liste, d in re.findall(r"([^{}]+)\{([^{}]*)\}", sans_media)
            if selecteur in [x.strip() for x in liste.split(",")]]


class TestCiblesTactiles(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.css = (support.site_complet(apercu=True) / "assets/site.css").read_text(encoding="utf-8")

    def test_bouton_pause_24_px_au_moins(self):
        d = " ".join(regles(self.css, ".sim-pause"))
        for prop in ("width", "height"):
            valeurs = [int(v) for v in re.findall(r"(?:^|[;{\s])" + prop + r":(\d+)px", d)]
            self.assertTrue(valeurs and valeurs[-1] >= 24, (prop, valeurs))
        # dans une scène réduite (--k < 1, colonnes étroites et mobile), le bouton garde 24 px à l'écran
        self.assertIn("transform:scale(calc(1 / var(--k,1)))", d)

    def test_lien_telephone_des_pages_legales(self):
        """Le lien prend la hauteur de ligne de l'adresse (24 px) : bloc en ligne, texte inchangé."""
        d = " ".join(regles(self.css, '.legal-card a[href^="tel:"]'))
        self.assertIn("display:inline-block", d)
        for p in ("mentions-legales/", "protection-des-donnees/"):
            src = (build.SRC / "pages" / p / "index.html").read_text(encoding="utf-8")
            self.assertIn('<span>Tél. : <a href="tel:+41442919419">+41 44 291 94 19</a></span>', src, p)


class TestEncartNewsletter(unittest.TestCase):
    def setUp(self):
        from outils.composer import newsletter
        self.newsletter = newsletter
        self.demo = newsletter.encart({"apercu": True})
        self.prod = newsletter.encart({"apercu": False})

    def test_consentement_avant_le_bouton(self):
        for e in (self.demo, self.prod):
            self.assertLess(e.index('name="email"'), e.index('name="consentement"'))
            self.assertLess(e.index('name="consentement"'), e.index('type="submit"'))

    def test_asterisque_sur_l_e_mail_requis(self):
        label = re.search(r'<label for="nl-email">(.*?)</label>', self.demo).group(1)
        self.assertTrue(label.endswith('<span class="req" aria-hidden="true">*</span>'), label)

    def test_region_annoncee_toujours_presente(self):
        """Plus de role="status" sur un élément masqué : une région aria-live présente dès le chargement, vide ; nav.js
        y injecte l'avis à l'envoi, ce qui le fait annoncer."""
        self.assertNotIn('role="status"', self.demo)
        avis = re.search(r'<p class="avis"[^>]*>(.*?)</p>', self.demo)
        self.assertEqual(avis.group(1), "")
        ouverture = avis.group(0)
        self.assertIn('aria-live="polite"', ouverture)
        self.assertNotIn("hidden", ouverture)
        self.assertIn(f'data-avis="{self.newsletter.AVIS_DEMO}"', ouverture)
        nav = (ICI / "assets/nav.js").read_text(encoding="utf-8")
        self.assertIn('avis.textContent = avis.getAttribute("data-avis")', nav)
        css = (ICI / "assets/composants/newsletter.css").read_text(encoding="utf-8")
        self.assertRegex(css, r"\.nl-f \.avis:empty\{[^}]*position:absolute")  # vide : hors du flux, jamais display:none

    def test_encart_des_pages_sans_status_masque(self):
        docs = support.site_complet(apercu=True)
        vus = 0
        for p in build.PAGES:
            h = support.chemin(docs, p).read_text(encoding="utf-8")
            for encart in re.findall(r'<section class="nl-s".*?</section>', h, re.S):
                vus += 1
                self.assertNotIn('role="status"', encart, p)
                self.assertRegex(encart, r'<p class="avis" aria-live="polite" data-libre data-avis="[^"]+"></p>', p)
        self.assertGreater(vus, 100)


class TestBlog(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        from outils.post import titres_blog
        cls.registre = titres_blog.registre()
        cls.docs = support.site_complet(apercu=True)

    def test_title_du_billet_secret_professionnel(self):
        p = "ressources/blog/secret-professionnel-outils-traduction/"
        titre = self.registre[p]["title"]
        self.assertIn("traduction", titre)
        self.assertIn("Secret professionnel", titre)
        self.assertLessEqual(len(titre), 60)
        h = support.chemin(self.docs, p).read_text(encoding="utf-8")
        self.assertIn(f"<title>{titre}</title>", h)

    def test_a_lire_ensuite_porte_les_nouveaux_titres(self):
        import html as H
        cartes = 0
        for p in build.PAGES:
            h = support.chemin(self.docs, p).read_text(encoding="utf-8")
            for bloc in re.findall(r"À lire ensuite</h2>(.*?)</section>", h, re.S):
                for href, titre in re.findall(r'<a href="(?:\.\./)+fr/([^"]+)"[^>]*><b><b>(.*?)</b></b>', bloc):
                    if href in self.registre:
                        cartes += 1
                        self.assertEqual(H.unescape(titre), self.registre[href]["h1"], (p, href))
        self.assertGreaterEqual(cartes, 7)  # 7 cartes vers un billet ou un guide retitré sur 3 pages
        organiser = support.chemin(self.docs, "ressources/guides/organiser-traduction-cabinet/").read_text(encoding="utf-8")
        self.assertNotIn("<b><b>Préparer un rapport annuel multilingue</b></b>", organiser)


SUIVI = re.compile(r'<a\b[^>]*\sdata-suivi="([^"]*)"[^>]*>')
CONVENTION = re.compile(r"^cta-(?:entete(?:-mobile)?|[a-z0-9]+(?:-[a-z0-9]+)*-(?:hero|fin))$")


class TestSuiviDesAppels(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.docs = support.site_complet(apercu=True)
        cls.pages = {p: support.chemin(cls.docs, p).read_text(encoding="utf-8") for p in build.PAGES}
        cls.js = (ICI / "assets/global/suivi.js").read_text(encoding="utf-8")

    def test_une_seule_convention(self):
        """data-suivi = cta-<contexte>-<position> (hero ou fin) ; l'en-tête : cta-entete, et cta-entete-mobile dans le
        menu mobile."""
        valeurs = {v for h in self.pages.values() for v in SUIVI.findall(h)}
        self.assertTrue(valeurs)
        for v in valeurs:
            self.assertRegex(v, CONVENTION)

    def test_entete_suivi_sur_toutes_les_pages_a_en_tete_complet(self):
        for p, h in self.pages.items():
            if 'class="hd-nav"' not in h:  # en-tête minimal (contact, merci) : pas de bouton
                continue
            self.assertRegex(h, r'<a class="btn btn-s" href="[^"]+" data-suivi="cta-entete">Demander une démo</a>', p)
            self.assertRegex(h, r'<a class="btn mm-cta" href="[^"]+" data-suivi="cta-entete-mobile">Demander une démo</a>', p)

    def test_appels_principaux_de_l_accueil_et_du_plugin_word(self):
        accueil = self.pages[""]
        self.assertRegex(accueil, r'<div class="hero-act"><a class="btn"[^>]* data-suivi="cta-accueil-hero"[^>]*>Demander une démo')
        self.assertRegex(accueil, r'<section class="sec cta">.*?<a class="btn"[^>]* data-suivi="cta-accueil-fin"[^>]*>Demander une démo')
        self.assertEqual(SUIVI.findall(accueil).count("cta-accueil-hero"), 1)
        self.assertEqual(SUIVI.findall(accueil).count("cta-accueil-fin"), 1)
        word = self.pages["corrext/plugin-word/"]
        self.assertEqual(SUIVI.findall(word).count("cta-plugin-word-hero"), 1)
        self.assertEqual(SUIVI.findall(word).count("cta-plugin-word-fin"), 1)
        self.assertNotIn('data-suivi="cta-plugin-word"', word)

    def test_champs_caches_tronques_a_la_longueur_d_envoi_php(self):
        php = (ICI / "envoi.php").read_text(encoding="utf-8")
        champs = {n: int(m) for n, m in re.findall(r"'(\w+)' => \[(\d+), ", php)}
        longueurs = re.search(r"var LONGUEURS = \{([^}]*)\}", self.js).group(1)
        js = {n: int(m) for n, m in re.findall(r"(\w+): (\d+)", longueurs)}
        attendus = ("page_entree", "page_origine", "utm_source", "utm_medium", "utm_campaign", "utm_term", "utm_content")
        self.assertEqual(sorted(js), sorted(attendus))
        for n in attendus:
            self.assertEqual(js[n], champs[n], n)
        self.assertIn("valeur.slice(0, LONGUEURS[nom])", self.js)

    def test_pause_n_est_pas_une_interaction(self):
        geste = re.search(r"function geste\(e\) \{(.*?)\n    \}", self.js, re.S).group(1)
        self.assertIn('e.target.closest(".sim-pause")', geste)
        self.assertLess(geste.index(".sim-pause"), geste.index("removeEventListener"))


if __name__ == "__main__":
    unittest.main()
