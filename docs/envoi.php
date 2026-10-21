<?php
/*
 * Envoi des formulaires du site Neur.on : demande de démo et inscription à la lettre d'information.
 * Hébergement : Hostpoint (Apache, PHP 8, extension mbstring). Aucun service tiers : la fonction mail() du serveur.
 *
 * Le build (outils/envoi.py) copie ce fichier à la racine du site et y écrit le destinataire et l'expéditeur lus
 * dans src/data/config.json. Le destinataire ne vient jamais de la requête.
 *
 * Contrôles, dans l'ordre : méthode POST ; champ piège ; origine de la requête (en-tête Origin, sinon Referer : l'un
 * des deux est exigé) ; durée passée sur la page (champ duree, mesuré par suivi.js) ; champs (e-mail sans guillemet,
 * chevron, virgule ni point-virgule) ; plafonds d'envoi par adresse IP (empreinte salée ; IPv6 ramenée à son réseau
 * /64), sur 10 minutes et sur une heure, et pour tout le site, dans un fichier verrouillé par flock.
 * Le nom du visiteur et l'objet sont entièrement encodés en mots base64 (RFC 2047) : rien n'y reste interprétable.
 *
 * Réponses (aucune donnée saisie n'y est renvoyée) :
 * - 405 à toute autre méthode que POST ;
 * - 303 vers /fr/contact/merci/ (avec ?type=newsletter pour la lettre d'information) après l'envoi ; de même quand
 *   le champ piège est rempli : un robot ne reçoit aucun signal, et rien n'est envoyé ;
 * - 303 vers /fr/contact/merci/?erreur=champs si un champ est invalide ;
 * - 303 vers /fr/contact/merci/?erreur=refus pour tout autre refus (origine, durée, type, plafond) ou si le serveur
 *   n'a pas pu envoyer l'e-mail, sans détail. Avec &type=newsletter pour la lettre d'information.
 *
 * Les fonctions pures (nettoyer_entete, valider, origine_autorisee, reseau_ip, cle_ip, limiter, encoder_entete,
 * composer, adresse_retour, expediteur), ainsi que compter et preparer_dossier sur un fichier ou un dossier donnés,
 * sont testées par tests/test_envoi.php : php tests/test_envoi.php
 */
declare(strict_types=1);

// Domaine du site : origine admise des envois (avec ou sans www) et expéditeur par défaut (noreply@DOMAINE).
// Pour un essai sur un autre domaine, par exemple un domaine provisoire de Hostpoint, le changer ici.
const DOMAINE = 'neur-on.ai';
// Destinataire, fixe : écrit par le build depuis src/data/config.json (clé « destinataire »).
const DESTINATAIRE = 'team@corrext.com';
// Expéditeur (en-tête From et adresse d'enveloppe), écrit par le build depuis la configuration (clé « expediteur »).
// Vide : noreply@ suivi de DOMAINE. Modifiable ici : de préférence une adresse couverte par l'enregistrement SPF.
const EXPEDITEUR = '';
// Durée minimale passée sur la page avant l'envoi, en millisecondes (champ duree, mesuré dans le navigateur).
const DELAI_MINIMAL = 3000;
// Plafonds contre l'envoi en masse. Par adresse IP : PLAFOND_IP envois en 10 minutes et PLAFOND_IP_HEURE en une
// heure ; pour tout le site : PLAFOND_GLOBAL en une heure. Une seule adresse ne peut jamais épuiser le plafond
// global : sur la même heure, elle n'obtient au plus que PLAFOND_IP_HEURE envois, très en dessous de PLAFOND_GLOBAL.
const PLAFOND_IP = 3;
const FENETRE_IP = 600;          // secondes
const PLAFOND_IP_HEURE = 6;
const FENETRE_IP_HEURE = 3600;   // secondes
const PLAFOND_GLOBAL = 60;
const FENETRE_GLOBALE = 3600;    // secondes
// Dossier des compteurs et du sel, hors de la racine web, fermé par un .htaccess écrit à sa création.
// Inutilisable : envoi refusé, avec une ligne dans le journal du serveur.
const DOSSIER_LIMITES = __DIR__ . '/../envoi-limites';
// Octets de texte par mot encodé d'un en-tête : 39 octets donnent 52 caractères base64, soit 64 avec
// « =?UTF-8?B?…?= » ; la première ligne, préfixe « Reply-To: » compris, tient en 75 caractères.
const OCTETS_PAR_MOT = 39;
// Page de réponse (chemin absolu du site).
const MERCI = '/fr/contact/merci/';

// Champs acceptés : nom => [longueur maximale en caractères, libellé dans l'e-mail]. Tout autre champ est ignoré.
const CHAMPS = [
    'prenom' => [100, 'Prénom'],
    'nom' => [100, 'Nom'],
    'email' => [254, 'E-mail professionnel'],
    'organisation' => [200, 'Organisation'],
    'secteur' => [50, 'Secteur'],
    'fonction' => [50, 'Fonction'],
    'taille' => [50, "Taille de l'organisation"],
    'langues' => [200, 'Langues concernées'],
    'volume' => [50, 'Volume mensuel approximatif'],
    'sujet' => [300, 'Ce que vous traduisez le plus souvent'],
    'message' => [5000, 'Votre message'],
    'consentement' => [3, 'Consentement au traitement des données'],
    'page_entree' => [500, "Page d'entrée"],
    'page_origine' => [500, "Page d'origine"],
    'utm_source' => [200, 'utm_source'],
    'utm_medium' => [200, 'utm_medium'],
    'utm_campaign' => [200, 'utm_campaign'],
    'utm_term' => [200, 'utm_term'],
    'utm_content' => [200, 'utm_content'],
];
// Champs du parcours, regroupés en fin d'e-mail.
const PARCOURS = ['page_entree', 'page_origine', 'utm_source', 'utm_medium', 'utm_campaign', 'utm_term', 'utm_content'];
// Champs obligatoires par type de formulaire.
const OBLIGATOIRES = [
    'demo' => ['prenom', 'nom', 'email', 'organisation', 'fonction', 'consentement'],
    // demande de documentation API (bouton de la page API et on-premises) : le formulaire de démo, autre objet
    'documentation' => ['prenom', 'nom', 'email', 'organisation', 'fonction', 'consentement'],
    'newsletter' => ['email', 'consentement'],
];
// Champs qui entrent dans un en-tête de l'e-mail (Reply-To) : aucun retour à la ligne admis.
const ENTETES = ['prenom', 'nom', 'email'];
// Caractères refusés dans l'e-mail, même quand FILTER_VALIDATE_EMAIL les admet (partie locale entre guillemets) :
// ils permettraient d'écrire un nom affiché ou une seconde adresse dans l'en-tête Reply-To.
const EMAIL_INTERDITS = '"<>,;';
// Objet de l'e-mail par type de formulaire.
const OBJETS = ['demo' => 'Demande de démo', 'documentation' => 'Demande de documentation API', 'newsletter' => 'Inscription newsletter'];
// Cases « Langues concernées » : au plus autant de valeurs.
const LANGUES_MAX = 10;


/** Vrai si la chaîne est de l'UTF-8 valide. */
function utf8_valide(string $texte): bool
{
    return preg_match('//u', $texte) === 1;
}

/**
 * Valeur destinée à un en-tête de l'e-mail : sans espaces autour, ou null si elle contient un retour à la ligne
 * (CR, LF) ou un autre caractère de contrôle, qui permettrait d'ajouter un en-tête (Bcc, etc.).
 */
function nettoyer_entete(string $valeur): ?string
{
    if (preg_match('/[\x00-\x1F\x7F]/', $valeur) === 1) {
        return null;
    }
    return trim($valeur);
}

/**
 * Contrôle d'une demande. $post : champs reçus ($_POST).
 * Renvoie ['ok' => bool, 'motif' => string, 'type' => 'demo'|'documentation'|'newsletter', 'donnees' => [nom => valeur]].
 * Motifs d'échec : piege (champ piège rempli), type (type inconnu), delai (duree mal formée ou inférieure à
 * DELAI_MINIMAL ; duree absente ou vide, sans JavaScript, est admise), champ:<nom> (champ manquant, trop long, mal
 * formé ou contenant un retour à la ligne interdit ; e-mail contenant un caractère de EMAIL_INTERDITS).
 */
function valider(array $post): array
{
    $type = (isset($post['type']) && is_string($post['type']) && array_key_exists($post['type'], OBLIGATOIRES)) ? $post['type'] : '';
    $echec = static function (string $motif) use ($type): array {
        return ['ok' => false, 'motif' => $motif, 'type' => $type === '' ? 'demo' : $type, 'donnees' => []];
    };

    $piege = $post['site_url'] ?? '';
    if (!is_string($piege) || $piege !== '') {
        return $echec('piege');
    }
    if ($type === '') {
        return $echec('type');
    }
    $duree = $post['duree'] ?? '';
    if (!is_string($duree) || ($duree !== '' && (preg_match('/^\d{1,10}\z/', $duree) !== 1 || (int) $duree < DELAI_MINIMAL))) {
        return $echec('delai');
    }

    $donnees = [];
    foreach (CHAMPS as $nom => $definition) {
        $brut = $post[$nom] ?? '';
        if ($nom === 'langues' && is_array($brut)) {
            if (count($brut) > LANGUES_MAX) {
                return $echec('champ:langues');
            }
            foreach ($brut as $case) {
                if (!is_string($case)) {
                    return $echec('champ:langues');
                }
            }
            $brut = implode(', ', $brut);
        }
        if (!is_string($brut) || !utf8_valide($brut)) {
            return $echec('champ:' . $nom);
        }
        if (in_array($nom, ENTETES, true)) {
            $valeur = nettoyer_entete($brut);
            if ($valeur === null) {
                return $echec('champ:' . $nom);
            }
        } elseif ($nom === 'message') {
            // Texte libre : retours à la ligne gardés (corps de l'e-mail seulement), autres caractères de contrôle ôtés
            $valeur = trim(str_replace(["\r\n", "\r"], "\n", (string) preg_replace('/[\x00-\x08\x0B\x0C\x0E-\x1F\x7F]/', '', $brut)));
        } else {
            // Champ d'une ligne : tout caractère de contrôle devient une espace
            $valeur = trim((string) preg_replace('/[\x00-\x1F\x7F]+/', ' ', $brut));
        }
        if (mb_strlen($valeur, 'UTF-8') > $definition[0]) {
            return $echec('champ:' . $nom);
        }
        if ($valeur === '' && in_array($nom, OBLIGATOIRES[$type], true)) {
            return $echec('champ:' . $nom);
        }
        $donnees[$nom] = $valeur;
    }
    if (filter_var($donnees['email'], FILTER_VALIDATE_EMAIL) === false || strpbrk($donnees['email'], EMAIL_INTERDITS) !== false) {
        return $echec('champ:email');
    }
    if ($donnees['consentement'] !== 'oui') {
        return $echec('champ:consentement');
    }
    return ['ok' => true, 'motif' => '', 'type' => $type, 'donnees' => $donnees];
}

/**
 * Vrai si la requête vient du site : l'en-tête Origin, sinon Referer, désigne DOMAINE ou www.DOMAINE.
 * Sans aucun des deux en-têtes (chaînes vides), la requête est refusée : les navigateurs actuels envoient Origin avec
 * un POST, son absence trahit un script. « Origin: null » est refusé.
 */
function origine_autorisee(string $origin, string $referer, string $domaine): bool
{
    $source = $origin !== '' ? $origin : $referer;
    if ($source === '') {
        return false;
    }
    $hote = parse_url($source, PHP_URL_HOST);
    if (!is_string($hote)) {
        return false;
    }
    $hote = strtolower($hote);
    return $hote === $domaine || $hote === 'www.' . $domaine;
}

/**
 * Adresse comptée pour les plafonds : une IPv4 entière ; une IPv6 ramenée à son réseau /64 (un même abonné en
 * reçoit souvent un bloc entier) ; une IPv6 qui porte une IPv4 (::ffff:a.b.c.d) ramenée à cette IPv4.
 */
function reseau_ip(string $ip): string
{
    if (filter_var($ip, FILTER_VALIDATE_IP, FILTER_FLAG_IPV6) === false) {
        return $ip;
    }
    $octets = (string) inet_pton($ip);
    if (substr($octets, 0, 12) === str_repeat("\0", 10) . "\xff\xff") {
        return (string) inet_ntop(substr($octets, 12));
    }
    return (string) inet_ntop(substr($octets, 0, 8) . str_repeat("\0", 8)) . '/64';
}

/** Clé d'une adresse IP dans les compteurs : empreinte salée de son réseau, l'adresse n'est jamais écrite. */
function cle_ip(string $ip, string $sel): string
{
    return hash_hmac('sha256', reseau_ip($ip), $sel);
}

/**
 * Plafonds d'envoi, sans effet de bord. $etat : ['ip' => [cle => [horodatages]], 'global' => [horodatages]] ;
 * $maintenant : heure en secondes. Les horodatages sortis de leur fenêtre sont oubliés (une heure pour une adresse,
 * FENETRE_GLOBALE pour le site). Le plafond de l'adresse est contrôlé d'abord : PLAFOND_IP en FENETRE_IP, puis
 * PLAFOND_IP_HEURE en FENETRE_IP_HEURE ; puis le plafond global. Renvoie
 * ['accepte' => bool, 'motif' => '' | 'ip' | 'global', 'etat' => état mis à jour] ; un envoi accepté est compté,
 * un envoi refusé ne l'est pas.
 */
function limiter(array $etat, string $cle, int $maintenant): array
{
    $recents = static function ($liste, int $fenetre) use ($maintenant): array {
        return array_values(array_filter(is_array($liste) ? $liste : [], static function ($t) use ($maintenant, $fenetre): bool {
            return is_int($t) && $t > $maintenant - $fenetre && $t <= $maintenant;
        }));
    };
    $ips = [];
    foreach ((is_array($etat['ip'] ?? null) ? $etat['ip'] : []) as $c => $liste) {
        $garde = $recents($liste, max(FENETRE_IP, FENETRE_IP_HEURE));
        if ($garde) {
            $ips[(string) $c] = $garde;
        }
    }
    $global = $recents($etat['global'] ?? [], FENETRE_GLOBALE);
    $adresse = $ips[$cle] ?? [];
    $adresse_pleine = count($recents($adresse, FENETRE_IP)) >= PLAFOND_IP
        || count($recents($adresse, FENETRE_IP_HEURE)) >= PLAFOND_IP_HEURE;
    $motif = $adresse_pleine ? 'ip' : (count($global) >= PLAFOND_GLOBAL ? 'global' : '');
    if ($motif === '') {
        $ips[$cle][] = $maintenant;
        $global[] = $maintenant;
    }
    return ['accepte' => $motif === '', 'motif' => $motif, 'etat' => ['ip' => $ips, 'global' => $global]];
}

/**
 * Compte un envoi dans le fichier des compteurs, verrouillé par flock pendant la lecture et l'écriture.
 * Vrai si l'envoi reste sous les plafonds. Ouverture, verrou ou écriture impossibles : refus, avec une ligne dans le
 * journal du serveur (jamais d'envoi sans compteur). Plafond global atteint : refus, avec une ligne dans le journal.
 */
function compter(string $fichier, string $cle, int $maintenant): bool
{
    $f = @fopen($fichier, 'c+');
    if ($f === false) {
        error_log('envoi.php : compteurs impossibles à ouvrir, envoi refusé');
        return false;
    }
    try {
        if (!flock($f, LOCK_EX)) {
            error_log('envoi.php : compteurs impossibles à verrouiller, envoi refusé');
            return false;
        }
        $contenu = (string) stream_get_contents($f);
        $etat = json_decode($contenu, true);
        if ($contenu !== '' && !is_array($etat)) {
            error_log('envoi.php : compteurs illisibles, remis à zéro');
        }
        $resultat = limiter(is_array($etat) ? $etat : [], $cle, $maintenant);
        $json = (string) json_encode($resultat['etat']);
        $ecrit = ftruncate($f, 0) && rewind($f) && fwrite($f, $json) === strlen($json) && fflush($f);
        flock($f, LOCK_UN);
        if (!$ecrit) {
            error_log('envoi.php : compteurs impossibles à écrire, envoi refusé');
            return false;
        }
        if ($resultat['motif'] === 'global') {
            error_log('envoi.php : plafond global atteint (' . PLAFOND_GLOBAL . ' envois par heure), envoi refusé');
        }
        return $resultat['accepte'];
    } finally {
        fclose($f);
    }
}

/**
 * Prépare le dossier des compteurs : le crée au besoin, y écrit un .htaccess « Require all denied » s'il manque.
 * Le .htaccess est écrit dans un fichier temporaire du même dossier, puis renommé (rename est atomique) : Apache ne
 * lit jamais un fichier à moitié écrit, et deux requêtes simultanées écrivent le même contenu.
 * Faux si le dossier est inutilisable (aucun repli : l'envoi sera refusé). @ : aucun avertissement avant les en-têtes.
 */
function preparer_dossier(string $dossier): bool
{
    if (!@is_dir($dossier) && !@mkdir($dossier, 0700, true)) {
        return false;
    }
    $htaccess = $dossier . '/.htaccess';
    if (!@is_file($htaccess)) {
        $regle = "Require all denied\n";
        $temporaire = $htaccess . '.' . bin2hex(random_bytes(8)) . '.tmp';
        if (@file_put_contents($temporaire, $regle) !== strlen($regle) || !@rename($temporaire, $htaccess)) {
            @unlink($temporaire);
            return false;
        }
    }
    return @is_writable($dossier);
}

/** Sel des empreintes d'IP : tiré au hasard une fois, gardé dans le dossier des compteurs. */
function sel(string $dossier): ?string
{
    $fichier = $dossier . '/sel';
    $f = @fopen($fichier, 'x');
    if ($f !== false) {
        fwrite($f, bin2hex(random_bytes(32)));
        fclose($f);
    }
    $sel = @file_get_contents($fichier);
    return is_string($sel) && strlen($sel) === 64 ? $sel : null;
}

/**
 * Texte d'en-tête entièrement encodé en mots base64 (RFC 2047), même en ASCII : aucun caractère n'y reste
 * interprétable (<, >, @, virgule, guillemet). Morceaux de OCTETS_PAR_MOT octets au plus, découpés par mb_str_split
 * sans couper un caractère, séparés par CRLF et une espace : chaque ligne tient en 75 caractères.
 */
function encoder_entete(string $texte): string
{
    $mots = [];
    $morceau = '';
    foreach (mb_str_split($texte, 1, 'UTF-8') as $caractere) {
        if ($morceau !== '' && strlen($morceau) + strlen($caractere) > OCTETS_PAR_MOT) {
            $mots[] = '=?UTF-8?B?' . base64_encode($morceau) . '?=';
            $morceau = '';
        }
        $morceau .= $caractere;
    }
    if ($morceau !== '') {
        $mots[] = '=?UTF-8?B?' . base64_encode($morceau) . '?=';
    }
    return implode("\r\n ", $mots);
}

/**
 * E-mail d'une demande validée : ['objet' => ..., 'corps' => ..., 'entetes' => ...], prêts pour mail().
 * Corps en texte UTF-8 (base64), qui liste les champs remplis ; Reply-To : l'e-mail du visiteur ; From : $expediteur.
 */
function composer(string $type, array $donnees, string $expediteur): array
{
    $lignes = [OBJETS[$type] . ' envoyée depuis le site.', ''];
    foreach (CHAMPS as $nom => $definition) {
        $valeur = $donnees[$nom] ?? '';
        if ($valeur !== '' && $nom !== 'message' && !in_array($nom, PARCOURS, true)) {
            $lignes[] = $definition[1] . ' : ' . $valeur;
        }
    }
    if (($donnees['message'] ?? '') !== '') {
        array_push($lignes, '', CHAMPS['message'][1] . ' :', $donnees['message']);
    }
    $parcours = [];
    foreach (PARCOURS as $nom) {
        if (($donnees[$nom] ?? '') !== '') {
            $parcours[] = CHAMPS[$nom][1] . ' : ' . $donnees[$nom];
        }
    }
    if ($parcours) {
        array_push($lignes, '', 'Parcours sur le site', ...$parcours);
    }
    $corps = str_replace("\n", "\r\n", implode("\n", $lignes) . "\n");

    $nom = trim(($donnees['prenom'] ?? '') . ' ' . ($donnees['nom'] ?? ''));
    $entetes = [
        'From: ' . encoder_entete('Site Neur.on') . ' <' . $expediteur . '>',
        // Nom entièrement encodé, adresse seule en clair sur sa ligne repliée
        'Reply-To: ' . ($nom !== '' ? encoder_entete($nom) . "\r\n " : '') . '<' . $donnees['email'] . '>',
        'MIME-Version: 1.0',
        'Content-Type: text/plain; charset=UTF-8',
        'Content-Transfer-Encoding: base64',
    ];
    return [
        'objet' => encoder_entete(OBJETS[$type]),
        'corps' => rtrim(chunk_split(base64_encode($corps), 76, "\r\n")),
        'entetes' => implode("\r\n", $entetes),
    ];
}

/** Adresse de la page de réponse (redirection 303). $statut : ok, champs (champ invalide) ou refus (tout autre refus). */
function adresse_retour(string $type, string $statut): string
{
    $parametres = [];
    if ($statut !== 'ok') {
        $parametres[] = 'erreur=' . ($statut === 'champs' ? 'champs' : 'refus');
    }
    if ($type === 'newsletter') {
        $parametres[] = 'type=newsletter';
    }
    return MERCI . ($parametres ? '?' . implode('&', $parametres) : '');
}

/** Expéditeur : celui de la configuration, sinon noreply@ suivi du domaine du site. */
function expediteur(string $configure, string $domaine): string
{
    return $configure !== '' ? $configure : 'noreply@' . $domaine;
}

/** Redirection 303 vers une page du site. */
function repondre(string $adresse): void
{
    http_response_code(303);
    header('Location: ' . $adresse);
}

/** Traitement d'une requête reçue par le serveur. */
function traiter(): void
{
    header('Cache-Control: no-store');
    if (($_SERVER['REQUEST_METHOD'] ?? '') !== 'POST') {
        http_response_code(405);
        header('Allow: POST');
        return;
    }
    $resultat = valider($_POST);
    $type = $resultat['type'];
    if ($resultat['motif'] === 'piege') {
        repondre(adresse_retour($type, 'ok'));
        return;
    }
    if (!origine_autorisee((string) ($_SERVER['HTTP_ORIGIN'] ?? ''), (string) ($_SERVER['HTTP_REFERER'] ?? ''), DOMAINE)) {
        repondre(adresse_retour($type, 'refus'));
        return;
    }
    if (!$resultat['ok']) {
        repondre(adresse_retour($type, strpos($resultat['motif'], 'champ:') === 0 ? 'champs' : 'refus'));
        return;
    }
    $sel = preparer_dossier(DOSSIER_LIMITES) ? sel(DOSSIER_LIMITES) : null;
    if ($sel === null) {
        error_log('envoi.php : dossier des compteurs inutilisable, envoi refusé');
        repondre(adresse_retour($type, 'refus'));
        return;
    }
    if (!compter(DOSSIER_LIMITES . '/compteurs.json', cle_ip((string) ($_SERVER['REMOTE_ADDR'] ?? ''), $sel), time())) {
        repondre(adresse_retour($type, 'refus'));
        return;
    }
    $expediteur = expediteur(EXPEDITEUR, DOMAINE);
    $reussi = false;
    if (filter_var(DESTINATAIRE, FILTER_VALIDATE_EMAIL) !== false && filter_var($expediteur, FILTER_VALIDATE_EMAIL) !== false) {
        $courriel = composer($type, $resultat['donnees'], $expediteur);
        $reussi = mail(DESTINATAIRE, $courriel['objet'], $courriel['corps'], $courriel['entetes'], '-f' . $expediteur);
    }
    if (!$reussi) {
        error_log('envoi.php : e-mail non envoyé (destinataire, expéditeur ou fonction mail() du serveur)');
    }
    repondre(adresse_retour($type, $reussi ? 'ok' : 'refus'));
}

// Exécuté seulement comme script appelé par le serveur, pas quand un test inclut ce fichier.
if (realpath((string) (get_included_files()[0] ?? '')) === __FILE__) {
    traiter();
}
