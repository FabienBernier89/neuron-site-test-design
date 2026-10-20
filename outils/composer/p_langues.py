"""Page Langues et formats, refonte validée par Fabien le 2026-10-20 (audit du même jour) :
hero ; les langues en un bloc (les quatre natives en évidence, les autres en liste compacte, la note sur les moteurs) ;
les conventions suisses (« Pourquoi traduire en Suisse » et le tableau des sigles réunis, sans doublon) ; les formats
(chiffres en tuiles, écran animé du dépôt et « la mise en page revient comme elle est partie », faits courts) ;
pour aller plus loin ; FAQ ; appel. Textes de la V1 mot pour mot ; chiffres des tuiles dans contenus-v2/R-niveaux.json.

    cd outils/composer && python3 p_langues.py
"""
from paire_modele import *
import generique

P = "langues-et-formats/"
t = liens(charger(P), P)


def href(a):
    return re.search(r'href="([^"]+)"', a).group(1)


def langues():
    na = bloc(t, "section", "lf-native")
    nat = "".join(f'<div class="lf-n"><p class="lf-nb"><b>{txt(bloc(x, "b"))}</b><span>{txt(bloc(x, "span", "en"))}</span></p><p>{brut(bloc(x, "p"))}</p></div>'
                  for x in blocs(na, "div", "lf-nat"))
    al = bloc(t, "section", "lf-all")
    ps = blocs(al, "p")
    autres = "".join(f'<li>{txt(re.sub(r"<span.*", "", li, flags=re.S))}<span>{txt(bloc(li, "span", "en"))}</span></li>'
                     for li in blocs(al, "li") if 'class="nat"' not in li)
    return section(h2(txt(bloc(na, "h2")), "son droit") + f'<p class="intro">{brut(bloc(bloc(na, "div", "sec-head"), "p"))}</p>'
                   + f'<div class="lf-ns">{nat}</div>'
                   + f'<p class="pa-st">{txt(bloc(al, "h2"))}</p><p class="lf-i">{brut(ps[0])}</p><ul class="lf-l">{autres}</ul>'
                   + f'<p class="lf-note">{brut(ps[1])}</p>')


def conventions():
    gv = bloc(t, "section", "gov")
    box = bloc(gv, "div", "gov-box")
    a = blocs(box, "a", "feat-link")[0]
    regles = [(txt(bloc(x, "b")), brut(re.sub(r"<b>.*?</b>", "", bloc(x, "span"), flags=re.S))) for x in blocs(bloc(gv, "div", "gov-steps"), "div") if "gov-steps" not in x[:30]]
    rangs = "".join(f'<div><h3>{b.rstrip(".")}</h3><p>{p}</p></div>' for b, p in regles if not b.startswith("Abréviations"))
    cp = bloc(t, "section", "compare")
    tab = bloc(cp, "table")
    entetes = [txt(x) for x in re.findall(r"<th[^>]*>(.*?)</th>", bloc(tab, "thead"), re.S)]
    lignes = "".join("<tr>" + "".join(
        (f'<th scope="row" class="pa-s" data-m="{e}">{txt(v)}</th>' if j == 0 else f'<td class="pa-n" data-m="{e}"><span class="pa-ref">{txt(v)}</span></td>')
        for j, (e, v) in enumerate(zip(entetes, re.findall(r"<t[hd][^>]*>(.*?)</t[hd]>", tr, re.S)))) + "</tr>"
        for tr in blocs(bloc(tab, "tbody"), "tr"))
    tete = "".join(f'<th scope="col" class="{"pa-s" if j == 0 else "pa-n"}">{e}</th>' for j, e in enumerate(entetes))
    return section(h2(txt(bloc(box, "h2")), "en italien") + f'<p class="intro">{brut(bloc(box, "p"))}</p>'
                   + f'<div class="lf-r">{rangs}</div>'
                   + f'<div class="lf-s"><h3 class="lf-sh">{txt(bloc(cp, "h2"))}</h3><p class="lf-i">{brut(bloc(cp, "p", "compare-note"))}</p>'
                   + f'<div class="pa-tw"><table class="pa-t"><thead><tr>{tete}</tr></thead><tbody>{lignes}</tbody></table></div>'
                   + f'<p class="legende">{txt(bloc(bloc(cp, "div", "cmp-legend"), "span"))}</p></div>'
                   + f'<p class="lf-lien"><a class="lien" href="{href(a)}">{txt(a)}</a></p>')


def formats():
    fa = bloc(t, "section", "facts")
    lead = bloc(fa, "div", "facts-lead")
    F = {txt(bloc(f, "b")): brut(bloc(f, "p")) for f in blocs(fa, "div", "fact")}
    tuiles_ = [("formats", "Formats acceptés"), ("fichiers", "Nombre de fichiers"), ("taille", "Taille maximale"), ("caracteres", "Texte collé")]
    def chiffre(n):  # « 25 Fichiers » : unité accolée en petit, comme les chiffres de l'accueil
        m = re.fullmatch(r"([\d']+) (.+)", n)
        return f'{m.group(1)} <span class="u">{m.group(2)}</span>' if m else n
    tl = tuiles([(chiffre(esc(texte(f"langues.tuile.{c}"))), None, F[f]) for c, f in tuiles_], "tl t4")
    ly = bloc(t, "section", "lf-layout")
    lien_ = bloc(ly, "a", "feat-link")
    puces = "".join(f'<li><span class="pa-ck">{COCHE}</span>{txt(li)}</li>' for li in blocs(bloc(ly, "ul"), "li"))
    ecran = scene(764, 460, V.vue_fichiers(fichiers_demo("pdf", "fichier")), sim="lot", curseur=False, label="Traduction d'un lot de fichiers")
    mise = (f'<div class="lf-m"><div class="lf-sc">{ecran}</div><div><h3>{txt(bloc(ly, "h3"))}</h3><p>{brut(bloc(ly, "p"))}</p><ul class="lf-ck">{puces}</ul>'
            f'<a class="lien" href="{href(lien_)}">{txt(lien_)}</a></div></div>')
    restes = [k for k in F if k not in {f for _, f in tuiles_} | {"Ce qui est rendu"}]  # « Ce qui est rendu » : dit par la mise en page
    faits_ = "".join(f'<div><h3>{k}</h3><p>{F[k]}</p></div>' for k in restes)
    return section(h2(txt(bloc(lead, "h2")), "leurs limites") + f'<p class="intro">{brut(bloc(lead, "p"))}</p>' + tl + mise + f'<div class="lf-f">{faits_}</div>')


th = bloc(t, "section", "thero")
h1 = bloc(th, "h1")
out = [hero(txt(bloc(h1, "em")), txt(re.sub(r"<em>.*?</em>", "", h1, flags=re.S)), brut(bloc(th, "p", "lead")), ("Demander une démo", C)),
       langues(), conventions(), formats(), generique.h_siblings(bloc(t, "section", "siblings"), {}), faq_section(t), cta_section(t, "Vos langues,")]
ecrire(P, entete_existant(P), "".join(out))
print(f"{P} écrite")
