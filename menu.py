"""Lit le méga-menu et le pied de page du site Neur.on, puis les rend au gabarit du test de design."""
import html as H
import re

CHEVRON = ('<svg viewBox="0 0 16 16" aria-hidden="true"><path d="M4 6l4 4 4-4" fill="none" '
           'stroke="currentColor" stroke-width="1.6" stroke-linecap="round" stroke-linejoin="round"/></svg>')
ECRAN = ('<svg viewBox="0 0 16 16" aria-hidden="true"><rect x="2" y="3" width="12" height="8" rx="1.5" '
         'fill="none" stroke="currentColor" stroke-width="1.4"/><path d="M6 13.5h4" stroke="currentColor" stroke-width="1.4"/></svg>')
SOLEIL = ('<svg viewBox="0 0 16 16" aria-hidden="true"><circle cx="8" cy="8" r="3" fill="none" stroke="currentColor" '
          'stroke-width="1.4"/><path d="M8 1.5v1.6M8 12.9v1.6M1.5 8h1.6M12.9 8h1.6M3.4 3.4l1.1 1.1M11.5 11.5l1.1 1.1'
          'M3.4 12.6l1.1-1.1M11.5 4.5l1.1-1.1" stroke="currentColor" stroke-width="1.4" stroke-linecap="round"/></svg>')
LUNE = ('<svg viewBox="0 0 16 16" aria-hidden="true"><path d="M13 9.5A5.5 5.5 0 0 1 6.5 3a5.5 5.5 0 1 0 6.5 6.5z" '
        'fill="none" stroke="currentColor" stroke-width="1.4" stroke-linejoin="round"/></svg>')
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
    return {"colonnes": colonnes, "copyright": _txt(bas.group(1)), "legal": legal, "iso": iso}


def rendre_entete(nav, actif="", minimal=False):
    h = ['<a class="skip" href="#main">Aller au contenu</a>\n',
         '<p class="ruban" data-libre>Version de test de design, non indexée. Une page modèle par type : '
         'les liens sans page mènent au modèle de leur type.</p>\n',
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
            else:
                h.append(f'<a class="{cls}" href="{_a(e["href"])}">{_e(e["libelle"])}</a>\n')
        h.append('</nav>\n<div class="hd-cta"><a class="btn btn-s" href="{{ROOT}}contact/">Demander une démo</a>'
                 '<button type="button" class="hd-burger" id="hdBurger" aria-expanded="false" aria-controls="mm" '
                 'aria-label="Ouvrir le menu"><span></span><span></span><span></span></button></div>\n')
    h.append("</div>\n")
    if not minimal:
        for cle, p in nav["panneaux"].items():
            h.append(f'<div class="mg" id="mg-{cle}" hidden>\n<div class="wrap mg-in">\n')
            for col in p["colonnes"]:
                h.append(f'<div class="mg-col"><p class="mg-h">{_e(col["titre"])}</p>\n')
                for l in col["liens"]:
                    em = f'<em>{_e(l["desc"])}</em>' if l["desc"] else ""
                    h.append(f'<a class="mg-a" href="{_a(l["href"])}"><b>{_e(l["titre"])}</b>{em}</a>\n')
                h.append("</div>\n")
            pr = p["promo"]
            if pr:
                h.append(f'<a class="mg-card" href="{_a(pr["href"])}"><span class="mg-mini" aria-hidden="true">'
                         '<span class="mg-mw"><i></i><i></i><i></i></span></span>'
                         f'<b>{_e(pr["titre"])}</b><span class="mg-t">{_e(pr["texte"])}</span>'
                         f'<span class="lien">{_e(pr["lien"])}</span></a>\n')
            h.append("</div>\n</div>\n")
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
    h.append('<a class="btn mm-cta" href="{{ROOT}}contact/">Demander une démo</a>\n</div>\n</div>\n')
    return "".join(h)


def rendre_pied(pied):
    cols = []
    for c in pied["colonnes"]:
        liens = [i for i in c["items"] if i["href"] and not i["href"].startswith("mailto:")]
        autres = [i for i in c["items"] if i not in liens]
        cols.append((c["titre"], liens))
        if autres:
            cols.append(("Contact", autres))
    cols.append(("Légal", pied["legal"]))
    h = ['<footer class="pied">\n<div class="wrap">\n<div class="fp-g">\n']
    for titre, items in cols:
        h.append(f'<div><p>{_e(titre)}</p><ul>\n')
        for i in items:
            if i["href"]:
                h.append(f'<li><a href="{_a(i["href"])}">{_e(i["texte"])}</a></li>\n')
            else:
                h.append(f'<li><span>{_e(i["texte"])}</span></li>\n')
        h.append("</ul></div>\n")
    h.append('</div>\n<div class="fp-b"><span>' + _e(pied["copyright"]) + "</span>" + THEME + "</div>\n"
             '<p class="fp-iso">' + _e(pied["iso"]) + "</p>\n</div>\n</footer>\n")
    return "".join(h)
