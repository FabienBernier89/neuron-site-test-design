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

    def test_cartes_texte_seul_aerees(self):
        """Option A : marge 28 px, écart 16 px, texte 15/25 adouci, réservé aux cartes sans visuel ni lien."""
        sel = ".cd:not(:has(.v,.kv,a,.cd-meta))"
        # sélecteur avec virgules internes (:has) : lu tel quel, regles() découperait la liste
        self.assertIn(sel + "{gap:16px}", self.css)
        self.assertIn(sel + " > *{padding:28px}", self.css)
        self.assertIn(sel + " p{margin-top:12px;font-size:15px;line-height:25px;color:var(--muted)}", self.css)

    def test_jauge_de_deroule_fine_et_constante(self):
        """Jauge de déroulé : ligne fine au bas de la scène, épaisseur constante à l'écran. Le bouton pause revenu avec
        l'audit du 2026-10-23 (WCAG 2.2.2) porte la classe anim-pause, testée dans test_accessibilite."""
        d = " ".join(regles(self.css, ".sim-jauge"))
        self.assertIn("height:calc(3px / var(--k,1))", d)
        self.assertIn("pointer-events:none", d)
        self.assertEqual(regles(self.css, ".sim-pause"), [])

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
        self.assertGreater(vus, 80)  # pages de lecture seulement depuis le 2026-10-16 (95 pages)


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
CONVENTION = re.compile(r"^cta-(?:entete(?:-mobile)?|[a-z0-9]+(?:-[a-z0-9]+)*-(?:hero|milieu|fin))$")


class TestSuiviDesAppels(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.docs = support.site_complet(apercu=True)
        cls.pages = {p: support.chemin(cls.docs, p).read_text(encoding="utf-8") for p in build.PAGES}
        cls.js = (ICI / "assets/global/suivi.js").read_text(encoding="utf-8")

    def test_documentation_api(self):
        """Le bouton de la page API mène au formulaire avec ?demande=documentation-api ; suivi.js passe alors le type
        du formulaire de démo à « documentation » (objet d'e-mail distinct dans envoi.php)."""
        h = self.pages["corrext/api-on-premises/"]
        self.assertRegex(h, r'<a class="btn" href="[^"]*contact/\?demande=documentation-api" data-suivi="cta-api-documentation-milieu">')
        self.assertIn('parametre("demande") === "documentation-api"', self.js)
        self.assertIn('type.value = "documentation"', self.js)

    def test_une_seule_convention(self):
        """data-suivi = cta-<contexte>-<position> (hero, milieu ou fin ; milieu : bouton d'une bande en cours de page,
        décision du 2026-10-15) ; l'en-tête : cta-entete, et cta-entete-mobile dans le menu mobile."""
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

    def test_geste_sans_exception_pour_un_bouton_pause(self):
        geste = re.search(r"function geste\(e\) \{(.*?)\n    \}", self.js, re.S).group(1)
        self.assertNotIn("sim-pause", geste)
        self.assertLess(geste.index("isTrusted"), geste.index("removeEventListener"))


class TestAnimationsSansPause(unittest.TestCase):
    """Les animations continuent au survol ; chaque scène animée porte une jauge de déroulé. Depuis l'audit du
    2026-10-23 (WCAG 2.2.2), chacune porte aussi un bouton pause (anim-pause) : seuls ce bouton et la sortie de l'écran
    suspendent la scène, jamais le survol."""

    @classmethod
    def setUpClass(cls):
        cls.sortie = support.site_complet(apercu=True)
        cls.sim = (cls.sortie / "assets/sim.js").read_text(encoding="utf-8")

    def test_le_survol_ne_met_pas_en_pause(self):
        self.assertNotIn("mouseenter", self.sim)
        self.assertIn("return this.visible && !this.arret && !this.enPause;", self.sim)

    def test_une_jauge_par_scene_animee(self):
        for f in self.sortie.rglob("index.html"):
            h = f.read_text(encoding="utf-8")
            self.assertNotIn("sim-pause", h, f)  # ancien bouton retiré le 2026-10-15 ; le nouveau est anim-pause
            self.assertEqual(len(re.findall(r'<div class="st" data-sim=', h)), h.count('class="anim-pause sim-pp"'), f)
            self.assertEqual(len(re.findall(r'<div class="st" data-sim=', h)), h.count('class="sim-jauge"'), f)

    def test_hero_joue_une_fois_puis_libre(self):
        """Accueil : la visite du hero se joue une fois, puis la démo devient cliquable (retour de Fabien du 2026-10-15)."""
        h = (self.sortie / "fr/index.html").read_text(encoding="utf-8")
        self.assertRegex(h, r'data-sim="app" data-tenue="0" data-interactif data-une-fois')
        self.assertRegex(h, r'<p class="sim-main" hidden>[^<]+</p><span class="sim-jauge"')
        self.assertIn("LIBRE.app = function", self.sim)
        self.assertIn('if (self.r.hasAttribute("data-une-fois")) { if (!self.arret) self.passerLibre(); return; }', self.sim)
        # en mode libre, un geste du visiteur ne coupe plus les animations de la démo
        self.assertIn("if (!e.isTrusted || self.libre) return;", self.sim)
        # les commandes du mode libre se pilotent aussi au clavier
        self.assertIn('el.setAttribute("tabindex", "0")', self.sim)

    def test_calques_masques_traversables(self):
        """Un calque masqué (opacité nulle) ne doit pas capter les clics de la démo libre : fenêtre CHnell,
        avertissement, alternatives, bouton Fast Lookup. Défaut trouvé le 2026-10-15 avec de vrais clics de souris."""
        css = (self.sortie / "assets/site.css").read_text(encoding="utf-8")
        self.assertIn(".cr-modal,.cr-notice,.cr-alts,.cr-lkb{pointer-events:none}", css)
        self.assertIn(".cr.modal .cr-modal{opacity:1;pointer-events:auto}", css)
        self.assertIn(".cr.avis .cr-notice,.cr.alts .cr-alts,.cr.lkb .cr-lkb{pointer-events:auto}", css)

    def test_surlignage_bleu(self):
        for f in self.sortie.glob("assets/*.css"):
            self.assertNotIn("#fff2a8", f.read_text(encoding="utf-8").lower(), f)


if __name__ == "__main__":
    unittest.main()
