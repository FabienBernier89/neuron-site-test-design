"""Audit d'homogénéité du design du 2026-10-23 : les composants validés propagés aux anciennes pages.

Situations en rangées, glossaire en fiche avec une démo CHnell à deux langues, cartes de liens et titres au standard,
Tarifs sur mobile, lien de commande des extraits, marque dans le blog. Le bento et les tuiles chiffrées, validés à
d'autres dates, restent en place en attendant l'arbitrage du propriétaire."""
import re
import sys
import unittest
from pathlib import Path

ICI = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ICI))
from tests import support  # noqa: E402

def sans_balises(t):
    return re.sub(r"\s+", " ", re.sub(r"<[^>]+>", "", t)).strip()


class TestAuditDesign(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.sortie = support.site_complet(apercu=True)
        cls.css = (cls.sortie / "assets/site.css").read_text(encoding="utf-8")
        cls.pages = {}
        for f in (cls.sortie / "fr").rglob("index.html"):
            rel = f.parent.relative_to(cls.sortie / "fr").as_posix()
            cls.pages["" if rel == "." else rel + "/"] = f.read_text(encoding="utf-8")

    def regles(self, selecteur):
        """Toutes les déclarations d'un sélecteur exact dans la feuille construite, dans l'ordre."""
        return re.findall(r"(?:^|[}\s])" + re.escape(selecteur) + r"\{([^}]*)\}", self.css, re.M)

    def page(self, chemin):
        return self.pages[chemin]

    # Blocs validés à des dates différentes : NON remplacés, listés pour arbitrage (consigne du propriétaire, 2026-10-23),
    # y compris les situations en cartes des domaines et paires, les cartes de liens en 14 px et les textes des pages
    # domaines, paires, métiers, niveaux, langues, comparatifs et LexMachina
    def test_blocs_valides_conserves(self):
        self.assertEqual(len([p for p, h in self.pages.items() if 'class="bt-p' in h]), 8)  # accueil, Corrext, six métiers
        self.assertIn('class="bt-v"', self.page("corrext/"))  # écran animé validé de la grande tuile
        self.assertIn('<div class="tl t4">', self.page(""))  # chiffres et niveaux de l'accueil
        for p, h in self.pages.items():
            if re.fullmatch(r"solutions/[a-z-]+/", p):
                self.assertIn('<div class="tl">', h, p)  # gains chiffrés des métiers (Fabien, 2026-10-19)
            if re.fullmatch(r"traduction/[a-z-]+/", p) and 'class="h2">Trois situations' in h:
                self.assertIn('<div class="sr">', h, p)  # rangées, comme les pages outils (arbitrage du 2026-10-23, B)
                self.assertNotIn('class="pa-sg"', h, p)

    # Item 5 : glossaire
    def test_glossaire_en_fiche_de_langues(self):
        pages = [p for p in self.pages if re.fullmatch(r"ressources/glossaire/[a-z0-9-]+/", p)]
        self.assertGreaterEqual(len(pages), 52)
        for p in pages:
            h = self.pages[p]
            self.assertNotIn("tl-lang", h, p)
            fiche = re.search(r'<dl class="fs fs-lang">(.*?)</dl>', h, re.S)
            self.assertIsNotNone(fiche, p)
            langues = re.findall(r"<dt>([^<]+)</dt>", fiche.group(1))
            self.assertEqual(len(langues), 4, p)
            self.assertEqual(len(set(langues)), 4, p)

    def test_demo_chnell_du_glossaire_a_deux_langues(self):
        """Aucune page du glossaire n'affiche la même langue des deux côtés de la démo, ni la même phrase."""
        n = 0
        for p, h in self.pages.items():
            if not p.startswith("ressources/glossaire/") or "cr-chst" not in h:
                continue
            n += 1
            l1 = re.search(r'class="cr-lang lk-l1">([^<]*)<', h).group(1)
            l2 = re.search(r'class="cr-lang lk-l2">([^<]*)<', h).group(1)
            self.assertNotEqual(l1, l2, p)
            a, b = re.search(r'<div style="--i:0"><p[^>]*>(.*?)</p><p[^>]*>(.*?)</p>', h, re.S).groups()  # lang posé par l'accessibilité
            self.assertTrue(a and b, p)
            self.assertNotEqual(sans_balises(a), sans_balises(b), p)
        self.assertGreaterEqual(n, 52)

    # Item 7 : accent italique des titres
    def test_titres_longs_avec_accent(self):
        for p, h in self.pages.items():
            for t in re.findall(r'<h2 class="h2[^"]*"[^>]*>(.*?)</h2>', h, re.S):
                mots = sans_balises(t).rstrip(" .?!: ").split(" ")
                if len(mots) > 4:
                    self.assertIn("<em>", t, (p, sans_balises(t)))
        for p in ("", "tarifs/", "traduction/contrats/"):
            fq = re.search(r'<div class="wrap fq"><h2 class="h2">(.*?)</h2>', self.page(p), re.S)
            self.assertIsNotNone(fq, p)
            self.assertIn("<em>", fq.group(1), p)

    # Item 1 : Tarifs sur mobile, une colonne sous 640 px après le bloc 1023 px
    def test_tarifs_une_colonne_sous_640(self):
        i1023 = self.css.index("@media (max-width:1023px){\n  .tf-pg{grid-template-columns:repeat(2")
        i640 = self.css.index("@media (max-width:640px){.tf-pg{grid-template-columns:minmax(0,1fr)}}")
        self.assertLess(i1023, i640)

    # Item 8 : URL longue des pages légales
    def test_liens_legaux_coupables(self):
        self.assertIn("overflow-wrap:anywhere", self.regles(".lg-c a")[0])

    # Item 10 : commander un extrait depuis la page Fiduciaires
    def test_fiduciaires_commander_un_extrait(self):
        h = self.page("solutions/fiduciaires-conseil/")
        self.assertRegex(h, r'<a class="lien" href="https://auszug-hr\.ch" rel="noopener">Commander un extrait</a>')

    # Item 11 : la marque dans les articles du blog
    def test_marque_sans_capitales_dans_le_blog(self):
        for p, h in self.pages.items():
            if p.startswith("ressources/blog/"):
                self.assertNotIn("NEUR.ON", h, p)


if __name__ == "__main__":
    unittest.main()
