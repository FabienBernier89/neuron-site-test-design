"""Table de segments par langue (src/langues/<langue>/segments.json) : la mémoire de traduction de la V2.

Une entrée par texte français, retrouvée par sa clé (empreinte du texte aux espaces normalisés) :
    "3f2a9c0d1e2b4a5f": {"fr": "Demander une démo", "trad": "Demo anfragen", "statut": "v1",
                         "source": "V1 de/kontakt/", "par_page": {}}
« par_page » porte les traductions propres à une page (même texte français, autre rendu) : même format sans « fr ».
Une entrée « par page seulement » (Ruling 19) n'a pas de traduction par défaut : « trad », « statut » et « source » y
valent null, et chercher ne rend rien hors de ses pages. C'est le cas d'un texte que la V1 garde en français sur une
page (terme d'une colonne française de tableau) : il n'est accepté tel quel que là.

Champ facultatif « v1 »: true : la traduction vient de la V1 validée par les traducteurs (statut v1) et le réimport l'a passée
au statut relu sans la modifier (outils/i18n/echanges.py). Elle reste exemptée des contrôles bloquants de controles.py, comme
une traduction v1 (Ruling 30 : un texte V1 validé peut porter une marque ou un libellé que le français n'a pas). Le champ n'existe
que sur l'entrée ou la traduction de page concernée, est absent sinon, et disparaît dès que poser() réécrit la traduction sans
v1=True, c'est-à-dire dès qu'elle change.

Statuts, du moins au plus sûr : mt (sortie brute de LexMachina), adapte (adaptée, non relue), v1 (validée par les
traducteurs en V1), invariant (jamais traduit), relu (relue par un traducteur expert). ACCEPTES dit lesquels une page
construite peut contenir : l'aperçu montre les traductions adaptées non relues (avec bandeau), jamais la production.

Écrire une traduction est refusé (ValueError) si elle contient un tiret cadratin ou demi-cadratin, si elle contient un
ß en allemand sans que le texte français le contienne, ou si le statut est inconnu.

Bibliothèque standard seulement."""
import hashlib
import html as H
import json
import re
from pathlib import Path

from outils.i18n import controles

ICI = Path(__file__).resolve().parent.parent.parent
SRC = ICI / "src"
LANGUES = ("de", "en", "it")
STATUTS = ("mt", "adapte", "v1", "invariant", "relu")
ACCEPTES = {"apercu": {"adapte", "v1", "invariant", "relu"}, "production": {"v1", "invariant", "relu"}}

_MARQUEUR = re.compile(r"\{/?\d+\}")  # marqueurs {n}…{/n} des balises en ligne protégées par l'extracteur
_ADRESSE = re.compile(r"(?:(?:https?://|www\.)\S+|mailto:\S+|[\w.+-]+@[\w-]+(?:\.[\w-]+)+)")


def cle(texte_fr):
    """Clé stable d'un texte français : empreinte SHA-1 tronquée, aux espaces et retours à la ligne normalisés."""
    return hashlib.sha1(" ".join(texte_fr.split()).encode()).hexdigest()[:16]


class Table:
    """Traductions d'une langue (de, en ou it), lues dans <dossier>/<langue>/segments.json."""

    def __init__(self, langue, dossier=SRC / "langues"):
        if langue not in LANGUES:
            raise ValueError(f"langue inconnue : « {langue} » (attendu : {', '.join(LANGUES)})")
        self.langue = langue
        self.fichier = Path(dossier) / langue / "segments.json"
        self.entrees = json.loads(self.fichier.read_text(encoding="utf-8")) if self.fichier.is_file() else {}

    def chercher(self, texte_fr, page):
        """Traduction de la page (par_page[page]) d'abord, sinon celle par défaut de l'entrée : {fr, trad, statut,
        source}, une copie ; None si le texte n'est pas dans la table, ou si l'entrée n'a que des traductions de page
        et aucune pour cette page."""
        entree = self.entrees.get(cle(texte_fr))
        if entree is None:
            return None
        propre = entree["par_page"].get(page)
        if propre is not None:
            return {"fr": entree["fr"], **propre}
        if entree["trad"] is None:
            return None
        return {k: entree[k] for k in ("fr", "trad", "statut", "source")}

    def poser(self, texte_fr, trad, statut, source, page=None, sans_defaut=False, v1=False):
        """Enregistre la traduction par défaut du texte, ou celle d'une page (la traduction par défaut doit alors
        exister déjà, sauf sans_defaut : l'entrée est alors créée « par page seulement », sans traduction par défaut).
        v1 : pose le champ « v1 » (voir plus haut). La table n'est écrite sur disque que par enregistrer()."""
        if statut not in STATUTS:
            raise ValueError(f"statut inconnu : « {statut} » (attendu : {', '.join(STATUTS)})")
        problemes = controles.tirets(trad)
        if self.langue == "de":
            problemes += controles.eszett(texte_fr, trad)
        if problemes:
            raise ValueError("; ".join(f"{p['regle']} : {p['detail']} ({p['extrait']})" for p in problemes))
        fr, k = " ".join(texte_fr.split()), cle(texte_fr)
        entree = self.entrees.get(k)
        if sans_defaut and page is None:
            raise ValueError("sans_defaut : une page est nécessaire")
        if page is not None:
            if entree is None and sans_defaut:
                entree = self.entrees[k] = {"fr": fr, "trad": None, "statut": None, "source": None, "par_page": {}}
            if entree is None:
                raise ValueError(f"« {fr[:50]} » : poser d'abord la traduction par défaut, puis celle de la page")
            entree["par_page"][page] = {"trad": trad, "statut": statut, "source": source, **({"v1": True} if v1 else {})}
            return
        self.entrees[k] = {"fr": fr, "trad": trad, "statut": statut, "source": source, **({"v1": True} if v1 else {}),
                           "par_page": entree["par_page"] if entree else {}}

    def t(self, texte_fr):
        """Traduction par défaut d'un libellé fixe ; KeyError si la table ne l'a pas."""
        entree = self.entrees.get(cle(texte_fr))
        if entree is None or entree["trad"] is None:
            raise KeyError(f"{self.langue} : pas de traduction pour « {' '.join(texte_fr.split())[:60]} »")
        return entree["trad"]

    def enregistrer(self):
        """Écrit le fichier : JSON trié par clé, indent 1, sans échapper les accents, textes par page triés."""
        sortie = {}
        for k in sorted(self.entrees):
            e = self.entrees[k]
            sortie[k] = {**e, "par_page": {p: e["par_page"][p] for p in sorted(e["par_page"])}}
        self.fichier.parent.mkdir(parents=True, exist_ok=True)
        self.fichier.write_text(json.dumps(sortie, indent=1, ensure_ascii=False) + "\n", encoding="utf-8")

    @staticmethod
    def est_invariant(texte_fr):
        """Vrai si le texte ne se traduit jamais : marques et libellés de l'application (proteges.json), invariants
        exacts, nombres, adresses e-mail et URL, ponctuation, ou un assemblage de ces éléments. Les marqueurs {n} des
        balises en ligne sont ignorés. Tout mot en plus (« Corrext Premium ») rend le texte traduisible."""
        p = controles.proteges()
        t = " ".join(H.unescape(_MARQUEUR.sub(" ", texte_fr)).split())
        if t in p["invariants_exacts"] or _ADRESSE.fullmatch(t):
            return True
        for nom in sorted(p["marques"] + p["libelles_application"], key=len, reverse=True):
            t = re.sub(controles._MOT_ENTIER[0] + re.escape(nom) + controles._MOT_ENTIER[1], " ", t)
        return not any(c.isalpha() for c in t)
