/* Cartes de fonctionnalités animées en CSS (.fx-g, cycles de 8 s) : bouton pause par grille (WCAG 2.2.2) et pause
   automatique hors écran (classe hors-champ, même modèle que schema-produits.js). Les scènes data-sim ont leur propre
   bouton, câblé par sim.js. Sans IntersectionObserver, rien n'est suspendu ; en mouvement réduit, rien ne bouge et le
   bouton reste masqué. Aucun texte affiché n'est écrit ici : les libellés viennent des attributs data- du bouton. */
(function () {
  "use strict";
  var reduit = window.matchMedia && window.matchMedia("(prefers-reduced-motion: reduce)").matches;
  var grilles = [].slice.call(document.querySelectorAll(".fx-g"));
  if (!grilles.length || reduit) return;

  /* Bouton pause : posé juste avant sa grille par outils/post/accessibilite.py */
  grilles.forEach(function (g) {
    var b = g.previousElementSibling;
    if (!b || !b.classList.contains("fx-pp")) return;
    b.hidden = false;
    b.addEventListener("click", function () {
      var pause = g.classList.toggle("en-pause");
      b.setAttribute("aria-label", b.getAttribute(pause ? "data-relancer" : "data-pause"));
      b.toggleAttribute("data-en-pause", pause);
    });
  });

  if (!("IntersectionObserver" in window)) return;
  var io = new IntersectionObserver(function (entrees) {
    entrees.forEach(function (en) { en.target.classList.toggle("hors-champ", !en.isIntersecting); });
  });
  grilles.forEach(function (g) { io.observe(g); });
})();
