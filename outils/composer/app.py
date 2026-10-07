"""Écran Corrext « Text translation » reproduit pour la scène d'accueil.

Structure, libellés et textes de l'application réelle (démo Corrext du site Neur.on) ; seul le rendu est affiné.
Les textes dynamiques (frappe, sorties, résultats CHnell) sont remplis par sim.js depuis SIM_EX.
"""


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
}

ENGINES = ["LexMachina", "DeepL Pro", "Azure OpenAI - GPT"]


def app_corrext(notice_titre, notice_texte, hint_ill, hint_titre, hint_texte):
    """Les textes de l'avis et de l'encart d'aide sont passés tels qu'extraits de la démo publiée."""
    menu = "".join(f'<span{" class=\"on\"" if i == 0 else ""} data-v="{e}">{e}</span>' for i, e in enumerate(ENGINES))
    pied = f'<span class="cr-ur">{IC["annuler"]}{IC["retablir"]}</span>'
    return (
        '<div class="cr" data-terme-co="intérêts moratoires" data-terme-lb="secret bancaire">'
        # Barre du haut
        '<div class="cr-top"><img class="cr-logo" src="{{ROOT}}assets/img/corrext-logo.svg" alt="Corrext" width="88" height="18">'
        f'<span class="cr-home">Home</span><span class="cr-sp"></span><span class="cr-bell">{IC["cloche"]}</span><span class="cr-av">AM</span></div>'
        # Avis (moteur tiers)
        f'<div class="cr-notice">{IC["info"]}<div><b>{notice_titre}</b><p>{notice_texte}</p></div></div>'
        '<div class="cr-corps">'
        # Onglets et interrupteur
        '<div class="cr-tabs"><div class="cr-tl"><span class="on">Text translation</span><span>File translation</span>'
        '<span>PDF to Word</span><span>Rephrasing</span></div>'
        '<span class="cr-sw on"><i></i>Highly sensitive content</span></div>'
        # Espace de travail
        '<div class="cr-work"><div class="cr-bar">'
        f'<span class="cr-sel cr-src"><span class="v0">Detect language</span><span class="v1">Detected language (French)</span>{IC["chevron"]}</span>'
        f'<span class="cr-swap">{IC["echange"]}</span>'
        f'<span class="cr-sel"><span>English</span>{IC["chevron"]}</span>'
        f'<span class="cr-sel cr-eng"><span class="cr-eng-v">LexMachina</span>{IC["chevron"]}<span class="cr-menu">{menu}</span></span>'
        '</div><div class="cr-panes">'
        f'<div class="cr-pane cr-in" data-ph="Enter the text you would like to translate."><p class="cr-txt"></p>'
        f'<span class="cr-ic cr-clear">{IC["croix"]}</span><span class="cr-lkb">{IC["loupe"]}Fast Lookup</span>'
        f'<div class="cr-foot">{pied}<span class="cr-cnt">0 / 10000</span></div></div>'
        f'<div class="cr-pane cr-tgt"><p class="cr-out"><span class="cr-sk"></span><span class="cr-sk"></span><span class="cr-sk"></span></p><span class="cr-ic cr-cp">{IC["copier"]}</span>'
        f'<span class="cr-ic cr-spark">{IC["etincelle"]}</span><div class="cr-foot">{pied}</div></div>'
        '</div></div>'
        # Sous l'espace de travail : encart d'aide ou alternatives
        '<div class="cr-bas">'
        f'<div class="cr-hint"><div class="cr-ill">{hint_ill}</div><div><b>{hint_titre}</b><p>{hint_texte}</p></div></div>'
        f'<div class="cr-alts"><div class="cr-alts-h"><b>Alternatives</b><span class="cr-gen">{IC["etincelle"]}Generate more</span>'
        f'<span class="cr-pg"><span class="cr-pgn">1 / 2</span><span class="cr-ic cr-up">{IC["haut"]}</span>'
        f'<span class="cr-ic cr-dn">{IC["bas"]}</span><span class="cr-ic cr-ax">{IC["croix"]}</span></span></div>'
        '<p class="cr-alt"><span class="cr-alt-ph">Generating alternatives…</span></p><span class="cr-alt-e"></span></div>'
        '</div></div>'
        # Fast Lookup : CHnell
        '<div class="cr-modal"><div class="cr-ch">'
        '<div class="cr-ch-h"><img src="{{ROOT}}assets/img/chnell-logo.svg" alt="CHnell" width="78" height="22"><span>powered by Neur.on</span></div>'
        f'<div class="cr-ch-q"><span class="cr-box">{IC["loupe"]}<b class="lk-q"></b></span><span class="cr-lang lk-l1"></span>'
        f'<span class="cr-swap">{IC["echange"]}</span><span class="cr-lang lk-l2"></span><span class="lk-c"></span></div>'
        '<div class="lk-r"></div>'
        '<div class="cr-ch-f"><span class="cr-more">Show more results</span><span class="cr-btn">Close</span></div>'
        '</div></div>'
        '</div>'
    )
