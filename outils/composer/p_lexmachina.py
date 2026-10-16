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
out.append(hero("LexMachina.", "Le moteur qui connaît les lois qu'il traduit", brut(bloc(th, "p", "lead")), ("Demander une démo", C)))
def k(cle):
    return _H.escape(texte(f"lexmachina.{cle}"), quote=False)


def lecture(sorties):
    """Tableau de lecture sous la comparaison (proposition 1-B retenue par Fabien le 2026-10-16) : la loi citée et la
    juridiction, telles que chaque moteur les écrit ; formes reprises des sorties réelles affichées dans l'animation."""
    lm, dp = (re.sub(r"<[^>]+>", "", x) for x in sorties)
    for terme, sortie in (("PILA", lm), ("Federal Tribunal", lm), ("LDIP", dp), ("Federal Supreme Court", dp)):
        assert terme in sortie, f"sortie de la comparaison modifiée : {terme} absent"
    ok = f'<span class="lm-ok">{k("lecture.officiel")}</span>'
    def cel(terme, note="", officiel=False):
        return f'<td><b>{terme}</b>{ok if officiel else ""}' + (f"<small>{k(note)}</small>" if note else "") + "</td>"
    lignes = (f'<tr><th scope="row">{k("lecture.loi")}</th>{cel("PILA", "lecture.pila", True)}{cel("LDIP", "lecture.ldip")}</tr>'
              f'<tr><th scope="row">{k("lecture.juridiction")}</th>{cel("Federal Tribunal")}{cel("Federal Supreme Court", "lecture.fsc", True)}</tr>')
    return (f'<table class="lm-tb"><thead><tr><th scope="col">{k("lecture.col")}</th><th scope="col">LexMachina</th>'
            f'<th scope="col">DeepL Pro</th></tr></thead><tbody>{lignes}</tbody></table>'
            f'<p class="lm-conc">{k("lecture.conclusion")}</p>')


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
sorties = [interne(bloc(c, "p")).strip() for c in blocs(nl, "div", "nlex-card")]
ecran = A.ecran_comparaison(phrase, sorties[0], sorties[1], "DeepL Pro")
ui = (f'<div class="mx q4"><div class="mx-p q4-src"><small>{lb}</small><p>{phrase}</p></div>'
      f'<div class="mx-g">{"".join(cartes_)}</div></div>')
titre_fen = txt(bloc(nl, "span", "nlex-tag"))
out.append(section(h2(h, "quatre caractères") + f'<p class="intro">{p}</p>'
                   + scene(1176, 440, ecran, sim="quatre", titre=titre_fen, curseur=False, label="Comparaison des sorties LexMachina et DeepL Pro")
                   + lecture(sorties) + f'<p class="legende">{brut(bloc(nl, "p", "nlex-cap"))}</p>'))
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
                   + f'<div class="lm-id"><ul class="lm-ch">{chiffres}</ul><ul class="lm-gr">{"".join(groupes)}</ul></div>'
                   + f'<p class="legende">{brut(bloc(sp, "p", "nls-foot"))}</p>'))
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
out.append(cta_section(t, "Jugez le moteur"))
ecrire(P, entete_existant(P), "".join(out))
print("lexmachina écrite")
