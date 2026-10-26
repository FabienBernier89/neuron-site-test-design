"""Image de partage (og:image) d'une langue : remplit le gabarit src/data/og/og.html (1200 x 630, reproduction de
assets/img/og-neuron.jpg de la V1, décision V10) et en fait une capture PNG avec Chrome sans interface.

    python3 -m outils.i18n.og_image <langue> <sortie.png>     # textes FR de src/data/og/textes.json, pour contrôler le gabarit

generer(langue, titre, accent, signature, sortie) : le titre passe en deux lignes à la largeur du gabarit ; l'accent est la
fin du titre, affichée en bleu. La police (Inter) et le logo blanc sont intégrés au HTML en données : la capture ne dépend
d'aucun fichier voisin. Le logo vient du site Neur.on V1 (variable NEURON_SRC, comme build.py), lu sans y écrire.

Chrome : /Applications/Google Chrome.app sur macOS, ou le programme donné par la variable CHROME. Sans Chrome, generer lève
RuntimeError. Le FR garde son image actuelle : ce module ne sert qu'aux autres langues.

Bibliothèque standard seulement."""
import base64
import html as H
import os
import subprocess
import sys
import tempfile
from pathlib import Path

ICI = Path(__file__).resolve().parent.parent.parent
GABARIT = ICI / "src/data/og/og.html"
POLICE = ICI / "assets/fonts/inter-latin.woff2"
LOGO = Path(os.environ.get("NEURON_SRC", ICI.parent / "neuron")).resolve() / "assets/img/neuron-logo-blanc.png"
CHROME_MAC = "/Applications/Google Chrome.app/Contents/MacOS/Google Chrome"
DIMENSIONS = (1200, 630)
DELAI = 60  # secondes accordées à Chrome


def chrome():
    """Chemin du programme Chrome (variable CHROME, sinon l'application macOS) ; None s'il est absent."""
    chemin = os.environ.get("CHROME") or CHROME_MAC
    return chemin if Path(chemin).is_file() else None


def _donnees(fichier, type_mime):
    return f"data:{type_mime};base64," + base64.b64encode(Path(fichier).read_bytes()).decode("ascii")


def remplir(langue, titre, accent, signature, ressources=True):
    """HTML du gabarit rempli. L'accent doit terminer le titre (il est affiché en bleu, dans un span). ressources=False
    laisse la police et le logo vides : pour contrôler le texte sans lire les fichiers."""
    if not accent or not titre.endswith(accent):
        raise ValueError(f"l'accent « {accent} » doit être la fin du titre « {titre} »")
    debut = titre[:len(titre) - len(accent)]
    corps = f"{H.escape(debut, quote=False)}<span>{H.escape(accent, quote=False)}</span>"
    valeurs = {"{{LANGUE}}": H.escape(langue), "{{TITRE}}": corps, "{{SIGNATURE}}": H.escape(signature, quote=False),
               "{{INTER}}": _donnees(POLICE, "font/woff2") if ressources else "",
               "{{LOGO}}": _donnees(LOGO, "image/png") if ressources else ""}
    gabarit = GABARIT.read_text(encoding="utf-8")
    for marque, valeur in valeurs.items():
        gabarit = gabarit.replace(marque, valeur)
    return gabarit


def generer(langue: str, titre: str, accent: str, signature: str, sortie: Path) -> None:
    """Écrit l'image de partage de la langue dans sortie (PNG de 1200 x 630)."""
    programme = chrome()
    if programme is None:
        raise RuntimeError("Chrome introuvable (variable CHROME ou /Applications/Google Chrome.app)")
    sortie = Path(sortie)
    sortie.parent.mkdir(parents=True, exist_ok=True)
    page = remplir(langue, titre, accent, signature)
    with tempfile.TemporaryDirectory(prefix="neuron-og-") as tmp:
        fichier, capture = Path(tmp) / "og.html", Path(tmp) / "og.png"
        fichier.write_text(page, encoding="utf-8")
        commande = [programme, "--headless=new", "--disable-gpu", "--hide-scrollbars", "--force-device-scale-factor=1",
                    f"--user-data-dir={Path(tmp) / 'profil'}", "--virtual-time-budget=3000",
                    f"--window-size={DIMENSIONS[0]},{DIMENSIONS[1]}", f"--screenshot={capture}", fichier.as_uri()]
        resultat = subprocess.run(commande, stdout=subprocess.DEVNULL, stderr=subprocess.PIPE, timeout=DELAI)
        if not capture.is_file():
            raise RuntimeError("Chrome n'a pas produit de capture : " + resultat.stderr.decode("utf-8", "replace")[-300:])
        sortie.write_bytes(capture.read_bytes())


def _principal(argv):
    import json
    if len(argv) != 2:
        print(__doc__.split("\n\n")[0], file=sys.stderr)
        return 2
    textes = {e["id"]: e for e in json.loads((GABARIT.parent / "textes.json").read_text(encoding="utf-8"))["entrees"]}
    t = textes["titre"]
    generer(argv[0], t["texte"], t["accent"], textes["signature"]["texte"], Path(argv[1]))
    print(f"Image écrite : {argv[1]}")
    return 0


if __name__ == "__main__":
    sys.exit(_principal(sys.argv[1:]))
