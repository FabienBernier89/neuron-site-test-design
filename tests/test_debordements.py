"""Outil de mesure des débordements (outils/debordements.mjs, tâche 6.3) : pages de fixtures minimales mesurées dans Chrome
sans interface, jamais le site. Ignorés si Node ou Chrome manquent."""
import json
import shutil
import subprocess
import tempfile
import unittest
from pathlib import Path

from outils.i18n import og_image

ICI = Path(__file__).resolve().parent.parent
OUTIL = ICI / "outils/debordements.mjs"
NODE = shutil.which("node")
PRET = NODE is not None and og_image.chrome() is not None
TIRET_CADRATIN, DEMI_CADRATIN = chr(0x2014), chr(0x2013)


def page(corps, tete=""):
    return ('<!doctype html><html lang="de"><head><meta charset="utf-8">'
            '<meta name="viewport" content="width=device-width,initial-scale=1">'
            f"<title>t</title><style>body{{margin:0;font:16px/24px sans-serif}}{tete}</style></head><body>{corps}</body></html>")


@unittest.skipUnless(PRET, "Node ou Chrome absent")
class TestDebordements(unittest.TestCase):
    def setUp(self):
        self._tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self._tmp.cleanup)
        self.racine = Path(self._tmp.name) / "site"

    def ecrire(self, adresse, html):
        fichier = self.racine / adresse / "index.html"
        fichier.parent.mkdir(parents=True, exist_ok=True)
        fichier.write_text(html, encoding="utf-8")

    def mesurer(self, pages, largeurs="390,1440", regles=None, extra=()):
        """Lance l'outil en JSON ; renvoie (code de sortie, rapport). Sans regles, aucune règle de lignes (fichier vide)."""
        fichier = Path(self._tmp.name) / "regles.json"
        fichier.write_text(json.dumps(regles or {}), encoding="utf-8")
        r = subprocess.run([NODE, str(OUTIL), "--racine", str(self.racine), "--pages", pages, "--largeurs", largeurs,
                            "--regles", str(fichier), "--json", *extra], capture_output=True, text=True, timeout=120)
        try:
            return r.returncode, json.loads(r.stdout)
        except ValueError:
            self.fail(f"sortie illisible (code {r.returncode}) : {r.stdout[:300]} {r.stderr[:300]}")

    def test_debordement_detecte(self):
        """Un span nowrap d'environ 600 px ou plus déborde à 390 px (texte hors de la page et de la fenêtre), pas à 1440 px."""
        self.ecrire("de", page('<p><span style="white-space:nowrap">' + "Ein sehr langes Wort ohne Umbruch. " * 3 + "</span></p>"))
        code, rapport = self.mesurer("de/")
        etroit, large = rapport["pages"]
        self.assertEqual((etroit["largeur"], large["largeur"]), (390, 1440))
        self.assertEqual(code, 1)
        self.assertTrue(etroit["hors_fenetre"], etroit)
        self.assertTrue(any("span" in o["selecteur"] and o["droite"] > 390 for o in etroit["hors_fenetre"]))
        self.assertTrue(any(o["selecteur"] == "html" for o in etroit["debordements"]), etroit["debordements"])
        self.assertEqual((large["debordements"], large["hors_fenetre"], large["lignes"]), ([], [], []))
        self.assertEqual(rapport["total"], len(etroit["debordements"]) + len(etroit["hors_fenetre"]))

    def test_page_saine_code_zero(self):
        self.ecrire("de", page("<h1>Titre</h1><p>Un texte qui passe à la ligne sans rien déborder.</p>"))
        code, rapport = self.mesurer("de/")
        self.assertEqual((code, rapport["total"]), (0, 0))

    def test_boite_a_contenu_plus_large(self):
        """Texte qui dépasse sa propre boîte à overflow caché, alors que la fenêtre n'est pas dépassée."""
        self.ecrire("de", page('<div id="b" style="width:200px;overflow:hidden"><span style="white-space:nowrap">'
                               "Donaudampfschifffahrtsgesellschaftskapitän</span></div>"))
        code, rapport = self.mesurer("de/", largeurs="390")
        o = rapport["pages"][0]["debordements"]
        self.assertEqual(code, 1)
        self.assertEqual([x["selecteur"] for x in o], ["#b"])
        self.assertGreater(o[0]["scrollWidth"], o[0]["clientWidth"] + 1)
        self.assertEqual(rapport["pages"][0]["hors_fenetre"], [])

    def test_lignes_depassees(self):
        """Un sélecteur qui passe son nombre de lignes est relevé, avec les lignes réelles ; les autres non."""
        self.ecrire("de", page('<div style="width:220px"><h3 class="t">Ein langer Titel der auf mehreren Zeilen steht '
                               'weil er nicht in eine Zeile passt</h3><h3 class="u">Kurz</h3></div>'))
        code, rapport = self.mesurer("de/", largeurs="1440", regles={".t": 2, ".u": 1})
        lignes = rapport["pages"][0]["lignes"]
        self.assertEqual(code, 1)
        self.assertEqual([(o["selecteur"], o["max"]) for o in lignes], [(".t", 2)])
        self.assertGreater(lignes[0]["lignes"], 2)
        code, rapport = self.mesurer("de/", largeurs="1440", regles={".t": 20, ".u": 1})
        self.assertEqual((code, rapport["total"]), (0, 0))

    def test_exclusions_voulues(self):
        """Lien d'évitement à -9999 px, zone faite pour défiler, texte tronqué par des points, texte pour lecteurs
        d'écran, élément transparent : aucun de ceux-là n'est un débordement."""
        self.ecrire("de", page(
            '<a href="#c" style="position:absolute;left:-9999px">Zum Inhalt</a>'
            '<div style="width:200px;overflow-x:auto"><span style="white-space:nowrap">Ein Streifen der gewollt läuft und läuft und läuft</span></div>'
            '<div style="width:100px;overflow:hidden;text-overflow:ellipsis;white-space:nowrap">Ein abgeschnittener langer Text</div>'
            '<span style="position:absolute;width:1px;height:1px;overflow:hidden;clip:rect(0 0 0 0);white-space:nowrap">Nur für Vorleser, lang</span>'
            '<div style="opacity:0;width:100px;overflow:hidden"><span style="white-space:nowrap">Unsichtbarer langer Text hier</span></div>'
            '<main id="c"><p>Inhalt</p></main>'))
        code, rapport = self.mesurer("de/", largeurs="390")
        self.assertEqual((code, rapport["total"]), (0, 0), rapport)

    def test_menus_mesures_ouverts(self):
        """Le panneau d'un méga-menu (hidden, ouvert par un clic) est mesuré ouvert, avec le nom de son état."""
        self.ecrire("de", page(
            '<header id="hd"><button type="button" data-mg aria-expanded="false" aria-controls="p">Produkt</button>'
            '<div id="p" class="mg" hidden><a class="mg-a" href="#"><em style="display:block;width:120px">'
            "Ein Untertitel der auf drei Zeilen umgebrochen wird und noch mehr</em></a></div></header>"
            "<script>var b=document.querySelector('[data-mg]'),p=document.getElementById('p');"
            "b.addEventListener('click',function(){b.setAttribute('aria-expanded','true');p.hidden=false})</script>"))
        code, rapport = self.mesurer("de/", largeurs="1440", regles={".mg-a em": 2})
        lignes = rapport["pages"][0]["lignes"]
        self.assertEqual(code, 1)
        self.assertEqual(len(lignes), 1, lignes)
        self.assertIn("Produkt", lignes[0]["etat"])
        self.assertGreater(lignes[0]["lignes"], 2)

    def test_captures_et_rapport_texte(self):
        """--captures écrit une image par page et par largeur ; sans --json, le rapport est en français."""
        self.ecrire("de/corrext/word-plugin", page("<p>Inhalt</p>"))
        sortie = Path(self._tmp.name) / "captures"
        r = subprocess.run([NODE, str(OUTIL), "--racine", str(self.racine), "--pages", "de/corrext/word-plugin/",
                            "--largeurs", "390,1440", "--captures", str(sortie)], capture_output=True, text=True, timeout=120)
        self.assertEqual(r.returncode, 0, r.stderr)
        self.assertEqual(sorted(f.name for f in sortie.glob("*.png")),
                         ["de-corrext-word-plugin_1440.png", "de-corrext-word-plugin_390.png"])
        self.assertIn("aucun débordement", r.stdout)
        self.assertEqual(len(r.stdout.strip().splitlines()), 2)

    def test_reference_ignore_les_releves_francais(self):
        """Vague finale, point 12 (Ruling 33) : --reference <rapport.json> ignore les relevés déjà présents dans le rapport
        de référence (même genre, largeur et sélecteur) et les compte à part."""
        self.ecrire("fr", page('<div id="b" style="width:200px;overflow:hidden"><span style="white-space:nowrap">'
                               "Texte trop long pour sa boîte</span></div>"))
        self.ecrire("de", page('<div id="b" style="width:200px;overflow:hidden"><span style="white-space:nowrap">'
                               "Ein viel zu langer Text für die Box</span></div><p id='n' style='width:50px;white-space:nowrap'>"
                               "Neuer Überlauf nur auf Deutsch</p>"))
        code, fr = self.mesurer("fr/", largeurs="390")
        self.assertEqual(code, 1)
        reference = Path(self._tmp.name) / "reference.json"
        reference.write_text(json.dumps(fr), encoding="utf-8")
        code, de = self.mesurer("de/", largeurs="390", extra=("--reference", str(reference)))
        p = de["pages"][0]
        self.assertGreaterEqual(p["connus"], 1)
        self.assertNotIn("#b", [o["selecteur"] for o in p["debordements"]])
        self.assertTrue(any("#n" in o["selecteur"] for o in p["hors_fenetre"] + p["debordements"]), p)
        self.assertEqual(code, 1)

    def test_ressource_introuvable_signalee(self):
        """Vague finale, point 12 : un 404 du serveur (image absente) est un problème listé avec la page ; une adresse
        mal encodée ne fait pas tomber le serveur (decodeURIComponent rattrapé)."""
        self.ecrire("de", page('<img src="manque.png" alt="" width="10" height="10"><img src="x%E0%A4%A.png" alt="">'))
        code, rapport = self.mesurer("de/", largeurs="1440")
        self.assertEqual(code, 1)
        introuvables = rapport["pages"][0]["introuvables"]
        self.assertIn("/de/manque.png", introuvables)
        self.assertEqual(rapport["total"], len(introuvables))

    def test_aide_code_zero(self):
        r = subprocess.run([NODE, str(OUTIL), "--help"], capture_output=True, text=True, timeout=60)
        self.assertEqual(r.returncode, 0, r.stderr)
        self.assertIn("--reference", r.stdout)

    def test_chrome_sans_port_arrete_et_profil_supprime(self):
        """Vague finale, point 12 : Chrome qui n'ouvre jamais son port est arrêté et son profil temporaire supprimé."""
        self.ecrire("de", page("<p>Inhalt</p>"))
        trace = Path(self._tmp.name) / "profil.txt"
        faux = Path(self._tmp.name) / "faux-chrome.sh"
        faux.write_text("#!/bin/sh\nfor a in \"$@\"; do case $a in --user-data-dir=*) echo \"${a#--user-data-dir=}\" > "
                        f"'{trace}';; esac; done\nexec sleep 60\n", encoding="utf-8")
        faux.chmod(0o755)
        r = subprocess.run([NODE, str(OUTIL), "--racine", str(self.racine), "--pages", "de/"], capture_output=True, text=True,
                           timeout=60, env={**__import__("os").environ, "CHROME": str(faux), "DEBORDEMENTS_DELAI_CHROME": "1500"})
        self.assertEqual(r.returncode, 2, r.stderr)
        self.assertIn("port de pilotage", r.stderr)
        profil = Path(trace.read_text(encoding="utf-8").strip())
        self.assertFalse(profil.exists(), profil)

    def test_erreur_d_usage(self):
        """Page absente de la racine : code 2 et message en français, sans lancer Chrome."""
        self.racine.mkdir(parents=True)
        r = subprocess.run([NODE, str(OUTIL), "--racine", str(self.racine), "--pages", "de/"],
                           capture_output=True, text=True, timeout=60)
        self.assertEqual(r.returncode, 2)
        self.assertIn("page absente", r.stderr)


@unittest.skipUnless(NODE, "Node absent")
class TestFichiersDeLOutil(unittest.TestCase):
    def test_regles_de_depart(self):
        regles = json.loads((ICI / "outils/debordements.json").read_text(encoding="utf-8"))
        self.assertEqual(regles, {".mg-a em": 2, ".tf-3 .tf-t h3": 2})

    def test_aucun_tiret_long(self):
        for f in (OUTIL, ICI / "outils/debordements.json"):
            texte = f.read_text(encoding="utf-8")
            self.assertNotIn(TIRET_CADRATIN, texte, f.name)
            self.assertNotIn(DEMI_CADRATIN, texte, f.name)

    def test_syntaxe_valide(self):
        r = subprocess.run([NODE, "--check", str(OUTIL)], capture_output=True, text=True)
        self.assertEqual(r.returncode, 0, r.stderr)


if __name__ == "__main__":
    unittest.main()
