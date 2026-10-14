/* Schéma « qui fait quoi » (lot B) : flux entre Corrext, LexMachina et CHnell, joués une fois quand le schéma devient
   visible. Un segment part de Corrext vers LexMachina, la traduction revient, puis le Fast Lookup interroge CHnell.
   Sans script, sans IntersectionObserver ou en mouvement réduit, rien n'est posé : le schéma reste dans son état final.
   Mouvement en transform et opacity, courbe commune des écrans Corrext. Aucun texte affiché n'est écrit ici. */
(function () {
  "use strict";
  var scenes = [].slice.call(document.querySelectorAll(".sp-sc"));
  if (!scenes.length || !("IntersectionObserver" in window) || !Element.prototype.animate) return;
  if (window.matchMedia && window.matchMedia("(prefers-reduced-motion: reduce)").matches) return;
  var COURBE = "cubic-bezier(.22,.8,.24,1)";

  function attendre(ms) {
    return new Promise(function (fin) { setTimeout(fin, ms); });
  }

  /* Trajet d'un paquet, en coordonnées de la scène : à mi-hauteur de l'illustration quand les blocs sont côte à côte,
     dans l'intervalle vertical quand ils sont empilés */
  function trajet(sc, de, vers) {
    var b = sc.getBoundingClientRect(), a = de.getBoundingClientRect(), c = vers.getBoundingClientRect();
    if (c.right <= a.left + 1 || c.left >= a.right - 1) {
      var ui = de.querySelector(".sp-ui").getBoundingClientRect(), y = ui.top + ui.height / 2 - b.top;
      return c.right <= a.left + 1 ? [a.left - b.left, y, c.right - b.left, y] : [a.right - b.left, y, c.left - b.left, y];
    }
    var x = a.left + a.width / 2 - b.left;
    return c.bottom <= a.top + 1 ? [x, a.top - b.top, x, c.bottom - b.top] : [x, a.bottom - b.top, x, c.top - b.top];
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
    /* Apparition sur place, trajet à la courbe commune (décélération à l'arrivée), extinction sur place */
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
    function etape(n) { return function () { sc.classList.add("sp-e" + n); }; }
    etape(0)();                                                      // illustrations et liaisons
    attendre(600)
      .then(function () { return paquet(sc, cx, lm, "sp-pk-t"); })  // segment envoyé au moteur
      .then(etape(1)).then(function () { return attendre(400); })   // LexMachina traduit
      .then(function () { return paquet(sc, lm, cx, "sp-pk-t"); })  // la traduction revient
      .then(etape(2)).then(function () { return attendre(500); })   // sortie affichée dans Corrext
      .then(etape(3)).then(function () { return attendre(400); })   // bouton Fast Lookup
      .then(function () { return paquet(sc, cx, ch, "sp-pk-l"); })  // terme envoyé à CHnell
      .then(etape(4));                                               // résultat de CHnell
  }

  /* Départ quand un tiers du schéma est visible, ou la moitié de l'écran pour un schéma empilé plus haut que l'écran */
  var io = new IntersectionObserver(function (entrees) {
    entrees.forEach(function (en) {
      if (!en.isIntersecting || (en.intersectionRatio < 0.35 && en.intersectionRect.height < window.innerHeight * 0.5)) return;
      io.unobserve(en.target);
      jouer(en.target);
    });
  }, { threshold: [0, 0.1, 0.2, 0.35, 0.5] });
  scenes.forEach(function (sc) {
    sc.classList.add("sp-pret");
    io.observe(sc);
  });
})();
