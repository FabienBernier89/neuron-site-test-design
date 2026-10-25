"""Exemples de loi du glossaire dans la langue de la page (tâche 3.3).

Chaque page de terme (ressources/glossaire/<terme>/) montre le terme dans un texte officiel, dans une fenêtre CHnell
(classe cr-chst) : une ligne alignée, le paragraphe allemand de la loi (lang="de") puis son équivalent français
(lang="fr"), avec au-dessus la langue des deux colonnes (lk-l1 « Allemand », lk-l2 « Français »). Règle de la spec V1 du
2026-10-02 : l'exemple s'affiche en allemand et en français sur la page allemande, en allemand et en italien sur la
page italienne, en allemand et en anglais sur la page anglaise.

Allemand : rien ne change (le français reste, balisé lang="fr", donc ni extrait ni traduit). Italien et anglais : le
paragraphe français est remplacé par le passage de même rang de la page V1 de la langue (lang="it" ou lang="en", texte
publié et validé par les traducteurs le 2026-10-05), et le libellé de la langue (lk-l2) par celui de la V1 (« Italiano »,
« English »), balisé lui aussi de la langue de la page : ni l'un ni l'autre n'est extrait comme texte à traduire.

Six pages de termes sont restées en français dans la V1 anglaise (la loi n'existe pas en anglais) : la V1 y affiche
l'allemand et le français, sous le libellé « French ». La page anglaise de la V2 fait de même : paragraphe français
gardé, libellé repris de la V1.

Garde-fous (ValueError, la page n'est alors pas publiable dans la langue) : page V1 de la langue absente ou sans exemple,
paragraphe allemand de la V1 différent de celui de la V2 (l'équivalent ne traduirait plus le même texte), nombre
d'exemples de la V1 différent de celui de la V2.

Bibliothèque standard seulement."""
import html as H
import re
from pathlib import Path

from outils.i18n import langues

LANGUES = ("it", "en")
_PAGE_TERME = re.compile(r"ressources/glossaire/[^/]+/")
# libellé de la langue de droite (lk-l2) et lignes alignées de la fenêtre CHnell d'un terme (cr-chst) ; les lignes
# s'arrêtent au pied de la fenêtre (cr-ch-f)
_ZONE = re.compile(r'<span class="cr-lang lk-l2">(?P<libelle>[^<]*)</span>(?P<entre>(?:(?!<span class="cr-lang lk-l2">).)*?'
                   r'<div class="lk-r">)(?P<lignes>.*?)(?=</div><div class="cr-ch-f">)', re.S)
_FRANCAIS = re.compile(r'<p lang="fr">(?P<corps>.*?)</p>', re.S)
_PARAGRAPHE = re.compile(r'<p lang="(?P<lang>de|fr)">(?P<corps>.*?)</p>', re.S)
# exemple de la V1 : une rangée de deux colonnes <div><i>Libellé</i><p lang="..">passage</p></div>
_RANGEE = re.compile(r'<div class="gex-row">(?P<rangee>.*?)<p class="gsrc"', re.S)
_COLONNE = re.compile(r'<div><i>(?P<libelle>.*?)</i><p lang="(?P<lang>[\w-]+)">(?P<corps>.*?)</p></div>', re.S)


def _texte(fragment):
    """Texte lisible d'un fragment HTML : balises retirées, entités désechappées, espaces normalisés."""
    return " ".join(H.unescape(re.sub(r"<[^>]+>", "", fragment)).split())


def _exemple_v1(neuron, page, langue):
    """Colonnes de l'exemple de la page V1 de la langue : [(libellé, lang, passage)], HTML interne tel que publié."""
    try:
        fichier = Path(neuron) / "docs" / langues.route(page, langue) / "index.html"
    except KeyError as e:
        raise ValueError(f"{page} : adresse inconnue en {langue} ({e})") from None
    if not fichier.is_file():
        raise ValueError(f"{page} : page V1 absente en {langue} ({fichier})")
    m = _RANGEE.search(fichier.read_text(encoding="utf-8"))
    colonnes = [(c["libelle"].strip(), c["lang"], c["corps"].strip()) for c in _COLONNE.finditer(m["rangee"])] if m else []
    if not colonnes:
        raise ValueError(f"{page} : aucun exemple de loi dans la page V1 en {langue}")
    return colonnes


def concerne(page, langue):
    """Vrai si l'exemple de loi de la page est à remplacer dans la langue : page de terme du glossaire, en italien ou en anglais."""
    return langue in LANGUES and _PAGE_TERME.fullmatch(page) is not None


def exemples(html, page, langue, neuron):
    """Page française assemblée -> la même page, l'exemple de loi du glossaire dans la langue de la page (voir le module).
    Rend `html` tel quel hors des pages de termes du glossaire et en allemand. À appeler avant l'extraction des segments
    (traduire.analyser) : le passage et le libellé posés portent le lang de la langue, l'extraction ne les voit pas.
    neuron : dossier du site V1 (lecture seule). ValueError si l'exemple ne se remplace pas de façon certaine."""
    if not concerne(page, langue):
        return html
    zones = list(_ZONE.finditer(html))
    paragraphes = [(p["lang"], p["corps"]) for z in zones for p in _PARAGRAPHE.finditer(z["lignes"])]
    francais = [corps for lang, corps in paragraphes if lang == "fr"]
    if not zones or not francais:
        raise ValueError(f"{page} : exemple de loi introuvable dans la page française assemblée")
    if len(zones) != len(francais):
        raise ValueError(f"{page} : {len(francais)} paragraphes français pour {len(zones)} fenêtres d'exemple (une ligne par "
                         f"fenêtre attendue)")
    v1 = _exemple_v1(neuron, page, langue)
    allemands_v1 = [_texte(c) for _, lang, c in v1 if lang == "de"]
    allemands = [_texte(corps) for lang, corps in paragraphes if lang == "de"]
    if allemands_v1 != allemands:
        raise ValueError(f"{page} : le paragraphe allemand de la V1 ({langue}) n'est pas celui de la page : son équivalent "
                         f"ne traduit plus le même texte")
    cibles = [c for c in v1 if c[1] == langue]
    gardes = [c for c in v1 if c[1] == "fr"]
    if len(cibles) == len(francais):
        remplacer = True
    elif not cibles and len(gardes) == len(francais):
        cibles, remplacer = gardes, False  # V1 restée en français : le français reste, le libellé vient de la V1
    else:
        raise ValueError(f"{page} : {len(cibles)} passage(s) lang=\"{langue}\" et {len(gardes)} passage(s) lang=\"fr\" dans la "
                         f"V1 ({langue}) pour {len(francais)} exemple(s) de la page")
    rang = iter(cibles)

    def zone(m):
        libelle, _, passage = next(rang)
        lignes = m["lignes"]
        if remplacer:
            lignes = _FRANCAIS.sub(lambda _: f'<p lang="{langue}">{passage}</p>', lignes, count=1)
        return f'<span class="cr-lang lk-l2" lang="{langue}">{libelle}</span>{m["entre"]}{lignes}'
    return _ZONE.sub(zone, html)
