"""Terminologie vérifiée dans CHnell : adresses, file d'attente, journal et glossaire (tâches 4.2 et 4.3).

Fabien fait vérifier chaque terme du lexique (terminologie.py, tâche 4.1) dans CHnell avant toute traduction nouvelle. Ce
module prépare la session et garde ses résultats ; il n'ouvre ni Corrext ni CHnell et ne fait aucune requête réseau.

url_chnell(terme, langue, fedlex) rend l'adresse de recherche CHnell d'un terme (fedlex : concordances de Fedlex seules).
file_attente(langue, lexique, journal, priorite_max) rend les termes retenus du lexique, jusqu'à la priorité donnée, qui
n'ont pas encore de ligne de journal pour cette langue, avec leurs deux adresses.

Le journal (journal.jsonl) a une ligne JSON par terme et par langue vérifiés, ajoutée par ajouter() :

    {"date": "2026-10-26", "fr": "capital-actions", "langue": "de", "url": "https://corrext.com/chnell/search?...",
     "resultats": 12, "sources": ["Fedlex : CO art. 620"], "retenu": "Aktienkapital", "statut": "confirme",
     "justification": "même équivalent dans les concordances Fedlex", "verifie_par": "agent"}

statut : confirme (CHnell donne l'équivalent retenu), corrige (CHnell donne un autre équivalent que celui du site ou de la
table, hors V1), absent (terme introuvable : retenu vaut null) ou a_arbitrer (équivalents à égalité, ou divergence avec la
V1 : la décision revient à Fabien). Le journal ne garde aucun extrait de texte : champs exacts, valeurs courtes, jamais
de tiret long ; un terme revérifié s'ajoute une nouvelle ligne, la dernière l'emporte.

construire_glossaire(journal, termes_v1) rend {fr: {langue: {"terme", "source", "statut"}}} avec les seules entrées confirme
et corrige. Toute divergence avec la V1 (décision V5) devient un arbitrage et sort du glossaire, sauf si la ligne est de
Fabien (verifie_par « Fabien » : arbitrage tranché). arbitrages() les liste pour la remise à Fabien.

Ruling 5 (décision V6) : journal.jsonl et glossaire.json vivent dans le dossier de la terminologie (hors dépôt, voir
terminologie.TERMINOLOGIE), jamais dans le dépôt public.

ZONE (sélecteur CSS de la zone de résultats) et lire_resultats() restent à faire : ils dépendent de la structure réelle de
la page CHnell, relevée avec Fabien à la première session (tâche 4.2, step 1). Aucune structure n'est inventée d'ici là.

Bibliothèque standard seulement."""
import json
import re
from datetime import date
from pathlib import Path
from urllib.parse import quote

from outils.i18n import controles, terminologie
from outils.i18n.table import LANGUES

URL = "https://corrext.com/chnell/search"
ZONE = None  # sélecteur CSS de la zone de résultats : à relever dans CHnell avec Fabien (tâche 4.2, step 1)
MESSAGE_CAPTURE = "capture CHnell à faire avec Fabien (tâche 4.2 step 1)"
PRIORITE_MAX = 3  # décision V5 : les trois priorités sont vérifiées

JOURNAL = "journal.jsonl"
GLOSSAIRE = "glossaire.json"
STATUTS = ("confirme", "corrige", "absent", "a_arbitrer")
STATUTS_GLOSSAIRE = ("confirme", "corrige")
CHAMPS = ("date", "fr", "langue", "url", "resultats", "sources", "retenu", "statut", "justification", "verifie_par")
# Garde-fou contre un extrait de CHnell collé par erreur : ces champs restent des mots ou des phrases courtes
LONGUEUR_MAX = {"fr": 120, "retenu": 120, "justification": 300, "verifie_par": 60}
LONGUEUR_SOURCE_MAX = 120
SOURCE_PAR_DEFAUT = "CHnell"
ARBITRE_PAR = "fabien"
VERIFICATEURS = ("agent", "Fabien")  # verifie_par : liste fermée (vague finale, point 14)
DATE = re.compile(r"^\d{4}-\d{2}-\d{2}$")


def url_chnell(terme, langue, fedlex=False):
    """Adresse de recherche CHnell d'un terme français vers la langue (fedlex : sources Fedlex seulement)."""
    if langue not in LANGUES:
        raise ValueError(f"langue inconnue : « {langue} » (attendu : {', '.join(LANGUES)})")
    return (f"{URL}?searchText={quote(terme)}&sourceLang=fr&targetLang={langue}&resource=1"
            + ("&sources=60" if fedlex else ""))


def _normal(texte):
    return " ".join(str(texte).split())


def file_attente(langue, lexique, journal, priorite_max):
    """Termes retenus du lexique (retenu : true), de priorité au plus priorite_max, sans ligne de journal pour cette langue :
    [{fr, langue, url, url_fedlex, priorite}], par priorité puis terme français."""
    faits = {_normal(e["fr"]) for e in journal if e.get("langue") == langue}
    restants = [e for e in lexique
                if e.get("retenu") is True and e["priorite"] <= priorite_max and _normal(e["fr"]) not in faits]
    return [{"fr": e["fr"], "langue": langue, "url": url_chnell(e["fr"], langue),
             "url_fedlex": url_chnell(e["fr"], langue, fedlex=True), "priorite": e["priorite"]}
            for e in sorted(restants, key=lambda e: (e["priorite"], e["fr"]))]


def lire_resultats(html):
    """Équivalents lus dans la page de résultats de CHnell : [{source, reference, extrait_fr, extrait_cible}]. À faire avec
    la structure réelle de la page (ZONE) ; ValueError prévu si la zone manque (page de connexion, erreur)."""
    raise NotImplementedError(MESSAGE_CAPTURE)


# ---------- journal ----------

def fichier_journal(dossier=None):
    return Path(dossier or terminologie.TERMINOLOGIE) / JOURNAL


def _texte_court(champ, valeur, maxi):
    if not isinstance(valeur, str) or not valeur.strip():
        raise ValueError(f"{champ} : texte non vide attendu")
    if len(valeur) > maxi:
        raise ValueError(f"{champ} : {len(valeur)} caractères, {maxi} au plus (le journal ne garde aucun extrait de texte)")


def _valider(entree):
    """ValueError (message en français) si l'entrée ne respecte pas le schéma du journal."""
    if not isinstance(entree, dict):
        raise ValueError("entrée du journal : objet attendu")
    manquants, en_trop = [c for c in CHAMPS if c not in entree], sorted(set(entree) - set(CHAMPS))
    if manquants or en_trop:
        raise ValueError("champs du journal : " + "; ".join(
            ([f"manquant(s) : {', '.join(manquants)}"] if manquants else [])
            + ([f"en trop (aucun extrait de texte) : {', '.join(en_trop)}"] if en_trop else [])))
    try:  # fromisoformat accepte aussi « 20261026 » ou « 2026-W43-1 » : la forme est d'abord imposée
        if not (isinstance(entree["date"], str) and DATE.fullmatch(entree["date"])):
            raise ValueError
        date.fromisoformat(entree["date"])
    except (TypeError, ValueError):
        raise ValueError(f"date : AAAA-MM-JJ attendu, reçu « {entree['date']} »") from None
    if entree["verifie_par"] not in VERIFICATEURS:
        raise ValueError(f"verifie_par : « {entree['verifie_par']} » inconnu (attendu : {', '.join(VERIFICATEURS)})")
    for champ in ("fr", "justification", "verifie_par"):
        _texte_court(champ, entree[champ], LONGUEUR_MAX[champ])
    langue = entree["langue"]
    if langue not in LANGUES:
        raise ValueError(f"langue : « {langue} » inconnue (attendu : {', '.join(LANGUES)})")
    if entree["statut"] not in STATUTS:
        raise ValueError(f"statut : « {entree['statut']} » inconnu (attendu : {', '.join(STATUTS)})")
    if not isinstance(entree["url"], str) or not entree["url"].startswith(URL + "?") \
            or f"targetLang={langue}&" not in entree["url"]:
        raise ValueError(f"url : adresse CHnell vers « {langue} » attendue (url_chnell)")
    n = entree["resultats"]
    if isinstance(n, bool) or not isinstance(n, int) or n < 0:
        raise ValueError("resultats : nombre entier positif ou nul attendu")
    if not isinstance(entree["sources"], list):
        raise ValueError("sources : liste attendue")
    for s in entree["sources"]:
        _texte_court("source", s, LONGUEUR_SOURCE_MAX)
    retenu = entree["retenu"]
    if retenu is None:
        if entree["statut"] in STATUTS_GLOSSAIRE:
            raise ValueError(f"retenu : l'équivalent est obligatoire pour le statut « {entree['statut']} »")
    else:
        _texte_court("retenu", retenu, LONGUEUR_MAX["retenu"])
        if entree["statut"] == "absent":
            raise ValueError("retenu : null attendu pour le statut « absent »")
    problemes = []
    for champ in ("fr", "retenu", "justification", "verifie_par"):
        problemes += controles.tirets(entree[champ] or "")
    for s in entree["sources"]:
        problemes += controles.tirets(s)
    if langue == "de" and retenu:
        problemes += controles.eszett(entree["fr"], retenu)
    if problemes:
        raise ValueError("; ".join(f"{p['regle']} : {p['detail']} ({p['extrait']})" for p in problemes))


def ajouter(journal, entree):
    """Ajoute une ligne JSON au journal (fichier journal.jsonl, créé avec son dossier au besoin) après validation du schéma :
    ValueError, sans rien écrire, si l'entrée est invalide."""
    _valider(entree)
    journal = Path(journal)
    journal.parent.mkdir(parents=True, exist_ok=True)
    with journal.open("a", encoding="utf-8") as f:
        f.write(json.dumps(entree, ensure_ascii=False) + "\n")


def charger_journal(dossier=None):
    """Lignes du journal du dossier de la terminologie ([] s'il n'existe pas encore)."""
    f = fichier_journal(dossier)
    if not f.is_file():
        return []
    entrees = []
    for i, texte in enumerate(f.read_text(encoding="utf-8").splitlines(), 1):
        if not texte.strip():
            continue
        try:
            entrees.append(json.loads(texte))
        except ValueError as e:
            raise ValueError(f"{f} : ligne {i} illisible ({e})") from None
    return entrees


# ---------- glossaire ----------

def _dernieres(journal):
    """Dernière ligne de chaque couple (terme français, langue) : un terme revérifié remplace l'avis précédent."""
    return {(_normal(e["fr"]), e["langue"]): e for e in journal}


def _equivalents_v1(termes_v1, langue, fr):
    """Équivalents du terme dans les termes V1 de la langue (termes-<langue>.json), sans doublon."""
    vus = []
    for t in termes_v1.get(langue, []):
        eq = t.get(langue)
        if isinstance(eq, str) and _normal(t["fr"]).casefold() == _normal(fr).casefold() and _normal(eq) not in vus:
            vus.append(_normal(eq))
    return vus


def _diverge_de_v1(e, v1):
    """Vrai si la ligne confirme ou corrige un équivalent absent des termes V1 du même terme, sans l'aval de Fabien."""
    return (e["statut"] in STATUTS_GLOSSAIRE and bool(v1) and e["verifie_par"].casefold() != ARBITRE_PAR
            and _normal(e["retenu"]).casefold() not in {v.casefold() for v in v1})


def arbitrages(journal, termes_v1):
    """Arbitrages à remettre à Fabien : lignes a_arbitrer du journal et divergences avec la V1 (dernière ligne de chaque
    terme), [{fr, langue, retenu, v1, justification, sources, raison}], par langue puis terme français.
    termes_v1 : {langue: contenu de termes-<langue>.json}."""
    sortie = []
    for (fr, langue), e in sorted(_dernieres(journal).items(), key=lambda kv: (kv[0][1], kv[0][0])):
        v1 = _equivalents_v1(termes_v1, langue, e["fr"])
        if e["statut"] == "a_arbitrer":
            raison = "à arbitrer dans la session CHnell"
        elif _diverge_de_v1(e, v1):
            raison = "diverge de la V1 (décision V5)"
        else:
            continue
        sortie.append({"fr": e["fr"], "langue": langue, "retenu": e["retenu"], "v1": v1,
                       "justification": e["justification"], "sources": e["sources"], "raison": raison})
    return sortie


def construire_glossaire(journal, termes_v1):
    """Glossaire de projet : {fr: {langue: {"terme", "source", "statut"}}} d'après la dernière ligne de chaque terme et
    langue du journal. Seules les lignes confirme et corrige y entrent, hors divergence avec la V1 (arbitrage, voir
    arbitrages). source : les sources du journal réunies, « CHnell » si la ligne n'en a pas.
    termes_v1 : {langue: contenu de termes-<langue>.json}."""
    glossaire = {}
    for (fr, langue), e in _dernieres(journal).items():
        if e["statut"] not in STATUTS_GLOSSAIRE or _diverge_de_v1(e, _equivalents_v1(termes_v1, langue, e["fr"])):
            continue
        glossaire.setdefault(e["fr"], {})[langue] = {"terme": e["retenu"], "statut": e["statut"],
                                                     "source": " ; ".join(e["sources"]) or SOURCE_PAR_DEFAUT}
    return {fr: {l: glossaire[fr][l] for l in sorted(glossaire[fr])} for fr in sorted(glossaire)}


def _fichier_glossaire(dossier):
    return Path(dossier or terminologie.TERMINOLOGIE) / GLOSSAIRE


def charger_glossaire(dossier=None):
    """Glossaire du dossier de la terminologie ({} s'il n'existe pas encore)."""
    f = _fichier_glossaire(dossier)
    return json.loads(f.read_text(encoding="utf-8")) if f.is_file() else {}


def ecrire_glossaire(glossaire, langue, dossier=None):
    """Remplace dans glossaire.json les entrées de la langue par celles de glossaire (construire_glossaire) ; les autres
    langues sont gardées. Rend le chemin du fichier. Le dossier est créé au besoin."""
    f = _fichier_glossaire(dossier)
    complet = charger_glossaire(dossier)
    for fr in list(complet):
        complet[fr].pop(langue, None)
        if not complet[fr]:
            del complet[fr]
    for fr, langues in glossaire.items():
        if langue in langues:
            complet.setdefault(fr, {})[langue] = langues[langue]
    f.parent.mkdir(parents=True, exist_ok=True)
    f.write_text(json.dumps({fr: {l: complet[fr][l] for l in sorted(complet[fr])} for fr in sorted(complet)},
                            indent=1, ensure_ascii=False) + "\n", encoding="utf-8")
    return f
