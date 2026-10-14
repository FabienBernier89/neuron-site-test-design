"""Page de remerciement des formulaires (lot C) : la réponse de envoi.php. Rejouable : cd outils/composer && python3 p_merci.py

Quatre variantes, choisies dans le navigateur par assets/merci.js d'après l'adresse : démo (par défaut, et sans
script), newsletter (?type=newsletter), champ invalide (?erreur=champs) et refus sans détail (?erreur=refus : anti-robot,
plafond d'envoi, échec du serveur). Les textes viennent de src/data/contenus-v2/C-suivi.json ;
les étapes « Ce qui se passe après l'envoi » sont celles de la page contact (texte du site actuel). La page n'est
jamais indexée : outils/post/z_formulaires.py lui donne son noindex."""
import html as H
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))  # outils/ : « from contenus import texte »
from contenus import texte  # noqa: E402
from source import RACINE, bloc, ecrire  # noqa: E402

P = "contact/merci/"
VARIANTES = ("demo", "newsletter", "erreur", "refus")
TITRES = {"demo": "merci.demo.h1", "newsletter": "merci.newsletter.h1", "erreur": "merci.erreur.h1", "refus": "merci.erreur.h1"}
ADRESSE = "team@corrext.com"


def esc(s, attribut=False):
    return H.escape(s, quote=attribut)


def titre():
    """H1 en deux parties (« Merci. » / « Votre demande est bien partie »), chacune avec ses variantes en attribut."""
    parties = {v: texte(TITRES[v]).split(". ", 1) for v in VARIANTES}
    parties = {v: (n + ".", s) for v, (n, s) in parties.items()}
    spans = []
    for i, cls in enumerate(("n", "s")):
        demo = parties["demo"][i]
        attrs = "".join(f' data-v-{v}="{esc(parties[v][i], True)}"' for v in VARIANTES[1:] if parties[v][i] != demo)
        spans.append(f'<span class="{cls}"{attrs}>{esc(demo)}</span>')
    return '<h1 class="h1">' + " ".join(spans) + "</h1>"


def paragraphes():
    out = []
    for v in VARIANTES:
        t = esc(texte(f"merci.{v}.texte"))
        t = t.replace(ADRESSE, f'<a href="mailto:{ADRESSE}">{ADRESSE}</a>', 1)
        out.append(f'<p data-seul="{v}"{"" if v == "demo" else " hidden"}>{t}</p>')
    return "".join(out)


def etapes():
    """Tuile « Ce qui se passe après l'envoi » de la page contact, telle quelle."""
    contact = (RACINE / "src/pages/contact/index.html").read_text(encoding="utf-8")
    tuiles = bloc(contact, "div", "tl")
    tuile = bloc(tuiles[tuiles.index(">") + 1:], "div")
    if "Ce qui se passe après l'envoi" not in tuile:
        raise ValueError("page contact : tuile « Ce qui se passe après l'envoi » introuvable")
    return f'<section class="sec mc-et" data-seul="demo"><div class="wrap">\n<div class="tl txt">{tuile}</div>\n</div></section>\n'


bouton = (f'<a class="btn" href="{{{{ROOT}}}}" data-v-erreur="{esc(texte("merci.formulaire"), True)}" '
          f'data-retour="{{{{ROOT}}}}fr/contact/">{esc(texte("merci.accueil"))}</a>')
entete = (f"<!--page\ntitle: {esc(texte('merci.title'))}\ndescription: {esc(texte('merci.description'))}\n"
          "menu: \ngabarit: contact\nscripts: merci.js\n-->\n")
corps = (f'<section class="hero mc"><div class="wrap hero-g">\n{titre()}\n<div class="hero-d">{paragraphes()}{bouton}</div>\n'
         "</div></section>\n" + etapes())

if __name__ == "__main__":
    ecrire(P, entete, corps)
    print("contact/merci écrit")
