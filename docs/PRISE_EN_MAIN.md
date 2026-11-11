# Utiliser les adhésions

Le formulaire, les cartes et le site sont dans le même projet. La fonction est attribuée par l’association, jamais par le demandeur.

## Au quotidien

1. Le candidat ouvre `/adhesion/`, renseigne ses informations, ajoute sa photo et envoie sa demande.
2. Tu ouvres `/admin/adhesions/` avec ton compte administrateur.
3. Tu vérifies la photo et le dossier, puis tu renseignes la fonction attribuée par l’association.
4. Tu valides la demande et confirmes le paiement reçu en indiquant sa référence. L’ordre de ces deux actions est libre.
5. La carte et le numéro sont créés automatiquement lorsque les deux conditions sont remplies. Tu peux afficher le recto-verso et télécharger le PDF.

Un refus nécessite un motif. Si la génération rencontre un problème, le numéro est conservé et tu peux réessayer depuis la fiche.

## Avant l’ouverture au public

Le développeur configure le serveur, le stockage privé, le montant et la devise du droit, les catégories de membres, la durée de validité et le compte administrateur. L’envoi d’emails nécessite un service SMTP configuré. Aucun prestataire de paiement en ligne n’est imposé.

GitHub Pages seul ne suffit pas : le service Python doit être hébergé avec un disque persistant. Le [guide technique](ADHESION.md) décrit les deux options d’hébergement et les commandes.

Le gabarit de carte fourni respecte le format ID-1, utilise le logo du site et le slogan officiel. Sa mise en page doit encore être confrontée au fichier de la maquette validée, qui n’était pas disponible. Imprime les cartes à 100 %, sans ajustement de taille.
