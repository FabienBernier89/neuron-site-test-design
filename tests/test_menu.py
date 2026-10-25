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
from outils.i18n import empreintes  # noqa: E402
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
        # « Tous les domaines » est rendu en simple lien fléché (mg-tous), sans sous-titre (Fabien, 2026-10-19)
        self.assertEqual(html.count('class="mg-a"') + html.count('class="mg-card"') + html.count('class="mg-tous"'), attendu + ajoutes)
        self.assertIn('<span class="lien">Voir tous les domaines</span>', html)

    def test_memes_libelles_dans_le_meme_ordre(self):
        titres = [l["titre"] for p in self.m["panneaux"].values() for c in p["colonnes"] for l in c["liens"]]
        self.assertEqual(titres[0], "Corrext, le poste de commande")
        self.assertEqual(titres[-1], "Agence de traduction ou plateforme")
        self.assertEqual([e["libelle"] for e in self.m["entrees"]], ["Corrext", "Solutions", "LexMachina", "Ressources"])

    def test_chaque_lien_du_mega_menu_a_un_sous_titre(self):
        """Tout lien du méga-menu porte un sous-titre ; ceux de la V1 qui n'en avaient pas reprennent le sous-titre de leur page."""
        h = build.chemin_page("").read_text(encoding="utf-8")
        liens = re.findall(r'<a class="mg-a" href="[^"]+">(.*?)</a>', h, re.S)
        self.assertGreater(len(liens), 30)
        for l in liens:
            self.assertRegex(l, r"^<b>[^<]+</b><em>[^<]+</em>$")
        self.assertIn("<b>Cabinets d&#x27;avocats</b><em>Traduire un dossier sans jamais le sortir de Suisse</em>".replace("&#x27;", "'"), h)

    def test_sous_titres_allonges_sources_et_utilises(self):
        """menu-sous-titres.json : chaque sous-titre allongé (deux lignes) est sourcé, validé (décision n° 9 de Fabien) et affiché sous son titre."""
        d = json.loads((ICI / "src/data/menu-sous-titres.json").read_text(encoding="utf-8"))
        h = build.chemin_page("").read_text(encoding="utf-8").replace("&#x27;", "'")
        self.assertEqual(len(d["entrees"]), 19)
        for e in d["entrees"]:
            self.assertEqual(e["statut"], "valide", e["titre"])  # décision n° 9 : « tous les textes en français sont bons »
            self.assertIn("décision n° 9", e["source"], e["titre"])
            self.assertIn(f"<b>{e['titre']}</b><em>{e['texte']}</em>", h, e["titre"])

    def test_sous_titres_sur_deux_lignes(self):
        """Sous-titres du méga-menu à hauteur fixe de deux lignes : les titres s'alignent d'une colonne à l'autre."""
        css = (build.DOCS / "assets/site.css").read_text(encoding="utf-8") if hasattr(build, "DOCS") else ""
        css = css or (build.chemin_page("").parents[1] / "assets/site.css").read_text(encoding="utf-8")
        self.assertIn(".mg-a em{display:block;max-width:248px;min-height:36px;margin-top:4px;font:400 13px/18px", css)

    def test_bouton_connexion(self):
        """Lien « Connexion » vers la page de connexion Corrext, à gauche du bouton de démo et dans le menu mobile."""
        url = ("https://auth.corrext.com/realms/corrext/protocol/openid-connect/auth?client_id=corrext&amp;scope=openid%20email%20profile"
               "&amp;response_type=code&amp;redirect_uri=https%3A%2F%2Fcorrext.com%2Fapi%2Fauth%2Fcallback%2Fkeycloak")
        sortie = build.chemin_page("").parent
        pages = list(sortie.rglob("index.html"))
        self.assertGreater(len(pages), 100)
        avec = [f for f in pages if '<div class="hd-cta">' in f.read_text(encoding="utf-8")]
        self.assertGreater(len(avec), 100)  # seules les pages à en-tête réduit (contact) n'ont pas ce bloc
        for f in avec:
            h = f.read_text(encoding="utf-8")
            entete = h[h.index('<div class="hd-cta">'):]
            self.assertTrue(entete.startswith(f'<div class="hd-cta"><a class="hd-cx" href="{url}">Connexion</a><a class="btn btn-s"'), f)
            self.assertIn(f'<a class="mm-cx" href="{url}">Connexion</a><a class="btn mm-cta"', h, f)

    def test_pied_disposition_v1(self):
        """Pied repris de la V1 : présentation, quatre colonnes, barre basse avec liens légaux et les trois thèmes."""
        html = build.chemin_page("").read_text(encoding="utf-8")
        pied = html[html.index('<footer class="pied">'):]
        source = (build.NEURON / "src/partials/footer.html").read_text(encoding="utf-8")
        apropos = re.search(r'<div class="footer-about">.*?<p>(.*?)</p>', source, re.S).group(1)
        self.assertIn('<div class="fp-a">', pied)
        self.assertIn(apropos, pied)
        self.assertIn('href="https://www.linkedin.com/company/neur-on"', pied)
        self.assertEqual([re.sub(r"<[^>]+>", "", t) for t in re.findall(r'<p class="fp-h">(.*?)</p>', pied)],
                         ["Plateforme", "Solutions", "Ressources", "Neur.on"])
        self.assertEqual(pied.count('<li class="fp-c">'), 2)
        self.assertIn('href="mailto:team@corrext.com"', pied)
        barre = re.search(r'<div class="fp-b">.*?</div>\n', pied, re.S).group(0)
        self.assertIn("Mentions légales et CGU", barre)
        self.assertIn("Protection des données", barre)
        self.assertNotIn('class="theme"', barre)
        colonne = re.search(r'<p class="fp-h">Neur\.on</p>.*?</div>\n', pied, re.S).group(0)
        self.assertEqual(colonne.count("data-theme-set="), 3)
        self.assertLess(colonne.index("team@corrext.com"), colonne.index('class="theme"'))


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
        self.assertEqual(set(brut), {"panneaux", "pied", "entrees", "libelles"})
        self.assertEqual(brut["libelles"], {"corrext": "Produit"})  # onglet « Corrext » renommé (Fabien, 2026-10-20)
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


class TestSelecteurDeLangue(unittest.TestCase):
    """Sélecteur de langue de l'en-tête (tâche 1.4) : balisage de la passe 1, résolution par page (menu.resoudre_selecteur),
    retrait quand une seule langue est construite."""

    @classmethod
    def setUpClass(cls):
        cls.nav = menu.lire_menu((build.NEURON / "src/partials/nav.html").read_text(encoding="utf-8"))

    FR_DE = {"fr": {"", "contact/"}, "de": {"", "contact/"}}

    def selecteurs(self, html):
        return re.findall(r'<nav class="hd-lang".*?</nav>', html)

    def test_selecteur_absent_si_une_langue(self):
        self.assertNotIn("hd-lang", menu.rendre_entete(self.nav))
        self.assertNotIn("hd-lang", menu.rendre_entete(self.nav, langues=("fr",)))
        self.assertNotIn("hd-lang", menu.rendre_entete(self.nav, minimal=True, langues=("fr",)))
        self.assertNotIn("hd-lang", menu.rendre_mobile(self.nav))

    def test_balisage_de_la_passe_1(self):
        """Une ligne, sans retour à la ligne autour, dans .hd-cta avant « Connexion » ; marqueurs {{LANGUE:xx}} à résoudre."""
        h = menu.rendre_entete(self.nav, langues=("fr", "de"))
        attendu = ('<nav class="hd-lang" aria-label="Langue"><a href="{{LANGUE:fr}}" hreflang="fr-CH" lang="fr" translate="no">FR</a>'
                   '<a href="{{LANGUE:de}}" hreflang="de-CH" lang="de" translate="no">DE</a></nav>')
        self.assertIn('<div class="hd-cta">' + attendu + '<a class="hd-cx"', h)
        self.assertEqual(len(self.selecteurs(h)), 2)  # en-tête et menu mobile
        self.assertEqual(self.selecteurs(h)[0], attendu)

    def test_selecteur_page_equivalente(self):
        """Depuis fr/contact/ : le lien DE mène à la page équivalente (de/kontakt/), la langue de la page est marquée."""
        h = menu.resoudre_selecteur(menu.rendre_entete(self.nav, langues=("fr", "de")), "contact/", "fr", self.FR_DE)
        self.assertNotIn("{{LANGUE:", h)
        self.assertIn('<a href="{{ROOT}}fr/contact/" hreflang="fr-CH" lang="fr" translate="no" aria-current="true">FR</a>', h)
        self.assertIn('<a href="{{ROOT}}de/kontakt/" hreflang="de-CH" lang="de" translate="no">DE</a>', h)
        self.assertEqual(h.count('aria-current="true"'), 2)  # en-tête et menu mobile

    def test_langue_de_la_page_marquee_hors_francais(self):
        h = menu.resoudre_selecteur(menu.rendre_entete(self.nav, langues=("fr", "de")), "contact/", "de", self.FR_DE)
        self.assertIn('<a href="{{ROOT}}de/kontakt/" hreflang="de-CH" lang="de" translate="no" aria-current="true">DE</a>', h)
        self.assertIn('<a href="{{ROOT}}fr/contact/" hreflang="fr-CH" lang="fr" translate="no">FR</a>', h)

    def test_selecteur_repli_accueil(self):
        """Page non construite en de : le lien DE mène à l'accueil allemand."""
        construites = {"fr": {"", "contact/", "corrext/"}, "de": {"", "contact/"}}
        h = menu.resoudre_selecteur(menu.rendre_entete(self.nav, langues=("fr", "de")), "corrext/", "fr", construites)
        self.assertIn('<a href="{{ROOT}}de/" hreflang="de-CH"', h)
        self.assertIn('<a href="{{ROOT}}fr/corrext/" hreflang="fr-CH" lang="fr" translate="no" aria-current="true">', h)

    def test_page_d_accueil_francaise(self):
        h = menu.resoudre_selecteur(menu.rendre_entete(self.nav, langues=("fr", "de")), "", "fr", self.FR_DE)
        self.assertIn('<a href="{{ROOT}}fr/" hreflang="fr-CH"', h)
        self.assertIn('<a href="{{ROOT}}de/" hreflang="de-CH"', h)

    def test_langue_non_construite_retiree(self):
        """Trois langues configurées, l'italien sans page : son lien disparaît, les deux autres restent."""
        h = menu.resoudre_selecteur(menu.rendre_entete(self.nav, langues=("fr", "de", "it")), "contact/", "fr", self.FR_DE)
        self.assertNotIn('hreflang="it-CH"', h)
        self.assertEqual(h.count('hreflang="de-CH"'), 2)

    def test_une_seule_langue_construite_retire_la_nav(self):
        h = menu.rendre_entete(self.nav, langues=("fr", "de"))
        sans = menu.resoudre_selecteur(h, "contact/", "fr", {"fr": {"", "contact/"}, "de": set()})
        self.assertNotIn("hd-lang", sans)
        self.assertEqual(sans, menu.rendre_entete(self.nav))  # octet pour octet l'en-tête français d'une seule langue
        self.assertEqual(menu.resoudre_selecteur(h, "contact/", "fr", {"fr": {"contact/"}}), menu.rendre_entete(self.nav))

    def test_selecteur_mobile(self):
        """Menu mobile : sélecteur en dernier dans .mm, après le bouton de démo."""
        m = menu.rendre_mobile(self.nav, langues=("fr", "de"))
        fin = m[m.index('<a class="btn mm-cta"'):]
        self.assertRegex(fin, r'Demander une démo</a>\n<nav class="hd-lang" aria-label="Langue">.*</nav></div>\n</div>\n$')
        res = menu.resoudre_selecteur(m, "contact/", "fr", self.FR_DE)
        self.assertIn('href="{{ROOT}}de/kontakt/"', res)
        self.assertEqual(menu.resoudre_selecteur(m, "contact/", "fr", {"fr": {"contact/"}}), menu.rendre_mobile(self.nav))

    def test_selecteur_gabarit_minimal(self):
        """Gabarit de contact (sans navigation) : le sélecteur est émis quand même, dans .hd-in après le logo."""
        h = menu.rendre_entete(self.nav, minimal=True, langues=("fr", "de"))
        self.assertEqual(len(self.selecteurs(h)), 1)
        self.assertNotIn('class="hd-cta"', h)
        self.assertRegex(h, r'</a>\n<nav class="hd-lang" aria-label="Langue">.*</nav></div>\n</header>\n$')
        res = menu.resoudre_selecteur(h, "contact/", "fr", self.FR_DE)
        self.assertIn('href="{{ROOT}}de/kontakt/"', res)
        self.assertEqual(menu.resoudre_selecteur(h, "contact/", "fr", {"fr": {"contact/"}}), menu.rendre_entete(self.nav, minimal=True))

    def test_page_hors_table_des_adresses(self):
        """La 404 n'est dans aucune table : lien français vers fr/, lien allemand vers l'accueil allemand, sans erreur."""
        h = menu.resoudre_selecteur(menu.rendre_entete(self.nav, langues=("fr", "de")), "404.html", "fr", self.FR_DE)
        self.assertIn('<a href="{{ROOT}}fr/" hreflang="fr-CH"', h)
        self.assertIn('<a href="{{ROOT}}de/" hreflang="de-CH"', h)

    def test_retrait_rend_le_fr_identique(self):
        """fr+de configurées, aucune page DE construite (TRADUIRE signale un segment manquant partout) : le français est
        identique octet pour octet à la référence prise avant le lot de traduction."""
        with tempfile.TemporaryDirectory() as tmp:
            absente = mock.patch.object(build, "TRADUIRE", lambda html, page, langue: (html, ["segment manquant"]))
            sortie = support.construire(tmp, pages=build.PAGES, langues=("fr", "de"), patches=[absente])
            self.assertFalse((sortie / "de").exists())
            obtenu = empreintes.empreintes(sortie)
        reference = json.loads((ICI / "tests/fixtures/i18n/empreintes-fr-apercu.json").read_text(encoding="utf-8"))
        self.assertEqual([k for k in obtenu if obtenu[k] != reference.get(k)], [])
        self.assertEqual(sorted(set(reference) - set(obtenu)), [])


class TestSelecteurDansLeBuild(unittest.TestCase):
    """Le build pose le sélecteur sur les pages construites quand plusieurs langues le sont (la traduction n'est pas
    branchée : les pages « de » portent le texte français, seuls le balisage et les adresses comptent)."""

    @classmethod
    def setUpClass(cls):
        cls._tmp = tempfile.TemporaryDirectory()
        cls.sortie = support.construire(cls._tmp.name, pages=("", "contact/"), langues=("fr", "de"))

    @classmethod
    def tearDownClass(cls):
        cls._tmp.cleanup()

    def lire(self, page, langue):
        return support.chemin(self.sortie, page, langue).read_text(encoding="utf-8")

    def test_page_francaise_renvoie_vers_la_page_allemande(self):
        h = self.lire("contact/", "fr")
        self.assertIn('<a href="../../de/kontakt/" hreflang="de-CH" lang="de" translate="no">DE</a>', h)
        self.assertIn('<a href="../../fr/contact/" hreflang="fr-CH" lang="fr" translate="no" aria-current="true">FR</a>', h)

    def test_lien_francais_du_selecteur_reste_francais_sur_la_page_allemande(self):
        """Le sélecteur est résolu après la localisation des liens : le lien FR n'est pas renvoyé vers la page DE."""
        h = self.lire("contact/", "de")
        self.assertIn('<a href="../../fr/contact/" hreflang="fr-CH" lang="fr" translate="no">FR</a>', h)
        self.assertIn('<a href="../../de/kontakt/" hreflang="de-CH" lang="de" translate="no" aria-current="true">DE</a>', h)
        self.assertNotIn("{{", h)

    def test_accueil_avec_entete_complet_et_menu_mobile(self):
        h = self.lire("", "de")
        self.assertEqual(h.count('<nav class="hd-lang"'), 2)
        self.assertIn('<div class="hd-cta"><nav class="hd-lang"', h)
        self.assertIn('<a href="../de/" hreflang="de-CH" lang="de" translate="no" aria-current="true">DE</a>', h)

    def test_page_404_avec_selecteur_vers_les_accueils(self):
        """Depuis la tâche 1.5 la 404 connaît les langues construites : sélecteur vers les accueils (elle n'est dans
        aucune table d'adresses), langue de la page marquée, sur la 404 française comme sur l'allemande."""
        fr = (self.sortie / "404.html").read_text(encoding="utf-8")
        self.assertIn('<a href="fr/" hreflang="fr-CH" lang="fr" translate="no" aria-current="true">FR</a>', fr)
        self.assertIn('<a href="de/" hreflang="de-CH" lang="de" translate="no">DE</a>', fr)
        de = (self.sortie / "de/404.html").read_text(encoding="utf-8")
        self.assertIn('<a href="de/" hreflang="de-CH" lang="de" translate="no" aria-current="true">DE</a>', de)

    def test_page_404_sans_selecteur_en_francais_seul(self):
        """Le français seul construit : la 404 n'a pas de sélecteur (elle est identique à celle d'avant la traduction)."""
        with tempfile.TemporaryDirectory() as tmp:
            sortie = support.construire(tmp, pages=("",), langues=("fr",))
            self.assertNotIn("hd-lang", (sortie / "404.html").read_text(encoding="utf-8"))


if __name__ == "__main__":
    unittest.main()
