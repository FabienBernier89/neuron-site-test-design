"""Script d'envoi des formulaires (envoi.php, à la racine du dépôt) : le build le copie à la racine du site, avec le
destinataire et l'expéditeur de src/data/config.json écrits dans ses constantes. Une adresse mal formée arrête le
build : elle ne doit jamais finir dans du code PHP.

Table des pages de remerciement (constante MERCI) : la source porte les quatre langues, pour que tests/test_envoi.php les
exerce ; le script généré n'en garde que les langues construites dont la page de remerciement existe (le français
toujours, c'est le repli d'une langue inconnue). Chaque adresse est relue dans src/data/routes.json : une source qui s'en
écarte arrête le build."""
import re
from pathlib import Path

from outils.i18n.langues import LANGUES, route

SOURCE = Path(__file__).resolve().parents[1] / "envoi.php"
ADRESSE = re.compile(r"[A-Za-z0-9._%+-]+@[A-Za-z0-9-]+(?:\.[A-Za-z0-9-]+)+")
PAGE_MERCI = "contact/merci/"  # page de remerciement des formulaires (outils/post/z_formulaires.py, MERCI)
TABLE_MERCI = re.compile(r"^const MERCI = \[\n(.*?)^\];", re.S | re.M)
LIGNE_MERCI = re.compile(r"    '([a-z]{2})' => '([^']*)',")


def _table_merci(php, langues):
    """php dont la table MERCI ne garde que les langues données (ordre de la source)."""
    m = TABLE_MERCI.search(php)
    if not m:
        raise ValueError("envoi.php : la table MERCI est introuvable")
    gardees = []
    for ligne in m.group(1).rstrip("\n").split("\n"):
        champs = LIGNE_MERCI.fullmatch(ligne)
        if not champs:
            raise ValueError(f"envoi.php : ligne illisible dans la table MERCI : {ligne!r}")
        langue, adresse = champs.groups()
        if adresse != "/" + route(PAGE_MERCI, langue):
            raise ValueError(f"envoi.php : MERCI[{langue!r}] vaut {adresse!r}, routes.json donne /{route(PAGE_MERCI, langue)}")
        if langue in langues:
            gardees.append(ligne)
    return php[:m.start(1)] + "\n".join(gardees) + "\n" + php[m.end(1):]


def rendre(config, langues=("fr",)):
    """Texte de envoi.php réglé par la configuration (clés « destinataire », obligatoire, et « expediteur », vide permis).
    langues : langues dont la page de remerciement est construite ; le français en fait toujours partie."""
    langues = tuple(langues)
    if "fr" not in langues:
        raise ValueError("envoi.php : le français doit figurer dans les langues (c'est la page de repli)")
    if any(l not in LANGUES for l in langues):
        raise ValueError(f"envoi.php : langue inconnue dans {langues!r}")
    reglages = {"destinataire": config.get("destinataire") or "", "expediteur": config.get("expediteur") or ""}
    if not ADRESSE.fullmatch(reglages["destinataire"]):
        raise ValueError(f"destinataire invalide dans src/data/config.json : {reglages['destinataire']!r}")
    if reglages["expediteur"] and not ADRESSE.fullmatch(reglages["expediteur"]):
        raise ValueError(f"expediteur invalide dans src/data/config.json : {reglages['expediteur']!r}")
    php = _table_merci(SOURCE.read_text(encoding="utf-8"), langues)
    for cle, valeur in reglages.items():
        marque = "'{{" + cle + "}}'"
        if php.count(marque) != 1:
            raise ValueError(f"envoi.php : la marque {marque} doit figurer une fois")
        php = php.replace(marque, "'" + valeur + "'")
    return php


def ecrire(cible, config, langues=("fr",)):
    Path(cible).write_text(rendre(config, langues), encoding="utf-8")
