"""Accessibilité et coût des animations (audit du 2026-10-23, docs/audits/2026-10-23-neuron-v2/annexe-perf.md) :
bouton pause (WCAG 2.2.2), pause hors écran, menu mobile modal, ordre du méga-menu, contraste du schéma, erreurs du
formulaire (WCAG 3.3.1), langues des passages étrangers, annonces des scènes, nom des listes d'onglets."""
import html as H
import re
import sys
import unittest
from pathlib import Path

ICI = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ICI))
import build  # noqa: E402
from outils import contenus  # noqa: E402
from tests import support  # noqa: E402

SCENE = re.compile(r'<div class="st" data-sim="[^"]*"[^>]*>')
BOUTON = re.compile(r'<button type="button" class="anim-pause (sim-pp|fx-pp)"[^>]*>.*?</button>', re.S)


def lum(hexa):
    """Luminance relative WCAG d'une couleur #rrggbb."""
    c = [int(hexa.lstrip("#")[i:i + 2], 16) / 255 for i in (0, 2, 4)]
    c = [v / 12.92 if v <= 0.03928 else ((v + 0.055) / 1.055) ** 2.4 for v in c]
    return 0.2126 * c[0] + 0.7152 * c[1] + 0.0722 * c[2]


def contraste(a, b):
    x, y = sorted((lum(a), lum(b)), reverse=True)
    return (x + 0.05) / (y + 0.05)


def jetons(css):
    """Jetons de couleur des deux thèmes, lus dans site.css (:root, puis le thème sombre)."""
    clair = dict(re.findall(r"--([a-z-]+):(#[0-9a-fA-F]{6})", re.search(r":root\{(.*?)\}", css, re.S).group(1)))
    sombre = dict(re.findall(r"--([a-z-]+):(#[0-9a-fA-F]{6})", re.search(r':root\[data-theme="sombre"\]\{(.*?)\}', css).group(1)))
    return {"clair": clair, "sombre": {**clair, **sombre}}


class Base(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.sortie = support.site_complet(apercu=True)
        cls.pages = {p: support.chemin(cls.sortie, p).read_text(encoding="utf-8") for p in build.PAGES}
        cls.css = (cls.sortie / "assets/site.css").read_text(encoding="utf-8")
        cls.sim = (ICI / "assets/sim.js").read_text(encoding="utf-8")
        cls.nav = (ICI / "assets/nav.js").read_text(encoding="utf-8")
        cls.global_js = (cls.sortie / "assets/global.js").read_text(encoding="utf-8")


class TestBoutonPause(Base):
    """Point 1 : un bouton pause accessible par scène animée et par grille de cartes animées."""

    def test_un_bouton_au_debut_de_chaque_scene_animee(self):
        total = 0
        for p, h in self.pages.items():
            for m in SCENE.finditer(h):
                total += 1
                self.assertTrue(h.startswith('<button type="button" class="anim-pause sim-pp"', m.end()), (p, m.group(0)[:80]))
        self.assertGreaterEqual(total, 20)

    def test_un_bouton_avant_chaque_grille_de_cartes(self):
        total = 0
        for p, h in self.pages.items():
            for m in re.finditer(r'<div class="fx-g[ "]', h):
                total += 1
                self.assertTrue(h[:m.start()].endswith("</button>"), p)
                self.assertIn('class="anim-pause fx-pp"', h[max(0, m.start() - 1200):m.start()], p)
        self.assertGreaterEqual(total, 10)

    def test_bouton_nomme_en_francais_et_masque_sans_script(self):
        pause, relancer = contenus.texte("a11y.animation.pause"), contenus.texte("a11y.animation.relancer")
        self.assertEqual((pause, relancer), ("Mettre l'animation en pause", "Relancer l'animation"))
        for p, h in self.pages.items():
            for b in BOUTON.finditer(h):
                o = H.unescape(re.match(r"<button[^>]*>", b.group(0)).group(0))
                self.assertIn(" hidden ", o, p)  # affiché par le script, jamais en mouvement réduit
                self.assertIn(f'aria-label="{pause}"', o, p)
                self.assertIn(f'data-pause="{pause}"', o, p)
                self.assertIn(f'data-relancer="{relancer}"', o, p)
                self.assertEqual(len(re.findall(r'<svg[^>]*aria-hidden="true"', b.group(0))), 2, p)

    def test_bouton_cable_par_les_scripts(self):
        self.assertIn('racine.querySelector(".anim-pause")', self.sim)
        self.assertIn("if (this.bouton && !reduit)", self.sim)
        self.assertIn('this.r.classList.toggle("en-pause", this.enPause)', self.sim)
        self.assertIn('b.getAttribute(this.enPause ? "data-relancer" : "data-pause")', self.sim)
        # le bouton d'une démo interactive n'interrompt pas la visite guidée comme un geste du visiteur
        self.assertIn("if (self.bouton && self.bouton.contains(e.target)) return;", self.sim)
        self.assertIn('g.classList.toggle("en-pause")', self.global_js)
        self.assertIn('b.getAttribute(pause ? "data-relancer" : "data-pause")', self.global_js)

    def test_css_suspend_les_animations_et_respecte_le_mouvement_reduit(self):
        self.assertRegex(self.css, r"\.en-pause \*,\.en-pause \*::before,\.en-pause \*::after[^{]*\{animation-play-state:paused!important\}")
        reduit = re.search(r"@media \(prefers-reduced-motion:reduce\)\{(.*?)\n\}", self.css, re.S).group(1)
        self.assertRegex(reduit, r"\.anim-pause[^{]*\{display:none\}")
        # cible tactile : 32 px à l'écran, quelle que soit la réduction de la scène
        self.assertIn("width:calc(32px / var(--k,1));height:calc(32px / var(--k,1))", self.css)


class TestPauseHorsEcran(Base):
    """Point 2 : hors écran, ni boucle requestAnimationFrame ni animation CSS."""

    def test_boucles_raf_sans_nouvelle_image_quand_la_scene_est_inactive(self):
        garde = "if (!self.actif()) { avant = null; self.suspendues.push(tic); return; }"
        self.assertEqual(self.sim.count(garde), 2)  # horloge (jauge) et attendre (déroulé de la scène)
        for nom in ("horloge", "attendre"):
            corps = re.search(r"Lecteur\.prototype\." + nom + r" = function.*?\n  \};", self.sim, re.S).group(0)
            self.assertLess(corps.index(garde), corps.rindex("requestAnimationFrame(tic)"), nom)
        self.assertNotIn("if (self.actif()) reste -=", self.sim)  # ancienne boucle qui tournait à vide hors écran
        self.assertIn("l.forEach(function (tic) { requestAnimationFrame(tic); });", self.sim)  # reprise

    def test_observateur_pose_hors_champ(self):
        self.assertIn("e.target.__lecteur.voir(e.isIntersecting && e.intersectionRatio >= 0.4, e.isIntersecting)", self.sim)
        self.assertIn('this.r.classList.toggle("hors-champ", !dansLaPage)', self.sim)
        self.assertIn('en.target.classList.toggle("hors-champ", !en.isIntersecting)', self.global_js)
        self.assertIn("io.observe(g)", self.global_js)
        self.assertRegex(self.css, r"\.hors-champ \*,\.hors-champ \*::before,\.hors-champ \*::after\{animation-play-state:paused!important\}")


class TestMenuMobile(Base):
    """Point 3 : menu mobile modal, Échap rend le focus au bouton, nom du bouton selon l'état."""

    def test_bouton_porte_le_nom_de_fermeture(self):
        fermer = contenus.texte("a11y.menu.fermer")
        self.assertEqual(fermer, "Fermer le menu")
        h = self.pages[""]
        self.assertIn(f'aria-label="Ouvrir le menu" data-fermer="{fermer}"', h)

    def test_piege_du_focus_et_page_inerte(self):
        self.assertIn("inertes().forEach(function (el) { el.inert = true; });", self.nav)
        self.assertIn("inertes().forEach(function (el) { el.inert = false; });", self.nav)
        tab = re.search(r'if \(e\.key === "Tab" && mm && !mm\.hidden\) \{(.*?)\n    \}', self.nav, re.S).group(1)
        self.assertIn("l[l.length - 1].focus()", tab)  # Maj+Tab sur le premier : retour au dernier
        self.assertIn("l[0].focus()", tab)               # Tab sur le dernier : retour au bouton
        self.assertIn("return [burger].concat(l);", self.nav)

    def test_echap_ferme_et_rend_le_focus(self):
        self.assertIn("if (mm && !mm.hidden) { fermerMobile(true); return; }", self.nav)
        self.assertIn("if (rendreFocus) burger.focus();", self.nav)
        self.assertIn('burger.setAttribute("aria-label", burger.getAttribute("data-fermer"))', self.nav)
        self.assertIn('burger.setAttribute("aria-label", ouvrirLibelle)', self.nav)


class TestMegaMenu(Base):
    """Point 4 : chaque panneau suit son bouton dans la navigation (une tabulation du bouton à la première entrée)."""

    def test_panneau_juste_apres_son_bouton(self):
        for p, h in self.pages.items():
            if 'class="hd-nav"' not in h:
                continue
            nav = re.search(r'<nav class="hd-nav".*?</nav>', h, re.S).group(0)
            boutons = re.findall(r'aria-controls="(mg-[^"]+)" data-mg>.*?</button>\n(<div class="mg" id="[^"]+")', nav, re.S)
            self.assertTrue(boutons, p)
            for cible, panneau in boutons:
                self.assertEqual(panneau, f'<div class="mg" id="{cible}"', p)
            self.assertEqual(h.count('<div class="mg" id='), len(boutons), p)


class TestContrasteSchema(Base):
    """Point 5 : étapes inactives du schéma « qui fait quoi » à 4,5:1 au moins, sans opacité."""

    def test_etapes_sans_opacite_et_en_couleur_attenuee(self):
        css = (ICI / "assets/composants/schema-produits.css").read_text(encoding="utf-8")
        regle = " ".join(re.findall(r"\n\.sp-pret \.sp-et li\{([^}]*)\}", css))
        self.assertNotIn("opacity", regle)
        self.assertIn("color:var(--muted)", regle)
        self.assertNotRegex(css, r"\.sp-et li[^{]*\{[^}]*opacity:\.\d")

    def test_contraste_des_etapes_inactives(self):
        for theme, t in jetons(self.css).items():
            for fond in ("page", "tile"):
                self.assertGreaterEqual(contraste(t["muted"], t[fond]), 4.5, (theme, fond))


class TestFormulaire(Base):
    """Point 6 : champs fautifs identifiés (aria-invalid, message lié, résumé annoncé), messages en français."""

    MESSAGES = ("resume", "requis", "choix", "email", "case")

    def test_region_des_erreurs_dans_chaque_formulaire(self):
        for config in ({"apercu": True}, {"apercu": False}):
            h = support.chemin(support.site_complet(**config), "contact/").read_text(encoding="utf-8")
            for f in re.findall(r"<form\b[^>]*>.*?</form>", h, re.S):
                r = re.search(r'<div class="f-err" role="alert"([^>]*)></div>', f)
                self.assertTrue(r, config)  # vide au chargement : rien à lire, rien d'affiché
                for n in self.MESSAGES:
                    self.assertIn(f'data-{n}="{H.escape(contenus.texte("a11y.formulaire." + n), quote=True)}"', r.group(1))

    def test_messages_en_francais_declares_a_relire(self):
        for n in self.MESSAGES:
            e = contenus.entree("a11y.formulaire." + n)
            self.assertEqual(e["statut"], "a_relire")
            self.assertRegex(e["texte"], r"[éèàç]|champ|case|option")

    def test_script_de_validation(self):
        js = self.global_js
        self.assertIn('c.setAttribute("aria-invalid", "true")', js)
        self.assertIn('c.setAttribute("aria-describedby", ids.join(" "))', js)
        self.assertIn("fautifs[0].focus()", js)
        self.assertIn('document.addEventListener("submit", function (e) {', js)
        self.assertRegex(js, r"\}, true\);\n\}\)\(\);")  # phase de capture : avant l'avis de démonstration de nav.js
        self.assertIn("e.stopPropagation()", js)
        self.assertIn("f.noValidate = true", js)

    def test_contraste_des_messages(self):
        css = (ICI / "assets/composants/formulaires.css").read_text(encoding="utf-8")
        clair = re.search(r"\nform\{--erreur:(#[0-9A-Fa-f]{6})\}", css).group(1)
        sombre = re.search(r':root\[data-theme="sombre"\] form\{--erreur:(#[0-9A-Fa-f]{6})\}', css).group(1)
        t = jetons(self.css)
        for fond in ("page", "tile"):
            self.assertGreaterEqual(contraste(clair, t["clair"][fond]), 4.5, fond)
            self.assertGreaterEqual(contraste(sombre, t["sombre"][fond]), 4.5, fond)


class TestLanguesAnnoncesOnglets(Base):
    """Points 7, 8 et 9 : langue des passages étrangers, annonces coupées pendant les visites, onglets nommés."""

    def test_terme_du_glossaire_et_lignes_chnell(self):
        h = self.pages["ressources/glossaire/aktiengesellschaft/"]
        self.assertIn('<span class="n" lang="de">Aktiengesellschaft', h)
        self.assertIn('<b lang="it">società anonima</b>', h)
        self.assertRegex(h, r'<p lang="de">Die <mark>Aktiengesellschaft</mark> ist eine Kapitalgesellschaft')
        contrats = self.pages["traduction/contrats/"]
        self.assertRegex(contrats, r'data-m="Allemand" lang="de"><b><a [^>]*>Gewährleistung wegen Mängel</a>')

    def test_annonces_muettes_pendant_la_visite(self):
        self.assertIn('el.setAttribute("aria-live", "off")', self.sim)
        self.assertIn("if (this.muet) couperAnnonces(this.scene, true);", self.sim)
        self.assertIn("couperAnnonces(self.scene, false);", self.sim)
        for p, h in self.pages.items():
            for balise in SCENE.findall(h):
                self.assertRegex(balise, r'role="group" aria-label="[^"]+"', p)

    def test_listes_d_onglets_nommees(self):
        for p, h in self.pages.items():
            for m in re.finditer(r'role="tablist"([^>]*)>', h):
                nom = re.search(r'aria-label="[^"]+"|aria-labelledby="([^"]+)"', m.group(1))
                self.assertTrue(nom, p)
                if nom.group(1):
                    self.assertIn(f'id="{nom.group(1)}"', h, p)


if __name__ == "__main__":
    unittest.main()
