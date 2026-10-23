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
  /* Menu mobile modal : le reste de la page devient inerte, la tabulation boucle entre le bouton et les entrées du
     menu, Échap ferme et rend le focus au bouton (audit du 2026-10-23, WCAG 2.4.3 et 2.4.11) */
  var ouvrirLibelle = burger && burger.getAttribute("aria-label");
  function inertes() {
    return [].filter.call(document.body.children, function (el) { return el !== hd && el !== mm && el.tagName !== "SCRIPT"; });
  }
  function focusables() {
    var l = [].filter.call(mm.querySelectorAll("a[href],button,input,select,textarea,[tabindex]"), function (el) {
      return el.tabIndex >= 0 && !el.disabled && el.getClientRects().length;
    });
    return [burger].concat(l);
  }
  function ouvrirMobile() {
    mm.hidden = false;
    burger.setAttribute("aria-expanded", "true");
    if (burger.hasAttribute("data-fermer")) burger.setAttribute("aria-label", burger.getAttribute("data-fermer"));
    document.body.style.overflow = "hidden";
    inertes().forEach(function (el) { el.inert = true; });
    var premier = focusables()[1];
    if (premier) premier.focus();
  }
  function fermerMobile(rendreFocus) {
    if (!mm || mm.hidden) return;
    mm.hidden = true;
    burger.setAttribute("aria-expanded", "false");
    if (ouvrirLibelle) burger.setAttribute("aria-label", ouvrirLibelle);
    document.body.style.overflow = "";
    inertes().forEach(function (el) { el.inert = false; });
    if (rendreFocus) burger.focus();
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
  /* Méga-menu : quand le focus quitte le bouton et son panneau (tabulation), le panneau se referme */
  document.addEventListener("focusin", function (e) {
    if (ouvert && !ouvert.btn.contains(e.target) && !ouvert.pan.contains(e.target)) fermer();
  });
  document.addEventListener("keydown", function (e) {
    if (e.key === "Tab" && mm && !mm.hidden) {
      var l = focusables(), i = l.indexOf(document.activeElement);
      if (e.shiftKey && i <= 0) { e.preventDefault(); l[l.length - 1].focus(); }
      else if (!e.shiftKey && (i < 0 || i === l.length - 1)) { e.preventDefault(); l[0].focus(); }
      return;
    }
    if (e.key !== "Escape") return;
    var b = ouvert && ouvert.btn;
    fermer();
    if (mm && !mm.hidden) { fermerMobile(true); return; }
    if (b) b.focus();
  });

  if (burger && mm) {
    burger.addEventListener("click", function () {
      if (mm.hidden) ouvrirMobile(); else fermerMobile(true);
    });
    /* passage en largeur bureau, menu ouvert : la page ne doit pas rester inerte */
    if (bureau.addEventListener) bureau.addEventListener("change", function (m) { if (m.matches) fermerMobile(false); });
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

  /* Formulaire de démonstration : aucun envoi. Un avis à data-avis est une région aria-live déjà présente : son texte,
     injecté à l'envoi, est annoncé ; un avis masqué (hidden) est simplement affiché. */
  [].forEach.call(document.querySelectorAll("form[data-demo]"), function (f) {
    f.addEventListener("submit", function (e) {
      e.preventDefault();
      var avis = f.querySelector(".avis");
      if (!avis) return;
      if (avis.hasAttribute("data-avis")) avis.textContent = avis.getAttribute("data-avis");
      avis.hidden = false;
    });
  });
})();
