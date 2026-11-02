"""Le .htaccess de production servi par un vrai Apache (tâches 10.1 et 10.2) : racine selon Accept-Language avec
Vary, anciennes adresses en 301 vers la page de leur langue, pages intérieures jamais redirigées, y compris sous un
dossier de langue qui a son propre .htaccess (page 404). Apache local (macOS : /usr/sbin/httpd), sans racine ni
réseau : un serveur temporaire sur 127.0.0.1 ; ignoré si Apache ou ses modules manquent."""
import http.client
import os
import shutil
import socket
import subprocess
import sys
import tempfile
import time
import unittest
from pathlib import Path

ICI = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ICI))
import build  # noqa: E402
import redirections  # noqa: E402

HTTPD = shutil.which("httpd") or "/usr/sbin/httpd"
MODULES = Path("/usr/libexec/apache2")
NECESSAIRES = ("mpm_prefork", "unixd", "authz_core", "dir", "mime", "rewrite", "headers", "log_config")
PRET = Path(HTTPD).is_file() and all((MODULES / f"mod_{m}.so").is_file() for m in NECESSAIRES)
QUATRE = ("fr", "de", "it", "en")


def port_libre():
    with socket.socket() as s:
        s.bind(("127.0.0.1", 0))
        return s.getsockname()[1]


@unittest.skipUnless(PRET, "Apache local ou ses modules absents")
class TestApache(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls._tmp = tempfile.TemporaryDirectory()
        tmp = Path(cls._tmp.name)
        racine = tmp / "site"
        redirs = redirections.lire(build.NEURON, QUATRE)
        (racine).mkdir()
        (racine / ".htaccess").write_text(redirections.htaccess(redirs, QUATRE), encoding="utf-8")
        for chemin in ("fr/", "de/", "it/", "en/", "de/ueber-uns/", "en/about/", "fr/a-propos/"):
            (racine / chemin).mkdir(parents=True, exist_ok=True)
            (racine / chemin / "index.html").write_text("<!doctype html><title>t</title>", encoding="utf-8")
        # comme build.main : le dossier d'une langue a son .htaccess (page 404), sans règle de réécriture
        (racine / "de/.htaccess").write_text("ErrorDocument 404 /de/404.html\n", encoding="utf-8")
        cls.port = port_libre()
        modules = "\n".join(f"LoadModule {m}_module {MODULES}/mod_{m}.so" for m in NECESSAIRES)
        conf = tmp / "httpd.conf"
        conf.write_text(f"""{modules}
ServerRoot "{tmp}"
Listen 127.0.0.1:{cls.port}
ServerName localhost
PidFile "{tmp}/httpd.pid"
ErrorLog "{tmp}/error.log"
DocumentRoot "{racine}"
DirectoryIndex index.html
<Directory "{racine}">
  AllowOverride All
  Require all granted
</Directory>
""", encoding="utf-8")
        # session à part : à l'arrêt, Apache signale tout son groupe de processus, qui ne doit pas être celui des tests
        cls.serveur = subprocess.Popen([HTTPD, "-f", str(conf), "-DFOREGROUND"], stdout=subprocess.DEVNULL,
                                       stderr=subprocess.PIPE, start_new_session=True)
        for _ in range(100):
            try:
                socket.create_connection(("127.0.0.1", cls.port), timeout=0.2).close()
                break
            except OSError:
                if cls.serveur.poll() is not None:
                    break
                time.sleep(0.1)
        else:
            cls.tearDownClass()
            raise unittest.SkipTest("Apache local n'a pas démarré")
        if cls.serveur.poll() is not None:
            erreur = cls.serveur.stderr.read().decode("utf-8", "replace")[-300:]
            cls._tmp.cleanup()
            raise unittest.SkipTest(f"Apache local n'a pas démarré : {erreur}")

    @classmethod
    def tearDownClass(cls):
        if getattr(cls, "serveur", None) and cls.serveur.poll() is None:
            cls.serveur.terminate()
            cls.serveur.wait(10)
        cls._tmp.cleanup()

    def get(self, chemin, langue=None):
        """(statut, Location, Vary) d'une requête sur l'hôte canonique, HTTPS déjà terminé par un proxy."""
        c = http.client.HTTPConnection("127.0.0.1", self.port, timeout=10)
        entetes = {"Host": "neur-on.ai", "X-Forwarded-Proto": "https"}
        if langue is not None:
            entetes["Accept-Language"] = langue
        c.request("GET", chemin, headers=entetes)
        r = c.getresponse()
        r.read()
        c.close()
        return r.status, r.getheader("Location"), r.getheader("Vary") or ""

    def test_racine_selon_la_langue_du_navigateur(self):
        for langue, cible in (("de-CH,de;q=0.9,en;q=0.8", "de"), ("gsw-CH", "de"), ("fr-CH, fr;q=0.9", "fr"),
                              ("it-CH", "it"), ("en-GB,en;q=0.9", "en"), ("es-ES,es;q=0.9", "en"), (None, "en")):
            with self.subTest(langue=langue):
                statut, location, vary = self.get("/", langue)
                self.assertEqual((statut, location), (302, f"https://neur-on.ai/{cible}/"))
                self.assertIn("Accept-Language", vary)

    def test_pages_interieures_jamais_redirigees(self):
        for chemin in ("/de/", "/fr/a-propos/", "/de/ueber-uns/"):
            with self.subTest(chemin=chemin):
                statut, location, vary = self.get(chemin, "en-GB")
                self.assertEqual((statut, location), (200, None))
                self.assertNotIn("Accept-Language", vary)

    def test_anciennes_adresses_vers_la_page_de_leur_langue(self):
        for chemin, cible in (("/de/about/", "https://neur-on.ai/de/ueber-uns/"), ("/de/about", "https://neur-on.ai/de/ueber-uns/"),
                              ("/about/", "https://neur-on.ai/en/about/"), ("/fr/about/", "https://neur-on.ai/fr/a-propos/"),
                              ("/de/category/unkategorisiert/", "https://neur-on.ai/de/ressourcen/blog/"),
                              ("/fr/terms-of-use/", "https://neur-on.ai/fr/mentions-legales/#conditions-d-utilisation")):
            with self.subTest(chemin=chemin):
                statut, location, vary = self.get(chemin, "fr-CH")
                self.assertEqual((statut, location), (301, cible))
                self.assertNotIn("Accept-Language", vary)


if __name__ == "__main__":
    unittest.main()
