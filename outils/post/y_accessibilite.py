"""Accessibilité (audit du 2026-10-23, docs/audits/2026-10-23-neuron-v2/annexe-perf.md). Nommé « y_ » pour passer
après les post-traitements qui posent les blocs concernés (cartes .fx-g de fonctionnalites.py), avant z_formulaires.

- Bouton pause des animations en boucle (WCAG 2.2.2) : un par scène animée (.st[data-sim], câblé par assets/sim.js)
  et un par grille de cartes animées (.fx-g, câblé par assets/global/animations.js). Le bouton naît masqué (hidden) :
  le script l'affiche, sauf en mouvement réduit, où rien ne bouge. Libellés lus dans src/data/contenus-v2.
- Listes d'onglets (role="tablist") : nommées par le titre h2 de leur section (aria-labelledby).
- Passages en allemand, anglais ou italien dont la langue est connue (WCAG 3.1.2) : lignes alignées de CHnell (langues
  affichées dans la barre de recherche), cellules des tableaux de termes (data-m="Allemand"...), tuiles « quatre langues »
  et terme du h1 du glossaire, avis et encart d'aide en anglais des écrans Corrext reproduits.
- Données des démos gardées dans leur langue sur toutes les versions du site (tâche 7.3) : les résultats réels de CHnell
  (Ruling 26 ; exemple de loi du glossaire, tâche 3.3, et démos des autres pages : fenêtre CHnell et schéma de
  l'accueil, résultats du panneau Word) portent un lang explicite, français compris, et leur référence (« SR-220 ...
  Data Set: Neur.on ») translate="no" ; les sources françaises des écrans de démo et les réécritures Rephrasing (françaises, comme dans la V1,
  où elles s'affichaient en français dans chaque langue) portent lang="fr" (Ruling 14). Un passage lang="fr" explicite
  n'est jamais traduit ; il ne change rien à la page française.
- Écrans de l'application reproduits (zones data-ui, vague finale, point 3) : les textes de l'interface en anglais
  (barres, menus, panneau de Word, commande d'extraits) et les sorties de démo anglaises portent lang="en" : en anglais
  dans toutes les langues du site, comme dans l'application et dans la V1, hors traduction (langues_ecrans).

Aucun texte affiché n'est ajouté ici. Idempotent : repasser une page déjà traitée ne la change pas."""
import html as H
import re

from outils import contenus

# Noms de langue affichés (interface Corrext en anglais, pages en français) et code BCP 47
CODES = {"German": "de", "Allemand": "de", "English": "en", "Anglais": "en", "Italian": "it", "Italien": "it",
         "French": "fr", "Français": "fr"}

PAUSE = ('<svg class="ap-pause" viewBox="0 0 16 16" aria-hidden="true" focusable="false"><rect x="4" y="3" width="2.6" '
         'height="10" rx="1"/><rect x="9.4" y="3" width="2.6" height="10" rx="1"/></svg>')
LECTURE = ('<svg class="ap-lecture" viewBox="0 0 16 16" aria-hidden="true" focusable="false"><path d="M5 3.2v9.6a.6.6 0 0 0 '
           '.9.5l7.4-4.8a.6.6 0 0 0 0-1L5.9 2.7a.6.6 0 0 0-.9.5z"/></svg>')
SCENE = re.compile(r'(<div class="st" data-sim="[^"]*"[^>]*>)(?!<button type="button" class="anim-pause)')
GRILLE = re.compile(r'(?<!</button>)(<div class="fx-g(?: [^"]*)?">)')
ONGLETS = re.compile(r'(<h2\b[^>]*>)((?:(?!<h2\b|role="tablist").)*?)(<div class="mt-os" role="tablist")(?=>)', re.S)


def _a(s):
    return H.escape(s, quote=True)


def bouton(classe):
    """Bouton pause / lecture : le nom change avec l'état (data-pause, data-relancer), l'icône suit (CSS)."""
    pause, relancer = contenus.texte("a11y.animation.pause"), contenus.texte("a11y.animation.relancer")
    return (f'<button type="button" class="anim-pause {classe}" hidden aria-label="{_a(pause)}" '
            f'data-pause="{_a(pause)}" data-relancer="{_a(relancer)}">{PAUSE}{LECTURE}</button>')


def boutons_pause(html):
    html = SCENE.sub(lambda m: m.group(1) + bouton("sim-pp"), html)
    return GRILLE.sub(lambda m: bouton("fx-pp") + m.group(1), html)


def onglets_nommes(html):
    """Chaque liste d'onglets reçoit aria-labelledby vers le h2 qui la précède dans sa section."""
    n = [0]

    def nommer(m):
        h2, entre, liste = m.groups()
        ident = re.search(r'\sid="([^"]+)"', h2)
        if ident:
            ident = ident.group(1)
        else:
            n[0] += 1
            ident = f"onglets-titre-{n[0]}"
            h2 = h2[:-1] + f' id="{ident}">'
        return h2 + entre + liste + f' aria-labelledby="{ident}"'
    if 'role="tablist" aria-labelledby' in html:
        return html
    return ONGLETS.sub(nommer, html)


def _lang(balise, code, francais=False):
    """Pose lang sur une balise ouvrante qui n'en a pas (le français, langue de la page, n'est pas répété, sauf si
    `francais` : un passage français voulu, qui doit le rester sur une page traduite)."""
    if not code or (code == "fr" and not francais) or " lang=" in balise:
        return balise
    return balise[:-1] + f' lang="{code}">'


LIGNE =re.compile(r'(<div style="--i:\d+">)(<p>)(.*?</p>)(<p>)')


def langues_chnell(html, francais=False):
    """Lignes alignées de CHnell : la 1re colonne dans la langue de gauche (lk-l1), la 2e dans celle de droite (lk-l2) ;
    le terme recherché (lk-q) dans la langue de gauche ; la référence de chaque ligne translate="no". francais : le
    français d'une ligne et du terme porte lang="fr" explicite (résultats gardés en français sur une page traduite)."""
    sortie, pos = [], 0
    for q in re.finditer(r'<div class="cr-ch-q">', html):
        if q.start() < pos:
            continue
        l1 = re.search(r'<span class="cr-lang lk-l1">([^<]*)</span>', html[q.start():q.start() + 2000])
        l2 = re.search(r'<span class="cr-lang lk-l2">([^<]*)</span>', html[q.start():q.start() + 2000])
        lr = html.find('<div class="lk-r">', q.start())
        if not (l1 and l2) or lr < 0:
            continue
        a, b = CODES.get(l1.group(1).strip()), CODES.get(l2.group(1).strip())
        if not (a or b):
            continue
        # fin des lignes : pied de la fenêtre CHnell, sinon bloc CHnell suivant ou fin de la section
        bornes = [html.find(b, lr) for b in ('<div class="cr-ch-f">', '<div class="cr-ch-q">', "</section>")]
        fin = min([b for b in bornes if b >= 0] or [len(html)])
        bloc = html[q.start():fin]
        bloc = re.sub(r'<b class="lk-q">', lambda m: _lang(m.group(0), a, francais), bloc, count=1)
        bloc = LIGNE.sub(lambda m: m.group(1) + _lang(m.group(2), a, francais) + m.group(3) + _lang(m.group(4), b, francais),
                         bloc)
        bloc = bloc.replace("</p><small>", '</p><small translate="no">')  # référence du segment (source, jeu de données)
        sortie.append(html[pos:q.start()] + bloc)
        pos = fin
    return "".join(sortie) + html[pos:]


def langues_schema(html):
    """Fenêtre CHnell du schéma « qui fait quoi » (sp-app-ch) : chaque segment (sp-seg) dans la langue de sa colonne
    (sp-lg, dans l'ordre), le terme recherché dans la première, la référence translate="no" (Ruling 26)."""
    sortie, pos = [], 0
    for m in re.finditer(r'<div class="sp-app sp-app-ch">', html):
        fin = html.find("</dd>", m.start())
        fin = len(html) if fin < 0 else fin
        bloc = html[m.start():fin]
        codes = [CODES.get(x.strip()) for x in re.findall(r'<span class="sp-lg">([^<]*)</span>', bloc)]
        if codes and all(codes):
            rang = iter(codes)
            bloc = re.sub(r'<span class="sp-seg">', lambda s: _lang(s.group(0), next(rang, None), True), bloc)
            bloc = re.sub(r'(<span class="sp-box">(?:(?!</span>).)*?)<b>', lambda s: s.group(1) + _lang("<b>", codes[0], True),
                          bloc, count=1, flags=re.S)
        bloc = bloc.replace('<small class="sp-src">', '<small class="sp-src" translate="no">')
        sortie.append(html[pos:m.start()] + bloc)
        pos = fin
    return "".join(sortie) + html[pos:]


def langues_word(html):
    """Résultats du Fast Lookup du panneau Word (wd-r : mémoire de traduction et CHnell, démo du français vers
    l'allemand) : la source française lang="fr", la référence (document, source CHnell) translate="no" (Ruling 26)."""
    def ligne(m):
        r = re.sub(r"^(<div[^>]*>)(<p>)", lambda p: p.group(1) + _lang(p.group(2), "fr", True), m.group(0))
        return r.replace("<small>", '<small translate="no">')
    return re.sub(r'<div class="wd-r" style="--i:\d+">(?:(?!</div>).)*</div>', ligne, html, flags=re.S)


# Sources françaises des écrans de démo et réécritures Rephrasing (toujours françaises) : lang="fr" (Ruling 14)
SOURCES_FR = ("cr-rtxt", "cr-rout", "cr-ill", "ap-src", "wd-s", "wd-ms", "cxe-src")
# Zones de texte d'une démo dont la source est française ou anglaise selon l'écran : lang="fr" si le texte est français
TEXTES_SOURCE = ("cr-txt", "sp-txt")
_OUVRANTE = re.compile(r'<(p|span|div|td)\b[^>]*\bclass="([^"]*)"[^>]*>')
_MOTS_FR = {"le", "la", "les", "des", "du", "de", "au", "aux", "l", "d", "à", "un", "une", "et", "en"}


def _francais(texte):
    """Texte français d'une zone source : au moins deux mots outils français (« Le débiteur en demeure doit des... »,
    jamais « The company must deduct... »)."""
    mots = re.findall(r"[^\W\d_]+", H.unescape(re.sub(r"<[^>]+>", " ", texte)).lower())
    return sum(m in _MOTS_FR for m in mots) >= 2


def sources_francaises(html):
    """lang="fr" sur les sources françaises des démos (SOURCES_FR, TEXTES_SOURCE dont le texte est français, source de
    l'exemple de traduction d'un comparatif)."""
    def poser(m):
        classes = set(m.group(2).split())
        if classes & set(SOURCES_FR):
            return _lang(m.group(0), "fr", True)
        if classes & set(TEXTES_SOURCE):
            fin = html.find("</" + m.group(1), m.end())
            if fin > m.end() and _francais(html[m.end():fin]):
                return _lang(m.group(0), "fr", True)
        return m.group(0)
    html = _OUVRANTE.sub(poser, html)
    # exemple de traduction d'un comparatif (« Source · français », puis les sorties des moteurs, déjà lang="it")
    return re.sub(r'(<div class="cp-xs"><p class="cp-xe">[^<]*</p>)(<p>)', lambda m: m.group(1) + _lang(m.group(2), "fr", True),
                  html)


def langues_tableaux(html):
    """Cellules des tableaux de termes, étiquetées par leur colonne (data-m) ; tuiles « quatre langues » du glossaire
    (<b>terme</b><p>Allemand</p>) ou fiche des langues (<dt>Allemand</dt><dd>terme</dd>) ; terme du h1 du glossaire, s'il
    figure dans l'une ou l'autre."""
    html = re.sub(r'<(th|td)\b[^>]*\sdata-m="([^"]+)"[^>]*>', lambda m: _lang(m.group(0), CODES.get(m.group(2))), html)
    tuiles = {}

    def tuile(m):
        code = CODES.get(m.group(3))
        tuiles[H.unescape(m.group(2)).strip()] = code
        return _lang(m.group(1), code) + m.group(2) + "</b><p>" + m.group(3) + "</p>"
    html = re.sub(r'(<b>)([^<]+)</b><p>(Allemand|Français|Italien|Anglais)</p>', tuile, html)
    # fiche des langues du glossaire (langue, terme ; audit design du 2026-10-23) : la langue y est déjà posée
    for m in re.finditer(r'<dt>(Allemand|Français|Italien|Anglais)</dt><dd lang="([a-z]{2})">([^<]+)</dd>', html):
        tuiles[H.unescape(m.group(3)).strip()] = m.group(2)
    h1 = re.search(r'(<h1 class="h1"><span class="n")(>)([^<]+?)( ·)?</span>', html)
    if h1 and tuiles.get(H.unescape(h1.group(3)).strip()):
        code = tuiles[H.unescape(h1.group(3)).strip()]
        if code != "fr" and " lang=" not in h1.group(1):
            html = html[:h1.start()] + h1.group(1) + f' lang="{code}"' + html[h1.start(2):]
    return html


def langues_interface(html):
    """Avis et encart d'aide de l'écran Corrext reproduit : phrases de l'interface, en anglais dans l'application."""
    html = html.replace('<div class="cr-notice">', '<div class="cr-notice" lang="en">')
    return re.sub(r'(<div class="cr-hint"><div class="cr-ill"[^>]*>(?:[^<]|</?mark>)*</div>)<div>', r'\1<div lang="en">', html)


# Écrans de l'application reproduits (zones data-ui) : textes de l'interface, en anglais dans l'application et donc dans
# toutes les langues du site, comme les colonnes CHnell (Ruling 26) et comme la V1, qui les gardait en anglais. Relevé du
# 2026-10-26 (vague finale, point 3) : 96 textes d'écran sans traduction sur le site, dont 28 sur les deux pages pilotes ;
# les anglais sont repérés par leur classe (zone toujours anglaise), par leur texte exact (libellé dont la classe sert aussi
# à des écrans en français) ou, pour les sorties de démo, par leur langue (_anglais). Les écrans en français (parcours
# de devis, ruban de Word, onglets Projets) gardent leur texte, traduit comme le reste.
CLASSES_EN = frozenset((
    "cr-ch-h", "sp-pw", "sp-top", "sp-bar", "sp-lkb", "sp-cnt", "sp-dom", "lk-c",        # CHnell et Corrext du schéma
    "cr-top", "cr-src", "cr-set", "cr-tgtsel", "cr-drop", "cr-file", "cr-alt-ph",        # Corrext : barres et menus
    "vw-ord", "vw-niv-c", "vw-tag",                                                       # commande d'extraits du registre
    "wd-ph", "wd-live", "wd-go", "wd-seg", "wd-rh", "wd-ml", "wd-ma", "wd-o"))            # panneau Corrext de Word
TEXTES_EN = re.compile("|".join((
    r"powered by Neur\.on", r"Home", r"Upload your file\(s\)", r"Translation target language", r"AI Assistant", r"Matches", r"Sync",
    r"Find the company", r"Select the certification level", r"Choose the delivery method", r"Set the delivery timeline",
    r"Choose the level required by the recipient of the translation\.")))
LANGUES_EN = {"German": "en", "French": "en", "English": "en", "Italian": "en"}  # noms anglais des langues de l'interface
CLASSES_LANGUE = frozenset(("cr-lang", "sp-lg"))  # nom d'une langue : anglais dans l'interface, sinon laissé (« Français »)
SORTIES = frozenset(("cr-out", "cr-alt", "cr-txt", "sp-out", "sp-txt"))  # sorties et sources de démo : selon leur langue
CLASSES_CODE = frozenset(("ap-h", "ap-req", "ap-st"))  # requête et réponse de l'exemple d'API : du code, translate="no"
_MOTS_EN = {"the", "of", "to", "in", "and", "a", "an", "shall", "be", "is", "with", "for", "by", "at", "from", "it", "its",
            "must", "when", "has", "been", "per", "without", "who", "which", "on"}
_BALISE = re.compile(r"<(/?)([a-zA-Z][a-zA-Z0-9-]*)\b([^>]*)>")
_VIDES = {"area", "base", "br", "col", "embed", "hr", "img", "input", "link", "meta", "param", "source", "track", "wbr",
          "path", "circle", "rect", "line", "polyline", "polygon", "ellipse", "use", "stop"}


def _anglais(texte):
    """Texte anglais d'une sortie de démo : au moins deux mots outils anglais et plus que de mots outils français
    (« The debtor in default shall owe... », jamais « Le débiteur en demeure doit... »)."""
    mots = re.findall(r"[^\W\d_]+", H.unescape(re.sub(r"<[^>]+>", " ", texte)).lower())
    en, fr = sum(m in _MOTS_EN for m in mots), sum(m in _MOTS_FR for m in mots)
    return en >= 2 and en > fr


def _elements_ecran(html):
    """Éléments à l'intérieur d'une zone data-ui : [(début de la balise ouvrante, fin de celle-ci, début de la fermante,
    attributs)], dans l'ordre du document."""
    pile, sortie = [], []
    for m in _BALISE.finditer(html):
        fermant, nom, attrs = m.group(1), m.group(2).lower(), m.group(3)
        if nom in _VIDES or attrs.rstrip().endswith("/"):
            continue
        if not fermant:
            ui = (pile[-1][3] if pile else False) or re.search(r"\sdata-ui(?:[\s=>]|$)", attrs) is not None
            pile.append((nom, m.start(), m.end(), ui, attrs, pile[-1][3] if pile else False))
            continue
        for i in range(len(pile) - 1, -1, -1):
            if pile[i][0] == nom:
                _, debut, fin_ouvrante, _, attributs, dans_ui = pile[i]
                del pile[i:]
                if dans_ui:
                    sortie.append((debut, fin_ouvrante, m.start(), attributs))
                break
    return sorted(sortie)


def langues_ecrans(html):
    """lang="en" sur les textes anglais des écrans de l'application (zones data-ui) : CLASSES_EN, TEXTES_EN, noms anglais
    des langues (CLASSES_LANGUE), sorties de démo anglaises (SORTIES, _anglais). Le terme cherché dans le panneau Word
    (wd-q) prend la langue des résultats qui le suivent ; la requête et la réponse de l'exemple d'API (CLASSES_CODE), du
    code, prennent translate="no". Un élément qui porte déjà lang ou translate est laissé ; ses descendants aussi."""
    poses, couverts = [], []
    for debut, fin_ouvrante, fermante, attrs in _elements_ecran(html):
        if any(a <= debut < b for a, b in couverts):
            continue
        if re.search(r"\s(?:lang|translate)=", attrs):
            couverts.append((debut, fermante))
            continue
        classes = set((re.search(r'\sclass="([^"]*)"', attrs) or [None, ""])[1].split())
        texte = " ".join(H.unescape(re.sub(r"<[^>]+>", " ", html[fin_ouvrante:fermante])).split())
        code = None
        if classes & CLASSES_EN or (texte and TEXTES_EN.fullmatch(texte)):
            code = "en"
        elif classes & CLASSES_LANGUE:
            code = LANGUES_EN.get(texte)
        elif classes & SORTIES and _anglais(texte):
            code = "en"
        elif classes & CLASSES_CODE:
            code = "code"
        elif "wd-q" in classes:
            suite = re.search(r'\slang="(de|it|en)"', html[fermante:fermante + 3000])
            code = suite.group(1) if suite else None
        if code:
            poses.append((fin_ouvrante, code))
            couverts.append((debut, fermante))
    for fin_ouvrante, code in sorted(poses, reverse=True):
        attribut = ' translate="no"' if code == "code" else f' lang="{code}"'
        html = html[:fin_ouvrante - 1] + attribut + html[fin_ouvrante - 1:]
    return html


def traiter(html, page):
    # résultats CHnell (exemple de loi du glossaire compris) : le français y reste du français sur les pages traduites
    # (glossaire, allemand : l'exemple est allemand et français ; italien et anglais : le français est remplacé par la
    # langue de la page, tâche 3.3 ; ailleurs : résultats réels de l'application, Ruling 26)
    debut = html.find('<main id="main">')
    if debut < 0:
        return html
    tete, corps = html[:debut], html[debut:]
    corps = boutons_pause(corps)
    corps = onglets_nommes(corps)
    corps = langues_chnell(corps, francais=True)
    corps = langues_schema(corps)
    corps = langues_word(corps)
    corps = sources_francaises(corps)
    corps = langues_tableaux(corps)
    corps = langues_interface(corps)
    corps = langues_ecrans(corps)
    return tete + corps
