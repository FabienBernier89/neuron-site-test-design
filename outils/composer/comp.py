"""Composants du site de test de design (catalogue de la tâche 2 du plan), en chaînes HTML."""

PAUSE = ('<button type="button" class="sim-pause" aria-pressed="false" aria-label="Mettre en pause la démonstration" data-libre>'
         '<svg class="ic-p" viewBox="0 0 10 10" aria-hidden="true"><path d="M2.5 1.5v7M7.5 1.5v7" stroke="currentColor" stroke-width="1.8" stroke-linecap="round"/></svg>'
         '<svg class="ic-l" viewBox="0 0 10 10" aria-hidden="true"><path d="M3 1.8v6.4L8.4 5z" fill="currentColor"/></svg></button>')


def scene(w, h, contenu, sim=None, titre="Corrext", curseur=True, label=""):
    """Scène C6 : panneau à dégradé, cadre, fenêtre. `sim` absent pour une scène statique."""
    attr_sim = f' data-sim="{sim}"' if sim else ""
    aria = f' role="img" aria-label="{label}"' if label and not sim else (f' aria-label="{label}"' if label else "")
    cur = '<span class="sim-cur" aria-hidden="true"></span>' if sim and curseur else ""
    return (f'<div class="ech" data-ech="{w}x{h}">'
            f'<div class="st"{attr_sim}{aria} style="width:{w}px;height:{h}px">'
            f'<div class="st-f"><div class="fen">'
            f'<div class="fen-b" aria-hidden="true"><i></i><i></i><i></i><span>{titre}</span></div>'
            f'<div class="fen-c" data-scene data-ui>{contenu}{cur}</div>'
            f'</div></div>{PAUSE if sim else ""}</div></div>')


def hero(n, s, lead="", bouton=None):
    d = ""
    if lead or bouton:
        d = '<div class="hero-d">' + (f"<p>{lead}</p>" if lead else "") + \
            (f'<a class="btn" href="{bouton[1]}">{bouton[0]}</a>' if bouton else "") + "</div>"
    return (f'<section class="hero">\n<div class="wrap hero-g">\n'
            f'<h1 class="h1"><span class="n">{n}</span> <span class="s">{s}</span></h1>\n{d}\n</div>\n</section>\n')


def section(contenu, cls="sec", ident=""):
    i = f' id="{ident}"' if ident else ""
    return f'<section class="{cls}"{i}><div class="wrap">\n{contenu}\n</div></section>\n'


def h2(texte, accent=None, cls="h2"):
    if accent and accent in texte:
        texte = texte.replace(accent, f"<em>{accent}</em>", 1)
    return f'<h2 class="{cls}">{texte}</h2>'


def ft(pill, titre, texte, visuel, lien=None, inv=False, liste=None, niveau="h3"):
    p = f'<span class="pill">{pill}</span>' if pill else ""
    ul = ("<ul>" + "".join(f"<li>{x}</li>" for x in liste) + "</ul>") if liste else ""
    a = f'<a class="lien" href="{lien[1]}">{lien[0]}</a>' if lien else ""
    return (f'<div class="ft{" inv" if inv else ""}"><div class="ft-t">{p}<{niveau} class="h3s">{titre}</{niveau}>'
            f'<p>{texte}</p>{ul}{a}</div>{visuel}</div>')


def tuiles(items, cls="tl"):
    """items : (chiffre ou None, libellé, texte)."""
    out = []
    for n, b, p in items:
        num = f'<span class="n">{n}</span>' if n else ""
        corps = (f"<b>{b}</b>" if b else "") + (f"<p>{p}</p>" if p else "")
        out.append(f"<div>{num}<div>{corps}</div></div>" if n else f"<div>{corps}</div>")
    return f'<div class="{cls}">' + "".join(out) + "</div>"


def bento(grande, petites):
    """grande : dict(pill, titre, texte, lien) ; petites : (libellé, texte, classe en plus)."""
    g = grande
    t = '<div class="bt"><div class="bt-g">'
    if g.get("pill"):
        t += f'<span class="pill">{g["pill"]}</span>'
    t += f'{g["titre"]}'
    if g.get("texte"):
        t += f'<p>{g["texte"]}</p>'
    if g.get("lien"):
        t += f'<a class="lien" href="{g["lien"][1]}">{g["lien"][0]}</a>'
    t += "</div>"
    for b, p, extra in petites:
        tete = b if b.startswith("<") else f"<b>{b}</b>"
        t += f'<div class="bt-p{(" " + extra) if extra else ""}">{tete}' + (f"<p>{p}</p>" if p else "") + "</div>"
    return t + "</div>"


def cartes(items):
    """items : (titre, texte, lien (libellé, href) ou None, visuel ou '')."""
    out = []
    for b, p, lien, v in items:
        vis = f'<div class="v">{v}</div>' if v else ""
        corps = f"{vis}<b>{b}</b>" + (f"<p>{p}</p>" if p else "")
        if lien and lien[0]:
            out.append(f'<a href="{lien[1]}">{corps}<span class="lien">{lien[0]}</span></a>')
        elif lien:
            out.append(f'<a href="{lien[1]}">{corps}</a>')
        else:
            out.append(f"<div>{corps}</div>")
    return '<div class="cd">' + "".join(out) + "</div>"


def bande(phrase, bouton):
    return f'<div class="bd"><p>{phrase}</p><a class="btn" href="{bouton[1]}">{bouton[0]}</a></div>'


def cta(l1, l2, bouton):
    return (f'<section class="cta"><div class="wrap"><h2><span class="l1">{l1}</span> <span class="l2">{l2}</span></h2>'
            f'<a class="btn" href="{bouton[1]}">{bouton[0]}</a></div></section>\n')


def faq(titre, qr):
    d = "".join(f'<details><summary>{q}</summary><div class="r">{r}</div></details>' for q, r in qr)
    return f'<section class="sec"><div class="wrap fq">{h2(titre)}<div>{d}</div></div></section>\n'


def dist(intro, items):
    lis = "".join(f"<li><b>{b}</b>" + (f"<span>{s}</span>" if s else "") + "</li>" for b, s in items)
    return f'<section class="sec dist"><div class="wrap"><p class="i">{intro}</p><ul class="d{len(items)}">{lis}</ul></div></section>\n'


# Gabarits d'interface des scènes (libellés de l'application, textes remplis par sim.js ou à la main)
def ui_traduction(puces, src="", out="", lg_src="French", lg_out="English"):
    """puces : liste de (libellé, attributs, actif)."""
    ch = "".join(f'<span class="mx-chip{" on" if on else ""}"{a}>{l}</span>' for l, a, on in puces)
    return (f'<div class="mx"><div class="mx-bar">{ch}</div><div class="mx-g">'
            f'<div class="mx-p"><small>{lg_src}</small><p class="mx-src">{src}</p></div>'
            f'<div class="mx-p"><small class="mx-lg">{lg_out}</small><p class="mx-out">{out}</p></div></div></div>')


def ui_moteurs(avis=""):
    a = f'<div class="mx-avis">{avis}</div>' if avis else ""
    return ('<div class="mx"><div class="mx-bar"><span class="mx-chip hs">Highly sensitive</span></div>'
            '<ul class="mx-l"><li class="suisse on"><i></i>LexMachina<span>Suisse</span></li>'
            '<li class="tiers"><i></i>DeepL Pro</li><li class="tiers"><i></i>Azure OpenAI GPT</li></ul>' + a + "</div>")
