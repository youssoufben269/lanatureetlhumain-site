# Publication de l’envoi direct des demandes d’adhésion

Le [formulaire public](https://www.lanatureetlhumain.org/adhesion/) utilise **Google Apps Script**. Le demandeur clique sur **Envoyer** ; le dossier et la photo sont transmis ensemble, sans téléchargement ni email manuel. Il reçoit une page de confirmation et un accusé par email. Le site reste sur GitHub Pages ; l’administration et les cartes restent locales.

## Publication effective

- Compte Google propriétaire et destinataire : **lanaturetlhumain@gmail.com**.
- Projet existant : **LNH - Réception des adhésions**. Autorisations accordées personnellement par le propriétaire ; installation terminée sans erreur affichée.
- Service Web Google : version 1, exécution en tant que propriétaire et accès aux dépôts sans connexion Google. L’URL de production est dans `adhesion/settings.json` ; aucun secret n’est nécessaire dans le navigateur.
- Version fonctionnelle publiée : commit **71c1b5d** sur `main`, [déploiement GitHub Pages réussi](https://github.com/youssoufben269/lanatureetlhumain-site/actions/runs/43144727203). L’exécution initiale était restée en file d’attente ; une relance par l’API officielle GitHub a abouti. Le mode `google`, le destinataire et l’URL `/exec` ont été relus depuis le site public.
- Le build publie seulement **19 fichiers publics**. Le serveur Python, les sources Google, l’administration, les tests et les données privées en sont exclus. Le domaine et le fichier `CNAME` sont conservés.

## Vérifications réalisées

Le parcours de dépôt a été effectué dans le navigateur, sans connexion Google, depuis la compilation statique locale reliée au service Google de production. Les informations et la photo étaient entièrement fictives, marquées **TEST TECHNIQUE / DOSSIER FICTIF À IGNORER**. Les notifications de l’association et du demandeur ont été envoyées uniquement à la boîte de l’association, puis retrouvées dans Gmail. La page de réception a confirmé l’enregistrement avec une référence de dépôt et l’envoi de l’accusé.

Le fichier JSON réellement joint à cet email a été téléchargé, puis importé dans une administration locale temporaire. Résultat : photo JPEG de **600 × 800 pixels sans EXIF**, consentement **2026-11-11-v2** conservé, historique `import_email`, profession distincte de la fonction. Un second import retrouve le même dossier. La fonction reste vide ; aucun numéro ni aucune carte n’est créé. L’administration temporaire a été supprimée après vérification. Le dossier de test et ses deux emails restent reconnaissables dans le compte Google ; ne pas les traiter comme une demande réelle.

Le dossier Drive **LNH - Demandes adhesion - PRIVE** a été contrôlé dans sa fenêtre de partage : accès général **Limité**, un seul utilisateur, le compte de l’association propriétaire. Aucune route publique de lecture des dossiers n’est prévue dans le service.

Le formulaire réellement publié a été ouvert et contrôlé en **FR/EN**, à une largeur mobile de **390 px** (document 375 px, sans débordement). Le bouton est actif, le panneau de téléchargement manuel reste masqué et aucune erreur JavaScript n’a été observée. La reprise de la photo après retour arrière a été renforcée pour ne pas dépendre uniquement de l’événement de sélection du fichier.

Les contrôles automatiques précédents restent valables : **70 tests Python, 68 réussis et 2 ignorés sous Windows**, et harnais Node de réception Google (validation, stockage, doublons, limites, notifications et reprise simulées). Les quatre tests d’import/artefact ont été réexécutés après activation. Les envois réels décrits ci-dessus complètent ces simulations ; les cas de quota épuisé et de reprise après incident Google ne sont pas provoqués en production.

## Exploitation

Ouvrir les emails reçus et importer leur dossier joint depuis `GERER_ADHESIONS.cmd`. Suivre [PRISE_EN_MAIN.md](PRISE_EN_MAIN.md). Les montants, catégories et règles réels restent à adopter/configurer pour les cartes ; le gabarit de carte demeure provisoire. Aucun prestataire de paiement n’est ajouté.

Voir [ENVOI_DIRECT_GOOGLE.md](ENVOI_DIRECT_GOOGLE.md) pour les limites gratuites, les autorisations, la maintenance et le retour au parcours manuel. Google Drive contient une copie des dossiers ; prévoir une conservation et des sauvegardes privées cohérentes avec les emails et l’administration locale. Le script ne prétend pas vérifier l’identité du demandeur ni la propriété de son adresse email.
