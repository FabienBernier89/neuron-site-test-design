"""Trame problème, situation visée, preuve, appel à l'action (lot D, spec V2 § 7) : accueil et 6 pages secteur.

Ordre attendu : hero, problème (tr-pb), situation visée (« Ce que Corrext change », existante), preuves (tr-pv),
exemple de cas d'usage, FAQ, appel à l'action. L'accueil place la souveraineté des données juste après le problème
(décision de Fabien du 2026-10-15) et intègre le schéma « qui fait quoi » du lot B après la plateforme. Les appels à l'action des pages secteur portent le secteur et l'attribut de suivi du lot C."""
import html as H
import json
import re
import subprocess
import sys
import unittest
from pathlib import Path

ICI = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ICI))
import build  # noqa: E402
from outils import contenus  # noqa: E402

SECTEURS = ["cabinets-avocats", "banques-finance", "directions-juridiques", "fiduciaires-conseil", "autorites-administration", "editeurs-legaltech"]
# Pages métier passées au nouveau modèle (Fabien, 2026-10-19, tests/test_metier.py) : hors de la trame du lot D, sauf
# les appels à l'action (secteur et suivi), vérifiés ici pour toutes les pages secteur
MODELE_METIER = ["cabinets-avocats", "banques-finance", "directions-juridiques", "fiduciaires-conseil", "autorites-administration", "editeurs-legaltech"]
SECTEURS_TOUS = SECTEURS
SECTEURS = [s for s in SECTEURS if s not in MODELE_METIER]
PAGES = [""] + [f"solutions/{s}/" for s in SECTEURS]
JSON_D = ICI / "src/data/contenus-v2/D-trame.json"
CSS = ICI / "assets/composants/trame.css"
# Preuves admises (spec V2 § 7, décision du contrôleur du 2026-10-14) : nom affiché attendu dans le bloc
PREUVES = {"iso": "ISO 27001", "infomaniak": "Infomaniak", "innosuisse": "Innosuisse", "segments": "15 millions",
           "sfa": "Swiss FinTech Awards 2024", "dshap": "Digital Shapers 2023", "kickstart": "Kickstart Innovation 2024"}
# Distinctions présentes sur le site mais hors de la liste admise : jamais dans le bloc preuves (BILANZ y figure
# seulement comme organisateur de Digital Shapers, selon le registre du site actuel)
HORS_LISTE = ("Entreprises les plus innovantes", "13e rang", "UBS", "Forum des 100", "Le Temps")
# Sections existantes de l'accueil, toutes gardées (titres ou textes repérables) ; le bloc d'usage « pilotée par vos
# juristes » est supprimé (Fabien, 2026-10-16)
ACCUEIL_EXISTANT = ["Adopté par les professionnels du droit et de la finance suisses", "15 M+",
                    "Toute votre traduction juridique, sur une",
                    "Un moteur, une plateforme, un concordancier", "Quatre niveaux de qualité",
                    "Ces solutions traduisent.", "Vos documents les plus sensibles", "Tout ce qu'il faut savoir",
                    "Prêt à voir Neur.on"]


DISCRETION = "ne publie ni nom de client ni témoignage"


def mots(t):
    return re.findall(r"[0-9a-zà-ÿœ]+", texte_brut(t).lower().replace("’", "'"))


def suites(t, n=5):
    """Suites de n mots consécutifs d'un fragment HTML (repérage des redites)."""
    m = mots(t)
    return {" ".join(m[i:i + n]) for i in range(len(m) - n + 1)}


def cle_page(p):
    return "accueil" if p == "" else p.split("/")[1]


def texte_brut(h):
    return re.sub(r"\s+", " ", H.unescape(re.sub(r"<[^>]+>", " ", h))).strip()


def sections(h):
    """Sections de <main>, dans l'ordre : (première classe utile, HTML)."""
    main = h[h.index('<main id="main">'):h.index("</main>")]
    res = []
    for s in re.findall(r"<section\b[^>]*>.*?</section>", main, re.S):
        cl = re.match(r'<section class="([^"]*)"', s).group(1).split()
        nom = cl[1] if cl[0] == "sec" and len(cl) > 1 else cl[0]
        if 'class="wrap fq"' in s:
            nom = "faq"
        res.append((nom, s))
    return res


def h2_v1(p, classe):
    """Titre h2 d'une section du site actuel (page FR publiée)."""
    t = (build.NEURON / "docs/fr" / p / "index.html").read_text(encoding="utf-8")
    sec = re.search(rf'<section class="{classe}[ "].*?</section>', t, re.S).group(0)
    return texte_brut(re.search(r"<h2[^>]*>(.*?)</h2>", sec, re.S).group(1))


class TestTrame(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        subprocess.run([sys.executable, str(ICI / "build.py")], check=True, cwd=ICI, stdout=subprocess.DEVNULL)
        cls.h = {p: build.chemin_page(p).read_text(encoding="utf-8") for p in PAGES + [f"solutions/{s}/" for s in MODELE_METIER]}

    # Test du plan (tâche D, étape 1)
    def ordre(self, h):
        return [c for c in re.findall(r'<section class="sec ([a-z-]+)', h) if c in ("tr-pb", "tr-pv", "cta")]

    def test_ordre_accueil_et_secteurs(self):
        for p in PAGES:
            h = build.chemin_page(p).read_text(encoding="utf-8")
            self.assertEqual(self.ordre(h)[0], "tr-pb", p)
            self.assertLess(self.ordre(h).index("tr-pv"), self.ordre(h).index("cta"), p)
        for s in SECTEURS:
            h = build.chemin_page(f"solutions/{s}/").read_text(encoding="utf-8")
            self.assertIn(f"secteur={s}", h)

    def test_schema_sur_l_accueil(self):
        self.assertEqual(build.chemin_page("").read_text(encoding="utf-8").count('class="sec sp"'), 1)

    # Ordre complet de la trame
    def test_ordre_complet_des_pages_secteur(self):
        for s in SECTEURS:
            p = f"solutions/{s}/"
            noms = [n for n, _ in sections(self.h[p])]
            facts = h2_v1(p, "facts")  # situation visée : « Ce que Corrext change… » (existante)
            visee = next(i for i, (_, x) in enumerate(sections(self.h[p])) if facts in texte_brut(x))
            self.assertEqual(noms[0], "hero", p)
            # Problème juste après le hero (le bandeau des distinctions, rattaché au hero, peut s'intercaler)
            self.assertEqual([n for n in noms[1:noms.index("tr-pb")] if n != "dist"], [], p)
            self.assertLess(noms.index("tr-pb"), visee, p)
            self.assertLess(visee, noms.index("tr-pv"), p)
            self.assertLess(noms.index("tr-pv"), noms.index("temo"), p)  # exemple de cas d'usage, gardé
            self.assertLess(noms.index("temo"), noms.index("faq"), p)
            self.assertEqual(noms[-1], "cta", p)
            for n in ("tr-pb", "tr-pv", "temo", "faq", "cta"):
                self.assertEqual(noms.count(n), 1, (p, n))

    def test_ordre_et_sections_de_l_accueil(self):
        noms = [n for n, _ in sections(self.h[""])]
        self.assertEqual(noms[0], "hero")
        self.assertEqual([n for n in noms[1:noms.index("tr-pb")] if n != "dist"], [])
        self.assertLess(noms.index("tr-pv"), noms.index("faq"))
        self.assertEqual(noms[-1], "cta")
        # Restructuration validée par Fabien le 2026-10-16 : les trois axes (LexMachina, Corrext, CHnell) suivent
        # directement le problème, le schéma du lot B suit les axes, puis la souveraineté
        secs = sections(self.h[""])
        axes = next(i for i, (_, x) in enumerate(secs) if "Un moteur, une plateforme, un concordancier" in texte_brut(x))
        self.assertEqual(axes, noms.index("tr-pb") + 1)
        self.assertEqual(secs[axes + 1][0], "sp")
        souverainete = next(i for i, (_, x) in enumerate(secs) if "Vos documents les plus sensibles" in texte_brut(x))
        self.assertEqual(souverainete, axes + 2)
        self.assertEqual(texte_brut(secs[axes][1]).count("Toute votre traduction juridique, sur une seule plateforme"), 1)
        # Aucune section existante supprimée (texte de <main> seulement : le menu reprend certains titres)
        h = self.h[""]
        lu = texte_brut(h[h.index('<main id="main">'):h.index("</main>")])
        for x in ACCUEIL_EXISTANT:
            self.assertEqual(lu.count(x), 1, x)

    # Appels à l'action des pages secteur (lot C : ?secteur= et data-suivi)
    def test_appels_a_l_action_des_pages_secteur(self):
        for s in SECTEURS_TOUS:
            h = self.h[f"solutions/{s}/"]
            main = h[h.index('<main id="main">'):h.index("</main>")]
            boutons = re.findall(r'<a class="btn"[^>]*>', main)
            self.assertEqual(len(boutons), 2, s)  # hero et appel final
            for b in boutons:
                self.assertRegex(b, rf'href="(\.\./)+fr/contact/\?secteur={s}"', s)
            # Deux valeurs de suivi distinctes : bouton du hero, bouton de l'appel final
            secs = dict(sections(h))
            self.assertRegex(secs["hero"], rf'<a class="btn"[^>]*data-suivi="cta-secteur-{s}-hero"', s)
            self.assertRegex(secs["cta"], rf'<a class="btn"[^>]*data-suivi="cta-secteur-{s}-fin"', s)
            # le formulaire de contact connaît ce secteur
            contact = build.chemin_page("contact/").read_text(encoding="utf-8")
            self.assertIn(f'<option value="{s}">', contact)

    # Contenus
    def test_probleme_trois_difficultes_tirees_du_json(self):
        for p in PAGES:
            c = cle_page(p)
            pb = dict(sections(self.h[p]))["tr-pb"]
            self.assertEqual(texte_brut(re.search(r"<h2[^>]*>(.*?)</h2>", pb, re.S).group(1)), contenus.texte(f"trame.pb.{c}.titre"), p)
            items = re.findall(r"<li\b.*?</li>", pb, re.S)
            self.assertEqual(len(items), 3, p)
            for n, li in enumerate(items, 1):
                lu = texte_brut(li)
                for partie in ("label", "titre", "texte"):
                    self.assertIn(contenus.texte(f"trame.pb.{c}.{n}.{partie}"), lu, (p, n, partie))
                self.assertRegex(li, r"<h3[ >]", (p, n))

    def test_probleme_sans_redite_du_hero_ni_de_la_section_suivante(self):
        """Aucune suite de 5 mots du problème ne figure dans le hero ni dans la section qui le suit ; sur l'accueil,
        les trois axes (section suivante depuis le 2026-10-16) remplacent les piliers."""
        for p in PAGES:
            secs = sections(self.h[p])
            i = [n for n, _ in secs].index("tr-pb")
            voisins = [x for n, x in secs if n == "hero"] + [secs[i + 1][1]]
            communes = suites(secs[i][1]) & set().union(*(suites(x) for x in voisins))
            self.assertEqual(communes, set(), p or "accueil")

    def test_debuts_de_titres_varies(self):
        titres = [contenus.texte(f"trame.pb.{cle_page(p)}.{n}.titre") for p in PAGES for n in (1, 2, 3)]
        debuts = [x.split()[0] for x in titres]
        for mot in set(debuts):
            self.assertLessEqual(debuts.count(mot), 5, (mot, debuts.count(mot)))
        self.assertLessEqual(debuts.count("Des"), 2)

    def test_preuves_admises_sans_redite_du_bandeau(self):
        """Page avec bandeau des distinctions (sec dist) : le registre ne reprend aucun élément du bandeau et garde le
        reste (15 millions de segments, Kickstart Innovation 2024). Autres pages : les 7 preuves admises."""
        avec_bandeau = []
        for p in PAGES:
            secs = dict(sections(self.h[p]))
            pv = secs["tr-pv"]
            lu = texte_brut(pv)
            bandeau = texte_brut(secs.get("dist", "")).replace(chr(0xa0), " ")
            if bandeau:
                avec_bandeau.append(p)
                for b in re.findall(r"<li><b>(.*?)</b>", secs["dist"]):
                    self.assertNotIn(texte_brut(b).replace(chr(0xa0), " "), lu, p)
            attendus = [nom for nom in PREUVES.values() if nom.split(" 20")[0] not in bandeau]
            self.assertEqual(len(re.findall(r"<li\b", pv)), len(attendus), p)
            for nom in PREUVES.values():
                (self.assertIn if nom in attendus else self.assertNotIn)(nom, lu, p)
            for x in HORS_LISTE:
                self.assertNotIn(x, lu, p)
            self.assertNotRegex(pv, r"<img\b")  # aucun logo : aucune marque de distinction dans assets/img
        self.assertEqual(avec_bandeau, [""])
        for p in avec_bandeau:
            lu = texte_brut(dict(sections(self.h[p]))["tr-pv"])
            for nom in ("15 millions", "Kickstart Innovation 2024"):
                self.assertIn(nom, lu, p)

    def test_iso_et_infomaniak_pas_plus_de_trois_fois_sur_l_accueil(self):
        h = self.h[""]
        lu = texte_brut(h[h.index('<main id="main">'):h.index("</main>")]).replace(chr(0xa0), " ")
        for x in ("ISO 27001", "Infomaniak"):
            self.assertLessEqual(lu.count(x), 3, x)

    def test_discretion_seulement_sans_exemple_de_cas_d_usage(self):
        """« ne publie ni nom de client ni témoignage » : jamais sur une page qui montre un exemple de cas d'usage."""
        for p in PAGES:
            h = self.h[p]
            main = texte_brut(h[h.index('<main id="main">'):h.index("</main>")])
            if "Exemple de cas d'usage" in main:
                self.assertNotIn(DISCRETION, main, p)
        self.assertIn(DISCRETION, texte_brut(dict(sections(self.h[""]))["tr-pv"]))  # accueil : aucun exemple

    def test_json_du_lot(self):
        f = json.loads(JSON_D.read_text(encoding="utf-8"))
        self.assertEqual(f["lot"], "D")
        par_cle = {e["cle"]: e for e in f["entrees"]}
        for e in f["entrees"]:
            self.assertIn(e["statut"], ("a_relire", "valide"), e["cle"])  # validés par Fabien le 2026-10-23
            self.assertTrue(e["source"].strip(), e["cle"])
            self.assertTrue(e["cle"].startswith("trame."), e["cle"])
        for p in PAGES:
            c = cle_page(p)
            for cle in [f"trame.pb.{c}.titre"] + [f"trame.pb.{c}.{n}.{x}" for n in (1, 2, 3) for x in ("label", "titre", "texte")]:
                self.assertEqual(par_cle[cle]["page"], p, cle)
        for i in PREUVES:
            for x in ("nom", "detail", "type"):
                e = par_cle[f"trame.pv.{i}.{x}"]
                self.assertEqual(e["page"], "*", e["cle"])
            # Chaque preuve porte sa source : page du site actuel ou base de connaissances
            self.assertRegex(par_cle[f"trame.pv.{i}.nom"]["source"], r"V1 |base de connaissances", i)
        for cle in ("trame.pv.titre", "trame.pv.intro", "trame.pv.discretion", "trame.pv.note"):
            self.assertIn(cle, par_cle)

    def test_lien_plugin_word_dans_le_schema(self):
        for p in ("", "corrext/"):
            h = build.chemin_page(p).read_text(encoding="utf-8")
            sp = re.search(r'<section class="sec sp".*?</section>', h, re.S).group(0)
            d = re.search(r'<div class="sp-n sp-cx">.*?<dd class="sp-d">(.*?)</dd>', sp, re.S).group(1)
            self.assertRegex(d, r'^[^<]*<a class="pw-lien" href="(\.\./)+fr/corrext/plugin-word/">plugin Word</a>[^<]*$', p)
            self.assertEqual(texte_brut(d), contenus.texte("schema.corrext.def"), p)  # texte inchangé


class TestStyles(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.css = CSS.read_text(encoding="utf-8")

    def test_jetons_du_site(self):
        # Couleurs par les jetons de site.css (thème sombre compris), aucune couleur codée en dur
        self.assertNotRegex(self.css, r"#[0-9a-fA-F]{3,6}\b")
        self.assertIn("var(--line)", self.css)

    def test_textes_d_au_moins_11_px(self):
        for taille in re.findall(r"font:[^;}]*?([\d.]+)px", self.css) + re.findall(r"font-size:([\d.]+)px", self.css):
            self.assertGreaterEqual(float(taille), 11, taille)

    def test_une_colonne_sur_mobile(self):
        mobile = re.search(r"@media \(max-width:(\d+)px\)\{(.*)\}\s*$", self.css, re.S)
        self.assertIsNotNone(mobile)
        self.assertGreaterEqual(int(mobile.group(1)), 767)
        for bloc in (".tr-pb-l", ".tr-pv-g"):
            self.assertRegex(mobile.group(2), re.escape(bloc) + r"[^{]*\{[^}]*grid-template-columns:minmax\(0,1fr\)")

    def test_mouvement_en_transform_et_opacity(self):
        for decl in re.findall(r"transition:([^;}]+)", self.css):
            for partie in decl.split(","):
                self.assertIn(partie.split()[0], {"transform", "opacity", "none"}, decl)


if __name__ == "__main__":
    unittest.main()
