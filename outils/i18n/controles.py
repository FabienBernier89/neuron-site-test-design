"""Contrôles d'invariants de la traduction DE, EN et IT, réutilisés par toutes les tâches du lot de traduction.

Chaque contrôle renvoie une liste de problèmes {"regle": str, "detail": str, "extrait": str}, vide si tout va bien.
Bibliothèque standard seulement. Les listes protégées (marques, libellés d'application, invariants exacts, termes
interdits) sont lues dans src/langues/proteges.json.

Les mots outils français (MOTS_OUTILS), la liste des ambigus (AMBIGUS), les seuils et l'heuristique _restes_fr sont
copiés de la V1 (Sites/neuron/outils/controle_traductions.py) : la V2 ne dépend pas du code V1. Il en va de même de la
logique de terminologie() (« _termes » de la V1)."""
import html as H
import json
import posixpath
import re
from collections import Counter
from html.parser import HTMLParser
from pathlib import Path
from urllib.parse import unquote, urlsplit

from outils.i18n.segments import CLASSES_NON_TRADUITES  # éléments jamais traduits, comme translate="no"
from outils.i18n.segments import variables as _variables

ICI = Path(__file__).resolve().parent.parent.parent
PROTEGES = ICI / "src/langues/proteges.json"
PRODUCTION = "https://neur-on.ai/"  # adresse du site publié (même valeur que build.PRODUCTION)
LANGUES = ("fr", "de", "it", "en")
HREFLANG = {"fr": "fr-CH", "de": "de-CH", "it": "it-CH", "en": "en"}
OG_LOCALE = {"fr": "fr_CH", "de": "de_CH", "it": "it_CH", "en": "en_GB"}

# ---------- copie de la V1 (controle_traductions.py, lignes 34 à 165) ----------

MOTS_OUTILS = {"le", "la", "les", "des", "une", "pour", "avec", "dans", "est", "sont", "qui", "que", "nous", "vous",
               "aux", "du", "au", "sur"}
# mots outils français qui sont aussi des mots courants de la langue cible : non comptés dans cette langue
AMBIGUS = {"de": {"des"}, "it": {"la", "le", "qui"}}
# petits mots qui relient les éléments d'un nom propre (« Banque Cantonale du Valais »)
LIAISONS = MOTS_OUTILS | {"de", "d", "l", "et"}
SEUIL_MOTS, SEUIL_TAUX = 12, 0.08

_MOT = re.compile(r"[^\W\d_]+(?:['’][^\W\d_]+)*")
_ESZETT = re.compile(r"[^\W\d_]*ß[^\W\d_]*")


def _restes_fr(texte, lang):
    """(mots outils comptés, mots) si le texte semble resté en français, sinon None."""
    mots = [(m.group(0), m.start()) for m in _MOT.finditer(texte)]
    if len(mots) <= SEUIL_MOTS:
        return None
    outils = MOTS_OUTILS - AMBIGUS.get(lang, set())
    n = 0
    for i, (mot, debut) in enumerate(mots):
        if mot.lower() not in outils:
            continue
        if mot[0].isupper() and not _debut_de_phrase(texte, debut):
            continue  # nom propre : La Poste, Le Temps
        if _entre_noms_propres(mots, i):
            continue  # nom propre : Banque Cantonale du Valais
        n += 1
    return (n, len(mots)) if n / len(mots) > SEUIL_TAUX else None


def _debut_de_phrase(texte, debut):
    avant = texte[:debut].rstrip(" «“\"'( ")
    return not avant or avant[-1] in ".!?:"


def _entre_noms_propres(mots, i):
    g = i - 1
    while g >= 0 and mots[g][0].lower() in LIAISONS:
        g -= 1
    d = i + 1
    while d < len(mots) and mots[d][0].lower() in LIAISONS:
        d += 1
    return g >= 0 and d < len(mots) and mots[g][0][0].isupper() and mots[d][0][0].isupper()


# ---------- outils communs ----------

TIRETS = {chr(0x2014): "tiret cadratin (U+2014)", chr(0x2013): "demi-cadratin (U+2013)"}
_BLANCS = re.compile(r"[ \t\r\n\f]+")  # pas \s : l'espace insécable doit survivre (contrôle des milliers)
_MARQUE_AVANT = r"(?<![A-Za-z0-9./@])"  # ni adresse e-mail, ni domaine, ni chemin (« team@corrext.com »)
_MARQUE_APRES = r"(?![A-Za-z0-9])(?!\.[a-z]{2,3}\b)"
_MOT_ENTIER = (r"(?<![^\W_])", r"(?![^\W_])")  # mot entier, accents compris


def probleme(regle, detail, extrait=""):
    return {"regle": regle, "detail": detail, "extrait": _extrait(extrait)}


def _visible(t):
    """Texte affichable : les tirets interdits sont remplacés par leur code, pour ne jamais les réécrire."""
    for c in TIRETS:
        t = t.replace(c, "[U+%04X]" % ord(c))
    return t


def _extrait(t, n=70):
    t = " ".join(str(t).split())
    return _visible(t if len(t) <= n else t[:n - 1] + "…")


def _autour(t, debut, fin, marge=30):
    return t[max(0, debut - marge):fin + marge]


def proteges():
    """Contenu de src/langues/proteges.json : marques, libelles_application, invariants_exacts, interdits."""
    return json.loads(PROTEGES.read_text(encoding="utf-8"))


def _primaire(code):
    return (code or "").strip().lower().replace("_", "-").split("-")[0]


# ---------- texte visible ----------

_VIDES = {"area", "base", "br", "col", "embed", "hr", "img", "input", "link", "meta", "param", "source", "track", "wbr"}
_BLOCS = {"address", "article", "aside", "blockquote", "body", "br", "button", "dd", "details", "div", "dl", "dt",
          "fieldset", "figcaption", "figure", "footer", "form", "h1", "h2", "h3", "h4", "h5", "h6", "head", "header",
          "hr", "html", "label", "legend", "li", "main", "nav", "ol", "option", "p", "section", "select", "summary",
          "table", "td", "textarea", "th", "title", "tr", "ul"}
_ATTRIBUTS = ("alt", "title", "aria-label", "placeholder")  # lisibles ; data-html, data-gen, data-avant ne le sont jamais
_METAS = {"description", "og:title", "og:description", "og:image:alt", "twitter:title", "twitter:description",
          "twitter:image:alt"}
_CLES_JSON_IGNOREES = {"@context", "@type", "@id", "inLanguage"}


def _chaines_json(valeur, sortie):
    """Valeurs texte d'un JSON-LD, sans les clés techniques ni les adresses."""
    if isinstance(valeur, dict):
        for cle, v in valeur.items():
            if cle not in _CLES_JSON_IGNOREES:
                _chaines_json(v, sortie)
    elif isinstance(valeur, list):
        for v in valeur:
            _chaines_json(v, sortie)
    elif isinstance(valeur, str) and not re.match(r"(?:https?:|mailto:|tel:|/)", valeur):
        sortie.append(valeur)


class _Lecteur(HTMLParser):
    """Textes lisibles d'une page : un texte par bloc (un élément en ligne ne coupe rien), plus les attributs lisibles,
    les méta de description et les valeurs du JSON-LD. Sous-arbres exclus : lang d'une autre langue (le lang de <html>
    est ignoré : c'est langue_page qui le juge), translate="no", classes jamais traduites (CLASSES_NON_TRADUITES, bloc
    de code de l'exemple d'API), scripts et styles (sauf JSON-LD)."""

    def __init__(self, langue):
        super().__init__(convert_charrefs=True)
        self.langue = langue
        self.pile = []        # (balise, ouvre une exclusion)
        self.exclus = 0       # nombre d'exclusions ouvertes
        self.tampon = []
        self.textes = []
        self.brut = None      # "ld", "ignore" ou None : contenu d'un script ou d'un style
        self.ld = []

    def _vider(self):
        t = _BLANCS.sub(" ", "".join(self.tampon)).strip(" \t\r\n\f")
        self.tampon = []
        if t:
            self.textes.append(t)

    def _lire_attributs(self, balise, a):
        for nom in _ATTRIBUTS:
            if a.get(nom, "").strip():
                self.textes.append(_BLANCS.sub(" ", a[nom]).strip())
        if balise == "meta" and a.get("content", "").strip():
            if (a.get("name") or a.get("property") or "").lower() in _METAS:
                self.textes.append(_BLANCS.sub(" ", a["content"]).strip())

    def handle_starttag(self, balise, attrs):
        a = {k: v or "" for k, v in attrs}
        exclut = balise != "html" and (
            ("lang" in a and _primaire(a["lang"]) != self.langue) or a.get("translate", "").lower() == "no"
            or bool(CLASSES_NON_TRADUITES & set(a.get("class", "").split())))
        if balise in _BLOCS:
            self._vider()
        if balise in _VIDES:
            if not self.exclus and not exclut:
                self._lire_attributs(balise, a)
            return
        self.pile.append((balise, exclut))
        self.exclus += exclut
        if self.exclus:
            if balise in ("script", "style"):
                self.brut = "ignore"
            return
        if balise == "script":
            self.brut = "ld" if "ld+json" in a.get("type", "").lower() else "ignore"
        elif balise == "style":
            self.brut = "ignore"
        self._lire_attributs(balise, a)

    def handle_endtag(self, balise):
        if balise in _VIDES or not any(b == balise for b, _ in self.pile):
            return
        if balise in _BLOCS:
            self._vider()
        while self.pile:
            b, exclut = self.pile.pop()
            self.exclus -= exclut
            if b == balise:
                break
        if balise in ("script", "style"):
            self.brut = None

    def handle_data(self, data):
        if self.brut == "ld" and not self.exclus:
            self.ld.append(data)
        elif self.brut is None and not self.exclus:
            self.tampon.append(data)

    def handle_comment(self, data):
        pass

    def fin(self):
        self._vider()
        for bloc in self.ld:
            try:
                _chaines_json(json.loads(bloc), self.textes)
            except ValueError:
                self.textes.append(_BLANCS.sub(" ", bloc).strip())
        return self.textes


def texte_visible(html, langue):
    """Textes et attributs lisibles d'une page, entités désechappées, un élément de la liste par bloc de texte.
    Exclus : sous-arbres dont le lang n'est pas `langue`, attributs data-html, data-gen et data-avant (données des
    démos), sous-arbres translate="no", scripts et styles (sauf le JSON-LD, lu par ses valeurs)."""
    lecteur = _Lecteur(langue)
    lecteur.feed(html)
    lecteur.close()
    return lecteur.fin()


# ---------- contrôles ----------

def tirets(texte):
    """Tiret cadratin (U+2014) et demi-cadratin (U+2013), y compris écrits en entité HTML."""
    texte = H.unescape(texte)
    problemes = []
    for c, nom in TIRETS.items():
        for m in re.finditer(re.escape(c), texte):
            problemes.append(probleme("tirets", nom, _autour(texte, m.start(), m.end())))
    return problemes


def interdits(texte):
    """Mots entiers de proteges()["interdits"] (« Lexikon » ne contient pas « Lexa »), sans tenir compte de la casse. Dans
    un terme de plusieurs mots, l'espace peut être insécable ou fine (« Legal 230 » écrit avec U+00A0 ou U+202F : vague
    finale, point 11)."""
    texte = H.unescape(texte)
    problemes = []
    for terme in proteges()["interdits"]:
        motif = re.compile(_MOT_ENTIER[0] + r"\s+".join(re.escape(m) for m in terme.split()) + _MOT_ENTIER[1], re.I)
        for m in motif.finditer(texte):
            problemes.append(probleme("interdits", f"terme interdit : « {terme} »", _autour(texte, m.start(), m.end())))
    return problemes


def marques(fr, tr, ui=False):
    """Même nombre de chaque marque dans le texte FR et dans sa traduction, avec la même casse. Si ui : les libellés
    d'application (anglais, inchangés) sont comptés aussi, en respectant leur casse."""
    p = proteges()
    fr, tr = H.unescape(fr), H.unescape(tr)
    problemes = []
    # du plus long au plus court : « CHnell » seul se compte après « Fast lookup CHnell »
    for nom in sorted(p["marques"], key=len, reverse=True):
        motif = re.compile(_MARQUE_AVANT + re.escape(nom) + _MARQUE_APRES, re.I)
        fa, fb = Counter(m.group(0) for m in motif.finditer(fr)), Counter(m.group(0) for m in motif.finditer(tr))
        fr, tr = motif.sub(" ", fr), motif.sub(" ", tr)
        problemes += _ecarts("marque", nom, fa, fb, casse=True)
    if ui:
        for nom in sorted(p["libelles_application"], key=len, reverse=True):
            motif = re.compile(_MOT_ENTIER[0] + re.escape(nom) + _MOT_ENTIER[1])
            na, nb = len(motif.findall(fr)), len(motif.findall(tr))
            fr, tr = motif.sub(" ", fr), motif.sub(" ", tr)
            problemes += _ecarts("libellé d'application", nom, Counter({nom: na}), Counter({nom: nb}), casse=False)
    return problemes


def _ecarts(genre, nom, fa, fb, casse):
    out = []
    if casse:
        for forme in sorted(fb):
            if forme not in fa and forme != nom and sum(fa.values()) and len(fa) and forme.lower() == nom.lower():
                out.append(probleme("marques", f"{genre} à la casse modifiée : « {forme} » au lieu de « {nom} »", forme))
    na, nb = sum(fa.values()), sum(fb.values())
    if na != nb and not out:
        out.append(probleme("marques", f"{genre} « {nom} » : {na} occurrence(s) en français, {nb} dans la traduction",
                            nom))
    return out


def eszett(fr, tr):
    """« ß » permis seulement dans un mot que le texte FR contient déjà tel quel (citation)."""
    trop = Counter(_ESZETT.findall(H.unescape(tr))) - Counter(_ESZETT.findall(H.unescape(fr)))
    return [probleme("eszett", f"« {mot} » ({n} fois) : pas de ß en allemand de Suisse, écrire « {mot.replace('ß', 'ss')} »",
                     mot) for mot, n in sorted(trop.items())]


_MARQUEURS_EN_LIGNE = re.compile(r"\{/?\d+\}")  # marqueurs {n}…{/n} des balises en ligne des unités de la table
_AVANT_LETTRE, _APRES_LETTRE = r"(?<![^\W\d_])", r"(?![^\W\d_])"  # bord de mot de la V1 : ni lettre avant, ni lettre après


_MARQUEURS_DANS_LE_MOT = re.compile(r"(?<=[^\W_])(?:\{/?\d+\})+(?=[^\W_])")  # « Aktien{1}kapital{/1} » : un seul mot


def _normaliser_terminologie(texte):
    """Texte sans marqueurs : un marqueur au milieu d'un mot disparaît (le mot reste entier), un autre devient une
    espace (vague finale, point 14)."""
    texte = _MARQUEURS_DANS_LE_MOT.sub("", texte)
    return " ".join(H.unescape(_MARQUEURS_EN_LIGNE.sub(" ", texte)).split())


def termes_presents(fr, langue, glossaire):
    """Termes du glossaire de projet (chnell.construire_glossaire : {fr: {langue: {"terme", ...}}}) dont le terme français
    figure dans le texte FR : liste de (terme français, équivalent retenu dans la langue), dans l'ordre du glossaire. Un
    sigle (CO, LB : majuscules, 6 caractères au plus) se cherche en mot entier à la casse exacte, un autre terme avec un
    pluriel facultatif, sans tenir compte de la casse (logique de « _termes » de la V1). Sert au contrôle terminologique et
    à la note des exports pour les traducteurs."""
    fr = _normaliser_terminologie(fr)
    occurrences = []  # (terme français, équivalent, positions trouvées)
    for terme_fr, langues in glossaire.items():
        eq = (langues.get(langue) or {}).get("terme")
        if not eq or not terme_fr.strip():
            continue
        if terme_fr.isupper() and len(terme_fr) <= 6:
            motif = re.compile(_AVANT_LETTRE + re.escape(terme_fr) + _APRES_LETTRE)
        else:
            motif = re.compile(_AVANT_LETTRE + r"[sx]?\s+".join(re.escape(m) for m in terme_fr.split()) + r"[sx]?"
                               + _APRES_LETTRE, re.I)
        positions = [m.span() for m in motif.finditer(fr)]
        if positions:
            occurrences.append((terme_fr, eq, positions))
    # un terme couvert par un terme plus long du glossaire n'est pas exigé à cet endroit (« certificat » dans « certificat
    # de travail », décision de Fabien du 2026-10-28) ; il reste exigé s'il apparaît aussi seul
    def couvert(debut, fin, terme):
        return any(t != terme and d <= debut and fin <= f and (f - d) > (fin - debut)
                   for t, _, spans in occurrences for d, f in spans)
    return [(t, eq) for t, eq, spans in occurrences if any(not couvert(d, f, t) for d, f in spans)]


def terminologie(fr, tr, langue, glossaire):
    """Termes du glossaire de projet dont le terme français figure dans le texte FR (termes_presents) sans que l'équivalent
    retenu figure dans la traduction : l'équivalent est reconnu par le début (5 lettres) de chacun de ses mots d'au moins
    3 lettres, pour tolérer les flexions. Une alerte, jamais une certitude : à revoir par un humain."""
    tr = _normaliser_terminologie(tr)
    problemes = []
    for terme_fr, eq in termes_presents(fr, langue, glossaire):
        mots = _MOT.findall(eq)
        prefixes = [m[:5].casefold() for m in ([m for m in mots if len(m) >= 3] or mots)]
        if not all(p in tr.casefold() for p in prefixes):
            problemes.append(probleme("terminologie", f"« {terme_fr} » sans « {eq} »", tr))
    return problemes


def variables(fr, tr):
    """Gabarit à variables nommées (« Segment {n} confirmé. », textes des démos, tâche 7.3) : la traduction garde chaque
    variable du français, ni plus ni moins, sans la traduire (« {n} », jamais « {nummer} »)."""
    a, b = _variables(fr), _variables(tr)
    if a == b:
        return []
    return [probleme("variables", f"variables du français : {', '.join('{%s}' % v for v in a) or 'aucune'} ; de la "
                                  f"traduction : {', '.join('{%s}' % v for v in b) or 'aucune'}", tr)]


# règles de controler_traductions qui bloquent ; le reste avertit
BLOQUANTS = ("tirets", "eszett", "marques", "interdits", "variables")
EXCLUS_DU_CONTROLE = ("v1", "invariant")  # statuts d'une traduction déjà validée ou jamais traduite


def exemptee(version):
    """Vrai si la traduction (une entrée de table ou une traduction de page) n'est pas soumise aux contrôles bloquants : statut
    v1 ou invariant, ou champ « v1 » (traduction V1 validée passée relu par le réimport sans changement, Ruling 30)."""
    return version.get("statut") in EXCLUS_DU_CONTROLE or bool(version.get("v1"))


def controler_traductions(langue, entrees, glossaire):
    """Contrôle les traductions d'une table (Table.entrees) hors statuts v1 et invariant et hors champ « v1 » (exemptee), par
    défaut et par page.
    Rend (nombre de traductions contrôlées, problèmes) ; chaque problème : {lieu, regle, detail, extrait, gravite} avec
    gravite « bloquant » (tirets, eszett, marques, interdits, variables) ou « avertissement » (terminologie)."""
    controlees, problemes = 0, []
    for cle in sorted(entrees):
        e = entrees[cle]
        versions = [(None, e)] + [(page, e["par_page"][page]) for page in sorted(e["par_page"])]
        for page, v in versions:
            if v.get("trad") is None or exemptee(v):
                continue
            controlees += 1
            lieu = f"« {_extrait(e['fr'], 50)} » [{cle}" + (f", page {page or 'accueil'}" if page is not None else "") + "]"
            tr = v["trad"]
            trouves = (tirets(tr) + (eszett(e["fr"], tr) if langue == "de" else []) + marques(e["fr"], tr) + interdits(tr)
                       + variables(e["fr"], tr))
            trouves += terminologie(e["fr"], tr, langue, glossaire)
            problemes += [{"lieu": lieu, **p, "gravite": "bloquant" if p["regle"] in BLOQUANTS else "avertissement"}
                          for p in trouves]
    return controlees, problemes


_MILLIERS = re.compile(r"(?<![\d.,'’])\d{1,3}(?:[   ]\d{3})+(?!\d|[   ]\d)")


def milliers(texte, langue):
    """DE et IT : aucun nombre dont les milliers sont séparés par une espace ou une espace insécable (écrire 15'000).
    Autres langues : sans objet (l'anglais écrit 15,000, le français garde l'espace)."""
    if langue not in ("de", "it"):
        return []
    texte = H.unescape(texte)
    return [probleme("milliers", f"séparateur de milliers par une espace : « {m.group(0)} », écrire l'apostrophe",
                     _autour(texte, m.start(), m.end())) for m in _MILLIERS.finditer(texte)]


class _Tete(HTMLParser):
    """Balises d'une page utiles aux contrôles de langue : lang de <html>, <link rel="alternate"> et méta og:locale."""

    def __init__(self):
        super().__init__(convert_charrefs=True)
        self.lang = None
        self.og_locale = None
        self.alternates = []  # (hreflang, href)
        self.liens = []       # href des <a> qui ne sont pas un sélecteur de langue

    def handle_starttag(self, balise, attrs):
        a = {k: v or "" for k, v in attrs}
        if balise == "html" and self.lang is None:
            self.lang = a.get("lang", "")
        elif balise == "meta" and a.get("property") == "og:locale":
            self.og_locale = a.get("content", "")
        elif balise == "link" and a.get("rel", "").lower() == "alternate" and a.get("hreflang"):
            self.alternates.append((a["hreflang"], a.get("href", "")))
        elif balise == "a" and "href" in a and "hreflang" not in a:
            self.liens.append(a["href"])


def _tete(html):
    t = _Tete()
    t.feed(html)
    t.close()
    return t


_LD = re.compile(r'<script[^>]*type=["\']application/ld\+json["\'][^>]*>(.*?)</script\s*>', re.S | re.I)


# objets JSON-LD dont le inLanguage est le leur, pas celui de la page : un terme du glossaire défini dans une autre
# langue (DefinedTerm de-CH sur une page italienne) le garde (Ruling 10)
_LANGUE_PROPRE = {"DefinedTerm", "DefinedTermSet"}


def _types(objet):
    t = objet.get("@type")
    return set(t) if isinstance(t, list) else {t}


def _in_language(valeur, sortie):
    """inLanguage des objets de la page (WebPage, Article, FAQPage...), hors DefinedTerm et DefinedTermSet (Ruling 11)."""
    if isinstance(valeur, dict):
        propre = bool(_types(valeur) & _LANGUE_PROPRE)
        for cle, v in valeur.items():
            if cle == "inLanguage":
                if isinstance(v, str) and not propre:
                    sortie.append(v)
            else:
                _in_language(v, sortie)
    elif isinstance(valeur, list):
        for v in valeur:
            _in_language(v, sortie)


def langue_page(html, langue):
    """<html lang>, og:locale (fr_CH, de_CH, it_CH, en_GB) et "inLanguage" du JSON-LD concordent avec la langue. Le
    inLanguage d'un DefinedTerm ou d'un DefinedTermSet (terme du glossaire dans sa propre langue) n'est pas contrôlé."""
    t = _tete(html)
    problemes = []
    if _primaire(t.lang) != langue:
        problemes.append(probleme("langue", f"<html lang> « {t.lang or ''} » : « {langue} » attendu", f'lang="{t.lang}"'))
    attendu = OG_LOCALE[langue]
    if t.og_locale != attendu:
        problemes.append(probleme("langue", f"og:locale « {t.og_locale or ''} » : « {attendu} » attendu",
                                  f'og:locale="{t.og_locale}"'))
    for bloc in _LD.findall(html):
        try:
            valeurs = []
            _in_language(json.loads(bloc), valeurs)
        except ValueError:
            continue
        for v in valeurs:
            if _primaire(v) != langue:
                problemes.append(probleme("langue", f"inLanguage « {v} » dans le JSON-LD : « {langue} » attendu",
                                          f'"inLanguage":"{v}"'))
    return problemes


def restes_fr(html, langue):
    """Textes lisibles de plus de 12 mots dont plus de 8 % de mots outils français (heuristique de la V1). Les passages
    lang="fr" voulus (citations) et les translate="no" ne comptent pas. Sans objet pour le français."""
    if langue == "fr":
        return []
    problemes = []
    for texte in texte_visible(html, langue):
        r = _restes_fr(texte, langue)
        if r:
            problemes.append(probleme("restes_fr", f"{r[0]} mots outils français sur {r[1]} mots : texte resté en français",
                                      texte))
    return problemes


def _cible_existe(sortie, chemin):
    cible = Path(sortie) / chemin
    return (cible / "index.html").is_file() or cible.is_file()


def _chemin_du_site(href, chemin):
    """Chemin de la cible d'un lien, relatif à la racine du site (« fr/contact/ »), ou None pour un lien qui ne mène
    pas à une page du site (externe, ancre, mailto, tel, jeton, hors du site)."""
    href = href.strip()
    if href.startswith(PRODUCTION):
        href = "/" + href[len(PRODUCTION):]
    if not href or re.match(r"(?:[A-Za-z][A-Za-z0-9+.-]*:|//|#|\{\{)", href):
        return None
    p = unquote(urlsplit(href).path)
    if not p:
        return None
    if p.startswith("/"):
        base = p.lstrip("/")
    else:
        dossier = chemin if chemin.endswith("/") or not chemin else posixpath.dirname(chemin)
        base = posixpath.join(dossier, p)
    cible = posixpath.normpath(base)
    if cible.startswith("..") or cible == ".":
        return None
    return cible + ("/" if p.endswith("/") else "")


def liens_langue(html, chemin, langue, sortie, tolere_fr):
    """Liens d'une page (<a href>, hors sélecteur de langue portant hreflang) : ils restent dans la langue de la page
    et mènent à une page présente dans `sortie`. Un lien vers le français est toléré si tolere_fr (page non encore
    traduite, aperçu), à condition que sa cible existe. `chemin` : « de/kontakt/ »."""
    problemes = []
    for href in _tete(html).liens:
        cible = _chemin_du_site(href, chemin)
        if cible is None:
            continue
        premier = cible.split("/")[0]
        if premier not in LANGUES:
            continue
        if premier != langue and not (premier == "fr" and tolere_fr):
            problemes.append(probleme("liens_langue", f"lien de la page {chemin} vers la langue « {premier} » au lieu de "
                                                      f"« {langue} »", href))
        elif not _cible_existe(sortie, cible):
            problemes.append(probleme("liens_langue", f"lien de la page {chemin} vers une page absente de la sortie : "
                                                      f"{cible}", href))
    return problemes


def _chemin_de_url(url):
    """Chemin d'une adresse de production dans la sortie (« fr/x/ »), ou None si elle n'est pas du site."""
    if not url.startswith(PRODUCTION):
        return None
    return urlsplit(url[len(PRODUCTION):]).path


_REDIRECTION = re.compile(r'<meta http-equiv="refresh"')


def hreflang(sortie):
    """Pour chaque page de sortie/{fr,de,it,en}/ : auto-référence, x-default vers la version de repli (décision V7 : la
    version anglaise que la page annonce, sinon la française), cibles existantes
    et dans la bonne langue, réciprocité (si A annonce B sous la langue de B, B annonce A sous la langue de A). Les pages
    de redirection des anciennes adresses (meta refresh, noindex) ne sont pas des pages du site : elles sont ignorées."""
    sortie = Path(sortie)
    pages = {}  # chemin de la page (« de/x/ ») -> liste (hreflang, href)
    for langue in LANGUES:
        for f in sorted((sortie / langue).rglob("index.html")):
            html = f.read_text(encoding="utf-8")
            if _REDIRECTION.search(html):
                continue
            pages[f.parent.relative_to(sortie).as_posix() + "/"] = _tete(html).alternates
    problemes = []
    for chemin, alternates in pages.items():
        langue, url = chemin.split("/")[0], PRODUCTION + chemin
        propre = HREFLANG[langue]
        if (propre, url) not in alternates:
            problemes.append(probleme("hreflang", f"{chemin} : auto-référence « {propre} » absente", url))
        par_langue = dict(alternates)
        if "x-default" not in par_langue:
            problemes.append(probleme("hreflang", f"{chemin} : x-default absent", ""))
        for hl, href in alternates:
            cible = _chemin_de_url(href)
            if cible is None:
                problemes.append(probleme("hreflang", f"{chemin} : adresse hors du site pour « {hl} »", href))
                continue
            if hl == "x-default":
                anglais = par_langue.get(HREFLANG["en"])
                if (href != anglais) if anglais else cible.split("/")[0] != "fr":
                    problemes.append(probleme("hreflang", f"{chemin} : x-default ne mène pas à la version de repli "
                                                          "(anglaise si elle existe, sinon française)", href))
            elif cible.split("/")[0] != next((l for l in LANGUES if HREFLANG[l] == hl), None):
                problemes.append(probleme("hreflang", f"{chemin} : « {hl} » mène à une page d'une autre langue", href))
            if not _cible_existe(sortie, cible):
                problemes.append(probleme("hreflang", f"{chemin} : cible absente de la sortie pour « {hl} »", href))
            elif hl not in ("x-default", propre) and cible in pages and (propre, url) not in pages[cible]:
                problemes.append(probleme("hreflang", f"{chemin} : annonce {cible} sous « {hl} », qui ne l'annonce pas en "
                                                      f"retour sous « {propre} »", href))
    return problemes


# Citations exactes d'un texte officiel, gardées telles quelles : lignes de résultats CHnell (zone d'exemple de loi du
# glossaire, Ruling 27 ; résultats réels des démos, Ruling 26), dans la fenêtre CHnell ou le schéma de l'accueil
_CITATIONS = (re.compile(r'(<div class="lk-r">).*?(?=</div><div class="cr-ch-f">)', re.S),
              re.compile(r'(<span class="sp-seg"[^>]*>).*?(?=</span>)', re.S))


def sans_citations(html):
    """Page sans le texte des citations exactes de la loi (_CITATIONS) : le contrôle des milliers ne les lit pas
    (« 100 000 franchi » reste la graphie officielle)."""
    for motif in _CITATIONS:
        html = motif.sub(lambda m: m.group(1), html)
    return html


def controler_page(html, langue):
    """Contrôles d'une page construite : tirets, interdits, langue_page, restes_fr, et milliers (de, it ; hors citations
    exactes de la loi, sans_citations). Les contrôles qui comparent au français (marques, eszett) et ceux qui regardent la
    sortie entière (liens_langue, hreflang) se lancent à part."""
    visible = "\n".join(texte_visible(sans_citations(html), langue))
    return (tirets(html) + interdits(html) + langue_page(html, langue) + restes_fr(html, langue)
            + milliers(visible, langue))


def controler_production(html, langue, tete=True):
    """Contrôles bloquants d'une page traduite et finalisée avant la production (vague finale, point 5 ; build.py) : les
    règles déterministes de controler_page qui ne dépendent d'aucun segment, tirets, termes interdits et langue de la page
    (<html lang>, og:locale, inLanguage). Les milliers et les marques se contrôlent par segment (controler_segment) : une
    traduction V1 validée en reste exemptée (Ruling 30 ; l'explication du séparateur de milliers de la page de style
    cite « 15 000 » à dessein). restes_fr, heuristique, n'avertit qu'à part. tete=False (page 404, sans og:locale ni
    données structurées) : seul <html lang> est contrôlé pour la langue."""
    problemes = tirets(html) + interdits(html)
    if tete:
        return problemes + langue_page(html, langue)
    lang = _tete(html).lang
    if _primaire(lang) != langue:
        problemes.append(probleme("langue", f"<html lang> « {lang or ''} » : « {langue} » attendu", f'lang="{lang}"'))
    return problemes


def controler_segment(fr, tr, langue):
    """Contrôles bloquants d'une traduction acceptée en production (traduire.analyser, mode production ; vague finale,
    point 5) : tirets, termes interdits, marques (même nombre qu'en français) et milliers (de, it). L'appelant n'y soumet
    pas une traduction exemptée (exemptee : v1, invariant, champ « v1 »)."""
    return tirets(tr) + interdits(tr) + marques(fr, tr) + milliers(_MARQUEURS_EN_LIGNE.sub(" ", tr), langue)

