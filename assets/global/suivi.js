/* Suivi des parcours : UTM, page d'entrée, page d'origine et secteur, gardés pour la visite (sessionStorage), puis
   versés dans les champs cachés de tout formulaire envoyé à envoi.php ; t0 (horodatage du chargement) et, à l'envoi,
   duree : millisecondes passées sur la page, mesurées par ce navigateur, pour le délai minimal de envoi.php.
   Événements Google Analytics, sans effet tant que la mesure n'est pas acceptée (consentement.js) :
   generate_lead (demande de démo) et sign_up (newsletter) à l'arrivée sur la page de remerciement après un envoi
   réussi, cta_click sur [data-suivi], demo_interaction au premier geste réel dans une démo [data-interactif] (le bouton
   pause n'en est pas un), outbound_click sur un lien vers un autre site.
   Convention des data-suivi : cta-<contexte>-<position>, position « hero », « milieu » (bouton d'une bande en cours de
   page) ou « fin » (cta-accueil-hero, cta-securite-milieu, cta-plugin-word-fin, cta-secteur-<slug>-hero) ; le bouton
   de l'en-tête : cta-entete, et cta-entete-mobile dans le menu mobile.
   Les champs cachés sont tronqués à la longueur maximale qu'accepte envoi.php (CHAMPS), sinon l'envoi serait refusé.
   Chaque accès au stockage est protégé : stockage bloqué, le formulaire reçoit au moins ce que porte la page affichée. */
(function () {
  "use strict";
  var CLE = "neuron-suivi";
  var UTM = ["utm_source", "utm_medium", "utm_campaign", "utm_term", "utm_content"];
  /* Longueur maximale de chaque champ caché, en caractères : celle de CHAMPS dans envoi.php */
  var LONGUEURS = { page_entree: 500, page_origine: 500, utm_source: 200, utm_medium: 200, utm_campaign: 200, utm_term: 200, utm_content: 200 };
  var chemin = location.pathname;

  function lire() {
    try { return JSON.parse(sessionStorage.getItem(CLE)) || {}; } catch (e) { return {}; }
  }
  function garder(etat) {
    try { sessionStorage.setItem(CLE, JSON.stringify(etat)); } catch (e) { /* stockage indisponible */ }
  }
  function parametre(nom) {
    try { return new URLSearchParams(location.search).get(nom) || ""; } catch (e) { return ""; }
  }

  /* Événement GA : seulement si le visiteur a accepté la mesure */
  function evenement(nom, params) {
    var c = window.NeuronConsentement;
    if (!c || !c.mesure() || typeof window.gtag !== "function") return;
    window.gtag("event", nom, params || {});
  }
  window.NeuronSuivi = { evenement: evenement };

  /* État de la visite : UTM de la dernière campagne, page d'entrée, pages vues en dernier, dernier secteur */
  var etat = lire();
  if (UTM.some(function (k) { return parametre(k); })) {
    etat.utm = {};
    UTM.forEach(function (k) { if (parametre(k)) etat.utm[k] = parametre(k).slice(0, 200); });
  }
  if (!etat.entree) etat.entree = chemin;
  if (etat.derniere !== chemin) {
    etat.precedente = etat.derniere || "";
    etat.derniere = chemin;
  }
  var secteur = chemin.match(/\/solutions\/([a-z0-9-]+)\/$/);
  if (secteur) etat.secteur = secteur[1];
  garder(etat);

  /* Page d'origine : la page du site d'où vient le visiteur (référent interne), sinon la précédente de la visite */
  function origine() {
    try {
      var r = new URL(document.referrer);
      if (r.origin === location.origin && r.pathname !== chemin) return r.pathname;
    } catch (e) { /* pas de référent */ }
    return etat.precedente || "";
  }

  function poser(f, nom, valeur) {
    var c = f.querySelector('input[type="hidden"][name="' + nom + '"]');
    valeur = String(valeur);
    if (LONGUEURS[nom]) valeur = valeur.slice(0, LONGUEURS[nom]);
    if (c) c.value = valeur;
  }

  var t0 = String(Math.floor(Date.now() / 1000));
  var debut = Date.now();
  /* Millisecondes depuis le début du chargement de la page (horloge du navigateur seulement) */
  function duree() {
    var p = window.performance;
    return String(Math.round(p && p.now ? p.now() : Date.now() - debut));
  }
  [].forEach.call(document.querySelectorAll("form[action]"), function (f) {
    if (!/envoi\.php$/.test(f.getAttribute("action"))) return;
    poser(f, "page_entree", etat.entree || chemin);
    poser(f, "page_origine", origine());
    poser(f, "t0", t0);
    UTM.forEach(function (k) { poser(f, k, (etat.utm && etat.utm[k]) || parametre(k).slice(0, 200)); });
    var s = f.querySelector('select[name="secteur"]');
    /* ?secteur= d'abord, sinon la dernière page secteur visitée ; une valeur hors liste est ignorée */
    [parametre("secteur"), etat.secteur].some(function (voulu) {
      var connu = s && !s.value && voulu && [].some.call(s.options, function (o) { return o.value === voulu; });
      if (connu) s.value = voulu;
      return connu;
    });
    f.addEventListener("submit", function () {
      poser(f, "duree", duree());
      var type = f.querySelector('input[name="type"]');
      etat.envoi = { type: type ? type.value : "demo", secteur: s ? s.value : "" };  // pour l'événement de la page merci
      garder(etat);
    });
  });

  /* Page de remerciement après un envoi réussi : generate_lead ou sign_up, une fois (pas au rechargement ni au retour
     arrière, pas sans envoi : visite venue d'une page du site ou envoi noté dans la visite) */
  if (/\/contact\/merci\/$/.test(chemin)) {
    var navigation = window.performance && performance.getEntriesByType ? performance.getEntriesByType("navigation")[0] : null;
    var premiere = !navigation || navigation.type === "navigate";
    var interne = false;
    try { interne = new URL(document.referrer).origin === location.origin; } catch (e) { /* pas de référent */ }
    if (!parametre("erreur") && premiere && (etat.envoi || interne)) {
      if (parametre("type") === "newsletter") evenement("sign_up", { method: "newsletter" });
      else evenement("generate_lead", { secteur: (etat.envoi && etat.envoi.secteur) || "" });
    }
    delete etat.envoi;
    garder(etat);
  }

  /* Clics : appels à l'action et liens sortants */
  document.addEventListener("click", function (e) {
    if (!e.target.closest) return;
    var cta = e.target.closest("[data-suivi]");
    if (cta) evenement("cta_click", { cta: cta.getAttribute("data-suivi"), link_url: cta.href || "" });
    var a = e.target.closest("a[href]");
    if (a && /^https?:$/.test(a.protocol) && a.hostname !== location.hostname) {
      evenement("outbound_click", { link_url: a.href, link_domain: a.hostname });
    }
  });

  /* Démos interactives : premier geste réel du visiteur, une fois par démo */
  [].forEach.call(document.querySelectorAll("[data-interactif]"), function (d) {
    function geste(e) {
      if (!e.isTrusted) return;
      d.removeEventListener("pointerdown", geste);
      d.removeEventListener("keydown", geste);
      evenement("demo_interaction", { demo: d.getAttribute("data-sim") || "" });
    }
    d.addEventListener("pointerdown", geste);
    d.addEventListener("keydown", geste);
  });
})();
