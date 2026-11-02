"""Invariants du site multilingue : non-régression octet par octet de la sortie française (empreintes de référence
prises au commit de départ du lot de traduction) et contrôles des pages construites dans les autres langues.

Toute régénération des références se fait par `python3 -m outils.i18n.empreintes <sortie> --ecrire <fichier>`, dans un
commit qui dit quel changement français est voulu."""
import json
import unittest
from pathlib import Path

import build
from tests import support
from outils.i18n import controles, empreintes

FIXTURES = Path(__file__).resolve().parent / "fixtures" / "i18n"
REF_APERCU = FIXTURES / "empreintes-fr-apercu.json"
REF_PRODUCTION = FIXTURES / "empreintes-fr-production.json"
# langues construites hors français ; build.CONFIG["langues"] n'existe qu'à partir de la tâche 1.2
LANGUES = [l for l in build.CONFIG.get("langues", ["fr"]) if l != "fr"]


def lire(fichier):
    return json.loads(fichier.read_text(encoding="utf-8"))


def ecarts(obtenu, attendu):
    """Résumé lisible de la différence entre deux jeux d'empreintes."""
    ajoutes = sorted(set(obtenu) - set(attendu))
    perdus = sorted(set(attendu) - set(obtenu))
    changes = sorted(k for k in set(obtenu) & set(attendu) if obtenu[k] != attendu[k])
    return f"ajoutés : {ajoutes[:10]} ; perdus : {perdus[:10]} ; modifiés ({len(changes)}) : {changes[:10]}"


class TestNonRegressionFR(unittest.TestCase):
    def verifier(self, sortie, reference):
        obtenu, attendu = empreintes.empreintes(sortie), lire(reference)
        self.assertEqual(obtenu, attendu, ecarts(obtenu, attendu))

    def test_apercu_identique(self):
        self.verifier(support.site_complet(langues=("fr",)), REF_APERCU)

    def test_production_identique(self):
        self.verifier(support.site_complet(langues=("fr",), apercu=False), REF_PRODUCTION)


class TestEmpreintes(unittest.TestCase):
    def test_ignore_assets_et_autres_extensions_et_version(self):
        import tempfile
        with tempfile.TemporaryDirectory() as tmp:
            racine = Path(tmp)
            (racine / "assets").mkdir()
            (racine / "assets/x.txt").write_text("a", encoding="utf-8")
            (racine / "a.png").write_bytes(b"png")
            (racine / ".htaccess").write_text("x", encoding="utf-8")
            (racine / "p").mkdir()
            (racine / "p/index.html").write_text('<link href="s.css?v=0123abcd">', encoding="utf-8")
            avant = empreintes.empreintes(racine)
            self.assertEqual(sorted(avant), [".htaccess", "p/index.html"])
            (racine / "p/index.html").write_text('<link href="s.css?v=ffffffff">', encoding="utf-8")
            self.assertEqual(empreintes.empreintes(racine), avant)
            (racine / "p/index.html").write_text('<link href="s.css">', encoding="utf-8")
            self.assertNotEqual(empreintes.empreintes(racine), avant)


@unittest.skipUnless(LANGUES, "aucune langue hors fr configurée")
class TestInvariantsLangues(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.sortie = support.site_complet()
        # pages de redirection des anciennes adresses (meta refresh) exclues : ce ne sont pas des pages du site
        cls.pages = {l: sorted(f for f in (cls.sortie / l).rglob("index.html")
                               if not controles._REDIRECTION.search(f.read_text(encoding="utf-8"))) for l in LANGUES}

    def test_nombre_de_pages_controlees(self):
        for l in LANGUES:
            self.assertGreaterEqual(len(self.pages[l]), 1, f"aucune page construite en « {l} »")

    def test_chaque_page_traduite_conforme(self):
        problemes = []
        for l in LANGUES:
            for f in self.pages[l]:
                for p in controles.controler_page(f.read_text(encoding="utf-8"), l):
                    problemes.append((f.relative_to(self.sortie).as_posix(), p["regle"], p["detail"]))
        self.assertEqual(problemes, [])

    def test_hreflang_reciproques(self):
        self.assertEqual(controles.hreflang(self.sortie), [])

    def test_liens_restent_dans_la_langue(self):
        problemes = []
        for l in LANGUES:
            for f in self.pages[l]:
                chemin = f.parent.relative_to(self.sortie).as_posix() + "/"
                problemes += controles.liens_langue(f.read_text(encoding="utf-8"), chemin, l, self.sortie,
                                                    tolere_fr=build.CONFIG["apercu"])
        self.assertEqual(problemes, [])


if __name__ == "__main__":
    unittest.main()
