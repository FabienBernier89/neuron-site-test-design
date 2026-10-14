"""Encart d'inscription à la lettre d'information (lot E).

`encart()` renvoie le bloc HTML inséré avant le pied de page par outils/post/newsletter.py. Les textes viennent de
src/data/contenus-v2/E-blog.json (clés « newsletter.* »). Le formulaire part vers /envoi.php (chemin absolu :
envoi.php n'est pas une page du site) avec les champs attendus par ce script : type, t0, site_url (piège), email,
consentement. Les champs de suivi (UTM, page d'entrée) et t0 sont remplis par assets/global/suivi.js.
Sur l'aperçu (« apercu » vrai dans src/data/config.json) le formulaire porte data-demo : nav.js bloque l'envoi et
injecte l'avis « aucun envoi » dans une région aria-live présente dès le chargement (annoncée par les lecteurs d'écran).
Ordre des champs : e-mail, consentement, bouton (le consentement se lit avant d'envoyer).
"""
import html
import json
import sys
from pathlib import Path

RACINE = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))  # outils/ : « from contenus import texte »
from contenus import texte  # noqa: E402

PAGE_DONNEES = "{{ROOT}}fr/protection-des-donnees/"
AVIS_DEMO = "Formulaire de démonstration : aucun envoi."  # phrase du formulaire de contact du site actuel


def _esc(s):
    return html.escape(s, quote=False)


def en_apercu(config=None):
    """Vrai quand le site est un aperçu. Sans configuration donnée, lit src/data/config.json (lecture seule)."""
    if config is None:
        config = json.loads((RACINE / "src/data/config.json").read_text(encoding="utf-8"))
    return bool(config.get("apercu"))


def _consentement():
    """Phrase de consentement, ses mots « politique de protection des données » portant le lien."""
    phrase, lien = _esc(texte("newsletter.consentement")), _esc(texte("newsletter.consentement.lien"))
    if lien not in phrase:
        raise ValueError("newsletter.consentement.lien doit figurer dans newsletter.consentement")
    return phrase.replace(lien, f'<a href="{PAGE_DONNEES}">{lien}</a>', 1)


def encart(config=None):
    """Bloc HTML de l'encart. config : réglages du site (clé « apercu »), par défaut ceux de src/data/config.json."""
    demo = en_apercu(config)
    avis = f'<p class="avis" aria-live="polite" data-libre data-avis="{html.escape(AVIS_DEMO)}"></p>' if demo else ""
    return (
        '<section class="nl-s" aria-labelledby="nl-titre"><div class="wrap"><div class="nl">'
        f'<div class="nl-t"><p class="nl-h" id="nl-titre">{_esc(texte("newsletter.titre"))}</p>'
        f'<p class="nl-x">{_esc(texte("newsletter.texte"))}</p></div>'
        f'<form class="nl-f" action="/envoi.php" method="post"{" data-demo" if demo else ""}>'
        '<input type="hidden" name="type" value="newsletter">'
        '<input type="hidden" name="t0" value="">'
        f'<div class="nl-piege" aria-hidden="true"><label for="nl-site">{_esc(texte("newsletter.piege"))}</label>'
        '<input type="text" id="nl-site" name="site_url" tabindex="-1" autocomplete="off" aria-hidden="true"></div>'
        f'<div class="nl-l"><label for="nl-email">{_esc(texte("newsletter.email"))}<span class="req" aria-hidden="true">*</span></label>'
        '<input type="email" id="nl-email" name="email" autocomplete="email" required></div>'
        '<div class="nl-c"><input type="checkbox" id="nl-consent" name="consentement" value="oui" autocomplete="off" required>'
        f'<label for="nl-consent">{_consentement()}<span class="req" aria-hidden="true">*</span></label></div>'
        f'<button type="submit" class="btn">{_esc(texte("newsletter.bouton"))}</button>'
        f"{avis}</form></div></div></section>\n"
    )
