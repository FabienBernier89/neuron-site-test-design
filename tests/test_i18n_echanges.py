"""Échanges avec les traducteurs (tâche 5.1) : export XLIFF 1.2, TMX 1.4 et glossaire CSV : outils/i18n/echanges.py.

Tout est synthétique : mini table allemande et mini pages écrites ici, dossiers temporaires pour les fichiers. Aucun test
ne lit ni n'écrit le dossier réel des échanges ni celui de la terminologie (Bibliotheque-Claude, Ruling 5)."""
import contextlib
import csv
import io
import json
import tempfile
import unittest
from pathlib import Path
from unittest import mock
from xml.etree import ElementTree as ET

import build
from outils.i18n import __main__ as cli
from outils.i18n import controles, echanges as E, traduire
from outils.i18n.table import Table, cle

ICI = Path(__file__).resolve().parent.parent
NS = "{urn:oasis:names:tc:xliff:document:1.2}"
XML_LANG = "{http://www.w3.org/XML/1998/namespace}lang"
JOUR = "2026-10-26"

CAPITAL = "Le {1}capital-actions{/1} de la société"
ADRESSE = "Adresse{1}Fribourg"
DEMO = "Demander une démo"
CONTACT = "Contact"
CORREXT = "Corrext Premium"
GLOSSAIRE = {"capital-actions": {"de": {"terme": "Aktienkapital", "source": "Fedlex : CO art. 620", "statut": "confirme"}},
             "prix": {"it": {"terme": "prezzo", "source": "CHnell", "statut": "confirme"}}}


def page(*corps):
    """Page FR assemblée minimale : un <p> par texte (le texte peut porter des balises)."""
    return ('<!DOCTYPE html>\n<html lang="fr"><head><meta charset="utf-8"></head><body>\n'
            f'<main id="main">{"".join(f"<p>{c}</p>" for c in corps)}</main>\n</body></html>')


PAGES = {"": page("Le <strong>capital-actions</strong> de la société", "Adresse<br>Fribourg", DEMO, CONTACT),
         "contact/": page(CONTACT, DEMO, "Neur.on"),
         "a-propos/": page("Notre équipe")}


def table_de(dossier):
    """Table allemande : un segment par statut, un marqueur ouvrant et un marqueur seul, une variante de page."""
    t = Table("de", dossier)
    t.poser(DEMO, "Demo anfragen", "v1", "V1 de/")
    t.poser(CAPITAL, "Das {1}Aktienkapital{/1} der Gesellschaft", "adapte", "adapté d'après la V1")
    t.poser(ADRESSE, "Adresse{1}Freiburg", "mt", "LexMachina")
    t.poser(CONTACT, "Kontakt", "v1", "V1 de/kontakt/")
    t.poser(CONTACT, "Kontakt aufnehmen", "v1", "V1 de/kontakt/", page="contact/")
    t.poser("Notre équipe", "Unser Team", "relu", "relu par Béatrice le 2026-09-01")
    t.poser(CORREXT, CORREXT, "invariant", "traduction V1 identique au français")
    t.poser("Neur.on", "Neur.on", "invariant", "traduction V1 identique au français")
    return t


def fichier_xliff(t, dossier, pages=None, statuts=("mt", "adapte", "v1", "invariant", "relu"), glossaire=None,
                  nom="de.xlf"):
    sortie = Path(dossier) / nom
    n = E.exporter_xliff("de", t, pages, set(statuts), sortie, assemblees=PAGES,
                         glossaire=GLOSSAIRE if glossaire is None else glossaire)
    return sortie, n


class Base(unittest.TestCase):
    def setUp(self):
        tmp = tempfile.TemporaryDirectory()
        self.addCleanup(tmp.cleanup)
        self.tmp = Path(tmp.name)
        self.langues = self.tmp / "langues"
        self.sortie = self.tmp / "export"
        self.table = table_de(self.langues)

    def exporter(self, **kw):
        return fichier_xliff(self.table, self.sortie, **kw)

    def unites(self, fichier):
        racine = ET.parse(fichier).getroot()
        return {u.get("id"): u for u in racine.iter(NS + "trans-unit")}


class TestExportXliff(Base):
    def test_xliff_bien_forme(self):
        fichier, n = self.exporter()
        racine = ET.parse(fichier).getroot()  # xml.etree le relit
        self.assertEqual(racine.tag, NS + "xliff")
        self.assertEqual(racine.get("version"), "1.2")
        f = racine.find(NS + "file")
        self.assertEqual((f.get("original"), f.get("source-language"), f.get("target-language"), f.get("datatype")),
                         ("neur-on.ai/de", "fr-CH", "de-CH", "html"))
        self.assertEqual(len(list(racine.iter(NS + "trans-unit"))), n)
        self.assertEqual(n, 7)  # CAPITAL, ADRESSE, DEMO, CONTACT (défaut), CONTACT (page), équipe, Neur.on
        self.assertTrue(fichier.read_bytes().startswith(b"<?xml"))

    def test_marqueurs_en_g_et_x(self):
        fichier, _ = self.exporter()
        u = self.unites(fichier)[cle(CAPITAL)]
        source, cible = u.find(NS + "source"), u.find(NS + "target")
        self.assertEqual([g.get("id") for g in source.iter(NS + "g")], ["1"])
        self.assertEqual(source.find(NS + "g").text, "capital-actions")
        self.assertEqual(cible.find(NS + "g").text, "Aktienkapital")
        self.assertEqual("".join(cible.itertext()), "Das Aktienkapital der Gesellschaft")
        a = self.unites(fichier)[cle(ADRESSE)]
        self.assertEqual([x.get("id") for x in a.find(NS + "source").iter(NS + "x")], ["1"])
        self.assertEqual([x.get("id") for x in a.find(NS + "target").iter(NS + "x")], ["1"])
        self.assertNotIn("{1}", fichier.read_text(encoding="utf-8"))

    def test_langues_des_unites(self):
        fichier, _ = self.exporter()
        u = self.unites(fichier)[cle(DEMO)]
        self.assertEqual(u.find(NS + "source").get(XML_LANG), "fr-CH")
        self.assertEqual(u.find(NS + "target").get(XML_LANG), "de-CH")
        self.assertEqual(u.find(NS + "source").text, DEMO)
        self.assertEqual(u.find(NS + "target").text, "Demo anfragen")

    def test_v1_et_invariant_approuves(self):
        fichier, _ = self.exporter()
        u = self.unites(fichier)
        self.assertEqual(u[cle(DEMO)].get("approved"), "yes")
        self.assertEqual(u[cle("Neur.on")].get("approved"), "yes")
        for texte in (CAPITAL, ADRESSE, "Notre équipe"):
            self.assertNotEqual(u[cle(texte)].get("approved"), "yes", texte)

    def test_note_contient_pages_et_glossaire(self):
        fichier, _ = self.exporter()
        note = self.unites(fichier)[cle(CAPITAL)].find(NS + "note").text
        self.assertIn("Pages : accueil", note)
        self.assertIn("Statut : adapte", note)
        self.assertIn("Glossaire : capital-actions = Aktienkapital", note)
        autre = self.unites(fichier)[cle(DEMO)].find(NS + "note").text
        self.assertNotIn("Glossaire", autre)
        self.assertIn("Pages : accueil, contact/", autre)

    def test_note_contient_le_contexte_v1(self):
        contexte = {"nature": "morceau", "page_v1": "de/kontakt/", "fr_complet": CAPITAL + ", suite",
                    "trad_complete": "Das Aktienkapital der Gesellschaft, Fortsetzung"}
        self.table.enregistrer()  # crée le dossier de la langue
        (self.langues / "de" / "contextes.json").write_text(json.dumps({cle(CAPITAL): {"fr": CAPITAL, "contexte": contexte}}),
                                                          encoding="utf-8")
        fichier, _ = self.exporter()
        note = self.unites(fichier)[cle(CAPITAL)].find(NS + "note").text
        self.assertIn("Contexte V1 (morceau, de/kontakt/)", note)
        self.assertIn("Fortsetzung", note)
        self.assertNotIn("Contexte V1", self.unites(fichier)[cle(DEMO)].find(NS + "note").text)

    def test_contexte_de_a_traduire_json(self):
        contexte = {"nature": "correction V2", "page_v1": "de/", "fr_complet": "avant", "trad_complete": "vorher"}
        self.table.enregistrer()
        (self.langues / "de" / "a_traduire.json").write_text(
            json.dumps({cle(ADRESSE): {"fr": ADRESSE, "contexte": contexte}}), encoding="utf-8")
        fichier, _ = self.exporter()
        self.assertIn("Contexte V1 (correction V2, de/)", self.unites(fichier)[cle(ADRESSE)].find(NS + "note").text)

    def test_filtre_par_statuts(self):
        fichier, n = self.exporter(statuts=("mt", "adapte"))
        self.assertEqual(set(self.unites(fichier)), {cle(CAPITAL), cle(ADRESSE)})
        self.assertEqual(n, 2)

    def test_filtre_par_pages(self):
        fichier, n = self.exporter(pages=["a-propos/"])
        self.assertEqual(set(self.unites(fichier)), {cle("Notre équipe")})
        fichier, n = self.exporter(pages=["contact/"], nom="contact.xlf")
        self.assertEqual(set(self.unites(fichier)), {f"{cle(CONTACT)}@contact/", cle(DEMO), cle("Neur.on")})
        self.assertIn("Pages : contact/", self.unites(fichier)[cle(DEMO)].find(NS + "note").text)

    def test_variante_de_page_a_son_unite(self):
        fichier, _ = self.exporter()
        u = self.unites(fichier)
        propre = u[f"{cle(CONTACT)}@contact/"]
        self.assertEqual(propre.find(NS + "target").text, "Kontakt aufnehmen")
        self.assertIn("Pages : contact/", propre.find(NS + "note").text)
        self.assertEqual(u[cle(CONTACT)].find(NS + "target").text, "Kontakt")
        self.assertIn("Pages : accueil", u[cle(CONTACT)].find(NS + "note").text)
        self.assertNotIn("contact/", u[cle(CONTACT)].find(NS + "note").text)  # la page a sa propre variante

    def test_segment_sans_page_non_exporte(self):
        self.table.poser("Texte orphelin", "Verwaister Text", "adapte", "test")
        fichier, _ = self.exporter()
        self.assertNotIn(cle("Texte orphelin"), self.unites(fichier))

    def test_pages_nombreuses_abregees(self):
        pages = {f"p{i}/": page(DEMO) for i in range(12)}
        sortie = self.sortie / "beaucoup.xlf"
        E.exporter_xliff("de", self.table, None, {"v1"}, sortie, assemblees=pages, glossaire={})
        note = self.unites(sortie)[cle(DEMO)].find(NS + "note").text
        self.assertIn("Pages : p0/, p1/", note)
        self.assertIn("et 4 autre(s)", note)

    def test_texte_special_echappe(self):
        self.table.poser("Prix & <devis>", "Preis & <Offerte>", "adapte", "test")
        sortie = self.sortie / "esc.xlf"
        E.exporter_xliff("de", self.table, None, {"adapte"}, sortie, glossaire={},
                         assemblees={"": page("Prix &amp; &lt;devis&gt;")})
        self.assertEqual(self.unites(sortie)[cle("Prix & <devis>")].find(NS + "target").text, "Preis & <Offerte>")

    def test_traduction_mal_imbriquee_non_exportee(self):
        self.table.poser(CAPITAL, "Das {1}Aktien{/1}kapital {/1}", "adapte", "test")  # balisage inutilisable en <g>
        fichier, _ = self.exporter()
        u = self.unites(fichier)[cle(CAPITAL)]
        self.assertIsNone(u.find(NS + "target"))
        self.assertIn("mal imbriqué", u.find(NS + "note").text)

    def test_langue_inconnue_refusee(self):
        with self.assertRaises(ValueError):
            E.exporter_xliff("fr", self.table, None, {"v1"}, self.sortie / "x.xlf", assemblees=PAGES, glossaire={})

    def test_termes_presents(self):
        self.assertEqual(controles.termes_presents(CAPITAL, "de", GLOSSAIRE), [("capital-actions", "Aktienkapital")])
        self.assertEqual(controles.termes_presents(CAPITAL, "it", GLOSSAIRE), [])
        self.assertEqual(controles.termes_presents("Le Prix", "it", GLOSSAIRE), [("prix", "prezzo")])


class TestExportTmxEtGlossaire(Base):
    def test_tmx_bien_forme(self):
        sortie = self.sortie / "de.tmx"
        n = E.exporter_tmx("de", self.table, {"v1"}, sortie)
        racine = ET.parse(sortie).getroot()
        self.assertEqual((racine.tag, racine.get("version")), ("tmx", "1.4"))
        en_tete = racine.find("header")
        self.assertEqual((en_tete.get("srclang"), en_tete.get("segtype"), en_tete.get("datatype")),
                         ("fr-CH", "paragraph", "html"))
        tus = racine.find("body").findall("tu")
        self.assertEqual(len(tus), n)
        self.assertEqual(n, 3)  # DEMO, CONTACT, CONTACT de la page contact/ : les seuls v1
        tu = next(t for t in tus if t.get("tuid") == cle(DEMO))
        langues = {v.get(XML_LANG): v.find("seg").text for v in tu.findall("tuv")}
        self.assertEqual(langues, {"fr-CH": DEMO, "de-CH": "Demo anfragen"})

    def test_tmx_marqueurs_en_bpt_ept_ph(self):
        sortie = self.sortie / "de.tmx"
        E.exporter_tmx("de", self.table, {"adapte", "mt"}, sortie)
        tus = {t.get("tuid"): t for t in ET.parse(sortie).getroot().iter("tu")}
        seg = tus[cle(CAPITAL)].findall("tuv")[1].find("seg")
        self.assertEqual(seg.find("bpt").get("i"), "1")
        self.assertEqual(seg.find("ept").get("i"), "1")
        self.assertEqual("".join(tus[cle(ADRESSE)].findall("tuv")[1].find("seg").itertext()), "Adresse{1}Freiburg")
        self.assertEqual(tus[cle(ADRESSE)].findall("tuv")[1].find("seg").find("ph").get("x"), "1")

    def test_csv_bom(self):
        sortie = self.sortie / "glossaire.csv"
        n = E.exporter_glossaire_csv("de", GLOSSAIRE, sortie)
        self.assertEqual(n, 1)  # « prix » n'a qu'un équivalent italien
        brut = sortie.read_bytes()
        self.assertTrue(brut.startswith(b"\xef\xbb\xbf"))
        lignes = list(csv.reader(io.StringIO(brut.decode("utf-8-sig")), delimiter=";"))
        self.assertEqual(lignes, [["fr", "de", "source", "statut"],
                                  ["capital-actions", "Aktienkapital", "Fedlex : CO art. 620", "confirme"]])

    def test_csv_glossaire_vide(self):
        sortie = self.sortie / "vide.csv"
        self.assertEqual(E.exporter_glossaire_csv("en", GLOSSAIRE, sortie), 0)
        self.assertEqual(sortie.read_text(encoding="utf-8-sig").strip(), "fr;en;source;statut")

    def test_aucun_export_dans_le_depot(self):
        dans_le_depot = ICI / "export-refuse-test"
        with self.assertRaises(ValueError) as c:
            E.exporter_xliff("de", self.table, None, {"v1"}, dans_le_depot / "de.xlf", assemblees=PAGES, glossaire={})
        self.assertIn("dépôt", str(c.exception))
        with self.assertRaises(ValueError):
            E.exporter_tmx("de", self.table, {"v1"}, dans_le_depot / "de.tmx")
        with self.assertRaises(ValueError):
            E.exporter_glossaire_csv("de", GLOSSAIRE, dans_le_depot / "g.csv")
        self.assertFalse(dans_le_depot.exists())

    def test_dossier_hors_depot_accepte(self):
        E.verifier_hors_depot(self.tmp / "ailleurs" / "x.xlf")  # aucune exception

    def test_dossier_par_defaut(self):
        with mock.patch.object(E.terminologie, "TERMINOLOGIE", Path("/x/site-v2/terminologie")):
            self.assertEqual(E.dossier_export("de", JOUR), Path("/x/site-v2") / f"{JOUR}-de")
        E.verifier_hors_depot(E.dossier_export("de", JOUR))  # le dossier réel est ignoré par git, ou hors de tout dépôt


class TestCommandes(Base):
    """Commandes exporter et importer de outils/i18n/__main__.py, tables et sorties dans des dossiers temporaires."""

    def lancer(self, *argv):
        sortie = io.StringIO()
        erreur = io.StringIO()
        with contextlib.redirect_stdout(sortie), contextlib.redirect_stderr(erreur), \
                mock.patch.object(build, "DOSSIER_LANGUES", self.langues), \
                mock.patch.object(traduire, "pages_assemblees", lambda langue, mode: PAGES), \
                mock.patch.object(cli.chnell, "charger_glossaire", lambda *a, **k: GLOSSAIRE):
            code = cli.main(list(argv))
        return code, sortie.getvalue(), erreur.getvalue()

    def test_exporter_ecrit_les_trois_fichiers(self):
        self.table.enregistrer()
        code, sortie, _ = self.lancer("exporter", "de", "--sortie", str(self.sortie))
        self.assertEqual(code, 0)
        self.assertEqual(sorted(p.name for p in self.sortie.iterdir()),
                         ["neur-on-de-glossaire.csv", "neur-on-de-v1.tmx", "neur-on-de.xlf"])
        self.assertIn("6 unité(s) XLIFF", sortie)  # sans le segment relu
        ET.parse(self.sortie / "neur-on-de.xlf")

    def test_exporter_refuse_le_depot(self):
        code, _, erreur = self.lancer("exporter", "de", "--sortie", str(ICI / "export-refuse-test"))
        self.assertEqual(code, 1)
        self.assertIn("dépôt", erreur)
        self.assertFalse((ICI / "export-refuse-test").exists())


if __name__ == "__main__":
    unittest.main()
