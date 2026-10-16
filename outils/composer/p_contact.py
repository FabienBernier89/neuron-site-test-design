from commun import *
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[2]))
from outils.contenus import texte  # noqa: E402
from outils.post.z_formulaires import _secteur  # noqa: E402
import html as _H


def e(s):
    return _H.escape(s, quote=False)


P = "contact/"
t = liens(charger(P), P)
out = []
th = bloc(t, "section", "thero")
spec = bloc(th, "div", "law-spec")
# Conversion (retour de Fabien du 2026-10-16, skill cro) : à gauche le titre, l'accroche (sa première phrase) et la
# réassurance (étapes après l'envoi, cadre, adresse) ; à droite le formulaire, obligatoires d'abord, facultatifs ensuite
lead = brut(bloc(th, "p", "lead"))
lead = lead[:lead.index(". ") + 1] if ". " in lead else lead
titre = ('<div class="ct-t"><h1 class="h1"><span class="n">Demandez une démo.</span> <span class="s">Corrext, ouvert sur vos propres documents</span></h1>'
         f'<p>{lead}</p></div>')
fo = bloc(t, "form", "cf-form")


def champ(f, plein=False):
    lab = bloc(f, "label")
    ident = re.search(r'for="([^"]+)"', lab).group(1)
    req = "cf-req" in lab
    libelle = txt(re.sub(r'<span class="cf-req"[^>]*>.*?</span>', "", lab, flags=re.S))
    m = re.search(r"<select\b.*?</select>|<textarea\b.*?</textarea>|<input\b[^>]*>", f, re.S)
    ctrl = m.group(0)
    ctrl = re.sub(r'\sclass="cf-in"', "", ctrl)
    hint = blocs(f, "p", "cf-hint")
    h = f'<p class="aide">{brut(hint[0])}</p>' if hint else ""
    etoile = '<span class="req" aria-hidden="true">*</span>' if req else ""
    return f'<div{" class=\"pl\"" if plein else ""}><label for="{ident}">{libelle}{etoile}</label>{ctrl}{h}</div>'


def champ_par_id(ident, plein=False):
    f = next(x for x in blocs(fo, "div", "cf-f") if f'id="{ident}"' in x)
    return champ(f, plein)


obligatoires = [champ_par_id("cf-prenom"), champ_par_id("cf-nom"), champ_par_id("cf-email", True),
                champ_par_id("cf-organisation"), champ_par_id("cf-fonction")]
fs = bloc(fo, "fieldset")
cases = "".join(f'<label class="case">{re.search(r"<input[^>]*>", c).group(0)}<span>{txt(bloc(c, "span"))}</span></label>' for c in blocs(fs, "label", "cf-check"))
facultatifs = [_secteur().replace('<div class="pl">', "<div>", 1), champ_par_id("cf-taille"),  # Secteur et Taille côte à côte
               f'<fieldset class="pl"><legend>{txt(bloc(fs, "legend"))}</legend><div class="cases">{cases}</div></fieldset>',
               champ_par_id("cf-volume", True), champ_par_id("cf-message", True)]  # « Ce que vous traduisez » retiré (2026-10-16)
cs = bloc(fo, "div", "cf-consent")
cons_lab = bloc(cs, "label")
cons = (f'<div class="cs">{re.search(r"<input[^>]*>", cs).group(0)}<label for="cf-consent">'
        f'{brut(re.sub(r"<span class=\"cf-req\"[^>]*>.*?</span>", "", interne(cons_lab), flags=re.S))}<span class="req" aria-hidden="true">*</span></label></div>')
envoi = bloc(fo, "div", "cf-send")
alt = bloc(envoi, "span", "cf-hint")
groupe = (f'<div class="ct-opt"><p class="ct-og">{e(texte("contact.facultatif.titre"))}</p>'
          f'<p class="ct-on">{e(texte("contact.facultatif.note"))}</p></div>')
form = (f'<form data-demo novalidate>{"".join(obligatoires)}{groupe}{"".join(facultatifs)}{cons}'
        f'<button type="submit" class="btn">{e(texte("contact.bouton"))}</button>'
        f'<p class="delai">{e(texte("contact.delai"))}</p>'  # délai de réponse, près du bouton (Fabien, 2026-10-16)
        f'<p class="avis" data-libre hidden>Formulaire de démonstration : aucun envoi.</p>'
        f'<p class="usage">{brut(bloc(fo, "p", "cf-usage"))}</p></form>')
droite = f'<div class="ct-f"><h2>{txt(bloc(fo, "h2"))}</h2><p>{brut(bloc(fo, "p", "cf-intro"))}</p>{form}</div>'
# Réassurance à gauche : ce qui se passe après l'envoi, le cadre, nous écrire
side = bloc(t, "div", "cf-side")
rassure = []
for c in blocs(side, "div", "cf-card"):
    titre_c = txt(bloc(c, "h2"))
    reste = c.replace(bloc(c, "h2"), "")
    if "cf-steps" in reste:
        def etape(s):
            corps = brut(re.sub(r"<b>.*?</b>", "", interne(blocs(s, "span")[1]), flags=re.S))
            corps = re.sub(r"\s*Jamais un accès anonyme en libre-service\.", "", corps)  # ton positif près du bouton
            return f'<li><b>{brut(bloc(s, "b"))}</b><span>{corps}</span></li>'
        rassure.append(f'<div class="ct-b"><p class="ct-bt">{titre_c}</p><ol class="ct-et">'
                       + "".join(etape(s) for s in blocs(bloc(reste, "div", "cf-steps"), "div")[1:]) + "</ol></div>")
    elif "cf-adr" in reste:
        adresse = brut(interne(bloc(reste, "address")))
    else:
        rassure.append(f'<div class="ct-b"><p class="ct-bt">{titre_c}</p><ul class="ct-ok">'
                       + "".join(f"<li>{brut(interne(s))}</li>" for s in blocs(bloc(reste, "div", "cf-seal"), "span") if "<span" not in s[5:]) + "</ul></div>")
rassure.append(f'<p class="ct-ecr">{brut(interne(alt))}</p>')
# Preuve sociale (retour de Fabien du 2026-10-16) : les distinctions du bandeau de l'accueil, publiables telles quelles
t0 = liens(charger(""), "")
hl = [txt(x) for x in blocs(bloc(t0, "div", "hero-logos"), "span", "hl") if "aria-hidden" not in x[:60]]
prix = [(x.split(" · ", 1)[0], x.split(" · ", 1)[1] if " · " in x else "") for x in hl]
choisis = [d for d in prix if not d[0].startswith(("ISO", "Hébergement"))][:4]  # le cadre (ISO, hébergement) est déjà plus bas
preuve = (f'<div class="ct-pv"><p class="ct-bt">{txt(bloc(bloc(t0, "section", "trust"), "h2"))}</p><ul>'
          + "".join(f"<li><b>{e(n)}</b>" + (f"<span>{e(d)}</span>" if d else "") + "</li>" for n, d in choisis) + "</ul></div>")
gauche = titre + '<div class="ct-r">' + preuve + "".join(rassure) + "</div>"
out.append(f'<section><div class="wrap ct">{gauche}{droite}</div></section>\n')
out.append(faq_section(t))
fc = bloc(t, "section", "final-cta")
# Appel final en bleu foncé (retour de Fabien du 2026-10-16)
out.append(cta("Une question", "avant de nous écrire ?", ("team@corrext.com", "mailto:team@corrext.com")).replace('<section class="cta">', '<section class="cta cta-n">', 1))
ecrire(P, entete_existant(P), "".join(out))
print("contact écrit")
