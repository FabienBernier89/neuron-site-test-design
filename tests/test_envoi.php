<?php
/*
 * Tests des fonctions de envoi.php (lot C). Lancement : php tests/test_envoi.php
 * Code de sortie 0 si tous les cas passent, 1 sinon. Aucun e-mail n'est envoyé : traiter() n'est pas appelé.
 * L'horloge et le stockage sont injectés : limiter() reçoit l'heure, compter() et preparer_dossier() un fichier ou un
 * dossier temporaires ; le journal du serveur est redirigé vers un fichier temporaire le temps des cas qui l'écrivent.
 */
declare(strict_types=1);

require __DIR__ . '/../envoi.php';

$echecs = 0;

function verifier(bool $condition, string $cas): void
{
    global $echecs;
    echo ($condition ? 'ok      ' : 'ÉCHEC   ') . $cas . "\n";
    if (!$condition) {
        $echecs++;
    }
}

function motif(array $post): string
{
    $r = valider($post);
    return $r['ok'] ? 'ok' : $r['motif'];
}

$demande = [
    'type' => 'demo', 'prenom' => 'Anne', 'nom' => 'Muster', 'email' => 'anne.muster@exemple.ch',
    'organisation' => 'Étude Muster', 'fonction' => 'avocat', 'consentement' => 'oui', 'site_url' => '', 'duree' => '45000',
];
$lettre = ['type' => 'newsletter', 'email' => 'anne.muster@exemple.ch', 'consentement' => 'oui', 'site_url' => '', 'duree' => '8000'];

// Demandes valides
$r = valider($demande);
verifier($r['ok'] && $r['type'] === 'demo' && $r['donnees']['organisation'] === 'Étude Muster', 'demande de démo complète acceptée');
verifier(motif($lettre) === 'ok', 'inscription newsletter acceptée');
$r = valider(['langues' => ['allemand', 'francais'], 'secteur' => 'banques-finance'] + $demande);
verifier($r['ok'] && $r['donnees']['langues'] === 'allemand, francais', 'langues cochées réunies');
$r = valider(['message' => "Ligne 1\r\nLigne 2"] + $demande);
verifier($r['ok'] && $r['donnees']['message'] === "Ligne 1\nLigne 2", 'retours à la ligne gardés dans le message (corps seulement)');
$r = valider(['organisation' => "Étude\r\nBcc: x@exemple.ch"] + $demande);
verifier($r['ok'] && strpos($r['donnees']['organisation'], "\n") === false, "retour à la ligne d'un champ d'une ligne remplacé par une espace");

// Injection d'en-têtes : aucun retour à la ligne dans un champ qui va dans un en-tête
foreach (["\r\n" => 'CR LF', "\n" => 'LF', "\r" => 'CR'] as $saut => $nom) {
    verifier(motif(['nom' => "Muster{$saut}Bcc: victime@exemple.ch"] + $demande) === 'champ:nom', "saut de ligne dans le nom refusé ($nom)");
    verifier(motif(['prenom' => "Anne{$saut}Bcc: victime@exemple.ch"] + $demande) === 'champ:prenom', "saut de ligne dans le prénom refusé ($nom)");
    verifier(motif(['email' => "anne.muster@exemple.ch{$saut}Bcc: victime@exemple.ch"] + $demande) === 'champ:email', "saut de ligne dans l'e-mail refusé ($nom)");
    verifier(nettoyer_entete("Anne{$saut}Bcc: victime@exemple.ch") === null, "nettoyer_entete refuse un saut de ligne ($nom)");
}
verifier(nettoyer_entete("Anne\x00Muster") === null, 'nettoyer_entete refuse un caractère de contrôle');
verifier(nettoyer_entete('  Anne Muster ') === 'Anne Muster', 'nettoyer_entete garde un nom propre, sans espaces autour');

// Robots : champ piège et durée passée sur la page (mesurée dans le navigateur)
verifier(motif(['site_url' => 'https://exemple.ch'] + $demande) === 'piege', 'champ piège rempli rejeté');
verifier(motif(['site_url' => ['x']] + $demande) === 'piege', 'champ piège en tableau rejeté');
verifier(motif(['duree' => '2999'] + $demande) === 'delai', 'envoi en moins de 3 s rejeté (duree 2999 ms)');
verifier(motif(['duree' => '0'] + $demande) === 'delai', 'envoi immédiat (moins de 3 s) rejeté');
verifier(motif(['duree' => '3000'] + $demande) === 'ok', 'envoi à 3 s accepté');
foreach (['abc', '-5', '12.5', '12345678901', "3500\n"] as $duree) {
    verifier(motif(['duree' => $duree] + $demande) === 'delai', 'durée mal formée rejetée : ' . json_encode($duree));
}
verifier(motif(['duree' => ['3500']] + $demande) === 'delai', 'durée en tableau rejetée');
$sans_duree = $demande;
unset($sans_duree['duree']);
verifier(motif($sans_duree) === 'ok', 'sans JavaScript (duree absente) : accepté, le plafond par IP protège');
verifier(motif(['duree' => ''] + $demande) === 'ok', 'sans JavaScript (duree vide) : accepté');

// Validation des champs
verifier(motif(['type' => 'autre'] + $demande) === 'type', 'type inconnu rejeté');
verifier(motif(['email' => 'pas-une-adresse'] + $demande) === 'champ:email', 'e-mail invalide rejeté (filter_var)');
// E-mail : guillemet, chevrons, virgule et point-virgule refusés, même dans une partie locale entre guillemets
foreach (['"anne"@exemple.ch', '"anne,muster"@exemple.ch', '"anne;muster"@exemple.ch', '"anne<muster>"@exemple.ch',
          '"a>b"@exemple.ch', 'anne"muster@exemple.ch', 'anne@exemple.ch,pirate@exemple.ch', 'anne@exemple.ch;pirate@exemple.ch',
          'Anne <anne@exemple.ch>'] as $adresse) {
    verifier(motif(['email' => $adresse] + $demande) === 'champ:email', 'e-mail avec " < > , ou ; refusé : ' . $adresse);
}
verifier(motif(['email' => '"anne,muster"@exemple.ch'] + $lettre) === 'champ:email', 'e-mail avec " < > , ou ; refusé (newsletter)');
verifier(motif(['email' => "anne.o'muster+demo@exemple.ch"] + $demande) === 'ok', 'e-mail ordinaire (apostrophe, plus) accepté');
verifier(motif(['consentement' => ''] + $demande) === 'champ:consentement', 'consentement absent rejeté');
verifier(motif(['consentement' => ''] + $lettre) === 'champ:consentement', 'consentement absent rejeté (newsletter)');
verifier(motif(['organisation' => ''] + $demande) === 'champ:organisation', 'champ obligatoire vide rejeté');
verifier(motif(['nom' => str_repeat('a', 101)] + $demande) === 'champ:nom', 'nom trop long rejeté');
verifier(motif(['nom' => str_repeat('é', 100)] + $demande) === 'ok', 'longueur comptée en caractères, pas en octets');
verifier(motif(['message' => str_repeat('a', 5001)] + $demande) === 'champ:message', 'message trop long rejeté');
verifier(motif(['nom' => ['Muster']] + $demande) === 'champ:nom', 'champ simple reçu en tableau rejeté');
verifier(motif(['langues' => array_fill(0, 11, 'allemand')] + $demande) === 'champ:langues', 'trop de langues rejeté');
verifier(motif(['nom' => "Muster\xC3"] + $demande) === 'champ:nom', 'UTF-8 invalide rejeté');
verifier(!array_key_exists('destinataire', valider(['destinataire' => 'pirate@exemple.ch'] + $demande)['donnees']), 'champ inconnu ignoré (destinataire jamais lu dans la requête)');

// Origine de la requête
verifier(origine_autorisee('https://neur-on.ai', '', 'neur-on.ai'), 'Origin du site accepté');
verifier(origine_autorisee('https://www.neur-on.ai', '', 'neur-on.ai'), 'Origin www accepté');
verifier(origine_autorisee('https://NEUR-ON.AI:443', '', 'neur-on.ai'), 'Origin avec port et majuscules accepté');
verifier(!origine_autorisee('https://exemple.ch', '', 'neur-on.ai'), "Origin d'un autre site refusé");
verifier(!origine_autorisee('https://neur-on.ai.exemple.ch', '', 'neur-on.ai'), 'Origin qui imite le domaine refusé');
verifier(!origine_autorisee('null', '', 'neur-on.ai'), 'Origin « null » refusé');
verifier(!origine_autorisee('https://exemple.ch', 'https://neur-on.ai/fr/contact/', 'neur-on.ai'), 'Origin prioritaire sur Referer');
verifier(origine_autorisee('', 'https://neur-on.ai/fr/contact/', 'neur-on.ai'), 'Referer du site accepté sans Origin');
verifier(!origine_autorisee('', 'https://exemple.ch/page', 'neur-on.ai'), "Referer d'un autre site refusé");
verifier(!origine_autorisee('', '', 'neur-on.ai'), 'sans Origin ni Referer : refusé (un navigateur envoie Origin avec un POST)');

// Plafonds : horloge et état injectés
verifier(reseau_ip('203.0.113.7') === '203.0.113.7', 'IPv4 gardée entière');
verifier(reseau_ip('2001:db8:1:2:3:4:5:6') === '2001:db8:1:2::/64', 'IPv6 ramenée à son réseau /64');
verifier(reseau_ip('::ffff:203.0.113.7') === '203.0.113.7', 'IPv6 qui porte une IPv4 : cette IPv4');
verifier(cle_ip('2001:db8:1:2::1', 'sel') === cle_ip('2001:db8:1:2:ffff:ffff:ffff:ffff', 'sel'), 'IPv6 du même /64 : même clé');
verifier(cle_ip('2001:db8:1:2::1', 'sel') !== cle_ip('2001:db8:1:3::1', 'sel'), 'IPv6 de deux /64 : clés distinctes');
verifier(cle_ip('203.0.113.7', 'sel') !== cle_ip('203.0.113.8', 'sel'), 'IPv4 voisines : clés distinctes');
$cle = cle_ip('203.0.113.7', str_repeat('a', 64));
verifier(strpos($cle, '203.0.113') === false && strlen($cle) === 64, "clé d'IP : empreinte, sans l'adresse");
verifier($cle !== cle_ip('203.0.113.7', str_repeat('b', 64)), "clé d'IP : dépend du sel");
$t = 1760000000;
$etat = [];
$acceptes = 0;
for ($i = 0; $i < 4; $i++) {
    $r = limiter($etat, $cle, $t + $i * 10);
    $etat = $r['etat'];
    $acceptes += $r['accepte'] ? 1 : 0;
}
verifier($acceptes === 3 && !$r['accepte'] && $r['motif'] === 'ip', 'par IP : 3 envois en 10 minutes, le 4e refusé');
verifier(count($etat['ip'][$cle]) === 3 && count($etat['global']) === 3, 'un envoi refusé ne compte pas');
verifier(limiter($etat, cle_ip('198.51.100.1', str_repeat('a', 64)), $t + 60)['accepte'], 'autre IP acceptée');
verifier(limiter($etat, $cle, $t + 600)['accepte'], 'par IP : de nouveau accepté une fois la fenêtre de 10 minutes passée');
verifier(!isset(limiter($etat, 'autre', $t + 4000)['etat']['ip'][$cle]), 'horodatages hors fenêtre oubliés');
// Par IP sur une heure : 3 envois toutes les 10 minutes respectent le plafond court, pas le plafond horaire
$etat = [];
$acceptes = [];
foreach ([0, 10, 20, 700, 710, 720, 1400, 1410] as $decalage) {
    $r = limiter($etat, $cle, $t + $decalage);
    $etat = $r['etat'];
    $acceptes[] = $r['accepte'];
}
verifier($acceptes === [true, true, true, true, true, true, false, false] && $r['motif'] === 'ip', 'par IP : 6 envois par heure, le 7e refusé même hors plafond de 10 minutes');
verifier(!limiter($etat, $cle, $t + 3599)['accepte'], "par IP : toujours refusé avant la fin de l'heure");
verifier(limiter($etat, $cle, $t + 3600)['accepte'], "par IP : de nouveau accepté une fois l'heure passée");
// Une seule adresse ne peut jamais épuiser le plafond global : 100 tentatives réparties sur une heure
$etat = [];
$acceptes = 0;
for ($i = 0; $i < 100; $i++) {
    $r = limiter($etat, $cle, $t + $i * 36);
    $etat = $r['etat'];
    $acceptes += $r['accepte'] ? 1 : 0;
}
verifier($acceptes === PLAFOND_IP_HEURE && count($etat['global']) <= PLAFOND_IP_HEURE, "une seule adresse n'épuise jamais le plafond global : 6 envois sur 100 tentatives en une heure");
verifier(limiter($etat, 'autre-adresse', $t + 3599)['accepte'], 'une autre adresse reste acceptée après ces 100 tentatives');
verifier(PLAFOND_IP_HEURE < PLAFOND_GLOBAL && FENETRE_IP_HEURE >= FENETRE_GLOBALE && PLAFOND_IP <= PLAFOND_IP_HEURE, 'plafonds cohérents : une adresse reste sous le plafond global');
$etat = [];
for ($i = 0; $i < 61; $i++) {
    $r = limiter($etat, 'ip' . $i, $t + $i);
    $etat = $r['etat'];
}
verifier(!$r['accepte'] && $r['motif'] === 'global' && count($etat['global']) === 60, 'global : 60 envois par heure, le 61e refusé');
verifier(limiter($etat, 'ip99', $t + 3600)['accepte'], "global : de nouveau accepté une fois l'heure passée");
verifier(limiter(['ip' => 'corrompu', 'global' => [null, 'x']], $cle, $t)['accepte'], 'état corrompu ignoré');

// Plafonds : fichier verrouillé (stockage injecté)
$fichier = tempnam(sys_get_temp_dir(), 'envoi-test');
$resultats = [];
for ($i = 0; $i < 4; $i++) {
    $resultats[] = compter($fichier, $cle, $t + $i);
}
verifier($resultats === [true, true, true, false], 'compter : fichier partagé entre les requêtes, 4e envoi refusé');
$contenu = (string) file_get_contents($fichier);
verifier(strpos($contenu, $cle) !== false && strpos($contenu, '203.0.113') === false, 'compter : le fichier garde l\'empreinte, jamais l\'IP');
unlink($fichier);
$journal = tempnam(sys_get_temp_dir(), 'envoi-journal');
ini_set('error_log', $journal);
verifier(!compter(sys_get_temp_dir() . '/dossier-absent-' . bin2hex(random_bytes(4)) . '/compteurs.json', $cle, $t), 'compter : fichier impossible à ouvrir, refus');
verifier(strpos((string) file_get_contents($journal), 'compteurs impossibles à ouvrir') !== false, 'compter : ouverture impossible notée au journal');
$fichier = tempnam(sys_get_temp_dir(), 'envoi-test');
file_put_contents($fichier, (string) json_encode(['ip' => [], 'global' => array_fill(0, PLAFOND_GLOBAL, $t)]));
verifier(!compter($fichier, $cle, $t + 1), 'compter : plafond global atteint, refus');
verifier(strpos((string) file_get_contents($journal), 'plafond global atteint') !== false, 'compter : plafond global noté au journal');
file_put_contents($fichier, 'pas du JSON');
verifier(compter($fichier, $cle, $t) && strpos((string) file_get_contents($journal), 'compteurs illisibles') !== false, 'compter : fichier illisible remis à zéro, noté au journal');
unlink($fichier);
ini_restore('error_log');
unlink($journal);
$base = sys_get_temp_dir() . '/envoi-dossier-' . bin2hex(random_bytes(4));
verifier(preparer_dossier($base . '/envoi-limites') && file_get_contents($base . '/envoi-limites/.htaccess') === "Require all denied\n", 'dossier des compteurs créé, fermé par un .htaccess « Require all denied »');
verifier(glob($base . '/envoi-limites/.htaccess.*') === [], '.htaccess écrit par renommage : aucun fichier temporaire laissé');
file_put_contents($base . '/envoi-limites/.htaccess', "# réglage local\n");
verifier(preparer_dossier($base . '/envoi-limites') && file_get_contents($base . '/envoi-limites/.htaccess') === "# réglage local\n", '.htaccess existant gardé');
file_put_contents($base . '/fichier', 'x');
verifier(!preparer_dossier($base . '/fichier/envoi-limites'), 'dossier impossible à créer : faux (envoi refusé, aucun repli)');
array_map('unlink', [$base . '/envoi-limites/.htaccess', $base . '/fichier']);
rmdir($base . '/envoi-limites');
rmdir($base);

// E-mail composé
/** Texte de tous les mots encodés d'un en-tête, décodés et mis bout à bout (RFC 2047, sans dépendre de mbstring). */
function decoder(string $entete): string
{
    preg_match_all('/=\?UTF-8\?B\?([A-Za-z0-9+\/=]*)\?=/', $entete, $m);
    return implode('', array_map('base64_decode', $m[1]));
}

/** Lignes de l'en-tête Reply-To : la première et ses lignes repliées ; la dernière porte l'adresse. */
function reply_to(string $entetes): array
{
    $lignes = [];
    foreach (explode("\r\n", $entetes) as $l) {
        if (strpos($l, 'Reply-To:') === 0 || ($lignes && $l !== '' && $l[0] === ' ')) {
            $lignes[] = $l;
        } elseif ($lignes) {
            break;
        }
    }
    return $lignes;
}

/** Vrai si le nom affiché de Reply-To ne laisse aucun caractère d'adresse en clair et redonne $nom au décodage. */
function nom_sans_clair(array $entete, string $nom): bool
{
    $adresse = array_pop($entete);
    $avant = implode("\r\n", $entete);
    $texte_clair = preg_replace('/=\?UTF-8\?B\?[A-Za-z0-9+\/=]*\?=/', '', substr($avant, strlen('Reply-To: ')));
    return trim($texte_clair) === '' && strpbrk($avant, '<>,@"') === false && decoder($avant) === $nom
        && preg_match('/^ <[^<>,"]+@[^<>,"]+>$/', $adresse) === 1;
}

$r = valider(['message' => "Bonjour,\nune démo ?", 'utm_source' => 'linkedin', 'page_entree' => '/fr/'] + $demande);
$c = composer('demo', $r['donnees'], 'noreply@neur-on.ai');
verifier(mb_decode_mimeheader($c['objet']) === 'Demande de démo', 'objet décodé : « Demande de démo »');
verifier(mb_decode_mimeheader(composer('newsletter', valider($lettre)['donnees'], 'noreply@neur-on.ai')['objet']) === 'Inscription newsletter', 'objet décodé : « Inscription newsletter »');
verifier(strpbrk(composer('newsletter', valider($lettre)['donnees'], 'noreply@neur-on.ai')['objet'], ' ') === false, 'objet entièrement encodé, même en ASCII');
verifier(nom_sans_clair(reply_to($c['entetes']), 'Anne Muster') && strpos($c['entetes'], "\r\n <anne.muster@exemple.ch>") !== false, 'Reply-To : nom ASCII encodé lui aussi, e-mail du visiteur seul en clair');
verifier(strpos($c['entetes'], 'From: =?UTF-8?B?' . base64_encode('Site Neur.on') . '?= <noreply@neur-on.ai>') !== false, 'From : nom encodé, expéditeur donné');
$en_tetes = preg_split('/\r\n(?![ \t])/', $c['entetes']);
verifier(count($en_tetes) === 5 && preg_match('/\r\n(?![ \t]|From:|Reply-To:|MIME-Version:|Content-Type:|Content-Transfer-Encoding:)/', $c['entetes']) === 0, 'exactement cinq en-têtes connus (lignes repliées comprises)');
verifier(stripos($c['entetes'], 'bcc') === false && stripos($c['entetes'], "\nTo:") === false, 'aucun Bcc ni To ajouté');
// Injection dans Reply-To : mots ASCII avant le premier accent (faille de mb_encode_mimeheader)
$attaque = composer('demo', valider(['prenom' => 'Pirate <pirate@exemple.com>,', 'nom' => 'Müller'] + $demande)['donnees'], 'noreply@neur-on.ai');
verifier(nom_sans_clair(reply_to($attaque['entetes']), 'Pirate <pirate@exemple.com>, Müller'), 'nom ASCII avec <, virgule et @ suivi d\'un accent : rien en clair hors de l\'adresse');
verifier(substr_count(implode("\r\n", reply_to($attaque['entetes'])), '@') === 1, 'une seule adresse de réponse');
$guillemets = composer('demo', valider(['nom' => 'Muster" <pirate@exemple.ch>, "x'] + $demande)['donnees'], 'noreply@neur-on.ai');
verifier(nom_sans_clair(reply_to($guillemets['entetes']), 'Anne Muster" <pirate@exemple.ch>, "x'), 'guillemets et adresse dans un nom ASCII : rien en clair');
$virgule = composer('demo', valider(['prenom' => 'Élodie', 'nom' => 'Müller, née Dupont'] + $demande)['donnees'], 'noreply@neur-on.ai');
verifier(nom_sans_clair(reply_to($virgule['entetes']), 'Élodie Müller, née Dupont'), 'virgule légitime dans un nom accentué : gardée, encodée');
// Longueur des lignes : nom de 200 caractères accentués
$long = composer('demo', valider(['prenom' => str_repeat('Élodie ', 14), 'nom' => str_repeat('é', 100)] + $demande)['donnees'], 'noreply@neur-on.ai');
$lignes_reply = reply_to($long['entetes']);
array_pop($lignes_reply);
verifier(count($lignes_reply) > 3 && max(array_map('strlen', $lignes_reply)) <= 75, 'nom encodé en mots de 39 octets : lignes de 75 caractères au plus, préfixe compris');
verifier(nom_sans_clair(reply_to($long['entetes']), trim(str_repeat('Élodie ', 14)) . ' ' . str_repeat('é', 100)), 'nom long retrouvé intact au décodage, sans caractère coupé');
$objet_long = encoder_entete(str_repeat('é', 120));
verifier(max(array_map('strlen', explode("\r\n", 'Subject: ' . $objet_long))) <= 75 && decoder($objet_long) === str_repeat('é', 120), 'objet long : lignes de 75 caractères au plus, préfixe compris');
verifier(encoder_entete('') === '', 'texte vide : rien');
$corps = base64_decode(str_replace("\r\n", '', $c['corps']));
verifier(strpos($corps, "Organisation : Étude Muster\r\n") !== false, 'corps UTF-8 : un champ par ligne');
verifier(strpos($corps, "Votre message :\r\nBonjour,\r\nune démo ?") !== false, 'corps : message en fin, lignes gardées');
verifier(strpos($corps, "Parcours sur le site\r\nPage d'entrée : /fr/\r\nutm_source : linkedin") !== false, 'corps : parcours regroupé');
verifier(max(array_map('strlen', explode("\r\n", $c['corps']))) <= 76, 'corps encodé en lignes de 76 caractères au plus');

// Adresses
verifier(adresse_retour('demo', 'ok') === '/fr/contact/merci/', 'retour démo');
verifier(adresse_retour('newsletter', 'ok') === '/fr/contact/merci/?type=newsletter', 'retour newsletter');
verifier(adresse_retour('demo', 'champs') === '/fr/contact/merci/?erreur=champs', 'retour champ invalide');
verifier(adresse_retour('demo', 'refus') === '/fr/contact/merci/?erreur=refus', 'retour refus, sans détail');
verifier(adresse_retour('newsletter', 'refus') === '/fr/contact/merci/?erreur=refus&type=newsletter', 'retour refus newsletter');
verifier(expediteur('', 'neur-on.ai') === 'noreply@neur-on.ai', 'expéditeur par défaut : noreply@ + domaine du site');
verifier(expediteur('contact@neur-on.ai', 'neur-on.ai') === 'contact@neur-on.ai', 'expéditeur de la configuration');

echo $echecs === 0 ? "\nTous les cas passent.\n" : "\n$echecs cas en échec.\n";
exit($echecs === 0 ? 0 : 1);
