"""Lit le méga-menu et le pied de page du site Neur.on, puis les rend au gabarit du test de design."""
import html as H
import json
import re
from pathlib import Path

AJOUTS = Path(__file__).resolve().parent / "src/data/menu-ajouts.json"  # entrées ajoutées par les lots de la V2
PAGES = Path(__file__).resolve().parent / "src/pages"
SOUS_TITRES = {e["titre"]: e["texte"] for e in json.loads(
    (Path(__file__).resolve().parent / "src/data/menu-sous-titres.json").read_text(encoding="utf-8"))["entrees"]}  # deux lignes chacun


def sous_titre_de_page(href):
    """Sous-titre d'un lien du méga-menu qui n'en a pas : la seconde ligne du titre de sa page (h1 > span.s), lue telle
    quelle dans la source (retour de Fabien du 2026-10-15). Chaîne vide si la page n'en a pas."""
    f = PAGES / href.split("#")[0] / "index.html"
    if not f.exists():
        return ""
    m = re.search(r'<h1[^>]*>.*?<span class="s">(.*?)</span>', f.read_text(encoding="utf-8"), re.S)
    return _txt(m.group(1)) if m else ""

CHEVRON = ('<svg viewBox="0 0 16 16" aria-hidden="true"><path d="M4 6l4 4 4-4" fill="none" '
           'stroke="currentColor" stroke-width="1.6" stroke-linecap="round" stroke-linejoin="round"/></svg>')
ECRAN = ('<svg viewBox="0 0 16 16" aria-hidden="true"><rect x="2" y="3" width="12" height="8" rx="1.5" '
         'fill="none" stroke="currentColor" stroke-width="1.4"/><path d="M6 13.5h4" stroke="currentColor" stroke-width="1.4"/></svg>')
SOLEIL = ('<svg viewBox="0 0 16 16" aria-hidden="true"><circle cx="8" cy="8" r="3" fill="none" stroke="currentColor" '
          'stroke-width="1.4"/><path d="M8 1.5v1.6M8 12.9v1.6M1.5 8h1.6M12.9 8h1.6M3.4 3.4l1.1 1.1M11.5 11.5l1.1 1.1'
          'M3.4 12.6l1.1-1.1M11.5 4.5l1.1-1.1" stroke="currentColor" stroke-width="1.4" stroke-linecap="round"/></svg>')
LUNE = ('<svg viewBox="0 0 16 16" aria-hidden="true"><path d="M13 9.5A5.5 5.5 0 0 1 6.5 3a5.5 5.5 0 1 0 6.5 6.5z" '
        'fill="none" stroke="currentColor" stroke-width="1.4" stroke-linejoin="round"/></svg>')
# Connexion à Corrext (adresse fournie par Fabien le 2026-10-15), en haut à droite et dans le menu mobile
CONNEXION = ("https://auth.corrext.com/realms/corrext/protocol/openid-connect/auth?client_id=corrext"
             "&scope=openid%20email%20profile&response_type=code"
             "&redirect_uri=https%3A%2F%2Fcorrext.com%2Fapi%2Fauth%2Fcallback%2Fkeycloak")
# Carte mise en avant de chaque panneau du méga-menu : mini-interface qui montre où mène le lien (peau des cartes de
# fonctionnalités, assets/composants/fonctionnalites.css). Libellés repris du site : démo, titres des comparatifs,
# distinctions du bandeau de l'accueil. Retour de Fabien du 2026-10-15 : plus de fenêtre vide.
def _visuels_mega():
    from outils.post.fonctionnalites import VISUELS
    return {
        "corrext/traduction-texte-et-document/#demo": VISUELS["fr/corrext/traduction-texte-et-document/"],
        "comparatif/": ('<div class="u-lbl">Comparatifs</div><div class="u-list u-niv">'
                        '<div class="u-it u-n1"><i></i>Corrext et DeepL</div>'
                        '<div class="u-it u-n2"><i></i>Corrext et les LLM généralistes</div>'
                        '<div class="u-it u-n3"><i></i>Agence de traduction ou plateforme</div></div>'),
        "a-propos/": ('<div class="u-lbl">À propos et distinctions</div><div class="u-list u-dl">'
                      '<div class="u-it"><span>Swiss FinTech Awards 2024</span><small>Lauréat Early Stage</small></div>'
                      '<div class="u-it"><span>BILANZ</span><small>Entreprises les plus innovantes 2024</small></div>'
                      '<div class="u-it"><span>Hébergement 100% suisse</span><small>Infomaniak</small></div></div>'),
    }


THEME = ('<div class="theme" role="group" aria-label="Thème d\'affichage">'
         '<button type="button" data-theme-set="systeme" aria-label="Thème du système">' + ECRAN + '</button>'
         '<button type="button" data-theme-set="clair" aria-label="Thème clair">' + SOLEIL + '</button>'
         '<button type="button" data-theme-set="sombre" aria-label="Thème sombre">' + LUNE + '</button></div>')


def _txt(s):
    """Texte brut d'un fragment HTML, sans SVG ni balises."""
    s = re.sub(r"<svg.*?</svg>", "", s, flags=re.S)
    return re.sub(r"\s+", " ", H.unescape(re.sub(r"<[^>]+>", "", s))).strip()


def _href(h):
    """Chemin du site actuel sans le préfixe {{ROOT}}fr/."""
    return re.sub(r"^\{\{ROOT\}\}(fr/)?", "", h)


def _a(href):
    return href if href.startswith(("http", "mailto:")) else "{{ROOT}}" + href


def _e(s):
    return H.escape(s, quote=False)


def lire_menu(nav):
    entrees = []
    for m in re.finditer(r'<div class="nav-item" data-key="(\w+)">\s*(<button.*?</button>|<a .*?</a>)', nav, re.S):
        cle, el = m.groups()
        if el.startswith("<button"):
            entrees.append({"cle": cle, "libelle": _txt(el), "panneau": True})
        else:
            entrees.append({"cle": cle, "libelle": _txt(el), "href": _href(re.search(r'href="([^"]+)"', el).group(1))})
    panneaux = {}
    bureau = nav.split("<!-- MENU MOBILE -->")[0]
    for bloc in re.split(r'<div class="mega" id="mega-', bureau)[1:]:
        cle = bloc[:bloc.index('"')]
        colonnes, promo = [], None
        for c in re.finditer(r'<div class="mega-col( mega-promo)?">(.*?)\n      </div>', bloc, re.S):
            titre = _txt(re.search(r'<p class="mega-h">(.*?)</p>', c.group(2), re.S).group(1))
            if c.group(1):
                a = re.search(r'<a href="([^"]+)"[^>]*>(.*?)</a>', c.group(2), re.S)
                promo = {"titre": titre,
                         "texte": _txt(re.search(r'<p class="mega-p">(.*?)</p>', c.group(2), re.S).group(1)),
                         "href": _href(a.group(1)), "lien": _txt(a.group(2))}
                continue
            liens = []
            for a in re.finditer(r'<a href="([^"]+)"[^>]*>(.*?)</a>', c.group(2), re.S):
                b = re.search(r"<b>(.*?)</b>", a.group(2), re.S)
                em = re.search(r"<em>(.*?)</em>", a.group(2), re.S)
                liens.append({"href": _href(a.group(1)), "titre": _txt(b.group(1) if b else a.group(2)),
                              "desc": _txt(em.group(1)) if em else ""})
            colonnes.append({"titre": titre, "liens": liens})
        panneaux[cle] = {"colonnes": colonnes, "promo": promo}
    return {"entrees": entrees, "panneaux": panneaux}


def lire_pied(pied):
    colonnes = []
    for m in re.finditer(r'<p class="ft-h">(.*?)</p>\s*<ul[^>]*>(.*?)</ul>', pied, re.S):
        items = []
        for li in re.findall(r"<li>(.*?)</li>", m.group(2), re.S):
            a = re.search(r'<a href="([^"]+)"[^>]*>(.*?)</a>', li, re.S)
            items.append({"href": _href(a.group(1)), "texte": _txt(a.group(2))} if a else {"href": "", "texte": _txt(li)})
        colonnes.append({"titre": _txt(m.group(1)), "items": items})
    bas = re.search(r'<div class="footer-bottom">\s*<span>(.*?)</span>(.*?)</div>\s*</div>', pied, re.S)
    legal = [{"href": _href(h), "texte": _txt(t)} for h, t in re.findall(r'<a href="([^"]+)">(.*?)</a>', bas.group(2))]
    iso = _txt(re.search(r'<p class="footer-iso">(.*?)</p>', pied, re.S).group(1))
    apropos = _txt(re.search(r'<div class="footer-about">.*?<p>(.*?)</p>', pied, re.S).group(1))
    social = re.search(r'<a class="footer-social" href="([^"]+)"[^>]*aria-label="([^"]+)"', pied)
    return {"colonnes": colonnes, "copyright": _txt(bas.group(1)), "legal": legal, "iso": iso,
            "apropos": apropos, "social": {"href": social.group(1), "label": social.group(2)}}


def _inserer(liste, nouveau, apres, quoi, deja):
    """Insère nouveau dans liste juste après l'élément dont le href est apres (en fin de liste si apres est vide).
    Plusieurs ajouts après le même élément gardent l'ordre du fichier."""
    if not apres:
        liste.append(nouveau)
        return
    i = next((k for k, x in enumerate(liste) if x.get("href") == apres), None)
    if i is None:
        raise ValueError(f"{quoi} : « apres » introuvable : {apres}")
    n = deja.get((id(liste), apres), 0)
    liste.insert(i + 1 + n, nouveau)
    deja[(id(liste), apres)] = n + 1


def appliquer_ajouts(nav, pied, ajouts=None):
    """Ajoute au menu lu (lire_menu) et au pied lu (lire_pied) les entrées de src/data/menu-ajouts.json, sur place.

    - panneaux : {panneau: [{"colonne", "apres", "href", "titre", "desc"}]}. Le lien suit l'entrée « apres »
      (un href), cherchée d'abord dans la colonne indiquée puis dans tout le panneau : il prend la colonne de cette
      entrée. Sans « apres », il termine la colonne indiquée (0 par défaut).
    - pied : {titre de colonne: [{"apres", "href", "texte"}]}, même règle d'insertion.
    - entrees : [{"avant", "cle", "libelle", "href"}] : lien du menu principal, placé avant l'entrée de clé « avant ».
    - libelles : {clé d'entrée: nouveau libellé} : renomme une entrée du menu principal (ordinateur et mobile).
    Une entrée mal adressée (panneau, colonne, « apres » ou titre inconnus) lève ValueError."""
    if ajouts is None:
        ajouts = json.loads(AJOUTS.read_text(encoding="utf-8"))
    deja = {}
    for cle, liens in ajouts.get("panneaux", {}).items():
        if cle not in nav["panneaux"]:
            raise ValueError(f"panneau inconnu : {cle}")
        colonnes = nav["panneaux"][cle]["colonnes"]
        for a in liens:
            nouveau = {"href": a["href"], "titre": a["titre"], "desc": a.get("desc", "")}
            n = a.get("colonne", 0)
            if not a.get("apres"):
                if not 0 <= n < len(colonnes):
                    raise ValueError(f"panneau {cle} : colonne {n} inexistante ({len(colonnes)} colonnes)")
                colonnes[n]["liens"].append(nouveau)
                continue
            ordre = ([colonnes[n]] if 0 <= n < len(colonnes) else []) + [c for k, c in enumerate(colonnes) if k != n]
            cible = next((c for c in ordre if any(l["href"] == a["apres"] for l in c["liens"])), None)
            if cible is None:
                raise ValueError(f"panneau {cle} : « apres » introuvable : {a['apres']}")
            _inserer(cible["liens"], nouveau, a["apres"], f"panneau {cle}", deja)
    for a in ajouts.get("entrees", []):
        i = next((k for k, x in enumerate(nav["entrees"]) if x["cle"] == a["avant"]), None)
        if i is None:
            raise ValueError(f"entrée de menu : « avant » introuvable : {a['avant']}")
        nav["entrees"].insert(i, {"cle": a["cle"], "libelle": a["libelle"], "href": a["href"]})
    for cle, libelle in ajouts.get("libelles", {}).items():
        e = next((x for x in nav["entrees"] if x["cle"] == cle), None)
        if e is None:
            raise ValueError(f"entrée de menu à renommer introuvable : {cle}")
        e["libelle"] = libelle
    for titre, items in ajouts.get("pied", {}).items():
        colonne = next((c for c in pied["colonnes"] if c["titre"] == titre), None)
        if colonne is None:
            raise ValueError(f"colonne de pied inconnue : {titre}")
        for a in items:
            _inserer(colonne["items"], {"href": a["href"], "texte": a["texte"]}, a.get("apres"), f"pied {titre}", deja)
    return nav, pied


def _panneau(cle, p):
    """Panneau du méga-menu, émis dans la nav juste après son bouton : la tabulation passe du bouton ouvert à la
    première entrée du panneau (audit du 2026-10-23, WCAG 2.4.3) ; la position à l'écran reste réglée en CSS."""
    h = [f'<div class="mg" id="mg-{cle}" hidden>\n<div class="wrap mg-in">\n']
    for col in p["colonnes"]:
        h.append(f'<div class="mg-col"><p class="mg-h">{_e(col["titre"])}</p>\n')
        for l in col["liens"]:
            if l["titre"].startswith("Tous les "):
                # lien vers le hub de la colonne : simple lien fléché, comme « Voir les comparatifs » (Fabien, 2026-10-19)
                h.append(f'<a class="mg-tous" href="{_a(l["href"])}"><span class="lien">Voir {_e(l["titre"][0].lower() + l["titre"][1:])}</span></a>\n')
                continue
            desc = SOUS_TITRES.get(l["titre"]) or l["desc"] or sous_titre_de_page(l["href"])
            em = f'<em>{_e(desc)}</em>' if desc else ""
            h.append(f'<a class="mg-a" href="{_a(l["href"])}"><b>{_e(l["titre"])}</b>{em}</a>\n')
        h.append("</div>\n")
    pr = p["promo"]
    if pr:
        vis = _visuels_mega().get(pr["href"])
        fond = f'<span class="fx-w mg-w">{vis}</span>' if vis else '<span class="mg-mw"><i></i><i></i><i></i></span>'
        h.append(f'<a class="mg-card" href="{_a(pr["href"])}"><span class="mg-mini" aria-hidden="true">{fond}</span>'
                 f'<b>{_e(pr["titre"])}</b><span class="mg-t">{_e(pr["texte"])}</span>'
                 f'<span class="lien">{_e(pr["lien"])}</span></a>\n')
    h.append("</div>\n</div>\n")
    return "".join(h)


def _libelle_fermer():
    """Nom du bouton du menu mobile une fois ouvert (contenus nouveaux de la V2, lot V)."""
    from outils import contenus
    return contenus.texte("a11y.menu.fermer")


def rendre_entete(nav, actif="", minimal=False):
    """En-tête et menus. Le ruban d'aperçu a été retiré le 2026-10-15 (demande de Fabien) ; le noindex reste."""
    h = ['<a class="skip" href="#main">Aller au contenu</a>\n',
         '<header class="hd' + (" min" if minimal else "") + '" id="hd">\n<div class="wrap hd-in">\n',
         '<a class="hd-logo" href="{{ROOT}}" aria-label="Neur.on, retour à l\'accueil">'
         '<img class="logo-c" src="{{ROOT}}assets/img/neuron-logo.png" alt="Neur.on" width="92" height="28">'
         '<img class="logo-s" src="{{ROOT}}assets/img/neuron-logo-blanc.png" alt="" width="92" height="28"></a>\n']
    if not minimal:
        h.append('<nav class="hd-nav" aria-label="Navigation principale">\n')
        for e in nav["entrees"]:
            cls = "hd-i" + (" actif" if e["cle"] == actif else "")
            if e.get("panneau"):
                h.append(f'<button type="button" class="{cls}" aria-expanded="false" aria-controls="mg-{e["cle"]}" '
                         f'data-mg>{_e(e["libelle"])}{CHEVRON}</button>\n')
                h.append(_panneau(e["cle"], nav["panneaux"][e["cle"]]))
            else:
                h.append(f'<a class="{cls}" href="{_a(e["href"])}">{_e(e["libelle"])}</a>\n')
        h.append('</nav>\n<div class="hd-cta"><a class="hd-cx" href="' + H.escape(CONNEXION) + '">Connexion</a>'
                 '<a class="btn btn-s" href="{{ROOT}}contact/" data-suivi="cta-entete">Demander une démo</a>'
                 '<button type="button" class="hd-burger" id="hdBurger" aria-expanded="false" aria-controls="mm" '
                 f'aria-label="Ouvrir le menu" data-fermer="{H.escape(_libelle_fermer(), quote=True)}">'
                 '<span></span><span></span><span></span></button></div>\n')
    h.append("</div>\n")
    h.append("</header>\n")
    if not minimal:
        h.append('<div class="mg-voile" hidden></div>\n')
        h.append(rendre_mobile(nav))
    return "".join(h)


def rendre_mobile(nav):
    h = ['<div class="mm" id="mm" hidden>\n<div class="wrap">\n']
    for e in nav["entrees"]:
        if not e.get("panneau"):
            h.append(f'<a class="mm-h" href="{_a(e["href"])}">{_e(e["libelle"])}</a>\n')
            continue
        p = nav["panneaux"][e["cle"]]
        h.append(f'<div class="mm-g"><button type="button" class="mm-h" aria-expanded="false">'
                 f'{_e(e["libelle"])}{CHEVRON}</button><div class="mm-b" hidden>\n')
        for col in p["colonnes"]:
            h.append(f'<p>{_e(col["titre"])}</p>\n')
            h.extend(f'<a href="{_a(l["href"])}">{_e(l["titre"])}</a>\n' for l in col["liens"])
        if p["promo"]:
            h.append(f'<a href="{_a(p["promo"]["href"])}">{_e(p["promo"]["lien"])}</a>\n')
        h.append("</div></div>\n")
    h.append('<a class="mm-cx" href="' + H.escape(CONNEXION) + '">Connexion</a>'
             '<a class="btn mm-cta" href="{{ROOT}}contact/" data-suivi="cta-entete-mobile">Demander une démo</a>\n</div>\n</div>\n')
    return "".join(h)


# Titres de colonne du pied reliés à leur page hub (sinon ces hubs n'ont aucun lien entrant)
HUBS_PIED = {"Plateforme": "corrext/", "Solutions": "solutions/", "Ressources": "ressources/"}


# Icônes et logo LinkedIn du pied de la V1 (repris tels quels)
EPINGLE = ('<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" '
           'stroke-linejoin="round" aria-hidden="true"><path d="M21 10c0 7-9 13-9 13s-9-6-9-13a9 9 0 0 1 18 0z"/>'
           '<circle cx="12" cy="10" r="3"/></svg>')
ENVELOPPE = ('<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" '
             'stroke-linejoin="round" aria-hidden="true"><path d="M4 4h16c1.1 0 2 .9 2 2v12c0 1.1-.9 2-2 2H4c-1.1 0-2-.9-2-2V6'
             'c0-1.1.9-2 2-2z"/><polyline points="22,6 12,13 2,6"/></svg>')
LINKEDIN = ('<svg viewBox="0 0 24 24" aria-hidden="true"><rect width="24" height="24" rx="3" fill="#0A66C2"/>'
            '<path fill="#ffffff" d="M4.98 3.5a2.5 2.5 0 1 1 0 5 2.5 2.5 0 0 1 0-5zM3 9h4v12H3zM9 9h3.8v1.71h.05c.53-.95 '
            '1.83-1.95 3.77-1.95 4.03 0 4.78 2.45 4.78 5.64V21h-4v-5.4c0-1.29-.02-2.95-1.8-2.95-1.8 0-2.08 1.4-2.08 '
            '2.85V21H9z"/></svg>')


def rendre_pied(pied):
    """Pied de la V1 : colonne de présentation (logo, texte, ISO, LinkedIn), quatre colonnes de liens,
    barre basse (copyright, liens légaux) ; sélecteur des trois thèmes sous l'e-mail de contact."""
    h = ['<footer class="pied">\n<div class="wrap">\n<div class="fp-g">\n'
         '<div class="fp-a">'
         '<a class="fp-logo" href="{{ROOT}}" aria-label="Neur.on, retour à l\'accueil">'
         '<img class="logo-c" src="{{ROOT}}assets/img/neuron-logo.png" alt="Neur.on" width="112" height="34">'
         '<img class="logo-s" src="{{ROOT}}assets/img/neuron-logo-blanc.png" alt="" width="112" height="34"></a>'
         '<p>' + _e(pied["apropos"]) + '</p>'
         '<p class="fp-iso">' + _e(pied["iso"]) + '</p>'
         f'<a class="fp-so" href="{H.escape(pied["social"]["href"])}" target="_blank" rel="noopener" '
         f'aria-label="{H.escape(pied["social"]["label"])}">' + LINKEDIN + '</a></div>\n']
    for c in pied["colonnes"]:
        hub = HUBS_PIED.get(c["titre"])
        tete = f'<a href="{_a(hub)}">{_e(c["titre"])}</a>' if hub else _e(c["titre"])
        h.append(f'<div><p class="fp-h">{tete}</p><ul>\n')
        for i in c["items"]:
            if i["href"].startswith("mailto:"):
                h.append(f'<li class="fp-c">{ENVELOPPE}<a href="{_a(i["href"])}">{_e(i["texte"])}</a></li>\n')
            elif i["href"]:
                h.append(f'<li><a href="{_a(i["href"])}">{_e(i["texte"])}</a></li>\n')
            else:
                h.append(f'<li class="fp-c">{EPINGLE}<span>{_e(i["texte"])}</span></li>\n')
        # Le choix du thème se place sous les coordonnées (colonne qui porte l'e-mail)
        contact = any(i["href"].startswith("mailto:") for i in c["items"])
        h.append("</ul>" + (THEME if contact else "") + "</div>\n")
    legal = "".join(f'<a href="{_a(l["href"])}">{_e(l["texte"])}</a>' for l in pied["legal"])
    h.append('</div>\n<div class="fp-b"><span>' + _e(pied["copyright"]) + '</span>'
             '<div class="fp-l">' + legal + "</div></div>\n</div>\n</footer>\n")
    return "".join(h)
