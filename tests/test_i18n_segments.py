"""Extracteur de segments de la V2 (outils/i18n/segments.py) : découpe de la page FR assemblée, exclusions,
classement des attributs, réinjection. Le test d'exhaustivité (« aucun texte à traduire n'échappe à l'extraction »,
condition de Fabien) lit la sortie FR complète construite par build.py."""
import functools
import html as H
import importlib.util
import json
import re
import unittest
from collections import Counter
from pathlib import Path

import build
from tests import support
from outils.i18n import controles
from outils.i18n import segments as S

FIXTURE = Path(__file__).resolve().parent / "fixtures" / "i18n" / "page-fr-assemblee.html"
PAGE = FIXTURE.read_text(encoding="utf-8")


@functools.lru_cache(maxsize=None)
def pages_du_site():
    """(chemin relatif, HTML) de chaque page de la sortie FR complète : lues une fois pour tous les tests."""
    sortie = support.site_complet()
    return tuple((str(f.relative_to(sortie)), f.read_text(encoding="utf-8")) for f in sorted(sortie.rglob("*.html")))


@functools.lru_cache(maxsize=None)
def unites_du_site(h):
    return S.extraire_page(h)


def v1():
    """Extracteur de la V1 (lecture seule), ou None si le site V1 est absent."""
    f = build.NEURON / "outils" / "segments.py"
    if not f.is_file():
        return None
    spec = importlib.util.spec_from_file_location("segments_v1", f)
    m = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(m)
    return m


def doc(corps, tete=""):
    """Page minimale : le <html lang> et la tête ne comptent pour rien, seules les unités du corps comptent."""
    return f'<!DOCTYPE html>\n<html lang="fr"><head><meta charset="utf-8">{tete}</head><body>{corps}</body></html>'


def identite(u):
    """Traduction qui rend le texte FR tel quel : valeur prête pour reinjecter_page."""
    return S.restaurer_unite(u["texte"], u)


def textes(unites, genre=None, attr=None):
    return [u["texte"] for u in unites if (genre is None or u["genre"] == genre) and (attr is None or u["attr"] == attr)]


def paires_blocs(unites):
    return [(u["texte"], u["table"]) for u in unites if u["genre"] == "bloc"]


class TestDecoupage(unittest.TestCase):
    SYNTHESE = (
        "<h1>Un <em>titre</em> &amp; son <a href=\"x/\">lien <strong>fort</strong></a></h1>\n"
        "<p>Texte avec<br>saut, <abbr>CO</abbr> et {{ROOT}}fr/page/ puis <span class=\"a\">un <i>mot</i></span>.</p>\n"
        "<ul><li>Premier</li><li><b>Deuxième</b> point</li></ul>\n"
        "<table><tr><th>Terme</th><td>Définition <code>x</code></td></tr></table>\n"
        "<p>Nombres 15&nbsp;000 francs.</p><div><span>Seul</span></div><p>  </p><p>12 345</p>")

    def test_meme_decoupage_que_la_v1(self):
        # unités « bloc » identiques (texte, table) à celles de l'extracteur V1 : sur une source synthétique, puis sur
        # les pages V1 qui ne contiennent aucun nœud exclu (lang d'une autre langue, translate="no")
        ancien = v1()
        if ancien is None:
            self.skipTest("site Neur.on V1 absent")
        attendu = paires_blocs(ancien.extraire_html(self.SYNTHESE))
        self.assertTrue(attendu)
        self.assertEqual(paires_blocs(S.extraire_page(self.SYNTHESE)), attendu)
        comparees = 0
        for f in sorted((build.NEURON / "src" / "pages").rglob("*.html")):
            source = f.read_text(encoding="utf-8")
            if re.search(r'\slang="(?!fr")|translate="no"', source):
                continue
            with self.subTest(page=str(f.relative_to(build.NEURON / "src" / "pages"))):
                self.assertEqual(paires_blocs(S.extraire_page(source)), paires_blocs(ancien.extraire_html(source)))
            comparees += 1
        self.assertGreater(comparees, 0)

    def test_page_assemblee(self):
        unites = S.extraire_page(PAGE)
        self.assertGreater(len(unites), 100)
        self.assertEqual([u["id"] for u in unites], [str(i) for i in range(1, len(unites) + 1)])
        self.assertEqual([u["debut"] for u in unites], sorted(u["debut"] for u in unites))
        for u in unites:
            self.assertEqual(u["html"], PAGE[u["debut"]:u["fin"]])
            self.assertEqual(set(u), {"id", "genre", "debut", "fin", "html", "texte", "table", "ui", "attr", "lang_fr"})
            self.assertIn(u["genre"], ("bloc", "attr", "ld", "json"))
            self.assertEqual(u["attr"] is not None, u["genre"] == "attr")
        t = textes(unites, "bloc")
        self.assertIn("Contact et démo · Neur.on, traduction juridique en Suisse", t)        # <title>
        self.assertIn("{1}Connexion{/1}{2}Demander une démo{/2}", t)                        # deux liens voisins : un passage, comme en V1
        self.assertIn("{1}Demandez une démo.{/1} {2}Corrext, ouvert sur vos propres documents{/2}", t)
        self.assertIn("Demander ma démonstration", t)
        self.assertNotIn("FR", t)                                                            # sélecteur de langue : translate="no"
        self.assertNotIn("DE", t)
        self.assertIn("Langue", textes(S.extraire_page(PAGE), "attr", "aria-label"))        # ... mais son aria-label se traduit

    def test_unites_sans_chevauchement(self):
        # deux unités ne se recouvrent jamais, sauf un attribut dans un passage (balise en ligne) qui l'englobe
        for h in (PAGE, self.SYNTHESE, doc('<p>Le <abbr title="Code des obligations">CO</abbr> et <a href="x/" aria-label="Lien">lien</a>.</p>')):
            u = S.extraire_page(h)
            for a, b in zip(u, u[1:]):
                if a["fin"] > b["debut"]:
                    self.assertEqual((a["genre"], b["genre"], b["fin"] <= a["fin"]), ("bloc", "attr", True), (a["html"], b["html"]))

    def test_attributs_ajoutes(self):
        # data-m et le content d'une meta de description : une unité chacun
        u = S.extraire_page(doc('<td class="pa-n" data-m="Allemand" lang="de">Konventionalstrafe</td>',
                                '<meta name="description" content="Une description à traduire.">'))
        self.assertEqual([(x["genre"], x["attr"], x["texte"]) for x in u],
                         [("attr", "content", "Une description à traduire."), ("attr", "data-m", "Allemand")])
        # les métas listées, et elles seules
        metas = "".join(f'<meta {k}="{v}" content="Texte lisible {i}">' for i, (k, v) in enumerate(
            [("name", "description"), ("property", "og:title"), ("property", "og:description"),
             ("property", "og:image:alt"), ("name", "twitter:title"), ("name", "twitter:description")]))
        metas += ('<meta name="robots" content="noindex, nofollow"><meta name="viewport" content="width=device-width, '
                  'initial-scale=1"><meta http-equiv="refresh" content="0; url=../fr/contact/">'
                  '<meta property="og:site_name" content="Neur.on"><meta name="theme-color" content="#001B4C">')
        self.assertEqual(textes(S.extraire_page(doc("", metas))), [f"Texte lisible {i}" for i in range(6)])

    def test_attributs_de_la_page_assemblee(self):
        unites = S.extraire_page(PAGE)
        attrs = Counter(u["attr"] for u in unites if u["genre"] == "attr")
        for nom in ("aria-label", "placeholder", "data-fermer", "data-resume", "data-requis", "data-email", "data-choix",
                    "data-case", "data-vide", "content"):
            self.assertGreater(attrs[nom], 0, nom)
        self.assertIn("Fermer le menu", textes(unites, "attr", "data-fermer"))
        self.assertIn("Neur.on, retour à l'accueil", textes(unites, "attr", "aria-label"))
        self.assertIn("Le formulaire n'a pas été envoyé. Corrigez les champs suivants :", textes(unites, "attr", "data-resume"))

    def test_exclusions(self):
        # <dd lang="de">, data-html et translate="no" : aucune unité
        self.assertEqual(textes(S.extraire_page(doc('<dl><div><dt>Allemand</dt><dd lang="de">Aktienkapital</dd></div></dl>'))),
                         ["Allemand"])
        self.assertEqual(textes(S.extraire_page(doc('<dd lang="de">Aktienkapital</dd>'))), [])
        self.assertEqual(S.extraire_page(doc('<p class="cr-out" data-html="La société doit &lt;mark&gt;déduire&lt;/mark&gt; l’impôt anticipé suisse">'
                                             '<span class="cr-sk"></span></p>')), [])
        self.assertEqual(S.extraire_page(doc('<nav class="hd-lang" translate="no"><a href="x/" lang="de" aria-label="Deutsch lisible" '
                                             'translate="no">DE</a>Texte exclu</nav>')), [])
        for nom in ("data-gen", "data-avant", "data-ph", "data-value", "data-title", "data-s", "data-dom"):
            self.assertEqual(textes(S.extraire_page(doc(f'<p {nom}="Un texte avec plusieurs mots">x1</p>'))), ["x1"], nom)

    def test_exclusions_imbriquees(self):
        # un sous-arbre étranger ne livre rien, y compris ses attributs descendants ; un lang="fr" rétabli à l'intérieur est lu
        u = S.extraire_page(doc('<div lang="de"><p title="Ein deutscher Titel">Deutsch</p><div lang="fr"><p>Français voulu</p></div>'
                                '<p>Wieder Deutsch</p></div><p>Après</p>'))
        self.assertEqual(textes(u), ["Français voulu", "Après"])
        # un élément en ligne étranger coupe le passage : l'allemand n'entre jamais dans un segment
        u = S.extraire_page(doc('<p>Le terme <span lang="de">Verzugszins</span> signifie intérêt moratoire.</p>'))
        self.assertEqual(textes(u), ["Le terme", "signifie intérêt moratoire."])
        # le lang de <html> ne masque jamais la page : un lang="de" à la racine est ignoré
        u = S.extraire_page('<!DOCTYPE html><html lang="de"><head></head><body><p>Mot français</p></body></html>')
        self.assertEqual(textes(u), ["Mot français"])
        # translate="yes" rétablit
        u = S.extraire_page(doc('<div translate="no"><p>Exclu</p><p translate="yes">Rétabli</p></div>'))
        self.assertEqual(textes(u), ["Rétabli"])

    def test_attributs_de_l_element_etranger(self):
        # le lang décrit le contenu : l'étiquette FR d'une cellule de tableau ou un aria-label FR restent à traduire
        u = S.extraire_page(doc('<table><tr><td data-m="Anglais" lang="en">fraud</td>'
                                '<td lang="de" aria-label="Traduction du segment 0">Betrug</td></tr></table>'))
        self.assertEqual([(x["attr"], x["texte"]) for x in u],
                         [("data-m", "Anglais"), ("aria-label", "Traduction du segment 0")])

    def test_lang_fr_et_ui(self):
        u = S.extraire_page(doc('<div data-ui><p>Écran</p><div lang="fr">Passage voulu en français</div></div><p>Hors écran</p>'
                                '<dd class="sp-ui" data-ui><p title="Titre lisible">Corrext</p></dd>'))
        self.assertEqual([(x["texte"], x["ui"], x["lang_fr"]) for x in u],
                         [("Écran", True, False), ("Passage voulu en français", True, True), ("Hors écran", False, False),
                          ("Titre lisible", True, False), ("Corrext", True, False)])
        # sur la page assemblée : les écrans d'application sont marqués, la page courante ne l'est pas
        self.assertFalse(any(x["ui"] for x in S.extraire_page(PAGE)))

    def test_aide_index(self):
        unites = S.extraire_page(PAGE)
        j = [u for u in unites if u["genre"] == "json"]
        self.assertEqual(len(j), 12)  # six questions, six rubriques (la même rubrique compte à chaque entrée)
        self.assertEqual([u["texte"] for u in j][:2], ["Qu'est-ce que Corrext ?", "Découvrir Corrext"])
        # les adresses (clé u) ne sont jamais extraites et la réinjection ne les touche pas
        out = S.reinjecter_page(PAGE, {u["id"]: u["texte"].upper() for u in j})
        index = json.loads(re.search(r'id="aide-index">(.*?)</script>', out, re.S).group(1))
        ancien = json.loads(re.search(r'id="aide-index">(.*?)</script>', PAGE, re.S).group(1))
        self.assertEqual([e["u"] for e in index], [e["u"] for e in ancien])
        self.assertEqual(index[0]["q"], "QU'EST-CE QUE CORREXT ?")

    def test_json_ld(self):
        ld = ('<script type="application/ld+json">{"@type": "DefinedTerm", "name": "Verjährung", "inLanguage": "de-CH", '
              '"alternateName": ["prescription", "prescrizione"], "description": "L\'extinction du droit d\'agir.", '
              '"termCode": "art. 127 CO", "url": "https://neur-on.ai/fr/", "inDefinedTermSet": {"@type": "DefinedTermSet", '
              '"name": "Glossaire juridique suisse", "inLanguage": "fr-CH"}, "award": ["Lauréat 2024", "Digital Shapers 2023"], '
              '"knowsLanguage": ["de", "fr"], "email": "team@corrext.com", "streetAddress": "Place de la Gare 15", '
              '"legalName": "Neur.on AI Solutions SA", "dateModified": "2026-10-23"}</script>')
        u = S.extraire_page(doc("", ld))
        self.assertEqual([x["genre"] for x in u], ["ld"] * 5)
        self.assertEqual([x["texte"] for x in u], ["L'extinction du droit d'agir.", "art. 127 CO", "Glossaire juridique suisse",
                                                   "Lauréat 2024", "Digital Shapers 2023"])
        # sur la page assemblée : le JSON-LD de la page, la question de la FAQ et sa réponse
        ld_page = textes(S.extraire_page(PAGE), "ld")
        self.assertIn("Contact et démo · Neur.on", ld_page)
        self.assertTrue(any(t.startswith("Société suisse établie à Fribourg") for t in ld_page))
        self.assertNotIn("de", ld_page)
        self.assertFalse(any(t.startswith("http") or t == "team@corrext.com" for t in ld_page))

    def test_valeur_des_champs(self):
        # value : libellé de bouton ou champ affiché sans saisie (disabled) ; jamais la valeur d'un champ de démo
        u = S.extraire_page(doc('<input type="submit" value="Envoyer la demande"><input type="text" class="cxp-input" '
                                'value="masqué en démo" disabled><input type="text" value="intérêt moratoire">'
                                '<input type="checkbox" value="Allemand"><input type="hidden" value="">'
                                '<input type="text" value="2,5" readonly>'))
        self.assertEqual([(x["attr"], x["texte"]) for x in u], [("value", "Envoyer la demande"), ("value", "masqué en démo")])

    def test_menus_de_demonstration(self):
        # data-v : valeur affichée par sim.js et comparée au texte visible, elle suit donc le segment du libellé
        u = S.extraire_page(doc('<li data-v="Double relecture et traduction certifiée">Double relecture et traduction certifiée</li>'))
        self.assertEqual(sorted((x["genre"], x["texte"]) for x in u), [("attr", "Double relecture et traduction certifiée"),
                                                                       ("bloc", "Double relecture et traduction certifiée")])
        # data-def : HTML rejoué par l'animation, balisage protégé par des marqueurs
        u = S.extraire_page(doc('<p class="cr-out" data-def="Le débiteur en &lt;u&gt;retard&lt;/u&gt; doit &lt;u&gt;verser&lt;/u&gt; des intérêts.">'
                                '<u>Celui</u> qui paie</p>'))
        d = [x for x in u if x["attr"] == "data-def"][0]
        self.assertEqual(d["texte"], "Le débiteur en {1}retard{/1} doit {2}verser{/2} des intérêts.")
        self.assertEqual(S.restaurer_unite("Der Schuldner {1}säumig{/1} muss {2}zahlen{/2} Zinsen.", d),
                         "Der Schuldner <u>säumig</u> muss <u>zahlen</u> Zinsen.")
        self.assertIn("&lt;u&gt;säumig&lt;/u&gt;",
                      S.reinjecter_page(doc('<p data-def="Le débiteur en &lt;u&gt;retard&lt;/u&gt; doit payer.">x</p>'),
                                        {"1": "Der Schuldner <u>säumig</u> muss zahlen."}))


class TestReinjection(unittest.TestCase):
    def test_reinjection_identite(self):
        # reinjecter_page(h, {u["id"]: u["texte"] restauré}) == h, sur la fixture
        unites = S.extraire_page(PAGE)
        self.assertEqual(S.reinjecter_page(PAGE, {u["id"]: identite(u) for u in unites}), PAGE)
        self.assertEqual(S.reinjecter_page(PAGE, {}), PAGE)

    def test_reinjection_identite_sur_le_site_complet(self):
        pages = pages_du_site()
        self.assertGreater(len(pages), 150)
        for chemin, h in pages:
            with self.subTest(page=chemin):
                self.assertEqual(S.reinjecter_page(h, {u["id"]: identite(u) for u in unites_du_site(h)}), h)

    def test_reinjection_remplace_chaque_genre(self):
        # toute unité sans balisage, traduite : la réextraction rend le texte traduit, la page ne change que par ses textes
        unites = S.extraire_page(PAGE)
        trad = {u["id"]: S.restaurer_unite("ZZ " + u["texte"], u) for u in unites if not u["table"]}
        self.assertGreater(len(trad), 100)
        sortie = S.reinjecter_page(PAGE, trad)
        reunites = S.extraire_page(sortie)
        self.assertEqual(len(reunites), len(unites))
        for u, r in zip(unites, reunites):
            self.assertEqual(r["texte"], ("ZZ " + u["texte"]) if u["id"] in trad else u["texte"], u["html"][:60])
            self.assertEqual((r["genre"], r["attr"]), (u["genre"], u["attr"]))
        self.assertEqual(Counter(u["genre"] for u in unites if u["id"] in trad), Counter(u["genre"] for u in unites if not u["table"]))
        # balises inchangées : la page n'a changé que par ses textes
        def balises(h):
            return re.findall(r"</?[a-zA-Z][^>]*>", re.sub(r'(content|aria-label|placeholder|alt|title|data-[a-z-]+)="[^"]*"', r"\1=''", h))
        self.assertEqual(balises(sortie), balises(PAGE))

    def test_marqueurs_restaures(self):
        h = doc('<p>La <a href="x/">règle</a> et le <b>cas</b> d\'espèce.</p>')
        u = S.extraire_page(h)[0]
        self.assertEqual(u["texte"], "La {1}règle{/1} et le {2}cas{/2} d'espèce.")
        sortie = S.reinjecter_page(h, {u["id"]: S.restaurer_unite("Die {1}Regel{/1} und der {2}Fall{/2}.", u)})
        self.assertIn('<p>Die <a href="x/">Regel</a> und der <b>Fall</b>.</p>', sortie)
        with self.assertRaises(ValueError):
            S.restaurer_unite("Die {1}Regel und der {2}Fall{/2}.", u)

    def test_caracteres_speciaux(self):
        h = doc('<p title="Titre FR">Texte</p><script type="application/ld+json">{"name": "Nom FR"}</script>')
        par = {(x["genre"], x["attr"]): x for x in S.extraire_page(h)}
        sortie = S.reinjecter_page(h, {
            par[("attr", "title")]["id"]: 'Titre "cité" & <fort>',
            par[("bloc", None)]["id"]: S.restaurer_unite("Texte & suite <ok>", par[("bloc", None)]),
            par[("ld", None)]["id"]: 'Nom "cité" </script> \\ fin'})
        self.assertIn('<p title="Titre &quot;cité&quot; &amp; &lt;fort&gt;">Texte &amp; suite &lt;ok&gt;</p>', sortie)
        self.assertEqual(json.loads(re.search(r'ld\+json">(.*?)</script>', sortie, re.S).group(1)), {"name": 'Nom "cité" </script> \\ fin'})
        self.assertEqual(sortie.count("</script>"), 1)
        # la réextraction relit exactement les textes écrits
        for x in S.extraire_page(sortie):
            if x["attr"] == "title":
                self.assertEqual(x["texte"], 'Titre "cité" & <fort>')

    def test_guillemets_simples_et_absents(self):
        h = doc("<p title='Titre simple'>a1</p><table><tr><td data-m=Allemand>b2</td></tr></table>")
        u = S.extraire_page(h)
        self.assertEqual([(x["attr"], x["texte"]) for x in u if x["genre"] == "attr"], [("title", "Titre simple"), ("data-m", "Allemand")])
        sortie = S.reinjecter_page(h, {x["id"]: "Neu d'un " + x["texte"] for x in u if x["genre"] == "attr"})
        self.assertIn("<p title='Neu d&#x27;un Titre simple'>", sortie)
        self.assertIn('<td data-m="Neu d&#x27;un Allemand">', sortie)

    def test_attribut_dans_un_passage(self):
        # <abbr title> dans une phrase : l'attribut a sa propre unité, traduite dans la balise restaurée du passage
        h = doc('<p>Le <abbr title="Code des obligations">CO</abbr> règle le cas, selon le <abbr title="Code des obligations">CO</abbr>.</p>')
        u = S.extraire_page(h)
        self.assertEqual([x["genre"] for x in u], ["bloc", "attr", "attr"])
        bloc = u[0]
        self.assertEqual(bloc["texte"], "Le {1}CO{/1} règle le cas, selon le {2}CO{/2}.")
        t_attr = {x["id"]: "Obligationenrecht" for x in u if x["genre"] == "attr"}
        h2 = h.replace("</p></body>", "</p><p>Fin</p></body>")   # un passage après : les décalages se voient
        self.assertNotEqual(h2, h)
        # passage inchangé, attributs traduits
        sortie = S.reinjecter_page(h, {u[0]["id"]: identite(u[0]), **t_attr})
        self.assertEqual(sortie.count('title="Obligationenrecht"'), 2)
        self.assertNotIn("Code des obligations", sortie)
        # passage et attributs traduits ensemble, texte plus court ou plus long que le français (offsets décalés)
        for de in ("Das {1}OR{/1} regelt den Fall, laut {2}OR{/2}.",
                   "Das {1}OR{/1} regelt in dem hier vorliegenden Fall ausdrücklich und abschliessend, laut {2}OR{/2}, die Sache."):
            sortie = S.reinjecter_page(h2, {bloc["id"]: S.restaurer_unite(de, bloc), **t_attr})
            attendu = de.replace("{1}", '<abbr title="Obligationenrecht">').replace("{2}", '<abbr title="Obligationenrecht">')
            attendu = attendu.replace("{/1}", "</abbr>").replace("{/2}", "</abbr>")
            self.assertEqual(sortie, doc(f"<p>{attendu}</p><p>Fin</p>"))
        # attribut seul, passage absent
        sortie = S.reinjecter_page(h, t_attr)
        self.assertEqual(sortie.count('title="Obligationenrecht"'), 2)
        self.assertIn("Le <abbr", sortie)


    def test_passage_et_attribut_traduits_longueurs_differentes(self):
        # cas de la relecture : le passage traduit n'a pas la longueur du français, un passage suit
        h = doc('<p>Le <abbr title="Code des obligations">CO</abbr> règle le cas.</p><p>Fin</p>')
        bloc, attr, fin = S.extraire_page(h)
        sortie = S.reinjecter_page(h, {bloc["id"]: S.restaurer_unite("Das {1}OR{/1} regelt den Fall.", bloc), attr["id"]: "Obligationenrecht"})
        self.assertEqual(sortie, doc('<p>Das <abbr title="Obligationenrecht">OR</abbr> regelt den Fall.</p><p>Fin</p>'))

    def test_attribut_introuvable_dans_le_passage(self):
        # un attribut qui ne se retrouve pas dans les balises du passage traduit : erreur, jamais une perte silencieuse
        h = doc('<p>Le <abbr title="Code des obligations">CO</abbr> règle le cas.</p>')
        bloc, attr = S.extraire_page(h)
        # balise du passage qui ne porte plus la valeur d'origine de l'attribut
        faux = dict(bloc, table={1: {"ouvre": '<abbr title="Autre valeur">', "ferme": "</abbr>"}})
        with self.assertRaises(ValueError):
            S.reinjecter_page(h, {bloc["id"]: S.restaurer("Das {1}OR{/1} regelt den Fall.", faux["table"]), attr["id"]: "Obligationenrecht"})

    def test_tout_traduit_sur_le_site_complet(self):
        # toutes les unités, marqueurs compris, préfixées de « ZZ » puis réinjectées : la ré-extraction rend chaque texte
        # préfixé (espaces normalisées) et la page garde la même suite de balises, donc reste bien formée
        for chemin, h in pages_du_site():
            unites = unites_du_site(h)
            trad = {u["id"]: S.restaurer_unite("ZZ " + u["texte"], u) for u in unites}
            sortie = S.reinjecter_page(h, trad)
            with self.subTest(page=chemin):
                reunites = S.extraire_page(sortie)
                self.assertEqual(len(reunites), len(unites))
                for u, r in zip(unites, reunites):
                    self.assertEqual(_normaliser(r["texte"]), _normaliser("ZZ " + u["texte"]), u["html"][:80])
                self.assertEqual(_suite_de_balises(sortie), _suite_de_balises(h))


class TestRestaurer(unittest.TestCase):
    """Relecture 2.1 : les espaces de la traduction sont gardées, y compris à l'intérieur d'une paire de marqueurs."""

    def test_espace_interieure_gardee(self):
        texte, table = S.proteger('<a href="x/">Regarder l\'interview </a>!')
        self.assertEqual(texte, "{1}Regarder l'interview {/1}!")
        self.assertEqual(S.restaurer(texte, table), '<a href="x/">Regarder l\'interview </a>!')
        self.assertEqual(S.restaurer("{1} Das Interview ansehen {/1}!", table), '<a href="x/"> Das Interview ansehen </a>!')

    def test_marqueurs_espaces_remis_en_forme(self):
        _, table = S.proteger('<a href="x/">Démo</a> et <br> suite')
        self.assertEqual(S.restaurer("{ 1 }Demo{ /1 } und {2} weiter", table), '<a href="x/">Demo</a> und <br> weiter')


class TestCodeNonTraduit(unittest.TestCase):
    """Relecture 2.1 : le bloc de code de l'exemple d'API (tarifs/, classe u-code) n'est jamais extrait, donc jamais
    traduit ni réindenté ; le français reste identique (exclusion par la classe, sans toucher à la source)."""

    def test_classe_u_code_exclue(self):
        h = doc('<pre class="u-code"><span class="l1"><b>POST</b> /v1/translate</span>\n<span class="l3">  <em>"engine"</em>: '
                '"lexmachina",</span></pre><p>Après</p>')
        self.assertEqual(textes(S.extraire_page(h)), ["Après"])

    def test_tarifs(self):
        h = dict(pages_du_site())["fr/tarifs/index.html"]
        self.assertIn('<pre class="u-code">', h)
        for u in unites_du_site(h):
            self.assertNotIn("source_language", u["texte"])
            self.assertNotIn("/v1/translate", u["texte"])


class TestClassement(unittest.TestCase):
    def test_listes_du_plan(self):
        for nom in ("alt", "aria-label", "title", "placeholder", "data-m", "data-v-erreur", "data-v-refus", "data-vide",
                    "data-fermer", "data-relancer", "data-pause", "data-resume", "data-requis", "data-email", "data-choix",
                    "data-case", "data-avis", "data-prerempli"):
            self.assertIn(nom, S.ATTRS_TEXTE)
        for nom in ("data-html", "data-gen", "data-avant", "data-ph", "data-value", "data-title", "data-s", "data-dom",
                    "data-suivi", "data-act", "data-seul", "data-ech", "data-sim", "data-style", "data-theme",
                    "data-theme-set", "data-reinit"):
            self.assertIn(nom, S.ATTRS_JAMAIS)
        self.assertFalse(set(S.ATTRS_TEXTE) & set(S.ATTRS_JAMAIS))

    def test_tout_attribut_texte_est_classe(self):
        # sur la sortie FR complète : tout attribut qui porte du texte (valeur de 2 mots ou plus avec minuscules, ou pour
        # un data-* toute valeur qui n'est ni un identifiant, ni un chemin, ni un nombre) est extrait ou classé « jamais »
        pages = [h for _, h in pages_du_site()]
        self.assertGreater(len(pages), 150)
        self.assertEqual(attributs_non_classes(pages), {})

    def test_le_controle_de_classement_attrape_un_attribut_nouveau(self):
        # sensibilité : un data-* ou une méta inconnus portant du texte sont signalés, un attribut classé ne l'est pas
        pages = ['<p data-nouveau="Un texte qui échappe">x</p><meta name="keywords" content="mots clés de la page">'
                 '<p data-m="Allemand" data-v-autre="Un texte de variante" data-terme-co="intérêts moratoires">y</p>']
        self.assertEqual(attributs_non_classes(pages), {("p", "data-nouveau"): "Un texte qui échappe",
                                                        ("meta", "content"): "mots clés de la page"})

    def test_aucun_texte_visible_oublie(self):
        # oracle indépendant : le lecteur d'invariants (controles.texte_visible) lit les textes, alt, title, aria-label,
        # placeholder et métas de description de la page ; chacun de ses mots doit se retrouver dans une unité
        oublies = {}
        for chemin, h in pages_du_site():
            lu = Counter(w for t in _lecteur_espace(h) for w in _MOT.findall(t))
            extrait = Counter(w for u in unites_du_site(h) if u["genre"] in ("bloc", "attr")
                              for w in _MOT.findall(re.sub(r"\{/?\d+\}", " ", u["texte"])))
            manque = lu - extrait
            if manque:
                oublies[chemin] = dict(manque.most_common(5))
        self.assertEqual(oublies, {})

    def test_json_ld_complet(self):
        # chaque chaîne du JSON-LD de la sortie complète est extraite, ou sa clé est classée dans LD_JAMAIS, ou c'est une
        # adresse, un code de langue ou le mot-vedette d'un terme défini dans une autre langue
        for chemin, h in pages_du_site():
            extraits = Counter(u["texte"] for u in unites_du_site(h) if u["genre"] == "ld")
            attendus = Counter()
            for m in re.finditer(r'<script type="application/ld\+json">(.*?)</script>', h, re.S):
                _chaines_ld(json.loads(m.group(1)), None, attendus)
            self.assertEqual(extraits, attendus, chemin)

    def test_classer_attribut(self):
        c = S.classer_attribut
        self.assertEqual(c("meta", {"name": "description"}, "content"), "texte")
        self.assertEqual(c("meta", {"property": "og:image:alt"}, "content"), "texte")
        self.assertEqual(c("meta", {"name": "robots"}, "content"), "jamais")
        self.assertEqual(c("meta", {"http-equiv": "refresh"}, "content"), "jamais")
        self.assertIsNone(c("meta", {"name": "keywords"}, "content"))
        self.assertEqual(c("input", {"type": "button"}, "value"), "texte")
        self.assertEqual(c("input", {"type": "text", "disabled": ""}, "value"), "texte")
        self.assertEqual(c("input", {"type": "text"}, "value"), "jamais")
        self.assertEqual(c("p", {}, "data-v-newsletter"), "texte")
        self.assertEqual(c("div", {}, "class"), "technique")
        self.assertIsNone(c("div", {}, "data-inconnu"))


class TestScripts(unittest.TestCase):
    def test_scripts_a_traduire(self):
        self.assertTrue(S.scripts_a_traduire("<script>el.textContent = 'Analyse en cours avec le moteur';</script>"))
        self.assertFalse(S.scripts_a_traduire('<script type="application/ld+json">{"name": "Un nom lisible"}</script>'))
        self.assertFalse(S.scripts_a_traduire('<script type="application/json" id="aide-index">[{"q": "Une question ?"}]</script>'))
        self.assertFalse(S.scripts_a_traduire("<script>var etat = {etape: 1, ok: true};</script>"))

    # Pages dont un script inline écrit du texte français que l'extraction ne voit pas : aucune depuis la tâche 7.3 (les
    # démos lisent leurs textes dans un bloc JSON extrait) ; le test échoue si une page en écrit, pour que rien
    # n'échappe sans être vu.
    SCRIPTS_CONNUS = set()

    def test_scripts_ecrivant_du_texte_sont_inventories(self):
        trouves = {chemin for chemin, h in pages_du_site() if S.scripts_a_traduire(h)}
        self.assertEqual(trouves, self.SCRIPTS_CONNUS)

    def test_element_en_ligne_francais_coupe_le_passage(self):
        """Tâche 7.3 : une source française de démo (lang="fr") dans une barre d'interface en ligne forme son unité
        lang_fr, sans entraîner les libellés voisins (traduits) ni y être entraînée."""
        h = ('<p><span>English</span><span>LexMachina</span><span lang="fr">Le débiteur <mark>doit</mark> des intérêts</span>'
             '<span>Fast Lookup</span></p>')
        self.assertEqual([(u["texte"], u["lang_fr"]) for u in S.extraire_page(h)],
                         [("{1}English{/1}{2}LexMachina{/2}", False), ("Le débiteur {1}doit{/1} des intérêts", True),
                          ("{1}Fast Lookup{/1}", False)])
        u = S.extraire_page(h)[0]
        traduit = S.reinjecter_page(h, {u["id"]: S.restaurer_unite("{1}Englisch{/1}{2}LexMachina{/2}", u)})
        self.assertEqual(traduit, h.replace("English", "Englisch"))

    def test_attributs_d_un_element_francais_voulu(self):
        """Le lang="fr" d'une source de démo ne gèle pas ses attributs d'interface (aria-label traduit), seulement le
        texte qu'elle rejoue (data-def)."""
        h = ('<p><input type="text" value="intérêt moratoire" aria-label="Rechercher un terme" lang="fr"></p>'
             '<p class="cr-rout" lang="fr" data-def="Le débiteur en &lt;u&gt;retard&lt;/u&gt;">Celui qui ne paie pas</p>')
        self.assertEqual([(u["attr"], u["texte"], u["lang_fr"]) for u in S.extraire_page(h)],
                         [("aria-label", "Rechercher un terme", False), ("data-def", "Le débiteur en {1}retard{/1}", True),
                          (None, "Celui qui ne paie pas", True)])

    def test_script_de_donnees_translate_no_non_lu(self):
        """Données des démos (tâche 7.3) : un bloc JSON translate="no" ne donne aucune unité ; le bloc des textes, si."""
        h = ('<p>Bonjour</p><script type="application/json" data-donnees translate="no">{"phrase": "Le débiteur en demeure"}'
             '</script><script type="application/json" data-textes>{"vide": "Aucun résultat."}</script>')
        self.assertEqual([u["texte"] for u in S.extraire_page(h)], ["Bonjour", "Aucun résultat."])

    def test_sim_data_et_scripts_externes_ne_sont_pas_dans_la_page(self):
        # les données de démo (window.SIM_EX) vivent dans assets/sim-data.js : jamais dans le HTML, donc jamais extraites
        for chemin, h in pages_du_site():
            self.assertNotIn("SIM_EX", h, chemin)


# ---------- outils de test ----------

_MOT = re.compile(r"[^\W\d_]+")


def _lecteur_espace(h):
    """Textes lisibles de la page selon controles.texte_visible, avec une espace à chaque frontière de balise, hors
    JSON-LD (lu à part)."""
    class Lecteur(controles._Lecteur):
        def handle_starttag(self, balise, attrs):
            self.tampon.append(" ")
            super().handle_starttag(balise, attrs)

        def handle_endtag(self, balise):
            self.tampon.append(" ")
            super().handle_endtag(balise)

    lecteur = Lecteur("fr")
    lecteur.feed(re.sub(r'<script type="application/ld\+json">.*?</script>', "", h, flags=re.S))
    lecteur.close()
    return lecteur.fin()


def _normaliser(texte):
    """Espaces normalisées (restaurer garde les espaces de la traduction, y compris autour des marqueurs)."""
    return " ".join(texte.split())


def _suite_de_balises(h):
    """Noms des balises ouvrantes et fermantes, dans l'ordre : deux pages bien formées de même structure ont la même."""
    return re.findall(r"</?([a-zA-Z][\w:-]*)", re.sub(r"<(script|style)\b[^>]*>.*?</\1\s*>", "<\\1>", h, flags=re.S))


def attributs_non_classes(pages):
    """{(balise, attribut): exemple} des attributs porteurs de texte que ni l'extraction ni les listes « jamais » ne couvrent."""
    inconnus = {}
    for h in pages:
        for balise, attrs in _balises(h):
            for nom, valeur in attrs.items():
                v = H.unescape(valeur or "")
                if S.classer_attribut(balise, attrs, nom) is not None:
                    continue
                texte = len(v.split()) >= 2 and re.search("[a-zà-ÿ]", v)
                data = nom.startswith("data-") and S.LETTRE.search(v) and not S.IDENT.fullmatch(v) and not S.CHEMIN.match(v)
                if texte or data:
                    inconnus.setdefault((balise, nom), v[:60])
    return inconnus


def _chaines_ld(valeur, cle, attendus, parent=None):
    """Chaînes du JSON-LD que l'extracteur doit livrer, selon les seules règles du plan : clés techniques exclues."""
    if isinstance(valeur, dict):
        for k, v in valeur.items():
            _chaines_ld(v, k, attendus, valeur)
    elif isinstance(valeur, list):
        for v in valeur:
            _chaines_ld(v, cle, attendus, parent)
    elif isinstance(valeur, str) and S.LETTRE.search(valeur) and not S.CHEMIN.match(valeur):
        langue = parent.get("inLanguage", "fr") if parent else "fr"
        etranger = cle == "name" and isinstance(langue, str) and _primaire(langue) != "fr"
        if cle in S.LD_JAMAIS or etranger:
            return
        attendus[valeur] += 1


def _primaire(code):
    return code.lower().split("-")[0]


_BALISE = re.compile(r"<([a-zA-Z][\w:-]*)((?:\s+[^\s=>/]+(?:\s*=\s*(?:\"[^\"]*\"|'[^']*'|[^\s>]+))?)*)\s*/?>")
_ATTR = re.compile(r"""\s([^\s=>/]+)(?:\s*=\s*(?:"([^"]*)"|'([^']*)'|([^\s>]+)))?""")


def _balises(h):
    """(balise, attributs) de chaque balise ouvrante, hors scripts et styles, indépendamment de l'extracteur."""
    h = re.sub(r"<(script|style)\b[^>]*>.*?</\1\s*>", lambda m: re.match(r"<[^>]*>", m.group(0)).group(0), h, flags=re.S)
    for m in _BALISE.finditer(h):
        attrs = {}
        for a in _ATTR.finditer(m.group(2)):
            attrs[a.group(1).lower()] = next((g for g in a.groups()[1:] if g is not None), "")
        yield m.group(1).lower(), attrs


if __name__ == "__main__":
    unittest.main()
