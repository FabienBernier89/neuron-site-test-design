/* Visite guidée de la démo « Extraits du registre du commerce » : recherche de la société d'exemple,
   langue cible, trois niveaux de certification, livraison, délai, pays, récapitulatif et confirmation locale,
   puis retour à l'état initial (la scène n'est pas réinitialisée entre deux boucles).
   Tout ce qui est tapé ou choisi provient de la démo elle-même : aucune donnée n'est inventée ici. */
(function () {
  "use strict";
  if (!window.SIM) return;
  var NOM = "visite-extraits-registre-commerce";
  var CPS = 13; /* frappe lisible : 13 caractères par seconde, chaque pas varie de 70 à 130 % */

  function rythme() { return 1000 / CPS * (0.7 + Math.random() * 0.6); }

  /* La démo place le focus sur l'étape affichée : on le rend aussitôt au visiteur (aucun vol de focus) */
  function rendreFocus(l, avant) {
    var maintenant = document.activeElement;
    if (maintenant === avant || !maintenant || !l.r.contains(maintenant)) return;
    if (avant && avant !== document.body && document.contains(avant) && avant.focus) {
      try { avant.focus({ preventScroll: true }); } catch (e) { /* navigateur sans option : on laisse tel quel */ }
    } else if (maintenant.blur) {
      maintenant.blur();
    }
  }
  /* Clic réel avec enfoncement visible, sans déplacer le focus du visiteur */
  function cliquer(l, sel) {
    var el = typeof sel === "string" ? l.q(sel) : sel;
    if (!el) return l.attendre(200);
    return l.appui(el).then(function () {
      var avant = document.activeElement;
      el.click();
      rendreFocus(l, avant);
      return l.attendre(250);
    });
  }
  /* Champ de saisie : efface puis tape caractère par caractère (événement input à chaque pas) */
  function effacer(l, el) {
    if (!el.value) return Promise.resolve();
    el.value = el.value.slice(0, -1);
    el.dispatchEvent(new Event("input", { bubbles: true }));
    return l.attendre(rythme()).then(function () { return effacer(l, el); });
  }
  function saisir(l, el, texte, i) {
    i = i || 0;
    if (i >= texte.length) return Promise.resolve();
    var c = texte.charAt(i);
    el.value += c;
    el.dispatchEvent(new Event("input", { bubbles: true }));
    /* petite hésitation entre deux mots */
    return l.attendre(rythme() + (c === " " ? 140 : 0)).then(function () { return saisir(l, el, texte, i + 1); });
  }
  /* Ligne du récapitulatif mise à jour : surlignage bref (animation CSS, rien ne reste affiché) */
  function surligner(l, sel) {
    var el = l.q(sel);
    if (!el) return Promise.resolve();
    el.classList.remove("maj");
    void el.offsetWidth;
    el.classList.add("maj");
    return Promise.resolve();
  }
  /* Valeur d'origine d'un sélecteur : l'option marquée par défaut, sinon la première */
  function origine(sel) {
    var o = [].filter.call(sel.options, function (x) { return x.defaultSelected; })[0] || sel.options[0];
    return o ? o.value : sel.value;
  }

  /* Si le visiteur prend la main, on retire les états passagers posés par la visite */
  function veiller(l, etat) {
    if (l.__ercVeille) return;
    l.__ercVeille = true;
    function nettoyer(e) {
      if (!e.isTrusted || (e.target.closest && e.target.closest(".sim-pause"))) return;
      var q = l.q("#cxrQ");
      if (q) {
        q.classList.remove("saisie");
        if (etat.frappe) q.value = etat.nom;
      }
      l.qa(".press,.maj").forEach(function (x) { x.classList.remove("press", "maj"); });
    }
    ["pointerdown", "keydown"].forEach(function (t) { l.r.addEventListener(t, nettoyer); });
  }

  SIM.enregistrer(NOM, function (l) {
    l.__ercLancee = true;
    if (SIM.reduit) return Promise.resolve(); /* mouvement réduit : la démo reste dans son état initial */
    var q = l.q("#cxrQ"), tgt = l.q("#cxrTgt"), pays = l.q("#cxrCountry");
    var niveaux = l.qa("#cxrLevels [role=radio]"), livraisons = l.qa("#cxrDeliv [role=radio]"), delais = l.qa("#cxrTime [role=radio]");
    var parUid = l.q('#cxrSeg [data-mode="uid"]'), parNom = l.q('#cxrSeg [data-mode="name"]');
    /* Société d'exemple et valeurs proposées par la démo */
    var etat = { nom: l.q("#cxrRes .cxr-co b").textContent, frappe: false };
    var depart = { tgt: origine(tgt), pays: origine(pays) };
    var anglais = [].filter.call(tgt.options, function (o) { return o.text === "English"; })[0];
    var international = [].filter.call(pays.options, function (o) { return o.text === "International"; })[0];
    var papier = livraisons.filter(function (x) { return /paper copy by post/i.test(x.getAttribute("data-value")); })[0] || livraisons[1];
    veiller(l, etat);

    return SIM.jouer(l, [
      SIM.fixe(1200),
      /* 1 · Recherche par nom de société : le champ se vide, le nom est tapé, puis Search */
      function () { return l.appui(q); },
      function () { q.classList.add("saisie"); etat.frappe = true; return l.attendre(260); },
      function () { return effacer(l, q); },
      SIM.fixe(280),
      function () { return saisir(l, q, etat.nom); },
      SIM.fixe(420),
      function () { etat.frappe = false; q.classList.remove("saisie"); return cliquer(l, "#cxrSearch"); },
      /* chargement de la démo (900 ms), puis résultat à lire */
      SIM.fixe(2100),
      function () { return cliquer(l, "#cxrSelect"); },
      SIM.fixe(1200),
      /* Langue cible */
      function () { return l.valeur(tgt, anglais ? anglais.value : depart.tgt); },
      SIM.fixe(1600),
      function () { return cliquer(l, "#cxrNext"); },
      SIM.fixe(1100),
      /* 2 · Les trois niveaux de certification, dans l'ordre */
      function () { return cliquer(l, niveaux[0]); },
      SIM.fixe(1300),
      function () { return cliquer(l, niveaux[1]); },
      SIM.fixe(1300),
      function () { return cliquer(l, niveaux[2]); },
      SIM.fixe(1600),
      function () { return cliquer(l, "#cxrNext"); },
      SIM.fixe(1000),
      /* 3 · Livraison : e-mail seul, puis exemplaire papier (le champ d'adresse apparaît, masqué en démo) */
      function () { return cliquer(l, livraisons[0]); },
      SIM.fixe(1100),
      function () { return cliquer(l, papier); },
      SIM.fixe(1600),
      function () { return cliquer(l, "#cxrNext"); },
      SIM.fixe(1200),
      /* 4 · Délai standard puis express, pays de livraison : le récapitulatif suit */
      function () { return cliquer(l, delais[0]); },
      function () { return surligner(l, "#cxrSumTl"); },
      SIM.fixe(1200),
      function () { return cliquer(l, delais[1]); },
      function () { return surligner(l, "#cxrSumTl"); },
      SIM.fixe(1300),
      function () { return l.valeur(pays, international ? international.value : depart.pays); },
      function () { return surligner(l, "#cxrSumCty"); },
      SIM.fixe(1400),
      /* Order a translation n'affiche qu'un message local : aucune commande n'est passée */
      function () { return cliquer(l, "#cxrOrder"); },
      SIM.fixe(2400),
      /* Retour à l'état initial : pays d'origine, Previous jusqu'à l'étape 1, langue d'origine,
         puis passage par la recherche par IDE et retour au nom (la démo remet alors la recherche à zéro) */
      function () { return l.valeur(pays, depart.pays); },
      SIM.fixe(450),
      function () { return cliquer(l, "#cxrPrev"); },
      SIM.fixe(450),
      function () { return cliquer(l, "#cxrPrev"); },
      SIM.fixe(450),
      function () { return cliquer(l, "#cxrPrev"); },
      SIM.fixe(700),
      function () { return l.valeur(tgt, depart.tgt); },
      SIM.fixe(500),
      function () { return cliquer(l, parUid); },
      SIM.fixe(1400),
      function () { return cliquer(l, parNom); },
      SIM.fixe(600)
    ]);
  });

  /* sim.js démarre ses lecteurs dès son exécution : si la scène était déjà prête avant ce fichier,
     son lancement a échoué faute de scène enregistrée, on le relance ici une seule fois */
  var racine = document.querySelector('[data-sim="' + NOM + '"]');
  if (racine && racine.__lecteur && !racine.__lecteur.__ercLancee) racine.__lecteur.lancer();
})();
