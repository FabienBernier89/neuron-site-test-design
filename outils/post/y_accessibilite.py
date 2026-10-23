"""Accessibilité (audit du 2026-10-23, docs/audits/2026-10-23-neuron-v2/annexe-perf.md). Nommé « y_ » pour passer
après les post-traitements qui posent les blocs concernés (cartes .fx-g de fonctionnalites.py), avant z_formulaires.

- Bouton pause des animations en boucle (WCAG 2.2.2) : un par scène animée (.st[data-sim], câblé par assets/sim.js)
  et un par grille de cartes animées (.fx-g, câblé par assets/global/animations.js). Le bouton naît masqué (hidden) :
  le script l'affiche, sauf en mouvement réduit, où rien ne bouge. Libellés lus dans src/data/contenus-v2.
- Listes d'onglets (role="tablist") : nommées par le titre h2 de leur section (aria-labelledby).
- Passages en allemand, anglais ou italien dont la langue est connue (WCAG 3.1.2) : lignes alignées de CHnell (langues
  affichées dans la barre de recherche), cellules des tableaux de termes (data-m="Allemand"...), tuiles « quatre
  langues » et terme du h1 du glossaire, avis et encart d'aide en anglais des écrans Corrext reproduits.

Aucun texte affiché n'est ajouté ici. Idempotent : repasser une page déjà traitée ne la change pas."""
import html as H
import re

from outils import contenus

# Noms de langue affichés (interface Corrext en anglais, pages en français) et code BCP 47
CODES = {"German": "de", "Allemand": "de", "English": "en", "Anglais": "en", "Italian": "it", "Italien": "it",
         "French": "fr", "Français": "fr"}

PAUSE = ('<svg class="ap-pause" viewBox="0 0 16 16" aria-hidden="true" focusable="false"><rect x="4" y="3" width="2.6" '
         'height="10" rx="1"/><rect x="9.4" y="3" width="2.6" height="10" rx="1"/></svg>')
LECTURE = ('<svg class="ap-lecture" viewBox="0 0 16 16" aria-hidden="true" focusable="false"><path d="M5 3.2v9.6a.6.6 0 0 0 '
           '.9.5l7.4-4.8a.6.6 0 0 0 0-1L5.9 2.7a.6.6 0 0 0-.9.5z"/></svg>')
SCENE = re.compile(r'(<div class="st" data-sim="[^"]*"[^>]*>)(?!<button type="button" class="anim-pause)')
GRILLE = re.compile(r'(?<!</button>)(<div class="fx-g(?: [^"]*)?">)')
ONGLETS = re.compile(r'(<h2\b[^>]*>)((?:(?!<h2\b|role="tablist").)*?)(<div class="mt-os" role="tablist")(?=>)', re.S)


def _a(s):
    return H.escape(s, quote=True)


def bouton(classe):
    """Bouton pause / lecture : le nom change avec l'état (data-pause, data-relancer), l'icône suit (CSS)."""
    pause, relancer = contenus.texte("a11y.animation.pause"), contenus.texte("a11y.animation.relancer")
    return (f'<button type="button" class="anim-pause {classe}" hidden aria-label="{_a(pause)}" '
            f'data-pause="{_a(pause)}" data-relancer="{_a(relancer)}">{PAUSE}{LECTURE}</button>')


def boutons_pause(html):
    html = SCENE.sub(lambda m: m.group(1) + bouton("sim-pp"), html)
    return GRILLE.sub(lambda m: bouton("fx-pp") + m.group(1), html)


def onglets_nommes(html):
    """Chaque liste d'onglets reçoit aria-labelledby vers le h2 qui la précède dans sa section."""
    n = [0]

    def nommer(m):
        h2, entre, liste = m.groups()
        ident = re.search(r'\sid="([^"]+)"', h2)
        if ident:
            ident = ident.group(1)
        else:
            n[0] += 1
            ident = f"onglets-titre-{n[0]}"
            h2 = h2[:-1] + f' id="{ident}">'
        return h2 + entre + liste + f' aria-labelledby="{ident}"'
    if 'role="tablist" aria-labelledby' in html:
        return html
    return ONGLETS.sub(nommer, html)


def _lang(balise, code):
    """Pose lang sur une balise ouvrante qui n'en a pas (le français, langue de la page, n'est pas répété)."""
    if not code or code == "fr" or " lang=" in balise:
        return balise
    return balise[:-1] + f' lang="{code}">'


LIGNE =re.compile(r'(<div style="--i:\d+">)(<p>)(.*?</p>)(<p>)')


def langues_chnell(html):
    """Lignes alignées de CHnell : la 1re colonne dans la langue de gauche (lk-l1), la 2e dans celle de droite (lk-l2) ;
    le terme recherché (lk-q) dans la langue de gauche."""
    sortie, pos = [], 0
    for q in re.finditer(r'<div class="cr-ch-q">', html):
        if q.start() < pos:
            continue
        l1 = re.search(r'<span class="cr-lang lk-l1">([^<]*)</span>', html[q.start():q.start() + 2000])
        l2 = re.search(r'<span class="cr-lang lk-l2">([^<]*)</span>', html[q.start():q.start() + 2000])
        lr = html.find('<div class="lk-r">', q.start())
        if not (l1 and l2) or lr < 0:
            continue
        a, b = CODES.get(l1.group(1).strip()), CODES.get(l2.group(1).strip())
        if not (a or b):
            continue
        # fin des lignes : pied de la fenêtre CHnell, sinon bloc CHnell suivant ou fin de la section
        bornes = [html.find(b, lr) for b in ('<div class="cr-ch-f">', '<div class="cr-ch-q">', "</section>")]
        fin = min([b for b in bornes if b >= 0] or [len(html)])
        bloc = html[q.start():fin]
        bloc = re.sub(r'<b class="lk-q">', lambda m: _lang(m.group(0), a), bloc, count=1)
        bloc = LIGNE.sub(lambda m: m.group(1) + _lang(m.group(2), a) + m.group(3) + _lang(m.group(4), b), bloc)
        sortie.append(html[pos:q.start()] + bloc)
        pos = fin
    return "".join(sortie) + html[pos:]


def langues_tableaux(html):
    """Cellules des tableaux de termes, étiquetées par leur colonne (data-m) ; tuiles « quatre langues » du glossaire
    (<b>terme</b><p>Allemand</p>) ou fiche des langues (<dt>Allemand</dt><dd>terme</dd>) ; terme du h1 du glossaire, s'il
    figure dans l'une ou l'autre."""
    html = re.sub(r'<(th|td)\b[^>]*\sdata-m="([^"]+)"[^>]*>', lambda m: _lang(m.group(0), CODES.get(m.group(2))), html)
    tuiles = {}

    def tuile(m):
        code = CODES.get(m.group(3))
        tuiles[H.unescape(m.group(2)).strip()] = code
        return _lang(m.group(1), code) + m.group(2) + "</b><p>" + m.group(3) + "</p>"
    html = re.sub(r'(<b>)([^<]+)</b><p>(Allemand|Français|Italien|Anglais)</p>', tuile, html)
    # fiche des langues du glossaire (langue, terme ; audit design du 2026-10-23) : la langue y est déjà posée
    for m in re.finditer(r'<dt>(Allemand|Français|Italien|Anglais)</dt><dd lang="([a-z]{2})">([^<]+)</dd>', html):
        tuiles[H.unescape(m.group(3)).strip()] = m.group(2)
    h1 = re.search(r'(<h1 class="h1"><span class="n")(>)([^<]+?)( ·)?</span>', html)
    if h1 and tuiles.get(H.unescape(h1.group(3)).strip()):
        code = tuiles[H.unescape(h1.group(3)).strip()]
        if code != "fr" and " lang=" not in h1.group(1):
            html = html[:h1.start()] + h1.group(1) + f' lang="{code}"' + html[h1.start(2):]
    return html


def langues_interface(html):
    """Avis et encart d'aide de l'écran Corrext reproduit : phrases de l'interface, en anglais dans l'application."""
    html = html.replace('<div class="cr-notice">', '<div class="cr-notice" lang="en">')
    return re.sub(r'(<div class="cr-hint"><div class="cr-ill">(?:[^<]|</?mark>)*</div>)<div>', r'\1<div lang="en">', html)


def traiter(html, page):
    debut = html.find('<main id="main">')
    if debut < 0:
        return html
    tete, corps = html[:debut], html[debut:]
    corps = boutons_pause(corps)
    corps = onglets_nommes(corps)
    corps = langues_chnell(corps)
    corps = langues_tableaux(corps)
    corps = langues_interface(corps)
    return tete + corps
