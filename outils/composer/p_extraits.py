"""Page Extraits du registre du commerce : composée par generique.py, avec une structure propre (proposition C retenue
par Fabien le 2026-10-21, audit design du 2026-10-23) : « Commander un extrait » en bouton principal du haut de page ;
la démo de commande et sa légende, les quatre étapes en frise ; le choix du niveau de certification, les trois
niveaux en colonnes ; « Qui traduit, et où » en encart centré ; l'appel final « Commander un extrait » vers le service
en ligne auszug-hr.ch.

    cd outils/composer && python3 p_extraits.py
"""
import generique
from outil_modele import *

P = "corrext/extraits-registre-commerce/"
SERVICE = "https://auszug-hr.ch"
APP = ["Find the company", "Select the certification level", "Choose the delivery method", "Set the delivery timeline"]  # libellés de l'application
ORDRE = ["Recherche", "Langues", "Niveau 1", "Niveau 2", "Niveau 3", "Livraison", "Délai", "Qui traduit", "Confidentialité"]
k = lambda c: texte(f"extraits.{c}")


def faits(t):
    fa = bloc(t, "section", "facts")
    F = {txt(bloc(f, "b")): bloc(f, "p") for f in blocs(fa, "div", "fact")}
    assert [n.split(" · ")[0] for n in F] == ORDRE, "faits de la V1 changés"
    return fa, F


def sans_note(p):
    return brut(p.replace(bloc(p, "small"), "")) if "<small>" in p else brut(p)


def niveaux_etapes(sec, ctx):
    """« Quel niveau de certification pour quel usage ? » (titre et texte du bloc de gouvernance de la V1), les trois
    niveaux en colonnes (faits de la V1), puis la frise des quatre étapes de commande."""
    fa, F = faits(ctx["t"])
    box = bloc(bloc(ctx["t"], "section", "gov"), "div", "gov-box")
    a = blocs(box, "a", "feat-link")[0]
    href = re.search(r'href="([^"]+)"', a).group(1)
    cols = ""
    for nom, p in F.items():
        if not nom.startswith("Niveau"):
            continue
        n, titre = nom.split(" · ", 1)
        pour = txt(bloc(p, "small")).split(" : ", 1)[1].rstrip(".")
        cols += (f'<div class="nv-c"><p class="nv-n">{n}</p><h3>{titre}</h3><p class="nv-l">{esc(k("certifie"))}</p><p>{sans_note(p)}</p>'
                 f'<p class="nv-l">{esc(k("pour"))}</p><p>{pour}</p></div>')
    niveaux = section(h2(txt(bloc(box, "h2")), "quel usage") + f'<p class="intro">{brut(bloc(box, "p"))}</p><div class="nv">{cols}</div>'
                      + f'<p class="rg-lien"><a class="lien" href="{href}">{txt(a)}</a></p>')
    return niveaux


def demo_et_etapes(sec, ctx):
    """La démo de commande, puis sa légende : les quatre étapes en frise, à la taille de texte standard (audit design
    du 2026-10-23 ; étape 1 en version concise, contenus extraits.etape1.texte)."""
    fa, F = faits(ctx["t"])
    def gras(t_, mots):  # mots clés en gras, comme dans la V1
        for m in mots:
            t_ = t_.replace(m, f'<strong class="kf">{m}</strong>', 1)
        return t_
    etapes_ = [("1", esc(k("etape1")), gras(esc(k("etape1.texte")), ["nom de société", "IDE", "plus de 30 langues"]), APP[0]),
               ("2", esc(k("etape2")), esc(k("etape2.texte")), APP[1]),
               ("3", "Livraison", sans_note(F["Livraison"]), APP[2]),
               ("4", "Délai", sans_note(F["Délai"]), APP[3])]
    titre = k("etapes")
    return generique.h_tdemo(sec, ctx) + section(h2(titre, " ".join(titre.split()[-2:])) + frise(etapes_).replace('<ol class="fr">', '<ol class="fr fr-l">', 1))


def qui_traduit(sec, ctx):
    """À la place du bloc de gouvernance (repris plus haut) : encart centré à fond teinté avec les deux garanties
    (audit design du 2026-10-23 : sans l'intro, qui répétait le haut de page, ni le lien, qui doublait l'appel final)."""
    fa, F = faits(ctx["t"])
    g = "".join(f'<div><h3>{n}</h3><p>{sans_note(F[n])}</p></div>' for n in ("Qui traduit", "Confidentialité"))
    return section(f'<div class="enc enc-2"><h2>{esc(k("qui"))}</h2><div class="enc-g">{g}</div></div>')


def appel(sec, ctx):
    """Appel final : commander sur le service en ligne (demande de Fabien du 2026-10-20), la démo en lien secondaire."""
    a, b = generique.couper_cta(txt(bloc(sec, "h2")))
    return cta(a, b, (esc(k("commander")), SERVICE)).replace(
        f'href="{SERVICE}">', f'href="{SERVICE}" rel="noopener">', 1).replace(
        "</a></div></section>", f'</a><a class="lien cta-2" href="{C}">Demander une démo</a></div></section>', 1)


def haut(sec, ctx):
    """Haut de page : « Commander un extrait » en bouton principal, la démo en lien secondaire (comme l'appel final)."""
    n, s_ = generique.couper_h1(bloc(sec, "h1"))
    lead = blocs(sec, "p", "lead")
    return hero(n, s_, brut(lead[0]) if lead else "", (esc(k("commander")), SERVICE)).replace(
        f'href="{SERVICE}">', f'href="{SERVICE}" rel="noopener">', 1).replace(
        "</a></div>", f'</a><a class="lien mt-demo" href="{C}">Demander une démo</a></div>', 1)


print(P, generique.composer(P, remplacer={"thero": haut, "tdemo": demo_et_etapes, "who": lambda sec, ctx: situations_rangees(sec, generique.mots_accent(sec)), "facts": niveaux_etapes, "gov": qui_traduit, "final-cta": appel}) or "écrite")
