# Envoi direct des dossiers avec Google Apps Script

Compte propriétaire prévu : **lanaturetlhumain@gmail.com**. Aucun compte supplémentaire ni serveur Python distant. Le site reste publié par GitHub Pages. Le code préparé n’active pas le service tant que son URL de déploiement n’est pas renseignée.

## Parcours

Le demandeur remplit le formulaire et clique sur **Envoyer**. Le navigateur transmet un POST HTTPS comprenant les champs et la photo, sans téléchargement ni passage par sa messagerie. Il est dirigé vers une page de réception Google portant l’identité de l’association. Cette navigation est volontaire : une requête `fetch` en mode `no-cors` ne permettrait pas de vérifier le résultat et ne doit jamais être présentée comme un envoi réussi.

La page confirme seulement un dossier durablement enregistré. Le dossier JSON, compatible avec l’import local existant, et la photo sont dans un dossier Google Drive privé. Deux emails sont préparés côté serveur : le dossier à l’association et un accusé au demandeur. Si Google refuse temporairement un email, la page précise que le dossier est enregistré et que la notification reste en attente. Un déclencheur horaire réessaie. Aucun numéro de membre ni carte n’est créé par Google.

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

Après un changement du service Google, créer une nouvelle version du déploiement existant pour conserver la même URL `/exec`. Sans ce geste, modifier les fichiers de l’éditeur ne met pas le service en production à jour. Pour revenir temporairement au parcours manuel, vider `googleEndpoint` puis republier Pages. Conserver les dossiers déjà reçus et le déclencheur tant que des notifications restent en attente.

## Sources

[Applications Web](https://developers.google.com/apps-script/guides/web), [autorisations](https://developers.google.com/apps-script/guides/services/authorization), [quotas Google](https://developers.google.com/apps-script/guides/services/quotas). Les offres et quotas peuvent évoluer.
