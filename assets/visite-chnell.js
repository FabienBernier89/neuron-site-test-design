/* Visite guidée de la démo Fast lookup CHnell : elle clique les vrais contrôles de la démo (champ, Search,
   inversion des langues, requêtes d'exemple, Advanced search, domaines, sources), puis ramène la démo
   à son état initial pour la boucle suivante (la scène n'est pas réinitialisée entre deux boucles).
   Aucun texte n'est écrit ici : le terme tapé est la valeur initiale du champ, le reste est lu dans la page. */
(function () {
  "use strict";
  if (!window.SIM) return;

  var CPS = 13; /* frappe lisible : caractères par seconde, variation de 70 à 130 % par caractère */

  /* Frappe dans un vrai champ : valeur posée caractère par caractère, événement input */
  function frappe(l, champ, texte) {
    var i = 0;
    function suite() {
      if (i >= texte.length) return Promise.resolve();
      i += 1;
      champ.value = texte.slice(0, i);
      champ.dispatchEvent(new Event("input", { bubbles: true }));
      return l.attendre(1000 / CPS * (0.7 + Math.random() * 0.6)).then(suite);
    }
    return suite();
  }
  /* Effacement caractère par caractère (retour arrière) */
  function effacer(l, champ) {
    function suite() {
      if (!champ.value) return Promise.resolve();
      champ.value = champ.value.slice(0, -1);
      champ.dispatchEvent(new Event("input", { bubbles: true }));
      return l.attendre(1000 / CPS * (0.7 + Math.random() * 0.6)).then(suite);
    }
    return suite();
  }

  /* Ordonnée d'un élément dans le contenu de la zone (offsetTop ignore la translation de cadrage) */
  function ordonnee(el, zone) {
    var y = 0, fin = zone.offsetParent;
    while (el && el !== zone && el !== fin) { y += el.offsetTop; el = el.offsetParent; }
    return y;
  }
  /* Cadrage : le contenu glisse (transform) pour montrer la plage [haut, bas] ; la page ne défile pas */
  function cadrer(l, z, haut, bas) {
    var zone = z.zone, cx = l.q("#cx"), h = zone.clientHeight, m = 14;
    var total = ordonnee(cx, zone) + cx.offsetHeight;
    var p = Math.min(Math.max(0, bas + m - h), Math.max(0, haut - m));
    p = Math.round(Math.max(0, Math.min(p, total - h)));
    if (p === z.pan) return l.attendre(60);
    z.pan = p;
    if (p) zone.style.setProperty("--cxv-y", p + "px"); else zone.style.removeProperty("--cxv-y");
    return l.attendre(520);
  }
  function enHaut(l, z) { return cadrer(l, z, 0, 0); }
  /* Cadre une plage d'éléments : du haut du premier au bas du dernier */
  function montrer(l, z, premier, dernier) {
    if (!premier || !dernier) return l.attendre(60);
    return cadrer(l, z, ordonnee(premier, z.zone), ordonnee(dernier, z.zone) + dernier.offsetHeight);
  }

  /* Le visiteur prend la main (même règle que le lecteur) : le cadrage devient un défilement interne,
     sans saut visible, et les états propres à la visite sont retirés */
  function priseEnMain(l, z, e) {
    if (!e.isTrusted || z.libre || (e.target.closest && e.target.closest(".sim-pause"))) return;
    z.libre = true;
    var zone = z.zone, cx = l.q("#cx"), p = z.pan;
    var t = window.getComputedStyle(cx).transform;
    if (t && t !== "none") p = -parseFloat(t.split(",")[5]) || 0;
    zone.classList.add("cxv-libre");
    zone.style.removeProperty("--cxv-y");
    zone.scrollTop = p;
    z.pan = 0;
    [].forEach.call(zone.querySelectorAll(".press,.cxv-focus,.cxv-ferme"), function (el) {
      el.classList.remove("press", "cxv-focus", "cxv-ferme");
    });
    if (zone.classList.contains("cxv-vide")) {
      zone.classList.remove("cxv-vide");
      z.champ.value = z.terme;
      z.pilules.forEach(function (b) { b.classList.toggle("on", b === z.pilule1); });
    }
  }

  /* Relevé de l'état initial de la démo (première boucle) */
  function preparer(l) {
    if (l.chn) return l.chn;
    var champ = l.q("#cxlQ"), pilules = l.qa("#cxEx [data-ex]");
    var p1 = l.q("#cxEx [data-ex].on") || pilules[0];
    var z = l.chn = {
      zone: l.q(".cx-zone"), champ: champ, terme: champ.defaultValue || champ.value,
      l1: l.q("#cxlL1").value, l2: l.q("#cxlL2").value, src: l.q("#cxlSrc").value,
      radio: l.q('input[name="cxlRes"]:checked'),
      pilules: pilules, pilule1: p1, pilule2: pilules.filter(function (b) { return b !== p1; })[0],
      pan: 0, n: 0, libre: false
    };
    ["pointerdown", "keydown"].forEach(function (type) {
      l.r.addEventListener(type, function (e) { priseEnMain(l, z, e); });
    });
    return z;
  }

  /* Filet de sécurité en fin de boucle : remet chaque réglage à sa valeur d'origine par les vrais contrôles */
  function remise(l, z) {
    var l1 = l.q("#cxlL1"), l2 = l.q("#cxlL2"), src = l.q("#cxlSrc"), adv = l.q("#cxlAdvBtn");
    l.qa('#cxlDoms [aria-pressed="true"]').forEach(function (b) { b.click(); });
    if (src.value !== z.src) { src.value = z.src; src.dispatchEvent(new Event("change", { bubbles: true })); }
    if (z.radio && !z.radio.checked) { z.radio.checked = true; z.radio.dispatchEvent(new Event("change", { bubbles: true })); }
    if (l1.value !== z.l1 || l2.value !== z.l2) {
      l1.value = z.l1; l2.value = z.l2;
      l1.dispatchEvent(new Event("change", { bubbles: true }));
    }
    if (adv.getAttribute("aria-expanded") === "true") adv.click();
    l.q("#cxlAdv").classList.remove("cxv-ferme");
    if (z.champ.value !== z.terme) z.pilule1.click();
  }

  /* Arrivée : champ vidé, résultats retirés (instantané à la première boucle, avant que la scène soit visible) */
  function vider(l, z) {
    var zone = z.zone, champ = z.champ;
    function retirer() {
      zone.classList.add("cxv-vide");
      z.pilules.forEach(function (b) { b.classList.remove("on"); });
    }
    if (z.n === 1) { champ.value = ""; retirer(); return l.attendre(60); }
    champ.classList.add("cxv-focus");
    return l.appui(champ).then(function () {
      retirer();
      return l.attendre(260);
    }).then(function () {
      return effacer(l, champ);
    }).then(function () {
      champ.classList.remove("cxv-focus");
      return l.attendre(200);
    });
  }

  SIM.enregistrer("visite-chnell", function (l) {
    var z = preparer(l);
    if (SIM.reduit) return Promise.resolve();          /* mouvement réduit : la démo reste dans son état initial */
    z.n += 1;
    var champ = z.champ, zone = z.zone, go = l.q("#cxlGo"), advp = l.q("#cxlAdv");
    var chipBanque = l.q('#cxlDoms [data-dom="BANKING & FINANCE"]');
    var fedlex = l.q('#cxlSrc option[value="fedlex.admin.ch"]');
    function cols() { return l.q("#cxlCols"); }
    /* Dernière ligne affichée des résultats (les lignes de contexte masquées n'ont pas de position) */
    function derniere() {
      var c = [].filter.call(cols().children, function (e) { return !e.hidden; });
      return c[c.length - 1];
    }

    return SIM.jouer(l, [
      /* 1. Écran vide */
      function () { return vider(l, z); },
      SIM.fixe(1300),
      /* 2. Frappe du terme d'exemple, puis lancement : squelette, puis segments alignés ligne à ligne */
      function () { champ.classList.add("cxv-focus"); return l.appui(champ); },
      function () { return frappe(l, champ, z.terme); },
      SIM.fixe(550),
      function () { return l.appui(go); },
      function () {
        champ.classList.remove("cxv-focus");
        go.click();
        zone.classList.remove("cxv-vide");
        return l.attendre(2400);
      },
      /* 3. Lecture des résultats : les deux segments, leur domaine et leur source officielle */
      function () { return montrer(l, z, cols(), l.q("#cxlMoreWrap")); },
      SIM.fixe(2300),
      function () { return enHaut(l, z); },
      SIM.fixe(500),
      /* 4. Inversion des langues, puis retour à la paire d'origine */
      function () { return l.cliquer("#cxlSwap"); },
      SIM.fixe(2300),
      function () { return l.cliquer("#cxlSwap"); },
      SIM.fixe(1200),
      /* 5. Deuxième requête d'exemple */
      function () { return l.cliquer(z.pilule2); },
      SIM.fixe(2700),
      /* 6. Recherche avancée : filtre de domaine, puis filtre de source */
      function () { return l.cliquer("#cxlAdvBtn"); },
      function () { return montrer(l, z, l.q("#cxlDoms"), cols().firstElementChild); },
      SIM.fixe(900),
      function () { return l.cliquer(chipBanque); },
      function () { return montrer(l, z, l.q("#cxlDoms"), derniere()); },
      SIM.fixe(2300),
      function () { return l.cliquer(chipBanque); },
      SIM.fixe(600),
      function () { return montrer(l, z, l.q("#cxlSrc"), cols().firstElementChild); },
      function () { return l.valeur("#cxlSrc", fedlex ? fedlex.value : z.src); },
      function () { return montrer(l, z, l.q("#cxlSrc"), derniere()); },
      SIM.fixe(2300),
      function () { return l.valeur("#cxlSrc", z.src); },
      SIM.fixe(700),
      /* 7. Fermeture du panneau, retour en haut de l'écran */
      function () { return enHaut(l, z); },
      function () { return l.appui("#cxlAdvBtn"); },
      function () { advp.classList.add("cxv-ferme"); return l.attendre(230); },
      function () { l.q("#cxlAdvBtn").click(); advp.classList.remove("cxv-ferme"); return l.attendre(800); },
      /* 8. Retour à l'état initial : première requête d'exemple, paire d'origine */
      function () { return l.cliquer(z.pilule1); },
      SIM.fixe(2400),
      function () { remise(l, z); return l.attendre(60); }
    ]);
  });

  /* sim.js démarre ses lecteurs dès son exécution (document « interactive » pendant les scripts différés),
     donc avant cet enregistrement : on lance alors la visite nous-mêmes, une seule fois */
  var racine = document.querySelector('[data-sim="visite-chnell"]');
  if (racine && racine.__lecteur && !racine.__lecteur.chn) racine.__lecteur.lancer();
})();
