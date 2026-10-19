"""Modèle des pages de paires de langues (traduction/<source>-<cible>/), validé par Fabien le 2026-10-19 sur la page
Allemand vers français, à dérouler ensuite sur les autres paires.

Ordre : hero ; CHnell en contexte (titre, phrase, scène animée) ; les équivalences officielles (la paire de la page
en avant, les autres langues en retrait, références en pastilles) ; « en pratique » en trois niveaux (le principe en
encart, ce qui se convertit avec l'exemple en grand, ce que Corrext garantit) ; les situations (icône et contexte de
la V1) ; FAQ ; les autres paires (cartes illustrées) ; appel.

Textes : la page actuelle (V1), mot pour mot ; nouveaux libellés dans src/data/contenus-v2/O-paires.json (à relire).
"""
import html as _H
import sys
from pathlib import Path

from blocs_communs import *

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))
from outils.contenus import texte  # noqa: E402

FLECHE = ('<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" '
          'stroke-linejoin="round" aria-hidden="true"><path d="M5 12h14M13 6l6 6-6 6"/></svg>')
COCHE = ('<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="3" stroke-linecap="round" '
         'stroke-linejoin="round" aria-hidden="true"><path d="M20 6 9 17l-5-5"/></svg>')
ICONES = {
    "moteur": '<path d="M4 19.5A2.5 2.5 0 0 1 6.5 17H20V3H6.5A2.5 2.5 0 0 0 4 5.5z"/><path d="M9 8h7M9 12h5"/>',
    "cadenas": '<rect x="5" y="11" width="14" height="10" rx="2"/><path d="M8 11V7a4 4 0 0 1 8 0v4"/>',
    "mise": '<path d="M4 6h16M4 12h10M4 18h16"/>',
}


def esc(s):
    return _H.escape(s, quote=False)


def icone(nom):
    return (f'<span class="pa-ic"><svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" '
            f'stroke-linejoin="round" aria-hidden="true">{ICONES[nom]}</svg></span>')


def lookup(slug, q, l1, l2, marque):
    """Recherche CHnell relevée pour la page (contenus-v2) : segments officiels alignés, clés a/b/src puis a2/b2/src2…"""
    k = lambda c: texte(f"{slug}.chnell.{c}")
    rows, n = [], 1
    while True:
        suf = "" if n == 1 else str(n)
        try:
            rows.append({"a": k("a" + suf), "b": k("b" + suf), "src": k("src" + suf)})
        except KeyError:
            break
        n += 1
    return {"q": q, "l1": l1, "l2": l2, "count": k("count"), "rows": rows, "mark": [q, marque]}


def chnell(P, cfg):
    """CHnell en contexte : titre, phrase propre à la paire, scène animée (sim « chnell »)."""
    cle = P.split("/")[1]
    return section(h2(esc(texte("paire.chnell.titre")), "dans le texte officiel") + f'<p class="intro intro-l">{esc(texte(f"{cle}.chnell.intro"))}</p>'
                   + scene(1176, 510, V.vue_chnell(cfg["lookup"]), sim="chnell", curseur=False, titre="CHnell", label="Fast lookup CHnell"))


def equivalences(t, cfg, accent):
    """Le tableau des équivalences de la V1 : la paire en avant, les autres langues en retrait, références en pastilles."""
    tt = bloc(t, "section", "tterms")
    tab = bloc(tt, "table")
    entetes = [txt(x) for x in re.findall(r"<th[^>]*>(.*?)</th>", bloc(tab, "thead"), re.S)]
    # page de paire : la paire en avant, le reste en retrait ; page de domaine (pas de sens) : la première langue en gras
    role = {cfg["source"]: "pa-s", cfg["cible"]: "pa-c"} if cfg.get("source") else {entetes[0]: "pa-s"}
    autre = "pa-m" if cfg.get("source") else "pa-n"
    tete = "".join(f'<th scope="col" class="{role.get(e, autre)}">{e}</th>' for e in entetes)
    lignes = ""
    for tr in blocs(bloc(tab, "tbody"), "tr"):
        cellules = [brut(c).strip() for c in re.findall(r"<t[hd][^>]*>(.*?)</t[hd]>", tr, re.S)]
        lignes += "<tr>" + "".join(
            (f'<th scope="row" class="{role.get(e, autre)}" data-m="{e}">{v}</th>' if j == 0 else
             f'<td class="pa-r" data-m="{e}"><span class="pa-ref">{v}</span></td>' if e == "Référence" else
             f'<td class="{role.get(e, autre)}" data-m="{e}">{v}</td>') for j, (e, v) in enumerate(zip(entetes, cellules))) + "</tr>"
    ps = [p for p in blocs(tt, "p") if "class=" not in p[:12]]
    notes = "".join(f'<p class="legende">{brut(p)}</p>' for p in blocs(tt, "p") if 'class="' in p[:20])
    return section(h2(txt(bloc(tt, "h2")), accent) + (f'<p class="intro">{brut(ps[0])}</p>' if ps else "")
                   + f'<div class="pa-tw"><table class="pa-t"><thead><tr>{tete}</tr></thead><tbody>{lignes}</tbody></table></div>' + notes)


def pratique(t, cfg, accent):
    """« En pratique » : le principe en encart, ce qui se convertit (exemple en grand), ce que Corrext garantit."""
    fa = bloc(t, "section", "facts")
    lead = bloc(fa, "div", "facts-lead")
    faits = {txt(bloc(f, "b")): brut(bloc(f, "p")) for f in blocs(fa, "div", "fact")}
    pris = {cfg["principe"]} | {n for n, _ in cfg["conversions"]} | {n for n, _ in cfg["garanties"]}
    assert set(faits) == pris, f"faits de la V1 non rangés : {set(faits) ^ pris}"
    encart = f'<div class="pa-pr"><p class="pa-pq">{cfg["principe"]}</p><p>{faits[cfg["principe"]]}</p></div>'

    def exemple(ex):
        """(avant, après) : conversion ; (None, terme) : forme juste seule ; (terme, None) : piège, barré."""
        a, b = ex
        long = " pa-ex-l" if a and b and len(a + b) > 16 else ""  # conversion longue : police réduite
        if a and b:
            return f'<p class="pa-ex{long}">{a}<i aria-hidden="true">{FLECHE}</i><span>{b}</span></p>'
        if b:
            return f'<p class="pa-ex{long}"><span>{b}</span></p>'
        return f'<p class="pa-ex{long}"><s>{a}</s></p>'
    conv = "".join(f'<div>{exemple(ex)}<h3>{n}</h3><p>{faits[n]}</p></div>' for n, ex in cfg["conversions"])
    # garanties en bandeau de réassurance (coche, séparateurs), distinct des cartes de situations (Fabien, 2026-10-19)
    gar = "".join(f'<div><span class="pa-ck">{COCHE}</span><div><h3>{n}</h3><p>{faits[n]}</p></div></div>' for n, _ in cfg["garanties"])
    return section(h2(txt(bloc(lead, "h2")), accent) + f'<p class="intro">{brut(bloc(lead, "p"))}</p>' + encart
                   + f'<p class="pa-st">{esc(texte("paire.convertit"))}</p><div class="pa-cv pa-cv{len(cfg["conversions"])}">{conv}</div>'
                   + f'<p class="pa-st">{esc(texte("paire.garantit"))}</p><div class="pa-gr">{gar}</div>')


def situations(t, accent):
    """Les situations de la V1, avec leur icône et leur contexte (Contentieux…)."""
    wh = bloc(t, "section", "who")
    cartes_ = []
    for r in blocs(wh, "article", "sc-row"):
        ic = re.search(r"<svg.*?</svg>", bloc(r, "span", "ws-ic"), re.S).group(0)
        cartes_.append(f'<div class="pa-si"><p class="pa-sc"><span class="pa-ic pa-ic-l">{ic}</span>{txt(bloc(r, "span", "sc-a"))}</p>'
                       f'<h3>{brut(bloc(r, "h3"))}</h3><p>{brut(bloc(r, "p"))}</p></div>')
    return section(h2(txt(bloc(wh, "h2")), accent) + f'<div class="pa-sg">{"".join(cartes_)}</div>')


def autres_paires(t):
    """Les autres paires : cartes reliées (outils/post/fonctionnalites.py les illustre)."""
    vn = blocs(t, "section", "vn")
    if not vn:
        return ""
    cs = []
    for a in blocs(vn[0], "a", "vn-card"):
        href = re.search(r'href="([^"]+)"', a).group(1)
        em = blocs(a, "em")
        cs.append(f'<a href="{href}"><b>{txt(bloc(a, "b", "vn-t"))}</b><p>{brut(bloc(a, "span", "vn-d"))}</p>'
                  + (f'<span class="lien">{txt(re.sub(r"<svg.*?</svg>", "", em[0], flags=re.S))}</span>' if em else "") + "</a>")
    return section(h2(txt(bloc(vn[0], "h2"))) + '<div class="cd">' + "".join(cs) + "</div>")
