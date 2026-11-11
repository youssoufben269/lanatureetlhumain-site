# Publication du parcours par email

Version initiale publiée le **11 novembre 2026**, commit `a42fa32`.

- Dépôt : `youssoufben269/lanatureetlhumain-site`, branche publique `main`.
- Publication passée de la racine brute du dépôt à **GitHub Actions**. Seuls les 18 fichiers sélectionnés par `scripts/prepare_public.py` sont publiés.
- [Déploiement réussi](https://github.com/youssoufben269/lanatureetlhumain-site/actions/runs/43086092166).
- [Formulaire accessible](https://www.lanatureetlhumain.org/adhesion/) : HTTP 200, 6 636 octets lors du contrôle initial, environ 1,5 seconde sur la connexion testée. Le lien **Adhérer** de l’accueil ouvre bien cette page ; les champs et le bouton sont actifs après chargement.
- Configuration distante vérifiée : mode **email**, destinataire exact **lanaturetlhumain@gmail.com**.
- L’administration, `.env` et le code du serveur ne sont pas servis par le site. Les données et cartes sont absentes de l’artefact public et restent sur l’ordinateur.

Le formulaire demande un **email de notification obligatoire**, distinct de l’adresse de réception de l’association. Il figure dans le dossier, dans le message préparé et dans la fiche locale. Il doit être utilisé pour répondre au demandeur et lui envoyer sa carte. Dans le parcours choisi, ces emails sont envoyés manuellement depuis Gmail.

Les tests fictifs couvrent le téléchargement du dossier, son import local, sa photo, la distinction profession/fonction et la carte après validation et paiement confirmé. Aucun email réel n’a été envoyé ; la réception Gmail n’est donc pas attestée par ces tests.

Voir [le guide pratique](PRISE_EN_MAIN.md). Le compte administrateur local se crée au premier lancement sur l’ordinateur ; il ne s’agit pas d’un compte de service externe. Le montant, la devise et les catégories réels restent à configurer avant les premières cartes. Le gabarit de carte demeure provisoire.
