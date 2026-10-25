"""Mémoire de traduction tirée de la V1 : alignement des pages V1 (français et langue cible) et pré-remplissage de la
table de la langue au statut v1.

Les traductions DE, EN et IT des 156 pages de la V1 ont été validées par les traducteurs (commit V1 61282643 du
2026-10-05). Décision V2 de Fabien : un segment v1 part sans nouvelle relecture parce qu'il est IDENTIQUE à un texte
déjà validé. L'alignement ne pose donc une traduction que lorsqu'il est certain ; dans le doute, rien n'est posé et le
segment suit le circuit normal (LexMachina, adaptation, relecture). Chaque refus est compté dans le rapport, avec sa
cause.

Alignement d'une page (aligner_detail), à partir des unités de segments.extraire_page (tête, menu, main, pied) :
- passages et attributs, dans l'ordre : la suite des signatures (genre, attribut, balise et classe qui précèdent
  l'unité, lang="fr", écran d'application, balises et suite des marqueurs {n}…{/n}) est comparée par difflib. Seules
  les unités des plages égales sont appariées, si les liens externes de leurs balises ont les mêmes cibles (au segment
  de langue près : fedlex …/fr et …/en) ; une unité d'un écart, et ses voisines de même signature (on ne sait pas
  laquelle manque), sont refusées ; si moins de SEUIL des unités trouvent leur place, la page n'est pas alignée ;
- chaînes des JSON-LD et des JSON de données : script par script (même rang, même genre), chemin JSON par chemin JSON,
  à condition que les deux scripts aient le même squelette (mêmes chemins, mêmes @type). Le chemin apparie aussi les
  chaînes que l'extraction de la page traduite ne livre pas (name d'une WebPage « de-CH », lu comme un terme défini) ;
- les unités sous un lang="fr" explicite ne sont jamais appariées (Ruling 14 : gardées en français, la V1 les garde
  aussi ; une paire identique validerait à tort le même texte ailleurs). Quand la V1 traduite remplace un tel passage
  par un passage dans sa langue (exemple du glossaire EN et IT), l'unité qui le précède (son libellé, « Français » face
  à « English ») n'est pas appariée non plus.

Pré-remplissage (prefill), sur les paires de toutes les pages :
- écartées : les permutations (_permutations : tableau dont la V1 allemande met la colonne allemande en premier), et
  les traductions identiques au français lues dans les données structurées (que les traducteurs n'ont pas relues : la
  featureList de corrext/ est restée en français dans la V1 anglaise), sauf invariant (traduire._invariant) ;
- une traduction unique devient la traduction par défaut. Un doublon divergent (deux traductions du même texte selon
  la page) n'a pas de traduction par défaut (Ruling 21) : chaque traduction est posée pour ses pages seulement. Une
  traduction identique au français alors que le même texte est traduit ailleurs est un oubli de la V1 : elle est
  écartée ;
- deux traductions différentes du même texte dans une même page ne se représentent pas (une seule traduction par
  page) : le texte n'est alors posé nulle part ;
- une traduction identique au français (hors invariant) n'est jamais la traduction par défaut (Ruling 19) : l'entrée
  est « par page seulement » (Table.poser, sans_defaut), le texte n'est accepté tel quel que sur les pages où la V1
  l'a gardé ; ailleurs il reste à traduire ;
- une entrée relue ou invariante n'est jamais écrasée ; une traduction refusée par les contrôles de Table.poser (tirets, ß) n'est
  pas posée. Chaque refus est compté dans le rapport.

Sources non posées, volontairement :
- src/partials/404-textes.json de la V1 : sa note dit « traduction de Claude, à relire » et la validation du
  2026-10-05 ne porte que sur les 156 pages (src/langues/<l>/statut.json de la V1). Ses textes sont comptés dans le
  rapport (« 404_non_posee »), jamais posés en v1 ;
- src/i18n/<l>.json de la V1 : ses textes affichés dans les 156 pages sont déjà appariés par les pages ; les autres
  n'ont été vus par aucun traducteur dans une page validée. Comptés dans le rapport (« i18n_hors_pages »).

La suite (blocs recomposés, variantes de balisage, contextes V1 des textes à traduire : tâche 3.2) est dans
outils/i18n/recomposition.py.

Bibliothèque standard seulement."""
import difflib
import json
import re
from pathlib import Path

from outils.i18n import controles
from outils.i18n import segments as S
from outils.i18n import traduire as T
from outils.i18n.table import cle

# Part minimale des passages et attributs d'une page FR appariés pour que la page compte comme alignée : garde-fou
# contre deux pages qui ne se correspondent pas. Mesuré sur la V1 : 97,5 % au moins, sauf la page EN Langues et formats
# (86,5 % : les 36 langues de la liste y portent leur nom local en lang="xx", structure différente, refusées une à une).
SEUIL = 0.5
STATUT = "v1"
PROTEGES = ("relu", "invariant")  # statuts jamais écrasés par la mémoire V1
MEMOIRE = ("v1", "invariant")  # statuts comptés dans la couverture de la mémoire V1 (ni adapte, ni mt, ni relu)

_SCRIPT = re.compile(r"<script\b([^>]*)>(.*?)</script\s*>", re.S | re.I)
_CLASSE = re.compile(r"""\sclass\s*=\s*(?:"([^"]*)"|'([^']*)')""", re.I)
_MARQUEURS = re.compile(r"\{/?\d+\}")
_HREF = re.compile(r"""\shref\s*=\s*(?:"([^"]*)"|'([^']*)')""", re.I)
_EXTERNE = re.compile(r"^(?:https?:|mailto:|tel:)", re.I)
_SEGMENT_LANGUE = re.compile(r"(?<=/)(?:fr|de|it|en)(?:-ch)?(?=/|$|[?#])", re.I)
_PARAM_LANGUE = re.compile(r"([?&](?:lang|language|locale)=)(?:fr|de|it|en)(?:[-_]ch)?\b", re.I)
_BLANCS = re.compile(r"[ \t\r\n\f]+")  # blancs HTML seulement : l'espace insécable d'une traduction est gardée

CAUSES = {
    "ecart": "écart de structure",
    "voisin": "voisin d'un écart, même signature",
    "ld_structure": "données structurées : squelette différent",
    "ld_valeur": "données structurées : valeur absente ou non textuelle",
    "meme_page": "divergence dans une même page",
    "permutation": "permutation probable dans la page",
    "relu": "entrée relue ou invariante gardée",
    "cible": "cible d'un lien différente",
    "meme_source": "nomme une source dont la V1 a changé le lien sur la page",
    "ld_illisible": "données structurées : JSON traduit illisible",
    "libelle": "libellé d'un passage en français que la V1 remplace",
    "ld_identique": "identique au français dans les données structurées (oubli probable de la V1)",
    "identique_traduit": "identique au français, traduit ailleurs (oubli probable de la V1)",
}


def _normal(texte):
    return " ".join(texte.split())


def _blancs(texte):
    return _BLANCS.sub(" ", texte).strip()


def _etiquette(balise):
    """Nom et classe d'une balise : (« p », « micro »)."""
    c = _CLASSE.search(balise)
    return (S._nom(balise), (c.group(1) if c.group(1) is not None else c.group(2)) if c else "")


def _signature(source, u):
    """Signature d'un passage ou d'un attribut : deux unités de même signature occupent la même place dans deux pages
    construites sur le même gabarit."""
    k = source.rfind("<", 0, u["debut"])
    balise = source[k:source.find(">", k) + 1] if k >= 0 else ""
    marqueurs = tuple(_etiquette(e.get("ouvre") or e.get("vide")) for _, e in sorted(u["table"].items()))
    return (u["genre"], u["attr"], u["lang_fr"], u["ui"], _etiquette(balise), marqueurs,
            tuple(_MARQUEURS.findall(u["texte"])))


def _cibles(table_marqueurs):
    """Cibles externes des balises d'une unité, marqueur par marqueur : adresse du lien, au segment ou au paramètre de
    langue près (fedlex.admin.ch/eli/…/fr et …/en sont la même cible) ; None pour un lien interne (adapté à la langue
    par les adresses du site) ou une balise sans lien."""
    sortie = []
    for _, e in sorted(table_marqueurs.items()):
        m = _HREF.search(e.get("ouvre") or e.get("vide"))
        href = (m.group(1) if m.group(1) is not None else m.group(2)) if m else ""
        if not _EXTERNE.match(href):
            sortie.append(None)
            continue
        href = _PARAM_LANGUE.sub(lambda x: x.group(1) + "*", _SEGMENT_LANGUE.sub("*", href.strip()))
        sortie.append(href.lower().rstrip("/"))
    return tuple(sortie)


def _scripts(source):
    """Scripts de données de la page, dans l'ordre : [(genre « ld » ou « json », début du corps, corps)]."""
    sortie = []
    for m in _SCRIPT.finditer(source):
        attrs = m.group(1).lower()
        genre = "ld" if "ld+json" in attrs else "json" if "application/json" in attrs else None
        if genre:
            sortie.append((genre, m.start(2), m.group(2)))
    return sortie


def _squelette(donnees):
    """Chemins des valeurs d'un JSON, avec leur type (la valeur elle-même pour un @type)."""
    chemins = set()

    def visite(v, chemin):
        if isinstance(v, dict):
            for k, x in v.items():
                visite(x, chemin + (k,))
        elif isinstance(v, list):
            for i, x in enumerate(v):
                visite(x, chemin + (i,))
        else:
            chemins.add((chemin, v if chemin and chemin[-1] == "@type" else type(v).__name__))
    visite(donnees, ())
    return chemins


def _apparier_donnees(fr_html, tr_html, unites):
    """Unités ld et json de la page FR appariées chemin par chemin : (paires [(unité, texte traduit)], refus)."""
    sf, st = _scripts(fr_html), _scripts(tr_html)
    position = {}
    for rang, (_, debut, corps) in enumerate(sf):
        for chemin, a, _ in S._chaines_json(corps):
            position[debut + a] = (rang, chemin)
    traduits = {}
    for rang, (genre, _, corps) in enumerate(sf):
        if rang < len(st) and st[rang][0] == genre:
            try:
                donnees_tr = json.loads(st[rang][2])
            except ValueError:
                traduits[rang] = None
                continue
            if _squelette(json.loads(corps)) == _squelette(donnees_tr):
                traduits[rang] = donnees_tr
    paires, refus = [], []
    for u in unites:
        rang, chemin = position[u["debut"]]
        if rang not in traduits:
            refus.append((u, "ld_structure"))
            continue
        if traduits[rang] is None:
            refus.append((u, "ld_illisible"))
            continue
        valeur = S._suivre(traduits[rang], chemin)
        if isinstance(valeur, str) and valeur.strip():
            paires.append((u, valeur))
        else:
            refus.append((u, "ld_valeur"))
    return paires, refus


def aligner_detail(fr_html, tr_html):
    """Alignement détaillé d'une page V1 et de sa traduction : None si la page ne s'aligne pas (moins de SEUIL des
    passages et attributs FR appariés), sinon {"paires": [(texte FR, texte traduit, genre)], "refus": [{"fr", "cause"}]}.
    Les textes sont ceux de extraire_page (marqueurs {n}…{/n} compris) ; les blancs HTML d'une traduction de passage
    sont ramenés à une espace. Les unités lang="fr" ne figurent ni dans les paires ni dans les refus."""
    ua, ub = S.extraire_page(fr_html), S.extraire_page(tr_html)
    ha = [u for u in ua if u["genre"] in ("bloc", "attr")]
    hb = [u for u in ub if u["genre"] in ("bloc", "attr")]
    sa, sb = [_signature(fr_html, u) for u in ha], [_signature(tr_html, u) for u in hb]
    ops = difflib.SequenceMatcher(None, sa, sb, autojunk=False).get_opcodes()
    apparies, causes = {}, {}
    for op, i1, i2, j1, _ in ops:
        if op == "equal":
            apparies.update((i1 + d, j1 + d) for d in range(i2 - i1))
    for op, i1, i2, j1, j2 in ops:
        if op == "equal":
            continue
        causes.update((i, "ecart") for i in range(i1, i2))
        if i1 > 0 and i1 - 1 in apparies and any(ha[i]["lang_fr"] for i in range(i1, i2)):
            # passage lang="fr" sans équivalent : la V1 traduite l'a remplacé par un passage dans sa langue (exemple du
            # glossaire) ; son libellé (« Français » face à « English ») ne vaut pas pour la V2, qui garde le français
            causes[i1 - 1] = "libelle"
        en_jeu = set(sa[i1:i2]) | set(sb[j1:j2])
        for pas, i in ((-1, i1 - 1), (1, i2)):  # voisines de même signature : laquelle manque, on ne le sait pas
            while 0 <= i < len(sa) and i in apparies and sa[i] in en_jeu:
                causes.setdefault(i, "voisin")
                i += pas
    if ha and (len(apparies) - sum(1 for i in causes if i in apparies)) / len(ha) < SEUIL:
        return None
    paires, refus, changes = [], [], {}
    for i, u in enumerate(ha):
        if u["lang_fr"]:
            continue
        cf, ct = _cibles(u["table"]), _cibles(hb[apparies[i]]["table"]) if i in apparies else None
        if i in causes:
            refus.append((u, causes[i]))
        elif cf != ct:
            # la V1 traduite cite une autre source (glossaire EN : Constitution au lieu de la LTF) ; on retient les
            # marqueurs dont la cible a changé, et eux seuls (même signature : mêmes marqueurs, dans le même ordre)
            refus.append((u, "cible"))
            changes[u["id"]] = [n for n, a, b in zip(sorted(u["table"]), cf, ct) if a != b]
        else:
            t = hb[apparies[i]]["texte"]
            paires.append((u, _blancs(t) if u["genre"] == "bloc" else t))
    p, r = _apparier_donnees(fr_html, tr_html, [u for u in ua if u["genre"] in ("ld", "json") and not u["lang_fr"]])
    paires += p
    refus += r
    # une source dont la V1 a changé le lien (glossaire EN : Constitution au lieu de la LTF) : tout texte de la page qui
    # la nomme est suspect (« art. 188 Cst. et art. 1 LTF · source : Fedlex, loi sur le Tribunal fédéral », sans lien)
    sources = set()
    for u, c in refus:
        if c == "cible":
            for n in changes[u["id"]]:
                m = re.search(r"\{%d\}(.*?)\{/%d\}" % (n, n), u["texte"])
                nom = _sans_balises(m.group(1)) if m else ""
                if len(nom) >= 8:
                    sources.add(nom)
    if sources:
        gardees = []
        for u, tr in paires:
            if any(s in _sans_balises(u["texte"]) for s in sources):
                refus.append((u, "meme_source"))
            else:
                gardees.append((u, tr))
        paires = gardees
    paires.sort(key=lambda x: x[0]["debut"])
    refus.sort(key=lambda x: x[0]["debut"])
    return {"paires": [(u["texte"], t, u["genre"]) for u, t in paires],
            "refus": [{"fr": u["texte"], "cause": CAUSES[c]} for u, c in refus]}


def aligner_page(fr_html, tr_html):
    """Paires (texte FR, texte traduit), unité par unité ; None si la page ne s'aligne pas (aligner_detail)."""
    d = aligner_detail(fr_html, tr_html)
    return None if d is None else [(fr, tr) for fr, tr, _ in d["paires"]]


# ---------- pré-remplissage ----------

def _compter(refus, cause, texte, distincts):
    e = refus.setdefault(cause, {"unites": 0, "textes": 0, "mots": 0})
    e["unites"] += 1
    if (cause, _normal(texte)) not in distincts:
        distincts.add((cause, _normal(texte)))
        e["textes"] += 1
        e["mots"] += T.mots(texte)


def _sans_balises(texte):
    return " ".join(_MARQUEURS.sub(" ", texte).split())


def couverture(table, pages, zone="main", balises=True):
    """Part des mots français (en %, une décimale) des pages V2 assemblées qui ont une traduction dans la table. Mots
    comptés une fois par texte distinct (comme l'audit, § 2.2), avis fictifs retirés, unités lang="fr" exclues.
    zone : « main » (contenu de <main>) ou « page » (page entière : tête, menu, pied compris).
    balises : True, le texte doit être celui d'une entrée, marqueurs {n}…{/n} compris (seule couverture utilisable par
    traduire) ; False, définition de l'audit (§ 1, 84,6 %) : le texte sans ses balises suffit, ce qui compte aussi les
    passages dont seul le balisage a changé entre la V1 et la V2. Seules comptent les traductions de la mémoire V1
    (statuts v1 et invariant, MEMOIRE) : ni les recompositions adaptées, ni les traductions relues."""
    total = couverts = 0
    vus = set()
    sans = ({_sans_balises(e["fr"]) for e in table.entrees.values()
             if e["statut"] in MEMOIRE or any(v["statut"] in MEMOIRE for v in e["par_page"].values())}
            if not balises else set())
    for page, html in pages.items():
        html = T.retirer_avis_fictifs(html)
        debut, fin = 0, len(html)
        if zone == "main":
            m = re.search(r"<main\b", html)
            debut, fin = (m.start(), html.find("</main>", m.start())) if m else (0, 0)
        for u in S.extraire_page(html):
            texte = _normal(u["texte"])
            if u["lang_fr"] or not debut <= u["debut"] < fin or texte in vus:
                continue
            vus.add(texte)
            n = T.mots(texte)
            total += n
            trouve = table.chercher(texte, page)
            if (trouve and trouve["statut"] in MEMOIRE) or (not balises and _sans_balises(texte) in sans):
                couverts += n
    return round(100 * couverts / total, 1) if total else 0.0


def _permutations(lues):
    """Paires lues dont la place dans la page traduite est celle d'un autre texte : la V1 a permuté des éléments (un
    tableau de langues dont la version allemande met la colonne allemande en premier : FR « Allemand » face à DE
    « Französisch »). lues : [(texte FR, traduction, page, adresse, genre)]. Renvoie les rangs suspects. Une paire X → T de la
    page P est suspecte :
    - si P a aussi la paire T → X (permutation littérale : « OR » face à « CO » et « CO » face à « OR ») ;
    - ou si T n'est jamais la traduction de X ailleurs, qu'un autre texte Y de P a T pour traduction ailleurs, et que
      la traduction de Y sur P est une traduction de X ailleurs (permutation croisée).
    « Ailleurs » : toute autre occurrence lue (autre page, ou autre place de la même page)."""
    trads = {}
    for fr, tr, *_ in lues:
        compte = trads.setdefault(fr, {})
        compte[_blancs(tr)] = compte.get(_blancs(tr), 0) + 1

    def ailleurs(fr, tr, t):
        """Vrai si t est une traduction de fr dans une occurrence autre que (fr → tr)."""
        n = trads.get(fr, {}).get(t, 0)
        return n - (t == _blancs(tr)) > 0

    par_page = {}
    for i, (fr, tr, page, *_) in enumerate(lues):
        par_page.setdefault(page, []).append(i)
    suspectes = set()
    for rangs in par_page.values():
        paires = {(lues[i][0], _blancs(lues[i][1])) for i in rangs}
        for i in rangs:
            x, tx = lues[i][0], lues[i][1]
            t = _blancs(tx)
            if t == x or ailleurs(x, tx, t):
                continue
            if (t, x) in paires:
                suspectes.add(i)
                continue
            for j in rangs:
                y, ty = lues[j][0], lues[j][1]
                if y != x and ailleurs(y, ty, t) and ailleurs(x, tx, _blancs(ty)):
                    suspectes.add(i)
                    break
    return suspectes


def _textes_404(neuron, langue):
    """Textes de la 404 de la V1 : [(texte FR, traduction)] lus dans src/partials/404.html (data-t) et
    src/partials/404-textes.json ; [] si les fichiers manquent."""
    gabarit, textes = neuron / "src/partials/404.html", neuron / "src/partials/404-textes.json"
    if not (gabarit.is_file() and textes.is_file()):
        return []
    trad = json.loads(textes.read_text(encoding="utf-8")).get(langue, {})
    fr = {m.group(1): m.group(2) for m in re.finditer(r'data-t="([^"]+)"[^>]*>(.*?)</', gabarit.read_text(encoding="utf-8"), re.S)}
    return [(fr[k], trad[k]) for k in fr if k in trad]


def _retirer_v1(table):
    """Retire de la table les traductions posées par une mémoire V1 précédente (statut v1, source « V1 … ») : la mémoire
    se recalcule entièrement à chaque appel, sans garder une paire qu'un contrôle refuse désormais. Une entrée qui garde
    une traduction de page d'un autre statut (relue) devient « par page seulement » si sa traduction par défaut venait
    de la V1 : le nouveau calcul la repose, ou non."""
    def de_v1(e):
        return e["statut"] == STATUT and (e["source"] or "").startswith("V1 ")
    for k in list(table.entrees):
        e = table.entrees[k]
        e["par_page"] = {p: v for p, v in e["par_page"].items() if not de_v1(v)}
        if de_v1(e):
            e.update(trad=None, statut=None, source=None)
        if e["trad"] is None and not e["par_page"]:
            del table.entrees[k]


def prefill(langue, neuron, table, pages=None):
    """Pré-remplit la table de la langue depuis la V1 (dossier neuron, lu en lecture seule) et renvoie le rapport :
    {"pages_alignees", "pages_non_alignees": [{"page", "cause"}], "segments_v1" (textes FR posés par défaut),
     "par_page_v1", "par_page_seulement" (textes posés pour leurs pages seulement : identiques au français, Ruling 19, ou
     doublons divergents, Ruling 21),
     "doublons_divergents": [{"fr", "trads", "pages"}], "couverture_mots" (main), "couverture_page",
     "couverture_texte" (main, balises ignorées : définition de l'audit),
     "refus": {cause: {"unites", "textes", "mots"}}, "refus_non_rattrapes": {"textes", "mots"}, "404_non_posee",
     "i18n_hors_pages"}.
    pages : pages FR assemblées de la V2 ({page: html}) pour la couverture ; par défaut celles du build
    (traduire.pages_assemblees). Les traductions d'une mémoire V1 précédente sont d'abord retirées (_retirer_v1). La
    table n'est pas écrite sur disque (Table.enregistrer)."""
    neuron = Path(neuron)
    routes = json.loads((neuron / "src/routes.json").read_text(encoding="utf-8"))
    _retirer_v1(table)
    occurrences = {}  # texte FR normalisé -> [(traduction, page, adresse V1)], dans l'ordre de lecture
    refus, distincts = {}, set()
    alignees, non_alignees, lues = 0, [], []
    for cle_fr, adresses in routes.items():
        page, adresse = cle_fr[3:], adresses.get(langue)
        f_fr = neuron / "docs" / cle_fr / "index.html"
        f_tr = neuron / "docs" / adresse / "index.html" if adresse else None
        if not (f_fr.is_file() and f_tr and f_tr.is_file()):
            non_alignees.append({"page": page, "cause": "page V1 absente"})
            continue
        try:
            d = aligner_detail(f_fr.read_text(encoding="utf-8"), f_tr.read_text(encoding="utf-8"))
        except ValueError as e:
            non_alignees.append({"page": page, "cause": f"page V1 illisible : {e}"})
            continue
        if d is None:
            non_alignees.append({"page": page, "cause": f"structure différente (moins de {SEUIL:.0%} des unités)"})
            continue
        alignees += 1
        for r in d["refus"]:
            _compter(refus, r["cause"], r["fr"], distincts)
        lues += [(_normal(fr), tr, page, adresse, genre) for fr, tr, genre in d["paires"]]
    suspectes = _permutations(lues)
    for i, (fr, tr, page, adresse, genre) in enumerate(lues):
        if i in suspectes:
            _compter(refus, CAUSES["permutation"], fr, distincts)
        elif genre in ("ld", "json") and _normal(tr) == fr and not T._invariant(fr, langue):
            # les traducteurs ont relu les pages affichées, pas les données structurées : un texte resté en français
            # n'y est pas une validation (featureList de corrext/ en anglais)
            _compter(refus, CAUSES["ld_identique"], fr, distincts)
        else:
            occurrences.setdefault(fr, []).append((tr, page, adresse))

    doublons, poses, par_page, seulement = [], 0, 0, 0
    for fr, occ in occurrences.items():
        entree = table.entrees.get(cle(fr))
        if entree and entree["statut"] in PROTEGES:
            _compter(refus, CAUSES["relu"], fr, distincts)
            continue
        # traductions distinctes (aux blancs près), dans l'ordre de lecture ; mêmes contrôles que Table.poser
        valides, refusees = {}, set()
        for tr, _, _ in occ:
            n = _blancs(tr)
            if n in valides or n in refusees:
                continue
            problemes = controles.tirets(tr) + (controles.eszett(fr, tr) if langue == "de" else [])
            if problemes:
                refusees.add(n)
                _compter(refus, "contrôle : " + problemes[0]["regle"], fr, distincts)
                continue
            valides[n] = tr
        identiques = [n for n in valides if _normal(n) == fr]
        if len(valides) > 1 and identiques and not T._invariant(fr, langue):
            # resté en français sur une page, traduit sur une autre : un oubli de la V1, jamais une validation ; ses
            # pages prennent la traduction
            del valides[identiques[0]]
            _compter(refus, CAUSES["identique_traduit"], fr, distincts)
        if not valides:
            continue
        par_page_fr = {}  # page -> {traduction normalisée: adresse V1}
        for tr, page, adresse in occ:
            if _blancs(tr) in valides:
                par_page_fr.setdefault(page, {}).setdefault(_blancs(tr), adresse)
        if any(len(v) > 1 for v in par_page_fr.values()):
            # deux traductions dans une même page : impossible de dire laquelle va où, le texte n'est posé nulle part
            _compter(refus, CAUSES["meme_page"], fr, distincts)
            continue
        defaut = next(iter(valides))
        if len(valides) > 1 or (_normal(defaut) == fr and not T._invariant(fr, langue)):
            # Ruling 21 : doublon divergent, chaque traduction n'est validée que sur ses pages ; Ruling 19 : gardé en
            # français par la V1 (terme d'une colonne française de tableau). Posés pour leurs pages seulement, jamais
            # par défaut : ailleurs, le même texte suit le circuit normal
            for page, trads in par_page_fr.items():
                (n, adresse), = trads.items()
                propre = table.entrees.get(cle(fr), {}).get("par_page", {}).get(page)
                if not (propre and propre["statut"] in PROTEGES):
                    table.poser(fr, valides[n], STATUT, f"V1 {adresse}", page=page, sans_defaut=True)
                    par_page += 1
            seulement += 1
            if len(valides) > 1:
                doublons.append({"fr": fr, "trads": list(valides), "pages": list(dict.fromkeys(p for _, p, _ in occ))})
            continue
        table.poser(fr, valides[defaut], STATUT, f"V1 {next(a for t, _, a in occ if _blancs(t) == defaut)}")
        poses += 1

    poses_fr = {e["fr"] for e in table.entrees.values()
                if e["statut"] == STATUT or any(v["statut"] == STATUT for v in e["par_page"].values())}
    non_rattrapes = {_normal(t) for c, t in distincts if c != CAUSES["relu"]} - poses_fr
    i18n = neuron / "src/i18n" / f"{langue}.json"
    hors_pages = [k for k in (json.loads(i18n.read_text(encoding="utf-8")) if i18n.is_file() else {})
                  if _normal(k) not in occurrences]
    if pages is None:
        pages = T.pages_assemblees(langue, "apercu")
    return {"langue": langue, "pages_alignees": alignees, "pages_non_alignees": non_alignees, "segments_v1": poses,
            "par_page_v1": par_page, "par_page_seulement": seulement, "doublons_divergents": doublons,
            "couverture_mots": couverture(table, pages), "couverture_page": couverture(table, pages, "page"),
            "couverture_texte": couverture(table, pages, balises=False),
            "refus": dict(sorted(refus.items())),
            "refus_non_rattrapes": {"textes": len(non_rattrapes), "mots": sum(T.mots(t) for t in non_rattrapes)},
            "404_non_posee": len(_textes_404(neuron, langue)), "i18n_hors_pages": len(hors_pages)}
