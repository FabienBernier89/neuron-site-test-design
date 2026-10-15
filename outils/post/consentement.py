"""Mesure d'audience (lot C, spec V2 § 6) : identifiant Google Analytics, bandeau de consentement, bouton « Préférences
cookies ».

Rien n'est ajouté sur l'aperçu (« apercu » vrai dans src/data/config.json), ni quand l'identifiant (« ga_id ») est vide :
l'aperçu n'affiche jamais le bandeau et ne charge jamais Google Analytics. En production, avec un identifiant :
- <meta name="ga-id"> dans la tête : assets/global/consentement.js le lit, et lui seul charge gtag.js, après « Accepter » ;
- le bandeau, caché, juste après le lien d'évitement (tôt dans l'ordre de lecture et de tabulation) ;
- le bouton qui le rouvre, dans la barre basse du pied (.fp-b), caché tant que le script ne l'a pas activé.
Les textes viennent de src/data/contenus-v2/C-suivi.json. Idempotent."""
import html as H
import re

from outils import contenus
from outils.post import _reglages

IDENTIFIANT = re.compile(r"G-[A-Z0-9]{4,16}")
PROTECTION = "{{ROOT}}protection-des-donnees/#suivi"  # § 5 « Outils de suivi web »
EVITEMENT = '<a class="skip" href="#main">Aller au contenu</a>\n'


def _t(cle):
    return H.escape(contenus.texte(cle), quote=False)


def bandeau():
    return ('<div class="cc" id="cc" role="region" aria-label="' + H.escape(contenus.texte("consentement.aria")) + '" hidden>'
            '<div class="wrap cc-in"><p>' + _t("consentement.texte") + ' <a href="' + PROTECTION + '">' + _t("consentement.lien") + "</a></p>"
            '<div class="cc-b"><button type="button" class="btn btn-s" data-cc="refuser">' + _t("consentement.refuser") + "</button>"
            '<button type="button" class="btn btn-s" data-cc="accepter">' + _t("consentement.accepter") + "</button></div></div></div>\n")


def bouton():
    return '<button type="button" class="fp-ck" data-cc-ouvrir hidden>' + _t("consentement.parametres") + "</button>"


def traiter(html, page):
    reglages = _reglages.config()
    ga = reglages.get("ga_id") or ""
    if reglages.get("apercu") or not ga:
        return html
    if not IDENTIFIANT.fullmatch(ga):
        raise ValueError(f"ga_id invalide dans src/data/config.json : {ga!r} (attendu : G-XXXXXXXX)")
    if 'name="ga-id"' not in html:
        html = html.replace("</head>", f'<meta name="ga-id" content="{ga}">\n</head>', 1)
    if 'id="cc"' not in html:
        if EVITEMENT in html:
            html = html.replace(EVITEMENT, EVITEMENT + bandeau(), 1)
        else:
            html = re.sub(r"<body[^>]*>\n?", lambda m: m.group(0) + bandeau(), html, count=1)
    barre = html.find('<div class="fp-b">')
    if barre >= 0 and "data-cc-ouvrir" not in html:
        fin = html.find("</div>\n", barre)  # fin de la barre basse, après les liens légaux
        html = html[:fin] + bouton() + html[fin:]
    return html
