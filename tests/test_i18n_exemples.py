"""Exemples de loi du glossaire dans la langue de la page (tâche 3.3) : outils/i18n/exemples_glossaire.py et son
branchement dans traduire.analyser.

Les pages V1 des tests sont synthétiques (dossier temporaire à la place de Sites/neuron) ; la dernière classe lit les 52 pages
de termes du site et leurs pages V1 réelles (lecture seule)."""
import json
import tempfile
import unittest
from pathlib import Path
from unittest import mock

import build
from tests import support
from outils.i18n import controles, exemples_glossaire as E, langues, traduire as T
from outils.i18n import segments as S
from outils.i18n.table import Table

PAGE = "ressources/glossaire/aktienkapital/"
ALLEMAND = "Das <mark>Aktienkapital</mark> beträgt mindestens 100 000 Franken."
FRANCAIS = "Le <mark>capital-actions</mark> ne peut être inférieur à 100 000 francs."
ITALIEN = "Il <mark>capitale azionario</mark> non può essere inferiore a 100 000 franchi."
FIXTURES = Path(__file__).resolve().parent / "fixtures" / "i18n"
ABSENT = FIXTURES / "absent"


def page_fr(francais=FRANCAIS):
    """Page française assemblée réduite à la fenêtre CHnell d'un terme, telle que le composeur et y_accessibilite l'écrivent."""
    return ('<!DOCTYPE html>\n<html lang="fr"><head><meta charset="utf-8"></head><body>\n<main id="main"><section>'
            '<div class="cr cr-frag cr-chst"><div class="cr-ch"><div class="cr-ch-q"><span class="cr-box"><b class="lk-q" '
            'lang="de">Aktienkapital</b></span><span class="cr-lang lk-l1">Allemand</span><span class="cr-swap"><svg viewBox="0 0 16 16" aria-hidden="true"><path d="M3 5h9"/></svg></span>'
            '<span class="cr-lang lk-l2">Français</span><span class="lk-c"></span></div><div class="lk-r">'
            f'<div style="--i:0"><p lang="de">{ALLEMAND}</p><p lang="fr">{francais}</p></div></div>'
            '<div class="cr-ch-f"><span class="cr-btn">Close</span></div></div></div></section></main>\n</body></html>\n')


def colonne(libelle, lang, passage):
    return f'<div><i>{libelle}</i><p lang="{lang}">{passage}</p></div>'


def ecrire_v1(neuron, page, langue, colonnes):
    """Page V1 de la langue, réduite à l'exemple : colonnes = [(libellé, lang, passage)]."""
    fichier = Path(neuron) / "docs" / langues.route(page, langue) / "index.html"
    fichier.parent.mkdir(parents=True, exist_ok=True)
    corps = "\n        ".join(colonne(*c) for c in colonnes)
    fichier.write_text('<section class="gex"><div class="gex-box"><h2>Le terme</h2>\n      <div class="gex-row">\n        '
                       f'{corps}\n      </div>\n      <p class="gsrc">Source</p></div></section>\n', encoding="utf-8")


class Base(unittest.TestCase):
    def setUp(self):
        tmp = tempfile.TemporaryDirectory()
        self.addCleanup(tmp.cleanup)
        self.neuron = Path(tmp.name)

    def v1(self, langue, colonnes, page=PAGE):
        ecrire_v1(self.neuron, page, langue, colonnes)


class TestExemples(Base):
    def test_de_garde_le_francais(self):
        # allemand : l'exemple reste allemand et français, sans même lire la V1 (dossier vide)
        h = page_fr()
        self.assertEqual(E.exemples(h, PAGE, "de", self.neuron), h)

    def test_it_remplace_par_l_italien_v1(self):
        self.v1("it", [("Tedesco", "de", ALLEMAND), ("Italiano", "it", ITALIEN)])
        h = E.exemples(page_fr(), PAGE, "it", self.neuron)
        self.assertIn(f'<p lang="de">{ALLEMAND}</p><p lang="it">{ITALIEN}</p>', h)  # l'allemand reste, de même rang
        self.assertIn('<span class="cr-lang lk-l2" lang="it">Italiano</span><span class="lk-c"></span>', h)
        self.assertNotIn("capital-actions", h)
        self.assertNotIn("Français", h)
        # le reste de la page ne bouge pas
        self.assertEqual(h.replace(f'<p lang="it">{ITALIEN}</p>', f'<p lang="fr">{FRANCAIS}</p>')
                         .replace(' lang="it">Italiano', '>Français'), page_fr())

    def test_en_remplace_par_l_anglais_v1(self):
        self.v1("en", [("German", "de", ALLEMAND), ("English", "en", "The <mark>share capital</mark> amounts to 100,000 francs.")])
        h = E.exemples(page_fr(), PAGE, "en", self.neuron)
        self.assertIn('<p lang="en">The <mark>share capital</mark> amounts to 100,000 francs.</p>', h)
        self.assertIn('<span class="cr-lang lk-l2" lang="en">English</span>', h)

    def test_le_passage_et_le_libelle_ne_sont_plus_a_traduire(self):
        # dans la page d'origine, le libellé et le paragraphe français sont des unités ; remplacés, il n'y en a plus
        avant = [u["texte"] for u in S.extraire_page(page_fr())]
        self.assertIn("{1}Français{/1}{2}{/2}", avant)
        self.v1("it", [("Tedesco", "de", ALLEMAND), ("Italiano", "it", ITALIEN)])
        apres = [u["texte"] for u in S.extraire_page(E.exemples(page_fr(), PAGE, "it", self.neuron))]
        self.assertFalse(any(m in t for t in apres for m in ("Français", "Italiano", "capitale", "capital-actions", "Aktien")))
        self.assertIn("{1}Allemand{/1}", apres)  # le libellé de gauche suit la table

    def test_nombres_differents_refuses(self):
        # deux passages italiens dans la V1 pour un exemple dans la page
        self.v1("it", [("Tedesco", "de", ALLEMAND), ("Italiano", "it", ITALIEN), ("Italiano", "it", ITALIEN)])
        with self.assertRaisesRegex(ValueError, "2 passage"):
            E.exemples(page_fr(), PAGE, "it", self.neuron)
        # aucun passage italien ni français dans la V1
        self.v1("it", [("Tedesco", "de", ALLEMAND)])
        with self.assertRaisesRegex(ValueError, "0 passage"):
            E.exemples(page_fr(), PAGE, "it", self.neuron)

    def test_pas_d_exemple_dans_la_page_refuse(self):
        self.v1("it", [("Tedesco", "de", ALLEMAND), ("Italiano", "it", ITALIEN)])
        with self.assertRaisesRegex(ValueError, "introuvable"):
            E.exemples(page_fr().replace('<p lang="fr">', "<p>"), PAGE, "it", self.neuron)

    def test_page_v1_absente_refusee(self):
        with self.assertRaisesRegex(ValueError, "page V1 absente"):
            E.exemples(page_fr(), PAGE, "it", self.neuron)

    def test_page_v1_sans_exemple_refusee(self):
        fichier = self.neuron / "docs" / langues.route(PAGE, "it") / "index.html"
        fichier.parent.mkdir(parents=True)
        fichier.write_text("<html><body>rien</body></html>", encoding="utf-8")
        with self.assertRaisesRegex(ValueError, "aucun exemple"):
            E.exemples(page_fr(), PAGE, "it", self.neuron)

    def test_allemand_different_refuse(self):
        self.v1("it", [("Tedesco", "de", ALLEMAND.replace("mindestens", "höchstens")), ("Italiano", "it", ITALIEN)])
        with self.assertRaisesRegex(ValueError, "paragraphe allemand"):
            E.exemples(page_fr(), PAGE, "it", self.neuron)

    def test_v1_restee_en_francais_garde_le_francais(self):
        # six termes de la V1 anglaise : l'exemple y reste allemand et français, libellé « French »
        self.v1("en", [("German", "de", ALLEMAND), ("French", "fr", FRANCAIS)])
        h = E.exemples(page_fr(), PAGE, "en", self.neuron)
        self.assertIn(f'<p lang="de">{ALLEMAND}</p><p lang="fr">{FRANCAIS}</p>', h)
        self.assertIn('<span class="cr-lang lk-l2" lang="en">French</span>', h)
        # en italien, le même cas (V1 en français) est accepté de la même façon
        self.v1("it", [("Tedesco", "de", ALLEMAND), ("Francese", "fr", FRANCAIS)])
        self.assertIn('lang="it">Francese</span>', E.exemples(page_fr(), PAGE, "it", self.neuron))

    def test_hors_pages_de_termes_inchange(self):
        h = page_fr()
        for page in ("ressources/glossaire/", "contact/", ""):
            self.assertEqual(E.exemples(h, page, "it", self.neuron), h)

    def test_aucun_tiret_cadratin_ni_demi_cadratin(self):
        self.v1("it", [("Tedesco", "de", ALLEMAND), ("Italiano", "it", ITALIEN)])
        self.assertEqual(controles.tirets(E.exemples(page_fr(), PAGE, "it", self.neuron)), [])


class TestBranchement(Base):
    """traduire.analyser applique les exemples avant l'extraction pour les pages de termes en italien et en anglais."""

    def table(self, langue):
        t = Table(langue, ABSENT)
        for u in S.extraire_page(E.exemples(page_fr(), PAGE, langue, self.neuron)):
            if not u["lang_fr"] and not T._invariant(u["texte"], langue):
                t.poser(u["texte"], f"{langue.upper()} {u['texte']}", "relu", "test")
        return t

    def traduire(self, langue, h=None):
        return T.traduire(h or page_fr(), PAGE, langue, self.table(langue), "production", self.neuron)

    def test_italien_publiable_avec_l_exemple_v1(self):
        self.v1("it", [("Tedesco", "de", ALLEMAND), ("Italiano", "it", ITALIEN)])
        html, manquants = self.traduire("it")
        self.assertEqual(manquants, [])
        self.assertIn(f'<p lang="it">{ITALIEN}</p>', html)
        self.assertIn('lang="it">Italiano</span>', html)
        self.assertIn(f'<p lang="de">{ALLEMAND}</p>', html)
        self.assertNotIn("capital-actions", html)

    def test_anglais_publiable_avec_l_exemple_v1(self):
        self.v1("en", [("German", "de", ALLEMAND), ("English", "en", "The <mark>share capital</mark> is 100,000 francs.")])
        html, manquants = self.traduire("en")
        self.assertEqual(manquants, [])
        self.assertIn('<p lang="en">The <mark>share capital</mark> is 100,000 francs.</p>', html)

    def test_site_v1_du_build_par_defaut(self):
        self.v1("it", [("Tedesco", "de", ALLEMAND), ("Italiano", "it", ITALIEN)])
        with mock.patch.object(build, "NEURON", self.neuron):
            html, manquants = T.traduire(page_fr(), PAGE, "it", self.table("it"), "production")
        self.assertEqual(manquants, [])
        self.assertIn(f'<p lang="it">{ITALIEN}</p>', html)

    def test_allemand_garde_le_francais_balise(self):
        # sans exemples : le paragraphe français (lang="fr") n'est ni extrait ni manquant, il reste français
        t = Table("de", ABSENT)
        for u in S.extraire_page(page_fr()):
            if not u["lang_fr"] and not T._invariant(u["texte"], "de"):
                t.poser(u["texte"], "DE " + u["texte"], "relu", "test")
        html, manquants = T.traduire(page_fr(), PAGE, "de", t, "production", self.neuron)
        self.assertEqual(manquants, [])
        self.assertIn(f'<p lang="de">{ALLEMAND}</p><p lang="fr">{FRANCAIS}</p>', html)
        self.assertEqual(controles.restes_fr(html, "de"), [])

    def test_exemple_refuse_page_non_publiable(self):
        self.v1("it", [("Tedesco", "de", ALLEMAND), ("Italiano", "it", ITALIEN), ("Italiano", "it", ITALIEN)])
        html, manquants = T.traduire(page_fr(), PAGE, "it", Table("it", ABSENT), "production", self.neuron)
        self.assertEqual(html, "")
        self.assertEqual([(m["raison"], m["cle"], m["statut"]) for m in manquants], [("exemples", None, None)])
        self.assertIn("2 passage", manquants[0]["fr"])


def _termes():
    return sorted(p for p in build.PAGES if p.startswith("ressources/glossaire/") and p != "ressources/glossaire/")


@unittest.skipUnless((build.NEURON / "docs").is_dir(), "site V1 absent")
class TestPagesReelles(unittest.TestCase):
    """Les 52 pages de termes du site et leurs pages V1 réelles, en italien et en anglais."""

    # termes restés en français dans la V1 anglaise (la loi n'existe pas en anglais) : allemand et français, libellé « French »
    FRANCAIS_EN_V1_EN = {"beschwerde", "bankgeheimnis", "quellensteuer", "steuerhinterziehung", "verrechnungssteuer",
                         "versicherungsvertrag"}

    @classmethod
    def setUpClass(cls):
        sortie = support.site_complet()
        cls.pages = {p: support.chemin(sortie, p).read_text(encoding="utf-8") for p in _termes()}

    def test_cinquante_deux_termes(self):
        self.assertEqual(len(self.pages), 52)

    def test_aucune_page_refusee_italien_et_anglais(self):
        for langue in ("it", "en"):
            for p, h in self.pages.items():
                nouveau = E.exemples(h, p, langue, build.NEURON)
                self.assertNotEqual(nouveau, h, (langue, p))
                self.assertEqual(controles.tirets(nouveau), [], (langue, p))
                # plus aucun passage français à traduire dans l'exemple : l'extraction ne voit que l'allemand de la V1 en lang
                textes = [u["texte"] for u in S.extraire_page(nouveau)]
                self.assertNotIn("{1}Français{/1}{2}{/2}", textes, (langue, p))
                self.assertNotIn("Italiano", " ".join(textes), (langue, p))  # le libellé V1 porte lang, il n'est pas extrait

    def test_francais_garde_dans_la_v1_anglaise(self):
        gardes = {p.split("/")[2] for p, h in self.pages.items()
                  if 'lang="fr">' in E.exemples(h, p, "en", build.NEURON).split('<div class="lk-r">')[1].split("cr-ch-f")[0]}
        self.assertEqual(gardes, self.FRANCAIS_EN_V1_EN)
        for p, h in self.pages.items():  # en italien, tous les exemples sont remplacés
            lignes = E.exemples(h, p, "it", build.NEURON).split('<div class="lk-r">')[1].split("cr-ch-f")[0]
            self.assertNotIn('lang="fr"', lignes, p)

    def test_allemand_inchange(self):
        for p, h in self.pages.items():
            self.assertEqual(E.exemples(h, p, "de", build.NEURON), h, p)


if __name__ == "__main__":
    unittest.main()
