"""Pont entre l'onglet Corrext connecté et le dépôt, pour la première traduction (LexMachina) des segments manquants.

    python3 -m outils.i18n.pont_corrext serve de [--pages "" corrext/plugin-word/] [--port 8812]
    python3 -m outils.i18n.pont_corrext reinjecter de

serve : sert à l'onglet Corrext les textes français de src/langues/<langue>/a_traduire.json (liste écrite par
« python3 -m outils.i18n etat <langue> ») par lots de 8000 caractères au plus et enregistre les traductions reçues, brutes,
dans src/langues/<langue>/brut/traductions.json (fichier de travail, ignoré par git). --pages ne sert que les textes manquants
des pages données (clés de page de build.PAGES, « » ou « accueil » pour l'accueil) : c'est ce qui permet de ne traduire que le
pilote. Un texte déjà traduit dans la table (quel que soit son statut) n'est jamais renvoyé à LexMachina.

reinjecter : pose les traductions brutes dans la table de la langue (src/langues/<langue>/segments.json) au statut mt, source
« LexMachina <date> ». Un texte déjà traduit à un autre statut que mt n'est jamais écrasé. Avant la pose :
- les espaces que LexMachina ajoute à l'intérieur des marqueurs {n}…{/n} sont retirées (sauf si le français en a) ;
- ß devient ss en allemand (sauf mot déjà présent dans le français), un tiret long devient un trait d'union : la sortie brute
  doit pouvoir entrer dans la table, l'adaptation reprend le texte ensuite ;
- une traduction aux marqueurs abîmés (manquants, en double, inversés) est posée sans balisage et listée dans
  src/langues/<langue>/brut/a_revoir.json avec sa sortie brute : l'adaptation remet le balisage d'après le français.
Le statut mt n'est jamais publiable (table.ACCEPTES) : l'adaptation (commande fusionner) vient toujours après.

Le jeton de session Corrext reste dans l'onglet du navigateur : ce serveur ne le voit jamais (outils/i18n/pont_corrext.js,
Sites/neuron/outils/CORREXT-MT.md). Il n'écoute que sur 127.0.0.1. Ce module n'ouvre aucune connexion sortante.

Bibliothèque standard seulement."""
import argparse
import json
import re
import sys
import threading
import time
from datetime import date
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path

from outils.i18n import controles, echanges, traduire
from outils.i18n import segments as S
from outils.i18n.table import LANGUES, SRC, Table

SRC_LANGUES = SRC / "langues"
PORT = 8812
LOT_MAX_CARACTERES = 8000   # taille d'un lot de textes envoyé en un appel (la limite de l'interface est de 10 000 par texte)
LOT_MAX_TEXTES = 25
DELAI_EN_COURS = 180        # secondes : un texte servi sans réponse revient dans les lots suivants
ORIGINE = "https://corrext.com"
# Identifiants relevés dans la V1 (Sites/neuron/outils/CORREXT-MT.md, 2026-10-02) : à revérifier dans la page « Fast translation »
# de Corrext avant le premier envoi.
LANGUE_SOURCE = 51                         # français : à revérifier dans Fast translation avant le premier envoi
CIBLES = {"de": 46, "it": 140, "en": 56}   # allemand, italien, anglais : à revérifier dans Fast translation avant le premier envoi
FOURNISSEUR_LEXMACHINA = 1                 # providerId de LexMachina : à revérifier dans Fast translation avant le premier envoi
SOURCE = "LexMachina {}"
BRUT = "brut"
TRADUCTIONS = "traductions.json"
A_REVOIR = "a_revoir.json"
A_TRADUIRE = "a_traduire.json"

_MARQ = re.compile(r"\{\s*(/?)\s*(\d+)\s*\}")
_BLANCS = "[ \t\r\n]+"  # pas \s : l'espace insécable du français est voulue


def _lire_json(fichier):
    return json.loads(fichier.read_text(encoding="utf-8")) if fichier.is_file() else {}


def _ecrire_json(fichier, donnees):
    """JSON lisible (accents gardés) ; les tirets longs de la sortie brute s'écrivent en échappement JSON, jamais en clair."""
    texte = json.dumps(donnees, ensure_ascii=False, indent=0)
    for c in controles.TIRETS:
        texte = texte.replace(c, "\\u%04x" % ord(c))
    fichier.parent.mkdir(parents=True, exist_ok=True)
    fichier.write_text(texte + "\n", encoding="utf-8")


class Pont:
    """Textes à traduire d'une langue, lots servis, traductions brutes reçues (état en mémoire, traductions écrites à chaque
    réception dans <dossier>/<langue>/brut/traductions.json). Les appels viennent de plusieurs fils : un verrou."""

    def __init__(self, langue, dossier=SRC_LANGUES, cles=None, table=None, horloge=time.time):
        """cles : ensemble de clés à servir seulement (cles_des_pages) ; table : les textes déjà traduits dans la table ne
        sont pas servis ; horloge : secondes, remplaçable pour un test."""
        if langue not in CIBLES:
            raise ValueError(f"langue inconnue : « {langue} » (attendu : {', '.join(CIBLES)})")
        self.langue = langue
        self.dossier = Path(dossier) / langue
        liste = self.dossier / A_TRADUIRE
        if not liste.is_file():
            raise ValueError(f"{liste} introuvable : lancer d'abord « python3 -m outils.i18n etat {langue} »")
        self.horloge = horloge
        self.verrou = threading.Lock()
        self.fichier = self.dossier / BRUT / TRADUCTIONS
        self.faits = _lire_json(self.fichier)
        self.a_traduire = {}
        for k, e in json.loads(liste.read_text(encoding="utf-8")).items():
            traduit = table is not None and table.entrees.get(k, {}).get("trad") is not None
            if (cles is None or k in cles) and not traduit:
                self.a_traduire[k] = e["fr"]
        self.en_cours = {}

    def lot(self, n=LOT_MAX_TEXTES):
        """Prochain lot : au plus n textes et LOT_MAX_CARACTERES caractères (un texte plus long part seul). Les textes servis
        sont mis de côté DELAI_EN_COURS secondes. Rend {lot: [{k, texte}], source, cible, fournisseur}."""
        n = max(1, min(n, 100))
        maintenant, lot, taille = self.horloge(), [], 0
        with self.verrou:
            for k, texte in self.a_traduire.items():
                servi = self.en_cours.get(k)
                if k in self.faits or (servi is not None and maintenant - servi < DELAI_EN_COURS):
                    continue
                if lot and (len(lot) >= n or taille + len(texte) > LOT_MAX_CARACTERES):
                    break
                lot.append({"k": k, "texte": texte})
                taille += len(texte)
                self.en_cours[k] = maintenant
        return {"lot": lot, "source": LANGUE_SOURCE, "cible": CIBLES[self.langue], "fournisseur": FOURNISSEUR_LEXMACHINA}

    def resultat(self, corps):
        """Enregistre les traductions reçues ([{k, traduction}]) : seules comptent une clé de la liste et une traduction
        non vide ; tout le reste est ignoré, et rien d'autre que ces deux champs n'est gardé. Rend le nombre de traductions
        reçues pour la liste."""
        with self.verrou:
            for r in corps if isinstance(corps, list) else []:
                if (isinstance(r, dict) and r.get("k") in self.a_traduire and isinstance(r.get("traduction"), str)
                        and r["traduction"].strip()):
                    self.faits[r["k"]] = r["traduction"]
            _ecrire_json(self.fichier, self.faits)
            return self.etat_sans_verrou()["faits"]

    def etat_sans_verrou(self):
        return {"total": len(self.a_traduire), "faits": sum(1 for k in self.a_traduire if k in self.faits)}

    def etat(self):
        with self.verrou:
            return self.etat_sans_verrou()


def _page_relais():
    """Page chargée en cadre par l'onglet Corrext : elle parle au pont (même origine) et au parent par messages."""
    return ("<!doctype html><meta charset=utf-8><script>"
            "addEventListener('message',async e=>{if(e.origin!=='" + ORIGINE + "')return;const m=e.data||{};"
            "let r;try{if(m.op==='lot')r=await (await fetch('/lot?n='+(m.n||25))).json();"
            "else if(m.op==='etat')r=await (await fetch('/etat')).json();"
            "else if(m.op==='resultat')r=await (await fetch('/resultat',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify(m.donnees)})).json();"
            "}catch(x){r={err:String(x)}}parent.postMessage({id:m.id,r},'" + ORIGINE + "')});"
            "parent.postMessage({pret:true},'" + ORIGINE + "');</script>")


def creer_serveur(pont, port=PORT):
    """Serveur HTTP du pont sur 127.0.0.1 (port 0 : un port libre, pour les tests). L'appelant le lance (serve_forever)."""

    class Gestionnaire(BaseHTTPRequestHandler):
        def _repondre(self, code=200, donnees=None):
            self.send_response(code)
            self.send_header("Access-Control-Allow-Origin", ORIGINE)
            self.send_header("Access-Control-Allow-Private-Network", "true")
            self.send_header("Access-Control-Allow-Methods", "GET, POST, OPTIONS")
            self.send_header("Access-Control-Allow-Headers", "Content-Type")
            self.send_header("Content-Type", "application/json; charset=utf-8")
            self.end_headers()
            if donnees is not None:
                self.wfile.write(json.dumps(donnees, ensure_ascii=False).encode("utf-8"))

        def do_OPTIONS(self):
            self._repondre(204)

        def do_GET(self):
            if self.path.startswith("/relais"):
                self.send_response(200)
                self.send_header("Content-Type", "text/html; charset=utf-8")
                self.end_headers()
                self.wfile.write(_page_relais().encode("utf-8"))
            elif self.path.startswith("/lot"):
                m = re.search(r"[?&]n=(\d+)", self.path)
                self._repondre(200, pont.lot(int(m.group(1)) if m else LOT_MAX_TEXTES))
            elif self.path.startswith("/etat"):
                self._repondre(200, pont.etat())
            else:
                self._repondre(404, {"err": "inconnu"})

        def do_POST(self):
            if not self.path.startswith("/resultat"):
                self._repondre(404, {"err": "inconnu"})
                return
            try:
                corps = json.loads(self.rfile.read(int(self.headers.get("Content-Length", 0))) or b"[]")
            except (ValueError, UnicodeDecodeError):
                self._repondre(400, {"err": "corps illisible"})
                return
            self._repondre(200, {"ok": pont.resultat(corps)})

        def log_message(self, *a):
            pass

    return ThreadingHTTPServer(("127.0.0.1", port), Gestionnaire)


def cles_des_pages(langue, pages, table, assemblees=None):
    """Clés des textes manquants des pages données (clés de page de build.PAGES ; « accueil » pour l'accueil, « llms » pour
    les libellés fixes des llms.txt) : ce que traduire.analyser relève, tous statuts de refus compris, dans les deux modes
    (le bandeau de consentement de la production compris). Le libellé du bandeau de l'aperçu, que toute page traduite non
    relue porte, en fait toujours partie s'il manque : un seul passage du pont suffit. assemblees : {page: html} ou
    {page: {mode: html}} (traduire.pages_union si absent). ValueError pour une page inconnue."""
    assemblees = assemblees if assemblees is not None else traduire.pages_union(langue)
    pages = ["" if p == echanges.ACCUEIL else p for p in pages]
    inconnues = [p for p in pages if p not in assemblees and p not in echanges.PSEUDO_PAGES]
    if inconnues:
        raise ValueError("page(s) inconnue(s) : " + ", ".join(inconnues) + " (clés de page : accueil, contact/, ...)")
    manquants = traduire.manquants_bandeau(table, "apercu")
    for page in pages:
        if page == echanges.LLMS:
            manquants += traduire.verifier_libelles(table, "apercu")
        elif page != echanges.BANDEAU:
            for html in traduire.variantes(assemblees[page]):
                manquants += traduire.analyser(html, page, langue, table, "apercu")["manquants"]
    return {m["cle"] for m in manquants if m["cle"]}


# ---------- réinjection ----------

def _espaces_marqueurs(fr, trad):
    """Marqueurs remis en forme ({ /1 } devient {/1}) puis espaces retirées à l'intérieur d'une paire quand le français n'en a
    pas : LexMachina écrit « {1} Texte {/1} » pour « {1}Texte{/1} »."""
    trad = _MARQ.sub(lambda m: "{%s%s}" % (m.group(1), m.group(2)), trad)
    for m in re.finditer(r"\{(\d+)\}", fr):
        n = m.group(1)
        if "{/%s}" % n not in fr:
            continue  # marqueur seul : ses espaces ne touchent pas une paire
        if not re.match(_BLANCS, fr[m.end():]):
            trad = re.sub(r"(\{%s\})%s" % (n, _BLANCS), r"\1", trad)
        debut_fermant = fr.index("{/%s}" % n)
        if not re.search(_BLANCS + r"$", fr[:debut_fermant]):
            trad = re.sub(_BLANCS + r"(\{/%s\})" % n, r"\1", trad)
    return trad


def _aplatir(trad, marqueurs):
    """Traduction sans aucun marqueur : un marqueur seul du français (<br>, jeton) devient une espace, les autres s'effacent."""
    return " ".join(_MARQ.sub(lambda m: " " if "vide" in marqueurs.get(int(m.group(2)), {}) else "", trad).split())


def reinjecter(langue, table, dossier=SRC_LANGUES, jour=None):
    """Pose les traductions brutes (brut/traductions.json) dans la table, en mémoire (l'appelant fait enregistrer()), au statut
    mt, source « LexMachina <jour> ». Écrit brut/a_revoir.json. Rend {poses, deja_traduits, hors_liste, eszett, a_revoir :
    [{cle, fr, trad_brute, probleme}]}. Voir le docstring du module pour les corrections mécaniques et les marqueurs abîmés."""
    dossier = Path(dossier) / langue
    source = SOURCE.format(jour or date.today().isoformat())
    liste = {k: e["fr"] for k, e in _lire_json(dossier / A_TRADUIRE).items()}
    faits = _lire_json(dossier / BRUT / TRADUCTIONS)
    rapport = {"poses": 0, "deja_traduits": 0, "hors_liste": 0, "eszett": 0, "a_revoir": []}
    for k in sorted(faits):
        if k not in liste:
            rapport["hors_liste"] += 1
            continue
        fr, brut = liste[k], faits[k]
        entree = table.entrees.get(k)
        if entree is not None and entree["trad"] is not None and entree["statut"] != "mt":
            rapport["deja_traduits"] += 1
            continue
        marqueurs = echanges._table_marqueurs(fr)
        trad, problemes = _espaces_marqueurs(fr, brut), []
        try:
            S.restaurer(trad, marqueurs)
        except ValueError as e:
            problemes.append(str(e))
            trad = _aplatir(trad, marqueurs)
        if controles.tirets(trad):
            problemes.append("tiret long de la sortie brute remplacé par un trait d'union : à reprendre")
            for c in controles.TIRETS:
                trad = trad.replace(c, "-")
        if langue == "de":
            avant = trad
            for p in controles.eszett(fr, trad):
                trad = trad.replace(p["extrait"], p["extrait"].replace("ß", "ss"))
            rapport["eszett"] += trad != avant
        try:
            table.poser(fr, trad, "mt", source)
        except ValueError as e:  # filet : ce que poser refuse encore (tiret écrit en entité HTML)
            rapport["a_revoir"].append({"cle": k, "fr": fr, "trad_brute": brut, "probleme": f"non posée : {e}"})
            continue
        rapport["poses"] += 1
        if problemes:
            rapport["a_revoir"].append({"cle": k, "fr": fr, "trad_brute": brut, "probleme": " ; ".join(problemes)})
    _ecrire_json(dossier / BRUT / A_REVOIR, rapport["a_revoir"])
    return rapport


# ---------- ligne de commande ----------

def afficher_reinjection(langue, rapport, fichier):
    lignes = [f"Réinjection {langue} : {rapport['poses']} traduction(s) posée(s) au statut mt, "
              f"{len(rapport['a_revoir'])} à revoir (marqueurs abîmés ou texte corrigé mécaniquement), "
              f"{rapport['deja_traduits']} déjà traduite(s) à un autre statut (non écrasées), "
              f"{rapport['hors_liste']} hors de la liste à traduire (ignorée(s))"]
    if langue == "de":
        lignes.append(f"ß remplacé par ss dans {rapport['eszett']} traduction(s)")
    lignes += [f"  {a['cle']} « {a['fr'][:60]} » : {a['probleme']}" for a in rapport["a_revoir"][:20]]
    if len(rapport["a_revoir"]) > 20:
        lignes.append(f"  et {len(rapport['a_revoir']) - 20} autre(s) : voir {fichier}")
    return "\n".join(lignes)


def main(argv=None):
    parser = argparse.ArgumentParser(prog="python3 -m outils.i18n.pont_corrext",
                                     description="Pont entre l'onglet Corrext connecté et la table de traduction.")
    sous = parser.add_subparsers(dest="commande", required=True)
    p = sous.add_parser("serve", help="servir les lots à l'onglet Corrext et enregistrer les traductions brutes")
    p.add_argument("langue", choices=LANGUES)
    p.add_argument("--pages", nargs="+", help='ne servir que les textes manquants de ces pages (« » ou accueil, corrext/plugin-word/, ...)')
    p.add_argument("--port", type=int, default=PORT)
    p = sous.add_parser("reinjecter", help="poser les traductions brutes dans la table au statut mt")
    p.add_argument("langue", choices=LANGUES)
    args = parser.parse_args(argv)
    table = Table(args.langue, SRC_LANGUES)
    if args.commande == "reinjecter":
        rapport = reinjecter(args.langue, table, SRC_LANGUES)
        table.enregistrer()
        print(afficher_reinjection(args.langue, rapport, SRC_LANGUES / args.langue / BRUT / A_REVOIR))
        print(f"Table : {table.fichier}")
        return 0
    try:
        cles = cles_des_pages(args.langue, args.pages, table) if args.pages else None
        pont = Pont(args.langue, SRC_LANGUES, cles=cles, table=table)
    except ValueError as e:
        print(f"Pont non lancé : {e}", file=sys.stderr)
        return 1
    serveur = creer_serveur(pont, args.port)
    etat = pont.etat()
    print(f"Pont {args.langue} sur http://localhost:{args.port} : {etat['faits']}/{etat['total']} déjà traduits"
          + (f" (pages : {', '.join(p or echanges.ACCUEIL for p in args.pages)})" if args.pages else ""))
    print(f"Identifiants envoyés à l'onglet : français {LANGUE_SOURCE}, cible {CIBLES[args.langue]}, fournisseur "
          f"{FOURNISSEUR_LEXMACHINA} (à revérifier dans Fast translation avant le premier envoi)")
    try:
        serveur.serve_forever()
    except KeyboardInterrupt:
        print("Pont arrêté.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
