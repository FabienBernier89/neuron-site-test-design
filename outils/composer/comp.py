"""Composants du site de test de design (catalogue de la tâche 2 du plan), en chaînes HTML."""

# Jauge discrète en bas de la scène : déroulé du cycle de l'animation (remplie par sim.js)
JAUGE = '<span class="sim-jauge" aria-hidden="true"><i></i></span>'


def scene(w, h, contenu, sim=None, titre="Corrext", curseur=True, label=""):
    """Scène C6 : panneau à dégradé, cadre, fenêtre. `sim` absent pour une scène statique.
    Nom accessible (`label`) : une scène statique est une image (role="img") ; une scène animée garde ses contenus
    lisibles, c'est un groupe nommé (role="group" : aria-label n'est pas admis sur un div sans rôle)."""
    attr_sim = f' data-sim="{sim}"' if sim else ""
    aria = f' role="{"group" if sim else "img"}" aria-label="{label}"' if label else ""
    cur = '<span class="sim-cur" aria-hidden="true"></span>' if sim and curseur else ""
    return (f'<div class="ech" data-ech="{w}x{h}">'
            f'<div class="st"{attr_sim}{aria} style="width:{w}px;height:{h}px">'
            f'<div class="st-f"><div class="fen">'
            f'<div class="fen-b" aria-hidden="true"><i></i><i></i><i></i><span>{titre}</span></div>'
            f'<div class="fen-c" data-scene data-ui>{contenu}{cur}</div>'
            f'</div></div>{JAUGE if sim else ""}</div></div>')


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


NOMS_OUTILS = ("Traduction texte et document", "Gestion de projet", "Fast lookup CHnell")
PETITS_MOTS = {"le", "la", "les", "du", "de", "des", "en", "au", "aux", "vers", "un", "une"}


def accent_fin(texte, n=2):
    """Règle commune de l'accent italique (generique.mots_accent) : les derniers mots d'un titre de plus de 4 mots,
    ponctuation finale exclue. None pour un titre court ou balisé."""
    if "<" in texte:
        return None
    fin = texte.rstrip(" .?!:\u00a0\u202f")
    mots = fin.split(" ")
    if len(mots) <= 4:
        return None
    for nom in NOMS_OUTILS:  # un nom d'outil en fin de titre reste entier (« sur Gestion de projet »)
        if fin.endswith(" " + nom):
            return nom
    # trois mots quand l'avant-dernier est un petit mot (« droit du travail », « l'allemand vers l'anglais ») sauf après
    # une conjonction (« et la souveraineté » reste « la souveraineté »), ou quand c'est une conjonction (« éditeurs et
    # LegalTechs », jamais « et LegalTechs » seul)
    if n == 2 and ((mots[-2].lower() in PETITS_MOTS and mots[-3].lower() not in ("et", "ou"))
                   or mots[-2].lower() in ("et", "ou")):
        n = 3
    return " ".join(mots[-n:])


def h2(texte, accent=None, cls="h2"):
    """Titre de section. Sans accent donné, la règle commune s'applique (audit design du 2026-10-23 : un titre de plus
    de 4 mots porte l'accent italique sur ses derniers mots) ; accent=False : titre sans accent."""
    if accent is None and "<em>" not in texte:
        auto = accent_fin(texte)
        if auto:
            i = texte.rindex(auto)  # dernière occurrence : la fin du titre
            texte = texte[:i] + f"<em>{auto}</em>" + texte[i + len(auto):]
    elif accent and accent in texte:
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


def frise_niveaux(items):
    """Niveaux de qualité 1 à 4 en frise (arbitrage de Fabien du 2026-10-23, option B : une progression se lit comme les
    étapes des pages outils) ; items : (numéro, titre, texte). Les chiffres clés gardent leurs tuiles (option A)."""
    return '<ol class="fr fr-nv">' + "".join(f'<li><span class="fr-n">{n}</span><h3>{b}</h3><p>{p}</p></li>' for n, b, p in items) + "</ol>"


def bento(grande, petites):
    """grande : dict(pill, titre, texte, lien, visuel) ; petites : (libellé, texte, classe en plus)."""
    g = grande
    t = '<div class="bt"><div class="bt-g">'
    if g.get("pill"):
        t += f'<span class="pill">{g["pill"]}</span>'
    t += f'{g["titre"]}'
    if g.get("texte"):
        t += f'<p>{g["texte"]}</p>'
    if g.get("lien"):
        t += f'<a class="lien" href="{g["lien"][1]}">{g["lien"][0]}</a>'
    if g.get("visuel"):  # écran animé en bas de la grande tuile (page Corrext, Fabien, 2026-10-23)
        t += f'<div class="bt-v">{g["visuel"]}</div>'
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
    """Bandeau des distinctions. Une distinction sans sous-titre passe sur deux lignes, coupée au dernier espace
    (retour de Fabien du 2026-10-15 : aucune tuile sur une seule ligne)."""
    def deux_lignes(b):
        i = b.rfind(" ")
        return b if i < 0 else b[:i] + "<br>" + b[i + 1:]
    lis = "".join(f"<li><b>{b if s else deux_lignes(b)}</b>" + (f"<span>{s}</span>" if s else "") + "</li>" for b, s in items)
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
