/* global/aide.js */
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
;
/* global/consentement.js */
/* Mesure d'audience : bandeau de consentement et Google Analytics 4, chargé seulement après « Accepter ».
   Sans identifiant (<meta name="ga-id">, absente de l'aperçu), ce script ne fait rien : ni bandeau, ni appel à Google.
   Mode consentement v2 : tout est refusé par défaut, la mesure n'est accordée qu'avec l'accord du visiteur.
   Le choix est gardé dans ce navigateur (même clé que le site actuel) ; « Préférences cookies », dans le pied de
   page, rouvre le bandeau. Un refus après un accord coupe la mesure et efface les cookies de Google Analytics.
   Tant qu'il est affiché, le bandeau réserve sa hauteur en bas de page ; après un choix, le focus revient au bouton
   qui l'a ouvert, sinon au contenu principal.
   window.NeuronConsentement.mesure() dit si la mesure est active (utilisé par suivi.js). */
(function () {
  "use strict";
  var actif = false;
  window.NeuronConsentement = { mesure: function () { return actif; } };
  var meta = document.querySelector('meta[name="ga-id"]');
  var id = meta ? meta.getAttribute("content") : "";
  var bandeau = document.getElementById("cc");
  if (!id || !/^G-[A-Z0-9]+$/.test(id) || !bandeau) return;
  var CLE = "neuron-consent";

  function lire() { try { return localStorage.getItem(CLE); } catch (e) { return null; } }
  function garder(v) { try { localStorage.setItem(CLE, v); } catch (e) { /* stockage indisponible : le choix vaut pour cette page */ } }

  function charger() {
    window["ga-disable-" + id] = false;
    actif = true;
    if (window.gtag) {  // déjà chargé sur cette page : la mesure reprend
      window.gtag("consent", "update", { analytics_storage: "granted" });
      return;
    }
    window.dataLayer = window.dataLayer || [];
    window.gtag = function () { window.dataLayer.push(arguments); };
    window.gtag("consent", "default", { analytics_storage: "denied", ad_storage: "denied", ad_user_data: "denied", ad_personalization: "denied" });
    window.gtag("consent", "update", { analytics_storage: "granted" });
    window.gtag("js", new Date());
    window.gtag("config", id);
    var s = document.createElement("script");
    s.async = true;
    s.src = "https://www.googletagmanager.com/gtag/js?id=" + encodeURIComponent(id);
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
    window["ga-disable-" + id] = true;  // plus aucun envoi vers Google depuis cette page
    if (window.gtag) window.gtag("consent", "update", { analytics_storage: "denied" });
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
;
/* global/metier.js */
/* Pages métier (2026-10-19) : onglets « Les outils du … » ; un clic ou les flèches montrent l'outil et son écran.
   Aucun texte affiché n'est écrit ici. */
(function () {
  "use strict";
  document.querySelectorAll("[data-onglets]").forEach(function (bloc) {
    var tabs = Array.prototype.slice.call(bloc.querySelectorAll('[role="tab"]'));
    function montrer(i, focus) {
      tabs.forEach(function (t, j) {
        var on = i === j;
        t.setAttribute("aria-selected", on ? "true" : "false");
        t.tabIndex = on ? 0 : -1;
        t.parentNode.classList.toggle("on", on);
        document.getElementById(t.getAttribute("aria-controls")).hidden = !on;
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
;
/* global/schema-produits.js */
/* Schéma « qui fait quoi » (lot B) : flux en trois étapes entre Corrext, LexMachina et CHnell, rejoué tant que le
   schéma reste à l'écran (proposition A retenue par Fabien le 2026-10-15).
   1. Corrext envoie le texte au moteur : LexMachina s'éclaire.
   2. La traduction revient : Corrext s'éclaire, la sortie s'affiche.
   3. Le Fast Lookup interroge CHnell : CHnell s'éclaire, le résultat s'affiche.
   L'étape en cours s'allume aussi dans la liste ol.sp-et. Sans script, sans IntersectionObserver ou en mouvement
   réduit, rien n'est posé : le schéma reste dans son état final. Mouvement en transform et opacity. Aucun texte
   affiché n'est écrit ici. */
(function () {
  "use strict";
  var scenes = [].slice.call(document.querySelectorAll(".sp-sc"));
  if (!scenes.length || !("IntersectionObserver" in window) || !Element.prototype.animate) return;
  if (window.matchMedia && window.matchMedia("(prefers-reduced-motion: reduce)").matches) return;
  var COURBE = "cubic-bezier(.22,.8,.24,1)";
  var ETATS = ["sp-e1", "sp-e2", "sp-e3", "sp-e4", "sp-a1", "sp-a2", "sp-a3"];

  function attendre(ms) {
    return new Promise(function (fin) { setTimeout(fin, ms); });
  }

  /* Trajet d'un paquet, en coordonnées de la scène : d'un visuel à l'autre, à mi-hauteur, quand les cartes sont côte à
     côte ; dans l'intervalle vertical quand elles sont empilées */
  function trajet(sc, de, vers) {
    var b = sc.getBoundingClientRect(), a = de.querySelector(".sp-ui").getBoundingClientRect(), c = vers.querySelector(".sp-ui").getBoundingClientRect();
    if (c.right <= a.left + 1 || c.left >= a.right - 1) {
      var y = a.top + a.height / 2 - b.top;
      return c.right <= a.left + 1 ? [a.left - b.left, y, c.right - b.left, y] : [a.right - b.left, y, c.left - b.left, y];
    }
    var x = a.left + a.width / 2 - b.left, n = de.getBoundingClientRect(), m = vers.getBoundingClientRect();
    return m.bottom <= n.top + 1 ? [x, n.top - b.top, x, m.bottom - b.top] : [x, n.bottom - b.top, x, m.top - b.top];
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
    function poser() { var c = [].slice.call(arguments); return function () { c.forEach(function (x) { sc.classList.add(x); }); }; }
    function oter() { var c = [].slice.call(arguments); return function () { c.forEach(function (x) { sc.classList.remove(x); }); }; }
    function cycle() {
      ETATS.forEach(function (x) { sc.classList.remove(x); });
      return attendre(700)
        .then(poser("sp-a1"))                                          // étape 1 : le texte part vers le moteur
        .then(function () { return paquet(sc, cx, lm, "sp-pk-t"); })
        .then(poser("sp-e1")).then(function () { return attendre(900); })
        .then(oter("sp-a1")).then(poser("sp-a2"))                      // étape 2 : la traduction revient
        .then(function () { return paquet(sc, lm, cx, "sp-pk-t"); })
        .then(poser("sp-e2")).then(function () { return attendre(1100); })
        .then(poser("sp-e3")).then(function () { return attendre(500); })
        .then(oter("sp-a2")).then(poser("sp-a3"))                      // étape 3 : le Fast Lookup interroge CHnell
        .then(function () { return paquet(sc, cx, ch, "sp-pk-l"); })
        .then(poser("sp-e4")).then(function () { return attendre(3200); })
        .then(oter("sp-a3")).then(function () { return attendre(1400); });
    }
    function boucle() {
      cycle().then(function () {
        if (sc.__visible) boucle(); else sc.__enAttente = true;    // reprise au prochain passage à l'écran
      });
    }
    sc.classList.add("sp-e0");                                         // illustrations et liaisons
    boucle();
  }

  /* Premier départ quand un tiers du schéma est visible (la moitié de l'écran pour un schéma empilé plus haut que
     l'écran) ; ensuite, le cycle suivant ne part que si le schéma est encore à l'écran */
  var io = new IntersectionObserver(function (entrees) {
    entrees.forEach(function (en) {
      var sc = en.target, vu = en.isIntersecting && (en.intersectionRatio >= 0.35 || en.intersectionRect.height >= window.innerHeight * 0.5);
      sc.__visible = en.isIntersecting;
      if (!vu) return;
      if (!sc.__parti) { sc.__parti = true; jouer(sc); }
      else if (sc.__enAttente) { sc.__enAttente = false; jouer(sc); }
    });
  }, { threshold: [0, 0.1, 0.2, 0.35, 0.5] });
  scenes.forEach(function (sc) {
    sc.classList.add("sp-pret");
    io.observe(sc);
  });
})();
;
/* global/sommaire.js */
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
;
/* global/suivi.js */
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
    /* ?demande=documentation-api (bouton de la page API et on-premises) : le formulaire de démo devient une demande
       de documentation API, objet d'e-mail distinct dans envoi.php ; le message est prérempli s'il est vide */
    var type = f.querySelector('input[type="hidden"][name="type"]');
    if (type && type.value === "demo" && parametre("demande") === "documentation-api") {
      type.value = "documentation";
      var m = f.querySelector('textarea[name="message"]');
      if (m && !m.value) m.value = "Je souhaite recevoir la documentation technique de l'API.";
    }
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
;
