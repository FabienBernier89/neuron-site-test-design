"""Données structurées (JSON-LD) d'une page assemblée : trois règles appliquées par build.assembler sur le HTML final.

1. @context : tout bloc de premier niveau qui n'en a pas reçoit "@context": "https://schema.org" (sans lui, les
   moteurs ignorent le bloc ; c'était le cas du SoftwareApplication de la page Corrext et de trois FAQPage).
2. Organization unique : toute organisation qui désigne Neur.on (même @id, nom « Neur.on » ou « Neur.on AI Solutions
   SA », ou adresse en https://neur-on.ai) est remplacée par l'entité de src/data/organisation.json, définie une seule
   fois par page (à sa première apparition) puis citée par {"@id": ...}. Cette entité est celle de la page d'accueil,
   copiée sans ajout : nom, dénomination légale, adresse de Fribourg, logo, url, sameAs (LinkedIn, seul profil
   officiel lié par le site). Aucune date de fondation ni aucun identifiant n'y figure, faute de source sur le site.
   Les propriétés propres à une page (contactPoint de la page contact) s'ajoutent à la définition de cette page.
3. dateModified : la date de dernière modification de la page (même source que le sitemap, build.date_page) est
   posée sur les nœuds de premier niveau qui décrivent la page elle-même et qui n'en ont pas : WebPage et ses
   sous-types (FAQPage, AboutPage, ContactPage, CollectionPage...), Article et ses sous-types (jamais avant leur
   datePublished, jamais à la place d'une date déjà posée). Une page sans aucun de ces nœuds reçoit un bloc WebPage
   minimal : url, nom (son title), langue, dateModified.
"""
import html as H
import json
import re
from pathlib import Path

CONTEXTE = "https://schema.org"
ORGANISATION = json.loads((Path(__file__).resolve().parents[1] / "src/data/organisation.json").read_text(encoding="utf-8"))
ID_ORGANISATION = ORGANISATION["@id"]
NOMS_NEURON = {"Neur.on", "Neur.on AI Solutions SA"}
BLOC = re.compile(r'(<script type="application/ld\+json">)(.*?)(</script>)', re.S)
TYPES_PAGE = {"WebPage", "FAQPage", "AboutPage", "ContactPage", "CollectionPage", "ItemPage", "ProfilePage", "QAPage",
              "SearchResultsPage", "CheckoutPage", "MedicalWebPage", "RealEstateListing"}
TYPES_ARTICLE = {"Article", "BlogPosting", "NewsArticle", "TechArticle", "Report", "ScholarlyArticle", "SocialMediaPosting"}


def types(o):
    t = o.get("@type") if isinstance(o, dict) else None
    return set(t) if isinstance(t, list) else {t}


def est_neuron(o):
    """Vrai pour une organisation qui désigne Neur.on (définition complète ou partielle, pas une simple référence)."""
    if not isinstance(o, dict) or "Organization" not in types(o):
        return False
    return (o.get("@id") == ID_ORGANISATION or o.get("name") in NOMS_NEURON
            or str(o.get("url", "")).startswith("https://neur-on.ai"))


def _parcourir(o, visite):
    """Appelle visite(noeud) sur chaque objet, en profondeur, dans l'ordre du document."""
    if isinstance(o, dict):
        visite(o)
        for v in o.values():
            _parcourir(v, visite)
    elif isinstance(o, list):
        for v in o:
            _parcourir(v, visite)


def _remplacer(o, nouveau):
    """Copie de o où chaque organisation Neur.on est remplacée par nouveau() (définition la première fois, puis référence)."""
    if isinstance(o, dict):
        if est_neuron(o):
            return nouveau()
        return {k: _remplacer(v, nouveau) for k, v in o.items()}
    if isinstance(o, list):
        return [_remplacer(v, nouveau) for v in o]
    return o


def premier_niveau(bloc):
    """Nœuds de premier niveau d'un bloc : le bloc lui-même, ou les nœuds de son @graph."""
    if isinstance(bloc, dict):
        return [n for n in bloc.get("@graph", [bloc]) if isinstance(n, dict)]
    return [n for n in bloc if isinstance(n, dict)] if isinstance(bloc, list) else []


def contexte(bloc):
    """Bloc dont chaque objet de premier niveau porte un @context (placé en tête)."""
    if isinstance(bloc, list):
        return [contexte(b) for b in bloc]
    if isinstance(bloc, dict) and "@context" not in bloc:
        return {"@context": CONTEXTE, **bloc}
    return bloc


def organisation(blocs):
    """Blocs où Neur.on n'est défini qu'une fois (première apparition), puis cité par son @id."""
    trouvees = []
    for b in blocs:
        _parcourir(b, lambda n: trouvees.append(n) if est_neuron(n) else None)
    if not trouvees:
        return blocs
    definition = dict(ORGANISATION)
    for n in trouvees:  # propriétés propres à la page, absentes de l'entité commune
        for k, v in n.items():
            if k not in definition and k != "@context":
                definition[k] = v
    deja = []

    def nouveau():
        if deja:
            return {"@id": ID_ORGANISATION}
        deja.append(True)
        return definition

    sortie = []
    for b in blocs:
        if isinstance(b, dict) and est_neuron(b):  # bloc qui est lui-même l'organisation : il garde son @context
            r = nouveau()
            sortie.append({"@context": b.get("@context", CONTEXTE), **r} if len(r) > 1 else None)
        else:
            sortie.append(_remplacer(b, nouveau))
    return sortie


def date_modification(blocs, date, url, titre):
    """Pose dateModified sur les nœuds qui décrivent la page ; ajoute un bloc WebPage si aucun n'existe."""
    decrit = False
    for b in blocs:
        for n in premier_niveau(b):
            t = types(n)
            if t & TYPES_PAGE:
                decrit = True
                n.setdefault("dateModified", date)
            elif t & TYPES_ARTICLE:
                decrit = True
                if "dateModified" not in n and str(n.get("datePublished", ""))[:10] <= date:
                    n["dateModified"] = date
    if not decrit:
        blocs.append({"@context": CONTEXTE, "@type": "WebPage", "url": url, "name": titre, "inLanguage": "fr-CH",
                      "dateModified": date})
    return blocs


def ecrire(bloc):
    """Bloc JSON-LD sérialisé pour un <script> (« </ » échappé)."""
    return json.dumps(bloc, ensure_ascii=False).replace("</", "<\\/")


def normaliser(html, page, date):
    """Applique les trois règles aux blocs JSON-LD de la page (chemin publié « corrext/ », « » pour l'accueil).
    date : AAAA-MM-JJ, ou None pour ne poser aucune date (page 404). Les blocs inchangés gardent leur texte."""
    trouves = list(BLOC.finditer(html))
    origine = [json.loads(m.group(2)) for m in trouves]
    blocs = organisation([contexte(json.loads(m.group(2))) for m in trouves])
    if date:
        titre = re.search(r"<title>(.*?)</title>", html, re.S)
        blocs = date_modification(blocs, date, "https://neur-on.ai/fr/" + page, H.unescape(titre.group(1)) if titre else "")
    morceaux, fin = [], 0
    for m, avant, apres in zip(trouves, origine, blocs):
        morceaux.append(html[fin:m.start()])
        if apres is not None:
            morceaux.append(m.group(0) if apres == avant else m.group(1) + ecrire(apres) + m.group(3))
        fin = m.end()
        if apres is None and html[fin:fin + 1] == "\n":
            fin += 1  # bloc supprimé (organisation déjà définie plus haut) : sa ligne disparaît avec lui
    sortie = "".join(morceaux) + html[fin:]
    nouveaux = blocs[len(trouves):]  # bloc WebPage ajouté : dans l'en-tête, juste avant </head>
    if nouveaux:
        insertion = "".join('<script type="application/ld+json">' + ecrire(b) + "</script>\n" for b in nouveaux)
        sortie = sortie.replace("</head>", insertion + "</head>", 1)
    return sortie
