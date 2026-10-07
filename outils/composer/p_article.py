from blog_commun import *
P = "ressources/blog/traduire-contrat-droit-suisse/"
t = liens(charger(P), P)
out = []
hd = bloc(t, "section", "ar-head")
meta = bloc(hd, "div", "ar-meta")
spans = [txt(s) for s in blocs(meta, "span") if "ar-cat" not in s[:25]]
corps = interne(bloc(t, "div", "art-wrap"))
lead = bloc(corps, "p", "art-lead")
corps = corps.replace(lead, "")
out.append(f'<section class="ar-h"><div class="wrap"><div class="ar"><span class="cat">{txt(bloc(meta, "span", "ar-cat"))}</span>'
           f'<h1>{txt(bloc(hd, "h1"))}</h1><p class="chapo">{brut(lead)}</p>'
           f'<span class="meta"><img src="{AUTEUR}" alt="" width="30" height="30"><span>{spans[0]}</span><time>{spans[1]}</time><span>{spans[2]}</span></span>'
           f'</div></div></section>\n')
out.append(f'<div class="wrap"><figure class="ar-fig">{COUV}</figure></div>\n')
out.append(f'<section class="ar-s"><div class="wrap"><div class="ar ar-c">{corps}</div></div></section>\n')
out.append(faq_section(t))
la = bloc(t, "section", "ar-latest")
out.append(section(h2(txt(bloc(la, "h2"))) + grille([carte_blog(c) for c in blocs(la, "a", "bl-card")[:3]])))
out.append(cta_section(t, "Voir la terminologie suisse à l'œuvre"))
ecrire(P, entete_existant(P), "".join(out))
print("article écrit")
