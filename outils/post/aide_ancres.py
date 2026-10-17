"""Centre d'aide : une ancre par question (retour de Fabien du 2026-10-17, refonte de l'accueil du centre d'aide).

Chaque <details> d'une page de rubrique (aide/<rubrique>/) reçoit un id tiré de sa question : la recherche de l'accueil
du centre d'aide et la liste « Pour bien démarrer » y renvoient, et assets/global/aide.js ouvre la question visée.
"""
import html as H
import re
import unicodedata


def ancre(question):
    """Identifiant stable d'une question : « q- » suivi de ses mots sans accents."""
    s = unicodedata.normalize("NFD", H.unescape(re.sub(r"<[^>]+>", "", question)).lower())
    s = re.sub(r"[^a-z0-9]+", "-", "".join(c for c in s if unicodedata.category(c) != "Mn")).strip("-")
    return "q-" + s[:64].rstrip("-")


def traiter(html, page):
    if not page.startswith("aide/") or page == "aide/":
        return html
    vus = set()

    def sub(m):
        i = ancre(m.group(2))
        while i in vus:
            i += "-2"
        vus.add(i)
        return f'<details id="{i}">{m.group(1)}{m.group(2)}'
    return re.sub(r"<details>(<summary>)(.*?)(?=</summary>)", sub, html, flags=re.S)
