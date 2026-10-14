"""Post-traitement du lot A : relie à la page du plugin Word la première mention existante du plugin.

Mentions cherchées, telles qu'elles figurent dans les textes du site actuel : « Plugin MS Word natif »,
« plugin MS Word natif » et « plugin Microsoft Word » sur toutes les pages, plus « complément Corrext » sur la page
de l'éditeur de relecture. Dans <main>, la première mention située hors lien devient un lien vers
corrext/plugin-word/ ; le texte ne change pas.

Ne sont jamais touchés : ce qui est hors de <main>, les attributs (un « > » entre guillemets ne ferme pas la balise),
les commentaires, et le contenu des éléments où un lien n'a pas sa place : lien existant, script, style, template,
noscript, intitulé d'une question repliable, bouton, champ de formulaire, SVG, tout sous-arbre aria-hidden="true"
et tout écran simulé (attribut data-scene). Une page qui relie déjà la page du plugin, et la page du plugin
elle-même, restent telles quelles. Le lien du schéma « qui fait quoi » (section sec sp, lot D) ne compte pas : il
appartient à la définition de Corrext, pas au texte de la page.
"""
import re

CIBLE = "corrext/plugin-word/"
MENTIONS = r"[Pp]lugin MS Word natif|plugin Microsoft Word"
# Formulations propres à une page : elles s'ajoutent aux mentions communes sur cette page seulement
MENTIONS_PAGE = {"corrext/editeur-de-relecture/": "complément Corrext"}
# Éléments dont le contenu ne reçoit pas de lien ; script et style sont sautés d'un bloc jusqu'à leur fermeture
EXCLUS = {"a", "summary", "button", "label", "select", "option", "textarea", "svg", "title", "template", "noscript"}
BRUTS = {"script", "style"}
VIDES = {"area", "base", "br", "col", "embed", "hr", "img", "input", "link", "meta", "source", "track", "wbr"}
# Balise : commentaire, ou nom puis attributs ; une valeur entre guillemets peut contenir « > »
BALISE = re.compile(r"<(!--.*?--|/?)([a-zA-Z][\w-]*)?((?:\"[^\"]*\"|'[^']*'|[^'\">])*?)(/?)>", re.S)
# Sous-arbres exclus d'après leurs attributs : masqués aux technologies d'assistance, écrans simulés
CACHE = re.compile(r"(?:^|\s)aria-hidden\s*=\s*([\"']?)true\1|(?:^|\s)data-scene(?=[\s=/]|$)")
DEJA_RELIE = re.compile(r'href="\{\{ROOT\}\}(?:fr/)?' + re.escape(CIBLE) + '"')
SCHEMA = re.compile(r'<section class="sec sp"[^>]*>.*?</section>', re.S)


def lien(texte):
    return f'<a class="pw-lien" href="{{{{ROOT}}}}{CIBLE}">{texte}</a>'


def motif(page):
    """Mentions reliées sur une page : les communes, plus celle propre à la page s'il y en a une."""
    propre = MENTIONS_PAGE.get(page)
    return re.compile(MENTIONS + ("|" + re.escape(propre) if propre else ""))


def _premiere_mention(zone, mention):
    """Position (début, fin) de la première mention de zone située dans un texte qui peut recevoir un lien."""
    exclu, pos = None, 0  # exclu : [nom, profondeur] de l'élément exclu ouvert le plus externe
    while True:
        m = BALISE.search(zone, pos)
        fin_texte = m.start() if m else len(zone)
        if exclu is None:
            t = mention.search(zone, pos, fin_texte)
            if t:
                return t.start(), t.end()
        if not m:
            return None
        pos = m.end()
        tete, nom, attributs, auto = m.group(1), (m.group(2) or "").lower(), m.group(3) or "", m.group(4)
        if tete.startswith("!--") or not nom:
            continue
        if tete == "" and nom in BRUTS:
            fermeture = zone.find(f"</{nom}>", pos)
            pos = len(zone) if fermeture < 0 else fermeture + len(nom) + 3
            continue
        ouvrant = tete == "" and not auto and nom not in VIDES
        if exclu is not None:
            # dans un sous-arbre exclu, seuls comptent les éléments de même nom, pour trouver sa fermeture
            if nom == exclu[0]:
                exclu[1] += 1 if ouvrant else -1 if tete == "/" else 0
                if exclu[1] == 0:
                    exclu = None
            continue
        if ouvrant and (nom in EXCLUS or CACHE.search(attributs)):
            exclu = [nom, 1]


def traiter(html, page):
    if page == CIBLE:
        return html
    ouvre = re.search(r"<main\b[^>]*>", html)
    if not ouvre:
        return html
    debut = ouvre.end()
    fin = html.find("</main>", debut)
    if fin < 0:
        return html
    zone = html[debut:fin]
    if DEJA_RELIE.search(SCHEMA.sub("", zone)):
        return html
    trouve = _premiere_mention(zone, motif(page))
    if not trouve:
        return html
    a, b = trouve
    return html[:debut] + zone[:a] + lien(zone[a:b]) + zone[b:] + html[fin:]
