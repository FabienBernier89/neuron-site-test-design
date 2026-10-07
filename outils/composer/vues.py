"""Vues Corrext par fonction : un écran précis pour chaque bloc explicatif.

Chaque vue reproduit l'état de l'application que décrit le texte voisin (lot de fichiers, devis, alternatives,
analyse d'un fichier, commande d'extrait, vignettes d'outil). Les libellés viennent tous des démos Corrext
publiées ou des maquettes du site Neur.on ; rien n'est inventé. Le HTML porte l'état final (lisible sans script),
la scène de sim.js rejoue le parcours qui y mène.
"""
import re

from app import IC, e, onglets, selecteur, travail, alternatives, chnell, lignes_chnell

COCHE = '<svg viewBox="0 0 16 16" aria-hidden="true" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M3.5 8.5l3 3 6-6.5"/></svg>'
CAL = ('<svg viewBox="0 0 16 16" aria-hidden="true" fill="none" stroke="currentColor" stroke-width="1.4" stroke-linecap="round" '
       'stroke-linejoin="round"><rect x="2.5" y="3.5" width="11" height="10" rx="1.6"/><path d="M2.5 6.5h11M5.5 2v3M10.5 2v3"/></svg>')
SCEAU = ('<svg viewBox="0 0 16 16" aria-hidden="true" fill="none" stroke="currentColor" stroke-width="1.4" stroke-linecap="round" '
         'stroke-linejoin="round"><circle cx="8" cy="6.5" r="4"/><path d="M5.6 9.8 4.8 14l3.2-1.6 3.2 1.6-.8-4.2"/></svg>')


def _etapes(libelles, courante):
    """Fil d'étapes : étapes passées cochées, étape courante numérotée."""
    out = []
    for i, l in enumerate(libelles):
        etat = "ok" if i < courante else "cur" if i == courante else ""
        pastille = COCHE if i < courante else str(i + 1)
        out.append(f'<span class="vw-et {etat}" data-i="{i}"><i>{pastille}</i><span>{l}</span></span>')
    return '<div class="vw-steps">' + '<b class="vw-lien"></b>'.join(out) + "</div>"


# ---------- Lot de fichiers (File translation) ----------

def ligne_fichier(nom, sous, run, fin, i=0):
    return (f'<div class="cr-file vw-f charge fait" style="--i:{i}">{IC["fichier"]}<span class="fm"><span class="fn">{nom}</span>'
            f'<span class="fs">{sous}</span><span class="bar"><i></i></span></span>'
            f'<span class="cr-st"><span class="s0">{run}</span><span class="s1">{fin}</span></span></div>')


def vue_fichiers(fichiers, cible="French", depot=None):
    """Onglet File translation : moteur LexMachina, mode Highly sensitive, fichiers rendus dans leur format.

    fichiers : liste de dict(nom, sous, run, fin) ; depot : dict(drop_t, drop_s) pour afficher la zone de dépôt.
    """
    cfg = ('<div class="cr-cfg"><div><label>Translation engine</label>'
           + selecteur("LexMachina", "cr-eng").replace('</span><svg', '<small class="vw-suisse">Suisse</small></span><svg', 1)
           + f'</div><div><label>Translation target language</label>{selecteur(cible)}</div></div>')
    zone = ""
    if depot:
        zone = (f'<div class="cr-drop vw-drop">{IC["depot"]}<span class="t">{depot["drop_t"]}</span>'
                f'<span class="s">{depot["drop_s"]}</span></div>')
    lignes = "".join(ligne_fichier(f["nom"], f["sous"], f["run"], f["fin"], i) for i, f in enumerate(fichiers))
    return (f'<div class="cr cr-frag cr-vw vw-lot">{onglets(1, hs=True)}<div class="vw-c">{cfg}'
            f'<p class="cr-h4">Upload your file(s)</p>{zone}<div class="vw-files">{lignes}</div></div></div>')


# ---------- Gestion de projet : devis avec relecture externe ----------

def vue_devis(fichier, langues, niveaux, choisi):
    """Étape Devis : parcours personnalisé, niveau de relecture choisi pour le fichier, échéance, création."""
    menu = "".join(f'<span{" class=\"on\"" if n == choisi else ""} data-v="{n}">{n}</span>' for n in niveaux)
    return ('<div class="cr cr-frag cr-vw vw-devis fini">'
            + _etapes(["Créer un projet", "Fichiers", "Devis"], 2)
            + '<div class="vw-c"><p class="vw-h">Devis</p><p class="vw-s">Choisissez qui relit la traduction automatique, puis obtenez le délai estimé et le devis.</p>'
            '<div class="vw-opts"><div class="vw-opt" data-o="0"><i></i><b>Relecture interne</b><span>Durée de la relecture interne : 1 à 2 heures</span></div>'
            '<div class="vw-opt on" data-o="1"><i></i><b>Parcours personnalisé</b><span>Relecture externe, échéance et ordre de priorité</span></div></div>'
            '<div class="vw-ext"><p class="vw-h5">Paramètres de la relecture externe</p>'
            '<div class="vw-tab"><div class="vw-tr vw-th"><span>Fichier</span><span>Langues</span><span>Relecture</span></div>'
            f'<div class="vw-tr"><span class="vw-fn">{IC["fichier"]}{fichier}</span><span>{langues}</span><span><em class="vw-tag">Externe</em></span></div>'
            f'<div class="vw-sub"><span class="vw-lab">Niveau de relecture</span>'
            f'<span class="cr-sel vw-niv"><span class="cr-v">{choisi}</span>{IC["chevron"]}<span class="cr-menu">{menu}</span></span></div></div>'
            f'<div class="vw-pied"><span class="vw-ech">{CAL}<span><b>Échéance</b><small>Contactez-nous pour une livraison plus rapide</small></span></span>'
            '<span class="cr-btn cr-btn-p vw-go">Créer le projet</span></div></div></div></div>')


# ---------- Alternatives par moteur ----------

def vue_alternatives(cle, src, sortie, alt, alt_moteur, total, tabs=False):
    """Espace de traduction rempli, panneau Alternatives ouvert sur la proposition d'un moteur tiers.

    cle : extrait de SIM_EX que la scène « alts » parcourt (pagineur, moteur de chaque proposition).
    """
    alts = alternatives(alt, alt_moteur).replace('<span class="cr-pgn">1 / 2</span>', f'<span class="cr-pgn">1 / {total}</span>', 1)
    return (f'<div class="cr cr-frag cr-vw vw-alts alts" data-ex="{cle}">' + (onglets(0, hs=True) if tabs else "")
            + travail(detecte=True, src=src, out=sortie) + f'<div class="cr-bas">{alts}</div></div>')


# ---------- Gestion de projet : analyse d'un fichier déposé ----------

def vue_analyse(fichier, pages, unite, langue, categorie):
    """Étape Fichiers : Corrext détecte la langue, la catégorie juridique et le nombre de pages standard."""
    return ('<div class="cr cr-frag cr-vw vw-an fini">'
            + _etapes(["Créer un projet", "Fichiers", "Devis"], 1)
            + '<div class="vw-c"><p class="vw-h">Fichiers</p><p class="vw-s">Déposez les documents à traduire. Corrext analyse chaque fichier avant le devis.</p>'
            f'<div class="vw-carte"><div class="vw-carte-h">{IC["fichier"]}<b>{fichier}</b><span class="vw-anl">Analyse en cours…</span>'
            f'<span class="vw-pg"><b>{pages}</b> {unite}</span></div>'
            f'<div class="vw-det"><div><label>Langue détectée</label><span class="cr-sel"><span class="cr-v">{langue}</span>{IC["chevron"]}</span></div>'
            f'<div><label>Catégorie détectée</label><span class="cr-sel"><span class="cr-v">{categorie}</span>{IC["chevron"]}</span></div></div></div>'
            '<div class="vw-opts vw-opts-mini"><div class="vw-opt"><i></i><b>Relecture interne</b><span>Durée de la relecture interne : 1 à 2 heures</span></div>'
            '<div class="vw-opt"><i></i><b>Parcours personnalisé</b><span>Relecture externe, échéance et ordre de priorité</span></div></div>'
            '</div></div>')


# ---------- Extraits du registre du commerce : commande ----------

def vue_extrait(etapes, niveaux, societe, ide, langue, choisi, recap):
    """Étape 2 de la commande : niveau de certification choisi, récapitulatif « Your order » à jour.

    niveaux : liste de (titre, description) ; recap : (Company, Target language, Certification level).
    """
    cartes = "".join(f'<div class="vw-niv-c{" on" if i == choisi else ""}" data-n="{i}"><i></i><span><b>{t}</b><small>{d}</small></span></div>'
                     for i, (t, d) in enumerate(niveaux))
    return ('<div class="cr cr-frag cr-vw vw-hr fini">' + _etapes(etapes, 1)
            + '<div class="vw-hr-g"><div class="vw-c">'
            f'<div class="vw-soc">{SCEAU}<span><b>{societe}</b><small>{ide}</small></span><em class="vw-tag">Selected</em></div>'
            f'<p class="vw-h">{etapes[1]}</p><p class="vw-s">Choose the level required by the recipient of the translation.</p>'
            f'<div class="vw-nivs">{cartes}</div></div>'
            f'<aside class="vw-ord"><p class="vw-h5">Your order</p><dl><dt>{recap[0]}</dt><dd>{societe}</dd><dt>{recap[1]}</dt><dd>{langue}</dd>'
            f'<dt>{recap[2]}</dt><dd class="vw-ord-n">{niveaux[choisi][0]}</dd></dl></aside></div></div>')


# ---------- Vignettes d'outil (cartes « outils les plus utilisés ») ----------

def vignette(win):
    """Reprend une maquette jv du site Neur.on (mêmes textes) et la rend au niveau des écrans Corrext."""
    corps = re.search(r'<div class="jv-body">(.*)</div>\s*</div>\s*$', win.strip(), re.S)
    corps = corps.group(1) if corps else ""
    return f'<div class="cr cr-vg">{corps}</div>'


def vue_chnell(lookup):
    """CHnell seul, résultats alignés et sources (texte de la page hub : Verzugszins, 324 segments)."""
    return (f'<div class="cr cr-frag cr-chst cr-vw vw-ch">{chnell(e(lookup["q"]), e(lookup["l1"]), e(lookup["l2"]), e(lookup["count"]), lignes_chnell(lookup))}</div>')
