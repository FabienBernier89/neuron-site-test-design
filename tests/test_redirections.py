"""Redirections du site Neur.on actuel : lues dans la V1, écrites en pages d'aperçu et en 301 Apache (spec V2 § 3)."""
import posixpath
import re
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

ICI = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ICI))
import build  # noqa: E402
import redirections  # noqa: E402

# Redirections de la V1 dans le périmètre du français : 8 sous fr/ et 47 anciennes adresses WordPress à la racine.
# Le plan en annonçait 56 (8 + 48) : le 48e était la page d'aiguillage de la racine, qui change de langue par
# location.replace sans être une redirection. Les 8 redirections sous de/ relèvent de la version allemande (lot F).
ATTENDU, SOUS_FR, A_LA_RACINE = 55, 8, 47


def page(chemin, corps=""):
    f = Path(chemin)
    f.parent.mkdir(parents=True, exist_ok=True)
    f.write_text(f"<!DOCTYPE html><html><head><title>t</title></head><body>{corps}</body></html>", encoding="utf-8")


def redirection(chemin, url):
    f = Path(chemin)
    f.parent.mkdir(parents=True, exist_ok=True)
    f.write_text(f'<!DOCTYPE html><html><head><meta http-equiv="refresh" content="0; url={url}"></head><body></body></html>',
                 encoding="utf-8")


class TestRedirections(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        subprocess.run([sys.executable, str(ICI / "build.py")], check=True, cwd=ICI, stdout=subprocess.DEVNULL)
        cls.r = redirections.lire(build.NEURON)
        cls.htaccess = (build.DOCS / ".htaccess").read_text(encoding="utf-8")

    def test_redirections_du_perimetre_vers_des_pages_existantes(self):
        self.assertEqual(len(self.r), ATTENDU)
        self.assertEqual(sum(1 for a in self.r if a.startswith("fr/")), SOUS_FR)
        self.assertEqual(sum(1 for a in self.r if not a.startswith("fr/")), A_LA_RACINE)
        for ancien, cible in self.r.items():
            self.assertTrue(ancien.endswith("/") and not ancien.startswith("/"), ancien)
            self.assertRegex(cible, r"^/fr/[a-z0-9/-]*(#[A-Za-z0-9_-]+)?$", (ancien, cible))
            page_cible = cible.split("#")[0][len("/fr/"):]
            self.assertIn(page_cible, build.PAGES, (ancien, cible))  # la page existe dans le site construit
            self.assertTrue(build.chemin_page(page_cible).exists(), (ancien, cible))

    def test_ancre_et_barre_finale(self):
        self.assertEqual(self.r["fr/terms-of-use/"], "/fr/mentions-legales/#conditions-d-utilisation")
        self.assertIn("RewriteRule ^fr/terms-of-use/?$ /fr/mentions-legales/#conditions-d-utilisation [R=301,L,NE]",
                      self.htaccess)
        self.assertIn("ErrorDocument 404 /404.html", self.htaccess)

    def test_htaccess_regles(self):
        lignes = self.htaccess.splitlines()
        self.assertLess(lignes.index("RewriteEngine On"), min(i for i, l in enumerate(lignes) if l.startswith("RewriteRule")))
        self.assertIn("RewriteRule ^$ /fr/ [R=302,L]", lignes)  # la racine part vers le français, provisoirement
        regles = [l.split() for l in lignes if l.startswith("RewriteRule ^") and "[R=301" in l]
        self.assertEqual(len(regles), ATTENDU)
        modeles = set()
        for _, modele, cible, options in regles:
            self.assertEqual(options, "[R=301,L,NE]")  # NE : l'ancre # n'est pas échappée
            self.assertTrue(cible.startswith("/fr/"), cible)
            sans_barre = modele[1:-len("/?$")]
            for url in (sans_barre, sans_barre + "/"):  # avec ou sans barre finale
                self.assertTrue(re.search(modele, url), (modele, url))
            self.assertFalse(re.search(modele, sans_barre + "/suite"), modele)
            modeles.add(modele)
        self.assertEqual(len(modeles), ATTENDU)  # aucune adresse en double
        self.assertEqual({"^" + a.rstrip("/") + "/?$" for a in self.r}, modeles)

    def test_pages_d_apercu(self):
        for ancien, cible in self.r.items():
            h = (build.DOCS / ancien / "index.html").read_text(encoding="utf-8")
            self.assertIn('<meta name="robots" content="noindex">', h, ancien)
            self.assertIn(f'<link rel="canonical" href="https://neur-on.ai{cible}">', h, ancien)
            url = re.search(r'<meta http-equiv="refresh" content="0; url=([^"]+)"', h).group(1)
            self.assertNotIn("../" * (ancien.count("/") + 1), url, ancien)
            chemin, _, ancre = url.partition("#")
            resolu = posixpath.normpath(posixpath.join("/" + ancien, chemin)) + "/"
            self.assertEqual(resolu + ("#" + ancre if ancre else ""), cible, ancien)
            self.assertIn(f'location.replace("{url}")', h, ancien)

    def test_chaines_hreflang_et_exclusions(self):
        """Une chaîne de redirections est suivie jusqu'à la page réelle ; une cible dans une autre langue passe par
        son équivalent français ; de/, it/, en/ et maquettes/ sont hors périmètre."""
        with tempfile.TemporaryDirectory() as tmp:
            d = Path(tmp) / "docs"
            page(d / "fr/c/index.html", '<h2 id="x">x</h2>')
            page(d / "en/page/index.html", '<link rel="alternate" hreflang="fr-CH" href="https://neur-on.ai/fr/c/">')
            redirection(d / "a/index.html", "../b/")                      # chaîne : a -> b -> fr/c
            redirection(d / "b/index.html", "../fr/c/")
            redirection(d / "vieux/index.html", "../en/page/#x")          # autre langue : équivalent français et ancre
            redirection(d / "fr/ancien/index.html", "../../fr/c/#x")
            redirection(d / "de/ancien/index.html", "../../fr/c/")        # hors périmètre
            redirection(d / "maquettes/m/index.html", "../fr/c/")         # hors périmètre
            self.assertEqual(redirections.lire(Path(tmp)), {
                "a/": "/fr/c/", "b/": "/fr/c/", "vieux/": "/fr/c/#x", "fr/ancien/": "/fr/c/#x"})

    def test_erreurs_explicites(self):
        """Cible absente, boucle, ancre introuvable, page sans équivalent français : le build s'arrête."""
        cas = {
            "cible absente": lambda d: redirection(d / "a/index.html", "../fr/absente/"),
            "boucle": lambda d: (redirection(d / "a/index.html", "../b/"), redirection(d / "b/index.html", "../a/")),
            "ancre introuvable": lambda d: redirection(d / "a/index.html", "../fr/c/#autre"),
            "sans équivalent français": lambda d: (page(d / "en/p/index.html"), redirection(d / "a/index.html", "../en/p/")),
        }
        for nom, preparer in cas.items():
            with self.subTest(nom), tempfile.TemporaryDirectory() as tmp:
                d = Path(tmp) / "docs"
                page(d / "fr/c/index.html", '<h2 id="x">x</h2>')
                preparer(d)
                with self.assertRaises(ValueError):
                    redirections.lire(Path(tmp))


if __name__ == "__main__":
    unittest.main()
