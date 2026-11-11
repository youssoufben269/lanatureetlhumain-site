# Option gratuite préparée, pas encore activée

Le demandeur a fixé un budget d’hébergement de **0 €**. Le profil proposé réutilise le même module Python : GitHub Pages pour le site, Render **Free** pour le serveur, et Supabase **Free** pour PostgreSQL et les fichiers privés. Aucun service payant, compte ou projet cloud n’a été créé. Les deux comptes ne sont pas une obligation du logiciel : un autre hébergeur compatible peut convenir. Sans autre service, une collecte par email et une gestion locale restent possibles, avec un parcours différent de l’administration complète en ligne.

## Persistance et confidentialité

`render.yaml` ne contient plus de plan payant ni de disque facturé. Le disque `/tmp/lnh-render` sert seulement au rendu temporaire des PDF. `LNH_REQUIRE_REMOTE_STORAGE=1` empêche le démarrage avec un repli involontaire vers une base ou des photos sur ce disque éphémère.

- Les dossiers, numéros, sessions et historique sont dans PostgreSQL, schéma **`lnh_private`**, hors du schéma public. Les tables activent RLS sans politique navigateur. Seul le rôle serveur autorisé doit y accéder.
- Photos et cartes restent dans le bucket **privé** `lnh-private`. Ne pas créer de bucket public ni de politique autorisant anonymement les lectures. Le module sert les objets après son propre contrôle d’accès.
- Les secrets `LNH_DATABASE_URL` et `LNH_SUPABASE_SERVICE_KEY` restent dans l’environnement serveur. Ils ne sont jamais fournis aux scripts du navigateur ni enregistrés dans Git.
- Utiliser la connexion Supabase **Session pooler, port 5432**, compatible IPv4, avec TLS. Le mode Transaction 6543 est refusé car la connexion utilise un schéma et des paramètres de session privés.

## Activation après ouverture des comptes gratuits

1. Le demandeur crée ses comptes Render et Supabase avec les offres Free uniquement, puis donne accès aux projets par les connexions ou le navigateur. Les identifiants et secrets ne doivent pas être collés dans le chat.
2. Dans Supabase Free, créer le projet et le bucket **privé** `lnh-private`. Configurer l’URL du projet, sa clé serveur autorisée et la connexion Session pooler dans les variables privées Render. Ne pas exposer `lnh_private` dans la Data API.
3. Déployer `render.yaml` depuis la branche `codex/adhesion-en-ligne`. Le plan doit rester **free**, sans disque, sans base Render, sans instance supplémentaire et sans option payante. Vérifier le récapitulatif avant toute création. Les migrations PostgreSQL sont appliquées au démarrage par le même service.
4. Render Free n’offrant pas nécessairement de shell, le premier administrateur peut être créé avec les variables privées `LNH_BOOTSTRAP_ADMIN_EMAIL` et `LNH_BOOTSTRAP_ADMIN_PASSWORD`. Le mot de passe doit être choisi par le responsable, au moins 14 caractères. La procédure n’écrase jamais un compte existant. Effacer le mot de passe de l’environnement après la première création ; ne conserver aucun compte ou mot de passe de démonstration.
5. Ajouter le CNAME du seul sous-domaine `adhesions`, vers la destination exacte fournie par Render. Conserver les DNS de `www` et le fichier `CNAME` actuels. Attendre la validation HTTPS de `adhesions.lanatureetlhumain.org`.
6. Vérifier l’adresse client derrière le proxy Render avant ouverture : ne pas faire confiance aveuglément à un en-tête transmis par le visiteur. La configuration actuelle conserve le filtrage des en-têtes non fiables ; un éventuel regroupement des limites par IP doit être résolu avec les garanties du proxy réellement observées.
7. Configurer `adhesion/assets/config.js` avec l’URL HTTPS du service. Dans GitHub Pages, passer de `main / (root)` à **GitHub Actions** avant fusion sur `main`. Le workflow publie seulement les fichiers publics.
8. Tester depuis le site public : demande/photo/consentement, administration, fonction, validation, paiement manuel, numérotation, PDF, déconnexion et refus. Redéployer le serveur et vérifier que les dossiers et fichiers restent accessibles. Configurer les catégories, le droit et la validité réellement adoptés avant toute délivrance. Le gabarit de carte demeure provisoire.

Le budget nul concerne l’hébergement ; les règles de validation et de paiement manuel de l’adhésion n’ont pas été supprimées. Aucun prestataire de paiement n’est ajouté. Les emails restent désactivés sans SMTP compatible configuré ; l’administration peut télécharger les cartes.

## Limites des offres gratuites

Render Free met le service en veille après inactivité : le premier appel peut demander environ une minute de réveil. Supabase Free fournit actuellement 500 Mo de base et 1 Go de fichiers, avec des quotas et une mise en pause possible après sept jours de faible activité. Une remise en route peut nécessiter une action du responsable. Il ne faut pas présenter cette configuration comme une disponibilité garantie. Aucun dispositif artificiel de maintien éveillé n’est ajouté.

Sources vérifiées le 11 novembre 2026 : [Render Free](https://render.com/docs/free), [quotas Supabase](https://supabase.com/docs/guides/platform/billing-on-supabase), [mise en pause](https://supabase.com/docs/guides/platform/free-project-pausing), [connexion PostgreSQL](https://supabase.com/docs/guides/database/connecting-to-postgres), [stockage privé](https://supabase.com/docs/guides/storage/buckets/fundamentals).

## État réel

Code préparé, tests locaux et parcours PostgreSQL de QA effectués. Aucun accès aux comptes Render/Supabase n’est disponible ; aucun serveur, base, bucket ou DNS cloud n’a été créé. `main` et le site publié n’ont pas été modifiés. L’activation publique reste à faire après choix de cette option et accès aux comptes gratuits.
