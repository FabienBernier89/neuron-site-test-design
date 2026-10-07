from commun import *
P = "lexmachina/"
t = liens(charger(P), P)
out = []
th = bloc(t, "section", "thero")
out.append(hero("LexMachina.", "Le moteur qui connaît les lois qu'il traduit", brut(bloc(th, "p", "lead")), ("Demander une démo", C)))
# Comparaison « quatre caractères » animée (S4)
nl = bloc(t, "section", "nlex")
h, p = tete(nl)
srcp = bloc(bloc(nl, "div", "nlex-src"), "p")
lb = txt(bloc(srcp, "span", "src-lb"))
phrase = brut(re.sub(r'<span class="src-lb">.*?</span>', "", srcp, flags=re.S))
cartes_ = []
for i, c in enumerate(blocs(nl, "div", "nlex-card")):
    eng = txt(bloc(c, "div", "eng"))
    pp = bloc(c, "p")
    cartes_.append(f'<div class="mx-p"><small>{eng}</small><p class="q4-out" data-q4="{i}" lang="en">{interne(pp).strip()}</p></div>')
ui = (f'<div class="mx q4"><div class="mx-p q4-src"><small>{lb}</small><p>{phrase}</p></div>'
      f'<div class="mx-g">{"".join(cartes_)}</div></div>')
titre_fen = txt(bloc(nl, "span", "nlex-tag"))
out.append(section(h2(h, "quatre caractères") + f'<p class="intro">{p}</p>'
                   + scene(1176, 420, ui, sim="quatre", titre=titre_fen, curseur=False, label="Comparaison des sorties LexMachina et DeepL Pro")
                   + f'<p class="legende">{brut(bloc(nl, "p", "nlex-note"))}</p><p class="legende">{brut(bloc(nl, "p", "nlex-cap"))}</p>'))
# Ce qu'est LexMachina : tuiles chiffres, puis cartes à puces
sp = bloc(t, "section", "nlspec")
h, p = tete(sp)
kpi = [(txt(bloc(k, "b")), txt(bloc(k, "span")), brut(bloc(k, "p"))) for k in blocs(sp, "div", "nls-k")]
ct = []
for k in blocs(sp, "div", "nls-t"):
    titre = txt(blocs(bloc(k, "h3"), "span")[-1])
    puces = "".join(f'<span class="pill">{txt(s)}</span>' for s in blocs(bloc(k, "div", "nls-chips"), "span"))
    ct.append(f'<div><b>{titre}</b><p>{brut(bloc(k, "p"))}</p><div class="puces">{puces}</div></div>')
out.append(section(h2(h, "exactement") + f'<p class="intro">{p}</p>' + tuiles(kpi, "tl t4")
                   + '<div class="cd cd-sp">' + "".join(ct) + "</div>"
                   + f'<p class="legende">{brut(bloc(sp, "p", "nls-foot"))}</p>'))
# Piliers
pi = bloc(t, "section", "pillars")
h, p = tete(pi)
out.append(section(h2(h, "un modèle spécialisé") + f'<p class="intro">{p}</p>'
                   + tuiles([(None, txt(blocs(bloc(x, "h3"), "span")[-1]), brut(bloc(x, "p"))) for x in blocs(pi, "div", "pillar")], "tl txt")))
# Pour aller plus loin : cartes avec valeurs clés
vn = bloc(t, "section", "vn")
cs = []
for a in blocs(vn, "a", "vn-card"):
    kv = "".join(f"<span><i>{txt(bloc(s, 'i'))}</i><b>{txt(bloc(s, 'b'))}</b></span>" for s in blocs(bloc(a, "span", "vn-kv"), "span")[1:] if "<i>" in s)
    cs.append((txt(bloc(a, "b", "vn-t")), brut(bloc(a, "span", "vn-d")), (txt(bloc(a, "em")), re.search(r'href="([^"]+)"', a).group(1)),
               f'<span class="kv">{kv}</span>'))
out.append(section(h2(txt(bloc(vn, "h2"))) + cartes(cs)))
out.append(faq_section(t))
out.append(cta_section(t, "Jugez le moteur"))
ecrire(P, entete_existant(P), "".join(out))
print("lexmachina écrite")
