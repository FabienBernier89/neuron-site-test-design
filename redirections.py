"""Redirections des anciennes adresses du site Neur.on : lecture dans le site actuel, pages d'aperçu, 301 Apache.

Le site Neur.on actuel (V1) garde des pages de redirection (meta refresh) pour ses anciennes adresses :
adresses WordPress à la racine (/about, /news, articles de 2020...) et anciens slugs sous fr/. On les relit,
on suit les chaînes jusqu'à une page réelle, et on en tire deux formes :
- des pages de redirection pour l'aperçu (GitHub Pages ne sait pas faire de 301) ;
- un .htaccess de vraies 301 pour Hostpoint.

Périmètre : français seul. Les redirections sous de/, it/, en/ relèvent des versions allemande, italienne et
anglaise (lot F). Les anciennes adresses de la racine renvoyaient vers la version anglaise ; faute de version
anglaise dans ce site, elles renvoient vers l'équivalent français de la même page, que la page anglaise
déclare dans son hreflang fr-CH.
"""
import html as H
import posixpath
import re
from pathlib import Path

LANGUES_HORS_PERIMETRE = ("de", "it", "en")
IGNORES = ("maquettes",)
PRODUCTION = "https://neur-on.ai"
REFRESH = re.compile(r'<meta http-equiv="refresh" content="[^"]*?url=([^"]+)"')
HREFLANG_FR = re.compile(r'<link rel="alternate" hreflang="fr-CH" href="' + re.escape(PRODUCTION) + r'(/fr/[^"]*)"')
ANCIEN_SUR = re.compile(r"^[a-z0-9_/-]+/$")                              # ancien chemin : pas de caractère à échapper
CIBLE_SURE = re.compile(r"^/fr/[a-z0-9/-]*(#[A-Za-z0-9_-]+)?$")
UN_AN = "public, max-age=31536000, immutable"


def _redirection(fichier, docs):
    """(page cible absolue, ancre) d'une page de redirection du site, ou None si la page n'en est pas une."""
    m = REFRESH.search(fichier.read_text(encoding="utf-8"))
    if not m:
        return None
    chemin, _, ancre = H.unescape(m.group(1)).partition("#")
    dossier = "/" + fichier.parent.relative_to(docs).as_posix() + "/"
    cible = posixpath.normpath(posixpath.join(dossier, chemin))
    return (cible + "/" if chemin.endswith("/") else cible), ancre


def _page_reelle(docs, chemin, redirs, ancien):
    """Fichier de la page réelle (ni absente, ni elle-même une redirection) ou ValueError."""
    f = docs / chemin.strip("/") / "index.html"
    if chemin in redirs or not f.is_file():
        raise ValueError(f"{ancien} : la cible {chemin} n'est pas une page réelle du site Neur.on")
    return f


def lire(neuron):
    """Redirections du périmètre : {ancien chemin (sans barre initiale, avec barre finale): cible absolue
    /fr/<page>/[#ancre]}. Lève ValueError si une cible n'existe pas, si une chaîne boucle, si une ancre manque
    dans la page cible ou si une page d'une autre langue n'a pas d'équivalent français."""
    docs = Path(neuron) / "docs"
    redirs = {}  # toutes les pages de redirection, toutes langues : "/ancien/" -> (cible, ancre)
    for f in sorted(docs.rglob("index.html")):
        dossier = f.parent.relative_to(docs)
        if dossier == Path(".") or dossier.parts[0] in IGNORES:
            continue
        r = _redirection(f, docs)
        if r:
            redirs["/" + dossier.as_posix() + "/"] = r
    resultat = {}
    for ancien in sorted(redirs):
        if ancien.split("/")[1] in LANGUES_HORS_PERIMETRE:
            continue
        cible, ancre = redirs[ancien]
        vus = {ancien}
        while cible in redirs:  # on suit la chaîne ; une ancre posée plus loin remplace la précédente
            if cible in vus:
                raise ValueError(f"{ancien} : boucle de redirections sur {cible}")
            vus.add(cible)
            cible, suite = redirs[cible]
            ancre = suite or ancre
        page = _page_reelle(docs, cible, redirs, ancien)
        if not cible.startswith("/fr/"):  # autre langue : l'équivalent français est déclaré par la page elle-même
            alt = HREFLANG_FR.search(page.read_text(encoding="utf-8"))
            if not alt:
                raise ValueError(f"{ancien} : la page {cible} n'a pas d'équivalent français (hreflang fr-CH)")
            cible = alt.group(1)
            page = _page_reelle(docs, cible, redirs, ancien)
        if ancre and f'id="{ancre}"' not in page.read_text(encoding="utf-8"):
            raise ValueError(f"{ancien} : l'ancre #{ancre} est absente de la page {cible}")
        resultat[ancien[1:]] = cible + ("#" + ancre if ancre else "")
    return resultat


def _verifier(ancien, cible):
    if not ANCIEN_SUR.match(ancien) or not CIBLE_SURE.match(cible):
        raise ValueError(f"redirection non écrivable telle quelle : {ancien} -> {cible}")


def page(ancien, cible):
    """Page de redirection de l'aperçu : meta refresh relatif, canonique vers la production, noindex."""
    _verifier(ancien, cible)
    relatif = "../" * ancien.count("/") + cible[1:]
    return ('<!DOCTYPE html>\n<html lang="fr"><head><meta charset="UTF-8"><title>Page déplacée · Neur.on</title>'
            '<meta name="robots" content="noindex">'
            f'<link rel="canonical" href="{PRODUCTION}{cible}">'
            f'<meta http-equiv="refresh" content="0; url={relatif}">'
            f'<script>location.replace("{relatif}")</script></head>'
            f'<body><p>Cette page a déménagé : <a href="{relatif}">voir la nouvelle adresse</a>.</p></body></html>\n')


def htaccess(redirs):
    """.htaccess Hostpoint : page d'erreur, racine vers le français, une 301 par ancienne adresse, cache d'un an des polices, feuilles et scripts."""
    lignes = ["# Généré par build.py : ne pas modifier à la main.",
              "ErrorDocument 404 /404.html",
              "RewriteEngine On",
              "# La langue n'est pas encore choisie côté serveur : la racine part vers le français (302, provisoire).",
              "RewriteRule ^$ /fr/ [R=302,L]",
              "# Anciennes adresses : avec ou sans barre finale, ancre conservée (NE).",
              ]
    for ancien, cible in sorted(redirs.items()):
        _verifier(ancien, cible)
        lignes.append(f"RewriteRule ^{ancien.rstrip('/')}/?$ {cible} [R=301,L,NE]")
    lignes += [
        "# Cache d'un an. Sans mod_headers, rien n'est posé.",
        "<IfModule mod_headers.c>",
        "  # Polices (assets/fonts/) : remplacer une police impose de changer son nom de fichier, le navigateur ne la",
        "  # redemande pas pendant un an.",
        '  <FilesMatch "\\.woff2$">',
        f'    Header set Cache-Control "{UN_AN}"',
        "  </FilesMatch>",
        "  # Feuilles et scripts : les pages les appellent avec ?v=<empreinte>, une nouvelle version change l'URL.",
        '  <FilesMatch "\\.(css|js)$">',
        f'    Header set Cache-Control "{UN_AN}"',
        "  </FilesMatch>",
        "</IfModule>",
    ]
    return "\n".join(lignes) + "\n"
