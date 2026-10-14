/* Page de remerciement (réponse de envoi.php) : variante choisie d'après l'adresse.
   Démo par défaut (le HTML sans script), ?type=newsletter, ?erreur=champs (champ invalide), ?erreur=refus (refus
   anti-robot, plafond d'envoi ou échec du serveur, sans détail). Les textes des variantes sont dans le HTML :
   data-v-<variante> remplace le texte d'un élément, data-seul="<variante>" ne garde que les blocs de la variante. */
(function () {
  "use strict";
  var p;
  try { p = new URLSearchParams(location.search); } catch (e) { return; }
  var erreur = p.get("erreur");
  var v = erreur === "champs" ? "erreur" : erreur ? "refus" : p.get("type") === "newsletter" ? "newsletter" : "demo";
  if (v === "demo") return;
  [].forEach.call(document.querySelectorAll("[data-v-" + v + "]"), function (el) {
    el.textContent = el.getAttribute("data-v-" + v);
  });
  [].forEach.call(document.querySelectorAll("[data-seul]"), function (el) {
    el.hidden = el.getAttribute("data-seul") !== v;
  });
  if (v !== "erreur") return;
  /* Erreur : le bouton ramène au formulaire, sur la page d'où il est parti si elle est du site */
  var b = document.querySelector("[data-retour]");
  if (!b) return;
  var retour = b.getAttribute("data-retour");
  try {
    var r = new URL(document.referrer);
    if (r.origin === location.origin && r.pathname !== location.pathname) retour = r.href;
  } catch (e) { /* pas de page d'origine lisible */ }
  b.href = retour;
})();
