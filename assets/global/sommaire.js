/* Pages légales : surligne dans le sommaire la section en cours de lecture (aria-current). */
(function () {
  "use strict";
  var toc = document.querySelector(".lg-toc");
  if (!toc || !("IntersectionObserver" in window)) return;
  var liens = [].slice.call(toc.querySelectorAll('a[href^="#"]'));
  var cibles = liens.map(function (a) { return document.getElementById(a.getAttribute("href").slice(1)); }).filter(Boolean);
  if (!cibles.length) return;

  function activer(id) {
    liens.forEach(function (a) {
      if (a.getAttribute("href") === "#" + id) a.setAttribute("aria-current", "true");
      else a.removeAttribute("aria-current");
    });
  }
  /* Section active : la dernière dont l'intertitre a dépassé le haut de la zone de lecture ;
     en bas de page, la dernière section, même courte */
  function calculer() {
    if (window.innerHeight + window.scrollY >= document.documentElement.scrollHeight - 2) {
      activer(cibles[cibles.length - 1].id);
      return;
    }
    var passees = cibles.filter(function (c) { return c.getBoundingClientRect().top <= 120; });
    activer((passees[passees.length - 1] || cibles[0]).id);
  }
  var io = new IntersectionObserver(calculer, { rootMargin: "-96px 0px -55% 0px", threshold: [0, 1] });
  cibles.forEach(function (c) { io.observe(c); });
  var attente = false;
  window.addEventListener("scroll", function () {
    if (attente) return;
    attente = true;
    requestAnimationFrame(function () { attente = false; calculer(); });
  }, { passive: true });
  liens.forEach(function (a) { a.addEventListener("click", function () { activer(a.getAttribute("href").slice(1)); }); });
  calculer();
})();
