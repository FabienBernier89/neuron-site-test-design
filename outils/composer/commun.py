"""Morceaux communs aux pages : lignes C7 depuis des .feature, FAQ, appel final."""
import re
from source import *
from comp import *
import app as A
import vues as V

C = "{{ROOT}}contact/"


def lignes_features(sec, titre_fen="Corrext", depart=0, visuels=None):
    """visuels : liste facultative de (contenu, sim, hauteur) qui remplace les maquettes du site actuel."""
    lignes = []
    for i, f in enumerate(blocs(sec, "div", "feature")):
        h3 = bloc(f, "h3")
        pn = blocs(h3, "span", "pn")
        pill = txt(pn[0]).rstrip(".") if pn else None
        titre = brut(re.sub(r'<span class="pn">.*?</span>', "", h3, flags=re.S))
        tx = bloc(f, "div", "feat-txt")
        texte = brut(bloc(tx, "p"))
        liste = [brut(li) for li in blocs(f, "li")]
        a = blocs(f, "a", "feat-link")
        lien = (txt(a[0]), re.search(r'href="([^"]+)"', a[0]).group(1)) if a else None
        win = blocs(f, "div", "win")
        if visuels and i < len(visuels) and visuels[i]:
            contenu, sim, haut = visuels[i]
            vis = scene(764, haut, contenu, sim=sim, titre=titre_fen, curseur=False, label=pill or titre)
        else:
            vis = scene(764, 515, '<div class="maq">' + win[0] + "</div>", titre=titre_fen, label=pill or titre) if win else ""
        lignes.append(ft(pill, titre, texte, vis, lien, inv=(i + depart) % 2 == 1, liste=liste))
    return "".join(lignes)


def textes_demo():
    """Textes de l'écran Corrext tels qu'ils figurent dans la démo publiée (page Traduction texte et document)."""
    from source import charger as _ch, liens as _li
    p = "corrext/traduction-texte-et-document/"
    cx = bloc(_li(_ch(p), p), "div", attr='id="cx"')
    av = bloc(cx, "div", "cx-notice")
    hi = bloc(cx, "div", "cx-hint")

    def depot(pid, rid, stid, fin):
        pan = bloc(cx, "div", attr=f'id="{pid}"')
        dr = bloc(pan, "button", "cx-drop")
        row = bloc(pan, "div", attr=f'id="{rid}"')
        return {"drop_t": brut(interne(bloc(dr, "span", "t"))), "drop_s": brut(interne(bloc(dr, "span", "s"))),
                "nom": txt(bloc(row, "span", "fn")), "sous": txt(bloc(row, "span", "fs")),
                "run": txt(bloc(row, "span", attr=f'id="{stid}"')), "fin": fin}

    reph = bloc(cx, "div", attr='id="cxp-reph"')
    chips = blocs(reph, "div", "cx-chips")
    return {
        "notice": (txt(bloc(av, "b")), brut(re.sub(r"<b>.*?</b>", "", interne(av), flags=re.S))),
        "hint": (brut(interne(bloc(hi, "div", "ill"))), txt(bloc(hi, "b")), brut(bloc(hi, "p"))),
        "fichier": depot("cxp-file", "cxFileRow", "cxFileSt", "Download"),
        "pdf": depot("cxp-pdf", "cxPdfRow", "cxPdfSt", "Download .docx"),
        "reph": {"styles": [txt(c) for c in blocs(chips[0], "button")], "options": [txt(c) for c in blocs(chips[1], "button")],
                 "reset": txt(bloc(reph, "button", "rst")), "apply": txt(bloc(reph, "button", attr='id="cxSetApply"')),
                 "ph": re.search(r'placeholder="([^"]+)"', bloc(reph, "textarea")).group(1)},
    }


NIVEAUX_RELECTURE = ["Relecture légère (traducteur juridique)", "Relecture complète (traducteur juridique)", "Double relecture et traduction certifiée"]


def fichiers_demo(*cles):
    """Fichiers de la démo publiée (onglets File translation et PDF to Word), rendus comme traduits."""
    T = textes_demo()
    return [dict(T[c], run=T["fichier"]["run"], fin=T["fichier"]["fin"]) for c in cles]


def textes_extrait():
    """Libellés de la démo « Extraits du registre du commerce » (étapes, niveaux, récapitulatif)."""
    from source import charger as _ch
    cx = bloc(_ch("corrext/extraits-registre-commerce/"), "div", attr='id="cx"')
    st = bloc(cx, "ol", attr='id="cxrSteps"')
    etapes = [txt(x) for x in re.findall(r'<span class="l">(.*?)</span>', st, re.S)]
    nivs = bloc(cx, "div", attr='id="cxrLevels"')
    niveaux = [(brut(interne(bloc(c, "b"))), brut(blocs(c, "span")[-1])) for c in blocs(nivs, "button", "cxr-card")]
    res = bloc(cx, "div", attr='id="cxrRes"')
    societe = txt(bloc(bloc(res, "span", "cxr-co"), "b"))
    ide = brut(blocs(bloc(res, "span", "cxr-co"), "span")[-1])
    return etapes, niveaux, societe, ide


def faq_section(t):
    fq = bloc(t, "section", "faq")
    qr = [(brut(bloc(d, "summary")), "".join(f"<p>{brut(p)}</p>" for p in blocs(d, "p"))) for d in blocs(fq, "details")]
    return faq(txt(bloc(fq, "h2")), qr)


def cta_section(t, coupe):
    """coupe : texte de la première ligne (sans grasse), le reste du h2 passe en serif."""
    h = txt(bloc(bloc(t, "section", "final-cta"), "h2"))
    assert h.startswith(coupe), (h, coupe)
    return cta(coupe, h[len(coupe):].strip(), ("Demander une démo", C))


def tete(sec, cls="sec-head"):
    th = bloc(sec, "div", cls)
    ps = blocs(th, "p")
    return txt(bloc(th, "h2")), (brut(ps[0]) if ps else "")


import json as _json
import subprocess as _sp
# Données réelles de la démo Corrext, lues dans le site Neur.on (Node évalue l'objet EX sans le modifier)
EX = _json.loads(_sp.run(["node", "-e", "const t=require('fs').readFileSync(process.argv[1],'utf8');const d=t.indexOf('var EX=')+7,f=t.indexOf('};\\n',d)+1;process.stdout.write(JSON.stringify(eval('('+t.slice(d,f)+')')))", str(NEURON / "assets/corrext-demo.js")], capture_output=True, text=True, check=True).stdout)


def esc(s):
    import html as _h
    return _h.escape(s, quote=False)


def ui_statique(cle):
    """Gabarit de traduction prérempli avec un extrait réel de la démo (src et sortie LexMachina en anglais)."""
    d = EX[cle]
    return ui_traduction([("LexMachina", "", True)], esc(d["src"]), esc(d["out"]["en"]["main"]))


def ui_chnell(nb=3):
    """Recherche CHnell réelle de la démo (Verzugszins), lignes alignées avec leur source."""
    lk = EX["co"]["lookup"]
    q = esc(lk["q"])
    lignes = "".join(f'<div class="mx-p ck"><p>{esc(r["a"]).replace(q, "<mark>" + q + "</mark>")}</p><p>{esc(r["b"])}</p><small>{esc(r["src"])}</small></div>' for r in lk["rows"][:nb])
    return (f'<div class="mx"><div class="mx-bar"><span class="mx-chip on">{esc(lk["q"])}</span>'
            f'<span class="mx-chip">{esc(lk["l1"])}</span><span class="mx-chip">{esc(lk["l2"])}</span>'
            f'<span class="mx-chip">{esc(lk["count"])}</span></div><div class="ck-l">{lignes}</div></div>')


def distinctions():
    t0 = liens(charger(""), "")
    hl = [txt(x) for x in blocs(bloc(t0, "div", "hero-logos"), "span", "hl") if "aria-hidden" not in x[:60]]
    items = [(x.split(" · ", 1)[0], x.split(" · ", 1)[1] if " · " in x else "") for x in hl]
    return dist(txt(bloc(bloc(t0, "section", "trust"), "h2")), items)
