# Module d’adhésion, administration et cartes

**Mode publié : formulaire avec envoi direct Google Apps Script et administration locale.** Suivre [PRISE_EN_MAIN.md](PRISE_EN_MAIN.md) et [ENVOI_DIRECT_GOOGLE.md](ENVOI_DIRECT_GOOGLE.md). Le build Pages utilise le mode `google` lorsque `googleEndpoint` est renseigné ; le mode email manuel reste un retour arrière possible. L’administration et les cartes restent privées sur l’ordinateur. Les instructions d’hébergement ci-dessous concernent une activation distante éventuelle.

Le site et le module appartiennent au même dépôt. La demande est accessible à `/adhesion/`, l’administration à `/admin/adhesions/`. Le nom et le slogan restent « La Nature et l’Humain » et « RÉSEAUX · PARTENARIATS · SOLUTIONS ».

## Base inspectée

La copie Git locale retrouvée provenait de `youssoufben269/lanatureetlhumain-site`, commit `ecb0626`. Le 11 novembre 2026, le dépôt distant a été récupéré et la branche `codex/adhesion-en-ligne` actualisée sur `origin/main` `82f0ad0`. Les ajouts récents de la section don et des coordonnées de Marseille sont conservés. HTML/CSS/JavaScript sans framework ni compilation ; traduction FR/EN par attributs `data-i18n` ; formulaire contact Formspree non configuré. Les photographies auparavant embarquées ont été extraites et optimisées dans `assets/` ; le logo conserve ses octets d’origine. Les modifications du module restent locales, sans commit, push ou mise en ligne pendant cette vérification. Consulter [le bilan](VALIDATION.md) et [le déploiement](DEPLOIEMENT.md).

L’accueil est conservé : ajout du lien Adhérer et harmonisation de la casse du slogan. Le domaine, les DNS, le contact, les photographies et les autres sections sont conservés. Le logo du module est extrait de l’image déjà utilisée sur le site. La maquette validée de carte n’était pas jointe ni accessible : le fichier `membership/cards.py` contient un **gabarit provisoire** à confronter à cette maquette avant impression en série. Ne pas présenter ce gabarit comme la reproduction certifiée de la maquette validée.

## Démarrer sur ton ordinateur

Python 3.12 ou supérieur. Depuis la racine du dépôt :

```powershell
python -m venv .venv
.\.venv\Scripts\python -m pip install -r requirements-dev.txt
.\.venv\Scripts\python -m membership migrate
.\.venv\Scripts\python -m membership create-admin --email ton-adresse@exemple.org
.\.venv\Scripts\python -m membership serve-dev
```

Le mot de passe est demandé sans être affiché, minimum 14 caractères. Aucun compte ni mot de passe de démonstration n’est livré. Ouvre `http://127.0.0.1:8787/adhesion/`, puis `/admin/adhesions/`. Le serveur de développement reste local. Les données de tests sont temporaires et n’entrent pas dans les livrables.

Les variables de `.env.example` doivent être définies dans l’environnement du processus ; le fichier n’est pas chargé automatiquement. Exemple PowerShell local : `$env:LNH_CURRENCY='KMF'`. Renseigne le montant réellement adopté avec `LNH_FEE_MINOR`. Sans montant configuré, l’administrateur peut examiner et approuver une demande, mais ne peut pas confirmer son paiement ni délivrer une carte.

## Utiliser le module

1. Le demandeur saisit nom, prénom, email, téléphone et catégorie souhaitée, puis ajoute une photo JPEG/PNG et donne son consentement. La motivation est obligatoire pour les nouvelles demandes. Adresse, ville, pays et profession restent facultatifs. Les anciens dossiers sans motivation restent importables par un administrateur. La photo dispose d’un aperçu avant envoi. Les données ne sont pas enregistrées en brouillon dans le navigateur.
2. L’administrateur se connecte, sélectionne le dossier et vérifie les informations et la photo. Aucune copie de pièce d’identité nationale n’est demandée.
3. L’association saisit la **fonction attribuée** dans son champ réservé. La profession déclarée est distincte et ne s’imprime pas sur la carte. Une fonction envoyée clandestinement par un demandeur est ignorée.
4. L’administrateur valide la demande et confirme le paiement reçu, avec une référence de reçu/transaction. L’ordre des deux actions est libre. La fonction doit être enregistrée avant la validation. La confirmation manuelle ne débite aucun compte.
5. Lorsque validation et paiement sont tous deux présents, le serveur attribue le numéro et génère le PDF. Ouvre l’aperçu recto-verso et télécharge la carte depuis le dossier.
6. Un refus exige un motif. Il ferme le dossier et désactive les liens de carte. Un paiement déjà reçu reste enregistré ; ce module ne réalise pas de remboursement. Une carte déjà téléchargée ne peut évidemment pas être retirée de l’ordinateur de son destinataire.

Les noms et fonctions sont contrôlés selon la capacité réelle du gabarit avant réservation d’un numéro. Après un échec de génération, l’association peut encore corriger la fonction tant qu’aucun PDF n’a été délivré ; le même numéro est conservé. La correction et la reprise figurent dans l’historique.

Les états utilisés sont soumise, en attente de paiement, en attente de validation, validée, refusée et carte générée. L’approbation et le paiement sont deux informations distinctes : « en attente de paiement » peut donc correspondre à une demande déjà approuvée. L’historique conserve les actions, leur auteur et les changements de statut. Une version de fiche empêche un second administrateur d’écraser une décision concurrente.

La base impose un numéro unique. Un compteur annuel est incrémenté sous transaction `BEGIN IMMEDIATE` ; il ne s’agit pas d’un simple `MAX + 1`. Les numéros suivent `ANH-AAAA-001`, sans plafond artificiel à 999. Ils persistent après redémarrage. Les dates débutent lorsque l’adhésion et son paiement sont confirmés ; durée configurable, 12 mois par défaut, à rapprocher des règles de l’association. Les cas de fin de mois et années bissextiles sont traités.

Si le PDF échoue, le numéro reste réservé et le statut reste « validée ». Corrige les ressources serveur, puis utilise « Réessayer la génération ». La reprise ne crée pas un nouveau numéro. La modification d’une fonction sur une carte déjà délivrée nécessite une procédure de réédition à ajouter ; elle est bloquée dans cette première version.

## Carte et impression

PDF vectoriel de deux pages : recto puis verso, chacune **85,60 × 53,98 mm**, format ID-1. Polices incorporées, photo réencodée et recadrée, QR vectoriel avec zone de silence. La carte contient photo, nom complet, numéro, fonction attribuée, dates d’adhésion et d’expiration, nom et slogan officiels.

Imprime à **100 %**, sans « ajuster à la page ». Le texte et le QR ne sont pas limités à 300 dpi puisqu’ils sont vectoriels. La photo 450 × 600 pixels couvre environ 15,9 × 21,2 mm, soit plus de 300 dpi si la source est suffisante. Pas de fond perdu ajouté ni de profil CMJN présumé : demander les spécifications du fabricant avant un tirage industriel. Le PDF est une carte individuelle recto-verso ; aucune imposition A4 n’est supposée.

L’aperçu utilise une copie locale de Mozilla PDF.js 5.6.205 (licence dans `docs/LICENSE-PDFJS.txt`), sans CDN. Il affiche les deux faces même si le navigateur n’intègre pas de lecteur PDF.

Par défaut, la signature est une composition typographique en italique explicitement marquée « simulée ». Ce n’est pas une signature électronique. Pour une signature autorisée de l’association, définis `LNH_SIGNATURE_PATH` vers un PNG serveur privé. Le modèle est regroupé dans `membership/cards.py` pour faciliter son remplacement par la maquette approuvée.

## QR et vérification

Au départ, `LNH_QR_MODE=website` : le QR ouvre `https://www.lanatureetlhumain.org/`. Il ne certifie donc pas à lui seul le statut d’un membre.

Pour activer ensuite la vérification individuelle, définir `LNH_PUBLIC_VERIFICATION=1` et `LNH_QR_MODE=member`. La destination devient `{LNH_MODULE_ORIGIN}/membre/ANH-AAAA-NNN`, et la page indique seulement numéro et carte active/inactive. Aucun email, téléphone, nom ou photo n’est exposé. Pour garder exactement le domaine principal, faire router `/membre/` vers ce service. GitHub Pages seul ne fournit pas cette route dynamique. Les PDF déjà délivrés conservent leur QR original.

## Hébergement

GitHub Pages sert uniquement des fichiers statiques. Pour ce module, un service Python et un disque persistant sont nécessaires. Le module reste dans le même projet, que l’hébergement soit partagé ou séparé.

Option simple : héberger ce dépôt entier sur un service Python avec HTTPS. Le serveur fournit les pages existantes et l’API, sans changement du code de l’accueil. Avec Python installé :

```sh
python -m pip install -r requirements.txt
python -m membership migrate
python -m membership create-admin --email administrateur@exemple.org
python -m membership serve --host 127.0.0.1 --port 8787
```

Utiliser Waitress derrière un proxy HTTPS, un compte de service dédié et un disque local persistant. Ne pas exposer le serveur de développement à Internet. Exemple Nginx dans `deploy/nginx-membership.conf`. Définir `LNH_MODULE_ORIGIN` à l’origine HTTPS réellement utilisée avant la première connexion ; les cookies deviennent `Secure`. Lancer le processus avec un superviseur. Installer les mises à jour de sécurité des dépendances lors de la maintenance, en relançant les tests.

Avec le proxy local proposé, définir `LNH_TRUSTED_PROXY=127.0.0.1`. Nginx écrase les en-têtes d’adresse source et Waitress ne les accepte que depuis ce proxy. Cela permet de limiter les tentatives par client réel sans accepter un `X-Forwarded-For` fourni directement par un visiteur. `LNH_TIMEZONE` contrôle les dates d’adhésion/expiration ; sa valeur initiale est `Indian/Comoro`. Les horodatages d’audit restent enregistrés en UTC.

Option conservant GitHub Pages : publier les nouvelles pages et ressources statiques dans le dépôt actuel ; héberger la même API sur `https://adhesions.lanatureetlhumain.org`. Configurer cette URL dans `adhesion/assets/config.js`, définir `LNH_MODULE_ORIGIN` sur cette origine et `LNH_ALLOWED_ORIGINS=https://www.lanatureetlhumain.org`. Les deux sous-domaines doivent partager le domaine `lanatureetlhumain.org` pour les cookies `SameSite=Strict`. Ne pas utiliser une API sur un autre domaine sans adapter l’architecture des sessions. Le certificat, le sous-domaine et le service d’hébergement restent à mettre en place. Ne pas modifier le `CNAME` existant pour simplement ajouter le module.

Pour GitHub Pages, le workflow livré publie uniquement une liste explicite de fichiers publics. La base, les photos, les cartes, le code serveur et les variables ne doivent jamais entrer dans un artefact Pages. Vérifie le mode de publication du dépôt avant toute mise en ligne. L’ajout du workflow ne change pas automatiquement les paramètres Pages existants.

SQLite convient à une petite association, sur une instance et un disque local. Ne pas utiliser un volume réseau ni plusieurs réplicas sans revoir cette couche. Pour plusieurs serveurs, migrer les transactions et compteurs vers PostgreSQL avant montée en charge.

## Emails

Aucun email n’est envoyé sans configuration SMTP et exécution du worker. Les notifications sont enregistrées en base dans une file transactionnelle : réception, validation avec paiement, refus, disponibilité de la carte. Configure `LNH_SMTP_HOST`, port, expéditeur et identifiants selon le service réel. Chiffrement SSL ou STARTTLS obligatoire, certificats vérifiés. Les secrets restent dans l’environnement serveur.

Exécute régulièrement, par exemple chaque minute avec le planificateur du serveur :

```sh
python -m membership flush-email
```

Une tentative échouée est reprogrammée avec délai croissant. Un lease permet la reprise après arrêt du worker. Comme pour tout envoi SMTP, un arrêt après acceptation du message mais avant enregistrement peut provoquer une répétition ; le `Message-ID` reste stable. Les notifications obsolètes non envoyées sont annulées lors d’un refus.

Le lien de carte envoyé par email est privé, aléatoire, stocké sous forme de hash côté accès, valable 7 jours. Son jeton est dans le fragment `#token=...` et n’entre pas dans l’URL des requêtes HTTP. Le serveur refuse un lien expiré ou une adhésion désactivée. Si l’email est désactivé ou si le lien a expiré, l’administrateur peut télécharger le PDF pour le remettre au membre par le canal choisi. Le chemin privé et l’URL administrateur du PDF sont enregistrés dans la fiche.

## Données et sécurité

Les requêtes publiques et les décisions sont validées côté serveur. Maximum photo : 3 Mo, 16 mégapixels, JPEG/PNG non animé, au moins 240 × 320 pixels. Le serveur vérifie le contenu réel et réencode les images pour retirer EXIF/GPS. Les noms de fichiers de stockage sont générés, jamais repris de l’upload. Les accès SQL sont paramétrés ; les valeurs affichées dans le navigateur passent par `textContent`.

Mots de passe scrypt avec sel unique, sessions aléatoires stockées sous forme de hash, expiration à 8 heures, cookie HttpOnly/SameSite, contrôle CSRF et origine sur les modifications. Les tentatives de connexion, envois et téléchargements publics sont limités en base. Les tokens de carte n’apparaissent pas dans les liens d’accès administrateur. Le serveur n’expose qu’une liste de pages publiques ; pas de montage global du dépôt. Les journaux applicatifs ne doivent pas contenir de corps de demande, de mot de passe ou de jeton.

`LNH_DATA_DIR` contient la base, les photos et les PDF, hors racine du serveur public. Chiffrer le volume et les sauvegardes par les moyens de l’hébergeur ; ce module ne prétend pas chiffrer lui-même SQLite. Sur Linux, répertoires 700/fichier base 600. Sur Windows, restreindre les ACL au compte du service et à l’administrateur lors du déploiement. Les fichiers privés et `.env` sont exclus de Git.

La notice et les catégories sont une base de configuration, à rapprocher des statuts, du droit retenu et des pratiques réelles de conservation avant ouverture. `LNH_RETENTION_DAYS` vaut 90 jours pour l’éligibilité des dossiers refusés à la suppression. Le responsable examine la liste avec `python -m membership purge-closed`, puis peut exécuter la purge avec `--confirm`. Les dossiers comportant un paiement restent exclus de cette purge automatique, pour préserver le suivi financier. Les sauvegardes, dossiers acceptés et pièces comptables nécessitent une politique propre à l’association.

Sauvegarder de manière cohérente la base SQLite et ses fichiers de photos/cartes ; utiliser l’API SQLite backup ou arrêter le service pendant la copie. Tester la restauration. Ne pas diffuser une copie de `var/`. Pour désactiver un administrateur, mettre `active=0` via une intervention serveur contrôlée : ses sessions sont alors refusées immédiatement. La procédure de renouvellement des cartes et une interface multi-comptes pourront être ajoutées au même module.

## Vérifier

```sh
python -m unittest discover -s tests -v
```

Les tests couvrent parcours complet dans les deux ordres, fonction réservée à l’association, consentement, uploads invalides, photo nettoyée, accès admin, CSRF/origine, fichiers privés, montants, collisions de version, numéros parallèles et persistance, PDF à deux faces avec dimensions physiques, reprise après échec, désactivation des liens, file email et conservation de l’accueil. `pypdf` est une dépendance de test, distincte du serveur.

Références techniques : [GitHub Pages](https://docs.github.com/en/pages/getting-started-with-github-pages/what-is-github-pages), [Waitress derrière un proxy](https://docs.pylonsproject.org/projects/waitress/en/stable/reverse-proxy.html), [PDF.js](https://mozilla.github.io/pdf.js/examples/), [SQLite et transactions Python](https://docs.python.org/3/library/sqlite3.html).
