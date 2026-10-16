from commun import *
import html as _H
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[2]))
from outils.contenus import texte  # noqa: E402
P = "lexmachina/"
t = liens(charger(P), P)
out = []
th = bloc(t, "section", "thero")
out.append(hero("LexMachina.", "Le moteur qui connaît les lois qu'il traduit", brut(bloc(th, "p", "lead")), ("Demander une démo", C)).replace('class="wrap hero-g"', 'class="wrap hero-g lm-hg"', 1))  # titre aligné en haut sur le texte de droite (Fabien, 2026-10-16)
def k(cle):
    return _H.escape(texte(f"lexmachina.{cle}"), quote=False)


# Comparaison (idée A retenue par Fabien le 2026-10-16, « le texte qui se corrige ») : la sortie de DeepL s'écrit, ses
# deux termes génériques se signalent, puis LexMachina retraduit et les termes officiels se surlignent. Deux sorties
# RÉELLES du même texte (celui de l'axe LexMachina de l'accueil) ; seuls les écarts réels sont marqués.
ECARTS = (("retenue à la source", "impôt anticipé"), ("établissement soumis à surveillance", "assujetti"))


def marquer(sortie, termes, cls=""):
    h = _H.escape(sortie, quote=False)
    for t_ in termes:
        assert t_ in h, f"sortie modifiée : « {t_} » absent"
        h = h.replace(t_, f'<mark{" class=" + chr(34) + cls + chr(34) if cls else ""}>{t_}</mark>', 1)
    return h


def ecran_corrige():
    gen = marquer(texte("lexmachina.compare.deepl").replace(" %", "\u00a0%"), [g for g, _ in ECARTS], "gen")  # « 35 % » insécable
    lm = marquer(texte("accueil.axes.lexmachina.demo.out"), [o for _, o in ECARTS])
    puces = "".join(f'<span>{k("compare.chip." + c)}</span>' for c in ("impot", "assujetti"))
    ecran = ('<div class="cr cr-frag cr-cg">'
            + A.travail(detecte=True, cible="French", moteur=k("compare.moteur"), src=_H.escape(texte("accueil.axes.lexmachina.demo.src"), quote=False), out="")
            .replace("Detected language (French)", _H.escape(texte("accueil.axes.lexmachina.demo.langue"), quote=False), 1)
            .replace('<p class="cr-out">', f'<p class="cr-out" data-gen="{_H.escape(gen)}" data-html="{_H.escape(lm)}">', 1)
            + f'<div class="cg-src">{puces}</div></div>')
    # Menu des moteurs de la scène : l'IA généraliste et LexMachina seulement, aucun moteur tiers nommé (Fabien, 2026-10-16)
    nom = k("compare.moteur")
    ecran = re.sub(r'(<span class="cr-sel cr-eng">.*?<span class="cr-menu">).*?(</span></span>)',
                   lambda m: m.group(1) + f'<span class="on" data-v="{nom}">{nom}</span><span data-v="LexMachina">LexMachina</span>' + m.group(2),
                   ecran, count=1, flags=re.S)
    assert "DeepL" not in ecran and "Azure" not in ecran
    return ecran


def lecture():
    """Tableau de lecture sous la comparaison (mise en page 1-B retenue par Fabien le 2026-10-16) : les deux écarts
    réels, tels que chaque moteur les écrit."""
    ok = f'<span class="lm-ok">{k("lecture.officiel")}</span>'
    def cel(terme, note, moteur, officiel=False):  # data-m : nom du moteur, affiché au-dessus de la cellule sur mobile
        return f'<td data-m="{moteur}"><b>{terme}</b>{ok if officiel else ""}<small>{k(note)}</small></td>'
    (g1, o1), (g2, o2) = ECARTS
    gen = k("compare.moteur")
    lignes = (f'<tr><th scope="row">{k("lecture.impot")}</th>{cel(o1, "lecture.lia", "LexMachina", True)}{cel(g1, "lecture.generique", gen)}</tr>'
              f'<tr><th scope="row">{k("lecture.statut")}</th>{cel(o2, "lecture.lfinma", "LexMachina", True)}{cel(g2, "lecture.periphrase", gen)}</tr>')
    return (f'<table class="lm-tb"><thead><tr><th scope="col">{k("lecture.col")}</th><th scope="col">LexMachina</th>'
            f'<th scope="col">{k("compare.moteur")}</th></tr></thead><tbody>{lignes}</tbody></table>')


OK_IC = ('<svg viewBox="0 0 16 16" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" '
         'stroke-linejoin="round" aria-hidden="true"><path d="M3.5 8.5l3 3 6-7"/></svg>')


def conclusion(note):
    """Conclusion et note de méthode réunies dans une carte (retour de Fabien du 2026-10-16) : à gauche la conclusion
    et le lien vers la démo, à droite la note, une phrase par ligne (la dernière reprise de la V1)."""
    derniere = [x.strip() for x in re.split(r"(?<=\.) (?=[A-Z])", note) if x.strip()][-1]
    assert derniere.startswith("Les sorties d'un moteur varient"), derniere
    phrases = [k("lecture.note1"), k("lecture.note2"), derniere]
    return (f'<div class="lm-cc"><div class="lm-cc-g"><p class="lm-conc">{k("lecture.conclusion")}</p>'
            f'<a class="lien" href="{{{{ROOT}}}}corrext/traduction-texte-et-document/#demo">{k("lecture.demo")}</a></div>'
            f'<div class="lm-cc-d"><p class="lm-cc-t">{k("lecture.exemple")}</p><ul>'
            + "".join(f"<li>{OK_IC}<span>{x}</span></li>" for x in phrases) + "</ul></div></div>")


nl = bloc(t, "section", "nlex")
out.append(section(h2(k("compare.titre"), "le terme officiel") + f'<p class="intro">{k("compare.intro")}</p>'
                   + scene(1176, 440, ecran_corrige(), sim="corrige", titre=k("compare.fenetre"), curseur=False,
                           label="Une IA généraliste puis LexMachina sur un texte fiscal suisse : les termes officiels remplacent les termes génériques")
                   + lecture() + conclusion(brut(bloc(nl, "p", "nlex-cap")))))
# Ce qu'est LexMachina (proposition 2-B retenue par Fabien le 2026-10-16) : les quatre chiffres en liste à gauche,
# l'environnement du moteur (matières, Corrext, autres moteurs) en trois groupes à pastilles à droite
sp = bloc(t, "section", "nlspec")
h, p = tete(sp)
COURTS = ("segments", "langues", "suisse", "alternatives")
chiffres = "".join(f'<li><span class="n">{txt(bloc(x, "b"))}</span><div><b>{txt(bloc(x, "span"))}</b><p>{k("spec." + c)}</p></div></li>'
                   for x, c in zip(blocs(sp, "div", "nls-k"), COURTS))
groupes = []
for i, x in enumerate(blocs(sp, "div", "nls-t")):
    titre = k("spec.corrext") if i == 1 else txt(blocs(bloc(x, "h3"), "span")[-1])
    puces = "".join(f'<span class="pill">{txt(y)}</span>' for y in blocs(bloc(x, "div", "nls-chips"), "span"))
    groupes.append(f'<li><b>{titre}</b><div class="puces">{puces}</div></li>')
out.append(section(h2(h, "exactement") + f'<p class="intro">{p}</p>'
                   + f'<div class="lm-id"><ul class="lm-ch">{chiffres}</ul><ul class="lm-gr">{"".join(groupes)}</ul></div>'))
# Note « Recherche : Innosuisse… » retirée (Fabien, 2026-10-16)
# Piliers
pi = bloc(t, "section", "pillars")
h, p = tete(pi)
out.append(section(h2(h, "un modèle spécialisé") + f'<p class="intro">{p}</p>'
                   + tuiles([(None, txt(blocs(bloc(x, "h3"), "span")[-1]), brut(bloc(x, "p"))) for x in blocs(pi, "div", "pillar")], "tl txt tl-lm")))  # textes un peu plus petits (Fabien, 2026-10-16)
# Pour aller plus loin : cartes avec valeurs clés
vn = bloc(t, "section", "vn")
cs = []
for a in blocs(vn, "a", "vn-card"):
    kv = "".join(f"<span><i>{txt(bloc(s, 'i'))}</i><b>{txt(bloc(s, 'b'))}</b></span>" for s in blocs(bloc(a, "span", "vn-kv"), "span")[1:] if "<i>" in s)
    cs.append((txt(bloc(a, "b", "vn-t")), brut(bloc(a, "span", "vn-d")), (txt(bloc(a, "em")), re.search(r'href="([^"]+)"', a).group(1)),
               f'<span class="kv">{kv}</span>'))
out.append(section(h2(txt(bloc(vn, "h2"))) + cartes(cs)))
out.append(faq_section(t))
l1, l2 = k("cta.titre").split(" sur ", 1)  # « Testez LexMachina » au lieu de « Jugez le moteur » (Fabien, 2026-10-16)
out.append(cta(l1, "sur " + l2, ("Demander une démo", C)))
ecrire(P, entete_existant(P), "".join(out))
print("lexmachina écrite")
