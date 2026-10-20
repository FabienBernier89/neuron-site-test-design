"""Écran « le texte qui se corrige » de la page LexMachina, partagé avec les pages métier (onglet du moteur)."""
import html as _H
import sys
from pathlib import Path

from commun import A
sys.path.insert(0, str(Path(__file__).resolve().parents[2]))
from outils.contenus import texte  # noqa: E402


def k(cle):
    return _H.escape(texte(f"lexmachina.{cle}"), quote=False)


# Comparaison (idée A retenue par Fabien le 2026-10-16, « le texte qui se corrige ») : la sortie de DeepL s'écrit, ses
# deux termes génériques se signalent, puis LexMachina retraduit et les termes officiels se surlignent. Deux sorties
# RÉELLES du même texte (celui de l'axe LexMachina de l'accueil) ; seuls les écarts réels sont marqués.
ECARTS = (("retenue à la source", "impôt anticipé"), ("établissement soumis à surveillance", "assujetti"))


def ecran_corrige():
    gen = A.marquer(texte("lexmachina.compare.deepl").replace(" %", "\u00a0%"), [g for g, _ in ECARTS], "gen")  # « 35 % » insécable
    lm = A.marquer(texte("accueil.axes.lexmachina.demo.out"), [o for _, o in ECARTS])
    puces = "".join(f'<span>{k("compare.chip." + c)}</span>' for c in ("impot", "assujetti"))
    # Moteur généraliste anonymisé : « IA généraliste », aucun moteur tiers nommé dans cette comparaison (Fabien, 2026-10-16)
    ecran = A.ecran_corrige(_H.escape(texte("accueil.axes.lexmachina.demo.src"), quote=False), gen, lm, puces, k("compare.moteur"),
                            detecte=_H.escape(texte("accueil.axes.lexmachina.demo.langue"), quote=False))
    assert "DeepL" not in ecran and "Azure" not in ecran
    return ecran
