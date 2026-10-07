"""Interface Corrext redessinée pour la scène d'accueil (libellés réels de l'application, textes remplis par sim.js)."""


def _ic(d, extra=""):
    return (f'<svg viewBox="0 0 16 16" aria-hidden="true" fill="none" stroke="currentColor" stroke-width="1.4" '
            f'stroke-linecap="round" stroke-linejoin="round"{extra}>{d}</svg>')


IC = {
    "texte": _ic('<path d="M3 4h10M3 8h10M3 12h6"/>'),
    "fichier": _ic('<path d="M4.5 1.8h4.8l2.9 2.9v9.5H4.5z"/><path d="M9.2 1.8v3h3"/>'),
    "pdf": _ic('<path d="M3 2.5h6v11H3z"/><path d="M11 5.5h2.5v8h-5.5"/>'),
    "reformuler": _ic('<path d="M3 13l.8-2.8L10.6 3.4l2 2-6.8 6.8z"/><path d="M9.2 4.8l2 2"/>'),
    "projet": _ic('<path d="M2 4.2h4.2l1.6 1.6H14v7.4H2z"/>'),
    "loupe": _ic('<circle cx="7" cy="7" r="4.2"/><path d="M10.2 10.2l3.4 3.4"/>'),
    "plus": _ic('<path d="M8 3.5v9M3.5 8h9"/>'),
    "fleche": _ic('<path d="M3 8h9.5M9.5 5l3 3-3 3"/>'),
    "envoi": _ic('<path d="M8 12.5V3.5M4.5 7L8 3.5 11.5 7"/>', ' stroke-width="1.8"'),
    "etincelle": _ic('<path d="M8 2.5l1.3 3.7L13 7.5l-3.7 1.3L8 12.5l-1.3-3.7L3 7.5l3.7-1.3z"/>'),
    "copier": _ic('<rect x="5.5" y="5.5" width="8" height="8" rx="1.5"/><path d="M10.5 5.5V3.5a1 1 0 0 0-1-1h-6a1 1 0 0 0-1 1v6a1 1 0 0 0 1 1h2"/>'),
}

EXTRAITS = [("co", "Contrat · art. 104 CO"), ("lb", "Banque · art. 47 LB"), ("ldip", "Arbitrage · art. 186 LDIP")]


def app_corrext():
    nav = (f'<span class="app-i on">{IC["texte"]}Text translation</span>'
           f'<span class="app-i">{IC["fichier"]}File translation</span>'
           f'<span class="app-i">{IC["pdf"]}PDF to Word</span>'
           f'<span class="app-i">{IC["reformuler"]}Rephrasing</span>')
    nav2 = (f'<span class="app-i">{IC["projet"]}Translation project</span>'
            f'<span class="app-i">{IC["loupe"]}Fast Lookup</span>')
    hist = "".join(f'<span class="app-h" data-k="{k}">{lib}</span>' for k, lib in EXTRAITS)
    return (
        '<div class="app" data-terme-co="intérêts moratoires" data-terme-lb="secret bancaire">'
        # Barre latérale
        '<div class="app-nav"><img class="app-logo" src="{{ROOT}}assets/img/corrext-logo.svg" alt="Corrext" width="84" height="18">'
        f'<span class="app-g">Fast translation</span>{nav}<span class="app-g">Corrext</span>{nav2}</div>'
        # Historique
        f'<div class="app-hist"><span class="app-new">{IC["plus"]}Text translation</span><div class="app-hl">{hist}</div></div>'
        # Zone principale
        '<div class="app-main"><div class="app-zone">'
        '<span class="app-t">Text translation</span>'
        '<div class="app-comp"><div class="app-src" data-ph="Enter the text you would like to translate."><span class="app-txt"></span></div>'
        f'<div class="app-bar"><span class="app-b">French</span>{IC["fleche"]}<span class="app-b">English</span>'
        f'<span class="app-b app-eng"><i></i>LexMachina</span><span class="app-send">{IC["envoi"]}</span></div></div>'
        '<div class="app-res"><div class="app-res-h"><span class="app-lg">English</span><span class="app-e">LexMachina</span>'
        f'<span class="app-act">{IC["etincelle"]}Generate more</span><span class="app-act app-cp">{IC["copier"]}</span></div>'
        '<p class="app-out"><span class="app-sk"></span><span class="app-sk"></span><span class="app-sk"></span></p>'
        '<div class="app-seg"><i class="app-pill"></i><span class="on" data-i="0">LexMachina</span>'
        '<span data-i="1">DeepL Pro</span><span data-i="2">Azure OpenAI - GPT</span></div></div>'
        '</div>'
        # Tiroir Fast Lookup
        f'<div class="app-lk"><div class="app-lk-h">{IC["loupe"]}<span>Fast Lookup</span></div>'
        f'<div class="app-lk-q"><b class="lk-q"></b><span class="lk-l1"></span>{IC["fleche"]}<span class="lk-l2"></span></div>'
        '<span class="lk-c"></span><div class="lk-r"></div><span class="app-b app-ctx">Show in context</span></div>'
        '</div></div>'
    )
