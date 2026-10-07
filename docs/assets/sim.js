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

  /* Pastille des onglets : posée sous l'onglet actif, puis glisse (translation et échelle horizontale) */
  function pilule(tl) {
    var on = tl.querySelector("span.on"), p = tl.querySelector(".cr-tl-pill");
    if (!on || !p) return;
    p.style.transform = "translateX(" + on.offsetLeft + "px) scaleX(" + (on.offsetWidth / 100) + ")";
  }
  /* Compteur de caractères des panneaux déjà remplis (le HTML porte la valeur initiale de l'application) */
  function compter(racine) {
    [].forEach.call(racine.querySelectorAll(".cr-in.rempli"), function (p) {
      var t = p.querySelector(".cr-txt"), c = p.querySelector(".cr-cnt");
      if (t && c) c.textContent = t.textContent.length + c.textContent.slice(c.textContent.indexOf(" /"));
    });
  }
  function poserPilules(racine) {
    [].forEach.call(racine.querySelectorAll(".cr-tl"), function (tl) {
      tl.classList.remove("pret");
      pilule(tl);
      void tl.offsetWidth;
      tl.classList.add("pret");
    });
  }

  function Lecteur(racine) {
    var self = this;
    this.r = racine;
    this.scene = racine.querySelector("[data-scene]");
    this.modele = this.scene.innerHTML;
    this.visible = false; this.pause = false; this.survol = false;
    var bouton = racine.querySelector(".sim-pause");
    if (bouton) bouton.addEventListener("click", function () {
      self.pause = !self.pause;
      bouton.setAttribute("aria-pressed", String(self.pause));
    });
    racine.addEventListener("mouseenter", function () { self.survol = true; });
    racine.addEventListener("mouseleave", function () { self.survol = false; });
  }
  Lecteur.prototype.actif = function () { return this.visible && !this.pause && !this.survol; };
  Lecteur.prototype.q = function (sel) { return sel ? this.scene.querySelector(sel) : this.scene; };
  Lecteur.prototype.qa = function (sel) { return [].slice.call(this.scene.querySelectorAll(sel)); };
  Lecteur.prototype.attendre = function (ms) {
    var self = this;
    if (reduit) return Promise.resolve();
    return new Promise(function (fin) {
      var reste = ms, avant = performance.now();
      function tic(t) {
        if (self.actif()) reste -= t - avant;
        avant = t;
        if (reste <= 0) fin(); else requestAnimationFrame(tic);
      }
      requestAnimationFrame(tic);
    });
  };
  Lecteur.prototype.taper = function (sel, texte, cps, apres) {
    var el = this.q(sel), self = this, i = 0, pas = Math.max(1, Math.round(texte.length / 120));
    if (reduit) { el.textContent = texte; if (apres) apres(texte.length); return Promise.resolve(); }
    el.textContent = "";
    function suite() {
      if (i >= texte.length) return Promise.resolve();
      i = Math.min(texte.length, i + pas);
      el.textContent = texte.slice(0, i);
      if (apres) apres(i);
      /* rythme humain : chaque pas varie de 70 à 130 % */
      return self.attendre(1000 / (cps || 60) * pas * (0.7 + Math.random() * 0.6)).then(suite);
    }
    return suite();
  };
  /* Appui sur un contrôle : léger enfoncement */
  Lecteur.prototype.appui = function (sel) {
    var self = this, el = typeof sel === "string" ? this.q(sel) : sel;
    el.classList.add("press");
    return this.attendre(170).then(function () { el.classList.remove("press"); return self.attendre(140); });
  };
  /* Révèle un texte mot par mot : fondu et léger glissement, 22 ms de décalage par mot (balises internes conservées) */
  Lecteur.prototype.mots = function (sel, texte, html) {
    var el = typeof sel === "string" ? this.q(sel) : sel, n = 0;
    el.classList.remove("vu", "sort");
    if (html) el.innerHTML = texte; else el.textContent = texte;
    (function decouper(noeud) {
      [].slice.call(noeud.childNodes).forEach(function (c) {
        if (c.nodeType === 1) { decouper(c); return; }
        if (c.nodeType !== 3) return;
        var frag = document.createDocumentFragment();
        c.textContent.split(/(\s+)/).forEach(function (m) {
          if (!m) return;
          if (/^\s+$/.test(m)) { frag.appendChild(document.createTextNode(m)); return; }
          var s = document.createElement("span");
          s.className = "w";
          s.style.setProperty("--i", n++);
          s.textContent = m;
          frag.appendChild(s);
        });
        noeud.replaceChild(frag, c);
      });
    })(el);
    void el.offsetWidth;
    el.classList.add("vu");
    return this.attendre(n * 22 + 450);
  };
  /* Passe à l'onglet i : pastille et vue correspondante */
  Lecteur.prototype.onglet = function (i) {
    var tl = this.q(".cr-tl"), self = this;
    tl.querySelectorAll("span").forEach(function (s) { s.classList.toggle("on", s.getAttribute("data-t") === String(i)); });
    pilule(tl);
    this.qa(".cr-vue,.cr-panel").forEach(function (v) { v.classList.toggle("on", v.getAttribute("data-t") === String(i)); });
    return self.attendre(650);
  };
  /* Ouvre un sélecteur, choisit une valeur, referme */
  Lecteur.prototype.selection = function (sel, valeur) {
    var self = this, s = this.q(sel);
    return this.appui(s).then(function () {
      s.classList.add("ouvert");
      return self.attendre(650);
    }).then(function () {
      [].forEach.call(s.querySelectorAll(".cr-menu span"), function (x) { x.classList.toggle("on", x.getAttribute("data-v") === valeur); });
      return self.attendre(450);
    }).then(function () {
      s.classList.remove("ouvert");
      s.querySelector(".cr-v").textContent = valeur;
      return self.attendre(200);
    });
  };
  /* Nouvelle traduction : la sortie s'efface, squelette, puis mots */
  Lecteur.prototype.retraduire = function (texte, racine) {
    var self = this, out = this.q(".cr-out"), cr = racine || this.q(".cr");
    out.classList.add("sort");
    return this.attendre(240).then(function () {
      out.classList.remove("vu", "sort");
      out.textContent = "";
      for (var i = 0; i < 3; i++) { var s = document.createElement("span"); s.className = "cr-sk"; out.appendChild(s); }
      cr.classList.add("traduit");
      return self.attendre(900);
    }).then(function () {
      cr.classList.remove("traduit");
      return self.mots(".cr-out", texte);
    });
  };
  Lecteur.prototype.lancer = function () {
    var self = this, fn = SCENES[this.r.getAttribute("data-sim")];
    if (!fn) return;
    var tenue = +(this.r.getAttribute("data-tenue") || 2000);
    (function boucle() {
      self.scene.innerHTML = self.modele;
      poserPilules(self.scene);
      compter(self.scene);
      fn(self).then(function () { if (!reduit) return self.attendre(tenue).then(boucle); });
    })();
  };

  function suite(etapes) {
    return etapes.reduce(function (p, f) { return p.then(f); }, Promise.resolve());
  }
  function fixe(ms) { return function (l) { return l.attendre(ms); }; }
  function extrait(l) {
    var cles = ["co", "lb", "ldip"], k = cles[(l.n || 0) % cles.length];
    l.n = (l.n || 0) + 1;
    return k;
  }
  function moteurTiers(d) {
    return d.out.en.alt.filter(function (x) { return x.e === "DeepL Pro"; })[0] || d.out.en.alt[0];
  }

  function remplirLookup(l, lk) {
    l.q(".lk-q").textContent = lk.q;
    l.q(".lk-l1").textContent = lk.l1;
    l.q(".lk-l2").textContent = lk.l2;
    l.q(".lk-c").textContent = lk.count;
    var r = l.q(".lk-r");
    r.textContent = "";
    lk.rows.forEach(function (ligne, i) {
      var bloc = document.createElement("div"), a = document.createElement("p"), b = document.createElement("p"), s = document.createElement("small");
      var j = ligne.a.indexOf(lk.q);
      bloc.style.setProperty("--i", i);
      if (j >= 0) {
        var m = document.createElement("mark");
        m.textContent = lk.q;
        a.appendChild(document.createTextNode(ligne.a.slice(0, j)));
        a.appendChild(m);
        a.appendChild(document.createTextNode(ligne.a.slice(j + lk.q.length)));
      } else {
        a.textContent = ligne.a;
      }
      b.textContent = ligne.b;
      s.textContent = ligne.src;
      bloc.appendChild(a); bloc.appendChild(b); bloc.appendChild(s);
      r.appendChild(bloc);
    });
  }
  function surligner(l, d, terme) {
    var el = l.q(".cr-txt"), i = d.src.indexOf(terme), m = document.createElement("mark");
    m.textContent = terme;
    el.textContent = "";
    el.appendChild(document.createTextNode(d.src.slice(0, i)));
    el.appendChild(m);
    el.appendChild(document.createTextNode(d.src.slice(i + terme.length)));
    void m.offsetWidth;
    m.classList.add("on");
  }

  /* Étapes communes de « Text translation » : frappe, traduction à la saisie, alternatives */
  function etapesTraduction(l, d, cr, nbAlts) {
    var entree = l.q(".cr-in"), cnt = l.q(".cr-cnt");
    function alternative(n) {
      return function () {
        var alt = l.q(".cr-alt"), e = l.q(".cr-alt-e");
        alt.classList.add("sort");
        e.classList.remove("on");
        return l.attendre(230).then(function () {
          l.q(".cr-pgn").textContent = (n + 1) + " / " + d.out.en.alt.length;
          e.textContent = d.out.en.alt[n].e;
          e.classList.add("on");
          return l.mots(".cr-alt", d.out.en.alt[n].t);
        });
      };
    }
    var etapes = [
      fixe(800),
      function () {
        entree.classList.add("rempli", "tape");
        return l.taper(".cr-txt", d.src, 58, function (i) {
          cnt.textContent = i + " / 10000";
          if (i > 22) l.q(".cr-src").classList.add("detecte");
        });
      },
      /* traduction à la saisie, sans bouton */
      function () { entree.classList.remove("tape"); cr.classList.add("traduit"); return l.attendre(1100); },
      function () { cr.classList.remove("traduit"); return l.mots(".cr-out", d.out.en.main); },
      fixe(1500),
      function () { return l.appui(".cr-spark"); },
      function () { cr.classList.add("alts"); return l.attendre(1100); },
      alternative(0),
      fixe(2300)
    ];
    if (nbAlts > 1) etapes = etapes.concat([function () { return l.appui(".cr-dn"); }, alternative(1), fixe(2300)]);
    return etapes.concat([function () { return l.appui(".cr-ax"); }, function () { cr.classList.remove("alts"); return l.attendre(900); }]);
  }

  /* Moteur hébergé à l'étranger : Highly sensitive coupé, avis affiché, puis retour à LexMachina */
  function etapesMoteurTiers(l, d, cr) {
    var tiers = moteurTiers(d);
    return [
      function () { return l.appui(".cr-sw"); },
      function () { l.q(".cr-sw").classList.remove("on"); return l.attendre(700); },
      function () { return l.selection(".cr-eng", tiers.e); },
      function () {
        cr.style.setProperty("--h-avis", (l.q(".cr-notice").offsetHeight + 12) + "px");
        cr.classList.add("avis");
        return l.attendre(400);
      },
      function () { return l.retraduire(tiers.t); },
      fixe(2800),
      function () { return l.selection(".cr-eng", "LexMachina"); },
      function () { cr.classList.remove("avis"); return l.attendre(300); },
      function () { return l.retraduire(d.out.en.main); },
      function () { return l.appui(".cr-sw"); },
      function () { l.q(".cr-sw").classList.add("on"); return l.attendre(1000); }
    ];
  }

  function etapesLookup(l, d, cr) {
    var terme = cr.getAttribute("data-terme-" + l.cle);
    if (!d.lookup || !terme || d.src.indexOf(terme) < 0) return [];
    return [
      function () { surligner(l, d, terme); remplirLookup(l, d.lookup); return l.attendre(750); },
      function () { cr.classList.add("lkb"); return l.attendre(800); },
      function () { return l.appui(".cr-lkb"); },
      function () { cr.classList.add("modal"); return l.attendre(5200); },
      function () { return l.appui(".cr-btn"); },
      function () { cr.classList.remove("modal"); cr.classList.remove("lkb"); return l.attendre(900); }
    ];
  }

  function finir(cr) {
    return [fixe(1000), function (l) { if (!reduit) cr.classList.add("fin"); return l.attendre(480); }];
  }
  function jouer(l, etapes) {
    return suite(etapes.map(function (f) { return function () { return f(l); }; }));
  }

  /* Accueil : écran « Text translation », un extrait différent à chaque boucle */
  SCENES.app = function (l) {
    l.cle = extrait(l);
    var d = EX[l.cle], cr = l.q(".cr");
    return jouer(l, etapesTraduction(l, d, cr, 2).concat(etapesMoteurTiers(l, d, cr), etapesLookup(l, d, cr), finir(cr)));
  };

  /* Page outil : Text translation, puis Rephrasing, File translation et PDF to Word */
  SCENES.outil = function (l) {
    l.cle = "co";
    var d = EX.co, cr = l.q(".cr");
    function depot(t) {
      var vue = l.q('.cr-vue[data-t="' + t + '"]');
      return [
        function () { return l.appui(vue.querySelector(".cr-drop")); },
        function () { vue.classList.add("depose"); return l.attendre(500); },
        function () { vue.classList.add("charge"); return l.attendre(2700); },
        function () { vue.classList.add("fini"); return l.attendre(1800); }
      ];
    }
    var reph = l.q('.cr-vue[data-t="3"]');
    var etapes = etapesTraduction(l, d, cr, 1).concat([
      /* Rephrasing : réglage par défaut, puis style Simplified */
      function () { return l.onglet(3); },
      function () {
        var src = reph.querySelector(".cr-rtxt");
        reph.querySelector(".cr-in").classList.add("rempli");
        src.textContent = d.src;
        reph.querySelector(".cr-rcnt").textContent = d.src.length + " / 5000";
        cr.classList.add("traduit");
        return l.attendre(900);
      },
      function () { cr.classList.remove("traduit"); return l.mots(reph.querySelector(".cr-rout"), d.reph.def, true); },
      fixe(1800),
      function () { var s = reph.querySelector(".cr-set"); return l.appui(s).then(function () { s.classList.add("ouvert"); return l.attendre(700); }); },
      function () { reph.querySelector('.cr-chip[data-s="Simplified"]').classList.add("on"); return l.attendre(700); },
      function () { return l.appui(reph.querySelector(".cr-btn-p")); },
      function () {
        var s = reph.querySelector(".cr-set");
        s.classList.remove("ouvert");
        s.classList.add("regle");
        reph.querySelector(".cr-rout").classList.add("sort");
        return l.attendre(450);
      },
      function () { return l.mots(reph.querySelector(".cr-rout"), d.reph.simp, true); },
      fixe(2600),
      /* File translation puis PDF to Word */
      function () { return l.onglet(1); }
    ]).concat(depot(1), [function () { return l.onglet(2); }], depot(2), finir(cr));
    return jouer(l, etapes);
  };

  /* Boucle « Text translation » : frappe et traduction à la saisie */
  SCENES.traduire = function (l) {
    l.cle = extrait(l);
    var d = EX[l.cle], cr = l.q(".cr"), entree = l.q(".cr-in"), cnt = l.q(".cr-cnt");
    return jouer(l, [
      fixe(600),
      function () {
        entree.classList.add("rempli", "tape");
        return l.taper(".cr-txt", d.src, 62, function (i) {
          cnt.textContent = i + " / 10000";
          if (i > 22) l.q(".cr-src").classList.add("detecte");
        });
      },
      function () { entree.classList.remove("tape"); cr.classList.add("traduit"); return l.attendre(1000); },
      function () { cr.classList.remove("traduit"); return l.mots(".cr-out", d.out.en.main); }
    ].concat(finir(cr)));
  };

  /* Boucle « Moteurs » : Highly sensitive verrouille LexMachina, les moteurs tiers se grisent */
  SCENES.sensible = function (l) {
    var cr = l.q(".cr"), eng = l.q(".cr-eng");
    function tiers(off) { [].forEach.call(eng.querySelectorAll(".cr-menu span"), function (s) { if (s.getAttribute("data-v") !== "LexMachina") s.classList.toggle("off", off); }); }
    return jouer(l, [
      fixe(900),
      function () { return l.appui(".cr-sw"); },
      function () { l.q(".cr-sw").classList.add("on"); tiers(true); return l.attendre(800); },
      function () { return l.appui(eng); },
      function () { eng.classList.add("ouvert"); return l.attendre(2600); },
      function () { eng.classList.remove("ouvert"); return l.attendre(900); },
      function () { return l.appui(".cr-sw"); },
      function () { l.q(".cr-sw").classList.remove("on"); tiers(false); return l.attendre(900); },
      function () { return l.appui(eng); },
      function () { eng.classList.add("ouvert"); return l.attendre(1800); },
      function () { eng.classList.remove("ouvert"); return l.attendre(400); }
    ].concat(finir(cr)));
  };

  /* Boucle « Alternatives » : chaque moteur rend sa traduction */
  SCENES.moteurs = function (l) {
    var d = EX.ldip, cr = l.q(".cr");
    return jouer(l, [
      fixe(900),
      function () { return l.selection(".cr-eng", d.out.en.alt[0].e); },
      function () { return l.retraduire(d.out.en.alt[0].t); },
      fixe(2200),
      function () { return l.selection(".cr-eng", d.out.en.alt[1].e); },
      function () { return l.retraduire(d.out.en.alt[1].t); },
      fixe(2200),
      function () { return l.selection(".cr-eng", "LexMachina"); },
      function () { return l.retraduire(d.out.en.main); },
      fixe(1600)
    ].concat(finir(cr)));
  };

  /* Boucle « Langues » : la langue cible passe de l'anglais à l'italien */
  SCENES.langues = function (l) {
    var d = EX.lb, cr = l.q(".cr"), menu = l.q(".cr-tgtsel");
    var italien = [].filter.call(menu.querySelectorAll(".cr-menu span"), function (s) { return s.getAttribute("data-v") === "Italian"; })[0];
    return jouer(l, [
      fixe(1200),
      function () { return l.selection(".cr-tgtsel", italien.getAttribute("data-v")); },
      function () { return l.retraduire(d.out.it.main); },
      fixe(2600),
      function () { return l.selection(".cr-tgtsel", "English"); },
      function () { return l.retraduire(d.out.en.main); },
      fixe(1600)
    ].concat(finir(cr)));
  };

  /* Sécurité : moteur tiers, avis Attorney-Client, retour en Suisse */
  SCENES.avis = function (l) {
    var d = EX.co, cr = l.q(".cr");
    return jouer(l, [fixe(1000)].concat(etapesMoteurTiers(l, d, cr), finir(cr)));
  };

  /* LexMachina : sortie du moteur, alternative DeepL Pro, puis les écarts se surlignent */
  SCENES.quatre = function (l) {
    var cr = l.q(".cr"), out = l.q(".cr-out"), alt = l.q(".cr-alt"), e = l.q(".cr-alt-e");
    return jouer(l, [
      function () { cr.classList.add("traduit"); return l.attendre(1000); },
      function () { cr.classList.remove("traduit"); return l.mots(out, out.getAttribute("data-html"), true); },
      fixe(900),
      function () { return l.appui(".cr-spark"); },
      function () { cr.classList.add("alts"); return l.attendre(900); },
      function () { e.textContent = e.getAttribute("data-v"); e.classList.add("on"); return l.mots(alt, alt.getAttribute("data-html"), true); },
      fixe(700),
      function () { l.qa("mark").forEach(function (m) { m.classList.add("vu"); }); return l.attendre(4200); }
    ].concat(finir(cr)));
  };

  /* Hub : le tableau de bord parcourt ses onglets */
  SCENES.tableau = function (l) {
    var cr = l.q(".cr"), n = l.qa(".cr-tl span").length, etapes = [fixe(2600)];
    for (var i = 1; i <= n; i++) {
      (function (j) { etapes.push(function () { return l.onglet(j % n); }, fixe(2900)); })(i);
    }
    return jouer(l, etapes.concat(finir(cr)));
  };

  var io = "IntersectionObserver" in window ? new IntersectionObserver(function (es) {
    es.forEach(function (e) { e.target.__lecteur.visible = e.isIntersecting; });
  }, { threshold: 0.4 }) : null;
  /* Pastilles des écrans statiques */
  poserPilules(document);
  compter(document);
  [].forEach.call(document.querySelectorAll("[data-sim]"), function (r) {
    var l = new Lecteur(r);
    r.__lecteur = l;
    if (io) io.observe(r); else l.visible = true;
    l.lancer();
  });
})();
