"""Pont LexMachina (tâche 6.1) : outils/i18n/pont_corrext.py et pont_corrext.js.

Serveur local sur le port 0 (choisi par le système, adresse 127.0.0.1) et client simulé : aucun accès au réseau, aucun appel à
Corrext, aucun lancement du pont réel. Tables et listes à traduire synthétiques, dans des dossiers temporaires."""
import contextlib
import io
import json
import re
import tempfile
import threading
import unittest
import urllib.error
import urllib.request
from pathlib import Path
from unittest import mock

from outils.i18n import pont_corrext as P
from outils.i18n.table import Table, cle

ICI = Path(__file__).resolve().parent.parent
TIRET_CADRATIN = chr(0x2014)
JOUR = "2026-10-26"

DEMO = "Demander une démo"
LIEN = "Le {1}capital-actions{/1} de la société"
ADRESSE = "Adresse{1}Fribourg"


def a_traduire(*textes):
    """Contenu de a_traduire.json : {clé: {"fr": texte}}."""
    return {cle(t): {"fr": t} for t in textes}


class Base(unittest.TestCase):
    def setUp(self):
        self._tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self._tmp.cleanup)
        self.langues = Path(self._tmp.name)

    def ecrire(self, langue, textes):
        d = self.langues / langue
        d.mkdir(parents=True, exist_ok=True)
        (d / "a_traduire.json").write_text(json.dumps(a_traduire(*textes), ensure_ascii=False), encoding="utf-8")

    def brut(self, langue="de"):
        f = self.langues / langue / "brut" / "traductions.json"
        return json.loads(f.read_text(encoding="utf-8")) if f.is_file() else {}


class Serveur(Base):
    """Le pont servi sur 127.0.0.1, port libre ; le client est urllib (rien ne sort de la machine)."""

    def demarrer(self, pont):
        serveur = P.creer_serveur(pont, port=0)
        self.addCleanup(serveur.server_close)
        fil = threading.Thread(target=lambda: serveur.serve_forever(poll_interval=0.01), daemon=True)
        fil.start()
        self.addCleanup(fil.join)
        self.addCleanup(serveur.shutdown)
        self.base = f"http://127.0.0.1:{serveur.server_address[1]}"
        return serveur

    def lot(self, n=None):
        with urllib.request.urlopen(self.base + "/lot" + (f"?n={n}" if n else "")) as r:
            return json.loads(r.read().decode("utf-8"))

    def envoyer(self, donnees):
        requete = urllib.request.Request(self.base + "/resultat", data=donnees if isinstance(donnees, bytes)
                                         else json.dumps(donnees).encode("utf-8"),
                                         headers={"Content-Type": "application/json"}, method="POST")
        with urllib.request.urlopen(requete) as r:
            return json.loads(r.read().decode("utf-8"))


class TestLots(Serveur):
    def test_lot_respecte_8000_caracteres(self):
        gros = [f"Texte {i} " + "mot " * 370 for i in range(30)]  # environ 1 490 caractères chacun
        self.ecrire("de", gros)
        self.demarrer(P.Pont("de", self.langues))
        vus, lots = set(), 0
        while True:
            j = self.lot()
            if not j["lot"]:
                break
            lots += 1
            self.assertLessEqual(sum(len(x["texte"]) for x in j["lot"]), P.LOT_MAX_CARACTERES)
            self.assertLessEqual(len(j["lot"]), P.LOT_MAX_TEXTES)
            self.assertFalse(vus & {x["k"] for x in j["lot"]}, "un texte est servi deux fois pendant qu'il est en cours")
            vus |= {x["k"] for x in j["lot"]}
        self.assertEqual(len(vus), 30)
        self.assertGreaterEqual(lots, 6)  # 30 textes à 5 par lot

    def test_lot_limite_le_nombre_de_textes(self):
        self.ecrire("de", [f"Mot {i}" for i in range(60)])
        self.demarrer(P.Pont("de", self.langues))
        self.assertEqual(len(self.lot()["lot"]), P.LOT_MAX_TEXTES)
        self.assertEqual(len(self.lot(3)["lot"]), 3)

    def test_lot_donne_les_identifiants_de_langue(self):
        self.ecrire("de", [DEMO])
        self.demarrer(P.Pont("de", self.langues))
        j = self.lot()
        self.assertEqual((j["source"], j["cible"], j["fournisseur"]), (51, 46, 1))
        self.assertEqual(j["lot"], [{"k": cle(DEMO), "texte": DEMO}])

    def test_identifiants_de_langue_du_pont(self):
        self.assertEqual({"fr": P.LANGUE_SOURCE, **P.CIBLES}, {"fr": 51, "de": 46, "it": 140, "en": 56})
        self.assertEqual(P.FOURNISSEUR_LEXMACHINA, 1)

    def test_un_texte_en_cours_revient_apres_le_delai(self):
        self.ecrire("de", [DEMO])
        horloge = {"t": 1000.0}
        self.demarrer(P.Pont("de", self.langues, horloge=lambda: horloge["t"]))
        self.assertEqual(len(self.lot()["lot"]), 1)
        self.assertEqual(self.lot()["lot"], [])
        horloge["t"] += P.DELAI_EN_COURS + 1
        self.assertEqual(len(self.lot()["lot"]), 1)

    def test_etat(self):
        self.ecrire("de", [DEMO, "Contact"])
        self.demarrer(P.Pont("de", self.langues))
        with urllib.request.urlopen(self.base + "/etat") as r:
            self.assertEqual(json.loads(r.read().decode("utf-8")), {"total": 2, "faits": 0})
        self.envoyer([{"k": cle(DEMO), "traduction": "Demo anfragen"}])
        with urllib.request.urlopen(self.base + "/etat") as r:
            self.assertEqual(json.loads(r.read().decode("utf-8")), {"total": 2, "faits": 1})

    def test_chemin_inconnu_donne_404(self):
        self.ecrire("de", [DEMO])
        self.demarrer(P.Pont("de", self.langues))
        with self.assertRaises(urllib.error.HTTPError) as c:
            urllib.request.urlopen(self.base + "/autre")
        self.assertEqual(c.exception.code, 404)

    def test_le_pont_ne_sert_que_la_boucle_locale(self):
        self.ecrire("de", [DEMO])
        serveur = self.demarrer(P.Pont("de", self.langues))
        self.assertEqual(serveur.server_address[0], "127.0.0.1")


class TestResultats(Serveur):
    def test_resultat_enregistre_mt(self):
        self.ecrire("de", [DEMO, LIEN])
        pont = P.Pont("de", self.langues)
        self.demarrer(pont)
        j = self.lot()
        rep = self.envoyer([{"k": x["k"], "traduction": {DEMO: "Demo anfragen", LIEN: "Das {1}Aktienkapital{/1} der Gesellschaft"}[x["texte"]]}
                            for x in j["lot"]])
        self.assertEqual(rep, {"ok": 2})
        self.assertEqual(self.brut(), {cle(DEMO): "Demo anfragen", cle(LIEN): "Das {1}Aktienkapital{/1} der Gesellschaft"})
        # un nouveau pont (reprise après arrêt) relit le fichier et ne redemande rien
        self.assertEqual(P.Pont("de", self.langues).lot()["lot"], [])
        # la réinjection pose les traductions au statut mt, source « LexMachina <date> »
        table = Table("de", self.langues)
        rapport = P.reinjecter("de", table, self.langues, jour=JOUR)
        self.assertEqual(rapport["poses"], 2)
        e = table.chercher(DEMO, "")
        self.assertEqual((e["trad"], e["statut"], e["source"]), ("Demo anfragen", "mt", f"LexMachina {JOUR}"))
        self.assertEqual(table.chercher(LIEN, "")["trad"], "Das {1}Aktienkapital{/1} der Gesellschaft")
        self.assertEqual(rapport["a_revoir"], [])

    def test_resultat_inconnu_ignore(self):
        self.ecrire("de", [DEMO])
        self.demarrer(P.Pont("de", self.langues))
        rep = self.envoyer([{"k": "0123456789abcdef", "traduction": "Inconnu"},
                            {"k": cle(DEMO), "traduction": "   "},
                            {"k": cle(DEMO), "traduction": 12},
                            {"k": cle(DEMO)},
                            "pas un objet",
                            {"k": cle(DEMO), "traduction": "Demo anfragen"}])
        self.assertEqual(rep, {"ok": 1})
        self.assertEqual(self.brut(), {cle(DEMO): "Demo anfragen"})

    def test_tiret_long_de_la_sortie_brute_jamais_ecrit_en_clair(self):
        self.ecrire("de", [DEMO])
        self.demarrer(P.Pont("de", self.langues))
        self.envoyer([{"k": cle(DEMO), "traduction": f"Demo {TIRET_CADRATIN} anfragen"}])
        fichier = self.langues / "de" / "brut" / "traductions.json"
        self.assertNotIn(TIRET_CADRATIN, fichier.read_text(encoding="utf-8"))
        self.assertEqual(self.brut()[cle(DEMO)], f"Demo {TIRET_CADRATIN} anfragen")  # relu tel quel par json

    def test_corps_illisible_refuse_sans_rien_ecrire(self):
        self.ecrire("de", [DEMO])
        self.demarrer(P.Pont("de", self.langues))
        with self.assertRaises(urllib.error.HTTPError) as c:
            self.envoyer(b"pas du json")
        self.assertEqual(c.exception.code, 400)
        self.assertEqual(self.brut(), {})

    def test_le_pont_n_enregistre_que_cle_et_traduction(self):
        """Le serveur ne lit ni ne garde rien d'autre que {k, traduction} : un jeton posté par erreur ne s'écrit nulle part."""
        self.ecrire("de", [DEMO])
        self.demarrer(P.Pont("de", self.langues))
        self.envoyer([{"k": cle(DEMO), "traduction": "Demo anfragen", "token": "secret-123"}])
        for f in self.langues.rglob("*"):
            if f.is_file():
                self.assertNotIn("secret-123", f.read_text(encoding="utf-8"))


class TestPortee(Base):
    def test_pages_limite_les_textes_servis(self):
        self.ecrire("de", [DEMO, "Contact", "Notre équipe"])
        pont = P.Pont("de", self.langues, cles={cle(DEMO), cle("Contact")})
        self.assertEqual({x["k"] for x in pont.lot()["lot"]}, {cle(DEMO), cle("Contact")})
        self.assertEqual(pont.etat(), {"total": 2, "faits": 0})

    def test_un_texte_deja_traduit_dans_la_table_n_est_pas_renvoye(self):
        self.ecrire("de", [DEMO, "Contact"])
        table = Table("de", self.langues)
        table.poser("Contact", "Kontakt", "mt", "LexMachina")
        pont = P.Pont("de", self.langues, table=table)
        self.assertEqual([x["k"] for x in pont.lot()["lot"]], [cle(DEMO)])

    def test_un_texte_par_page_seulement_est_renvoye(self):
        """Une entrée sans traduction par défaut (Ruling 19) n'est pas traduite : elle manque sur les autres pages."""
        self.ecrire("de", [DEMO])
        table = Table("de", self.langues)
        table.poser(DEMO, DEMO, "v1", "V1", page="a/", sans_defaut=True)
        self.assertEqual(len(P.Pont("de", self.langues, table=table).lot()["lot"]), 1)

    def test_cles_des_pages(self):
        pages = {"": "<!DOCTYPE html>\n<html lang=\"fr\"><head><meta charset=\"utf-8\"></head><body>\n<main id=\"main\"><p>Demander une démo</p></main>\n</body></html>",
                 "corrext/plugin-word/": "<!DOCTYPE html>\n<html lang=\"fr\"><head><meta charset=\"utf-8\"></head><body>\n<main id=\"main\"><p>Un plugin pour Word</p></main>\n</body></html>",
                 "contact/": "<!DOCTYPE html>\n<html lang=\"fr\"><head><meta charset=\"utf-8\"></head><body>\n<main id=\"main\"><p>Contact</p></main>\n</body></html>"}
        table = Table("de", self.langues)
        cles = P.cles_des_pages("de", ["", "corrext/plugin-word/"], table, pages)
        self.assertEqual(cles, {cle("Demander une démo"), cle("Un plugin pour Word")})
        # « accueil » désigne la page d'accueil, comme dans la commande exporter
        self.assertEqual(P.cles_des_pages("de", ["accueil"], table, pages), {cle("Demander une démo")})
        with self.assertRaises(ValueError) as e:
            P.cles_des_pages("de", ["nexiste/pas/"], table, pages)
        self.assertIn("nexiste/pas/", str(e.exception))


class TestReinjection(Base):
    def reinjecter(self, textes_et_brut, table=None):
        """Écrit a_traduire.json et traductions.json, réinjecte ; rend (table, rapport)."""
        self.ecrire("de", [t for t, _ in textes_et_brut])
        brut = self.langues / "de" / "brut"
        brut.mkdir(parents=True, exist_ok=True)
        (brut / "traductions.json").write_text(json.dumps({cle(t): b for t, b in textes_et_brut}, ensure_ascii=False),
                                               encoding="utf-8")
        table = table or Table("de", self.langues)
        return table, P.reinjecter("de", table, self.langues, jour=JOUR)

    def test_marqueurs_abimes_vont_dans_a_revoir(self):
        table, rapport = self.reinjecter([(LIEN, "Das {1}Aktienkapital der Gesellschaft"),   # fermant perdu
                                          (ADRESSE, "Adresse{1}Freiburg{1}"),                 # marqueur seul en double
                                          (DEMO, "Demo anfragen")])
        self.assertEqual(rapport["poses"], 3)
        self.assertEqual({a["cle"] for a in rapport["a_revoir"]}, {cle(LIEN), cle(ADRESSE)})
        a = next(x for x in rapport["a_revoir"] if x["cle"] == cle(LIEN))
        self.assertEqual((a["fr"], a["trad_brute"]), (LIEN, "Das {1}Aktienkapital der Gesellschaft"))
        self.assertIn("{1}", a["probleme"])
        # le texte posé est le texte aplati, sans marqueur ; il reste au statut mt, jamais publiable tel quel
        e = table.chercher(LIEN, "")
        self.assertEqual((e["trad"], e["statut"]), ("Das Aktienkapital der Gesellschaft", "mt"))
        # le fichier a_revoir.json est écrit à côté des traductions brutes
        fichier = self.langues / "de" / "brut" / "a_revoir.json"
        self.assertEqual({a["cle"] for a in json.loads(fichier.read_text(encoding="utf-8"))}, {cle(LIEN), cle(ADRESSE)})

    def test_espaces_ajoutees_dans_les_marqueurs_retirees(self):
        table, rapport = self.reinjecter([(LIEN, "Das {1} Aktienkapital {/1} der Gesellschaft")])
        self.assertEqual(table.chercher(LIEN, "")["trad"], "Das {1}Aktienkapital{/1} der Gesellschaft")
        self.assertEqual(rapport["a_revoir"], [])

    def test_espace_voulue_dans_le_francais_est_gardee(self):
        fr = "Le {1} mot{/1} seul"
        table, _ = self.reinjecter([(fr, "Das {1} Wort{/1} allein")])
        self.assertEqual(table.chercher(fr, "")["trad"], "Das {1} Wort{/1} allein")

    def test_eszett_remplace_par_ss(self):
        table, rapport = self.reinjecter([("Une rue", "Eine Straße"), ("Un pied", "Ein Fuß")])
        self.assertEqual(table.chercher("Une rue", "")["trad"], "Eine Strasse")
        self.assertEqual(table.chercher("Un pied", "")["trad"], "Ein Fuss")
        self.assertEqual(rapport["eszett"], 2)

    def test_eszett_du_francais_est_garde(self):
        table, _ = self.reinjecter([("Citation « Straße »", "Zitat « Straße »")])
        self.assertEqual(table.chercher("Citation « Straße »", "")["trad"], "Zitat « Straße »")

    def test_tiret_long_remplace_et_signale(self):
        brut = f"Demo {TIRET_CADRATIN} anfragen"
        table, rapport = self.reinjecter([(DEMO, brut)])
        self.assertEqual(table.chercher(DEMO, "")["trad"], "Demo - anfragen")
        a = rapport["a_revoir"]
        self.assertEqual([x["cle"] for x in a], [cle(DEMO)])
        self.assertIn("tiret", a[0]["probleme"])
        self.assertEqual(a[0]["trad_brute"], brut)
        # le fichier a_revoir.json ne contient pas non plus le caractère interdit
        fichier = (self.langues / "de" / "brut" / "a_revoir.json").read_text(encoding="utf-8")
        self.assertNotIn(TIRET_CADRATIN, fichier)

    def test_une_traduction_deja_adaptee_n_est_jamais_ecrasee(self):
        table = Table("de", self.langues)
        table.poser(DEMO, "Demo anfragen", "relu", "relu par X", v1=True)
        table.poser("Contact", "Kontakt", "adapte", "adapté")
        table.poser("Notre équipe", "Altes Team", "mt", "LexMachina 2026-10-20")
        table, rapport = self.reinjecter([(DEMO, "Demo bestellen"), ("Contact", "Kontakt aufnehmen"),
                                          ("Notre équipe", "Unser Team")], table)
        self.assertEqual(rapport["poses"], 1)  # seule la sortie mt est remplacée par la plus récente
        self.assertEqual(rapport["deja_traduits"], 2)
        e = table.chercher(DEMO, "")
        self.assertEqual((e["trad"], e["statut"]), ("Demo anfragen", "relu"))
        self.assertTrue(table.entrees[cle(DEMO)]["v1"])
        self.assertEqual(table.chercher("Contact", "")["trad"], "Kontakt")
        self.assertEqual(table.chercher("Notre équipe", "")["trad"], "Unser Team")

    def test_les_traductions_par_page_sont_conservees(self):
        table = Table("de", self.langues)
        table.poser(DEMO, DEMO, "v1", "V1", page="a/", sans_defaut=True)
        table, _ = self.reinjecter([(DEMO, "Demo anfragen")], table)
        self.assertEqual(table.chercher(DEMO, "")["trad"], "Demo anfragen")
        self.assertEqual(table.chercher(DEMO, "a/")["statut"], "v1")

    def test_traduction_hors_liste_ignoree(self):
        self.ecrire("de", [DEMO])
        brut = self.langues / "de" / "brut"
        brut.mkdir(parents=True)
        (brut / "traductions.json").write_text(json.dumps({cle("Contact"): "Kontakt", cle(DEMO): "Demo anfragen"}),
                                               encoding="utf-8")
        table = Table("de", self.langues)
        rapport = P.reinjecter("de", table, self.langues, jour=JOUR)
        self.assertEqual((rapport["poses"], rapport["hors_liste"]), (1, 1))
        self.assertIsNone(table.chercher("Contact", ""))

    def test_sans_traductions_brutes(self):
        self.ecrire("de", [DEMO])
        rapport = P.reinjecter("de", Table("de", self.langues), self.langues, jour=JOUR)
        self.assertEqual((rapport["poses"], rapport["a_revoir"]), (0, []))

    def test_ligne_de_commande(self):
        self.ecrire("de", [DEMO])
        brut = self.langues / "de" / "brut"
        brut.mkdir(parents=True)
        (brut / "traductions.json").write_text(json.dumps({cle(DEMO): "Demo anfragen"}), encoding="utf-8")
        sortie = io.StringIO()
        with contextlib.redirect_stdout(sortie), mock.patch.object(P, "SRC_LANGUES", self.langues):
            code = P.main(["reinjecter", "de"])
        self.assertEqual(code, 0)
        self.assertIn("1 traduction(s) posée(s)", sortie.getvalue())
        self.assertEqual(Table("de", self.langues).chercher(DEMO, "")["statut"], "mt")


class TestClientNavigateur(unittest.TestCase):
    """pont_corrext.js s'exécute dans l'onglet Corrext connecté : le jeton y reste."""

    def setUp(self):
        self.js = (ICI / "outils/i18n/pont_corrext.js").read_text(encoding="utf-8")

    def test_le_jeton_ne_quitte_jamais_l_onglet(self):
        self.assertNotIn("Authorization", self.js)
        self.assertNotIn("accessToken", self.js)
        self.assertNotIn("api/auth", self.js)
        # les seules requêtes du script visent le pont local
        self.assertEqual(set(re.findall(r"fetch\(([^,)]+)", self.js)), {"base + \"/lot?n=25\"", "base + \"/etat\"",
                                                                                    "base + \"/resultat\""})
        self.assertIn('"http://localhost:8812"', self.js)

    def test_le_script_ne_connait_ni_langue_ni_fournisseur(self):
        """Source, cible et fournisseur viennent du serveur (constantes de pont_corrext.py, à revérifier avant l'envoi)."""
        self.assertIn("j.source", self.js)
        self.assertIn("j.cible", self.js)
        self.assertIn("j.fournisseur", self.js)

    def test_aucun_tiret_long(self):
        for f in ("pont_corrext.js", "pont_corrext.py"):
            t = (ICI / "outils/i18n" / f).read_text(encoding="utf-8")
            self.assertNotIn(TIRET_CADRATIN, t)
            self.assertNotIn(chr(0x2013), t)


if __name__ == "__main__":
    unittest.main()
