/* En-tête : méga-menu (survol et clic), voile, menu mobile en accordéons, thème, formulaire neutralisé. */
(function () {
  "use strict";
  var hd = document.getElementById("hd");
  var racine = document.documentElement;
  var bureau = window.matchMedia("(min-width:1024px)");
  var voile = document.querySelector(".mg-voile"), ouvert = null, minuterie = null;
  var burger = document.getElementById("hdBurger"), mm = document.getElementById("mm");

  function fermer() {
    if (!ouvert) return;
    ouvert.btn.setAttribute("aria-expanded", "false");
    ouvert.pan.hidden = true;
    if (voile) voile.hidden = true;
    ouvert = null;
  }
  function ouvrir(btn) {
    if (ouvert && ouvert.btn === btn) return;
    fermer();
    var pan = document.getElementById(btn.getAttribute("aria-controls"));
    btn.setAttribute("aria-expanded", "true");
    pan.hidden = false;
    if (voile) voile.hidden = false;
    ouvert = { btn: btn, pan: pan };
  }
  function fermerMobile() {
    if (!mm || mm.hidden) return;
    mm.hidden = true;
    burger.setAttribute("aria-expanded", "false");
    document.body.style.overflow = "";
  }

  if (hd) {
    [].forEach.call(hd.querySelectorAll("[data-mg]"), function (btn) {
      btn.addEventListener("click", function () { if (ouvert && ouvert.btn === btn) fermer(); else ouvrir(btn); });
      btn.addEventListener("mouseenter", function () { if (!bureau.matches) return; clearTimeout(minuterie); ouvrir(btn); });
    });
    [].forEach.call(hd.querySelectorAll("a.hd-i"), function (a) {
      a.addEventListener("mouseenter", function () { if (bureau.matches) fermer(); });
    });
    hd.addEventListener("mouseleave", function () { if (bureau.matches) minuterie = setTimeout(fermer, 150); });
    hd.addEventListener("mouseenter", function () { clearTimeout(minuterie); });
  }
  if (voile) voile.addEventListener("click", fermer);
  document.addEventListener("keydown", function (e) {
    if (e.key !== "Escape") return;
    var b = ouvert && ouvert.btn;
    fermer();
    fermerMobile();
    if (b) b.focus();
  });

  if (burger && mm) {
    burger.addEventListener("click", function () {
      var o = mm.hidden;
      mm.hidden = !o;
      burger.setAttribute("aria-expanded", String(o));
      document.body.style.overflow = o ? "hidden" : "";
    });
  }
  [].forEach.call(document.querySelectorAll(".mm-g > .mm-h"), function (b) {
    b.addEventListener("click", function () {
      var o = b.getAttribute("aria-expanded") !== "true";
      b.setAttribute("aria-expanded", String(o));
      b.nextElementSibling.hidden = !o;
    });
  });

  /* Thème : préférence de confort propre à ce navigateur */
  function marquer() {
    [].forEach.call(document.querySelectorAll("[data-theme-set]"), function (b) {
      b.setAttribute("aria-pressed", String(b.getAttribute("data-theme-set") === racine.dataset.theme));
    });
  }
  [].forEach.call(document.querySelectorAll("[data-theme-set]"), function (b) {
    b.addEventListener("click", function () {
      racine.dataset.theme = b.getAttribute("data-theme-set");
      try { localStorage.setItem("theme", racine.dataset.theme); } catch (e) { /* stockage indisponible */ }
      marquer();
    });
  });
  marquer();

  /* Formulaire de démonstration : aucun envoi */
  [].forEach.call(document.querySelectorAll("form[data-demo]"), function (f) {
    f.addEventListener("submit", function (e) {
      e.preventDefault();
      var avis = f.querySelector(".avis");
      if (avis) avis.hidden = false;
    });
  });
})();
