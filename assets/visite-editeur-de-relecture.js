/* Visite guidée de la démo Éditeur de relecture : origine des traductions, reprise d'une formulation de la mémoire,
   confirmation et progression, Fast Lookup en direct, alternatives par moteur, reformulation par les réglages,
   puis retour à l'état initial. Chaque geste passe par un vrai contrôle de la démo ; aucun texte n'est ajouté :
   la seule saisie reprend la requête d'origine du champ Fast Lookup. */
(function () {
  "use strict";
  if (!window.SIM) return;

  var origine = null;   // état initial de la démo, relevé au premier passage
  var muette = false;   // région live coupée pendant la visite

  /* Certains gestionnaires de la démo appellent focus() : pendant un clic simulé, on neutralise cet appel
     pour ne jamais prendre le focus du visiteur ni faire défiler quoi que ce soit. */
  function sansFocus(fn) {
    var proto = HTMLElement.prototype, f = proto.focus;
    proto.focus = function () {};
    try { fn(); } finally { proto.focus = f; }
  }
  function cible(l, c) { return typeof c === "string" ? l.q(c) : c; }
  /* Appui visible puis vrai clic. L'enfoncement se relâche en temps réel, même si la visite s'arrête. */
  function clic(l, c) {
    var el = cible(l, c);
    if (!el) return l.attendre(200);
    el.classList.add("press");
    setTimeout(function () { el.classList.remove("press"); }, 170);
    return l.attendre(260).then(function () { sansFocus(function () { el.click(); }); });
  }
  function ligne(l, i) { return l.q('.cxe-tab tbody tr[data-i="' + i + '"]'); }
  function caseDe(l, i) { return ligne(l, i).querySelector(".cxe-chk"); }

  /* Saisie dans un vrai champ : valeur posée caractère par caractère, événement input à chaque frappe
     (11 à 15 caractères par seconde, chaque frappe varie de 70 à 130 %) */
  function saisir(l, champ, texte) {
    var cps = 11 + Math.random() * 4, i = 0;
    function frappe() {
      if (i >= texte.length) return Promise.resolve();
      i++;
      champ.value = texte.slice(0, i);
      champ.dispatchEvent(new Event("input", { bubbles: true }));
      return l.attendre(1000 / cps * (0.7 + Math.random() * 0.6)).then(frappe);
    }
    return frappe();
  }

  /* Relevé de l'état initial : traductions, cases, segment choisi, onglet, requête et côté Fast Lookup */
  function releve(l) {
    var lignes = l.qa(".cxe-tab tbody tr[data-i]");
    return {
      textes: l.qa(".cxe-tab .cxe-tgt").map(function (t) { return t.textContent; }),
      cases: l.qa(".cxe-tab tbody .cxe-chk").map(function (c) { return c.checked; }),
      sel: lignes.filter(function (r) { return r.classList.contains("sel"); }).map(function (r) { return r.getAttribute("data-i"); })[0],
      onglet: l.qa(".cxe-rb").map(function (b) { return b.getAttribute("aria-selected"); }).indexOf("true"),
      q: l.q("#cxeQ").value,
      cote: l.q(".cxe-seg button.on").getAttribute("data-side")
    };
  }

  /* Retour à l'état initial par les contrôles de la démo (le Reset des réglages a déjà été joué à l'écran) */
  function restaurer(l, d) {
    sansFocus(function () {
      if (l.q("#cxePop").classList.contains("on")) l.q("#cxeSet").click();
      l.qa(".cxe-tab tbody .cxe-chk").forEach(function (c, i) { if (c.checked !== d.cases[i]) c.click(); });
      /* Traduction d'origine remise en place ; l'événement blur laisse la démo enregistrer le texte courant */
      l.qa(".cxe-tab .cxe-tgt").forEach(function (t, i) {
        if (t.textContent !== d.textes[i]) { t.textContent = d.textes[i]; t.dispatchEvent(new Event("blur")); }
        var td = t.parentNode;
        td.classList.remove("cxe-upd");
        if (!td.className) td.removeAttribute("class");
      });
      var r = ligne(l, d.sel);
      if (r && !r.classList.contains("sel")) r.click();
      if (l.q("#cxeAiA").getAttribute("aria-selected") !== "true") l.q("#cxeAiA").click();
      var cote = l.q('.cxe-seg button[data-side="' + d.cote + '"]');
      if (!cote.classList.contains("on") || l.q("#cxeQ").value !== d.q) cote.click();
      var o = l.qa(".cxe-rb")[d.onglet];
      if (o && o.getAttribute("aria-selected") !== "true") o.click();
      l.q(".cxe-qbox").classList.remove("edr-actif");
    });
  }

  /* Fin de boucle : l'écran s'efface (450 ms, en temps réel pour ne jamais rester vide), la démo revient
     à son état initial, puis l'écran réapparaît */
  function finBoucle(l) {
    var zone = l.q(".cx-zone");
    zone.classList.add("edr-fin");
    return new Promise(function (ok) { setTimeout(ok, 480); }).then(function () {
      restaurer(l, origine);
      zone.classList.remove("edr-fin");
      return l.attendre(1300);
    });
  }

  /* Les annonces de la démo (région live) restent muettes pendant la visite automatique ;
     elles reviennent au premier geste réel du visiteur, celui qui arrête la visite */
  function couperAnnonces(l) {
    var live = l.q("#cxeLive"), racine = l.q().closest("[data-sim]");
    if (muette || !live || !racine) return;
    muette = true;
    live.setAttribute("aria-live", "off");
    function rendre(e) {
      if (!e.isTrusted || (e.target.closest && e.target.closest(".sim-pause"))) return;
      live.setAttribute("aria-live", "polite");
      l.q(".cxe-qbox").classList.remove("edr-actif");
      racine.removeEventListener("pointerdown", rendre);
      racine.removeEventListener("keydown", rendre);
    }
    racine.addEventListener("pointerdown", rendre);
    racine.addEventListener("keydown", rendre);
  }

  SIM.enregistrer("visite-editeur-de-relecture", function (l) {
    l.edrLancee = true;
    if (SIM.reduit) return Promise.resolve();   // mouvement réduit : la démo reste dans son état initial
    if (!origine) origine = releve(l);
    couperAnnonces(l);
    var champ = l.q("#cxeQ"), boite = l.q(".cxe-qbox");
    return SIM.jouer(l, [
      SIM.fixe(1200),
      /* Origine de la traduction : le segment 3 est repris tel quel de la mémoire (TM 100 %) */
      function (l) { return clic(l, ligne(l, 3)); },
      SIM.fixe(1700),
      /* Segment 2, traduit par le moteur : la mémoire propose une formulation déjà validée, Apply la reprend */
      function (l) { return clic(l, ligne(l, 2)); },
      SIM.fixe(1900),
      function (l) { return clic(l, "#cxeMemOk"); },
      SIM.fixe(2100),
      /* Confirmation des segments relus : la progression avance */
      function (l) { return clic(l, caseDe(l, 2)); },
      SIM.fixe(1100),
      function (l) { return clic(l, caseDe(l, 3)); },
      SIM.fixe(1600),
      /* Fast Lookup : recherche en direct dans les mémoires et dans CHnell, puis côté cible */
      function (l) { return clic(l, "#cxeT1"); },
      SIM.fixe(1300),
      function (l) { return clic(l, "#cxeQClr"); },
      SIM.fixe(500),
      function (l) { return clic(l, boite); },
      function (l) { boite.classList.add("edr-actif"); return saisir(l, champ, origine.q); },
      function (l) { return l.attendre(650); },
      function (l) { boite.classList.remove("edr-actif"); return l.attendre(2000); },
      function (l) { return clic(l, '.cxe-seg button[data-side="tgt"]'); },
      SIM.fixe(2300),
      /* Assistant IA : la même phrase traduite par plusieurs moteurs */
      function (l) { return clic(l, ligne(l, 4)); },
      SIM.fixe(700),
      function (l) { return clic(l, "#cxeT2"); },
      SIM.fixe(2400),
      /* Reformulation : réglages, style Simplified, Apply, puis reprise dans le segment */
      function (l) { return clic(l, "#cxeAiR"); },
      SIM.fixe(2000),
      function (l) { return clic(l, "#cxeSet"); },
      SIM.fixe(800),
      function (l) { return clic(l, '#cxePop [data-style="simp"]'); },
      SIM.fixe(700),
      function (l) { return clic(l, "#cxeSetOk"); },
      SIM.fixe(2900),
      function (l) { return clic(l, "#cxeRApply"); },
      SIM.fixe(2200),
      /* Réglages remis à zéro : Reset, puis Apply rend la reformulation par défaut */
      function (l) { return clic(l, "#cxeSet"); },
      SIM.fixe(700),
      function (l) { return clic(l, "#cxeReset"); },
      SIM.fixe(700),
      function (l) { return clic(l, "#cxeSetOk"); },
      SIM.fixe(1700),
      finBoucle
    ]);
  });

  /* sim.js démarre ses lecteurs dès son exécution (script différé, document déjà « interactive »), avant
     l'enregistrement de cette scène : on lance alors sa lecture ici, une seule fois */
  var racine = document.querySelector('[data-sim="visite-editeur-de-relecture"]');
  if (racine && racine.__lecteur && !racine.__lecteur.edrLancee) racine.__lecteur.lancer();
})();
