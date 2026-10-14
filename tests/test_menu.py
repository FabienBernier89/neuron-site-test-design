"""Le méga-menu reprend une à une les entrées du site actuel (spec § 6, test 3), plus les ajouts de menu-ajouts.json."""
import copy
import json
import re
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path
from unittest import mock

ICI = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ICI))
import build  # noqa: E402
import menu  # noqa: E402
from tests import support  # noqa: E402


class TestMenu(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        subprocess.run([sys.executable, str(ICI / "build.py")], check=True, cwd=ICI, stdout=subprocess.DEVNULL)
        cls.nav = (build.NEURON / "src/partials/nav.html").read_text(encoding="utf-8")
        cls.m = menu.lire_menu(cls.nav)
        cls.ajouts = json.loads((ICI / "src/data/menu-ajouts.json").read_text(encoding="utf-8"))

    def test_meme_nombre_de_liens(self):
        bureau = self.nav.split("<!-- MENU MOBILE -->")[0]
        attendu = len(re.findall(r"<a ", bureau[bureau.index('<div class="mega"'):]))
        lu = sum(len(c["liens"]) for p in self.m["panneaux"].values() for c in p["colonnes"])
        lu += sum(1 for p in self.m["panneaux"].values() if p["promo"])
        self.assertEqual(lu, attendu)
        html = build.chemin_page("").read_text(encoding="utf-8")
        ajoutes = sum(len(v) for v in self.ajouts["panneaux"].values())  # entrées ajoutées par les lots de la V2
        self.assertEqual(html.count('class="mg-a"') + html.count('class="mg-card"'), attendu + ajoutes)

    def test_memes_libelles_dans_le_meme_ordre(self):
        titres = [l["titre"] for p in self.m["panneaux"].values() for c in p["colonnes"] for l in c["liens"]]
        self.assertEqual(titres[0], "Corrext, le poste de commande")
        self.assertEqual(titres[-1], "Agence de traduction ou plateforme")
        self.assertEqual([e["libelle"] for e in self.m["entrees"]], ["Corrext", "Solutions", "LexMachina", "Ressources"])

    def test_pied_six_colonnes(self):
        html = build.chemin_page("").read_text(encoding="utf-8")
        pied = html[html.index('<footer class="pied">'):]
        self.assertEqual(pied.count("<div><p>"), 6)


EDITEUR = "corrext/editeur-de-relecture/"  # dans la colonne « Les outils » du panneau Corrext et dans le pied « Plateforme »


def ajout(href, apres=None, colonne=0):
    a = {"colonne": colonne, "href": href, "titre": "Titre " + href, "desc": "Description " + href}
    return {**a, "apres": apres} if apres else a


class TestAjoutsDeMenu(unittest.TestCase):
    """menu.appliquer_ajouts : entrées de src/data/menu-ajouts.json insérées dans le méga-menu et le pied de page."""

    @classmethod
    def setUpClass(cls):
        cls.nav_v1 = menu.lire_menu((build.NEURON / "src/partials/nav.html").read_text(encoding="utf-8"))
        cls.pied_v1 = menu.lire_pied((build.NEURON / "src/partials/footer.html").read_text(encoding="utf-8"))

    def frais(self):
        return copy.deepcopy(self.nav_v1), copy.deepcopy(self.pied_v1)

    def test_fichier_par_defaut_vide(self):
        brut = json.loads((ICI / "src/data/menu-ajouts.json").read_text(encoding="utf-8"))
        self.assertEqual(set(brut), {"panneaux", "pied"})
        nav, pied = self.frais()
        menu.appliquer_ajouts(nav, pied, {"panneaux": {}, "pied": {}})
        self.assertEqual((nav, pied), (self.nav_v1, self.pied_v1))

    def test_ajout_apres_une_entree_du_panneau_et_du_pied(self):
        nav, pied = self.frais()
        ajouts = {"panneaux": {"corrext": [ajout("corrext/plugin-essai/", EDITEUR)]},
                  "pied": {"Plateforme": [{"apres": EDITEUR, "href": "corrext/plugin-essai/", "texte": "Plugin d'essai"}]}}
        self.assertIs(menu.appliquer_ajouts(nav, pied, ajouts)[0], nav)
        # colonne 0 déclarée comme dans l'exemple du plan, alors que l'entrée de référence est dans « Les outils » :
        # le lien suit l'entrée citée, où qu'elle soit dans le panneau
        liens = [l["href"] for c in nav["panneaux"]["corrext"]["colonnes"] for l in c["liens"]]
        self.assertEqual(liens[liens.index(EDITEUR) + 1], "corrext/plugin-essai/")
        outils = nav["panneaux"]["corrext"]["colonnes"][1]["liens"]
        self.assertEqual(outils[2]["href"], EDITEUR)
        self.assertEqual(outils[3], {"href": "corrext/plugin-essai/", "titre": "Titre corrext/plugin-essai/",
                                     "desc": "Description corrext/plugin-essai/"})
        items = [i["href"] for c in pied["colonnes"] if c["titre"] == "Plateforme" for i in c["items"]]
        self.assertEqual(items[items.index(EDITEUR) + 1], "corrext/plugin-essai/")
        # le reste du menu est inchangé : un lien de plus dans le panneau et dans le pied
        self.assertEqual(sum(len(c["liens"]) for c in nav["panneaux"]["corrext"]["colonnes"]),
                         sum(len(c["liens"]) for c in self.nav_v1["panneaux"]["corrext"]["colonnes"]) + 1)
        self.assertEqual(nav["panneaux"]["solutions"], self.nav_v1["panneaux"]["solutions"])

    def test_plusieurs_ajouts_apres_la_meme_entree_gardent_l_ordre_du_fichier(self):
        nav, pied = self.frais()
        menu.appliquer_ajouts(nav, pied, {"panneaux": {"corrext": [
            ajout("corrext/premier/", EDITEUR), ajout("corrext/deuxieme/", EDITEUR), ajout("corrext/suite/", "corrext/premier/")]}})
        liens = [l["href"] for l in nav["panneaux"]["corrext"]["colonnes"][1]["liens"]]
        debut = liens.index(EDITEUR)
        self.assertEqual(liens[debut + 1:debut + 4], ["corrext/premier/", "corrext/suite/", "corrext/deuxieme/"])

    def test_sans_apres_en_fin_de_la_colonne_indiquee(self):
        nav, pied = self.frais()
        menu.appliquer_ajouts(nav, pied, {"panneaux": {"ressources": [ajout("ressources/essai/", colonne=2)]},
                                          "pied": {"Ressources": [{"href": "ressources/essai/", "texte": "Essai"}]}})
        self.assertEqual(nav["panneaux"]["ressources"]["colonnes"][2]["liens"][-1]["href"], "ressources/essai/")
        self.assertEqual([c for c in pied["colonnes"] if c["titre"] == "Ressources"][0]["items"][-1],
                         {"href": "ressources/essai/", "texte": "Essai"})

    def test_ajouts_rendus_dans_l_en_tete_mobile_et_le_pied(self):
        nav, pied = self.frais()
        menu.appliquer_ajouts(nav, pied, {"panneaux": {"corrext": [ajout("corrext/plugin-essai/", EDITEUR)]},
                                          "pied": {"Plateforme": [{"apres": EDITEUR, "href": "corrext/plugin-essai/", "texte": "Essai"}]}})
        entete = menu.rendre_entete(nav)
        self.assertIn('<a class="mg-a" href="{{ROOT}}corrext/plugin-essai/"><b>Titre corrext/plugin-essai/</b>'
                      '<em>Description corrext/plugin-essai/</em></a>', entete)
        self.assertIn('<a href="{{ROOT}}corrext/plugin-essai/">Titre corrext/plugin-essai/</a>', entete)  # menu mobile
        self.assertIn('<li><a href="{{ROOT}}corrext/plugin-essai/">Essai</a></li>', menu.rendre_pied(pied))

    def test_erreurs_explicites(self):
        cas = {
            "panneau inconnu": {"panneaux": {"absent": [ajout("x/")]}},
            "entrée de référence absente": {"panneaux": {"corrext": [ajout("x/", "n/existe/pas/")]}},
            "colonne hors limite": {"panneaux": {"corrext": [ajout("x/", colonne=9)]}},
            "colonne de pied inconnue": {"pied": {"Absente": [{"href": "x/", "texte": "x"}]}},
            "référence de pied absente": {"pied": {"Plateforme": [{"apres": "n/existe/pas/", "href": "x/", "texte": "x"}]}},
        }
        for nom, ajouts in cas.items():
            with self.subTest(nom):
                nav, pied = self.frais()
                with self.assertRaises(ValueError):
                    menu.appliquer_ajouts(nav, pied, ajouts)

    def test_ajouts_pris_dans_la_construction(self):
        """Le build lit menu-ajouts.json : le lien est dans le panneau, le menu mobile et le pied de toutes les pages."""
        with tempfile.TemporaryDirectory() as tmp:
            f = Path(tmp) / "menu-ajouts.json"
            f.write_text(json.dumps({"panneaux": {"corrext": [ajout("contact/", EDITEUR, 1)]},
                                     "pied": {"Plateforme": [{"apres": EDITEUR, "href": "contact/", "texte": "Lien ajouté"}]}}),
                         encoding="utf-8")
            sortie = support.construire(tmp, ["", "contact/"], patches=[mock.patch.object(menu, "AJOUTS", f)])
            h = (sortie / "fr/index.html").read_text(encoding="utf-8")
            self.assertEqual(h.count("<b>Titre contact/</b>"), 1)
            self.assertIn('<li><a href="../fr/contact/">Lien ajouté</a></li>', h)
            self.assertIn('<a href="../fr/contact/">Titre contact/</a>', h)  # menu mobile


if __name__ == "__main__":
    unittest.main()
