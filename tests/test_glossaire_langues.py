"""Tableau des termes du glossaire (ressources/glossaire/) : chaque colonne de langue porte son lang (allemand, français,
italien, anglais), pour les lecteurs d'écran et pour la traduction : les équivalents ne se traduisent pas (le français
reste du français voulu, Ruling 14 ; les autres langues sont exclues), seule la colonne Domaine se traduit
(lot t06 de la traduction allemande du 2026-10-27)."""
import unittest

from outils.i18n import segments as S
from outils.post import y_accessibilite as Y

TABLE = ('<table><thead><tr><th>Allemand</th><th>Français</th><th>Italien</th><th>Anglais</th><th>Domaine</th></tr>'
         '</thead><tbody><tr><td><a href="x/">Abtretung</a></td><td>cession de créance</td><td>cessione del credito</td>'
         '<td>assignment of a claim</td><td>Droit des obligations</td></tr></tbody></table>')


class TestColonnesDeLangue(unittest.TestCase):
    def test_lang_pose_par_colonne(self):
        h = Y.langues_tableaux(TABLE)
        self.assertIn('<td lang="de"><a href="x/">Abtretung</a></td>', h)
        self.assertIn('<td lang="fr">cession de créance</td>', h)
        self.assertIn('<td lang="it">cessione del credito</td>', h)
        self.assertIn('<td lang="en">assignment of a claim</td>', h)
        self.assertIn("<td>Droit des obligations</td>", h)
        self.assertIn("<th>Allemand</th>", h)  # les en-têtes restent du texte de la page, à traduire

    def test_seule_la_colonne_domaine_se_traduit(self):
        page = f'<html lang="fr"><body><main>{Y.langues_tableaux(TABLE)}</main></body></html>'
        traduits = [u["texte"] for u in S.extraire_page(page) if not u["lang_fr"]]
        self.assertEqual(sorted(traduits), sorted(["Allemand", "Français", "Italien", "Anglais", "Domaine",
                                                   "Droit des obligations"]))

    def test_tableau_sans_colonne_de_langue_inchange(self):
        autre = "<table><thead><tr><th>Niveau</th><th>Usage</th></tr></thead><tbody><tr><td>1</td><td>x</td></tr></tbody></table>"
        self.assertEqual(Y.langues_tableaux(autre), autre)


if __name__ == "__main__":
    unittest.main()
