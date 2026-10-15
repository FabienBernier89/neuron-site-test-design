"""Blocs de liens vers les fonctionnalités : cartes illustrées d'une mini-interface Corrext animée.

Retour de Fabien du 2026-10-15 : les blocs « Les autres outils de Corrext », « Pour aller plus loin », « Les outils les
plus utilisés »... reprennent la construction de la référence (grand visuel, une seule mini-interface animée, titre,
texte, lien). Tout bloc de cartes (.cd) dont CHAQUE lien mène à une page de VISUELS est reconstruit ; les autres
(glossaire, ressources, blocs mixtes) ne changent pas.

Les libellés des mini-interfaces viennent des vignettes d'outil de la V1 (src/generators.py, VIGNETTES), des démos
publiées et des pages du site (tableau des trois modes, niveaux de qualité, langues et formats) : rien n'est inventé.
Les animations sont en CSS (assets/composants/fonctionnalites.css) ; sans animation (mouvement réduit), chaque
mini-interface montre son état final.
"""
import re

FLECHE = ('<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" '
          'stroke-linejoin="round" aria-hidden="true"><path d="M5 12h14M13 6l6 6-6 6"/></svg>')
COCHE = ('<svg class="u-ck" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.6" '
         'stroke-linecap="round" stroke-linejoin="round" aria-hidden="true"><path d="M20 6 9 17l-5-5"/></svg>')
LOUPE = ('<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.2" stroke-linecap="round" '
         'stroke-linejoin="round" aria-hidden="true"><circle cx="11" cy="11" r="7"/><path d="m20 20-3.5-3.5"/></svg>')
LIVRE = ('<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" '
         'stroke-linejoin="round" aria-hidden="true"><path d="M4 19.5A2.5 2.5 0 0 1 6.5 17H20V3H6.5A2.5 2.5 0 0 0 4 5.5z"/></svg>')


def _etape(libelle, i):
    return f'<span class="u-et u-et{i}"><b>{COCHE}</b>{libelle}</span>'


VISUELS = {
    # V1 « outil-texte » : la sortie anglaise s'écrit à côté du texte source
    "fr/corrext/traduction-texte-et-document/": (
        '<div class="u-lg">French → English <span class="u-chip">LexMachina</span></div>'
        '<div class="u-2"><div lang="fr">Le débiteur en demeure doit des intérêts moratoires au taux de 5% l\'an …</div>'
        '<div lang="en"><span class="u-out">The debtor in default shall owe default interest at the rate of 5% per annum …</span></div></div>'),
    # V1 « outil-projet » : étapes cochées l'une après l'autre, puis choix de la relecture
    "fr/corrext/gestion-de-projet/": (
        '<div class="u-lbl">Translation project</div>'
        '<div class="u-st">' + _etape("Set-up", 1) + "<i></i>" + _etape("File overview", 2) + "<i></i>"
        '<span class="u-et u-cur"><b>3</b>Quotes</span></div>'
        '<div class="u-opts"><div class="u-op u-op1"><b>Internal review</b><span>par vos équipes</span></div>'
        '<div class="u-op u-op2"><b>Custom workflow</b><span>traducteur juridique</span></div></div>'),
    # V1 « outil-lexmachina » : l'interrupteur grise les moteurs tiers, la sélection passe sur LexMachina
    "fr/lexmachina/": (
        '<div class="u-row"><span class="u-fort">Highly sensitive content</span><span class="u-sw"></span></div>'
        '<div class="u-list"><div class="u-it u-lm"><span>LexMachina <small>Suisse</small></span>' + COCHE + '</div>'
        '<div class="u-it u-dp"><span>DeepL Pro</span>' + COCHE + '</div>'
        '<div class="u-it u-az"><span>Azure OpenAI GPT</span></div></div>'),
    # V1 « outil-chnell » : recherche, occurrences surlignées, source officielle
    "fr/corrext/chnell/": (
        f'<div class="u-q">{LOUPE}<b>Verzugszins</b><span>German → French</span></div>'
        '<div class="u-res"><div lang="de">… den fehlenden Betrag zuzüglich <mark>Verzugszins</mark> nicht mehr nachbelasten …</div>'
        '<div lang="fr">… prélever le montant manquant avec l\'<mark>intérêt moratoire</mark> …</div></div>'
        f'<div class="u-src">{LIVRE}Feuille fédérale</div>'),
    # V1 « outil-extraits » : le niveau de certification descend jusqu'à l'apostille
    "fr/corrext/extraits-registre-commerce/": (
        f'<div class="u-q">{LOUPE}<b>Muster AG</b><span>CHE-000.000.000</span></div>'
        '<div class="u-list u-niv"><div class="u-it u-n1"><i></i>Corrext Certification</div>'
        '<div class="u-it u-n2"><i></i>Notarized Certification</div>'
        '<div class="u-it u-n3"><i></i>Notarized &amp; Apostilled</div></div>'),
    # Démo de l'éditeur : segments du contrat d'exemple confirmés un à un
    "fr/corrext/editeur-de-relecture/": (
        '<div class="u-pg"><span class="u-bar"><i></i></span><span>des segments confirmés</span></div>'
        '<div class="u-sg u-sg1"><span lang="fr">Article 1 · Objet</span><span lang="de">Artikel 1 · Gegenstand</span><b>MT</b>' + COCHE + '</div>'
        '<div class="u-sg u-sg2"><span lang="fr">Contrat de mandat (exemple fictif)</span><span lang="de">Auftragsvertrag (fiktives Beispiel)</span><b>MT</b>' + COCHE + '</div>'),
    # Tableau des trois modes (page sécurité) : avec l'interrupteur, le traitement reste en Suisse
    "fr/securite-souverainete/": (
        '<div class="u-row"><span class="u-fort">Highly sensitive content</span><span class="u-sw"></span></div>'
        '<div class="u-list"><div class="u-kv"><small>Stockage du projet et des fichiers</small><span>Serveurs suisses de Corrext</span></div>'
        '<div class="u-kv u-tr"><small>Traitement du texte par le moteur</small><span class="u-a">Hors de Suisse</span><span class="u-b">Exclusivement en Suisse</span></div></div>'),
    # Page Langues et formats : quatre langues natives, formats bureautiques
    "fr/langues-et-formats/": (
        '<div class="u-lbl">Quatre langues natives</div>'
        '<div class="u-chips"><span class="u-c1">Allemand</span><span class="u-c2">Français</span>'
        '<span class="u-c3">Italien</span><span class="u-c4">Anglais</span></div>'
        '<div class="u-lbl u-sep">Formats</div>'
        '<div class="u-chips u-fmt"><span>.docx</span><span>.pptx</span><span>.xlsx</span><span>PDF</span></div>'),
    # Page Niveaux de qualité : les quatre niveaux, du moteur seul à l'apostille
    "fr/niveaux-de-qualite/": (
        '<div class="u-list u-niv u-q4"><div class="u-it u-n1"><i>1</i>Traduction machine</div>'
        '<div class="u-it u-n2"><i>2</i>Post-édition</div><div class="u-it u-n3"><i>3</i>Relecture juridique</div>'
        '<div class="u-it u-n4"><i>4</i>Certification et apostille</div></div>'),
    # V1 « outil-api » : la requête s'affiche ligne à ligne ; la note d'illustration de la V1 est conservée
    "fr/corrext/api-on-premises/": (
        '<pre class="u-code"><span class="l1"><b>POST</b> /v1/translate</span>\n<span class="l2">{</span>\n'
        '<span class="l3">  <em>"source_language"</em>: "de",</span>\n<span class="l4">  <em>"target_language"</em>: "fr",</span>\n'
        '<span class="l5">  <em>"engine"</em>: "lexmachina",</span>\n<span class="l6">  <em>"domain"</em>: "banking"</span>\n'
        '<span class="l7">}</span></pre><div class="u-note">Illustration · le contrat d\'interface est remis au cadrage</div>'),
}

CIBLE = re.compile(r'href="\{\{ROOT\}\}(fr/[^"#?]*)"')


def _fin_div(html, debut):
    """Index juste après le </div> qui ferme le <div ouvert à `debut` (divs imbriqués compris)."""
    n, i = 0, debut
    for m in re.compile(r"<div\b|</div>").finditer(html, debut):
        n += 1 if m.group(0) == "<div" else -1
        if n == 0:
            return m.end()
    raise ValueError("div non fermé")


def _carte(a):
    href = CIBLE.search(a).group(1)
    corps = a[a.index(">") + 1:a.rindex("</a>")]
    v = corps.find('<div class="v">')
    if v >= 0:
        corps = corps[:v] + corps[_fin_div(corps, v):]
    # titre : texte du premier <b> de premier niveau (certaines sources doublent la balise : <b><b>…</b></b>)
    titre = re.sub(r"</?b>", "", re.search(r"<b>(.*?</b>)\s*(?=<p>|<span|$)", corps, re.S).group(1))
    texte = re.search(r"<p>(.*?)</p>", corps, re.S) or re.search(r'<span(?! class="lien")[^>]*>(.*?)</span>', corps, re.S)
    lien = re.search(r'<span class="lien">(.*?)</span>', corps, re.S)
    libelle = lien.group(1) if lien else "En savoir plus"
    return (f'<a class="fx" href="{{{{ROOT}}}}{href}"><div class="fx-v" aria-hidden="true"><div class="fx-w">{VISUELS[href]}</div></div>'
            f'<b class="fx-t">{titre}</b>' + (f'<p class="fx-p">{texte.group(1)}</p>' if texte else "")
            + f'<span class="fx-l">{libelle} {FLECHE}</span></a>')


def traiter(html, page):
    sortie, pos = [], 0
    for m in re.finditer(r'<div class="cd">', html):
        if m.start() < pos:
            continue
        fin = _fin_div(html, m.start())
        interieur = html[m.end():fin - len("</div>")]
        cartes = re.findall(r"<a href=.*?</a>", interieur, re.S)
        cibles = [CIBLE.search(c) for c in cartes]
        reste = re.sub(r"<a href=.*?</a>", "", interieur, flags=re.S).strip()
        if not cartes or reste or not all(c and c.group(1) in VISUELS for c in cibles):
            continue
        sortie.append(html[pos:m.start()])
        sortie.append(f'<div class="fx-g fx-n{len(cartes)}">' + "".join(_carte(c) for c in cartes) + "</div>")
        pos = fin
    if not sortie:
        return html
    return "".join(sortie) + html[pos:]
