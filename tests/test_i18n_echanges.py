"""Échanges avec les traducteurs (tâches 5.1 et 5.2) : export XLIFF 1.2, TMX 1.4 et glossaire CSV, réimport des
corrections : outils/i18n/echanges.py.

Tout est synthétique : mini table allemande et mini pages écrites ici, dossiers temporaires pour les fichiers. Aucun test
ne lit ni n'écrit le dossier réel des échanges ni celui de la terminologie (Bibliotheque-Claude, Ruling 5)."""
import contextlib
import csv
import io
import json
import re
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
TIRET_CADRATIN = chr(0x2014)
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

    def confirmer(self, fichier):
        """Le relecteur confirme tous les segments à relire (état translated), comme Trados le ferait."""
        texte = fichier.read_text(encoding="utf-8")
        fichier.write_text(texte.replace('state="needs-review-translation"', 'state="translated"'), encoding="utf-8")

    def importer(self, fichier, relecteur="Alice", glossaire=None, confirme=True, **kw):
        if confirme:
            self.confirmer(fichier)
        kw.setdefault("assemblees", PAGES)  # pages du site au réimport (traduire.pages_union par défaut)
        return E.importer_xliff(fichier, self.table, relecteur, glossaire=GLOSSAIRE if glossaire is None else glossaire,
                                jour=JOUR, **kw)

    def remplacer(self, fichier, ancien, nouveau):
        texte = fichier.read_text(encoding="utf-8")
        self.assertIn(ancien, texte)
        fichier.write_text(texte.replace(ancien, nouveau, 1), encoding="utf-8")


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

    def test_etats_a_l_export(self):  # Ruling 31
        fichier, _ = self.exporter()
        u = self.unites(fichier)
        etat = lambda t: u[cle(t)].find(NS + "target").get("state")
        self.assertEqual((etat(CAPITAL), etat(ADRESSE)), ("needs-review-translation", "needs-review-translation"))
        self.assertEqual((etat(DEMO), etat("Neur.on"), etat("Notre équipe")), ("final", "final", "signed-off"))
        self.assertEqual(u[cle(DEMO)].get("approved"), "yes")
        self.assertIsNone(u[cle(CAPITAL)].get("approved"))

    def test_caractere_interdit_en_xml_refuse(self):
        self.table.poser(DEMO, "Demo\x0b anfragen", "v1", "V1 de/")
        with self.assertRaises(ValueError) as c:
            self.exporter()
        self.assertIn("U+000B", str(c.exception))
        self.assertIn(cle(DEMO), str(c.exception))
        self.assertFalse((self.sortie / "de.xlf").exists())
        with self.assertRaises(ValueError):
            E.exporter_tmx("de", self.table, {"v1"}, self.sortie / "de.tmx")
        self.assertFalse((self.sortie / "de.tmx").exists())

    def test_tabulation_et_saut_de_ligne_acceptes(self):
        self.table.poser(DEMO, "Demo\tanfragen\nbitte", "v1", "V1 de/")
        fichier, _ = self.exporter()
        self.assertEqual(self.unites(fichier)[cle(DEMO)].find(NS + "target").text, "Demo\tanfragen\nbitte")

    def test_sans_traduction(self):
        pages = {"": page(DEMO, "Texte jamais traduit", "Neur.on"), "contact/": page("Texte jamais traduit", "12 345")}
        m = E.sans_traduction("de", self.table, {"", "contact/"}, pages)
        self.assertEqual(m, {cle("Texte jamais traduit"): {"fr": "Texte jamais traduit", "pages": ["", "contact/"]},
                             cle(traduire.LIBELLE_BANDEAU): {"fr": traduire.LIBELLE_BANDEAU, "pages": ["bandeau"]}})
        self.assertEqual(E.sans_traduction("de", self.table, {"contact/"}, pages)[cle("Texte jamais traduit")]["pages"],
                         ["contact/"])
        self.assertIn("Accueil", {x["fr"] for x in E.sans_traduction("de", self.table, None, pages).values()})  # llms

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

    def test_libelle_du_bandeau_toujours_exporte(self):
        """Vague finale, point 8 : le libellé du bandeau de l'aperçu part avec toute sélection de pages (pseudo-page
        « bandeau »), pour être relu dès le premier tour."""
        self.table.poser(traduire.LIBELLE_BANDEAU, "Arbeitsversion, Übersetzung nicht geprüft", "adapte", "test")
        fichier, _ = self.exporter(pages=["a-propos/"])
        u = self.unites(fichier)
        self.assertEqual(set(u), {cle("Notre équipe"), cle(traduire.LIBELLE_BANDEAU)})
        self.assertIn("Pages : bandeau", u[cle(traduire.LIBELLE_BANDEAU)].find(NS + "note").text)

    def test_textes_des_deux_modes_exportes(self):
        """Vague finale, point 1 : {page: {mode: html}} (traduire.pages_union) : un texte de la seule production est
        exporté, une seule unité par texte présent dans les deux modes."""
        self.table.poser("Préférences cookies", "Cookie-Einstellungen", "adapte", "test")
        union = {"": {"apercu": PAGES[""], "production": PAGES[""].replace("</main>", "<p>Préférences cookies</p></main>")}}
        sortie = self.sortie / "union.xlf"
        E.exporter_xliff("de", self.table, None, {"adapte", "v1"}, sortie, assemblees=union, glossaire={})
        u = self.unites(sortie)
        self.assertIn(cle("Préférences cookies"), u)
        self.assertEqual(sum(1 for k in u if k == cle(DEMO)), 1)

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


class TestImportXliff(Base):
    def test_aller_retour_sans_modification(self):
        fichier, n = self.exporter()
        avant = json.loads(json.dumps(self.table.entrees))
        r = self.importer(fichier)
        self.assertEqual(r["rejetes"], [])
        self.assertEqual(r["modifies"], [])
        self.assertEqual(r["relus"], n)
        for k, e in self.table.entrees.items():
            self.assertEqual(e["trad"], avant[k]["trad"])
            self.assertIn(e["statut"], ("relu", "invariant"), e["fr"])
            for p in e["par_page"].values():
                self.assertEqual(p["statut"], "relu")
        self.assertEqual(self.table.entrees[cle(DEMO)]["statut"], "relu")
        self.assertEqual(self.table.entrees[cle(DEMO)]["source"], f"V1 de/ ; relu par Alice le {JOUR}")

    def test_mt_adapte_intacts_comptes_a_part(self):
        fichier, _ = self.exporter()
        self.remplacer(fichier, "Das <g id=\"1\">Aktienkapital</g> der Gesellschaft", "Das <g id=\"1\">Grundkapital</g> der Gesellschaft")
        r = self.importer(fichier)
        self.assertEqual(r["mt_adapte_intacts"], 1)  # ADRESSE (mt) ; CAPITAL (adapte) a été modifié
        self.assertEqual(len(r["modifies"]), 1)

    def test_sans_etat_ni_approved_non_confirme(self):  # Ruling 31
        fichier, n = self.exporter()
        r = self.importer(fichier, confirme=False)
        self.assertEqual(sorted(x["cle"] for x in r["non_confirmes"]), sorted([cle(CAPITAL), cle(ADRESSE)]))
        self.assertEqual({x["raison"] for x in r["non_confirmes"]}, {"non confirmé par le relecteur"})
        self.assertEqual(r["relus"], n - 2)
        self.assertEqual(r["rejetes"], [])
        for texte, statut in ((CAPITAL, "adapte"), (ADRESSE, "mt")):
            e = self.table.entrees[cle(texte)]
            self.assertEqual((e["statut"], e["source"].endswith("Alice le " + JOUR)), (statut, False), texte)
        self.assertEqual(self.table.entrees[cle(DEMO)]["statut"], "relu")  # approved="yes" à l'export

    def test_non_confirme_modifie_non_applique(self):
        fichier, _ = self.exporter()
        self.remplacer(fichier, "Adresse<x id=\"1\"/>Freiburg", "Adresse<x id=\"1\"/>Zürich")
        r = self.importer(fichier, confirme=False)
        non = next(x for x in r["non_confirmes"] if x["cle"] == cle(ADRESSE))
        self.assertTrue(non["modifie"])
        self.assertEqual(self.table.entrees[cle(ADRESSE)]["trad"], "Adresse{1}Freiburg")
        self.assertEqual(r["modifies"], [])

    def test_state_translated_vaut_confirmation(self):
        fichier, _ = self.exporter()
        self.remplacer(fichier, 'state="needs-review-translation">Adresse', 'state="translated">Adresse')
        r = self.importer(fichier, confirme=False)
        self.assertEqual([x["cle"] for x in r["non_confirmes"]], [cle(CAPITAL)])
        self.assertEqual(self.table.entrees[cle(ADRESSE)]["statut"], "relu")
        self.assertEqual(self.table.entrees[cle(CAPITAL)]["statut"], "adapte")

    def test_approved_vaut_confirmation(self):
        fichier, _ = self.exporter()
        self.remplacer(fichier, f'<trans-unit id="{cle(CAPITAL)}"', f'<trans-unit id="{cle(CAPITAL)}" approved="yes"')
        r = self.importer(fichier, confirme=False)
        self.assertEqual([x["cle"] for x in r["non_confirmes"]], [cle(ADRESSE)])
        self.assertEqual(self.table.entrees[cle(CAPITAL)]["statut"], "relu")

    def test_etat_new_ou_needs_review_non_confirme(self):
        fichier, _ = self.exporter()
        self.remplacer(fichier, 'state="needs-review-translation">Das', 'state="needs-review-l10n">Das')
        self.remplacer(fichier, 'state="needs-review-translation">Adresse', 'state="new">Adresse')
        r = self.importer(fichier, confirme=False)
        self.assertEqual(len(r["non_confirmes"]), 2)

    def test_sans_etat_option_explicite(self):
        fichier, n = self.exporter()
        r = self.importer(fichier, confirme=False, sans_etat=True)
        self.assertEqual((r["non_confirmes"], r["relus"]), ([], n))
        self.assertEqual(self.table.entrees[cle(CAPITAL)]["statut"], "relu")

    def test_aller_retour_sans_effet_de_bord_sur_les_fr(self):
        fichier, _ = self.exporter()
        avant = {k: e["fr"] for k, e in self.table.entrees.items()}
        self.importer(fichier)
        self.assertEqual({k: e["fr"] for k, e in self.table.entrees.items()}, avant)

    def test_correction_appliquee(self):
        fichier, _ = self.exporter()
        self.remplacer(fichier, "Demo anfragen", "Demo vereinbaren")
        r = self.importer(fichier)
        self.assertEqual(r["rejetes"], [])
        self.assertEqual(len(r["modifies"]), 1)
        m = r["modifies"][0]
        self.assertEqual((m["cle"], m["avant"], m["apres"]), (cle(DEMO), "Demo anfragen", "Demo vereinbaren"))
        self.assertEqual(m["pages"], ["accueil", "contact/"])
        e = self.table.entrees[cle(DEMO)]
        self.assertEqual((e["trad"], e["statut"]), ("Demo vereinbaren", "relu"))
        self.assertTrue(e["source"].endswith(f" ; relu par Alice le {JOUR}"))

    def test_correction_avec_balises(self):
        fichier, _ = self.exporter()
        self.remplacer(fichier, "Aktienkapital</g> der", "Grundkapital</g> der")
        r = self.importer(fichier)
        self.assertEqual(r["rejetes"], [])
        self.assertEqual(self.table.entrees[cle(CAPITAL)]["trad"], "Das {1}Grundkapital{/1} der Gesellschaft")
        self.assertEqual(r["modifies"][0]["apres"], "Das {1}Grundkapital{/1} der Gesellschaft")

    def test_variante_de_page_corrigee(self):
        fichier, _ = self.exporter()
        self.remplacer(fichier, "Kontakt aufnehmen", "Kontakt herstellen")
        r = self.importer(fichier)
        self.assertEqual(r["modifies"][0]["pages"], ["contact/"])
        e = self.table.entrees[cle(CONTACT)]
        self.assertEqual(e["trad"], "Kontakt")
        self.assertEqual(e["par_page"]["contact/"]["trad"], "Kontakt herstellen")
        self.assertEqual(e["par_page"]["contact/"]["statut"], "relu")

    def test_marqueur_supprime_rejete(self):
        fichier, _ = self.exporter()
        self.remplacer(fichier, 'Das <g id="1">Aktienkapital</g>', "Das Aktienkapital")
        r = self.importer(fichier)
        self.assertEqual([(x["cle"], x["raison"]) for x in r["rejetes"]], [(cle(CAPITAL), "balisage")])
        e = self.table.entrees[cle(CAPITAL)]  # traduction précédente et statut conservés
        self.assertEqual((e["trad"], e["statut"]), ("Das {1}Aktienkapital{/1} der Gesellschaft", "adapte"))
        self.assertEqual(r["modifies"], [])

    def test_marqueur_seul_supprime_rejete(self):
        fichier, _ = self.exporter()
        self.remplacer(fichier, 'Adresse<x id="1"/>Freiburg', "Adresse Freiburg")
        r = self.importer(fichier)
        self.assertEqual([(x["cle"], x["raison"]) for x in r["rejetes"]], [(cle(ADRESSE), "balisage")])
        self.assertEqual(self.table.entrees[cle(ADRESSE)]["trad"], "Adresse{1}Freiburg")
        self.assertEqual(self.table.entrees[cle(ADRESSE)]["statut"], "mt")

    def test_marqueur_ajoute_rejete(self):
        fichier, _ = self.exporter()
        self.remplacer(fichier, "Kontakt aufnehmen", 'Kontakt <x id="2"/>aufnehmen')
        r = self.importer(fichier)
        self.assertEqual([x["raison"] for x in r["rejetes"]], ["balisage"])
        self.assertEqual(self.table.entrees[cle(CONTACT)]["par_page"]["contact/"]["trad"], "Kontakt aufnehmen")

    def test_marqueur_double_rejete(self):
        fichier, _ = self.exporter()
        self.remplacer(fichier, 'Das <g id="1">Aktienkapital</g> der', 'Das <g id="1">Aktienkapital</g> <g id="1">der</g>')
        self.assertEqual([x["raison"] for x in self.importer(fichier)["rejetes"]], ["balisage"])

    def test_marqueur_inverse_rejete_par_csv(self):
        csv_ = self.csv("{/1}Aktienkapital{1}")
        r = E.importer_csv(csv_, self.table, "Alice", glossaire={}, jour=JOUR, assemblees=PAGES)
        self.assertEqual([(x["cle"], x["raison"]) for x in r["rejetes"]], [(cle(CAPITAL), "balisage")])

    def test_balise_inconnue_rejetee(self):
        fichier, _ = self.exporter()
        self.remplacer(fichier, "Demo anfragen", "Demo <ph id=\"9\">x</ph>anfragen")
        r = self.importer(fichier)
        self.assertEqual([x["raison"] for x in r["rejetes"]], ["balisage"])
        self.assertEqual(self.table.entrees[cle(DEMO)]["trad"], "Demo anfragen")

    def test_mrk_de_segmentation_ignore(self):
        fichier, _ = self.exporter()
        self.remplacer(fichier, "Demo anfragen", 'Demo <mrk mtype="seg" mid="1">vereinbaren</mrk>')
        r = self.importer(fichier)
        self.assertEqual(r["rejetes"], [])
        self.assertEqual(self.table.entrees[cle(DEMO)]["trad"], "Demo vereinbaren")

    def test_segment_inconnu_rejete(self):
        fichier, _ = self.exporter()
        self.remplacer(fichier, f'id="{cle(DEMO)}"', 'id="0000000000000000"')
        r = self.importer(fichier)
        self.assertEqual([(x["cle"], x["raison"]) for x in r["rejetes"]], [("0000000000000000", "segment inconnu")])
        self.assertNotIn("0000000000000000", self.table.entrees)
        self.assertEqual(self.table.entrees[cle(DEMO)]["statut"], "v1")  # son unité manque : rien n'y touche

    def test_variante_de_page_inconnue_rejetee(self):
        fichier, _ = self.exporter()
        self.remplacer(fichier, f'id="{cle(CONTACT)}@contact/"', f'id="{cle(CONTACT)}@autre/"')
        r = self.importer(fichier)
        self.assertEqual([x["raison"] for x in r["rejetes"]], ["segment inconnu"])

    def test_tiret_long_rejete(self):
        fichier, _ = self.exporter()
        self.remplacer(fichier, "Demo anfragen", f"Demo {TIRET_CADRATIN} anfragen")
        r = self.importer(fichier)
        self.assertEqual([(x["cle"], x["raison"]) for x in r["rejetes"]], [(cle(DEMO), "tirets")])
        e = self.table.entrees[cle(DEMO)]
        self.assertEqual((e["trad"], e["statut"]), ("Demo anfragen", "v1"))

    def test_eszett_rejete_en_allemand(self):
        fichier, _ = self.exporter()
        self.remplacer(fichier, "Unser Team", "Unser Team, groß")
        r = self.importer(fichier)
        self.assertEqual([x["raison"] for x in r["rejetes"]], ["eszett"])
        self.assertEqual(self.table.entrees[cle("Notre équipe")]["trad"], "Unser Team")

    def test_marque_modifiee_rejetee(self):
        fichier, _ = self.exporter()
        self.remplacer(fichier, "Demo anfragen", "Demo anfragen bei Corrext")
        self.assertEqual([x["raison"] for x in self.importer(fichier)["rejetes"]], ["marques"])

    def test_terme_interdit_rejete(self):
        fichier, _ = self.exporter()
        self.remplacer(fichier, "Unser Team", "Unser Lexa Team")
        self.assertEqual([x["raison"] for x in self.importer(fichier)["rejetes"]], ["interdits"])

    def test_milliers_a_l_espace_rejetes(self):
        """Ruling 35 : « 20 000 » rejeté dès la relecture en allemand (XLIFF et CSV), bloquant comme en production."""
        fichier, _ = self.exporter()
        self.remplacer(fichier, "Unser Team", "Unser Team von 20 000 Fachleuten")
        self.assertEqual([x["raison"] for x in self.importer(fichier)["rejetes"]], ["milliers"])
        self.assertEqual(self.table.entrees[cle("Notre équipe")]["trad"], "Unser Team")
        f = self.tmp / "c.csv"
        f.write_text(f'cle;fr;trad\n{cle(DEMO)};{DEMO};"Demo für 15 000 Seiten"\n', encoding="utf-8-sig")
        r = E.importer_csv(f, self.table, "Alice", glossaire={}, jour=JOUR, assemblees=PAGES)
        self.assertEqual([x["raison"] for x in r["rejetes"]], ["milliers"])

    def test_traduction_vide_rejetee(self):
        fichier, _ = self.exporter()
        self.remplacer(fichier, "Demo anfragen", "")
        r = self.importer(fichier)
        self.assertEqual([(x["cle"], x["raison"]) for x in r["rejetes"]], [(cle(DEMO), "traduction vide")])
        self.assertEqual(self.table.entrees[cle(DEMO)]["trad"], "Demo anfragen")

    def test_texte_fr_change_sur_le_site_depuis_l_export(self):
        """Vague finale, point 2 : le texte FR change dans la page après l'export (sa clé change avec lui). L'unité rendue
        est rejetée, jamais posée sur l'ancienne entrée ; sa traduction devient le contexte du texte qui l'a remplacé."""
        fichier, _ = self.exporter()
        self.remplacer(fichier, "Demo anfragen", "Demo vereinbaren")
        nouveau = "Demander une démo gratuite"
        pages = {p: h.replace(f"<p>{DEMO}</p>", f"<p>{nouveau}</p>") for p, h in PAGES.items()}
        r = self.importer(fichier, assemblees=pages)
        self.assertEqual([(x["cle"], x["raison"]) for x in r["rejetes"]], [(cle(DEMO), E.PLUS_PRESENT)])
        e = self.table.entrees[cle(DEMO)]
        self.assertEqual((e["trad"], e["statut"]), ("Demo anfragen", "v1"))
        self.assertNotIn(cle(nouveau), self.table.entrees)
        [o] = r["reorientes"]
        self.assertEqual((o["nouvelle_cle"], o["fr"], o["fr_avant"], o["trad"]), (cle(nouveau), nouveau, DEMO, "Demo vereinbaren"))
        contextes = E.contextes_reorientes({}, r)
        self.assertEqual(contextes[cle(nouveau)]["contexte"]["nature"], E.NATURE_RELECTURE)
        self.assertEqual(contextes[cle(nouveau)]["contexte"]["trad_complete"], "Demo vereinbaren")
        # repris dans a_traduire.json (etat), donc dans le lot d'adaptation et la note de l'export suivant
        a_traduire = traduire.fichier_a_traduire({cle(nouveau): nouveau}, contextes)
        self.assertEqual(a_traduire[cle(nouveau)]["contexte"]["fr_complet"], DEMO)
        self.assertIn("Version précédente relue", E._ligne_contexte(contextes[cle(nouveau)]["contexte"]))

    def test_texte_fr_disparu_sans_remplacant(self):
        fichier, _ = self.exporter()
        pages = {p: h.replace(f"<p>{DEMO}</p>", "") for p, h in PAGES.items()}
        r = self.importer(fichier, assemblees=pages)
        [rejet] = r["rejetes"]
        self.assertEqual((rejet["cle"], rejet["raison"]), (cle(DEMO), E.PLUS_PRESENT))
        self.assertIn("Demo anfragen", rejet["detail"])  # la traduction rendue reste dans le rapport
        self.assertEqual(r["reorientes"], [])

    def test_contextes_de_relecture_gardes_par_la_memoire(self):
        relecture = {"fr": "x", "contexte": {"nature": E.NATURE_RELECTURE, "fr_complet": "y", "trad_complete": "z"}}
        v1 = {"fr": "a", "contexte": {"nature": "morceau"}}
        self.assertEqual(E.garder_contextes_relecture({"k1": relecture, "k2": v1}, {"k3": v1}), {"k1": relecture, "k3": v1})
        self.assertEqual(E.garder_contextes_relecture({"k1": relecture}, {"k1": v1}), {"k1": v1})  # la V1 l'emporte

    def test_unites_exportees_absentes_du_fichier_rendu(self):
        """Vague finale, point 15 : le rapport liste les unités de l'export que le fichier rendu a perdues."""
        fichier, _ = self.exporter()
        rendu = self.sortie / "rendu.xlf"
        racine = ET.parse(fichier).getroot()
        corps = racine.find(f"{NS}file/{NS}body")
        corps.remove(next(u for u in corps if u.get("id") == cle(CAPITAL)))
        ET.register_namespace("", NS[1:-1])
        ET.ElementTree(racine).write(rendu, encoding="UTF-8", xml_declaration=True)
        r = self.importer(rendu, export=fichier)
        self.assertEqual(r["absents"], [{"cle": cle(CAPITAL), "fr": CAPITAL}])
        self.assertIsNone(self.importer(rendu)["absents"])  # sans export d'origine : non contrôlé

    def test_v1_intacts_comptes_a_part(self):
        """Vague finale, point 15 : les traductions V1 confirmées sans modification ont leur compteur (provenance)."""
        fichier, n = self.exporter()
        self.remplacer(fichier, "Demo anfragen", "Demo vereinbaren")
        r = self.importer(fichier)
        # v1 intacts : Kontakt (défaut) et Kontakt aufnehmen (contact/) ; Demo anfragen a été modifiée
        self.assertEqual(r["v1_intacts"], 2)
        self.assertEqual(r["relus"], n)

    def test_source_modifiee_dans_le_fichier(self):
        fichier, _ = self.exporter()
        self.remplacer(fichier, f">{DEMO}</source>", ">Demander une autre démo</source>")
        r = self.importer(fichier)
        self.assertEqual([x["raison"] for x in r["rejetes"]], ["segment FR modifié depuis l'export"])

    def test_identique_au_francais_pose_invariant(self):  # Ruling 18
        self.table.poser("Corrext Premium ouvert", "Corrext Premium offen", "adapte", "test")
        self.table.poser("Prix catalogue", "Listenpreis", "adapte", "test")
        pages = {"": page("Corrext Premium ouvert", "Prix catalogue")}
        sortie = self.sortie / "ident.xlf"
        E.exporter_xliff("de", self.table, None, {"adapte"}, sortie, assemblees=pages, glossaire={})
        self.remplacer(sortie, "Corrext Premium offen", "Corrext Premium ouvert")
        r = self.importer(sortie, glossaire={}, assemblees=pages)
        self.assertEqual(r["rejetes"], [])
        e = self.table.entrees[cle("Corrext Premium ouvert")]
        self.assertEqual((e["statut"], e["trad"]), ("invariant", "Corrext Premium ouvert"))
        self.assertEqual(e["source"], f"relu par Alice le {JOUR}, identique au français")
        self.assertEqual(self.table.entrees[cle("Prix catalogue")]["statut"], "relu")
        self.assertEqual(r["relus"], 2)
        self.assertEqual(r["invariants"], 1)
        self.assertEqual([m["cle"] for m in r["modifies"]], [cle("Corrext Premium ouvert")])

    def test_identique_au_francais_apres_les_controles_bloquants(self):
        # le contrôle bloquant s'applique avant la pose invariant : un texte français qui porte un terme interdit
        self.table.poser("Notre ancien hébergeur Exoscale", "Unser früherer Hoster Exoscale", "adapte", "test")
        sortie = self.sortie / "ident2.xlf"
        E.exporter_xliff("de", self.table, None, {"adapte"}, sortie, glossaire={},
                         assemblees={"": page("Notre ancien hébergeur Exoscale")})
        self.remplacer(sortie, "Unser früherer Hoster Exoscale", "Notre ancien hébergeur Exoscale")
        r = self.importer(sortie, glossaire={}, assemblees={"": page("Notre ancien hébergeur Exoscale")})
        self.assertEqual([x["raison"] for x in r["rejetes"]], ["interdits"])
        self.assertEqual(self.table.entrees[cle("Notre ancien hébergeur Exoscale")]["statut"], "adapte")

    def test_v1_sans_modification_non_controlee(self):
        # une traduction V1 validée dont la marque diffère du français (« Corrext » en plus) revient intacte : acceptée
        self.table.poser("Exemple de prix", "Beispiel Corrext Preis", "v1", "V1 de/")
        pages = {"": page("Exemple de prix")}
        sortie = self.sortie / "v1.xlf"
        E.exporter_xliff("de", self.table, [""], {"v1"}, sortie, assemblees=pages, glossaire={})
        r = self.importer(sortie, glossaire={}, assemblees=pages)
        self.assertEqual((r["rejetes"], r["modifies"], r["relus"]), ([], [], 1))
        self.assertEqual(self.table.entrees[cle("Exemple de prix")]["statut"], "relu")
        # mais dès que le relecteur la modifie, les contrôles bloquants s'appliquent
        self.table.poser("Exemple de prix", "Beispiel Corrext Preis", "v1", "V1 de/")
        self.remplacer(sortie, "Beispiel Corrext Preis", "Beispiel Corrext Preise")
        r = self.importer(sortie, glossaire={}, assemblees=pages)
        self.assertEqual([x["raison"] for x in r["rejetes"]], ["marques"])
        self.assertEqual(self.table.entrees[cle("Exemple de prix")]["trad"], "Beispiel Corrext Preis")
        self.assertEqual(self.table.entrees[cle("Exemple de prix")]["statut"], "v1")

    def test_adapte_sans_modification_controle(self):
        self.table.poser("Exemple de prix", "Beispiel Corrext Preis", "adapte", "test")
        pages = {"": page("Exemple de prix")}
        sortie = self.sortie / "adapte.xlf"
        E.exporter_xliff("de", self.table, [""], {"adapte"}, sortie, assemblees=pages, glossaire={})
        r = self.importer(sortie, glossaire={}, assemblees=pages)
        self.assertEqual([x["raison"] for x in r["rejetes"]], ["marques"])
        self.assertEqual(self.table.entrees[cle("Exemple de prix")]["statut"], "adapte")

    def poser_v1_avec_marque_en_trop(self):
        self.table.poser("Exemple de prix", "Beispiel Corrext Preis", "v1", "V1 de/")  # Ruling 30
        self.table.poser(CONTACT, "Kontakt Corrext", "v1", "V1 de/", page="contact/")

    def bloquants(self):
        _, problemes = controles.controler_traductions("de", self.table.entrees, {})
        return [p for p in problemes if p["gravite"] == "bloquant"]

    def test_import_intact_puis_controler_zero_bloquant(self):  # Ruling 30
        self.poser_v1_avec_marque_en_trop()
        pages = {**PAGES, "prix/": page("Exemple de prix")}
        sortie = self.sortie / "intact.xlf"
        E.exporter_xliff("de", self.table, None, {"mt", "adapte", "v1", "invariant"}, sortie, assemblees=pages, glossaire={})
        self.assertEqual(self.bloquants(), [])
        r = self.importer(sortie, glossaire={}, assemblees=pages)
        self.assertEqual(r["rejetes"], [])
        e = self.table.entrees[cle("Exemple de prix")]
        self.assertEqual((e["statut"], e["v1"]), ("relu", True))
        self.assertTrue(self.table.entrees[cle(CONTACT)]["par_page"]["contact/"]["v1"])
        self.assertEqual(self.bloquants(), [])  # la provenance V1 garde l'exemption après le passage à relu
        self.table.enregistrer()  # et le champ survit à l'écriture
        self.assertEqual(Table("de", self.langues).entrees[cle("Exemple de prix")]["v1"], True)

    def test_v1_relu_reste_reimportable_a_l_identique(self):
        self.poser_v1_avec_marque_en_trop()
        sortie = self.sortie / "deux.xlf"
        E.exporter_xliff("de", self.table, None, {"v1"}, sortie, assemblees={**PAGES, "prix/": page("Exemple de prix")},
                         glossaire={})
        pages = {**PAGES, "prix/": page("Exemple de prix")}
        self.importer(sortie, glossaire={}, assemblees=pages)
        sortie2 = self.sortie / "trois.xlf"
        E.exporter_xliff("de", self.table, None, {"relu"}, sortie2, assemblees=pages, glossaire={})
        r = self.importer(sortie2, glossaire={}, assemblees=pages)
        self.assertEqual(r["rejetes"], [])
        self.assertTrue(self.table.entrees[cle("Exemple de prix")]["v1"])

    def test_modification_retire_l_exemption(self):
        self.poser_v1_avec_marque_en_trop()
        sortie = self.sortie / "modif.xlf"
        pages = {**PAGES, "prix/": page("Exemple de prix")}
        E.exporter_xliff("de", self.table, None, {"v1"}, sortie, assemblees=pages, glossaire={})
        self.importer(sortie, glossaire={}, assemblees=pages)
        sortie2 = self.sortie / "modif2.xlf"
        E.exporter_xliff("de", self.table, None, {"relu"}, sortie2, assemblees=pages, glossaire={})
        self.remplacer(sortie2, "Beispiel Corrext Preis", "Beispiel Corrext Preise")  # modifié : contrôles bloquants
        r = self.importer(sortie2, glossaire={}, assemblees=pages)
        self.assertIn(("marques", cle("Exemple de prix")), [(x["raison"], x["cle"]) for x in r["rejetes"]])
        self.assertEqual(self.table.entrees[cle("Exemple de prix")]["trad"], "Beispiel Corrext Preis")
        # une modification acceptée (sans le défaut) fait disparaître le champ
        self.remplacer(sortie2, "Beispiel Corrext Preise", "Beispiel Preis")
        self.importer(sortie2, glossaire={}, assemblees=pages)
        e = self.table.entrees[cle("Exemple de prix")]
        self.assertEqual((e["trad"], e["statut"], "v1" in e), ("Beispiel Preis", "relu", False))

    def test_controler_traductions_respecte_le_champ_v1(self):
        entrees = {cle("Exemple de prix"): {"fr": "Exemple de prix", "trad": "Beispiel Corrext Preis", "statut": "relu",
                                            "source": "x", "v1": True, "par_page": {}}}
        self.assertEqual(controles.controler_traductions("de", entrees, {}), (0, []))
        del entrees[cle("Exemple de prix")]["v1"]
        controlees, problemes = controles.controler_traductions("de", entrees, {})
        self.assertEqual((controlees, [p["regle"] for p in problemes]), (1, ["marques"]))

    def test_terminologie_en_avertissement(self):
        fichier, _ = self.exporter()
        self.remplacer(fichier, "Aktienkapital</g> der", "Kapital</g> der")
        r = self.importer(fichier)
        self.assertEqual(r["rejetes"], [])  # avertissement, pas un rejet
        self.assertEqual(self.table.entrees[cle(CAPITAL)]["statut"], "relu")
        self.assertEqual(len(r["avertissements"]), 1)
        self.assertEqual(r["avertissements"][0]["cle"], cle(CAPITAL))
        self.assertIn("capital-actions", r["avertissements"][0]["detail"])

    def test_doublon_rejete(self):
        fichier, _ = self.exporter()
        texte = fichier.read_text(encoding="utf-8")
        bloc = re.search(r'<trans-unit id="%s".*?</trans-unit>' % cle("Notre équipe"), texte, re.S).group(0)
        fichier.write_text(texte.replace(bloc, bloc + "\n" + bloc), encoding="utf-8")
        r = self.importer(fichier)
        self.assertEqual([x["raison"] for x in r["rejetes"]], ["doublon"])

    def test_fichier_d_une_autre_langue_refuse(self):
        fichier, _ = self.exporter()
        self.remplacer(fichier, 'target-language="de-CH"', 'target-language="it-CH"')
        avant = json.dumps(self.table.entrees, sort_keys=True)
        with self.assertRaises(ValueError) as c:
            self.importer(fichier)
        self.assertIn("it-CH", str(c.exception))
        self.assertEqual(json.dumps(self.table.entrees, sort_keys=True), avant)

    def test_fichier_illisible_refuse(self):
        fichier = self.tmp / "casse.xlf"
        fichier.write_text("<xliff><file>", encoding="utf-8")
        with self.assertRaises(ValueError):
            self.importer(fichier)

    def test_deux_importations_ne_doublent_pas_la_source(self):
        fichier, _ = self.exporter()
        self.importer(fichier)
        self.importer(fichier)
        self.assertEqual(self.table.entrees[cle(DEMO)]["source"], f"V1 de/ ; relu par Alice le {JOUR}")

    def test_table_non_ecrite_par_l_import(self):
        fichier, _ = self.exporter()
        self.table.enregistrer()
        avant = self.table.fichier.read_text(encoding="utf-8")
        self.importer(fichier)
        self.assertEqual(self.table.fichier.read_text(encoding="utf-8"), avant)  # enregistrer() reste à l'appelant

    def csv(self, trad_capital):
        f = self.tmp / "corrections.csv"
        f.write_text("cle;fr;trad\n" + f'{cle(CAPITAL)};"{CAPITAL}";"{trad_capital}"\n', encoding="utf-8-sig")
        return f


class TestImportCsv(Base):
    def ecrire(self, lignes, entete="cle;fr;trad"):
        f = self.tmp / "corrections.csv"
        with open(f, "w", encoding="utf-8-sig", newline="") as sortie:
            sortie.write(entete + "\n")
            csv.writer(sortie, delimiter=";").writerows(lignes)
        return f

    def importer_csv(self, f, **kw):
        kw.setdefault("assemblees", PAGES)
        return E.importer_csv(f, self.table, "Alice", glossaire=kw.pop("glossaire", {}), jour=JOUR, **kw)

    def test_correction_appliquee(self):
        f = self.ecrire([[cle(DEMO), DEMO, "Demo vereinbaren"], [cle(CONTACT), CONTACT, "Kontakt"]])
        r = self.importer_csv(f)
        self.assertEqual(r["rejetes"], [])
        self.assertEqual(r["relus"], 2)
        self.assertEqual([(m["avant"], m["apres"]) for m in r["modifies"]], [("Demo anfragen", "Demo vereinbaren")])
        self.assertEqual(self.table.entrees[cle(DEMO)]["statut"], "relu")

    def test_rejets(self):
        f = self.ecrire([["0000000000000000", "x", "y"], [cle(DEMO), "Autre texte", "Demo"], [cle(CONTACT), CONTACT, ""],
                         [cle(CAPITAL), CAPITAL, "Das Aktienkapital"], [cle("Notre équipe"), "Notre équipe", "Équipe " + TIRET_CADRATIN]])
        r = self.importer_csv(f)
        self.assertEqual([x["raison"] for x in r["rejetes"]],
                         ["segment inconnu", "segment FR modifié depuis l'export", "traduction vide", "balisage", "tirets"])
        self.assertEqual(r["relus"], 0)

    def test_variante_de_page(self):
        f = self.ecrire([[f"{cle(CONTACT)}@contact/", CONTACT, "Kontaktieren Sie uns"]])
        r = self.importer_csv(f)
        self.assertEqual(self.table.entrees[cle(CONTACT)]["par_page"]["contact/"]["trad"], "Kontaktieren Sie uns")
        self.assertEqual(r["modifies"][0]["pages"], ["contact/"])

    def test_colonnes_obligatoires(self):
        f = self.ecrire([], entete="id;texte")
        with self.assertRaises(ValueError):
            self.importer_csv(f)


class TestPreparer(Base):
    """Vague finale, point 7 (Ruling 32) : lot d'adaptation {cle, fr, mt, contexte_v1, glossaire} hors du dépôt."""

    def a_traduire(self):
        contexte = {"nature": "morceau", "page_v1": "de/", "fr_complet": "Le capital-actions de la société anonyme",
                    "trad_complete": "Das Aktienkapital der Aktiengesellschaft"}
        return {cle(CAPITAL): {"fr": CAPITAL, "contexte": contexte}, cle(ADRESSE): {"fr": ADRESSE},
                cle("Texte neuf"): {"fr": "Texte neuf"}}, contexte

    def test_lot(self):
        self.table.poser(CAPITAL, "Das {1}Aktienkapital{/1} der Firma", "mt", "LexMachina")
        a_traduire, contexte = self.a_traduire()
        lot, sans_mt = E.preparer_lot(self.table, a_traduire, {}, GLOSSAIRE)
        self.assertEqual([x["cle"] for x in lot], sorted([cle(CAPITAL), cle(ADRESSE)]))
        capital = next(x for x in lot if x["cle"] == cle(CAPITAL))
        self.assertEqual(capital, {"cle": cle(CAPITAL), "fr": CAPITAL, "mt": "Das {1}Aktienkapital{/1} der Firma",
                                   "contexte_v1": contexte, "glossaire": [{"fr": "capital-actions", "terme": "Aktienkapital"}]})
        self.assertEqual(next(x for x in lot if x["cle"] == cle(ADRESSE))["contexte_v1"], None)
        self.assertEqual(sans_mt, {cle("Texte neuf"): "Texte neuf"})
        # contextes.json l'emporte ; des textes relevés à l'instant (--pages) remplacent a_traduire.json
        autre = {"nature": "variante de balisage"}
        lot, _ = E.preparer_lot(self.table, a_traduire, {cle(CAPITAL): {"fr": CAPITAL, "contexte": autre}}, GLOSSAIRE,
                                textes={cle(CAPITAL): CAPITAL})
        self.assertEqual([(x["cle"], x["contexte_v1"]) for x in lot], [(cle(CAPITAL), autre)])

    def test_commande_hors_depot(self):
        self.table.poser(CAPITAL, "Das {1}Aktienkapital{/1} der Firma", "mt", "LexMachina")
        self.table.enregistrer()
        a_traduire, _ = self.a_traduire()
        (self.langues / "de" / "a_traduire.json").write_text(json.dumps(a_traduire), encoding="utf-8")
        sortie = io.StringIO()
        with contextlib.redirect_stdout(sortie), mock.patch.object(build, "DOSSIER_LANGUES", self.langues), \
                mock.patch.object(cli.chnell, "charger_glossaire", lambda *a, **k: GLOSSAIRE):
            self.assertEqual(cli.main(["preparer", "de", "--sortie", str(self.sortie / "lot")]), 0)
            lot = json.loads((self.sortie / "lot" / "lot-de.json").read_text(encoding="utf-8"))
            self.assertEqual([x["cle"] for x in lot], sorted([cle(CAPITAL), cle(ADRESSE)]))
            self.assertIn("1 texte(s) sans sortie brute", sortie.getvalue())
            with contextlib.redirect_stderr(io.StringIO()) as erreur:
                self.assertEqual(cli.main(["preparer", "de", "--sortie", str(ICI / "lot-refuse-test")]), 1)
            self.assertIn("dépôt", erreur.getvalue())
        self.assertFalse((ICI / "lot-refuse-test").exists())


class TestCommandes(Base):
    """Commandes exporter et importer de outils/i18n/__main__.py, tables et sorties dans des dossiers temporaires."""

    def lancer(self, *argv, pages=PAGES):
        sortie = io.StringIO()
        erreur = io.StringIO()
        with contextlib.redirect_stdout(sortie), contextlib.redirect_stderr(erreur), \
                mock.patch.object(build, "DOSSIER_LANGUES", self.langues), \
                mock.patch.object(traduire, "pages_assemblees", lambda langue, mode: pages), \
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

    def test_exporter_dit_les_textes_sans_traduction(self):
        self.table.enregistrer()
        pages = {**PAGES, "nouveau/": page("Texte jamais traduit", "Autre texte neuf")}
        with mock.patch.object(traduire, "pages_assemblees", lambda langue, mode: pages):
            sortie = io.StringIO()
            with contextlib.redirect_stdout(sortie), mock.patch.object(build, "DOSSIER_LANGUES", self.langues), \
                    mock.patch.object(cli.chnell, "charger_glossaire", lambda *a, **k: GLOSSAIRE):
                code = cli.main(["exporter", "de", "--pages", "nouveau/", "--sortie", str(self.sortie)])
        self.assertEqual(code, 0)
        # le libellé du bandeau de l'aperçu, absent de la table, est toujours compté (vague finale, point 8)
        self.assertIn("3 texte(s) sans traduction, non exportés, sur 2 page(s) : nouveau/ (2), bandeau (1)", sortie.getvalue())

    def test_exporter_refuse_le_depot(self):
        code, _, erreur = self.lancer("exporter", "de", "--sortie", str(ICI / "export-refuse-test"))
        self.assertEqual(code, 1)
        self.assertIn("dépôt", erreur)
        self.assertEqual(erreur.lower().count("refusé"), 1)  # pas de « export refusé : export refusé »
        self.assertFalse((ICI / "export-refuse-test").exists())

    def test_importer_ecrit_la_table_et_le_rapport(self):
        self.table.enregistrer()
        fichier, _ = self.exporter()
        self.remplacer(fichier, "Demo anfragen", "Demo vereinbaren")
        code, sortie, _ = self.lancer("importer", "de", str(fichier), "--relecteur", "Alice Müller",
                                      "--sortie", str(self.sortie))
        self.assertEqual(code, 0)
        self.assertIn("1 modifié(s)", sortie)
        self.assertIn("Demo anfragen", sortie)
        relue = Table("de", self.langues)
        self.assertEqual(relue.entrees[cle(DEMO)]["trad"], "Demo vereinbaren")
        rapports = list(self.sortie.glob("rapport-import-*.txt"))
        self.assertEqual(len(rapports), 1)
        self.assertIn("Alice", rapports[0].name)
        self.assertIn("Demo vereinbaren", rapports[0].read_text(encoding="utf-8"))
        self.assertIn("Export d'origine non fourni", sortie)  # de.xlf n'est pas nommé neur-on-de.xlf

    def test_importer_texte_modifie_et_unite_perdue(self):
        """Vague finale, points 2 et 15 : texte FR modifié sur le site depuis l'export (contexte écrit dans
        contextes.json) et unité de l'export perdue par le fichier rendu (export d'origine trouvé à côté du fichier)."""
        self.table.enregistrer()
        export, _ = self.exporter(nom="neur-on-de.xlf")
        rendu = self.sortie / "neur-on-de-rendu.xlf"
        texte = export.read_text(encoding="utf-8").replace("Demo anfragen", "Demo vereinbaren")
        texte = re.sub(r'\s*<trans-unit id="' + cle(CAPITAL) + r'">.*?</trans-unit>', "", texte, flags=re.S)
        rendu.write_text(texte, encoding="utf-8")
        self.confirmer(rendu)
        nouveau = "Demander une démo gratuite"
        pages = {p: h.replace(f"<p>{DEMO}</p>", f"<p>{nouveau}</p>") for p, h in PAGES.items()}
        code, sortie, _ = self.lancer("importer", "de", str(rendu), "--relecteur", "Alice", "--sortie", str(self.sortie),
                                      pages=pages)
        self.assertEqual(code, 0, sortie)
        self.assertIn("Unités de l'export absentes du fichier rendu (1)", sortie)
        self.assertIn(cle(CAPITAL), sortie)
        self.assertIn(f"{cle(DEMO)} -> {cle(nouveau)}", sortie)
        contextes = json.loads((self.langues / "de" / traduire.CONTEXTES).read_text(encoding="utf-8"))
        self.assertEqual(contextes[cle(nouveau)]["contexte"]["trad_complete"], "Demo vereinbaren")
        self.assertEqual(Table("de", self.langues).entrees[cle(DEMO)]["statut"], "v1")

    def test_importer_avec_rejets_code_zero_et_les_dit(self):
        self.table.enregistrer()
        fichier, _ = self.exporter()
        self.remplacer(fichier, "Demo anfragen", f"Demo {TIRET_CADRATIN}")
        code, sortie, _ = self.lancer("importer", "de", str(fichier), "--relecteur", "Alice", "--sortie", str(self.sortie))
        self.assertEqual(code, 0)
        self.assertIn("1 rejeté(s)", sortie)
        self.assertIn("tirets", sortie)
        self.assertEqual(Table("de", self.langues).entrees[cle(DEMO)]["trad"], "Demo anfragen")

    def test_importer_sans_confirmation_puis_sans_etat(self):
        self.table.enregistrer()
        fichier, _ = self.exporter()
        code, sortie, _ = self.lancer("importer", "de", str(fichier), "--relecteur", "Alice", "--sortie", str(self.sortie))
        self.assertEqual(code, 0)
        self.assertIn("2 non confirmé(s) par le relecteur", sortie)
        self.assertIn("Non confirmés par le relecteur", sortie)
        self.assertEqual(Table("de", self.langues).entrees[cle(CAPITAL)]["statut"], "adapte")
        code, sortie, _ = self.lancer("importer", "de", str(fichier), "--relecteur", "Alice", "--sortie", str(self.sortie),
                                      "--sans-etat")
        self.assertEqual(code, 0)
        self.assertIn("0 non confirmé(s)", sortie)
        self.assertIn("2 segment(s) mt ou adapte confirmé(s) sans aucune modification", sortie)
        self.assertEqual(Table("de", self.langues).entrees[cle(CAPITAL)]["statut"], "relu")

    def test_importer_csv(self):
        self.table.enregistrer()
        f = self.tmp / "c.csv"
        f.write_text(f"cle;fr;trad\n{cle(DEMO)};{DEMO};Demo vereinbaren\n", encoding="utf-8-sig")
        code, sortie, _ = self.lancer("importer", "de", str(f), "--relecteur", "Alice", "--sortie", str(self.sortie))
        self.assertEqual(code, 0)
        self.assertEqual(Table("de", self.langues).entrees[cle(DEMO)]["trad"], "Demo vereinbaren")

    def test_importer_fichier_d_une_autre_langue(self):
        self.table.enregistrer()
        fichier, _ = self.exporter()
        self.remplacer(fichier, 'target-language="de-CH"', 'target-language="en"')
        code, _, erreur = self.lancer("importer", "de", str(fichier), "--relecteur", "Alice", "--sortie", str(self.sortie))
        self.assertEqual(code, 1)
        self.assertIn("de-CH", erreur)
        self.assertIn("« en »", erreur)
        self.assertEqual(erreur.lower().count("refusé"), 1)


if __name__ == "__main__":
    unittest.main()
