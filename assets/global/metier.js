/* Pages métier (2026-10-19) : onglets « Les outils du … » ; un clic ou les flèches montrent l'outil et son écran.
   Aucun texte affiché n'est écrit ici. */
(function () {
  "use strict";
  document.querySelectorAll("[data-onglets]").forEach(function (bloc) {
    var tabs = Array.prototype.slice.call(bloc.querySelectorAll('[role="tab"]'));
    var reduit = window.matchMedia && window.matchMedia("(prefers-reduced-motion: reduce)").matches;
    function montrer(i, focus) {
      tabs.forEach(function (t, j) {
        var on = i === j;
        t.setAttribute("aria-selected", on ? "true" : "false");
        t.tabIndex = on ? 0 : -1;
        t.parentNode.classList.toggle("on", on);
        var p = document.getElementById(t.getAttribute("aria-controls"));
        if (!on && !p.hidden && !reduit) {  // fondu enchaîné : l'écran quitté s'efface par-dessus le nouveau
          p.classList.add("mt-sort");
          setTimeout(function () { p.classList.remove("mt-sort"); }, 380);
        }
        p.hidden = !on;
      });
      if (focus) tabs[i].focus();
      window.dispatchEvent(new Event("resize"));  // la scène montrée recalcule son échelle (assets/sim.js)
    }
    tabs.forEach(function (t, i) {
      t.addEventListener("click", function () { montrer(i); });
      t.addEventListener("keydown", function (e) {
        var n = { ArrowDown: 1, ArrowRight: 1, ArrowUp: -1, ArrowLeft: -1 }[e.key];
        if (n) { e.preventDefault(); montrer((i + n + tabs.length) % tabs.length, true); }
      });
    });
    montrer(0);
  });
})();
