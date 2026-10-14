/* Scène « word » de la page Plugin Word : le bouton Corrext du ruban affiche le panneau, la mémoire propose une
   formulation déjà validée (Apply), Fast Lookup cherche le terme dans les mémoires et dans CHnell, puis l'assistant IA
   propose d'harmoniser le terme dans tout le document (Oui, partout). Boucle d'environ trente secondes.
   Le HTML porte l'état final de la scène : il reste affiché tel quel sans script et en mouvement réduit. Aucun texte
   n'est écrit ici : la traduction d'origine du segment 2 vient de son attribut data-avant, la requête du champ. */
(function () {
  "use strict";
  if (!window.SIM) return;

  SIM.enregistrer("word", function (l) {
    if (SIM.reduit) return Promise.resolve();   // mouvement réduit : état final, sans animation
    var wd = l.q(".wd");
    var lignes = l.qa(".wd-page .wd-l[data-i]");
    var cible = l.q('.wd-l[data-i="2"] .wd-t');
    var memoire = cible.textContent, avant = cible.getAttribute("data-avant");
    var terme = l.q(".wd-kde"), champ = l.q(".wd-q"), requete = champ.textContent;
    var boite = champ.parentNode, resultats = l.q(".wd-res"), correspondance = l.q(".wd-mem"), assistant = l.q(".wd-ia");

    function choisir(i) {
      lignes.forEach(function (x) { x.classList.toggle("sel", x.getAttribute("data-i") === String(i)); });
    }

    return SIM.jouer(l, [
      /* Départ : panneau fermé, aucun segment choisi, traduction d'origine du segment 2, onglet Matches */
      function () {
        wd.classList.remove("ouvert");
        choisir(-1);
        cible.textContent = avant;
        terme.classList.remove("on");
        champ.textContent = "";
        [resultats, correspondance, assistant].forEach(function (x) { x.classList.remove("vu"); });
        return l.onglet(2);
      },
      SIM.fixe(700),
      /* Le bouton Corrext du ruban affiche le panneau Corrext editor */
      function () { return l.appui(".wd-btn"); },
      function () { wd.classList.add("ouvert"); return l.attendre(1000); },
      /* Segment 2 choisi : la mémoire cherche, puis propose la formulation validée d'un projet précédent */
      function () { choisir(2); wd.classList.add("traduit"); return l.attendre(900); },
      function () { wd.classList.remove("traduit"); correspondance.classList.add("vu"); return l.attendre(2400); },
      function () { return l.appui(".wd-apply"); },
      function () { cible.classList.add("maj"); return l.mots(cible, memoire); },
      SIM.fixe(1500),
      /* Segment 3 : le terme est sélectionné, puis cherché dans Fast Lookup, côté cible */
      function () { cible.classList.remove("maj"); choisir(3); return l.attendre(700); },
      function () { terme.classList.add("on"); return l.attendre(1000); },
      function () { return l.onglet(1); },
      function () { boite.classList.add("tape"); return l.taper(".wd-q", requete, 12); },
      function () { boite.classList.remove("tape"); resultats.classList.add("vu"); return l.attendre(4400); },
      /* AI Assistant : alternatives par moteur, puis proposition d'harmonisation */
      function () { return l.onglet(0); },
      SIM.fixe(2200),
      function () { assistant.classList.add("vu"); return l.attendre(2800); },
      function () { return l.appui(".wd-oui"); },
      function () { assistant.classList.add("fait"); wd.classList.add("harmonise"); return l.attendre(3400); },
      /* Fin de boucle : l'écran s'efface avant de reprendre */
      SIM.fixe(600),
      function () { wd.classList.add("fin"); return l.attendre(480); }
    ]);
  });
})();
