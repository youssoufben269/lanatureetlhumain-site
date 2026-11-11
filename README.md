# Administration du site La Nature et l'Humain

Le module d’adhésion, son administration et le générateur de cartes sont intégrés à ce dépôt. Consulte [le guide d’utilisation et de configuration](docs/ADHESION.md). L’interface publique se trouve dans `adhesion/`, l’administration dans `admin/adhesions/`, le service privé dans `membership/`. Un service Python avec stockage persistant est nécessaire en plus de GitHub Pages.

La branche `codex/adhesion-en-ligne` a été actualisée sur `origin/main` `82f0ad0` le 11 novembre 2026 et prépare le module pour publication. Son hébergement Python reste à configurer avant activation sur le site. Voir [les vérifications](docs/VALIDATION.md) et [la procédure de déploiement](docs/DEPLOIEMENT.md).

Ce dépôt contient le site public de l'association.

Adresse en ligne :
https://www.lanatureetlhumain.org/

## Fichiers importants

- `index.html` : page principale du site.
- `assets/` : photographies optimisées de l’accueil et logo officiel, nécessaires à son affichage.
- `scripts/prepare_public.py` : préparation du seul contenu public pour Pages.
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

1. Comparer avec la dernière version distante et conserver ses changements.
2. Transférer les fichiers du site et toutes leurs ressources, notamment `assets/`, `adhesion/` et `admin/adhesions/`. Garder `CNAME` tel quel.
3. Configurer et vérifier le service Python avant de rendre le formulaire accessible au public.
4. Sélectionner GitHub Actions comme source Pages et utiliser le workflow fourni, qui publie uniquement `.pages-build/`. Suivre `docs/DEPLOIEMENT.md` avant le premier push sur `main`.

## Ce qu'il vaut mieux éviter

- Ne pas renommer `index.html`.
- Ne pas supprimer `CNAME`.
- Ne pas changer le domaine dans GitHub Pages sans raison.
- Ne pas modifier les DNS si le site fonctionne déjà.

## Limite actuelle

L’accueil reste statique. Le tableau de bord des adhésions se trouve à `/admin/adhesions/` et nécessite le service Python décrit dans `docs/ADHESION.md`.

Pour publier des actualités régulièrement ou permettre à plusieurs personnes de modifier le contenu sans toucher au code, envisager plus tard un CMS comme WordPress, Webflow, Framer ou Decap CMS.

## Formulaire de contact

Le site contient un formulaire de contact.

GitHub Pages étant un hébergement statique, il ne peut pas envoyer les messages directement. Pour activer l'envoi depuis le site, utiliser un service externe comme Formspree.

Étapes recommandées :

1. Créer un compte sur https://formspree.io/
2. Créer un nouveau formulaire.
3. Copier l'endpoint officiel fourni, au format :
   `https://formspree.io/f/xxxxxxxx`
4. Ouvrir `index.html`.
5. Chercher :
   `id="contact-form" data-endpoint=""`
6. Remplacer uniquement la valeur vide par l'endpoint officiel.
7. Enregistrer avec `Commit changes`.

Ne jamais inventer d'endpoint Formspree. Tant que l'endpoint officiel n'a pas été créé, conserver `data-endpoint=""`.

Tant que `data-endpoint` est vide, le formulaire ouvre un email prérempli vers `contact@lanatureetlhumain.org`.
