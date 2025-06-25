# TikTok API Integration

Une intégration élégante de l'API TikTok avec authentification OAuth et interface utilisateur moderne.

## Fonctionnalités

- 🔐 Authentification OAuth TikTok
- 👤 Affichage du profil utilisateur
- 🎨 Interface utilisateur moderne style Apple
- 🔄 Gestion automatique des tokens
- 📱 Design responsive
- 🔒 Sécurité renforcée

## Configuration Technique

### Prérequis

```bash
pip install -r requirements.txt
```

### Variables d'Environnement

Créez un fichier `.env` avec :

```env
TIKTOK_CLIENT_KEY=votre_client_key
TIKTOK_CLIENT_SECRET=votre_client_secret
TIKTOK_REDIRECT_URI=https://votre-domaine.com/webhook
SUPABASE_URL=votre_url_supabase
SUPABASE_KEY=votre_key_supabase
DEBUG=False
```

### Base de Données

La table Supabase `tiktok_tokens` doit contenir :

```sql
- access_token (text)
- refresh_token (text)
- expires_in (integer)
- open_id (text)
- creator_nickname (text)
- creator_avatar_url (text)
- is_active (boolean)
- created_at (timestamp)
```

## Routes API

### `/oauth` (GET)
- Initialise le processus d'authentification TikTok
- Retourne l'URL de redirection TikTok

### `/webhook` (GET)
- Gère le retour d'authentification TikTok
- Sauvegarde les informations du créateur
- Redirige vers la page d'accueil

### `/user/profile` (GET)
- Retourne les informations du profil utilisateur
- Format de réponse :
```json
{
    "success": true,
    "nickname": "nom_utilisateur",
    "avatar_url": "url_avatar"
}
```

### `/logout` (POST)
- Déconnecte l'utilisateur
- Désactive le token actif

## Interface Utilisateur

### Design Moderne
- Dégradé de fond animé
- Effet glassmorphism
- Animations fluides
- Police système optimisée
- Support du mode sombre

### Composants

#### Bouton de Connexion
```html
<button class="tiktok-button">
    <svg><!-- Icon TikTok --></svg>
    Se connecter
</button>
```

#### Section Profil
```html
<div class="profile-container">
    <img class="profile-avatar" src="avatar_url">
    <div class="profile-info">
        <div class="profile-nickname">Nom d'utilisateur</div>
        <div class="profile-status">Compte connecté</div>
    </div>
</div>
```

### Styles CSS Principaux

```css
:root {
    --background: #000000;
    --text: #FFFFFF;
    --text-secondary: #86868B;
}

body {
    background: linear-gradient(135deg, #000000, #1a1a1a, #000B1F, #001F3F);
    background-size: 400% 400%;
    animation: gradientBG 15s ease infinite;
}

.tiktok-button {
    background: rgba(255, 255, 255, 0.1);
    backdrop-filter: blur(10px);
    border: 1px solid rgba(255, 255, 255, 0.2);
    border-radius: 980px;
}
```

## Flux d'Authentification

1. L'utilisateur clique sur "Se connecter"
2. Redirection vers l'authentification TikTok
3. TikTok redirige vers `/webhook` avec le code
4. Le backend traite l'authentification et sauvegarde les données
5. Redirection automatique vers la page d'accueil
6. Affichage du profil utilisateur

## Sécurité

- Tokens stockés de manière sécurisée
- Gestion automatique des expirations
- Protection CSRF
- Headers sécurisés
- HTTPS obligatoire

## Personnalisation

### Couleurs
Modifiez les variables CSS dans `:root` :
```css
:root {
    --background: votre_couleur;
    --text: votre_couleur;
    --text-secondary: votre_couleur;
}
```

### Animations
Ajustez les durées d'animation :
```css
.profile-container {
    animation: fadeIn 0.8s cubic-bezier(0.28, 0.11, 0.32, 1);
}
```

## Support des Appareils

- 📱 Mobile (>320px)
- 💻 Tablette (>768px)
- 🖥️ Desktop (>1024px)
- Support des préférences de mouvement réduites
- Support du mode sombre système

## Développement

```bash
# Installation
pip install -r requirements.txt

# Générer les certificats SSL
python generate_cert.py

# Démarrer le serveur
python start.py
```

## Logs

Les logs sont stockés dans `/logs/tiktok_api.log` avec rotation automatique.

## Contribution

1. Fork le projet
2. Créez votre branche (`git checkout -b feature/AmazingFeature`)
3. Commit vos changements (`git commit -m 'Add some AmazingFeature'`)
4. Push vers la branche (`git push origin feature/AmazingFeature`)
5. Ouvrez une Pull Request
``` 