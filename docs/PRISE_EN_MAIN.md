# Demandes d’adhésion, cartes sur ton ordinateur

**Le formulaire public envoie directement les dossiers avec Google Apps Script.** Le compte de l’association, `lanaturetlhumain@gmail.com`, reçoit les demandes ; le service conserve aussi une copie dans son Drive privé. Aucun nouveau compte ni hébergement payant n’est nécessaire. La validation et les cartes restent sur ton ordinateur.

## Pour le demandeur

1. Ouvrir **Adhérer** sur [le site officiel](https://www.lanatureetlhumain.org/adhesion/) et remplir le formulaire avec son email, sa photo, sa motivation et le consentement. La motivation est obligatoire.
2. Cliquer sur **Envoyer**. Le dossier et la photo sont transmis ensemble. Aucun fichier à télécharger ni email à composer.
3. Lire la page de confirmation Google portant l’identité de l’association. La référence affichée est une référence de dépôt, pas un numéro de membre. Un accusé de réception est envoyé à l’email saisi ; vérifier les courriers indésirables si nécessaire.

Si la page indique que l’envoi n’a pas pu être confirmé, revenir au formulaire et réessayer. Ne pas recommencer si un accusé a déjà été reçu. Si les notifications restent en attente, le dossier enregistré reste conservé et le service réessaie les emails automatiquement. La validation de l’adhésion et le paiement ne sont pas automatiques.

## Pour toi

1. Dans Gmail, ouvrir le **dossier PDF** pour l’examen administratif et la **photo JPEG/PNG jointe séparément**. Le PDF inclut aussi la photo. Les rubriques regroupent identité, coordonnées, catégorie, profession, motivation, consentement et cadre réservé à l’association. Conserver les pièces dans un emplacement privé, hors Git et hors fichiers publics du site.
2. Double-cliquer sur **GERER_ADHESIONS.cmd**, à la racine de `site-web/`. Garder la fenêtre ouverte pendant l’utilisation.
3. Au premier lancement, choisir ton email et un mot de passe local d’au moins 14 caractères. Ce compte protège l’administration de ton ordinateur ; il ne crée aucun compte chez un fournisseur.
4. Pour importer les données sans les ressaisir, ouvrir le lien **Dossier privé** de l’email avec le compte de l’association. Télécharger `demande-adhesion-lnh.json`, puis le sélectionner dans **Dossier reçu par email** de l’administration locale et cliquer sur **Importer le dossier** après vérification. Ce fichier technique reste réservé à l’import ; les responsables examinent le PDF, pas le JSON. Le PDF seul n’est pas un fichier d’import.
5. Vérifier les informations et la photo. Attribuer la **fonction** dans l’administration : elle reste distincte de la profession déclarée. Un second import du même email ne crée pas de doublon et n’écrase pas le dossier existant.
6. Valider la demande et confirmer manuellement le paiement reçu, selon les règles adoptées par l’association. Le numéro et la carte ne sont créés qu’après ces deux conditions.
7. Afficher le recto-verso, télécharger le PDF et le joindre toi-même à ton email de réponse au membre. Aucun email automatique n’est requis.

L’historique identifie l’import par email et son administrateur. La date affichée pour le consentement correspond à son enregistrement lors de l’import ; elle n’est pas présentée comme une vérification de la date d’envoi du demandeur.

## Paramètres avant les premières cartes

Le montant réel du droit, la devise, les catégories et la validité restent à configurer selon les décisions de l’association. Sans montant configuré, les dossiers peuvent être importés et examinés, mais le paiement et la délivrance de carte restent bloqués. Ne pas réutiliser le tarif fictif des tests. Le [guide technique](ADHESION.md) décrit les variables ; la configuration peut être préparée une fois les valeurs réelles communiquées.

La carte fournie est un **gabarit provisoire**, pas une reproduction certifiée de la maquette validée. Le QR ouvre le site officiel. Imprimer à 100 %, sans ajustement de taille.

## Installation locale si nécessaire

L’environnement Python `.venv` existe sur l’ordinateur où le module a été testé. Sur un autre poste, installer Python 3.12+ puis, depuis `site-web/`, exécuter :

```powershell
python -m venv .venv
.\.venv\Scripts\python -m pip install -r requirements.txt
```

Le lanceur conserve les données dans `site-web/var/`, hors Git et hors publication. Sauvegarder ce dossier de façon privée et cohérente, service arrêté. Ne pas supprimer la base pour changer une configuration ou réinitialiser une numérotation.

## Site publié

Le workflow Pages prépare uniquement les pages, images et scripts publics. La configuration publiée utilise le mode **google**. L’administration, les lecteurs de cartes, le serveur Python, les tests et les données privées ne sont pas inclus dans l’artefact. Les options d’hébergement distant restent disponibles dans le code pour un besoin futur ; elles ne sont pas nécessaires au parcours actuel.

La procédure technique, les quotas et le retour au parcours manuel figurent dans [ENVOI_DIRECT_GOOGLE.md](ENVOI_DIRECT_GOOGLE.md). Le contrôle de réception réel est décrit dans [PUBLICATION_DIRECTE.md](PUBLICATION_DIRECTE.md).
