"""Échanges avec les traducteurs experts (tâches 5.1 et 5.2) : export de la table d'une langue en XLIFF 1.2 (Trados Studio),
en TMX 1.4 et en glossaire CSV, puis réimport des corrections. Les traducteurs relisent tout avant la production.

Export XLIFF (exporter_xliff) : un <file> (original « neur-on.ai/<langue> », source fr-CH, cible HREFLANG de la langue,
datatype html), un <trans-unit> par texte français de la table, dans l'ordre des pages du site. L'identifiant est la clé
du texte (table.cle) ; une traduction propre à une page (par_page) a sa propre unité, « <clé>@<page> » (« accueil »
pour la page d'accueil). Les marqueurs des balises en ligne deviennent des éléments XLIFF : {n}…{/n} en <g id="n">…</g>,
{n} seul en <x id="n"/>. La <note> de chaque unité dit les pages (huit au plus, puis « et N autre(s) »), le statut, les
termes du glossaire de projet présents dans le texte et le contexte V1 (contextes.json et a_traduire.json). Les segments
v1 et invariant sont marqués approved="yes" et state="final" (décision V2 : visibles et corrigeables, sans nouvelle relecture) ;
mt et adapte portent state="needs-review-translation", relu state="signed-off". Un caractère interdit en XML 1.0 (contrôles C0
hors tabulation, saut de ligne et retour chariot) fait refuser l'export. La source
des traductions (« V1 de/kontakt/ », nom du moteur) n'est jamais écrite : l'export part chez un tiers. Les textes sont ceux
des pages assemblées dans les deux modes (traduire.pages_union : le bandeau de consentement n'existe qu'en production) ; le
libellé du bandeau de l'aperçu a sa pseudo-page « bandeau », exportée avec toute sélection de pages.

Export TMX 1.4 (exporter_tmx) : les traductions des statuts demandés (les segments v1 approuvés, décision V12), source
fr-CH, marqueurs en <bpt>/<ept>/<ph>. Glossaire CSV (exporter_glossaire_csv) : fr;<langue>;source;statut, UTF-8 avec BOM,
séparateur point-virgule (ouverture directe dans Excel).

Réimport (importer_xliff, importer_csv) : chaque unité rendue est contrôlée avant d'entrer dans la table. Un segment est
rejeté, avec sa raison, et garde sa traduction et son statut précédents, si : « segment inconnu » (clé absente de la table),
« segment plus présent sur le site » (le texte FR a changé sur le site depuis l'export, sa clé avec lui : la traduction
rendue devient le contexte du nouveau texte quand il est identifiable), « segment FR modifié depuis l'export » (source
retouchée dans le fichier), « traduction vide », « balisage » (marqueur supprimé, ajouté, en double, inversé ou
élément XLIFF inconnu : segments.restaurer), « tirets », « eszett », « marques », « interdits », « variables » (variable
nommée d'un gabarit des démos perdue, ajoutée ou renommée : « Segment {n} confirmé. » ; contrôles bloquants de controles.py)
ou « doublon ». Une traduction v1, invariant ou à champ « v1 » (table.py) rendue sans modification n'est pas
soumise aux contrôles bloquants (Ruling 30), comme dans controler (4.4) ; la terminologie n'avertit que (avertissements,
jamais un rejet). Ruling 31 : l'import ne pose relu que sur une confirmation positive du relecteur, state translated, final ou
signed-off, ou approved="yes" dans le fichier rendu (un CSV est une confirmation en soi) ; sinon le segment est laissé tel
quel et listé « non confirmé par le relecteur » (option sans_etat : tout segment valide vaut confirmation, pour un outil qui
n'écrirait pas les états). Un segment accepté passe au statut relu, avec « ; relu par <relecteur> le <date> » ajouté à sa source ; une traduction identique au
français passe au statut invariant (Ruling 18), source « relu par <relecteur> le <date>, identique au français » ; une
traduction v1 qui passe relu sans changement garde le champ « v1 ». Un fichier
écrit pour une autre langue est refusé en entier (ValueError). L'import ne modifie que la table en mémoire : enregistrer()
reste à l'appelant.

Fusion des adaptations (fusionner, tâche 6.2) : propositions [{"cle", "trad", "note"}] d'un agent d'adaptation ou de relecture
croisée, posées au statut adapte dans la table. Mêmes contrôles que le réimport : clé inconnue, balisage faux (marqueurs),
« tirets », « eszett », « marques », « interdits », « variables » ; la terminologie n'avertit que. S'y ajoutent trois refus :
« déjà relu » (une entrée relue par un traducteur expert, ou portant le champ « v1 », n'est jamais réécrite), « déjà validé » (statut v1 ou
invariant : validé avant) et « format » (proposition mal formée). Une entrée au statut mt ou adapte, avec ou sans traduction
par défaut, est remplacée ; ses traductions par page restent. Les notes de l'agent remontent dans le rapport, jamais dans la
table (elles ne sortent pas dans les exports).

Les exports vont hors du dépôt public (verifier_hors_depot : un dossier du dépôt est refusé sauf s'il est ignoré par git),
par défaut dans ~/Claude project/Bibliotheque-Claude/07-Ressources-traduction/Neuron/site-v2/<date>-<langue>/.

Commandes : python3 -m outils.i18n exporter <langue> ..., importer <langue> <fichier> --relecteur <nom> et fusionner <langue>
<propositions.json> (outils/i18n/__main__.py). Bibliothèque standard seulement."""
import csv
import difflib
import json
import re
import subprocess
import unicodedata
from datetime import date
from pathlib import Path
from xml.etree import ElementTree as ET
from xml.sax.saxutils import escape

from outils.i18n import chnell, controles, terminologie, traduire
from outils.i18n import segments as S
from outils.i18n.langues import HREFLANG
from outils.i18n.table import LANGUES, cle

NS_XLIFF = "urn:oasis:names:tc:xliff:document:1.2"
XML_LANG = "{http://www.w3.org/XML/1998/namespace}lang"
SOURCE_LANGUE = HREFLANG["fr"]  # fr-CH
STATUTS_XLIFF_PAR_DEFAUT = ("mt", "adapte", "v1", "invariant")  # relu a déjà été relu par un expert
APPROUVES = ("v1", "invariant")  # marqués approved="yes" dans l'XLIFF (décision V2)
ETATS = {"mt": "needs-review-translation", "adapte": "needs-review-translation", "v1": "final", "invariant": "final",
         "relu": "signed-off"}  # état XLIFF 1.2 de la cible
ETATS_CONFIRMES = ("translated", "final", "signed-off")  # états d'une cible que le relecteur a confirmée (Ruling 31)
_XML_INTERDIT = re.compile("[\x00-\x08\x0b\x0c\x0e-\x1f\ufffe\uffff\ud800-\udfff]")  # hors XML 1.0
ACCUEIL = "accueil"  # la page d'accueil (clé de page « ») dans les notes et les identifiants
LLMS = "llms"        # pseudo-page des libellés fixes des fichiers llms.txt
BANDEAU = traduire.PAGE_BANDEAU  # pseudo-page du libellé du bandeau de l'aperçu (« Version de travail... »)
PSEUDO_PAGES = (LLMS, BANDEAU)
PAGES_VISIBLES = 8
COLONNES_CSV = ("cle", "fr", "trad")
PLUS_PRESENT = "segment plus présent sur le site"  # raison de rejet : la clé n'apparaît plus dans les pages assemblées
NATURE_RELECTURE = "relecture d'une version précédente"  # contexte posé pour la nouvelle clé d'un texte FR modifié
SEUIL_VOISIN = 0.6  # ressemblance minimale (difflib) entre l'ancien texte FR et le texte qui l'a remplacé sur sa page

_MARQ = re.compile(r"\{(/?)(\d+)\}")
_BLANCS = re.compile(r"[ \t\r\n\f]+")  # pas \s : l'espace insécable est une modification


def _normal(texte):
    return " ".join(texte.split())


def _blancs(texte):
    """Texte aux blancs ASCII regroupés : une espace insécable remplacée par une espace est une vraie modification."""
    return _BLANCS.sub(" ", texte).strip()


# ---------- destination des exports ----------

def dossier_export(langue, jour=None):
    """Dossier d'export par défaut : <dossier des échanges>/<date>-<langue>/, le dossier des échanges étant le parent de
    celui de la terminologie (Bibliotheque-Claude/07-Ressources-traduction/Neuron/site-v2/)."""
    return terminologie.TERMINOLOGIE.parent / f"{jour or date.today().isoformat()}-{langue}"


def verifier_hors_depot(chemin):
    """Refuse (ValueError) un chemin situé dans un dépôt git, sauf s'il est ignoré par ce dépôt : le dépôt de la V2 est
    public, aucun export pour traducteur ni aucune terminologie n'y entre. Un chemin hors de tout dépôt est accepté."""
    chemin = Path(chemin).expanduser().resolve()
    for dossier in (chemin, *chemin.parents):
        if not (dossier / ".git").exists():
            continue
        try:
            ignore = subprocess.run(["git", "-C", str(dossier), "check-ignore", "-q", "--", str(chemin)],
                                    capture_output=True).returncode == 0
        except OSError:
            ignore = False  # git absent : dans le doute, refuser
        if not ignore:
            raise ValueError(f"{chemin} est dans le dépôt {dossier} (public) ; choisir un dossier de "
                             f"Bibliotheque-Claude/07-Ressources-traduction/Neuron/site-v2/")
        return


def _ecrire(sortie, texte, encodage="utf-8"):
    sortie = Path(sortie)
    sortie.parent.mkdir(parents=True, exist_ok=True)
    sortie.write_text(texte, encoding=encodage, newline="")


def _controler_xml(ident, *textes):
    """ValueError clair si un texte contient un caractère interdit en XML 1.0 (le fichier serait illisible)."""
    for t in textes:
        m = _XML_INTERDIT.search(t)
        if m:
            raise ValueError(f"caractère interdit en XML 1.0 (U+{ord(m.group(0)):04X}) dans l'unité {ident} : "
                             f"« {t[max(0, m.start() - 20):m.end() + 20]!r} », à corriger dans la table avant l'export")


# ---------- marqueurs ----------

def _en_xliff(texte):
    """Texte à marqueurs -> contenu XLIFF : {n}…{/n} en <g id="n">…</g>, {n} seul en <x id="n"/>, texte échappé.
    ValueError si les marqueurs ne sont pas imbriqués (un <g> ne peut pas chevaucher un autre)."""
    fermants = {m.group(2) for m in _MARQ.finditer(texte) if m.group(1)}
    sortie, pile, pos = [], [], 0
    for m in _MARQ.finditer(texte):
        sortie.append(escape(texte[pos:m.start()]))
        pos = m.end()
        n = m.group(2)
        if m.group(1):
            if not pile or pile[-1] != n:
                raise ValueError(f"balisage mal imbriqué : {{/{n}}}")
            pile.pop()
            sortie.append("</g>")
        elif n in fermants:
            pile.append(n)
            sortie.append(f'<g id="{n}">')
        else:
            sortie.append(f'<x id="{n}"/>')
    sortie.append(escape(texte[pos:]))
    if pile:
        raise ValueError(f"balisage mal imbriqué : {{{pile[-1]}}} sans fermeture")
    return "".join(sortie)


def _en_tmx(texte):
    """Texte à marqueurs -> contenu TMX 1.4 : {n} ouvrant en <bpt i="n">, {/n} en <ept i="n">, {n} seul en <ph x="n">
    (le code natif est le marqueur lui-même)."""
    fermants = {m.group(2) for m in _MARQ.finditer(texte) if m.group(1)}
    sortie, pos = [], 0
    for m in _MARQ.finditer(texte):
        sortie.append(escape(texte[pos:m.start()]))
        pos = m.end()
        n, brut = m.group(2), escape(m.group(0))
        if m.group(1):
            sortie.append(f'<ept i="{n}">{brut}</ept>')
        elif n in fermants:
            sortie.append(f'<bpt i="{n}">{brut}</bpt>')
        else:
            sortie.append(f'<ph x="{n}">{brut}</ph>')
    sortie.append(escape(texte[pos:]))
    return "".join(sortie)


def _vers_marqueurs(element):
    """Contenu d'un <source> ou <target> XLIFF -> texte à marqueurs. <mrk> (segmentation des outils) est déplié ;
    tout autre élément que <g> et <x> est refusé (ValueError)."""
    morceaux = [element.text or ""]
    for enfant in element:
        nom = enfant.tag.rsplit("}", 1)[-1]
        n = (enfant.get("id") or "").strip()
        if nom in ("g", "x"):
            if not n.isdigit():
                raise ValueError(f"<{nom}> sans identifiant numérique")
            n = str(int(n))
            morceaux.append("{%s}" % n if nom == "x" else "{%s}%s{/%s}" % (n, _vers_marqueurs(enfant), n))
        elif nom == "mrk":
            morceaux.append(_vers_marqueurs(enfant))
        else:
            raise ValueError(f"élément <{nom}> non géré")
        morceaux.append(enfant.tail or "")
    return "".join(morceaux)


def _table_marqueurs(fr):
    """Table des marqueurs du texte français, au format de segments.restaurer : paires (ouvre, ferme) et marqueurs seuls
    (vide)."""
    fermants = {int(m.group(2)) for m in _MARQ.finditer(fr) if m.group(1)}
    return {n: ({"ouvre": "", "ferme": ""} if n in fermants else {"vide": ""})
            for n in sorted({int(m.group(2)) for m in _MARQ.finditer(fr)})}


# ---------- export ----------

def _glossaire_de(langue, glossaire):
    if glossaire is None:
        glossaire = chnell.charger_glossaire()
    return {fr: l for fr, l in glossaire.items() if langue in l}


def _contextes(table):
    """Contextes V1 des textes (clé -> contexte) : contextes.json (mémoire V1, tâche 3.2) puis a_traduire.json (contexte
    des textes encore à traduire), dans le dossier de la table."""
    sortie = {}
    for nom in (traduire.CONTEXTES, "a_traduire.json"):
        fichier = table.fichier.parent / nom
        if fichier.is_file():
            for k, e in json.loads(fichier.read_text(encoding="utf-8")).items():
                if e.get("contexte"):
                    sortie.setdefault(k, e["contexte"])
    return sortie


def _textes(pages, assemblees):
    """Textes français à traduire des pages choisies (None : tout le site), dans l'ordre du site : couples (page, texte).
    assemblees : {page: html} ou {page: {mode: html}} (traduire.pages_union : les textes des deux modes). Hors unités
    lang="fr" et avis fictifs ; les libellés fixes des llms.txt viennent ensuite sous la page « llms », puis le libellé du
    bandeau de l'aperçu sous la page « bandeau », toujours (toute page traduite non relue le porte en aperçu)."""
    from outils import llms
    for page, valeur in assemblees.items():
        if pages is not None and page not in pages:
            continue
        for html in traduire.variantes(valeur):
            for u in S.extraire_page(traduire.retirer_avis_fictifs(html)):
                if not u["lang_fr"]:
                    yield page, u["texte"]
    if pages is None or LLMS in pages:
        for texte in llms.libelles_fixes():
            yield LLMS, texte
    yield BANDEAU, traduire.LIBELLE_BANDEAU


def _unites(table, pages, statuts, assemblees):
    """Unités à exporter, dans l'ordre du site : [{"id", "cle", "page", "fr", "trad", "statut", "pages"}]. Une traduction
    propre à une page a son unité, la traduction par défaut la sienne pour les pages sans variante. Un texte hors de la
    sélection ou sans entrée dans la table n'en fait pas partie."""
    unites = {}
    for page, texte in _textes(pages, assemblees):
        k = cle(texte)
        entree = table.entrees.get(k)
        if entree is None:
            continue
        propre = entree["par_page"].get(page)
        if propre is not None:
            ident, version, variante = f"{k}@{page or ACCUEIL}", propre, page
        elif entree["trad"] is not None:
            ident, version, variante = k, entree, None
        else:
            continue
        if version["statut"] not in statuts or version["trad"] is None:
            continue
        u = unites.setdefault(ident, {"id": ident, "cle": k, "page": variante, "fr": entree["fr"],
                                      "trad": version["trad"], "statut": version["statut"], "pages": []})
        if page not in u["pages"]:
            u["pages"].append(page)
    return list(unites.values())


def sans_traduction(langue, table, pages, assemblees):
    """Textes des pages choisies (None : tout le site) sans aucune traduction pour la page (ni par défaut ni propre à la
    page) et qui ne sont pas des invariants : ils ne peuvent pas figurer dans l'export. Rend {clé: {"fr", "pages":
    {page: ...}}}, pages dans l'ordre du site, pour dire au relecteur ce qui reste à traduire d'abord."""
    manquants = {}
    for page, texte in _textes(pages, assemblees):
        if table.chercher(texte, page) is None and not traduire._invariant(texte, langue):
            m = manquants.setdefault(cle(texte), {"fr": " ".join(texte.split()), "pages": []})
            if page not in m["pages"]:
                m["pages"].append(page)
    return manquants


def _liste_pages(pages):
    noms = [p or ACCUEIL for p in pages]
    if len(noms) <= PAGES_VISIBLES:
        return ", ".join(noms)
    return ", ".join(noms[:PAGES_VISIBLES]) + f" et {len(noms) - PAGES_VISIBLES} autre(s)"


def _ligne_contexte(c):
    sans = lambda t: _MARQ.sub("", t or "")  # les marqueurs encombrent la lecture d'un contexte
    if c.get("nature") == NATURE_RELECTURE:
        return (f"Version précédente relue ({c.get('page_v1', '')}) : français d'alors : {sans(c.get('fr_complet'))} ; "
                f"traduction rendue par le relecteur : {sans(c.get('trad_complete'))}")
    return (f"Contexte V1 ({c.get('nature', '')}, {c.get('page_v1', '')}) : texte français complet : "
            f"{sans(c.get('fr_complet'))} ; traduction V1 complète : {sans(c.get('trad_complete'))}")


def _note(u, termes, contexte, avertissement):
    lignes = [f"Pages : {_liste_pages(u['pages'])}", f"Statut : {u['statut']}"]
    if termes:
        lignes.append("Glossaire : " + " ; ".join(f"{fr} = {eq}" for fr, eq in termes))
    if contexte:
        lignes.append(_ligne_contexte(contexte))
    if avertissement:
        lignes.append(avertissement)
    return "\n".join(lignes)


def exporter_xliff(langue, table, pages, statuts, sortie, assemblees=None, glossaire=None):
    """Écrit l'XLIFF 1.2 de la langue dans sortie (un fichier .xlf) : un <trans-unit> par texte dont le statut est dans
    statuts, restreint aux pages données (clés de page, « » pour l'accueil ; None : tout le site, libellés des llms.txt
    compris ; le libellé du bandeau de l'aperçu est toujours exporté). Rend le nombre d'unités. assemblees : {page: HTML
    français assemblé} ou {page: {mode: html}} (traduire.pages_union par défaut : textes des deux modes) ; glossaire :
    {fr: {langue: {terme, ...}}} (chnell.charger_glossaire par défaut). ValueError si la sortie est dans le dépôt ou si
    la langue n'est pas celle de la table."""
    if langue not in LANGUES or table.langue != langue:
        raise ValueError(f"langue « {langue} » : la table est celle de « {table.langue} »")
    verifier_hors_depot(sortie)
    if assemblees is None:
        assemblees = traduire.pages_union(langue)
    glossaire = _glossaire_de(langue, glossaire)
    contextes = _contextes(table)
    cible = HREFLANG[langue]
    unites = _unites(table, None if pages is None else set(pages), set(statuts), assemblees)
    morceaux = ['<?xml version="1.0" encoding="UTF-8"?>\n',
                f'<xliff version="1.2" xmlns="{NS_XLIFF}">\n',
                f'  <file original="neur-on.ai/{langue}" source-language="{SOURCE_LANGUE}" target-language="{cible}" '
                f'datatype="html">\n    <body>\n']
    for u in unites:
        termes = controles.termes_presents(u["fr"], langue, glossaire)
        _controler_xml(u["id"], u["fr"], u["trad"], *(eq for _, eq in termes), *[
            str(v) for v in (contextes.get(u["cle"]) or {}).values()])
        avertissement = ""
        try:
            en_cible = _en_xliff(u["trad"])
        except ValueError as e:
            en_cible = None
            avertissement = (f"Traduction actuelle non exportée ({e}), à reprendre : "
                             f"{_MARQ.sub('', u['trad'])}")
        attribut = ' approved="yes"' if u["statut"] in APPROUVES else ""
        ident = escape(u["id"], {'"': "&quot;"})
        morceaux.append(f'      <trans-unit id="{ident}"{attribut}>\n'
                        f'        <source xml:lang="{SOURCE_LANGUE}">{_en_xliff(u["fr"])}</source>\n')
        if en_cible is not None:
            morceaux.append(f'        <target xml:lang="{cible}" state="{ETATS[u["statut"]]}">{en_cible}</target>\n')
        morceaux.append(f'        <note>{escape(_note(u, termes, contextes.get(u["cle"]), avertissement))}</note>\n'
                        '      </trans-unit>\n')
    morceaux.append("    </body>\n  </file>\n</xliff>\n")
    _ecrire(sortie, "".join(morceaux))
    return len(unites)


def exporter_tmx(langue, table, statuts, sortie):
    """Écrit la mémoire de traduction TMX 1.4 des traductions dont le statut est dans statuts (par défaut des appelants :
    v1, les segments validés par les traducteurs), traductions par défaut et traductions de page. Rend le nombre
    d'unités de traduction."""
    if langue not in LANGUES or table.langue != langue:
        raise ValueError(f"langue « {langue} » : la table est celle de « {table.langue} »")
    verifier_hors_depot(sortie)
    cible = HREFLANG[langue]
    morceaux = ['<?xml version="1.0" encoding="UTF-8"?>\n<tmx version="1.4">\n',
                f'  <header creationtool="neur-on.ai" creationtoolversion="1.0" segtype="paragraph" o-tmf="neur-on-site-v2" '
                f'adminlang="{SOURCE_LANGUE}" srclang="{SOURCE_LANGUE}" datatype="html"/>\n  <body>\n']
    n = 0
    for k in sorted(table.entrees):
        e = table.entrees[k]
        versions = [(None, e)] + [(p, e["par_page"][p]) for p in sorted(e["par_page"])]
        for page, v in versions:
            if v.get("trad") is None or v.get("statut") not in statuts:
                continue
            ident = k if page is None else f"{k}@{page or ACCUEIL}"
            _controler_xml(ident, e["fr"], v["trad"])
            props = f'      <prop type="x-statut">{v["statut"]}</prop>\n'
            if page is not None:
                props += f'      <prop type="x-page">{escape(page or ACCUEIL)}</prop>\n'
            morceaux.append(f'    <tu tuid="{escape(ident, {chr(34): "&quot;"})}">\n{props}'
                            f'      <tuv xml:lang="{SOURCE_LANGUE}"><seg>{_en_tmx(e["fr"])}</seg></tuv>\n'
                            f'      <tuv xml:lang="{cible}"><seg>{_en_tmx(v["trad"])}</seg></tuv>\n    </tu>\n')
            n += 1
    morceaux.append("  </body>\n</tmx>\n")
    _ecrire(sortie, "".join(morceaux))
    return n


def exporter_glossaire_csv(langue, glossaire, sortie):
    """Écrit le glossaire de projet de la langue en CSV (fr;<langue>;source;statut, UTF-8 avec BOM, séparateur
    point-virgule). glossaire : {fr: {langue: {terme, source, statut}}} (chnell.charger_glossaire). Rend le nombre de
    termes."""
    verifier_hors_depot(sortie)
    sortie = Path(sortie)
    sortie.parent.mkdir(parents=True, exist_ok=True)
    lignes = [[fr, langues[langue]["terme"], langues[langue]["source"], langues[langue]["statut"]]
              for fr, langues in sorted(glossaire.items()) if langue in langues]
    with open(sortie, "w", encoding="utf-8-sig", newline="") as f:
        ecrivain = csv.writer(f, delimiter=";", lineterminator="\r\n")
        ecrivain.writerow(["fr", langue, "source", "statut"])
        ecrivain.writerows(lignes)
    return len(lignes)


# ---------- réimport ----------

def presents(assemblees):
    """Clés des textes du site par page, d'après les pages assemblées des deux modes (traduire.pages_union) et les
    pseudo-pages « llms » et « bandeau » : {page: {clé: texte FR}}."""
    sortie = {}
    for page, texte in _textes(None, assemblees):
        sortie.setdefault(page, {})[cle(texte)] = _normal(texte)
    return sortie


def _voisin(fr_avant, pages, sur_le_site, table):
    """Texte qui a remplacé fr_avant sur ses pages : parmi les textes de ces pages (toutes si elles sont inconnues) sans
    traduction dans la table, le seul plus proche de fr_avant (difflib, SEUIL_VOISIN au moins) ; None si aucun ou si
    deux textes sont aussi proches."""
    plat = lambda t: " ".join(_MARQ.sub(" ", t).split())
    candidats = {}
    for page in (pages or list(sur_le_site)):
        for texte in sur_le_site.get(page, {}).values():
            if table.chercher(texte, page) is None and not traduire._invariant(texte, table.langue):
                candidats[texte] = difflib.SequenceMatcher(None, plat(fr_avant), plat(texte)).ratio()
    meilleurs = sorted(candidats.items(), key=lambda kv: -kv[1])
    if not meilleurs or meilleurs[0][1] < SEUIL_VOISIN or (len(meilleurs) > 1 and meilleurs[1][1] == meilleurs[0][1]):
        return None
    return meilleurs[0][0]


def _decouper_id(ident):
    """Identifiant d'unité -> (clé du texte, page ou None) : « <clé> » ou « <clé>@<page> » (« accueil » pour la page « »)."""
    if "@" not in ident:
        return ident, None
    k, page = ident.split("@", 1)
    return k, "" if page == ACCUEIL else page


def _pages_de_la_note(unite):
    """Pages lues dans la note d'une unité (« Pages : a, b et 3 autre(s) ») : (noms de pages, nombre d'autres pages)."""
    for note in unite.iter(f"{{{NS_XLIFF}}}note"):
        m = re.search(r"^Pages : (.*)$", note.text or "", re.M)
        if m:
            texte = m.group(1).strip()
            autres = re.search(r" et (\d+) autre\(s\)$", texte)
            if autres:
                texte = texte[:autres.start()]
            return [p.strip() for p in texte.split(", ") if p.strip()], int(autres.group(1)) if autres else 0
    return [], 0


def _lire_xliff(fichier, langue):
    """Unités d'un XLIFF rendu : [{"id", "fr", "trad", "erreur", "confirme", "pages", "autres_pages"}] (confirme : approved="yes"
    ou état de la cible dans ETATS_CONFIRMES). ValueError si le fichier est
    illisible, n'est pas du XLIFF 1.2, ou n'est pas écrit pour cette langue."""
    try:
        racine = ET.parse(fichier).getroot()
    except (ET.ParseError, OSError) as e:
        raise ValueError(f"fichier XLIFF illisible : {e}") from e
    if racine.tag != f"{{{NS_XLIFF}}}xliff":
        raise ValueError("ce fichier n'est pas un XLIFF 1.2 (espace de noms attendu : " + NS_XLIFF + ")")
    unites, fichiers = [], list(racine.iter(f"{{{NS_XLIFF}}}file"))
    if not fichiers:
        raise ValueError("fichier XLIFF sans élément <file>")
    for f in fichiers:
        if f.get("target-language") != HREFLANG[langue] or f.get("source-language") != SOURCE_LANGUE:
            raise ValueError(f"le fichier est écrit de « {f.get('source-language')} » vers « {f.get('target-language')} » "
                             f"(target-language), pas de {SOURCE_LANGUE} vers « {HREFLANG[langue]} »")
        for tu in f.iter(f"{{{NS_XLIFF}}}trans-unit"):
            source, cible = tu.find(f"{{{NS_XLIFF}}}source"), tu.find(f"{{{NS_XLIFF}}}target")
            u = {"id": tu.get("id") or "", "fr": "", "trad": None, "erreur": None,
                 "confirme": tu.get("approved") == "yes" or (cible is not None and cible.get("state") in ETATS_CONFIRMES)}
            try:
                u["fr"] = _vers_marqueurs(source) if source is not None else ""
                u["trad"] = _vers_marqueurs(cible) if cible is not None else None
            except ValueError as e:
                u["erreur"] = str(e)
            u["pages"], u["autres_pages"] = _pages_de_la_note(tu)
            unites.append(u)
    return unites


def _lire_csv(fichier):
    """Lignes d'un CSV de corrections (colonnes cle;fr;trad, UTF-8 avec ou sans BOM) : mêmes unités que _lire_xliff."""
    try:
        with open(fichier, encoding="utf-8-sig", newline="") as f:
            lecteur = csv.DictReader(f, delimiter=";")
            champs = [(c or "").strip() for c in (lecteur.fieldnames or [])]
            if not set(COLONNES_CSV) <= set(champs):
                raise ValueError(f"colonnes attendues : {';'.join(COLONNES_CSV)} (trouvé : {';'.join(champs) or 'aucune'})")
            lecteur.fieldnames = champs
            lignes = list(lecteur)
    except (OSError, UnicodeDecodeError, csv.Error) as e:
        raise ValueError(f"fichier CSV illisible : {e}") from e
    unites = []
    for ligne in lignes:
        ident = (ligne["cle"] or "").strip()
        page = _decouper_id(ident)[1]
        unites.append({"id": ident, "fr": ligne["fr"] or "", "trad": ligne["trad"], "erreur": None, "confirme": True,
                       "pages": [] if page is None else [page or ACCUEIL], "autres_pages": 0})
    return unites


def _appliquer(unites, table, relecteur, glossaire, jour, sans_etat=False, assemblees=None, attendues=None):
    """Contrôle chaque unité rendue et pose les acceptées dans la table (en mémoire). Voir importer_xliff."""
    if not relecteur or not relecteur.strip():
        raise ValueError("le nom du relecteur est obligatoire")
    if controles.tirets(relecteur):
        raise ValueError("le nom du relecteur contient un tiret long")
    jour = jour or date.today().isoformat()
    glossaire = _glossaire_de(table.langue, glossaire)
    sur_le_site = presents(traduire.pages_union(table.langue) if assemblees is None else assemblees)
    toutes = set().union(*sur_le_site.values()) if sur_le_site else set()
    suite = f"relu par {relecteur.strip()} le {jour}"
    rapport = {"relus": 0, "invariants": 0, "mt_adapte_intacts": 0, "v1_intacts": 0, "modifies": [], "rejetes": [],
               "non_confirmes": [], "avertissements": [], "reorientes": [],
               "absents": None if attendues is None else [], "export_controle": attendues is not None}
    vus = set()
    for u in unites:
        ident = u["id"]
        k, page = _decouper_id(ident)
        entree = table.entrees.get(k)

        def rejeter(raison, detail=""):
            rapport["rejetes"].append({"cle": ident, "raison": raison, "detail": detail,
                                       "fr": _normal(entree["fr"]) if entree else _normal(u["fr"])})

        if ident in vus:
            rejeter("doublon", "unité présente plusieurs fois dans le fichier")
            continue
        vus.add(ident)
        if (entree is None or (page is not None and page not in entree["par_page"])
                or (page is None and entree["trad"] is None)):
            rejeter("segment inconnu", "aucun texte français de la table n'a cette clé")
            continue
        if k not in (toutes if page is None else sur_le_site.get(page, {})):
            # le texte français a changé sur le site depuis l'export (sa clé avec lui) : rien n'est posé ; la traduction
            # rendue sert de contexte au texte qui l'a remplacé, s'il est identifiable sur ses pages, sinon au rapport
            pages = [("" if p == ACCUEIL else p) for p in (u["pages"] or ([] if page is None else [page or ACCUEIL]))]
            nouveau = _voisin(entree["fr"], [p for p in pages if p in sur_le_site], sur_le_site, table)
            trad = u["trad"] if not u["erreur"] else None
            if nouveau is not None and trad and trad.strip():
                rapport["reorientes"].append({"cle": ident, "nouvelle_cle": cle(nouveau), "fr_avant": _normal(entree["fr"]),
                                              "fr": nouveau, "trad": trad, "pages": pages})
                rejeter(PLUS_PRESENT, f"remplacé sur le site par « {nouveau[:60]} » (clé {cle(nouveau)}) : la traduction "
                                      "rendue devient le contexte de ce texte pour l'adaptation")
            else:
                rejeter(PLUS_PRESENT, "aucun texte identifiable ne l'a remplacé ; traduction rendue : "
                                      + (_MARQ.sub("", trad) if trad else "aucune"))
            continue
        if u["erreur"]:
            rejeter("balisage", u["erreur"])
            continue
        if _normal(u["fr"]) != _normal(entree["fr"]):
            rejeter("segment FR modifié depuis l'export", "le texte français du fichier n'est plus celui de la table")
            continue
        trad = u["trad"]
        if trad is None or not trad.strip():
            rejeter("traduction vide")
            continue
        try:
            S.restaurer(trad, _table_marqueurs(entree["fr"]))
        except ValueError as e:
            rejeter("balisage", str(e))
            continue
        ancienne = entree if page is None else entree["par_page"][page]
        avant = ancienne["trad"]
        modifie = avant is None or _blancs(trad) != _blancs(avant)
        # une traduction v1, invariant ou à champ « v1 » rendue sans modification a été validée avant : comme controler (4.4),
        # on ne la contrôle pas (Ruling 30) ; dès que le relecteur la change, les contrôles bloquants s'appliquent
        exemptee = not modifie and controles.exemptee(ancienne)
        problemes = [] if exemptee else (
            controles.tirets(trad) + (controles.eszett(entree["fr"], trad) if table.langue == "de" else [])
            + controles.marques(entree["fr"], trad) + controles.interdits(trad) + controles.variables(entree["fr"], trad))
        if problemes:
            rejeter(problemes[0]["regle"], "; ".join(f"{p['detail']} : {p['extrait']}" for p in problemes))
            continue
        if not (u["confirme"] or sans_etat):  # Ruling 31 : jamais relu sans confirmation positive, segment laissé tel quel
            rapport["non_confirmes"].append({"cle": ident, "raison": "non confirmé par le relecteur", "modifie": modifie,
                                             "fr": _normal(entree["fr"])})
            continue
        identique = _normal(trad) == _normal(entree["fr"])
        if identique:
            statut, source = "invariant", f"{suite}, identique au français"
        else:
            base = ancienne.get("source") or ""
            statut = "relu"
            source = base if base.endswith(suite) else (f"{base} ; {suite}" if base else suite)
        try:
            # la provenance V1 validée suit une traduction passée relu sans changement (Ruling 30)
            v1 = (not modifie and not identique and (ancienne["statut"] == "v1" or bool(ancienne.get("v1"))))
            table.poser(entree["fr"], trad if modifie else avant, statut, source, page=page, v1=v1)
        except ValueError as e:  # filet : les contrôles de Table.poser sont ceux déjà faits ci-dessus
            rejeter("tirets" if "tirets" in str(e) else "eszett", str(e))
            continue
        rapport["relus"] += 1
        rapport["invariants"] += identique
        rapport["mt_adapte_intacts"] += (not modifie and ancienne["statut"] in ("mt", "adapte"))
        # traduction V1 confirmée sans modification (provenance V1 gardée, ou invariant si identique au français)
        rapport["v1_intacts"] += (not modifie and (ancienne["statut"] == "v1" or bool(ancienne.get("v1"))))
        if modifie:
            pages = u["pages"] or ([] if page is None else [page or ACCUEIL])
            rapport["modifies"].append({"cle": ident, "fr": _normal(entree["fr"]), "avant": avant, "apres": trad,
                                        "pages": pages, "autres_pages": u["autres_pages"]})
        for p in ([] if exemptee else controles.terminologie(entree["fr"], trad, table.langue, glossaire)):
            rapport["avertissements"].append({"cle": ident, "detail": p["detail"]})
    if attendues is not None:
        rendus = {u["id"] for u in unites}
        for ident in attendues:
            if ident not in rendus:
                entree = table.entrees.get(_decouper_id(ident)[0])
                rapport["absents"].append({"cle": ident, "fr": _normal(entree["fr"]) if entree else ""})
    return rapport


def unites_exportees(fichier, langue):
    """Identifiants des unités d'un XLIFF exporté (l'export d'origine, pour dire ce que le fichier rendu a perdu)."""
    return [u["id"] for u in _lire_xliff(fichier, langue)]


def garder_contextes_relecture(anciens, nouveaux):
    """Contextes recalculés par la mémoire (nouveaux) complétés de ceux qu'un réimport avait posés (NATURE_RELECTURE) dans
    l'ancien contextes.json : relancer la commande memoire ne les efface pas."""
    return {**{k: e for k, e in anciens.items() if (e.get("contexte") or {}).get("nature") == NATURE_RELECTURE},
            **nouveaux}


def contextes_reorientes(contextes, rapport):
    """contextes.json ({clé: {"fr", "contexte"}}) complété des traductions rendues pour un texte FR modifié depuis
    l'export (rapport["reorientes"] d'un réimport) : la nouvelle clé reçoit un contexte NATURE_RELECTURE (ancien français,
    traduction du relecteur), repris dans a_traduire.json, le lot d'adaptation et la note de l'export suivant. Un contexte
    V1 déjà présent pour la clé est gardé."""
    sortie = dict(contextes)
    for r in rapport.get("reorientes", []):
        if r["nouvelle_cle"] in sortie and (sortie[r["nouvelle_cle"]].get("contexte") or {}).get("nature") != NATURE_RELECTURE:
            continue
        sortie[r["nouvelle_cle"]] = {"fr": r["fr"], "contexte": {
            "nature": NATURE_RELECTURE, "page_v1": ", ".join(p or ACCUEIL for p in r["pages"]) or "pages inconnues",
            "fr_complet": r["fr_avant"], "trad_complete": r["trad"]}}
    return sortie


def importer_xliff(fichier, table, relecteur, glossaire=None, jour=None, sans_etat=False, assemblees=None, export=None):
    """Réimporte un XLIFF corrigé par le relecteur dans la table (en mémoire : l'appelant fait enregistrer()). Rend
    {"relus": int, "invariants": int, "modifies": [{cle, fr, avant, apres, pages, autres_pages}], "rejetes": [{cle, raison,
    detail, fr}], "avertissements": [{cle, detail}]} ; relus compte les segments acceptés (dont les « invariants » posés
    pour une traduction identique au français, Ruling 18). Un segment rejeté garde sa traduction et son statut. glossaire :
    {fr: {langue: {terme, ...}}} (chnell.charger_glossaire par défaut) ; jour : AAAA-MM-JJ (aujourd'hui par défaut).
    ValueError si le fichier est illisible, n'est pas du XLIFF 1.2 ou n'est pas écrit pour la langue de la table.
    Ruling 31 : seuls les segments confirmés (approved="yes", ou état de la cible translated, final, signed-off) passent relu ;
    les autres restent tels quels et sont listés dans « non_confirmes » [{cle, raison, modifie, fr}] ; « modifie » dit si le
    relecteur y a écrit autre chose que la traduction actuelle (ignoré). sans_etat : tout segment valide vaut confirmation.
    « mt_adapte_intacts » compte les segments mt ou adapte confirmés sans aucune modification. Une traduction v1 qui passe
    relu sans changement garde le champ « v1 » de la table (Ruling 30) ; « v1_intacts » les compte à part.
    Texte FR modifié sur le site depuis l'export (vague finale, point 2) : une unité dont la clé n'apparaît plus dans les
    pages assemblées (assemblees : {page: html} ou {page: {mode: html}}, traduire.pages_union par défaut) est rejetée
    (« segment plus présent sur le site ») ; quand le texte qui l'a remplacé sur ses pages est identifiable (_voisin), la
    traduction rendue va dans « reorientes » [{cle, nouvelle_cle, fr_avant, fr, trad, pages}] (contextes_reorientes en
    fait le contexte de la nouvelle clé), sinon dans le détail du rejet. export : XLIFF d'origine (unites_exportees) ; ses
    unités absentes du fichier rendu sont listées dans « absents » [{cle, fr}] (None sans export)."""
    attendues = unites_exportees(export, table.langue) if export is not None else None
    return _appliquer(_lire_xliff(fichier, table.langue), table, relecteur, glossaire, jour, sans_etat, assemblees,
                      attendues)


def importer_csv(fichier, table, relecteur, glossaire=None, jour=None, assemblees=None):
    """Repli tableur : réimporte un CSV de colonnes cle;fr;trad (la clé d'une traduction de page : « <clé>@<page> »), mêmes
    contrôles et même rapport que importer_xliff (assemblees : idem) ; une ligne du CSV vaut confirmation (Ruling 31)."""
    return _appliquer(_lire_csv(fichier), table, relecteur, glossaire, jour, assemblees=assemblees)


def nom_pour_fichier(texte):
    """Texte -> fragment de nom de fichier : lettres et chiffres ASCII, séparés par des tirets (« Alice Müller » donne
    « Alice-Muller »)."""
    ascii_ = unicodedata.normalize("NFKD", texte).encode("ascii", "ignore").decode()
    return re.sub(r"[^A-Za-z0-9]+", "-", ascii_).strip("-") or "relecteur"


# ---------- fusion des adaptations ----------

STATUT_FUSION = "adapte"  # seul statut que la fusion pose : relu vient toujours d'un relecteur humain (importer)


def fusionner(fichier, table, statut=STATUT_FUSION, glossaire=None, jour=None):
    """Fusionne dans la table (en mémoire : l'appelant fait enregistrer()) les propositions d'un fichier JSON, liste de
    {"cle": clé du texte français (table.cle), "trad": traduction à marqueurs {n}, "note": remarque facultative}. Chaque
    proposition passe les contrôles ci-dessous ; une proposition refusée laisse la table intacte et les autres sont posées.
    Rend {"poses": int, "refuses": [{cle, raison, detail, fr}], "avertissements": [{cle, detail}], "notes": [{cle, fr, note}]}.
    Raisons de refus : « format », « doublon » (clé déjà vue dans le fichier), « clé inconnue » (aucun texte de la table),
    « déjà relu » (statut relu ou champ « v1 »), « déjà validé » (v1 ou invariant), « traduction vide », « marqueurs »
    (segments.restaurer contre les marqueurs du français), puis la première règle bloquante de controles : « tirets »,
    « eszett » (allemand), « marques », « interdits », « variables ». La source de l'entrée reçoit « ; adapté le <jour> ».
    statut : « adapte » seulement. glossaire : {fr: {langue: {terme, ...}}} (chnell.charger_glossaire par défaut). ValueError
    si le statut n'est pas permis ou si le fichier est introuvable, illisible ou n'est pas une liste."""
    if statut != STATUT_FUSION:
        raise ValueError(f"statut « {statut} » refusé : la fusion ne pose que « {STATUT_FUSION} » (« relu » vient d'un "
                         "relecteur humain, commande importer)")
    fichier = Path(fichier)
    try:
        propositions = json.loads(fichier.read_text(encoding="utf-8"))
    except OSError:
        raise ValueError(f"fichier introuvable : {fichier}") from None
    except ValueError as e:
        raise ValueError(f"fichier JSON illisible : {fichier} ({e})") from None
    if not isinstance(propositions, list):
        raise ValueError(f"{fichier} : une liste de propositions [{{\"cle\", \"trad\", \"note\"}}] est attendue")
    glossaire = _glossaire_de(table.langue, glossaire)
    suite = f"adapté le {jour or date.today().isoformat()}"
    rapport = {"poses": 0, "refuses": [], "avertissements": [], "notes": []}
    vus = set()
    for p in propositions:
        ident = p.get("cle") if isinstance(p, dict) and isinstance(p.get("cle"), str) else None
        entree = table.entrees.get(ident)

        def refuser(raison, detail=""):
            rapport["refuses"].append({"cle": ident, "raison": raison, "detail": detail,
                                       "fr": _normal(entree["fr"]) if entree else ""})

        if ident is None or not isinstance(p.get("trad"), str) or not isinstance(p.get("note", ""), (str, type(None))):
            refuser("format", 'proposition attendue : {"cle": "...", "trad": "...", "note": "..."}')
            continue
        trad, note = p["trad"], (p.get("note") or "").strip()
        if ident in vus:
            refuser("doublon", "clé présente plusieurs fois dans le fichier")
            continue
        vus.add(ident)
        if entree is None:
            refuser("clé inconnue", "aucun texte français de la table n'a cette clé")
            continue
        if entree["statut"] == "relu" or entree.get("v1"):
            refuser("déjà relu", "traduction relue par un traducteur expert : jamais réécrite")
            continue
        if entree["statut"] in ("v1", "invariant"):
            refuser("déjà validé", f"statut {entree['statut']} : validé avant la V2")
            continue
        if not trad.strip():
            refuser("traduction vide")
            continue
        try:
            S.restaurer(trad, _table_marqueurs(entree["fr"]))
        except ValueError as e:
            refuser("marqueurs", str(e))
            continue
        problemes = (controles.tirets(trad) + (controles.eszett(entree["fr"], trad) if table.langue == "de" else [])
                     + controles.marques(entree["fr"], trad) + controles.interdits(trad)
                     + controles.variables(entree["fr"], trad))
        if problemes:
            refuser(problemes[0]["regle"], "; ".join(f"{q['detail']} : {q['extrait']}" for q in problemes))
            continue
        base = entree["source"] or ""
        table.poser(entree["fr"], trad, statut, base if base.endswith(suite) else (f"{base} ; {suite}" if base else suite))
        rapport["poses"] += 1
        if note:
            rapport["notes"].append({"cle": ident, "fr": _normal(entree["fr"]), "note": note})
        for q in controles.terminologie(entree["fr"], trad, table.langue, glossaire):
            rapport["avertissements"].append({"cle": ident, "detail": q["detail"]})
    return rapport
