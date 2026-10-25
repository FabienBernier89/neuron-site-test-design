"""llms.txt et llms-full.txt du site V2, générés à chaque build depuis les pages construites (format llmstxt.org).

llms.txt : titre, résumé (la description méta de l'accueil), puis une section par partie du site, chaque page sous la
forme « - [titre](adresse): description ». Titre et description sont ceux de la méta de la page (title sans le
suffixe « · Neur.on »), sans aucun ajout : le fichier ne dit rien que le site ne dise déjà. Les pages non indexées
(remerciement) n'y figurent pas. La section « Optional » (mot clé du format) réunit ce qu'un assistant peut ignorer
quand le contexte manque : billets du blog, fiches du glossaire, pages légales.

llms-full.txt : le texte visible des pages de référence (PAGES_COMPLETES : accueil, Corrext et ses outils, LexMachina,
sécurité, langues et formats, niveaux de qualité, tarifs, hubs des solutions et de la traduction, comparatifs,
à propos, presse, contact), en Markdown, lu dans le <main> de la page construite. Les scènes d'interface (écrans
Corrext animés, fenêtres de démonstration, schémas) et tout ce qui est masqué aux lecteurs d'écran en sont exclus :
ce sont des données de démonstration, pas du contenu.
"""
import html as H
import re
from html.parser import HTMLParser

from .i18n.langues import route

PRODUCTION = "https://neur-on.ai/"
SUFFIXE = " · Neur.on"
# Nom de chaque langue dans sa propre langue (jamais traduit) : libellé des liens de la section « Versions linguistiques »
NOMS_LANGUES = {"fr": "Français", "de": "Deutsch", "it": "Italiano", "en": "English"}

# (titre de section, règle d'appartenance) dans l'ordre du fichier ; une page prend la première section qui l'accepte
SECTIONS = [
    ("Accueil", lambda p: p == ""),
    ("Corrext, la plateforme", lambda p: p.startswith("corrext/")),
    ("LexMachina, le moteur", lambda p: p.startswith("lexmachina/")),
    ("Sécurité, langues et qualité", lambda p: p in ("securite-souverainete/", "langues-et-formats/", "niveaux-de-qualite/")),
    ("Tarifs", lambda p: p.startswith("tarifs/")),
    ("Solutions par métier", lambda p: p.startswith("solutions/")),
    ("Traduction juridique par domaine et par paire de langues", lambda p: p.startswith("traduction/")),
    ("Comparatifs", lambda p: p.startswith("comparatif/")),
    ("À propos et presse", lambda p: p.startswith("a-propos/")),
    ("Contact", lambda p: p.startswith("contact/")),
    ("Ressources", lambda p: p.startswith("ressources/") and not secondaire(p)),
    ("Centre d'aide", lambda p: p.startswith("aide/")),
    ("Optional", lambda p: True),
]


def secondaire(page):
    """Billet du blog (hors index et actualités) ou fiche du glossaire : rangé dans « Optional »."""
    return bool(re.match(r"^ressources/(?:blog/(?!actualites/)[^/]+|glossaire/[^/]+)/$", page))


def titre(meta):
    t = H.unescape(meta.get("title", "")).strip()
    return t[:-len(SUFFIXE)] if t.endswith(SUFFIXE) else t


def adresse(page, langue="fr"):
    """Adresse de production d'une page dans une langue (le français se déduit de la page, comme partout)."""
    return PRODUCTION + ("fr/" + page if langue == "fr" else route(page, langue))


def fichier(nom, langue="fr"):
    """Adresse de production d'un fichier llms (« llms.txt ») : à la racine pour le français, sous /<l>/ sinon."""
    return PRODUCTION + ("" if langue == "fr" else langue + "/") + nom


# Libellés fixes, passés à t (traduction de la langue ; identité en français). Les phrases portent {date} et {url} ; la
# ponctuation de SOURCE fait partie du libellé (typographie propre à chaque langue : « Source : », « Quelle: »), l'espace
# qui le sépare de l'adresse est ajoutée par llms_full_txt.
INTRO_INDEX = "Site en français (Suisse), mis à jour le {date}. Texte intégral des pages principales : {url}"
INTRO_COMPLET = "Site en français (Suisse), mis à jour le {date}. Index de toutes les pages : {url}"
TITRE_COMPLET = "Neur.on : texte intégral des pages principales"
TITRE_VERSIONS = "Versions linguistiques"
SOURCE = "Source :"
OPTIONAL = "Optional"  # mot clé du format llms.txt : jamais traduit


def libelles_fixes():
    """Libellés qu'un fichier llms d'une autre langue que le français peut passer à t : titres des sections (hors
    « Optional », mot clé du format), phrases d'introduction, titre du texte intégral, préfixe des sources.
    « Versions linguistiques » n'apparaît que dans le fichier français."""
    return [nom for nom, _ in SECTIONS if nom != OPTIONAL] + [INTRO_INDEX, INTRO_COMPLET, TITRE_COMPLET, SOURCE]


def remplir(phrase, date, url):
    """Phrase d'introduction (éventuellement traduite) dont {date} et {url} sont remplacés."""
    return phrase.replace("{date}", date).replace("{url}", url)


def llms_txt(pages, date, langue="fr", t=lambda s: s, langues=("fr",)):
    """pages : [(chemin publié, méta)] des pages indexables de la langue, dans l'ordre du build ; date : AAAA-MM-JJ.
    langue : langue du fichier (adresses de cette langue) ; t : traduction des libellés fixes (titres de SECTIONS,
    phrase d'introduction). langues : langues construites ; le fichier français, s'il y en a plusieurs, gagne une section
    « Versions linguistiques » (les fichiers llms des autres langues), avant « Optional » qui reste la dernière."""
    metas = dict(pages)
    accueil = metas.get("", {})
    lignes = ["# Neur.on", "", "> " + H.unescape(accueil.get("description", "")).strip(), "",
              remplir(t(INTRO_INDEX), date, fichier("llms-full.txt", langue)), ""]
    ranges = {nom: [] for nom, _ in SECTIONS}
    for page, meta in pages:
        nom = next(n for n, regle in SECTIONS if regle(page))
        desc = H.unescape(meta.get("description", "")).strip()
        ranges[nom].append(f"- [{titre(meta)}]({adresse(page, langue)})" + (f": {desc}" if desc else ""))
    if langue == "fr" and len(langues) > 1:
        ranges[TITRE_VERSIONS] = [f"- [{NOMS_LANGUES[l]}]({fichier('llms.txt', l)})" for l in langues if l != "fr"]
    sections = [n for n, _ in SECTIONS]
    sections.insert(sections.index(OPTIONAL), TITRE_VERSIONS)  # « Optional » reste la dernière section du format
    for nom in sections:
        if ranges.get(nom):
            lignes += [f"## {nom if nom == OPTIONAL else t(nom)}", ""] + ranges[nom] + [""]
    return "\n".join(lignes).rstrip("\n") + "\n"


PAGES_COMPLETES = ("", "corrext/", "corrext/traduction-texte-et-document/", "corrext/gestion-de-projet/",
                   "corrext/editeur-de-relecture/", "corrext/chnell/", "corrext/extraits-registre-commerce/",
                   "corrext/plugin-word/", "corrext/api-on-premises/", "lexmachina/", "securite-souverainete/",
                   "langues-et-formats/", "niveaux-de-qualite/", "tarifs/", "solutions/", "traduction/", "comparatif/",
                   "comparatif/deepl-traduction-juridique/", "comparatif/chatgpt-traduction-juridique/",
                   "comparatif/agence-ou-plateforme/", "a-propos/", "a-propos/presse/", "contact/")

# Conteneurs exclus du texte : scènes d'interface (écran Corrext .cr/.cx, scène animée .st, échantillon .ech,
# fenêtre .fen, document .doc, maquette .maq, schéma « qui fait quoi » .sp-app/.sp-sc, visite guidée .vw-*)
CLASSES_EXCLUES = re.compile(r"^(?:cr|cx|st|ech|fen|doc|maq|sp-app|sp-sc|vw-.*|cr-.*)$")
BALISES_EXCLUES = {"script", "style", "svg", "noscript", "template", "form", "button", "select", "textarea", "nav",
                   "canvas", "video", "audio", "iframe"}
VIDES = {"br", "img", "hr", "input", "meta", "link", "source", "wbr", "col", "area", "base", "embed", "param", "track"}
BLOCS = {"p", "li", "h1", "h2", "h3", "h4", "h5", "h6", "dt", "dd", "tr", "blockquote", "figcaption", "summary",
         "caption"}
CONTENEURS = {"div", "section", "article", "aside", "header", "footer", "ul", "ol", "dl", "table", "figure", "details"}
CELLULES = {"td", "th"}  # une ligne de tableau par ligne de texte, cellules séparées par « | »


class _Texte(HTMLParser):
    """Texte Markdown d'un fragment HTML : titres (#), paragraphes, puces, cellules ; scènes et masqués exclus."""

    def __init__(self):
        super().__init__(convert_charrefs=True)
        self.pile = []        # balises ouvertes : (nom, exclue)
        self.exclusion = 0    # profondeur d'exclusion en cours
        self.blocs, self.courant, self.prefixe = [], [], ""
        self.apres_fin = False  # dernier événement : une balise fermante (deux éléments accolés, à séparer)

    def _exclue(self, tag, attrs):
        a = dict(attrs)
        classes = (a.get("class") or "").split()
        return (tag in BALISES_EXCLUES or a.get("aria-hidden") == "true" or "hidden" in a
                or "data-sim" in a or "data-ech" in a or any(CLASSES_EXCLUES.match(c) for c in classes))

    def _vider(self):
        texte = re.sub(r"\s+", " ", "".join(self.courant)).strip()
        if texte:
            self.blocs.append(self.prefixe + texte)
        self.courant, self.prefixe = [], ""

    def handle_starttag(self, tag, attrs):
        if tag in VIDES:
            if tag == "br" and not self.exclusion:
                self.courant.append(" ")
            return
        exclue = self.exclusion > 0 or self._exclue(tag, attrs)
        self.pile.append((tag, exclue))
        if exclue:
            self.exclusion += 1
            return
        if tag in CONTENEURS:  # un conteneur sépare deux textes (carte, colonne, bouton suivant)
            self._vider()
        elif tag in BLOCS:
            self._vider()
            self.prefixe = ("#" * int(tag[1]) + " ") if re.fullmatch(r"h[1-6]", tag) else ("- " if tag == "li" else "")
        elif tag in CELLULES:
            if "".join(self.courant).strip():
                self.courant.append(" | ")
        elif self.apres_fin:  # « <b>Swiss FinTech Awards 2024</b><span>Lauréat</span> » : un espace entre les deux
            self.courant.append(" ")
        self.apres_fin = False

    def handle_endtag(self, tag):
        if tag in VIDES:
            return
        while self.pile:  # referme jusqu'à la balise correspondante (HTML tolérant)
            nom, exclue = self.pile.pop()
            if exclue:
                self.exclusion -= 1
            elif nom in BLOCS or nom in CONTENEURS:
                self._vider()
            if nom == tag:
                break
        self.apres_fin = True

    def handle_data(self, data):
        if not self.exclusion:
            self.courant.append(data)
            self.apres_fin = False

    def texte(self):
        self._vider()
        sortie = []
        for b in self.blocs:  # pas deux fois de suite la même ligne (titre répété par un intertitre visuel)
            if not sortie or sortie[-1] != b:
                sortie.append(b)
        return "\n\n".join(sortie)


def texte_principal(html):
    """Texte Markdown du <main> d'une page construite."""
    debut, fin = html.find("<main"), html.find("</main>")
    if debut < 0 or fin < 0:
        return ""
    lecteur = _Texte()
    lecteur.feed(html[debut:fin])
    lecteur.close()
    return lecteur.texte()


def llms_full_txt(pages, lire_html, date, langue="fr", t=lambda s: s):
    """pages : [(chemin publié, méta)] des pages indexables de la langue ; lire_html(page) : HTML construit de la page
    dans cette langue. langue et t : voir llms_txt."""
    metas = dict(pages)
    entete = ["# " + t(TITRE_COMPLET), "",
              "> " + H.unescape(metas.get("", {}).get("description", "")).strip(), "",
              remplir(t(INTRO_COMPLET), date, fichier("llms.txt", langue)), ""]
    parties = []
    for page in PAGES_COMPLETES:
        if page not in metas:
            continue
        corps = texte_principal(lire_html(page))
        parties.append(f"---\n\n{t(SOURCE)} {adresse(page, langue)}\n\n{corps}\n")
    return "\n".join(entete) + "\n" + "\n".join(parties)
