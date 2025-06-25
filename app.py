# -*- coding: utf-8 -*-
from flask import Flask, request, jsonify, make_response, render_template, redirect
from flask_cors import CORS
import requests
import os
from dotenv import load_dotenv
import json
from datetime import datetime
import secrets
import logging
import sys
import traceback
from logging.handlers import RotatingFileHandler
from supabase.client import create_client, Client
from contextlib import contextmanager

class EmojiFormatter(logging.Formatter):
    """Formateur personnalisé pour ajouter des emojis aux logs"""
    def format(self, record):
        # Ajouter l'emoji par défaut si non spécifié
        if not hasattr(record, 'emoji'):
            record.emoji = '🔵'
        return super().format(record)

def setup_logging(debug_mode):
    """Configure le système de logging"""
    # Créer le dossier logs s'il n'existe pas
    if not os.path.exists('logs'):
        os.makedirs('logs')
    
    # Configuration du format
    log_format = '%(asctime)s [%(levelname)s] %(message)s'
    console_format = '%(asctime)s %(emoji)s %(message)s'
    date_format = '%Y-%m-%d %H:%M:%S'
    
    # Niveau de log basé sur le mode debug
    log_level = logging.DEBUG if debug_mode else logging.INFO
    
    # Configuration du logger principal
    logging.basicConfig(
        level=log_level,
        format=log_format,
        datefmt=date_format,
        encoding='utf-8'
    )
    
    # Logger pour la console avec des emojis
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setLevel(log_level)
    console_handler.setFormatter(EmojiFormatter(
        fmt=console_format,
        datefmt=date_format
    ))
    
    # Logger pour le fichier
    file_handler = RotatingFileHandler(
        'logs/tiktok_api.log',
        maxBytes=1024 * 1024,  # 1 MB
        backupCount=5,
        encoding='utf-8'
    )
    file_handler.setLevel(log_level)
    file_handler.setFormatter(logging.Formatter(log_format))
    
    # Obtenir le logger principal
    logger = logging.getLogger()
    
    # Supprimer les handlers existants
    logger.handlers.clear()
    
    # Ajouter les nouveaux handlers
    logger.addHandler(console_handler)
    logger.addHandler(file_handler)
    
    return logger

# Charger les variables d'environnement
load_dotenv()
debug_mode = os.getenv('DEBUG', 'False').lower() == 'true'
logger = setup_logging(debug_mode)

def log(message, level='info', emoji='ℹ️'):
    """Fonction utilitaire pour les logs avec emojis"""
    logger = logging.getLogger()
    log_method = getattr(logger, level.lower(), logger.info)
    log_method(message, extra={'emoji': emoji})

log("🔧 Démarrage de l'application")

app = Flask(__name__)
CORS(app)

# Configuration Supabase
SUPABASE_URL = os.getenv('SUPABASE_URL')
SUPABASE_KEY = os.getenv('SUPABASE_KEY')

# Configuration TikTok API
TIKTOK_AUTH_URL = "https://www.tiktok.com/v2/auth/authorize/"
TIKTOK_API_URL = "https://open.tiktokapis.com/v2/oauth/token/"
TIKTOK_CLIENT_KEY = os.getenv('TIKTOK_CLIENT_KEY', 'sbawsypybjjzimm3xs')
TIKTOK_CLIENT_SECRET = os.getenv('TIKTOK_CLIENT_SECRET', 'oVlOlWrR1LvLkhN3tfKPxnosTOoTvc9m')
TIKTOK_REDIRECT_URI = os.getenv('TIKTOK_REDIRECT_URI', 'https://141.253.120.227:3000/webhook')

# Vérification des variables d'environnement obligatoires
required_env_vars = {
    'SUPABASE_URL': SUPABASE_URL,
    'SUPABASE_KEY': SUPABASE_KEY,
    'TIKTOK_CLIENT_KEY': TIKTOK_CLIENT_KEY,
    'TIKTOK_CLIENT_SECRET': TIKTOK_CLIENT_SECRET,
    'TIKTOK_REDIRECT_URI': TIKTOK_REDIRECT_URI
}

missing_vars = [var for var, value in required_env_vars.items() if not value]
if missing_vars:
    log(f"❌ Erreur: Variables d'environnement manquantes: {', '.join(missing_vars)}", "error", "💥")
    log("ℹ️ Assurez-vous d'avoir créé un fichier .env à partir de env_example.txt", "info", "💡")
    sys.exit(1)

log(f"📊 Configuration Supabase: URL={SUPABASE_URL}")
supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)

log(f"📊 Configuration Supabase: URL={SUPABASE_URL}")

@contextmanager
def get_db_connection():
    """Gestionnaire de contexte pour la connexion à la base de données"""
    conn = None
    try:
        conn = psycopg2.connect(
            host=DB_HOST,
            port=DB_PORT,
            dbname=DB_NAME,
            user=DB_USER,
            password=DB_PASSWORD,
            cursor_factory=RealDictCursor
        )
        yield conn
    except Exception as e:
        log(f"❌ Erreur de connexion à la base de données: {e}", "error", "💥")
        raise
    finally:
        if conn is not None:
            conn.close()

def get_creator_info(access_token):
    """Récupérer les informations du créateur TikTok"""
    try:
        log("\n🎭 Récupération des informations du créateur...")
        
        headers = {
            'Authorization': f'Bearer {access_token}',
            'Content-Type': 'application/json; charset=UTF-8'
        }
        
        url = 'https://open.tiktokapis.com/v2/post/publish/creator_info/query/'
        
        response = requests.post(url, headers=headers)
        response.raise_for_status()
        
        creator_data = response.json()
        
        if debug_mode:
            log(f"   Données créateur: {json.dumps(creator_data, indent=2)}", "debug", "🔍")
        
        # Vérifier si la réponse est OK
        if creator_data.get('error', {}).get('code') == 'ok':
            return creator_data
        else:
            log(f"❌ Erreur API TikTok: {creator_data.get('error', {}).get('message')}", "error", "💥")
            return None
            
    except Exception as e:
        log(f"❌ Erreur lors de la récupération des informations créateur: {str(e)}", "error", "💥")
        if debug_mode:
            log(traceback.format_exc(), "error", "🔍")
        return None

def save_to_database(token_data):
    """Sauvegarder les données du token et les informations du créateur dans Supabase"""
    try:
        log("\n🔄 Préparation de l'insertion dans Supabase...")
        
        if debug_mode:
            log(f"   Token data brute: {json.dumps(token_data, indent=2)}", "debug", "🔍")
        
        # Récupérer les informations du créateur
        creator_info = get_creator_info(token_data.get('access_token'))
        
        # Désactiver les anciens tokens
        supabase.table('tiktok_tokens').update({
            'is_active': False
        }).eq('open_id', token_data.get('open_id')).execute()
        
        # Préparer les données à insérer
        insert_data = {
            'access_token': token_data.get('access_token'),
            'refresh_token': token_data.get('refresh_token'),
            'expires_in': token_data.get('expires_in'),
            'open_id': token_data.get('open_id'),
            'union_id': token_data.get('union_id'),
            'scope': token_data.get('scope'),
            'created_at': datetime.now().isoformat(),
            'updated_at': datetime.now().isoformat(),
            'is_active': True
        }
        
        # Ajouter les informations du créateur si disponibles
        if creator_info and creator_info.get('data'):
            creator_data = creator_info['data']
            insert_data.update({
                'creator_avatar_url': creator_data.get('creator_avatar_url'),
                'creator_username': creator_data.get('creator_username'),
                'creator_nickname': creator_data.get('creator_nickname'),
                'privacy_level_options': creator_data.get('privacy_level_options'),
                'comment_disabled': creator_data.get('comment_disabled'),
                'duet_disabled': creator_data.get('duet_disabled'),
                'stitch_disabled': creator_data.get('stitch_disabled'),
                'max_video_post_duration_sec': creator_data.get('max_video_post_duration_sec')
            })
            
            log(f"👤 Informations créateur récupérées:")
            log(f"   Username: {creator_data.get('creator_username')}")
            log(f"   Nickname: {creator_data.get('creator_nickname')}")
        
        # Insérer les données
        result = supabase.table('tiktok_tokens').insert(insert_data).execute()
        
        log("✅ Données insérées dans Supabase avec succès")
        if result.data:
            log(f"   ID: {result.data[0].get('id', 'N/A')}")
        
        return True
        
    except Exception as e:
        log(f"❌ ERREUR Supabase: {str(e)}", "error", "💥")
        log(f"   Type d'erreur: {type(e).__name__}", "error", "💥")
        if debug_mode:
            log(f"   Traceback complet:", "error", "🔍")
            import traceback
            log(traceback.format_exc(), "error", "🔍")
        return False

def call_tiktok_api(code):
    """Appeler l'API TikTok pour obtenir le token d'accès"""
    try:
        log("\n🌐 Préparation appel API TikTok...")
        
        headers = {
            'Content-Type': 'application/x-www-form-urlencoded',
            'Cache-Control': 'no-cache'
        }
        
        data = {
            'client_key': TIKTOK_CLIENT_KEY,
            'client_secret': TIKTOK_CLIENT_SECRET,
            'code': code,
            'grant_type': 'authorization_code',
            'redirect_uri': TIKTOK_REDIRECT_URI
        }
        
        if debug_mode:
            log("   Headers de la requête:", "debug", "🔍")
            log(f"   {json.dumps(headers, indent=2)}", "debug", "🔍")
            log("   Données de la requête:", "debug", "🔍")
            masked_data = data.copy()
            masked_data['client_secret'] = '***'
            log(f"   {json.dumps(masked_data, indent=2)}", "debug", "🔍")
        
        log(f"📤 Envoi requête vers {TIKTOK_API_URL}")
        log(f"   Code: {code[:20]}...")
        
        response = requests.post(TIKTOK_API_URL, headers=headers, data=data)
        log(f"📥 Réponse reçue: Status {response.status_code}")
        
        if debug_mode:
            log("   Headers de la réponse:", "debug", "🔍")
            log(f"   {json.dumps(dict(response.headers), indent=2)}", "debug", "🔍")
        
        if response.status_code == 200:
            token_data = response.json()
            log("✅ Token obtenu avec succès")
            log(f"   Access token: {token_data.get('access_token', '')[:10]}...")
            log(f"   Expires in: {token_data.get('expires_in')}")
            
            if debug_mode:
                masked_token_data = token_data.copy()
                masked_token_data['access_token'] = masked_token_data['access_token'][:10] + '...'
                if 'refresh_token' in masked_token_data:
                    masked_token_data['refresh_token'] = masked_token_data['refresh_token'][:10] + '...'
                log(f"   Réponse complète: {json.dumps(masked_token_data, indent=2)}", "debug", "🔍")
            
            return token_data
        else:
            log(f"❌ Erreur API: {response.status_code}", "error", "💥")
            log(f"   Réponse: {response.text}", "error", "💥")
            return None
            
    except Exception as e:
        log(f"❌ ERREUR API: {str(e)}", "error", "💥")
        log(f"   Type d'erreur: {type(e).__name__}", "error", "💥")
        if debug_mode:
            log("   Traceback complet:", "error", "🔍")
            import traceback
            log(traceback.format_exc(), "error", "🔍")
        return None

@app.route('/oauth', methods=['GET'])
def oauth():
    """Démarrer le processus d'authentification TikTok"""
    try:
        log("\n🔐 Démarrage de l'authentification TikTok...")
        
        # Générer un état aléatoire pour la sécurité
        state = secrets.token_urlsafe(32)
        
        # Construire l'URL d'authentification TikTok
        auth_params = {
            'client_key': TIKTOK_CLIENT_KEY,
            'response_type': 'code',
            'scope': 'user.info.basic,video.list',
            'redirect_uri': TIKTOK_REDIRECT_URI,
            'state': state
        }
        
        auth_url = f"{TIKTOK_AUTH_URL}?{'&'.join(f'{k}={v}' for k, v in auth_params.items())}"
        
        if debug_mode:
            log(f"   URL d'authentification: {auth_url}", "debug", "🔍")
        
        # Rediriger directement vers TikTok
        return redirect(auth_url)
        
    except Exception as e:
        log(f"❌ Erreur lors de la création de l'URL d'authentification: {str(e)}", "error", "💥")
        if debug_mode:
            log(traceback.format_exc(), "error", "🔍")
        return render_template('close.html', success=False, message="Erreur lors de l'authentification")

@app.route('/webhook', methods=['GET', 'POST'])
def webhook():
    """Gérer le retour d'authentification TikTok"""
    try:
        log("\n📨 Réception du webhook TikTok...")
        
        # Récupérer le code d'autorisation
        code = request.args.get('code')
        if not code:
            log("❌ Code d'autorisation manquant", "error", "💥")
            return render_template('close.html', success=False, message="Code d'autorisation manquant")
        
        # Appeler l'API TikTok pour échanger le code
        token_data = call_tiktok_api(code)
        if not token_data:
            return render_template('close.html', success=False, message="Erreur lors de l'échange du code")
        
        # Sauvegarder les données dans Supabase
        save_to_database(token_data)
        
        # Retourner une page HTML qui se ferme automatiquement
        return render_template('close.html', success=True)
        
    except Exception as e:
        log(f"❌ Erreur lors du traitement du webhook: {str(e)}", "error", "💥")
        if debug_mode:
            log(traceback.format_exc(), "error", "🔍")
        return render_template('close.html', success=False, message="Une erreur est survenue")

@app.route('/health', methods=['GET'])
def health_check():
    """Endpoint de santé pour vérifier que l'API fonctionne"""
    log("\n💓 Health check appelé")
    try:
        if debug_mode:
            log("   Test de connexion Supabase...", "debug", "🔍")
        
        # Test rapide de connexion Supabase
        result = supabase.table('tiktok_tokens').select('count').execute()
        db_status = "connected"
        token_count = len(result.data) if result.data else 0
        
        if debug_mode:
            log(f"   Nombre de tokens: {token_count}", "debug", "🔍")
            
    except Exception as e:
        log(f"❌ Erreur connexion Supabase: {str(e)}", "error", "💥")
        if debug_mode:
            log("   Traceback complet:", "error", "🔍")
            import traceback
            log(traceback.format_exc(), "error", "🔍")
        db_status = "error"
        token_count = -1
    
    response = {
        'status': 'healthy',
        'timestamp': datetime.now().isoformat(),
        'service': 'TikTok API Webhook',
        'database': {
            'status': db_status,
            'token_count': token_count
        },
        'debug_mode': debug_mode
    }
    
    if debug_mode:
        log(f"   Réponse: {json.dumps(response, indent=2)}", "debug", "🔍")
    return jsonify(response), 200

@app.route('/', methods=['GET'])
def home():
    """Page d'accueil avec bouton de connexion TikTok"""
    log("\n🏠 Page d'accueil appelée")
    return render_template('index.html', 
                         debug_mode=debug_mode,
                         redirect_uri=TIKTOK_REDIRECT_URI)

def get_user_profile(access_token):
    """Récupérer les informations du profil utilisateur TikTok"""
    try:
        log("\n👤 Récupération du profil utilisateur...")
        
        headers = {
            'Authorization': f'Bearer {access_token}',
            'Content-Type': 'application/json'
        }
        
        url = 'https://open.tiktokapis.com/v2/user/info/'
        response = requests.get(url, headers=headers)
        response.raise_for_status()
        
        user_data = response.json()
        
        if debug_mode:
            log(f"   Données utilisateur: {json.dumps(user_data, indent=2)}", "debug", "🔍")
        
        return user_data.get('data', {})
    except Exception as e:
        log(f"❌ Erreur lors de la récupération du profil: {str(e)}", "error", "💥")
        if debug_mode:
            log(traceback.format_exc(), "error", "🔍")
        return None

@app.route('/user/profile', methods=['GET'])
def get_profile():
    """Endpoint pour récupérer le profil de l'utilisateur connecté"""
    try:
        log("\n🎯 Requête de profil utilisateur reçue")
        
        # Récupérer le dernier token actif avec les informations du créateur
        result = supabase.table('tiktok_tokens') \
            .select('*, creator_nickname, creator_avatar_url') \
            .eq('is_active', True) \
            .order('created_at', desc=True) \
            .limit(1) \
            .execute()
        
        if not result.data:
            log("❌ Aucun token actif trouvé", "warning", "⚠️")
            return jsonify({
                'success': False,
                'error': 'Non authentifié'
            }), 401
        
        token_data = result.data[0]
        
        # Construire la réponse avec les données déjà en base
        response_data = {
            'success': True,
            'nickname': token_data.get('creator_nickname', ''),
            'avatar_url': token_data.get('creator_avatar_url', '')
        }
        
        log("✅ Profil utilisateur récupéré avec succès", "info", "🎉")
        return jsonify(response_data)
        
    except Exception as e:
        log(f"❌ Erreur lors de la récupération du profil: {str(e)}", "error", "💥")
        return jsonify({
            'success': False,
            'error': 'Erreur serveur'
        }), 500

@app.route('/logout', methods=['POST'])
def logout():
    """Endpoint pour déconnecter l'utilisateur"""
    try:
        log("\n🚪 Requête de déconnexion reçue")
        
        # Désactiver tous les tokens actifs
        result = supabase.table('tiktok_tokens') \
            .update({'is_active': False}) \
            .eq('is_active', True) \
            .execute()
        
        log("✅ Déconnexion réussie", "info", "🔓")
        return jsonify({
            'success': True,
            'message': 'Déconnecté avec succès'
        })
        
    except Exception as e:
        log(f"❌ Erreur lors de la déconnexion: {str(e)}", "error", "💥")
        return jsonify({
            'success': False,
            'error': 'Erreur serveur'
        }), 500

if __name__ == '__main__':
    log("\n🚀 Démarrage de l'API TikTok Webhook")
    port = int(os.getenv('PORT', 5000))
    
    log(f"📡 Configuration serveur:")
    log(f"   Port: {port}")
    log(f"   Debug: {debug_mode}")
    log(f"   URL: http://0.0.0.0:{port}")
    
    if debug_mode:
        log("\n🔍 Mode DEBUG activé - Logs détaillés activés", "debug", "🔍")
    
    log("\n⏳ Démarrage du serveur...")
    
    # Configuration SSL
    ssl_context = ('certs/cert.pem', 'certs/key.pem')
    
    # Démarrage du serveur en mode HTTPS
    app.run(
        host='0.0.0.0',
        port=port,
        ssl_context=ssl_context,
        debug=debug_mode
    ) 