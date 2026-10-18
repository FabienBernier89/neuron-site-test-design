"""Compose les pages comparatives (comparatif/<page>/) sur le modèle validé par Fabien le 2026-10-18.

Ordre : hero ; « La réponse courte » en bref (la réponse, puis trois différences en tuiles) ; ce que l'autre solution fait
bien (liste cochée) ; le tableau des critères regroupé en trois thèmes ; l'exemple (scène « le texte qui se corrige »,
tableau de lecture, carte conclusion et note) ; la question de gouvernance (texte et démo de l'avis Attorney-Client,
puis trois garde-fous) ; les autres comparatifs (cartes illustrées) ; FAQ ; appel.

Textes : la page actuelle (V1), mot pour mot ; nouveaux libellés dans src/data/contenus-v2/N-comparatifs.json (à
relire). La ligne « Requêtes couvertes par cette page » (note SEO interne affichée au lecteur) n'est plus reprise.

    cd outils/composer && python3 p_comparatif.py
"""
import html as _H
import sys
from pathlib import Path

from commun import *

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))
from outils.contenus import texte  # noqa: E402

OK = ('<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="3" stroke-linecap="round" '
      'stroke-linejoin="round" aria-hidden="true"><path d="M20 6 9 17l-5-5"/></svg>')
TRAIT = ('<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="3" stroke-linecap="round" '
         'aria-hidden="true"><path d="M7 12h10"/></svg>')
STATUTS = {"cmp-y": ("y", OK), "cmp-p": ("p", "½"), "cmp-n": ("n", TRAIT)}
ICONES = {
    "lieu": '<path d="M12 21s-7-6.2-7-11.5A7 7 0 0 1 19 9.5C19 14.8 12 21 12 21z"/><circle cx="12" cy="9.5" r="2.5"/>',
    "terme": '<path d="M4 19.5A2.5 2.5 0 0 1 6.5 17H20V3H6.5A2.5 2.5 0 0 0 4 5.5z"/><path d="M9 8h7M9 12h5"/>',
    "relecture": '<path d="M4 20h4l10-10-4-4L4 16z"/><path d="m13 7 4 4"/>',
}

# Une configuration par page comparative
PAGES = {
    "comparatif/deepl-traduction-juridique/": {
        "cle": "deepl-traduction-juridique",
        # trois différences de « La réponse courte » : points de « Ce que Corrext ajoute autour » (V1), dans l'ordre
        "differences": [(0, "lieu"), (2, "terme"), (3, "relecture")],
        # critères du tableau, par thème (indices des lignes de la V1)
        "groupes": [("confidentialite", (0, 1, 2, 10)), ("qualite", (3, 4, 5)), ("relecture", (6, 7, 8, 9))],
        "exemple": {"demo": "lb", "cible": "German", "moteur": "DeepL Pro", "ecarts": [("unterstellte", "beaufsichtigte")],
                    "fenetre": "Banque · art. 47 LB"},  # intitulé de l'exemple dans la démo Corrext publiée
        "cta": "Comparez les moteurs vous-même,",
    },
}


def esc(s):
    return _H.escape(s, quote=False)


def composer(P):
    cfg = PAGES[P]
    k = lambda c: esc(texte(f"{cfg['cle']}.{c}"))
    t = liens(charger(P), P)
    out = []

    # Hero
    th = bloc(t, "section", "thero")
    h1 = bloc(th, "h1")
    n = txt(bloc(h1, "em"))
    s = txt(re.sub(r"<em>.*?</em>", "", h1, flags=re.S))
    out.append(hero(n, s, brut(bloc(th, "p", "lead")), ("Demander une démo", C)))

    # En bref : la réponse, puis les trois différences
    ans = bloc(t, "section", "cp-answer")
    reponse = brut(bloc(ans, "p"))
    premiere, suite = reponse.split(". ", 1)
    fair = bloc(t, "section", "cp-fair")
    cols = blocs(fair, "div", "cp-col")
    ajouts = blocs(cols[1], "li")
    tuiles_d = "".join(
        f'<li><span class="cp-ic"><svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" '
        f'stroke-linejoin="round" aria-hidden="true">{ICONES[ic]}</svg></span><div><b>{txt(bloc(ajouts[i], "b"))}</b>'
        f'<p>{brut(re.sub(r"<b>.*?</b>", "", interne(ajouts[i]), flags=re.S))}</p></div></li>' for i, ic in cfg["differences"])
    out.append(section(h2(txt(bloc(ans, "h2"))) + f'<div class="cp-eb"><div><p class="cp-q">{premiere}.</p><p class="cp-s">{suite}</p></div>'
                       f'<ul>{tuiles_d}</ul></div>'))

    # Ce que l'autre solution fait bien : liste cochée
    forces = blocs(cols[0], "li")
    liste = "".join(f'<li><span class="cp-ok">{OK}</span><div><b>{txt(bloc(x, "b"))}</b>'
                    f'<p>{brut(re.sub(r"<b>.*?</b>", "", interne(x), flags=re.S))}</p></div></li>' for x in forces)
    titre_f = txt(bloc(cols[0], "h2"))
    out.append(section(h2(titre_f, "fait bien" if "fait bien" in titre_f else None) + f'<p class="intro">{brut(bloc(cols[0], "p"))}</p>'
                       f'<ul class="cp-fb">{liste}</ul>'))

    # Le tableau, regroupé en trois thèmes
    cp = bloc(t, "section", "compare")
    tab = bloc(cp, "table")
    entetes = [txt(x) for x in re.findall(r"<th[^>]*>(.*?)</th>", bloc(tab, "thead"), re.S)]
    col_b = entetes[2]
    nom_b, _, precision = col_b.partition(" (")
    lignes = []
    for tr in blocs(bloc(tab, "tbody"), "tr"):
        cellules = []
        for td in blocs(tr, "td"):
            st = re.search(r'class="(cmp-[ynp])"', td).group(1)
            cls, ic = STATUTS[st]
            cellules.append((cls, ic, brut(re.sub(r'<span class="cmp-[ynp]"[^>]*></span>', "", interne(td)).strip())))
        lignes.append((txt(bloc(tr, "th")), cellules))
    corps = ""
    for g, idx in cfg["groupes"]:
        corps += f'<tr class="cp-g"><th colspan="3" scope="colgroup">{k("cmp.groupe." + g)}</th></tr>'
        for i in idx:
            crit, cel = lignes[i]
            corps += f'<tr><th scope="row">{crit}</th>' + "".join(
                f'<td data-m="{(entetes[1], nom_b)[j]}"{" class=" + chr(34) + "cp-c" + chr(34) if j == 1 else ""}><span class="cp-st {c}">{ic}</span>{v}</td>'
                for j, (c, ic, v) in enumerate(cel)) + "</tr>"
    assert sum(len(i) for _, i in cfg["groupes"]) == len(lignes), "un critère du tableau n'est rangé dans aucun thème"
    leg = "".join(f'<span><span class="cp-st {STATUTS[c][0]}">{STATUTS[c][1]}</span>{txt(x)}</span>'
                  for c, x in re.findall(r'<span><span class="(cmp-[ynp])"[^>]*></span>(.*?)</span>', bloc(cp, "div", "cmp-legend"), re.S))
    titre_t = txt(bloc(cp, "h2"))
    out.append(section(h2(titre_t, "deux côtés" if "deux côtés" in titre_t else None) + f'<p class="intro">{brut(bloc(cp, "p", "compare-note"))}</p>'
                       f'<div class="cp-tw"><table class="cp-t"><thead><tr><th></th><th scope="col">{entetes[1]}</th>'
                       f'<th scope="col" class="cp-c">{nom_b}' + (f'<small>{precision.rstrip(")")}</small>' if precision else "") + "</th></tr></thead>"
                       f'<tbody>{corps}</tbody></table></div><p class="cp-leg">{leg}</p>'
                       f'<p class="legende">{brut(bloc(cp, "p", "cmp-mention"))}</p>', ident="tableau"))

    # L'exemple : scène, tableau de lecture, carte conclusion et note
    ex = bloc(t, "section", "cp-ex")
    ecfg = cfg["exemple"]
    d = EX[ecfg["demo"]]
    sortie_lm = d["out"]["de"]["main"] if ecfg["cible"] == "German" else d["out"]["en"]["main"]
    sortie_gen = next(x for x in d["out"]["de" if ecfg["cible"] == "German" else "en"]["alt"] if x["e"] == ecfg["moteur"])["t"]
    gen = A.marquer(sortie_gen, [g for g, _ in ecfg["ecarts"]], "gen")
    lm = A.marquer(sortie_lm, [o for _, o in ecfg["ecarts"]])
    ecran = A.ecran_corrige(esc(d["src"]), gen, lm, f'<span>{k("cmp.ex.chip")}</span>', ecfg["moteur"], cible=ecfg["cible"], classe=" cr-cg-ecart")
    tete = bloc(ex, "div", "sec-head")
    titre_e = txt(bloc(tete, "h2"))
    note = brut(bloc(ex, "p", "cp-ex-note"))
    phrases = [x.strip() for x in re.split(r"(?<=\.) (?=[A-Z])", note) if x.strip()]
    mention = [p for p in re.split(r"(?<=\.) (?=[A-Z])", brut(blocs(ex, "p")[-1])) if p.strip()]
    ok_pill = f'<span class="lm-ok">{k("cmp.ex.officiel")}</span>'
    (g1, o1), = ecfg["ecarts"]
    ref_lm = re.search(r"Artikel 47 BankG", sortie_lm).group(0)
    ref_gen = re.search(r"Art\. 47 BankG", sortie_gen).group(0)
    abrev = re.search(r"l'abréviation allemande de la loi sur les banques", note).group(0)
    assujetti = re.search(r"« établissement assujetti »", note).group(0)
    lecture = (f'<table class="lm-tb"><thead><tr><th scope="col">{k("cmp.ex.col")}</th><th scope="col">LexMachina</th><th scope="col">{ecfg["moteur"]}</th></tr></thead><tbody>'
               f'<tr><th scope="row">{assujetti}</th><td data-m="LexMachina"><b>{o1}</b>{ok_pill}<small>{k("cmp.ex.assujetti.note.lm")}</small></td>'
               f'<td data-m="{ecfg["moteur"]}"><b>{g1}</b><small>{k("cmp.ex.assujetti.note.gen")}</small></td></tr>'
               f'<tr><th scope="row">{k("cmp.ex.reference")}</th><td data-m="LexMachina"><b>{ref_lm}</b><small>{abrev}</small></td>'
               f'<td data-m="{ecfg["moteur"]}"><b>{ref_gen}</b><small>{abrev}</small></td></tr></tbody></table>')
    notes = [mention[0], k("cmp.ex.verifie"), next(p for p in mention if p.startswith("Il s'agit d'un exemple ponctuel"))]
    carte = (f'<div class="lm-cc"><div class="lm-cc-g"><p class="lm-conc">{k("cmp.ex.conclusion")}</p>'
             f'<a class="lien" href="{{{{ROOT}}}}corrext/traduction-texte-et-document/#demo">{k("cmp.ex.demo")}</a></div>'
             f'<div class="lm-cc-d"><ul>' + "".join(f"<li>{OK}<span>{x}</span></li>" for x in notes) + "</ul></div></div>")
    out.append(section(h2(titre_e, "les banques" if "les banques" in titre_e else None) + f'<p class="intro">{brut(bloc(tete, "p"))}</p>'
                       + scene(1176, 440, ecran, sim="corrige", titre=ecfg["fenetre"], curseur=False,
                               label=f"{ecfg['moteur']} puis LexMachina sur une phrase de droit bancaire")
                       + lecture + carte, ident="exemple"))

    # Gouvernance : texte et démo de l'avis, puis trois garde-fous
    gov = bloc(t, "section", "gov")
    boite = bloc(gov, "div", "gov-box")
    titre_g = txt(bloc(boite, "h2"))
    para = brut(bloc(boite, "p"))
    lien = bloc(boite, "a", "feat-link")
    demo = A.ecran_securite(*textes_demo()["notice"], esc(EX["co"]["src"]), esc(EX["co"]["out"]["en"]["main"]))
    pas = re.findall(r"<span>(<b>.*?)</span>\s*</div>", bloc(boite, "div", "gov-steps"), re.S)
    etapes = [(txt(bloc(x, "b")).rstrip("."), brut(re.sub(r"<b>.*?</b>", "", x, flags=re.S)).strip()) for x in pas]
    assert len(etapes) == 3, len(etapes)
    out.append(section(f'<div class="cp-gv"><div>{h2(titre_g, "un cabinet" if "un cabinet" in titre_g else None)}<p>{para}</p>'
                       f'<p class="cp-gv-l"><a class="lien" href="{re.search(r"href=\"([^\"]+)\"", lien).group(1)}">{txt(lien)}</a></p></div>'
                       + scene(1176, 520, demo, sim="avis", curseur=False, titre="Corrext", label="Choix du moteur et avis Attorney-Client privilege") + "</div>"
                       + tuiles([(None, b, p) for b, p in etapes], "tl txt")))

    # Les autres comparatifs : cartes reliées (outils/post/fonctionnalites.py les illustre)
    vn = bloc(t, "section", "vn")
    cartes_vn = []
    for a in blocs(vn, "a", "vs-card"):
        href = re.search(r'href="\{\{ROOT\}\}([^"]+)"', a).group(1)
        cible = (RACINE / "src/pages" / href[3:] / "index.html").read_text(encoding="utf-8")
        h1c = bloc(cible, "h1")
        cartes_vn.append(f'<a href="{{{{ROOT}}}}{href}"><b>{txt(bloc(h1c, "span", "n")).rstrip(".")}</b><p>{txt(bloc(h1c, "span", "s"))}</p>'
                         f'<span class="lien">{txt(re.sub(r"<svg.*?</svg>", "", bloc(a, "em"), flags=re.S))}</span></a>')
    out.append(section(h2(txt(bloc(vn, "h2"))) + '<div class="cd">' + "".join(cartes_vn) + "</div>"))

    out.append(faq_section(t))
    out.append(cta_section(t, cfg["cta"]))
    ecrire(P, entete_existant(P), "".join(out))
    print(f"{P} écrite")


if __name__ == "__main__":
    for p in PAGES:
        composer(p)
