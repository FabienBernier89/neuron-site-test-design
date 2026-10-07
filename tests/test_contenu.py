"""Tous les textes viennent mot pour mot du site Neur.on publié (spec § 2, § 9 tests 9 et 10)."""
import html as H
import re
import subprocess
import sys
import unittest
from html.parser import HTMLParser
from pathlib import Path

ICI = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ICI))
import build  # noqa: E402


def norm(s):
    s = H.unescape(s).replace(" ", " ").replace(" ", " ").replace("’", "'")
    return re.sub(r"\s+", " ", s).strip()


def sans_balises(t, sep):
    t = re.sub(r"<(script|style)\b.*?</\1>", " ", t, flags=re.S)
    return norm(re.sub(r"<[^>]+>", sep, t))


def deux_variantes(t):
    return sans_balises(t, " ") + "\n" + sans_balises(t, "")


class Textes(HTMLParser):
    """Textes de <main>. data-libre, script et style sont ignorés, data-ui est classé à part."""
    VIDES = {"area", "base", "br", "col", "embed", "hr", "img", "input", "link", "meta", "source", "track", "wbr"}

    def __init__(self):
        super().__init__()
        self.pile, self.main, self.textes, self.ui, self.titres = [], False, [], [], []

    def handle_starttag(self, tag, attrs):
        if tag in self.VIDES:
            return
        a = dict(attrs)
        parent = self.pile[-1][1] if self.pile else None
        etat = parent or ("ui" if "data-ui" in a else "libre" if ("data-libre" in a or tag in ("script", "style")) else None)
        self.pile.append([tag, etat, tag in ("h1", "h2"), ""])
        if tag == "main":
            self.main = True

    def handle_endtag(self, tag):
        if tag in self.VIDES:
            return
        while self.pile:
            t, _etat, titre, texte = self.pile.pop()
            if titre:
                self.titres.append(norm(texte))
            if t == tag:
                break
        if tag == "main":
            self.main = False

    def handle_data(self, d):
        for el in self.pile:
            if el[2]:
                el[3] += d
        if not self.main or not self.pile:
            return
        t = norm(d)
        if len(t) < 3 or not re.search(r"[A-Za-zÀ-ÿ0-9]", t) or self.pile[-1][1] == "libre":
            return
        (self.ui if self.pile[-1][1] == "ui" else self.textes).append(t)


def corpus_fr():
    m = [deux_variantes(f.read_text(encoding="utf-8")) for f in (build.NEURON / "docs/fr").rglob("*.html")]
    m += [deux_variantes(f.read_text(encoding="utf-8")) for f in (build.NEURON / "src/data").glob("*.json")]
    return "\n".join(m)


def corpus_ui():
    m = [norm((build.NEURON / "assets/corrext-demo.js").read_text(encoding="utf-8")),
         norm((build.NEURON / "src/generators.py").read_text(encoding="utf-8"))]
    m += [deux_variantes(f.read_text(encoding="utf-8")) for f in (build.NEURON / "src/pages").rglob("*.html")]
    m += [deux_variantes(f.read_text(encoding="utf-8")) for f in (build.NEURON / "src/data").glob("*.json")]
    # Maquettes publiées (vignettes générées) : reproductions d'interface déjà en ligne
    m += [deux_variantes(f.read_text(encoding="utf-8")) for f in (build.NEURON / "docs/fr").rglob("*.html")]
    return "\n".join(m)


class TestContenu(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        subprocess.run([sys.executable, str(ICI / "build.py")], check=True, cwd=ICI)
        cls.fr, cls.ui = corpus_fr(), corpus_ui()
        cls.lus, cls.sources = {}, {}
        for p in build.PAGES:
            x = Textes()
            x.feed((build.DOCS / p / "index.html").read_text(encoding="utf-8"))
            cls.lus[p] = x
            cls.sources[p] = deux_variantes((build.NEURON / "docs/fr" / p / "index.html").read_text(encoding="utf-8"))

    def test_textes_repris_mot_pour_mot(self):
        for p, x in self.lus.items():
            for t in x.textes:
                self.assertTrue(t in self.sources[p] or t in self.fr,
                                f"{p or 'accueil'} : texte absent du site actuel : {t[:100]}")

    def test_interface_reprise_de_l_application(self):
        for p, x in self.lus.items():
            for t in x.ui:
                self.assertTrue(t in self.ui, f"{p or 'accueil'} : libellé d'interface inconnu : {t[:100]}")

    def test_titres_de_la_page_source(self):
        for p, x in self.lus.items():
            for t in x.titres:
                self.assertTrue(t in self.sources[p], f"{p or 'accueil'} : titre absent de la page source : {t}")


if __name__ == "__main__":
    unittest.main()
