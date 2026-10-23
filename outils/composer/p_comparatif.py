"""Compose les pages comparatives (comparatif/<page>/) sur le modèle validé par Fabien le 2026-10-18, adapté au contenu
de chaque page (demande du 2026-10-18 : « en adaptant bien les éléments en fonction du contenu de chaque page »).

Ordre : hero ; « La réponse courte » en bref ; ce que l'autre solution fait bien (liste cochée) ou les trois modèles
(page agence) ; le tableau des critères regroupé en trois thèmes ; l'exemple (scène « le texte qui se corrige »,
exemple statique, ou les niveaux de relecture pour la page agence) ; la question de gouvernance (texte, démo,
trois garde-fous) ; les autres comparatifs (cartes illustrées) ; FAQ ; appel.

Textes : la page actuelle (V1), mot pour mot ; nouveaux libellés dans src/data/contenus-v2/N-comparatifs.json (à
relire). Les notes SEO « Requêtes couvertes par cette page » ne sont plus affichées.

    cd outils/composer && python3 p_comparatif.py
"""
import html as _H
import sys
from pathlib import Path

from commun import *

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))
from outils import contenus  # noqa: E402
from outils.contenus import texte  # noqa: E402

OK = ('<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="3" stroke-linecap="round" '
      'stroke-linejoin="round" aria-hidden="true"><path d="M20 6 9 17l-5-5"/></svg>')
TRAIT = ('<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="3" stroke-linecap="round" '
         'aria-hidden="true"><path d="M7 12h10"/></svg>')
STATUTS = {"cmp-y": ("y", OK), "cmp-p": ("p", "½"), "cmp-n": ("n", TRAIT), "cmp-na": ("na", "")}  # na : critère non comparé
ICONES = {
    "lieu": '<path d="M12 21s-7-6.2-7-11.5A7 7 0 0 1 19 9.5C19 14.8 12 21 12 21z"/><circle cx="12" cy="9.5" r="2.5"/>',
    "terme": '<path d="M4 19.5A2.5 2.5 0 0 1 6.5 17H20V3H6.5A2.5 2.5 0 0 0 4 5.5z"/><path d="M9 8h7M9 12h5"/>',
    "relecture": '<path d="M4 20h4l10-10-4-4L4 16z"/><path d="m13 7 4 4"/>',
    "reference": '<path d="M12 3v18M5 7h14M7 7l-3 7h6zM17 7l-3 7h6z"/>',
    "agence": '<circle cx="9" cy="8" r="3.2"/><path d="M3.5 19a5.5 5.5 0 0 1 11 0"/><path d="M16 11a3 3 0 1 0 0-6M17.5 19a5 5 0 0 0-2.3-4.2"/>',
    "outil": '<path d="M13 2 4 14h7l-1 8 9-12h-7z"/>',
    "corrext": '<path d="m12 3 9 5-9 5-9-5z"/><path d="m3 13 9 5 9-5"/>',
}

# Une configuration par page comparative
PAGES = {
    "comparatif/deepl-traduction-juridique/": {
        "cle": "deepl-traduction-juridique",
        # trois différences de « La réponse courte » : points de « Ce que Corrext ajoute autour » (V1)
        "differences": [(0, "lieu"), (2, "terme"), (3, "relecture")],
        # critères du tableau, par thème (indices des lignes de la V1)
        "groupes": [("confidentialite", (0, 1, 2, 10)), ("qualite", (3, 4, 5)), ("relecture", (6, 7, 8, 9))],
        "exemple": {"type": "scene", "demo": "lb", "cible": "German", "moteur": "DeepL Pro",
                    "ecarts": [("unterstellte", "beaufsichtigte")], "fenetre": "Banque · art. 47 LB"},  # intitulé de la démo publiée
        "gouvernance": "avis",
        "cta": "Comparez les moteurs vous-même,",
    },
    "comparatif/chatgpt-traduction-juridique/": {
        "cle": "chatgpt-traduction-juridique",
        # trois différences : points de « Ce qu'ils ne peuvent pas prouver seuls » (V1), ce que Corrext apporte
        "differences": [(0, "terme"), (1, "reference"), (2, "relecture")],
        "groupes": [("qualite", (0, 4, 5, 6)), ("confidentialite", (1, 2, 3, 11)), ("relecture", (7, 8, 9, 10))],
        # erreur de terminologie de ChatGPT que LexMachina évite, et sa preuve dans CHnell (Fabien, 2026-10-18) ;
        # remplace l'exemple de la V1 où LexMachina se trompait
        "exemple": {"type": "preuve"},
        "gouvernance": "avis",
        "cta": "Mettez les moteurs face",
    },
    "comparatif/agence-ou-plateforme/": {
        "cle": "agence-ou-plateforme",
        "differences": None,  # la réponse seule ; les trois modèles suivent dans leur propre section
        "groupes": [("demarrage", (0, 1, 2)), ("qualite", (3, 4, 7)), ("controle", (5, 6, 8))],
        "exemple": {"type": "niveaux"},
        "gouvernance": "devis",
        "cta": "Voyez le tunnel projet",
    },
}


def esc(s):
    return _H.escape(s, quote=False)


def accent(titre, mots):
    """Accent serif sur la fin du titre quand elle figure dans la liste (comme la V1)."""
    return next((m for m in mots if m in titre), None)


def sans_b(li):
    return brut(re.sub(r"<b>.*?</b>", "", interne(li), flags=re.S))


def icone(nom):
    return (f'<span class="cp-ic"><svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" '
            f'stroke-linejoin="round" aria-hidden="true">{ICONES[nom]}</svg></span>')


def phrases(p):
    return [x.strip() for x in re.split(r"(?<=\.) (?=[A-ZÀ-Ý])", p) if x.strip()]


def en_bref(t, cfg):
    ans = bloc(t, "section", "cp-answer")
    reponse = brut(bloc(ans, "p"))
    premiere, suite = reponse.split(". ", 1) if ". " in reponse else reponse.split(" : ", 1)
    droite = ""
    if cfg["differences"]:
        cols = blocs(bloc(t, "section", "cp-fair"), "div", "cp-col")
        pts = blocs(cols[1], "li")
        droite = "<ul>" + "".join(f'<li>{icone(ic)}<div><b>{txt(bloc(pts[i], "b"))}</b><p>{sans_b(pts[i])}</p></div></li>'
                                  for i, ic in cfg["differences"]) + "</ul>"
    corps = f'<div><p class="cp-q">{premiere}.</p><p class="cp-s">{suite}</p></div>' + droite
    return section(h2(txt(bloc(ans, "h2"))) + f'<div class="cp-eb{"" if droite else " cp-eb1"}">{corps}</div>')


def forces(t):
    col = blocs(bloc(t, "section", "cp-fair"), "div", "cp-col")[0]
    liste = "".join(f'<li><span class="cp-ok">{OK}</span><div><b>{txt(bloc(x, "b"))}</b><p>{sans_b(x)}</p></div></li>'
                    for x in blocs(col, "li"))
    titre = txt(bloc(col, "h2"))
    return section(h2(titre, accent(titre, ("fait bien", "remarquablement bien"))) + f'<p class="intro">{brut(bloc(col, "p"))}</p>'
                   f'<ul class="cp-fb">{liste}</ul>')


def modeles(t):
    """Page agence : les trois modèles, chacun avec sa force et son revers (V1)."""
    sec = bloc(t, "section", "cp-models")
    tete = bloc(sec, "div", "sec-head")
    cartes = []
    for m, ic in zip(blocs(sec, "div", "cp-model"), ("agence", "outil", "corrext")):
        h3 = bloc(m, "h3")
        nom = txt(bloc(h3, "span", "pn")).rstrip(".")
        sous = txt(re.sub(r'<span class="pn">.*?</span>', "", re.sub(r'<span class="ws-ic">.*?</span>', "", h3, flags=re.S), flags=re.S))
        cartes.append(f'<div class="cp-md">{icone(ic)}<h3>{nom}</h3><p class="cp-md-s">{sous}</p>'
                      f'<p>{brut(blocs(m, "p")[0])}</p><p class="cp-md-t">{txt(bloc(m, "p", "tag"))}</p></div>')
    titre = txt(bloc(tete, "h2"))
    return section(h2(titre, accent(titre, ("forces réelles",))) + f'<p class="intro">{brut(bloc(tete, "p"))}</p>'
                   f'<div class="cp-mg">{"".join(cartes)}</div>')


def tableau(t, cfg, k):
    cp = bloc(t, "section", "compare")
    tab = bloc(cp, "table")
    entetes = [txt(x) for x in re.findall(r"<th[^>]*>(.*?)</th>", bloc(tab, "thead"), re.S)][1:]
    noms = []
    for e in entetes:
        nom, _, precision = e.partition(" (")
        noms.append((nom, precision.rstrip(")")))
    lignes = []
    for tr in blocs(bloc(tab, "tbody"), "tr"):
        cellules = []
        for td in blocs(tr, "td"):
            st = re.search(r'class="(cmp-(?:na|[ynp]))"', td)
            cls, ic = STATUTS[st.group(1)] if st else STATUTS["cmp-na"]
            cellules.append((cls, ic, brut(re.sub(r'<span class="cmp-(?:na|[ynp])"[^>]*></span>', "", interne(td)).strip())))
        lignes.append((txt(bloc(tr, "th")), cellules))
    groupes = cfg["groupes"] or [(None, tuple(range(len(lignes))))]
    assert sorted(i for _, idx in groupes for i in idx) == list(range(len(lignes))), "chaque critère dans un seul thème"
    derniere = len(noms) - 1  # Corrext, colonne teintée
    corps = ""
    for g, idx in groupes:
        if g:
            corps += f'<tr class="cp-g"><th colspan="{len(noms) + 1}" scope="colgroup">{k("cmp.groupe." + g)}</th></tr>'
        for i in idx:
            crit, cel = lignes[i]
            corps += f'<tr><th scope="row">{crit}</th>' + "".join(
                f'<td data-m="{noms[j][0]}"{" class=" + chr(34) + "cp-c" + chr(34) if j == derniere else ""}>'
                f'<span class="cp-st {c}">{ic}</span>{v}</td>' for j, (c, ic, v) in enumerate(cel)) + "</tr>"
    tete = "".join(f'<th scope="col"{" class=" + chr(34) + "cp-c" + chr(34) if j == derniere else ""}>{n}'
                   + (f"<small>{p}</small>" if p else "") + "</th>" for j, (n, p) in enumerate(noms))
    leg = "".join(f'<span><span class="cp-st {STATUTS[c][0]}">{STATUTS[c][1]}</span>{txt(x)}</span>'
                  for c, x in re.findall(r'<span><span class="(cmp-[ynp])"[^>]*></span>(.*?)</span>', bloc(cp, "div", "cmp-legend"), re.S))
    titre = txt(bloc(cp, "h2"))
    note = blocs(cp, "p", "compare-note") or blocs(bloc(cp, "div", "sec-head"), "p")
    liens_t = blocs(cp, "div", "cmp-links")
    suite = ('<p class="cp-tl">' + "".join(f'<a class="lien" href="{re.search(r"href=\"([^\"]+)\"", a).group(1)}">{txt(a)}</a>'
                                            for a in blocs(liens_t[0], "a")) + "</p>") if liens_t else ""
    return section(h2(titre, accent(titre, ("deux côtés", "d'un dossier", "document signé", "un tableau"))) + f'<p class="intro">{brut(note[0])}</p>'
                   f'<div class="cp-tw"><table class="cp-t cp-t{len(noms)}"><thead><tr><th></th>{tete}</tr></thead>'
                   f'<tbody>{corps}</tbody></table></div><p class="cp-leg">{leg}</p>{suite}'
                   f'<p class="legende">{brut(bloc(cp, "p", "cmp-mention"))}</p>', ident="tableau")


def carte_conclusion(q, notes, k):
    return (f'<div class="lm-cc"><div class="lm-cc-g"><p class="lm-conc">{q}</p>'
            f'<a class="lien" href="{{{{ROOT}}}}#demo">{k("cmp.ex.demo")}</a></div>'
            f'<div class="lm-cc-d"><ul>' + "".join(f"<li>{OK}<span>{x}</span></li>" for x in notes) + "</ul></div></div>")


def exemple_scene(t, cfg, k):
    """Page DeepL : la scène « le texte qui se corrige », tableau de lecture, carte conclusion."""
    ex = bloc(t, "section", "cp-ex")
    e = cfg["exemple"]
    d = EX[e["demo"]]
    lang = "de" if e["cible"] == "German" else "en"
    sortie_lm = d["out"][lang]["main"]
    sortie_gen = next(x for x in d["out"][lang]["alt"] if x["e"] == e["moteur"])["t"]
    gen = A.marquer(sortie_gen, [g for g, _ in e["ecarts"]], "gen")
    lm = A.marquer(sortie_lm, [o for _, o in e["ecarts"]])
    ecran = A.ecran_corrige(esc(d["src"]), gen, lm, f'<span>{k("cmp.ex.chip")}</span>', e["moteur"], cible=e["cible"], classe=" cr-cg-ecart")
    tete = bloc(ex, "div", "sec-head")
    titre = txt(bloc(tete, "h2"))
    note = brut(bloc(ex, "p", "cp-ex-note"))
    mention = phrases(brut(blocs(ex, "p")[-1]))
    (g1, o1), = e["ecarts"]
    ref_lm = re.search(r"Artikel 47 BankG", sortie_lm).group(0)
    ref_gen = re.search(r"Art\. 47 BankG", sortie_gen).group(0)
    abrev = re.search(r"l'abréviation allemande de la loi sur les banques", note).group(0)
    assujetti = re.search(r"« établissement assujetti »", note).group(0)
    ok = f'<span class="lm-ok">{k("cmp.ex.officiel")}</span>'
    lecture = (f'<table class="lm-tb"><thead><tr><th scope="col">{k("cmp.ex.col")}</th><th scope="col">LexMachina</th><th scope="col">{e["moteur"]}</th></tr></thead><tbody>'
               f'<tr><th scope="row">{assujetti}</th><td data-m="LexMachina"><b>{o1}</b>{ok}<small>{k("cmp.ex.assujetti.note.lm")}</small></td>'
               f'<td data-m="{e["moteur"]}"><b>{g1}</b><small>{k("cmp.ex.assujetti.note.gen")}</small></td></tr>'
               f'<tr><th scope="row">{k("cmp.ex.reference")}</th><td data-m="LexMachina"><b>{ref_lm}</b><small>{abrev}</small></td>'
               f'<td data-m="{e["moteur"]}"><b>{ref_gen}</b><small>{abrev}</small></td></tr></tbody></table>')
    notes = [mention[0], k("cmp.ex.verifie"), next(p for p in mention if p.startswith("Il s'agit d'un exemple ponctuel"))]
    return section(h2(titre, accent(titre, ("les banques",))) + f'<p class="intro">{brut(bloc(tete, "p"))}</p>'
                   + scene(1176, 440, ecran, sim="corrige", titre=e["fenetre"], curseur=False,
                           label=f"{e['moteur']} puis LexMachina sur une phrase de droit bancaire")
                   + lecture + carte_conclusion(k("cmp.ex.conclusion"), notes, k), ident="exemple")


def exemple_statique(t, cfg, k):
    """Page IA génératives : l'exemple de la V1 (une sortie fautive de LexMachina et l'alternative juste du même panneau),
    les deux sorties côte à côte, sans animation, puis la carte conclusion avec la note de la V1."""
    ex = bloc(t, "section", "cp-ex")
    tete = bloc(ex, "div", "sec-head")
    titre = txt(bloc(tete, "h2"))
    src = bloc(ex, "div", "cp-ex-src")
    cartes = []
    for c in blocs(ex, "div", "cp-ex-card"):
        faux = " bad" in c[:40]
        p = interne(bloc(c, "p")).strip().replace("<mark>", f'<mark class="{"cp-faux" if faux else "cp-juste"}">', 1)
        cartes.append(f'<div class="cp-xc{" cp-xc-f" if faux else ""}"><p class="cp-xe">{txt(bloc(c, "span", "cp-ex-eng"))}</p><p lang="de">{p}</p></div>')
    note = phrases(brut(bloc(ex, "p", "cp-ex-note")))
    cap = phrases(brut(bloc(ex, "p", "cp-ex-cap")))
    return section(h2(titre, accent(titre, ("la nôtre",))) + f'<p class="intro">{brut(bloc(tete, "p"))}</p>'
                   f'<div class="cp-xs"><p class="cp-xe">{txt(bloc(src, "p", "cp-ex-lbl"))}</p><p>{brut(blocs(src, "p")[1])}</p></div>'
                   f'<div class="cp-xg">{"".join(cartes)}</div>'
                   + carte_conclusion(note[0], [cap[0], note[1], cap[-1]], k), ident="exemple")


def exemple_preuve(t, cfg, k):
    """Page IA génératives : la sortie de ChatGPT (abréviation française gardée), celle de LexMachina (abréviation des
    textes fédéraux), puis la preuve dans CHnell (segments officiels alignés, scène « chnell »), et la carte conclusion."""
    def marque(texte_, terme, cls):
        return re.sub(r"\b" + re.escape(terme) + r"\b", f'<mark class="{cls}">{terme}</mark>', texte_)
    cartes = (f'<div class="cp-xc cp-xc-f"><p class="cp-xe">{k("cmp.ex.gpt.label")}</p><p lang="it">{marque(k("cmp.ex.gpt"), "LB", "cp-faux")}</p></div>'
              f'<div class="cp-xc"><p class="cp-xe">{k("cmp.ex.lm.label")}</p><p lang="it">{marque(k("cmp.ex.lm"), "LBCR", "cp-juste")}</p></div>')
    lookup = {"q": "LBCR", "l1": "Italian", "l2": "French", "count": texte(f"{cfg['cle']}.cmp.ex.chnell.count"),
              "rows": [{"a": texte(f"{cfg['cle']}.cmp.ex.chnell.a1"), "b": texte(f"{cfg['cle']}.cmp.ex.chnell.b1"),
                        "src": texte(f"{cfg['cle']}.cmp.ex.chnell.src1")}], "mark": ["LBCR", "LB"]}
    preuve = scene(1176, 340, V.vue_chnell(lookup), sim="chnell", curseur=False, titre="CHnell",
                   label="CHnell : LBCR et LB alignés dans les textes officiels")
    notes = [k("cmp.ex.note.releve"), k("cmp.ex.note.chnell"), k("cmp.ex.note.ponctuel")]
    return section(h2(k("cmp.ex.titre"), "la source qui tranche") + f'<p class="intro">{k("cmp.ex.intro")}</p>'
                   f'<div class="cp-xs"><p class="cp-xe">{k("cmp.ex.source.label")}</p><p>{k("cmp.ex.source")}</p></div>'
                   f'<div class="cp-xg">{cartes}</div>'
                   f'<h3 class="cp-pv">{k("cmp.ex.preuve.titre")}</h3>' + preuve
                   + carte_conclusion(k("cmp.ex.conclusion"), notes, k), ident="exemple")


def niveaux(t):
    """Page agence : les trois niveaux de relecture externe, tels que l'application les affiche (V1)."""
    sec = bloc(t, "section", "cp-lev")
    tete = bloc(sec, "div", "sec-head")
    cartes = []
    for i, it in enumerate(blocs(sec, "div", "cp-lev-item"), 1):
        n = bloc(it, "div", "n")
        sous = blocs(n, "small")
        nom = txt(re.sub(r"<small>.*?</small>", "", n, flags=re.S))
        cartes.append(f'<div class="cp-lv"><span class="cp-lv-n">{i}</span><h3>{nom}</h3>'
                      + (f'<p class="cp-lv-s">{txt(sous[0])}</p>' if sous else "") + f'<p>{brut(bloc(it, "p"))}</p></div>')
    titre = txt(bloc(tete, "h2"))
    return section(h2(titre, accent(titre, ("dans l'outil",))) + f'<p class="intro">{brut(bloc(tete, "p"))}</p>'
                   f'<div class="cp-lvg">{"".join(cartes)}</div><p class="legende">{brut(bloc(sec, "p", "cp-lev-note"))}</p>', ident="relecture")


def gouvernance(t, cfg):
    gov = bloc(t, "section", "gov")
    boite = bloc(gov, "div", "gov-box")
    titre = txt(bloc(boite, "h2"))
    lien = bloc(boite, "a", "feat-link")
    if cfg["gouvernance"] == "avis":
        demo = scene(900, 780, A.ecran_securite(*textes_demo()["notice"], esc(EX["co"]["src"]), esc(EX["co"]["out"]["en"]["main"])),
                     sim="avis", curseur=False, titre="Corrext", label="Choix du moteur et avis Attorney-Client privilege")
    else:
        demo = scene(764, 560, V.vue_devis("Darlehensvertrag_2026.docx", "DE → FR", NIVEAUX_RELECTURE, NIVEAUX_RELECTURE[1]),
                     sim="devis", curseur=False, titre="Corrext", label="Devis d'un projet avec relecture externe")
    pas = re.findall(r"<span>(<b>.*?)</span>\s*</div>", bloc(boite, "div", "gov-steps"), re.S)
    etapes = [(txt(bloc(x, "b")).rstrip("."), brut(re.sub(r"<b>.*?</b>", "", x, flags=re.S)).strip()) for x in pas]
    assert len(etapes) == 3, len(etapes)
    return section(f'<div class="cp-gv"><div>{h2(titre, accent(titre, ("un cabinet", "au cabinet", "les agences")))}<p>{brut(bloc(boite, "p"))}</p>'
                   f'<p class="cp-gv-l"><a class="lien" href="{re.search(r"href=\"([^\"]+)\"", lien).group(1)}">{txt(lien)}</a></p></div>'
                   + demo + "</div>" + tuiles([(None, b, p) for b, p in etapes], "tl txt"))


def autres(t):
    """Les autres comparatifs : cartes reliées (outils/post/fonctionnalites.py les illustre)."""
    vn = bloc(t, "section", "vn")
    cartes = []
    for a in blocs(vn, "a", "vs-card"):
        href = re.search(r'href="\{\{ROOT\}\}([^"]+)"', a).group(1)
        cible = (RACINE / "src/pages" / href[3:] / "index.html").read_text(encoding="utf-8")
        h1 = bloc(cible, "h1")
        cartes.append(f'<a href="{{{{ROOT}}}}{href}"><b>{txt(bloc(h1, "span", "n")).rstrip(".")}</b><p>{txt(bloc(h1, "span", "s"))}</p>'
                      f'<span class="lien">{txt(re.sub(r"<svg.*?</svg>", "", bloc(a, "em"), flags=re.S))}</span></a>')
    return section(h2(txt(bloc(vn, "h2"))) + '<div class="cd">' + "".join(cartes) + "</div>")


def exemple(t, cfg, k):
    typ = cfg["exemple"]["type"]
    if typ == "niveaux":
        return niveaux(t)
    return {"scene": exemple_scene, "statique": exemple_statique, "preuve": exemple_preuve}[typ](t, cfg, k)


def composer(P):
    cfg = PAGES[P]
    k = lambda c: esc(texte(f"{cfg['cle']}.{c}"))
    t = liens(charger(P), P)
    th = bloc(t, "section", "thero")
    h1 = bloc(th, "h1")
    out = [hero(txt(bloc(h1, "em")), txt(re.sub(r"<em>.*?</em>", "", h1, flags=re.S)), brut(bloc(th, "p", "lead")), ("Demander une démo", C)),
           en_bref(t, cfg),
           forces(t) if cfg["differences"] else modeles(t),
           tableau(t, cfg, k),
           exemple(t, cfg, k),
           gouvernance(t, cfg),
           autres(t),
           faq_section(t),
           cta_section(t, cfg["cta"])]
    corps = "".join(out)
    # corrections déclarées pour cette page (contenus-v2, champ « remplace ») : une phrase de la V1 remplacée mot pour mot
    for e in contenus.toutes():
        if e["page"] == P and "remplace" in e:
            ancien = esc(e["remplace"])
            assert corps.count(ancien) == 1, f"{P} : phrase à remplacer introuvable : {ancien[:60]}"
            corps = corps.replace(ancien, esc(e["texte"]))
    ecrire(P, entete_existant(P), corps)
    print(f"{P} écrite")


# Page générale des comparatifs (comparatif/), adaptée au même modèle (demande de Fabien du 2026-10-19)
HUB = {"cle": "comparatif", "groupes": None}
METHODE_IC = ["comparons", "pas", "autres", "corrext", "exemples", "date"]
ICONES.update({
    "comparons": '<path d="M20 6 9 17l-5-5"/>',
    "pas": '<circle cx="12" cy="12" r="9"/><path d="M8 12h8"/>',
    "autres": '<path d="M12 3v18M5 7h14M7 7l-3 7h6zM17 7l-3 7h6z"/>',
    "corrext": '<path d="m12 3 9 5-9 5-9-5z"/><path d="m3 13 9 5 9-5"/>',
    "exemples": '<path d="M14 3H7a2 2 0 0 0-2 2v14a2 2 0 0 0 2 2h10a2 2 0 0 0 2-2V8z"/><path d="M14 3v5h5M9 13h6M9 17h4"/>',
    "date": '<rect x="4" y="5" width="16" height="15" rx="2"/><path d="M8 3v4M16 3v4M4 10h16"/>',
})


def composer_hub():
    P = "comparatif/"
    k = lambda c: esc(texte(f"comparatif.{c}"))
    t = liens(charger(P), P)
    th = bloc(t, "section", "thero")
    h1 = bloc(th, "h1")
    out = [hero(txt(bloc(h1, "em")), txt(re.sub(r"<em>.*?</em>", "", h1, flags=re.S)), brut(bloc(th, "p", "lead")), ("Demander une démo", C))]
    # Trois comparaisons : cartes reliées, illustrées par outils/post/fonctionnalites.py
    ft_ = bloc(t, "section", "cph-feats")
    tete = bloc(ft_, "div", "sec-head")
    cartes = []
    for f in blocs(ft_, "div", "feature"):
        lien = bloc(f, "a", "feat-link")
        href = re.search(r'href="\{\{ROOT\}\}([^"]+)"', lien).group(1)
        h3 = bloc(f, "h3")
        cartes.append(f'<a href="{{{{ROOT}}}}{href}"><b>{txt(bloc(h3, "span", "pn")).rstrip(".")}</b><p>{brut(blocs(bloc(f, "div", "feat-txt"), "p")[0])}</p>'
                      '<span class="lien">Lire le comparatif</span></a>')  # libellé court et identique (cartes « Les autres comparatifs » de la V1)
    titre = txt(bloc(tete, "h2"))
    out.append(section(h2(titre, accent(titre, ("questions différentes",))) + f'<p class="intro">{brut(bloc(tete, "p"))}</p>'
                       '<div class="cd">' + "".join(cartes) + "</div>"))
    # Notre méthode : la promesse et les liens à gauche, les six engagements en liste à icônes à droite
    m = bloc(t, "section", "cph-method")
    lead = bloc(m, "div", "facts-lead")
    faits = blocs(m, "div", "fact")
    assert len(faits) == len(METHODE_IC), len(faits)
    liste = "".join(f'<li>{icone(ic)}<div><b>{txt(bloc(x, "b"))}</b><p>{brut(re.sub(r"<small>.*?</small>", "", bloc(x, "p"), flags=re.S))}</p>'
                    + "".join(f"<small>{txt(sm)}</small>" for sm in blocs(x, "small")) + "</div></li>" for x, ic in zip(faits, METHODE_IC))
    liens_m = "".join(f'<a class="lien" href="{re.search(r"href=\"([^\"]+)\"", a).group(1)}">{txt(a)}</a>' for a in blocs(bloc(lead, "div", "links"), "a"))
    out.append(section(f'<div class="cp-mt"><div class="cp-mt-g">{h2(txt(bloc(lead, "h2")))}<p>{brut(bloc(lead, "p"))}</p>'
                       f'<p class="cp-mt-l">{liens_m}</p></div><ul class="cp-mt-d">{liste}</ul></div>', ident="methode"))
    # Le tableau de synthèse, au style des pages comparatives
    out.append(tableau(t, HUB, k).replace('id="tableau"', 'id="synthese"', 1))
    out.append(autres_pour_aller_plus_loin(t))
    out.append(faq_section(t))
    out.append(cta_section(t, "La meilleure comparaison"))
    ecrire(P, entete_existant(P), "".join(out))
    print(f"{P} écrite")


def autres_pour_aller_plus_loin(t):
    """« Pour aller plus loin » de la page générale : cartes reliées aux pages outils (illustrées par le post)."""
    vn = bloc(t, "section", "vn")
    cartes = []
    for a in blocs(vn, "a", "vn-card"):
        href = re.search(r'href="\{\{ROOT\}\}([^"]+)"', a).group(1)
        cartes.append(f'<a href="{{{{ROOT}}}}{href}"><b>{txt(bloc(a, "b", "vn-t"))}</b><p>{brut(bloc(a, "span", "vn-d"))}</p>'
                      f'<span class="lien">{txt(re.sub(r"<svg.*?</svg>", "", bloc(a, "em"), flags=re.S))}</span></a>')
    return section(h2(txt(bloc(vn, "h2"))) + '<div class="cd">' + "".join(cartes) + "</div>")


if __name__ == "__main__":
    for p in PAGES:
        composer(p)
    composer_hub()
