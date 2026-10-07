/* Simulations de l'interface Corrext : scènes horodatées, lecture à la visibilité, pause accessible.
   Aucun texte affiché n'est écrit ici : les textes viennent du HTML de la page ou de window.SIM_EX. */
(function () {
  "use strict";
  var reduit = window.matchMedia && window.matchMedia("(prefers-reduced-motion: reduce)").matches;
  var EX = window.SIM_EX || {};
  var SCENES = {};

  /* Mise à l'échelle des scènes : dessinées à leur taille de référence, réduites dans les colonnes étroites */
  function echelonner() {
    [].forEach.call(document.querySelectorAll("[data-ech]"), function (b) {
      var t = b.getAttribute("data-ech").split("x"), w = +t[0], h = +t[1];
      var k = Math.min(1, b.clientWidth / w);
      b.firstElementChild.style.setProperty("--k", k);
      b.style.height = (h * k) + "px";
    });
  }
  echelonner();
  window.addEventListener("resize", echelonner);

  /* Onglets d'interface (tableau de bord du hub) : délégation, car la scène est recréée à chaque boucle */
  document.addEventListener("click", function (e) {
    var onglet = e.target.closest && e.target.closest("[data-sim] [role=tab]");
    if (!onglet) return;
    [].forEach.call(onglet.parentNode.querySelectorAll("[role=tab]"), function (o) {
      var actif = o === onglet, pan = document.getElementById(o.getAttribute("aria-controls"));
      o.setAttribute("aria-selected", String(actif));
      o.classList.toggle("on", actif);
      if (pan) pan.hidden = !actif;
    });
  });

  function Lecteur(racine) {
    var self = this;
    this.r = racine;
    this.scene = racine.querySelector("[data-scene]");
    this.modele = this.scene.innerHTML;
    this.visible = false; this.pause = false; this.survol = false; this.arret = false;
    var bouton = racine.querySelector(".sim-pause");
    if (bouton) bouton.addEventListener("click", function () {
      self.pause = !self.pause;
      bouton.setAttribute("aria-pressed", String(self.pause));
    });
    racine.addEventListener("mouseenter", function () { self.survol = true; });
    racine.addEventListener("mouseleave", function () { self.survol = false; });
    /* Sur la démo interactive, une action réelle du visiteur arrête la visite guidée */
    if (racine.getAttribute("data-sim") === "visite") {
      ["pointerdown", "keydown"].forEach(function (type) {
        racine.addEventListener(type, function (e) {
          if (e.isTrusted && !e.target.closest(".sim-pause")) { self.arret = true; if (self.cur()) self.cur().style.opacity = 0; }
        });
      });
    }
  }
  Lecteur.prototype.cur = function () { return this.r.querySelector(".sim-cur"); };
  Lecteur.prototype.actif = function () { return this.visible && !this.pause && !this.survol && !this.arret; };
  Lecteur.prototype.q = function (sel) { return sel ? this.scene.querySelector(sel) : this.scene; };
  Lecteur.prototype.attendre = function (ms) {
    var self = this;
    if (reduit) return Promise.resolve();
    return new Promise(function (fin) {
      var reste = ms, avant = performance.now();
      function tic(t) {
        if (self.arret) return;
        if (self.actif()) reste -= t - avant;
        avant = t;
        if (reste <= 0) fin(); else requestAnimationFrame(tic);
      }
      requestAnimationFrame(tic);
    });
  };
  Lecteur.prototype.taper = function (sel, texte, cps) {
    var el = this.q(sel), self = this, i = 0, pas = Math.max(1, Math.round(texte.length / 120));
    if (reduit) { el.textContent = texte; return Promise.resolve(); }
    el.textContent = "";
    function suite() {
      if (i >= texte.length) return Promise.resolve();
      i = Math.min(texte.length, i + pas);
      el.textContent = texte.slice(0, i);
      return self.attendre(1000 / (cps || 60) * pas).then(suite);
    }
    return suite();
  };
  Lecteur.prototype.poser = function (sel, texte) { this.q(sel).textContent = texte; return Promise.resolve(); };
  Lecteur.prototype.classe = function (sel, cls, oui) {
    [].forEach.call(this.scene.querySelectorAll(sel), function (el) { el.classList.toggle(cls, oui); });
    return Promise.resolve();
  };
  Lecteur.prototype.viser = function (sel) {
    var cur = this.cur(), el = this.q(sel);
    if (!cur || !el || reduit) return Promise.resolve();
    var k = parseFloat(getComputedStyle(this.r).getPropertyValue("--k")) || 1;
    var c = el.getBoundingClientRect(), b = cur.offsetParent.getBoundingClientRect();
    cur.style.transform = "translate(" + ((c.left + c.width / 2 - b.left) / k) + "px," + ((c.top + c.height / 2 - b.top) / k) + "px)";
    return this.attendre(750);
  };
  Lecteur.prototype.cliquer = function (sel, reel) {
    var self = this, cur = this.cur();
    return this.viser(sel).then(function () {
      var el = self.q(sel);
      if (!el) return;
      if (cur && !reduit) { cur.classList.remove("clic"); void cur.offsetWidth; cur.classList.add("clic"); }
      if (reel) el.click();
      return self.attendre(300);
    });
  };
  Lecteur.prototype.choisir = function (sel, valeur) {
    var self = this;
    return this.viser(sel).then(function () {
      var el = self.q(sel);
      el.value = valeur;
      el.dispatchEvent(new Event("change", { bubbles: true }));
      return self.attendre(300);
    });
  };
  Lecteur.prototype.lancer = function () {
    var self = this, fn = SCENES[this.r.getAttribute("data-sim")];
    if (!fn) return;
    var rejouer = this.r.getAttribute("data-sim") !== "visite";
    (function boucle() {
      if (rejouer) self.scene.innerHTML = self.modele;
      fn(self).then(function () { if (!reduit && !self.arret) return self.attendre(2000).then(boucle); });
    })();
  };

  function suite(etapes) {
    return etapes.reduce(function (p, f) { return p.then(f); }, Promise.resolve());
  }

  /* S1 et S3 : visite guidée de la vraie démo Corrext (#cx), contrôles réels.
     Premier extrait : alternatives, puis moteur tiers (Highly sensitive coupé, avis affiché), retour à LexMachina. */
  SCENES.visite = function (l) {
    return suite(["co", "lb", "ldip"].map(function (cle, n) {
      return function () {
        var etapes = [
          function () { return l.cliquer('#cxEx [data-ex="' + cle + '"]', true); },
          function () { return l.attendre(4800); },
          function () { return l.cliquer("#cxSpark", true); },
          function () { return l.attendre(2800); },
          function () { return l.cliquer("#cxDn", true); },
          function () { return l.attendre(2400); },
          function () { return l.cliquer("#cxAltX", true); }
        ];
        if (n === 0) {
          etapes = etapes.concat([
            function () { return l.cliquer("#cxSwitch", true); },
            function () { return l.attendre(900); },
            function () { return l.choisir("#cxEng", "DeepL Pro"); },
            function () { return l.attendre(5200); },
            function () { return l.choisir("#cxEng", "LexMachina"); },
            function () { return l.attendre(1800); },
            function () { return l.cliquer("#cxSwitch", true); }
          ]);
        }
        if (EX[cle].lookup) {
          etapes = etapes.concat([
            function () { return l.cliquer("#cxLookupBtn", true); },
            function () { return l.attendre(3600); },
            function () { return l.cliquer("#cxLkClose", true); }
          ]);
        }
        etapes.push(function () { return l.attendre(900); });
        return suite(etapes);
      };
    }));
  };

  /* S2 : tableau de bord du hub, onglets parcourus */
  SCENES.tableau = function (l) {
    var onglets = [].map.call(l.scene.querySelectorAll("[role=tab]"), function (o) { return "#" + o.id; });
    return suite(onglets.concat(onglets[0]).map(function (sel) {
      return function () { return l.cliquer(sel, true).then(function () { return l.attendre(3400); }); };
    }));
  };

  /* S3a : coller un extrait, la sortie LexMachina s'écrit */
  SCENES.traduire = function (l) {
    return suite([
      function () { return l.taper(".mx-src", EX.co.src, 90); },
      function () { return l.attendre(700); },
      function () { return l.taper(".mx-out", EX.co.out.en.main, 110); },
      function () { return l.attendre(2400); }
    ]);
  };

  /* S3b : changer de moteur, chaque sortie attribuée à son moteur */
  SCENES.moteurs = function (l) {
    var d = EX.ldip.out.en;
    function moteur(i) {
      var sel = '.mx-chip[data-i="' + i + '"]', texte = i === 0 ? d.main : d.alt[i - 1].t;
      return function () {
        return suite([
          function () { return l.cliquer(sel, false); },
          function () { return l.classe(".mx-chip", "on", false).then(function () { return l.classe(sel, "on", true); }); },
          function () { return l.taper(".mx-out", texte, 120); },
          function () { return l.attendre(2200); }
        ]);
      };
    }
    return suite([function () { return l.poser(".mx-src", EX.ldip.src); }, moteur(0), moteur(1), moteur(2)]);
  };

  /* S3c : changer la langue cible (anglais, italien) */
  SCENES.langues = function (l) {
    return suite([
      function () { return l.poser(".mx-src", EX.lb.src); },
      function () { return l.taper(".mx-out", EX.lb.out.en.main, 120); },
      function () { return l.attendre(1600); },
      function () { return l.cliquer('.mx-chip[data-l="it"]', false); },
      function () { return l.classe(".mx-chip", "on", false).then(function () { return l.classe('.mx-chip[data-l="it"]', "on", true); }); },
      function () { return l.poser(".mx-lg", l.q('.mx-chip[data-l="it"]').textContent); },
      function () { return l.taper(".mx-out", EX.lb.out.it.main, 120); },
      function () { return l.attendre(2400); }
    ]);
  };

  /* S3d et S5 : Highly sensitive verrouille LexMachina, un moteur tiers ouvre l'avis */
  SCENES.sensible = function (l) {
    return suite([
      function () { return l.attendre(900); },
      function () { return l.cliquer(".mx-chip.hs", false); },
      function () { return l.classe(".mx-chip.hs", "sombre", true); },
      function () { return l.classe(".mx-l li.tiers", "ui-off", true); },
      function () { return l.attendre(1200); },
      function () { return l.viser(".mx-l li.tiers"); },
      function () { return l.attendre(2600); }
    ]);
  };
  SCENES.avis = function (l) {
    return suite([
      function () { return l.attendre(800); },
      function () { return l.cliquer(".mx-l li:nth-child(2)", false); },
      function () { return l.classe(".mx-l li", "on", false).then(function () { return l.classe(".mx-l li:nth-child(2)", "on", true); }); },
      function () { return l.classe(".mx-avis", "on", true); },
      function () { return l.attendre(3200); },
      function () { return l.classe(".mx-avis", "on", false); },
      function () { return l.cliquer(".mx-chip.hs", false); },
      function () { return l.classe(".mx-chip.hs", "sombre", true); },
      function () { return l.classe(".mx-l li", "on", false).then(function () { return l.classe(".mx-l li.suisse", "on", true); }); },
      function () { return l.classe(".mx-l li.tiers", "ui-off", true); },
      function () { return l.attendre(3000); }
    ]);
  };

  /* S4 : la comparaison « quatre caractères » s'écrit, puis les écarts se surlignent */
  SCENES.quatre = function (l) {
    var cartes = [].slice.call(l.scene.querySelectorAll(".q4-out"));
    var textes = cartes.map(function (c) { return c.innerHTML; });
    cartes.forEach(function (c) { c.innerHTML = ""; });
    return suite(cartes.map(function (c, i) {
      return function () {
        var brut = textes[i].replace(/<[^>]+>/g, "");
        return l.taper("[data-q4='" + i + "']", brut, 140).then(function () { c.innerHTML = textes[i]; });
      };
    }).concat([
      function () { return l.attendre(500); },
      function () { return l.classe("mark", "vu", true); },
      function () { return l.attendre(4200); }
    ]));
  };

  var io = "IntersectionObserver" in window ? new IntersectionObserver(function (es) {
    es.forEach(function (e) { e.target.__lecteur.visible = e.isIntersecting; });
  }, { threshold: 0.4 }) : null;
  [].forEach.call(document.querySelectorAll("[data-sim]"), function (r) {
    var l = new Lecteur(r);
    r.__lecteur = l;
    if (io) io.observe(r); else l.visible = true;
    l.lancer();
  });
})();
