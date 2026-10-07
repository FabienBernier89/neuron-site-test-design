"""Sections récurrentes des pages métier, domaine et paire."""
from commun import *


def gov_bento(t, accent):
    gv = bloc(t, "section", "gov")
    box = bloc(gv, "div", "gov-box")
    a = blocs(box, "a", "feat-link")
    pas = []
    for s in blocs(bloc(gv, "div", "gov-steps"), "span"):
        if "<b>" not in s[:12]:
            continue
        pas.append((brut(bloc(s, "b")), brut(re.sub(r"<b>.*?</b>", "", interne(s), flags=re.S)), ""))
    if len(pas) == 3:
        pas[-1] = (pas[-1][0], pas[-1][1], "bt-l")
    g = {"titre": h2(txt(bloc(box, "h2")), accent, "h3s"), "texte": brut(bloc(box, "p"))}
    if a:
        g["lien"] = (txt(a[0]), re.search(r'href="([^"]+)"', a[0]).group(1))
    return section(bento(g, pas))


def faits(t, accent, cls="tl txt t2"):
    fa = bloc(t, "section", "facts")
    lead = bloc(fa, "div", "facts-lead")
    items = [(None, txt(bloc(f, "b")), brut(bloc(f, "p"))) for f in blocs(fa, "div", "fact")]
    return section(h2(txt(bloc(lead, "h2")), accent) + f'<p class="intro">{brut(bloc(lead, "p"))}</p>' + tuiles(items, cls))


def situations_cartes(t, accent):
    wh = bloc(t, "section", "who")
    return section(h2(txt(bloc(wh, "h2")), accent) + cartes([(brut(bloc(r, "h3")), brut(bloc(r, "p")), None, "") for r in blocs(wh, "article", "sc-row")]))


def termes(t, accent):
    tt = bloc(t, "section", "tterms")
    hh = bloc(tt, "h2")
    ps = [p for p in blocs(tt, "p") if "class=" not in p[:12]]
    intro = f'<p class="intro">{brut(ps[0])}</p>' if ps else ""
    tab = sans_svg(bloc(tt, "table"))
    notes = "".join(f'<p class="legende">{brut(p)}</p>' for p in blocs(tt, "p") if 'class="' in p[:20])
    return section(h2(txt(hh), accent) + intro + '<div class="tb">' + tab + "</div>" + notes)


def voisins(t):
    vn = blocs(t, "section", "vn")
    if not vn:
        return ""
    vn = vn[0]
    cs = []
    for a in blocs(vn, "a", "vn-card"):
        term = (blocs(a, "span", "vn-term") or [""])[0]
        kv = "".join(f"<span><i>{txt(bloc(s, 'i'))}</i><b>{txt(bloc(s, 'b'))}</b></span>" for s in blocs(term, "span")[1:] if "<i>" in s) if term else ""
        reste = a.replace(term, "")
        em = blocs(reste, "em")
        cs.append((txt(bloc(reste, "b", "vn-t")), brut(bloc(reste, "span", "vn-d")),
                   (txt(em[0]) if em else None, re.search(r'href="([^"]+)"', a).group(1)), f'<span class="kv">{kv}</span>' if kv else ""))
    return section(h2(txt(bloc(vn, "h2"))) + cartes(cs))


def scene_statique(contenu, titre, h=420):
    return section(scene(1176, h, contenu, titre=titre, label=titre), "sec sec-st")
