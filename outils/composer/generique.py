"""Composeur générique : transpose chaque bloc d'une page publiée de Neur.on vers les composants du test de design.

Les textes sont repris mot pour mot ; seuls la structure et l'habillage changent. Un repli structuré traite les
blocs rares (titre, introduction, éléments répétés en tuiles ou en cartes, tableaux, listes).
Usage : python3 generique.py [chemin/ ...]   (sans argument : toutes les pages publiées absentes de src/pages)
"""
import re
import sys
from pathlib import Path

from blocs_communs import *  # noqa: F401,F403 (source, comp, commun, app)
from blog_commun import carte_blog, grille, COUV, AUTEUR

RACINE_TEST = Path(__file__).resolve().parents[2]
SOURCE_FR = NEURON / "docs/fr"
REDIRECTIONS = {"about/", "category/non-classifiee/", "category/uncategorized-fr/", "impressum/", "news/",
                "privacy-policy/", "schedule-a-demo/", "terms-of-use/"}


# ---------- Outils ----------

def sections(t):
    """Sections de premier niveau, dans l'ordre de la page."""
    res, fin = [], 0
    for m in re.finditer(r"<section\b", t):
        if m.start() < fin:
            continue
        from source import _fin
        fin = _fin(t, m.start(), "section")
        res.append(t[m.start():fin])
    return res


def classes(sec):
    return re.search(r'<section class="([^"]*)"', sec).group(1).split()


def href(el):
    m = re.search(r'href="([^"]+)"', el)
    return m.group(1) if m else ""


def bouton(sec, defaut=("Demander une démo", C)):
    b = blocs(sec, "a", "btn-blue") or blocs(sec, "a", "btn")
    return (txt(b[0]), href(b[0])) if b else defaut


def couper_h1(h1):
    """Partie en lede (em) en sans grasse, suite en serif ; à défaut, coupe au premier « : » ou « . »."""
    corps = interne(h1).strip()
    m = re.match(r"<em>(.*?)</em>\s*(.*)", corps, re.S)
    if m:
        a, b = txt(m.group(1)), txt(m.group(2))
        if b.startswith("· "):
            a, b = a + " ·", b[2:]
        return a, b
    texte = txt(corps)
    for sep in (" : ", ". ", " · "):
        if sep in texte:
            a, b = texte.split(sep, 1)
            return a + sep.rstrip(), b
    return texte, ""


def couper_cta(h):
    for sep in (" : ", ", ", " ? "):
        if sep in h and not h.endswith(sep.strip()):
            a, b = h.split(sep, 1)
            return a + sep.rstrip(), b
    mots = h.split(" ")
    k = max(1, (len(mots) + 1) // 2 - 1)
    return " ".join(mots[:k]), " ".join(mots[k:])


def titre(sec, accent=True):
    h = blocs(sec, "h2")
    if not h:
        return ""
    texte = re.sub(r"\s+", " ", txt(re.sub(r"<[^>]+>", " ", h[0]))).strip()
    mots = texte.rstrip(" .?!").split(" ")
    acc = " ".join(mots[-2:]) if accent and len(mots) > 4 else None
    return h2(texte, acc)


def premier_p(sec):
    tete_ = (blocs(sec, "div", "sec-head") or blocs(sec, "div", "facts-lead") or [""])[0]
    zone = tete_ or sec
    for p in blocs(zone, "p"):
        if 'class="' not in p[:15] or "lead" in p[:30] or "intro" in p[:30]:
            return brut(p)
    return ""


# ---------- Transpositions par type de bloc ----------

def h_thero(sec, ctx):
    n, s = couper_h1(bloc(sec, "h1"))
    lead = blocs(sec, "p", "lead")
    out = hero(n, s, brut(lead[0]) if lead else "", bouton(sec))
    if ctx["P"].startswith("ressources/glossaire/") and "law-spec" in sec:
        spec = bloc(sec, "div", "law-spec")
        tl = [(None, txt(bloc(r, "b")), txt(bloc(r, "i"))) for r in blocs(spec, "div", "sr")]
        out += section(f'<p class="k-lab">{txt(bloc(bloc(spec, "div", "sh"), "b"))}</p>' + tuiles(tl, "tl txt t4 tl-lang"))
    return out


def h_ar_head(sec, ctx):
    meta = (blocs(sec, "div", "ar-meta") or [""])[0]
    cat = blocs(meta, "span", "ar-cat")
    spans = [txt(s) for s in blocs(meta, "span") if "ar-cat" not in s[:25] and txt(s)]
    chapo = ""
    art = ctx.get("art")
    if art:
        lead = blocs(art, "p", "art-lead")
        if lead:
            chapo = brut(lead[0])
            ctx["lead_pris"] = lead[0]
    meta_html = "".join(f"<span>{esc(x)}</span>" for x in spans)
    out = (f'<section class="ar-h"><div class="wrap"><div class="ar">'
           + (f'<span class="cat">{txt(cat[0])}</span>' if cat else "")
           + f'<h1>{txt(bloc(sec, "h1"))}</h1>' + (f'<p class="chapo">{chapo}</p>' if chapo else "")
           + f'<span class="meta"><img src="{AUTEUR}" alt="" width="30" height="30">{meta_html}</span></div></div></section>\n')
    if art and "<img" not in art[:3000]:
        out += f'<div class="wrap"><figure class="ar-fig">{COUV}</figure></div>\n'
    return out


def h_art(sec, ctx):
    corps = blocs(sec, "div", "art-wrap")
    corps = interne(corps[0]) if corps else interne(bloc(sec, "div", "container"))
    if ctx.get("lead_pris"):
        corps = corps.replace(ctx["lead_pris"], "")
    corps = re.sub(r"<script\b.*?</script>", "", corps, flags=re.S)
    return f'<section class="ar-s"><div class="wrap"><div class="ar ar-c">{corps}</div></div></section>\n'


def h_ar_latest(sec, ctx):
    cs = blocs(sec, "a", "bl-card")[:3]
    return section(titre(sec, False) + grille([carte_blog(c) for c in cs])) if cs else ""


def h_faq(sec, ctx):
    qr = []
    for d in blocs(sec, "details"):
        q = brut(bloc(d, "summary"))
        rep = re.sub(r"<summary\b.*?</summary>", "", interne(d), flags=re.S)
        qr.append((q, sans_svg(rep).strip()))
    return faq(txt(bloc(sec, "h2")), qr) if qr else ""


def h_final_cta(sec, ctx):
    h = txt(bloc(sec, "h2"))
    a, b = couper_cta(h)
    return cta(a, b, bouton(sec))


def h_facts(sec, ctx):
    if not blocs(sec, "div", "facts-lead"):
        return h_generique(sec, ctx)
    return faits(sec, mots_accent(sec))


def mots_accent(sec):
    t = txt((blocs(sec, "h2") or ["<h2></h2>"])[0]).rstrip(" .?!")
    m = t.split(" ")
    return " ".join(m[-2:]) if len(m) > 4 else None


def h_who(sec, ctx):
    if not blocs(sec, "article", "sc-row"):
        return h_generique(sec, ctx)
    return situations_cartes(sec, mots_accent(sec))


def h_gov(sec, ctx):
    return gov_bento(sec, mots_accent(sec))


def h_siblings(sec, ctx):
    cs = []
    for a in blocs(sec, "a", "jv-tool"):
        win = bloc(a, "div", "jv-win")
        tf = txt(bloc(bloc(win, "div", "jv-bar"), "b"))
        reste = a.replace(win, "")
        em = blocs(reste, "em")
        cs.append((brut(bloc(reste, "b")), brut(bloc(reste, "span")), (txt(em[0]) if em else None, href(a)),
                   scene(355, 199, '<div class="maq">' + win + "</div>", titre=tf, label=tf)))
    if not cs:
        for a in blocs(sec, "a"):
            b = blocs(a, "b")
            if not b:
                continue
            sp = [s for s in blocs(a, "span") if txt(s)]
            cs.append((brut(b[0]), brut(sp[-1]) if sp else "", (None, href(a)), ""))
    if not cs:
        return h_generique(sec, ctx)
    return section(titre(sec) + cartes(cs))


def h_vn(sec, ctx):
    return voisins(sec)


def h_tterms(sec, ctx):
    return termes(sec, "dans les quatre langues" if "quatre langues" in sec else mots_accent(sec))


def h_tlaws(sec, ctx):
    lead = bloc(sec, "div", "tlaws-lead")
    cs = [(txt(bloc(x, "b")), brut(bloc(x, "p")), None, f'<span class="kv kv-ab"><b>{txt(bloc(x, "span", "ab"))}</b></span>') for x in blocs(sec, "div", "tlaw")]
    grille_cls = "cd c4" if len(cs) % 4 == 0 else "cd"
    return section(h2(txt(bloc(lead, "h2")), mots_accent(lead)) + f'<p class="intro">{brut(bloc(lead, "p"))}</p>' + cartes(cs).replace('class="cd"', f'class="{grille_cls}"', 1))


def h_compare(sec, ctx):
    tables = blocs(sec, "table")
    if not tables:
        return h_generique(sec, ctx)
    note = blocs(sec, "p", "compare-note")
    leg = blocs(sec, "div", "cmp-legend")
    leg_html = ('<p class="legende cmp-leg">' + "".join("<span>" + interne(x) + "</span>" for x in blocs(leg[0], "span")[::2]) + "</p>") if leg else ""
    fin = "".join(f'<p class="legende">{brut(p)}</p>' for p in blocs(sec, "p", "cmp-note"))
    return section(titre(sec) + (f'<p class="intro">{brut(note[0])}</p>' if note else "")
                   + "".join('<div class="tb">' + sans_svg(tb) + "</div>" for tb in tables) + leg_html + fin)


def h_temo(sec, ctx):
    lk = EX["co"]["lookup"]
    r0 = lk["rows"][0]
    vis = f'<div class="qt-v" data-ui><small><span>{esc(lk["q"])}</span> · <span>{esc(lk["l1"])}</span> · <span>{esc(lk["l2"])}</span></small><p>{esc(r0["a"])}</p><p class="qt-tr">{esc(r0["b"])}</p></div>'
    return (f'<section class="sec temo temo-ex"><div class="wrap"><figure class="qt">{vis}<div><blockquote>{interne(bloc(sec, "blockquote")).strip()}</blockquote>'
            f'<figcaption><span class="temo-lab">Exemple de cas d\'usage</span></figcaption></div></figure></div></section>\n')


def h_levels(sec, ctx):
    niv = [(str(i + 1), brut(bloc(x, "h3")), brut(bloc(x, "p"))) for i, x in enumerate(blocs(sec, "div", "lev"))]
    if not niv:
        return h_generique(sec, ctx)
    return section(titre(sec) + (f'<p class="intro">{premier_p(sec)}</p>' if premier_p(sec) else "") + tuiles(niv, "tl t4"))


def h_pillars(sec, ctx):
    items = []
    for x in blocs(sec, "div", "pillar"):
        h3 = bloc(x, "h3")
        sp = [s for s in blocs(h3, "span") if txt(s)]
        items.append((None, txt(sp[-1]) if sp else txt(h3), brut(bloc(x, "p"))))
    return section(titre(sec) + (f'<p class="intro">{premier_p(sec)}</p>' if premier_p(sec) else "") + tuiles(items, "tl txt"))


def h_trust(sec, ctx):
    lignes = blocs(sec, "div", "ledger-row")
    if not lignes:
        return h_generique(sec, ctx)
    items = []
    for r in lignes:
        tn = bloc(r, "span", "tn")
        sm = blocs(tn, "small")
        nom = txt(re.sub(r"<small\b.*?</small>", "", tn, flags=re.S))
        items.append((txt(bloc(r, "span", "ty")), nom, txt(sm[0]) if sm else ""))
    lead = (blocs(sec, "div", "trust-lead") or [sec])[0]
    tete_ = h2(txt(bloc(lead, "h2")), mots_accent(lead)) if blocs(lead, "h2") else ""
    ps = [p for p in blocs(lead, "p") if 'class="' not in p[:12]]
    return section(tete_ + (f'<p class="intro">{brut(ps[0])}</p>' if ps else "") + tuiles(items, "tl t4 tl-ledger"))


def h_gterm(sec, ctx):
    gauche = bloc(sec, "div", "gterm-grid")
    d = blocs(gauche, "div")[0]
    meta = blocs(d, "div", "gmeta")
    puces = "".join(f'<span class="pill">{txt(s)}</span>' for s in blocs(meta[0], "span")) if meta else ""
    note = blocs(sec, "div", "gnote")
    droite = ""
    if note:
        a = blocs(note[0], "a")
        droite = (f'<div class="gt-n"><p>{brut(bloc(note[0], "p"))}</p>'
                  + (f'<a class="lien" href="{href(a[0])}">{txt(a[0])}</a>' if a else "") + "</div>")
    return section(f'<div class="gt"><div>{h2(txt(bloc(d, "h2")))}<p class="gt-d">{brut(bloc(d, "p", "gdef"))}</p>'
                   f'<div class="puces">{puces}</div></div>{droite}</div>')


def h_gex(sec, ctx):
    row = bloc(sec, "div", "gex-row")
    cols = blocs(row, "div")
    langues = [txt(bloc(c, "i")) for c in cols]
    paras = [interne(bloc(c, "p")).strip() for c in cols]
    marque = re.search(r"<mark>(.*?)</mark>", paras[0])
    q = marque.group(1) if marque else ""
    ligne = f'<div style="--i:0"><p>{paras[0]}</p><p>{paras[1] if len(paras) > 1 else ""}</p></div>'
    carte = (f'<div class="cr cr-frag cr-chst">{A.chnell(q, langues[0], langues[1] if len(langues) > 1 else "", "", ligne)}</div>')
    src = blocs(sec, "p", "gsrc")
    return section(titre(sec, False) + scene(1176, 330, carte, titre="CHnell", label="Fast lookup CHnell")
                   + (f'<p class="legende">{brut(src[0])}</p>' if src else ""))


def h_hc(sec, ctx):
    nav = blocs(sec, "nav", "hc-side")
    menu = ""
    if nav:
        n = nav[0]
        menu = '<nav class="hc-nav" aria-label="Rubriques du centre d\'aide">'
        retour = blocs(n, "a", "hc-back")
        if retour:
            menu += f'<a class="hc-retour" href="{href(retour[0])}">{txt(retour[0])}</a>'
        for bloc_t in re.split(r'(?=<p class="hc-side-t">)', n):
            ts = blocs(bloc_t, "p", "hc-side-t")
            if not ts:
                continue
            menu += f'<p>{txt(ts[0])}</p><ul>' + "".join(f'<li><a href="{href(a)}">{txt(a)}</a></li>' for a in blocs(bloc_t, "a") if "hc-back" not in a[:40]) + "</ul>"
        menu += "</nav>"
    main = (blocs(sec, "div", "hc-main") or [sec])[0]
    h1 = blocs(main, "h1")
    intro = blocs(main, "p", "hc-intro")
    qr = []
    for d in blocs(main, "details"):
        rep = re.sub(r"<summary\b.*?</summary>", "", interne(d), flags=re.S)
        qr.append(f'<details><summary>{brut(bloc(d, "summary"))}</summary><div class="r">{sans_svg(rep).strip()}</div></details>')
    reste = main
    for x in blocs(main, "details") + h1 + intro + blocs(main, "div", "faq-list"):
        reste = reste.replace(x, "")
    reste_txt = "".join(f"<p>{brut(p)}</p>" for p in blocs(reste, "p") if txt(p))
    return (f'<section class="sec hc-s"><div class="wrap hc-g">{menu}<div class="hc-m">'
            + (f'<h1 class="h1">{txt(h1[0])}</h1>' if h1 else "")
            + (f'<p class="intro">{brut(intro[0])}</p>' if intro else "")
            + f'<div class="fq-l">{"".join(qr)}</div>{reste_txt}</div></div></section>\n')


def h_tdemo(sec, ctx):
    zone = "".join(blocs(sec, "div", "cx-ex")) + bloc(sec, "div", attr='id="cx"')
    ctx["demo"] = True
    return section(scene(1176, 720, f'<div class="cx-zone">{zone}</div>', titre="Corrext", label="Démonstration de l'interface Corrext"), "sec sec-st", "demo")


def h_glist(sec, ctx):
    tete_ = bloc(sec, "div", "sec-head")
    th = "".join(f"<th>{txt(s)}</th>" for s in blocs(bloc(sec, "div", "ghead"), "span"))
    lignes = []
    for a in blocs(sec, "a", "grow2"):
        cel = [f'<td><a href="{href(a)}">{txt(bloc(a, "b"))}</a></td>'] + [f"<td>{txt(s)}</td>" for s in blocs(a, "span") if 'class="' in s[:14]]
        lignes.append("<tr>" + "".join(cel) + "</tr>")
    return section(h2(txt(bloc(tete_, "h2"))) + f'<p class="intro">{brut(bloc(tete_, "p"))}</p>'
                   + f'<div class="tb tb-g"><table><thead><tr>{th}</tr></thead><tbody>{"".join(lignes)}</tbody></table></div>')


def h_rcol(sec, ctx):
    cs = []
    for a in [x for x in blocs(sec, "a") if "<b>" in x]:
        i_ = blocs(a, "i")
        if not blocs(a, "span"):
            continue
        texte = brut(bloc(a, "span")) + (f'</p><p class="cd-meta">{txt(i_[0])}' if i_ else "")
        cs.append((brut(bloc(a, "b")), texte, (None, href(a)), ""))
    return section(titre(sec) + (f'<p class="intro">{premier_p(sec)}</p>' if premier_p(sec) else "") + cartes(cs))


def h_elist(sec, ctx):
    cs = []
    for a in blocs(sec, "a", "ecard"):
        ps = blocs(a, "p")
        go = blocs(a, "span", "go")
        meta = [p for p in ps if 'class="meta"' in p[:20]]
        texte = brut(ps[0]) + (f'</p><p class="cd-meta">{txt(meta[0])}' if meta else "")
        cs.append((brut(bloc(a, "h3")), texte, (txt(go[0]) if go else None, href(a)), ""))
    return section(titre(sec, False) + (f'<p class="intro">{premier_p(sec)}</p>' if premier_p(sec) else "") + cartes(cs))


def h_ac(sec, ctx):
    out = []
    for an in blocs(sec, "section", "ac-annee"):
        h = bloc(an, "h2")
        em = blocs(h, "em")
        annee = txt(re.sub(r"<em>.*?</em>", "", h, flags=re.S))
        tete_ = f'<h2 class="h2">{annee} <em>{txt(em[0])}</em></h2>' if em else f'<h2 class="h2">{annee}</h2>'
        items = []
        for it in blocs(an, "article", "ac-item"):
            img = re.search(r'<img [^>]*src="([^"]+)"', it)
            meta = bloc(it, "p", "ac-meta")
            date = txt(bloc(meta, "time"))
            cat = [txt(s) for s in blocs(meta, "span")]
            corps = (blocs(it, "div", "ac-corps") or [""])[0]
            texte = "".join(f"<p>{brut(p)}</p>" for p in blocs(corps, "p"))
            vis = f'<img src="{img.group(1)}" alt="" loading="lazy">' if img else COUV
            items.append(f'<article class="acl">{vis}<div><span class="meta"><time>{date}</time>'
                         + "".join(f"<span>{c}</span>" for c in cat) + f'</span><h3>{brut(bloc(it, "h3"))}</h3>{texte}</div></article>')
        out.append(section(tete_ + "".join(items)))
    return "".join(out)


def h_lf_all(sec, ctx):
    items = []
    for li in blocs(sec, "li"):
        en = blocs(li, "span", "en")
        nat = blocs(li, "span", "nat")
        nom = txt(re.sub(r"<span\b.*?</span>", "", li, flags=re.S))
        items.append(f'<div><b>{nom}</b>' + (f"<span>{txt(en[0])}</span>" if en else "") + (f"<em>{txt(nat[0])}</em>" if nat else "") + "</div>")
    intro = blocs(sec, "p", "intro")
    reste = [p for p in blocs(sec, "p") if 'class="intro"' not in p[:20]]
    return section(titre(sec) + (f'<p class="intro">{brut(intro[0])}</p>' if intro else "")
                   + "".join(f'<p class="para">{brut(p)}</p>' for p in reste) + f'<div class="lf-g">{"".join(items)}</div>')


def h_legal(sec, ctx):
    corps = (blocs(sec, "div", "container") or [sec])[0]
    return f'<section class="ar-s"><div class="wrap"><div class="ar ar-c">{sans_svg(interne(corps))}</div></div></section>\n'


def h_generique(sec, ctx):
    """Repli : titre, introduction, éléments répétés en tuiles ou en cartes, tableaux et listes."""
    out = titre(sec)
    p0 = premier_p(sec)
    if p0:
        out += f'<p class="intro">{p0}</p>'
    # Éléments répétés : la classe la plus fréquente parmi les blocs qui portent un titre court
    compte = {}
    for m in re.finditer(r'<(article|a|li|div)\b[^>]*class="([^"]+)"', sec):
        compte.setdefault((m.group(1), m.group(2)), 0)
        compte[(m.group(1), m.group(2))] += 1
    items = []
    for (tag, cl), n in sorted(compte.items(), key=lambda x: -x[1]):
        if n < 2:
            break
        bl = [b for b in blocs(sec, tag, cl.split()[0]) if re.search(r"<(h3|h4|b|strong)\b", b)]
        if len(bl) >= 2:
            for b in bl:
                t_ = re.search(r"<(h3|h4|b|strong)\b[^>]*>(.*?)</\1>", b, re.S)
                corps = b.replace(t_.group(0), "", 1)
                ps = blocs(corps, "p")
                texte = brut(ps[0]) if ps else brut(re.sub(r"<(ul|ol)\b.*?</\1>", "", interne(corps) if corps.startswith("<") else corps, flags=re.S))
                lien = (None, href(b)) if tag == "a" else None
                items.append((brut(t_.group(2)), texte, lien, ""))
            break
    if items:
        out += cartes(items) if any(i[2] for i in items) else tuiles([(None, a, b) for a, b, _l, _v in items], "tl txt" + (" t2" if len(items) in (2, 4) else ""))
    for tb in blocs(sec, "table"):
        out += '<div class="tb">' + sans_svg(tb) + "</div>"
    if not items:
        for p in blocs(sec, "p")[1:] if p0 else blocs(sec, "p"):
            if txt(p) and brut(p) != p0:
                out += f"<p class=\"para\">{brut(p)}</p>"
        for ul in blocs(sec, "ul"):
            out += '<ul class="liste">' + "".join(f"<li>{brut(li)}</li>" for li in blocs(ul, "li")) + "</ul>"
    return section(out) if out.strip() else ""


GESTION = {
    "thero": h_thero, "hc-hero": h_thero, "ar-head": h_ar_head, "art": h_art, "ar-latest": h_ar_latest,
    "faq": h_faq, "final-cta": h_final_cta, "facts": h_facts, "who": h_who, "gov": h_gov,
    "siblings": h_siblings, "vn": h_vn, "tterms": h_tterms, "tlaws": h_tlaws, "compare": h_compare,
    "temo": h_temo, "levels": h_levels, "pillars": h_pillars, "trust": h_trust, "gterm": h_gterm,
    "gex": h_gex, "hc": h_hc, "tdemo": h_tdemo, "legal": h_legal, "glist": h_glist, "rcol": h_rcol, "elist": h_elist, "ac": h_ac, "lf-all": h_lf_all,
}


def menu_de(P):
    if P.startswith(("corrext/", "securite-souverainete/", "niveaux-de-qualite/", "langues-et-formats/")):
        return "corrext"
    if P.startswith("lexmachina/"):
        return "lexmachina"
    if P.startswith(("solutions/", "traduction/")):
        return "solutions"
    if P.startswith(("ressources/", "aide/", "comparatif/")):
        return "ressources"
    return ""


def entete(P):
    import html as H
    src = (SOURCE_FR / P / "index.html").read_text(encoding="utf-8")
    titre_ = H.unescape(re.search(r"<title>(.*?)</title>", src, re.S).group(1)).strip()
    desc = H.unescape(re.search(r'<meta name="description" content="([^"]*)"', src).group(1)).strip()
    return f"<!--page\ntitle: {titre_}\ndescription: {desc}\nmenu: {menu_de(P)}\ngabarit: standard\n-->\n"


def scripts_demo(P):
    """Styles et scripts propres à la page source (démos interactives), repris tels quels."""
    src = (SOURCE_FR / P / "index.html").read_text(encoding="utf-8")
    tete_ = src[:src.index("</head>")]
    styles = "".join(f"<style>{s}</style>\n" for s in re.findall(r"<style>(.*?)</style>", tete_, re.S))
    corps = src[src.index("<body"):]
    scripts = "".join(f"<script>{s}</script>\n" for s in re.findall(r"<script>(.*?)</script>", corps, re.S))
    return styles, scripts


def composer(P):
    t = liens(charger(P), P)
    secs = sections(t)
    ctx = {"P": P, "t": t}
    arts = [s for s in secs if classes(s)[0] == "art"]
    if arts:
        ctx["art"] = arts[0]
    out, inconnus = [], []
    for sec in secs:
        cl = classes(sec)[0]
        f = GESTION.get(cl)
        if not f:
            inconnus.append(cl)
            f = h_generique
        out.append(f(sec, ctx))
    corps = "".join(out)
    if ctx.get("demo"):
        st, sc = scripts_demo(P)
        corps = st + corps + liens(sc, P)
    ecrire(P, entete(P), corps)
    return inconnus


def pages_manquantes():
    faites = {str(p.parent.relative_to(RACINE_TEST / "src/pages")) + "/" for p in (RACINE_TEST / "src/pages").rglob("index.html")}
    faites = {("" if x == "./" else x) for x in faites}
    toutes = []
    for f in sorted(SOURCE_FR.rglob("index.html")):
        P = str(f.parent.relative_to(SOURCE_FR)) + "/"
        P = "" if P == "./" else P
        if P in REDIRECTIONS or P in faites:
            continue
        toutes.append(P)
    return toutes


if __name__ == "__main__":
    cibles = sys.argv[1:] or pages_manquantes()
    bilan = {}
    for P in cibles:
        for cl in composer(P):
            bilan.setdefault(cl, []).append(P)
    print(len(cibles), "pages composées")
    for cl, ps in sorted(bilan.items()):
        print(f"  repli générique : {cl} ({len(ps)}) ex. {ps[0]}")
