from commun import *
P = "contact/"
t = liens(charger(P), P)
out = []
th = bloc(t, "section", "thero")
spec = bloc(th, "div", "law-spec")
tuiles_g = "".join(f'<li><b>{txt(bloc(r, "i"))}</b><span>{txt(bloc(r, "b"))}</span></li>' for r in blocs(spec, "div", "sr"))
gauche = (f'<div class="ct-l"><h1 class="h1"><span class="n">Demandez une démo.</span> <span class="s">Corrext, ouvert sur vos propres documents</span></h1>'
          f'<p>{brut(bloc(th, "p", "lead"))}</p><p class="k">{txt(bloc(bloc(spec, "div", "sh"), "b"))}</p><ul>{tuiles_g}</ul></div>')
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


champs = []
for rang in blocs(fo, "div", "cf-row"):
    champs += [champ(f) for f in blocs(rang, "div", "cf-f")]
    if "cf-sujet" in rang:
        pass
fs = bloc(fo, "fieldset")
cases = "".join(f'<label class="case">{re.search(r"<input[^>]*>", c).group(0)}<span>{txt(bloc(c, "span"))}</span></label>' for c in blocs(fs, "label", "cf-check"))
champs.insert(6, f'<fieldset class="pl"><legend>{txt(bloc(fs, "legend"))}</legend><div class="cases">{cases}</div></fieldset>')
message = [f for f in blocs(fo, "div", "cf-f") if "cf-message" in f][0]
champs.append(champ(message, True))
cs = bloc(fo, "div", "cf-consent")
cons_lab = bloc(cs, "label")
cons = (f'<div class="cs">{re.search(r"<input[^>]*>", cs).group(0)}<label for="cf-consent">'
        f'{brut(re.sub(r"<span class=\"cf-req\"[^>]*>.*?</span>", "", interne(cons_lab), flags=re.S))}<span class="req" aria-hidden="true">*</span></label></div>')
envoi = bloc(fo, "div", "cf-send")
alt = bloc(envoi, "span", "cf-hint")
form = (f'<form data-demo novalidate>{"".join(champs)}{cons}'
        f'<button type="submit" class="btn">{txt(bloc(envoi, "button"))}</button>'
        f'<p class="avis" data-libre hidden>Formulaire de démonstration : aucun envoi.</p>'
        f'<p class="alt">{brut(interne(alt))}</p><p class="usage">{brut(bloc(fo, "p", "cf-usage"))}</p></form>')
droite = f'<div class="ct-f"><h2>{txt(bloc(fo, "h2"))}</h2><p>{brut(bloc(fo, "p", "cf-intro"))}</p>{form}</div>'
out.append(f'<section><div class="wrap ct">{gauche}{droite}</div></section>\n')
# Après l'envoi, nous écrire, le cadre : trois tuiles
side = bloc(t, "div", "cf-side")
tl = []
for c in blocs(side, "div", "cf-card"):
    titre = txt(bloc(c, "h2"))
    reste = c.replace(bloc(c, "h2"), "")
    if "cf-steps" in reste:
        corps = "".join(f'<li><b>{brut(bloc(s, "b"))}</b> {brut(re.sub(r"<b>.*?</b>", "", interne(blocs(s, "span")[1]), flags=re.S))}</li>' for s in blocs(bloc(reste, "div", "cf-steps"), "div")[1:])
        corps = f"<ol>{corps}</ol>"
    elif "cf-adr" in reste:
        corps = f'<p>{brut(interne(bloc(reste, "address")))}</p><p class="sous">{txt(bloc(reste, "h3"))}</p><p>' + " · ".join(f"<span>{txt(s)}</span>" for s in blocs(bloc(reste, "div", "cf-langs"), "span")) + "</p>"
    else:
        corps = "<ul>" + "".join(f"<li>{brut(interne(s))}</li>" for s in blocs(bloc(reste, "div", "cf-seal"), "span") if "<span" not in s[5:]) + "</ul>"
    tl.append(f"<div><b>{titre}</b><div class=\"tl-c\">{corps}</div></div>")
out.append(section('<div class="tl txt">' + "".join(tl) + "</div>"))
out.append(faq_section(t))
fc = bloc(t, "section", "final-cta")
out.append(cta("Une question", "avant de nous écrire ?", ("team@corrext.com", "mailto:team@corrext.com")))
ecrire(P, entete_existant(P), "".join(out))
print("contact écrit")
