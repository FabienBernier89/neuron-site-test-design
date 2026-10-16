"""Lot E : titres de blog et de guides orientés problème, liste du blog en deux sections, encart newsletter
(spec V2 § 8, brief du lot E)."""
import html as H
import json
import re
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

ICI = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ICI))
import build  # noqa: E402
from outils import contenus  # noqa: E402
from outils.composer import newsletter  # noqa: E402
from tests import support  # noqa: E402

BILLETS = ["ressources/blog/comprendre-devis-traduction-juridique/", "ressources/blog/secret-professionnel-outils-traduction/",
           "ressources/blog/traduire-contrat-droit-suisse/"]
GUIDES = sorted(f"ressources/guides/{d.name}/" for d in (ICI / "src/pages/ressources/guides").iterdir() if (d / "index.html").is_file())
ENCART = re.compile(r'<section class="nl-s".*?</section>', re.S)


def lire(page):
    return build.chemin_page(page).read_text(encoding="utf-8")


def titres():
    """Entrées de titre d'E-blog.json : {page: {"h1": texte, "title": texte, "og": texte, "ancien": texte}}."""
    r = {}
    for e in contenus.toutes():
        m = re.fullmatch(r"(.+)\.(h1|title|og)", e["cle"])
        if e["lot"] == "E" and m and e["page"].startswith("ressources/") and e["page"] != "ressources/blog/":
            r.setdefault(e["page"], {})[m.group(2)] = e["texte"]
            if m.group(2) == "h1":
                r[e["page"]]["ancien"] = e["ancien"]
    return r


def h1_texte(h):
    return H.unescape(re.sub(r"<[^>]+>", "", re.search(r"<h1[^>]*>(.*?)</h1>", h, re.S).group(1)))


class TestTitres(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        subprocess.run([sys.executable, str(ICI / "build.py")], check=True, cwd=ICI, stdout=subprocess.DEVNULL)
        cls.t = titres()

    def test_tous_les_billets_et_guides_sont_retitres(self):
        # Le plan parlait de 6 guides : le site Neur.on n'en publie que 2 (la liste se lit sur le disque)
        self.assertEqual(sorted(self.t), sorted(BILLETS + GUIDES))
        self.assertEqual(len(GUIDES), 2)
        for p, x in self.t.items():
            self.assertEqual(sorted(x), ["ancien", "h1", "og", "title"], p)

    def test_h1_title_og_et_headline_alignes(self):
        for p, x in self.t.items():
            h = lire(p)
            # billet : le H1 est le titre ; guide : le titre suit le repère « Guide. »
            self.assertEqual(h1_texte(h).strip().removeprefix("Guide. "), x["h1"], p)
            self.assertEqual(len(re.findall(r"<h1\b", h)), 1, p)
            self.assertIn(f"<title>{x['title']}</title>", h, p)
            self.assertIn(f'<meta property="og:title" content="{x["og"]}">', h, p)
            self.assertIn('"headline": ' + json.dumps(x["h1"], ensure_ascii=False), h, p)

    def test_title_60_caracteres_au_plus_avec_le_suffixe(self):
        for p, x in self.t.items():
            self.assertLessEqual(len(x["title"]), 60, p)
            self.assertTrue(x["title"].endswith(" · Neur.on"), p)
            self.assertTrue(x["og"].endswith(" · Neur.on"), p)
            self.assertLessEqual(len(x["og"]), 72, p)  # au-delà, les réseaux coupent le titre

    def test_titre_nouveau_et_mot_cle_conserve(self):
        for p, x in self.t.items():
            self.assertNotEqual(x["h1"], x["ancien"], p)
        self.assertIn("devis", self.t[BILLETS[0]]["h1"].lower())
        self.assertIn("secret professionnel", self.t[BILLETS[1]]["h1"].lower())
        self.assertIn("contrat en droit suisse", self.t[BILLETS[2]]["h1"].lower())
        self.assertIn("traduction juridique dans un cabinet", self.t["ressources/guides/organiser-traduction-cabinet/"]["h1"])
        self.assertIn("rapport annuel multilingue", self.t["ressources/guides/rapport-annuel-multilingue/"]["h1"].lower())

    def test_guides_gardent_leur_repere_guide(self):
        for p in GUIDES:
            self.assertIn('<span class="n">Guide.</span>', lire(p), p)

    def test_urls_inchangees(self):
        for p in self.t:
            self.assertTrue(build.chemin_page(p).is_file(), p)
            self.assertIn(f'<link rel="canonical" href="https://neur-on.ai/fr/{p}">', lire(p), p)

    def test_ancien_titre_absent_des_titres_et_cartes(self):
        """Ni dans un titre de page, ni dans la carte qui renvoie vers l'article, ni dans le JSON-LD."""
        for p in build.PAGES:
            h = lire(p)
            for q, x in self.t.items():
                a = re.escape(x["ancien"])
                self.assertIsNone(re.search(r"<h[1-3][^>]*>" + a + r"</h[1-3]>", h), f"{p} : titre d'origine de {q} dans un titre ou une carte")
                self.assertNotIn(f'<span class="s">{x["ancien"]}</span>', h, f"{p} : titre d'origine de {q} dans un H1 de guide")
                self.assertNotIn('"headline": ' + json.dumps(x["ancien"], ensure_ascii=False), h, f"{p} : headline d'origine de {q}")

    def test_cartes_et_liste_json_ld_portent_le_nouveau_titre(self):
        liste = lire("ressources/blog/")
        for p in BILLETS:
            self.assertIn(f"<h3>{self.t[p]['h1']}</h3>", liste, p)
            self.assertIn('"headline": ' + json.dumps(self.t[p]["h1"], ensure_ascii=False) + ', "datePublished"', liste, p)
        # « Les derniers articles » d'un billet : les cartes des deux autres billets
        autre = lire(BILLETS[2])
        for p in BILLETS[:2]:
            self.assertIn(f"<h3>{self.t[p]['h1']}</h3>", autre, p)

    def test_hub_des_guides_relie_et_titre_chaque_guide(self):
        hub = lire("ressources/guides/")
        # Cartes illustrées depuis le 2026-10-16 (outils/post/fonctionnalites.py) : le titre est un <b class="fx-t">
        for p in GUIDES:
            self.assertIn(f'<b class="fx-t">{self.t[p]["h1"]}</b>', hub, p)
            carte = re.search(r'<a class="fx" href="../../../fr/' + re.escape(p) + r'">.*?</a>', hub, re.S)
            self.assertIsNotNone(carte, f"{p} : carte du hub non reliée")
            self.assertIn(f'<b class="fx-t">{self.t[p]["h1"]}</b>', carte.group(0), f"{p} : titre absent de sa carte")

    def test_titres_nouveaux_a_relire_avec_source(self):
        for e in contenus.toutes():
            if e["lot"] == "E":
                self.assertEqual(e["statut"], "a_relire", e["cle"])
                self.assertTrue(e["source"].strip(), e["cle"])
                if e["cle"].endswith(".h1"):
                    self.assertIn("titre d'origine : " + e["ancien"], e["source"], e["cle"])


class TestListeDuBlog(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        subprocess.run([sys.executable, str(ICI / "build.py")], check=True, cwd=ICI, stdout=subprocess.DEVNULL)
        cls.h = lire("ressources/blog/")
        cls.main = cls.h[cls.h.index("<main"):cls.h.index("</main>")]

    def test_guides_puis_actualites(self):
        g, a = self.main.index(">Guides</h2>"), self.main.index(">Actualités</h2>")
        self.assertLess(g, a)
        self.assertEqual(len(re.findall(r"<h2\b", self.main)), 3)  # Guides, Actualités, appel final
        entre = self.main[g:a]
        for p in BILLETS:
            self.assertIn(f'href="../../../fr/{p}"', entre, p)
        self.assertIn('href="../../../fr/ressources/guides/"', entre)

    def test_actualites_apres_les_guides_et_sans_billet(self):
        apres = self.main[self.main.index(">Actualités</h2>"):]
        for p in BILLETS:
            self.assertNotIn(f'href="../../../fr/{p}"', apres, p)
        self.assertGreaterEqual(len(re.findall(r'<a class="bl-c"', apres)), 30)
        self.assertIn("Toutes les brèves de Neur.on, année par année", apres)
        self.assertIn("Suivre Neur.on sur LinkedIn", apres)

    def test_aucune_carte_perdue(self):
        v1 = (build.NEURON / "docs/fr/ressources/blog/index.html").read_text(encoding="utf-8")
        attendues = set(re.findall(r'<a class="bl-card" href="[^"]*/blog/([^/"]+)/"', v1)) | set(
            re.findall(r'<a class="bl-feat-card" href="[^"]*/blog/([^/"]+)/"', v1))
        presentes = set(re.findall(r'<a class="bl-[cf]" href="[^"]*/blog/([^/"]+)/"', self.main))
        self.assertEqual(attendues, presentes)

    def test_textes_de_section_dans_les_contenus_nouveaux(self):
        for cle in ("ressources/blog.guides.titre", "ressources/blog.guides.intro", "ressources/blog.guides.lien",
                    "ressources/blog.actualites.titre", "ressources/blog.actualites.intro"):
            self.assertIn(contenus.texte(cle), H.unescape(self.main), cle)


class TestEncartNewsletter(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        subprocess.run([sys.executable, str(ICI / "build.py")], check=True, cwd=ICI, stdout=subprocess.DEVNULL)

    def test_encart_est_un_formulaire_envoi_php_post(self):
        e = newsletter.encart()
        self.assertIsInstance(e, str)
        self.assertRegex(e, r'<form[^>]*\baction="/envoi\.php"')
        self.assertRegex(e, r'<form[^>]*\bmethod="post"')
        self.assertNotIn("{{ROOT}}envoi", e)

    def test_champs_attendus_par_envoi_php(self):
        e = newsletter.encart()
        self.assertIn('<input type="hidden" name="type" value="newsletter">', e)
        self.assertRegex(e, r'<input type="hidden" name="t0"')
        piege = re.search(r'<input[^>]*name="site_url"[^>]*>', e).group(0)
        for attr in ('tabindex="-1"', 'autocomplete="off"', 'aria-hidden="true"'):
            self.assertIn(attr, piege)
        self.assertRegex(e, r'<input[^>]*type="email"[^>]*name="email"[^>]*\brequired\b|<input[^>]*name="email"[^>]*type="email"[^>]*\brequired\b')
        case = re.search(r'<input[^>]*type="checkbox"[^>]*>', e).group(0)
        self.assertIn("required", case)
        self.assertIn('name="consentement"', case)
        self.assertIn('href="{{ROOT}}fr/protection-des-donnees/"', e)

    def test_piege_masque_aux_utilisateurs_et_aux_lecteurs_d_ecran(self):
        e = newsletter.encart()
        self.assertRegex(e, r'<div class="nl-piege" aria-hidden="true">.*?name="site_url".*?</div>')
        css = (ICI / "assets/composants/newsletter.css").read_text(encoding="utf-8")
        self.assertRegex(css, r"\.nl-piege\s*\{[^}]*position:\s*absolute[^}]*left:\s*-\d+")

    def test_demo_selon_la_configuration_sans_la_modifier(self):
        avant = (ICI / "src/data/config.json").read_bytes()
        self.assertIn("data-demo", newsletter.encart({"apercu": True}))
        self.assertNotIn("data-demo", newsletter.encart({"apercu": False}))
        # sans réglage donné : celui du dépôt, aperçu ou production
        self.assertEqual("data-demo" in newsletter.encart(), newsletter.en_apercu())
        self.assertEqual((ICI / "src/data/config.json").read_bytes(), avant)

    def test_encart_sur_la_liste_les_billets_les_guides_et_les_autres_pages(self):
        pages = ["ressources/blog/", "ressources/guides/"] + BILLETS + GUIDES + ["", "corrext/", "solutions/cabinets-avocats/", "ressources/blog/actualites/"]
        for p in pages:
            h = lire(p)
            self.assertEqual(h.count('name="type" value="newsletter"'), 1, p)
            self.assertEqual(len(ENCART.findall(h)), 1, p)
            self.assertIn('action="/envoi.php"', h, p)

    def test_encart_juste_avant_le_pied_de_page(self):
        for p in ("ressources/blog/", BILLETS[2], GUIDES[0], "", "corrext/"):
            h = lire(p)
            fin = ENCART.search(h).end()
            self.assertIn(h[fin:h.index('<footer class="pied">')].strip(), ("", "</main>"), p)

    def test_pas_d_encart_sur_la_page_de_contact_ni_la_404(self):
        self.assertNotIn("nl-s", lire("contact/"))
        self.assertNotIn("nl-s", (build.DOCS / "404.html").read_text(encoding="utf-8"))

    def test_formulaire_actif_hors_apercu(self):
        with tempfile.TemporaryDirectory() as tmp:
            sortie = support.construire(tmp, pages=("", "ressources/blog/"), config={"apercu": False})
            for p in ("", "ressources/blog/"):
                h = (sortie / "fr" / p / "index.html").read_text(encoding="utf-8")
                self.assertEqual(h.count('name="type" value="newsletter"'), 1, p)
                self.assertNotIn("data-demo", ENCART.search(h).group(0), p)

    def test_textes_de_l_encart_dans_les_contenus_nouveaux(self):
        e = H.unescape(re.sub(r"<[^>]+>", "", newsletter.encart()))
        for cle in ("newsletter.titre", "newsletter.texte", "newsletter.email", "newsletter.bouton", "newsletter.consentement", "newsletter.piege"):
            self.assertIn(contenus.texte(cle), e, cle)

    def test_pied_de_page_intact(self):
        h = lire("ressources/blog/")
        pied = h[h.index('<footer class="pied">'):]
        self.assertNotIn("nl-", pied)


class TestSujetsHorsDuDepot(unittest.TestCase):
    def test_sujets_de_guides_hors_du_depot_public(self):
        """Les sujets de guides (références légales non vérifiées) vivent hors du dépôt public, dans la bibliothèque
        privée de Fabien ; le dépôt les ignore s'ils y reviennent."""
        self.assertFalse((ICI / "SUJETS-GUIDES.md").exists())
        self.assertIn("SUJETS-GUIDES.md", (ICI / ".gitignore").read_text(encoding="utf-8").splitlines())


if __name__ == "__main__":
    unittest.main()
