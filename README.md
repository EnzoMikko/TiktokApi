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

## Implémentation Frontend

### Structure HTML Essentielle
```html
<!DOCTYPE html>
<html lang="fr">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>TikTok Login</title>
    <!-- Police Inter de Google Fonts -->
    <link rel="preconnect" href="https://fonts.googleapis.com">
    <link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
    <link href="https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&display=swap" rel="stylesheet">
    <style>
        /* Styles CSS ici */
    </style>
</head>
<body>
    <!-- Formes d'arrière-plan animées -->
    <div class="background-shapes">
        <div class="shape shape-1"></div>
        <div class="shape shape-2"></div>
    </div>

    <!-- Conteneur principal -->
    <div class="container">
        <!-- Logo et titre -->
        <div class="logo-container">
            <h1>TikTok Login</h1>
            <p class="subtitle">Connectez-vous avec votre compte TikTok</p>
        </div>

        <!-- Bouton de connexion -->
        <button onclick="startOAuth()" class="tiktok-button">
            Se connecter avec TikTok
        </button>

        <!-- Information de debug (optionnel) -->
        {% if debug_mode %}
        <div class="debug-info">
            <p>Mode Debug: Activé</p>
            <p>Redirect URI: {{ redirect_uri }}</p>
        </div>
        {% endif %}
    </div>
</body>
</html>
```

### Styles CSS Essentiels
```css
:root {
    --primary: #8B5CF6;
    --primary-dark: #7C3AED;
    --background: #1A1A2E;
    --text: #E2E8F0;
    --text-secondary: #94A3B8;
}

body {
    font-family: 'Inter', sans-serif;
    background: linear-gradient(135deg, var(--background), #2D1B69);
    color: var(--text);
    min-height: 100vh;
    display: flex;
    align-items: center;
    justify-content: center;
    padding: 1rem;
}

.container {
    background: rgba(42, 42, 62, 0.7);
    backdrop-filter: blur(20px);
    padding: 3rem;
    border-radius: 24px;
    text-align: center;
    max-width: 420px;
    border: 1px solid rgba(255, 255, 255, 0.1);
}

.tiktok-button {
    display: inline-flex;
    align-items: center;
    justify-content: center;
    padding: 0.875rem 2rem;
    background: linear-gradient(135deg, var(--primary), var(--primary-dark));
    color: white;
    border: none;
    border-radius: 16px;
    font-weight: 600;
    cursor: pointer;
    width: 100%;
}

/* Styles pour l'effet glassmorphism */
.background-shapes {
    position: absolute;
    width: 100%;
    height: 100%;
    overflow: hidden;
    z-index: 0;
}

.shape {
    position: absolute;
    background: var(--primary);
    filter: blur(80px);
    opacity: 0.2;
    border-radius: 50%;
}
```

### JavaScript Minimal
```javascript
async function startOAuth() {
    try {
        const response = await fetch('https://141.253.120.227:3000/oauth');
        const data = await response.json();
        
        if (data.redirect_url) {
            window.location.href = data.redirect_url;
        } else {
            throw new Error('URL de redirection non trouvée');
        }
    } catch (error) {
        console.error('Erreur:', error);
        alert('Erreur de connexion TikTok');
    }
}
```

### Points Clés de l'Implémentation

1. **Structure de Base**
   - Utilisation de la police Inter de Google Fonts
   - Conteneur principal avec effet glassmorphism
   - Formes d'arrière-plan animées pour un effet dynamique

2. **Design Moderne**
   - Interface sombre avec effet de flou
   - Dégradés et effets de survol
   - Bouton de connexion stylisé
   - Responsive design

3. **Fonctionnalités**
   - Bouton de connexion TikTok
   - Mode debug conditionnel
   - Gestion des erreurs de base

4. **Sécurité**
   - Viewport sécurisé
   - Gestion asynchrone de l'OAuth
   - Support pour le mode debug
``` 