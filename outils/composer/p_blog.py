from blog_commun import *
P = "ressources/blog/"
t = liens(charger(P), P)
out = []
out.append('<section class="bl-h"><h1 class="h1"><span class="n">Blog.</span> <span class="s">Ce qu\'il faut savoir pour traduire le droit suisse</span></h1></section>\n')
fe = bloc(t, "a", "bl-feat-card")
meta = bloc(fe, "div", "bl-meta")
ms = [txt(s) for s in blocs(meta, "span") if "bl-cat" not in s[:25]]
feat = (f'<a class="bl-f" href="{re.search(r"href=\"([^\"]+)\"", fe).group(1)}">{visuel(fe)}<div>'
        f'<span class="cat">{txt(bloc(meta, "span", "bl-cat"))}</span><h2>{brut(bloc(fe, "h2"))}</h2>'
        f'<p class="x">{brut(bloc(bloc(fe, "div", "bl-feat-body"), "p"))}</p>'
        f'<span class="meta"><img src="{AUTEUR}" alt="" width="30" height="30"><span>{ms[1]}</span><time>{ms[0]}</time></span></div></a>')
cs = blocs(bloc(t, "section", "bl-list"), "a", "bl-card")
out.append(section(feat + grille([carte_blog(c) for c in cs[1:10]]), "sec bl-s"))
ac = bloc(t, "a", "bl-actu-card")
li = bloc(t, "section", "bl-li")
btn = bloc(li, "a", "btn")
out.append(section(f'<p class="bl-plus"><a class="lien" href="{re.search(r"href=\"([^\"]+)\"", ac).group(1)}">{txt(bloc(ac, "b"))}</a></p>'
                   + bande(txt(bloc(li, "h2")), (txt(btn), re.search(r'href="([^"]+)"', btn).group(1)))))
out.append(cta_section(t, "Ces sujets se voient mieux"))
ecrire(P, entete_existant(P), "".join(out))
print("blog écrit")
