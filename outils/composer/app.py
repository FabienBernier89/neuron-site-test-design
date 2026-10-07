"""Écrans Corrext reproduits pour les scènes du site de test (structure, libellés et données de l'application réelle).

Seul le rendu est affiné. Les textes viennent de la démo Corrext publiée (passés en paramètres ou lus dans SIM_EX
par sim.js) ; aucun libellé n'est inventé.
"""
import html as _h


def _ic(d, extra=""):
    return (f'<svg viewBox="0 0 16 16" aria-hidden="true" fill="none" stroke="currentColor" stroke-width="1.4" '
            f'stroke-linecap="round" stroke-linejoin="round"{extra}>{d}</svg>')


IC = {
    "cloche": _ic('<path d="M4.2 11.5V7.4a3.8 3.8 0 0 1 7.6 0v4.1l1.2 1.3H3z"/><path d="M6.6 14.2a1.5 1.5 0 0 0 2.8 0"/>'),
    "chevron": _ic('<path d="M4.5 6.5L8 10l3.5-3.5"/>'),
    "echange": _ic('<path d="M3 5.5h9.5M10 3l2.5 2.5L10 8M13 10.5H3.5M6 8l-2.5 2.5L6 13"/>'),
    "croix": _ic('<path d="M4.5 4.5l7 7M11.5 4.5l-7 7"/>'),
    "copier": _ic('<rect x="5.5" y="5.5" width="8" height="8" rx="1.6"/><path d="M10.5 5.5V3.6a1.1 1.1 0 0 0-1.1-1.1H3.6a1.1 1.1 0 0 0-1.1 1.1v5.8a1.1 1.1 0 0 0 1.1 1.1h1.9"/>'),
    "etincelle": _ic('<path d="M8 2.2l1.3 3.6 3.6 1.3-3.6 1.3L8 12l-1.3-3.6L3.1 7.1l3.6-1.3z"/><path d="M12.6 11.2l.5 1.3 1.3.5-1.3.5-.5 1.3-.5-1.3-1.3-.5 1.3-.5z"/>'),
    "annuler": _ic('<path d="M5 6.5H10a3 3 0 0 1 0 6H7"/><path d="M7 4.5L5 6.5l2 2"/>'),
    "retablir": _ic('<path d="M11 6.5H6a3 3 0 0 0 0 6h3"/><path d="M9 4.5l2 2-2 2"/>'),
    "loupe": _ic('<circle cx="7" cy="7" r="4.2"/><path d="M10.2 10.2l3.4 3.4"/>'),
    "haut": _ic('<path d="M4.5 9.5L8 6l3.5 3.5"/>'),
    "bas": _ic('<path d="M4.5 6.5L8 10l3.5-3.5"/>'),
    "info": _ic('<circle cx="8" cy="8" r="6"/><path d="M8 7.3v3.6M8 5.1v.1"/>'),
    "depot": _ic('<path d="M8 10.5V3.5M5 6.5l3-3 3 3"/><path d="M3 10.5v1.8A1.2 1.2 0 0 0 4.2 13.5h7.6a1.2 1.2 0 0 0 1.2-1.2v-1.8"/>'),
    "fichier": _ic('<path d="M4.5 1.8h4.8l2.9 2.9v9.5H4.5z"/><path d="M9.2 1.8v3h3"/>'),
    "cadenas": _ic('<rect x="3.5" y="7" width="9" height="6.5" rx="1.5"/><path d="M5.5 7V5.2a2.5 2.5 0 0 1 5 0V7"/>'),
}

ENGINES = ["LexMachina", "DeepL Pro", "Azure OpenAI - GPT"]
ONGLETS = ["Text translation", "File translation", "PDF to Word", "Rephrasing"]


def e(s):
    return _h.escape(s, quote=False)


# ---------- Morceaux d'écran ----------

def barre_haut():
    return ('<div class="cr-top"><img class="cr-logo" src="{{ROOT}}assets/img/corrext-logo.svg" alt="Corrext" width="88" height="18">'
            f'<span class="cr-home">Home</span><span class="cr-sp"></span><span class="cr-bell">{IC["cloche"]}</span><span class="cr-av">AM</span></div>')


def avis(titre, texte):
    return f'<div class="cr-notice">{IC["info"]}<div><b>{titre}</b><p>{texte}</p></div></div>'


def onglets(actif=0, hs=True, interrupteur=True):
    sp = "".join(f'<span{" class=\"on\"" if i == actif else ""} data-t="{i}">{o}</span>' for i, o in enumerate(ONGLETS))
    sw = f'<span class="cr-sw{" on" if hs else ""}"><i></i>Highly sensitive content</span>' if interrupteur else ""
    return f'<div class="cr-tabs"><div class="cr-tl"><i class="cr-tl-pill"></i>{sp}</div>{sw}</div>'


def menu(valeurs, actif, suisse=False):
    items = []
    for v in valeurs:
        sui = '<small>Suisse</small>' if suisse and v == "LexMachina" else f'<em>{IC["cadenas"]}</em>' if suisse else ""
        items.append(f'<span{" class=\"on\"" if v == actif else ""} data-v="{v}">{v}{sui}</span>')
    return f'<span class="cr-menu">{"".join(items)}</span>'


def selecteur(valeur, classe="", valeurs=None, suisse=False):
    m = menu(valeurs, valeur, suisse) if valeurs else ""
    return f'<span class="cr-sel {classe}"><span class="cr-v">{valeur}</span>{IC["chevron"]}{m}</span>'


def barre_travail(detecte=False, cible="English", moteur="LexMachina", suisse=False):
    src = (f'<span class="cr-sel cr-src{" detecte" if detecte else ""}"><span class="v0">Detect language</span>'
           f'<span class="v1">Detected language (French)</span>{IC["chevron"]}</span>')
    return (f'<div class="cr-bar">{src}<span class="cr-swap">{IC["echange"]}</span>'
            f'{selecteur(cible, "cr-tgtsel", ["German", "English", "Italian"])}'
            f'{selecteur(moteur, "cr-eng", ENGINES, suisse)}</div>')


def panneaux(src="", out="", cnt="0 / 10000", ph="Enter the text you would like to translate.", squelette=True):
    pied = f'<span class="cr-ur">{IC["annuler"]}{IC["retablir"]}</span>'
    sk = '<span class="cr-sk"></span><span class="cr-sk"></span><span class="cr-sk"></span>' if squelette and not out else ""
    rempli = " rempli" if src else ""
    return ('<div class="cr-panes">'
            f'<div class="cr-pane cr-in{rempli}" data-ph="{ph}"><p class="cr-txt">{src}</p>'
            f'<span class="cr-ic cr-clear">{IC["croix"]}</span><span class="cr-lkb">{IC["loupe"]}Fast Lookup</span>'
            f'<div class="cr-foot">{pied}<span class="cr-cnt">{cnt}</span></div></div>'
            f'<div class="cr-pane cr-tgt"><p class="cr-out{" vu" if out else ""}">{out or sk}</p><span class="cr-ic cr-cp">{IC["copier"]}</span>'
            f'<span class="cr-ic cr-spark">{IC["etincelle"]}</span><div class="cr-foot">{pied}</div></div>'
            '</div>')


def travail(**k):
    bt = {x: k.pop(x) for x in ("detecte", "cible", "moteur", "suisse") if x in k}
    return f'<div class="cr-work">{barre_travail(**bt)}{panneaux(**k)}</div>'


def encart(ill, titre, texte):
    return f'<div class="cr-hint"><div class="cr-ill">{ill}</div><div><b>{titre}</b><p>{texte}</p></div></div>'


def alternatives(texte="", moteur=""):
    corps = texte or '<span class="cr-alt-ph">Generating alternatives…</span>'
    chip = f'<span class="cr-alt-e{" on" if moteur else ""}">{moteur}</span>'
    return (f'<div class="cr-alts"><div class="cr-alts-h"><b>Alternatives</b><span class="cr-gen">{IC["etincelle"]}Generate more</span>'
            f'<span class="cr-pg"><span class="cr-pgn">1 / 2</span><span class="cr-ic cr-up">{IC["haut"]}</span>'
            f'<span class="cr-ic cr-dn">{IC["bas"]}</span><span class="cr-ic cr-ax">{IC["croix"]}</span></span></div>'
            f'<p class="cr-alt{" vu" if texte else ""}">{corps}</p>{chip}</div>')


def chnell(q="", l1="", l2="", compte="", lignes_html=""):
    return ('<div class="cr-ch">'
            '<div class="cr-ch-h"><img src="{{ROOT}}assets/img/chnell-logo.svg" alt="CHnell" width="78" height="22"><span>powered by Neur.on</span></div>'
            f'<div class="cr-ch-q"><span class="cr-box">{IC["loupe"]}<b class="lk-q">{q}</b></span><span class="cr-lang lk-l1">{l1}</span>'
            f'<span class="cr-swap">{IC["echange"]}</span><span class="cr-lang lk-l2">{l2}</span><span class="lk-c">{compte}</span></div>'
            f'<div class="lk-r">{lignes_html}</div>'
            '<div class="cr-ch-f"><span class="cr-more">Show more results</span><span class="cr-btn">Close</span></div>'
            '</div>')


def lignes_chnell(lookup):
    """Lignes alignées de CHnell, terme recherché surligné (rendu statique)."""
    q = e(lookup["q"])
    out = []
    for i, r in enumerate(lookup["rows"]):
        out.append(f'<div style="--i:{i}"><p>{e(r["a"]).replace(q, "<mark>" + q + "</mark>")}</p><p>{e(r["b"])}</p><small>{e(r["src"])}</small></div>')
    return "".join(out)


# ---------- Écrans complets ----------

def app_corrext(notice_titre, notice_texte, hint_ill, hint_titre, hint_texte):
    """Accueil : écran « Text translation » complet."""
    return ('<div class="cr" data-terme-co="intérêts moratoires" data-terme-lb="secret bancaire">'
            + barre_haut() + avis(notice_titre, notice_texte)
            + '<div class="cr-corps">' + onglets() + travail()
            + '<div class="cr-bas">' + encart(hint_ill, hint_titre, hint_texte) + alternatives() + '</div></div>'
            + '<div class="cr-modal">' + chnell() + '</div></div>')


def ecran_outil(notice_titre, notice_texte, hint_ill, hint_titre, hint_texte, fichier, pdf, reph):
    """Page outil : les quatre onglets de Traduction texte et document, dans une même fenêtre.

    fichier, pdf : dict(drop_t, drop_s, nom, sous, run, fin) ; reph : dict(styles, options, reset, apply, ph).
    """
    def depot(d):
        return (f'<p class="cr-h4">Upload your file(s)</p><div class="cr-drop">{IC["depot"]}<span class="t">{d["drop_t"]}</span>'
                f'<span class="s">{d["drop_s"]}</span></div>'
                f'<div class="cr-file">{IC["fichier"]}<span class="fm"><span class="fn">{d["nom"]}</span><span class="fs">{d["sous"]}</span>'
                f'<span class="bar"><i></i></span></span><span class="cr-st"><span class="s0">{d["run"]}</span><span class="s1">{d["fin"]}</span></span></div>')
    cfg = ('<div class="cr-cfg"><div><label>Translation engine</label>' + selecteur("LexMachina") + '</div>'
           '<div><label>Translation target language</label>' + selecteur("French") + '</div></div>')
    chips = "".join(f'<span class="cr-chip" data-s="{s}">{s}</span>' for s in reph["styles"])
    opts = "".join(f'<span class="cr-chip">{s}</span>' for s in reph["options"])
    pop = (f'<div class="cr-pop"><p class="cr-h5">Styles</p><div class="cr-chips">{chips}</div>'
           f'<p class="cr-h5">Options</p><div class="cr-chips">{opts}</div>'
           f'<div class="cr-pop-a"><span class="cr-rst">{reph["reset"]}</span><span class="cr-btn cr-btn-p">{reph["apply"]}</span></div></div>')
    barre_reph = (f'<div class="cr-bar"><span class="cr-sel cr-src detecte"><span class="v0">Detect language</span><span class="v1">Detected language (French)</span>{IC["chevron"]}</span>'
                  f'<span class="cr-swap">{IC["echange"]}</span><span class="cr-sel cr-set"><span class="cr-v">Settings</span><i class="cr-dot"></i>{IC["chevron"]}{pop}</span></div>')
    pied = f'<span class="cr-ur">{IC["annuler"]}{IC["retablir"]}</span>'
    panes_reph = ('<div class="cr-panes">'
                  f'<div class="cr-pane cr-in" data-ph="{reph["ph"]}"><p class="cr-txt cr-rtxt"></p>'
                  f'<div class="cr-foot">{pied}<span class="cr-cnt cr-rcnt">0 / 5000</span></div></div>'
                  f'<div class="cr-pane cr-tgt"><p class="cr-out cr-rout"></p><span class="cr-ic cr-cp">{IC["copier"]}</span><div class="cr-foot">{pied}</div></div></div>')
    vues = ('<div class="cr-vues">'
            '<div class="cr-vue on" data-t="0">' + travail() + '<div class="cr-bas">' + encart(hint_ill, hint_titre, hint_texte) + alternatives() + '</div></div>'
            '<div class="cr-vue cr-upl" data-t="1">' + cfg + depot(fichier) + '</div>'
            '<div class="cr-vue cr-upl" data-t="2">' + depot(pdf) + '</div>'
            f'<div class="cr-vue" data-t="3"><div class="cr-work">{barre_reph}{panes_reph}</div></div>'
            '</div>')
    return ('<div class="cr cr-outil" data-terme-co="intérêts moratoires" data-terme-lb="secret bancaire">'
            + barre_haut() + avis(notice_titre, notice_texte)
            + '<div class="cr-corps">' + onglets() + vues + '</div></div>')


def ecran_securite(notice_titre, notice_texte, src, out):
    """Sécurité : interrupteur, choix du moteur et avis, sur un extrait déjà traduit."""
    return ('<div class="cr cr-sec">' + barre_haut() + avis(notice_titre, notice_texte)
            + '<div class="cr-corps">' + onglets() + travail(detecte=True, src=src, out=out, suisse=True)
            + '</div></div>')


def ecran_comparaison(src, sortie_html, alt_html, alt_moteur):
    """LexMachina : sortie du moteur et alternative DeepL Pro, écarts surlignés (textes de la section « quatre caractères »)."""
    return ('<div class="cr cr-frag cr-q4">' + travail(detecte=True, src=src, out="")
            .replace('<p class="cr-out">', f'<p class="cr-out" data-html="{_h.escape(sortie_html)}">', 1)
            + '<div class="cr-bas">' + alternatives().replace('<p class="cr-alt">', f'<p class="cr-alt" data-html="{_h.escape(alt_html)}">', 1)
            .replace('<span class="cr-alt-e">', f'<span class="cr-alt-e" data-v="{alt_moteur}">', 1) + '</div></div>')


def fragment_travail(src="", out="", detecte=False, cible="English", moteur="LexMachina", suisse=False, classe=""):
    """Espace de traduction seul (boucles par fonctionnalité, panneaux statiques)."""
    return (f'<div class="cr cr-frag {classe}">'
            + travail(detecte=detecte or bool(src), cible=cible, moteur=moteur, suisse=suisse, src=src, out=out) + '</div>')


def fragment_moteurs(src, out):
    """Interrupteur Highly sensitive et menu des moteurs (boucle « Moteurs »)."""
    return ('<div class="cr cr-frag cr-hs">' + onglets(interrupteur=True, hs=False)
            + travail(detecte=True, src=src, out=out, suisse=True) + '</div>')


def fragment_chnell(lookup):
    return f'<div class="cr cr-frag cr-chst">{chnell(e(lookup["q"]), e(lookup["l1"]), e(lookup["l2"]), e(lookup["count"]), lignes_chnell(lookup))}</div>'


def tableau_bord(onglets_dash, panneaux_dash, donnees, kpis):
    """Hub : tableau de bord de Corrext (onglets, panneaux et indicateurs repris de la reproduction publiée)."""
    tl = "".join(f'<span{" class=\"on\"" if i == 0 else ""} data-t="{i}">{o}</span>' for i, o in enumerate(onglets_dash))
    pans = "".join(f'<div class="cr-panel{" on" if i == 0 else ""}" data-t="{i}">{p}</div>' for i, p in enumerate(panneaux_dash))
    return ('<div class="cr cr-dash">' + barre_haut()
            + f'<div class="cr-corps"><div class="cr-tabs"><div class="cr-tl"><i class="cr-tl-pill"></i>{tl}</div><span class="cr-data">{donnees}</span></div>'
            + f'<div class="cr-dp">{pans}</div><div class="cr-kpis">{kpis}</div></div></div>')
