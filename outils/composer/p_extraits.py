"""Page Extraits du registre du commerce : composée par generique.py, avec une structure propre (proposition C retenue
par Fabien le 2026-10-21) : le choix du niveau de certification d'abord, les trois niveaux en colonnes (un seul exposé
des niveaux, au lieu des cartes et du bento de la V1), puis la commande en quatre étapes en frise, « Qui traduit, et
où » en rangées et l'appel final « Commander un extrait » vers le service en ligne auszug-hr.ch.

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
    etapes_ = [("1", esc(k("etape1")), f'{sans_note(F["Recherche"])} {sans_note(F["Langues"])}', APP[0]),
               ("2", esc(k("etape2")), esc(k("etape2.texte")), APP[1]),
               ("3", "Livraison", sans_note(F["Livraison"]), APP[2]),
               ("4", "Délai", sans_note(F["Délai"]), APP[3])]
    titre = k("etapes")
    return niveaux + section(h2(titre, " ".join(titre.split()[-2:])) + frise(etapes_))


def qui_traduit(sec, ctx):
    """À la place du bloc de gouvernance (repris plus haut) : qui traduit et la confidentialité, en rangées."""
    fa, F = faits(ctx["t"])
    lead = bloc(fa, "div", "facts-lead")
    a = [x for x in blocs(lead, "a", "feat-link") if SERVICE in x][0]
    titre = k("qui")
    return section(rangees(h2(titre, titre.split(", ")[1]), brut(bloc(lead, "p")), (txt(a), SERVICE),
                           [("Qui traduit", sans_note(F["Qui traduit"])), ("Confidentialité", sans_note(F["Confidentialité"]))]))


def appel(sec, ctx):
    """Appel final : commander sur le service en ligne (demande de Fabien du 2026-10-20), la démo en lien secondaire."""
    a, b = generique.couper_cta(txt(bloc(sec, "h2")))
    return cta(a, b, (esc(k("commander")), SERVICE)).replace(
        f'href="{SERVICE}">', f'href="{SERVICE}" rel="noopener">', 1).replace(
        "</a></div></section>", f'</a><a class="lien cta-2" href="{C}">Demander une démo</a></div></section>', 1)


print(P, generique.composer(P, remplacer={"facts": niveaux_etapes, "gov": qui_traduit, "final-cta": appel}) or "écrite")
