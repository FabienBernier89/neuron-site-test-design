"""Compose la page Plugin Word (corrext/plugin-word/), page nouvelle de la V2.

Textes : src/data/contenus-v2/A-plugin-word.json, à relire par Fabien. Scène « word » : fenêtre Word reprise de la
maquette de l'accueil du site actuel (ruban, assistant IA), document et panneau Corrext repris de la démo de
l'éditeur de relecture (segments, mémoire, Fast Lookup, alternatives) et du centre d'aide (panneau « Corrext editor »,
onglets). Le HTML porte l'état final de la scène ; assets/visite-word.js rejoue le parcours qui y mène.

    cd outils/composer && NEURON_SRC=<site Neur.on> python3 p_plugin_word.py
"""
import html as H
import json
import os
import re
import sys
from pathlib import Path

RACINE = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(RACINE))
from outils.contenus import texte  # noqa: E402
from comp import scene, hero, section, h2, tuiles, bento, cta, faq  # noqa: E402
from app import IC  # noqa: E402

NEURON = Path(os.environ.get("NEURON_SRC") or RACINE.parent / "neuron")
P = "corrext/plugin-word/"
C = "{{ROOT}}contact/"
DEMO = "Demander une démo"
SUIVI = ' data-suivi="cta-plugin-word-{}"'  # convention cta-<contexte>-<position> : hero ou fin
EDITEUR = NEURON / "docs/fr/corrext/editeur-de-relecture/index.html"


def t(cle):
    """Texte d'un contenu nouveau, échappé pour le HTML."""
    return H.escape(texte(cle), quote=False)


def e(s):
    return H.escape(s, quote=False)


# ---------- Données de la démo de l'éditeur de relecture (site actuel, lues sans modification) ----------

def segments():
    """Segments du contrat fictif : source, traduction, origine (MT ou TM), jauge de qualité, correspondance."""
    brut = EDITEUR.read_text(encoding="utf-8")
    out = []
    for m in re.finditer(r'<tr data-i="(\d+)"[^>]*>(.*?)</tr>', brut, re.S):
        tr = m.group(2)
        sim = re.search(r'<span class="cxe-sim">([^<]+)</span>', tr)
        out.append({"i": int(m.group(1)),
                    "src": H.unescape(re.search(r'<td class="cxe-src">(.*?)</td>', tr, re.S).group(1)),
                    "tgt": H.unescape(re.search(r'<div class="cxe-tgt"[^>]*>(.*?)</div>', tr, re.S).group(1)),
                    "origine": re.search(r"<b>(MT|TM)</b>", tr).group(1),
                    "jauge": len(re.findall(r'<i class="on"></i>', tr)),
                    "sim": sim.group(1) if sim else ""})
    assert [s["i"] for s in out] == list(range(6)), "la démo de l'éditeur de relecture a changé de forme"
    return out


def chnell():
    """Résultats CHnell du Fast Lookup de la démo (variable LK.ch du script) : source, cible, document."""
    brut = EDITEUR.read_text(encoding="utf-8")
    bloc = brut[brut.index("ch:[", brut.index("var LK=")):]
    bloc = bloc[:bloc.index("}]\n") + 2]
    chaine = r"'((?:[^'\\]|\\.)*)'"
    lignes = re.findall(r"s:" + chaine + r",\s*t:" + chaine + r",\s*d:" + chaine, bloc)
    assert len(lignes) == 2, "les résultats CHnell de la démo ont changé de forme"
    return [{"s": s.replace("\\'", "'"), "t": c.replace("\\'", "'"), "d": d.replace("\\'", "'")} for s, c, d in lignes]


def verifier_demo():
    """Les libellés que seule la démo affiche (script) figurent mot pour mot dans la page de l'éditeur."""
    brut = EDITEUR.read_text(encoding="utf-8").replace("\\'", "'")
    with open(RACINE / "src/data/contenus-v2/A-plugin-word.json", encoding="utf-8") as f:
        for x in json.load(f)["entrees"]:
            if x["cle"].startswith("plugin-word.demo."):
                assert x["texte"] in brut, f"{x['cle']} absent de la démo de l'éditeur de relecture"


# ---------- Scène « word » ----------

TERME = "Verzugszins"
TERME_FR = re.compile(r"int[ée]r[êe]ts?\s+moratoires?", re.I)
TERME_DE = re.compile(TERME + r"\w*")
PANNEAU = ('<svg viewBox="0 0 16 16" aria-hidden="true" fill="none" stroke="currentColor" stroke-width="1.4" '
           'stroke-linecap="round" stroke-linejoin="round"><rect x="2" y="2.5" width="12" height="11" rx="1.6"/>'
           '<path d="M9.5 2.5v11M11.2 5.5h1M11.2 7.5h1"/></svg>')  # bouton du ruban : affiche le panneau latéral


def marquer(s, motif, cls="wd-k"):
    """Texte échappé, chaque occurrence du motif surlignée."""
    return motif.sub(lambda m: f'<mark class="{cls}">{m.group(0)}</mark>', e(s))


def ligne(s, sel=False, cible=None, avant=None):
    jauge = "".join('<i class="on"></i>' if k < s["jauge"] else "<i></i>" for k in range(3)) if s["origine"] == "MT" else ""
    origine = (f'<span class="wd-o"><b>{s["origine"]}</b>'
               + (f'<span class="wd-g" aria-hidden="true">{jauge}</span>' if jauge else f'<span class="wd-sim">{e(s["sim"])}</span>')
               + "</span>")
    av = f' data-avant="{H.escape(avant)}"' if avant else ""
    return (f'<div class="wd-l{" sel" if sel else ""}" data-i="{s["i"]}"><p class="wd-s">{marquer(s["src"], TERME_FR, "wd-k wd-kfr")}</p>'
            f'<p class="wd-t" lang="de"{av}>{cible if cible is not None else e(s["tgt"])}</p>{origine}</div>')


def ecran_word():
    seg = segments()
    memoire = texte("plugin-word.demo.memoire-cible")
    # état final : mémoire appliquée au segment 2, segment 3 choisi, terme surligné
    lignes = "".join(
        ligne(s, cible=e(memoire), avant=s["tgt"]) if s["i"] == 2 else
        ligne(s, sel=True, cible=marquer(s["tgt"], TERME_DE, "wd-k wd-kde on")) if s["i"] == 3 else ligne(s)
        for s in seg)
    document = ('<div class="wd-doc"><div class="wd-page">'
                '<div class="wd-l wd-th"><p>Source (français)</p><p>Traduction (allemand)</p><span></span></div>'
                f'{lignes}</div></div>')
    ruban = ('<div class="wd-rib"><div class="wd-tabs"><span>Accueil</span><span>Insertion</span><span>Révision</span>'
             '<span class="on">Corrext</span></div>'
             f'<div class="wd-bar"><span class="wd-btn">{PANNEAU}<span>Corrext</span></span></div></div>')
    onglets = ('<div class="cr-tl"><i class="cr-tl-pill"></i><span class="on" data-t="0">AI Assistant</span>'
               '<span data-t="1">Fast Lookup</span><span data-t="2">Matches</span><span data-t="3">Sync</span></div>')
    alt = [("LexMachina", texte("plugin-word.demo.alt-lexmachina")), ("DeepL Pro", texte("plugin-word.demo.alt-deepl"))]
    vue_ia = ('<div class="cr-vue on" data-t="0">'
              f'<div class="wd-sub"><span class="on">Alternatives</span><span>Rephrasing</span><span class="wd-gen">{IC["etincelle"]}Generate more</span></div>'
              '<div class="wd-alts">'
              + "".join(f'<div class="wd-alt"><p lang="de">{e(x)}</p><span class="wd-e">{m}</span></div>' for m, x in alt)
              + '</div>'
              f'<div class="wd-ia vu"><p class="wd-ia-h">{IC["etincelle"]}Assistant IA</p>'
              f'<p class="wd-ia-t">Terme harmonisé : « <b>{TERME}</b> ». L\'appliquer dans tout le document ?</p>'
              '<div class="wd-ia-a"><span class="wd-oui">Oui, partout</span><span class="wd-non">Ignorer</span></div></div>'
              '<div class="wd-tm"><p class="wd-lab">Terminologie</p><div class="wd-terme">CHnell · droit suisse</div></div>'
              '</div>')
    tm = seg[3]

    def resultat(i, s, c, d):
        return (f'<div class="wd-r" style="--i:{i}"><p>{marquer(s, TERME_FR)}</p><p lang="de">{marquer(c, TERME_DE)}</p>'
                f'<small>{e(d)}</small></div>')
    vue_lk = ('<div class="cr-vue" data-t="1">'
              '<div class="wd-qr"><span class="wd-live"><i></i>Live search</span></div>'
              f'<div class="wd-qr"><span class="cr-box">{IC["loupe"]}<b class="wd-q">{TERME}</b></span>'
              '<span class="cr-btn wd-go">Search</span></div>'
              '<div class="wd-seg"><span>Source</span><span class="on">Target</span></div>'
              '<div class="wd-res vu"><p class="wd-rh">Translation memories</p>'
              + resultat(0, tm["src"], tm["tgt"], texte("plugin-word.demo.lookup-document"))
              + '<p class="wd-rh">CHnell</p>'
              + "".join(resultat(i + 1, r["s"], r["t"], r["d"]) for i, r in enumerate(chnell()))
              + '</div></div>')
    vue_mem = ('<div class="cr-vue" data-t="2"><div class="wd-sk" aria-hidden="true"><span class="cr-sk"></span>'
               '<span class="cr-sk"></span><span class="cr-sk"></span></div>'
               f'<div class="wd-mem vu"><p class="wd-ml">{t("plugin-word.demo.memoire-libelle")}</p>'
               f'<p class="wd-ms">{t("plugin-word.demo.memoire-source")}</p><p class="wd-mt" lang="de">{e(memoire)}</p>'
               '<div class="wd-ma"><span class="cr-btn cr-btn-p wd-apply">Apply</span></div></div></div>')
    panneau = ('<div class="wd-pan"><div class="wd-ph"><b>Corrext editor</b>'
               f'<span class="wd-x">{IC["croix"]}</span></div>{onglets}'
               f'<div class="wd-vues">{vue_ia}{vue_lk}{vue_mem}</div></div>')
    return f'<div class="cr wd ouvert">{ruban}<div class="wd-c">{document}{panneau}</div></div>'


# ---------- Page ----------

def faq_jsonld(qr):
    d = {"@context": "https://schema.org", "@type": "FAQPage",
         "mainEntity": [{"@type": "Question", "name": q, "acceptedAnswer": {"@type": "Answer", "text": r}} for q, r in qr]}
    return '<script type="application/ld+json">' + json.dumps(d, ensure_ascii=False).replace("</", "<\\/") + "</script>\n"


def composer():
    verifier_demo()
    titre = texte("plugin-word.hero.titre")
    n, s = titre.split(". ", 1)
    out = [hero(e(n + "."), e(s), t("plugin-word.hero.lead"), (DEMO, C)).replace('<a class="btn"', '<a class="btn"' + SUIVI.format("hero"), 1)]

    ecran = ecran_word()
    out.append(section(scene(1176, 640, ecran, sim="word", titre="Microsoft Word", curseur=False,
                             label=H.escape(texte("plugin-word.scene.label"))), "sec sec-st", "demo"))

    fonctions = [(None, t(f"plugin-word.fonctions.{k}.titre"), t(f"plugin-word.fonctions.{k}.texte"))
                 for k in ("segments", "memoire", "lookup", "alternatives", "harmonisation", "progression")]
    out.append(section(h2(t("plugin-word.fonctions.titre"), "dans Word") + f'<p class="intro">{t("plugin-word.fonctions.intro")}</p>'
                       + tuiles(fonctions, "tl txt")
                       + f'<p class="pw-suite"><a class="lien" href="{{{{ROOT}}}}corrext/editeur-de-relecture/">{t("plugin-word.fonctions.lien")}</a></p>'))

    etapes = [(f"0{i}", t(f"plugin-word.poste.etape{i}.titre"), t(f"plugin-word.poste.etape{i}.texte")) for i in range(1, 5)]
    out.append(section(h2(t("plugin-word.poste.titre"), "relié à votre projet") + f'<p class="intro">{t("plugin-word.poste.texte")}</p>'
                       + tuiles(etapes, "tl t4 tl-ledger")))

    petites = [(t(f"plugin-word.garanties.{k}.titre"), t(f"plugin-word.garanties.{k}.texte"), "")
               for k in ("suisse", "sensible", "acces", "iso")]
    out.append(section(bento({"titre": h2(t("plugin-word.garanties.titre"), "que Corrext", "h3s"), "texte": t("plugin-word.garanties.texte"),
                              "lien": (t("plugin-word.garanties.lien"), "{{ROOT}}securite-souverainete/")}, petites), "sec pw-garanties"))

    qr = [(texte(f"plugin-word.faq.q{i}"), texte(f"plugin-word.faq.r{i}")) for i in range(1, 5)]
    out.append(faq(t("plugin-word.faq.titre"), [(e(q), f"<p>{e(r)}</p>") for q, r in qr]))
    out.append(faq_jsonld(qr))

    l1, l2 = texte("plugin-word.cta.titre").split(" sur ", 1)
    out.append(cta(e(l1), e("sur " + l2), (DEMO, C)).replace('<a class="btn"', '<a class="btn"' + SUIVI.format("fin"), 1))

    entete = ("<!--page\n"
              f"title: {texte('plugin-word.meta.title')}\n"
              f"description: {texte('plugin-word.meta.description')}\n"
              "menu: corrext\ngabarit: standard\nscripts: visite-word.js\n-->\n")
    return entete + "".join(out)


def ecrire():
    f = RACINE / "src/pages" / P / "index.html"
    f.parent.mkdir(parents=True, exist_ok=True)
    f.write_text(composer(), encoding="utf-8")


if __name__ == "__main__":
    ecrire()
    print("plugin Word écrit")
