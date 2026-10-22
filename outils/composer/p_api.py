"""Page API et on-premises : composée par generique.py, sauf trois blocs (audit validé par Fabien le 2026-10-21).

- « Un appel, les mêmes réglages que dans l'interface » : réparé (son titre est un h3 dans la V1), texte et réglages
  cochés à gauche, l'écran de l'appel d'API de la page Éditeurs à droite (metier_modele.ecran_api).
- « Ce qui est disponible, et sous quelle forme » : tableau d'une ligne par capacité (proposition B), toutes
  disponibles aujourd'hui (Fabien, 2026-10-21), puis un appel pour demander la documentation de l'API.
- « Ce que nous avons besoin de savoir » : les cinq questions en liste numérotée.

    cd outils/composer && python3 p_api.py
"""
import generique
import trame
from metier_modele import *
from outil_modele import situations_rangees

P = "corrext/api-on-premises/"
k = lambda c: texte(f"api.{c}")
SOUV = "Souveraineté, dans les deux cas"
# détail « sous quelle forme » remplacé : la V1 disait « Aucune documentation publique » et « À cadrer dans un projet
# d'intégration » (Word) ; tout est disponible aujourd'hui, la documentation se transmet sur demande
DETAIL = {"API REST": "api.forme.api", "Collaboration dans Word": "api.forme.word"}


def appel_api(sec, ctx):
    ft = bloc(sec, "div", "feat-txt")
    a = blocs(ft, "a", "feat-link")[0]
    href = re.search(r'href="([^"]+)"', a).group(1)
    reglages = "".join(f'<li><i>{COCHE}</i>{brut(re.sub(r"<span class=.chk.>.*?</span>", "", interne(li), flags=re.S))}</li>' for li in blocs(ft, "li"))
    note = brut(re.sub(r"<svg.*?</svg>", "", interne(bloc(sec, "p", "api-illus")), flags=re.S))
    ecran = scene(764, 500, ecran_api(), sim="api", titre="Microsoft Word", curseur=False, label="Traduction d'un paragraphe Word par appel d'API")
    return section(f'<div class="ai"><div>{h2(txt(bloc(ft, "h3")), "les mêmes réglages")}<p class="intro">{brut(bloc(ft, "p"))}</p>'
                   f'<ul class="ai-l">{reglages}</ul><p class="rg-lien"><a class="lien" href="{href}">{txt(a)}</a></p></div>'
                   f'<div class="ai-v">{ecran}<p class="ai-n">{note}</p></div></div>')


def disponible(sec, ctx):
    lead = bloc(sec, "div", "facts-lead")
    lignes, souv = "", None
    for f in blocs(sec, "div", "fact"):
        nom, p = txt(bloc(f, "b")), bloc(f, "p")
        sm = bloc(p, "small") if "<small>" in p else ""
        quoi = brut(p.replace(sm, "")) if sm else brut(p)
        forme = esc(texte(DETAIL[nom])) if nom in DETAIL else (brut(interne(sm)) if sm else "")
        forme = forme.replace("la page Plugin Word", '<a href="{{ROOT}}fr/corrext/plugin-word/">la page Plugin Word</a>')
        if nom == SOUV:
            souv = f'<div class="ad-souv"><b>{nom}</b><p>{quoi}{" " + forme if forme else ""}</p></div>'
            continue
        lignes += (f'<tr><th scope="row" class="pa-s">{nom}</th><td class="pa-n">{quoi}</td>'
                   f'<td class="pa-n"><span class="ad-p">{esc(k("dispo"))}</span><span class="ad-f">{forme}</span></td></tr>')
    assert souv, "fait « Souveraineté » absent de la V1"
    tete = "".join(f'<th scope="col" class="{c}">{esc(k(x))}</th>' for x, c in (("col.capacite", "pa-s"), ("col.quoi", "pa-n"), ("col.forme", "pa-n")))
    table = section(h2(txt(bloc(lead, "h2")), "quelle forme") + f'<p class="intro">{esc(k("intro"))}</p>'
                    f'<div class="pa-tw"><table class="pa-t ad-t"><thead><tr>{tete}</tr></thead><tbody>{lignes}</tbody></table></div>' + souv)
    doc = trame.bouton_suivi(f'<div class="ad-doc"><div><h2>{esc(k("doc.titre"))}</h2><p>{esc(k("doc.texte"))}</p></div>'
                             f'<a class="btn" href="{C}">{esc(k("doc.bouton"))}</a></div>', "api-documentation", "milieu").replace(
        f'href="{C}"', f'href="{C}?demande=documentation-api"', 1)  # suivi.js en fait une demande de documentation
    return table + section(doc)


def questions(sec, ctx):
    box = bloc(sec, "div", "gov-box")
    a = blocs(box, "a", "feat-link")[0]
    href = re.search(r'href="([^"]+)"', a).group(1)
    qs = "".join(f'<li><span class="qa-n">{i}</span><div><h3>{txt(bloc(x, "b")).rstrip(".")}</h3><p>{brut(re.sub(r"<b>.*?</b>", "", interne(x), flags=re.S))}</p></div></li>'
                 for i, x in enumerate([s for s in blocs(bloc(sec, "div", "gov-steps"), "span") if "<b>" in s[:12]], 1))
    return section(f'<div class="qa"><div>{h2(txt(bloc(box, "h2")), "une intégration")}<p class="intro">{brut(bloc(box, "p"))}</p>'
                   f'<p class="rg-lien"><a class="lien" href="{href}">{txt(a)}</a></p></div><ol class="qa-l">{qs}</ol></div>')


print(P, generique.composer(P, remplacer={"who": lambda sec, ctx: situations_rangees(sec, generique.mots_accent(sec)), "api-int": appel_api, "facts": disponible, "gov": questions}) or "écrite")
