# Envoi direct des dossiers avec Google Apps Script

Compte propriétaire prévu : **lanaturetlhumain@gmail.com**. Aucun compte supplémentaire ni serveur Python distant. Le site reste publié par GitHub Pages. Le code préparé n’active pas le service tant que son URL de déploiement n’est pas renseignée.

## État de publication

Le projet **LNH - Réception des adhésions** est installé dans le compte de l’association : [ouvrir le projet](https://script.google.com/home/projects/1Cn6q4KvG-42_6MhU0ofMvbwMwgSHedocvrGD-4eSmstc6MrUYR246z4X/edit). Le propriétaire a accordé les autorisations Google. L’installation s’est terminée sans erreur ; le dossier **LNH - Demandes adhesion - PRIVE** a été vérifié en accès général **Limité**, avec le seul compte de l’association comme propriétaire.

Le déploiement Web **version 7** est actif depuis le 12 novembre 2026 : [service de réception](https://script.google.com/macros/s/AKfycbzv0FPJvqn-2luW_vuMmG2jU1U8IA4BnEDOZH1L3HXnEZyjX5beQm2LJbUUbPrSWMPP/exec). Exécution en tant que propriétaire ; accès public au dépôt des demandes, sans accès public aux fichiers. `googleEndpoint` est renseigné et le site publié sert le mode `google`. L’association reçoit le PDF et la photo en deux pièces jointes, vérifiées dans Gmail. Le PDF utilise des textes noirs et gris et un en-tête centré avec le siège social à Marseille, le téléphone et l’email publiés sur le site. La motivation est obligatoire pour les nouvelles demandes.

Un dossier fictif a été envoyé avec une photo de test. Les deux emails ont été retrouvés dans la boîte de l’association ; le fichier reçu a été téléchargé et importé dans une administration locale de test. Photo 600 × 800, sans EXIF, consentement v2 conservé, second import sans doublon, aucune fonction, aucun numéro et aucune carte délivrés. Aucun dossier réel n’a été utilisé. [Bilan complet](PUBLICATION_DIRECTE.md).

Les étapes ci-dessous servent à comprendre ou réinstaller le service. **Ne pas créer un deuxième projet pour la maintenance du service existant.**

## Parcours

Le demandeur remplit le formulaire et clique sur **Envoyer**. Le navigateur transmet un POST HTTPS comprenant les champs et la photo, sans téléchargement ni passage par sa messagerie. Il est dirigé vers une page de réception Google portant l’identité de l’association. Cette navigation est volontaire : une requête `fetch` en mode `no-cors` ne permettrait pas de vérifier le résultat et ne doit jamais être présentée comme un envoi réussi.

La page confirme seulement un dossier durablement enregistré. Le service prépare un **PDF administratif A4** avec le logo, le slogan, la référence, la date au Bénin, l’identité et la photo, les coordonnées, la catégorie, la profession déclarée, la motivation, le consentement et un cadre réservé à l’association. Deux parties commencent chacune sur une nouvelle page ; les textes longs peuvent ajouter des pages sans être tronqués. Les espaces et retours à la ligne sont normalisés pour l’impression ; le texte d’origine reste dans les données privées.

L’association reçoit **deux pièces jointes : le dossier PDF et la photo JPEG/PNG séparée**. Aucun JSON n’est joint à cet email. Une copie du PDF, la photo et les données techniques compatibles avec l’import local restent dans le dossier Drive privé. Le lien de ce dossier dans l’email exige le compte de l’association ; il ne donne aucun accès public. Pour un import local sans ressaisie, y télécharger `demande-adhesion-lnh.json`. Les anciens emails ne sont pas modifiés rétroactivement.

Le demandeur reçoit séparément un accusé. Une conversion PDF ou une notification en échec ne supprime pas le dossier et ne bloque pas l’essai d’envoi de cet accusé. Le déclencheur horaire réessaie les notifications manquantes ; un PDF déjà créé est réutilisé. Les quotas Google de conversion et de mail restent applicables. Aucun nouveau scope OAuth, compte ou service payant n’est ajouté. Aucun numéro de membre ni carte n’est créé par Google.

## Activation dans le compte de l’association

1. Se connecter à [Google Apps Script](https://script.google.com/home) avec **lanaturetlhumain@gmail.com**.
2. Créer un projet **LNH - Réception des adhésions**. Remplacer `Code.gs` par [le fichier livré](../google-apps-script/Code.gs).
3. Dans les paramètres du projet, afficher le manifeste `appsscript.json`, puis remplacer son contenu par [le manifeste livré](../google-apps-script/appsscript.json).
4. Enregistrer et exécuter **installer**. Le compte propriétaire doit autoriser l’accès Drive, l’envoi de mails et le déclencheur horaire. Le code exige le compte de l’association et refuse le compte personnel. L’installation ne transmet aucun email.
5. Vérifier que **LNH - Demandes adhesion - PRIVE** n’a aucun partage public. Le dossier est créé privé dans le Drive du compte propriétaire. Ne pas le déplacer dans un espace partagé.
6. Déployer une **application Web**, exécutée **en tant que propriétaire**, avec accès **Tout le monde** (y compris sans connexion Google). Seule la réception est publique ; aucune route de lecture des dossiers n’existe. Ne jamais publier le Drive ou ajouter une API publique de lecture.
7. Copier l’URL de production finissant par `/exec` dans `adhesion/settings.json`, propriété **googleEndpoint**. Une URL `/dev` ne convient pas. Préparer et publier Pages avec le workflow existant. Le build active automatiquement le mode `google` uniquement avec une URL valide ; sans URL, le parcours email déjà publié reste utilisable.
8. Vérifier depuis un navigateur non connecté : dossier fictif et photo, consentement, réception privée, email de l’association, accusé au demandeur et import local de ce dossier. L’envoi d’un email de test demande l’accord sur ses destinataires. Effacer ensuite les seules données de test via les fonctions ordinaires de suppression.

## Protections et limites

- Validation serveur des champs, catégorie, consentement et fichier JPEG/PNG ; taille 3 Mo, minimum 240 × 320 et maximum 16 mégapixels. Le navigateur réencode la photo sans EXIF. Le serveur Google contrôle signature et dimensions ; le décodage et nettoyage complet sont refaits par le service local avant les cartes.
- Champs inconnus ignorés : fonction, validation, paiement et numéro ne peuvent pas être définis par le demandeur.
- Verrou Google Script pour sérialiser les écritures et réutilisation de la même référence pour les doubles clics ou nouvelles tentatives identiques. Référence de dépôt `LNH-D-…`, distincte du numéro de membre. Une référence ne peut pas écraser un autre contenu.
- Plafonds initiaux : 10 dossiers par heure, 30 par jour, 2 par email et par jour. Le formulaire comporte un piège anti-robot et un délai minimal ; ces contrôles ne remplacent pas un CAPTCHA et ne garantissent pas l’absence d’abus. Google Apps Script ne fournit pas ici d’adresse IP fiable du visiteur. Réviser ces seuils selon la fréquentation et surveiller les quotas et la capacité Drive.
- Les emails d’accusé contiennent un texte fixe, sans photo ni message libre du demandeur. L’association reçoit le dossier joint ; les réponses vont à l’email vérifié syntaxiquement du demandeur.
- Envoi d’email et mise à jour d’état ne sont pas une transaction unique : une interruption après l’envoi peut produire une notification doublée lors de la reprise. Le dossier et sa référence restent uniques. Un quota épuisé reporte les emails, sans supprimer les dossiers.
- La lecture des dossiers n’exige jamais leur partage public. Les autorisations Drive demandées par `DriveApp` sont étendues au compte ; le code livré ne travaille que dans son dossier dédié. Ne pas autoriser un projet dont le code a changé sans le relire.
- Notice directe version **2026-11-11-v2**. L’import local accepte cette version et conserve la version effectivement consentie ; les anciens dossiers `v1` restent importables. La réception Google ne prétend pas vérifier l’identité, la propriété de l’adresse email ou la date d’un paiement.
- Décider la durée de conservation et supprimer les dossiers arrivés à échéance dans Drive et les emails correspondants. La reprise horaire parcourt les dossiers conservés ; archiver les dossiers traités hors du dossier d’entrée pour limiter le temps d’exécution, sans perdre les sauvegardes privées.

## Mise à jour et retour arrière

### Exception temporaire pour les essais du propriétaire

À la demande explicite du propriétaire, une adresse peut être exemptée des limites applicatives pendant la configuration. La propriété privée Apps Script `LNH_TEST_EMAIL_HASHES` contient l’empreinte SHA-256 hexadécimale de l’adresse normalisée (minuscules, espaces extérieurs supprimés). Aucun email personnel ni sa valeur d’empreinte n’est conservé dans les sources ou ce guide. Ne pas ajouter une autre adresse sans autorisation.

Pour cette seule adresse, les limites de 2 demandes par jour, 10 par heure et 30 par jour ne sont pas appliquées, et ses essais n’incrémentent pas les compteurs publics. Les limites restent actives pour les autres adresses. Les champs obligatoires, consentement, validation de la photo, verrou, référence unique et interdiction de délivrer une carte restent inchangés. Les quotas de Google Drive, conversion PDF et MailApp continuent de s’appliquer ; les notifications en attente sont reprises automatiquement.

Une propriété vide ou absente désactive immédiatement l’exception, sans nouveau déploiement. À la fin de la configuration, vider uniquement `LNH_TEST_EMAIL_HASHES` ; conserver `LNH_RATE`, `LNH_FOLDER_ID` et tous les dossiers reçus. Aucun compteur existant n’est remis à zéro. Les refus connus affichent maintenant une explication en FR/EN (limite, session, motivation, champs ou service occupé), sans afficher les données du demandeur ni les erreurs internes.

Après un changement du service Google, créer une nouvelle version du déploiement existant pour conserver la même URL `/exec`. Sans ce geste, modifier les fichiers de l’éditeur ne met pas le service en production à jour. Pour revenir temporairement au parcours manuel, vider `googleEndpoint` puis republier Pages. Conserver les dossiers déjà reçus et le déclencheur tant que des notifications restent en attente.

## Sources

[Applications Web](https://developers.google.com/apps-script/guides/web), [autorisations](https://developers.google.com/apps-script/guides/services/authorization), [quotas Google](https://developers.google.com/apps-script/guides/services/quotas). Les offres et quotas peuvent évoluer.
