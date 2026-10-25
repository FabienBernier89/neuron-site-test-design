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

Bibliothèque standard seulement."""
import bisect
import difflib
import functools
import html as H
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
    passages dont seul le balisage a changé entre la V1 et la V2."""
    total = couverts = 0
    vus = set()
    sans = {_sans_balises(e["fr"]) for e in table.entrees.values()} if not balises else set()
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
            if table.chercher(texte, page) is not None or (not balises and _sans_balises(texte) in sans):
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


# ---------- tâche 3.2 : blocs recomposés, variantes de balisage, morceaux et corrections ----------
#
# Ce que l'alignement strict ne pose pas. Rien n'y est jamais v1 : un texte posé ici n'est pas identique à un texte
# validé. Statut adapte (accepté en aperçu seulement, avec le bandeau ; relu ensuite), ou aucune traduction et un
# contexte V1 pour l'adaptation (a_traduire.json, traduire.fichier_a_traduire).

ADAPTE = "adapte"
VALIDES = ("v1", "invariant", "relu")  # traductions dont une recomposition ou une variante peut partir
SOURCE_RECOMPOSITION = "recomposition V1 "
SOURCE_VARIANTE = "variante de balisage "  # suivi de la source de la traduction V1 (« V1 de/kontakt/ »)
MOTS_MORCEAU = 2  # un morceau plus court n'a pas de contexte : un mot isolé se retrouve dans trop de textes V1
_JETON = re.compile(r"\{(/?)(\d+)\}")
_BALISE = re.compile(r"<[^>]+>")


def _plat(texte):
    """Texte sans marqueurs ni balises, espaces normalisées (comparaison des corrections et des morceaux)."""
    return " ".join(_BALISE.sub(" ", _MARQUEURS.sub(" ", texte)).split())


def _sans_blancs(texte):
    """Texte sans marqueurs ni aucun blanc : clé des variantes de balisage (« Grec{1}Greek{/1} », « Grec {1}Greek{/1} »)."""
    return "".join(_MARQUEURS.sub("", texte).split())


@functools.lru_cache(maxsize=None)
def _textes_page_v1(chemin, _mtime):
    """Textes FR d'une page V1 construite, dans l'ordre de la page, aux espaces normalisées (unités lang="fr" exclues)."""
    html = Path(chemin).read_text(encoding="utf-8")
    return tuple(_normal(u["texte"]) for u in S.extraire_page(html) if not u["lang_fr"])


def _index_v1(langue, neuron, table):
    """Textes des pages FR de la V1 et leur traduction validée sur leur page :
    {"rangs": {texte: {page: [rangs dans la page]}}, "trad": {(texte, page): (traduction, a_un_defaut)},
     "tous": textes V1 avec ou sans traduction, "adresses": {page: adresse V1 de la langue},
     "variantes": {texte sans marqueurs ni blancs: [textes V1]}, "long_max"}.
    Traduction validée : celle que la table rend pour la page (Table.chercher), statut VALIDES, ou le texte lui-même
    pour un invariant sans entrée. a_un_defaut : l'entrée a une traduction par défaut (False pour un texte posé « par
    page seulement », identique au français ou doublon divergent : Rulings 19 et 21)."""
    routes = json.loads((Path(neuron) / "src/routes.json").read_text(encoding="utf-8"))
    rangs, trads, tous, adresses = {}, {}, set(), {}
    for cle_fr, routes_page in routes.items():
        page, adresse = cle_fr[3:], routes_page.get(langue)
        f = Path(neuron) / "docs" / cle_fr / "index.html"
        if not (adresse and f.is_file()):
            continue
        adresses[page] = adresse
        for rang, texte in enumerate(_textes_page_v1(str(f), f.stat().st_mtime)):
            tous.add(texte)
            if (texte, page) not in trads:
                e = table.chercher(texte, page)
                if e and e["statut"] in VALIDES:
                    trads[(texte, page)] = (e["trad"], table.entrees[cle(texte)]["trad"] is not None)
                elif e is None and T._invariant(texte, langue):
                    trads[(texte, page)] = (texte, True)
                else:
                    trads[(texte, page)] = None
            if trads[(texte, page)] is not None:
                rangs.setdefault(texte, {}).setdefault(page, []).append(rang)
    variantes = {}
    for texte in rangs:
        variantes.setdefault(_sans_blancs(texte), []).append(texte)
    return {"rangs": rangs, "trad": {k: v for k, v in trads.items() if v}, "tous": tous, "adresses": adresses,
            "variantes": {k: sorted(v) for k, v in variantes.items()}, "long_max": max(map(len, rangs), default=0)}


def _manquants_v2(langue, table, pages):
    """{texte: [pages V2]} des textes sans traduction pour leur page, comme traduire.analyser les verrait (avis
    fictifs retirés ; unités lang="fr" et invariants exclus)."""
    sortie = {}
    for page, html in pages.items():
        for u in S.extraire_page(T.retirer_avis_fictifs(html)):
            texte = _normal(u["texte"])
            if not u["lang_fr"] and table.chercher(texte, page) is None and not T._invariant(texte, langue):
                sortie.setdefault(texte, [])
                if page not in sortie[texte]:
                    sortie[texte].append(page)
    return sortie


def _retirer_recompositions(table):
    """Retire les traductions posées par une recomposition précédente (statut adapte, source « recomposition V1 … »
    ou « variante de balisage … ») : elles se recalculent entièrement à chaque appel, comme la mémoire V1."""
    def d_ici(e):
        return e["statut"] == ADAPTE and (e["source"] or "").startswith((SOURCE_RECOMPOSITION, SOURCE_VARIANTE))
    for k in list(table.entrees):
        e = table.entrees[k]
        e["par_page"] = {p: v for p, v in e["par_page"].items() if not d_ici(v)}
        if d_ici(e):
            e.update(trad=None, statut=None, source=None)
        if e["trad"] is None and not e["par_page"]:
            del table.entrees[k]


def _paires_marqueurs(texte):
    """Numéros des marqueurs qui ont une fermeture {/n} dans le texte (les autres sont des balises vides)."""
    return {int(m.group(2)) for m in _JETON.finditer(texte) if m.group(1)}


def _jetons_marqueurs(texte):
    """Marqueurs du texte dans l'ordre : [« {1} », « {/1} », …]."""
    return [m.group(0) for m in _JETON.finditer(texte)]


def _marqueurs_conformes(trad, fr):
    """Vrai si la traduction a exactement les marqueurs du texte français, chaque ouverture avant sa fermeture."""
    jetons = _jetons_marqueurs(trad)
    if sorted(jetons) != sorted(_jetons_marqueurs(fr)) or len(set(jetons)) != len(jetons):
        return False
    return all(jetons.index("{%d}" % n) < jetons.index("{/%d}" % n) for n in _paires_marqueurs(fr))


def _coupures(texte):
    """Bornes des morceaux possibles d'un texte normalisé : [(fin du morceau précédent, début du suivant)], de (0, 0)
    à (len, len). On ne coupe que hors de toute paire de marqueurs ouverte : sur une espace, ou contre un marqueur."""
    paires = _paires_marqueurs(texte)
    marques = {m.start(): m for m in _JETON.finditer(texte)}
    fins = {m.end() for m in marques.values()}
    bornes, prof, i = [(0, 0)], 0, 0
    while i < len(texte):
        if prof == 0 and i > 0:
            if texte[i] == " ":
                bornes.append((i, i + 1))
            elif (i in marques or i in fins) and texte[i - 1] != " ":
                bornes.append((i, i))
        m = marques.get(i)
        if m:
            if int(m.group(2)) in paires:
                prof += -1 if m.group(1) else 1
            i = m.end()
        else:
            i += 1
    return bornes + [(len(texte), len(texte))]


def _canonique(morceau, paires):
    """(morceau renuméroté depuis 1 dans l'ordre d'apparition, {numéro canonique: numéro d'origine}), ou None si le
    morceau coupe une paire de marqueurs."""
    ordre, ouverts, vus = {}, set(), set()
    for m in _JETON.finditer(morceau):
        n = int(m.group(2))
        if m.group(1):
            if n not in ouverts:
                return None
            ouverts.discard(n)
        else:
            ordre.setdefault(n, len(ordre) + 1)
            if n in paires:
                if n in vus:
                    return None
                ouverts.add(n)
                vus.add(n)
    if ouverts:
        return None
    texte = _JETON.sub(lambda m: "{%s%d}" % (m.group(1), ordre[int(m.group(2))]), morceau)
    return texte, {c: n for n, c in ordre.items()}


def _recompositions(texte, index):
    """Recompositions du texte V2 : {page V1: (traduction, toutes les parties ont une traduction par défaut)}, pour
    chaque page V1 dont deux textes ou plus, dans l'ordre de la page, forment le texte (séparés par une espace ou
    accolés contre un marqueur), marqueurs renumérotés. Une partie peut être une variante de balisage sûre d'un texte
    V1 (_variante_sure : blancs seulement), sa traduction est alors recalée (Ruling 20). Une page dont une partie n'a
    pas de traduction valable, ou dont la traduction composée perd un marqueur, est écartée."""
    paires, bornes = _paires_marqueurs(texte), _coupures(texte)
    n = len(bornes)
    memo = {}

    def morceau(k, m):
        """(texte V1, {numéro canonique: numéro d'origine}, morceau canonique) ou None."""
        if (k, m) not in memo:
            brut = texte[bornes[k][1]:bornes[m][0]]
            c = _canonique(brut, paires) if 0 < len(brut) <= index["long_max"] else None
            memo[(k, m)] = None
            if c and c[0] in index["rangs"]:
                memo[(k, m)] = (c[0], c[1], c[0])
            elif c:
                v1 = [x for x in index["variantes"].get(_sans_blancs(c[0]), ()) if _variante_sure(x, c[0])]
                memo[(k, m)] = (v1[0], c[1], c[0]) if v1 else None
        return memo[(k, m)]

    # pages possibles, sans l'ordre : un morceau (un), deux ou plus (plus)
    un, plus = [set() for _ in range(n)], [set() for _ in range(n)]
    for m in range(1, n):
        c = morceau(0, m)
        if c:
            un[m] = set(index["rangs"][c[0]])
        for k in range(1, m):
            avant = un[k] | plus[k]
            if avant:
                c = morceau(k, m)
                if c:
                    plus[m] |= avant & index["rangs"][c[0]].keys()
    sortie = {}
    for page in sorted(plus[n - 1]):
        chemin = _dans_l_ordre(page, n, morceau, index)
        if chemin is None:
            continue
        parties, defaut = [], True
        for k, m in chemin:
            v1, origine, canon = morceau(k, m)
            trad, a_defaut = index["trad"][(v1, page)]
            defaut &= a_defaut
            trad = trad if v1 == canon else _recaler(v1, canon, trad)
            try:
                trad = _JETON.sub(lambda j: "{%s%d}" % (j.group(1), origine[int(j.group(2))]), trad)
            except (KeyError, TypeError):
                break
            parties.append((texte[bornes[k][0]:bornes[k][1]] if k else "") + trad)
        else:
            trad = "".join(parties)
            if _marqueurs_conformes(trad, texte):
                sortie[page] = (trad, defaut)
    return sortie


def _dans_l_ordre(page, n, morceau, index):
    """Découpage [(borne, borne)] en deux morceaux ou plus, textes de la page V1 pris dans l'ordre de la page (rangs
    croissants), ou None. Programmation dynamique sur les bornes : rang le plus petit atteint avec un morceau, puis
    avec deux ou plus (le plus petit rang laisse le plus de choix pour la suite)."""
    def suivant(c, apres):
        rangs = index["rangs"][c[0]].get(page, [])
        i = bisect.bisect_right(rangs, apres)
        return rangs[i] if i < len(rangs) else None

    un, plus = [None] * n, [None] * n  # (rang, précédent) ; précédent = (borne, état)
    for m in range(1, n):
        c = morceau(0, m)
        if c and suivant(c, -1) is not None:
            un[m] = (suivant(c, -1), None)
        for k in range(1, m):
            etats = [(e[0], s) for s, e in (("un", un[k]), ("plus", plus[k])) if e]
            if not etats:
                continue
            c = morceau(k, m)
            if not c:
                continue
            rang, etat = min(etats)
            r = suivant(c, rang)
            if r is not None and (plus[m] is None or r < plus[m][0]):
                plus[m] = (r, (k, etat))
    if plus[n - 1] is None:
        return None
    chemin, m, etat = [], n - 1, "plus"
    while m:
        rang, prec = (plus if etat == "plus" else un)[m]
        k, etat = prec if prec else (0, None)
        chemin.append((k, m))
        m = k
    return chemin[::-1]


def _variante_sure(fr_v1, fr_v2):
    """Vrai si le texte V2 ne diffère du texte V1 que par les blancs : mêmes marqueurs dans le même ordre, mêmes mots
    entre deux marqueurs (aux blancs près). Condition de Ruling 20 pour recaler une traduction V1."""
    if _jetons_marqueurs(fr_v1) != _jetons_marqueurs(fr_v2):
        return False
    return [_normal(x) for x in _JETON.split(fr_v1)[::3]] == [_normal(x) for x in _JETON.split(fr_v2)[::3]]


def _recaler(fr_v1, fr_v2, trad):
    """Traduction V1 recalée sur le balisage V2, ou None si le recalage n'est pas sûr. Sûr : mêmes marqueurs dans le
    même ordre, et mêmes mots entre deux marqueurs (aux blancs près) ; seuls les blancs contre un marqueur diffèrent,
    et ils sont reportés dans la traduction (blanc retiré ou ajouté du même côté du même marqueur)."""
    if not (_variante_sure(fr_v1, fr_v2) and _marqueurs_conformes(trad, fr_v1)):
        return None
    ta, tb = _JETON.split(fr_v1)[::3], _JETON.split(fr_v2)[::3]
    jetons = _jetons_marqueurs(fr_v1)
    # blanc avant et après chaque marqueur, en V1 et en V2
    avant = {j: (ta[i][-1:].isspace(), tb[i][-1:].isspace()) for i, j in enumerate(jetons)}
    apres = {j: (ta[i + 1][:1].isspace(), tb[i + 1][:1].isspace()) for i, j in enumerate(jetons)}
    morceaux, marqueurs = _JETON.split(trad)[::3], _jetons_marqueurs(trad)
    for i, texte in enumerate(morceaux):
        gauche, droite = (marqueurs[i - 1] if i else None), (marqueurs[i] if i < len(marqueurs) else None)
        if gauche:
            a, b = apres[gauche]
            texte = texte.lstrip() if a and not b else (" " + texte if b and not a and texte[:1] != " " and
                                                        (texte or droite) else texte)
        if droite:
            a, b = avant[droite]
            texte = texte.rstrip() if a and not b else (texte + " " if b and not a and texte[-1:] != " " and
                                                        (texte or gauche) else texte)
        morceaux[i] = texte
    sortie = "".join(m + (marqueurs[i] if i < len(marqueurs) else "") for i, m in enumerate(morceaux))
    return sortie if _marqueurs_conformes(sortie, fr_v2) else None


def _sans_englobant(texte):
    """Texte sans le marqueur {1}…{/1} qui l'entoure tout entier, renuméroté depuis 1 ; None s'il n'en a pas."""
    m = re.fullmatch(r"\{1\}(.*)\{/1\}", texte)
    if not m or "{1}" in m.group(1) or "{/1}" in m.group(1):
        return None
    c = _canonique(m.group(1), _paires_marqueurs(texte))
    return c[0] if c else None


def _decaler(texte, pas):
    """Marqueurs renumérotés de pas (+1 : place libérée pour un marqueur englobant {1})."""
    return _JETON.sub(lambda m: "{%s%d}" % (m.group(1), int(m.group(2)) + pas), texte)


def _recaler_englobant(fr_v1, fr_v2, trad):
    """Ruling 23 : traduction V1 recalée quand la V2 ne diffère de la V1 que par un marqueur englobant (autour du texte
    entier) ajouté ou retiré, le texte intérieur et les autres marqueurs identiques et dans le même ordre ; None sinon.
    Ajout : la traduction entière est entourée du marqueur {1} (les siens décalés de 1). Retrait : la traduction V1
    doit elle-même être entourée de ce marqueur, qui est retiré."""
    if not _marqueurs_conformes(trad, fr_v1):
        return None
    if _sans_englobant(fr_v2) == fr_v1:
        sortie = "{1}" + _decaler(trad, 1) + "{/1}"
    elif _sans_englobant(fr_v1) == fr_v2:
        # la traduction doit garder le marqueur {1} autour de tout ; ses marqueurs intérieurs (dans l'ordre de la
        # traduction, qui peut différer du français) perdent 1
        m = re.fullmatch(r"\{1\}(.*)\{/1\}", trad.strip(), re.S)
        sortie = _decaler(m.group(1), -1) if m and "{/1}" not in m.group(1) else None
    else:
        return None
    return sortie if sortie is not None and _marqueurs_conformes(sortie, fr_v2) else None


def _corrections():
    """[(page V2 ou None pour tout le site, ancien, nouveau)] : corrections V2 des phrases de la V1. Entrées
    contenus-v2 « remplace » (renommages, sur tout le site ; autres entrées, sur leur page) et « insere_avant »
    (pseudonymisation), passages retirés par outils/post/sans_agents.py."""
    from outils import contenus
    from outils.post import sans_agents
    sortie = []
    for e in contenus.toutes():
        page = None if e["cle"].startswith("renommage.") else e.get("page")
        if "remplace" in e:
            sortie.append((page, e["remplace"], e["texte"]))
        elif "insere_avant" in e:
            sortie.append((page, e["insere_avant"], f"{e['texte']} {e['insere_avant']}"))
    return sortie + [(sans_agents.PAGE, passage, "") for passage in sans_agents.RETIRES]


def _index_corrections(index, corrections):
    """{texte plat corrigé: [(texte V1, page V1)]} : textes V1 auxquels une correction V2 s'applique, tels que la V2
    les affiche après correction."""
    plates = [(p, _plat(H.unescape(a)), _plat(H.unescape(b))) for p, a, b in corrections]
    sortie = {}
    for (texte, page) in index["trad"]:
        avant = _plat(texte)
        apres = avant
        for p, a, b in plates:
            if a and (p is None or p == page) and a in apres:
                apres = " ".join(apres.replace(a, b).split())
        if apres and apres != avant:
            sortie.setdefault(apres, []).append((texte, page))
    return sortie


def _contexte(nature, texte_v1, page, trad, index):
    """Contexte V1 d'un texte à traduire : texte V1 complet et sa traduction sur la page V1 (trad, ou celle de
    l'index si trad est None)."""
    return {"nature": nature, "page_v1": index["adresses"][page], "fr_complet": texte_v1,
            "trad_complete": trad if trad is not None else index["trad"][(texte_v1, page)][0]}


def _preferer(candidats, pages_v2):
    """Candidat [(texte V1, page V1)] d'une page V2 du texte d'abord, puis le premier dans l'ordre."""
    return min(candidats, key=lambda c: (c[1] not in pages_v2, c[1], c[0]))


def _morceau(texte, pages_v2, index, par_page_v1):
    """(texte V1, page V1) le plus court qui contient le texte (mots entiers, au moins MOTS_MORCEAU mots), sur une
    page V2 du texte d'abord, ailleurs ensuite ; None sinon."""
    plat = _plat(texte)
    if len(plat.split()) < MOTS_MORCEAU:
        return None
    motif = re.compile(r"(?<!\w)" + re.escape(plat) + r"(?!\w)")

    def chercher(textes):
        trouves = [(len(p), t) for t, p in textes if plat in p and p != plat and motif.search(p)]
        return min(trouves)[1] if trouves else None
    for page in pages_v2:
        t = chercher(par_page_v1.get(page, ()))
        if t:
            return t, page
    t = chercher(par_page_v1["*"])
    return (t, min(index["rangs"][t])) if t else None


def recomposer(langue, neuron, table, pages=None, corrections=None):
    """Complète la table de la langue après la mémoire V1 (prefill) : blocs recomposés et variantes de balisage au
    statut adapte, contextes V1 des textes qui restent à traduire. Renvoie :
    {"recomposes", "variantes_recalees", "variantes_refusees", "morceaux", "corrections" (textes),
     "refus": {cause: textes}, "contextes": {clé: {"fr", "contexte": {nature, page_v1, fr_complet, trad_complete}}}}.

    - Recomposition : un texte V2 égal à la suite ordonnée de deux textes V1 ou plus d'une même page V1 (séparés par
      une espace, ou accolés contre un marqueur ; marqueurs renumérotés) reçoit la suite de leurs traductions, source
      « recomposition V1 <adresse> ». Un texte qui est lui-même un texte de la V1 (refusé par l'alignement) n'est
      jamais recomposé de ses parties.
    - Variante de balisage : un texte V2 dont les mots sont ceux d'un texte V1 traduit, au balisage près, reçoit la
      traduction V1 recalée sur ses marqueurs, source « variante de balisage V1 <adresse> » : blancs seulement
      (_recaler, Ruling 20), ou marqueur englobant ajouté ou retiré (_recaler_englobant, Ruling 23, source suivie de
      « (marqueur englobant) ») ; sinon, aucune traduction et la traduction V1 en contexte.
    - Rulings 19 et 21 : une traduction par défaut n'est posée que si toutes les parties ont une traduction par défaut
      et que toutes les pages V1 donnent le même résultat ; sinon, seulement pour les pages V2 qui ont la leur. Une
      traduction identique au français (hors invariant) n'est jamais posée : adapte, elle serait refusée par
      l'exhaustivité.
    - Contextes, pour les textes qui restent à traduire : correction V2 (renommages, sans_agents, pseudonymisation,
      entrées « remplace » : l'ancienne phrase V1 et sa traduction), variante refusée, recomposition non posée sur la
      page, morceau (texte contenu dans un texte V1 plus long).

    pages : pages FR assemblées de la V2 ({page: html}), par défaut traduire.pages_assemblees. corrections : liste
    [(page ou None, ancien, nouveau)], par défaut _corrections(). Les traductions d'une recomposition précédente sont
    d'abord retirées. La table n'est pas écrite sur disque."""
    if pages is None:
        pages = T.pages_assemblees(langue, "apercu")
    if corrections is None:
        corrections = _corrections()
    _retirer_recompositions(table)
    index = _index_v1(langue, neuron, table)
    manquants = _manquants_v2(langue, table, pages)
    refus, a_contexte = {}, {}  # a_contexte : {texte: {nature: contexte}}, choisi à la fin par ordre de priorité

    def identique(texte, trad):
        return _normal(trad) == texte and not T._invariant(texte, langue)

    def poser(texte, resultats, defaut, source_defaut):
        """resultats : {page V2: (traduction, source)} ; defaut : traduction par défaut ou None (alors, seulement
        pour les pages V2 de resultats : Rulings 19 et 21). Retire du texte les pages V2 servies."""
        if defaut is not None:
            table.poser(texte, defaut, ADAPTE, source_defaut)
        for page, (trad, source) in resultats.items():
            if trad != defaut:
                table.poser(texte, trad, ADAPTE, source, page=page, sans_defaut=True)
        reste = [] if defaut is not None else [p for p in manquants[texte] if p not in resultats]
        if reste:
            manquants[texte] = reste
        else:
            del manquants[texte]

    def recaler(c, texte, trad, source):
        """(traduction recalée, source) : blancs seulement (Ruling 20), ou marqueur englobant (Ruling 23) ; None."""
        r = _recaler(c, texte, trad)
        if r:
            return r, SOURCE_VARIANTE + source
        r = _recaler_englobant(c, texte, trad)
        return (r, SOURCE_VARIANTE + source + " (marqueur englobant)") if r else None

    # 1. variantes de balisage (Rulings 20 et 23) : texte entier
    recalees, variantes_vues = set(), set()
    for texte, pages_v2 in list(manquants.items()):
        candidats = [c for c in index["variantes"].get(_sans_blancs(texte), ()) if c != texte]
        if not candidats or texte in index["tous"]:
            continue
        variantes_vues.add(texte)
        resultats, defauts = {}, set()
        for c in candidats:
            e = table.entrees.get(cle(c))
            if e and e["trad"] is not None and e["statut"] in VALIDES:
                r = recaler(c, texte, e["trad"], e["source"])
                if r and not identique(texte, r[0]):
                    defauts.add(r)
            for page in pages_v2:
                # traduction propre à une page : seulement d'une page V1 où le texte figure (Ruling 21) ; ailleurs,
                # la traduction par défaut, si elle est unique
                trouve = table.chercher(c, page) if page in index["rangs"][c] else None
                if page not in resultats and trouve and trouve["statut"] in VALIDES:
                    r = recaler(c, texte, trouve["trad"], trouve["source"])
                    if r and not identique(texte, r[0]):
                        resultats[page] = r
        (defaut, source), = defauts if len(defauts) == 1 else ((None, None),)
        c = min(candidats, key=lambda x: (not any(p in index["rangs"][x] for p in pages_v2), x))
        a_contexte.setdefault(texte, {})["variante de balisage"] = (c, _preferer([(c, p) for p in index["rangs"][c]],
                                                                                    pages_v2)[1], None)
        if defaut is not None or resultats:
            recalees.add(texte)
            poser(texte, {p: r for p, r in resultats.items() if r[0] != defaut}, defaut, source)

    # 2. blocs recomposés
    recomposes = set()
    for texte, pages_v2 in list(manquants.items()):
        if texte in index["tous"]:
            continue
        par_page_v1 = {p: (t, d) for p, (t, d) in _recompositions(texte, index).items() if not identique(texte, t)}
        if not par_page_v1:
            continue
        page_defaut = min(par_page_v1)
        a_contexte.setdefault(texte, {})["recomposition"] = (texte, page_defaut, par_page_v1[page_defaut][0])
        trads = {t for t, _ in par_page_v1.values()}
        defaut = par_page_v1[page_defaut][0] if len(trads) == 1 and all(d for _, d in par_page_v1.values()) else None
        resultats = {p: (par_page_v1[p][0], SOURCE_RECOMPOSITION + index["adresses"][p])
                     for p in pages_v2 if p in par_page_v1}
        if defaut is None and not resultats:
            refus["recomposition divergente ou partielle, sans page V1 du texte"] = refus.get(
                "recomposition divergente ou partielle, sans page V1 du texte", 0) + 1
            continue
        recomposes.add(texte)
        poser(texte, resultats, defaut, SOURCE_RECOMPOSITION + index["adresses"][page_defaut])

    # 3. contextes des textes qui restent à traduire, par priorité : correction V2, variante refusée, recomposition non
    # posée sur la page, morceau
    corriges = _index_corrections(index, corrections)
    plats_par_page = {"*": []}
    vus = set()
    for (texte, page) in index["trad"]:
        plats_par_page.setdefault(page, []).append((texte, _plat(texte)))
        if texte not in vus:
            vus.add(texte)
            plats_par_page["*"].append((texte, _plat(texte)))
    contextes, natures = {}, {}
    for texte, pages_v2 in manquants.items():
        choix = None
        if _plat(texte) in corriges:
            choix = ("correction V2", *_preferer(corriges[_plat(texte)], pages_v2), None)
        elif texte in a_contexte:
            nature = next(n for n in ("variante de balisage", "recomposition") if n in a_contexte[texte])
            choix = (nature, *a_contexte[texte][nature])
        else:
            trouve = _morceau(texte, pages_v2, index, plats_par_page)
            choix = ("morceau", *trouve, None) if trouve else None
        if choix:
            contextes[cle(texte)] = {"fr": texte, "contexte": _contexte(*choix, index)}
            natures[choix[0]] = natures.get(choix[0], 0) + 1
    refusees = variantes_vues - recalees - recomposes
    if refusees:
        refus["variante : recalage non sûr (marqueurs différents) ou identique au français"] = len(refusees)
    return {"recomposes": len(recomposes), "variantes_recalees": len(recalees), "variantes_refusees": len(refusees),
            "morceaux": natures.get("morceau", 0), "corrections": natures.get("correction V2", 0),
            "contextes_par_nature": dict(sorted(natures.items())), "refus": dict(sorted(refus.items())),
            "contextes": dict(sorted(contextes.items()))}
