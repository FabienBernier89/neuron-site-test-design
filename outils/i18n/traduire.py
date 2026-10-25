"""Traduction d'une page française assemblée par le build (passe 2) et état de la traduction d'une langue.

traduire découpe la page en segments (segments.extraire_page), remplace chaque segment par sa traduction de la table
de la langue (Table), réinjecte (segments.reinjecter_page) et vérifie le résultat. Une page n'est publiable dans une
langue que si elle est entièrement et correctement traduite ; sinon traduire rend "" et la liste des manquants
{cle, fr, statut, raison}, raison étant :
- « absent » : le texte français n'est pas dans la table (texte nouveau, ou modifié après la traduction) ;
- « statut » : sa traduction a un statut refusé dans ce mode (Table.ACCEPTES : mt partout, adapte en production) ;
- « balisage » : la traduction perd, double ou inverse un marqueur {n}…{/n} des balises en ligne ;
- « exhaustivite » : la page traduite, ré-extraite, garde un texte français de la page d'origine sans que ce soit
  voulu (condition de Fabien : ne jamais oublier un texte à traduire ; décision V2, Ruling 3) ;
- « scripts » : un script de la page écrit du texte français que l'extraction ne voit pas (Ruling 13, tâche 7.3).

Restent en français, sans être manquants : les unités sous un lang="fr" explicite (Ruling 14), les invariants
(Table.est_invariant), et une traduction de statut invariant ou v1 identique au français. Hors français, les avis
fictifs des pages métier sont retirés avant l'extraction (décision V8, Ruling 4). En aperçu, une page qui contient une
traduction non relue (statut adapte) reçoit le bandeau « Version de travail, traduction non relue » (décision V4,
Ruling 2), traduit par la table ; jamais en production.

Commande : python3 -m outils.i18n etat de [--production] (outils/i18n/__main__.py).

Bibliothèque standard seulement."""
import html as H
import re
import shutil
import tempfile
from pathlib import Path

from outils.i18n import controles
from outils.i18n import segments as S
from outils.i18n.table import ACCEPTES, Table, cle

MODES = ("apercu", "production")
RELUS = {"v1", "invariant", "relu"}  # statuts qui ne demandent pas le bandeau de l'aperçu
IDENTIQUES = {"invariant", "v1"}      # statuts d'une traduction identique au français admise par l'exhaustivité
LIBELLE_BANDEAU = "Version de travail, traduction non relue"
CONTEXTES = "contextes.json"  # contextes V1 des textes à traduire, par langue (recomposition.recomposer, commande memoire)
BANDEAU = '<div class="bandeau-travail" role="note">{}</div>\n'
# Pages dont les scripts inline n'écrivent que des libellés anglais de l'application (inventaire de la tâche 2.1,
# tests/test_i18n_segments.py, SCRIPTS_CONNUS) : elles ne sont pas bloquées par la raison « scripts »
SCRIPTS_ANGLAIS = {"corrext/extraits-registre-commerce/"}
# Avis fictifs des pages métier (outils/composer/metier_modele.py, avis) : la section qui les porte, ou l'avis seul
_SECTION_AVIS = re.compile(r'<section class="sec mt-avis">(?:(?!</section>).)*?\bdata-avis-fictif\b.*?</section>\n?', re.S)
_AVIS = re.compile(r"<figure\b[^>]*\bdata-avis-fictif\b[^>]*>.*?</figure>", re.S)
_MOT = re.compile(r"[^\W\d_]+")
_MARQUEUR = re.compile(r"\{/?\d+\}")


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


def analyser(html, page, langue, table, mode):
    """Traduction détaillée d'une page : {"html": page traduite ou "", "manquants": [...], "statuts": {clé: statut}}.
    statuts : statut de chaque texte français de la page (celui de la table, « invariant » pour un invariant sans
    entrée, « absent » sinon) ; les unités lang="fr" n'y figurent pas."""
    if mode not in MODES:
        raise ValueError(f"mode inconnu : « {mode} » (attendu : {', '.join(MODES)})")
    html = retirer_avis_fictifs(html)
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
        utilises.add(entree["statut"])
    if S.scripts_a_traduire(html) and page not in SCRIPTS_ANGLAIS:
        manquants.append({"cle": None, "fr": "texte écrit par un script de la page (tâche 7.3)", "statut": None,
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
            traduit = traduit.replace("<body>\n", "<body>\n" + BANDEAU.format(H.escape(texte, quote=False)), 1)
    return {"html": "" if manquants else traduit, "manquants": manquants, "statuts": statuts}


def traduire(html, page, langue, table, mode):
    """Page française assemblée -> (page traduite, manquants). La page traduite n'est rendue que si rien ne manque,
    sinon "". page : clé de la page dans build.PAGES (« contact/ »), « 404 » pour la page 404 ; c'est aussi la clé de
    par_page dans la table. mode : « apercu » ou « production »."""
    r = analyser(html, page, langue, table, mode)
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


def etat_detaille(langue, mode):
    """État de la traduction d'une langue sur tout le site, tel que le build le verrait : (etat, a_traduire), etat
    ayant la forme de etat() et a_traduire étant {clé: texte FR} de tous les manquants. Pages : pages_assemblees."""
    import build  # import tardif : build importe ce module
    assemblees = pages_assemblees(langue, mode)
    table = Table(langue, build.DOSSIER_LANGUES)
    pages, statuts, a_traduire = {}, {}, {}
    for page, html in assemblees.items():
        r = analyser(html, page, langue, table, mode)
        pages[page] = _resume(r["manquants"])
        statuts.update(r["statuts"])
        a_traduire.update((m["cle"], m["fr"]) for m in r["manquants"] if m["cle"])
    manquants_llms = verifier_libelles(table, mode)
    pages["llms"] = _resume(manquants_llms)
    a_traduire.update((m["cle"], m["fr"]) for m in manquants_llms)
    compte = {}
    for s in statuts.values():
        compte[s] = compte.get(s, 0) + 1
    etat = {"pages": pages, "segments": dict(sorted(compte.items())),
            "mots_a_traduire": sum(mots(t) for t in a_traduire.values())}
    return etat, a_traduire


def etat(langue, mode):
    """{"pages": {page: {"publiable", "manquants", "mots"}}, "segments": {statut: nombre de textes}, "mots_a_traduire"}.
    pages : chaque page de build.PAGES, plus « 404 » et « llms » (libellés fixes des llms.txt) ; mots : mots français
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
