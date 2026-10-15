"""Trame problème, situation visée, preuve, appel à l'action (lot D, spec V2 § 7) : accueil et 6 pages secteur, puis
la page Sécurité et souveraineté (décision de Fabien du 2026-10-15), qui reprend le problème et les preuves.

Ordre des blocs : hero, problème, situation visée (existante), preuves, exemple de cas d'usage, FAQ, appel à l'action.
Ce module fournit les deux blocs nouveaux et l'habillage des appels à l'action ; chaque composeur garde ses blocs
existants et les range dans cet ordre (p_accueil.py, p_metier.py, generique.py).

- probleme(cle) : section « sec tr-pb », trois difficultés de la page (cle : « accueil » ou dossier de la page secteur).
- preuves(cle, bandeau, exemple) : section « sec tr-pv », registre des preuves admises, dans l'ordre utile à la page.
  Une preuve déjà citée par le bandeau des distinctions de la page n'y revient pas ; la phrase de discrétion (« ne publie
  ni nom de client ni témoignage ») ne paraît que sur une page sans exemple de cas d'usage.
- appel(section, slug) : appel final en « sec cta » ; sur une page secteur, boutons vers le formulaire avec le secteur.
- boutons_secteur(html, slug, position) : liens « Demander une démo » vers contact/?secteur=<slug>, avec
  data-suivi="cta-secteur-<slug>-<position>" (lot C), position « hero » ou « fin ».
- bouton_suivi(html, contexte, position) : attribut data-suivi="cta-<contexte>-<position>" sur le bouton « Demander
  une démo » d'un bloc, lien inchangé (page sans secteur, comme la page Sécurité et souveraineté).

Textes : src/data/contenus-v2/D-trame.json (statut à relire, une source par entrée) ; pour la page Sécurité et
souveraineté, F-souverainete.json. Styles : assets/composants/trame.css.
"""
import html as _h
import re
import sys
from pathlib import Path

ICI = Path(__file__).resolve().parent
RACINE = ICI.parents[1]
for _chemin in (str(ICI), str(RACINE)):
    if _chemin not in sys.path:
        sys.path.append(_chemin)

from comp import h2  # noqa: E402
from outils.contenus import texte  # noqa: E402

SECTEURS = ("cabinets-avocats", "banques-finance", "directions-juridiques", "fiduciaires-conseil",
            "autorites-administration", "editeurs-legaltech")
# Partie du titre du problème mise en italique d'accent (absente du titre : aucun accent)
ACCENTS = {"accueil": "traduction juridique", "cabinets-avocats": "dossier multilingue",
           "banques-finance": "établissement financier", "directions-juridiques": "direction juridique",
           "fiduciaires-conseil": "document d'entreprise", "autorites-administration": "secteur public",
           "editeurs-legaltech": "produit juridique", "securite-souverainete": "document confidentiel"}
# Preuves admises (spec V2 § 7), de la plus utile à la moins utile pour chaque page
ORDRE = {
    "accueil": ("iso", "infomaniak", "segments", "innosuisse", "sfa", "dshap", "kickstart"),
    "cabinets-avocats": ("iso", "infomaniak", "segments", "innosuisse", "sfa", "dshap", "kickstart"),
    "banques-finance": ("iso", "infomaniak", "sfa", "kickstart", "segments", "innosuisse", "dshap"),
    "directions-juridiques": ("iso", "infomaniak", "segments", "innosuisse", "sfa", "dshap", "kickstart"),
    "fiduciaires-conseil": ("iso", "infomaniak", "sfa", "kickstart", "segments", "innosuisse", "dshap"),
    "autorites-administration": ("iso", "infomaniak", "innosuisse", "segments", "sfa", "dshap", "kickstart"),
    "editeurs-legaltech": ("segments", "innosuisse", "iso", "infomaniak", "sfa", "kickstart", "dshap"),
    # Page Sécurité et souveraineté : les cinq faits de la souveraineté, sans les distinctions (brief du 2026-10-15)
    "securite-souverainete": ("iso", "infomaniak", "traitement", "nlpd", "cloudact"),
}
# Pages qui présentent leurs preuves avec leur propre introduction, sans la phrase de discrétion ni la note sur les
# références clients (elles concernent les distinctions et les clients, pas les faits de sécurité)
INTRO_PROPRE = {"securite-souverainete": "trame.pv.securite-souverainete.intro"}
# Repère de chaque preuve dans le texte du bandeau des distinctions (comp.dist)
REPERES = {"iso": "ISO 27001", "infomaniak": "Infomaniak", "innosuisse": "Innosuisse", "segments": "15 millions",
           "sfa": "Swiss FinTech Awards", "dshap": "Digital Shapers", "kickstart": "Kickstart Innovation",
           "traitement": "Traitement en Suisse", "nlpd": "nLPD", "cloudact": "CLOUD Act"}
CONTACT = re.compile(r'<a class="btn" href="\{\{ROOT\}\}(?:fr/)?contact/"')


def e(s):
    return _h.escape(s, quote=False)


def _titre(cle_texte, accent, ident):
    return h2(e(texte(cle_texte)), accent).replace("<h2 ", f'<h2 id="{ident}" ', 1)


def probleme(cle):
    """Section « le problème » : titre de la page et trois difficultés (libellé, titre, texte)."""
    t = lambda x: e(texte(f"trame.pb.{cle}.{x}"))  # noqa: E731
    items = "".join(f'<li><span class="tr-k">{t(f"{n}.label")}</span><h3 class="tr-t">{t(f"{n}.titre")}</h3>'
                    f'<p>{t(f"{n}.texte")}</p></li>' for n in (1, 2, 3))
    return ('<section class="sec tr-pb" aria-labelledby="tr-pb-titre"><div class="wrap">\n'
            + _titre(f"trame.pb.{cle}.titre", ACCENTS.get(cle), "tr-pb-titre")
            + f'<ol class="tr-pb-l">{items}</ol>\n</div></section>\n')


def _brut(h):
    return re.sub(r"\s+", " ", _h.unescape(re.sub(r"<[^>]+>", " ", h))).replace(chr(0xa0), " ")


def preuves(cle, bandeau="", exemple=True):
    """Section « preuves » : titre, introduction et note à gauche, registre à filets à droite (nom, détail, nature).

    bandeau : HTML du bandeau des distinctions de la page, s'il y en a un ; ses preuves ne sont pas répétées, et
    l'introduction qui les énumère disparaît. exemple : la page montre un exemple de cas d'usage ; la phrase de
    discrétion n'y paraît pas, pour ne pas contredire l'exemple. Une page de INTRO_PROPRE garde sa seule introduction,
    sans note."""
    deja = _brut(bandeau)
    ids = [i for i in ORDRE[cle] if REPERES[i] not in deja]
    if not ids:
        raise ValueError(f"{cle} : toutes les preuves figurent déjà dans le bandeau")
    lignes = "".join(f'<li><span class="tr-pv-n"><b>{e(texte(f"trame.pv.{i}.nom"))}</b>'
                     f'<span>{e(texte(f"trame.pv.{i}.detail"))}</span></span>'
                     f'<span class="pill tr-pv-ty">{e(texte(f"trame.pv.{i}.type"))}</span></li>' for i in ids)
    if cle in INTRO_PROPRE:
        intro, note = [texte(INTRO_PROPRE[cle])], ""
    else:
        intro = ([] if exemple else [texte("trame.pv.discretion")]) + ([] if deja.strip() else [texte("trame.pv.intro")])
        note = f'<p class="legende">{e(texte("trame.pv.note"))}</p>'
    p_intro = f'<p class="intro">{e(" ".join(intro))}</p>' if intro else ""
    return ('<section class="sec tr-pv" aria-labelledby="tr-pv-titre"><div class="wrap tr-pv-g">\n'
            '<div class="tr-pv-t">' + _titre("trame.pv.titre", "vérifier", "tr-pv-titre")
            + f'{p_intro}{note}</div>'
            + f'<ul class="tr-pv-l">{lignes}</ul>\n</div></section>\n')


def boutons_secteur(html, slug, position):
    """Boutons « Demander une démo » d'une page secteur : formulaire prérempli (?secteur=) et attribut de suivi,
    distinct pour le hero (« hero ») et pour l'appel final (« fin »)."""
    if slug not in SECTEURS:
        raise ValueError(f"secteur inconnu : {slug}")
    if position not in ("hero", "fin"):
        raise ValueError(f"position de bouton inconnue : {position}")
    return CONTACT.sub(f'<a class="btn" href="{{{{ROOT}}}}contact/?secteur={slug}" data-suivi="cta-secteur-{slug}-{position}"', html)


def bouton_suivi(html, contexte, position):
    """Attribut de suivi du seul bouton « Demander une démo » (lien vers contact/) d'un bloc :
    data-suivi="cta-<contexte>-<position>", convention du lot C. ValueError s'il n'y a pas exactement un bouton."""
    if position not in ("hero", "milieu", "fin"):
        raise ValueError(f"position de bouton inconnue : {position}")
    if len(CONTACT.findall(html)) != 1:
        raise ValueError(f"cta-{contexte}-{position} : un seul bouton vers contact/ attendu dans le bloc")
    return CONTACT.sub(lambda m: m.group(0) + f' data-suivi="cta-{contexte}-{position}"', html)


def appel(section, slug=None):
    """Appel final (comp.cta) rangé dans la trame : classe « sec cta » ; boutons du secteur si la page en a un."""
    if not section.startswith('<section class="cta">'):
        raise ValueError("appel final attendu : section produite par comp.cta()")
    s = section.replace('<section class="cta">', '<section class="sec cta">', 1)
    return boutons_secteur(s, slug, "fin") if slug else s
