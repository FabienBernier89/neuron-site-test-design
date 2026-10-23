/* Erreurs des formulaires (audit du 2026-10-23, WCAG 3.3.1) : à l'envoi d'un formulaire incomplet, chaque champ fautif
   reçoit aria-invalid et un message lié par aria-describedby, un résumé s'écrit dans la région role="alert" posée en
   tête du formulaire (outils/post/z_formulaires.py), et le focus va au premier champ fautif. Le message d'un champ
   disparaît dès qu'il est corrigé. Sans script, le navigateur contrôle seul les champs obligatoires (production).
   Aucun texte affiché n'est écrit ici : les messages viennent des attributs data- de la région. */
(function () {
  "use strict";
  var formulaires = [].slice.call(document.querySelectorAll("form"));
  formulaires = formulaires.filter(function (f) { return f.querySelector(".f-err"); });
  if (!formulaires.length) return;
  var n = 0;

  function champs(f) {
    return [].filter.call(f.elements, function (c) {
      return c.willValidate && c.type !== "hidden" && !c.closest("[aria-hidden=true]");
    });
  }
  function message(c, r) {
    var v = c.validity;
    if (v.valueMissing) return r.getAttribute(c.type === "checkbox" ? "data-case" : c.tagName === "SELECT" ? "data-choix" : "data-requis");
    if (v.typeMismatch && c.type === "email") return r.getAttribute("data-email");
    return c.validationMessage;
  }
  /* Nom court du champ pour le résumé : son libellé, sans l'astérisque ; une case à cocher garde son seul message */
  function libelle(c) {
    if (c.type === "checkbox") return "";
    var l = c.labels && c.labels[0];
    if (!l) return "";
    var copie = l.cloneNode(true);
    [].forEach.call(copie.querySelectorAll("[aria-hidden=true]"), function (x) { x.remove(); });
    return copie.textContent.trim();
  }
  function lier(c, id, oui) {
    var ids = (c.getAttribute("aria-describedby") || "").split(/\s+/).filter(function (x) { return x && x !== id; });
    if (oui) ids.push(id);
    if (ids.length) c.setAttribute("aria-describedby", ids.join(" ")); else c.removeAttribute("aria-describedby");
  }
  function effacer(c) {
    var p = c.__msg;
    if (p) { p.remove(); c.__msg = null; lier(c, p.id, false); }
    c.removeAttribute("aria-invalid");
  }
  function signaler(c, texte) {
    if (!c.id) c.id = "champ-" + (++n);
    var p = c.__msg;
    if (!p) {
      p = document.createElement("p");
      p.className = "f-msg";
      p.id = c.id + "-erreur";
      /* sous le champ ; pour une case à cocher, sous la ligne case et libellé */
      var ancre = c.type === "checkbox" ? c.parentNode : c;
      ancre.parentNode.insertBefore(p, ancre.nextSibling);
      c.__msg = p;
    }
    p.textContent = texte;
    c.setAttribute("aria-invalid", "true");
    lier(c, p.id, true);
  }

  formulaires.forEach(function (f) {
    var r = f.querySelector(".f-err");
    f.noValidate = true;  // le script prend le relais des bulles du navigateur, dont la langue n'est pas garantie
    champs(f).forEach(function (c) {
      ["input", "change"].forEach(function (type) {
        c.addEventListener(type, function () { if (c.getAttribute("aria-invalid") === "true" && c.checkValidity()) effacer(c); });
      });
    });
  });

  /* Phase de capture sur le document : le contrôle passe avant les autres écouteurs (formulaire de démonstration de
     nav.js, suivi.js) et les arrête si un champ est fautif */
  document.addEventListener("submit", function (e) {
    var f = e.target, r = f.querySelector && f.querySelector(".f-err");
    if (!r || formulaires.indexOf(f) < 0) return;
    var fautifs = [];
    champs(f).forEach(function (c) {
      if (c.checkValidity()) effacer(c); else { signaler(c, message(c, r)); fautifs.push(c); }
    });
    r.textContent = "";
    if (!fautifs.length) return;
    e.preventDefault();
    e.stopPropagation();
    var titre = document.createElement("p"), liste = document.createElement("ul");
    titre.textContent = r.getAttribute("data-resume");
    fautifs.forEach(function (c) {
      var li = document.createElement("li"), a = document.createElement("a"), nom = libelle(c);
      a.href = "#" + c.id;
      a.textContent = (nom ? nom + " : " : "") + c.__msg.textContent;
      a.addEventListener("click", function (ev) { ev.preventDefault(); c.focus(); });
      li.appendChild(a);
      liste.appendChild(li);
    });
    r.appendChild(titre);
    r.appendChild(liste);
    fautifs[0].focus();
  }, true);
})();
