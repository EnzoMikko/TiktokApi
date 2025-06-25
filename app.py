# -*- coding: utf-8 -*-
from flask import Flask, request, jsonify, make_response, render_template
from flask_cors import CORS
import requests
import os
from dotenv import load_dotenv
import json
from datetime import datetime
import secrets
import logging
import sys
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
TIKTOK_REDIRECT_URI = os.getenv('TIKTOK_REDIRECT_URI', 'https://mikkon8n.app.n8n.cloud/webhook-test/36b971b6-d5a3-4153-a36f-18d4904c40d1')

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

def save_to_database(token_data):
    """Sauvegarder les données du token dans Supabase"""
    try:
        log("\n🔄 Préparation de l'insertion dans Supabase...")
        
        if debug_mode:
            log(f"   Token data brute: {json.dumps(token_data, indent=2)}", "debug", "🔍")
        
        log(f"   Token data: access_token={token_data.get('access_token')[:10]}...")
        log(f"   expires_in={token_data.get('expires_in')}")
        log(f"   open_id={token_data.get('open_id')}")
        
        # Désactiver les anciens tokens
        supabase.table('tiktok_tokens').update({
            'is_active': False
        }).eq('open_id', token_data.get('open_id')).execute()
        
        # Insérer le nouveau token
        result = supabase.table('tiktok_tokens').insert({
            'access_token': token_data.get('access_token'),
            'refresh_token': token_data.get('refresh_token'),
            'expires_in': token_data.get('expires_in'),
            'open_id': token_data.get('open_id'),
            'union_id': token_data.get('union_id'),
            'scope': token_data.get('scope'),
            'created_at': datetime.now().isoformat(),
            'updated_at': datetime.now().isoformat(),
            'is_active': True
        }).execute()
        
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
    """Endpoint pour initier le flux d'authentification TikTok"""
    log("\n🔄 Démarrage du flux d'authentification TikTok")
    
    try:
        # Générer un état CSRF sécurisé
        csrf_state = secrets.token_urlsafe(32)
        log(f"   État CSRF généré: {csrf_state[:10]}...")
        
        # Construire l'URL d'autorisation
        auth_url = f"{TIKTOK_AUTH_URL}?"
        auth_params = {
            'client_key': TIKTOK_CLIENT_KEY,
            'scope': 'user.info.basic',
            'response_type': 'code',
            'redirect_uri': TIKTOK_REDIRECT_URI,
            'state': csrf_state
        }
        
        if debug_mode:
            log("   Paramètres d'autorisation:", "debug", "🔍")
            log(f"   {json.dumps(auth_params, indent=2)}", "debug", "🔍")
        
        # Créer un cookie sécurisé avec l'état CSRF
        response = make_response(jsonify({
            'redirect_url': auth_url + '&'.join(f"{k}={v}" for k, v in auth_params.items())
        }))
        
        response.set_cookie(
            'csrf_state',
            csrf_state,
            max_age=3600,
            secure=True,
            httponly=True,
            samesite='Lax'
        )
        
        log("✅ URL d'autorisation générée avec protection CSRF")
        return response
        
    except Exception as e:
        log(f"❌ ERREUR OAUTH: {str(e)}", "error", "💥")
        if debug_mode:
            log("   Traceback complet:", "error", "🔍")
            import traceback
            log(traceback.format_exc(), "error", "🔍")
        return jsonify({'error': str(e)}), 500

@app.route('/webhook', methods=['GET', 'POST'])
def webhook():
    """Endpoint webhook pour recevoir le code d'autorisation"""
    log("\n🔄 Nouvelle requête webhook reçue")
    log(f"   Méthode: {request.method}")
    
    try:
        if debug_mode:
            log("   Headers de la requête:", "debug", "🔍")
            log(f"   {json.dumps(dict(request.headers), indent=2)}", "debug", "🔍")
            log("   Cookies:", "debug", "🔍")
            log(f"   {json.dumps(dict(request.cookies), indent=2)}", "debug", "🔍")
        
        if request.method == 'GET':
            log("   Type: GET - Recherche du code dans les paramètres")
            if debug_mode:
                log(f"   Paramètres: {json.dumps(dict(request.args), indent=2)}", "debug", "🔍")
            
            code = request.args.get('code')
            state = request.args.get('state')
            
            # Vérifier l'état CSRF
            stored_state = request.cookies.get('csrf_state')
            if not stored_state or stored_state != state:
                log("❌ État CSRF invalide", "error", "🔒")
                if debug_mode:
                    log(f"   État reçu: {state}", "debug", "🔍")
                    log(f"   État stocké: {stored_state}", "debug", "🔍")
                return jsonify({'error': 'État CSRF invalide'}), 400
                
            if not code:
                log("❌ Code manquant dans les paramètres GET", "error", "❌")
                return jsonify({'error': 'Code d\'autorisation manquant'}), 400
        else:
            log("   Type: POST - Recherche du code dans le body")
            data = request.get_json()
            
            if debug_mode:
                log(f"   Body reçu: {json.dumps(data, indent=2)}", "debug", "🔍")
            
            if not data:
                log("❌ Body JSON manquant", "error", "❌")
                return jsonify({'error': 'Données JSON manquantes'}), 400
            
            code = data.get('code')
            if not code:
                log("❌ Code manquant dans le body", "error", "❌")
                return jsonify({'error': 'Code d\'autorisation manquant dans le body'}), 400
        
        log(f"✅ Code extrait: {code[:20]}...")
        
        # Appeler l'API TikTok
        token_data = call_tiktok_api(code)
        
        if token_data:
            # Sauvegarder dans Supabase
            if save_to_database(token_data):
                # Supprimer le cookie CSRF après utilisation
                response = jsonify({
                    'success': True,
                    'message': 'Token obtenu et sauvegardé avec succès',
                    'data': {
                        'access_token': token_data.get('access_token', '')[:20] + '...',
                        'expires_in': token_data.get('expires_in'),
                        'open_id': token_data.get('open_id')
                    }
                })
                response.delete_cookie('csrf_state')
                log("🎉 Opération réussie - Token sauvegardé")
                return response, 200
            else:
                log("⚠️ Échec sauvegarde - Envoi réponse 500", "error", "💥")
                return jsonify({
                    'success': False,
                    'message': 'Token obtenu mais erreur lors de la sauvegarde'
                }), 500
        else:
            log("⚠️ Échec API TikTok - Envoi réponse 500", "error", "💥")
            return jsonify({
                'success': False,
                'message': 'Erreur lors de l\'obtention du token'
            }), 500
            
    except Exception as e:
        log(f"❌ ERREUR WEBHOOK: {str(e)}", "error", "💥")
        if debug_mode:
            log("   Traceback complet:", "error", "🔍")
            import traceback
            log(traceback.format_exc(), "error", "🔍")
        return jsonify({'error': str(e)}), 500

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
    
    app.run(host='0.0.0.0', port=port, debug=debug_mode) 