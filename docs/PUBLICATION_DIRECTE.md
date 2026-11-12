# Publication de l’envoi direct des demandes d’adhésion

Le [formulaire public](https://www.lanatureetlhumain.org/adhesion/) utilise **Google Apps Script**. Le demandeur clique sur **Envoyer** ; le dossier et la photo sont transmis ensemble, sans téléchargement ni email manuel. Il reçoit une page de confirmation et un accusé par email. Le site reste sur GitHub Pages ; l’administration et les cartes restent locales.

## Notifications institutionnelles du 12 novembre 2026

Le déploiement existant est actif en **version 8**, avec la même URL `/exec`. L’email commence par « Madame, Monsieur » et confirme la réception de votre demande. La réserve « Cet accusé de réception ne vaut pas validation » est remplacée par : « L’association examinera votre demande et vous informera de la décision prise ainsi que des prochaines étapes, le cas échéant. » La confirmation affichée après envoi et les messages d’erreur utilisent également le vouvoiement. La version anglaise est harmonisée.

Harnais Node réexécuté avec succès ; version 8 confirmée dans Google. Aucun nouvel email réel envoyé pour cette correction de texte. Les emails déjà reçus ne sont pas modifiés.

## Légende de la photo du 12 novembre 2026

Le déploiement Google existant est en **version 7**. À la demande du propriétaire, la légende du portrait et son texte alternatif deviennent **« Photo d’identité »** dans les nouveaux PDF, à la place de « Photographie fournie ». L’URL, les coordonnées, la mise en page et l’exception privée d’essai sont conservées. Harnais Node réexécuté avec succès et mise à jour du déploiement confirmée dans Google. Les PDF déjà reçus ne sont pas réécrits.

## Correction du refus d’essai : exception privée demandée par le propriétaire

Le service Google est actif en **version 6**, même URL `/exec`. Deux dossiers antérieurs de l’adresse utilisée pour les essais ont été retrouvés dans Gmail, et le compteur privé de cette adresse était à 2. Le propriétaire a confirmé utiliser la même adresse et a demandé un nombre illimité d’essais pendant la configuration.

La propriété privée `LNH_TEST_EMAIL_HASHES` contient une seule empreinte autorisée. Elle exonère cette adresse des limites applicatives et exclut ses essais des compteurs publics, sans remettre les anciens compteurs à zéro. Les autres adresses conservent leurs limites. La valeur privée et l’adresse personnelle ne figurent pas dans Git. Les quotas Google et toutes les validations restent applicables. Pour rétablir les limites à la fin des essais, vider cette propriété dans le projet existant.

Le message générique est complété par une explication FR/EN pour les refus connus : limite par email, horaire ou quotidienne, formulaire à recharger, motivation, champs, référence conflictuelle ou service occupé. Les erreurs internes et données saisies ne sont pas exposées.

Le harnais Node a été réexécuté : exemption avec compteurs saturés, plusieurs dépôts, compteurs inchangés, autres adresses toujours limitées, révocation immédiate de l’exemption, validations et idempotence conservées, quota MailApp épuisé et reprise, textes FR/EN et absence de réflexion d’un code d’erreur non reconnu. Aucun email n’est envoyé par ces tests simulés. La suite Python n’est pas modifiée par cette correction.

Vérification réelle depuis le formulaire public, avec la seule adresse autorisée et un dossier clairement fictif : référence se terminant par `f89ae613`, page **Demande reçue**, dossier et photo enregistrés et accusé envoyé. Ce dépôt passe malgré les deux essais précédents. Aucune carte ni numéro de membre n’a été délivré. Ne pas valider le dossier de contrôle.

## Finition du 12 novembre 2026 : motivation et en-tête institutionnel

Le service Google existant est actif en **version 5**, avec la même URL `/exec`. Le PDF comporte un en-tête centré sur les deux parties : logo original en couleurs, nom en noir, slogan gris, siège social au **60 traverse Moulin de la Villette, 13003 Marseille, France**, téléphone **+33 7 45 95 39 60** et **contact@lanatureetlhumain.org**. Les coordonnées sont identiques à celles du site actuel. Les polices bleues ont été remplacées par du noir ou du gris foncé ; les rubriques et mentions ont été relues dans un registre institutionnel. Le statut précise : « L’adhésion est soumise à l’examen du dossier et à la validation de l’association. » Les champs facultatifs vides portent la mention « Information non communiquée ».

Le formulaire affiche **Motivation \*** en FR/EN. La motivation est obligatoire pour toute nouvelle demande, avec contrôle côté navigateur et serveur Google/Python, y compris pour une valeur composée uniquement d’espaces. Les anciens dossiers sans motivation restent importables par un administrateur. La notice de confidentialité et la documentation pratique reflètent cette obligation. Le formulaire a été publié au commit `de1d419`, [Pages terminé avec succès](https://github.com/youssoufben269/lanatureetlhumain-site/actions/runs/43153109894).

Contrôles : **72 tests Python, 70 réussis et 2 ignorés sous Windows**, harnais Node réussi ; formulaire public vérifié en FR/EN, motivation vide et espaces refusés, largeur de 390 px sans débordement (document 375 px). Nouveau dépôt réel de données fictives depuis le site public : référence terminant par `fc5f485f`, dossier et accusé retrouvés dans la seule boîte de l’association via son alias `+chartepdf`. PDF et photo séparée présents. Le PDF réellement reçu a été téléchargé et rendu avec Poppler : deux pages A4, logo et photo visibles, aucun texte coupé, coordonnées et rubriques lisibles. La position des quatre lignes d’en-tête est centrée à moins de 0,3 point du milieu de page. Les couleurs de texte sont neutres, sans bleu. Aucun numéro ni carte n’a été délivré. Le PDF de démonstration reste hors Git et de Pages. Les anciens emails et PDF déjà reçus ne sont pas réécrits.

## Mise à jour du 12 novembre 2026 : PDF et photo séparée

Le service existant est déployé en **version 3**, avec la même URL `/exec`, sans nouvelle autorisation ni modification du formulaire public. L’email destiné à l’association comporte désormais **un dossier PDF administratif et une photo JPEG/PNG en pièce jointe distincte**. Le JSON n’est plus joint ; il reste dans le dossier Drive privé, dont le lien figure dans l’email, pour l’import local sans ressaisie. Les emails antérieurs restent inchangés.

Deux dépôts fictifs effectués depuis le site public ont été retrouvés dans Gmail, avec les deux pièces jointes et les accusés séparés. Le PDF normal comporte deux pages A4 ; le dossier long, avec une motivation de 1 980 caractères et une adresse longue, comporte trois pages sans texte tronqué. Les fichiers réellement reçus ont été téléchargés, rendus avec Poppler et inspectés : logo, slogan, accents, référence, date locale au Bénin, photo intégrée, rubriques et cadre administratif lisibles. Les références de dépôt de test finissent par `ebbd548a` et `c4052f6e`. Ne pas les valider ni générer de cartes. Le second accusé utilise un alias `+controlepdf` de la même boîte de l’association ; aucun tiers n’a reçu de message.

La photo séparée a été téléchargée depuis Gmail et décodée : JPEG, 600 × 800 pixels, sans EXIF. Tests : harnais Node réussi (deux pièces jointes, type PDF/image, conservation privée du JSON, échappement HTML, textes longs, idempotence, conversion en échec et reprise, accusé indépendant) ; **70 tests Python exécutés, 68 réussis et 2 ignorés sous Windows**. Build Pages : toujours 19 fichiers publics, aucune pièce de dossier. Les incidents de conversion et quotas sont simulés ; ils n’ont pas été provoqués sur Google.

Le PDF provient de la conversion HTML Google (`HtmlOutput.getAs`), avec les scopes déjà autorisés. Les quotas de conversion et d’email du compte restent applicables. La nouvelle version ne délivre aucun numéro de membre ni carte et conserve les règles de l’administration locale.

## Publication effective

- Compte Google propriétaire et destinataire : **lanaturetlhumain@gmail.com**.
- Projet existant : **LNH - Réception des adhésions**. Autorisations accordées personnellement par le propriétaire ; installation terminée sans erreur affichée.
- Service Web Google : version 1, exécution en tant que propriétaire et accès aux dépôts sans connexion Google. L’URL de production est dans `adhesion/settings.json` ; aucun secret n’est nécessaire dans le navigateur.
- Version fonctionnelle publiée : commit **71c1b5d** sur `main`, [déploiement GitHub Pages réussi](https://github.com/youssoufben269/lanatureetlhumain-site/actions/runs/43144727203). L’exécution initiale était restée en file d’attente ; une relance par l’API officielle GitHub a abouti. Le mode `google`, le destinataire et l’URL `/exec` ont été relus depuis le site public.
- Finition publiée : **078330b**, [déploiement réussi](https://github.com/youssoufben269/lanatureetlhumain-site/actions/runs/43146320689). Le JavaScript distribué par le site est identique au fichier Git de cette version. Le retour arrière après sélection d’une photo a été retesté dans le navigateur : aperçu conservé. Les chemins `/admin/adhesions/`, `/.env`, `/membership/config.py` et `/var/members.sqlite3` répondent tous **404**.
- Le build publie seulement **19 fichiers publics**. Le serveur Python, les sources Google, l’administration, les tests et les données privées en sont exclus. Le domaine et le fichier `CNAME` sont conservés.

## Vérifications réalisées

Le parcours de dépôt a été effectué dans le navigateur, sans connexion Google, depuis la compilation statique locale reliée au service Google de production. Les informations et la photo étaient entièrement fictives, marquées **TEST TECHNIQUE / DOSSIER FICTIF À IGNORER**. Les notifications de l’association et du demandeur ont été envoyées uniquement à la boîte de l’association, puis retrouvées dans Gmail. La page de réception a confirmé l’enregistrement avec une référence de dépôt et l’envoi de l’accusé.

Le fichier JSON réellement joint à cet email a été téléchargé, puis importé dans une administration locale temporaire. Résultat : photo JPEG de **600 × 800 pixels sans EXIF**, consentement **2026-11-11-v2** conservé, historique `import_email`, profession distincte de la fonction. Un second import retrouve le même dossier. La fonction reste vide ; aucun numéro ni aucune carte n’est créé. L’administration temporaire a été supprimée après vérification. Le dossier de test et ses deux emails restent reconnaissables dans le compte Google ; ne pas les traiter comme une demande réelle.

Le dossier Drive **LNH - Demandes adhesion - PRIVE** a été contrôlé dans sa fenêtre de partage : accès général **Limité**, un seul utilisateur, le compte de l’association propriétaire. Aucune route publique de lecture des dossiers n’est prévue dans le service.

Le formulaire réellement publié a été ouvert et contrôlé en **FR/EN**, à une largeur mobile de **390 px** (document 375 px, sans débordement). Le bouton est actif, le panneau de téléchargement manuel reste masqué et aucune erreur JavaScript n’a été observée. La reprise de la photo après retour arrière a été renforcée pour ne pas dépendre uniquement de l’événement de sélection du fichier.

Les contrôles automatiques précédents restent valables : **70 tests Python, 68 réussis et 2 ignorés sous Windows**, et harnais Node de réception Google (validation, stockage, doublons, limites, notifications et reprise simulées). Les quatre tests d’import/artefact ont été réexécutés après activation. Les envois réels décrits ci-dessus complètent ces simulations ; les cas de quota épuisé et de reprise après incident Google ne sont pas provoqués en production.

## Exploitation

Ouvrir le **PDF joint** pour l’examen du dossier et la **photo jointe séparément**. Pour le traitement local sans ressaisie, télécharger le fichier d’import technique depuis le lien Drive privé de l’email, puis l’importer depuis `GERER_ADHESIONS.cmd`. Suivre [PRISE_EN_MAIN.md](PRISE_EN_MAIN.md). Les montants, catégories et règles réels restent à adopter/configurer pour les cartes ; le gabarit de carte demeure provisoire. Aucun prestataire de paiement n’est ajouté.

Voir [ENVOI_DIRECT_GOOGLE.md](ENVOI_DIRECT_GOOGLE.md) pour les limites gratuites, les autorisations, la maintenance et le retour au parcours manuel. Google Drive contient une copie des dossiers ; prévoir une conservation et des sauvegardes privées cohérentes avec les emails et l’administration locale. Le script ne prétend pas vérifier l’identité du demandeur ni la propriété de son adresse email.
