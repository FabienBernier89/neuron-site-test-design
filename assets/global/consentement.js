/* Mesure d'audience : bandeau de consentement et Google Tag Manager, chargé seulement après « Accepter » ; le conteneur
   porte Google Analytics 4 et les événements poussés par suivi.js dans dataLayer.
   Sans identifiant (<meta name="gtm-id">, absente de l'aperçu), ce script ne fait rien : ni bandeau, ni appel à Google.
   Mode consentement v2 : tout est refusé par défaut, seule la mesure (analytics_storage) est accordée, et seulement avec
   l'accord du visiteur ; Tag Manager n'est chargé qu'à ce moment-là.
   Le choix est gardé dans ce navigateur (même clé que le site actuel) ; « Préférences cookies », dans le pied de
   page, rouvre le bandeau. Un refus après un accord coupe la mesure et efface les cookies de Google Analytics.
   Tant qu'il est affiché, le bandeau réserve sa hauteur en bas de page ; après un choix, le focus revient au bouton
   qui l'a ouvert, sinon au contenu principal.
   window.NeuronConsentement.mesure() dit si la mesure est active (utilisé par suivi.js). */
(function () {
  "use strict";
  var actif = false;
  window.NeuronConsentement = { mesure: function () { return actif; } };
  var meta = document.querySelector('meta[name="gtm-id"]');
  var id = meta ? meta.getAttribute("content") : "";
  var bandeau = document.getElementById("cc");
  if (!id || !/^GTM-[A-Z0-9]+$/.test(id) || !bandeau) return;
  var charge = false;  // Tag Manager déjà chargé sur cette page
  var CLE = "neuron-consent";

  function lire() { try { return localStorage.getItem(CLE); } catch (e) { return null; } }
  function garder(v) { try { localStorage.setItem(CLE, v); } catch (e) { /* stockage indisponible : le choix vaut pour cette page */ } }

  function charger() {
    actif = true;
    if (charge) {  // déjà chargé sur cette page : la mesure reprend
      window.gtag("consent", "update", { analytics_storage: "granted" });
      return;
    }
    charge = true;
    window.dataLayer = window.dataLayer || [];
    window.gtag = window.gtag || function () { window.dataLayer.push(arguments); };
    window.gtag("consent", "default", { analytics_storage: "denied", ad_storage: "denied", ad_user_data: "denied", ad_personalization: "denied" });
    window.gtag("consent", "update", { analytics_storage: "granted" });
    window.dataLayer.push({ "gtm.start": new Date().getTime(), event: "gtm.js" });
    var s = document.createElement("script");
    s.async = true;
    s.src = "https://www.googletagmanager.com/gtm.js?id=" + encodeURIComponent(id);
    document.head.appendChild(s);
  }

  function effacerCookies() {
    var morceaux = location.hostname.split(".");
    document.cookie.split(";").forEach(function (c) {
      var nom = c.split("=")[0].trim();
      if (!/^_ga(_|$)/.test(nom)) return;
      document.cookie = nom + "=; Max-Age=0; path=/";
      for (var i = 0; i < morceaux.length - 1; i++) {
        document.cookie = nom + "=; Max-Age=0; path=/; domain=." + morceaux.slice(i).join(".");
      }
    });
  }

  function couper() {
    actif = false;
    /* Les balises du conteneur exigent analytics_storage : plus aucun envoi vers Google depuis cette page */
    if (charge) window.gtag("consent", "update", { analytics_storage: "denied" });
    effacerCookies();
  }

  var ouvreur = null;
  /* Hauteur du bandeau réservée en bas de page : la fin du pied reste lisible */
  function reserver() {
    document.body.style.paddingBottom = bandeau.hidden ? "" : bandeau.offsetHeight + "px";
  }
  function montrer(par) {
    ouvreur = par || null;
    bandeau.hidden = false;
    reserver();
    if (par) bandeau.querySelector("[data-cc]").focus();
  }
  function fermer() {
    bandeau.hidden = true;
    reserver();
    var cible = ouvreur || document.getElementById("main") || document.body;
    if (!cible.hasAttribute("tabindex") && !/^(A|BUTTON|INPUT|SELECT|TEXTAREA)$/.test(cible.tagName)) cible.setAttribute("tabindex", "-1");
    cible.focus({ preventScroll: true });
    ouvreur = null;
  }
  window.addEventListener("resize", function () { if (!bandeau.hidden) reserver(); });

  bandeau.addEventListener("click", function (e) {
    var b = e.target.closest ? e.target.closest("[data-cc]") : null;
    if (!b) return;
    var accord = b.getAttribute("data-cc") === "accepter";
    garder(accord ? "granted" : "denied");
    fermer();
    if (accord) charger(); else couper();
  });
  [].forEach.call(document.querySelectorAll("[data-cc-ouvrir]"), function (b) {
    b.hidden = false;
    b.addEventListener("click", function () { montrer(b); });
  });

  var choix = lire();
  if (choix === "granted") charger();
  else if (choix !== "denied") montrer(null);
})();
