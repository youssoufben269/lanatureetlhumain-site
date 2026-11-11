# Mise à jour et hébergement

## État vérifié le 11 novembre 2026

- Branche locale : `codex/adhesion-en-ligne`, actualisée sur `origin/main` `82f0ad0`. Le distant comporte deux commits après `ecb0626` : section don/nettoyage institutionnel, puis coordonnées de Marseille. Ils sont conservés.
- Le module et les corrections sont préparés sur `codex/adhesion-en-ligne` pour leur transfert au dépôt. Un stash de précaution conserve les modifications suivies antérieures à l’actualisation. La mise en ligne du service reste à effectuer après choix de l’hébergement.
- `https://www.lanatureetlhumain.org/` répond HTTP 200 ; le domaine sans `www` redirige vers cette adresse. Les DNS publics pointent vers GitHub Pages. `/adhesion/` répond 404 : le module n’est pas publié.
- L’accueil public annoncé par HTTP pèse 10 982 788 octets. Un téléchargement avec compression a reçu seulement 1 740 288 octets en 45 secondes, malgré un premier octet à 0,78 seconde. Ce test constate une lenteur de transfert sur la connexion testée, sans isoler l’opérateur réseau. La version locale externalise les mêmes photographies et conserve les octets du logo : environ 74 Ko de HTML et 1,16 Mo d’images au total, au lieu de près de 11 Mo intégrés au HTML.

## Architecture retenue pour la préparation

Conserver le site public et `www` sur GitHub Pages. Héberger le service Python sur **une seule instance Linux avec disque persistant**, derrière HTTPS, à `https://adhesions.lanatureetlhumain.org`. Le disque privé doit survivre aux redémarrages et redéploiements. Un serveur privé avec Nginx et systemd convient ; aucun fournisseur ni abonnement n’a été créé.

Les formulaires publics peuvent rester dans Pages avec `window.LNH_API_BASE = 'https://adhesions.lanatureetlhumain.org'` dans `adhesion/assets/config.js`. L’administration et les liens privés de carte peuvent aussi être ouverts directement sur le sous-domaine, ce qui évite une dépendance aux cookies entre origines pour l’usage administratif. Le service sert uniquement ses routes autorisées. Ne jamais monter tout le dépôt dans une racine publique.

## Ordre de mise en service

Paramètres GitHub observés : Pages publie actuellement `main` depuis `/ (root)` ; le domaine et HTTPS sont corrects. Ne pas fusionner tous les fichiers du module dans cette source publique brute. Passer à GitHub Actions avant la fusion sur `main` et utiliser le workflow qui sélectionne les fichiers publics.

1. Fournir l’hébergement Linux, l’accès administrateur serveur et une destination de sauvegarde. Créer un compte système `lnh`, installer Python 3.12+, copier les sources dans `/opt/lnh/site-web` et installer `requirements.txt` dans un environnement virtuel. Ne pas transférer `.qa/`, `.venv/`, `.pages-build/`, les tests de démonstration ou leur base.
2. Créer `/srv/lnh-private`, propriétaire `lnh`, mode 700. Y conserver SQLite, les photos et les PDF. Le fichier `/etc/lnh/membership.env`, lisible seulement par le responsable serveur et le service, contient les paramètres réels. `.env.example` sert de modèle, pas de configuration active.
3. Configurer `LNH_MODULE_ORIGIN=https://adhesions.lanatureetlhumain.org`, `LNH_ALLOWED_ORIGINS=https://www.lanatureetlhumain.org`, `LNH_WEBSITE_URL=https://www.lanatureetlhumain.org`, `LNH_DATA_DIR=/srv/lnh-private` et `LNH_TRUSTED_PROXY=127.0.0.1`. Renseigner les catégories, le droit en unité minimale, la devise, la durée, le fuseau et la politique de conservation réellement adoptés. Les valeurs de QA ne sont pas des paramètres de production.
4. Sous ce compte et avec le même environnement, exécuter `python -m membership migrate`, puis `python -m membership create-admin --email ADRESSE_REELLE`. La commande demande le mot de passe sans l’afficher. Aucun compte de QA ne doit être réutilisé.
5. Installer et adapter `deploy/lnh-membership.service`. Le service écoute uniquement sur `127.0.0.1:8787`. Adapter `deploy/nginx-membership.conf` au certificat réel. Ajouter seulement le DNS du nouveau sous-domaine, sans modifier le domaine principal ni `CNAME`. Installer un certificat valide et vérifier `/api/health` depuis HTTPS.
6. Tester d’abord le formulaire et l’administration sur le sous-domaine : validation, paiement manuel, aperçu, téléchargement, déconnexion et refus. Tester aussi la restauration de la sauvegarde. Confronter le gabarit de carte à la maquette approuvée avant impression en série.
7. Configurer l’URL API dans `adhesion/assets/config.js`. Dans GitHub, vérifier que **Settings > Pages > Source** utilise **GitHub Actions**, puis publier les changements après revue. Le workflow `pages.yml` utilise `scripts/prepare_public.py`, qui copie une liste de fichiers publics dans `.pages-build/`. Ne pas choisir une publication brute de toute la racine du dépôt.
8. Vérifier le site public sur ordinateur et téléphone : accueil, photos, don, contact, FR/EN, lien Adhérer, transmission au service, cookies, accès administrateur et ressources PDF.js. Le contact existant reste en mode email prérempli tant qu’aucun endpoint officiel n’est configuré.

L’exécution locale de `python scripts/prepare_public.py` prépare les fichiers Pages, sans rien publier. Les quatre ressources dans `assets/` doivent accompagner `index.html` ; remplacer uniquement le HTML ne suffit plus.

## Emails et exploitation

Aucun SMTP n’est configuré dans l’environnement vérifié. Aucun message réel n’a été envoyé. Pour activer les notifications, configurer les variables SMTP chiffrées puis planifier `python -m membership flush-email` avec le même compte, la même configuration et le même stockage. Les secrets ne passent ni dans Git ni dans les journaux.

Le worker coordonne l’envoi avec un refus sous verrou SQLite. Un envoi déjà engagé précède donc le refus ; un email déjà accepté par le serveur ne peut pas être rappelé. Pour ce petit service, le verrou est tenu pendant le transport. Le timeout réseau vaut 30 secondes par opération, sans plafond global de livraison : le worker peut retarder brièvement les autres écritures. Surveiller ce point avant toute hausse de volume. Les reprises après un arrêt SMTP peuvent produire un doublon ; le Message-ID reste stable.

Les jetons de carte restent privés, expirent sept jours après leur prise en charge pour expédition et ne sont jamais recréés après révocation. Sans SMTP, les liens préparés à la génération restent utilisables sept jours ; l’administration conserve son accès protégé. Prévoir des sauvegardes cohérentes de SQLite et des fichiers liés, et limiter le serveur à une instance avec disque local.

## Accès et décisions encore nécessaires

La lecture du dépôt distant fonctionne. Aucun accès à l’hébergement Python, au DNS du sous-domaine, à l’installation du certificat, aux paramètres Pages ou à un SMTP n’a été utilisé. Leur configuration et les essais HTTPS réels restent à faire. Aucun montant, catégorie définitive, signature autorisée ou fichier de maquette validée n’a été fourni dans cette intervention. Aucun déploiement n’a été effectué.
