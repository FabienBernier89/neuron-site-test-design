"""Lexique des termes à vérifier dans CHnell avant toute traduction nouvelle (tâche 4.1).

candidats(langue, table, termes_v1, pages) rend la liste des termes techniques, juridiques et financiers que Fabien fait
vérifier dans CHnell, chaque entrée gardant son origine :

    {"fr": "capital-actions", "origine": ["v1:termes-de", "segments-nouveaux"], "priorite": 2,
     "pages": ["ressources/glossaire/capital-actions/"], "occurrences": 4, "retenu": true}

Trois sources, fusionnées par terme français (priorité la plus haute, origines réunies, pages réunies) :
1. termes V1 (termes-<langue>.json) des types loi, tableau, glossaire, metier et publication dont le terme FR figure dans
   un segment V2 : priorité 2 si au moins un de ces segments n'a pas de traduction V1 (texte nouveau ou modifié, origine
   « segments-nouveaux »), sinon priorité 3 (confirmation). retenu : true.
2. références légales des segments sans traduction V1 (origine « reference-legale », priorité 1, retenu : true) :
   abréviations de la colonne FR des termes de type loi (« LB », « CO », « Cst. »), et motif « art. 47 LB »,
   « art. 104 al. 1 CO ».
3. n-grammes de 2 à 4 mots présents au moins 2 fois dans les segments sans traduction V1, sans mot outil en bord ni
   marque (origine « ngramme », priorité 1, retenu : null : l'agent trie, Fabien valide la liste, décision V5). Un n-gramme
   contenu dans un n-gramme plus long de même fréquence est retiré, et un n-gramme déjà terme V1 n'est pas doublé.

Un segment « sans traduction V1 » est un texte de la page FR assemblée qui n'a ni entrée v1 ou invariant dans la table de
la langue (pour cette page), ni statut d'invariant (Table.est_invariant) : texte absent de la table, adapté, ou en mt.
Les marques et les libellés de l'application (src/langues/proteges.json) ne sont jamais candidats : un n-gramme ne peut
ni les contenir ni les traverser, et un passage plus anglais, italien ou allemand que français n'a pas de n-grammes
(démos, équivalents du glossaire). Les unités lang="fr" (sources françaises des démos) et les avis fictifs hors FR ne
comptent pas, comme dans traduire.analyser. « pages » : clés de page de build.PAGES (chaîne vide pour l'accueil), triées.
« occurrences » : occurrences dans les segments distincts concernés ; un même texte repris sur plusieurs pages (menu, pied)
compte une fois, pour qu'un libellé de navigation ne passe pas pour un terme répété.

Le lexique vit hors du dépôt public (Ruling 5, décision V6) : TERMINOLOGIE, surchargé par la variable d'environnement
NEURON_TERMINOLOGIE, contient lexique.json ({langue: [entrées]}), puis journal.jsonl et glossaire.json (tâches 4.2 et
4.3). Aucun test ne lit ni n'écrit ce dossier. Commande : python3 -m outils.i18n lexique de.

Bibliothèque standard seulement."""
import json
import os
import re
from collections import Counter
from functools import lru_cache
from pathlib import Path

from outils.i18n import controles, traduire
from outils.i18n import segments as S
from outils.i18n.table import LANGUES, Table

TERMINOLOGIE = Path(os.environ.get("NEURON_TERMINOLOGIE") or
                    Path.home() / "Claude project/Bibliotheque-Claude/07-Ressources-traduction/Neuron/site-v2/terminologie")
LEXIQUE = "lexique.json"
TYPES_V1 = ("loi", "tableau", "glossaire", "metier", "publication")
ORIGINES = ("v1:termes-", "segments-nouveaux", "reference-legale", "ngramme")  # ordre d'affichage des origines
STATUTS_V1 = {"v1", "invariant"}  # statuts d'une traduction déjà validée : le segment n'est pas nouveau
N_MIN, N_MAX, FREQUENCE_MIN = 2, 4, 2

# Mots outils français : un n-gramme ne commence ni ne finit par l'un d'eux (les élisions portent leur apostrophe)
MOTS_OUTILS = frozenset("""
le la les l' un une des du de d' au aux à a en dans sur sous par pour avec sans chez entre vers contre selon sauf depuis
pendant avant après dès et ou ni mais or donc car que qu' si lorsque lorsqu' puisque puisqu' quand comme jusqu' parmi
je j' tu il elle on nous vous ils elles me m' te t' se s' lui leur leurs y ce c' cet cette ces ça ceci cela celui celle
ceux celles qui quoi dont où quel quelle quels quelles lequel laquelle lesquels lesquelles
mon ma mes ton ta tes son sa ses notre nos votre vos
ne n' pas plus moins très trop aussi ainsi alors déjà encore toujours jamais souvent bien mal peu beaucoup puis
tout tous toute toutes même autre autres chaque plusieurs certains certaines quelques tel telle tels telles
est sont être été étant a ont avoir avez avons êtes sommes soit sera seront serait fait faire peut peuvent pouvez
doit doivent
""".split())

# Mots outils propres au français, et à l'anglais, à l'italien et à l'allemand : les démos et le glossaire portent aussi
# des textes dans ces langues, qui ne sont pas des termes français (un passage où l'étranger l'emporte est ignoré)
FRANCAIS = frozenset("les des du une est sont dans pour avec sur que qui vous nous aux ce cette ces votre notre au et".split())
ETRANGERS = frozenset("""
the of and to in is are for with by from this that be shall must was were
il lo gli della dello dei degli delle che per con nel nella sono è una ai
der die das und ist nicht für mit von zu den dem ein eine im auf
""".split())

_MARQUEUR = re.compile(r"\{/?\d+\}")
_FRONTIERE_CELLULES = re.compile(r"\{/\d+\}(?:\{/?\d+\})*\{\d+\}")  # fin d'un élément en ligne collé au début du suivant
# mot (composé avec traits d'union, élision comprise : « l' » est un mot à part) ou jeton à chiffre (rupture)
_JETON = re.compile(r"\w*\d\w*|[^\W\d_]+(?:-[^\W\d_]+)*'?")
_ABREVIATION = re.compile(r"^(?=(?:.*[A-Z]){2}|.*\.$)[A-Za-z]+\.?$")  # CC, LBA, nLPD, Cst.
_ARTICLE = r"art\. \d+[a-z]*(?: al\. \d+)? "


def _normal(texte):
    return " ".join(texte.replace("’", "'").split())


def _sans_marqueurs(texte):
    """Texte d'un segment pour la recherche de termes : marqueurs {n} remplacés par une espace, apostrophes droites."""
    return _normal(_MARQUEUR.sub(" ", texte))


def _pour_ngrammes(texte):
    """Texte d'un segment pour les n-grammes, apostrophes droites : deux éléments en ligne collés (cellules de démo)
    sont séparés par un saut de ligne, qui coupe les passages ; les autres marqueurs deviennent des espaces."""
    return _MARQUEUR.sub(" ", _FRONTIERE_CELLULES.sub("\n", texte.replace("\u2019", "'")))


@lru_cache(maxsize=2)
def _motif_protege(libelles):
    """Motif des marques (insensible à la casse), ou des libellés de l'application : insensible à la casse pour un
    libellé de plusieurs mots (« Translation engine »), sensible pour un seul mot (« Alternatives » est aussi un mot
    français). Du plus long au plus court."""
    p = controles.proteges()
    avant, apres = controles._MOT_ENTIER
    if not libelles:
        noms = sorted(p["marques"], key=len, reverse=True)
        return re.compile(avant + "(?:" + "|".join(re.escape(n) for n in noms) + ")" + apres, re.I)
    noms = sorted(p["libelles_application"], key=len, reverse=True)
    phrases = "|".join(re.escape(n) for n in noms if " " in n)
    mots = "|".join(re.escape(n) for n in noms if " " not in n)
    return re.compile(avant + "(?:(?i:" + phrases + ")|" + mots + ")" + apres)


def _est_protege(texte):
    """Vrai si le texte est une marque ou un libellé de l'application, ou en contient un."""
    return bool(_motif_protege(False).search(texte) or _motif_protege(True).search(texte))


# ---------- segments V2 ----------

def segments_v2(langue, table, pages):
    """Segments distincts du site tel que la langue le verrait : {texte brut: {"pages": {page}, "nouveau": {page}}},
    texte brut = texte de l'unité sans marqueurs, aux espaces normalisés. « nouveau » : pages où le texte n'a pas de
    traduction V1 (ni invariant). pages : {clé de page: HTML assemblé} (traduire.pages_assemblees)."""
    segments = {}
    for page, html in sorted(pages.items()):
        for u in S.extraire_page(traduire.retirer_avis_fictifs(html)):
            if u["lang_fr"]:
                continue
            brut = u["texte"]
            entree = table.chercher(brut, page)
            nouveau = not ((entree and entree["statut"] in STATUTS_V1) or Table.est_invariant(brut))
            cle = _sans_marqueurs(brut)
            if not cle:
                continue
            s = segments.setdefault(cle, {"brut": brut, "pages": set(), "nouveau": set()})
            s["pages"].add(page)
            if nouveau:
                s["nouveau"].add(page)
    return segments


# ---------- source 1 : termes V1 ----------

def _motif_terme(fr):
    """Motif d'un terme FR : mot entier ; sensible à la casse pour une abréviation (« CO »), sinon insensible."""
    sensible = bool(_ABREVIATION.match(fr))
    return re.compile(controles._MOT_ENTIER[0] + re.escape(fr) + controles._MOT_ENTIER[1], 0 if sensible else re.I)


def _origine_v1(langue):
    return f"v1:termes-{langue}"


def _candidats_v1(langue, termes_v1, segments):
    """Entrées de la source 1 (une par terme FR distinct)."""
    sortie = {}
    textes = list(segments)
    minuscules = [t.lower() for t in textes]
    vus = set()
    for t in termes_v1:
        fr = _normal(t["fr"])
        if t.get("type") not in TYPES_V1 or fr in vus or _est_protege(fr):
            continue
        vus.add(fr)
        motif, bas = _motif_terme(fr), fr.lower()
        touches = [i for i, m in enumerate(minuscules) if bas in m and motif.search(textes[i])]
        nouveaux = [i for i in touches if segments[textes[i]]["nouveau"]]
        retenus, nouveau = (nouveaux, True) if nouveaux else (touches, False)
        if not retenus:
            continue
        pages = set()
        for i in retenus:
            s = segments[textes[i]]
            pages |= s["nouveau"] if nouveau else s["pages"]
        sortie[fr] = {"fr": fr, "origine": {_origine_v1(langue)} | ({"segments-nouveaux"} if nouveau else set()),
                      "priorite": 2 if nouveau else 3, "pages": pages,
                      "occurrences": sum(len(motif.findall(textes[i])) for i in retenus), "retenu": True}
    return sortie


# ---------- source 2 : références légales ----------

def abreviations_loi(termes_v1):
    """Abréviations de la colonne FR des termes de type loi (« CC », « LBA », « nLPD », « Cst. »), triées."""
    return sorted({_normal(t["fr"]) for t in termes_v1
                   if t.get("type") == "loi" and _ABREVIATION.match(_normal(t["fr"]))})


def _candidats_references(termes_v1, segments):
    """Entrées de la source 2 : abréviations de lois et références « art. 47 LB » des segments sans traduction V1."""
    abreviations = abreviations_loi(termes_v1)
    if not abreviations:
        return {}
    alternance = "|".join(re.escape(a) for a in sorted(abreviations, key=len, reverse=True))
    fin = r"(?![^\W_])"
    motif_ref = re.compile(r"(?<![^\W_])" + _ARTICLE + "(?:" + alternance + ")" + fin)
    motif_abr = re.compile(r"(?<![^\W_])(?:" + alternance + ")" + fin)
    comptes, pages = Counter(), {}
    for texte, s in segments.items():
        if not s["nouveau"]:
            continue
        for motif in (motif_ref, motif_abr):
            for m in motif.finditer(texte):
                fr = _normal(m.group(0))
                comptes[fr] += 1
                pages.setdefault(fr, set()).update(s["nouveau"])
    return {fr: {"fr": fr, "origine": {"reference-legale"}, "priorite": 1, "pages": pages[fr],
                 "occurrences": n, "retenu": True} for fr, n in comptes.items()}


# ---------- source 3 : n-grammes ----------

def _passages(texte):
    """Suites de mots d'un texte de segment, sans rupture : la ponctuation, les nombres, les sauts de ligne, les marques
    et les libellés de l'application coupent les passages (un n-gramme ne les traverse jamais)."""
    texte = _motif_protege(True).sub(" \n ", _motif_protege(False).sub(" \n ", texte))
    passages = []
    for bloc in texte.split("\n"):
        courant, fin = [], 0
        for m in _JETON.finditer(bloc):
            if courant and bloc[fin:m.start()].strip():  # ponctuation entre deux mots
                passages.append(courant)
                courant = []
            fin = m.end()
            if any(c.isnumeric() for c in m.group(0)):
                if courant:
                    passages.append(courant)
                courant = []
            else:
                courant.append(m.group(0))
        if courant:
            passages.append(courant)
    return passages


def _etranger(passage):
    """Vrai si le passage est plus anglais, italien ou allemand que français (mots outils, à égalité : gardé)."""
    mots = [j.lower() for j in passage]
    return sum(m in ETRANGERS for m in mots) > sum(m in FRANCAIS for m in mots)


def _affichage(jetons):
    return "".join(j if j.endswith("'") else j + " " for j in jetons).strip()


def _candidats_ngrammes(segments, exclus):
    """Entrées de la source 3. exclus : termes (en minuscules) déjà candidats d'une autre source, jamais doublés."""
    comptes, formes, formes_debut, pages = Counter(), {}, {}, {}
    for texte, s in segments.items():
        if not s["nouveau"]:
            continue
        for passage in _passages(_pour_ngrammes(s["brut"])):
            if _etranger(passage):
                continue
            bas = [j.lower() for j in passage]
            for n in range(N_MIN, N_MAX + 1):
                for i in range(len(passage) - n + 1):
                    gram = tuple(bas[i:i + n])
                    if gram[0] in MOTS_OUTILS or gram[-1] in MOTS_OUTILS:
                        continue
                    comptes[gram] += 1
                    forme = passage[i:i + n]
                    if i == 0 and forme[0][1:].islower():  # majuscule de début de phrase : retirée
                        forme = [forme[0].lower()] + forme[1:]
                        formes_debut.setdefault(gram, Counter())[_affichage(forme)] += 1
                    else:
                        formes.setdefault(gram, Counter())[_affichage(forme)] += 1
                    pages.setdefault(gram, set()).update(s["nouveau"])
    frequents = {g: n for g, n in comptes.items() if n >= FREQUENCE_MIN}
    for gram, n in frequents.items():  # contenu dans un n-gramme plus long de même fréquence : retiré
        for taille in range(N_MIN, len(gram)):
            for i in range(len(gram) - taille + 1):
                sous = gram[i:i + taille]
                if frequents.get(sous) == n:
                    comptes[sous] = 0
    sortie = {}
    for gram, n in comptes.items():
        if n < FREQUENCE_MIN:
            continue
        # graphie la plus fréquente en milieu de phrase (celle des noms propres), sinon en début de phrase
        fr = sorted((formes.get(gram) or formes_debut[gram]).items(), key=lambda kv: (-kv[1], kv[0]))[0][0]
        if fr.lower() in exclus:
            continue
        sortie[fr] = {"fr": fr, "origine": {"ngramme"}, "priorite": 1, "pages": pages[gram], "occurrences": n,
                      "retenu": None}
    return sortie


# ---------- assemblage ----------

def _rang_origine(origine):
    return next(i for i, debut in enumerate(ORIGINES) if origine.startswith(debut)), origine


def _fusionner(sources):
    """Fusion par terme français : priorité la plus haute, origines et pages réunies, plus grand nombre d'occurrences,
    retenu true si une source le retient."""
    fusion = {}
    for source in sources:
        for fr, e in source.items():
            f = fusion.get(fr)
            if f is None:
                fusion[fr] = {**e, "origine": set(e["origine"]), "pages": set(e["pages"])}
                continue
            f["origine"] |= e["origine"]
            f["pages"] |= e["pages"]
            f["priorite"] = min(f["priorite"], e["priorite"])
            f["occurrences"] = max(f["occurrences"], e["occurrences"])
            f["retenu"] = True if (f["retenu"] or e["retenu"]) else None
    return fusion


def candidats(langue, table, termes_v1, pages=None):
    """Lexique des termes à vérifier pour une langue : liste d'entrées {fr, origine, priorite, pages, occurrences,
    retenu}, triée par priorité puis par terme français. termes_v1 : contenu de Sites/neuron/src/i18n/termes-<langue>.json.
    pages : {clé de page: HTML FR assemblé} ; traduire.pages_assemblees(langue, "apercu") si absent."""
    if langue not in LANGUES:
        raise ValueError(f"langue inconnue : « {langue} » (attendu : {', '.join(LANGUES)})")
    if pages is None:
        pages = traduire.pages_assemblees(langue, "apercu")
    segments = segments_v2(langue, table, pages)
    v1 = _candidats_v1(langue, termes_v1, segments)
    references = _candidats_references(termes_v1, segments)
    deja = {_normal(t["fr"]).lower() for t in termes_v1 if t.get("type") in TYPES_V1} | {fr.lower() for fr in references}
    ngrammes = _candidats_ngrammes(segments, deja)
    fusion = _fusionner([v1, references, ngrammes])
    entrees = [{"fr": e["fr"], "origine": sorted(e["origine"], key=_rang_origine), "priorite": e["priorite"],
                "pages": sorted(e["pages"]), "occurrences": e["occurrences"], "retenu": e["retenu"]}
               for e in fusion.values()]
    return sorted(entrees, key=lambda e: (e["priorite"], e["fr"]))


# ---------- fichier du lexique ----------

def _fichier(dossier):
    return Path(dossier or TERMINOLOGIE) / LEXIQUE


def _lire(dossier):
    f = _fichier(dossier)
    return json.loads(f.read_text(encoding="utf-8")) if f.is_file() else {}


def charger_lexique(langue, dossier=None):
    """Entrées du lexique d'une langue ([] si le fichier ou la langue n'existe pas encore)."""
    return _lire(dossier).get(langue, [])


def ecrire_lexique(langue, entrees, dossier=None):
    """Remplace les entrées de la langue dans lexique.json (les autres langues sont gardées) ; rend le chemin du fichier.
    Le dossier est créé au besoin."""
    f = _fichier(dossier)
    contenu = _lire(dossier)
    contenu[langue] = entrees
    f.parent.mkdir(parents=True, exist_ok=True)
    f.write_text(json.dumps({l: contenu[l] for l in sorted(contenu)}, indent=1, ensure_ascii=False) + "\n",
                 encoding="utf-8")
    return f


def conserver_decisions(nouveau, ancien):
    """Nouveau lexique où les décisions déjà prises (retenu true ou false) de l'ancien lexique l'emportent : relancer la
    commande ne défait jamais une validation de Fabien."""
    decisions = {e["fr"]: e["retenu"] for e in ancien if e.get("retenu") is not None}
    return [{**e, "retenu": decisions.get(e["fr"], e["retenu"])} for e in nouveau]


def compter(entrees):
    """{"total", "priorites": {1: n, 2: n, 3: n}, "origines": {origine: n}} ; une entrée compte dans chacune de ses origines."""
    origines = Counter(o for e in entrees for o in e["origine"])
    return {"total": len(entrees), "priorites": {p: sum(1 for e in entrees if e["priorite"] == p) for p in (1, 2, 3)},
            "origines": dict(sorted(origines.items()))}
