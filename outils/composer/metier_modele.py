"""Modèle des pages métier (solutions/<métier>/), choisi par Fabien le 2026-10-19 sur la page Cabinets d'avocats
(maquettes A1, B1, C1, D2), à dérouler ensuite sur les autres métiers.

Ordre : hero (et lien vers la démo en direct) ; bandeau des distinctions ; gains chiffrés ; avis client ; sans Corrext,
avec Corrext ; les outils du métier en onglets avec un grand écran ; les niveaux de relecture ; sécurité (bloc de
gouvernance de la V1) ; déploiement ; FAQ ; appel.

Textes : la V1, mot pour mot ; nouveaux libellés dans src/data/contenus-v2/Q-metiers.json. L'avis client est un
emplacement fictif (statut « a_remplacer »), toujours affiché avec la mention « Avis fictif · à remplacer ».
"""
from paire_modele import *

CROIX = ('<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.6" stroke-linecap="round" '
         'aria-hidden="true"><path d="M6 6l12 12M18 6 6 18"/></svg>')


def lien_demo(hero_html, href):
    """Second lien du hero, discret, vers la démo en direct (libellé du méga-menu)."""
    return hero_html.replace("</a></div>", f'</a><a class="lien mt-demo" href="{href}">Ouvrir la démo en direct</a></div>', 1)


def gains(slug):
    """Trois tuiles chiffrées, même composant que les chiffres de l'accueil (.tl, .n) ; la note des maxima dessous."""
    k = lambda c: esc(texte(f"{slug}.gains.{c}"))
    try:
        titre = texte(f"{slug}.gains.titre")  # titre propre à la page (Éditeurs : des chiffres du moteur, pas des économies)
    except KeyError:
        titre = texte("metier.gains.titre")
    note = any(texte(f"{slug}.gains.{i}.n").endswith("%") and texte(f"{slug}.gains.{i}.n") != "100 %" for i in (1, 2, 3))

    def chiffre(n):  # « 30 Langues » : unité accolée en petit, comme les chiffres de l'accueil
        m = re.fullmatch(r"([\d.,]+(?: M\+)?) ([A-Za-zÀ-ÿ]+)", n)
        return f'{m.group(1)} <span class="u">{m.group(2)}</span>' if m else n
    return section(h2(titre, " ".join(titre.split()[-3:])) + tuiles([(chiffre(k(f"{i}.n")), None, k(f"{i}.t")) for i in (1, 2, 3)], "tl")
                   + (f'<p class="mt-note">{esc(texte("metier.gains.note"))}</p>' if note else ""))


def avis(slug):
    """B1 : citation centrée ; emplacement fictif tant que l'avis réel n'est pas fourni."""
    k = lambda c: esc(texte(f"{slug}.avis.{c}"))
    return section(f'<figure class="mt-av" data-avis-fictif><span class="mt-fict">{esc(texte("metier.avis.fictif"))}</span>'
                   f'<blockquote>{k("texte")}</blockquote><figcaption><span class="mt-ph" aria-hidden="true"></span>'
                   f'<span><b>{k("nom")}</b>{k("fonction")}</span></figcaption></figure>', "sec mt-avis")


def sans_avec(slug, n=5):
    """C1 : tableau face à face, colonne « Avec » teintée."""
    lignes = "".join(f'<div role="row"><p role="cell" class="mt-sans"><i>{CROIX}</i>{esc(texte(f"{slug}.sa.{i}.sans"))}</p>'
                     f'<p role="cell" class="mt-avec"><i>{COCHE}</i>{esc(texte(f"{slug}.sa.{i}.avec"))}</p></div>' for i in range(1, n + 1))
    titre = texte("metier.sa.titre")
    return section(h2(titre, titre.split(", ", 1)[1]) + f'<div class="mt-sa" role="table"><div role="row" class="mt-sah">'
                   f'<span role="columnheader">{esc(texte("metier.sa.sans"))}</span><span role="columnheader">{esc(texte("metier.sa.avec"))}</span></div>{lignes}</div>')


SERVICE_EXTRAITS = "https://auszug-hr.ch"  # service en ligne de commande des extraits (page Extraits du registre)


def outils(slug, items, accent, commander=None):
    """D2 : onglets à gauche (usage, outil, texte, lien), grand écran animé à droite.
    items : (titre, texte, href, scène, libellé du lien) ; commander : nom de l'onglet qui présente les extraits du
    registre, qui reçoit en plus le lien « Commander un extrait » vers le service en ligne (audit CRO du 2026-10-23)."""
    titre = texte(f"{slug}.outils.titre")
    onglets, panneaux = "", ""
    for i, (nom, txt_, href, sc, lien_) in enumerate(items, 1):
        actif = i == 1
        liens_ = f'<a class="lien" href="{href}">{lien_}</a>'
        if nom == commander:
            liens_ = (f'<p class="mt-ls">{liens_}<a class="lien" href="{SERVICE_EXTRAITS}" rel="noopener">'
                      f'{esc(texte("extraits.commander"))}</a></p>')
        onglets += (f'<div class="mt-o{" on" if actif else ""}"><button type="button" role="tab" id="mt-t{i}" aria-controls="mt-p{i}" '
                    f'aria-selected="{"true" if actif else "false"}"><span class="mt-l">{esc(texte(f"{slug}.outils.{i}.usage"))}</span>'
                    f'<span class="mt-ot">{nom}</span></button><div class="mt-od"><div><p>{txt_}</p>'
                    f'{liens_}</div></div></div>')
        panneaux += f'<div class="mt-p" role="tabpanel" id="mt-p{i}" aria-labelledby="mt-t{i}"{"" if actif else " hidden"}>{sc}</div>'
    return section(h2(titre, accent) + f'<div class="mt-ou" data-onglets><div class="mt-os" role="tablist">{onglets}</div>'
                   f'<div class="mt-ps">{panneaux}</div></div>')


def niveaux():
    """Les quatre niveaux de la page Niveaux de qualité, en tuiles chiffrées (même rendu que cette page)."""
    P = "niveaux-de-qualite/"
    lv = bloc(liens(charger(P), P), "section", "levels")
    niv = [(str(i + 1), brut(bloc(x, "h3")), brut(bloc(x, "p"))) for i, x in enumerate(blocs(lv, "div", "lev"))]
    t = texte("metier.niveaux.titre")  # titre de la page Niveaux de qualité, déclaré pour les pages métier
    assert t == txt(bloc(lv, "h2")), "le titre des niveaux a changé dans la V1"
    return section(h2(t, "devant une autorité") + f'<p class="intro">{brut(bloc(bloc(lv, "div", "sec-head"), "p"))}</p>' + tuiles(niv, "tl t4"))


def deploiement(items):
    """Cartes reliées : démo, centre d'aide, API (libellés et sous-titres du méga-menu)."""
    titre = texte("metier.deploiement.titre")
    return section(h2(titre, "sans complexité") + cartes([(b, p, (lien_, href), "") for b, p, lien_, href in items]))


ETAPES_SECURITE = "autorites-administration"  # page de la V1 dont le bloc de gouvernance porte les trois faits de sécurité


def securite(slug, accent, texte_v1):
    """Bloc sécurité d'une page dont la V1 n'en a pas : titre propre à la page (contenus), texte de la V1 de la page,
    les trois faits de sécurité du site (hébergement, traitement en Suisse, sur site) et le lien vers la page Sécurité."""
    P = f"solutions/{ETAPES_SECURITE}/"
    gv = bloc(liens(charger(P), P), "section", "gov")
    pas = [(brut(bloc(x, "b")), brut(re.sub(r"<b>.*?</b>", "", interne(x), flags=re.S)), "") for x in blocs(bloc(gv, "div", "gov-steps"), "span") if "<b>" in x[:12]]
    pas[-1] = (pas[-1][0], pas[-1][1], "bt-l")
    a = blocs(bloc(gv, "div", "gov-box"), "a", "feat-link")[0]
    g = {"titre": h2(texte(f"{slug}.securite.titre"), accent, "h3s"), "texte": texte_v1, "lien": (txt(a), re.search(r'href="([^"]+)"', a).group(1))}
    return section(bento(g, pas))


def ecran_api():
    """Intégration par API (page Éditeurs, demande de Fabien du 2026-10-20) : un paragraphe d'un document Word part en
    appel d'API, la traduction LexMachina s'insère dans le document et un commentaire propose l'alternative d'un autre
    moteur, l'écart surligné. Appel : champs de l'illustration de la page API et on-premises de la V1 (« Illustration,
    pas documentation ») ; traduction et alternative : sorties réelles relevées dans Corrext (exemple « lb »). L'écart entre
    les deux sorties est surligné en bleu des deux côtés : aucune des deux n'est présentée comme fausse."""
    d = EX["lb"]
    sortie, alt = d["out"]["de"]["main"], d["out"]["de"]["alt"][0]
    ecart_lm, ecart_alt = "beaufsichtigte Institut", "unterstellte Institut"
    assert ecart_lm in sortie and ecart_alt in alt["t"]
    champs = [("source_language", "fr"), ("target_language", "de"), ("engine", "lexmachina"), ("domain", "banking")]
    req = "".join(f'<span class="ap-l" style="--i:{i}"><i>"{k}"</i>: <b>"{v}"</b>{"," if i < len(champs) - 1 else ""}</span>' for i, (k, v) in enumerate(champs))
    # état final dans le HTML (mouvement réduit) ; assets/sim.js (SCENES.api) retire puis rejoue les étapes
    return ('<div class="cr ap sel envoye recu insere com">'
            '<div class="ap-rib"><span>Accueil</span><span>Insertion</span><span>Révision</span></div>'
            '<div class="ap-c"><div class="ap-doc"><div class="ap-page">'
            f'<p class="ap-src">{esc(d["src"])}</p>'
            f'<p class="ap-out" lang="de">{A.marquer(sortie, [ecart_lm])}</p>'
            f'<div class="ap-com"><p class="ap-ch">Alternatives<span>{esc(alt["e"])}</span></p>'
            f'<p lang="de">{A.marquer(alt["t"], [ecart_alt])}</p></div>'
            '</div></div>'
            f'<div class="ap-api"><p class="ap-h"><b>POST</b> /v1/translate</p><div class="ap-req">{{{req}}}</div>'
            f'<p class="ap-st"><i></i>{esc(texte("metier.api.statut"))}</p>'
            '<p class="ap-note">Illustration, pas documentation.</p></div>'
            '</div></div>')
