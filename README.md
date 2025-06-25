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

## Documentation détaillée des endpoints

### 1. Page d'accueil (`GET /`)
```http
GET / HTTP/1.1
Host: localhost:5000
```
**Réponse** : Page HTML avec le bouton de connexion TikTok

### 2. Démarrage OAuth (`GET /oauth`)
```http
GET /oauth HTTP/1.1
Host: localhost:5000
```

**Réponse** : Redirection vers TikTok
```http
HTTP/1.1 302 Found
Location: https://www.tiktok.com/v2/auth/authorize/?client_key=YOUR_CLIENT_KEY&response_type=code&scope=user.info.basic,video.list&redirect_uri=YOUR_REDIRECT_URI&state=RANDOM_STATE
```

### 3. Webhook (`GET /webhook`)
#### Réception du code d'autorisation
```http
GET /webhook?code=AUTH_CODE&state=RANDOM_STATE HTTP/1.1
Host: localhost:5000
```

#### Échange du code contre un token (Appel à l'API TikTok)
**Requête vers TikTok**
```http
POST https://open.tiktokapis.com/v2/oauth/token/
Content-Type: application/x-www-form-urlencoded

client_key=YOUR_CLIENT_KEY
&client_secret=YOUR_CLIENT_SECRET
&code=AUTH_CODE
&grant_type=authorization_code
```

**Réponse de TikTok**
```json
{
    "access_token": "act.xxx...",
    "refresh_token": "rft.xxx...",
    "open_id": "USER_OPEN_ID",
    "expires_in": 86400,
    "scope": "user.info.basic,video.list"
}
```

#### Récupération des informations du créateur (Appel à l'API TikTok)
**Requête vers TikTok**
```http
POST https://open.tiktokapis.com/v2/post/publish/creator_info/query/
Content-Type: application/json
Authorization: Bearer act.xxx...
```

**Réponse de TikTok**
```json
{
   "data": {
      "creator_avatar_url": "https://...",
      "creator_username": "username",
      "creator_nickname": "Nickname",
      "privacy_level_options": ["PUBLIC_TO_EVERYONE", "MUTUAL_FOLLOW_FRIENDS", "SELF_ONLY"],
      "comment_disabled": false,
      "duet_disabled": false,
      "stitch_disabled": true,
      "max_video_post_duration_sec": 300
   },
   "error": {
      "code": "ok",
      "message": "",
      "log_id": "202210112248442CB9319E1FB30C1073F3"
   }
}
```

**Réponse finale du webhook**
```json
{
    "status": "success",
    "message": "Token stored successfully"
}
```

### 4. Vérification de santé (`GET /health`)
```http
GET /health HTTP/1.1
Host: localhost:5000
```

**Réponse**
```json
{
    "status": "healthy",
    "timestamp": "2024-03-25T10:30:00Z"
}
```

## Structure des données Supabase

### Table: tiktok_tokens
Voici la structure des données stockées dans Supabase après une authentification réussie :

```json
{
    "id": "uuid",
    "access_token": "act.xxx...",
    "refresh_token": "rft.xxx...",
    "expires_in": 86400,
    "open_id": "USER_OPEN_ID",
    "union_id": "UNION_ID",
    "scope": "user.info.basic,video.list",
    "creator_avatar_url": "https://...",
    "creator_username": "username",
    "creator_nickname": "Nickname",
    "privacy_level_options": ["PUBLIC_TO_EVERYONE", "MUTUAL_FOLLOW_FRIENDS", "SELF_ONLY"],
    "comment_disabled": false,
    "duet_disabled": false,
    "stitch_disabled": true,
    "max_video_post_duration_sec": 300,
    "created_at": "2024-03-25T10:30:00Z",
    "updated_at": "2024-03-25T10:30:00Z",
    "is_active": true
}
```

## Gestion des erreurs

### 1. Erreur d'authentification TikTok
```json
{
    "error": {
        "code": "auth_error",
        "message": "Invalid authorization code"
    }
}
```

### 2. Erreur de token expiré
```json
{
    "error": {
        "code": "token_expired",
        "message": "Access token has expired"
    }
}
```

### 3. Erreur de base de données
```json
{
    "error": {
        "code": "database_error",
        "message": "Failed to store token in database"
    }
}
``` 