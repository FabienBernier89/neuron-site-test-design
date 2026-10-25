"""Tâche 3.2 : ce que l'alignement strict de la mémoire V1 (memoire_v1.py) ne pose pas.

Blocs recomposés et variantes de balisage, au statut adapte (accepté en aperçu seulement, avec le bandeau ; relu
ensuite), jamais v1 : un texte posé ici n'est pas identique à un texte validé. Pour les textes qui restent à traduire,
un contexte V1 pour l'adaptation (contextes.json, repris dans a_traduire.json par traduire.fichier_a_traduire) :
correction V2, variante refusée, recomposition non posée, morceau d'un texte V1 plus long. Point d'entrée : recomposer,
appelé par la commande « python3 -m outils.i18n memoire <langue> » après memoire_v1.prefill.

Bibliothèque standard seulement."""
import bisect
import functools
import html as H
import json
import re
from pathlib import Path

from outils.i18n import segments as S
from outils.i18n import traduire as T
from outils.i18n.memoire_v1 import _MARQUEURS, _normal
from outils.i18n.table import cle

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


def retirer_recompositions(table):
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
    retirer_recompositions(table)
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
        # défaut unique : une seule traduction recalée, quelle que soit la page V1 qui la donne (source : la première)
        defaut, source = None, None
        if len({r for r, _ in defauts}) == 1:
            defaut, source = min(defauts, key=lambda d: d[1])
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
