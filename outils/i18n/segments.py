"""Découpe de la page FR assemblée en segments à traduire, et réinjection des traductions.

Copie de l'extracteur de la V1 (Sites/neuron/outils/segments.py : découpe en blocs, protection des balises en ligne
par des marqueurs {n}…{/n}, restauration), étendue pour la page complète telle que le build l'assemble :
- la tête (<title>, content des métas de texte), le corps, les attributs lisibles ou lus par les scripts ;
- le JSON-LD (sans alternateName) et les JSON de données (index du centre d'aide) ;
- les exclusions : sous-arbres dont le lang n'est pas fr, éléments translate="no" ou de CLASSES_NON_TRADUITES,
  attributs classés « jamais » ;
- le drapeau ui (écran d'application, ancêtre [data-ui]) et le drapeau lang_fr (passage en français voulu ; un élément en
  ligne lang="fr" coupe le passage qui l'entoure, comme un élément étranger).

Un segment est une unité {id, genre, debut, fin, html, texte, table, ui, attr, lang_fr} :
- genre « bloc » : passage de texte continu avec ses balises en ligne, remplacées par des marqueurs (texte, table) ;
- genre « attr » : valeur d'un attribut (attr = son nom ; « content » pour une méta) ;
- genre « ld » et « json » : chaîne d'un JSON-LD ou d'un JSON de données (texte brut, lu en textContent).

Les unités de genre « attr » portées par une balise en ligne à l'intérieur d'un passage sont des unités à part, dont
la plage est comprise dans celle du passage : reinjecter_page les traduit aussi dans les balises restaurées du passage.

Bibliothèque standard seulement."""
import bisect
import html
import json
import re

# ---------- copie de la V1 : découpe en blocs et marqueurs ----------

EN_LIGNE = {"a", "strong", "b", "em", "i", "mark", "span", "abbr", "br", "q", "code", "small", "sup", "sub",
            "time", "u", "s", "tspan", "kbd"}
VIDES = {"br", "img", "wbr"}
# clés JSON jamais traduites : identifiants, chemins, dimensions, équivalents officiels déjà fixés
TECH = {"slug", "icone", "vis", "href", "url", "src", "date", "maj", "w", "h", "id", "ancre",
        "vignette", "lien", "de", "fr", "it", "en", "exemple", "cle", "nav", "hero", "lastmod", "categorie",
        "sous_categorie", "auteur_personne", "mentions", "date_affichee", "u", "outil", "espace",
        "temoignage_exemple", "exemple_flag", "type", "langues", "page", "source_num"}
# valeur en forme d'identifiant (« generee », « francais-allemand », « kuendigung ») : jamais traduite
IDENT = re.compile(r"[a-z0-9]+(?:[-_][a-z0-9]+)*")
LETTRE = re.compile(r"[A-Za-zÀ-ÖØ-öø-ÿ]")
JETON = re.compile(r"\{\{[^}]+\}\}")
PLACE = re.compile(r"\{\d+\}")  # emplacement d'un gabarit T("{0} actualités").format(n)
CHEMIN = re.compile(r"^(https?:|mailto:|tel:|/|\{\{ROOT\}\}|fr/|assets/|#)")


def _nom(tag):
    m = re.match(r"</?\s*([a-zA-Z0-9-]+)", tag)
    return m.group(1).lower() if m else ""


def proteger(fragment):
    """HTML en ligne -> (texte à traduire avec marqueurs, table des marqueurs)."""
    jetons = re.findall(r"\{\{[^}]+\}\}|\{\d+\}|<[^>]+>|[^<{]+|[<{]", fragment)
    sortie, table, pile, n = [], {}, [], 0
    # numérotation : une ouverture ou un élément vide prend un numéro ; la fermeture reprend celui de l'ouverture
    fermees = set()
    ouvertures = []
    for i, j in enumerate(jetons):
        if j.startswith("<") and not j.startswith("</") and _nom(j) not in VIDES and not j.endswith("/>"):
            ouvertures.append(i)
    appariement = {}
    for i, j in enumerate(jetons):
        if j.startswith("</"):
            nom = _nom(j)
            for k in range(len(pile) - 1, -1, -1):
                if _nom(jetons[pile[k]]) == nom:
                    appariement[pile[k]] = i
                    fermees.add(i)
                    del pile[k:]
                    break
        elif j.startswith("<") and i in ouvertures:
            pile.append(i)
    num = {}
    for i, j in enumerate(jetons):
        if JETON.fullmatch(j) or PLACE.fullmatch(j) or (j.startswith("<") and not j.startswith("</")):
            n += 1
            num[i] = n
            if i in appariement:
                table[n] = {"ouvre": j, "ferme": jetons[appariement[i]]}
                num[appariement[i]] = n
                sortie.append("{%d}" % n)
            else:
                table[n] = {"vide": j}
                sortie.append("{%d}" % n)
        elif j.startswith("</"):
            if i in fermees:
                sortie.append("{/%d}" % num[i])
            else:  # fermeture orpheline : élément vide
                n += 1
                table[n] = {"vide": j}
                sortie.append("{%d}" % n)
        else:
            sortie.append(html.unescape(j))
    return "".join(sortie), table


_MARQ = re.compile(r"\{\s*(/?)\s*(\d+)\s*\}")


def restaurer(texte, table):
    """Texte traduit avec marqueurs -> HTML. Lève ValueError si un marqueur manque, est en double ou dans le désordre.
    Les espaces de la traduction sont gardées telles quelles, y compris à l'intérieur d'une paire de marqueurs."""
    vus = {}
    for m in _MARQ.finditer(texte):
        vus.setdefault((m.group(1), int(m.group(2))), []).append(m.start())
    for n, e in table.items():
        if "vide" in e:
            if len(vus.get(("", n), [])) != 1:
                raise ValueError(f"marqueur {{{n}}} absent ou en double")
        else:
            o, f = vus.get(("", n), []), vus.get(("/", n), [])
            if len(o) != 1 or len(f) != 1 or o[0] > f[0]:
                raise ValueError(f"marqueurs {{{n}}}…{{/{n}}} absents, en double ou inversés")
    if any(int(m.group(2)) not in table for m in _MARQ.finditer(texte)):
        raise ValueError("marqueur inconnu")
    # marqueurs écrits avec des espaces (« { /1 } ») remis en forme ; les espaces autour des marqueurs sont celles de
    # la traduction, gardées telles quelles (la V1 rognait celle d'avant « {/n} » : « l'interview {/1}! »)
    texte = _MARQ.sub(lambda m: "{%s%s}" % (m.group(1), m.group(2)), texte)
    morceaux, pos = [], 0
    for m in re.finditer(r"\{(/?)(\d+)\}", texte):
        morceaux.append(html.escape(texte[pos:m.start()], quote=False))
        e = table[int(m.group(2))]
        morceaux.append(e["vide"] if "vide" in e else (e["ferme"] if m.group(1) else e["ouvre"]))
        pos = m.end()
    morceaux.append(html.escape(texte[pos:], quote=False))
    return "".join(morceaux)


def _a_du_texte(fragment):
    t = PLACE.sub("", JETON.sub("", re.sub(r"<[^>]+>", "", fragment)))
    return bool(LETTRE.search(html.unescape(t)))


# ---------- texte français écrit par un script (tâche 7.3) ----------

# Lettres accentuées du français (ni ä, ö, ü, ß : allemand) ; un seul de ces caractères suffit.
_ACCENTS_FR = frozenset("éèêëàâçùûîïôœÉÈÊËÀÂÇÙÛÎÏÔŒ")
# Mots du français sans accent, assez sûrs pour qu'un seul suffise : mots outils (sans « a », « on », « plus », « son »,
# communs à l'anglais) et mots d'interface (« Retirer », « 1 jour ») qu'un libellé d'un seul mot peut porter.
MOTS_FR = frozenset((
    "le", "la", "les", "un", "une", "des", "du", "de", "au", "aux", "et", "ou", "est", "sont", "ce", "cet", "cette",
    "ces", "qui", "que", "dont", "dans", "pour", "avec", "sans", "sur", "sous", "par", "vers", "chez", "entre", "ne",
    "pas", "se", "sa", "ses", "leur", "leurs", "votre", "vos", "notre", "nos", "nous", "vous", "il", "ils", "elle",
    "elles", "je", "tu", "en", "tout", "tous", "toute", "toutes", "aucun", "aucune",
    "oui", "non", "retirer", "ajouter", "fermer", "ouvrir", "replier", "supprimer", "annuler", "valider", "confirmer",
    "enregistrer", "rechercher", "copier", "effacer", "choisir", "choisissez", "cliquez", "appliquer", "calculer",
    "suivant", "jour", "jours", "heure", "heures", "semaine", "mois", "fichier", "fichiers", "langue", "langues",
    "projet", "projets", "devis", "relecture", "traduction", "traductions", "panneau"))
# élision du français (« l'intérêt », « d'un ») : la lettre est un mot entier, suivi d'une apostrophe et d'une lettre ;
# « project's » ou « I'd » n'en sont pas
_ELISION = re.compile(r"(?<![^\W\d_])(?:l|d|qu|n|s|c|j)['’](?=[^\W\d_])", re.I)
# Mots outils allemands : un texte allemand (« des Betrages ») n'est pas pris pour du français
MOTS_DE = frozenset(("der", "die", "das", "und", "ist", "nicht", "mit", "von", "dem", "den", "ein", "eine", "zu",
                     "im", "auf", "zum", "zur", "wird", "werden"))
_MOT_FR = re.compile(r"[^\W\d_]+")
_CODE = re.compile(r"[a-z][A-Za-z0-9_-]*")  # clé, code de langue, événement, classe : jamais du texte
_CHEMIN_JS = re.compile(r"\S*/\S*")  # adresse ou chemin sans espace (« ../fr/protection-des-donnees/ »)
# avant un « / », ces signes et ces mots ouvrent une expression régulière (sinon c'est une division)
_AVANT_REGEX = set("(,=:[!&|?{};+-*%<>~^")
_MOTS_AVANT_REGEX = {"return", "typeof", "instanceof", "in", "of", "new", "delete", "void", "throw", "case", "do", "else"}


def litteraux_js(code):
    """Chaînes littérales d'un code JavaScript ('…', "…", `…`), échappements résolus, sans les commentaires ni les
    expressions régulières (/int[ée]r[êe]ts?/gi). Analyse lexicale simple, suffisante pour les scripts du site."""
    sortie, i, n, dernier = [], 0, len(code), ""
    while i < n:
        c = code[i]
        if code.startswith("//", i):
            i = code.find("\n", i)
            i = n if i < 0 else i
        elif code.startswith("/*", i):
            i = code.find("*/", i + 2)
            i = n if i < 0 else i + 2
        elif c in "'\"`":
            j, morceaux = i + 1, []
            while j < n and code[j] != c:
                if code[j] == "\\" and j + 1 < n:
                    suivant = code[j + 1]
                    morceaux.append({"n": "\n", "t": "\t", "r": ""}.get(suivant, suivant))
                    j += 2
                else:
                    morceaux.append(code[j])
                    j += 1
            sortie.append("".join(morceaux))
            i, dernier = j + 1, "chaine"
        elif c == "/" and (dernier in _AVANT_REGEX or dernier in _MOTS_AVANT_REGEX or not dernier):
            j, classe = i + 1, False
            while j < n and (classe or code[j] != "/") and code[j] != "\n":
                if code[j] == "\\":
                    j += 1
                elif code[j] == "[":
                    classe = True
                elif code[j] == "]":
                    classe = False
                j += 1
            j += 1
            while j < n and code[j].isalpha():  # drapeaux
                j += 1
            i, dernier = j, "regex"
        elif c.isspace():
            i += 1
        elif c.isalnum() or c in "_$":
            j = i
            while j < n and (code[j].isalnum() or code[j] in "_$"):
                j += 1
            dernier, i = code[i:j], j
        else:
            dernier, i = c, i + 1
    return sortie


def est_francais(texte):
    """Vrai si une chaîne (HTML compris) porte du texte français : une lettre accentuée du français, ou un mot de MOTS_FR
    ou une élision (« l'intérêt »), sans mot outil allemand. Une chaîne d'un seul mot en minuscules (clé, code « de »,
    classe, événement) ou un chemin sans espace n'en est pas."""
    t = html.unescape(re.sub(r"<[^>]*>", " ", texte))
    if not LETTRE.search(t) or _CODE.fullmatch(t.strip()) or _CHEMIN_JS.fullmatch(t.strip()):
        return False
    if _ACCENTS_FR & set(t):
        return True
    mots = {m.lower() for m in _MOT_FR.findall(t)}
    return bool(mots & MOTS_FR or _ELISION.search(t)) and not (mots & MOTS_DE)


def francais_des_scripts(source):
    """Chaînes françaises des scripts d'une page (hors JSON : JSON-LD, index de l'aide, textes et données des démos,
    lus par extraire_page ou exclus par translate="no"), dans l'ordre de la page."""
    trouves = []
    for m in re.finditer(r"<script\b([^>]*)>(.*?)</script>", source, re.S):
        if "json" in m.group(1):
            continue
        trouves += [s for s in litteraux_js(m.group(2)) if est_francais(s)]
    return trouves


def scripts_a_traduire(source):
    """Vrai si un script de la page écrit du texte français que l'extraction ne voit pas (francais_des_scripts) ; un mot
    seul compte (« Retirer »). Les libellés anglais de l'application et les données dans leur langue ne comptent pas."""
    return bool(francais_des_scripts(source))


# ---------- gabarits à variables nommées (tâche 7.3) ----------

# « Segment {n} confirmé. » : variable nommée, en minuscules, jamais un marqueur {1} ni un jeton {{ROOT}}
VARIABLE = re.compile(r"(?<!\{)\{([a-z][a-z0-9_]*)\}(?!\})")


def variables(texte):
    """Variables nommées d'un gabarit, triées (une variable répétée compte autant de fois)."""
    return sorted(VARIABLE.findall(texte or ""))


# ---------- classement des attributs ----------

# Classes des éléments jamais traduits, comme translate="no" : bloc de code de l'exemple d'API (tarifs/, JSON indenté
# découpé en balises en ligne). Exclus par leur classe pour laisser le français identique ; controles.texte_visible
# les exclut aussi.
CLASSES_NON_TRADUITES = {"u-code"}

# Attributs dont la valeur est du texte français affiché ou lu par un script : extraits, où qu'ils soient.
ATTRS_TEXTE = ("alt", "aria-label", "title", "placeholder", "data-m", "data-v-erreur", "data-v-refus", "data-vide",
               "data-fermer", "data-relancer", "data-pause", "data-resume", "data-requis", "data-email", "data-choix",
               "data-case", "data-avis", "data-prerempli",
               # ajouts de la tâche 2.1 (voir le rapport) :
               "data-v",      # assets/sim.js l'écrit dans le sélecteur affiché et le compare au texte visible du libellé
               "data-def")    # HTML rejoué par la scène « reph » de sim.js : suit la sortie visible, qui est traduite
# Parmi eux, ceux dont la valeur est un fragment HTML (balises en ligne à protéger par des marqueurs).
ATTRS_HTML = ("data-def",)
# Préfixe des variantes de texte de la page de remerciement (merci.js : data-v-<variante> remplace le texte de l'élément).
PREFIXE_VARIANTE = "data-v-"
# Attributs jamais traduits : démos en langue d'origine, libellés de l'application (anglais, inchangés), clés de
# script, identifiants de suivi, réglages.
ATTRS_JAMAIS = ("data-html", "data-gen", "data-avant", "data-ph", "data-value", "data-title", "data-s", "data-dom",
                "data-suivi", "data-act", "data-seul", "data-ech", "data-sim", "data-style", "data-theme", "data-theme-set",
                "data-reinit",
                # ajouts de la tâche 2.1 (voir le rapport) :
                "data-terme-co", "data-terme-lb")  # clés de surlignage, cherchées dans window.SIM_EX (sim-data.js, en FR)
# Attributs HTML, ARIA et SVG standard dont la valeur n'est jamais du texte de langue : classés « technique ».
ATTRS_TECHNIQUES = (
    "class", "id", "href", "src", "srcset", "sizes", "type", "rel", "as", "crossorigin", "charset", "name", "property",
    "http-equiv", "media", "hreflang", "lang", "translate", "dir", "role", "style", "target", "action", "method", "for",
    "autocomplete", "inputmode", "enterkeyhint", "tabindex", "colspan", "rowspan", "scope", "loading", "decoding",
    "focusable", "spellcheck", "contenteditable", "min", "max", "step", "start", "pattern", "accept", "maxlength",
    "minlength", "width", "height", "viewbox", "d", "points", "transform", "fill", "stroke", "stroke-width",
    "stroke-linecap", "stroke-linejoin", "x", "y", "x1", "x2", "y1", "y2", "cx", "cy", "r", "rx", "ry", "xmlns",
    "aria-controls", "aria-labelledby", "aria-describedby", "aria-live", "aria-hidden", "aria-expanded",
    "aria-pressed", "aria-checked", "aria-selected", "aria-current", "aria-orientation", "aria-multiline",
    "aria-haspopup", "aria-disabled", "aria-modal", "aria-atomic", "aria-relevant", "aria-owns", "aria-activedescendant",
    "aria-valuenow", "aria-valuemin", "aria-valuemax", "aria-level", "aria-busy", "aria-invalid", "aria-required",
    "disabled", "readonly", "required", "hidden", "checked", "selected", "multiple", "novalidate", "async", "defer",
    "data-ui", "data-scene", "data-interactif", "data-une-fois", "data-demo", "data-libre", "data-aide-recherche",
    "data-mg", "data-modele", "data-retour", "data-live", "data-en-pause", "data-for")
# content des seules métas de texte : lu par les moteurs de recherche, les réseaux sociaux et les assistants
METAS_TEXTE = ("description", "og:title", "og:description", "og:image:alt", "twitter:title", "twitter:description",
               "twitter:image:alt")
# métas sans texte de langue : réglages, adresses, gabarit de couleur, nom de marque
METAS_JAMAIS = ("viewport", "robots", "theme-color", "og:url", "og:type", "og:image", "og:locale", "og:site_name",
                "twitter:card", "twitter:image", "referrer", "color-scheme", "format-detection", "generator")
# value : libellé d'un bouton, ou champ affiché mais non saisissable (disabled) ; sinon valeur de démo, clé de script ou
# donnée de formulaire, jamais traduite
BOUTONS = ("submit", "button", "reset")


def classer_attribut(balise, attrs, nom):
    """Classement d'un attribut : « texte » (extrait), « jamais » (volontairement laissé tel quel), « technique »
    (attribut standard sans texte de langue) ou None (non classé : le test d'exhaustivité l'attrape).
    attrs : attributs de la balise, nom -> valeur (« » si l'attribut n'a pas de valeur)."""
    if nom in ATTRS_TEXTE or nom.startswith(PREFIXE_VARIANTE):
        return "texte"
    if nom in ATTRS_JAMAIS:
        return "jamais"
    if nom == "content" and balise == "meta":
        cle = (attrs.get("name") or attrs.get("property") or "").lower()
        if cle in METAS_TEXTE:
            return "texte"
        if cle in METAS_JAMAIS or ("http-equiv" in attrs and not cle):
            return "jamais"
        return None
    if nom == "value":
        if balise == "input" and (attrs.get("type", "").lower() in BOUTONS or "disabled" in attrs):
            return "texte"
        return "jamais"
    if nom in ATTRS_TECHNIQUES:
        return "technique"
    return None


# ---------- JSON-LD et JSON de données ----------

# clés du JSON-LD dont les valeurs ne sont jamais traduites : types, identifiants, adresses, codes de langue ou de
# pays, noms propres (raison sociale, rue, localité), énumérations de schema.org, dates ; alternateName porte les
# équivalents quadrilingues du glossaire (audit i18n § 4.4)
LD_JAMAIS = {"@type", "@context", "@id", "@language", "url", "item", "inLanguage", "image", "logo", "sameAs",
             "mainEntityOfPage", "email", "telephone", "knowsLanguage", "availableLanguage", "areaServed",
             "addressCountry", "addressRegion", "addressLocality", "streetAddress", "postalCode", "legalName",
             "alternateName", "dateModified", "datePublished", "dateCreated", "availability", "applicationCategory",
             "operatingSystem", "credentialCategory", "identifier", "position", "contentUrl", "thumbnailUrl"}

_CHAINE_JSON = re.compile(r'"(?:[^"\\]|\\.)*"', re.S)
_ATOME_JSON = re.compile(r"[^\s,\]}]+")


def _chaines_json(src):
    """Chaînes d'un texte JSON avec leur position : [(chemin, debut, fin)], debut et fin encadrant le contenu de la
    chaîne (guillemets exclus) dans src. Lève ValueError si le JSON est mal formé."""
    sortie = []

    def blancs(i):
        while i < len(src) and src[i] in " \t\r\n":
            i += 1
        return i

    def valeur(i, chemin):
        i = blancs(i)
        c = src[i:i + 1]
        if c == '"':
            m = _CHAINE_JSON.match(src, i)
            if not m:
                raise ValueError("chaîne JSON non terminée")
            sortie.append((chemin, m.start() + 1, m.end() - 1))
            return m.end()
        if c in "{[":
            fermant = "}" if c == "{" else "]"
            i = blancs(i + 1)
            if src[i:i + 1] == fermant:
                return i + 1
            rang = 0
            while True:
                if c == "{":
                    m = _CHAINE_JSON.match(src, blancs(i))
                    if not m:
                        raise ValueError("clé JSON attendue")
                    cle = json.loads(m.group(0))
                    i = blancs(m.end())
                    if src[i:i + 1] != ":":
                        raise ValueError("« : » attendu")
                    i = valeur(i + 1, chemin + (cle,))
                else:
                    i = valeur(i, chemin + (rang,))
                    rang += 1
                i = blancs(i)
                suite = src[i:i + 1]
                if suite == ",":
                    i = blancs(i + 1)
                elif suite == fermant:
                    return i + 1
                else:
                    raise ValueError("« , » ou fermeture attendus")
        m = _ATOME_JSON.match(src, i)
        if not m:
            raise ValueError("valeur JSON attendue")
        return m.end()

    fin = valeur(0, ())
    if blancs(fin) != len(src):
        raise ValueError("texte après la valeur JSON")
    return sortie


def _suivre(donnees, chemin):
    for p in chemin:
        donnees = donnees[p]
    return donnees


def _cle_ld(chemin):
    """Clé de l'objet qui porte la chaîne (celle de la liste pour un élément de liste)."""
    for p in reversed(chemin):
        if isinstance(p, str):
            return p
    return None


def _ld_a_extraire(donnees, chemin, valeur):
    cle = _cle_ld(chemin)
    if cle in LD_JAMAIS or not LETTRE.search(valeur) or CHEMIN.match(valeur):
        return False
    # le nom d'un terme défini dans une autre langue (DefinedTerm de-CH) est le mot-vedette : il ne se traduit pas
    if chemin and chemin[-1] == "name":
        parent = _suivre(donnees, chemin[:-1])
        langue = parent.get("inLanguage") if isinstance(parent, dict) else None
        if isinstance(langue, str) and _primaire(langue) != "fr":
            return False
    return True


def _json_a_extraire(chemin, valeur):
    cle = _cle_ld(chemin)
    return cle not in TECH and LETTRE.search(valeur) and not CHEMIN.match(valeur) and not IDENT.fullmatch(valeur)


# ---------- extraction ----------

_VIDES_HTML = {"area", "base", "br", "col", "embed", "hr", "img", "input", "link", "meta", "param", "source", "track", "wbr"}
_JETONS = re.compile(r"<!--.*?-->|<(script|style)\b[^>]*>.*?</\1\s*>|<[^>]+>|[^<]+", re.S)
_ATTRIBUT = re.compile(r"""([^\s"'<>/=]+)(?:\s*=\s*(?:"([^"]*)"|'([^']*)'|([^\s"'=<>`]+)))?""")


def _primaire(code):
    return (code or "").strip().lower().replace("_", "-").split("-")[0]


def _attributs(tag, base):
    """Attributs d'une balise ouvrante : [(nom, valeur, debut, fin, guillemet)], positions absolues de la valeur."""
    debut = re.match(r"<\s*[^\s/>]+", tag)
    sortie = []
    for a in _ATTRIBUT.finditer(tag, debut.end() if debut else 0):
        for k, q in ((2, '"'), (3, "'"), (4, "")):
            if a.group(k) is not None:
                sortie.append((a.group(1).lower(), a.group(k), base + a.start(k), base + a.end(k), q))
                break
        else:
            sortie.append((a.group(1).lower(), None, None, None, ""))
    return sortie


def _entree(parent, balise, attrs):
    """Contexte d'un élément ouvrant : langue en vigueur, translate, écran d'application. Le lang de <html> est ignoré
    (la page traduite le change) ; un lang étranger ou translate="no" exclut le contenu de l'élément."""
    lang, explicite = parent["lang"], parent["explicite"]
    if balise != "html" and attrs.get("lang", "").strip():
        lang, explicite = attrs["lang"], True
    non_traduit = parent["non_traduit"]
    t = attrs.get("translate", "").strip().lower()
    if t == "no" or CLASSES_NON_TRADUITES & set(attrs.get("class", "").split()):
        non_traduit = True
    elif t == "yes":
        non_traduit = False
    return {"nom": balise, "lang": lang, "explicite": explicite, "non_traduit": non_traduit,
            "exclu": _primaire(lang) != "fr" or non_traduit,
            "lang_fr": explicite and _primaire(lang) == "fr",
            "ui": parent["ui"] or "data-ui" in attrs}


_RACINE = {"nom": "", "lang": "fr", "explicite": False, "non_traduit": False, "exclu": False, "lang_fr": False, "ui": False}


def extraire_page(source):
    """Segments d'une page assemblée (HTML complet), triés par position, numérotés de 1 à n."""
    unites = []
    pile = []
    run = []
    contexte = {}

    def haut():
        return pile[-1] if pile else _RACINE

    def ajoute(genre, debut, fin, texte, table, attr=None, ctx=None):
        ctx = ctx or haut()
        unites.append({"id": "", "genre": genre, "debut": debut, "fin": fin, "html": source[debut:fin], "texte": texte,
                       "table": table, "ui": ctx["ui"], "attr": attr, "lang_fr": ctx["lang_fr"]})

    def vide_run():
        if not run:
            return
        # aux bords : retirer les blancs et les balises dont la paire n'est pas dans le passage
        jet = [source[a:b] for a, b in run]
        pile_ligne, paire = [], set()
        for i, j in enumerate(jet):
            if j.startswith("</"):
                for k in range(len(pile_ligne) - 1, -1, -1):
                    if _nom(jet[pile_ligne[k]]) == _nom(j):
                        paire.update((pile_ligne[k], i)); del pile_ligne[k:]; break
            elif j.startswith("<") and _nom(j) not in VIDES:
                pile_ligne.append(i)
        bord = lambda i: (not jet[i].startswith("<") and not jet[i].strip()) or (jet[i].startswith("<") and i not in paire)
        while run and bord(0):
            run.pop(0); jet.pop(0); paire = {p - 1 for p in paire if p > 0}
        while run and bord(len(run) - 1):
            run.pop(); jet.pop()
        if not run:
            contexte.clear()
            return
        d, f = run[0][0], run[-1][1]
        while d < f and source[d].isspace():
            d += 1
        while f > d and source[f - 1].isspace():
            f -= 1
        if _a_du_texte(source[d:f]):
            texte, table = proteger(source[d:f])
            ajoute("bloc", d, f, texte, table, ctx=contexte or haut())
        run.clear()
        contexte.clear()

    def script(j, d):
        """JSON-LD et JSON de données : une unité par chaîne à traduire ; les autres scripts ne livrent rien."""
        ouvrant = re.match(r"<script\b[^>]*>", j, re.I)
        genre = ("ld" if "ld+json" in ouvrant.group(0).lower() else
                 "json" if "application/json" in ouvrant.group(0).lower() else None)
        if genre is None:
            return
        fermant = re.search(r"</script\s*>\s*$", j, re.I)
        debut, fin = d + ouvrant.end(), d + fermant.start()
        corps = source[debut:fin]
        try:
            donnees = json.loads(corps)
            chaines = _chaines_json(corps)
        except ValueError as e:
            raise ValueError(f"JSON illisible à la position {debut} : {e}") from e
        for chemin, a, b in chaines:
            brut = corps[a:b]
            valeur = json.loads('"' + brut + '"')
            if _suivre(donnees, chemin) != valeur:
                raise ValueError(f"chaîne JSON mal localisée à la position {debut + a}")
            if (_ld_a_extraire(donnees, chemin, valeur) if genre == "ld" else _json_a_extraire(chemin, valeur)):
                ajoute(genre, debut + a, debut + b, valeur, {})

    for m in _JETONS.finditer(source):
        d, f, j = m.start(), m.end(), m.group(0)
        if j.startswith("<!--"):
            vide_run()
        elif m.group(1):  # script ou style
            vide_run()
            if m.group(1).lower() == "script" and not haut()["exclu"]:
                # un script de données translate="no" ou d'une autre langue (données des démos, tâche 7.3) n'est pas lu
                ouvrant = re.match(r"<script\b[^>]*>", j, re.I).group(0)
                attrs = {n: (v if v is not None else "") for n, v, _, _, _ in _attributs(ouvrant, d)}
                if not _entree(haut(), "script", attrs)["exclu"]:
                    script(j, d)
        elif j.startswith("</"):
            nom = _nom(j)
            ferme = next((k for k in range(len(pile) - 1, -1, -1) if pile[k]["nom"] == nom), None)
            if not haut()["exclu"]:
                if nom in EN_LIGNE and not (ferme is not None and pile[ferme].get("coupe")):
                    run.append((d, f))
                else:
                    vide_run()
            if ferme is not None:
                del pile[ferme:]
        elif j.startswith("<!"):  # doctype
            vide_run()
        elif j.startswith("<"):
            nom = _nom(j)
            attrs_pos = _attributs(j, d)
            attrs = {n: (v if v is not None else "") for n, v, _, _, _ in attrs_pos}
            parent = haut()
            entree = _entree(parent, nom, attrs)
            if not (parent["exclu"] or entree["non_traduit"]):
                # un lang étranger sur l'élément exclut son contenu, pas ses attributs : l'étiquette data-m d'une cellule
                # lang="de" est du français de l'interface. De même, le lang="fr" voulu d'un élément (source d'une démo)
                # ne s'étend pas à ses attributs d'interface (aria-label du champ de recherche de l'éditeur, traduit),
                # sauf au texte qu'il rejoue lui-même (data-def, ATTRS_HTML : réécriture française de la démo)
                interface = dict(entree, lang_fr=parent["lang_fr"])
                for n, v, a, b, _ in attrs_pos:
                    if v is None or classer_attribut(nom, attrs, n) != "texte":
                        continue
                    brut = html.unescape(v)
                    if not LETTRE.search(brut) or CHEMIN.match(brut):
                        continue
                    if n in ATTRS_HTML:
                        texte, table = proteger(brut)
                    else:
                        texte, table = brut, {}
                    ajoute("attr", a, b, texte, table, attr=n, ctx=entree if n in ATTRS_HTML else interface)
            # un élément en ligne qui ouvre un passage français voulu (lang="fr" explicite, source d'une démo) coupe le
            # passage comme un élément étranger : son texte est une unité lang_fr à part, jamais traduite (tâche 7.3)
            entree["coupe"] = nom in EN_LIGNE and entree["lang_fr"] and not parent["lang_fr"]
            if entree["exclu"] or entree["coupe"]:
                vide_run()
            elif nom in EN_LIGNE:
                run.append((d, f))
            else:
                vide_run()
            if nom not in _VIDES_HTML and not j.endswith("/>"):
                pile.append(entree)
        else:  # texte
            if not haut()["exclu"]:
                run.append((d, f))
                if not contexte and j.strip():
                    contexte.update(haut())
    vide_run()
    unites.sort(key=lambda u: u["debut"])
    for i, u in enumerate(unites, 1):
        u["id"] = str(i)
    return unites


# ---------- restauration et réinjection ----------

def restaurer_unite(traduction, unite):
    """Traduction d'une unité -> valeur à donner à reinjecter_page : HTML restauré pour un passage ou un attribut HTML
    (marqueurs remplacés par les balises, texte échappé), texte brut pour les autres genres."""
    if unite["genre"] == "bloc" or unite["attr"] in ATTRS_HTML:
        return restaurer(traduction, unite["table"])
    return traduction


def _ecrire_attribut(valeur, guillemet):
    """Valeur d'attribut échappée. Une valeur écrite sans guillemets à l'origine est réécrite entre guillemets."""
    v = html.escape(valeur, quote=True)
    return v if guillemet else '"' + v + '"'


def _ecrire_json(valeur):
    # « </ » ne doit jamais fermer le script
    return json.dumps(valeur, ensure_ascii=False)[1:-1].replace("</", "<\\/")


def _remplacer_dans_passage(texte, attributs):
    """Dans le HTML restauré d'un passage, remplace chaque valeur d'attribut d'origine par sa traduction.
    attributs : [(unité d'attribut, valeur écrite)] ; les balises du passage viennent de sa table, donc portent la
    valeur d'origine telle qu'elle est dans la source. Lève ValueError si l'attribut n'est pas retrouvé (la traduction
    serait perdue en silence)."""
    for u, nouvelle in attributs:
        guillemet = u["guillemet"]
        fin = re.escape(guillemet) if guillemet else r"(?=[\s/>])"
        motif = re.compile(r"(\s%s\s*=\s*%s)%s(%s)" % (re.escape(u["attr"]), re.escape(guillemet), re.escape(u["html"]), fin))
        texte, n = motif.subn(lambda m: m.group(1) + nouvelle + m.group(2) if guillemet else m.group(1) + nouvelle, texte, count=1)
        if not n:
            raise ValueError(f"attribut {u['attr']}=\"{u['html']}\" introuvable dans le passage traduit : {texte[:80]}")
    return texte


def reinjecter_page(source, traductions):
    """traductions : {id: valeur traduite}, la valeur étant celle que renvoie restaurer_unite (HTML restauré pour un
    passage, texte brut sinon). Une unité absente, ou dont la valeur est celle du français, garde sa source telle
    quelle : réinjecter la restauration du texte FR rend donc la page à l'identique, octet pour octet. Un attribut
    porté par une balise en ligne d'un passage s'écrit dans les balises du passage traduit, ou à sa place dans la source
    si le passage est gardé tel quel."""
    unites = extraire_page(source)
    passages = [u for u in unites if u["genre"] == "bloc"]
    debuts = [p["debut"] for p in passages]
    modifs = []                 # (debut, fin, texte écrit), sans recouvrement
    internes = {}               # id du passage -> [(unité d'attribut, valeur écrite)]
    passages_traduits = {}      # id du passage -> HTML traduit
    for u in unites:
        t = traductions.get(u["id"])
        if t is None or t == restaurer_unite(u["texte"], u):
            continue
        if u["genre"] == "bloc":
            passages_traduits[u["id"]] = t
        elif u["genre"] == "attr":
            q = source[u["debut"] - 1] if u["debut"] > 0 and source[u["debut"] - 1] in "\"'" else ""
            u["guillemet"] = q
            ecrit = _ecrire_attribut(t, q)
            k = bisect.bisect_right(debuts, u["debut"]) - 1
            if k >= 0 and u["fin"] <= passages[k]["fin"]:
                internes.setdefault(passages[k]["id"], []).append((u, ecrit))
            else:
                modifs.append((u["debut"], u["fin"], ecrit))
        else:
            modifs.append((u["debut"], u["fin"], _ecrire_json(t)))
    par_id = {p["id"]: p for p in passages}
    for pid, t in passages_traduits.items():
        p = par_id[pid]
        modifs.append((p["debut"], p["fin"], _remplacer_dans_passage(t, internes.pop(pid, []))))
    for pid, attributs in internes.items():  # passages gardés tels quels
        modifs += [(u["debut"], u["fin"], ecrit) for u, ecrit in attributs]
    out = source
    for d, f, t in sorted(modifs, key=lambda m: -m[0]):
        out = out[:d] + t + out[f:]
    return out
