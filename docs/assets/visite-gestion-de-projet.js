/* Visite guidée de la démo Gestion de projet : le tunnel en trois étapes joué sur les vrais contrôles
   (nom, confidentialité, langue cible, dépôt du fichier d'exemple, devis interne puis personnalisé),
   puis retour à l'état initial, car la scène n'est pas réinitialisée entre deux boucles.
   Aucun texte n'est écrit ici : le nom et la langue viennent de la démo (valeur du champ, liste des langues). */
(function () {
  "use strict";
  if (!window.SIM) return;
  var NOM = "visite-gestion-de-projet";

  /* Vrai pendant un geste de la visite : les appels focus() et select() de la démo sont alors ignorés,
     car ils feraient défiler la page ou prendraient le focus du visiteur. Dès son premier geste (l.arret),
     la démo retrouve son comportement d'origine. */
  var muet = false;
  function neutraliser(l) {
    if (l.cxpNeutre) return;
    l.cxpNeutre = true;
    l.qa("button, input, select, [tabindex]").forEach(function (e) {
      ["focus", "select"].forEach(function (m) {
        var origine = e[m];
        if (typeof origine !== "function") return;
        e[m] = function () { if (muet && !l.arret) return; return origine.apply(this, arguments); };
      });
    });
  }

  function cible(l, x) { return typeof x === "string" ? l.q(x) : x; }

  /* Clic réel avec enfoncement visible ; garde = durée pendant laquelle le focus reste neutralisé */
  function cliquer(l, x, garde) {
    var e = cible(l, x);
    if (!e) return l.attendre(200);
    return l.appui(e).then(function () {
      muet = true;
      try { e.click(); } finally { if (!garde) muet = false; }
      return l.attendre(garde || 250);
    }).then(function () { muet = false; });
  }

  /* Saisie dans un vrai champ : valeur posée caractère par caractère, événement input à chaque frappe,
     au rythme humain lisible (11 à 15 caractères par seconde, chaque frappe varie de 70 à 130 %) */
  function saisir(l, x, texte) {
    var e = cible(l, x), i = 0;
    e.classList.add("saisie");
    e.value = "";
    e.dispatchEvent(new Event("input", { bubbles: true }));
    function suite() {
      if (i >= texte.length) return Promise.resolve();
      i++;
      e.value = texte.slice(0, i);
      e.dispatchEvent(new Event("input", { bubbles: true }));
      return l.attendre(1000 / (11 + Math.random() * 4) * (0.7 + Math.random() * 0.6)).then(suite);
    }
    return suite();
  }

  /* Remise à zéro silencieuse d'un champ de recherche (filtre de la liste levé) */
  function vider(e) {
    e.value = "";
    e.dispatchEvent(new Event("input", { bubbles: true }));
  }

  /* Exécute l'action seulement si la démo n'est pas déjà dans l'état voulu */
  function si(test, action, tenue) {
    return function (l) {
      if (!test()) return Promise.resolve();
      return action(l).then(function () { return l.attendre(tenue || 300); });
    };
  }

  SIM.enregistrer(NOM, function (l) {
    if (SIM.reduit) return Promise.resolve();          // mouvement réduit : la démo reste dans son état initial
    if (l.cxpEnCours) return new Promise(function () {}); // un seul parcours à la fois
    l.cxpEnCours = true;
    neutraliser(l);

    var q = function (s) { return l.q(s); };
    var nom = q("#cxpName"), defaut = q("#cxpDefault"), recherche = q("#cxpLangSearch"), pop = q("#cxpLangPop");
    var niveau = q("#cxpLevel"), info = q("#cxpInfo");
    /* Langue cible : l'allemand, cohérent avec la paire FR → DE du tableau de devis */
    var caseLangue = q('#cxpLangList input[value="Allemand"]');
    var langue = caseLangue.value;
    var ligneLangue = caseLangue.closest("label");
    function etape(n) { return q("#cxpStep" + n).classList.contains("on"); }

    return SIM.jouer(l, [
      SIM.fixe(1000),

      /* Étape 1 · nom du projet saisi librement (valeur d'exemple de la démo) */
      function (l) { return cliquer(l, defaut); },
      SIM.fixe(350),
      function (l) { return saisir(l, nom, nom.defaultValue); },
      SIM.fixe(900),
      function () { nom.classList.remove("saisie"); return l.attendre(200); },

      /* Confidentialité : contenu hautement sensible (traitement en Suisse) */
      function (l) { return cliquer(l, '.cxp-card[data-conf="sensitive"]'); },
      SIM.fixe(1600),

      /* Langues cibles : ouverture de la liste, recherche, case cochée, puce affichée */
      function (l) { return cliquer(l, "#cxpLangBtn"); },
      SIM.fixe(500),
      function (l) { return saisir(l, recherche, langue.slice(0, 4)); },
      SIM.fixe(700),
      /* appui sur la ligne, clic sur la case elle-même (un clic sur l'étiquette déplacerait le focus) */
      function (l) { return l.appui(ligneLangue).then(function () { caseLangue.click(); return l.attendre(250); }); },
      SIM.fixe(1000),
      function (l) { recherche.classList.remove("saisie"); return cliquer(l, "#cxpLangBtn"); },
      function () { if (pop.hidden) vider(recherche); return l.attendre(1000); },

      /* Étape 2 · dépôt du fichier d'exemple, analyse, valeurs détectées */
      function (l) { return cliquer(l, "#cxpNext"); },
      SIM.fixe(800),
      function (l) { return cliquer(l, "#cxpDrop", 2600); },
      SIM.fixe(900),
      function (l) { return l.appui("#cxpFileCat"); },
      SIM.fixe(1300),

      /* Étape 3 · relecture interne, puis parcours personnalisé avec un traducteur juridique */
      function (l) { return cliquer(l, "#cxpNext"); },
      SIM.fixe(1800),
      function (l) { return cliquer(l, "#cxpTabCus"); },
      SIM.fixe(900),
      function (l) { return l.appui("#cxpDue"); },
      SIM.fixe(500),
      function (l) { return cliquer(l, "#cxpInfoBtn"); },
      SIM.fixe(2600),
      function (l) { return cliquer(l, "#cxpInfoBtn"); },
      SIM.fixe(400),
      function (l) { return l.valeur(niveau, "full"); },
      SIM.fixe(2500),
      function (l) { return cliquer(l, "#cxpQuote"); },
      SIM.fixe(2000),

      /* Retour à l'état initial, pas à pas et seulement là où c'est nécessaire */
      si(function () { return niveau.value !== ""; }, function (l) { return l.valeur(niveau, ""); }),
      si(function () { return !info.hidden; }, function (l) { return cliquer(l, "#cxpInfoBtn"); }),
      si(function () { return q("#cxpTabCus").classList.contains("on"); }, function (l) { return cliquer(l, "#cxpTabInt"); }, 450),
      si(function () { return etape(3); }, function (l) { return cliquer(l, "#cxpPrev"); }, 500),
      si(function () { return !q("#cxpFileCard").hidden; }, function (l) { return cliquer(l, "#cxpFileDel"); }, 400),
      si(function () { return etape(2); }, function (l) { return cliquer(l, "#cxpPrev"); }, 500),
      si(function () { return !pop.hidden; }, function (l) { return cliquer(l, "#cxpLangBtn"); }),
      function () { if (recherche.value) vider(recherche); return Promise.resolve(); },
      si(function () { return !!q("#cxpLangChips .cx-chip"); }, function (l) { return cliquer(l, "#cxpLangChips .cx-chip"); }),
      si(function () { return !!q("#cxpLangChips .cx-chip"); }, function (l) { return cliquer(l, "#cxpLangChips .cx-chip"); }),
      si(function () { return !q('.cxp-card[data-conf="standard"]').classList.contains("on"); }, function (l) { return cliquer(l, '.cxp-card[data-conf="standard"]'); }),
      si(function () { return defaut.classList.contains("off"); }, function (l) { return cliquer(l, defaut); }),
      SIM.fixe(800)
    ]).then(function () { l.cxpEnCours = false; });
  });

  /* sim.js crée les lecteurs dès son exécution, avant ce fichier : si le lecteur de la scène existe déjà
     sans avoir trouvé la visite, on le lance ici (le garde l.cxpEnCours empêche un double parcours). */
  var racine = document.querySelector('[data-sim="' + NOM + '"]');
  if (racine && racine.__lecteur && !racine.__lecteur.cxpEnCours) racine.__lecteur.lancer();
})();
