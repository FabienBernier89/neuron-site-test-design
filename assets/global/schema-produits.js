/* Schéma « qui fait quoi » (lot B) : flux en trois étapes entre Corrext, LexMachina et CHnell, rejoué tant que le
   schéma reste à l'écran (proposition A retenue par Fabien le 2026-10-15).
   1. Corrext envoie le texte au moteur : LexMachina s'éclaire.
   2. La traduction revient : Corrext s'éclaire, la sortie s'affiche.
   3. Le Fast Lookup interroge CHnell : CHnell s'éclaire, le résultat s'affiche.
   L'étape en cours s'allume aussi dans la liste ol.sp-et. Sans script, sans IntersectionObserver ou en mouvement
   réduit, rien n'est posé : le schéma reste dans son état final. Mouvement en transform et opacity. Aucun texte
   affiché n'est écrit ici. */
(function () {
  "use strict";
  var scenes = [].slice.call(document.querySelectorAll(".sp-sc"));
  if (!scenes.length || !("IntersectionObserver" in window) || !Element.prototype.animate) return;
  if (window.matchMedia && window.matchMedia("(prefers-reduced-motion: reduce)").matches) return;
  var COURBE = "cubic-bezier(.22,.8,.24,1)";
  var ETATS = ["sp-e1", "sp-e2", "sp-e3", "sp-e4", "sp-a1", "sp-a2", "sp-a3"];

  function attendre(ms) {
    return new Promise(function (fin) { setTimeout(fin, ms); });
  }

  /* Trajet d'un paquet, en coordonnées de la scène : d'un visuel à l'autre, à mi-hauteur, quand les cartes sont côte à
     côte ; dans l'intervalle vertical quand elles sont empilées */
  function trajet(sc, de, vers) {
    var b = sc.getBoundingClientRect(), a = de.querySelector(".sp-ui").getBoundingClientRect(), c = vers.querySelector(".sp-ui").getBoundingClientRect();
    if (c.right <= a.left + 1 || c.left >= a.right - 1) {
      var y = a.top + a.height / 2 - b.top;
      return c.right <= a.left + 1 ? [a.left - b.left, y, c.right - b.left, y] : [a.right - b.left, y, c.left - b.left, y];
    }
    var x = a.left + a.width / 2 - b.left, n = de.getBoundingClientRect(), m = vers.getBoundingClientRect();
    return m.bottom <= n.top + 1 ? [x, n.top - b.top, x, m.bottom - b.top] : [x, n.bottom - b.top, x, m.top - b.top];
  }

  function position(t, k, echelle) {
    return "translate(" + (t[0] + (t[2] - t[0]) * k) + "px," + (t[1] + (t[3] - t[1]) * k) + "px) scale(" + echelle + ")";
  }

  /* Un paquet traverse la liaison, puis disparaît */
  function paquet(sc, de, vers, classe) {
    var t = trajet(sc, de, vers), p = document.createElement("span");
    p.className = "sp-pk " + classe;
    p.setAttribute("aria-hidden", "true");
    sc.appendChild(p);
    var anim = p.animate([
      { transform: position(t, 0, 0.4), opacity: 0 },
      { transform: position(t, 0, 1), opacity: 1, offset: 0.14, easing: COURBE },
      { transform: position(t, 1, 1), opacity: 1, offset: 0.86 },
      { transform: position(t, 1, 0.4), opacity: 0 }
    ], { duration: 950, fill: "forwards" });
    return new Promise(function (fin) {
      anim.onfinish = function () { p.remove(); fin(); };
    });
  }

  function jouer(sc) {
    var lm = sc.querySelector(".sp-lm"), cx = sc.querySelector(".sp-cx"), ch = sc.querySelector(".sp-ch");
    function poser() { var c = [].slice.call(arguments); return function () { c.forEach(function (x) { sc.classList.add(x); }); }; }
    function oter() { var c = [].slice.call(arguments); return function () { c.forEach(function (x) { sc.classList.remove(x); }); }; }
    function cycle() {
      ETATS.forEach(function (x) { sc.classList.remove(x); });
      return attendre(700)
        .then(poser("sp-a1"))                                          // étape 1 : le texte part vers le moteur
        .then(function () { return paquet(sc, cx, lm, "sp-pk-t"); })
        .then(poser("sp-e1")).then(function () { return attendre(900); })
        .then(oter("sp-a1")).then(poser("sp-a2"))                      // étape 2 : la traduction revient
        .then(function () { return paquet(sc, lm, cx, "sp-pk-t"); })
        .then(poser("sp-e2")).then(function () { return attendre(1100); })
        .then(poser("sp-e3")).then(function () { return attendre(500); })
        .then(oter("sp-a2")).then(poser("sp-a3"))                      // étape 3 : le Fast Lookup interroge CHnell
        .then(function () { return paquet(sc, cx, ch, "sp-pk-l"); })
        .then(poser("sp-e4")).then(function () { return attendre(3200); })
        .then(oter("sp-a3")).then(function () { return attendre(1400); });
    }
    function boucle() {
      cycle().then(function () {
        if (sc.__visible) boucle(); else sc.__enAttente = true;    // reprise au prochain passage à l'écran
      });
    }
    sc.classList.add("sp-e0");                                         // illustrations et liaisons
    boucle();
  }

  /* Premier départ quand un tiers du schéma est visible (la moitié de l'écran pour un schéma empilé plus haut que
     l'écran) ; ensuite, le cycle suivant ne part que si le schéma est encore à l'écran */
  var io = new IntersectionObserver(function (entrees) {
    entrees.forEach(function (en) {
      var sc = en.target, vu = en.isIntersecting && (en.intersectionRatio >= 0.35 || en.intersectionRect.height >= window.innerHeight * 0.5);
      sc.__visible = en.isIntersecting;
      if (!vu) return;
      if (!sc.__parti) { sc.__parti = true; jouer(sc); }
      else if (sc.__enAttente) { sc.__enAttente = false; jouer(sc); }
    });
  }, { threshold: [0, 0.1, 0.2, 0.35, 0.5] });
  scenes.forEach(function (sc) {
    sc.classList.add("sp-pret");
    io.observe(sc);
  });
})();
