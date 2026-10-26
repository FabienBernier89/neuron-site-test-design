"""Traduction d'une page française assemblée par le build (passe 2) et état de la traduction d'une langue.

traduire découpe la page en segments (segments.extraire_page), remplace chaque segment par sa traduction de la table
de la langue (Table), réinjecte (segments.reinjecter_page) et vérifie le résultat. Une page n'est publiable dans une
langue que si elle est entièrement et correctement traduite ; sinon traduire rend "" et la liste des manquants
{cle, fr, statut, raison}, raison étant :
- « absent » : le texte français n'est pas dans la table (texte nouveau, ou modifié après la traduction) ;
- « statut » : sa traduction a un statut refusé dans ce mode (Table.ACCEPTES : mt partout, adapte en production) ;
- « balisage » : la traduction perd, double ou inverse un marqueur {n}…{/n} des balises en ligne ;
- « variables » : la traduction d'un gabarit des démos (« Segment {n} confirmé. ») perd, ajoute ou renomme une variable
  nommée (controles.variables, tâche 7.3) ;
- « exhaustivite » : la page traduite, ré-extraite, garde un texte français de la page d'origine sans que ce soit
  voulu (condition de Fabien : ne jamais oublier un texte à traduire ; décision V2, Ruling 3) ;
- « scripts » : un script de la page écrit du texte français que l'extraction ne voit pas (Ruling 13 ; depuis la tâche
  7.3, les démos lisent leurs textes dans un bloc JSON extrait : aucune page du site n'est concernée) ;
- « exemples » : l'exemple de loi d'une page du glossaire ne se remplace pas de façon certaine par celui de la V1 (italien
  et anglais, tâche 3.3, exemples_glossaire.py) ; la page est alors non publiable, sans autre manquant relevé.

Restent en français, sans être manquants : les unités sous un lang="fr" explicite (Ruling 14 : sources françaises des
démos, français de l'exemple de loi du glossaire, balisé par outils/post/y_accessibilite.py), les invariants
(Table.est_invariant), et une traduction de statut invariant ou v1 identique au français. Sur les pages de termes du
glossaire, l'exemple de loi italien et anglais est celui de la page V1 (statut v1 de fait, texte validé le 2026-10-05) :
il est posé avant l'extraction, avec son lang, et n'est jamais traduit ni compté. Hors français, les avis
fictifs des pages métier sont retirés avant l'extraction (décision V8, Ruling 4). En aperçu, une page qui contient une
traduction non relue (statut adapte) reçoit le bandeau « Version de travail, traduction non relue » (décision V4,
Ruling 2), traduit par la table ; jamais en production.

Pages françaises de la chaîne (pages_union) : les commandes qui listent, envoient, exportent ou réimportent les textes
(etat, pont, exporter, importer, lexique, memoire) partent de l'union des pages assemblées en aperçu et en production : le
bandeau de consentement des cookies n'existe qu'en production, la note « Formulaire de démonstration » qu'en aperçu. Le
libellé du bandeau de l'aperçu (LIBELLE_BANDEAU) est un texte à traduire comme les autres, listé dès le premier tour
(pseudo-page « bandeau »), pour ne pas demander un second passage du pont.

Commande : python3 -m outils.i18n etat de [--production] (outils/i18n/__main__.py).

Bibliothèque standard seulement."""
import html as H
import re
import shutil
import tempfile
from pathlib import Path

from outils.i18n import controles, exemples_glossaire
from outils.i18n import segments as S
from outils.i18n.table import ACCEPTES, Table, cle

MODES = ("apercu", "production")
RELUS = {"v1", "invariant", "relu"}  # statuts qui ne demandent pas le bandeau de l'aperçu
IDENTIQUES = {"invariant", "v1"}      # statuts d'une traduction identique au français admise par l'exhaustivité
LIBELLE_BANDEAU = "Version de travail, traduction non relue"
PAGE_BANDEAU = "bandeau"  # pseudo-page du libellé du bandeau (etat, export, pont), comme « llms » pour les llms.txt
CONTEXTES = "contextes.json"  # contextes V1 des textes à traduire, par langue (recomposition.recomposer, commande memoire)
BANDEAU = '<div class="bandeau-travail" role="note">{}</div>\n'
# Avis fictifs des pages métier (outils/composer/metier_modele.py, avis) : la section qui les porte, ou l'avis seul
_SECTION_AVIS = re.compile(r'<section class="sec mt-avis">(?:(?!</section>).)*?\bdata-avis-fictif\b.*?</section>\n?', re.S)
_AVIS = re.compile(r"<figure\b[^>]*\bdata-avis-fictif\b[^>]*>.*?</figure>", re.S)
_MOT = re.compile(r"[^\W\d_]+")
_MARQUEUR = re.compile(r"\{/?\d+\}")
_BODY = re.compile(r"<body\b[^>]*>\n?")


def _normal(texte):
    return " ".join(texte.split())


def mots(texte):
    """Nombre de mots d'un texte français (marqueurs ignorés)."""
    return len(_MOT.findall(_MARQUEUR.sub(" ", texte)))


def retirer_avis_fictifs(html):
    """Page sans les avis fictifs (décision V8) : la section .mt-avis entière, sinon l'avis seul."""
    return _AVIS.sub("", _SECTION_AVIS.sub("", html))


def _invariant(texte, langue):
    """Vrai si le texte reste tel quel sans entrée de table : Table.est_invariant, sauf un nombre dont les milliers sont
    séparés par une espace en allemand ou en italien (15 000 doit devenir 15'000)."""
    return Table.est_invariant(texte) and not controles.milliers(texte, langue)


def _manquant(texte, statut, raison):
    return {"cle": cle(texte), "fr": _normal(texte), "statut": statut, "raison": raison}


def libelle(table, texte_fr, mode, page=None):
    """Traduction d'un libellé fixe (bandeau, libellés des llms.txt) : (traduction, None) ou (None, manquant). Une
    traduction identique au français doit avoir un statut invariant ou v1, comme pour l'exhaustivité d'une page."""
    entree = table.chercher(texte_fr, page)
    if entree is None:
        return None, _manquant(texte_fr, None, "absent")
    if entree["statut"] not in ACCEPTES[mode]:
        return None, _manquant(texte_fr, entree["statut"], "statut")
    if _normal(entree["trad"]) == _normal(texte_fr) and entree["statut"] not in IDENTIQUES:
        return None, _manquant(texte_fr, entree["statut"], "exhaustivite")
    return entree["trad"], None


def _neuron():
    """Dossier du site V1 (lecture seule), tel que le build le lit."""
    import build  # import tardif : build importe ce module
    return build.NEURON


def analyser(html, page, langue, table, mode, neuron=None):
    """Traduction détaillée d'une page : {"html": page traduite ou "", "manquants": [...], "statuts": {clé: statut}}.
    statuts : statut de chaque texte français de la page (celui de la table, « invariant » pour un invariant sans
    entrée, « absent » sinon) ; les unités lang="fr" n'y figurent pas. neuron : dossier du site V1 (lecture seule), lu
    pour l'exemple de loi des pages du glossaire en italien et en anglais ; build.NEURON si absent."""
    if mode not in MODES:
        raise ValueError(f"mode inconnu : « {mode} » (attendu : {', '.join(MODES)})")
    html = retirer_avis_fictifs(html)
    try:
        if exemples_glossaire.concerne(page, langue):
            html = exemples_glossaire.exemples(html, page, langue, neuron or _neuron())
    except ValueError as e:
        return {"html": "", "manquants": [{"cle": None, "fr": str(e), "statut": None, "raison": "exemples"}], "statuts": {}}
    unites = S.extraire_page(html)
    manquants, vus, statuts, traductions, utilises = [], set(), {}, {}, set()

    def signaler(m):
        if (m["cle"], m["raison"]) not in vus:
            vus.add((m["cle"], m["raison"]))
            manquants.append(m)

    for u in unites:
        if u["lang_fr"]:
            continue
        texte = u["texte"]
        entree = table.chercher(texte, page)
        if entree is None:
            if _invariant(texte, langue):
                statuts[cle(texte)] = "invariant"
                utilises.add("invariant")
            else:
                statuts[cle(texte)] = "absent"
                signaler(_manquant(texte, None, "absent"))
            continue
        statuts[cle(texte)] = entree["statut"]
        if entree["statut"] not in ACCEPTES[mode]:
            signaler(_manquant(texte, entree["statut"], "statut"))
            continue
        try:
            traductions[u["id"]] = S.restaurer_unite(entree["trad"], u)
        except ValueError:
            signaler(_manquant(texte, entree["statut"], "balisage"))
            continue
        if controles.variables(texte, entree["trad"]):
            traductions.pop(u["id"])
            signaler(_manquant(texte, entree["statut"], "variables"))
            continue
        utilises.add(entree["statut"])
    ecrits = S.textes_des_scripts(html)
    if ecrits:
        manquants.append({"cle": None, "fr": f"texte écrit par un script de la page : « {_normal(ecrits[0])[:60]} »"
                          + (f" et {len(ecrits) - 1} autre(s)" if len(ecrits) > 1 else ""), "statut": None,
                          "raison": "scripts"})
    traduit = S.reinjecter_page(html, traductions)
    # exhaustivité : aucun texte français de la page d'origine ne doit rester tel quel dans la page traduite
    francais = {_normal(u["texte"]) for u in unites if not u["lang_fr"]}
    deja = {m["cle"] for m in manquants}
    for r in S.extraire_page(traduit):
        texte = r["texte"]
        if r["lang_fr"] or _normal(texte) not in francais or cle(texte) in deja or _invariant(texte, langue):
            continue
        entree = table.chercher(texte, page)
        if entree and entree["statut"] in IDENTIQUES and _normal(entree["trad"]) == _normal(texte):
            continue
        signaler(_manquant(texte, entree["statut"] if entree else None, "exhaustivite"))
    if not manquants and mode == "apercu" and utilises - RELUS:
        texte, m = libelle(table, LIBELLE_BANDEAU, mode, page)
        if m:
            signaler(m)
        else:
            traduit = _poser_bandeau(traduit, texte)
    return {"html": "" if manquants else traduit, "manquants": manquants, "statuts": statuts}


def _poser_bandeau(html, texte):
    """Bandeau de l'aperçu juste après l'ouverture de <body> (attributs permis) ; ValueError si <body> est introuvable :
    une page traduite non relue ne se publie jamais sans son bandeau."""
    m = _BODY.search(html)
    if m is None:
        raise ValueError("bandeau de l'aperçu : balise <body> introuvable dans la page traduite")
    ouverture = m.group(0) if m.group(0).endswith("\n") else m.group(0) + "\n"
    return html[:m.start()] + ouverture + BANDEAU.format(H.escape(texte, quote=False)) + html[m.end():]


def traduire(html, page, langue, table, mode, neuron=None):
    """Page française assemblée -> (page traduite, manquants). La page traduite n'est rendue que si rien ne manque,
    sinon "". page : clé de la page dans build.PAGES (« contact/ »), « 404 » pour la page 404 ; c'est aussi la clé de
    par_page dans la table. mode : « apercu » ou « production ». neuron : dossier du site V1 (voir analyser)."""
    r = analyser(html, page, langue, table, mode, neuron)
    return r["html"], r["manquants"]


# ---------- état d'une langue ----------

def _resume(manquants):
    distincts = {m["cle"]: m["fr"] for m in manquants if m["cle"]}
    return {"publiable": not manquants, "manquants": len(manquants), "mots": sum(mots(t) for t in distincts.values())}


def pages_assemblees(langue, mode):
    """Pages françaises assemblées telles que TRADUIRE les reçoit dans le build ({page: html}, 404 comprise sous la clé
    « 404 ») : assemblées comme par build.py (langues fr et `langue`, mode demandé) dans un dossier temporaire ; rien
    n'est écrit dans docs/."""
    import build  # import tardif : build importe ce module
    if mode not in MODES:
        raise ValueError(f"mode inconnu : « {mode} » (attendu : {', '.join(MODES)})")
    docs, config = build.DOCS, build.CONFIG
    tmp = Path(tempfile.mkdtemp(prefix="neuron-etat-"))
    try:
        build.DOCS = tmp / "docs"
        build.DOCS.mkdir()
        langues = ["fr"] + [l for l in config.get("langues", []) if l not in ("fr", langue)] + [langue]
        build.CONFIG = {**config, "apercu": mode == "apercu", "langues": langues}
        _, assemblees, nav, pied, v = build.assembler_pages()
        assemblees["404"] = build.page_404_a_traduire(build.assembler_404_fr(nav, pied, v))
    finally:
        build.DOCS, build.CONFIG = docs, config
        shutil.rmtree(tmp, ignore_errors=True)
    return assemblees


def pages_union(langue):
    """Pages françaises assemblées des deux modes, pour la chaîne de traduction (etat, pont, exporter, importer, lexique,
    memoire) : {page: {"apercu": html, "production": html}}, 404 comprise sous la clé « 404 ». Une page n'existe que
    dans un mode : elle n'a que celui-là. Le bandeau de consentement (production seulement) et la note des formulaires de
    démonstration (aperçu seulement) sont ainsi listés, exportés et réimportés comme le reste ; sans cela, une langue
    entièrement relue resterait bloquée en production. Rien n'est écrit dans docs/."""
    union = {}
    for mode in MODES:
        for page, html in pages_assemblees(langue, mode).items():
            union.setdefault(page, {})[mode] = html
    return union


def variantes(valeur):
    """Variantes distinctes d'une page de pages_union ({mode: html}), dans l'ordre des modes ; une chaîne seule (pages
    assemblées d'un seul mode) en est l'unique variante."""
    if not isinstance(valeur, dict):
        return [valeur]
    sortie = []
    for m in MODES:
        if m in valeur and valeur[m] not in sortie:
            sortie.append(valeur[m])
    return sortie


def page_du_mode(valeur, mode):
    """Page assemblée dans le mode donné (valeur de pages_union, ou chaîne seule) ; à défaut, la première variante."""
    if isinstance(valeur, dict):
        return valeur.get(mode) or variantes(valeur)[0]
    return valeur


def manquants_bandeau(table, mode):
    """Manquants du libellé du bandeau de l'aperçu : seul l'aperçu l'affiche, la production ne le demande jamais."""
    if mode != "apercu":
        return []
    return [m for m in (libelle(table, LIBELLE_BANDEAU, mode)[1],) if m]


def etat_detaille(langue, mode):
    """État de la traduction d'une langue sur tout le site : (etat, a_traduire), etat ayant la forme de etat() et
    a_traduire étant {clé: texte FR} de tous les manquants. Pages : pages_union ; chaque page est jugée publiable sur sa
    version du mode demandé, telle que le build la verrait, mais a_traduire et les comptes par statut réunissent les
    textes des deux modes (le bandeau de consentement de la production est listé dès l'aperçu). En aperçu, le libellé du
    bandeau de travail a sa ligne (« bandeau »)."""
    import build  # import tardif : build importe ce module
    assemblees = pages_union(langue)
    table = Table(langue, build.DOSSIER_LANGUES)
    pages, statuts, a_traduire = {}, {}, {}
    for page, valeur in assemblees.items():
        propre = page_du_mode(valeur, mode)
        for html in variantes(valeur):
            r = analyser(html, page, langue, table, mode)
            if html == propre:
                pages[page] = _resume(r["manquants"])
            statuts.update(r["statuts"])
            a_traduire.update((m["cle"], m["fr"]) for m in r["manquants"] if m["cle"])
    fixes = [("llms", verifier_libelles(table, mode))] + ([(PAGE_BANDEAU, manquants_bandeau(table, mode))]
                                                          if mode == "apercu" else [])
    for nom, manquants in fixes:
        pages[nom] = _resume(manquants)
        a_traduire.update((m["cle"], m["fr"]) for m in manquants)
    compte = {}
    for s in statuts.values():
        compte[s] = compte.get(s, 0) + 1
    etat = {"pages": pages, "segments": dict(sorted(compte.items())),
            "mots_a_traduire": sum(mots(t) for t in a_traduire.values())}
    return etat, a_traduire


def etat(langue, mode):
    """{"pages": {page: {"publiable", "manquants", "mots"}}, "segments": {statut: nombre de textes}, "mots_a_traduire"}.
    pages : chaque page de build.PAGES, plus « 404 », « llms » (libellés fixes des llms.txt) et, en aperçu, « bandeau »
    (libellé du bandeau de travail) ; mots : mots français
    des textes manquants. segments : textes français distincts du site par statut (« absent » : sans entrée)."""
    return etat_detaille(langue, mode)[0]


def fichier_a_traduire(a_traduire, contextes):
    """Contenu de src/langues/<langue>/a_traduire.json : {clé: {"fr": texte FR, "contexte": {...}}}, « contexte »
    seulement quand la mémoire V1 en a un (recomposition.recomposer, fichier contextes.json : morceau d'un texte V1 plus
    long, correction V2, variante de balisage refusée, recomposition non posée) : {nature, page_v1, fr_complet,
    trad_complete}, pour l'adaptation. a_traduire : {clé: texte FR} (etat_detaille) ; contextes : {clé: {"fr",
    "contexte"}}."""
    sortie = {}
    for k in sorted(a_traduire):
        sortie[k] = {"fr": a_traduire[k]}
        if k in contextes:
            sortie[k]["contexte"] = contextes[k]["contexte"]
    return sortie


def verifier_libelles(table, mode):
    """Manquants des libellés fixes des llms.txt d'une langue (outils/llms.py, libelles_fixes)."""
    from outils import llms
    return [m for m in (libelle(table, t, mode)[1] for t in llms.libelles_fixes()) if m]
