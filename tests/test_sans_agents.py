"""Corrext n'a pas d'agents IA (Fabien, 2026-10-16) : aucune page ne présente d'agents comme une fonctionnalité."""
import re
import sys
import unittest
from pathlib import Path

ICI = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ICI))
from tests import support  # noqa: E402

INTERDIT = re.compile(r"(?i)agents? (IA|d'IA|juridiques?|spécialisés?)|agentique|agentic|AI agents?")


class TestSansAgentsIA(unittest.TestCase):
    def test_aucune_page_ne_parle_d_agents_ia(self):
        sortie = support.site_complet(apercu=True)
        for f in sortie.rglob("*.html"):
            c = str(f.relative_to(sortie))
            self.assertIsNone(INTERDIT.search(f.read_text(encoding="utf-8")), c)


if __name__ == "__main__":
    unittest.main()
