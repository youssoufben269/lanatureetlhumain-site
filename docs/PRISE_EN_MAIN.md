# Demandes par email, cartes sur ton ordinateur

Le parcours choisi ne nécessite aucun nouveau compte de service et aucun hébergement payant. Le site prépare les dossiers ; tu reçois les emails sur **lanaturetlhumain@gmail.com** et tu traites les demandes localement.

## Pour le demandeur

1. Ouvrir la rubrique **Adhérer** du site et remplir le formulaire avec la photo et le consentement.
2. Cliquer sur **Préparer mon email**, puis **Télécharger mon dossier**. Ce fichier contient les informations et la photo ; celle-ci est redimensionnée et réencodée sans métadonnées EXIF.
3. Cliquer sur **Ouvrir ma messagerie**, joindre le dossier téléchargé au message et l’envoyer. La pièce jointe n’est pas ajoutée automatiquement.

Si aucune messagerie ne s’ouvre, l’adresse et le texte à copier sont affichés. Le site ne prétend jamais que le message est envoyé ou reçu. Les données ne sont enregistrées ni sur GitHub ni dans le stockage du navigateur.

## Pour toi

1. Dans Gmail, télécharger le dossier joint dans un emplacement privé sur ton ordinateur. Ne le copier ni dans Git ni dans les fichiers publics du site.
2. Double-cliquer sur **GERER_ADHESIONS.cmd**, à la racine de `site-web/`. Garder la fenêtre ouverte pendant l’utilisation.
3. Au premier lancement, choisir ton email et un mot de passe local d’au moins 14 caractères. Ce compte protège l’administration de ton ordinateur ; il ne crée aucun compte chez un fournisseur.
4. Se connecter à l’administration qui s’ouvre, sélectionner le fichier reçu dans **Dossier reçu par email**, confirmer sa vérification et cliquer sur **Importer le dossier**.
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

Le workflow Pages prépare uniquement les pages, images et scripts publics. La configuration publiée utilise le mode **email**. L’administration, les lecteurs de cartes, le serveur Python, les tests et les données privées ne sont pas inclus dans l’artefact. Les options d’hébergement distant restent disponibles dans le code pour un besoin futur ; elles ne sont pas nécessaires au parcours actuel.
