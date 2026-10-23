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


HOTE = "neur-on.ai"
UN_MOIS = "public, max-age=2592000"
REVALIDER = "no-cache"


def htaccess(redirs):
    """.htaccess de production pour Hostpoint (Apache), dans cet ordre :
    1. page d'erreur ;
    2. racine vers le français (302, provisoire : la langue n'est pas encore choisie côté serveur) ;
    3. une 301 par ancienne adresse ;
    4. adresse canonique : HTTP vers HTTPS et www.neur-on.ai vers neur-on.ai, en 301 ;
    5. compression (mod_deflate) et en-têtes de cache (mod_headers), chacun sous garde IfModule.
    Pas de chaîne : les règles 2 et 3 renvoient directement vers https://neur-on.ai/fr/..., si bien que
    http://www.neur-on.ai/about/ arrive en un seul saut sur https://neur-on.ai/fr/a-propos/ ; la règle 4 ne sert
    qu'aux autres adresses et va elle aussi droit à la forme finale. Derrière un proxy qui termine le HTTPS,
    l'en-tête X-Forwarded-Proto évite une boucle de redirection."""
    base = f"https://{HOTE}"
    lignes = ["# Généré par build.py : ne pas modifier à la main.",
              "ErrorDocument 404 /404.html",
              "RewriteEngine On",
              "# La langue n'est pas encore choisie côté serveur : la racine part vers le français (302, provisoire).",
              f"RewriteRule ^$ {base}/fr/ [R=302,L]",
              "# Anciennes adresses : avec ou sans barre finale, ancre conservée (NE), directement en HTTPS sur l'hôte canonique.",
              ]
    for ancien, cible in sorted(redirs.items()):
        _verifier(ancien, cible)
        lignes.append(f"RewriteRule ^{ancien.rstrip('/')}/?$ {base}{cible} [R=301,L,NE]")
    lignes += [
        "# Adresse canonique : HTTPS (sauf si un proxy l'a déjà terminé) et sans www, en un seul saut. Seuls les deux",
        "# noms du site sont concernés : une adresse de test de l'hébergeur n'est pas renvoyée vers la production.",
        "RewriteCond %{HTTP_HOST} ^(www\\.)?neur-on\\.ai$ [NC]",
        "RewriteCond %{HTTPS} !=on",
        "RewriteCond %{HTTP:X-Forwarded-Proto} !=https",
        f"RewriteRule ^ {base}%{{REQUEST_URI}} [R=301,L,NE]",
        "RewriteCond %{HTTP_HOST} ^www\\.neur-on\\.ai$ [NC]",
        f"RewriteRule ^ {base}%{{REQUEST_URI}} [R=301,L,NE]",
        "# Compression des textes (pages, feuilles, scripts, données, SVG). Polices woff2 et images déjà compressées.",
        "<IfModule mod_deflate.c>",
        "  <IfModule mod_filter.c>",
        "    AddOutputFilterByType DEFLATE text/html text/plain text/css text/xml text/javascript application/javascript"
        " application/json application/ld+json application/xml image/svg+xml image/x-icon",
        "  </IfModule>",
        "</IfModule>",
        "# Cache. Sans mod_headers, rien n'est posé.",
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
        "  # Images : appelées sans empreinte, une image remplacée sous le même nom doit pouvoir revenir. Un mois.",
        '  <FilesMatch "\\.(webp|png|jpe?g|gif|svg|ico)$">',
        f'    Header set Cache-Control "{UN_MOIS}"',
        "  </FilesMatch>",
        "  # Pages et fichiers pour les robots : toujours revalidés auprès du serveur, une mise en ligne est vue aussitôt.",
        '  <FilesMatch "\\.(html|xml|txt)$">',
        f'    Header set Cache-Control "{REVALIDER}"',
        "  </FilesMatch>",
        "</IfModule>",
    ]
    return "\n".join(lignes) + "\n"
