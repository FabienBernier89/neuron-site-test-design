"""Schéma « qui fait quoi » (lot B, spec V2 § 5) : Corrext au centre, LexMachina et les moteurs à gauche, CHnell à droite.

`rendre()` renvoie la section complète. Le post-traitement outils/post/schema_produits.py l'insère sur les pages
Corrext, LexMachina et CHnell ; l'accueil l'importe au lot D.

- Les définitions forment un <dl> lisible sans CSS : un groupe par produit (dt, définition, complément, lien).
- Chaque groupe porte une illustration au niveau des écrans Corrext (dd.sp-ui). Elle est marquée `hidden` (absente
  sans CSS et pour les moteurs qui lisent le texte) et `aria-hidden` ; la feuille schema-produits.css l'affiche.
- Textes nouveaux : src/data/contenus-v2/B-schema.json. Libellés et données des illustrations : démo Corrext publiée
  (assets/corrext-demo.js du site Neur.on), lus et non recopiés.
"""
import html as _h
import json
import os
import re
import sys
from pathlib import Path

ICI = Path(__file__).resolve().parent
RACINE = ICI.parents[1]
for _chemin in (str(ICI), str(RACINE)):  # appelé depuis outils/composer comme depuis le build (post-traitement)
    if _chemin not in sys.path:
        sys.path.append(_chemin)

import app as A  # noqa: E402
from outils.contenus import texte  # noqa: E402

NEURON = Path(os.environ.get("NEURON_SRC") or RACINE.parent / "neuron")
CHAINE = r'"((?:[^"\\]|\\.)*)"'
TERME_SOURCE = "intérêts moratoires"  # terme surligné par la démo de l'accueil (data-terme-co)
TERME_CIBLE = "intérêt moratoire"     # équivalent publié : « Verzugszins » devient « intérêt moratoire » (page LexMachina)
# Par produit : classe du groupe, page, libellé du lien (repris du méga-menu du site actuel)
PRODUITS = {"lexmachina": ("sp-lm", "lexmachina/", "LexMachina, le moteur"),
            "corrext": ("sp-cx", "corrext/", "Corrext, la plateforme"),
            "chnell": ("sp-ch", "corrext/chnell/", "Fast lookup CHnell")}
# Mention reliée dans une définition (lot D) : produit, texte exact de la mention, page visée
LIENS_DEF = {"corrext": ("plugin Word", "corrext/plugin-word/")}
CADENAS = ('<svg viewBox="0 0 16 16" aria-hidden="true" fill="none" stroke="currentColor" stroke-width="1.6" '
           'stroke-linecap="round" stroke-linejoin="round"><rect x="3.5" y="7" width="9" height="6.5" rx="1.5"/>'
           '<path d="M5.5 7V5.2a2.5 2.5 0 0 1 5 0V7"/></svg>')


def e(s):
    return _h.escape(s, quote=False)


def _js(s):
    """Chaîne JavaScript entre guillemets doubles, déséchappée."""
    return json.loads('"' + s.replace("\\'", "'") + '"')


def donnees_demo():
    """Exemple « Contrat · art. 104 CO » de la démo Corrext publiée : texte source, sortie LexMachina vers l'anglais,
    recherche CHnell associée et sa ligne tirée de fedlex.admin.ch. ValueError si la démo a changé de forme."""
    js = (NEURON / "assets/corrext-demo.js").read_text(encoding="utf-8")
    try:
        debut = js.index("co:{label:")
        src = _js(re.compile(r"src:" + CHAINE).search(js, debut).group(1))
        sortie = _js(re.compile(r"en:\{main:" + CHAINE).search(js, debut).group(1))
        lk = js.index("lookup:{", debut)
        q, l1, l2, compte = map(_js, re.compile(r"lookup:\{q:" + CHAINE + ",l1:" + CHAINE + ",l2:" + CHAINE + ",count:" + CHAINE).match(js, lk).groups())
        lignes = re.compile(r"\{a:" + CHAINE + ",b:" + CHAINE + ",dom:" + CHAINE + ",src:" + CHAINE + r"\}")
        a, b, dom, source = next(map(_js, m.groups()) for m in lignes.finditer(js, lk) if "fedlex.admin.ch" in m.group(4))
    except (ValueError, AttributeError, StopIteration) as err:
        raise ValueError("La démo Corrext du site Neur.on a changé de forme : adapter schema_produits.donnees_demo()") from err
    if TERME_SOURCE not in src or q not in a:
        raise ValueError("Termes de la démo introuvables : adapter TERME_SOURCE ou la recherche CHnell")
    return {"src": src, "sortie": sortie, "q": q, "l1": l1, "l2": l2, "compte": compte, "a": a, "b": b, "dom": dom, "source": source}


def surligner(t, terme):
    """Texte échappé, chaque occurrence du terme (casse ignorée) dans un <mark>."""
    return re.sub(re.escape(e(terme)), lambda m: f"<mark>{m.group(0)}</mark>", e(t), flags=re.I)


def ui_lexmachina():
    """Choix du moteur : libellés de l'application (Translation engine, menu des moteurs, mention Suisse)."""
    items = "".join(f'<span class="on">{e(m)}<small>Suisse</small></span>' if m == "LexMachina" else f"<span>{e(m)}</span>"
                    for m in A.ENGINES)
    return ('<div class="sp-app sp-app-lm"><span class="sp-lbl">Translation engine</span>'
            f'<span class="sp-sel"><span>LexMachina</span>{A.IC["chevron"]}</span>'
            f'<span class="sp-menu">{items}</span></div>')


def ui_corrext(d):
    """Écran « Text translation » réduit : barre de l'application, langues, moteur, texte source et sortie."""
    return ('<div class="sp-app sp-app-cx">'
            '<span class="sp-top"><img src="{{ROOT}}assets/img/corrext-logo.svg" alt="" width="88" height="18">'
            f'<span class="sp-tab">{e(A.ONGLETS[0])}</span></span>'
            f'<span class="sp-bar"><span>Detected language (French)</span>{A.IC["echange"]}<span>English</span>'
            f'<span class="sp-eng">LexMachina</span></span>'
            '<span class="sp-panes">'
            f'<span class="sp-pane"><span class="sp-txt">{surligner(d["src"], TERME_SOURCE)}</span>'
            f'<span class="sp-lkb">{A.IC["loupe"]}Fast Lookup</span></span>'
            '<span class="sp-pane sp-tgt"><span class="sp-sk"></span><span class="sp-sk"></span><span class="sp-sk"></span>'
            f'<span class="sp-out">{e(d["sortie"])}</span></span>'
            '</span></div>')


def ui_chnell(d):
    """Fast lookup CHnell : recherche de la démo, compteur et une ligne alignée, terme surligné dans les deux langues."""
    return ('<div class="sp-app sp-app-ch">'
            '<span class="sp-top"><img src="{{ROOT}}assets/img/chnell-logo.svg" alt="" width="78" height="22">'
            '<span class="sp-pw">powered by Neur.on</span></span>'
            f'<span class="sp-q"><span class="sp-box">{A.IC["loupe"]}<b>{e(d["q"])}</b></span>'
            f'<span class="sp-lg">{e(d["l1"])}</span>{A.IC["echange"]}<span class="sp-lg">{e(d["l2"])}</span>'
            f'<span class="sp-cnt">{e(d["compte"])}</span></span>'
            f'<span class="sp-res"><small class="sp-dom">{e(d["dom"])}</small>'
            f'<span class="sp-seg">{surligner(d["a"], d["q"])}</span>'
            f'<span class="sp-seg">{surligner(d["b"], TERME_CIBLE)}</span>'
            f'<small class="sp-src">{e(d["source"])}</small></span></div>')


def definition(cle):
    """Définition échappée ; la mention de LIENS_DEF (première occurrence) devient un lien, texte inchangé."""
    d = e(texte("schema." + cle + ".def"))
    if cle in LIENS_DEF:
        mention, chemin = LIENS_DEF[cle]
        if mention not in d:
            raise ValueError(f"schema.{cle}.def : mention « {mention} » introuvable, adapter LIENS_DEF")
        d = d.replace(mention, f'<a class="pw-lien" href="{{{{ROOT}}}}{chemin}">{mention}</a>', 1)
    return d


def groupe(cle, nom, ui, complement=""):
    classe, chemin, libelle = PRODUITS[cle]
    x = f'<dd class="sp-x">{e(complement)}</dd>' if complement else ""
    return (f'<div class="sp-n {classe}">'
            f"<dt>{nom}</dt>"
            f'<dd class="sp-ui" hidden aria-hidden="true" data-ui>{ui}</dd>'
            f'<dd class="sp-d">{definition(cle)}</dd>{x}'
            f'<dd class="sp-a"><a class="lien" href="{{{{ROOT}}}}{chemin}">{e(libelle)}</a></dd>'
            "</div>")


def rendre():
    """Section complète du schéma : titre, introduction, scène (définitions et illustrations), hébergement."""
    d = donnees_demo()
    accent = "qui fait quoi"
    titre = e(texte("schema.titre")).replace(accent, f"<em>{accent}</em>", 1)
    return ('<section class="sec sp" aria-labelledby="sp-titre"><div class="wrap">\n'
            f'<h2 class="h2" id="sp-titre">{titre}</h2>'
            f'<p class="intro">{e(texte("schema.intro"))}</p>\n'
            '<div class="sp-sc">'
            '<dl class="sp-dl">'
            + groupe("lexmachina", "LexMachina", ui_lexmachina(), texte("schema.lexmachina.tiers"))
            + groupe("corrext", "Corrext", ui_corrext(d), texte("schema.corrext.role"))
            + groupe("chnell", "CHnell", ui_chnell(d), texte("schema.chnell.lookup"))
            + "</dl>"
            # Les trois étapes du flux, dans l'ordre où le script les joue (retour de Fabien du 2026-10-15)
            + '<ol class="sp-et">' + "".join(f"<li>{e(texte(f'schema.etape{i}'))}</li>" for i in (1, 2, 3)) + "</ol>"
            # légende d'hébergement retirée le 2026-10-15 (demande de Fabien)
            "</div>\n</div></section>\n")


if __name__ == "__main__":
    print(rendre())
