# Administration du site La Nature et l'Humain

Ce dépôt contient le site public de l'association.

Adresse en ligne :
https://www.lanatureetlhumain.org/

## Fichiers importants

- `index.html` : page principale du site.
- `CNAME` : domaine personnalisé utilisé par GitHub Pages.

Ne pas supprimer le fichier `CNAME`. Il permet à GitHub Pages de garder le domaine `www.lanatureetlhumain.org`.

## Modifier le site

Pour changer un texte, une adresse, un téléphone ou une section :

1. Ouvrir le dépôt GitHub.
2. Cliquer sur `index.html`.
3. Cliquer sur l’icône crayon pour modifier.
4. Chercher le texte à remplacer.
5. Enregistrer avec `Commit changes`.
6. Attendre quelques secondes ou minutes.
7. Vérifier le résultat sur https://www.lanatureetlhumain.org/

## Mettre à jour depuis une nouvelle version préparée

Si une nouvelle version du site est générée localement :

1. Remplacer le fichier `index.html` du dépôt GitHub par la nouvelle version.
2. Garder le fichier `CNAME` tel quel.
3. Enregistrer la modification.
4. GitHub Pages republie automatiquement le site.

## Ce qu'il vaut mieux éviter

- Ne pas renommer `index.html`.
- Ne pas supprimer `CNAME`.
- Ne pas changer le domaine dans GitHub Pages sans raison.
- Ne pas modifier les DNS si le site fonctionne déjà.

## Limite actuelle

Le site est statique. Il n'a pas encore de tableau de bord interne.

Pour publier des actualités régulièrement ou permettre à plusieurs personnes de modifier le contenu sans toucher au code, envisager plus tard un CMS comme WordPress, Webflow, Framer ou Decap CMS.
