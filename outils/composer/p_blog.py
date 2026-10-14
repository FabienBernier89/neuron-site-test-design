"""Liste du blog : section « Guides » (les billets éditoriaux et un lien vers les guides), puis « Actualités ».
Les textes de la page actuelle sont repris tels quels ; les intitulés de section viennent de E-blog.json."""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))  # outils/ : « from contenus import texte »
from contenus import texte
from blog_commun import *

P = "ressources/blog/"
# Billets éditoriaux : le premier est la vedette de la page actuelle, les deux autres ouvrent sa grille
BILLETS = ("traduire-contrat-droit-suisse", "comprendre-devis-traduction-juridique", "secret-professionnel-outils-traduction")


def slug(carte):
    return re.search(r'href="[^"]*/blog/([^/"]+)/"', carte).group(1)


t = liens(charger(P), P)
out = []
out.append('<section class="bl-h"><h1 class="h1"><span class="n">Blog.</span> <span class="s">Ce qu\'il faut savoir pour traduire le droit suisse</span></h1></section>\n')
fe = bloc(t, "a", "bl-feat-card")
meta = bloc(fe, "div", "bl-meta")
ms = [txt(s) for s in blocs(meta, "span") if "bl-cat" not in s[:25]]
feat = (f'<a class="bl-f" href="{re.search(r"href=\"([^\"]+)\"", fe).group(1)}">{visuel(fe)}<div>'
        f'<span class="cat">{txt(bloc(meta, "span", "bl-cat"))}</span><h3>{brut(bloc(fe, "h2"))}</h3>'
        f'<p class="x">{brut(bloc(bloc(fe, "div", "bl-feat-body"), "p"))}</p>'
        f'<span class="meta"><img src="{AUTEUR}" alt="" width="30" height="30"><span>{ms[1]}</span><time>{ms[0]}</time></span></div></a>')
cs = blocs(bloc(t, "section", "bl-list"), "a", "bl-card")[1:]  # la première carte de la liste est la vedette
assert slug(fe) == BILLETS[0], slug(fe)
guides = [c for c in cs if slug(c) in BILLETS]
actus = [c for c in cs if slug(c) not in BILLETS]
assert [slug(c) for c in guides] == list(BILLETS[1:]), [slug(c) for c in guides]
out.append(section(h2(texte("ressources/blog.guides.titre")) + f'<p class="intro">{texte("ressources/blog.guides.intro")}</p>'
                   + feat + grille([carte_blog(c) for c in guides])
                   + f'<p class="bl-plus"><a class="lien" href="{{{{ROOT}}}}fr/ressources/guides/">{texte("ressources/blog.guides.lien")}</a></p>',
                   "sec bl-guides"))
out.append(section(h2(texte("ressources/blog.actualites.titre")) + f'<p class="intro">{texte("ressources/blog.actualites.intro")}</p>'
                   + grille([carte_blog(c) for c in actus]), "sec bl-a"))
ac = bloc(t, "a", "bl-actu-card")
li = bloc(t, "section", "bl-li")
btn = bloc(li, "a", "btn")
out.append(section(f'<p class="bl-plus"><a class="lien" href="{re.search(r"href=\"([^\"]+)\"", ac).group(1)}">{txt(bloc(ac, "b"))}</a></p>'
                   + bande(txt(bloc(li, "h2")), (txt(btn), re.search(r'href="([^"]+)"', btn).group(1)))))
out.append(cta_section(t, "Ces sujets se voient mieux"))
ecrire(P, entete_existant(P), "".join(out))
print("blog écrit")
