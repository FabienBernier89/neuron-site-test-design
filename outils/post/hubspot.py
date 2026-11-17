"""Page Protection des données : deux paragraphes nouveaux sur HubSpot (conservé, décision de Fabien du 2026-11-17).

HubSpot (portail 26502466) n'est chargé qu'après « Accepter » dans le bandeau, par Tag Manager ; il suit les visites et
garde les demandes envoyées par les formulaires du site. La page le dit à deux endroits :
- rubrique 3 « Formulaire de contact » : un paragraphe juste après celui qui finit par APRES_FORMULAIRE ;
- rubrique 5 « Outils de suivi web » : un paragraphe après ceux sur Google Analytics, juste avant AVANT_SUIVI.
Rien d'autre ne change. Si une ancre manque ou figure deux fois, le build s'arrête plutôt que de publier un texte au
mauvais endroit.

Textes : src/data/contenus-v2/C-suivi.json (clés CLE_FORMULAIRE et CLE_SUIVI), validés par Fabien ; traductions dans
src/langues/<langue>/segments.json. Idempotent."""
import html as H

from outils import contenus

PAGE = "protection-des-donnees/"
CLE_FORMULAIRE = "protection-des-donnees.formulaire.hubspot"
CLE_SUIVI = "protection-des-donnees.hubspot"
APRES_FORMULAIRE = "Nous ne transmettons pas ces données à des tiers sans votre consentement.</p>"
AVANT_SUIVI = '<p class="legal-see">'


def _paragraphe(cle):
    return "<p>" + H.escape(contenus.texte(cle), quote=False) + "</p>"


def _une_fois(html, ancre):
    if html.count(ancre) != 1:
        raise ValueError(f"{PAGE} : ancre introuvable ou en double ({html.count(ancre)}) : {ancre[:60]}")


def traiter(html, page):
    if page != PAGE:
        return html
    formulaire, suivi = _paragraphe(CLE_FORMULAIRE), _paragraphe(CLE_SUIVI)
    if formulaire not in html:
        _une_fois(html, APRES_FORMULAIRE)
        html = html.replace(APRES_FORMULAIRE, APRES_FORMULAIRE + "\n      " + formulaire, 1)
    if suivi not in html:
        _une_fois(html, AVANT_SUIVI)
        html = html.replace(AVANT_SUIVI, suivi + "\n\n      " + AVANT_SUIVI, 1)
    return html
