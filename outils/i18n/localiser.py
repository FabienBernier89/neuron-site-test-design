"""Localisation d'une page française assemblée dans une autre langue (tâche 1.3) : liens, tête, données structurées.

Trois fonctions, appelées par build.finaliser dans cet ordre :
- poser_alternates : balises hreflang de la tête, pour toutes les langues (français compris), d'après les pages
  réellement construites ; c'est elle qui décide quelles versions une page annonce ;
- localiser : liens vers la version de la langue, canonique et Open Graph, og:locale, inLanguage de la page, image de
  partage, champ « langue » des formulaires, liens Fedlex vers le texte de loi de la langue (Ruling 22) ; hors
  français seulement, et sans toucher aux balises alternate ;
- le reste de finaliser (images, dimensions, liens relatifs) est inchangé.

Le texte visible n'est pas de leur ressort (c'est la traduction, passe 2). Bibliothèque standard seulement."""
import re

from .langues import HREFLANG, ICI, LANGUES, OG_LOCALE, route

PRODUCTION = "https://neur-on.ai/"  # adresse du site publié (même valeur que build.PRODUCTION)
IMAGES = ICI / "assets/img"  # visuels du site : og-neuron-<langue>.png s'y trouve quand il a été produit
ATTRIBUT_LIEN_FR = "data-lien-fr"  # aperçu : lien d'une page traduite resté vers une page française non traduite

# Un seul passage sur la page, quatre formes reconnues. Une balise alternate est reconnue pour être laissée telle quelle.
_FORMES = re.compile(
    r'(?P<alternate><link rel="alternate"[^>]*>)'
    # lien relatif à la racine, dans n'importe quel attribut (href, data-retour) ; déjà localisé (de/, it/, en/) : ignoré
    r'|(?P<attr>[a-z-]+)="\{\{ROOT\}\}(?!(?:de|it|en)/)(?:fr/)?(?P<relatif>[^"#?]*)(?P<suite>[#?][^"]*)?"'
    # lien {{ROOT}}fr/<p> hors attribut : adresses des données de page (index de recherche de l'aide)
    r'|\{\{ROOT\}\}fr/(?P<explicite>[^"\'\s<>#?\\&]*)'
    # adresse de production d'une page française (canonique, og:url, données structurées)
    r'|https://neur-on\.ai/fr/(?P<absolu>[^"\'\s<>#?\\]*)')
_ALTERNATE_HREFLANG = re.compile(r'<link rel="alternate" hreflang="[^"]+" href="[^"]+">\n?')
_LANG_HTML = re.compile(r'<html lang="(?:fr|@LANG@)"')
_OG_LOCALE = re.compile(r'(<meta property="og:locale" content=")fr_CH(">)')
_IN_LANGUAGE = re.compile(r'("inLanguage"\s*:\s*)"fr-CH"')
_OG_IMAGE = re.compile(r'(<meta property="og:image" content=")https://neur-on\.ai/assets/img/og-neuron\.jpg(">)')
_CHAMP_LANGUE = re.compile(r'<input\b[^>]*\bname="langue"[^>]*>')
# Lien Fedlex vers la version française d'un acte : seule forme présente dans la sortie FR (relevé du 2026-10-25 :
# 52 liens, 17 actes, aucun paramètre de langue). Le segment de langue de l'ELI suit la langue de la page.
_FEDLEX = re.compile(r"""(https://(?:www\.)?fedlex\.admin\.ch/eli/cc/(?P<acte>[^/"'\s]+/[^/"'\s]+)/)fr(?=["'/#?])""")
# Fedlex ne publie l'anglais que d'une partie des actes. Règle de la V1 anglaise (lue dans ses pages, cohérente acte
# par acte) : lien anglais quand il existe, sinon texte allemand. Actes classés d'après la V1 ; un acte absent des deux
# listes mène au texte allemand (toujours publié) et le test test_actes_du_site_tous_classes_pour_l_anglais échoue,
# pour qu'on vérifie sur Fedlex.
FEDLEX_ANGLAIS = {
    "11/529_488_529", "1955/871_893_899", "1969/737_757_755", "1982/846_846_846", "1988/1776_1776_1776",
    "1993/1798_1798_1798", "1993/274_274_274", "1996/546_546_546", "1998/892_892_892", "1999/404", "2002/226",
    "2006/822", "2007/758", "2008/736", "2009/615", "2010/262", "2010/267", "2019/758", "2022/491",
    "24/233_245_233", "27/317_321_377", "54/757_781_799"}
FEDLEX_SANS_ANGLAIS = {
    "1966/371_385_384", "1966/57_57_57", "1991/1184_1184_1184", "1991/1256_1256_1256", "2004/320", "2005/734",
    "2006/218", "2007/686", "24/719_735_717", "51/117_121_129"}


def _fedlex(m, langue):
    """Adresse Fedlex de l'acte dans la langue de la page (anglais seulement s'il est publié, sinon allemand)."""
    cible = langue if langue != "en" or m.group("acte") in FEDLEX_ANGLAIS else "de"
    return m.group(1) + cible


def localiser(html, page, langue, construites, marquer=False):
    """(html, pages absentes) : la page française assemblée, localisée dans la langue (hors français, sinon rien ne
    change). Un lien ({{ROOT}}[fr/]<p> en attribut, {{ROOT}}fr/<p> ailleurs, ou https://neur-on.ai/fr/<p>) mène à l'adresse de la langue quand p est une page
    construite dans cette langue (construites[langue]) ; sinon il reste inchangé et p est renvoyée dans l'ensemble des
    pages absentes. Les ressources ({{ROOT}}assets/...) ne sont pas des pages.

    Tête : <html lang> prend le code court de la langue (de, it, en : décision 10), og:locale et l'inLanguage de la
    page (et d'elle seule : les termes du glossaire gardent le leur) prennent le code régional. L'image de partage
    og-neuron.jpg devient og-neuron-<langue>.png quand ce fichier existe ; les visuels d'articles restent. Un champ
    <input name="langue" value="fr"> prend la langue. Un lien Fedlex vers un acte en français (…/eli/cc/<acte>/fr) mène
    à l'acte dans la langue de la page ; en anglais, au texte allemand si Fedlex ne publie pas l'anglais de l'acte
    (FEDLEX_ANGLAIS, règle de la V1). marquer (aperçu, vague finale, point 13) : un lien href resté vers une page non
    traduite reçoit l'attribut data-lien-fr, pour le repérer dans la page."""
    if langue == "fr":
        return html, set()
    absentes = set()
    pages = construites.get(langue, ())

    def adresse(p):
        if p in pages:
            return route(p, langue)
        absentes.add(p)
        return None

    def sub(m):
        if m.group("alternate"):
            return m.group(0)
        if m.group("explicite") is not None:
            cible = adresse(m.group("explicite"))
            return m.group(0) if cible is None else "{{ROOT}}" + cible
        if m.group("absolu") is not None:
            cible = adresse(m.group("absolu"))
            return m.group(0) if cible is None else PRODUCTION + cible
        if m.group("relatif").startswith("assets/"):
            return m.group(0)
        cible = adresse(m.group("relatif"))
        if cible is None:
            return m.group(0) + (" " + ATTRIBUT_LIEN_FR if marquer and m.group("attr") == "href" else "")
        return f'{m.group("attr")}="{{{{ROOT}}}}{cible}{m.group("suite") or ""}"'

    html = _FORMES.sub(sub, html)
    html = _LANG_HTML.sub(f'<html lang="{langue}"', html, count=1)
    html = _OG_LOCALE.sub(rf"\g<1>{OG_LOCALE[langue]}\g<2>", html)
    html = _IN_LANGUAGE.sub(rf'\1"{HREFLANG[langue]}"', html)
    if (IMAGES / f"og-neuron-{langue}.png").is_file():
        html = _OG_IMAGE.sub(rf"\g<1>{PRODUCTION}assets/img/og-neuron-{langue}.png\g<2>", html)
    html = _CHAMP_LANGUE.sub(lambda m: m.group(0).replace('value="fr"', f'value="{langue}"'), html)
    html = _FEDLEX.sub(lambda m: _fedlex(m, langue), html)
    return html, absentes


def alternates(page, construites):
    """[(hreflang, adresse de production)] d'une page : ses versions construites dans l'ordre de LANGUES, puis
    ("x-default", version de repli). Avec le seul français : [("fr-CH", u), ("x-default", u)]. Décision V7 : x-default
    désigne la version anglaise dès qu'elle est construite (même langue que le repli de la racine), sinon la française."""
    francais = PRODUCTION + "fr/" + page  # déduite de la page : une page française absente de la table est permise
    versions = [(HREFLANG[l], francais if l == "fr" else PRODUCTION + route(page, l))
                for l in LANGUES if page in construites.get(l, ())]
    anglais = PRODUCTION + route(page, "en") if page in construites.get("en", ()) else None
    return versions + [("x-default", anglais or francais)]


def poser_alternates(html, page, construites):
    """Remplace toutes les balises <link rel="alternate" hreflang> de la tête par alternates(page, construites), à la
    place de la première. Une page sans alternate (la 404) est rendue telle quelle."""
    tete, fin, reste = html.partition("</head>")
    if not _ALTERNATE_HREFLANG.search(tete):
        return html
    balises = "".join(f'<link rel="alternate" hreflang="{hl}" href="{url}">\n' for hl, url in alternates(page, construites))
    premiere = []

    def sub(m):
        if premiere:
            return ""
        premiere.append(m)
        return balises

    return _ALTERNATE_HREFLANG.sub(sub, tete) + fin + reste
