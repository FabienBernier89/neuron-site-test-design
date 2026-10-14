"""Script d'envoi des formulaires (envoi.php, à la racine du dépôt) : le build le copie à la racine du site, avec le
destinataire et l'expéditeur de src/data/config.json écrits dans ses constantes. Une adresse mal formée arrête le
build : elle ne doit jamais finir dans du code PHP."""
import re
from pathlib import Path

SOURCE = Path(__file__).resolve().parents[1] / "envoi.php"
ADRESSE = re.compile(r"[A-Za-z0-9._%+-]+@[A-Za-z0-9-]+(?:\.[A-Za-z0-9-]+)+")


def rendre(config):
    """Texte de envoi.php réglé par la configuration (clés « destinataire », obligatoire, et « expediteur », vide permis)."""
    reglages = {"destinataire": config.get("destinataire") or "", "expediteur": config.get("expediteur") or ""}
    if not ADRESSE.fullmatch(reglages["destinataire"]):
        raise ValueError(f"destinataire invalide dans src/data/config.json : {reglages['destinataire']!r}")
    if reglages["expediteur"] and not ADRESSE.fullmatch(reglages["expediteur"]):
        raise ValueError(f"expediteur invalide dans src/data/config.json : {reglages['expediteur']!r}")
    php = SOURCE.read_text(encoding="utf-8")
    for cle, valeur in reglages.items():
        marque = "'{{" + cle + "}}'"
        if php.count(marque) != 1:
            raise ValueError(f"envoi.php : la marque {marque} doit figurer une fois")
        php = php.replace(marque, "'" + valeur + "'")
    return php


def ecrire(cible, config):
    Path(cible).write_text(rendre(config), encoding="utf-8")
