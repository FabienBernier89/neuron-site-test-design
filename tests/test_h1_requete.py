"""H1 orientés requête et titles différenciés (lot Y, décision de Fabien du 2026-10-23, point 11 de l'audit).

Les 24 pages Solutions et Traduction du tableau de docs/audits/2026-10-23-neuron-v2/propositions-a-valider.md § 1 :
la 1re ligne du H1 prend la proposition validée, l'accroche reste. Cannibalisations (option sans suppression ni
redirection) : les deux pages banques et les trois billets des Swiss FinTech Awards 2024 ont des titles distincts."""
import json
import re
import subprocess
import sys
import unittest
from pathlib import Path

ICI = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ICI))
import build  # noqa: E402

# Tableau validé : page, 1re ligne d'origine, proposition (1re ligne), accroche conservée (2e ligne)
TABLEAU = [
    ("solutions/cabinets-avocats/", "Cabinets d'avocats.", "Traduction juridique pour cabinets d'avocats.", "Traduire un dossier sans jamais le sortir de Suisse"),
    ("solutions/banques-finance/", "Banques et finance.", "Traduction juridique et financière pour les banques.", "Le vocabulaire prudentiel, traité en Suisse"),
    ("solutions/directions-juridiques/", "Directions juridiques et Legal Ops.", "Traduction juridique pour directions juridiques et Legal Ops.", "Une traduction mesurable"),
    ("solutions/autorites-administration/", "Autorités et administration.", "Traduction juridique pour autorités et administrations.", "Rien ne quitte la Suisse"),
    ("solutions/fiduciaires-conseil/", "Fiduciaires et conseil.", "Traduction pour fiduciaires et conseil.", "Documents d'entreprise traduits et certifiés"),
    ("solutions/editeurs-legaltech/", "LegalTechs et éditeurs juridiques.", "Moteur de traduction juridique pour LegalTechs et éditeurs.", "Notre moteur dans votre produit"),
    ("traduction/allemand-francais/", "Allemand vers français.", "Traduction juridique allemand-français.", "Le droit suisse d'une rive à l'autre"),
    ("traduction/francais-allemand/", "Français vers allemand.", "Traduction juridique français-allemand.", "Écrire pour un lecteur alémanique"),
    ("traduction/allemand-anglais/", "Allemand vers anglais.", "Traduction juridique allemand-anglais.", "Rendre le droit suisse intelligible"),
    ("traduction/anglais-allemand/", "Anglais vers allemand.", "Traduction juridique anglais-allemand.", "Ramener le contrat au droit suisse"),
    ("traduction/francais-anglais/", "Français vers anglais.", "Traduction juridique français-anglais.", "Le dossier romand à l'international"),
    ("traduction/italien-francais/", "Italien vers français.", "Traduction juridique italien-français.", "La troisième langue officielle, à part entière"),
    ("traduction/contrats/", "Contrats.", "Traduction de contrats.", "Le Code des obligations, d'une langue à l'autre"),
    ("traduction/assurance/", "Assurance.", "Traduction juridique en assurance.", "Des conditions générales aux dossiers de sinistre"),
    ("traduction/banque-finance/", "Banque et finance.", "Traduction bancaire et financière.", "Du contrat de crédit au prospectus"),
    ("traduction/compliance-finma/", "Compliance et FINMA.", "Traduction compliance et FINMA.", "Écrire dans la langue de l'autorité"),
    ("traduction/contentieux-arbitrage/", "Contentieux et arbitrage.", "Traduction en contentieux et arbitrage.", "Ce que lira un juge ou un arbitre"),
    ("traduction/droit-des-societes/", "Droit des sociétés.", "Traduction en droit des sociétés.", "Statuts et procès-verbaux traduits"),
    ("traduction/droit-du-travail/", "Droit du travail.", "Traduction en droit du travail.", "Du contrat d'embauche au certificat de travail"),
    ("traduction/droit-penal/", "Droit pénal.", "Traduction en droit pénal.", "Les actes d'une procédure pénale, d'une langue à l'autre"),
    ("traduction/fiscalite/", "Fiscalité.", "Traduction fiscale.", "Trois niveaux d'impôt, trois langues officielles"),
    ("traduction/fusions-acquisitions/", "Fusions et acquisitions.", "Traduction en fusions et acquisitions.", "Lire la data room avant le closing"),
    ("traduction/propriete-intellectuelle/", "Propriété intellectuelle.", "Traduction en propriété intellectuelle.", "Des titres opposables à un tiers"),
    ("traduction/rapports-annuels-financiers/", "Rapports annuels.", "Traduction de rapports annuels.", "La clôture en quatre langues, à date fixe"),
]
BANQUES = ["solutions/banques-finance/", "traduction/banque-finance/"]
FINTECH = ["ressources/blog/neuron-top-10-startups-fintech-suisses-2024/",
           "ressources/blog/neuron-quatre-finalistes-swiss-fintech-awards-2024/",
           "ressources/blog/neuron-finaliste-early-stage-swiss-fintech-awards-2024/"]
# H1 des billets : inchangés (seuls title et og:title différencient les billets)
H1_FINTECH = ["Neur.on dans le Top 10 des start-up fintech suisses des Swiss FinTech Awards 2024",
              "Neur.on parmi les 4 finalistes des Swiss FinTech Awards 2024",
              "Neur.on finaliste des Swiss FinTech Awards 2024 dans la catégorie Early Stage"]
H1 = re.compile(r'<h1 class="h1"><span class="n">(.*?)</span> <span class="s">(.*?)</span></h1>')


def lire(page):
    return build.chemin_page(page).read_text(encoding="utf-8")


def title(h):
    return re.search(r"<title>(.*?)</title>", h, re.S).group(1)


def og(h):
    return re.search(r'<meta property="og:title" content="([^"]*)">', h).group(1)


def mots(t):
    return set(re.findall(r"\w+", t.lower().replace("neur.on", ""))) - {"swiss", "fintech", "awards", "2024", "de", "et", "la", "les", "des", "pour", "sur"}


class TestH1Requete(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        subprocess.run([sys.executable, str(ICI / "build.py")], check=True, cwd=ICI, stdout=subprocess.DEVNULL)
        cls.pages = {p: lire(p) for p, *_ in TABLEAU}
        cls.lot = json.loads((ICI / "src/data/contenus-v2/Y-h1-requete.json").read_text(encoding="utf-8"))

    def test_vingt_quatre_pages(self):
        self.assertEqual(len(TABLEAU), 24)
        self.assertEqual(len({p for p, *_ in TABLEAU}), 24)

    def test_h1_commence_par_la_proposition_et_garde_son_accroche(self):
        for p, ancien, proposition, accroche in TABLEAU:
            h = self.pages[p]
            self.assertEqual(len(re.findall(r"<h1\b", h)), 1, p)
            m = H1.search(h)
            self.assertIsNotNone(m, p)
            self.assertEqual(m.group(1).replace("&amp;", "&"), proposition, p)
            self.assertEqual(m.group(2), accroche, p)
            self.assertNotIn(f'<span class="n">{ancien}</span>', h, p)

    def test_requete_dans_le_h1(self):
        for p, _a, proposition, _s in TABLEAU:
            self.assertIn("traduction", proposition.lower(), p)

    def test_seul_le_h1_change(self):
        """L'ancienne 1re ligne reste partout ailleurs (menu, fil d'Ariane, cartes) : aucune substitution sur la page."""
        from outils.post import titres_requete
        page = ('<nav><a href="#">Contrats.</a></nav><h1 class="h1"><span class="n">Contrats.</span> '
                '<span class="s">Le Code des obligations, d\'une langue à l\'autre</span></h1><h3>Contrats.</h3>'
                '<title>X</title>')
        sortie = titres_requete.traiter(page, "traduction/contrats/")
        self.assertEqual(sortie, page.replace('<span class="n">Contrats.</span>', '<span class="n">Traduction de contrats.</span>'))
        self.assertEqual(sortie.count("Contrats."), 2)  # menu et carte intacts
        with self.assertRaises(ValueError):  # 1re ligne d'origine disparue : le build échoue au lieu d'ignorer
            titres_requete.traiter("<h1>Autre</h1>", "traduction/contrats/")
        self.assertEqual(titres_requete.traiter(page, "corrext/"), page)  # page hors du lot : intacte

    def test_lot_y_aligne_sur_le_tableau(self):
        h1 = {e["page"]: e for e in self.lot["entrees"] if e["cle"].endswith(".h1-requete")}
        self.assertEqual(sorted(h1), sorted(p for p, *_ in TABLEAU))
        for p, ancien, proposition, _s in TABLEAU:
            self.assertEqual(h1[p]["texte"], proposition, p)
            self.assertEqual(h1[p]["ancien"], ancien, p)
            self.assertEqual(h1[p]["statut"], "valide", p)
            self.assertIn("Décision de Fabien du 2026-10-23 (point 11)", h1[p]["source"], p)

    def test_titles_des_pages_banques_distincts(self):
        a, b = (lire(p) for p in BANQUES)
        self.assertNotEqual(title(a), title(b))
        # plus de quasi-doublon : au plus 2 mots en commun hors « traduction » et marque
        self.assertLessEqual(len((mots(title(a)) & mots(title(b))) - {"traduction"}), 1)
        for h in (a, b):
            self.assertLessEqual(len(title(h)), 60)
            self.assertTrue(title(h).endswith(" · Neur.on"))
            self.assertEqual(og(h), title(h))
        self.assertIn("banques", title(a))
        self.assertIn("Traduction bancaire et financière", title(b))  # cohérent avec le nouveau H1

    def test_titles_des_billets_fintech_distincts(self):
        hs = [lire(p) for p in FINTECH]
        titres = [title(h) for h in hs]
        self.assertEqual(len(set(titres)), 3, titres)
        self.assertEqual(len({og(h) for h in hs}), 3)
        for i, t in enumerate(titres):
            self.assertLessEqual(len(t), 60, t)
            for j in range(i + 1, 3):  # chaque billet a son angle propre
                self.assertTrue(mots(t) - mots(titres[j]) and mots(titres[j]) - mots(t), (t, titres[j]))
        self.assertNotIn("finaliste", titres[1] + titres[2])  # les deux titles quasi identiques ont changé d'angle

    def test_billets_fintech_gardent_h1_et_headline(self):
        for p, h1 in zip(FINTECH, H1_FINTECH):
            h = lire(p)
            self.assertIn(f"<h1>{h1}</h1>", h, p)
            self.assertIn('"headline": ' + json.dumps(h1, ensure_ascii=False), h, p)

    def test_urls_inchangees(self):
        for p in [x[0] for x in TABLEAU] + FINTECH:
            self.assertIn(f'<link rel="canonical" href="https://neur-on.ai/fr/{p}">', lire(p), p)

    def test_aucun_tiret_interdit(self):
        texte = (ICI / "src/data/contenus-v2/Y-h1-requete.json").read_text(encoding="utf-8")
        self.assertNotIn(chr(0x2014), texte)
        self.assertNotIn(chr(0x2013), texte)


if __name__ == "__main__":
    unittest.main()
