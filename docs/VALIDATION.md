# Vérification finale du 11 novembre 2026

## Complément : hébergement gratuit

Budget demandé : 0 €. Même module Python, stockage PostgreSQL et Supabase privé en option, conservation du mode SQLite local. Les secrets sont exclus des pages publiques ; schéma PostgreSQL privé avec RLS, bucket privé, verrou transactionnel des écritures, contrôle des deux conditions de délivrance et numéros conservés. Le profil éphémère refuse de démarrer sans les deux stockages distants.

Suite après ces ajouts : **66 tests exécutés, 64 réussis et 2 ignorés sous Windows** (permissions POSIX et création de liens symboliques). Les 22 tests précédents restent réussis. Les nouveaux contrôles couvrent les adaptateurs PostgreSQL et stockage, la reprise des cartes distantes, les fichiers temporaires, les secrets, le refus d’un repli local et l’initialisation unique de l’administrateur. Les appels Supabase sont simulés.

Contrôle PostgreSQL supplémentaire : un moteur PostgreSQL WASM local avec protocole TCP et psycopg a exécuté les migrations, la création d’un compte de test, la demande avec photo, la validation puis le paiement, la réservation du numéro et le PDF recto-verso. Le redémarrage avec un dossier local neuf a retrouvé le dossier et le numéro. Les fichiers distants étaient simulés en mémoire ; aucun appel vers un projet Supabase réel n’a été effectué. Ce test ne vaut pas validation de la concurrence d’un serveur PostgreSQL cloud.

Les offres gratuites, les limites et les accès manquants sont décrits dans [RENDER.md](RENDER.md). Aucun déploiement cloud n’a été effectué.

Mise à jour de préparation à la publication : **22 tests réussis** après correction du démarrage CLI Waitress sans proxy. Le formulaire local est accessible avec la commande documentée. Les paramètres GitHub Pages ont désormais été consultés : publication depuis `main` et `/ (root)`, domaine `www.lanatureetlhumain.org`, DNS validés et HTTPS forcé. Le passage à GitHub Actions reste nécessaire avant intégration sur `main`. Les sources sont préparées sur `codex/adhesion-en-ligne` pour leur transfert au dépôt ; aucune mise en ligne du module n’est effectuée. Les mentions de travail non committé ci-dessous décrivent l’étape de vérification antérieure au transfert.

## Base et publication

Travail dans `site-web/`, branche `codex/adhesion-en-ligne`. Après récupération du distant, la branche a été avancée de `ecb0626` à **`82f0ad0`**, dernière version observée de `origin/main`. Les changements locaux ont été sauvegardés dans un stash, puis réappliqués. Le conflit dans le dictionnaire de traduction a été résolu en conservant le nouveau texte distant et l’entrée Adhérer. Le stash de précaution est conservé. Aucun fichier n’est en conflit ; aucun commit, push ou déploiement de cette intervention.

La section don, le contenu institutionnel récent et les coordonnées de Marseille sont conservés. La comparaison du texte visible avec `origin/main` confirme son identité, hormis le lien Adhérer ajouté et la casse normalisée du slogan. `CNAME` reste `www.lanatureetlhumain.org`. Le logo, les trois sujets photographiques, les crédits, la navigation et le formulaire de contact sont conservés.

Contrôle public : accueil HTTP 200, domaine sans www redirigé vers www, DNS GitHub Pages corrects. **`/adhesion/` retourne HTTP 404 : le module n’est pas publié.** L’accueil public annonce 10 982 788 octets. Le transfert compressé testé a expiré après 45 secondes avec environ 1,74 Mo reçus, malgré un premier octet à 0,78 seconde. Le test constate une lenteur sur la connexion utilisée, sans en attribuer toute la cause à l’opérateur.

## Corrections de cette passe

- Intégration des deux commits distants récents sans les écraser.
- Photos extraites et optimisées dans `assets/` : HTML local **73 702 octets**, images **1 163 184 octets**, environ 89 % de moins au total. Les proportions, sujets et crédits sont conservés. Le logo conserve ses octets d’origine, sans réencodage.
- Langue conservée entre accueil et formulaire ; notice anglaise, titre et texte alternatif de l’aperçu photo traduits. Redirections vers les routes avec slash pour préserver les ressources relatives.
- Contrôle de capacité des noms, catégories et fonctions avant réservation du numéro. Correction de fonction possible après échec tant qu’aucun PDF n’a été délivré, avec conservation du numéro et historique. Une carte produite reste non modifiable par cette interface.
- Migrations sérialisées ; reprise de la concurrence lors de l’activation WAL de SQLite.
- État du message et du membre relu avant transport email, coordination avec refus, protection contre les anciennes réservations et prolongation du lien lors d’un envoi retardé. Un accès révoqué n’est pas recréé. Le compromis du verrou SQLite pendant SMTP est documenté.
- Publication Pages par liste publique explicite, ressources d’accueil incluses ; modèle systemd et procédure d’hébergement ajoutés.

## Résultats des tests

**21 tests réussis**, avec `python -m unittest discover -s tests -v`. Python 3.12.14, Pillow 13.0.0, ReportLab 4.4.9, pypdf 6.21.4 ; Waitress 3.0.2 installé dans l’environnement local ignoré.

Couverture : validation et paiement dans les deux ordres, absence de numéro/carte après une seule condition, fonction réservée à l’association, doublons, consentement, uploads, nettoyage EXIF, montants, collisions de fiches, six attributions simultanées de numéros, persistance, PDF, échecs et reprises, contrôle des accès, CSRF/origine, sessions, déconnexion, refus, liens révoqués et emails différés. Les neuf tests emails utilisent des transports simulés et neutralisent les connexions SMTP réelles.

Cinq séries supplémentaires de huit initialisations simultanées de bases neuves ont réussi après correction. Syntaxe de tous les scripts JavaScript applicatifs et du script d’accueil vérifiée. `git diff --check` réussi. La préparation Pages produit **22 fichiers publics**, sans service serveur, tests, base, photo de candidat, carte, `.env` ou données de QA. Aucun fichier privé ne figure parmi les fichiers Git suivis ou non ignorés.

## Navigateur et PDF

Parcours réellement effectué sous **Waitress local** : lien Adhérer, formulaire en anglais, informations et profession déclarée, photo de test avec aperçu, consentement, envoi, connexion administrateur, consultation du dossier et de la photo, fonction « Responsable Environnement et Climat », approbation, constat de l’absence de numéro et de paiement, paiement manuel fictif, création de `ANH-2026-001`, aperçu PDF.js avec deux canvas, téléchargement effectif et déconnexion.

Le montant de 5 000 KMF, Amina Dossier Test, la référence de reçu, la silhouette et le compte sont **fictifs**. Le stockage reste dans `.qa/`, hors sources publiables. Ces essais ne configurent aucun tarif réel.

Bureau observé à environ 1 265 px. Mobile contrôlé à **390 × 844 px** pour formulaire, administration, carte et accueil anglais : aucun débordement horizontal. Retour de langue et notice anglaise vérifiés. Photos et logos chargés, formulaire de contact présent avec endpoint vide. Aucune erreur ou alerte JavaScript relevée dans la session contrôlée. Il ne s’agit pas d’un test sur appareil physique ni de tous les moteurs mobiles.

Le PDF téléchargé contient **deux pages de 85,60 × 53,98 mm**. Extraction pypdf, rendu Poppler à 300 dpi et inspection visuelle effectués. Photo fictive, nom, fonction, numéro, dates 11.11.2026 et 11.11.2027, logo et slogan sont lisibles. La profession déclarée est absente. Signature simulée explicitement désignée. Le QR du verso a été décodé : **`https://www.lanatureetlhumain.org/`**. Les tests vérifient aussi le refus de téléchargements non autorisés et la révocation.

**Le gabarit reste provisoire.** La maquette approuvée n’est ni fournie ni présente dans le dépôt distant actuel. Aucune conformité graphique à cette maquette ni validation d’impression en série n’est revendiquée.

## Limites et prochaine mise en service

Voir [la procédure de déploiement](DEPLOIEMENT.md) : serveur Python unique, disque privé persistant, sauvegarde/restauration, sous-domaine et HTTPS, paramètres réels du droit, catégories, validité, compte administrateur, signature éventuelle et maquette approuvée. Aucun SMTP configuré, aucun email réel envoyé, aucun prestataire de paiement ajouté.

Le parcours GitHub Pages vers le futur sous-domaine API, les cookies HTTPS, le reverse proxy et le certificat restent à tester sur l’hébergement réel. Aucun accès à cette infrastructure ou au DNS du sous-domaine n’a été fourni ou utilisé. Les paramètres Pages doivent être vérifiés avant publication. Les fichiers sont intégrés localement au dossier du dépôt, sans nouveau commit ni envoi au distant. **Le fonctionnement local ne vaut pas mise en ligne.**

---

# Historique : première vérification locale du 11 novembre 2026

Les constats ci-dessous décrivent la passe initiale et sont remplacés par le bilan final ci-dessus, notamment pour la base distante, Waitress, le nombre de tests et le contrôle mobile.

Base de travail : copie locale du dépôt `youssoufben269/lanatureetlhumain-site`, commit `ecb0626`. La branche distante n’a pas pu être récupérée. Aucun commit, push ni déploiement public n’a été réalisé.

**9 tests d’intégration réussis**, avec le runtime Python 3.12.14, Pillow 13.0.0 et ReportLab 4.4.9. Vérification syntaxique des scripts JavaScript et `git diff --check` réussies. Le serveur de production Waitress n’est pas installé dans ce runtime : le parcours HTTP a été vérifié avec le serveur local WSGI, pas sous l’hébergement final.

Parcours réellement effectué dans le navigateur : formulaire public, photo JPEG de test, consentement, envoi, connexion administrateur, consultation de la photo, attribution de « Responsable Environnement et Climat », approbation, confirmation manuelle d’un paiement fictif, création de `ANH-2026-001`, affichage des deux faces par PDF.js, puis déconnexion. Aucune erreur JavaScript détectée sur ce parcours ni sur l’accueil. La bascule FR/EN du formulaire est vérifiée. L’accueil conserve ses rubriques et son formulaire de contact. Aucun débordement horizontal détecté au viewport de bureau contrôlé. Les règles CSS mobiles sont présentes ; le contrôle effectif d’un viewport étroit reste à effectuer sur le navigateur/hébergement cible.

La demande de démonstration utilise une identité fictive, une silhouette portant « PHOTO TEST » et un montant **fictif** de 5 000 KMF. Ces valeurs ne configurent pas le service livré. Les données, sessions, mots de passe et fichiers privés de démonstration sont exclus des sources transférées et de l’archive.

Le PDF de démonstration a été rendu à 300 dpi et les deux faces inspectées. `pdfinfo` et les tests confirment deux pages ID-1 de 85,60 × 53,98 mm. Le nom, la fonction attribuée, le numéro, les dates, le logo et le slogan sont lisibles. Les textes et le QR sont vectoriels. La photo est à une résolution suffisante pour ce format. La signature simulée est explicitement identifiée.

Restent avant publication : comparaison avec le dépôt distant à jour, hébergement Python et HTTPS, stockage privé persistant, paramètres réels du droit, catégories et validité, création du compte administrateur de l’association, SMTP si souhaité, rapprochement du gabarit avec la maquette validée. Le QR actuel ouvre le site officiel ; la vérification individuelle reste désactivée.
