# TikTok API Webhook

API Flask pour gérer l'authentification TikTok avec stockage des tokens et informations du créateur dans Supabase.

## Fonctionnalités

- Authentification TikTok Login Kit Web
- Stockage sécurisé des tokens dans Supabase
- Récupération des informations du créateur TikTok
- Support HTTPS avec certificat auto-signé (développement)
- Protection CSRF
- Mode debug avec logs détaillés
- Interface utilisateur moderne pour la connexion

## Configuration requise

- Python 3.8+
- Un compte Supabase
- Un compte développeur TikTok
- OpenSSL (pour le certificat HTTPS)

## Installation

1. Cloner le repository :
```bash
git clone <votre-repo>
cd TiktokApi
```

2. Créer un environnement virtuel :
```bash
python -m venv venv
source venv/bin/activate  # Linux/Mac
venv\Scripts\activate     # Windows
```

3. Installer les dépendances :
```bash
pip install -r requirements.txt
```

4. Copier le fichier d'exemple d'environnement :
```bash
cp env_example.txt .env
```

5. Configurer les variables d'environnement dans `.env` :
```
DEBUG=True

# Supabase Configuration
SUPABASE_URL=votre_url_supabase
SUPABASE_KEY=votre_cle_supabase

# TikTok API Configuration
TIKTOK_CLIENT_KEY=votre_client_key
TIKTOK_CLIENT_SECRET=votre_client_secret
TIKTOK_REDIRECT_URI=votre_redirect_uri

# Server Configuration
PORT=5000
```

6. Générer le certificat SSL pour le développement :
```bash
python generate_cert.py
```

## Structure du projet

```
TiktokApi/
├── app.py              # Application principale Flask
├── generate_cert.py    # Générateur de certificat SSL
├── env_example.txt     # Exemple de configuration
├── requirements.txt    # Dépendances Python
├── certs/             # Certificats SSL
│   ├── cert.pem       # Certificat public
│   └── key.pem        # Clé privée
├── templates/          # Templates HTML
│   └── index.html     # Page de connexion
└── logs/              # Logs de l'application
```

## Utilisation

1. Démarrer l'application :
```bash
python app.py
```

2. Accéder à l'interface web (HTTPS) :
```
https://localhost:5000
```

Note : Comme nous utilisons un certificat auto-signé pour le développement, votre navigateur affichera un avertissement de sécurité. C'est normal, vous pouvez continuer en ajoutant une exception.

3. Cliquer sur le bouton de connexion TikTok pour démarrer le flux d'authentification

## Endpoints API

- `GET /` : Page d'accueil avec bouton de connexion
- `GET /oauth` : Démarrage du flux d'authentification TikTok
- `GET/POST /webhook` : Endpoint pour recevoir le code d'autorisation
- `GET /health` : Vérification de l'état de l'API

## Informations stockées

Pour chaque utilisateur connecté, nous stockons :
- Token d'accès et de rafraîchissement
- URL de l'avatar du créateur
- Nom d'utilisateur et surnom
- Options de confidentialité
- États des fonctionnalités (commentaires, duets, stitches)
- Durée maximale des vidéos autorisée

## Logs

Les logs sont stockés dans le dossier `logs/` avec rotation automatique des fichiers.
En mode debug, des logs détaillés sont disponibles dans la console et les fichiers.

## Sécurité

- Support HTTPS pour le développement
- Protection CSRF sur le flux d'authentification
- Stockage sécurisé des tokens dans Supabase
- Gestion des tokens expirés
- Validation des données entrantes

## Support

Pour toute question ou problème, veuillez ouvrir une issue sur le repository. 