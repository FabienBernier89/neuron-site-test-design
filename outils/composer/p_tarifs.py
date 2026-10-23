"""Compose la page Tarifs (tarifs/), page nouvelle de la V2 : une page d'information, sans aucun prix.

Plan validé par Fabien le 2026-10-16 (structure d'une page tarifs de référence, adaptée à Neur.on) : hero à deux
boutons, une offre par organisation, ce que réunit la plateforme, comment obtenir votre offre (les trois étapes de la page contact), modules selon les
besoins (cartes de fonctionnalités illustrées par outils/post/fonctionnalites.py), FAQ, appel « Prêt à essayer ? ».
Textes : src/data/contenus-v2/I-tarifs.json (à relire) ; définitions des produits : B-schema.json.

    cd outils/composer && python3 p_tarifs.py
"""
import html as H
import json
import sys
from pathlib import Path

RACINE = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(RACINE))
from outils.contenus import texte  # noqa: E402
from comp import section, h2, cartes, faq, cta  # noqa: E402
import trame  # noqa: E402

P = "tarifs/"
C = "{{ROOT}}contact/"
DEMO = "Demander une démo"
EN_DIRECT = "{{ROOT}}#demo"  # démo interactive de l'accueil (Fabien, 2026-10-23)


def t(cle):
    """Texte d'un contenu nouveau, échappé pour le HTML."""
    return H.escape(texte(cle), quote=False)


def hero():
    n, s = (H.escape(x, quote=False) for x in texte("tarifs.hero.titre").split(". ", 1))
    return ('<section class="hero">\n<div class="wrap hero-g tf-hg">\n'
            f'<h1 class="h1"><span class="n">{n}.</span> <span class="s">{s}</span></h1>\n'
            f'<div class="hero-d"><p>{t("tarifs.hero.lead")}</p>'
            f'<div class="tf-act"><a class="btn" href="{C}" data-suivi="cta-tarifs-hero">{DEMO}</a>'
            f'<a class="btn btn-2" href="{EN_DIRECT}">{t("tarifs.hero.demo")}</a></div>'
            f'<p class="note">{t("tarifs.hero.note")}</p></div>\n</div>\n</section>\n')


# Profils : libellé, titre (texte du site ou nouveau), texte, page de la solution, suffixe du suivi
# Six profils, un par page Solutions (retour de Fabien du 2026-10-16)
PROFILS = [("cabinets", "solutions/cabinets-avocats/"), ("banques", "solutions/banques-finance/"),
           ("directions", "solutions/directions-juridiques/"), ("autorites", "solutions/autorites-administration/"),
           ("fiduciaires", "solutions/fiduciaires-conseil/"), ("integrateurs", "solutions/editeurs-legaltech/")]


def profils():
    cartes_html = []
    for cle, page in PROFILS:
        titre = t(f"tarifs.profils.{cle}.titre")
        cartes_html.append(
            f'<div class="tf-p"><p class="tf-k">{t(f"tarifs.profils.{cle}.label")}</p><h3>{titre}</h3>'
            f'<p class="tf-d">{t(f"tarifs.profils.{cle}.texte")}</p>'
            f'<div class="tf-pa"><a class="btn btn-2" href="{C}" data-suivi="cta-tarifs-{cle}-milieu">{DEMO}</a>'
            f'<a class="lien" href="{{{{ROOT}}}}{page}">{t("tarifs.profils.lien")}</a></div></div>')
    return section(h2(t("tarifs.profils.titre"), "chaque organisation") + '<div class="tf-pg">' + "".join(cartes_html) + "</div>")


def socle():
    items = [(t(f"tarifs.socle.{k}.titre"), H.escape(texte(f"schema.{k}.def"), quote=False), None, "") for k in ("corrext", "lexmachina", "chnell")]
    items += [
(t("tarifs.socle.hebergement.titre"), t("tarifs.socle.hebergement.texte"), None, "")]
    return section(h2(t("tarifs.socle.titre"), "la plateforme") + cartes(items).replace('<div class="cd">', '<div class="cd c4">', 1))


def offre():
    """Comment obtenir votre offre : les trois étapes de la page contact (pas de devis de l'application ici)."""
    etapes = "".join(f'<li><span class="tf-n">0{i}</span><h3>{t(f"tarifs.offre.etape{i}.titre")}</h3>'
                     f'<p>{t(f"tarifs.offre.etape{i}.texte")}</p></li>' for i in (1, 2, 3))
    return section(h2(t("tarifs.offre.titre"), "votre offre") + f'<p class="intro">{t("tarifs.offre.intro")}</p>'
                   + f'<ol class="tf-et">{etapes}</ol>')


def modules():
    # Liens vers des fonctionnalités : outils/post/fonctionnalites.py les rend en cartes illustrées et animées
    items = [(t(f"tarifs.modules.{k}.titre"), t(f"tarifs.modules.{k}"), (None, "{{ROOT}}fr/" + page), "")
             for k, page in (("niveaux", "niveaux-de-qualite/"), ("extraits", "corrext/extraits-registre-commerce/"), ("api", "corrext/api-on-premises/"))]
    return section(h2(t("tarifs.modules.titre"), "vos besoins") + cartes(items))


def faq_jsonld(qr):
    d = {"@context": "https://schema.org", "@type": "FAQPage",
         "mainEntity": [{"@type": "Question", "name": q, "acceptedAnswer": {"@type": "Answer", "text": r}} for q, r in qr]}
    return '<script type="application/ld+json">' + json.dumps(d, ensure_ascii=False).replace("</", "<\\/") + "</script>\n"


def composer():
    qr = [(texte(f"tarifs.faq.q{i}"), texte(f"tarifs.faq.r{i}")) for i in range(1, 6)]
    l1, l2 = (H.escape(x, quote=False) for x in texte("tarifs.cta.titre").split("? ", 1))
    appel = cta(l1 + "?", l2, (DEMO, C)).replace('<a class="btn"', '<a class="btn" data-suivi="cta-tarifs-fin"', 1)
    out = [hero(), profils(), socle(), offre(), modules(),
           faq(t("tarifs.faq.titre"), [(H.escape(q, quote=False), f"<p>{H.escape(r, quote=False)}</p>") for q, r in qr]),
           faq_jsonld(qr), trame.appel(appel)]
    entete = ("<!--page\n"
              f"title: {texte('tarifs.meta.title')}\n"
              f"description: {texte('tarifs.meta.description')}\n"
              "menu: tarifs\ngabarit: standard\n-->\n")
    return entete + "".join(out)


def ecrire():
    f = RACINE / "src/pages" / P / "index.html"
    f.parent.mkdir(parents=True, exist_ok=True)
    f.write_text(composer(), encoding="utf-8")


if __name__ == "__main__":
    ecrire()
    print("tarifs écrit")
