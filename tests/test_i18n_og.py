"""Image de partage par langue (outils/i18n/og_image.py, gabarit src/data/og/og.html, tâche 6.3 de la traduction)."""
import json
import tempfile
import unittest
from pathlib import Path

import build
from outils.i18n import og_image
from outils.i18n.table import Table

ICI = Path(__file__).resolve().parent.parent
TEXTES = ICI / "src/data/og/textes.json"
TIRET_CADRATIN, DEMI_CADRATIN = chr(0x2014), chr(0x2013)
# textes de test synthétiques : ni vraie traduction ni texte du site
TITRE, ACCENT, SIGNATURE = "Titre de test pour une langue", "pour une langue", "Ligne de signature de test"


class TestGabarit(unittest.TestCase):
    def test_gabarit_rempli(self):
        """Titre dans le h1, accent dans un span à la fin, signature, langue ; plus aucun marqueur."""
        html = og_image.remplir("de", TITRE, ACCENT, SIGNATURE)
        self.assertIn('<html lang="de">', html)
        self.assertIn("<h1>Titre de test <span>pour une langue</span></h1>", html)
        self.assertIn(f'<p class="signature">{SIGNATURE}</p>', html)
        self.assertNotIn("{{", html)
        self.assertIn("data:font/woff2;base64,", html)
        self.assertIn("data:image/png;base64,", html)
        self.assertEqual(html.count("base64"), 2)  # la police et le logo, une fois chacun (pas dans un commentaire)

    def test_texte_echappe(self):
        html = og_image.remplir("en", "Tax & <b>Finance</b>", "<b>Finance</b>", "A & B", ressources=False)
        self.assertIn("<h1>Tax &amp; <span>&lt;b&gt;Finance&lt;/b&gt;</span></h1>", html)
        self.assertIn("A &amp; B", html)

    def test_accent_en_fin_de_titre(self):
        for accent in ("", "inconnu", "Titre"):
            with self.subTest(accent=accent), self.assertRaises(ValueError):
                og_image.remplir("de", TITRE, accent, SIGNATURE, ressources=False)

    def test_textes_fr_de_la_v1(self):
        """Les deux textes FR de l'image actuelle, avec leur source, et un accent qui termine le titre."""
        textes = {e["id"]: e for e in json.loads(TEXTES.read_text(encoding="utf-8"))["entrees"]}
        self.assertEqual(textes["titre"]["texte"], "Traduction par IA pour le droit, la fiscalité et la finance")
        self.assertEqual(textes["titre"]["accent"], "et la finance")
        self.assertTrue(textes["titre"]["texte"].endswith(textes["titre"]["accent"]))
        self.assertEqual(textes["signature"]["texte"], "Corrext et LexMachina · données stockées en Suisse · ISO 27001")
        for e in textes.values():
            self.assertEqual(e["source"], "og-neuron.jpg (V1)")

    def test_fr_garde_son_image(self):
        """Le FR ne passe pas par le gabarit : og:image du site reste og-neuron.jpg."""
        self.assertIn("og-neuron.jpg", (ICI / "build.py").read_text(encoding="utf-8"))
        self.assertFalse((ICI / "assets/img/og-neuron-fr.png").exists())

    def test_textes_non_relus_refuses(self):
        """Vague finale, point 9 : titre et signature doivent être des traductions relues, v1 ou invariantes de la table."""
        with tempfile.TemporaryDirectory() as tmp:
            t = Table("de", Path(tmp))
            t.poser("Titre FR", TITRE, "relu", "test")
            t.poser("Signature FR", SIGNATURE, "adapte", "test")
            with self.assertRaises(ValueError) as e:
                og_image.generer("de", TITRE, ACCENT, SIGNATURE, Path(tmp) / "x.png", t)
            self.assertIn("relue", str(e.exception))
            with self.assertRaises(ValueError):
                og_image.verifier_textes(t, "Texte absent de la table")
            t.poser("Signature FR", SIGNATURE, "v1", "V1 de/")
            og_image.verifier_textes(t, TITRE, SIGNATURE)  # aucune exception
            with self.assertRaises(ValueError):
                og_image.generer("it", TITRE, ACCENT, SIGNATURE, Path(tmp) / "x.png", t)
            self.assertFalse((Path(tmp) / "x.png").exists())

    def test_ligne_de_commande_francais_seulement(self):
        import contextlib
        import io
        erreur = io.StringIO()
        with contextlib.redirect_stderr(erreur):
            self.assertEqual(og_image._principal(["de", "x.png"]), 2)
        self.assertIn("image française de contrôle", erreur.getvalue())

    def test_aucun_tiret_long(self):
        for f in (og_image.GABARIT, TEXTES, ICI / "outils/i18n/og_image.py"):
            texte = f.read_text(encoding="utf-8")
            self.assertNotIn(TIRET_CADRATIN, texte, f.name)
            self.assertNotIn(DEMI_CADRATIN, texte, f.name)


@unittest.skipUnless(og_image.chrome() and og_image.LOGO.is_file(), "Chrome ou logo du site Neur.on absent")
class TestImage(unittest.TestCase):
    def test_image_dimensions(self):
        with tempfile.TemporaryDirectory() as tmp:
            sortie = Path(tmp) / "sous-dossier" / "og-test.png"
            t = Table("de", Path(tmp))
            t.poser("Titre FR", TITRE, "relu", "test")
            t.poser("Signature FR", SIGNATURE, "invariant", "test")
            og_image.generer("de", TITRE, ACCENT, SIGNATURE, sortie, t)
            self.assertEqual(build.taille_image(sortie), (1200, 630))
            self.assertGreater(sortie.stat().st_size, 10000)  # une image rendue, pas une page blanche


if __name__ == "__main__":
    unittest.main()
