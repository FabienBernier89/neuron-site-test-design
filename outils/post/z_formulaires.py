"""Formulaires vers envoi.php (lot C, spec V2 § 6). Nommé « z_ » pour passer après les autres post-traitements, dont
l'encart newsletter qu'un autre lot insère.

- Tout formulaire dont l'action finit par « envoi.php » reçoit l'action absolue /envoi.php, la méthode POST (imposée),
  les champs cachés de suivi (remplis dans le navigateur par assets/global/suivi.js, dont « duree », le temps passé sur
  la page au moment de l'envoi) et le champ piège. Sur l'aperçu, il porte
  data-demo : nav.js bloque l'envoi. En production, data-demo, novalidate et l'avis « aucun envoi » disparaissent :
  le formulaire part, après le contrôle des champs obligatoires par le navigateur.
- Le formulaire de démo de la page contact reçoit son action et le champ Secteur (les 6 pages secteur, plus « Autre »).
- Les cases à cocher qui partagent un nom partent en tableau (« langues[] ») : PHP n'en garderait qu'une.
- La page de remerciement n'est jamais indexée, même en production.
- Chaque formulaire reçoit en tête une région role="alert", vide au chargement : assets/global/formulaires.js y écrit le
  résumé des erreurs et place sous chaque champ fautif le message lié (aria-invalid, aria-describedby). Les messages
  viennent de src/data/contenus-v2 (lot V) par les attributs data- de cette région (audit du 2026-10-23, WCAG 3.3.1).

Idempotent : repasser une page déjà traitée ne la change pas."""
import html as H
import re

from outils import contenus
from outils.post import _reglages

ACTION = "/envoi.php"  # chemin absolu : envoi.php n'est pas une page du site, relier() ne doit pas le toucher
MERCI = "contact/merci/"
# Pages secteur de la V2 : dossier src/pages/solutions/<slug>/ et libellé du pied de page (repris du site actuel)
SECTEURS = (("cabinets-avocats", "Cabinets d'avocats"), ("banques-finance", "Banques et finance"),
            ("directions-juridiques", "Directions juridiques"), ("autorites-administration", "Autorités et administration"),
            ("fiduciaires-conseil", "Fiduciaires et conseil"), ("editeurs-legaltech", "LegalTechs et éditeurs"))
# Champs cachés, remplis par suivi.js ; « type » vaut « demo » sauf si le formulaire le fixe (« newsletter »).
# « duree » (millisecondes sur la page) sert au délai minimal de envoi.php ; « t0 » (horodatage) reste pour l'interface.
CACHES = ("type", "t0", "duree", "page_entree", "page_origine", "utm_source", "utm_medium", "utm_campaign", "utm_term", "utm_content")
PIEGE = '<div class="piege" aria-hidden="true"><input type="text" name="site_url" tabindex="-1" autocomplete="off"></div>'
FORMULAIRE = re.compile(r"(<form\b[^>]*>)(.*?)(</form>)", re.S)
AVIS = re.compile(r'<p class="avis"[^>]*>.*?</p>', re.S)


def _esc(s):
    return H.escape(s, quote=False)


def _attribut(nom):
    """Attribut booléen ou valué d'une balise ouvrante (data-demo, novalidate...)."""
    return re.compile(r'\s' + nom + r'(?:="[^"]*")?(?=[\s>])')


def _action(ouverture):
    m = re.search(r'\saction="([^"]*)"', ouverture)
    return m.group(1) if m else None


def _secteur():
    options = ['<option value="">' + _esc(contenus.texte("contact.secteur.choix")) + "</option>"]
    options += [f'<option value="{slug}">{_esc(libelle)}</option>' for slug, libelle in SECTEURS]
    options.append('<option value="autre">' + _esc(contenus.texte("contact.secteur.autre")) + "</option>")
    return ('<div class="pl"><label for="cf-secteur">' + _esc(contenus.texte("contact.secteur.libelle")) + "</label>"
            '<select id="cf-secteur" name="secteur" autocomplete="off">' + "".join(options) + "</select></div>")


def _resume():
    """Région des erreurs : vide, donc invisible, tant que le formulaire n'a pas été envoyé incomplet."""
    attributs = "".join(f' data-{n}="{H.escape(contenus.texte("a11y.formulaire." + n), quote=True)}"'
                        for n in ("resume", "requis", "choix", "email", "case"))
    return f'<div class="f-err" role="alert"{attributs}></div>'


def _ouverture(o, apercu):
    # Méthode imposée : envoi.php refuse tout autre méthode que POST
    if re.search(r"\smethod=", o):
        o = re.sub(r"""\smethod=(?:"[^"]*"|'[^']*'|[^\s>]+)""", ' method="post"', o, count=1)
    else:
        o = o[:-1] + ' method="post">'
    if apercu:
        if not _attribut("data-demo").search(o):
            o = o[:-1] + " data-demo>"
    else:
        o = _attribut("novalidate").sub("", _attribut("data-demo").sub("", o))
    return o


def _corps(corps, apercu):
    ajout = "".join(f'<input type="hidden" name="{n}" value="{"demo" if n == "type" else ""}">'
                    for n in CACHES if not re.search(r'\sname="' + n + '"', corps))
    if 'name="site_url"' not in corps:
        ajout += PIEGE
    if 'class="f-err"' not in corps:
        ajout += _resume()
    corps = ajout + corps
    # Cases à cocher de même nom : un tableau pour PHP
    for nom in set(re.findall(r'<input\b(?=[^>]*\stype="checkbox")[^>]*\sname="([^"\[\]]+)"', corps)):
        if len(re.findall(r'\sname="' + re.escape(nom) + '"', corps)) > 1:
            corps = corps.replace(f' name="{nom}"', f' name="{nom}[]"')
    # Formulaire de démo : le secteur suit l'organisation
    if 'name="organisation"' in corps and 'name="secteur"' not in corps:
        fin = corps.index("</div>", corps.index('name="organisation"')) + len("</div>")
        corps = corps[:fin] + _secteur() + corps[fin:]
    if not apercu:
        corps = AVIS.sub("", corps)
    return corps


def traiter(html, page):
    apercu = bool(_reglages.config().get("apercu"))

    def formulaire(m):
        o, corps, fin = m.groups()
        action = _action(o)
        if action is None and page == "contact/" and 'name="prenom"' in corps:  # formulaire de démo du site actuel
            o, action = o.replace("<form", f'<form action="{ACTION}"', 1), ACTION
        if not (action or "").endswith("envoi.php"):
            return m.group(0)
        if action != ACTION:  # {{ROOT}}envoi.php, ../envoi.php... : toujours le chemin absolu
            o = re.sub(r'\saction="[^"]*"', f' action="{ACTION}"', o, count=1)
        return _ouverture(o, apercu) + _corps(corps, apercu) + fin

    html = FORMULAIRE.sub(formulaire, html)
    if page == MERCI and '<meta name="robots"' not in html:
        html = html.replace("<title>", '<meta name="robots" content="noindex">\n<title>', 1)
    return html
