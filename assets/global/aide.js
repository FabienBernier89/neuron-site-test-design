/* Centre d'aide (2026-10-17) : 1. une question visée par l'adresse (#q-…) s'ouvre ; 2. sur l'accueil du centre d'aide,
   la recherche filtre l'index des questions écrit dans la page (outils/composer/p_aide.py) et renvoie à la question.
   Aucun texte affiché n'est écrit ici. */
(function () {
  "use strict";
  function ouvrir() {
    var id = decodeURIComponent(location.hash.slice(1));
    var d = id && document.getElementById(id);
    if (d && d.tagName === "DETAILS") { d.open = true; d.scrollIntoView({ block: "start" }); }
  }
  window.addEventListener("hashchange", ouvrir);
  ouvrir();

  var f = document.querySelector("[data-aide-recherche]"), src = document.getElementById("aide-index");
  if (!f || !src) return;
  var input = f.querySelector("input"), res = f.querySelector(".hc-res"), data = JSON.parse(src.textContent);
  function norm(s) { return s.toLowerCase().normalize("NFD").replace(/[̀-ͯ]/g, ""); }
  data.forEach(function (x) { x.n = norm(x.q + " " + x.r); });
  function afficher() {
    var mots = norm(input.value).split(/\s+/).filter(function (m) { return m.length > 1; });
    res.textContent = "";
    if (!mots.length) { res.hidden = true; return; }
    var trouves = data.filter(function (x) { return mots.every(function (m) { return x.n.indexOf(m) >= 0; }); }).slice(0, 8);
    if (!trouves.length) {
      var p = document.createElement("p"); p.className = "hc-vide"; p.textContent = f.getAttribute("data-vide"); res.appendChild(p);
    }
    trouves.forEach(function (x) {
      var a = document.createElement("a"), b = document.createElement("b"), s = document.createElement("span");
      a.href = x.u; a.setAttribute("role", "option"); b.textContent = x.q; s.textContent = x.r;
      a.appendChild(b); a.appendChild(s); res.appendChild(a);
    });
    res.hidden = false;
  }
  input.addEventListener("input", afficher);
  input.addEventListener("keydown", function (e) {
    var liens = [].slice.call(res.querySelectorAll("a")), i = liens.indexOf(document.activeElement);
    if (e.key === "ArrowDown" && liens.length) { e.preventDefault(); liens[0].focus(); }
    if (e.key === "Escape") { input.value = ""; afficher(); }
  });
  res.addEventListener("keydown", function (e) {
    var liens = [].slice.call(res.querySelectorAll("a")), i = liens.indexOf(document.activeElement);
    if (e.key === "ArrowDown" && i < liens.length - 1) { e.preventDefault(); liens[i + 1].focus(); }
    if (e.key === "ArrowUp") { e.preventDefault(); (i > 0 ? liens[i - 1] : input).focus(); }
  });
  f.addEventListener("submit", function (e) {
    e.preventDefault();
    var a = res.querySelector("a");
    if (a) location.href = a.href;
  });
})();
