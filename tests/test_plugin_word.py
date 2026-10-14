"""Plugin Word (lot A de la V2) : page corrext/plugin-word/, scène « word », entrées de menu et de pied, mentions
existantes reliées par le post-traitement lien_plugin_word, textes nouveaux tirés de src/data/contenus-v2."""
import html as H
import json
import posixpath
import re
import subprocess
import sys
import unittest
from pathlib import Path

ICI = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ICI))
sys.path.insert(0, str(ICI / "outils/composer"))
import build  # noqa: E402
from outils import contenus  # noqa: E402
from outils.post import lien_plugin_word  # noqa: E402

PAGE = "corrext/plugin-word/"
EDITEUR_V1 = build.NEURON / "docs/fr/corrext/editeur-de-relecture/index.html"


def sans_balises(h):
    return re.sub(r"<[^>]+>", "", h)


def resoudre(page, href):
    """Chemin publié visé par un lien relatif d'une page construite (sans fr/ ni index.html)."""
    return posixpath.normpath(posixpath.join("fr", page, href.split("#")[0].split("?")[0]))


class TestPluginWord(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        subprocess.run([sys.executable, str(ICI / "build.py")], check=True, cwd=ICI, stdout=subprocess.DEVNULL)
        cls.h = build.chemin_page(PAGE).read_text(encoding="utf-8")
        cls.accueil = build.chemin_page("").read_text(encoding="utf-8")

    def test_page_menu_scene(self):
        self.assertEqual(len(re.findall(r"<h1[ >]", self.h)), 1)
        self.assertIn('data-sim="word"', self.h)
        self.assertRegex(build.chemin_page("corrext/chnell/").read_text(encoding="utf-8"), r'href="(\.\./)+fr/corrext/plugin-word/"')

    def test_mentions_existantes_reliees(self):
        hub = build.chemin_page("corrext/").read_text(encoding="utf-8")
        self.assertRegex(hub, r'<a [^>]*href="(\.\./)+fr/corrext/plugin-word/"[^>]*>Plugin MS Word natif</a>')
        self.assertRegex(self.accueil, r'<a [^>]*href="(\.\./)+fr/corrext/plugin-word/"[^>]*>plugin Microsoft Word</a>')
        # une seule mention reliée par page : la seconde du hub (FAQ) reste du texte
        self.assertEqual(len(re.findall(r">[Pp]lugin MS Word natif</a>", hub)), 1)
        self.assertIn("Par un plugin MS Word natif ou une application", hub)
        # page de l'éditeur de relecture : la première mention du complément Corrext, section « Travailler dans Word »
        editeur = build.chemin_page("corrext/editeur-de-relecture/").read_text(encoding="utf-8")
        self.assertRegex(editeur, r'Ouvrez-le dans Word avec le <a class="pw-lien" href="(\.\./)+fr/corrext/plugin-word/">'
                                  r'complément Corrext</a> :')
        principal = editeur[editeur.index("<main"):editeur.index("</main>")]
        self.assertEqual(len(re.findall(r'href="(?:\.\./)+fr/corrext/plugin-word/"', principal)), 1)

    def test_page_gabarit_corrext_et_script_de_scene(self):
        self.assertIn('class="hd-i actif" aria-expanded="false" aria-controls="mg-corrext"', self.h)
        self.assertRegex(self.h, r'<script src="(\.\./)+assets/visite-word\.js\?v=[0-9a-f]{8}" defer></script>')
        self.assertRegex(self.h, r'<script src="(\.\./)+assets/sim\.js\?v=[0-9a-f]{8}" defer></script>')
        self.assertIn('data-ech="1176x640"', self.h)
        self.assertEqual(self.h.count('data-sim="word"'), 1)

    def test_scene_libelles_de_la_maquette_word_et_de_l_editeur(self):
        scene = self.h[self.h.index('data-sim="word"'):self.h.index("</section>", self.h.index('data-sim="word"'))]
        texte = H.unescape(sans_balises(scene))
        for libelle in ("Accueil", "Insertion", "Révision", "Corrext", "Assistant IA", "Terme harmonisé : « Verzugszins ». "
                        "L'appliquer dans tout le document ?", "Oui, partout", "Ignorer", "Terminologie", "CHnell · droit suisse",
                        "Corrext editor", "AI Assistant", "Fast Lookup", "Matches", "Sync", "Alternatives", "Translation memories",
                        "From this project's TM", "Apply", "Contrat de mandat (exemple fictif)", "100%"):
            self.assertIn(libelle, texte, libelle)

    def test_appel_a_l_action_suivi_vers_contact(self):
        ctas = re.findall(r'<a [^>]*data-suivi="cta-plugin-word-(?:hero|fin)"[^>]*>', self.h)
        self.assertEqual(len(ctas), 2)
        for a in ctas:
            href = re.search(r'href="([^"]+)"', a).group(1)
            self.assertNotIn("secteur=", href)
            self.assertEqual(resoudre(PAGE, href), "fr/contact")

    def test_faq_quatre_questions_et_donnees_structurees(self):
        questions = [H.unescape(q) for q in re.findall(r"<summary>(.*?)</summary>", self.h)]
        self.assertEqual(len(questions), 4)
        faq = [d for d in build.blocs_json(self.h) if isinstance(d, dict) and d.get("@type") == "FAQPage"]
        self.assertEqual(len(faq), 1)
        self.assertEqual([q["name"] for q in faq[0]["mainEntity"]], questions)
        fil = [d for d in build.blocs_json(self.h) if isinstance(d, dict) and d.get("@type") == "BreadcrumbList"]
        self.assertEqual(fil[0]["itemListElement"][-1]["name"], "Plugin Word")

    def test_menu_et_pied(self):
        ajouts = json.loads((ICI / "src/data/menu-ajouts.json").read_text(encoding="utf-8"))
        panneau = [a for a in ajouts["panneaux"]["corrext"] if a["href"] == PAGE]
        pied = [a for a in ajouts["pied"]["Plateforme"] if a["href"] == PAGE]
        self.assertEqual(len(panneau), 1)
        self.assertEqual(len(pied), 1)
        self.assertEqual(panneau[0]["apres"], "corrext/editeur-de-relecture/")
        self.assertEqual(pied[0]["apres"], "corrext/editeur-de-relecture/")
        # textes du menu : ceux des contenus nouveaux, à relire par Fabien
        self.assertEqual(panneau[0]["titre"], contenus.texte("plugin-word.menu.titre"))
        self.assertEqual(panneau[0]["desc"], contenus.texte("plugin-word.menu.desc"))
        self.assertEqual(pied[0]["texte"], contenus.texte("plugin-word.menu.titre"))
        chnell = build.chemin_page("corrext/chnell/").read_text(encoding="utf-8")
        # dans le panneau Corrext (bureau), le menu mobile et le pied, juste après l'éditeur de relecture
        self.assertRegex(chnell, r'fr/corrext/editeur-de-relecture/"><b>[^<]+</b><em>[^<]+</em></a>\n'
                                 r'<a class="mg-a" href="(\.\./)+fr/corrext/plugin-word/"><b>Plugin Word</b>')
        self.assertRegex(chnell, r'fr/corrext/editeur-de-relecture/">[^<]+</a>\n<a href="(\.\./)+fr/corrext/plugin-word/">Plugin Word</a>')
        self.assertRegex(chnell, r'fr/corrext/editeur-de-relecture/">[^<]+</a></li>\n<li><a href="(\.\./)+fr/corrext/plugin-word/">Plugin Word</a></li>')

    def test_textes_de_la_page_issus_des_contenus(self):
        cles = {e["cle"] for e in contenus.toutes() if e["page"] == PAGE}
        for c in ("plugin-word.hero.titre", "plugin-word.hero.lead", "plugin-word.faq.titre", "plugin-word.cta.titre"):
            self.assertIn(c, cles)
        h1 = H.unescape(sans_balises(re.search(r"<h1[^>]*>(.*?)</h1>", self.h, re.S).group(1)))
        self.assertEqual(h1, contenus.texte("plugin-word.hero.titre"))

    def test_libelles_de_la_demo_repris_mot_pour_mot(self):
        """Les libellés que seule la démo de l'éditeur affiche (script) sont dans les contenus pour la relecture,
        et figurent mot pour mot dans la page de l'éditeur de relecture du site actuel."""
        brut = EDITEUR_V1.read_text(encoding="utf-8").replace("\\'", "'")
        demo = [e for e in contenus.toutes() if e["cle"].startswith("plugin-word.demo.")]
        self.assertGreaterEqual(len(demo), 4)
        for e in demo:
            self.assertIn(e["texte"], brut, e["cle"])

    def test_composeur_rejouable(self):
        import p_plugin_word
        source = (ICI / "src/pages" / PAGE / "index.html").read_text(encoding="utf-8")
        self.assertEqual(p_plugin_word.composer(), source)

    def test_script_de_scene_sans_texte_affiche(self):
        js = (ICI / "assets/visite-word.js").read_text(encoding="utf-8")
        self.assertIn('SIM.enregistrer("word"', js)
        self.assertIn("SIM.reduit", js)
        for c in re.findall(r'"([^"\\]*)"', js):
            self.assertIsNone(re.search(r"[a-zà-ÿ]{3,} [a-zà-ÿ]{3,} [a-zà-ÿ]{3,}", c, re.I), c)


class TestLienPluginWord(unittest.TestCase):
    """outils/post/lien_plugin_word.traiter : première mention hors lien reliée, texte inchangé."""
    LIEN = '<a class="pw-lien" href="{{ROOT}}corrext/plugin-word/">'

    def test_premiere_mention_hors_lien_seulement(self):
        h = ('<main><p>Le <a href="{{ROOT}}x/">plugin MS Word natif</a> ici.</p>'
             '<p>Un plugin MS Word natif, puis un plugin Microsoft Word.</p></main>')
        r = lien_plugin_word.traiter(h, "corrext/")
        self.assertEqual(r.count("corrext/plugin-word/"), 1)
        self.assertIn("Un " + self.LIEN + "plugin MS Word natif</a>, puis un plugin Microsoft Word.", r)
        self.assertIn('<a href="{{ROOT}}x/">plugin MS Word natif</a>', r)

    def test_texte_inchange(self):
        h = '<main><div class="bt-p"><b>Word</b><p>Plugin MS Word natif ou application.</p></div></main>'
        r = lien_plugin_word.traiter(h, "corrext/")
        self.assertNotEqual(r, h)
        self.assertEqual(sans_balises(r), sans_balises(h))

    def test_hors_main_attributs_scripts_et_elements_interactifs_intacts(self):
        h = ('<head><meta name="description" content="plugin Microsoft Word"></head><body><nav>plugin Microsoft Word</nav>'
             '<main><div aria-label="plugin Microsoft Word"><script>var s="plugin Microsoft Word";</script>'
             '<details><summary>Un plugin Microsoft Word ?</summary><div class="r"><p>Via le plugin Microsoft Word.</p></div></details>'
             '</div></main><footer>plugin Microsoft Word</footer></body>')
        r = lien_plugin_word.traiter(h, "")
        self.assertEqual(r.count(self.LIEN), 1)
        self.assertIn("<p>Via le " + self.LIEN + "plugin Microsoft Word</a>.</p>", r)
        self.assertEqual(r.replace(self.LIEN + "plugin Microsoft Word</a>", "plugin Microsoft Word"), h)

    def test_chevron_dans_un_attribut_entre_guillemets(self):
        """Un « > » dans un attribut entre guillemets ne termine pas la balise : aucun lien dans l'attribut."""
        h = ('<main><div data-x="a > plugin Microsoft Word" title=\'b > plugin MS Word natif\'>'
             '<p>Un plugin Microsoft Word.</p></div></main>')
        r = lien_plugin_word.traiter(h, "corrext/")
        self.assertEqual(r.count(self.LIEN), 1)
        self.assertIn('data-x="a > plugin Microsoft Word" title=\'b > plugin MS Word natif\'>', r)
        self.assertIn("<p>Un " + self.LIEN + "plugin Microsoft Word</a>.</p>", r)
        self.assertEqual(r.replace(self.LIEN + "plugin Microsoft Word</a>", "plugin Microsoft Word"), h)

    def test_sous_arbres_exclus(self):
        """template, noscript, sous-arbre aria-hidden="true" et écran simulé [data-scene] : aucun lien dedans,
        y compris après un élément de même nom fermé à l'intérieur."""
        cas = (("<template>", "</template>"), ("<noscript>", "</noscript>"),
               ('<div aria-hidden="true"><div>x</div>', "</div>"),
               ('<div class="fen-c" data-scene data-ui><div>x</div>', "</div>"))
        for ouvrant, fermant in cas:
            with self.subTest(ouvrant):
                h = f"<main>{ouvrant}<p>Un plugin MS Word natif.</p>{fermant}<p>Puis un plugin Microsoft Word.</p></main>"
                r = lien_plugin_word.traiter(h, "corrext/")
                self.assertEqual(r.count(self.LIEN), 1)
                self.assertIn("<p>Puis un " + self.LIEN + "plugin Microsoft Word</a>.</p>", r)
        # un élément vide marqué aria-hidden n'ouvre pas de sous-arbre exclu
        h = '<main><img aria-hidden="true" alt=""><p>Un plugin Microsoft Word.</p></main>'
        self.assertIn("<p>Un " + self.LIEN + "plugin Microsoft Word</a>.</p>", lien_plugin_word.traiter(h, "corrext/"))

    def test_complement_corrext_relie_sur_la_page_de_l_editeur(self):
        h = ('<main><p>Ouvrez-le dans Word avec le complément Corrext : le panneau.</p>'
             '<p>Relisez-le avec le complément Corrext, puis réimportez-le.</p></main>')
        r = lien_plugin_word.traiter(h, "corrext/editeur-de-relecture/")
        self.assertEqual(r.count(self.LIEN), 1)
        self.assertIn("avec le " + self.LIEN + "complément Corrext</a> : le panneau.", r)
        self.assertEqual(sans_balises(r), sans_balises(h))
        # la formulation n'est reliée que sur la page de l'éditeur de relecture
        self.assertEqual(lien_plugin_word.traiter(h, "aide/editeur-de-relecture/"), h)

    def test_page_du_plugin_page_sans_mention_et_idempotence(self):
        h = '<main><p>Un plugin MS Word natif.</p><p>Un plugin Microsoft Word.</p></main>'
        self.assertEqual(lien_plugin_word.traiter(h, "corrext/plugin-word/"), h)
        self.assertEqual(lien_plugin_word.traiter("<main><p>Rien.</p></main>", "x/"), "<main><p>Rien.</p></main>")
        # une page qui relie déjà la page du plugin (ici après un premier passage) n'est plus modifiée
        une = lien_plugin_word.traiter(h, "corrext/")
        self.assertEqual(une.count("corrext/plugin-word/"), 1)
        self.assertEqual(lien_plugin_word.traiter(une, "corrext/"), une)
        self.assertEqual(lien_plugin_word.traiter("<p>Sans main : plugin MS Word natif.</p>", "x/"),
                         "<p>Sans main : plugin MS Word natif.</p>")


if __name__ == "__main__":
    unittest.main()
