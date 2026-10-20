"""Modèle des pages métier (outils/composer/metier_modele.py), choisi par Fabien le 2026-10-19 sur Cabinets d'avocats :
ordre des blocs, gains présentés comme des maxima, avis fictif toujours signalé, onglets des outils accessibles."""
import re
import subprocess
import sys
import unittest
from pathlib import Path

ICI = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ICI))
import build  # noqa: E402
from outils import contenus  # noqa: E402

PAGES = [f"solutions/{s}/" for s in ("cabinets-avocats", "banques-finance", "directions-juridiques", "fiduciaires-conseil",
                                      "autorites-administration", "editeurs-legaltech")]
# Pages dont la V1 n'a pas de bloc sécurité : bloc construit, et pas de niveaux de relecture (Fabien, 2026-10-20)
SECURITE_CONSTRUITE = ("solutions/fiduciaires-conseil/", "solutions/editeurs-legaltech/")


def texte_brut(h):
    return re.sub(r"\s+", " ", re.sub(r"<[^>]+>", " ", h)).replace("&#x27;", "'").replace("&amp;", "&").strip()


class TestMetier(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        subprocess.run([sys.executable, str(ICI / "build.py")], check=True, cwd=ICI, stdout=subprocess.DEVNULL)
        cls.h = {p: build.chemin_page(p).read_text(encoding="utf-8") for p in PAGES}

    def main(self, p):
        h = self.h[p]
        return h[h.index('<main id="main">'):h.index("</main>")]

    def test_ordre_des_blocs(self):
        reperes = ["Demander une démo", "Adopté par les professionnels", 'class="tl"', contenus.texte("metier.avis.fictif"),
                   contenus.texte("metier.sa.titre"), 'role="tablist"', "Du document qu'on lit", "Sécurité et souveraineté des données",
                   contenus.texte("metier.deploiement.titre"), "Questions fréquentes", 'class="sec cta"']
        for p in PAGES:
            m = self.main(p).replace("&#x27;", "'").replace("<em>", "").replace("</em>", "")
            r_ = [r for r in reperes if not (p in SECURITE_CONSTRUITE and r == "Du document qu'on lit")]
            pos = [m.find(r) for r in r_]
            self.assertNotIn(-1, pos, (p, [r for r, x in zip(r_, pos) if x < 0]))
            self.assertEqual(pos, sorted(pos), p)
            # l'ancienne trame (problème, preuves, exemple de cas d'usage) a disparu
            for ancien in ('class="sec tr-pb"', 'class="sec tr-pv"', "temo-ex", "Exemple de cas d'usage"):
                self.assertNotIn(ancien, m, (p, ancien))

    def test_gains_en_maxima(self):
        for p in PAGES:
            slug = p.split("/")[1]
            m = texte_brut(self.main(p))
            # la note des maxima accompagne un pourcentage d'économies, jamais des chiffres de description
            pourcent = any(contenus.texte(f"{slug}.gains.{i}.n") not in ("100 %",) and contenus.texte(f"{slug}.gains.{i}.n").endswith("%") for i in (1, 2, 3))
            (self.assertIn if pourcent else self.assertNotIn)(contenus.texte("metier.gains.note"), m)
            for i in (1, 2, 3):
                n, t = contenus.texte(f"{slug}.gains.{i}.n"), contenus.texte(f"{slug}.gains.{i}.t")
                # chiffre seul dans la tuile (Fabien, 2026-10-19) ; un pourcentage d'économies n'est jamais une moyenne :
                # le texte dit « au maximum », sauf pour le 100 % du traitement en Suisse
                self.assertRegex(n, r"^(\d+ %|\d+ [A-ZÉ][a-zé]+|\d+ M\+)$")
                self.assertTrue(not n.endswith("%") or n == "100 %" or "au maximum" in t, (n, t))
            self.assertIn('<div class="tl">', self.main(p))

    def test_avis_fictif_toujours_signale(self):
        """Tant qu'un avis est fictif (statut a_remplacer), il porte la mention et l'attribut data-avis-fictif."""
        for p in PAGES:
            slug = p.split("/")[1]
            m = self.main(p)
            fictif = [contenus.entree(f"{slug}.avis.{c}")["statut"] == "a_remplacer" for c in ("texte", "nom", "fonction")]
            if any(fictif):
                self.assertIn("data-avis-fictif", m, p)
                self.assertIn(contenus.texte("metier.avis.fictif"), texte_brut(m), p)

    def test_onglets_accessibles(self):
        for p in PAGES:
            m = self.main(p)
            tabs = re.findall(r'<button type="button" role="tab" id="([^"]+)" aria-controls="([^"]+)" aria-selected="(true|false)"', m)
            self.assertEqual(len(tabs), 3, p)
            self.assertEqual([s for _, _, s in tabs].count("true"), 1, p)
            for t, c, s in tabs:
                self.assertRegex(m, rf'role="tabpanel" id="{c}" aria-labelledby="{t}"' + ("" if s == "true" else " hidden"), (p, c))
        js = (ICI / "assets/global/metier.js").read_text(encoding="utf-8")
        for x in ("aria-selected", "ArrowDown", "hidden"):
            self.assertIn(x, js)


if __name__ == "__main__":
    unittest.main()
