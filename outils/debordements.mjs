#!/usr/bin/env node
// Débordements de texte et de mise en page d'un site déjà construit, mesurés dans Chrome sans interface (tâche 6.3 de la traduction).
//
//   node outils/debordements.mjs --racine <sortie> --pages de/,de/corrext/word-plugin/ --largeurs 390,1440 [--json] [--captures <dossier>] [--regles <fichier.json>] [--reference <rapport.json>]
//   node outils/debordements.mjs --help
//
// --racine    dossier du site construit (par exemple celui de SORTIE=... python3 build.py) ; servi en local sur 127.0.0.1.
// --pages     adresses des pages à mesurer, relatives à la racine (« de/ », « fr/corrext/plugin-word/ »), séparées par des virgules.
// --largeurs  largeurs de fenêtre en pixels (390 : téléphone, 1440 : bureau), séparées par des virgules. La largeur est
//             émulée : la fenêtre sans interface n'impose donc pas sa largeur minimale. Pas de mode mobile : Chrome mobile
//             élargit sa fenêtre pour montrer un contenu trop large et la mesure ne verrait plus le débordement.
// --json      rapport en JSON sur la sortie standard, au lieu du texte lisible.
// --captures  dossier où écrire une capture pleine page par page et par largeur, les éléments en cause cernés de rouge.
// --regles    nombre de lignes maximal par sélecteur (par défaut outils/debordements.json : {"sélecteur CSS": lignes max}).
// --reference rapport JSON d'une mesure précédente (celle des pages françaises, --json) : un relevé qui y figure déjà (même
//             genre, même largeur, même sélecteur) n'est pas un défaut de la traduction (Ruling 33) ; il est compté à part.
//
// Pour chaque page et chaque largeur, le script relève :
//  1. les éléments dont le contenu dépasse la boîte (scrollWidth > clientWidth + 1) ET dont un texte visible dépasse
//     réellement le bord de la boîte (une icône ou un bouton plus large que son conteneur n'est pas un débordement de
//     texte), hors zones faites pour défiler (overflow-x auto ou scroll), hors texte volontairement tronqué
//     (text-overflow: ellipsis) et hors éléments de 1 px (texte réservé aux lecteurs d'écran) ;
//  2. les éléments qui sortent de la fenêtre (à gauche de 0 ou à droite de la largeur), hors ceux contenus par un parent
//     qui les rogne ou les fait défiler (le corps et la racine ne comptent pas : ils cachent l'erreur, ils ne la réparent pas)
//     et hors ceux entièrement à gauche de la fenêtre (technique volontaire des liens d'évitement, positionnés à -9999 px) ;
//  3. les éléments d'un sélecteur de --regles qui passent leur nombre de lignes.
// Les menus sont mesurés ouverts : un par un le méga-menu à partir de 1024 px, le menu mobile déplié en dessous.
// Les animations sont réduites (prefers-reduced-motion) et la page est parcourue d'un bout à l'autre avant la mesure.
//
// Une ressource demandée par la page et absente de la racine (404 du serveur local) est un problème, listée avec la page
// (la demande automatique de /favicon.ico par Chrome exceptée).
//
// Code de sortie : 0 aucun problème, 1 au moins un problème, 2 erreur d'usage ou d'environnement (Chrome, page absente).
// Chrome est arrêté et son profil temporaire supprimé dans tous les cas, y compris sur Ctrl+C (SIGINT) ou SIGTERM.
// Chrome : /Applications/Google Chrome.app sur macOS, ou le programme donné par la variable CHROME. Aucune dépendance npm :
// le WebSocket de Node pilote Chrome par le protocole CDP.
import { spawn } from "node:child_process";
import { createServer } from "node:http";
import { existsSync, mkdirSync, mkdtempSync, readFileSync, rmSync, statSync, writeFileSync } from "node:fs";
import { tmpdir } from "node:os";
import { dirname, extname, join, normalize, resolve, sep } from "node:path";
import { fileURLToPath } from "node:url";

const ICI = dirname(fileURLToPath(import.meta.url));
const CHROME = process.env.CHROME || "/Applications/Google Chrome.app/Contents/MacOS/Google Chrome";
const DELAI_CHROME = parseInt(process.env.DEBORDEMENTS_DELAI_CHROME || "20000", 10);  // ms pour ouvrir le port de pilotage
const HAUTEUR = 900;          // hauteur de la fenêtre émulée
const HAUTEUR_CAPTURE_MAX = 16000;
const attendre = ms => new Promise(r => setTimeout(r, ms));

function echec(message) {
  console.error("Erreur : " + message);
  process.exit(2);
}

// ---------- arguments ----------
function aide() {
  // l'en-tête de ce fichier, sans les marques de commentaire
  const lignes = readFileSync(fileURLToPath(import.meta.url), "utf8").split("\n").slice(1);
  console.log(lignes.slice(0, lignes.findIndex(l => !l.startsWith("//"))).map(l => l.replace(/^\/\/ ?/, "")).join("\n"));
  process.exit(0);
}

function lireArguments(argv) {
  const a = { racine: null, pages: [], largeurs: [390, 1440], json: false, captures: null, regles: join(ICI, "debordements.json"),
    reference: null };
  for (let i = 0; i < argv.length; i++) {
    const cle = argv[i];
    const valeur = () => { if (i + 1 >= argv.length) echec(`${cle} attend une valeur`); return argv[++i]; };
    if (cle === "--help" || cle === "-h") aide();
    else if (cle === "--racine") a.racine = resolve(valeur());
    else if (cle === "--pages") a.pages = valeur().split(",").map(s => s.trim()).filter(Boolean);
    else if (cle === "--largeurs") a.largeurs = valeur().split(",").map(s => parseInt(s, 10)).filter(n => n > 0);
    else if (cle === "--json") a.json = true;
    else if (cle === "--captures") a.captures = resolve(valeur());
    else if (cle === "--regles") a.regles = resolve(valeur());
    else if (cle === "--reference") a.reference = resolve(valeur());
    else echec(`option inconnue : ${cle}`);
  }
  if (!a.racine || !a.pages.length || !a.largeurs.length) echec("usage : node outils/debordements.mjs --racine <sortie> --pages de/,de/corrext/word-plugin/ --largeurs 390,1440 [--json] [--captures <dossier>]");
  if (!existsSync(a.racine) || !statSync(a.racine).isDirectory()) echec(`racine introuvable : ${a.racine}`);
  return a;
}

// ---------- serveur statique local ----------
const TYPES = { ".html": "text/html; charset=utf-8", ".css": "text/css; charset=utf-8", ".js": "text/javascript; charset=utf-8",
  ".mjs": "text/javascript; charset=utf-8", ".json": "application/json", ".svg": "image/svg+xml", ".png": "image/png", ".jpg": "image/jpeg",
  ".jpeg": "image/jpeg", ".webp": "image/webp", ".ico": "image/x-icon", ".woff2": "font/woff2", ".woff": "font/woff",
  ".txt": "text/plain; charset=utf-8", ".xml": "application/xml" };

const introuvables = [];  // chemins servis en 404, dans l'ordre (mesurer prend ceux de sa page)

function servir(racine) {
  const serveur = createServer((req, rep) => {
    let chemin;
    try { chemin = normalize(decodeURIComponent(new URL(req.url, "http://x").pathname)); }
    catch (e) { rep.writeHead(400).end("adresse illisible"); introuvables.push(req.url + " (adresse illisible)"); return; }
    let fichier = join(racine, chemin);
    if (fichier !== racine && !fichier.startsWith(racine + sep)) { rep.writeHead(403).end(); return; }
    if (existsSync(fichier) && statSync(fichier).isDirectory()) fichier = join(fichier, "index.html");
    if (!existsSync(fichier)) {
      if (chemin !== "/favicon.ico") introuvables.push(chemin);  // demande automatique de Chrome : pas une ressource de la page
      rep.writeHead(404).end("introuvable");
      return;
    }
    rep.writeHead(200, { "Content-Type": TYPES[extname(fichier)] || "application/octet-stream" }).end(readFileSync(fichier));
  });
  return new Promise(ok => serveur.listen(0, "127.0.0.1", () => ok(serveur)));
}

// ---------- Chrome et protocole CDP ----------
let arreterChrome = null;  // arrêt de Chrome et suppression du profil, une seule fois (fin normale, erreur ou signal)

async function lancerChrome() {
  if (!existsSync(CHROME)) echec(`Chrome introuvable : ${CHROME} (variable CHROME)`);
  const profil = mkdtempSync(join(tmpdir(), "neuron-debordements-"));
  const chrome = spawn(CHROME, ["--headless=new", "--disable-gpu", "--hide-scrollbars", "--remote-debugging-port=0",
    `--user-data-dir=${profil}`, "--no-first-run", "--no-default-browser-check", "about:blank"], { stdio: ["ignore", "ignore", "pipe"] });
  const fin = new Promise(ok => chrome.once("exit", ok));
  let fait = false;
  const nettoyer = async () => {
    if (fait) return;
    fait = true;
    chrome.kill();
    await Promise.race([fin, attendre(5000)]);
    rmSync(profil, { recursive: true, force: true });
  };
  arreterChrome = nettoyer;
  const adresse = await new Promise((ok, ko) => {
    let journal = "";
    const delai = setTimeout(() => ko(new Error(`Chrome n'a pas ouvert son port de pilotage en ${DELAI_CHROME / 1000} s : `
      + journal.slice(-200))), DELAI_CHROME);
    chrome.stderr.on("data", d => {
      journal += d;
      const m = /DevTools listening on (ws:\/\/\S+)/.exec(journal);
      if (m) { clearTimeout(delai); ok(m[1]); }
    });
    chrome.once("exit", () => { clearTimeout(delai); ko(new Error("Chrome s'est arrêté au lancement : " + journal.slice(-200))); });
  }).catch(async e => { await nettoyer(); throw e; });  // port jamais ouvert : Chrome arrêté, profil supprimé
  return { adresse, nettoyer };
}

async function ouvrirSession(adresse) {
  const ws = new WebSocket(adresse);
  await new Promise((ok, ko) => { ws.addEventListener("open", ok); ws.addEventListener("error", () => ko(new Error("connexion CDP refusée"))); });
  let id = 0;
  const attente = new Map();
  const ecouteurs = [];
  ws.addEventListener("message", e => {
    const m = JSON.parse(e.data);
    if (m.id && attente.has(m.id)) { const [ok, ko] = attente.get(m.id); attente.delete(m.id); m.error ? ko(new Error(m.error.message)) : ok(m.result); }
    else if (m.method) ecouteurs.slice().forEach(f => f(m));
  });
  const appeler = (method, params = {}, sessionId) => new Promise((ok, ko) => {
    const i = ++id;
    const delai = setTimeout(() => { attente.delete(i); ko(new Error(`délai dépassé : ${method}`)); }, 60000);
    attente.set(i, [r => { clearTimeout(delai); ok(r); }, e => { clearTimeout(delai); ko(e); }]);
    ws.send(JSON.stringify({ id: i, method, params, sessionId }));
  });
  const evenement = (method, sessionId) => new Promise((ok, ko) => {
    const delai = setTimeout(() => ko(new Error(`événement attendu : ${method}`)), 60000);
    const f = m => { if (m.method === method && m.sessionId === sessionId) { clearTimeout(delai); ecouteurs.splice(ecouteurs.indexOf(f), 1); ok(m.params); } };
    ecouteurs.push(f);
  });
  const { targetId } = await appeler("Target.createTarget", { url: "about:blank" });
  const { sessionId } = await appeler("Target.attachToTarget", { targetId, flatten: true });
  const cdp = (method, params) => appeler(method, params, sessionId);
  await cdp("Page.enable");
  await cdp("Emulation.setEmulatedMedia", { features: [{ name: "prefers-reduced-motion", value: "reduce" }] });
  return { cdp, evenement: m => evenement(m, sessionId), fermer: () => ws.close() };
}

async function evaluer(cdp, expression) {
  const r = await cdp("Runtime.evaluate", { expression, awaitPromise: true, returnByValue: true });
  if (r.exceptionDetails) throw new Error("script de la page : " + (r.exceptionDetails.exception?.description || r.exceptionDetails.text));
  return r.result.value;
}

// ---------- code exécuté dans la page ----------
// Dresse la liste des états à mesurer (page, puis chaque menu ouvert) et prépare window.__ouvrir[i] pour y passer.
function preparerDansPage() {
  const etats = [{ nom: "page", ouvrir: () => {} }];
  const bureau = window.matchMedia("(min-width:1024px)").matches;
  if (bureau) {
    for (const btn of document.querySelectorAll("#hd [data-mg]")) {
      etats.push({ nom: "méga-menu « " + btn.textContent.trim() + " »", ouvrir: () => { if (btn.getAttribute("aria-expanded") !== "true") btn.click(); } });
    }
  } else {
    const burger = document.getElementById("hdBurger"), mm = document.getElementById("mm");
    if (burger && mm) {
      etats.push({ nom: "menu mobile", ouvrir: () => {
        if (mm.hidden) burger.click();
        for (const b of mm.querySelectorAll(".mm-g > .mm-h")) if (b.getAttribute("aria-expanded") !== "true") b.click();
      } });
    }
  }
  window.__ouvrir = etats.map(e => e.ouvrir);
  return etats.map(e => e.nom);
}

// Mesure la page telle qu'elle est affichée. regles : {sélecteur: lignes maximales} ; L : largeur de la fenêtre.
function mesurerDansPage(regles, L) {
  const segment = el => el.tagName.toLowerCase() + (el.classList.length ? "." + [...el.classList].slice(0, 2).join(".") : "");
  const selecteur = el => {
    const chaine = [];
    for (let e = el; e && e.nodeType === 1 && chaine.length < 3; e = e.parentElement) {
      if (e.id) { chaine.unshift("#" + e.id); break; }
      chaine.unshift(segment(e));
    }
    return chaine.join(" > ");
  };
  const extrait = el => (el.textContent || "").replace(/\s+/g, " ").trim().slice(0, 70);
  const rend = el => {
    const r = el.getBoundingClientRect();
    if (r.width === 0 && r.height === 0) return false;
    const s = getComputedStyle(el);
    if (s.visibility === "hidden" || s.display === "none") return false;
    // un parent transparent (menu de démonstration fermé, par exemple) rend l'élément invisible
    for (let a = el; a; a = a.parentElement) if (getComputedStyle(a).opacity === "0") return false;
    return true;
  };
  const defile = s => s.overflowX === "auto" || s.overflowX === "scroll";
  const rogne = s => defile(s) || s.overflowX === "hidden" || s.overflowX === "clip";
  const dedans = r => r.left >= -1 && r.right <= L + 1;
  // un parent (hors corps et racine) rogne ou fait défiler l'élément, et tient lui-même dans la fenêtre
  const contenu = el => {
    for (let a = el.parentElement; a && a !== document.body && a !== document.documentElement; a = a.parentElement) {
      if (rogne(getComputedStyle(a)) && dedans(a.getBoundingClientRect())) return true;
    }
    return false;
  };
  // un texte visible de l'élément dépasse le bord droit de sa boîte (ou le bord gauche)
  const texteDepasse = el => {
    const b = el.getBoundingClientRect();
    const gauche = b.left + el.clientLeft, droite = gauche + el.clientWidth;
    const marche = document.createTreeWalker(el, NodeFilter.SHOW_TEXT);
    for (let n = marche.nextNode(); n; n = marche.nextNode()) {
      if (!n.nodeValue.trim() || !n.parentElement || !rend(n.parentElement)) continue;
      const r = document.createRange();
      r.selectNodeContents(n);
      for (const x of r.getClientRects()) if (x.width > 0.5 && (x.right > droite + 1 || x.left < gauche - 1)) return true;
    }
    return false;
  };
  const nbLignes = el => {
    const rects = [];
    const marche = document.createTreeWalker(el, NodeFilter.SHOW_TEXT);
    for (let n = marche.nextNode(); n; n = marche.nextNode()) {
      if (!n.nodeValue.trim()) continue;
      const r = document.createRange();
      r.selectNodeContents(n);
      for (const x of r.getClientRects()) if (x.width > 0.5 && x.height > 0.5) rects.push(x);
    }
    rects.sort((a, b) => a.top - b.top || a.left - b.left);
    let n = 0, bas = -Infinity;
    for (const x of rects) {
      if (x.top >= bas - 1) { n++; bas = x.bottom; } else bas = Math.max(bas, x.bottom);
    }
    return n;
  };

  const res = { debordements: [], hors_fenetre: [], lignes: [] };
  window.__problemes = [];
  const noter = (liste, el, donnees) => { liste.push({ selecteur: selecteur(el), texte: extrait(el), ...donnees }); window.__problemes.push(el); };

  for (const el of document.querySelectorAll("*")) {
    if (el.closest("svg") && el.tagName.toLowerCase() !== "svg") continue;
    const s = getComputedStyle(el);
    if (s.display === "none") continue;
    // 1. contenu plus large que la boîte
    if (el instanceof HTMLElement && el.clientWidth > 1 && el.clientHeight > 1 && el.scrollWidth > el.clientWidth + 1
        && !defile(s) && s.textOverflow !== "ellipsis" && rend(el) && texteDepasse(el)) {
      noter(res.debordements, el, { scrollWidth: el.scrollWidth, clientWidth: el.clientWidth });
    }
    // 2. élément hors de la fenêtre
    if (el !== document.documentElement && el !== document.body && rend(el)) {
      const r = el.getBoundingClientRect();
      if ((r.right > L + 1 || r.left < -1) && r.right > 0 && !contenu(el)) {
        noter(res.hors_fenetre, el, { gauche: Math.round(r.left), droite: Math.round(r.right), fenetre: L });
      }
    }
  }
  // 3. nombre de lignes par sélecteur
  for (const [sel, max] of Object.entries(regles)) {
    for (const el of document.querySelectorAll(sel)) {
      if (!rend(el)) continue;
      const n = nbLignes(el);
      if (n > max) { res.lignes.push({ selecteur: sel, max, lignes: n, element: selecteur(el), texte: extrait(el) }); window.__problemes.push(el); }
    }
  }
  return res;
}

// Parcourt la page de haut en bas (déclenche les blocs chargés au défilement) et revient en haut.
async function parcourirDansPage() {
  const pas = Math.max(200, window.innerHeight - 100);
  for (let y = 0; y < document.documentElement.scrollHeight; y += pas) { window.scrollTo(0, y); await new Promise(r => setTimeout(r, 60)); }
  window.scrollTo(0, 0);
  await document.fonts.ready;
  await new Promise(r => setTimeout(r, 250));
  return document.documentElement.scrollHeight;
}

function cernerDansPage() {
  for (const el of window.__problemes || []) el.style.outline = "3px solid #ff2d2d";
}

// ---------- mesure d'une page à une largeur ----------
const cle = o => JSON.stringify([o.selecteur, o.element || "", o.texte]);

async function mesurer(session, url, largeur, regles, captures, nomCapture) {
  const { cdp, evenement } = session;
  await cdp("Emulation.setDeviceMetricsOverride", { width: largeur, height: HAUTEUR, deviceScaleFactor: 1, mobile: false });
  const charge = evenement("Page.loadEventFired");
  const debut404 = introuvables.length;
  await cdp("Page.navigate", { url });
  await charge;
  const hauteurPage = await evaluer(cdp, `(${parcourirDansPage})()`);
  const noms = await evaluer(cdp, `(${preparerDansPage})()`);
  const cumul = { debordements: [], hors_fenetre: [], lignes: [] };
  const vus = new Set();
  for (let i = 0; i < noms.length; i++) {
    if (i > 0) { await evaluer(cdp, `window.__ouvrir[${i}](); true`); await attendre(150); }
    const r = await evaluer(cdp, `(${mesurerDansPage})(${JSON.stringify(regles)}, ${largeur})`);
    for (const genre of Object.keys(cumul)) {
      for (const o of r[genre]) {
        const k = genre + cle(o);
        if (!vus.has(k)) { vus.add(k); cumul[genre].push({ ...o, etat: noms[i] }); }
      }
    }
    if (i === 0 && captures) {
      await evaluer(cdp, `(${cernerDansPage})(); true`);
      const img = await cdp("Page.captureScreenshot", { format: "png", captureBeyondViewport: true,
        clip: { x: 0, y: 0, width: largeur, height: Math.min(hauteurPage, HAUTEUR_CAPTURE_MAX), scale: 1 } });
      writeFileSync(join(captures, nomCapture), Buffer.from(img.data, "base64"));
    }
  }
  cumul.introuvables = [...new Set(introuvables.slice(debut404))];
  return cumul;
}

// Relevés déjà présents dans le rapport de référence (pages françaises, Ruling 33) : retirés des problèmes, comptés à part.
const GENRES = ["debordements", "hors_fenetre", "lignes"];
const cleReference = (genre, largeur, o) => JSON.stringify([genre, largeur, o.selecteur, o.element || ""]);

function lireReference(fichier) {
  let r;
  try { r = JSON.parse(readFileSync(fichier, "utf8")); } catch (e) { echec(`rapport de référence illisible : ${fichier} (${e.message})`); }
  const connus = new Set();
  for (const p of r.pages || []) for (const g of GENRES) for (const o of p[g] || []) connus.add(cleReference(g, p.largeur, o));
  return connus;
}

function retirerConnus(resultat, connus) {
  resultat.connus = 0;
  for (const g of GENRES) {
    const avant = resultat[g].length;
    resultat[g] = resultat[g].filter(o => !connus.has(cleReference(g, resultat.largeur, o)));
    resultat.connus += avant - resultat[g].length;
  }
  return resultat;
}

const problemes = r => r.debordements.length + r.hors_fenetre.length + r.lignes.length + (r.introuvables || []).length;

// ---------- rapport ----------
function regrouper(liste) {
  const groupes = new Map();
  for (const o of liste) {
    const k = o.selecteur + "|" + (o.element || "");
    if (!groupes.has(k)) groupes.set(k, { ...o, nombre: 0 });
    groupes.get(k).nombre++;
  }
  return [...groupes.values()];
}

function texteRapport(resultats) {
  const lignes = [];
  for (const r of resultats) {
    const n = problemes(r);
    lignes.push(`${r.page} à ${r.largeur} px : ${n ? n + " problème(s)" : "aucun débordement"}`
      + (r.connus ? ` (${r.connus} relevé(s) déjà présent(s) dans la référence, ignoré(s))` : ""));
    for (const o of regrouper(r.debordements)) lignes.push(`  contenu plus large que sa boîte : ${o.selecteur} (${o.nombre}) : ${o.scrollWidth} px pour ${o.clientWidth} px [${o.etat}] « ${o.texte} »`);
    for (const o of regrouper(r.hors_fenetre)) lignes.push(`  hors de la fenêtre : ${o.selecteur} (${o.nombre}) : de ${o.gauche} à ${o.droite} px pour ${o.fenetre} px [${o.etat}] « ${o.texte} »`);
    for (const o of regrouper(r.lignes)) lignes.push(`  trop de lignes : ${o.selecteur} (${o.nombre}) : ${o.lignes} lignes pour ${o.max} au plus [${o.etat}] « ${o.texte} »`);
    for (const c of r.introuvables || []) lignes.push(`  ressource introuvable (404) : ${c}`);
  }
  return lignes.join("\n");
}

// ---------- programme ----------
const arg = lireArguments(process.argv.slice(2));
let regles = {};
if (existsSync(arg.regles)) {
  try { regles = JSON.parse(readFileSync(arg.regles, "utf8")); } catch (e) { echec(`${arg.regles} illisible : ${e.message}`); }
}
for (const p of arg.pages) {
  const fichier = join(arg.racine, p, "index.html");
  if (!existsSync(fichier)) echec(`page absente de la racine : ${p} (${fichier})`);
}
if (arg.captures) mkdirSync(arg.captures, { recursive: true });

const connus = arg.reference ? lireReference(arg.reference) : null;
const serveur = await servir(arg.racine);
const base = `http://127.0.0.1:${serveur.address().port}/`;
for (const signal of ["SIGINT", "SIGTERM"]) {
  process.once(signal, async () => {  // Ctrl+C ou arrêt : jamais de Chrome orphelin ni de profil laissé dans /tmp
    if (arreterChrome) await arreterChrome();
    serveur.close();
    process.exit(signal === "SIGINT" ? 130 : 143);
  });
}
let chrome = null, session = null, code = 0;
try {
  chrome = await lancerChrome();
  session = await ouvrirSession(chrome.adresse);
  const resultats = [];
  for (const page of arg.pages) {
    for (const largeur of arg.largeurs) {
      const nom = (page.replace(/\/+$/, "").replace(/\//g, "-") || "racine") + "_" + largeur + ".png";
      const r = { page, largeur, ...(await mesurer(session, base + page, largeur, regles, arg.captures, nom)) };
      resultats.push(connus ? retirerConnus(r, connus) : r);
    }
  }
  const total = resultats.reduce((n, r) => n + problemes(r), 0);
  console.log(arg.json ? JSON.stringify({ total, pages: resultats }, null, 1) : texteRapport(resultats));
  code = total ? 1 : 0;
} catch (e) {
  console.error("Erreur : " + e.message);
  code = 2;
} finally {
  if (session) session.fermer();
  if (arreterChrome) await arreterChrome();
  serveur.close();
}
process.exit(code);
