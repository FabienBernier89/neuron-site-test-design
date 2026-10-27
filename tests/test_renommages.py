"""outils/post/renommages.py : une correction s'applique une seule fois, même quand le nouveau texte contient l'ancien
(« est exigé » devient « est exigée », décision de Fabien du 2026-10-27 sur les extraits du registre)."""
import unittest
from unittest import mock

from outils.post import renommages


class TestRenommages(unittest.TestCase):
    def traiter(self, html, paires):
        with mock.patch.object(renommages, "_paires", lambda page: paires):
            return renommages.traiter(html, "page/")

    def test_nouveau_texte_qui_contient_l_ancien(self):
        self.assertEqual(self.traiter("<h2>où la traduction <em>est exigé</em></h2>", [("est exigé", "est exigée")]),
                         "<h2>où la traduction <em>est exigée</em></h2>")

    def test_forme_echappee_remplacee(self):
        self.assertEqual(self.traiter("<p>Qu&#x27;est-ce</p><p>l'extrait</p>",
                                      [("l'extrait", "la traduction")]), "<p>Qu&#x27;est-ce</p><p>la traduction</p>")
        self.assertEqual(self.traiter("<p>A &amp; B</p>", [("A & B", "A & C")]), "<p>A &amp; C</p>")


if __name__ == "__main__":
    unittest.main()
