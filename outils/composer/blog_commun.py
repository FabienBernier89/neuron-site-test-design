"""Cartes du blog (C17) : image réelle ou couverture typographique « NEUR.ON » du site actuel."""
from commun import *

COUV = '<span class="couv" aria-hidden="true">NEUR<span>.ON</span></span>'
AUTEUR = "{{ROOT}}assets/img/neuron-mark.png"


def visuel(c):
    img = re.search(r'<img [^>]*src="([^"]+)"', c)
    return f'<img src="{img.group(1)}" alt="" loading="lazy">' if img else COUV


def carte_blog(c):
    href = re.search(r'href="([^"]+)"', c).group(1)
    tag = blocs(c, "span", "bl-tag")
    date = blocs(c, "time")
    return (f'<a class="bl-c" href="{href}">{visuel(c)}'
            + (f'<span class="cat">{txt(tag[0])}</span>' if tag else "")
            + f'<h3>{brut(bloc(c, "h3"))}</h3><p class="x">{brut(bloc(c, "p"))}</p>'
            + (f'<span class="meta"><img src="{AUTEUR}" alt="" width="30" height="30"><time>{txt(date[0])}</time></span>' if date else "")
            + "</a>")


def grille(cartes_html):
    return '<div class="bl-g">' + "".join(cartes_html) + "</div>"
