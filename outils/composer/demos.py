"""Démos interactives reprises de la V1 dont les textes sortent des scripts (tâche 7.3 de la traduction, Ruling 13) :
corrext/chnell/, corrext/editeur-de-relecture/, corrext/gestion-de-projet/.

Le script inline de la page V1 est remplacé par celui de demos/<outil>.js, précédé de deux blocs JSON écrits depuis
demos/<outil>.json :
- <script type="application/json" data-textes> : les textes français affichés ou annoncés par la démo (notes « Démo : »,
  annonces aria-live, noms accessibles), lus par extraire_page et traduits avec la page ; une phrase coupée autour d'une
  valeur devient un gabarit à variable nommée (« Segment {n} confirmé. »), traduit d'un seul tenant ;
- <script type="application/json" data-donnees translate="no"> : les données de la démo dans leur langue (source
  française et traduction allemande du contrat, résultats réels de CHnell), jamais traduites (Rulings 14 et 26).

Garde-fous (ValueError) : le script V1 doit être celui qui a servi à la réécriture (empreinte EMPREINTES_V1, sinon la
démo V1 a changé et demos/ est à reprendre) ; chaque texte français, coupé à ses variables, se lit mot pour mot dans les
chaînes du script V1 (repris), et chaque donnée y est une chaîne entière (aucun texte inventé).

Ajustements du HTML des démos (ajuster) : data-code sur les cases de langues de la gestion de projet (relecture 7.2 ; la
valeur reste la clé de l'état, le libellé est traduit) et lang="fr" sur le champ de recherche de l'éditeur, qui porte un
terme de la source française (« intérêt moratoire »)."""
import hashlib
import json
import re
import sys
from pathlib import Path

if str(Path(__file__).resolve().parents[2]) not in sys.path:  # lancé depuis outils/composer (LISEZMOI.md)
    sys.path.insert(0, str(Path(__file__).resolve().parents[2]))
from outils.i18n.segments import VARIABLE, litteraux_js  # noqa: E402

DOSSIER = Path(__file__).resolve().parent / "demos"
OUTILS = {"corrext/chnell/": "chnell", "corrext/editeur-de-relecture/": "editeur-de-relecture",
          "corrext/gestion-de-projet/": "gestion-de-projet"}
# 16 premiers caractères du sha256 de « <script>…</script>\n », script de la page V1 tel que generique.scripts_demo le lit
EMPREINTES_V1 = {"corrext/chnell/": "67bea932f56ef295",
                 "corrext/editeur-de-relecture/": "3bd60cdb35a03d6b",
                 "corrext/gestion-de-projet/": "5eacc8f31f257f5e"}
# cases de langues cibles de la gestion de projet : valeur (libellé français) -> code de langue
CODES = {"Allemand": "de", "Français": "fr", "Italien": "it", "Anglais": "en", "Tchèque": "cs", "Hongrois": "hu",
         "Arabe": "ar", "Bulgare": "bg", "Danois": "da", "Grec": "el", "Espagnol": "es", "Néerlandais": "nl"}


def concerne(P):
    return P in OUTILS


def chaines_v1(script_v1):
    """Chaînes du script V1, échappements résolus (analyse lexicale de outils/i18n/segments.py)."""
    return litteraux_js(script_v1)


def fragments_v1(script_v1):
    """Morceaux de texte des chaînes du script V1 : chaque chaîne coupée à ses balises."""
    return [f for c in chaines_v1(script_v1) for f in re.split(r"<[^>]*>", c) if f]


def repris(morceau, fragments):
    """Vrai si un morceau de texte (entre deux variables) se lit dans le script V1 : dans une seule chaîne, ou bout à bout
    dans des chaînes entières (phrase coupée autour d'une valeur : ' élément' puis ' en attente')."""
    if not morceau or any(morceau in f for f in fragments):
        return True
    atteints = {0}
    for i in range(len(morceau)):
        if i in atteints:
            atteints |= {i + len(f) for f in fragments if morceau.startswith(f, i)}
    return len(morceau) in atteints


def _feuilles(valeur):
    if isinstance(valeur, dict):
        for v in valeur.values():
            yield from _feuilles(v)
    elif isinstance(valeur, list):
        for v in valeur:
            yield from _feuilles(v)
    elif isinstance(valeur, str):
        yield valeur


def _bloc_json(attributs, valeur):
    texte = json.dumps(valeur, ensure_ascii=False, indent=1).replace("</", "<\\/")
    return f"<script {attributs}>\n{texte}\n</script>\n"


def scripts(P, script_v1):
    """Scripts de la démo de la page P à la place du script V1 (contenu de sa balise <script>) : blocs des textes et des
    données, puis le script réécrit. ValueError si la démo V1 a changé ou si un texte ne se lit pas dans la V1."""
    empreinte = hashlib.sha256(f"<script>{script_v1}</script>\n".encode("utf-8")).hexdigest()[:16]
    if empreinte != EMPREINTES_V1[P]:
        raise ValueError(f"{P} : le script de la démo V1 a changé (empreinte {empreinte}) : reprendre outils/composer/demos/")
    nom = OUTILS[P]
    contenu = json.loads((DOSSIER / f"{nom}.json").read_text(encoding="utf-8"))
    fragments, chaines = fragments_v1(script_v1), set(chaines_v1(script_v1))
    for cle, texte in contenu["textes"].items():
        for morceau in VARIABLE.split(texte)[::2]:
            if not repris(morceau, fragments):
                raise ValueError(f"{P} : texte « {cle} » absent du script V1 : « {morceau} »")
    for donnee in _feuilles(contenu.get("donnees", {})):
        if donnee not in chaines:
            raise ValueError(f"{P} : donnée absente du script V1 : « {donnee[:60]} »")
    sortie = _bloc_json("type=\"application/json\" data-textes", contenu["textes"])
    if "donnees" in contenu:
        sortie += _bloc_json("type=\"application/json\" data-donnees translate=\"no\"", contenu["donnees"])
    return sortie + "<script>\n" + (DOSSIER / f"{nom}.js").read_text(encoding="utf-8") + "</script>\n"


def ajuster(P, zone):
    """HTML de la démo de la page P (copie de la V1) avec les attributs que ses scripts lisent (voir le module)."""
    if P == "corrext/gestion-de-projet/":
        n = [0]

        def code(m):
            n[0] += 1
            return f'{m.group(0)[:-1]} data-code="{CODES[m.group(1)]}">'
        zone = re.sub(r'<input type="checkbox" value="([^"]+)">', lambda m: code(m) if m.group(1) in CODES else m.group(0), zone)
        if n[0] != len(CODES):
            raise ValueError(f"{P} : {n[0]} cases de langues trouvées, {len(CODES)} attendues")
    if P == "corrext/editeur-de-relecture/":
        zone, n = re.subn(r'(<input type="text" enterkeyhint="search" id="cxeQ" value="intérêt moratoire"[^>]*?)>',
                          r'\1 lang="fr">', zone)
        if n != 1:
            raise ValueError(f"{P} : champ de recherche de la démo introuvable")
    return zone
